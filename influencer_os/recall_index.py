"""Local recall index: a rebuildable SQLite projection of creator research
records (ADR 0010, Phase 1 slice 4 batch B) and Phase 2 learning records —
published post records, analytics snapshots, and performance summaries
(Phase 2 slice 5).

One shared database at ``workspace-library/index/influencer-os.sqlite`` holds
rows for every creator; ``rebuild_index`` deletes and reinserts only one
creator's rows. The index is file-first by design: it is never a validation
dependency, it is never the only copy of anything, and it can be deleted and
rebuilt at any time. Source paths are stored relative to the Creator
Workspace so the database survives machine moves.
"""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from influencer_os.projects import collect_anchored_learning_records
from influencer_os.research import (
    RESEARCH_JSONL_FILES,
    _iter_jsonl_lines,
    load_workspace_scope,
    parse_frontmatter,
)
from influencer_os.validation import ValidationError, load_json


INDEX_DB_RELATIVE = Path("index") / "influencer-os.sqlite"

# Record types whose bare id must resolve to exactly one source locator.
# Finding ids are exempt: a finding may live in findings.md and also be
# promoted into a stable-finding file, and the recall draft resolves
# finding_id to "findings.md section or stable finding metadata". The
# stable_finding_id itself is unique — one stable-finding file per id.
UNIQUE_RECORD_TYPES = frozenset({
    "research-evidence",
    "metric-snapshot",
    "idea-queue-entry",
    "idea-promotion",
    "project",
    "video-understanding-pack",
    "content-card",
    "stable-finding",
    "published-post-record",
    "analytics-snapshot",
    "performance-summary",
    "generation-approval-record",
    "generation-asset",
    "quality-review",
})

