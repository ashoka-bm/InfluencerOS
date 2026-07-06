"""Semantic lookup projection: a rebuildable SQLite FTS5 keyword index over
curated decision-support material (ADR 0011, Phase 2 slice 6, Decision 1).

This is the keyword leg of the Agentic OS reference's hybrid memory search,
adapted from ``command-centre/src/lib/memory/`` (chunker.ts, reranker.ts,
scope.ts) into stdlib Python over the existing
``workspace-library/index/influencer-os.sqlite``. The vector leg follows the
reference exactly when Command Centre is un-deferred; only the candidate
generator changes — the chunk contract and rerank stages built here are
already the reference's.

Design rules carried from the reference and ADR 0011:

- **Allowlist by construction.** The indexer walks an explicit list of
  workspace paths plus schema-valid PerformanceSummary records whose
  ``semantic_lookup.index_allowed`` is true. It never walks ``analytics/``,
  raw exports, transcripts, or media, and rejects symlinked lookup sources so
  raw payloads cannot leak into the projection by any filter mistake or path
  alias.
- **Creator scope is a hard leak boundary.** Every row carries
  ``creator_slug``; queries require one, search a creator-local FTS table so
  BM25 statistics cannot be influenced by another creator, and filter on the
  real metadata columns in SQL (reference ``scope.ts`` discipline, covered by
  dedicated no-leak tests).
- **Deterministic chunks with provenance.** Heading-aware markdown chunking
  (soft target 1200 chars, hard cap 2000, 150-char overlap on hard splits)
  recording heading and 1-based start/end source lines — same input, same
  chunks (reference chunker.ts).
- **Rerank over denormalized columns.** Final score = BM25 relevance (the
  bm25() score mapped through a sigmoid into (0, 1), the keyword analogue of
  the reference's non-negative cosine similarity) x authority weight
  (longest-prefix path map, config-tunable) x recency decay (exponential
  half-life with a dampening floor; undated rows do not decay), then a
  floor-ratio gate (reference reranker.ts).
- **Stable change detection.** Sources store a sha256 over normalized
  content (LF endings, trimmed) so rebuilds skip unchanged files.
- **Queries are never persisted** (reference privacy default): lookups open
  the database read-only and write nothing.

Like the recall index, the projection is file-first: never a validation
dependency, never the only copy of anything, safe to delete and rebuild.
"""
import hashlib
import json
import math
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

from influencer_os.projects import collect_anchored_learning_records
from influencer_os.recall_index import default_index_path
from influencer_os.research import load_workspace_scope
from influencer_os.validation import ValidationError, load_json


# Chunking tunables (reference chunker.ts DEFAULTS).
CHUNK_TARGET_CHARS = 1200
CHUNK_OVERLAP_CHARS = 150
CHUNK_MAX_CHARS = 2000

# Rerank tunables (reference reranker.ts RERANK_DEFAULTS; the plan's starting
# values). Overridable per creator via context/lookup-config.json.
DEFAULT_HALF_LIFE_DAYS = 14.0
DEFAULT_FLOOR_RATIO = 0.3
DEFAULT_RECENCY_FLOOR = 0.7

# Authority weights by longest-prefix workspace-relative path (plan-adapted
# creator-scope defaults; reference discovery.authorityWeightFor pattern).
# Performance summaries are the only indexed source under projects/.
DEFAULT_AUTHORITY_WEIGHTS = {
    "memory/learnings.md": 1.5,
    "projects/": 1.3,
    "brand_context/": 1.2,
    "research/": 1.0,
}

LOOKUP_CONFIG_RELATIVE = Path("context") / "lookup-config.json"

# Markdown sources indexed for every creator (ADR 0011 allowlist). The walk
# is these exact paths plus index-allowed PerformanceSummary summary_text —
# nothing else, so denied material is unreachable, not filtered out.
MARKDOWN_ALLOWLIST = (
    Path("brand_context") / "identity.md",
    Path("brand_context") / "soul.md",
    Path("brand_context") / "personal-brand.md",
    Path("research") / "findings.md",
    Path("memory") / "learnings.md",
)
STABLE_FINDINGS_DIR = Path("research") / "stable-findings"

