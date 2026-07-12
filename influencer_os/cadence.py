"""Quarter Plan and Revision record contracts (ADR 0047 core, part A)."""

import datetime
from pathlib import Path

from influencer_os.constructors import (
    check_seed_fields,
    creator_id_suffix,
    load_seed,
    load_workspace_manifest,
    next_sequenced_id,
    rebuild_projections,
)
from influencer_os.creator_scope import check_creator_scope, load_workspace_scope
from influencer_os.json_io import write_json_atomic
from influencer_os.readiness import require_production_ready
from influencer_os.validation import (
    ValidationError,
    load_json,
    validate_record,
)


QUARTER_PLANS_DIR = "quarter-plans"
REVISIONS_DIR = "revisions"
QUARTER_WEEKS = 13

QUARTER_SEED_REQUIRED = (
    "retrospective",
    "campaign_concept_set",
    "campaign_lifecycle_decisions",
    "campaign_duration_target_changes",
    "schedule_shape",
    "revision_proposals",
    "approval",
)
QUARTER_SEED_OPTIONAL = (
    "governing_foundation_revision_id",
    "governing_strategy_revision_id",
    "notes",
)

REVISION_SEED_REQUIRED = ("quarter_plan_id", "amended_areas", "rationale")
REVISION_SEED_OPTIONAL = ("notes",)


def _today(now=None):
    if now is None:
        return datetime.date.today()
    if isinstance(now, datetime.datetime):
        return now.date()
    if isinstance(now, datetime.date):
        return now
    raise TypeError("now must be a datetime.date or datetime.datetime")


def quarter_anchor_date(workspace_dir):
    """Return the one production-ready flip date, failing closed.

    ADR 0047 implementation settlement: readiness-gates.json is the single
    source of truth; no second anchor or mutable cadence clock is maintained.
    """
    readiness_path = Path(workspace_dir) / "readiness-gates.json"
    readiness = load_json(readiness_path)
    validate_record("readiness-gates", readiness)
    milestone = readiness["milestones"]["production"]
    approved_on = milestone.get("approved_on")
    if milestone.get("status") != "ready" or approved_on is None:
        raise ValidationError(
            "Quarter anchor requires a ready production milestone with "
            "milestones.production.approved_on in readiness-gates.json"
        )
    return approved_on


def quarter_window(anchor_date, quarter_number):
    if quarter_number < 1:
        raise ValidationError("quarter_number must be at least 1")
    anchor = (
        anchor_date
        if isinstance(anchor_date, datetime.date)
        else datetime.date.fromisoformat(anchor_date)
    )
    start = anchor + datetime.timedelta(weeks=QUARTER_WEEKS * (quarter_number - 1))
    end = start + datetime.timedelta(weeks=QUARTER_WEEKS)
    return start, end


def _quarter_plan_paths(workspace_dir):
    plans_dir = Path(workspace_dir) / QUARTER_PLANS_DIR
    return sorted(plans_dir.glob("*.json")) if plans_dir.exists() else []


def _revision_paths(workspace_dir, family):
    family_dir = Path(workspace_dir) / REVISIONS_DIR / family
    return sorted(family_dir.glob("*.json")) if family_dir.exists() else []


def _revision_ids(workspace_dir, family=None):
    families = (family,) if family else ("foundation", "strategy")
    return {
        path.stem
        for current_family in families
        for path in _revision_paths(workspace_dir, current_family)
    }


def _check_revision_refs(plan, revision_ids):
    plan_id = plan["quarter_plan_id"]
    for field in (
        "governing_foundation_revision_id",
        "governing_strategy_revision_id",
    ):
        revision_id = plan.get(field)
        if revision_id is not None and revision_id not in revision_ids:
            raise ValidationError(
                f"quarter plan {plan_id} names {field} {revision_id!r}, "
                "which resolves to no Revision on disk"
            )
    for proposal in plan["revision_proposals"]:
        revision_id = proposal["revision_id"]
        expected_prefix = f"{proposal['revision_type']}_revision_"
        if not revision_id.startswith(expected_prefix):
            raise ValidationError(
                f"quarter plan {plan_id} proposal type "
                f"{proposal['revision_type']!r} disagrees with {revision_id!r}"
            )
        if revision_id not in revision_ids:
            raise ValidationError(
                f"quarter plan {plan_id} proposes Revision {revision_id!r}, "
                "which resolves to no Revision on disk"
            )


