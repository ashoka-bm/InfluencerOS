"""Campaign hierarchy records (ADRs 0029-0032, Slice 1).

Seed-based constructors (docs/record-constructors.md) for the Campaign,
CampaignConcept, and ContentOpportunity records plus the content
opportunity queue, an activation helper for the human campaign-activation
decision, and the cross-record workspace walker that keeps the hierarchy
consistent: a Concept belongs to exactly one Campaign and selects only
Campaign-approved audience segments and pillars; a Concept Approval
authorizes an exact project set below explicit commercial-expression
ceilings.

Workspace layout (campaign-concept-pressure implementation plan):

    campaigns/<campaign_id>/campaign.json
    campaigns/<campaign_id>/concepts/<campaign_concept_id>.json
    campaigns/<campaign_id>/approvals/<concept_approval_id>.json
    research/content-opportunity-queue/queue.json
    research/content-opportunity-queue/entries/<content_opportunity_id>.json
"""

import datetime
from copy import deepcopy
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
from influencer_os.validation import (
    ValidationError,
    load_json,
    research_platform_for_surface,
    validate_record,
)

CAMPAIGNS_DIR = "campaigns"
OPPORTUNITY_QUEUE_DIR = Path("research") / "content-opportunity-queue"

CAMPAIGN_SEED_REQUIRED = (
    "name",
    "objective",
    "primary_content_pillar_id",
    "primary_audience_segment",
    "measurable_outcome",
)
CAMPAIGN_SEED_OPTIONAL = (
    "supporting_content_pillar_ids",
    "supporting_audience_segments",
    "primary_offer_conversion_asset_id",
    "supporting_conversion_asset_ids",
    "notes",
    "campaign_id",
)

CONCEPT_SEED_REQUIRED = (
    "campaign_id",
    "title",
    "hypothesis",
    "audience_tension",
    "promise",
    "audience_segment",
    "content_pillar_id",
    "primary_commercial_function",
)
# The intent trio, finding refs, and evidence are copied from the assigned
# opportunity when one is named; they are authored (intended_payoff
# required) only for campaign-scoped concepts with no opportunity.
CONCEPT_SEED_OPTIONAL = (
    "supporting_commercial_functions",
    "source_content_opportunity_id",
    "evidence_refs",
    "intended_payoff",
    "intended_emotion",
    "core_message",
    "source_finding_ids",
    "related_concepts",
    "notes",
    "campaign_concept_id",
)

# Human-driven concept lifecycle moves; 'active' is only ever set by the
# approval commit, and an active concept only retires.
CONCEPT_STATUS_TRANSITIONS = {
    "draft": {"researching", "ready_for_approval", "retired"},
    "researching": {"draft", "ready_for_approval", "retired"},
    "ready_for_approval": {"draft", "researching", "retired"},
    "active": {"retired"},
    "retired": set(),
}

OPPORTUNITY_SEED_REQUIRED = (
    "title",
    "hook",
    "premise_summary",
    "intended_payoff",
    "topic_cluster",
    "platform_recommendations",
    "format_recommendations",
    "schedule_fit_type",
    "evidence_refs",
    "scores",
)
OPPORTUNITY_SEED_OPTIONAL = (
    "intended_emotion",
    "core_message",
    "content_pillar_ids",
    "source_finding_ids",
    "urgency_window",
    "creator_fit_notes",
    "production_notes",
    "avoid_notes",
    "stale_on",
    "assignment_intent_note",
    "content_opportunity_id",
)


def _today(now):
    moment = now if now is not None else datetime.datetime.now()
    return moment.strftime("%Y-%m-%d")


def campaign_dir(creator_workspace, campaign_id):
    return Path(creator_workspace) / CAMPAIGNS_DIR / campaign_id


def _campaign_path(creator_workspace, campaign_id):
    return campaign_dir(creator_workspace, campaign_id) / "campaign.json"


def _queue_path(creator_workspace):
    return Path(creator_workspace) / OPPORTUNITY_QUEUE_DIR / "queue.json"


def _entries_dir(creator_workspace):
    return Path(creator_workspace) / OPPORTUNITY_QUEUE_DIR / "entries"


def load_campaign(creator_workspace, campaign_id):
    campaign_path = _campaign_path(creator_workspace, campaign_id)
    if not campaign_path.exists():
        raise ValidationError(
            f"campaign_id {campaign_id!r} resolves to no campaign: "
            f"{campaign_path}"
        )
    campaign = load_json(campaign_path)
    validate_record("campaign", campaign)
    return campaign


def _load_creator_profile(workspace_dir):
    profile_path = Path(workspace_dir) / "creator-profile.json"
    if not profile_path.exists():
        raise ValidationError(
            f"Missing creator profile: {profile_path}; campaigns select "
            "pillars and audience segments from the profile"
        )
    profile = load_json(profile_path)
    validate_record("creator-profile", profile)
    return profile


def _profile_pillar_ids(profile):
    return {pillar["pillar_id"] for pillar in profile["content_pillars"]}


