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
    review_has_new_research_demand,
    validate_research_demand_loops,
    validate_file,
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
    "terminal_review_record_id",
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
        # A proposal authorizes a downstream Revision; that Revision points
        # back to this approved Quarter Plan when Phase F executes. Requiring
        # the downstream record here would invert the provenance direction
        # and make construction circular.


def _validated_campaign_records(workspace_dir, scope):
    records = {}
    campaigns_dir = Path(workspace_dir) / "campaigns"
    for path in sorted(campaigns_dir.glob("*/campaign.json")):
        record = load_json(path)
        validate_record("campaign", record)
        check_creator_scope(record, scope, path)
        campaign_id = record["campaign_id"]
        if path.parent.name != campaign_id:
            raise ValidationError(
                f"{path}: directory does not match campaign_id {campaign_id!r}"
            )
        records[campaign_id] = record
    return records


def _validated_concept_records(workspace_dir, scope, campaigns):
    records = {}
    concepts_glob = Path(workspace_dir) / "campaigns"
    for path in sorted(concepts_glob.glob("*/concepts/*.json")):
        record = load_json(path)
        validate_record("campaign-concept", record)
        check_creator_scope(record, scope, path)
        concept_id = record["campaign_concept_id"]
        if path.stem != concept_id:
            raise ValidationError(
                f"{path}: filename does not match campaign_concept_id {concept_id!r}"
            )
        owning_campaign_id = path.parent.parent.name
        if record["campaign_id"] != owning_campaign_id or owning_campaign_id not in campaigns:
            raise ValidationError(
                f"{path}: Campaign Concept does not resolve to its owning Campaign"
            )
        records[concept_id] = record
    return records


def _validated_performance_summary_records(workspace_dir, scope):
    """Schema-validated, creator-scoped PerformanceSummaries on disk."""
    records = {}
    projects_dir = Path(workspace_dir) / "projects"
    if not projects_dir.exists():
        return records
    for path in sorted(projects_dir.glob("*/performance-summary.json")):
        record = load_json(path)
        validate_record("performance-summary", record)
        check_creator_scope(record, scope, path)
        records[record["performance_summary_id"]] = record
    return records


def _check_reference_closure(plan, concepts, campaigns, summaries):
    """Close the Campaign/Concept/PerformanceSummary references 5a deferred.

    A Quarter Plan's Campaign Concept set, Campaign lifecycle decisions,
    Campaign Duration Target changes, and retrospective PerformanceSummary
    ids must each resolve to a real record at rest (settlement A). The
    retrospective's free-text `lesson_refs` are provenance pointers into
    memory/learnings.md and are not resolved here (settlement B).
    """
    plan_id = plan["quarter_plan_id"]
    for entry in plan["campaign_concept_set"]:
        concept_id = entry["campaign_concept_id"]
        concept = concepts.get(concept_id)
        if concept is None:
            raise ValidationError(
                f"quarter plan {plan_id} names campaign_concept_id "
                f"{concept_id!r}, which resolves to no Campaign Concept on disk"
            )
        if entry["disposition"] == "re_confirmed" and concept["status"] != "active":
            raise ValidationError(
                f"quarter plan {plan_id} marks Campaign Concept {concept_id!r} "
                f"re_confirmed, but its status is {concept['status']!r}; only "
                "active Concepts may be re_confirmed"
            )
    for entry in plan["campaign_lifecycle_decisions"]:
        campaign_id = entry["campaign_id"]
        if campaign_id not in campaigns:
            raise ValidationError(
                f"quarter plan {plan_id} names campaign_id {campaign_id!r} in a "
                "lifecycle decision, which resolves to no Campaign on disk"
            )
    for entry in plan["campaign_duration_target_changes"]:
        campaign_id = entry["campaign_id"]
        if campaign_id not in campaigns:
            raise ValidationError(
                f"quarter plan {plan_id} names campaign_id {campaign_id!r} in a "
                "duration-target change, which resolves to no Campaign on disk"
            )
    for summary_id in plan["retrospective"]["performance_summary_ids"]:
        if summary_id not in summaries:
            raise ValidationError(
                f"quarter plan {plan_id} names performance_summary_id "
                f"{summary_id!r}, which resolves to no PerformanceSummary on disk"
            )


