"""Seed-based deterministic record constructors (ADR 0042).

Skills author seeds — only genuinely authored fields — and these
constructors assemble, validate, and write the full canonical records.
The field classes (authored / derived / copied / stamped) per record type
are specified in docs/record-constructors.md. A seed that supplies a
derived or copied field fails closed rather than being silently
overwritten.

In-flight research runs are a staged workspace area: `scaffold
search-plan` creates `system/staging/research-runs/<research_run_id>/`
holding the search plan, the connector budget, and accumulating fetch
results and evidence ledgers. `complete-run` derives the run record from
the plan and the accumulated ledgers, validates the whole folder, and
moves it into canonical `research/runs/` — so at-rest validation's
invariant (every canonical run folder is complete and valid) never sees a
half-finished run.
"""

import datetime
import re
import shutil
import tempfile
from pathlib import Path

from influencer_os.json_io import write_json_atomic
from influencer_os.projects import init_project
from influencer_os.validation import (
    ValidationError,
    load_json,
    validate_record,
    validate_jsonl_file,
    validate_research_search_plan_semantics,
)

STAGING_DIR = Path("system") / "staging"
STAGED_RUNS_DIR = STAGING_DIR / "research-runs"

SCAFFOLD_TYPES = {
    "project": (
        "Project manifest + folder from a seed and its locked idea "
        "promotion (subsumes init-project)"
    ),
    "search-plan": (
        "ResearchSearchPlan + staged in-flight run directory under "
        "system/staging/research-runs/ (complete-run moves it canonical)"
    ),
}

PROJECT_SEED_REQUIRED = (
    "project_slug",
    "content_unit_type",
    "platform_targets",
    "learning_goal",
    "acceptance_criteria",
    "idea_promotion_id",
)
PROJECT_SEED_OPTIONAL = (
    "constraints",
    "dependencies",
    "notes",
    "reference_asset_ids",
    "target_formats",
    "project_id",
)

SEARCH_PLAN_SEED_REQUIRED = (
    "mode",
    "scope",
    "platforms",
    "decision_basis",
    "adapters_considered",
    "planned_queries",
)
SEARCH_PLAN_SEED_OPTIONAL = (
    "schedule_slot_ids",
    "planned_sources",
    "skipped_sources",
    "approval_gates",
    "future_connector_notes",
    "research_run_id",
)


def load_seed(seed):
    """Accept a seed as a dict or a path to a JSON file."""
    if isinstance(seed, (str, Path)):
        return load_json(seed)
    return dict(seed)


def check_seed_fields(seed, required, optional, record_label):
    allowed = set(required) | set(optional)
    unknown = sorted(set(seed) - allowed)
    if unknown:
        raise ValidationError(
            f"{record_label} seed carries non-seed fields {unknown}; seeds "
            "hold only authored fields — derived and copied fields are "
            "constructor-owned (docs/record-constructors.md)"
        )
    missing = sorted(field for field in required if field not in seed)
    if missing:
        raise ValidationError(
            f"{record_label} seed is missing authored fields {missing}"
        )


def load_workspace_manifest(creator_workspace):
    manifest_path = Path(creator_workspace) / "creator-workspace.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Missing creator workspace manifest: {manifest_path}"
        )
    manifest = load_json(manifest_path)
    validate_record("creator-workspace", manifest)
    return manifest


def creator_id_suffix(creator_profile_id):
    return creator_profile_id.removeprefix("creator_")


def id_token(text):
    token = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    if not token:
        raise ValidationError(f"cannot derive an id token from {text!r}")
    return token


def next_sequenced_id(prefix, existing_ids):
    """`<prefix>_NNN` with the next free zero-padded sequence."""
    pattern = re.compile(re.escape(prefix) + r"_(\d+)$")
    top = 0
    for existing in existing_ids:
        match = pattern.match(existing)
        if match:
            top = max(top, int(match.group(1)))
    return f"{prefix}_{top + 1:03d}"


def _now(now):
    return now if now is not None else datetime.datetime.now()