def _check_campaign_profile_refs(campaign, profile, conversion_asset_ids):
    """Campaign pillar and offer refs must resolve; audience segments are
    free-form creator-profile inputs and are not cross-pinned (AGENTS.md:
    audience is a creator-profile input, never invented or redefined)."""
    known_pillars = _profile_pillar_ids(profile)
    campaign_id = campaign["campaign_id"]
    named = [campaign["primary_content_pillar_id"]]
    named.extend(campaign["supporting_content_pillar_ids"])
    unknown = sorted(set(named) - known_pillars)
    if unknown:
        raise ValidationError(
            f"campaign {campaign_id} names content pillars {unknown} that "
            "do not exist on the creator profile"
        )
    named_assets = []
    if campaign.get("primary_offer_conversion_asset_id"):
        named_assets.append(campaign["primary_offer_conversion_asset_id"])
    named_assets.extend(campaign.get("supporting_conversion_asset_ids", []))
    unknown_assets = sorted(set(named_assets) - set(conversion_asset_ids))
    if unknown_assets:
        raise ValidationError(
            f"campaign {campaign_id} names conversion assets "
            f"{unknown_assets} that do not exist under conversion-assets/"
        )


def _workspace_conversion_asset_ids(workspace_dir):
    asset_ids = set()
    assets_dir = Path(workspace_dir) / "conversion-assets"
    if assets_dir.exists():
        for asset_path in sorted(assets_dir.glob("*.json")):
            asset_ids.add(load_json(asset_path)["conversion_asset_id"])
    return asset_ids


def _existing_campaign_ids(workspace_dir):
    campaigns_root = Path(workspace_dir) / CAMPAIGNS_DIR
    if not campaigns_root.exists():
        return set()
    return {path.name for path in campaigns_root.iterdir() if path.is_dir()}


def scaffold_campaign(seed, creator_workspace, now=None):
    """Build and write one draft Campaign from its authored seed."""
    workspace_dir = Path(creator_workspace)
    seed = load_seed(seed)
    check_seed_fields(
        seed, CAMPAIGN_SEED_REQUIRED, CAMPAIGN_SEED_OPTIONAL, "campaign"
    )
    workspace_manifest = load_workspace_manifest(workspace_dir)
    creator_profile_id = workspace_manifest["creator_profile_id"]
    existing = _existing_campaign_ids(workspace_dir)
    campaign_id = seed.get("campaign_id") or next_sequenced_id(
        f"campaign_{creator_id_suffix(creator_profile_id)}", existing
    )
    if campaign_id in existing:
        raise ValidationError(f"campaign id already exists: {campaign_id}")
    today = _today(now)
    campaign = {
        "campaign_id": campaign_id,
        "creator_profile_id": creator_profile_id,
        "name": seed["name"],
        "objective": seed["objective"],
        "status": "draft",
        "primary_content_pillar_id": seed["primary_content_pillar_id"],
        "supporting_content_pillar_ids": list(
            seed.get("supporting_content_pillar_ids", [])
        ),
        "primary_audience_segment": seed["primary_audience_segment"],
        "supporting_audience_segments": list(
            seed.get("supporting_audience_segments", [])
        ),
        "measurable_outcome": seed["measurable_outcome"],
        "created_on": today,
        "updated_on": today,
    }
    if seed.get("primary_offer_conversion_asset_id"):
        campaign["primary_offer_conversion_asset_id"] = seed[
            "primary_offer_conversion_asset_id"
        ]
    if "supporting_conversion_asset_ids" in seed:
        campaign["supporting_conversion_asset_ids"] = list(
            seed["supporting_conversion_asset_ids"]
        )
    if seed.get("notes"):
        campaign["notes"] = seed["notes"]
    validate_record("campaign", campaign)
    profile = _load_creator_profile(workspace_dir)
    _check_campaign_profile_refs(
        campaign, profile, _workspace_conversion_asset_ids(workspace_dir)
    )
    campaign_path = _campaign_path(workspace_dir, campaign_id)
    campaign_path.parent.mkdir(parents=True, exist_ok=False)
    write_json_atomic(campaign_path, campaign)
    validate_campaign_records(workspace_dir)
    return {
        "campaign_path": campaign_path,
        "campaign_id": campaign_id,
        "warnings": rebuild_projections(workspace_dir),
    }


def activate_campaign(creator_workspace, campaign_id, activation_note=None,
                      now=None):
    """Record the human activation decision on a draft campaign. Activation
    is approval metadata, not a new production Gate (ADR 0029)."""
    workspace_dir = Path(creator_workspace)
    campaign = load_campaign(workspace_dir, campaign_id)
    if campaign["status"] != "draft":
        raise ValidationError(
            f"campaign {campaign_id} has status {campaign['status']!r}; "
            "only a draft campaign activates"
        )
    today = _today(now)
    campaign["status"] = "active"
    campaign["updated_on"] = today
    activation = {"approved_by": "user", "activated_on": today}
    if activation_note:
        activation["activation_note"] = activation_note
    campaign["activation"] = activation
    validate_record("campaign", campaign)
    campaign_path = _campaign_path(workspace_dir, campaign_id)
    write_json_atomic(campaign_path, campaign)
    validate_campaign_records(workspace_dir)
    return {
        "campaign_path": campaign_path,
        "campaign_id": campaign_id,
        "warnings": rebuild_projections(workspace_dir),
    }


# --- campaign concept -------------------------------------------------------


