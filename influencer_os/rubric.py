"""Production Rubric and friction-event seams (Improvement OS, ADR 0025).

The rubric is the growing list of binary quality criteria; friction is
captured as rejection/incident events on the existing system-event ledger.
The Rubric Ratchet: every rejection must cite an existing criterion or mint
a new one; unclassified rejections are allowed and counted as a rubric-gap
signal. Verdicts are durable, rejected drafts stay ephemeral.
"""

import datetime
import json
import re
from pathlib import Path

from influencer_os.validation import (
    ROOT,
    ValidationError,
    load_json,
    validate_record,
)

OS_RUBRIC_PATH = ROOT / "context" / "production-rubric.json"
WORKSPACE_RUBRIC_FILENAME = "production-rubric.json"
EVENTS_LEDGER_RELATIVE = Path("system") / "creator-events.jsonl"

EVENT_ID_PATTERN = re.compile(r"^event_[a-zA-Z0-9_-]+$")

# Reflection runs (ADR 0025): declare-then-attest for reflection itself. A
# run under system/reflection-runs/ lists exactly the ledger events it
# processed; an event is unprocessed until a claiming run lists it. Failed
# runs claim nothing, so a crashed reflection never consumes the watermark.
REFLECTION_RUNS_DIR_RELATIVE = Path("system") / "reflection-runs"
REFLECTION_JOB_TYPE = "reflection"
CLAIMING_RUN_STATUSES = frozenset({"completed", "completed_no_material_update"})

# Trigger defaults (D3): workspace-tunable via reflection_thresholds on
# creator-workspace.json; the keys are drift-pinned to the schema.
DEFAULT_REFLECTION_THRESHOLDS = {
    "recurrence_k": 3,
    "unprocessed_n": 10,
    "unclassified_n": 3,
}


def load_rubric(path):
    path = Path(path)
    rubric = load_json(path)
    try:
        validate_record("production-rubric", rubric)
    except ValidationError as exc:
        raise ValidationError(f"{path}: {exc}") from None
    # blocking_adr must resolve to a real ADR file (batch-1 review, Medium):
    # the pairing rule alone would let a hand-edited rubric block on a
    # nonexistent decision. Filesystem resolution lives here at the load
    # seam; record semantics stay filesystem-free.
    for criterion in rubric.get("criteria", []):
        adr_ref = criterion.get("blocking_adr")
        if adr_ref is not None and not (ROOT / adr_ref).is_file():
            raise ValidationError(
                f"{path}: criterion {criterion['criterion_id']!r} cites "
                f"blocking_adr {adr_ref!r} which does not resolve to a file"
            )
    return rubric


def collect_criteria(workspace_dir, os_rubric_path=OS_RUBRIC_PATH, scope=None):
    """Union of OS-scope and creator-scope criteria, keyed by criterion_id.

    A duplicate id across the two files fails closed: criterion ids double as
    recurrence keys, so an ambiguous id would make violation counting and
    resolution ambiguous.
    """
    workspace_dir = Path(workspace_dir)
    criteria = {}
    sources = (
        (Path(os_rubric_path), "os"),
        (workspace_dir / WORKSPACE_RUBRIC_FILENAME, "creator"),
    )
    for path, expected_scope in sources:
        if not path.exists():
            continue
        rubric = load_rubric(path)
        if not rubric:
            continue
        if rubric["scope"] != expected_scope:
            raise ValidationError(
                f"{path}: rubric scope {rubric['scope']!r} does not match its "
                f"location (expected {expected_scope!r})"
            )
        if expected_scope == "creator" and scope is not None:
            for field in ("creator_profile_id", "creator_slug"):
                if rubric.get(field) != scope[field]:
                    raise ValidationError(
                        f"{path}: {field} {rubric.get(field)!r} does not match "
                        f"the owning creator workspace ({scope[field]!r})"
                    )
        for criterion in rubric["criteria"]:
            criterion_id = criterion["criterion_id"]
            if criterion_id in criteria:
                raise ValidationError(
                    f"{path}: duplicate criterion id {criterion_id!r} across "
                    "rubric scopes; criterion ids are recurrence keys and must "
                    "be unique across the OS and creator rubrics"
                )
            criteria[criterion_id] = criterion
    return criteria


