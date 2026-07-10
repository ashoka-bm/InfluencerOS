"""Staged pre-approval promotion bundles (ADR 0042 stage/commit).

``stage_promotion`` builds the entire draft set behind the idea-promotion
gate — the locked promotion, one project manifest per embedded project
seed, optional authored evidence briefs, and the planned entry / queue /
schedule flips — into ``system/staging/<stage_id>/``, prevalidated against
the same gate that guards the canonical write. Staging touches no
canonical path, so it can run speculatively while the human reads the
package (present-from-draft: the human approves exactly the bytes commit
will write).

``commit_stage`` re-verifies content hashes of the upstream inputs the
stage was derived from (a stale stage fails closed and is re-staged, never
patched), stamps the approval fields, writes the records in the required
construction order, applies the flips, runs at-rest validation, and
rebuilds the board and recall-index projections. Every record is built and
gate-checked before the first canonical write, so a mid-sequence failure
is a filesystem fault, not a planning fault; ``validate all`` pinpoints
any residue.
"""

import datetime
import hashlib
import json
import shutil
from copy import deepcopy
from pathlib import Path

from influencer_os.boards import rebuild_board
from influencer_os.calendars import schedule_research_state_errors
from influencer_os.constructors import (
    STAGING_DIR,
    build_project_manifest,
    check_seed_fields,
    create_project_from_manifest,
    creator_id_suffix,
    id_token,
    load_seed,
    load_workspace_manifest,
    next_sequenced_id,
)
from influencer_os.json_io import write_json_atomic
from influencer_os.projects import _validate_approval_surface, validate_project
from influencer_os.recall_index import rebuild_index
from influencer_os.research import (
    collect_project_manifests,
    validate_promotion_gate,
    validate_queue,
    validate_research,
)
from influencer_os.validation import (
    ValidationError,
    load_json,
    validate_intent_carry_forward,
    validate_record,
)

STAGE_MANIFEST_NAME = "stage.json"

PROMOTION_SEED_REQUIRED = (
    "approved_platforms",
    "approved_formats",
    "projects",
)
PROMOTION_SEED_OPTIONAL = (
    "schedule_slot_ids",
    "creative_elements_to_carry_forward",
    "approval_note",
    "idea_promotion_id",
)

# The embedded project seeds omit idea_promotion_id (the bundle owns it)
# and may add an authored evidence-brief body.
BUNDLE_PROJECT_SEED_REQUIRED = (
    "project_slug",
    "content_unit_type",
    "platform_targets",
    "learning_goal",
    "acceptance_criteria",
)
BUNDLE_PROJECT_SEED_OPTIONAL = (
    "constraints",
    "dependencies",
    "notes",
    "reference_asset_ids",
    "target_formats",
    "project_id",
    "evidence_brief",
)


def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _sha256_record(record):
    return _sha256_bytes(
        json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    )


def _entry_path(workspace_dir, entry_id):
    return (
        Path(workspace_dir) / "research" / "idea-queue" / "entries"
        / f"{entry_id}.json"
    )


def _queue_manifest_path(workspace_dir):
    return Path(workspace_dir) / "research" / "idea-queue" / "queue.json"


def _schedule_path(workspace_dir):
    return Path(workspace_dir) / "content-schedule.json"


def _queue_entry_ref(queue_manifest, entry_id):
    for ref in queue_manifest.get("entry_refs", []):
        if ref["idea_queue_entry_id"] == entry_id:
            return ref
    raise ValidationError(
        f"queue manifest lists no entry_ref for {entry_id}; the entry must "
        "be tracked before promotion"
    )


def _claimed_slots(schedule, slot_ids, promotion_id):
    slots = {slot["slot_id"]: slot for slot in schedule.get("calendar_slots", [])}
    claimed = {}
    for slot_id in slot_ids:
        if slot_id not in slots:
            raise ValidationError(
                f"promotion {promotion_id} claims {slot_id!r}, which resolves "
                "to no schedule slot"
            )
        claimed[slot_id] = slots[slot_id]
    return claimed