CREATE_SOURCES_SQL = """
CREATE TABLE IF NOT EXISTS lookup_sources (
    creator_slug TEXT NOT NULL,
    source_path TEXT NOT NULL,
    title TEXT,
    content_date TEXT,
    authority_weight REAL NOT NULL,
    content_sha256 TEXT NOT NULL,
    indexed_on TEXT NOT NULL,
    PRIMARY KEY (creator_slug, source_path)
)
"""

CREATE_CHUNKS_SQL = """
CREATE TABLE IF NOT EXISTS lookup_chunks (
    id INTEGER PRIMARY KEY,
    creator_slug TEXT NOT NULL,
    creator_profile_id TEXT NOT NULL,
    source_path TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    heading TEXT,
    heading_level INTEGER,
    start_line INTEGER,
    end_line INTEGER,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    authority_weight REAL NOT NULL,
    content_date TEXT,
    indexed_on TEXT NOT NULL,
    UNIQUE (creator_slug, source_path, chunk_index)
)
"""


def chunk_markdown(text, target_chars=CHUNK_TARGET_CHARS,
                   overlap_chars=CHUNK_OVERLAP_CHARS,
                   max_chars=CHUNK_MAX_CHARS):
    """Heading-aware deterministic chunking (reference chunker.ts).

    Headings start new chunks and tag every chunk under them; a heading-less
    run soft-flushes at ``target_chars``; a section over ``max_chars`` is
    window-split with ``overlap_chars`` of overlap. Returns dicts with dense
    ``chunk_index``, ``content``, ``heading``, ``heading_level``, and 1-based
    ``start_line``/``end_line``.
    """
    lines = text.splitlines()
    raw_sections = []
    current_heading = None
    current_level = None
    buffer = []

    def flush_buffer():
        section = _normalize_section(buffer)
        if section is not None:
            raw_sections.append(
                (current_heading, current_level, section[0], section[1])
            )
        buffer.clear()

    for index, line in enumerate(lines):
        heading = _parse_heading(line)
        if heading is not None:
            flush_buffer()
            current_heading, current_level = heading
            continue
        buffer.append((index + 1, line))
        if _buffer_length(buffer) >= target_chars:
            flush_buffer()
    flush_buffer()

    chunks = []
    for heading, level, section_lines, content in raw_sections:
        for piece, start_line, end_line in _split_to_windows(
            section_lines, content, target_chars, overlap_chars, max_chars
        ):
            chunks.append({
                "chunk_index": len(chunks),
                "content": piece,
                "heading": heading,
                "heading_level": level,
                "start_line": start_line,
                "end_line": end_line,
                "content_hash": hashlib.sha256(piece.encode()).hexdigest(),
            })
    return chunks


def _parse_heading(line):
    stripped = line.rstrip()
    if not stripped.startswith("#"):
        return None
    marks = len(stripped) - len(stripped.lstrip("#"))
    if not 1 <= marks <= 6:
        return None
    rest = stripped[marks:]
    if not rest.startswith(" ") and not rest.startswith("\t"):
        return None
    title = rest.strip().rstrip("#").strip()
    if not title:
        return None
    return title, marks


def _buffer_length(buffer):
    if not buffer:
        return 0
    return sum(len(text) for _number, text in buffer) + len(buffer) - 1


def _normalize_section(buffer):
    """Trim blank edge lines and edge whitespace; None when nothing remains."""
    first = next(
        (index for index, (_n, text) in enumerate(buffer) if text.strip()), None
    )
    if first is None:
        return None
    last = len(buffer) - 1
    while last > first and not buffer[last][1].strip():
        last -= 1
    active = []
    for offset, (line_number, text) in enumerate(buffer[first:last + 1]):
        if offset == 0:
            text = text.lstrip()
        if offset == last - first:
            text = text.rstrip()
        active.append((line_number, text))
    content = "\n".join(text for _number, text in active)
    if not content:
        return None
    return active, content


