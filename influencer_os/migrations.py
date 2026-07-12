"""Explicit migrations for durable creator workspace records."""

import datetime
import json
import shutil
from copy import deepcopy
from pathlib import Path

from influencer_os.json_io import write_json_atomic
from influencer_os.reference_assets import SETUP_IMAGE_ASSET_TYPES
from influencer_os.validation import ValidationError, load_json, validate_record


def migrate_visual_foundation(workspace_path):
    """Upgrade legacy avatar/visual-plan records to the required foundation."""
    from influencer_os.brand_boards import rebuild_brand_board

    workspace_dir = Path(workspace_path)
    board_path = (
        workspace_dir / "references" / "brand" / "personal-brand-board.json"
    )
    plan_path = workspace_dir / "references" / "visual-continuity-plan.json"
    library_path = workspace_dir / "references" / "reference-library.json"
    profile_path = workspace_dir / "creator-profile.json"

    board = deepcopy(load_json(board_path))
    plan = deepcopy(load_json(plan_path))
    library = load_json(library_path)
    profile = load_json(profile_path)
    validate_record("reference-library", library)
    assets_by_id = {asset["asset_id"]: asset for asset in library["assets"]}

    if "avatar_image" in board:
        if "avatar_asset_id" in board:
            raise ValidationError(
                "legacy brand board carries both avatar_image and avatar_asset_id"
            )
        legacy_path = board.pop("avatar_image")
        candidates = [
            asset["asset_id"]
            for asset in library["assets"]
            if asset["path"] == legacy_path
        ]
        if not candidates:
            candidates = [
                asset_id
                for asset_id in profile["reference_refs"].get(
                    "primary_character_asset_ids", []
                )
                if asset_id in assets_by_id
            ]
        if len(candidates) != 1:
            raise ValidationError(
                "cannot migrate avatar_image unambiguously; expected one matching "
                "Reference Asset or one primary character asset"
            )
        board["avatar_asset_id"] = candidates[0]

    if "setup_reference_generation" not in plan:
        review = plan["selection_review"]
        if review["status"] == "approved":
            avatar_id = board.get("avatar_asset_id")
            asset_ids = [
                asset["asset_id"]
                for asset in library["assets"]
                if asset["asset_type"] in SETUP_IMAGE_ASSET_TYPES
                and asset["asset_status"] in {"planned", "prompted"}
                and asset.get("prompt_path")
                and asset["asset_id"] != avatar_id
            ]
            plan["setup_reference_generation"] = {
                "status": "authorized",
                "asset_ids": asset_ids,
                "max_calls": len(asset_ids),
                "authorized_on": review["decided_on"],
                "authorized_by": "user",
                "notice": (
                    "Migrated authorization: one initial generation call per "
                    "listed creator-setup reference asset was authorized by the "
                    "approved Visual Continuity Plan."
                ),
            }
        else:
            plan["setup_reference_generation"] = {
                "status": "not_authorized",
                "asset_ids": [],
                "max_calls": 0,
                "authorized_on": None,
                "authorized_by": None,
                "notice": "Setup reference generation has not been authorized.",
            }

    validate_record("personal-brand-board", board)
    validate_record("visual-continuity-plan", plan)
    changed = []
    if load_json(board_path) != board:
        changed.append(board_path)
    if load_json(plan_path) != plan:
        changed.append(plan_path)
    for path, record in ((board_path, board), (plan_path, plan)):
        if path in changed:
            write_json_atomic(path, record)
    if board_path in changed:
        result = rebuild_brand_board(workspace_dir)
        changed.append(result["board_path"])
    return {
        "workspace_path": workspace_dir,
        "changed_paths": [path.relative_to(workspace_dir) for path in changed],
    }


def migrate_content_series(workspace_path):
    """Rename legacy strategy campaigns to Content Series (ADR 0031).

    `content_strategy.content_campaigns` records describe recurring
    anchor-and-derivative publishing patterns, not the operational Campaign
    boundary, so they become `content_series` with `content_series_*` ids;
    calendar-slot `content_campaign_id` refs follow the same mechanical
    rename. All records are prepared and validated before any write."""
    workspace_dir = Path(workspace_path)
    strategy_path = workspace_dir / "content-strategy.json"
    if not strategy_path.exists():
        raise FileNotFoundError(f"Missing content strategy: {strategy_path}")

    def renamed_series_id(campaign_id):
        return "content_series_" + campaign_id.removeprefix("campaign_")

    strategy = deepcopy(load_json(strategy_path))
    if "content_campaigns" in strategy and "content_series" in strategy:
        raise ValidationError(
            f"{strategy_path} carries both content_campaigns and "
            "content_series; resolve that conflict before migration"
        )
    if "content_campaigns" in strategy:
        series_list = []
        for legacy in strategy.pop("content_campaigns"):
            legacy = deepcopy(legacy)
            series = {"content_series_id": renamed_series_id(legacy.pop("campaign_id"))}
            series.update(legacy)
            series_list.append(series)
        strategy["content_series"] = series_list
    strategy.setdefault("content_series", [])

    schedule_path = workspace_dir / "content-schedule.json"
    schedule = None
    if schedule_path.exists():
        schedule = deepcopy(load_json(schedule_path))
        for slot in schedule.get("calendar_slots", []):
            if "content_campaign_id" in slot:
                slot["content_series_id"] = renamed_series_id(
                    slot.pop("content_campaign_id")
                )

    validate_record("content-strategy", strategy)
    if schedule is not None:
        validate_record("creator-content-schedule", schedule)

    pending = [(strategy_path, strategy)]
    if schedule is not None:
        pending.append((schedule_path, schedule))
    changed = [path for path, record in pending if load_json(path) != record]
    for path, record in pending:
        if path in changed:
            write_json_atomic(path, record)
    return {
        "workspace_path": workspace_dir,
        "changed_paths": [path.relative_to(workspace_dir) for path in changed],
    }


