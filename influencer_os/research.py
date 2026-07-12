"""Research-module validation: JSONL records, findings frontmatter, and
creator research state (ADR 0020 slice, batch B).

Frontmatter is a scoped YAML subset matching the hand-rolled validator
philosophy — fail-closed, no third-party dependency. Supported: top-level
``key: value`` scalars and ``key:`` followed by ``- item`` string lists.
Nested mappings or any other construct are errors, never silent skips.
"""
import datetime
import json
from collections import Counter
from pathlib import Path

from influencer_os.calendars import schedule_research_state_errors
from influencer_os.creator_scope import check_creator_scope, load_workspace_scope
from influencer_os.json_io import write_json_atomic
from influencer_os.rubric import validate_events_ledger
from influencer_os.validation import (
    GATED_RESEARCH_ACCESS_METHODS,
    is_standing_approved_adapter,
    ValidationError,
    iter_jsonl_lines,
    load_json,
    validate_file,
    validate_intent_carry_forward,
    validate_jsonl_file,
    validate_record,
)


RESEARCH_INTELLIGENCE_FILES = {
    "sources.json": "research-sources",
    "hashtags.json": "research-hashtags",
    "search-terms.json": "research-search-terms",
    "reference-creators.json": "reference-creators",
    "watchlist.json": "research-watchlist",
}

# (filename, schema, record id field, research-run outputs field). A run's
# outputs id lists must reconcile exactly with its JSONL contents.
RESEARCH_JSONL_FILES = (
    ("evidence.jsonl", "research-evidence", "evidence_id", "evidence_ids"),
    ("metric-snapshots.jsonl", "metric-snapshot", "metric_snapshot_id", "metric_snapshot_ids"),
)

SYSTEM_JSONL_FILES = (
    ("project-warnings.jsonl", "project-warning"),
)

# Formats with a production plan schema (projects.PRODUCTION_PLAN_SCHEMAS).
# An approval must approve at least one of these; approving only unsupported
# formats records approval intent on the concept instead (ADR 0020/0031).
PRODUCTION_SUPPORTED_FORMATS = frozenset({
    "format_short_form_video",
    "format_carousel",
    "format_single_image_post",
    "format_story_sequence",
    "format_article",
    "format_thread",
})

# A material run (one that declares a material update, a finding, or a queue
# entry) that grounded its output in few promoted-to-evidence sources is a
# thin-evidence run. This is an advisory WARN, never a failure: thin research is
# allowed (local-first posture), it just must not read as well-corroborated.
# Runs that checked fewer than the minimum are too small for the promoted-to-
# evidence rate to mean anything, so they are not evaluated.
THIN_EVIDENCE_MIN_CHECKED = 3
THIN_EVIDENCE_PROMOTION_RATE = 0.34


def _ensure_contained_workspace_file(path, workspace_dir, context):
    workspace_root = Path(workspace_dir).resolve()
    resolved = Path(path).resolve()
    if not resolved.is_relative_to(workspace_root):
        raise ValidationError(f"{context} escapes Creator Workspace: {path}")
    if not resolved.is_file():
        raise ValidationError(f"{context} is not a file: {path}")


def check_project_warning_pairing(record):
    """A warning targeting approved work carries both project_id and
    concept_approval_id; a queue-level warning carries neither (ADR 0020
    pairing, retargeted by ADR 0031)."""
    if ("project_id" in record) != ("concept_approval_id" in record):
        raise ValidationError(
            "project warning must carry both project_id and concept_approval_id "
            "when it targets approved work, and neither for queue-level warnings"
        )


def collect_project_manifests(workspace_dir):
    """Map project_id -> (manifest path, manifest) from projects/*/project.json.

    Project folders are named by project_slug (`init-project` layout), so
    resolution goes through each manifest's project_id; id-named folders in
    older fixtures resolve the same way. A duplicate project_id fails closed
    because it makes link resolution ambiguous."""
    workspace_dir = Path(workspace_dir)
    projects_dir = workspace_dir / "projects"
    manifests = {}
    if projects_dir.exists():
        for manifest_path in sorted(projects_dir.glob("*/project.json")):
            try:
                record = load_json(manifest_path)
            except json.JSONDecodeError as exc:
                raise ValidationError(f"{manifest_path}: invalid JSON: {exc}") from None
            if not isinstance(record, dict):
                raise ValidationError(
                    f"{manifest_path}: project manifest must be a JSON object, "
                    f"not {type(record).__name__}"
                )
            project_id = record.get("project_id")
            if not isinstance(project_id, str) or not project_id:
                raise ValidationError(
                    f"{manifest_path}: project manifest has no project_id"
                )
            if project_id in manifests:
                raise ValidationError(
                    f"project_id {project_id!r} appears more than once under "
                    f"projects/: {manifests[project_id][0]} and {manifest_path}"
                )
            manifests[project_id] = (manifest_path, record)
    return manifests


def check_approval_concept_links(approval, concept):
    """An active approval pins its concept: the concept must be active, and
    the approval's intent snapshot must carry the concept's intent verbatim
    (ADR 0024). Superseded and cancelled approvals impose no concept
    requirement — the concept may have retired or been re-approved."""
    if approval["approval_status"] != "active":
        return
    approval_id = approval["concept_approval_id"]
    concept_id = concept["campaign_concept_id"]
    if concept["status"] != "active":
        raise ValidationError(
            f"Concept approval {approval_id} is active but its concept "
            f"{concept_id} has status {concept['status']!r}; an active "
            "approval requires the concept to be 'active'"
        )
    validate_intent_carry_forward(
        approval, concept,
        f"concept approval {approval_id}", f"concept {concept_id}",
    )


def check_approval_created_projects(approval, projects_by_id):
    """The approval authorizes an exact project set (ADR 0029): every listed
    project must exist and lock this approval as its upstream ref, and no
    unlisted project may reference the approval. Projects are never deleted
    in v1, so a dangling id is invalid state."""
    approval_id = approval["concept_approval_id"]
    listed = set(approval["project_ids_created"])
    approval_evidence_ids = list(dict.fromkeys(
        ref["evidence_id"] for ref in approval["evidence_refs"]
    ))
    for project_id in approval["project_ids_created"]:
        if project_id not in projects_by_id:
            raise ValidationError(
                f"Concept approval {approval_id} lists created project "
                f"{project_id!r} with no project record"
            )
        _, project = projects_by_id[project_id]
        locked = project.get("source_refs", {}).get("concept_approval_id")
        if locked != approval_id:
            raise ValidationError(
                f"Concept approval {approval_id} lists created project "
                f"{project_id!r}, but that project's locked approval is "
                f"{locked!r}; source_refs.concept_approval_id does not point back"
            )
        cached_evidence_ids = project.get("source_refs", {}).get(
            "research_evidence_ids"
        )
        if cached_evidence_ids != approval_evidence_ids:
            raise ValidationError(
                f"Concept approval {approval_id} evidence does not match its "
                "ordered historical snapshot retained by created project "
                f"{project_id}: {cached_evidence_ids!r} != "
                f"{approval_evidence_ids!r}"
            )
    for project_id, (_path, project) in projects_by_id.items():
        locked = project.get("source_refs", {}).get("concept_approval_id")
        if locked == approval_id and project_id not in listed:
            raise ValidationError(
                f"project {project_id} locks concept approval {approval_id}, "
                "but the approval's exact project set does not list it; a "
                "partial approval/project set is invalid (ADR 0029)"
            )