def _iso_seconds(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:%S")


# --- project ---------------------------------------------------------------


def project_paths_block(project_slug):
    """The constant per-project layout block (only root varies, by slug)."""
    return {
        "root": f"projects/{project_slug}/",
        "plan": "plan/",
        "reviews": "reviews/",
        "generation": "generation/",
        "output_package": "output-package/",
        "published": "published/",
        "analytics": "analytics/",
        "performance_summary": "performance-summary.json",
        "evidence_brief": "evidence-brief.md",
    }


def _copied_promotion_refs(promotion):
    """source_refs cached from the locked promotion — machine-copied so the
    PROMOTION_CACHED_SUBSETS consistency checks hold by construction."""
    refs = {"idea_queue_entry_id": promotion["idea_queue_entry_id"]}
    if promotion.get("research_finding_ids"):
        refs["research_finding_ids"] = list(promotion["research_finding_ids"])
    evidence_ids = []
    metric_ids = []
    pack_ids = []
    for evidence_ref in promotion["evidence_refs"]:
        if evidence_ref["evidence_id"] not in evidence_ids:
            evidence_ids.append(evidence_ref["evidence_id"])
        for metric_id in evidence_ref.get("metric_snapshot_ids", []):
            if metric_id not in metric_ids:
                metric_ids.append(metric_id)
        for pack_id in evidence_ref.get("video_understanding_pack_ids", []):
            if pack_id not in pack_ids:
                pack_ids.append(pack_id)
    if evidence_ids:
        refs["research_evidence_ids"] = evidence_ids
    if metric_ids:
        refs["metric_snapshot_ids"] = metric_ids
    if pack_ids:
        refs["video_understanding_pack_ids"] = pack_ids
    return refs


def build_project_manifest(seed, *, creator_profile_id, promotion,
                           project_id, today):
    """Assemble a full project manifest from authored seed fields, derived
    defaults, and fields copied from the locked promotion."""
    check_seed_fields(
        seed, PROJECT_SEED_REQUIRED, PROJECT_SEED_OPTIONAL, "project"
    )
    if seed["idea_promotion_id"] != promotion["idea_promotion_id"]:
        raise ValidationError(
            f"project seed names promotion {seed['idea_promotion_id']!r} but "
            f"was built against {promotion['idea_promotion_id']!r}"
        )
    source_refs = {
        "idea_promotion_id": promotion["idea_promotion_id"],
        "reference_asset_ids": list(seed.get("reference_asset_ids", [])),
        "evidence_brief_path": "evidence-brief.md",
    }
    source_refs.update(_copied_promotion_refs(promotion))
    project = {
        "project_id": project_id,
        "creator_profile_id": creator_profile_id,
        "project_slug": seed["project_slug"],
        "created_on": today,
        "status": "created",
        "content_unit_type": seed["content_unit_type"],
        "source_refs": source_refs,
        "project_paths": project_paths_block(seed["project_slug"]),
        "target_formats": list(
            seed.get("target_formats", [f"format_{seed['content_unit_type']}"])
        ),
        "platform_targets": list(seed["platform_targets"]),
        "learning_goal": seed["learning_goal"],
        "acceptance_criteria": list(seed["acceptance_criteria"]),
    }
    for optional_field in ("constraints", "dependencies", "notes"):
        if optional_field in seed:
            project[optional_field] = seed[optional_field]
    validate_record("project", project)
    return project


def create_project_from_manifest(project, creator_workspace):
    """Run the canonical project constructor (gate, folders, scaffolds,
    advisory) on an in-memory manifest."""
    with tempfile.TemporaryDirectory() as temp_dir:
        manifest_path = Path(temp_dir) / "project.json"
        write_json_atomic(manifest_path, project)
        return init_project(manifest_path, creator_workspace)


def _load_promotion(workspace_dir, promotion_id):
    promotion_path = (
        Path(workspace_dir) / "research" / "idea-promotions"
        / f"{promotion_id}.json"
    )
    if not promotion_path.exists():
        raise ValidationError(
            f"idea_promotion_id {promotion_id!r} resolves to no promotion: "
            f"{promotion_path}"
        )
    promotion = load_json(promotion_path)
    validate_record("idea-promotion", promotion)
    return promotion


def _unclaimed_promotion_project_id(workspace_dir, promotion):
    from influencer_os.research import collect_project_manifests

    existing = collect_project_manifests(workspace_dir)
    unclaimed = [
        project_id
        for project_id in promotion["project_ids_created"]
        if project_id not in existing
    ]
    if len(unclaimed) == 1:
        return unclaimed[0]
    promotion_id = promotion["idea_promotion_id"]
    if not unclaimed:
        raise ValidationError(
            f"promotion {promotion_id} lists no unclaimed project id; a new "
            "project needs a new promotion package (stage promotion), since "
            "the locked promotion pre-lists every project it creates"
        )
    raise ValidationError(
        f"promotion {promotion_id} has several unclaimed project ids "
        f"{unclaimed}; pin one via the seed's project_id"
    )


def scaffold_project(seed, creator_workspace, now=None):
    """Build and create one project from a seed against its locked
    promotion. The project id comes from a seed pin or the promotion's
    single unclaimed pre-listed id."""
    workspace_dir = Path(creator_workspace)
    seed = load_seed(seed)
    check_seed_fields(
        seed, PROJECT_SEED_REQUIRED, PROJECT_SEED_OPTIONAL, "project"
    )
    workspace_manifest = load_workspace_manifest(workspace_dir)
    promotion = _load_promotion(workspace_dir, seed["idea_promotion_id"])
    project_id = seed.get("project_id") or _unclaimed_promotion_project_id(
        workspace_dir, promotion
    )
    project = build_project_manifest(
        seed,
        creator_profile_id=workspace_manifest["creator_profile_id"],
        promotion=promotion,
        project_id=project_id,
        today=_now(now).strftime("%Y-%m-%d"),
    )
    project_dir = create_project_from_manifest(project, workspace_dir)
    return {"project_dir": project_dir, "project_id": project_id}


# --- search plan / research run pair ---------------------------------------


def staged_run_dir(creator_workspace, research_run_id):
    return Path(creator_workspace) / STAGED_RUNS_DIR / research_run_id


def _existing_run_ids(workspace_dir):
    run_ids = set()
    for runs_root in (
        workspace_dir / "research" / "runs",
        workspace_dir / STAGED_RUNS_DIR,
    ):
        if runs_root.exists():
            run_ids.update(
                path.name for path in runs_root.iterdir() if path.is_dir()
            )
    return run_ids


def scaffold_search_plan(seed, creator_workspace, now=None):
    """Write a validated search plan into a staged in-flight run directory.
    The run id is allocated here so the plan and the eventual run record
    share it by construction."""
    workspace_dir = Path(creator_workspace)
    seed = load_seed(seed)
    check_seed_fields(
        seed, SEARCH_PLAN_SEED_REQUIRED, SEARCH_PLAN_SEED_OPTIONAL,
        "search-plan",
    )
    workspace_manifest = load_workspace_manifest(workspace_dir)
    creator_profile_id = workspace_manifest["creator_profile_id"]
    moment = _now(now)
    run_id = seed.get("research_run_id")
    if run_id is None:
        prefix = (
            f"research_run_{creator_id_suffix(creator_profile_id)}"
            f"_{moment.strftime('%Y_%m_%d')}"
        )
        run_id = next_sequenced_id(prefix, _existing_run_ids(workspace_dir))
    elif run_id in _existing_run_ids(workspace_dir):
        raise ValidationError(f"research run id already exists: {run_id}")

    schedule_slot_ids = list(seed.get("schedule_slot_ids", []))
    if schedule_slot_ids:
        schedule_path = workspace_dir / "content-schedule.json"
        if not schedule_path.exists():
            raise ValidationError(
                "seed names schedule slots but the workspace has no "
                "content-schedule.json"
            )
        known_slots = {
            slot["slot_id"]
            for slot in load_json(schedule_path).get("calendar_slots", [])
        }
        unknown = sorted(set(schedule_slot_ids) - known_slots)
        if unknown:
            raise ValidationError(
                f"seed names schedule slots that do not exist: {unknown}"
            )

    plan = {
        "research_search_plan_id": (
            "research_search_plan_" + run_id.removeprefix("research_run_")
        ),
        "research_run_id": run_id,
        "creator_profile_id": creator_profile_id,
        "created_on": _iso_seconds(moment),
        "mode": seed["mode"],
        "scope": seed["scope"],
        "schedule_slot_ids": schedule_slot_ids,
        "platforms": list(seed["platforms"]),
        "decision_basis": seed["decision_basis"],
        "adapters_considered": seed["adapters_considered"],
        "planned_queries": seed["planned_queries"],
        "planned_sources": seed.get("planned_sources", []),
        "skipped_sources": seed.get("skipped_sources", []),
        "approval_gates": seed.get("approval_gates", []),
        "future_connector_notes": seed.get("future_connector_notes", []),
    }
    validate_record("research-search-plan", plan)
    validate_research_search_plan_semantics(plan)

    run_dir = staged_run_dir(workspace_dir, run_id)
    if run_dir.exists():
        raise FileExistsError(f"Staged research run already exists: {run_dir}")
    run_dir.mkdir(parents=True)
    plan_path = run_dir / "search-plan.json"
    write_json_atomic(plan_path, plan)
    return {
        "run_dir": run_dir,
        "search_plan_path": plan_path,
        "research_run_id": run_id,
    }


def _scan_jsonl_ids(run_dir, filename, schema_name, id_field):
    path = Path(run_dir) / filename
    if not path.exists():
        return []
    records = validate_jsonl_file(schema_name, path)
    ids = []
    for record in records:
        if record[id_field] not in ids:
            ids.append(record[id_field])
    return ids


def _entries_citing_run(workspace_dir, run_id):
    entries_dir = (
        Path(workspace_dir) / "research" / "idea-queue" / "entries"
    )
    entry_ids = []
    if entries_dir.exists():
        for entry_path in sorted(entries_dir.glob("*.json")):
            entry = load_json(entry_path)
            cited = {
                ref["research_run_id"]
                for ref in entry.get("evidence_refs", [])
            }
            if run_id in cited:
                entry_ids.append(entry["idea_queue_entry_id"])
    return entry_ids


def _stable_findings_citing_run(workspace_dir, run_id):
    from influencer_os.research import parse_frontmatter

    stable_dir = Path(workspace_dir) / "research" / "stable-findings"
    finding_ids = []
    if stable_dir.exists():
        for stable_path in sorted(stable_dir.glob("*.md")):
            data, _body = parse_frontmatter(stable_path)
            if run_id in data.get("source_run_ids", []):
                finding_ids.append(data["finding_id"])
    return finding_ids


def complete_run(run_dir, creator_workspace, *, material_update,
                 error=None, finding_ids=None, intelligence_updates=None,
                 now=None):
    """Derive the research-run record from its staged plan and accumulated
    ledgers, validate, and move the run folder into canonical
    research/runs/. Copied header fields come verbatim from the plan, so
    run/plan drift cannot occur."""
    workspace_dir = Path(creator_workspace)
    run_dir = Path(run_dir)
    if not run_dir.exists() and not run_dir.is_absolute():
        candidate = staged_run_dir(workspace_dir, str(run_dir))
        if candidate.exists():
            run_dir = candidate
    plan_path = run_dir / "search-plan.json"
    if not plan_path.exists():
        raise FileNotFoundError(f"Staged run has no search plan: {plan_path}")
    plan = load_json(plan_path)
    validate_record("research-search-plan", plan)
    run_id = plan["research_run_id"]

    failed = error is not None
    if not failed and not (run_dir / "source-yield.jsonl").exists():
        raise ValidationError(
            f"completed run {run_id} needs a source-yield.jsonl ledger "
            "(what the run actually did); only failed runs may omit it"
        )

    outputs = {
        "finding_ids": (
            list(finding_ids)
            if finding_ids is not None
            else _stable_findings_citing_run(workspace_dir, run_id)
        ),
        "idea_queue_entry_ids": _entries_citing_run(workspace_dir, run_id),
        "evidence_ids": _scan_jsonl_ids(
            run_dir, "evidence.jsonl", "research-evidence", "evidence_id"
        ),
        "metric_snapshot_ids": _scan_jsonl_ids(
            run_dir, "metric-snapshots.jsonl", "metric-snapshot",
            "metric_snapshot_id",
        ),
        "research_intelligence_updates": list(intelligence_updates or []),
    }
    if failed:
        run_status = "failed"
    elif material_update:
        run_status = "completed"
    else:
        run_status = "completed_no_material_update"
    run_record = {
        "research_run_id": run_id,
        "creator_profile_id": plan["creator_profile_id"],
        "started_on": plan["created_on"],
        "completed_on": _iso_seconds(_now(now)),
        "mode": plan["mode"],
        "scope": plan["scope"],
        "schedule_slot_ids": list(plan["schedule_slot_ids"]),
        "platforms": list(plan["platforms"]),
        "material_update": bool(material_update) and not failed,
        "outputs": outputs,
        "run_status": run_status,
    }
    if failed:
        run_record["error"] = error
    validate_record("research-run", run_record)
    write_json_atomic(run_dir / "research-run.json", run_record)

    canonical_dir = workspace_dir / "research" / "runs" / run_id
    if canonical_dir.resolve() == run_dir.resolve():
        raise ValidationError(
            f"run {run_id} is already canonical; complete-run finishes "
            "staged in-flight runs"
        )
    if canonical_dir.exists():
        raise FileExistsError(f"Canonical run already exists: {canonical_dir}")
    canonical_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(run_dir), str(canonical_dir))

    from influencer_os.research import validate_research

    validate_research(workspace_dir)
    return {
        "run_dir": canonical_dir,
        "research_run_id": run_id,
        "run_status": run_status,
        "outputs": outputs,
    }