def _split_to_windows(section_lines, content, target_chars, overlap_chars,
                      max_chars):
    """Window-split oversized sections keeping source line ranges."""
    if len(content) <= max_chars:
        yield content, section_lines[0][0], section_lines[-1][0]
        return

    spans = []
    offset = 0
    for index, (line_number, text) in enumerate(section_lines):
        start = offset
        end = start + len(text)
        offset = end + (0 if index == len(section_lines) - 1 else 1)
        spans.append((line_number, start, end))

    def line_for_offset(target):
        for line_number, start, end in spans:
            if start <= target <= end:
                return line_number
        return spans[-1][0]

    window_size = min(target_chars, max_chars)
    step = max(1, target_chars - overlap_chars)
    start = 0
    while start < len(content):
        end = min(start + window_size, len(content))
        raw = content[start:end]
        leading = len(raw) - len(raw.lstrip())
        trailing = len(raw) - len(raw.rstrip())
        adjusted_start = start + leading
        adjusted_end = end - trailing
        piece = content[adjusted_start:adjusted_end]
        if piece:
            yield (piece, line_for_offset(adjusted_start),
                   line_for_offset(max(adjusted_start, adjusted_end - 1)))
        if end >= len(content):
            break
        start += step


def load_lookup_config(workspace_dir):
    """Per-creator rerank/authority tunables from an optional
    ``context/lookup-config.json``; defaults are the reference's. A present
    but malformed config fails closed rather than silently reverting."""
    config = {
        "half_life_days": DEFAULT_HALF_LIFE_DAYS,
        "floor_ratio": DEFAULT_FLOOR_RATIO,
        "recency_floor": DEFAULT_RECENCY_FLOOR,
        "authority_weights": dict(DEFAULT_AUTHORITY_WEIGHTS),
    }
    config_path = Path(workspace_dir) / LOOKUP_CONFIG_RELATIVE
    if not config_path.exists():
        return config
    data = load_json(config_path)
    if not isinstance(data, dict):
        raise ValidationError(f"{config_path}: lookup config must be a JSON object")
    unknown = sorted(set(data) - set(config))
    if unknown:
        raise ValidationError(
            f"{config_path}: unknown lookup config keys {unknown}; "
            f"expected a subset of {sorted(config)}"
        )
    for key in ("half_life_days", "floor_ratio", "recency_floor"):
        if key in data:
            value = data[key]
            if not isinstance(value, (int, float)) or isinstance(value, bool) \
                    or not math.isfinite(value) or value <= 0:
                raise ValidationError(
                    f"{config_path}: {key} must be a positive number, got {value!r}"
                )
            config[key] = float(value)
    if config["floor_ratio"] >= 1 or config["recency_floor"] > 1:
        raise ValidationError(
            f"{config_path}: floor_ratio must be < 1 and recency_floor <= 1"
        )
    if "authority_weights" in data:
        weights = data["authority_weights"]
        if not isinstance(weights, dict) or not all(
            isinstance(prefix, str) and isinstance(weight, (int, float))
            and not isinstance(weight, bool) and math.isfinite(weight)
            and weight > 0
            for prefix, weight in weights.items()
        ):
            raise ValidationError(
                f"{config_path}: authority_weights must map path prefixes to "
                "positive numbers"
            )
        config["authority_weights"] = {
            prefix: float(weight) for prefix, weight in weights.items()
        }
    return config


def authority_weight_for(source_path, weights):
    """Longest matching path-prefix weight, 1.0 when nothing matches
    (reference discovery.authorityWeightFor)."""
    best_len = -1
    best_weight = 1.0
    for prefix, weight in weights.items():
        if str(source_path).startswith(prefix) and len(prefix) > best_len:
            best_len = len(prefix)
            best_weight = weight
    return best_weight