def _slot_selection_matches_concept(research_state, concept):
    """Whether a selected slot's research resolution names this concept —
    directly, or through the content opportunity the concept was assigned
    from (exit criterion 2: slot research resolves to an opportunity or a
    campaign-owned concept)."""
    selected_concept = research_state.get("selected_campaign_concept_id")
    if selected_concept is not None:
        return selected_concept == concept["campaign_concept_id"]
    selected_opportunity = research_state.get("selected_content_opportunity_id")
    return (
        selected_opportunity is not None
        and selected_opportunity == concept.get("source_content_opportunity_id")
    )


def check_approval_slot_claims(workspace_dir, approval, concept,
                               resolved_run_ids=None, schedule=None):
    """An active approval's claimed schedule slots must resolve, be filled,
    and carry selected slot research that names the approval's concept (or
    its source opportunity). Superseded/cancelled approvals impose nothing:
    the schedule is mutable planning state, so freed slots legitimately
    reopen or disappear while the locked approval keeps its historical claim.

    ``schedule`` lets a staged-commit preflight run this gate against the
    simulated post-commit schedule (ADR 0042); omitted, the at-rest
    schedule is loaded from disk."""
    if approval["approval_status"] != "active":
        return
    claimed = approval.get("schedule_slot_ids", [])
    if not claimed:
        return
    approval_id = approval["concept_approval_id"]
    if schedule is None:
        schedule_path = Path(workspace_dir) / "content-schedule.json"
        if not schedule_path.exists():
            raise ValidationError(
                f"Concept approval {approval_id} claims schedule slots but the "
                "workspace has no content-schedule.json"
            )
        # Schema-validate before reading: this check is reachable from validate
        # project, which does not otherwise validate the schedule, and a
        # malformed slot must fail cleanly, not crash on a missing key.
        validate_file("creator-content-schedule", schedule_path)
        schedule = load_json(schedule_path)
    else:
        validate_record("creator-content-schedule", schedule)
    state_errors = schedule_research_state_errors(schedule)
    if state_errors:
        raise ValidationError("; ".join(state_errors))
    slots = {
        slot["slot_id"]: slot
        for slot in schedule.get("calendar_slots", [])
    }
    approval_run_ids = (
        set(resolved_run_ids)
        if resolved_run_ids is not None
        else {ref["research_run_id"] for ref in approval["evidence_refs"]}
    )
    for slot_id in claimed:
        if slot_id not in slots:
            raise ValidationError(
                f"Concept approval {approval_id} claims {slot_id!r}, which "
                "resolves to no schedule slot in content-schedule.json"
            )
        status = slots[slot_id]["status"]
        if status != "filled":
            raise ValidationError(
                f"Concept approval {approval_id} is active but claimed slot "
                f"{slot_id} has status {status!r}; a claimed slot must be "
                "'filled'"
            )
        slot = slots[slot_id]
        research_state = slot["research_state"]
        source_slot_id = slot_id
        if research_state["status"] == "inherits_anchor":
            source_slot_id = research_state["anchor_slot_id"]
            source_slot = slots[source_slot_id]
            research_state = source_slot["research_state"]
        if research_state["status"] != "selected":
            raise ValidationError(
                f"Concept approval {approval_id} claims slot {slot_id}, but its "
                f"research source slot {source_slot_id} is not selected"
            )
        if not _slot_selection_matches_concept(research_state, concept):
            raise ValidationError(
                f"Concept approval {approval_id} approves concept "
                f"{approval['campaign_concept_id']}, but slot {slot_id} "
                "research selected a different opportunity or concept"
            )

        qualifying_runs = []
        for run_id in research_state["research_run_ids"]:
            run_path = (
                Path(workspace_dir)
                / "research"
                / "runs"
                / run_id
                / "research-run.json"
            )
            if not run_path.exists():
                raise ValidationError(
                    f"calendar slot {source_slot_id} references missing focused "
                    f"research run {run_id}"
                )
            _ensure_contained_workspace_file(
                run_path,
                workspace_dir,
                f"calendar slot {source_slot_id} research run {run_id}",
            )
            validate_file("research-run", run_path)
            run = load_json(run_path)
            if run["research_run_id"] != run_id:
                raise ValidationError(
                    f"calendar slot {source_slot_id} references run path {run_id}, "
                    f"but its manifest declares research_run_id "
                    f"{run['research_run_id']!r}"
                )
            if (
                run["mode"] == "scheduled_needs"
                and run["run_status"] != "failed"
                and source_slot_id in run["schedule_slot_ids"]
                and run_id in approval_run_ids
            ):
                qualifying_runs.append(run_id)
        if not qualifying_runs:
            raise ValidationError(
                f"Concept approval {approval_id} claims slot {slot_id} without "
                "carrying evidence from a completed focused scheduled_needs run "
                f"that names source slot {source_slot_id}"
            )


def check_schedule_research_provenance(workspace_dir, opportunities, concepts):
    """Resolve selected schedule state against the canonical opportunity
    queue and campaign concepts: a selected slot names either a shortlisted/
    assigned Content Opportunity or a live Campaign Concept, and the
    selection cites evidence from the slot's focused research runs."""
    schedule_path = Path(workspace_dir) / "content-schedule.json"
    if not schedule_path.exists():
        return
    validate_file("creator-content-schedule", schedule_path)
    schedule = load_json(schedule_path)
    state_errors = schedule_research_state_errors(schedule)
    if state_errors:
        raise ValidationError("; ".join(state_errors))
    for slot in schedule.get("calendar_slots", []):
        state = slot["research_state"]
        if state["status"] not in {"candidates_ready", "selected"}:
            continue
        slot_id = slot["slot_id"]
        for run_id in state["research_run_ids"]:
            run_path = (
                Path(workspace_dir)
                / "research"
                / "runs"
                / run_id
                / "research-run.json"
            )
            if not run_path.exists():
                raise ValidationError(
                    f"calendar slot {slot_id} references missing research run {run_id}"
                )
            _ensure_contained_workspace_file(
                run_path,
                workspace_dir,
                f"calendar slot {slot_id} research run {run_id}",
            )
            validate_file("research-run", run_path)
            run = load_json(run_path)
            if run["research_run_id"] != run_id:
                raise ValidationError(
                    f"calendar slot {slot_id} references run path {run_id}, but "
                    f"its manifest declares research_run_id {run['research_run_id']!r}"
                )
            if (
                run["mode"] != "scheduled_needs"
                or run["run_status"] == "failed"
                or slot_id not in run["schedule_slot_ids"]
            ):
                raise ValidationError(
                    f"calendar slot {slot_id} research run {run_id} is not a "
                    "focused scheduled_needs run naming that slot"
                )
        if state["status"] != "selected":
            continue
        opportunity_id = state.get("selected_content_opportunity_id")
        if opportunity_id is not None:
            if opportunity_id not in opportunities:
                raise ValidationError(
                    f"calendar slot {slot_id} selected content opportunity "
                    f"{opportunity_id!r}, but that opportunity does not exist"
                )
            selection = opportunities[opportunity_id]
            if selection["status"] not in {"shortlisted", "assigned"}:
                raise ValidationError(
                    f"calendar slot {slot_id} selected content opportunity "
                    f"{opportunity_id}, but its status is "
                    f"{selection['status']!r}; expected 'shortlisted' or "
                    "'assigned'"
                )
            selection_label = f"opportunity {opportunity_id}"
        else:
            concept_id = state["selected_campaign_concept_id"]
            if concept_id not in concepts:
                raise ValidationError(
                    f"calendar slot {slot_id} selected campaign concept "
                    f"{concept_id!r}, but that concept does not exist"
                )
            selection = concepts[concept_id]
            if selection["status"] == "retired":
                raise ValidationError(
                    f"calendar slot {slot_id} selected campaign concept "
                    f"{concept_id}, but it is retired"
                )
            selection_label = f"concept {concept_id}"
        selection_run_ids = {
            ref["research_run_id"] for ref in selection["evidence_refs"]
        }
        if not selection_run_ids.intersection(state["research_run_ids"]):
            raise ValidationError(
                f"calendar slot {slot_id} selected {selection_label}, but it "
                "does not cite evidence from the slot's selected research runs"
            )


