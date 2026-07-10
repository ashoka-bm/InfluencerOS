"""Research retention pruning (ADR 0020 workflow retention rules, slice 4
batch D).

Prune removes unpromoted, unreferenced evidence past the retention window
(default 30 days) and the metric snapshots that belong to it. Anything a
opportunity, concept, approval, or project references is preserved — the
Product Invariant's provenance chain always survives. Stale queue entries
are never touched (staleness stays auditable). Removals are recorded on the
run manifest as ``pruned_evidence_ids``/``pruned_metric_snapshot_ids`` so
the original ``outputs`` declaration stays intact and outputs reconciliation
stays exact. Dry-run by default; only ``apply=True`` deletes.
"""
import datetime
import json
from pathlib import Path

from influencer_os.creator_scope import load_workspace_scope
from influencer_os.json_io import write_json_atomic
from influencer_os.research import validate_research
from influencer_os.validation import (
    ValidationError,
    iter_jsonl_lines,
    load_json,
    validate_record,
)


DEFAULT_RETENTION_DAYS = 30


def _load_validated(path, schema_name):
    record = load_json(path)
    try:
        validate_record(schema_name, record)
    except ValidationError as exc:
        raise ValidationError(f"{path}: {exc}") from None
    return record


def _record_date(value, context):
    try:
        return datetime.date.fromisoformat(value[:10])
    except ValueError:
        raise ValidationError(f"{context}: {value!r} has no parseable date") from None


def collect_protected_ids(workspace_dir):
    """Evidence and metric-snapshot ids referenced by any content
    opportunity, campaign concept, concept approval, or project.
    Referenced records are never prunable."""
    workspace_dir = Path(workspace_dir)
    research_dir = workspace_dir / "research"
    protected_evidence = set()
    protected_metrics = set()

    ref_scans = (
        (research_dir / "content-opportunity-queue" / "entries",
         "content-opportunity"),
    )
    for directory, schema_name in ref_scans:
        if not directory.exists():
            continue
        for record_path in sorted(directory.glob("*.json")):
            record = _load_validated(record_path, schema_name)
            for ref in record["evidence_refs"]:
                protected_evidence.add(ref["evidence_id"])
                protected_metrics.update(ref.get("metric_snapshot_ids", []))

    campaign_scans = (
        ("campaigns/*/concepts/*.json", "campaign-concept"),
        ("campaigns/*/approvals/*.json", "concept-approval"),
    )
    for pattern, schema_name in campaign_scans:
        for record_path in sorted(workspace_dir.glob(pattern)):
            record = _load_validated(record_path, schema_name)
            for ref in record["evidence_refs"]:
                protected_evidence.add(ref["evidence_id"])
                protected_metrics.update(ref.get("metric_snapshot_ids", []))

    projects_dir = workspace_dir / "projects"
    if projects_dir.exists():
        for manifest_path in sorted(projects_dir.glob("*/project.json")):
            record = _load_validated(manifest_path, "project")
            source_refs = record["source_refs"]
            protected_evidence.update(source_refs.get("research_evidence_ids", []))
            protected_metrics.update(source_refs.get("metric_snapshot_ids", []))

    return protected_evidence, protected_metrics


def _load_jsonl_records(path, schema_name):
    """Return (line_number, raw_line, record) triples, schema-validated."""
    entries = []
    for line_number, line in iter_jsonl_lines(path):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"{path}:{line_number}: invalid JSON: {exc}") from None
        try:
            validate_record(schema_name, record)
        except ValidationError as exc:
            raise ValidationError(f"{path}:{line_number}: {exc}") from None
        entries.append((line_number, line, record))
    return entries