def _normalized_sha256(text):
    """Stable change-detection hash: LF endings, trimmed (reference
    indexer discipline)."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    return hashlib.sha256(normalized.encode()).hexdigest()


def _title_from_markdown(text):
    for line in text.splitlines():
        parsed = _parse_heading(line)
        if parsed is not None and parsed[1] == 1:
            return parsed[0]
    return None


def _date_from_filename(path):
    stem = Path(path).name
    if len(stem) >= 10:
        candidate = stem[:10]
        try:
            date.fromisoformat(candidate)
            return candidate
        except ValueError:
            pass
    return None


def _quote_identifier(name):
    if not name.startswith("lookup_fts_"):
        raise ValidationError(f"unsafe lookup table name: {name!r}")
    return '"' + name.replace('"', '""') + '"'


def _fts_table_name(creator_slug):
    digest = hashlib.sha256(creator_slug.encode()).hexdigest()[:16]
    return f"lookup_fts_{digest}"


def _has_symlink_component(path, root):
    root = Path(root)
    path = Path(path)
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def _require_lookup_source_file(path, workspace_dir):
    """Lookup sources must be real in-workspace files, not symlink aliases.

    The allowlist is meaningful only if an allowlisted path cannot redirect to
    denied material such as analytics/raw, transcripts, media, or secrets.
    """
    path = Path(path)
    workspace_dir = Path(workspace_dir)
    if _has_symlink_component(path, workspace_dir):
        raise ValidationError(
            f"{path}: lookup sources must not be symlinks or live under "
            "symlinked directories"
        )
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError:
        raise ValidationError(f"{path}: lookup source does not exist") from None
    workspace_resolved = workspace_dir.resolve()
    try:
        resolved.relative_to(workspace_resolved)
    except ValueError:
        raise ValidationError(
            f"{path}: lookup source must resolve inside {workspace_dir}"
        ) from None
    if not path.is_file():
        raise ValidationError(f"{path}: lookup source must be a regular file")


def collect_lookup_sources(workspace_dir, config=None):
    """The full indexable surface for one creator: markdown allowlist files,
    stable findings, and index-allowed PerformanceSummary narratives.

    Returns source dicts carrying their pre-chunked content. Performance
    summaries index only ``semantic_lookup.summary_text`` from records the
    shared anchoring walk already schema-validated (the same fail-closed seam
    the recall index uses); ``index_allowed: false`` records are skipped, and
    ``analytics/`` is never visited by construction.
    """
    workspace_dir = Path(workspace_dir)
    if config is None:
        config = load_lookup_config(workspace_dir)
    weights = config["authority_weights"]
    sources = []

    def add_markdown(path):
        relative = path.relative_to(workspace_dir)
        _require_lookup_source_file(path, workspace_dir)
        text = path.read_text()
        sources.append({
            "source_path": str(relative),
            "title": _title_from_markdown(text),
            "content_date": _date_from_filename(relative),
            "authority_weight": authority_weight_for(relative, weights),
            "content_sha256": _normalized_sha256(text),
            "chunks": chunk_markdown(text),
        })

    for relative in MARKDOWN_ALLOWLIST:
        path = workspace_dir / relative
        if path.exists():
            add_markdown(path)

    stable_dir = workspace_dir / STABLE_FINDINGS_DIR
    if stable_dir.exists() and _has_symlink_component(stable_dir, workspace_dir):
        raise ValidationError(
            f"{stable_dir}: lookup source directories must not be symlinks"
        )
    if stable_dir.is_dir():
        for path in sorted(stable_dir.glob("*.md")):
            add_markdown(path)

    for record_path, record_type, _id_field, record in (
        collect_anchored_learning_records(workspace_dir)
    ):
        if record_type != "performance-summary":
            continue
        lookup = record["semantic_lookup"]
        if lookup["index_allowed"] is not True:
            continue
        summary_text = lookup["summary_text"]
        relative = record_path.relative_to(workspace_dir)
        _require_lookup_source_file(record_path, workspace_dir)
        # JSON-sourced chunks cite the record, not text lines: chunker line
        # numbers would point into summary_text, not the file on disk.
        chunks = chunk_markdown(summary_text)
        for chunk in chunks:
            chunk["heading"] = record["performance_summary_id"]
            chunk["heading_level"] = None
            chunk["start_line"] = None
            chunk["end_line"] = None
        sources.append({
            "source_path": str(relative),
            "title": record["performance_summary_id"],
            "content_date": record["created_on"],
            "authority_weight": authority_weight_for(relative, weights),
            "content_sha256": _normalized_sha256(summary_text),
            "chunks": chunks,
        })

    return sources


def rebuild_lookup(workspace_path, db_path=None):
    """Rebuild one creator's lookup projection. Idempotent and incremental:
    sources whose normalized hash and authority weight are unchanged keep
    their rows; changed sources are re-chunked; vanished sources are removed.
    Deleting the database and rebuilding reproduces identical rows modulo
    ``indexed_on``."""
    workspace_dir = Path(workspace_path)
    scope = load_workspace_scope(workspace_dir)
    config = load_lookup_config(workspace_dir)
    sources = collect_lookup_sources(workspace_dir, config=config)
    db_file = Path(db_path) if db_path else default_index_path(workspace_dir)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    indexed_on = datetime.now(timezone.utc).isoformat(timespec="seconds")
    creator_slug = scope["creator_slug"]

    connection = sqlite3.connect(db_file)
    try:
        _require_fts5(connection)
        connection.execute(CREATE_SOURCES_SQL)
        connection.execute(CREATE_CHUNKS_SQL)

        existing = {
            row[0]: (row[1], row[2])
            for row in connection.execute(
                "SELECT source_path, content_sha256, authority_weight "
                "FROM lookup_sources WHERE creator_slug = ?",
                (creator_slug,),
            )
        }
        current_paths = {source["source_path"] for source in sources}

        skipped = 0
        for stale_path in sorted(set(existing) - current_paths):
            _delete_source(connection, creator_slug, stale_path)
        for source in sources:
            previous = existing.get(source["source_path"])
            if previous == (source["content_sha256"], source["authority_weight"]):
                skipped += 1
                continue
            _delete_source(connection, creator_slug, source["source_path"])
            connection.execute(
                "INSERT INTO lookup_sources (creator_slug, source_path, title, "
                "content_date, authority_weight, content_sha256, indexed_on) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (creator_slug, source["source_path"], source["title"],
                 source["content_date"], source["authority_weight"],
                 source["content_sha256"], indexed_on),
            )
            connection.executemany(
                "INSERT INTO lookup_chunks (creator_slug, creator_profile_id, "
                "source_path, chunk_index, heading, heading_level, start_line, "
                "end_line, content, content_hash, authority_weight, "
                "content_date, indexed_on) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (creator_slug, scope["creator_profile_id"],
                     source["source_path"], chunk["chunk_index"],
                     chunk["heading"], chunk["heading_level"],
                     chunk["start_line"], chunk["end_line"], chunk["content"],
                     chunk["content_hash"], source["authority_weight"],
                     source["content_date"], indexed_on)
                    for chunk in source["chunks"]
                ],
            )
        _rebuild_creator_fts(connection, creator_slug)
        connection.commit()
    finally:
        connection.close()

    chunk_count = sum(len(source["chunks"]) for source in sources)
    return {
        "db_path": db_file,
        "creator_slug": creator_slug,
        "source_count": len(sources),
        "chunk_count": chunk_count,
        "unchanged_sources": skipped,
    }


def _delete_source(connection, creator_slug, source_path):
    connection.execute(
        "DELETE FROM lookup_chunks WHERE creator_slug = ? AND source_path = ?",
        (creator_slug, source_path),
    )
    connection.execute(
        "DELETE FROM lookup_sources WHERE creator_slug = ? AND source_path = ?",
        (creator_slug, source_path),
    )


def _rebuild_creator_fts(connection, creator_slug):
    """Populate a creator-local FTS table so BM25 statistics cannot be affected
    by another creator's corpus."""
    table = _quote_identifier(_fts_table_name(creator_slug))
    connection.execute(
        f"CREATE VIRTUAL TABLE IF NOT EXISTS {table} USING fts5("
        "content, heading, chunk_id UNINDEXED)"
    )
    connection.execute(f"DELETE FROM {table}")
    connection.execute(
        f"INSERT INTO {table} (rowid, content, heading, chunk_id) "
        "SELECT id, content, COALESCE(heading, ''), id "
        "FROM lookup_chunks WHERE creator_slug = ? "
        "ORDER BY source_path, chunk_index",
        (creator_slug,),
    )


