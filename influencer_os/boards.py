"""Content Board projection: rebuild and agreement validation (ADR 0020,
slice 4 batch C).

The board is a rebuildable projection over canonical records: opportunity queue
entries are parent cards, projects are child cards (linked through their
locked Concept Approval), and card ids derive deterministically from source
record ids (``card_<source_record_id>``). ``columns`` and ``manual_order``
are preserved projection metadata — a rebuild refreshes every card from
canonical records but never clobbers the user's board arrangement.
Canonical records store no board state.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from influencer_os.creator_scope import check_creator_scope, load_workspace_scope
from influencer_os.json_io import write_json_atomic
from influencer_os.research import (
    check_project_warning_pairing,
    check_project_warning_target_refs,
)
from influencer_os.validation import (
    ValidationError,
    load_json,
    validate_jsonl_file,
    validate_record,
)


# Lower rank sorts first on a card's badge list.
SEVERITY_RANK = {"urgent": 0, "important": 1, "info": 2}

# Default columns follow the workflow doc's recommended board progression.
# Columns are projection metadata: rebuilds preserve an existing board's
# columns, so a UI may regroup statuses without fighting the rebuild.
DEFAULT_BOARD_COLUMNS = tuple(
    {"column_id": f"column_{status}", "title": title}
    for status, title in (
        ("new", "New"),
        ("reviewed", "Reviewed"),
        ("shortlisted", "Shortlisted"),
        ("needs_more_research", "Needs More Research"),
        ("assigned", "Assigned"),
        ("created", "Created"),
        ("planning", "Planning"),
        ("ready_for_generation", "Ready For Generation"),
        ("generated", "Generated"),
        ("packaged", "Packaged"),
        ("published", "Published"),
        ("analyzed", "Analyzed"),
        ("archived", "Archived"),
        ("rejected", "Rejected"),
        ("expired", "Expired"),
    )
)

CARD_FIELDS = (
    "card_type",
    "status",
    "source_record_type",
    "source_record_id",
    "warning_badges",
    "child_card_ids",
    "parent_card_id",
)


def board_path_for(workspace_dir):
    return Path(workspace_dir) / "boards" / "content-board.json"


def board_id_for(scope):
    prefix = "creator_"
    profile_id = scope["creator_profile_id"]
    suffix = profile_id[len(prefix):] if profile_id.startswith(prefix) else profile_id
    return f"content_board_{suffix}"


def _load_validated(path, schema_name):
    record = load_json(path)
    try:
        validate_record(schema_name, record)
    except ValidationError as exc:
        raise ValidationError(f"{path}: {exc}") from None
    return record


def derive_board_cards(workspace_dir):
    """Derive the full card list from canonical records: content
    opportunities, projects (parent resolution through the approval ->
    concept -> source opportunity chain), and active warnings (badges)."""
    workspace_dir = Path(workspace_dir)
    research_dir = workspace_dir / "research"

    entries = {}
    entries_dir = research_dir / "content-opportunity-queue" / "entries"
    if entries_dir.exists():
        for entry_path in sorted(entries_dir.glob("*.json")):
            record = _load_validated(entry_path, "content-opportunity")
            entries[record["content_opportunity_id"]] = record

    approvals = {}
    for approval_path in sorted(
        workspace_dir.glob("campaigns/*/approvals/*.json")
    ):
        record = _load_validated(approval_path, "concept-approval")
        approvals[record["concept_approval_id"]] = record

    concepts = {}
    for concept_path in sorted(
        workspace_dir.glob("campaigns/*/concepts/*.json")
    ):
        record = _load_validated(concept_path, "campaign-concept")
        concepts[record["campaign_concept_id"]] = record

    projects = {}
    projects_dir = workspace_dir / "projects"
    if projects_dir.exists():
        for manifest_path in sorted(projects_dir.glob("*/project.json")):
            record = _load_validated(manifest_path, "project")
            projects[record["project_id"]] = record

    # A warning badges exactly the card it targets: approved-work warnings
    # (project_id present) badge the project card; queue-level warnings badge
    # the opportunity card. Resolved warnings do not badge.
    opportunity_badges = {}
    project_badges = {}
    warnings_path = workspace_dir / "system" / "project-warnings.jsonl"
    if warnings_path.exists():
        def warning_check(record):
            check_project_warning_pairing(record)
            check_project_warning_target_refs(record, workspace_dir)

        warning_records = validate_jsonl_file(
            "project-warning", warnings_path, record_check=warning_check,
        )
        for warning in warning_records:
            if warning.get("resolved_status") == "resolved":
                continue
            if "project_id" in warning:
                target = project_badges.setdefault(warning["project_id"], set())
            elif "content_opportunity_id" in warning:
                target = opportunity_badges.setdefault(
                    warning["content_opportunity_id"], set()
                )
            else:
                continue
            target.add(warning["severity"])

    def badge_list(severities):
        return sorted(severities or (), key=SEVERITY_RANK.__getitem__)

    # Pillar -> Campaign -> Concept -> Project hierarchy (ADR 0029): pillar
    # cards come from the creator profile, campaigns hang from their primary
    # pillar, concepts from their campaign, and projects resolve their parent
    # concept through the locked approval. Unassigned opportunities stay
    # top-level queue cards.
    campaigns = {}
    for campaign_path in sorted(workspace_dir.glob("campaigns/*/campaign.json")):
        record = _load_validated(campaign_path, "campaign")
        campaigns[record["campaign_id"]] = record

    pillars = {}
    profile_path = workspace_dir / "creator-profile.json"
    if profile_path.exists():
        profile = _load_validated(profile_path, "creator-profile")
        for pillar in profile["content_pillars"]:
            pillars[pillar["pillar_id"]] = pillar

    project_parents = {}
    for project_id, project in sorted(projects.items()):
        approval_id = project["source_refs"]["concept_approval_id"]
        approval = approvals.get(approval_id)
        if approval is None:
            raise ValidationError(
                f"project {project_id} names concept approval {approval_id!r} "
                "with no approval record; cannot resolve its parent card"
            )
        concept_id = approval["campaign_concept_id"]
        if concept_id not in concepts:
            raise ValidationError(
                f"project {project_id} resolves to concept "
                f"{concept_id!r} with no concept record; "
                "cannot build its parent card"
            )
        project_parents[project_id] = concept_id

    concept_children = {}
    for project_id, concept_id in sorted(project_parents.items()):
        concept_children.setdefault(concept_id, []).append(project_id)
    campaign_children = {}
    for concept_id, concept in sorted(concepts.items()):
        campaign_id = concept["campaign_id"]
        if campaign_id not in campaigns:
            raise ValidationError(
                f"concept {concept_id} names campaign {campaign_id!r} with "
                "no campaign record; cannot build its parent card"
            )
        campaign_children.setdefault(campaign_id, []).append(concept_id)
    pillar_children = {}
    for campaign_id, campaign in sorted(campaigns.items()):
        pillar_id = campaign["primary_content_pillar_id"]
        if pillar_id not in pillars:
            raise ValidationError(
                f"campaign {campaign_id} names pillar {pillar_id!r} that is "
                "not on the creator profile; cannot build its parent card"
            )
        pillar_children.setdefault(pillar_id, []).append(campaign_id)

    def card(record_id, card_type, source_record_type, status,
             child_ids=(), parent_id=None, badges=None):
        record_card = {
            "content_card_id": f"card_{record_id}",
            "card_type": card_type,
            "status": status,
            "source_record_type": source_record_type,
            "source_record_id": record_id,
            "warning_badges": badge_list(badges),
            "child_card_ids": [f"card_{child}" for child in child_ids],
        }
        if parent_id is not None:
            record_card["parent_card_id"] = f"card_{parent_id}"
        return record_card

    cards = []
    # Pillars appear only when campaign work exists under them; a pillar
    # with no campaigns is profile state, not board state.
    for pillar_id in sorted(pillar_children):
        cards.append(card(
            pillar_id, "pillar", "content_pillar", "active",
            child_ids=sorted(pillar_children[pillar_id]),
        ))
        for campaign_id in sorted(pillar_children[pillar_id]):
            campaign = campaigns[campaign_id]
            cards.append(card(
                campaign_id, "campaign", "campaign", campaign["status"],
                child_ids=sorted(campaign_children.get(campaign_id, ())),
                parent_id=pillar_id,
            ))
            for concept_id in sorted(campaign_children.get(campaign_id, ())):
                concept = concepts[concept_id]
                cards.append(card(
                    concept_id, "concept", "campaign_concept",
                    concept["status"],
                    child_ids=sorted(concept_children.get(concept_id, ())),
                    parent_id=campaign_id,
                ))
                for project_id in sorted(
                    concept_children.get(concept_id, ())
                ):
                    cards.append(card(
                        project_id, "project", "project",
                        projects[project_id]["status"],
                        parent_id=concept_id,
                        badges=project_badges.get(project_id),
                    ))
    for entry_id, entry in sorted(entries.items()):
        cards.append(card(
            entry_id, "opportunity", "content_opportunity", entry["status"],
            badges=opportunity_badges.get(entry_id),
        ))
    return cards


def rebuild_board(workspace_path):
    """Rebuild ``boards/content-board.json`` from canonical records. Cards
    are fully derived; ``columns`` and ``manual_order`` survive from the
    existing board (new cards append in canonical order, stale ids drop)."""
    workspace_dir = Path(workspace_path)
    scope = load_workspace_scope(workspace_dir)
    cards = derive_board_cards(workspace_dir)
    card_ids = [card["content_card_id"] for card in cards]
    board_path = board_path_for(workspace_dir)

    columns = [dict(column) for column in DEFAULT_BOARD_COLUMNS]
    manual_order = list(card_ids)
    if board_path.exists():
        existing = _load_validated(board_path, "content-board")
        columns = existing["columns"]
        surviving = [
            card_id
            for card_id in dict.fromkeys(existing["manual_order"])
            if card_id in set(card_ids)
        ]
        manual_order = surviving + [
            card_id for card_id in card_ids if card_id not in set(surviving)
        ]

    board = {
        "content_board_id": board_id_for(scope),
        "creator_profile_id": scope["creator_profile_id"],
        "updated_on": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "columns": columns,
        "cards": cards,
        "manual_order": manual_order,
    }
    try:
        validate_record("content-board", board)
    except ValidationError as exc:
        raise ValidationError(f"rebuilt board is invalid: {exc}") from None
    board_path.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(board_path, board)
    return {
        "board_path": board_path,
        "card_count": len(cards),
        "opportunity_cards": sum(1 for card in cards if card["card_type"] == "opportunity"),
        "project_cards": sum(1 for card in cards if card["card_type"] == "project"),
    }


def validate_board(workspace_path):
    """The board must agree with canonical records: same card set, same card
    contents, and a ``manual_order`` listing every card exactly once. Only
    ``columns``, ``manual_order`` ordering, and ``updated_on`` are free."""
    workspace_dir = Path(workspace_path)
    board_path = board_path_for(workspace_dir)
    if not board_path.exists():
        raise FileNotFoundError(
            f"Missing content board: {board_path} (run rebuild-board)"
        )
    scope = load_workspace_scope(workspace_dir)
    board = _load_validated(board_path, "content-board")
    check_creator_scope(board, scope, board_path)

    expected_board_id = board_id_for(scope)
    if board["content_board_id"] != expected_board_id:
        raise ValidationError(
            f"{board_path}: content_board_id {board['content_board_id']!r} "
            f"does not match the derived id {expected_board_id!r}"
        )

    expected = {card["content_card_id"]: card for card in derive_board_cards(workspace_dir)}
    actual = {card["content_card_id"]: card for card in board["cards"]}
    if len(actual) != len(board["cards"]):
        raise ValidationError(f"{board_path}: duplicate content_card_id values")
    missing = sorted(set(expected) - set(actual))
    if missing:
        raise ValidationError(
            f"{board_path}: board is stale — missing cards {missing} "
            "(run rebuild-board)"
        )
    unexpected = sorted(set(actual) - set(expected))
    if unexpected:
        raise ValidationError(
            f"{board_path}: board is stale — cards {unexpected} have no "
            "canonical source record (run rebuild-board)"
        )
    for card_id, expected_card in expected.items():
        actual_card = actual[card_id]
        for field in CARD_FIELDS:
            if actual_card.get(field) != expected_card.get(field):
                raise ValidationError(
                    f"{board_path}: card {card_id} field {field} is "
                    f"{actual_card.get(field)!r}, canonical records derive "
                    f"{expected_card.get(field)!r} (run rebuild-board)"
                )

    manual_order = board["manual_order"]
    if len(set(manual_order)) != len(manual_order):
        raise ValidationError(f"{board_path}: manual_order has duplicate card ids")
    if set(manual_order) != set(actual):
        raise ValidationError(
            f"{board_path}: manual_order must list every card exactly once"
        )

    return {
        "workspace_path": workspace_dir,
        "board_path": board_path,
        "card_count": len(actual),
    }