def _existing_concept_ids(workspace_dir):
    concept_ids = set()
    campaigns_root = Path(workspace_dir) / CAMPAIGNS_DIR
    if campaigns_root.exists():
        for concept_path in campaigns_root.glob("*/concepts/*.json"):
            concept_ids.add(concept_path.stem)
    return concept_ids


def _load_opportunity(workspace_dir, opportunity_id):
    entry_path = _entries_dir(workspace_dir) / f"{opportunity_id}.json"
    if not entry_path.exists():
        raise ValidationError(
            f"source_content_opportunity_id {opportunity_id!r} resolves to "
            f"no content opportunity: {entry_path}"
        )
    opportunity = load_json(entry_path)
    validate_record("content-opportunity", opportunity)
    return opportunity


def check_concept_against_campaign(concept, campaign):
    """A Concept selects one Campaign-approved audience segment and one
    Campaign-approved content pillar (ADR 0029)."""
    concept_id = concept["campaign_concept_id"]
    if concept["campaign_id"] != campaign["campaign_id"]:
        raise ValidationError(
            f"concept {concept_id} names campaign {concept['campaign_id']!r} "
            f"but belongs to {campaign['campaign_id']!r}"
        )
    approved_segments = {campaign["primary_audience_segment"]}
    approved_segments.update(campaign["supporting_audience_segments"])
    if concept["audience_segment"] not in approved_segments:
        raise ValidationError(
            f"concept {concept_id} selects audience segment "
            f"{concept['audience_segment']!r}, which campaign "
            f"{campaign['campaign_id']} does not approve"
        )
    approved_pillars = {campaign["primary_content_pillar_id"]}
    approved_pillars.update(campaign["supporting_content_pillar_ids"])
    if concept["content_pillar_id"] not in approved_pillars:
        raise ValidationError(
            f"concept {concept_id} selects content pillar "
            f"{concept['content_pillar_id']!r}, which campaign "
            f"{campaign['campaign_id']} does not approve"
        )


def scaffold_campaign_concept(seed, creator_workspace, now=None):
    """Build and write one draft Campaign Concept from its authored seed.

    Assigning a Content Opportunity is one transactional operation: the
    concept copies the opportunity's evidence, intent trio, and finding
    refs, and the opportunity flips to 'assigned' with the back-link in the
    same invocation — entry, queue manifest, and concept never drift."""
    workspace_dir = Path(creator_workspace)
    seed = load_seed(seed)
    check_seed_fields(
        seed, CONCEPT_SEED_REQUIRED, CONCEPT_SEED_OPTIONAL, "campaign-concept"
    )
    workspace_manifest = load_workspace_manifest(workspace_dir)
    creator_profile_id = workspace_manifest["creator_profile_id"]
    campaign = load_campaign(workspace_dir, seed["campaign_id"])

    source_opportunity_id = seed.get("source_content_opportunity_id")
    opportunity = None
    if source_opportunity_id is not None:
        copied_fields = [
            field
            for field in ("evidence_refs", "intended_payoff",
                          "intended_emotion", "core_message",
                          "source_finding_ids")
            if field in seed
        ]
        if copied_fields:
            raise ValidationError(
                f"campaign-concept seed supplies {copied_fields} alongside "
                "source_content_opportunity_id; those fields are copied from "
                "the assigned opportunity (docs/record-constructors.md)"
            )
        opportunity = _load_opportunity(workspace_dir, source_opportunity_id)
        if opportunity["status"] not in {"new", "reviewed", "shortlisted",
                                         "needs_more_research"}:
            raise ValidationError(
                f"content opportunity {source_opportunity_id} has status "
                f"{opportunity['status']!r}; only an open opportunity can be "
                "assigned to a concept"
            )
        copied = {
            "evidence_refs": deepcopy(opportunity["evidence_refs"]),
            "intended_payoff": opportunity["intended_payoff"],
        }
        for field in ("intended_emotion", "core_message"):
            if field in opportunity:
                copied[field] = opportunity[field]
        if opportunity.get("source_finding_ids"):
            copied["source_finding_ids"] = list(opportunity["source_finding_ids"])
    else:
        if "intended_payoff" not in seed:
            raise ValidationError(
                "campaign-concept seed is missing authored fields "
                "['intended_payoff']; a campaign-scoped concept authors its "
                "intent directly"
            )
        copied = {
            "evidence_refs": deepcopy(seed.get("evidence_refs", [])),
            "intended_payoff": seed["intended_payoff"],
        }
        for field in ("intended_emotion", "core_message"):
            if field in seed:
                copied[field] = seed[field]
        if seed.get("source_finding_ids"):
            copied["source_finding_ids"] = list(seed["source_finding_ids"])

    existing = _existing_concept_ids(workspace_dir)
    concept_id = seed.get("campaign_concept_id") or next_sequenced_id(
        f"campaign_concept_{creator_id_suffix(creator_profile_id)}", existing
    )
    if concept_id in existing:
        raise ValidationError(f"campaign concept id already exists: {concept_id}")
    today = _today(now)
    concept = {
        "campaign_concept_id": concept_id,
        "campaign_id": seed["campaign_id"],
        "creator_profile_id": creator_profile_id,
        "title": seed["title"],
        "hypothesis": seed["hypothesis"],
        "audience_tension": seed["audience_tension"],
        "promise": seed["promise"],
        "audience_segment": seed["audience_segment"],
        "content_pillar_id": seed["content_pillar_id"],
        "primary_commercial_function": seed["primary_commercial_function"],
        "supporting_commercial_functions": list(
            seed.get("supporting_commercial_functions", [])
        ),
        "status": "draft",
        "created_on": today,
        "updated_on": today,
    }
    concept.update(copied)
    if source_opportunity_id is not None:
        concept["source_content_opportunity_id"] = source_opportunity_id
    if "related_concepts" in seed:
        concept["related_concepts"] = deepcopy(seed["related_concepts"])
    if seed.get("notes"):
        concept["notes"] = seed["notes"]
    validate_record("campaign-concept", concept)
    check_concept_against_campaign(concept, campaign)
    for related in concept.get("related_concepts", []):
        if related["campaign_concept_id"] not in existing:
            raise ValidationError(
                f"concept {concept_id} relates to "
                f"{related['campaign_concept_id']!r}, which does not exist"
            )

    # Prepare the assignment flip before any write (all-or-nothing).
    flipped_entry = None
    flipped_queue = None
    if opportunity is not None:
        flipped_entry = deepcopy(opportunity)
        flipped_entry["status"] = "assigned"
        linked = list(flipped_entry.get("linked_campaign_concept_ids", []))
        if concept_id not in linked:
            linked.append(concept_id)
        flipped_entry["linked_campaign_concept_ids"] = linked
        flipped_entry["updated_on"] = today
        validate_record("content-opportunity", flipped_entry)
        queue_path = _queue_path(workspace_dir)
        if not queue_path.exists():
            raise ValidationError(
                f"content opportunity {source_opportunity_id} has no queue "
                f"manifest at {queue_path}"
            )
        flipped_queue = load_json(queue_path)
        validate_record("content-opportunity-queue", flipped_queue)
        for ref in flipped_queue["entry_refs"]:
            if ref["content_opportunity_id"] == source_opportunity_id:
                ref["status"] = "assigned"
                break
        else:
            raise ValidationError(
                f"queue manifest does not track {source_opportunity_id}; the "
                "entry must be tracked before assignment"
            )
        flipped_queue["updated_on"] = today
        _recounted_queue(flipped_queue)
        validate_record("content-opportunity-queue", flipped_queue)

    concepts_dir = campaign_dir(workspace_dir, seed["campaign_id"]) / "concepts"
    concepts_dir.mkdir(parents=True, exist_ok=True)
    concept_path = concepts_dir / f"{concept_id}.json"
    # Flip the opportunity before writing the concept: a crash between the
    # writes leaves the entry linking a not-yet-written concept — detectably
    # invalid — and an already-assigned opportunity cannot be assigned twice.
    if flipped_entry is not None:
        write_json_atomic(
            _entries_dir(workspace_dir) / f"{source_opportunity_id}.json",
            flipped_entry,
        )
        write_json_atomic(_queue_path(workspace_dir), flipped_queue)
    write_json_atomic(concept_path, concept)
    validate_campaign_records(workspace_dir)
    return {
        "concept_path": concept_path,
        "campaign_concept_id": concept_id,
        "warnings": rebuild_projections(workspace_dir),
    }