def check_event_resolution(record, criteria_by_id, context=None):
    """A friction event citing a criterion must cite a live one (the Rubric
    Ratchet at rest). Structural rules (rejection requires recurrence_key and
    exactly one of criterion_id / unclassified) live in the schema semantics;
    this is the resolution half, which needs the collected rubric."""
    criterion_id = record.get("criterion_id")
    if criterion_id is None:
        return
    prefix = f"{context}: " if context else ""
    criterion = criteria_by_id.get(criterion_id)
    if criterion is None:
        raise ValidationError(
            f"{prefix}event {record.get('event_id')!r} cites unknown rubric "
            f"criterion {criterion_id!r}; cite an existing criterion or mint "
            "one first (cite-or-mint, ADR 0025)"
        )
    if criterion["status"] == "retired":
        raise ValidationError(
            f"{prefix}event {record.get('event_id')!r} cites retired rubric "
            f"criterion {criterion_id!r}; retired criteria cannot be cited"
        )


def load_reflection_runs(workspace_dir, scope=None):
    """Load and validate every reflection run: schema-valid, filename == id,
    job_type 'reflection', and creator-scoped to the owning workspace."""
    workspace_dir = Path(workspace_dir)
    runs_dir = workspace_dir / REFLECTION_RUNS_DIR_RELATIVE
    runs = []
    if not runs_dir.exists():
        return runs
    for path in sorted(runs_dir.glob("*.json")):
        run = load_json(path)
        try:
            validate_record("automation-run", run)
        except ValidationError as exc:
            raise ValidationError(f"{path}: {exc}") from None
        if run["automation_run_id"] != path.stem:
            raise ValidationError(
                f"{path}: filename must match automation_run_id "
                f"({run['automation_run_id']!r})"
            )
        if run["job_type"] != REFLECTION_JOB_TYPE:
            raise ValidationError(
                f"{path}: runs under {REFLECTION_RUNS_DIR_RELATIVE} must have "
                f"job_type {REFLECTION_JOB_TYPE!r}, got {run['job_type']!r}"
            )
        if scope is not None and run["creator_profile_id"] != scope["creator_profile_id"]:
            raise ValidationError(
                f"{path}: creator_profile_id {run['creator_profile_id']!r} does "
                f"not match the owning creator workspace "
                f"({scope['creator_profile_id']!r})"
            )
        runs.append(run)
    return runs


def reconcile_reflection_runs(runs, ledger_event_ids, context=None):
    """Both-direction watermark reconciliation, fail-closed: a claiming run
    may not list a nonexistent event, and no event is claimed twice. Returns
    the set of claimed (processed) event ids."""
    prefix = f"{context}: " if context else ""
    claimed = {}
    for run in runs:
        if run["run_status"] not in CLAIMING_RUN_STATUSES:
            # Declare-then-attest (batch-1 review, High): a crashed run
            # records last_error, never partial claims — otherwise its
            # event_ids escape both the dangling and double-claim checks.
            if run["event_ids"]:
                raise ValidationError(
                    f"{prefix}reflection run {run['automation_run_id']} is "
                    f"{run['run_status']} but attests event_ids; a non-claiming "
                    "run must attest event_ids: []"
                )
            continue
        run_id = run["automation_run_id"]
        for event_id in run["event_ids"]:
            if event_id not in ledger_event_ids:
                raise ValidationError(
                    f"{prefix}reflection run {run_id} claims event "
                    f"{event_id!r} which does not exist on the ledger"
                )
            if event_id in claimed:
                raise ValidationError(
                    f"{prefix}event {event_id!r} is claimed by both "
                    f"{claimed[event_id]} and {run_id}; an event is processed "
                    "at most once"
                )
            claimed[event_id] = run_id
    return set(claimed)