def _require_fts5(connection):
    try:
        connection.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS _fts5_probe USING fts5(probe)"
        )
        connection.execute("DROP TABLE IF EXISTS _fts5_probe")
    except sqlite3.OperationalError as exc:
        raise ValidationError(
            f"this Python's sqlite3 lacks FTS5 support ({exc}); the semantic "
            "lookup projection requires an FTS5-enabled SQLite build"
        ) from None


def _fts_query(terms):
    """A safe FTS5 MATCH string: every term becomes a quoted token (implicit
    AND), so user input can never inject FTS5 query syntax."""
    tokens = [token for term in terms for token in term.split()]
    if not tokens:
        raise ValidationError("query-lookup requires at least one search term")
    return " ".join('"' + token.replace('"', '""') + '"' for token in tokens)


def bm25_relevance(bm25_score):
    """Map an FTS5 bm25() score (lower is better, magnitude corpus-dependent,
    can cross zero on tiny corpora) through a sigmoid into (0, 1). The rerank
    stages assume non-negative relevance the way the reference's cosine
    similarities are non-negative: authority must boost, and the floor-ratio
    gate must always keep the top hit."""
    return 1.0 / (1.0 + math.exp(bm25_score))


def recency_factor(content_date, half_life_days, today=None):
    """Exponential decay from a YYYY-MM-DD date; 1.0 for undated rows and
    unparseable dates; future dates clamp to 1.0 (reference reranker.ts)."""
    if not content_date:
        return 1.0
    try:
        content = date.fromisoformat(str(content_date)[:10])
    except ValueError:
        return 1.0
    if today is None:
        today = datetime.now(timezone.utc).date()
    age_days = max(0, (today - content).days)
    return math.exp(-age_days / half_life_days)