def _input_hashes(workspace_dir, entry_id, slot_ids, promotion_id):
    """Content hashes of exactly the upstream state the stage was derived
    from: the entry file, the entry's queue-manifest row, and each claimed
    slot. Unrelated queue or schedule changes do not invalidate a stage."""
    hashes = {
        "entry": _sha256_bytes(
            _entry_path(workspace_dir, entry_id).read_bytes()
        )
    }
    queue_manifest = load_json(_queue_manifest_path(workspace_dir))
    hashes["queue_entry_ref"] = _sha256_record(
        _queue_entry_ref(queue_manifest, entry_id)
    )
    if slot_ids:
        schedule = load_json(_schedule_path(workspace_dir))
        claimed = _claimed_slots(schedule, slot_ids, promotion_id)
        hashes["slots"] = {
            slot_id: _sha256_record(slot) for slot_id, slot in claimed.items()
        }
    else:
        hashes["slots"] = {}
    return hashes


def _active_linked_promotion(workspace_dir, entry):
    promotions_dir = Path(workspace_dir) / "research" / "idea-promotions"
    for promotion_id in entry.get("linked_idea_promotion_ids", []):
        promotion_path = promotions_dir / f"{promotion_id}.json"
        if promotion_path.exists():
            promotion = load_json(promotion_path)
            if promotion.get("promotion_status") == "active":
                return promotion_id
    return None


def _existing_promotion_ids(workspace_dir):
    ids = set()
    promotions_dir = Path(workspace_dir) / "research" / "idea-promotions"
    if promotions_dir.exists():
        ids.update(path.stem for path in promotions_dir.glob("*.json"))
    staging_root = Path(workspace_dir) / STAGING_DIR
    if staging_root.exists():
        for stage_manifest in staging_root.glob(f"*/{STAGE_MANIFEST_NAME}"):
            staged = load_json(stage_manifest)
            if "idea_promotion_id" in staged:
                ids.add(staged["idea_promotion_id"])
    return ids


def _flipped_entry(entry, promotion, today):
    flipped = deepcopy(entry)
    flipped["status"] = "promoted"
    promotion_links = list(flipped.get("linked_idea_promotion_ids", []))
    if promotion["idea_promotion_id"] not in promotion_links:
        promotion_links.append(promotion["idea_promotion_id"])
    flipped["linked_idea_promotion_ids"] = promotion_links
    project_links = list(flipped.get("linked_project_ids", []))
    for project_id in promotion["project_ids_created"]:
        if project_id not in project_links:
            project_links.append(project_id)
    flipped["linked_project_ids"] = project_links
    flipped["updated_on"] = today
    validate_record("idea-queue-entry", flipped)
    return flipped


def _flipped_schedule(schedule, slot_ids):
    flipped = deepcopy(schedule)
    for slot in flipped.get("calendar_slots", []):
        if slot["slot_id"] in slot_ids:
            slot["status"] = "filled"
    validate_record("creator-content-schedule", flipped)
    state_errors = schedule_research_state_errors(flipped)
    if state_errors:
        raise ValidationError("; ".join(state_errors))
    return flipped


def _flipped_queue_manifest(queue_manifest, entry_id, today):
    flipped = deepcopy(queue_manifest)
    _queue_entry_ref(flipped, entry_id)["status"] = "promoted"
    counts = {}
    for ref in flipped["entry_refs"]:
        counts[ref["status"]] = counts.get(ref["status"], 0) + 1
    flipped["status_counts"] = counts
    flipped["updated_on"] = today
    validate_record("idea-queue", flipped)
    return flipped


def _gate_preflight(workspace_dir, promotion, staged_projects, entry, today):
    """Run the real promotion gate against the simulated post-commit state:
    flipped entry, flipped schedule, and the staged projects merged over
    the existing manifests."""
    flipped_entry = _flipped_entry(entry, promotion, today)
    slot_ids = promotion.get("schedule_slot_ids", [])
    flipped_schedule = None
    if slot_ids:
        schedule_path = _schedule_path(workspace_dir)
        if not schedule_path.exists():
            raise ValidationError(
                f"promotion {promotion['idea_promotion_id']} claims schedule "
                "slots but the workspace has no content-schedule.json"
            )
        flipped_schedule = _flipped_schedule(load_json(schedule_path), slot_ids)
    projects_by_id = dict(collect_project_manifests(workspace_dir))
    for project in staged_projects:
        projects_by_id[project["project_id"]] = (None, project)
    warnings = validate_promotion_gate(
        workspace_dir,
        promotion,
        projects_by_id=projects_by_id,
        entry=flipped_entry,
        schedule=flipped_schedule,
    )
    for project in staged_projects:
        _validate_approval_surface(project, promotion)
    return warnings