def refresh_campaign_concept_research(workspace_dir, concept_id, research_run_id,
                                      now=None):
    """Append one focused run's canonical evidence to a scheduled Concept.

    The Weekly Planning Cycle may re-confirm an existing Campaign Concept, but
    its next Concept Approval still needs the new slot-specific research. This
    deterministic updater derives refs from the canonical run ledgers; callers
    never hand-edit the Campaign Concept record.
    """
    workspace_dir = Path(workspace_dir)
    scope = load_workspace_scope(workspace_dir)
    validate_research(workspace_dir)
    concept_paths = sorted(
        workspace_dir.glob(f"campaigns/*/concepts/{concept_id}.json")
    )
    if len(concept_paths) != 1:
        raise ValidationError(
            f"campaign_concept_id {concept_id!r} must resolve to exactly one "
            f"concept; found {len(concept_paths)}"
        )
    concept_path = concept_paths[0]
    _ensure_contained_workspace_file(
        concept_path, workspace_dir, f"campaign concept {concept_id}"
    )
    concept = load_json(concept_path)
    validate_record("campaign-concept", concept)
    check_creator_scope(concept, scope, f"concept {concept_id}")
    if concept["status"] == "retired":
        raise ValidationError(
            f"campaign concept {concept_id} is retired and cannot receive "
            "weekly research"
        )

    schedule_path = workspace_dir / "content-schedule.json"
    validate_file("creator-content-schedule", schedule_path)
    schedule = load_json(schedule_path)
    matching_slots = [
        slot
        for slot in schedule["calendar_slots"]
        if slot.get("campaign_concept_id") == concept_id
    ]
    matching_slot_ids = {slot["slot_id"] for slot in matching_slots}

    run_dir = workspace_dir / "research" / "runs" / research_run_id
    run_path = run_dir / "research-run.json"
    if not run_path.exists():
        raise ValidationError(
            f"research run {research_run_id!r} does not exist"
        )
    _ensure_contained_workspace_file(
        run_path, workspace_dir, f"research run {research_run_id}"
    )
    validate_file("research-run", run_path)
    run = load_json(run_path)
    check_creator_scope(run, scope, f"research run {research_run_id}")
    if run["research_run_id"] != research_run_id:
        raise ValidationError(
            f"research run path {research_run_id!r} declares "
            f"{run['research_run_id']!r}"
        )
    declared_focused_slots = matching_slot_ids.intersection(
        run["schedule_slot_ids"]
    )
    non_ready_slot_ids = sorted(
        slot["slot_id"]
        for slot in matching_slots
        if (
            slot["slot_id"] in declared_focused_slots
            and research_run_id in slot["research_state"]["research_run_ids"]
            and slot["research_state"]["status"] != "candidates_ready"
        )
    )
    if non_ready_slot_ids:
        raise ValidationError(
            f"research run {research_run_id} may refresh concept {concept_id} "
            "only while its matching scheduled slot remains candidates_ready; "
            f"found {non_ready_slot_ids}"
        )
    canonical_run_slot_ids = {
        slot["slot_id"]
        for slot in matching_slots
        if (
            slot["research_state"]["status"] == "candidates_ready"
            and research_run_id in slot["research_state"]["research_run_ids"]
        )
    }
    focused_slots = declared_focused_slots.intersection(
        canonical_run_slot_ids
    )
    if declared_focused_slots and not focused_slots:
        raise ValidationError(
            f"research run {research_run_id} names scheduled slot(s) "
            f"{sorted(declared_focused_slots)} but is absent from their "
            "canonical research_state.research_run_ids"
        )
    if (
        run["mode"] != "scheduled_needs"
        or run["run_status"] == "failed"
        or not focused_slots
    ):
        raise ValidationError(
            f"research run {research_run_id} must be a completed focused "
            f"scheduled_needs run naming a slot scheduled to {concept_id}"
        )

    evidence = validate_jsonl_file(
        "research-evidence", run_dir / "evidence.jsonl"
    )
    metrics_path = run_dir / "metric-snapshots.jsonl"
    metrics = (
        validate_jsonl_file("metric-snapshot", metrics_path)
        if metrics_path.exists()
        else []
    )
    metrics_by_evidence = {}
    for metric in metrics:
        if metric["research_run_id"] != research_run_id:
            raise ValidationError(
                f"metric snapshot {metric['metric_snapshot_id']} does not "
                f"belong to research run {research_run_id}"
            )
        metrics_by_evidence.setdefault(metric["evidence_id"], []).append(
            metric["metric_snapshot_id"]
        )
    derived_refs = []
    for item in evidence:
        if item["research_run_id"] != research_run_id:
            raise ValidationError(
                f"evidence {item['evidence_id']} does not belong to research "
                f"run {research_run_id}"
            )
        check_creator_scope(
            item, scope, f"research evidence {item['evidence_id']}"
        )
        ref = {
            "research_run_id": research_run_id,
            "evidence_id": item["evidence_id"],
        }
        metric_ids = metrics_by_evidence.get(item["evidence_id"], [])
        if metric_ids:
            ref["metric_snapshot_ids"] = metric_ids
        derived_refs.append(ref)
    if not derived_refs:
        raise ValidationError(
            f"research run {research_run_id} has no evidence to attach to "
            f"campaign concept {concept_id}"
        )

    refreshed = dict(concept)
    refreshed["evidence_refs"] = [dict(ref) for ref in concept["evidence_refs"]]
    existing_by_key = {
        (ref["research_run_id"], ref["evidence_id"]): ref
        for ref in refreshed["evidence_refs"]
    }
    for ref in derived_refs:
        key = (ref["research_run_id"], ref["evidence_id"])
        if key in existing_by_key:
            if existing_by_key[key] != ref:
                raise ValidationError(
                    f"concept {concept_id} already carries a different ref "
                    f"for evidence {ref['evidence_id']}"
                )
            continue
        refreshed["evidence_refs"].append(ref)
    finding_ids = list(refreshed.get("source_finding_ids", []))
    for finding_id in run["outputs"]["finding_ids"]:
        if finding_id not in finding_ids:
            finding_ids.append(finding_id)
    if finding_ids:
        refreshed["source_finding_ids"] = finding_ids
    if now is None:
        today = datetime.date.today()
    elif isinstance(now, datetime.datetime):
        today = now.date()
    else:
        today = now
    refreshed["updated_on"] = today.isoformat()
    validate_record("campaign-concept", refreshed)
    write_json_atomic(concept_path, refreshed)
    return {
        "campaign_concept_id": concept_id,
        "concept_path": concept_path,
        "research_run_id": research_run_id,
        "focused_slot_ids": sorted(focused_slots),
        "evidence_refs_added": [
            ref for ref in derived_refs
            if ref not in concept["evidence_refs"]
        ],
    }


def find_concept_approval(workspace_dir, approval_id):
    """Locate one concept approval across campaigns/*/approvals/."""
    matches = sorted(
        Path(workspace_dir).glob(f"campaigns/*/approvals/{approval_id}.json")
    )
    if not matches:
        return None
    _ensure_contained_workspace_file(
        matches[0], workspace_dir, f"concept approval {approval_id}"
    )
    return load_json(matches[0])


def find_campaign_concept(workspace_dir, concept_id):
    """Locate one campaign concept across campaigns/*/concepts/."""
    matches = sorted(
        Path(workspace_dir).glob(f"campaigns/*/concepts/{concept_id}.json")
    )
    if not matches:
        return None
    _ensure_contained_workspace_file(
        matches[0], workspace_dir, f"campaign concept {concept_id}"
    )
    return load_json(matches[0])