def rerank(hits, config, today=None):
    """The reference three-stage rerank over candidate rows: authority boost,
    dampened recency decay, then floor-ratio gating. ``hits`` carry a
    non-negative ``relevance`` (here ``-bm25``); returns hits sorted by
    ``final_score`` descending with sub-floor rows dropped."""
    if not hits:
        return []
    scored = []
    for hit in hits:
        score = hit["relevance"] * hit["authority_weight"]
        factor = recency_factor(
            hit["content_date"], config["half_life_days"], today=today
        )
        score *= (
            config["recency_floor"] + (1.0 - config["recency_floor"]) * factor
        )
        scored.append((score, hit))
    top_score = max(score for score, _hit in scored)
    threshold = top_score * config["floor_ratio"]
    kept = [
        dict(hit, final_score=round(score, 6))
        for score, hit in scored
        if score >= threshold
    ]
    kept.sort(key=lambda hit: (-hit["final_score"], hit["source_path"],
                               hit["chunk_index"]))
    return kept


QUERY_COLUMNS = (
    "creator_slug", "source_path", "chunk_index", "heading", "start_line",
    "end_line", "content", "authority_weight", "content_date",
)


def query_lookup(workspace_path, terms, db_path=None, limit=8):
    """Creator-scoped lookup over the projection. The scope predicate is SQL
    (``creator_slug = ?``), the database is opened read-only so queries are
    never persisted, and results cite ``source_path:start_line-end_line``."""
    workspace_dir = Path(workspace_path)
    scope = load_workspace_scope(workspace_dir)
    config = load_lookup_config(workspace_dir)
    creator_slug = scope["creator_slug"]
    if limit < 1:
        raise ValidationError(f"query limit must be positive, got {limit}")
    db_file = Path(db_path) if db_path else default_index_path(workspace_dir)
    if not db_file.exists():
        raise ValidationError(
            f"no lookup database at {db_file}; run rebuild-lookup first"
        )
    match = _fts_query(terms)

    # Read-only open (privacy default): a query cannot write, journal, or
    # otherwise persist anything.
    connection = sqlite3.connect(f"file:{db_file}?mode=ro", uri=True)
    try:
        try:
            fts_table = _fts_table_name(creator_slug)
            quoted_fts_table = _quote_identifier(fts_table)
            fetched = connection.execute(
                "SELECT c.creator_slug, c.source_path, c.chunk_index, "
                "c.heading, c.start_line, c.end_line, c.content, "
                f"c.authority_weight, c.content_date, bm25({quoted_fts_table}) "
                f"FROM {quoted_fts_table} JOIN lookup_chunks c "
                f"ON c.id = {quoted_fts_table}.chunk_id "
                f"WHERE {quoted_fts_table} MATCH ? AND c.creator_slug = ? "
                f"ORDER BY bm25({quoted_fts_table}) LIMIT ?",
                (match, creator_slug, max(limit * 4, 24)),
            ).fetchall()
        except sqlite3.OperationalError as exc:
            raise ValidationError(
                f"lookup query failed ({exc}); rebuild the lookup projection "
                "with rebuild-lookup"
            ) from None
    finally:
        connection.close()

    hits = [
        dict(zip(QUERY_COLUMNS, row[:-1]), relevance=bm25_relevance(row[-1]))
        for row in fetched
    ]
    return rerank(hits, config)[:limit]