def stage_promotion(seed, creator_workspace, entry_id, now=None):
    """Build the full promotion draft bundle into system/staging/,
    prevalidated through the real gate. Writes nothing canonical."""
    workspace_dir = Path(creator_workspace)
    seed = load_seed(seed)
    check_seed_fields(
        seed, PROMOTION_SEED_REQUIRED, PROMOTION_SEED_OPTIONAL, "promotion"
    )
    if not seed["projects"]:
        raise ValidationError(
            "a promotion that creates no production work is invalid state; "
            "the bundle needs at least one project seed"
        )
    moment = now if now is not None else datetime.datetime.now()
    today = moment.strftime("%Y-%m-%d")

    workspace_manifest = load_workspace_manifest(workspace_dir)
    creator_profile_id = workspace_manifest["creator_profile_id"]
    suffix = creator_id_suffix(creator_profile_id)

    entry_path = _entry_path(workspace_dir, entry_id)
    if not entry_path.exists():
        raise ValidationError(f"idea queue entry not found: {entry_path}")
    entry = load_json(entry_path)
    validate_record("idea-queue-entry", entry)
    if entry["creator_profile_id"] != creator_profile_id:
        raise ValidationError(
            f"entry {entry_id} belongs to {entry['creator_profile_id']!r}, "
            f"not this workspace's {creator_profile_id!r}"
        )
    active = _active_linked_promotion(workspace_dir, entry)
    if active is not None:
        raise ValidationError(
            f"entry {entry_id} already has active promotion {active}; "
            "supersede it explicitly before staging a new package"
        )
    if not entry.get("intended_emotion") or not entry.get("core_message"):
        raise ValidationError(
            f"entry {entry_id} lacks the intent pair (intended_emotion, "
            "core_message); add it to the entry with the user before "
            "promotion (ADR 0024)"
        )

    promotion_id = seed.get("idea_promotion_id") or next_sequenced_id(
        f"idea_promotion_{suffix}", _existing_promotion_ids(workspace_dir)
    )

    existing_project_ids = set(collect_project_manifests(workspace_dir))
    seen_slugs = set()
    project_builds = []
    for project_seed in seed["projects"]:
        project_seed = dict(project_seed)
        check_seed_fields(
            project_seed,
            BUNDLE_PROJECT_SEED_REQUIRED,
            BUNDLE_PROJECT_SEED_OPTIONAL,
            f"bundle project {project_seed.get('project_slug', '?')}",
        )
        evidence_brief = project_seed.pop("evidence_brief", None)
        slug = project_seed["project_slug"]
        if slug in seen_slugs:
            raise ValidationError(
                f"bundle names project slug {slug!r} twice; each project "
                "needs its own slug"
            )
        seen_slugs.add(slug)
        if (workspace_dir / "projects" / slug).exists():
            raise ValidationError(
                f"project folder already exists for slug {slug!r}; commit "
                "would fail mid-sequence"
            )
        project_id = project_seed.get("project_id") or next_sequenced_id(
            f"project_{suffix}_{id_token(project_seed['project_slug'])}",
            existing_project_ids,
        )
        if project_id in existing_project_ids:
            raise ValidationError(f"project id already exists: {project_id}")
        existing_project_ids.add(project_id)
        project_builds.append((project_seed, project_id, evidence_brief))

    promotion = {
        "idea_promotion_id": promotion_id,
        "idea_queue_entry_id": entry_id,
        "creator_profile_id": creator_profile_id,
        "approved_by": "user",
        # Provisional so the draft validates; commit re-stamps (ADR 0042).
        "approved_on": today,
        "intended_payoff": entry["intended_payoff"],
        "intended_emotion": entry["intended_emotion"],
        "core_message": entry["core_message"],
        "approved_platforms": list(seed["approved_platforms"]),
        "approved_formats": list(seed["approved_formats"]),
        "research_finding_ids": list(entry.get("source_finding_ids", [])),
        "evidence_refs": deepcopy(entry["evidence_refs"]),
        "score_snapshot": deepcopy(entry["scores"]),
        "creative_elements_to_carry_forward": list(
            seed.get("creative_elements_to_carry_forward", [])
        ),
        "project_ids_created": [
            project_id for _seed, project_id, _brief in project_builds
        ],
        "promotion_status": "active",
    }
    if seed.get("approval_note"):
        promotion["approval_note"] = seed["approval_note"]
    if seed.get("schedule_slot_ids"):
        promotion["schedule_slot_ids"] = list(seed["schedule_slot_ids"])
    validate_record("idea-promotion", promotion)
    validate_intent_carry_forward(promotion, entry)

    staged_projects = []
    for project_seed, project_id, _brief in project_builds:
        project_seed = {**project_seed, "idea_promotion_id": promotion_id}
        staged_projects.append(
            build_project_manifest(
                project_seed,
                creator_profile_id=creator_profile_id,
                promotion=promotion,
                project_id=project_id,
                today=today,
            )
        )

    warnings = _gate_preflight(
        workspace_dir, promotion, staged_projects, entry, today
    )

    stage_id = f"stage_{promotion_id}"
    stage_dir = workspace_dir / STAGING_DIR / stage_id
    if stage_dir.exists():
        raise FileExistsError(f"Stage already exists: {stage_dir}")
    records_dir = stage_dir / "records"
    records_dir.mkdir(parents=True)
    write_json_atomic(records_dir / "idea-promotion.json", promotion)
    for project, (_seed, _project_id, evidence_brief) in zip(
        staged_projects, project_builds
    ):
        project_dir = records_dir / "projects" / project["project_slug"]
        project_dir.mkdir(parents=True)
        write_json_atomic(project_dir / "project.json", project)
        if evidence_brief is not None:
            (project_dir / "evidence-brief.md").write_text(evidence_brief)

    stage_manifest = {
        "stage_id": stage_id,
        "kind": "promotion",
        "created_at": moment.strftime("%Y-%m-%dT%H:%M:%S"),
        "creator_profile_id": creator_profile_id,
        "idea_queue_entry_id": entry_id,
        "idea_promotion_id": promotion_id,
        "project_ids": promotion["project_ids_created"],
        "project_slugs": [
            project["project_slug"] for project in staged_projects
        ],
        "input_hashes": _input_hashes(
            workspace_dir,
            entry_id,
            promotion.get("schedule_slot_ids", []),
            promotion_id,
        ),
        "gate_warnings": warnings,
    }
    write_json_atomic(stage_dir / STAGE_MANIFEST_NAME, stage_manifest)
    return {
        "stage_dir": stage_dir,
        "stage_id": stage_id,
        "promotion": promotion,
        "projects": staged_projects,
        "warnings": warnings,
    }


