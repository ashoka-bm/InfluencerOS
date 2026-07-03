"""Research-module validation: JSONL records, findings frontmatter, and
creator research state (ADR 0020 slice, batch B).

Frontmatter is a scoped YAML subset matching the hand-rolled validator
philosophy — fail-closed, no third-party dependency. Supported: top-level
``key: value`` scalars and ``key:`` followed by ``- item`` string lists.
Nested mappings or any other construct are errors, never silent skips.
"""
import json
from pathlib import Path

from influencer_os.validation import ValidationError, load_json, validate_file, validate_record


RESEARCH_INTELLIGENCE_FILES = {
    "sources.json": "research-sources",
    "hashtags.json": "research-hashtags",
    "search-terms.json": "research-search-terms",
    "reference-creators.json": "reference-creators",
    "watchlist.json": "research-watchlist",
}

RESEARCH_JSONL_FILES = (
    ("evidence.jsonl", "research-evidence"),
    ("metric-snapshots.jsonl", "metric-snapshot"),
)

SYSTEM_JSONL_FILES = (
    ("project-warnings.jsonl", "project-warning"),
    ("creator-events.jsonl", "system-event"),
)

# Formats with a production plan schema (projects.PRODUCTION_PLAN_SCHEMAS).
# A promotion must approve at least one of these; approving only unsupported
# formats records approval intent on the queue entry instead (ADR 0020).
PRODUCTION_SUPPORTED_FORMATS = frozenset({
    "format_short_form_video",
    "format_carousel",
    "format_single_image_post",
    "format_story_sequence",
})


def _iter_jsonl_lines(path):
    # Split on newlines only: splitlines() would also break on U+2028/U+2029,
    # which are legal inside JSON strings, corrupting records and line numbers.
    for line_number, line in enumerate(path.read_text().split("\n"), start=1):
        if line.strip():
            yield line_number, line


def validate_jsonl_file(schema_name, path, record_check=None):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Missing JSONL file: {path}")
    records = []
    for line_number, line in _iter_jsonl_lines(path):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"{path}:{line_number}: invalid JSON: {exc}") from None
        try:
            validate_record(schema_name, record)
            if record_check is not None:
                record_check(record)
        except ValidationError as exc:
            raise ValidationError(f"{path}:{line_number}: {exc}") from None
        records.append(record)
    return records


def check_project_warning_pairing(record):
    """A warning targeting promoted work carries both project_id and
    idea_promotion_id; a queue-level warning carries neither (ADR 0020)."""
    if ("project_id" in record) != ("idea_promotion_id" in record):
        raise ValidationError(
            "project warning must carry both project_id and idea_promotion_id "
            "when it targets promoted work, and neither for queue-level warnings"
        )


def load_workspace_scope(workspace_dir):
    """The research module is creator-scoped: every record in a Creator
    Workspace must belong to the workspace's creator."""
    manifest_path = Path(workspace_dir) / "creator-workspace.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing creator workspace manifest: {manifest_path}")
    manifest = load_json(manifest_path)
    try:
        validate_record("creator-workspace", manifest)
    except ValidationError as exc:
        raise ValidationError(f"{manifest_path}: {exc}") from None
    return {
        "creator_profile_id": manifest["creator_profile_id"],
        "creator_slug": manifest["creator_slug"],
    }


def check_creator_scope(record, scope, context=None):
    """Pin a record's creator fields to the owning workspace. Fields a
    record's schema does not carry (project warnings) are skipped."""
    for field, expected in scope.items():
        value = record.get(field)
        if value is not None and value != expected:
            prefix = f"{context}: " if context else ""
            raise ValidationError(
                f"{prefix}{field} {value!r} does not match the owning "
                f"creator workspace ({expected!r})"
            )


def parse_frontmatter(path):
    path = Path(path)
    text = path.read_text()
    if not text.startswith("---\n"):
        raise ValidationError(f"{path}: missing frontmatter block")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValidationError(f"{path}: unterminated frontmatter block")
    data = _parse_yaml_subset(text[4:end], path)
    body = text[end + len("\n---\n"):]
    return data, body