def set_concept_status(creator_workspace, concept_id, new_status, now=None):
    """Record a human concept lifecycle move. 'active' is only ever set by
    the approval commit; an active concept only retires."""
    workspace_dir = Path(creator_workspace)
    concept_paths = sorted(
        workspace_dir.glob(f"campaigns/*/concepts/{concept_id}.json")
    )
    if not concept_paths:
        raise ValidationError(
            f"campaign_concept_id {concept_id!r} resolves to no concept"
        )
    concept_path = concept_paths[0]
    concept = load_json(concept_path)
    validate_record("campaign-concept", concept)
    allowed = CONCEPT_STATUS_TRANSITIONS.get(concept["status"], set())
    if new_status not in allowed:
        raise ValidationError(
            f"concept {concept_id} cannot move from {concept['status']!r} to "
            f"{new_status!r}; allowed: {sorted(allowed)}"
        )
    concept["status"] = new_status
    concept["updated_on"] = _today(now)
    validate_record("campaign-concept", concept)
    write_json_atomic(concept_path, concept)
    validate_campaign_records(concept_path.parents[3])
    return {
        "concept_path": concept_path,
        "campaign_concept_id": concept_id,
        "warnings": rebuild_projections(concept_path.parents[3]),
    }


# --- content opportunity ----------------------------------------------------


def _existing_opportunity_ids(workspace_dir):
    entries_dir = _entries_dir(workspace_dir)
    if not entries_dir.exists():
        return set()
    return {path.stem for path in entries_dir.glob("*.json")}


def _recounted_queue(queue):
    counts = {}
    for ref in queue["entry_refs"]:
        counts[ref["status"]] = counts.get(ref["status"], 0) + 1
    queue["status_counts"] = counts
    return queue