def collect_campaign_concepts(workspace_dir):
    """Map campaign_concept_id -> concept across every campaign."""
    concepts = {}
    for concept_path in sorted(
        Path(workspace_dir).glob("campaigns/*/concepts/*.json")
    ):
        _ensure_contained_workspace_file(
            concept_path,
            workspace_dir,
            f"campaign concept file {concept_path.name}",
        )
        concept = load_json(concept_path)
        concepts[concept["campaign_concept_id"]] = concept
    return concepts


def check_project_warning_target_refs(record, workspace_dir, projects_by_id=None):
    """A warning must target records that exist and form one consistent
    approval chain — opportunities, projects, and approvals are never
    deleted in v1, so a dangling target is invalid state, not history, and
    a mismatched tuple would badge the wrong card on the board."""
    workspace_dir = Path(workspace_dir)
    warning_id = record.get("project_warning_id", "<unknown>")
    entry_id = record.get("content_opportunity_id")
    if entry_id is None and "project_id" not in record:
        raise ValidationError(
            f"project warning {warning_id} targets nothing; a queue-level "
            "warning names its content opportunity"
        )
    if entry_id is not None:
        entry_path = (
            workspace_dir / "research" / "content-opportunity-queue" / "entries"
            / f"{entry_id}.json"
        )
        if not entry_path.exists():
            raise ValidationError(
                f"project warning {warning_id} targets content opportunity "
                f"{entry_id!r} with no entry file"
            )
    if "project_id" in record:
        project_id = record["project_id"]
        if projects_by_id is None:
            projects_by_id = collect_project_manifests(workspace_dir)
        if project_id not in projects_by_id:
            raise ValidationError(
                f"project warning {warning_id} targets project {project_id!r} "
                "with no project record"
            )
        approval_id = record["concept_approval_id"]
        approval = find_concept_approval(workspace_dir, approval_id)
        if approval is None:
            raise ValidationError(
                f"project warning {warning_id} targets concept approval "
                f"{approval_id!r} with no approval record"
            )
        _, project = projects_by_id[project_id]
        locked_approval = project.get("source_refs", {}).get("concept_approval_id")
        if locked_approval != approval_id:
            raise ValidationError(
                f"project warning {warning_id} pairs project {project_id!r} "
                f"with concept approval {approval_id!r}, but the project's "
                f"locked approval is {locked_approval!r}"
            )
        if entry_id is not None:
            concept = find_campaign_concept(
                workspace_dir, approval["campaign_concept_id"]
            )
            source_opportunity = (
                concept.get("source_content_opportunity_id")
                if concept is not None
                else None
            )
            if source_opportunity != entry_id:
                raise ValidationError(
                    f"project warning {warning_id} targets content opportunity "
                    f"{entry_id!r}, but concept approval {approval_id!r} "
                    f"resolves to source opportunity {source_opportunity!r}"
                )


def parse_frontmatter(path):
    path = Path(path)
    text = path.read_text()
    if not text.startswith("---\n"):
        raise ValidationError(f"{path}: missing frontmatter block")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValidationError(f"{path}: unterminated frontmatter block")
    data = _parse_yaml_subset(text[4:end], path)
    body = text[end + len("\n---\n"):]
    return data, body


def _parse_yaml_subset(block, path):
    data = {}
    current_list_key = None
    for line_number, raw_line in enumerate(block.splitlines(), start=2):
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            if current_list_key is None:
                raise ValidationError(f"{path}:{line_number}: list item without a list key")
            data[current_list_key].append(_parse_scalar(stripped[2:].strip()))
            continue
        if raw_line[0] in (" ", "\t"):
            raise ValidationError(
                f"{path}:{line_number}: nested frontmatter is not supported (scoped YAML subset)"
            )
        key, separator, value = raw_line.partition(":")
        if not separator or not key.strip():
            raise ValidationError(f"{path}:{line_number}: expected 'key: value'")
        key = key.strip()
        value = value.strip()
        if value:
            data[key] = _parse_scalar(value)
            current_list_key = None
        else:
            data[key] = []
            current_list_key = key
    return data


def _parse_scalar(value):
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1]
    if value == "true":
        return True
    if value == "false":
        return False
    try:
        return int(value)
    except ValueError:
        return value


def validate_findings_file(path):
    data, body = parse_frontmatter(path)
    try:
        validate_record("research-findings", data)
    except ValidationError as exc:
        raise ValidationError(f"{path}: {exc}") from None
    limit = data["summary_char_limit"]
    if len(body) > limit:
        raise ValidationError(
            f"{path}: body is {len(body)} characters, over summary_char_limit {limit}"
        )
    return data


def validate_stable_finding_file(path):
    data, _ = parse_frontmatter(path)
    try:
        validate_record("stable-finding", data)
    except ValidationError as exc:
        raise ValidationError(f"{path}: {exc}") from None
    return data