def _parse_yaml_subset(block, path):
    data = {}
    current_list_key = None
    for line_number, raw_line in enumerate(block.splitlines(), start=2):
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            if current_list_key is None:
                raise ValidationError(f"{path}:{line_number}: list item without a list key")
            data[current_list_key].append(_parse_scalar(stripped[2:].strip()))
            continue
        if raw_line[0] in (" ", "\t"):
            raise ValidationError(
                f"{path}:{line_number}: nested frontmatter is not supported (scoped YAML subset)"
            )
        key, separator, value = raw_line.partition(":")
        if not separator or not key.strip():
            raise ValidationError(f"{path}:{line_number}: expected 'key: value'")
        key = key.strip()
        value = value.strip()
        if value:
            data[key] = _parse_scalar(value)
            current_list_key = None
        else:
            data[key] = []
            current_list_key = key
    return data


def _parse_scalar(value):
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1]
    if value == "true":
        return True
    if value == "false":
        return False
    try:
        return int(value)
    except ValueError:
        return value


def validate_findings_file(path):
    data, body = parse_frontmatter(path)
    try:
        validate_record("research-findings", data)
    except ValidationError as exc:
        raise ValidationError(f"{path}: {exc}") from None
    limit = data["summary_char_limit"]
    if len(body) > limit:
        raise ValidationError(
            f"{path}: body is {len(body)} characters, over summary_char_limit {limit}"
        )
    return data


def validate_stable_finding_file(path):
    data, _ = parse_frontmatter(path)
    try:
        validate_record("stable-finding", data)
    except ValidationError as exc:
        raise ValidationError(f"{path}: {exc}") from None
    return data


def validate_research(workspace_path):
    workspace_dir = Path(workspace_path)
    research_dir = workspace_dir / "research"
    if not research_dir.exists():
        raise FileNotFoundError(f"Missing research directory: {research_dir}")

    scope = load_workspace_scope(workspace_dir)

    def scoped(record):
        check_creator_scope(record, scope)

    checked = []

    schedule_path = workspace_dir / "content-schedule.json"
    if schedule_path.exists():
        validate_file("creator-content-schedule", schedule_path)
        check_creator_scope(load_json(schedule_path), scope, schedule_path)
        checked.append("content-schedule.json")

    findings_path = research_dir / "findings.md"
    if findings_path.exists():
        findings_data = validate_findings_file(findings_path)
        check_creator_scope(findings_data, scope, findings_path)
        checked.append("research/findings.md")

    stable_dir = research_dir / "stable-findings"
    if stable_dir.exists():
        for stable_path in sorted(stable_dir.glob("*.md")):
            stable_data = validate_stable_finding_file(stable_path)
            check_creator_scope(stable_data, scope, stable_path)
            checked.append(str(stable_path.relative_to(workspace_dir)))

    runs_dir = research_dir / "runs"
    if runs_dir.exists():
        for run_dir in sorted(path for path in runs_dir.iterdir() if path.is_dir()):
            run_manifest = run_dir / "research-run.json"
            if not run_manifest.exists():
                raise ValidationError(f"Research run folder has no research-run.json: {run_dir}")
            validate_file("research-run", run_manifest)
            run_record = load_json(run_manifest)
            if run_record["research_run_id"] != run_dir.name:
                raise ValidationError(
                    f"{run_manifest}: folder name {run_dir.name!r} does not match "
                    f"research_run_id {run_record['research_run_id']!r} "
                    "(layout is research/runs/<research-run-id>/)"
                )
            check_creator_scope(run_record, scope, run_manifest)
            checked.append(str(run_manifest.relative_to(workspace_dir)))
            for filename, schema_name in RESEARCH_JSONL_FILES:
                jsonl_path = run_dir / filename
                if jsonl_path.exists():
                    validate_jsonl_file(schema_name, jsonl_path, record_check=scoped)
                    checked.append(str(jsonl_path.relative_to(workspace_dir)))

    for filename, schema_name in RESEARCH_INTELLIGENCE_FILES.items():
        intel_path = research_dir / "intelligence" / filename
        if intel_path.exists():
            validate_file(schema_name, intel_path)
            check_creator_scope(load_json(intel_path), scope, intel_path)
            checked.append(str(intel_path.relative_to(workspace_dir)))

    board_path = workspace_dir / "boards" / "content-board.json"
    if board_path.exists():
        validate_file("content-board", board_path)
        check_creator_scope(load_json(board_path), scope, board_path)
        checked.append("boards/content-board.json")

    for filename, schema_name in SYSTEM_JSONL_FILES:
        system_path = workspace_dir / "system" / filename
        if system_path.exists():
            if schema_name == "project-warning":
                def record_check(record):
                    check_project_warning_pairing(record)
                    check_creator_scope(record, scope)
            else:
                record_check = scoped
            validate_jsonl_file(schema_name, system_path, record_check=record_check)
            checked.append(str(system_path.relative_to(workspace_dir)))

    warnings, promotion_paths = validate_promotions(workspace_dir, scope=scope)
    checked.extend(promotion_paths)

    return {"workspace_path": workspace_dir, "checked_paths": checked, "warnings": warnings}