def scaffold_quarter_plan(seed, creator_workspace, now=None):
    require_production_ready(creator_workspace)
    workspace_dir = Path(creator_workspace)
    seed = load_seed(seed)
    check_seed_fields(
        seed, QUARTER_SEED_REQUIRED, QUARTER_SEED_OPTIONAL, "quarter-plan"
    )
    manifest = load_workspace_manifest(workspace_dir)
    existing_paths = _quarter_plan_paths(workspace_dir)
    existing = [load_json(path) for path in existing_paths]
    quarter_number = max(
        (record["quarter_number"] for record in existing), default=0
    ) + 1
    anchor = quarter_anchor_date(workspace_dir)
    start, end = quarter_window(anchor, quarter_number)
    suffix = creator_id_suffix(manifest["creator_profile_id"])
    quarter_plan_id = next_sequenced_id(
        f"quarter_plan_{suffix}", {path.stem for path in existing_paths}
    )
    plan = {
        "quarter_plan_id": quarter_plan_id,
        "creator_profile_id": manifest["creator_profile_id"],
        "creator_slug": manifest["creator_slug"],
        "quarter_number": quarter_number,
        "quarter_start_date": start.isoformat(),
        "quarter_end_date": end.isoformat(),
        "production_ready_anchor_date": anchor,
        "retrospective": seed["retrospective"],
        "campaign_concept_set": seed["campaign_concept_set"],
        "campaign_lifecycle_decisions": seed["campaign_lifecycle_decisions"],
        "campaign_duration_target_changes": seed[
            "campaign_duration_target_changes"
        ],
        "schedule_shape": seed["schedule_shape"],
        "revision_proposals": seed["revision_proposals"],
        "approval": seed["approval"],
        "created_on": _today(now).isoformat(),
    }
    for optional_field in QUARTER_SEED_OPTIONAL:
        if optional_field in seed:
            plan[optional_field] = seed[optional_field]
    validate_record("quarter-plan", plan)
    check_creator_scope(plan, load_workspace_scope(workspace_dir), quarter_plan_id)
    _check_revision_refs(plan, _revision_ids(workspace_dir))
    path = workspace_dir / QUARTER_PLANS_DIR / f"{quarter_plan_id}.json"
    if path.exists():
        raise ValidationError(f"quarter plan already exists: {path}")
    write_json_atomic(path, plan)
    validate_cadence_records(workspace_dir)
    return {
        "path": path,
        "id": quarter_plan_id,
        "warnings": rebuild_projections(workspace_dir),
    }


def _scaffold_revision(seed, creator_workspace, family, now=None):
    require_production_ready(creator_workspace)
    workspace_dir = Path(creator_workspace)
    seed = load_seed(seed)
    check_seed_fields(
        seed,
        REVISION_SEED_REQUIRED,
        REVISION_SEED_OPTIONAL,
        f"{family}-revision",
    )
    manifest = load_workspace_manifest(workspace_dir)
    plan_ids = {path.stem for path in _quarter_plan_paths(workspace_dir)}
    if seed["quarter_plan_id"] not in plan_ids:
        raise ValidationError(
            f"quarter_plan_id {seed['quarter_plan_id']!r} resolves to no "
            "Quarter Plan on disk"
        )
    existing_paths = _revision_paths(workspace_dir, family)
    existing = [load_json(path) for path in existing_paths]
    version = max((record["version"] for record in existing), default=0) + 1
    suffix = creator_id_suffix(manifest["creator_profile_id"])
    revision_id = f"{family}_revision_{suffix}_{version:03d}"
    path = (
        workspace_dir
        / REVISIONS_DIR
        / family
        / f"{revision_id}.json"
    )
    if path.exists():
        raise ValidationError(
            f"immutable {family} Revision version {version} already exists: {path}"
        )
    revision = {
        f"{family}_revision_id": revision_id,
        "creator_profile_id": manifest["creator_profile_id"],
        "creator_slug": manifest["creator_slug"],
        "version": version,
        "quarter_plan_id": seed["quarter_plan_id"],
        "amended_areas": seed["amended_areas"],
        "rationale": seed["rationale"],
        "created_on": _today(now).isoformat(),
    }
    if "notes" in seed:
        revision["notes"] = seed["notes"]
    validate_record(f"{family}-revision", revision)
    check_creator_scope(revision, load_workspace_scope(workspace_dir), revision_id)
    write_json_atomic(path, revision)
    validate_cadence_records(workspace_dir)
    return {
        "path": path,
        "id": revision_id,
        "warnings": rebuild_projections(workspace_dir),
    }