def _resolve_stage_dir(stage, creator_workspace):
    stage_dir = Path(stage)
    if not stage_dir.exists():
        candidate = Path(creator_workspace) / STAGING_DIR / str(stage)
        if candidate.exists():
            stage_dir = candidate
    manifest_path = stage_dir / STAGE_MANIFEST_NAME
    if not manifest_path.exists():
        raise FileNotFoundError(f"No stage manifest at {manifest_path}")
    return stage_dir, load_json(manifest_path)


def commit_stage(stage, creator_workspace, now=None):
    """Commit a staged promotion bundle at the human approval gate: verify
    the stage is not stale, stamp approval, write canonically in
    construction order, apply the flips, validate, and rebuild
    projections."""
    workspace_dir = Path(creator_workspace)
    stage_dir, stage_manifest = _resolve_stage_dir(stage, workspace_dir)
    if stage_manifest.get("kind") != "promotion":
        raise ValidationError(
            f"stage {stage_manifest.get('stage_id')} has kind "
            f"{stage_manifest.get('kind')!r}; only promotion bundles commit here"
        )
    moment = now if now is not None else datetime.datetime.now()
    today = moment.strftime("%Y-%m-%d")

    entry_id = stage_manifest["idea_queue_entry_id"]
    promotion_id = stage_manifest["idea_promotion_id"]

    # Stale-stage check: fail closed on any upstream drift since staging.
    current_hashes = _input_hashes(
        workspace_dir,
        entry_id,
        sorted(stage_manifest["input_hashes"]["slots"]),
        promotion_id,
    )
    if current_hashes != stage_manifest["input_hashes"]:
        raise ValidationError(
            f"stage {stage_manifest['stage_id']} is stale: its upstream "
            "inputs changed since staging; discard and re-stage from the "
            "current entry/schedule (stages are never patched)"
        )

    records_dir = stage_dir / "records"
    promotion = load_json(records_dir / "idea-promotion.json")
    promotion["approved_on"] = today
    validate_record("idea-promotion", promotion)

    staged_projects = []
    briefs = {}
    for slug in stage_manifest["project_slugs"]:
        project_dir = records_dir / "projects" / slug
        project = load_json(project_dir / "project.json")
        validate_record("project", project)
        staged_projects.append(project)
        brief_path = project_dir / "evidence-brief.md"
        if brief_path.exists():
            briefs[slug] = brief_path.read_text()

    for slug in stage_manifest["project_slugs"]:
        if (workspace_dir / "projects" / slug).exists():
            raise ValidationError(
                f"project folder already exists for slug {slug!r}; a "
                "colliding project landed since staging — re-stage"
            )

    entry = load_json(_entry_path(workspace_dir, entry_id))
    validate_record("idea-queue-entry", entry)
    warnings = _gate_preflight(
        workspace_dir, promotion, staged_projects, entry, today
    )

    # Prepare every flip before the first canonical write.
    flipped_entry = _flipped_entry(entry, promotion, today)
    queue_manifest_path = _queue_manifest_path(workspace_dir)
    flipped_queue = _flipped_queue_manifest(
        load_json(queue_manifest_path), entry_id, today
    )
    slot_ids = promotion.get("schedule_slot_ids", [])
    flipped_schedule = None
    if slot_ids:
        flipped_schedule = _flipped_schedule(
            load_json(_schedule_path(workspace_dir)), slot_ids
        )

    promotion_path = (
        workspace_dir / "research" / "idea-promotions" / f"{promotion_id}.json"
    )
    if promotion_path.exists():
        raise FileExistsError(f"Promotion already exists: {promotion_path}")

    # Construction order (promote-idea contract): promotion -> projects ->
    # evidence briefs -> entry and manifest flip -> schedule slots ->
    # validate -> rebuild.
    promotion_path.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(promotion_path, promotion)
    project_dirs = []
    for project in staged_projects:
        project_dir = create_project_from_manifest(project, workspace_dir)
        brief = briefs.get(project["project_slug"])
        if brief is not None:
            (project_dir / "evidence-brief.md").write_text(brief)
        project_dirs.append(project_dir)
    write_json_atomic(_entry_path(workspace_dir, entry_id), flipped_entry)
    write_json_atomic(queue_manifest_path, flipped_queue)
    if flipped_schedule is not None:
        write_json_atomic(_schedule_path(workspace_dir), flipped_schedule)

    validate_queue(workspace_dir)
    validate_research(workspace_dir)
    for project_dir in project_dirs:
        validate_project(project_dir)
    # Projections are rebuildable derivations of the now-validated canonical
    # records; a rebuild fault (e.g. a non-standard index root) must not fail
    # the committed promotion.
    for rebuild in (rebuild_board, rebuild_index):
        try:
            rebuild(workspace_dir)
        except (ValidationError, ValueError, FileNotFoundError) as exc:
            warnings.append(f"warning: {rebuild.__name__} failed: {exc}")

    shutil.rmtree(stage_dir)
    return {
        "promotion_path": promotion_path,
        "promotion_id": promotion_id,
        "project_dirs": project_dirs,
        "warnings": warnings,
    }