def validate_queue(workspace_path):
    workspace_dir = Path(workspace_path)
    queue_dir = workspace_dir / "research" / "idea-queue"
    manifest_path = queue_dir / "queue.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing idea queue manifest: {manifest_path}")

    scope = load_workspace_scope(workspace_dir)

    manifest = load_json(manifest_path)
    validate_record("idea-queue", manifest)
    check_creator_scope(manifest, scope, manifest_path)

    entries_dir = queue_dir / "entries"
    entries = {}
    if entries_dir.exists():
        for entry_path in sorted(entries_dir.glob("*.json")):
            record = load_json(entry_path)
            try:
                validate_record("idea-queue-entry", record)
            except ValidationError as exc:
                raise ValidationError(f"{entry_path}: {exc}") from None
            if record["idea_queue_entry_id"] != entry_path.stem:
                raise ValidationError(
                    f"{entry_path}: filename does not match idea_queue_entry_id "
                    f"{record['idea_queue_entry_id']!r}"
                )
            check_creator_scope(record, scope, entry_path)
            entries[record["idea_queue_entry_id"]] = record

    manifest_refs = {ref["idea_queue_entry_id"]: ref["status"] for ref in manifest["entry_refs"]}
    missing = sorted(set(manifest_refs) - set(entries))
    if missing:
        raise ValidationError(f"Queue manifest names entries with no entry file: {missing}")
    unlisted = sorted(set(entries) - set(manifest_refs))
    if unlisted:
        raise ValidationError(f"Queue entry files missing from the manifest: {unlisted}")
    for entry_id, status in manifest_refs.items():
        if entries[entry_id]["status"] != status:
            raise ValidationError(
                f"Queue manifest status {status!r} does not match entry file status "
                f"{entries[entry_id]['status']!r} for {entry_id}"
            )

    status_counts = manifest.get("status_counts")
    if status_counts is not None:
        actual_counts = {}
        for status in manifest_refs.values():
            actual_counts[status] = actual_counts.get(status, 0) + 1
        for status, count in status_counts.items():
            if actual_counts.get(status, 0) != count:
                raise ValidationError(
                    f"Queue manifest status_counts[{status!r}] is {count}, but "
                    f"{actual_counts.get(status, 0)} entries have that status"
                )
        uncounted = sorted(set(actual_counts) - set(status_counts))
        if uncounted:
            raise ValidationError(
                f"Queue manifest status_counts omit statuses present in the queue: {uncounted}"
            )

    evidence_ids, metric_ids = collect_research_record_ids(workspace_dir)
    video_pack_ids = collect_video_pack_ids(workspace_dir)
    for entry in entries.values():
        for ref in entry["evidence_refs"]:
            if ref["evidence_id"] not in evidence_ids:
                raise ValidationError(
                    f"{entry['idea_queue_entry_id']}: evidence ref {ref['evidence_id']!r} "
                    "does not resolve to any research run evidence record"
                )
            for metric_id in ref.get("metric_snapshot_ids", []):
                if metric_id not in metric_ids:
                    raise ValidationError(
                        f"{entry['idea_queue_entry_id']}: metric snapshot ref {metric_id!r} "
                        "does not resolve to any research run metric snapshot"
                    )
            for pack_id in ref.get("video_understanding_pack_ids", []):
                if pack_id not in video_pack_ids:
                    raise ValidationError(
                        f"{entry['idea_queue_entry_id']}: video understanding pack ref "
                        f"{pack_id!r} does not resolve to a video-understanding-pack record"
                    )

    return {
        "workspace_path": workspace_dir,
        "entry_count": len(entries),
        "manifest_path": manifest_path,
    }