INDEX_COLUMNS = (
    "record_id",
    "record_type",
    "creator_profile_id",
    "creator_slug",
    "project_id",
    "source_path",
    "line_number",
    "content_hash",
    "indexed_on",
)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS records (
    record_id TEXT NOT NULL,
    record_type TEXT NOT NULL,
    creator_profile_id TEXT NOT NULL,
    creator_slug TEXT NOT NULL,
    project_id TEXT,
    source_path TEXT NOT NULL,
    line_number INTEGER,
    content_hash TEXT NOT NULL,
    indexed_on TEXT NOT NULL,
    PRIMARY KEY (creator_slug, record_type, record_id, source_path)
)
"""

CREATE_LOOKUP_INDEX_SQL = (
    "CREATE INDEX IF NOT EXISTS idx_records_record_id ON records (record_id)"
)


def default_index_path(workspace_dir):
    """ADR 0010 default: one database beside the creators/ root. A workspace
    outside the standard layout must name its database explicitly."""
    workspace_dir = Path(workspace_dir).resolve()
    if workspace_dir.parent.name != "creators":
        raise ValidationError(
            f"{workspace_dir} is not under a creators/ root; pass an explicit "
            "index database path (the ADR 0010 default is "
            "workspace-library/index/influencer-os.sqlite)"
        )
    return workspace_dir.parent.parent / INDEX_DB_RELATIVE


def _hash_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _required_field(data, field, path):
    value = data.get(field)
    if not value:
        raise ValidationError(f"{path}: record has no {field}")
    return value


def collect_index_rows(workspace_dir, scope=None):
    """Walk one Creator Workspace and return index rows for every record kind
    the recall draft resolves, failing closed on ambiguous ids."""
    workspace_dir = Path(workspace_dir)
    if scope is None:
        scope = load_workspace_scope(workspace_dir)
    research_dir = workspace_dir / "research"
    rows = []

    def add_row(record_id, record_type, source_path, content_hash,
                line_number=None, project_id=None):
        rows.append({
            "record_id": record_id,
            "record_type": record_type,
            "creator_profile_id": scope["creator_profile_id"],
            "creator_slug": scope["creator_slug"],
            "project_id": project_id,
            "source_path": str(source_path.relative_to(workspace_dir)),
            "line_number": line_number,
            "content_hash": content_hash,
        })

    runs_dir = research_dir / "runs"
    if runs_dir.exists():
        for run_dir in sorted(path for path in runs_dir.iterdir() if path.is_dir()):
            for filename, schema_name, id_field, _outputs_field in RESEARCH_JSONL_FILES:
                jsonl_path = run_dir / filename
                if not jsonl_path.exists():
                    continue
                for line_number, line in _iter_jsonl_lines(jsonl_path):
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValidationError(
                            f"{jsonl_path}:{line_number}: invalid JSON: {exc}"
                        ) from None
                    record_id = _required_field(
                        record, id_field, f"{jsonl_path}:{line_number}"
                    )
                    add_row(record_id, schema_name, jsonl_path,
                            _hash_bytes(line.encode()), line_number=line_number)

    findings_path = research_dir / "findings.md"
    if findings_path.exists():
        data, _body = parse_frontmatter(findings_path)
        file_hash = _hash_bytes(findings_path.read_bytes())
        for finding_id in data.get("finding_ids", []):
            add_row(finding_id, "research-finding", findings_path, file_hash)

    stable_dir = research_dir / "stable-findings"
    if stable_dir.exists():
        for stable_path in sorted(stable_dir.glob("*.md")):
            data, _body = parse_frontmatter(stable_path)
            file_hash = _hash_bytes(stable_path.read_bytes())
            add_row(_required_field(data, "stable_finding_id", stable_path),
                    "stable-finding", stable_path, file_hash)
            add_row(_required_field(data, "finding_id", stable_path),
                    "research-finding", stable_path, file_hash)

    file_scans = (
        (research_dir / "idea-queue" / "entries", "*.json",
         "idea_queue_entry_id", "idea-queue-entry"),
        (research_dir / "idea-promotions", "*.json",
         "idea_promotion_id", "idea-promotion"),
        (research_dir / "video-understanding-packs", "*.json",
         "video_understanding_pack_id", "video-understanding-pack"),
    )
    for directory, pattern, id_field, record_type in file_scans:
        if directory.exists():
            for record_path in sorted(directory.glob(pattern)):
                record = load_json(record_path)
                add_row(_required_field(record, id_field, record_path),
                        record_type, record_path,
                        _hash_bytes(record_path.read_bytes()))

    if runs_dir.exists():
        for pack_path in sorted(runs_dir.glob("*/video-understanding-packs/*.json")):
            record = load_json(pack_path)
            add_row(_required_field(record, "video_understanding_pack_id", pack_path),
                    "video-understanding-pack", pack_path,
                    _hash_bytes(pack_path.read_bytes()))

    projects_dir = workspace_dir / "projects"
    if projects_dir.exists():
        for project_dir in sorted(
            path for path in projects_dir.iterdir() if path.is_dir()
        ):
            manifest_path = project_dir / "project.json"
            if manifest_path.exists():
                manifest = load_json(manifest_path)
                project_id = _required_field(manifest, "project_id", manifest_path)
                add_row(project_id, "project", manifest_path,
                        _hash_bytes(manifest_path.read_bytes()),
                        project_id=project_id)

    # Phase 3 generation records (ADR 0023 slice 4): approval records and
    # manifest ledger rows, validated through the same shared seams the
    # project validator runs so a schema-invalid or unbound record fails
    # closed here too.
    if projects_dir.exists():
        from influencer_os.generation import (
            validate_project_generation_assets,
            validate_project_generation_records,
        )

        for project_dir in sorted(
            path for path in projects_dir.iterdir() if path.is_dir()
        ):
            manifest_path = project_dir / "project.json"
            if not manifest_path.exists():
                continue
            manifest = load_json(manifest_path)
            project_id = manifest.get("project_id")
            approvals, _warnings = validate_project_generation_records(
                project_dir, manifest
            )
            for record_id in approvals:
                record_path = (
                    project_dir / "generation" / "approval-records" / f"{record_id}.json"
                )
                add_row(record_id, "generation-approval-record", record_path,
                        _hash_bytes(record_path.read_bytes()),
                        project_id=project_id)
            rows_by_id = validate_project_generation_assets(
                project_dir, manifest, approvals
            )
            ledger_path = project_dir / "generation" / "asset-manifest.json"
            if rows_by_id:
                ledger_hash = _hash_bytes(ledger_path.read_bytes())
                for asset_id in rows_by_id:
                    add_row(asset_id, "generation-asset", ledger_path,
                            ledger_hash, project_id=project_id)

    # Phase 2 learning records (slice 5): the shared anchoring walk fails
    # closed on schema-invalid, misnamed, or unanchored records; `validate
    # workspace` runs the same function at rest.
    for record_path, record_type, id_field, record in (
        collect_anchored_learning_records(workspace_dir)
    ):
        add_row(record[id_field], record_type, record_path,
                _hash_bytes(record_path.read_bytes()),
                project_id=record["project_id"])

    board_path = workspace_dir / "boards" / "content-board.json"
    if board_path.exists():
        board = load_json(board_path)
        board_hash = _hash_bytes(board_path.read_bytes())
        for card in board.get("cards", []):
            card_id = _required_field(card, "content_card_id", board_path)
            card_project_id = (
                card.get("source_record_id")
                if card.get("source_record_type") == "project"
                else None
            )
            add_row(card_id, "content-card", board_path, board_hash,
                    project_id=card_project_id)

    seen = {}
    for row in rows:
        if row["record_type"] not in UNIQUE_RECORD_TYPES:
            continue
        key = (row["record_type"], row["record_id"])
        locator = (row["source_path"], row["line_number"])
        if key in seen and seen[key] != locator:
            raise ValidationError(
                f"{row['record_type']} id {row['record_id']!r} appears at more "
                f"than one source ({seen[key][0]} and {row['source_path']}); "
                "ids must resolve to exactly one locator"
            )
        seen[key] = locator

    return rows


def rebuild_index(workspace_path, db_path=None):
    """Rebuild one creator's rows in the shared recall index. Idempotent:
    the creator's previous rows are deleted before reinsertion."""
    workspace_dir = Path(workspace_path)
    scope = load_workspace_scope(workspace_dir)
    rows = collect_index_rows(workspace_dir, scope=scope)
    db_file = Path(db_path) if db_path else default_index_path(workspace_dir)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    indexed_on = datetime.now(timezone.utc).isoformat(timespec="seconds")

    connection = sqlite3.connect(db_file)
    try:
        connection.execute(CREATE_TABLE_SQL)
        connection.execute(CREATE_LOOKUP_INDEX_SQL)
        connection.execute(
            "DELETE FROM records WHERE creator_slug = ?", (scope["creator_slug"],)
        )
        connection.executemany(
            f"INSERT INTO records ({', '.join(INDEX_COLUMNS)}) "
            f"VALUES ({', '.join('?' for _ in INDEX_COLUMNS)})",
            [
                tuple(row[column] for column in INDEX_COLUMNS[:-1]) + (indexed_on,)
                for row in rows
            ],
        )
        connection.commit()
    finally:
        connection.close()

    return {
        "db_path": db_file,
        "creator_slug": scope["creator_slug"],
        "row_count": len(rows),
    }


def resolve_record_id(db_path, record_id, creator_slug=None):
    """Resolve a record id to its indexed locator rows. Returns a list of
    dicts (multiple rows only for the documented finding duality or for
    cross-creator id reuse when creator_slug is not given)."""
    query = (
        f"SELECT {', '.join(INDEX_COLUMNS)} FROM records WHERE record_id = ?"
    )
    params = [record_id]
    if creator_slug is not None:
        query += " AND creator_slug = ?"
        params.append(creator_slug)
    query += " ORDER BY record_type, source_path, line_number"
    connection = sqlite3.connect(db_path)
    try:
        fetched = connection.execute(query, params).fetchall()
    finally:
        connection.close()
    return [dict(zip(INDEX_COLUMNS, row)) for row in fetched]