def validate_research(workspace_path):
    workspace_dir = Path(workspace_path)
    research_dir = workspace_dir / "research"
    if not research_dir.exists():
        raise FileNotFoundError(f"Missing research directory: {research_dir}")

    scope = load_workspace_scope(workspace_dir)

    def scoped(record):
        check_creator_scope(record, scope)

    checked = []
    source_yield_stats = {}
    run_warnings = []

    schedule_path = workspace_dir / "content-schedule.json"
    if schedule_path.exists():
        validate_file("creator-content-schedule", schedule_path)
        schedule = load_json(schedule_path)
        state_errors = schedule_research_state_errors(schedule)
        if state_errors:
            raise ValidationError("; ".join(state_errors))
        check_creator_scope(schedule, scope, schedule_path)
        checked.append("content-schedule.json")

    findings_path = research_dir / "findings.md"
    if findings_path.exists():
        findings_data = validate_findings_file(findings_path)
        check_creator_scope(findings_data, scope, findings_path)
        checked.append("research/findings.md")

    stable_dir = research_dir / "stable-findings"
    if stable_dir.exists():
        for stable_path in sorted(stable_dir.glob("*.md")):
            stable_data = validate_stable_finding_file(stable_path)
            # The entries/approvals filename==id pattern: it also makes a
            # duplicated stable_finding_id impossible at rest.
            if stable_data["stable_finding_id"] != stable_path.stem:
                raise ValidationError(
                    f"{stable_path}: filename does not match stable_finding_id "
                    f"{stable_data['stable_finding_id']!r}"
                )
            check_creator_scope(stable_data, scope, stable_path)
            checked.append(str(stable_path.relative_to(workspace_dir)))

    runs_dir = research_dir / "runs"
    if runs_dir.exists():
        for run_dir in sorted(path for path in runs_dir.iterdir() if path.is_dir()):
            run_manifest = run_dir / "research-run.json"
            if not run_manifest.exists():
                raise ValidationError(f"Research run folder has no research-run.json: {run_dir}")
            _ensure_contained_workspace_file(
                run_manifest,
                workspace_dir,
                f"research run {run_dir.name}",
            )
            validate_file("research-run", run_manifest)
            run_record = load_json(run_manifest)
            if run_record["research_run_id"] != run_dir.name:
                raise ValidationError(
                    f"{run_manifest}: folder name {run_dir.name!r} does not match "
                    f"research_run_id {run_record['research_run_id']!r} "
                    "(layout is research/runs/<research-run-id>/)"
                )
            check_creator_scope(run_record, scope, run_manifest)
            checked.append(str(run_manifest.relative_to(workspace_dir)))
            run_id = run_record["research_run_id"]

            search_plan = None
            search_plan_path = run_dir / "search-plan.json"
            completed_run = run_record["run_status"] != "failed"
            if completed_run and not search_plan_path.exists():
                raise ValidationError(f"Research run folder has no search-plan.json: {run_dir}")
            if search_plan_path.exists():
                try:
                    validate_file("research-search-plan", search_plan_path)
                except ValidationError as exc:
                    raise ValidationError(f"{search_plan_path}: {exc}") from None
                search_plan = load_json(search_plan_path)
                if search_plan["research_run_id"] != run_id:
                    raise ValidationError(
                        f"{search_plan_path}: research_run_id "
                        f"{search_plan['research_run_id']!r} does not match "
                        f"the containing run {run_id!r}"
                    )
                if search_plan["mode"] != run_record["mode"]:
                    raise ValidationError(
                        f"{search_plan_path}: mode {search_plan['mode']!r} "
                        f"does not match research-run.json mode {run_record['mode']!r}"
                    )
                if search_plan["schedule_slot_ids"] != run_record["schedule_slot_ids"]:
                    raise ValidationError(
                        f"{search_plan_path}: schedule_slot_ids "
                        f"{search_plan['schedule_slot_ids']!r} do not match "
                        f"research-run.json {run_record['schedule_slot_ids']!r}"
                    )
                missing_run_platforms = sorted(
                    set(run_record["platforms"]) - set(search_plan["platforms"])
                )
                if missing_run_platforms:
                    raise ValidationError(
                        f"{search_plan_path}: research-run.json platforms "
                        f"{missing_run_platforms!r} are not present in "
                        "search-plan.json platforms"
                    )
                check_creator_scope(search_plan, scope, search_plan_path)
                checked.append(str(search_plan_path.relative_to(workspace_dir)))

            def run_scoped(record, _run_id=run_id):
                check_creator_scope(record, scope)
                record_run = record.get("research_run_id")
                if record_run != _run_id:
                    raise ValidationError(
                        f"research_run_id {record_run!r} does not match "
                        f"the containing run {_run_id!r}"
                    )

            run_records = {filename: [] for filename, *_ in RESEARCH_JSONL_FILES}
            for filename, schema_name, id_field, outputs_field in RESEARCH_JSONL_FILES:
                jsonl_path = run_dir / filename
                jsonl_ids = set()
                if jsonl_path.exists():
                    records = validate_jsonl_file(
                        schema_name, jsonl_path, record_check=run_scoped
                    )
                    id_counts = Counter(record[id_field] for record in records)
                    duplicate_ids = sorted(
                        record_id for record_id, count in id_counts.items() if count > 1
                    )
                    if duplicate_ids:
                        # A duplicated id validates against the declared
                        # outputs (set comparison) but makes every ref to it
                        # ambiguous and bricks the recall index rebuild.
                        raise ValidationError(
                            f"{jsonl_path}: duplicate {id_field} values within "
                            f"the run: {duplicate_ids}"
                        )
                    run_records[filename] = records
                    jsonl_ids = set(id_counts)
                    checked.append(str(jsonl_path.relative_to(workspace_dir)))
                declared_ids = set(run_record["outputs"][outputs_field])
                # Prune records removals instead of rewriting outputs, so the
                # manifest keeps its original account of what the run produced:
                # JSONL contents must equal outputs minus pruned ids.
                pruned_field = f"pruned_{outputs_field}"
                pruned_ids = set(run_record.get(pruned_field, []))
                undeclared_pruned = sorted(pruned_ids - declared_ids)
                if undeclared_pruned:
                    raise ValidationError(
                        f"{run_manifest}: {pruned_field} list ids never "
                        f"declared in outputs.{outputs_field}: {undeclared_pruned}"
                    )
                still_present = sorted(pruned_ids & jsonl_ids)
                if still_present:
                    raise ValidationError(
                        f"{run_manifest}: {pruned_field} list ids still "
                        f"present in {filename}: {still_present}"
                    )
                expected_ids = declared_ids - pruned_ids
                undeclared = sorted(jsonl_ids - expected_ids)
                if undeclared:
                    raise ValidationError(
                        f"{run_manifest}: outputs.{outputs_field} omit ids "
                        f"present in {filename}: {undeclared}"
                    )
                ghost = sorted(expected_ids - jsonl_ids)
                if ghost:
                    raise ValidationError(
                        f"{run_manifest}: outputs.{outputs_field} list ids "
                        f"not present in {filename} and not pruned: {ghost}"
                    )

            # Metric snapshots are run-scoped observations of run evidence:
            # a snapshot whose evidence_id is absent from the run severs the
            # trajectory link and can never be pruned (snapshots prune with
            # their evidence).
            run_evidence_ids = {
                record["evidence_id"] for record in run_records["evidence.jsonl"]
            }
            for snapshot in run_records["metric-snapshots.jsonl"]:
                if snapshot["evidence_id"] not in run_evidence_ids:
                    raise ValidationError(
                        f"{run_dir / 'metric-snapshots.jsonl'}: metric snapshot "
                        f"{snapshot['metric_snapshot_id']} snapshots evidence "
                        f"{snapshot['evidence_id']!r}, which is not in this "
                        "run's evidence.jsonl"
                    )

            source_yield_path = run_dir / "source-yield.jsonl"
            if completed_run and not source_yield_path.exists():
                raise ValidationError(f"Research run folder has no source-yield.jsonl: {run_dir}")
            if source_yield_path.exists():
                source_yield_records = validate_jsonl_file(
                    "research-source-yield", source_yield_path, record_check=run_scoped
                )
                yield_id_counts = Counter(
                    record["research_source_yield_id"]
                    for record in source_yield_records
                )
                duplicate_yield_ids = sorted(
                    yield_id for yield_id, count in yield_id_counts.items() if count > 1
                )
                if duplicate_yield_ids:
                    # A duplicated id makes every ref to it ambiguous and
                    # double-counts into yield_stats — the same guard the
                    # evidence and metric ledgers already carry.
                    raise ValidationError(
                        f"{source_yield_path}: duplicate research_source_yield_id "
                        f"values within the run: {duplicate_yield_ids}"
                    )
                plan_platforms = set(search_plan["platforms"]) if search_plan else set()
                run_metric_ids = {
                    record["metric_snapshot_id"]
                    for record in run_records["metric-snapshots.jsonl"]
                }
                for record in source_yield_records:
                    # The yield ledger records what the run actually did. A gated
                    # access method attests the run executed something the slice
                    # forbids, unless it is an exact standing-approved ADR 0022
                    # connector (a non-approved api_backed adapter like
                    # youtube_data_api still fails here).
                    if record["access_method"] in GATED_RESEARCH_ACCESS_METHODS and not (
                        is_standing_approved_adapter(record.get("adapter_id"), record["access_method"])
                    ):
                        raise ValidationError(
                            f"{source_yield_path}: source yield "
                            f"{record['research_source_yield_id']} used gated "
                            f"access method {record['access_method']!r} with adapter "
                            f"{record.get('adapter_id')!r}, which is not permitted "
                            "in this slice"
                        )
                    if plan_platforms and record["platform"] not in plan_platforms:
                        raise ValidationError(
                            f"{source_yield_path}: source yield "
                            f"{record['research_source_yield_id']} platform "
                            f"{record['platform']!r} is not in search-plan.json platforms"
                        )
                    missing_evidence = sorted(set(record["evidence_ids"]) - run_evidence_ids)
                    if missing_evidence:
                        raise ValidationError(
                            f"{source_yield_path}: source yield "
                            f"{record['research_source_yield_id']} references evidence "
                            f"not present in this run: {missing_evidence}"
                        )
                    missing_metrics = sorted(set(record["metric_snapshot_ids"]) - run_metric_ids)
                    if missing_metrics:
                        raise ValidationError(
                            f"{source_yield_path}: source yield "
                            f"{record['research_source_yield_id']} references metric "
                            f"snapshots not present in this run: {missing_metrics}"
                        )
                    if record["source_key"].startswith("source_intel_"):
                        stats = source_yield_stats.setdefault(
                            record["source_key"],
                            {
                                "checked_count": 0,
                                "promoted_to_evidence_count": 0,
                                "background_use_count": 0,
                                "low_yield_count": 0,
                            },
                        )
                        stats["checked_count"] += 1
                        if record["outcome"] == "promoted_to_evidence":
                            stats["promoted_to_evidence_count"] += 1
                        elif record["outcome"] == "used_as_background":
                            stats["background_use_count"] += 1
                        else:
                            stats["low_yield_count"] += 1
                checked_sources = len(source_yield_records)
                promoted_sources = sum(
                    1 for record in source_yield_records
                    if record["outcome"] == "promoted_to_evidence"
                )
                # Derive "material" from the run's declared outputs, not only the
                # material_update flag: a stale or wrong flag must not suppress
                # the warning when the run actually produced a finding or idea.
                run_outputs = run_record["outputs"]
                run_is_material = (
                    run_record["material_update"]
                    or bool(run_outputs["finding_ids"])
                    or bool(run_outputs["content_opportunity_ids"])
                )
                if (
                    run_is_material
                    and checked_sources >= THIN_EVIDENCE_MIN_CHECKED
                    and promoted_sources
                    < THIN_EVIDENCE_PROMOTION_RATE * checked_sources
                ):
                    run_warnings.append(
                        f"{run_manifest}: run is a material research update but only "
                        f"{promoted_sources} of {checked_sources} checked sources "
                        "produced evidence; treat its findings as thin-evidence, "
                        "not well-corroborated"
                    )
                checked.append(str(source_yield_path.relative_to(workspace_dir)))

    for filename, schema_name in RESEARCH_INTELLIGENCE_FILES.items():
        intel_path = research_dir / "intelligence" / filename
        if intel_path.exists():
            validate_file(schema_name, intel_path)
            check_creator_scope(load_json(intel_path), scope, intel_path)
            checked.append(str(intel_path.relative_to(workspace_dir)))

    sources_path = research_dir / "intelligence" / "sources.json"
    if source_yield_stats and not sources_path.exists():
        raise ValidationError(
            f"source-yield references saved source ids, but {sources_path} is missing"
        )
    if sources_path.exists():
        sources = load_json(sources_path)
        sources_by_id = {item["source_intel_id"]: item for item in sources["items"]}
        zero_stats = {
            "checked_count": 0,
            "promoted_to_evidence_count": 0,
            "background_use_count": 0,
            "low_yield_count": 0,
        }
        # records -> sources: every source a yield record credited must be saved.
        for source_id in sorted(source_yield_stats):
            if source_id not in sources_by_id:
                raise ValidationError(
                    f"{sources_path}: source-yield references {source_id!r}, "
                    "but sources.json has no matching item"
                )
        # sources -> records: every saved source's counts must equal the
        # aggregate of its yield records — all zeros when it has none — so a
        # hand-edited source cannot advertise an invented usefulness history.
        for source_id, item in sorted(sources_by_id.items()):
            expected_stats = source_yield_stats.get(source_id, zero_stats)
            actual_stats = item.get("yield_stats", {})
            for field, expected_value in expected_stats.items():
                actual_value = actual_stats.get(field)
                if actual_value != expected_value:
                    raise ValidationError(
                        f"{sources_path}: {source_id}.yield_stats.{field} "
                        f"is {actual_value!r}, expected {expected_value!r} "
                        "from source-yield.jsonl records"
                    )

    board_path = workspace_dir / "boards" / "content-board.json"
    if board_path.exists():
        validate_file("content-board", board_path)
        check_creator_scope(load_json(board_path), scope, board_path)
        checked.append("boards/content-board.json")

    for filename, schema_name in SYSTEM_JSONL_FILES:
        system_path = workspace_dir / "system" / filename
        if system_path.exists():
            def record_check(record):
                check_project_warning_pairing(record)
                check_project_warning_target_refs(record, workspace_dir)
                check_creator_scope(record, scope)
            validate_jsonl_file(schema_name, system_path, record_check=record_check)
            checked.append(str(system_path.relative_to(workspace_dir)))

    checked.extend(validate_events_ledger(workspace_dir, scope))

    warnings, approval_paths, _approvals_by_id = validate_approvals(
        workspace_dir, scope=scope
    )
    checked.extend(approval_paths)
    warnings = run_warnings + warnings

    # Approval checks run identically on the research and queue paths: when
    # the opportunity queue exists, the research path also verifies the
    # entry-side consistency (manifest agreement, ref resolution, and the
    # opportunity <-> concept assignment closure).
    queue_manifest_path = (
        workspace_dir / "research" / "content-opportunity-queue" / "queue.json"
    )
    if queue_manifest_path.exists():
        entries = _check_opportunity_consistency(workspace_dir, scope)
        check_schedule_research_provenance(
            workspace_dir, entries, collect_campaign_concepts(workspace_dir)
        )
        checked.append("research/content-opportunity-queue/queue.json")

    return {"workspace_path": workspace_dir, "checked_paths": checked, "warnings": warnings}