def resolve_reflection_thresholds(manifest):
    thresholds = dict(DEFAULT_REFLECTION_THRESHOLDS)
    thresholds.update(manifest.get("reflection_thresholds") or {})
    return thresholds


def reflection_report(workspace_path, scope=None):
    """Compute the event-driven reflection trigger (ADR 0025): unprocessed
    friction counts, per-recurrence-key counts, the unclassified rubric-gap
    signal, and the advisory warnings for crossed thresholds. Validates the
    ledger and runs first (fail-closed), then reports; never mutates."""
    from influencer_os.research import load_workspace_scope, validate_events_ledger

    workspace_dir = Path(workspace_path)
    if scope is None:
        scope = load_workspace_scope(workspace_dir)
    validate_events_ledger(workspace_dir, scope)

    ledger_path = workspace_dir / EVENTS_LEDGER_RELATIVE
    records = []
    if ledger_path.exists():
        for line in ledger_path.read_text().split("\n"):
            if line.strip():
                records.append(json.loads(line))
    runs = load_reflection_runs(workspace_dir, scope=scope)
    claimed = reconcile_reflection_runs(runs, {r["event_id"] for r in records})

    friction_types = ("rejection", "incident")
    unprocessed = [
        record
        for record in records
        if record.get("event_type") in friction_types
        and record["event_id"] not in claimed
    ]
    recurrence_counts = {}
    for record in unprocessed:
        key = record["recurrence_key"]
        recurrence_counts[key] = recurrence_counts.get(key, 0) + 1
    unclassified_count = sum(1 for r in unprocessed if r.get("unclassified"))

    manifest = load_json(workspace_dir / "creator-workspace.json")
    thresholds = resolve_reflection_thresholds(manifest)

    warnings = []
    for key, count in sorted(recurrence_counts.items()):
        if count >= thresholds["recurrence_k"]:
            warnings.append(
                f"warning: reflection due — recurrence key '{key}' has {count} "
                f"unprocessed friction events (threshold "
                f"{thresholds['recurrence_k']}); run distill-production-learning"
            )
    if len(unprocessed) >= thresholds["unprocessed_n"]:
        warnings.append(
            f"warning: reflection due — {len(unprocessed)} unprocessed friction "
            f"events (threshold {thresholds['unprocessed_n']}); run "
            "distill-production-learning"
        )
    if unclassified_count >= thresholds["unclassified_n"]:
        warnings.append(
            f"warning: rubric gap — {unclassified_count} unprocessed "
            f"unclassified rejections (threshold {thresholds['unclassified_n']}); "
            "the rubric is missing criteria for taste that keeps recurring"
        )

    return {
        "unprocessed_count": len(unprocessed),
        "recurrence_counts": recurrence_counts,
        "unclassified_count": unclassified_count,
        "claimed_count": len(claimed),
        "run_count": len(runs),
        "thresholds": thresholds,
        "warnings": warnings,
    }


def _slug_token(creator_slug):
    return creator_slug.replace("-", "_")


def _next_event_id(creator_slug, existing_ids):
    prefix = f"event_{_slug_token(creator_slug)}_"
    highest = 0
    for event_id in existing_ids:
        if event_id.startswith(prefix):
            suffix = event_id[len(prefix):]
            if suffix.isdigit():
                highest = max(highest, int(suffix))
    return f"{prefix}{highest + 1:03d}"