def scaffold_foundation_revision(seed, creator_workspace, now=None):
    return _scaffold_revision(seed, creator_workspace, "foundation", now=now)


def scaffold_strategy_revision(seed, creator_workspace, now=None):
    return _scaffold_revision(seed, creator_workspace, "strategy", now=now)


def _validate_revision_family(workspace_dir, scope, family, plan_ids, checked):
    revisions = []
    suffix = creator_id_suffix(scope["creator_profile_id"])
    for path in _revision_paths(workspace_dir, family):
        revision = load_json(path)
        validate_record(f"{family}-revision", revision)
        check_creator_scope(revision, scope, path)
        revision_id = revision[f"{family}_revision_id"]
        if path.stem != revision_id:
            raise ValidationError(
                f"{path}: filename does not match {family}_revision_id "
                f"{revision_id!r}"
            )
        expected_id = f"{family}_revision_{suffix}_{revision['version']:03d}"
        if revision_id != expected_id:
            raise ValidationError(
                f"{path}: Revision id must encode its immutable sequential "
                f"version as {expected_id!r}"
            )
        if revision["quarter_plan_id"] not in plan_ids:
            raise ValidationError(
                f"{path}: quarter_plan_id {revision['quarter_plan_id']!r} "
                "resolves to no Quarter Plan on disk"
            )
        revisions.append(revision)
        checked.append(str(path.relative_to(workspace_dir)))
    versions = [revision["version"] for revision in revisions]
    expected = list(range(1, len(versions) + 1))
    if sorted(versions) != expected:
        raise ValidationError(
            f"{family} Revision versions must be unique and contiguous from "
            f"1; found {sorted(versions)}, expected {expected}"
        )


def validate_cadence_records(workspace_dir):
    """Validate cadence records and return the advisory Quarter warning."""
    workspace_dir = Path(workspace_dir)
    scope = load_workspace_scope(workspace_dir)
    checked = []
    plans = []
    anchor = None
    plan_paths = _quarter_plan_paths(workspace_dir)
    revision_paths = {
        family: _revision_paths(workspace_dir, family)
        for family in ("foundation", "strategy")
    }
    has_records = bool(plan_paths or any(revision_paths.values()))
    if has_records:
        anchor = quarter_anchor_date(workspace_dir)
    else:
        readiness = load_json(workspace_dir / "readiness-gates.json")
        milestone = readiness["milestones"]["production"]
        if (
            milestone.get("status") == "ready"
            and milestone.get("approved_on") is not None
        ):
            anchor = milestone["approved_on"]

    for path in plan_paths:
        plan = load_json(path)
        validate_record("quarter-plan", plan)
        check_creator_scope(plan, scope, path)
        if path.stem != plan["quarter_plan_id"]:
            raise ValidationError(
                f"{path}: filename does not match quarter_plan_id "
                f"{plan['quarter_plan_id']!r}"
            )
        start, end = quarter_window(anchor, plan["quarter_number"])
        expected = (anchor, start.isoformat(), end.isoformat())
        actual = (
            plan["production_ready_anchor_date"],
            plan["quarter_start_date"],
            plan["quarter_end_date"],
        )
        if actual != expected:
            raise ValidationError(
                f"{path}: Quarter window {actual!r} does not derive from "
                f"production_ready anchor {anchor!r}; expected {expected!r}"
            )
        plans.append(plan)
        checked.append(str(path.relative_to(workspace_dir)))

    plan_ids = {plan["quarter_plan_id"] for plan in plans}
    for family in ("foundation", "strategy"):
        _validate_revision_family(workspace_dir, scope, family, plan_ids, checked)

    revision_ids = _revision_ids(workspace_dir)
    for plan in plans:
        _check_revision_refs(plan, revision_ids)
        # Slice 5a intentionally defers Campaign/Concept reference closure in
        # concept sets and lifecycle decisions to the cycle workflow in 5b.

    warnings = []
    if anchor is not None:
        current_number = max(
            (plan["quarter_number"] for plan in plans), default=1
        )
        _, current_end = quarter_window(anchor, current_number)
        if datetime.date.today() > current_end:
            warnings.append(
                "warning: overdue Quarter; current Quarter "
                f"{current_number} ended {current_end.isoformat()}. Run the "
                "human-initiated Quarterly Planning Cycle."
            )
    return {
        "checked_paths": sorted(checked),
        "warnings": warnings,
    }