def scaffold_content_opportunity(seed, creator_workspace, now=None):
    """Build and write one new Content Opportunity and upsert the queue
    manifest in the same invocation, so entry and manifest never drift."""
    workspace_dir = Path(creator_workspace)
    seed = load_seed(seed)
    check_seed_fields(
        seed, OPPORTUNITY_SEED_REQUIRED, OPPORTUNITY_SEED_OPTIONAL,
        "content-opportunity",
    )
    workspace_manifest = load_workspace_manifest(workspace_dir)
    creator_profile_id = workspace_manifest["creator_profile_id"]
    suffix = creator_id_suffix(creator_profile_id)
    existing = _existing_opportunity_ids(workspace_dir)
    opportunity_id = seed.get("content_opportunity_id") or next_sequenced_id(
        f"content_opportunity_{suffix}", existing
    )
    if opportunity_id in existing:
        raise ValidationError(
            f"content opportunity id already exists: {opportunity_id}"
        )
    today = _today(now)
    opportunity = {"content_opportunity_id": opportunity_id}
    for field in OPPORTUNITY_SEED_REQUIRED:
        opportunity[field] = deepcopy(seed[field])
    opportunity["creator_profile_id"] = creator_profile_id
    opportunity["status"] = "new"
    opportunity["created_on"] = today
    opportunity["updated_on"] = today
    for field in OPPORTUNITY_SEED_OPTIONAL:
        if field != "content_opportunity_id" and field in seed:
            opportunity[field] = deepcopy(seed[field])
    validate_record("content-opportunity", opportunity)

    queue_path = _queue_path(workspace_dir)
    if queue_path.exists():
        queue = load_json(queue_path)
        validate_record("content-opportunity-queue", queue)
    else:
        queue = {
            "content_opportunity_queue_id": (
                f"content_opportunity_queue_{suffix}"
            ),
            "creator_profile_id": creator_profile_id,
            "entry_refs": [],
        }
    queue["entry_refs"] = list(queue["entry_refs"]) + [
        {"content_opportunity_id": opportunity_id, "status": "new"}
    ]
    queue["updated_on"] = today
    _recounted_queue(queue)
    validate_record("content-opportunity-queue", queue)

    entries_dir = _entries_dir(workspace_dir)
    entries_dir.mkdir(parents=True, exist_ok=True)
    entry_path = entries_dir / f"{opportunity_id}.json"
    write_json_atomic(entry_path, opportunity)
    write_json_atomic(queue_path, queue)
    validate_campaign_records(workspace_dir)
    return {
        "entry_path": entry_path,
        "queue_path": queue_path,
        "content_opportunity_id": opportunity_id,
        "warnings": rebuild_projections(workspace_dir),
    }


def check_project_expression_against_approval(project, approval, concept):
    """A Project executes one Concept-approved Commercial Function at or
    below its Concept Approval's expression ceilings (ADR 0030)."""
    from influencer_os.pressure import (
        expression_within_ceilings,
        is_valid_expression,
    )

    project_id = project.get("project_id", "<unknown>")
    expression = project.get("commercial_expression")
    if expression is None:
        raise ValidationError(
            f"project {project_id} is approval-backed but carries no "
            "commercial_expression; exact planned values are required "
            "(ADR 0030)"
        )
    approved_functions = {concept["primary_commercial_function"]}
    approved_functions.update(concept["supporting_commercial_functions"])
    if expression["commercial_function"] not in approved_functions:
        raise ValidationError(
            f"project {project_id} executes commercial function "
            f"{expression['commercial_function']!r}, which concept "
            f"{concept['campaign_concept_id']} does not approve"
        )
    if not is_valid_expression(
        expression["offer_integration"], expression["cta_intensity"]
    ):
        raise ValidationError(
            f"project {project_id} plans the invalid expression "
            f"{expression['offer_integration']}/{expression['cta_intensity']} "
            "(ADR 0030 matrix hole)"
        )
    if not expression_within_ceilings(
        expression["offer_integration"],
        expression["cta_intensity"],
        approval["max_offer_integration"],
        approval["max_cta_intensity"],
    ):
        raise ValidationError(
            f"project {project_id} plans "
            f"{expression['offer_integration']}/{expression['cta_intensity']}, "
            f"above approval {approval['concept_approval_id']} ceilings "
            f"{approval['max_offer_integration']}/"
            f"{approval['max_cta_intensity']}; escalation requires a new "
            "Concept Approval"
        )


# --- projections ------------------------------------------------------------