def prune_research(workspace_path, retention_days=DEFAULT_RETENTION_DAYS,
                   apply=False, as_of=None):
    """Apply the workflow retention rules to one Creator Workspace.

    Evidence is prunable when it is older than the retention window, its id
    is unreferenced, and every metric snapshot pointing at it is
    unreferenced; its snapshots prune with it. Dry-run unless ``apply``.
    """
    workspace_dir = Path(workspace_path)
    load_workspace_scope(workspace_dir)
    if as_of is None:
        as_of = datetime.date.today()
    elif isinstance(as_of, str):
        as_of = datetime.date.fromisoformat(as_of)
    cutoff = as_of - datetime.timedelta(days=retention_days)

    protected_evidence, protected_metrics = collect_protected_ids(workspace_dir)

    runs = []
    runs_dir = workspace_dir / "research" / "runs"
    if runs_dir.exists():
        for run_dir in sorted(path for path in runs_dir.iterdir() if path.is_dir()):
            evidence_path = run_dir / "evidence.jsonl"
            metrics_path = run_dir / "metric-snapshots.jsonl"
            evidence_entries = (
                _load_jsonl_records(evidence_path, "research-evidence")
                if evidence_path.exists() else []
            )
            metric_entries = (
                _load_jsonl_records(metrics_path, "metric-snapshot")
                if metrics_path.exists() else []
            )

            metrics_by_evidence = {}
            for _line, _raw, record in metric_entries:
                metrics_by_evidence.setdefault(record["evidence_id"], []).append(record)

            prunable_evidence = set()
            for _line, _raw, record in evidence_entries:
                evidence_id = record["evidence_id"]
                if evidence_id in protected_evidence:
                    continue
                captured = _record_date(
                    record["captured_on"], f"{evidence_path} {evidence_id}"
                )
                if captured >= cutoff:
                    continue
                snapshots = metrics_by_evidence.get(evidence_id, [])
                if any(
                    snapshot["metric_snapshot_id"] in protected_metrics
                    for snapshot in snapshots
                ):
                    continue
                prunable_evidence.add(evidence_id)

            prunable_metrics = {
                record["metric_snapshot_id"]
                for _line, _raw, record in metric_entries
                if record["evidence_id"] in prunable_evidence
            }
            if not prunable_evidence:
                continue

            runs.append({
                "run_dir": run_dir,
                "research_run_id": run_dir.name,
                "pruned_evidence_ids": sorted(prunable_evidence),
                "pruned_metric_snapshot_ids": sorted(prunable_metrics),
                "evidence_entries": evidence_entries,
                "metric_entries": metric_entries,
            })

    if apply:
        # Pre-flight: refuse to mutate an already-invalid workspace. Without
        # this, a pre-existing inconsistency surfaces mid-apply and reads as
        # if the prune corrupted the workspace.
        try:
            validate_research(workspace_dir)
        except (ValidationError, FileNotFoundError) as exc:
            raise ValidationError(
                "prune --apply refused: the workspace fails validate research "
                f"before any change ({exc}); fix the workspace first"
            ) from exc
        for run in runs:
            evidence_ids = set(run["pruned_evidence_ids"])
            metric_ids = set(run["pruned_metric_snapshot_ids"])
            _rewrite_jsonl(
                run["run_dir"] / "evidence.jsonl",
                run["evidence_entries"], "evidence_id", evidence_ids,
            )
            if metric_ids:
                _rewrite_jsonl(
                    run["run_dir"] / "metric-snapshots.jsonl",
                    run["metric_entries"], "metric_snapshot_id", metric_ids,
                )
            _record_pruned_ids(run["run_dir"], evidence_ids, metric_ids)
        # The pruned workspace must still validate; a failure here is a bug.
        validate_research(workspace_dir)

    return {
        "workspace_path": workspace_dir,
        "applied": apply,
        "as_of": as_of.isoformat(),
        "cutoff": cutoff.isoformat(),
        "retention_days": retention_days,
        "runs": [
            {
                "research_run_id": run["research_run_id"],
                "pruned_evidence_ids": run["pruned_evidence_ids"],
                "pruned_metric_snapshot_ids": run["pruned_metric_snapshot_ids"],
            }
            for run in runs
        ],
        "evidence_pruned": sum(len(run["pruned_evidence_ids"]) for run in runs),
        "metric_snapshots_pruned": sum(
            len(run["pruned_metric_snapshot_ids"]) for run in runs
        ),
    }


def _rewrite_jsonl(path, entries, id_field, pruned_ids):
    """Rewrite a JSONL file keeping the original raw text of kept lines."""
    kept = [raw for _line, raw, record in entries if record[id_field] not in pruned_ids]
    path.write_text("".join(raw + "\n" for raw in kept))


def _record_pruned_ids(run_dir, evidence_ids, metric_ids):
    manifest_path = run_dir / "research-run.json"
    manifest = _load_validated(manifest_path, "research-run")
    manifest["pruned_evidence_ids"] = sorted(
        set(manifest.get("pruned_evidence_ids", [])) | evidence_ids
    )
    if metric_ids or manifest.get("pruned_metric_snapshot_ids"):
        manifest["pruned_metric_snapshot_ids"] = sorted(
            set(manifest.get("pruned_metric_snapshot_ids", [])) | metric_ids
        )
    try:
        validate_record("research-run", manifest)
    except ValidationError as exc:
        raise ValidationError(f"pruned run manifest is invalid: {exc}") from None
    write_json_atomic(manifest_path, manifest)