def validate_queue(workspace_path):
    workspace_dir = Path(workspace_path)
    manifest_path = (
        workspace_dir / "research" / "content-opportunity-queue" / "queue.json"
    )
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Missing content opportunity queue manifest: {manifest_path}"
        )

    scope = load_workspace_scope(workspace_dir)

    # Entry-side consistency first (queue-focused errors surface first),
    # then the same approval check set as validate research (gate, creator
    # scope, filename==id, slot claims, gate warnings) so no approval state
    # can validate on one command and fail the other.
    entries = _check_opportunity_consistency(workspace_dir, scope)
    check_schedule_research_provenance(
        workspace_dir, entries, collect_campaign_concepts(workspace_dir)
    )
    warnings, _approval_paths, _approvals_by_id = validate_approvals(
        workspace_dir, scope=scope
    )

    return {
        "workspace_path": workspace_dir,
        "entry_count": len(entries),
        "manifest_path": manifest_path,
        "warnings": warnings,
    }


def _check_opportunity_consistency(workspace_dir, scope):
    """Entry-side opportunity queue consistency, shared by validate_queue
    and validate_research: manifest/entry agreement (delegated to the
    campaign walker's queue check), evidence and finding ref resolution,
    and the opportunity <-> concept assignment closure."""
    from influencer_os.campaigns import _check_opportunity_queue

    workspace_dir = Path(workspace_dir)
    manifest_path = (
        workspace_dir / "research" / "content-opportunity-queue" / "queue.json"
    )
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Missing content opportunity queue manifest: {manifest_path}"
        )

    concepts = collect_campaign_concepts(workspace_dir)
    entries = _check_opportunity_queue(
        workspace_dir, scope, [], set(concepts)
    )

    evidence_runs, metric_runs, metric_evidence = collect_research_record_ids(workspace_dir)
    video_pack_ids = collect_video_pack_ids(workspace_dir)
    known_finding_ids = collect_finding_ids(workspace_dir)
    for entry in entries.values():
        for ref in entry["evidence_refs"]:
            problems = resolve_evidence_ref(
                ref, evidence_runs, metric_runs, video_pack_ids, metric_evidence
            )
            if problems:
                raise ValidationError(
                    f"{entry['content_opportunity_id']}: {problems[0]}"
                )
        for finding_id in entry.get("source_finding_ids", []):
            if finding_id not in known_finding_ids:
                raise ValidationError(
                    f"{entry['content_opportunity_id']}: source finding ref "
                    f"{finding_id!r} does not resolve to any findings "
                    "frontmatter, stable finding, or run output"
                )

    # Assignment closure: assigning an opportunity creates a concept with
    # provenance back to the opportunity (ADR 0031). Both sides are written
    # by one workflow, so a one-sided link is always invalid state.
    concepts_by_source = {}
    for concept in concepts.values():
        # A retired concept keeps its historical source ref while the
        # opportunity legitimately reverts to the open pool.
        if concept["status"] == "retired":
            continue
        source_id = concept.get("source_content_opportunity_id")
        if source_id is not None:
            concepts_by_source.setdefault(source_id, []).append(
                concept["campaign_concept_id"]
            )
    for entry_id, entry in entries.items():
        linked_concepts = entry.get("linked_campaign_concept_ids", [])
        for concept_id in linked_concepts:
            concept = concepts.get(concept_id)
            if concept is None:
                raise ValidationError(
                    f"{entry_id}: linked campaign concept {concept_id!r} has "
                    "no concept record"
                )
            if concept.get("source_content_opportunity_id") != entry_id:
                raise ValidationError(
                    f"{entry_id}: linked campaign concept {concept_id!r} was "
                    f"assigned from "
                    f"{concept.get('source_content_opportunity_id')!r}"
                )
        if entry["status"] == "assigned":
            if not linked_concepts:
                raise ValidationError(
                    f"{entry_id}: status is 'assigned' but "
                    "linked_campaign_concept_ids is empty"
                )
        elif linked_concepts:
            raise ValidationError(
                f"{entry_id}: status is {entry['status']!r} but the "
                f"opportunity links concept(s) {sorted(linked_concepts)}"
            )
        unlinked = sorted(
            set(concepts_by_source.get(entry_id, [])) - set(linked_concepts)
        )
        if unlinked:
            raise ValidationError(
                f"{entry_id}: concept(s) {unlinked} name this opportunity as "
                "their source, but the opportunity does not link them back"
            )

    return entries