def validate_promotion_gate(workspace_dir, promotion):
    """Enforce the promotion gate (Phase 0C workstream 12 residue).

    A promotion must point to a real idea queue entry. Unresolved evidence
    refs warn for human-approved promotions (the human saw the evidence) and
    fail for any future automated promotion path. Returns warning strings.
    """
    workspace_dir = Path(workspace_dir)
    promotion_id = promotion["idea_promotion_id"]
    entry_id = promotion["idea_queue_entry_id"]
    entry_path = workspace_dir / "research" / "idea-queue" / "entries" / f"{entry_id}.json"
    if not entry_path.exists():
        raise ValidationError(
            f"Idea promotion {promotion_id} does not point to a real idea queue entry: "
            f"research/idea-queue/entries/{entry_id}.json is missing"
        )
    entry = load_json(entry_path)
    try:
        validate_record("idea-queue-entry", entry)
    except ValidationError as exc:
        raise ValidationError(f"{entry_path}: {exc}") from None
    if entry["creator_profile_id"] != promotion["creator_profile_id"]:
        raise ValidationError(
            f"Idea promotion {promotion_id} points to a queue entry owned by a "
            f"different creator: {entry['creator_profile_id']!r} != "
            f"{promotion['creator_profile_id']!r}"
        )
    if not set(promotion["approved_formats"]) & PRODUCTION_SUPPORTED_FORMATS:
        raise ValidationError(
            f"Idea promotion {promotion_id} approves no production-supported "
            f"format ({sorted(promotion['approved_formats'])}); record the "
            "approval intent on the queue entry instead until the format lands"
        )

    evidence_ids, metric_ids = collect_research_record_ids(workspace_dir)
    video_pack_ids = collect_video_pack_ids(workspace_dir)
    unresolved = []
    for ref in promotion["evidence_refs"]:
        if ref["evidence_id"] not in evidence_ids:
            unresolved.append(ref["evidence_id"])
        unresolved.extend(
            metric_id
            for metric_id in ref.get("metric_snapshot_ids", [])
            if metric_id not in metric_ids
        )
        unresolved.extend(
            pack_id
            for pack_id in ref.get("video_understanding_pack_ids", [])
            if pack_id not in video_pack_ids
        )
    if unresolved:
        message = (
            f"idea promotion {promotion_id} has unresolved evidence refs: "
            f"{sorted(set(unresolved))}"
        )
        if promotion["approved_by"] != "user":
            raise ValidationError(message)
        return [f"warning: {message} (human-approved promotion: warning only)"]
    return []


def validate_promotions(workspace_path, scope=None):
    """Validate every promotion record and its gate; returns warning strings."""
    workspace_dir = Path(workspace_path)
    if scope is None:
        scope = load_workspace_scope(workspace_dir)
    promotions_dir = workspace_dir / "research" / "idea-promotions"
    warnings = []
    checked = []
    if promotions_dir.exists():
        for promotion_path in sorted(promotions_dir.glob("*.json")):
            promotion = load_json(promotion_path)
            try:
                validate_record("idea-promotion", promotion)
            except ValidationError as exc:
                raise ValidationError(f"{promotion_path}: {exc}") from None
            if promotion["idea_promotion_id"] != promotion_path.stem:
                raise ValidationError(
                    f"{promotion_path}: filename does not match idea_promotion_id "
                    f"{promotion['idea_promotion_id']!r}"
                )
            check_creator_scope(promotion, scope, promotion_path)
            warnings.extend(validate_promotion_gate(workspace_dir, promotion))
            checked.append(str(promotion_path.relative_to(workspace_dir)))
    return warnings, checked


def collect_research_record_ids(workspace_dir):
    """Scan run JSONL files for evidence and metric snapshot ids (no index yet)."""
    evidence_ids = set()
    metric_ids = set()
    runs_dir = Path(workspace_dir) / "research" / "runs"
    if runs_dir.exists():
        scans = (
            ("evidence.jsonl", "evidence_id", evidence_ids),
            ("metric-snapshots.jsonl", "metric_snapshot_id", metric_ids),
        )
        for filename, id_field, ids in scans:
            for jsonl_path in sorted(runs_dir.glob(f"*/{filename}")):
                for line_number, line in _iter_jsonl_lines(jsonl_path):
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValidationError(
                            f"{jsonl_path}:{line_number}: invalid JSON: {exc}"
                        ) from None
                    if id_field not in record:
                        raise ValidationError(
                            f"{jsonl_path}:{line_number}: record has no {id_field}"
                        )
                    ids.add(record[id_field])
    return evidence_ids, metric_ids


def collect_video_pack_ids(workspace_dir):
    """Video Understanding Pack ids resolve to <pack-id>.json files, either in
    the workspace-level pack directory or inside a run folder."""
    research_dir = Path(workspace_dir) / "research"
    pack_ids = {path.stem for path in research_dir.glob("video-understanding-packs/*.json")}
    pack_ids |= {path.stem for path in research_dir.glob("runs/*/video-understanding-packs/*.json")}
    return pack_ids