def derive_pressure_projection(creator_workspace):
    """Advisory per-platform Pressure Projection over the current schedule
    horizon (ADR 0030/0032): every Project-linked slot contributes one
    Audience Touch per targeted platform, tiers come from each project's
    derived Commercial Pressure, pre-Project slots count as unresolved —
    unknown is never reported as low — and a platform whose known
    high-pressure share exceeds the advisory threshold gets a warning that
    never blocks anything."""
    from influencer_os.pressure import (
        HIGH_PRESSURE_SHARE_ADVISORY_THRESHOLD,
        PRESSURE_TIERS,
        derive_commercial_pressure,
        pressure_indicator,
    )

    workspace_dir = Path(creator_workspace)
    schedule_path = workspace_dir / "content-schedule.json"
    if not schedule_path.exists():
        raise FileNotFoundError(f"Missing content schedule: {schedule_path}")
    schedule = load_json(schedule_path)
    validate_record("creator-content-schedule", schedule)
    projects = _workspace_project_manifests(workspace_dir)

    touches_by_platform = {}
    unresolved_slots = []
    resolved_slots = []
    for slot in schedule.get("calendar_slots", []):
        project_id = slot.get("project_id")
        if project_id is None:
            unresolved_slots.append(slot["slot_id"])
            continue
        project = projects.get(project_id)
        if project is None:
            raise ValidationError(
                f"calendar slot {slot['slot_id']} names project "
                f"{project_id!r}, which does not exist"
            )
        expression = project.get("commercial_expression")
        if expression is None:
            unresolved_slots.append(slot["slot_id"])
            continue
        tier = derive_commercial_pressure(
            expression["offer_integration"], expression["cta_intensity"]
        )
        resolved_slots.append(slot["slot_id"])
        platforms = {
            platform
            for platform in (
                research_platform_for_surface(surface)
                for surface in project.get("platform_targets", [])
            )
            if platform is not None
        }
        for platform in sorted(platforms):
            touches_by_platform.setdefault(platform, []).append(tier)

    platforms = {}
    for platform, tiers in sorted(touches_by_platform.items()):
        indicator = pressure_indicator(tiers)
        indicator["advisory_warning"] = (
            indicator["high_share"] is not None
            and indicator["high_share"] > HIGH_PRESSURE_SHARE_ADVISORY_THRESHOLD
        )
        platforms[platform] = indicator

    total_slots = len(resolved_slots) + len(unresolved_slots)
    return {
        "platforms": platforms,
        "tiers": list(PRESSURE_TIERS),
        "unresolved_slot_ids": unresolved_slots,
        "unresolved_slot_count": len(unresolved_slots),
        "known_slot_count": len(resolved_slots),
        "known_coverage": (
            len(resolved_slots) / total_slots if total_slots else None
        ),
    }


def derive_campaign_evaluation(creator_workspace):
    """Rebuildable Campaign and Concept evaluation summaries aggregated
    solely from canonical records (ADR 0032): lifecycle and delivery
    counts, commercial function and pressure mix, and the campaign's
    declared measurable outcome. Missing analytics stay unknown — no
    inferred conversion credit, fractional attribution, or duplicated
    success."""
    from influencer_os.pressure import derive_commercial_pressure

    workspace_dir = Path(creator_workspace)
    projects = _workspace_project_manifests(workspace_dir)
    campaigns = {}
    for campaign_path in sorted(
        workspace_dir.glob("campaigns/*/campaign.json")
    ):
        campaign = load_json(campaign_path)
        validate_record("campaign", campaign)
        campaign_id = campaign["campaign_id"]
        concepts = {}
        for concept_path in sorted(
            workspace_dir.glob(f"campaigns/{campaign_id}/concepts/*.json")
        ):
            concept = load_json(concept_path)
            concepts[concept["campaign_concept_id"]] = concept
        approvals = []
        for approval_path in sorted(
            workspace_dir.glob(f"campaigns/{campaign_id}/approvals/*.json")
        ):
            approvals.append(load_json(approval_path))

        concept_summaries = {}
        for concept_id, concept in concepts.items():
            # Superseded/cancelled approvals still count: projects are never
            # deleted in v1, so their delivered work stays in the history a
            # summary reports (2026-07-10 adversarial review).
            concept_project_ids = list(dict.fromkeys(
                project_id
                for approval in approvals
                if approval["campaign_concept_id"] == concept_id
                for project_id in approval["project_ids_created"]
            ))
            status_counts = {}
            function_counts = {}
            pressure_counts = {}
            published = 0
            for project_id in concept_project_ids:
                project = projects.get(project_id)
                if project is None:
                    continue
                status = project["status"]
                status_counts[status] = status_counts.get(status, 0) + 1
                if status in ("published", "analyzed"):
                    published += 1
                expression = project.get("commercial_expression")
                if expression is not None:
                    function = expression["commercial_function"]
                    function_counts[function] = (
                        function_counts.get(function, 0) + 1
                    )
                    tier = derive_commercial_pressure(
                        expression["offer_integration"],
                        expression["cta_intensity"],
                    )
                    pressure_counts[tier] = pressure_counts.get(tier, 0) + 1
            concept_summaries[concept_id] = {
                "status": concept["status"],
                "primary_commercial_function": concept[
                    "primary_commercial_function"
                ],
                "project_count": len(concept_project_ids),
                "project_status_counts": status_counts,
                "published_project_count": published,
                "commercial_function_counts": function_counts,
                "pressure_tier_counts": pressure_counts,
            }

        campaigns[campaign_id] = {
            "name": campaign["name"],
            "objective": campaign["objective"],
            "status": campaign["status"],
            "measurable_outcome": campaign["measurable_outcome"],
            "measured_progress": "unknown",
            "concept_count": len(concepts),
            "concepts": concept_summaries,
        }
    return {"workspace_path": workspace_dir, "campaigns": campaigns}


# --- workspace walker -------------------------------------------------------


