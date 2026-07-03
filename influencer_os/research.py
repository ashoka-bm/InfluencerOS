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


def validate_jsonl_file(schema_name, path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Missing JSONL file: {path}")
    records = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"{path}:{line_number}: invalid JSON: {exc}") from None
        try:
            validate_record(schema_name, record)
        except ValidationError as exc:
            raise ValidationError(f"{path}:{line_number}: {exc}") from None
        records.append(record)
    return records


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

    checked = []

    schedule_path = workspace_dir / "content-schedule.json"
    if schedule_path.exists():
        validate_file("creator-content-schedule", schedule_path)
        checked.append("content-schedule.json")

    findings_path = research_dir / "findings.md"
    if findings_path.exists():
        validate_findings_file(findings_path)
        checked.append("research/findings.md")

    stable_dir = research_dir / "stable-findings"
    if stable_dir.exists():
        for stable_path in sorted(stable_dir.glob("*.md")):
            validate_stable_finding_file(stable_path)
            checked.append(str(stable_path.relative_to(workspace_dir)))

    runs_dir = research_dir / "runs"
    if runs_dir.exists():
        for run_dir in sorted(path for path in runs_dir.iterdir() if path.is_dir()):
            run_manifest = run_dir / "research-run.json"
            if not run_manifest.exists():
                raise ValidationError(f"Research run folder has no research-run.json: {run_dir}")
            validate_file("research-run", run_manifest)
            checked.append(str(run_manifest.relative_to(workspace_dir)))
            for filename, schema_name in RESEARCH_JSONL_FILES:
                jsonl_path = run_dir / filename
                if jsonl_path.exists():
                    validate_jsonl_file(schema_name, jsonl_path)
                    checked.append(str(jsonl_path.relative_to(workspace_dir)))

    for filename, schema_name in RESEARCH_INTELLIGENCE_FILES.items():
        intel_path = research_dir / "intelligence" / filename
        if intel_path.exists():
            validate_file(schema_name, intel_path)
            checked.append(str(intel_path.relative_to(workspace_dir)))

    board_path = workspace_dir / "boards" / "content-board.json"
    if board_path.exists():
        validate_file("content-board", board_path)
        checked.append("boards/content-board.json")

    for filename, schema_name in SYSTEM_JSONL_FILES:
        system_path = workspace_dir / "system" / filename
        if system_path.exists():
            validate_jsonl_file(schema_name, system_path)
            checked.append(str(system_path.relative_to(workspace_dir)))

    return {"workspace_path": workspace_dir, "checked_paths": checked}


def validate_queue(workspace_path):
    workspace_dir = Path(workspace_path)
    queue_dir = workspace_dir / "research" / "idea-queue"
    manifest_path = queue_dir / "queue.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing idea queue manifest: {manifest_path}")

    manifest = load_json(manifest_path)
    validate_record("idea-queue", manifest)

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

    evidence_ids, metric_ids = collect_research_record_ids(workspace_dir)
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

    return {
        "workspace_path": workspace_dir,
        "entry_count": len(entries),
        "manifest_path": manifest_path,
    }


def collect_research_record_ids(workspace_dir):
    """Scan run JSONL files for evidence and metric snapshot ids (no index yet)."""
    evidence_ids = set()
    metric_ids = set()
    runs_dir = Path(workspace_dir) / "research" / "runs"
    if runs_dir.exists():
        for jsonl_path in runs_dir.glob("*/evidence.jsonl"):
            for line in jsonl_path.read_text().splitlines():
                if line.strip():
                    evidence_ids.add(json.loads(line).get("evidence_id"))
        for jsonl_path in runs_dir.glob("*/metric-snapshots.jsonl"):
            for line in jsonl_path.read_text().splitlines():
                if line.strip():
                    metric_ids.add(json.loads(line).get("metric_snapshot_id"))
    return evidence_ids, metric_ids
