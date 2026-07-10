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
)
from influencer_os.creator_scope import check_creator_scope, load_workspace_scope
from influencer_os.json_io import write_json_atomic
from influencer_os.validation import ValidationError, load_json, validate_record

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
CONCEPT_SEED_OPTIONAL = (
    "supporting_commercial_functions",
    "source_content_opportunity_id",
    "evidence_refs",
    "related_concepts",
    "notes",
    "campaign_concept_id",
)

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
    return {"campaign_path": campaign_path, "campaign_id": campaign_id}


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
    return {"campaign_path": campaign_path, "campaign_id": campaign_id}


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
    When the seed assigns a Content Opportunity, evidence refs are copied
    from the opportunity (never re-authored)."""
    workspace_dir = Path(creator_workspace)
    seed = load_seed(seed)
    check_seed_fields(
        seed, CONCEPT_SEED_REQUIRED, CONCEPT_SEED_OPTIONAL, "campaign-concept"
    )
    workspace_manifest = load_workspace_manifest(workspace_dir)
    creator_profile_id = workspace_manifest["creator_profile_id"]
    campaign = load_campaign(workspace_dir, seed["campaign_id"])

    source_opportunity_id = seed.get("source_content_opportunity_id")
    if source_opportunity_id is not None:
        if "evidence_refs" in seed:
            raise ValidationError(
                "campaign-concept seed supplies evidence_refs alongside "
                "source_content_opportunity_id; evidence is copied from the "
                "assigned opportunity (docs/record-constructors.md)"
            )
        opportunity = _load_opportunity(workspace_dir, source_opportunity_id)
        evidence_refs = deepcopy(opportunity["evidence_refs"])
    else:
        evidence_refs = deepcopy(seed.get("evidence_refs", []))

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
        "evidence_refs": evidence_refs,
        "created_on": today,
        "updated_on": today,
    }
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
    concepts_dir = campaign_dir(workspace_dir, seed["campaign_id"]) / "concepts"
    concepts_dir.mkdir(parents=True, exist_ok=True)
    concept_path = concepts_dir / f"{concept_id}.json"
    write_json_atomic(concept_path, concept)
    return {"concept_path": concept_path, "campaign_concept_id": concept_id}


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
    return {
        "entry_path": entry_path,
        "queue_path": queue_path,
        "content_opportunity_id": opportunity_id,
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
    return {"workspace_path": workspace_dir, "checked_paths": checked}