def migrate_campaign_model(workspace_path):
    """Mechanically convert a legacy idea-queue workspace to the campaign
    model (ADR 0031): unassigned queue entries become Content Opportunities,
    the queue manifest is rebuilt, run outputs and slot research selections
    rename their fields, and legacy directories are removed.

    Migration never invents Campaign ownership: any idea promotion, promoted
    entry, or promotion-locked project fails the preflight with no writes —
    durable promoted records need an explicit human mapping to a Campaign
    and Concept, and disposable fixture workspaces are rebuilt instead.
    """
    workspace_dir = Path(workspace_path)
    legacy_queue_dir = workspace_dir / "research" / "idea-queue"
    promotions_dir = workspace_dir / "research" / "idea-promotions"

    blockers = []
    if promotions_dir.exists() and any(promotions_dir.glob("*.json")):
        blockers.append(
            "idea promotions exist; promoted work needs an explicit "
            "Campaign/Concept mapping (rebuild fixture workspaces instead)"
        )
    entries = {}
    entries_dir = legacy_queue_dir / "entries"
    if entries_dir.exists():
        for entry_path in sorted(entries_dir.glob("*.json")):
            entry = load_json(entry_path)
            entries[entry["idea_queue_entry_id"]] = entry
            if entry.get("status") == "promoted":
                blockers.append(
                    f"queue entry {entry['idea_queue_entry_id']} is promoted; "
                    "promoted work needs an explicit Campaign/Concept mapping"
                )
    for manifest_path in sorted(workspace_dir.glob("projects/*/project.json")):
        project = load_json(manifest_path)
        if "idea_promotion_id" in project.get("source_refs", {}):
            blockers.append(
                f"project {project.get('project_id')} locks a legacy idea "
                "promotion; promoted work needs an explicit mapping"
            )
    warnings_path = workspace_dir / "system" / "project-warnings.jsonl"
    legacy_warnings = []
    if warnings_path.exists():
        for line in warnings_path.read_text().splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if "idea_promotion_id" in record or "project_id" in record:
                blockers.append(
                    f"project warning {record.get('project_warning_id')} "
                    "targets promoted work; promoted work needs an explicit "
                    "mapping"
                )
            legacy_warnings.append(record)
    if blockers:
        raise ValidationError(
            "campaign-model migration preflight failed (no records were "
            "written): " + "; ".join(blockers)
        )

    def renamed_entry_id(entry_id):
        return "content_opportunity_" + entry_id.removeprefix("idea_queue_entry_")

    opportunities = {}
    for entry_id, entry in entries.items():
        record = deepcopy(entry)
        record.pop("idea_queue_entry_id")
        record.pop("linked_idea_promotion_ids", None)
        record.pop("linked_project_ids", None)
        if "approval_intent_note" in record:
            record["assignment_intent_note"] = record.pop("approval_intent_note")
        opportunity = {"content_opportunity_id": renamed_entry_id(entry_id)}
        opportunity.update(record)
        validate_record("content-opportunity", opportunity)
        opportunities[opportunity["content_opportunity_id"]] = opportunity

    queue = None
    if entries or (legacy_queue_dir / "queue.json").exists():
        creator_profile_id = None
        legacy_manifest = None
        if (legacy_queue_dir / "queue.json").exists():
            legacy_manifest = load_json(legacy_queue_dir / "queue.json")
            creator_profile_id = legacy_manifest["creator_profile_id"]
        elif opportunities:
            creator_profile_id = next(iter(opportunities.values()))[
                "creator_profile_id"
            ]
        if creator_profile_id is not None:
            suffix = creator_profile_id.removeprefix("creator_")
            entry_refs = [
                {
                    "content_opportunity_id": opportunity_id,
                    "status": opportunity["status"],
                }
                for opportunity_id, opportunity in sorted(opportunities.items())
            ]
            counts = {}
            for ref in entry_refs:
                counts[ref["status"]] = counts.get(ref["status"], 0) + 1
            queue = {
                "content_opportunity_queue_id": (
                    f"content_opportunity_queue_{suffix}"
                ),
                "creator_profile_id": creator_profile_id,
                "updated_on": (
                    legacy_manifest["updated_on"]
                    if legacy_manifest is not None
                    else datetime.date.today().isoformat()
                ),
                "entry_refs": entry_refs,
                "status_counts": counts,
            }
            if legacy_manifest is not None and "grouping_notes" in legacy_manifest:
                queue["grouping_notes"] = legacy_manifest["grouping_notes"]
            validate_record("content-opportunity-queue", queue)

    # Field renames in research runs, source-yield ledgers, and the schedule.
    renamed_files = []
    for run_path in sorted(workspace_dir.glob("research/runs/*/research-run.json")):
        run = deepcopy(load_json(run_path))
        outputs = run.get("outputs", {})
        if "idea_queue_entry_ids" in outputs:
            outputs["content_opportunity_ids"] = [
                renamed_entry_id(entry_id)
                for entry_id in outputs.pop("idea_queue_entry_ids")
            ]
            validate_record("research-run", run)
            renamed_files.append((run_path, run))
    for yield_path in sorted(
        workspace_dir.glob("research/runs/*/source-yield.jsonl")
    ):
        lines = yield_path.read_text().splitlines()
        changed = False
        rewritten = []
        for line in lines:
            if not line.strip():
                continue
            record = json.loads(line)
            if "idea_queue_entry_ids" in record:
                record["content_opportunity_ids"] = [
                    renamed_entry_id(entry_id)
                    for entry_id in record.pop("idea_queue_entry_ids")
                ]
                changed = True
            validate_record("research-source-yield", record)
            rewritten.append(record)
        if changed:
            renamed_files.append((yield_path, rewritten))

    schedule = None
    schedule_path = workspace_dir / "content-schedule.json"
    if schedule_path.exists():
        schedule = deepcopy(load_json(schedule_path))
        schedule_changed = False
        for slot in schedule.get("calendar_slots", []):
            state = slot.get("research_state", {})
            if "selected_idea_queue_entry_id" in state:
                state["selected_content_opportunity_id"] = renamed_entry_id(
                    state.pop("selected_idea_queue_entry_id")
                )
                schedule_changed = True
        if schedule_changed:
            validate_record("creator-content-schedule", schedule)
        else:
            schedule = None

    # All records validated; write, then remove the legacy directories.
    changed_paths = []
    queue_dir = workspace_dir / "research" / "content-opportunity-queue"
    if opportunities:
        (queue_dir / "entries").mkdir(parents=True, exist_ok=True)
        for opportunity_id, opportunity in sorted(opportunities.items()):
            path = queue_dir / "entries" / f"{opportunity_id}.json"
            write_json_atomic(path, opportunity)
            changed_paths.append(path)
    if queue is not None:
        queue_dir.mkdir(parents=True, exist_ok=True)
        path = queue_dir / "queue.json"
        write_json_atomic(path, queue)
        changed_paths.append(path)
    for path, record in renamed_files:
        if str(path).endswith(".jsonl"):
            path.write_text(
                "".join(json.dumps(row) + "\n" for row in record)
            )
        else:
            write_json_atomic(path, record)
        changed_paths.append(path)
    if schedule is not None:
        write_json_atomic(schedule_path, schedule)
        changed_paths.append(schedule_path)
    warnings_changed = False
    rewritten_warnings = []
    for record in legacy_warnings:
        if "idea_queue_entry_id" in record:
            record = dict(record)
            record["content_opportunity_id"] = renamed_entry_id(
                record.pop("idea_queue_entry_id")
            )
            warnings_changed = True
        validate_record("project-warning", record)
        rewritten_warnings.append(record)
    if warnings_changed:
        warnings_path.write_text(
            "".join(json.dumps(row) + "\n" for row in rewritten_warnings)
        )
        changed_paths.append(warnings_path)
    if legacy_queue_dir.exists():
        shutil.rmtree(legacy_queue_dir)
        changed_paths.append(legacy_queue_dir)
    if promotions_dir.exists():
        shutil.rmtree(promotions_dir)
        changed_paths.append(promotions_dir)

    # Projections are rebuildable derivations; refresh them so validate all
    # passes immediately after migration (a rebuild fault must not fail the
    # completed migration).
    from influencer_os.boards import rebuild_board
    from influencer_os.recall_index import rebuild_index

    for rebuild in (rebuild_board, rebuild_index):
        try:
            rebuild(workspace_dir)
        except (ValidationError, ValueError, FileNotFoundError):
            pass

    return {
        "workspace_path": workspace_dir,
        "changed_paths": [
            path.relative_to(workspace_dir) for path in changed_paths
        ],
    }