def validate_approval_gate(
    workspace_dir,
    approval,
    projects_by_id=None,
    research_ids=None,
    video_pack_ids=None,
    known_finding_ids=None,
    concept=None,
    schedule=None,
    strict_evidence=False,
):
    """Enforce the concept approval gate (ADR 0029/0031).

    An approval must point to a real campaign concept and carry the
    concept's evidence and intent verbatim. Unresolved evidence refs fail
    for any automated path; for human-approved records they warn at rest
    (already-canonical approvals may outlive pruned research) but fail
    when ``strict_evidence`` is set — the staged-commit gate sets it so a
    fresh approval never commits with dangling provenance. Returns warning
    strings.

    The optional research_ids / video_pack_ids / known_finding_ids caches
    let validate_approvals collect the research corpus once instead of per
    approval. ``concept`` and ``schedule`` let a staged-commit preflight
    (ADR 0042) run the gate against the simulated post-commit state;
    omitted, both load from disk as at rest.
    """
    workspace_dir = Path(workspace_dir)
    approval_id = approval["concept_approval_id"]
    concept_id = approval["campaign_concept_id"]
    if concept is None:
        concept = find_campaign_concept(workspace_dir, concept_id)
        if concept is None:
            raise ValidationError(
                f"Concept approval {approval_id} does not point to a real "
                f"campaign concept: {concept_id} resolves to no concept file"
            )
    try:
        validate_record("campaign-concept", concept)
    except ValidationError as exc:
        raise ValidationError(f"concept {concept_id}: {exc}") from None
    if concept["creator_profile_id"] != approval["creator_profile_id"]:
        raise ValidationError(
            f"Concept approval {approval_id} points to a concept owned by a "
            f"different creator: {concept['creator_profile_id']!r} != "
            f"{approval['creator_profile_id']!r}"
        )
    if not set(approval["approved_formats"]) & PRODUCTION_SUPPORTED_FORMATS:
        raise ValidationError(
            f"Concept approval {approval_id} approves no production-supported "
            f"format ({sorted(approval['approved_formats'])}); record the "
            "approval intent on the concept instead until the format lands"
        )
    concept_evidence = concept["evidence_refs"]
    approval_evidence = approval["evidence_refs"]
    historical_snapshot = concept_evidence[:len(approval_evidence)]
    if approval_evidence != historical_snapshot:
        raise ValidationError(
            f"Concept approval {approval_id} evidence does not match concept "
            f"{concept_id}'s ordered historical snapshot; approvals never "
            "delete, reorder, duplicate, rewrite, or inject research refs"
        )
    check_approval_concept_links(approval, concept)
    if projects_by_id is None:
        projects_by_id = collect_project_manifests(workspace_dir)
    check_approval_created_projects(approval, projects_by_id)
    from influencer_os.campaigns import check_project_expression_against_approval

    for project_id in approval["project_ids_created"]:
        _path, project = projects_by_id[project_id]
        check_project_expression_against_approval(project, approval, concept)

    if research_ids is None:
        research_ids = collect_research_record_ids(workspace_dir)
    evidence_runs, metric_runs, metric_evidence = research_ids
    if video_pack_ids is None:
        video_pack_ids = collect_video_pack_ids(workspace_dir)
    warnings = []

    unresolved = []
    resolved_run_ids = set()
    for ref in approval["evidence_refs"]:
        problems = resolve_evidence_ref(
            ref, evidence_runs, metric_runs, video_pack_ids, metric_evidence
        )
        unresolved.extend(problems)
        if not problems:
            resolved_run_ids.add(ref["research_run_id"])
    unresolved_message = None
    if unresolved:
        unresolved_message = (
            f"concept approval {approval_id} has unresolved evidence refs: "
            + "; ".join(sorted(set(unresolved)))
        )
        if strict_evidence or approval["approved_by"] != "user":
            raise ValidationError(unresolved_message)
        warnings.append(
            f"warning: {unresolved_message} (human-approved: warning only)"
        )
    try:
        check_approval_slot_claims(
            workspace_dir,
            approval,
            concept,
            resolved_run_ids=resolved_run_ids,
            schedule=schedule,
        )
    except ValidationError as exc:
        if unresolved_message is not None:
            raise ValidationError(f"{unresolved_message}; {exc}") from None
        raise

    if known_finding_ids is None:
        known_finding_ids = collect_finding_ids(workspace_dir)
    unresolved_findings = sorted(
        finding_id
        for finding_id in set(concept.get("source_finding_ids", []))
        if finding_id not in known_finding_ids
    )
    if unresolved_findings:
        message = (
            f"concept approval {approval_id} approves concept {concept_id} "
            "with finding refs that resolve to no findings frontmatter, "
            f"stable finding, or run output: {unresolved_findings}"
        )
        if strict_evidence or approval["approved_by"] != "user":
            raise ValidationError(message)
        warnings.append(
            f"warning: {message} (human-approved: warning only)"
        )
    return warnings