def _check_opportunity_queue(workspace_dir, scope, checked, concept_ids):
    queue_path = _queue_path(workspace_dir)
    entries_dir = _entries_dir(workspace_dir)
    entry_paths = sorted(entries_dir.glob("*.json")) if entries_dir.exists() else []
    if not queue_path.exists():
        if entry_paths:
            raise ValidationError(
                f"{entries_dir} holds opportunity entries but "
                f"{queue_path} is missing; the queue manifest tracks every entry"
            )
        return {}
    queue = load_json(queue_path)
    validate_record("content-opportunity-queue", queue)
    check_creator_scope(queue, scope, queue_path)
    entries = {}
    for entry_path in entry_paths:
        entry = load_json(entry_path)
        validate_record("content-opportunity", entry)
        check_creator_scope(entry, scope, entry_path)
        if entry["content_opportunity_id"] != entry_path.stem:
            raise ValidationError(
                f"{entry_path}: filename does not match content_opportunity_id "
                f"{entry['content_opportunity_id']!r}"
            )
        for concept_id in entry.get("linked_campaign_concept_ids", []):
            if concept_id not in concept_ids:
                raise ValidationError(
                    f"content opportunity {entry_path.stem} links concept "
                    f"{concept_id!r}, which does not exist"
                )
        entries[entry["content_opportunity_id"]] = entry
        checked.append(str(entry_path.relative_to(workspace_dir)))
    ref_ids = [ref["content_opportunity_id"] for ref in queue["entry_refs"]]
    if len(set(ref_ids)) != len(ref_ids):
        raise ValidationError(
            f"{queue_path}: entry_refs list a content opportunity twice"
        )
    missing_files = sorted(set(ref_ids) - set(entries))
    if missing_files:
        raise ValidationError(
            f"{queue_path}: entry_refs name opportunities with no entry "
            f"file: {missing_files}"
        )
    untracked = sorted(set(entries) - set(ref_ids))
    if untracked:
        raise ValidationError(
            f"{queue_path}: entries exist on disk that the queue does not "
            f"track: {untracked}"
        )
    for ref in queue["entry_refs"]:
        entry_status = entries[ref["content_opportunity_id"]]["status"]
        if ref["status"] != entry_status:
            raise ValidationError(
                f"{queue_path}: entry_ref status {ref['status']!r} does not "
                f"match entry {ref['content_opportunity_id']} status "
                f"{entry_status!r}"
            )
    declared_counts = queue.get("status_counts", {})
    actual_counts = {}
    for ref in queue["entry_refs"]:
        actual_counts[ref["status"]] = actual_counts.get(ref["status"], 0) + 1
    for status, count in declared_counts.items():
        if actual_counts.get(status, 0) != count:
            raise ValidationError(
                f"{queue_path}: status_counts declares {count} {status!r} "
                f"entries, found {actual_counts.get(status, 0)}"
            )
    for status, count in actual_counts.items():
        if status not in declared_counts:
            raise ValidationError(
                f"{queue_path}: status_counts omits {count} {status!r} entries"
            )
    checked.append(str(queue_path.relative_to(workspace_dir)))
    return entries


def _workspace_project_manifests(workspace_dir):
    projects = {}
    for manifest_path in sorted(
        Path(workspace_dir).glob("projects/*/project.json")
    ):
        manifest = load_json(manifest_path)
        projects[manifest["project_id"]] = manifest
    return projects


def _check_schedule_ownership(workspace_dir, campaign_ids,
                              concepts_by_campaign, approvals_by_campaign):
    """All populated calendar-slot ownership refs must agree (ADR 0029):
    the slot's concept belongs to the slot's campaign, and the slot's
    project resolves — transitively through its concept approval when one
    exists — to the same concept and campaign."""
    schedule_path = Path(workspace_dir) / "content-schedule.json"
    if not schedule_path.exists():
        return
    schedule = load_json(schedule_path)
    concept_owners = {
        concept_id: campaign_id
        for campaign_id, concepts in concepts_by_campaign.items()
        for concept_id in concepts
    }
    approvals_by_id = {
        approval_id: approval
        for approvals in approvals_by_campaign.values()
        for approval_id, approval in approvals.items()
    }
    projects = None
    for slot in schedule.get("calendar_slots", []):
        slot_id = slot["slot_id"]
        campaign_ref = slot.get("campaign_id")
        concept_ref = slot.get("campaign_concept_id")
        project_ref = slot.get("project_id")
        if campaign_ref and campaign_ref not in campaign_ids:
            raise ValidationError(
                f"calendar slot {slot_id} names campaign {campaign_ref!r}, "
                "which does not exist"
            )
        if concept_ref:
            owner = concept_owners.get(concept_ref)
            if owner is None:
                raise ValidationError(
                    f"calendar slot {slot_id} names concept {concept_ref!r}, "
                    "which does not exist"
                )
            if campaign_ref and owner != campaign_ref:
                raise ValidationError(
                    f"calendar slot {slot_id} ownership disagrees: concept "
                    f"{concept_ref} belongs to campaign {owner}, not "
                    f"{campaign_ref}"
                )
        if project_ref:
            if projects is None:
                projects = _workspace_project_manifests(workspace_dir)
            project = projects.get(project_ref)
            if project is None:
                raise ValidationError(
                    f"calendar slot {slot_id} names project {project_ref!r}, "
                    "which does not exist"
                )
            approval_id = project.get("source_refs", {}).get(
                "concept_approval_id"
            )
            if approval_id:
                approval = approvals_by_id.get(approval_id)
                if approval is None:
                    raise ValidationError(
                        f"calendar slot {slot_id} project {project_ref} names "
                        f"concept approval {approval_id!r}, which does not exist"
                    )
                approval_concept = approval["campaign_concept_id"]
                if concept_ref and approval_concept != concept_ref:
                    raise ValidationError(
                        f"calendar slot {slot_id} ownership disagrees: project "
                        f"{project_ref} was approved under concept "
                        f"{approval_concept}, not {concept_ref}"
                    )
                approval_campaign = concept_owners.get(approval_concept)
                if campaign_ref and approval_campaign != campaign_ref:
                    raise ValidationError(
                        f"calendar slot {slot_id} ownership disagrees: project "
                        f"{project_ref} resolves to campaign "
                        f"{approval_campaign}, not {campaign_ref}"
                    )