def _read_ledger_event_ids(ledger_path):
    if not ledger_path.exists():
        return []
    event_ids = []
    for line_number, line in enumerate(ledger_path.read_text().split("\n"), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValidationError(
                f"{ledger_path}:{line_number}: invalid JSON: {exc}"
            ) from None
        if isinstance(record, dict) and record.get("event_id"):
            event_ids.append(record["event_id"])
    return event_ids


def log_incident(
    workspace_path,
    *,
    event_type,
    recurrence_key,
    message,
    source_id,
    criterion_id=None,
    unclassified=False,
    iteration_count=None,
    project_id=None,
    severity="important",
    source_type="skill",
    occurred_on=None,
    event_id=None,
):
    """Append one validated friction event to the creator-events ledger.

    Writer and at-rest sweep share the same checks: schema + structural
    semantics via validate_record, resolution via the collected rubric, and
    creator scope via the workspace manifest.
    """
    from influencer_os.research import check_creator_scope, load_workspace_scope

    workspace_dir = Path(workspace_path)
    scope = load_workspace_scope(workspace_dir)
    ledger_path = workspace_dir / EVENTS_LEDGER_RELATIVE
    existing_ids = _read_ledger_event_ids(ledger_path)

    if event_id is None:
        event_id = _next_event_id(scope["creator_slug"], existing_ids)
    if event_id in existing_ids:
        raise ValidationError(f"duplicate event id {event_id!r} in {ledger_path}")
    if occurred_on is None:
        occurred_on = datetime.datetime.now().isoformat(timespec="seconds")

    record = {
        "event_id": event_id,
        "occurred_on": occurred_on,
        "event_type": event_type,
        "severity": severity,
        "message": message,
        "source_type": source_type,
        "source_id": source_id,
        "creator_profile_id": scope["creator_profile_id"],
        "creator_slug": scope["creator_slug"],
        "recurrence_key": recurrence_key,
    }
    if criterion_id is not None:
        record["criterion_id"] = criterion_id
    if unclassified:
        record["unclassified"] = True
    if iteration_count is not None:
        record["iteration_count"] = iteration_count
    if project_id is not None:
        record["project_id"] = project_id

    validate_record("system-event", record)
    check_creator_scope(record, scope)
    check_event_resolution(record, collect_criteria(workspace_dir, scope=scope))

    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a") as handle:
        handle.write(json.dumps(record, allow_nan=False) + "\n")
    return {"event_id": event_id, "ledger_path": str(ledger_path)}


def mint_criterion(
    workspace_path,
    *,
    criterion_id,
    statement,
    os_scope=False,
    origin="rejection",
    category=None,
    minted_from_event_id=None,
    minted_on=None,
    notes=None,
):
    """Add one minted criterion to the OS or creator rubric.

    The duplicate check spans both scopes: criterion ids are recurrence keys
    and must stay unique across the OS and creator rubrics.
    """
    workspace_dir = Path(workspace_path)
    existing = collect_criteria(workspace_dir)
    if criterion_id in existing:
        raise ValidationError(
            f"criterion id {criterion_id!r} already exists; criterion ids must "
            "be unique across the OS and creator rubrics"
        )

    rubric_path = OS_RUBRIC_PATH if os_scope else workspace_dir / WORKSPACE_RUBRIC_FILENAME
    if not rubric_path.exists():
        raise FileNotFoundError(f"Missing rubric file: {rubric_path}")
    rubric = load_rubric(rubric_path)

    criterion = {
        "criterion_id": criterion_id,
        "statement": statement,
        "status": "minted",
        "origin": origin,
        "minted_on": minted_on or datetime.date.today().isoformat(),
    }
    if category is not None:
        criterion["quality_review_category"] = category
    if minted_from_event_id is not None:
        criterion["minted_from_event_id"] = minted_from_event_id
    if notes is not None:
        criterion["notes"] = notes

    rubric["criteria"].append(criterion)
    validate_record("production-rubric", rubric)
    rubric_path.write_text(json.dumps(rubric, indent=2, allow_nan=False) + "\n")
    return {"criterion_id": criterion_id, "rubric_path": str(rubric_path)}
