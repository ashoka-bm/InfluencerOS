"""Explicit migrations for durable creator workspace records."""

from copy import deepcopy
from pathlib import Path

from influencer_os.calendars import schedule_research_state_errors
from influencer_os.json_io import write_json_atomic
from influencer_os.validation import ValidationError, load_json, validate_record


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


def migrate_slot_research(workspace_path):
    """Backfill slot-first research provenance without inventing weak links.

    A filled legacy slot is migrated only when one active promotion identifies
    its selected queue entry and at least one shared evidence run can be tied
    to the slot. All records are prepared and validated before any write.
    """
    workspace_dir = Path(workspace_path)
    schedule_path = workspace_dir / "content-schedule.json"
    if not schedule_path.exists():
        raise FileNotFoundError(f"Missing content schedule: {schedule_path}")

    schedule = deepcopy(load_json(schedule_path))
    runs = {}
    plans = {}
    inferable_run_ids = set()
    runs_dir = workspace_dir / "research" / "runs"
    if runs_dir.exists():
        for run_path in sorted(runs_dir.glob("*/research-run.json")):
            run = deepcopy(load_json(run_path))
            run_id = run["research_run_id"]
            plan_path = run_path.with_name("search-plan.json")
            plan = deepcopy(load_json(plan_path)) if plan_path.exists() else None
            run_has_slots = "schedule_slot_ids" in run
            plan_has_slots = plan is None or "schedule_slot_ids" in plan
            if not run_has_slots and not plan_has_slots:
                inferable_run_ids.add(run_id)
            elif not run_has_slots:
                run["schedule_slot_ids"] = list(plan["schedule_slot_ids"])
            elif plan is not None and not plan_has_slots:
                plan["schedule_slot_ids"] = list(run["schedule_slot_ids"])
            elif plan is not None and plan["schedule_slot_ids"] != run["schedule_slot_ids"]:
                raise ValidationError(
                    f"research run {run_id} and search plan have different "
                    "schedule_slot_ids; resolve that conflict before migration"
                )
            runs[run_id] = (run_path, run)
            if plan is not None:
                plans[run_id] = (plan_path, plan)

    entries = {}
    entries_dir = workspace_dir / "research" / "idea-queue" / "entries"
    if entries_dir.exists():
        for entry_path in sorted(entries_dir.glob("*.json")):
            entry = load_json(entry_path)
            entries[entry["idea_queue_entry_id"]] = entry

    active_promotions = []
    promotions_dir = workspace_dir / "research" / "idea-promotions"
    if promotions_dir.exists():
        for promotion_path in sorted(promotions_dir.glob("*.json")):
            promotion = load_json(promotion_path)
            if promotion["promotion_status"] == "active":
                active_promotions.append(promotion)

    def focus_run_on_slot(run_id, slot_id):
        run_pair = runs.get(run_id)
        if run_pair is None:
            return None
        run = run_pair[1]
        if run.get("mode") != "scheduled_needs" or run.get("run_status") == "failed":
            return None
        if run_id in inferable_run_ids:
            run.setdefault("schedule_slot_ids", [])
            if slot_id not in run["schedule_slot_ids"]:
                run["schedule_slot_ids"].append(slot_id)
            plan_pair = plans.get(run_id)
            if plan_pair is not None:
                plan_pair[1].setdefault("schedule_slot_ids", [])
                if slot_id not in plan_pair[1]["schedule_slot_ids"]:
                    plan_pair[1]["schedule_slot_ids"].append(slot_id)
        if slot_id not in run.get("schedule_slot_ids", []):
            return None
        return run

    for slot in schedule.get("calendar_slots", []):
        if "research_state" in slot:
            continue
        slot_id = slot["slot_id"]
        if slot["status"] != "filled":
            slot["research_state"] = {
                "status": "unresearched",
                "research_run_ids": [],
            }
            continue

        claimants = [
            promotion
            for promotion in active_promotions
            if slot_id in promotion.get("schedule_slot_ids", [])
        ]
        if len(claimants) != 1:
            raise ValidationError(
                f"filled legacy slot {slot_id} needs exactly one active promotion "
                f"for safe migration; found {len(claimants)}"
            )
        promotion = claimants[0]
        entry_id = promotion["idea_queue_entry_id"]
        entry = entries.get(entry_id)
        if entry is None:
            raise ValidationError(
                f"filled legacy slot {slot_id} promotion selects missing entry {entry_id}"
            )
        promotion_run_ids = {
            ref["research_run_id"] for ref in promotion["evidence_refs"]
        }
        entry_run_ids = {ref["research_run_id"] for ref in entry["evidence_refs"]}
        candidate_run_ids = sorted(promotion_run_ids.intersection(entry_run_ids))
        focused_run_ids = []
        for run_id in candidate_run_ids:
            if focus_run_on_slot(run_id, slot_id) is not None:
                focused_run_ids.append(run_id)
        if not focused_run_ids:
            raise ValidationError(
                f"filled legacy slot {slot_id} has no shared nonfailed "
                "scheduled_needs evidence run that can be tied to the slot"
            )
        slot["research_state"] = {
            "status": "selected",
            "research_run_ids": focused_run_ids,
            "selected_idea_queue_entry_id": entry_id,
        }

    for slot in schedule.get("calendar_slots", []):
        state = slot["research_state"]
        if state["status"] not in {"candidates_ready", "selected"}:
            continue
        slot_id = slot["slot_id"]
        for run_id in state["research_run_ids"]:
            if focus_run_on_slot(run_id, slot_id) is None:
                raise ValidationError(
                    f"calendar slot {slot_id} research run {run_id} cannot be "
                    "migrated as focused scheduled_needs provenance"
                )
        if state["status"] == "selected":
            entry_id = state["selected_idea_queue_entry_id"]
            entry = entries.get(entry_id)
            if entry is None:
                raise ValidationError(
                    f"calendar slot {slot_id} selects missing queue entry {entry_id}"
                )
            entry_run_ids = {
                ref["research_run_id"] for ref in entry["evidence_refs"]
            }
            if not entry_run_ids.intersection(state["research_run_ids"]):
                raise ValidationError(
                    f"calendar slot {slot_id} selected entry {entry_id} has no "
                    "evidence from the slot's research runs"
                )

    for run_id, (_run_path, run) in runs.items():
        run.setdefault("schedule_slot_ids", [])
        if run_id in plans:
            plans[run_id][1].setdefault(
                "schedule_slot_ids", list(run["schedule_slot_ids"])
            )

    completed_run_ids = sorted(
        run_id
        for run_id, (_path, run) in runs.items()
        if run.get("run_status") != "failed"
    )
    schedule.setdefault(
        "content_strategy_id",
        f"content_strategy_{schedule['creator_slug'].replace('-', '_')}",
    )
    schedule.setdefault(
        "research_basis",
        {
            "status": (
                "research_informed" if completed_run_ids else "strategy_scaffold"
            ),
            "research_run_ids": completed_run_ids,
        },
    )

    validate_record("creator-content-schedule", schedule)
    state_errors = schedule_research_state_errors(schedule)
    if state_errors:
        raise ValidationError("; ".join(state_errors))
    for _run_id, (_path, run) in runs.items():
        validate_record("research-run", run)
    for _run_id, (_path, plan) in plans.items():
        validate_record("research-search-plan", plan)

    pending = [(schedule_path, schedule)]
    pending.extend((path, run) for path, run in runs.values())
    pending.extend((path, plan) for path, plan in plans.values())
    changed = []
    for path, record in pending:
        if load_json(path) != record:
            changed.append(path)
    for path, record in pending:
        if path in changed:
            write_json_atomic(path, record)

    return {
        "workspace_path": workspace_dir,
        "changed_paths": [path.relative_to(workspace_dir) for path in changed],
    }