def validate_approvals(workspace_path, scope=None):
    """Validate every concept approval and its gate. Returns warning
    strings, checked paths, and the approval map keyed by
    concept_approval_id."""
    workspace_dir = Path(workspace_path)
    if scope is None:
        scope = load_workspace_scope(workspace_dir)
    approval_paths = sorted(workspace_dir.glob("campaigns/*/approvals/*.json"))
    warnings = []
    checked = []
    approvals_by_id = {}
    if approval_paths:
        projects_by_id = collect_project_manifests(workspace_dir)
        # Collect the research corpus once for the whole sweep; the gate
        # would otherwise rescan it per approval.
        research_ids = collect_research_record_ids(workspace_dir)
        video_pack_ids = collect_video_pack_ids(workspace_dir)
        known_finding_ids = collect_finding_ids(workspace_dir)
        concepts = collect_campaign_concepts(workspace_dir)
        claimed_slots = {}
        for approval_path in approval_paths:
            approval = load_json(approval_path)
            try:
                validate_record("concept-approval", approval)
            except ValidationError as exc:
                raise ValidationError(f"{approval_path}: {exc}") from None
            if approval["concept_approval_id"] != approval_path.stem:
                raise ValidationError(
                    f"{approval_path}: filename does not match "
                    f"concept_approval_id {approval['concept_approval_id']!r}"
                )
            check_creator_scope(approval, scope, approval_path)
            if approval["approval_status"] == "active":
                for slot_id in approval.get("schedule_slot_ids", []):
                    earlier = claimed_slots.setdefault(
                        slot_id, approval["concept_approval_id"]
                    )
                    if earlier != approval["concept_approval_id"]:
                        raise ValidationError(
                            f"Schedule slot {slot_id} is claimed by more than "
                            f"one active approval: {earlier} and "
                            f"{approval['concept_approval_id']}"
                        )
            warnings.extend(
                validate_approval_gate(
                    workspace_dir,
                    approval,
                    projects_by_id=projects_by_id,
                    research_ids=research_ids,
                    video_pack_ids=video_pack_ids,
                    known_finding_ids=known_finding_ids,
                    concept=concepts.get(approval["campaign_concept_id"]),
                )
            )
            approvals_by_id[approval["concept_approval_id"]] = approval
            checked.append(str(approval_path.relative_to(workspace_dir)))
    return warnings, checked, approvals_by_id


def collect_research_record_ids(workspace_dir):
    """Scan run JSONL files and map evidence and metric snapshot ids to their
    containing run folder, plus each metric snapshot's evidence link.
    File-first by design: the recall index is a rebuildable projection, never
    a validation dependency. Duplicate ids fail closed — cross-run because
    they make run-scoped ref resolution ambiguous, within-run because every
    ref to the id becomes ambiguous and the recall index rebuild fails."""
    evidence_runs = {}
    metric_runs = {}
    metric_evidence = {}
    runs_dir = Path(workspace_dir) / "research" / "runs"
    if runs_dir.exists():
        scans = (
            ("evidence.jsonl", "evidence_id", evidence_runs),
            ("metric-snapshots.jsonl", "metric_snapshot_id", metric_runs),
        )
        for filename, id_field, id_runs in scans:
            for jsonl_path in sorted(runs_dir.glob(f"*/{filename}")):
                run_id = jsonl_path.parent.name
                for line_number, line in iter_jsonl_lines(jsonl_path):
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValidationError(
                            f"{jsonl_path}:{line_number}: invalid JSON: {exc}"
                        ) from None
                    if id_field not in record:
                        raise ValidationError(
                            f"{jsonl_path}:{line_number}: record has no {id_field}"
                        )
                    record_id = record[id_field]
                    existing_run = id_runs.get(record_id)
                    if existing_run == run_id:
                        raise ValidationError(
                            f"{jsonl_path}:{line_number}: {id_field} {record_id!r} "
                            "is duplicated within the run; ids must be unique"
                        )
                    if existing_run is not None:
                        raise ValidationError(
                            f"{jsonl_path}:{line_number}: {id_field} {record_id!r} "
                            f"appears in more than one run ({existing_run!r} and "
                            f"{run_id!r}); ids must resolve to exactly one run"
                        )
                    id_runs[record_id] = run_id
                    if id_field == "metric_snapshot_id":
                        metric_evidence[record_id] = record.get("evidence_id")
    return evidence_runs, metric_runs, metric_evidence


def resolve_evidence_ref(ref, evidence_runs, metric_runs, video_pack_ids, metric_evidence=None):
    """Return problem strings for one structured evidence ref (empty when the
    ref resolves). Evidence and metric snapshots must live in the run the ref
    names — the ADR 0020 ref shape carries research_run_id precisely so
    provenance cannot float across runs — and each referenced snapshot must
    snapshot the ref's own evidence, not another record's. Video packs may be
    workspace-level, so they resolve by id alone."""
    problems = []
    ref_run = ref["research_run_id"]
    evidence_id = ref["evidence_id"]
    evidence_run = evidence_runs.get(evidence_id)
    if evidence_run is None:
        problems.append(
            f"evidence ref {evidence_id!r} does not resolve to any "
            "research run evidence record"
        )
    elif evidence_run != ref_run:
        problems.append(
            f"evidence ref {evidence_id!r} resolves to run {evidence_run!r}, "
            f"but the ref names run {ref_run!r}"
        )
    for metric_id in ref.get("metric_snapshot_ids", []):
        metric_run = metric_runs.get(metric_id)
        if metric_run is None:
            problems.append(
                f"metric snapshot ref {metric_id!r} does not resolve to any "
                "research run metric snapshot"
            )
        elif metric_run != ref_run:
            problems.append(
                f"metric snapshot ref {metric_id!r} resolves to run "
                f"{metric_run!r}, but the ref names run {ref_run!r}"
            )
        elif (
            metric_evidence is not None
            and metric_evidence.get(metric_id) != evidence_id
        ):
            problems.append(
                f"metric snapshot ref {metric_id!r} snapshots evidence "
                f"{metric_evidence.get(metric_id)!r}, not the ref's evidence "
                f"{evidence_id!r}"
            )
    for pack_id in ref.get("video_understanding_pack_ids", []):
        if pack_id not in video_pack_ids:
            problems.append(
                f"video understanding pack ref {pack_id!r} does not resolve "
                "to a video-understanding-pack record"
            )
    return problems


def collect_finding_ids(workspace_dir):
    """Every finding id the workspace has declared: the rolling findings
    frontmatter, stable findings, and each run's immutable outputs. Findings
    legitimately rotate out of the rolling summary (the char limit demotes
    them), so refs resolve against the union — a ghost id fails while a
    rotated finding still resolves through the run that produced it."""
    research_dir = Path(workspace_dir) / "research"
    finding_ids = set()
    findings_path = research_dir / "findings.md"
    if findings_path.exists():
        data, _body = parse_frontmatter(findings_path)
        finding_ids.update(data.get("finding_ids", []))
    stable_dir = research_dir / "stable-findings"
    if stable_dir.exists():
        for stable_path in sorted(stable_dir.glob("*.md")):
            data, _body = parse_frontmatter(stable_path)
            if data.get("finding_id"):
                finding_ids.add(data["finding_id"])
    runs_dir = research_dir / "runs"
    if runs_dir.exists():
        for manifest_path in sorted(runs_dir.glob("*/research-run.json")):
            outputs = load_json(manifest_path).get("outputs", {})
            finding_ids.update(outputs.get("finding_ids", []))
    return finding_ids


def collect_video_pack_ids(workspace_dir):
    """Video Understanding Pack ids resolve to <pack-id>.json files, either in
    the workspace-level pack directory or inside a run folder. The file is
    read and its video_understanding_pack_id must match the filename stem, so
    a ref cannot resolve through a mislabeled or malformed pack file."""
    research_dir = Path(workspace_dir) / "research"
    pack_ids = set()
    for pattern in (
        "video-understanding-packs/*.json",
        "runs/*/video-understanding-packs/*.json",
    ):
        for path in sorted(research_dir.glob(pattern)):
            try:
                record = load_json(path)
            except json.JSONDecodeError as exc:
                raise ValidationError(f"{path}: invalid JSON: {exc}") from None
            pack_id = record.get("video_understanding_pack_id")
            if pack_id != path.stem:
                raise ValidationError(
                    f"{path}: filename does not match "
                    f"video_understanding_pack_id {pack_id!r}"
                )
            pack_ids.add(pack_id)
    return pack_ids