def _check_terminal_review_ref(workspace_dir, plan):
    """Resolve and close the mandatory terminal Quarterly Review loop."""
    review_id = plan["terminal_review_record_id"]
    plan_id = plan["quarter_plan_id"]
    review_path = Path(workspace_dir) / "reviews" / f"{review_id}.json"
    if not review_path.is_file():
        raise ValidationError(
            f"quarter plan {plan_id} names terminal_review_record_id "
            f"{review_id!r}, which resolves to no review under reviews/"
        )
    review = load_json(review_path)
    validate_record("review-record", review)
    if review["review_record_id"] != review_path.stem:
        raise ValidationError(
            f"{review_path}: filename does not match review_record_id "
            f"{review['review_record_id']!r}"
        )
    check_creator_scope(review, load_workspace_scope(workspace_dir), review_path)
    if review.get("review_role") != "quarterly":
        raise ValidationError(
            f"quarter plan {plan_id} terminal_review_record_id {review_id!r} "
            "must reference a 'quarterly' review"
        )
    for ref in review["artifact_refs"]:
        relative_ref = Path(ref)
        artifact_path = Path(workspace_dir) / relative_ref
        if relative_ref.is_absolute() or ".." in relative_ref.parts:
            raise ValidationError(
                f"Quarterly Review {review_id} artifact ref must stay inside "
                f"the Creator Workspace: {ref!r}"
            )
        if not artifact_path.is_file() or artifact_path.is_symlink():
            raise ValidationError(
                f"Quarterly Review {review_id} artifact ref does not resolve "
                f"to a regular workspace file: {ref!r}"
            )
    required_packet_refs = {
        f"quarter-plans/packets/{plan_id}/draft-quarter-plan.json",
        f"quarter-plans/packets/{plan_id}/campaign-concept-set.json",
    }
    missing_packet_refs = required_packet_refs - set(review["artifact_refs"])
    if missing_packet_refs:
        raise ValidationError(
            f"quarter plan {plan_id} terminal Quarterly Review {review_id!r} "
            f"does not reference its reviewed plan packet: {sorted(missing_packet_refs)}"
        )

    reviews_by_id = {}
    for path in sorted((Path(workspace_dir) / "reviews").glob("*.json")):
        candidate = load_json(path)
        validate_record("review-record", candidate)
        candidate_id = candidate["review_record_id"]
        if candidate_id != path.stem:
            raise ValidationError(
                f"{path}: filename does not match review_record_id {candidate_id!r}"
            )
        check_creator_scope(candidate, load_workspace_scope(workspace_dir), path)
        reviews_by_id[candidate_id] = candidate
    validate_research_demand_loops(reviews_by_id)
    loop = review["research_demand_loop"]
    if (
        loop["extra_research_round"] < 2
        and review_has_new_research_demand(review)
    ):
        raise ValidationError(
            f"quarter plan {plan_id} terminal Quarterly Review issues new "
            "Research Demands before the two-extra-round cap; continue the loop"
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
    scope = load_workspace_scope(workspace_dir)
    check_creator_scope(plan, scope, quarter_plan_id)
    _check_revision_refs(plan, _revision_ids(workspace_dir))
    campaigns = _validated_campaign_records(workspace_dir, scope)
    concepts = _validated_concept_records(workspace_dir, scope, campaigns)
    summaries = _validated_performance_summary_records(workspace_dir, scope)
    _check_reference_closure(plan, concepts, campaigns, summaries)
    _check_terminal_review_ref(workspace_dir, plan)
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


def coming_week_staleness_warnings(workspace_dir, now=None):
    """Return advisory warnings for unresolved slots in the coming week."""
    schedule_path = Path(workspace_dir) / "content-schedule.json"
    if not schedule_path.exists():
        return []
    validate_file("creator-content-schedule", schedule_path)
    schedule = load_json(schedule_path)
    today = _today(now)
    window_end = today + datetime.timedelta(days=6)
    warnings = []
    for slot in schedule["calendar_slots"]:
        target_date = datetime.date.fromisoformat(slot["target_date"])
        research_status = slot["research_state"]["status"]
        if (
            today <= target_date <= window_end
            and slot["status"] not in {"filled", "skipped"}
            and research_status in {"unresearched", "candidates_ready"}
        ):
            warnings.append(
                f"warning: coming-week Anchor Slot {slot['slot_id']} targets "
                f"{slot['target_date']} but research is {research_status}. Run "
                "the human-initiated Weekly Planning Cycle."
            )
    return warnings


def validate_cadence_records(workspace_dir):
    """Validate cadence records and return advisory cadence warnings."""
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
    campaigns = _validated_campaign_records(workspace_dir, scope)
    concepts = _validated_concept_records(workspace_dir, scope, campaigns)
    summaries = _validated_performance_summary_records(workspace_dir, scope)
    for plan in plans:
        _check_revision_refs(plan, revision_ids)
        # Slice 5b closes the Campaign/Concept/PerformanceSummary reference
        # closure 5a deferred to the cycle workflow: the Quarter Plan's
        # provenance is a workspace invariant at rest (settlement A).
        _check_reference_closure(plan, concepts, campaigns, summaries)
        _check_terminal_review_ref(workspace_dir, plan)

    warnings = coming_week_staleness_warnings(workspace_dir)
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