def validate_campaign_records(workspace_path):
    """Validate the campaign hierarchy and opportunity queue at rest.

    Structural closure only — research-corpus evidence resolution and the
    approval->project closure join the promotion-gate machinery at the
    Slice 3 cutover.
    """
    workspace_dir = Path(workspace_path)
    scope = load_workspace_scope(workspace_dir)
    checked = []
    campaigns_root = workspace_dir / CAMPAIGNS_DIR
    profile = None
    conversion_asset_ids = set()
    campaign_ids = set()
    concepts_by_campaign = {}
    approvals_by_campaign = {}
    if campaigns_root.exists():
        profile = _load_creator_profile(workspace_dir)
        conversion_asset_ids = _workspace_conversion_asset_ids(workspace_dir)
        for campaign_folder in sorted(campaigns_root.iterdir()):
            if not campaign_folder.is_dir():
                raise ValidationError(
                    f"{campaign_folder}: campaigns/ holds one folder per "
                    "campaign; stray files are invalid"
                )
            campaign_path = campaign_folder / "campaign.json"
            if not campaign_path.exists():
                raise ValidationError(
                    f"{campaign_folder} has no campaign.json"
                )
            campaign = load_json(campaign_path)
            validate_record("campaign", campaign)
            check_creator_scope(campaign, scope, campaign_path)
            if campaign["campaign_id"] != campaign_folder.name:
                raise ValidationError(
                    f"{campaign_path}: folder name does not match campaign_id "
                    f"{campaign['campaign_id']!r}"
                )
            _check_campaign_profile_refs(campaign, profile, conversion_asset_ids)
            campaign_ids.add(campaign["campaign_id"])
            checked.append(str(campaign_path.relative_to(workspace_dir)))

            concepts = {}
            concepts_dir = campaign_folder / "concepts"
            for concept_path in sorted(concepts_dir.glob("*.json")) if concepts_dir.exists() else []:
                concept = load_json(concept_path)
                validate_record("campaign-concept", concept)
                check_creator_scope(concept, scope, concept_path)
                if concept["campaign_concept_id"] != concept_path.stem:
                    raise ValidationError(
                        f"{concept_path}: filename does not match "
                        f"campaign_concept_id {concept['campaign_concept_id']!r}"
                    )
                check_concept_against_campaign(concept, campaign)
                concepts[concept["campaign_concept_id"]] = concept
                checked.append(str(concept_path.relative_to(workspace_dir)))
            for concept in concepts.values():
                for related in concept.get("related_concepts", []):
                    if related["campaign_concept_id"] not in concepts:
                        raise ValidationError(
                            f"concept {concept['campaign_concept_id']} relates "
                            f"to {related['campaign_concept_id']!r}, which does "
                            f"not exist in campaign {campaign['campaign_id']}"
                        )
            concepts_by_campaign[campaign["campaign_id"]] = concepts

            approvals = {}
            approvals_dir = campaign_folder / "approvals"
            for approval_path in sorted(approvals_dir.glob("*.json")) if approvals_dir.exists() else []:
                approval = load_json(approval_path)
                validate_record("concept-approval", approval)
                check_creator_scope(approval, scope, approval_path)
                if approval["concept_approval_id"] != approval_path.stem:
                    raise ValidationError(
                        f"{approval_path}: filename does not match "
                        f"concept_approval_id {approval['concept_approval_id']!r}"
                    )
                if approval["campaign_concept_id"] not in concepts:
                    raise ValidationError(
                        f"approval {approval['concept_approval_id']} names "
                        f"concept {approval['campaign_concept_id']!r}, which "
                        f"does not exist in campaign {campaign['campaign_id']}"
                    )
                approvals[approval["concept_approval_id"]] = approval
                checked.append(str(approval_path.relative_to(workspace_dir)))
            approvals_by_campaign[campaign["campaign_id"]] = approvals

    all_concept_ids = set()
    for concepts in concepts_by_campaign.values():
        all_concept_ids.update(concepts)
    for concepts in concepts_by_campaign.values():
        for concept in concepts.values():
            source_id = concept.get("source_content_opportunity_id")
            if source_id and source_id not in _existing_opportunity_ids(workspace_dir):
                raise ValidationError(
                    f"concept {concept['campaign_concept_id']} names source "
                    f"opportunity {source_id!r}, which does not exist"
                )

    _check_opportunity_queue(workspace_dir, scope, checked, all_concept_ids)
    _check_schedule_ownership(
        workspace_dir, campaign_ids, concepts_by_campaign, approvals_by_campaign
    )
    return {"workspace_path": workspace_dir, "checked_paths": checked}
