"""Staged pre-approval concept bundles (ADR 0042 stage/commit, retargeted
to the campaign model by ADR 0029/0031).

``stage_concept_approval`` builds the entire draft set behind the concept
approval gate — the locked approval, one project manifest per embedded
project seed, optional authored evidence briefs, and the planned concept /
schedule flips — into ``system/staging/<stage_id>/``, prevalidated against
the same gate that guards the canonical write. Staging touches no
canonical path, so it can run speculatively while the human reads the
package (present-from-draft: the human approves exactly the bytes commit
will write).

``commit_stage`` re-verifies content hashes of the upstream inputs the
stage was derived from (a stale stage fails closed and is re-staged, never
patched) and of the staged records themselves, then parses the exact
verified byte snapshot (the human approves exactly the staged bytes; a
post-presentation edit fails closed). The single commit-owned delta is the
approval's ``approved_on``, provisional at stage time and re-stamped to
the commit day; every other staged field commits byte-exact. Commit then
writes the records in the required construction order, applies the flips,
runs at-rest validation, and rebuilds the board and recall-index
projections.

The approval and its exact project set are one transactional operation
(ADR 0029): project ids are allocated into the approval snapshot at stage
time, and an in-process failure mid-commit rolls back every canonical
write, so a partial approval/project set never rests canonical. Only a
hard crash inside the write window can leave residue, which at-rest
validation rejects (an approval listing a missing project is invalid
state); ``validate all`` pinpoints it.
"""

import datetime
import hashlib
import json
import shutil
from copy import deepcopy
from pathlib import Path

from influencer_os.calendars import schedule_research_state_errors
from influencer_os.campaigns import campaign_dir
from influencer_os.readiness import require_production_ready
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
    rebuild_projections,
)
from influencer_os.json_io import write_json_atomic
from influencer_os.projects import validate_project
from influencer_os.research import (
    collect_project_manifests,
    find_campaign_concept,
    validate_approval_gate,
    validate_queue,
    validate_research,
)
from influencer_os.validation import (
    ValidationError,
    load_json,
    validate_record,
)

STAGE_MANIFEST_NAME = "stage.json"

APPROVAL_SEED_REQUIRED = (
    "approved_platforms",
    "approved_formats",
    "max_offer_integration",
    "max_cta_intensity",
    "projects",
)
APPROVAL_SEED_OPTIONAL = (
    "approval_note",
    "concept_approval_id",
)

# The embedded project seeds omit concept_approval_id (the bundle owns it)
# and may add an authored evidence-brief body plus per-project slot claims.
BUNDLE_PROJECT_SEED_REQUIRED = (
    "project_slug",
    "content_unit_type",
    "platform_targets",
    "learning_goal",
    "acceptance_criteria",
    "commercial_expression",
)
BUNDLE_PROJECT_SEED_OPTIONAL = (
    "constraints",
    "dependencies",
    "notes",
    "reference_asset_ids",
    "target_formats",
    "project_id",
    "schedule_slot_ids",
    "evidence_brief",
)


def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _staged_record_bytes(records_dir):
    """One snapshot of every staged record file's bytes, keyed by posix
    path relative to the records dir. Commit hashes, parses, and writes
    from this single read, so the verified bytes are the committed bytes
    (no window between hashing and loading)."""
    return {
        path.relative_to(records_dir).as_posix(): path.read_bytes()
        for path in sorted(records_dir.rglob("*"))
        if path.is_file()
    }


def _staged_record_hashes(records_dir):
    """Content hashes of every staged record file, keyed by posix path
    relative to the records dir. The stage manifest pins these so commit
    writes exactly the bytes the human reviewed (ADR 0042); any edit,
    addition, or removal under records/ after staging fails the commit."""
    return {
        rel: _sha256_bytes(data)
        for rel, data in _staged_record_bytes(records_dir).items()
    }


def _sha256_record(record):
    return _sha256_bytes(
        json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    )


def _concept_path(workspace_dir, concept):
    return (
        campaign_dir(workspace_dir, concept["campaign_id"]) / "concepts"
        / f"{concept['campaign_concept_id']}.json"
    )


def _schedule_path(workspace_dir):
    return Path(workspace_dir) / "content-schedule.json"


def _claimed_slots(schedule, slot_ids, approval_id):
    slots = {slot["slot_id"]: slot for slot in schedule.get("calendar_slots", [])}
    claimed = {}
    for slot_id in slot_ids:
        if slot_id not in slots:
            raise ValidationError(
                f"approval {approval_id} claims {slot_id!r}, which resolves "
                "to no schedule slot"
            )
        claimed[slot_id] = slots[slot_id]
    return claimed


def _input_hashes(workspace_dir, concept, slot_ids, approval_id):
    """Content hashes of exactly the upstream state the stage was derived
    from: the concept file and each claimed slot. Unrelated campaign or
    schedule changes do not invalidate a stage."""
    hashes = {
        "concept": _sha256_bytes(
            _concept_path(workspace_dir, concept).read_bytes()
        )
    }
    if slot_ids:
        schedule = load_json(_schedule_path(workspace_dir))
        claimed = _claimed_slots(schedule, slot_ids, approval_id)
        hashes["slots"] = {
            slot_id: _sha256_record(slot) for slot_id, slot in claimed.items()
        }
    else:
        hashes["slots"] = {}
    return hashes


def _existing_approval_ids(workspace_dir):
    ids = set()
    for approval_path in Path(workspace_dir).glob("campaigns/*/approvals/*.json"):
        ids.add(approval_path.stem)
    staging_root = Path(workspace_dir) / STAGING_DIR
    if staging_root.exists():
        for stage_manifest in staging_root.glob(f"*/{STAGE_MANIFEST_NAME}"):
            staged = load_json(stage_manifest)
            if "concept_approval_id" in staged:
                ids.add(staged["concept_approval_id"])
    return ids


def _flipped_concept(concept, today):
    flipped = deepcopy(concept)
    flipped["status"] = "active"
    flipped["updated_on"] = today
    validate_record("campaign-concept", flipped)
    return flipped


def _flipped_schedule(schedule, slot_projects, concept):
    """Claimed slots flip to filled and gain their ownership refs: the
    owning campaign, concept, and (per the slot mapping) project."""
    flipped = deepcopy(schedule)
    for slot in flipped.get("calendar_slots", []):
        if slot["slot_id"] in slot_projects:
            slot["status"] = "filled"
            slot["campaign_id"] = concept["campaign_id"]
            slot["campaign_concept_id"] = concept["campaign_concept_id"]
            slot["project_id"] = slot_projects[slot["slot_id"]]
    validate_record("creator-content-schedule", flipped)
    state_errors = schedule_research_state_errors(flipped)
    if state_errors:
        raise ValidationError("; ".join(state_errors))
    return flipped


def _gate_preflight(workspace_dir, approval, staged_projects, concept, today):
    """Run the real approval gate against the simulated post-commit state:
    flipped concept, flipped schedule, and the staged projects merged over
    the existing manifests."""
    flipped_concept = _flipped_concept(concept, today)
    slot_ids = approval.get("schedule_slot_ids", [])
    flipped_schedule = None
    if slot_ids:
        schedule_path = _schedule_path(workspace_dir)
        if not schedule_path.exists():
            raise ValidationError(
                f"approval {approval['concept_approval_id']} claims schedule "
                "slots but the workspace has no content-schedule.json"
            )
        slot_projects = {
            slot_id: project_id
            for project_id, claimed in _project_slot_claims(
                approval, staged_projects
            ).items()
            for slot_id in claimed
        }
        flipped_schedule = _flipped_schedule(
            load_json(schedule_path), slot_projects, concept
        )
    projects_by_id = dict(collect_project_manifests(workspace_dir))
    for project in staged_projects:
        projects_by_id[project["project_id"]] = (None, project)
    return validate_approval_gate(
        workspace_dir,
        approval,
        projects_by_id=projects_by_id,
        concept=flipped_concept,
        schedule=flipped_schedule,
        # A fresh approval never enters canon with dangling provenance; the
        # human-approved leniency exists only for at-rest re-validation of
        # historical approvals whose research was later pruned.
        strict_evidence=True,
    )


def _project_slot_claims(approval, staged_projects):
    """Map project_id -> claimed slot ids from the stage manifest's
    project_slots block (rebuilt at commit from the manifest)."""
    return {
        project["project_id"]: project.get("_slot_claims", [])
        for project in staged_projects
    }


def stage_concept_approval(seed, creator_workspace, concept_id, now=None):
    """Build the full concept-approval draft bundle into system/staging/,
    prevalidated through the real gate. Writes nothing canonical."""
    workspace_dir = Path(creator_workspace)
    require_production_ready(workspace_dir)
    seed = load_seed(seed)
    check_seed_fields(
        seed, APPROVAL_SEED_REQUIRED, APPROVAL_SEED_OPTIONAL, "approval"
    )
    if not seed["projects"]:
        raise ValidationError(
            "an approval that creates no production work is invalid state; "
            "the bundle needs at least one project seed"
        )
    moment = now if now is not None else datetime.datetime.now()
    today = moment.strftime("%Y-%m-%d")

    workspace_manifest = load_workspace_manifest(workspace_dir)
    creator_profile_id = workspace_manifest["creator_profile_id"]
    suffix = creator_id_suffix(creator_profile_id)

    concept = find_campaign_concept(workspace_dir, concept_id)
    if concept is None:
        raise ValidationError(
            f"campaign concept not found: {concept_id!r} resolves to no "
            "concept under campaigns/*/concepts/"
        )
    validate_record("campaign-concept", concept)
    if concept["creator_profile_id"] != creator_profile_id:
        raise ValidationError(
            f"concept {concept_id} belongs to "
            f"{concept['creator_profile_id']!r}, not this workspace's "
            f"{creator_profile_id!r}"
        )
    # One unchanged concept may receive later approvals for additional
    # projects (campaign-concept-pressure plan); no active-approval guard.
    if concept["status"] not in {"ready_for_approval", "active"}:
        raise ValidationError(
            f"concept {concept_id} has status {concept['status']!r}; only a "
            "ready_for_approval or active concept can receive an approval"
        )
    if not concept.get("intended_emotion") or not concept.get("core_message"):
        raise ValidationError(
            f"concept {concept_id} lacks the intent pair (intended_emotion, "
            "core_message); add it to the concept with the user before "
            "approval (ADR 0024)"
        )

    approval_id = seed.get("concept_approval_id") or next_sequenced_id(
        f"concept_approval_{suffix}", _existing_approval_ids(workspace_dir)
    )

    existing_project_ids = set(collect_project_manifests(workspace_dir))
    seen_slugs = set()
    slot_owners = {}
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
        slot_claims = list(project_seed.pop("schedule_slot_ids", []))
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
        for slot_id in slot_claims:
            earlier = slot_owners.setdefault(slot_id, project_id)
            if earlier != project_id:
                raise ValidationError(
                    f"bundle claims slot {slot_id} for two projects "
                    f"({earlier} and {project_id}); a slot hosts one "
                    "publishable unit"
                )
        project_builds.append(
            (project_seed, project_id, slot_claims, evidence_brief)
        )

    approval = {
        "concept_approval_id": approval_id,
        "campaign_concept_id": concept_id,
        "creator_profile_id": creator_profile_id,
        "approved_by": "user",
        # Provisional so the draft validates; commit re-stamps (ADR 0042).
        "approved_on": today,
        "approval_status": "active",
        "intended_payoff": concept["intended_payoff"],
        "intended_emotion": concept["intended_emotion"],
        "core_message": concept["core_message"],
        "approved_platforms": list(seed["approved_platforms"]),
        "approved_formats": list(seed["approved_formats"]),
        "max_offer_integration": seed["max_offer_integration"],
        "max_cta_intensity": seed["max_cta_intensity"],
        "evidence_refs": deepcopy(concept["evidence_refs"]),
        "project_ids_created": [
            project_id for _seed, project_id, _slots, _brief in project_builds
        ],
    }
    if seed.get("approval_note"):
        approval["approval_note"] = seed["approval_note"]
    claimed_slot_ids = sorted(slot_owners)
    if claimed_slot_ids:
        approval["schedule_slot_ids"] = claimed_slot_ids
    validate_record("concept-approval", approval)

    staged_projects = []
    for project_seed, project_id, slot_claims, _brief in project_builds:
        project_seed = {**project_seed, "concept_approval_id": approval_id}
        project = build_project_manifest(
            project_seed,
            creator_profile_id=creator_profile_id,
            approval=approval,
            concept=concept,
            project_id=project_id,
            today=today,
        )
        project["_slot_claims"] = slot_claims
        staged_projects.append(project)

    warnings = _gate_preflight(
        workspace_dir, approval, staged_projects, concept, today
    )
    for project in staged_projects:
        project.pop("_slot_claims", None)

    stage_id = f"stage_{approval_id}"
    stage_dir = workspace_dir / STAGING_DIR / stage_id
    if stage_dir.exists():
        raise FileExistsError(f"Stage already exists: {stage_dir}")
    records_dir = stage_dir / "records"
    records_dir.mkdir(parents=True)
    write_json_atomic(records_dir / "concept-approval.json", approval)
    for project, (_seed, _project_id, _slots, evidence_brief) in zip(
        staged_projects, project_builds
    ):
        project_dir = records_dir / "projects" / project["project_slug"]
        project_dir.mkdir(parents=True)
        write_json_atomic(project_dir / "project.json", project)
        if evidence_brief is not None:
            (project_dir / "evidence-brief.md").write_text(evidence_brief)

    stage_manifest = {
        "stage_id": stage_id,
        "kind": "concept-approval",
        "created_at": moment.strftime("%Y-%m-%dT%H:%M:%S"),
        "creator_profile_id": creator_profile_id,
        "campaign_id": concept["campaign_id"],
        "campaign_concept_id": concept_id,
        "concept_approval_id": approval_id,
        "project_ids": approval["project_ids_created"],
        "project_slugs": [
            project["project_slug"] for project in staged_projects
        ],
        "project_slots": {
            project_id: slots
            for _seed, project_id, slots, _brief in project_builds
        },
        "input_hashes": _input_hashes(
            workspace_dir,
            concept,
            claimed_slot_ids,
            approval_id,
        ),
        "record_hashes": _staged_record_hashes(records_dir),
        "gate_warnings": warnings,
    }
    write_json_atomic(stage_dir / STAGE_MANIFEST_NAME, stage_manifest)
    return {
        "stage_dir": stage_dir,
        "stage_id": stage_id,
        "approval": approval,
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
    """Commit a staged concept-approval bundle at the human approval gate:
    verify the stage is not stale, stamp approval, write canonically in
    construction order, apply the flips, validate, and rebuild
    projections."""
    workspace_dir = Path(creator_workspace)
    stage_dir, stage_manifest = _resolve_stage_dir(stage, workspace_dir)
    if stage_manifest.get("kind") != "concept-approval":
        raise ValidationError(
            f"stage {stage_manifest.get('stage_id')} has kind "
            f"{stage_manifest.get('kind')!r}; only concept-approval bundles "
            "commit here"
        )
    moment = now if now is not None else datetime.datetime.now()
    today = moment.strftime("%Y-%m-%d")

    concept_id = stage_manifest["campaign_concept_id"]
    approval_id = stage_manifest["concept_approval_id"]

    concept = find_campaign_concept(workspace_dir, concept_id)
    if concept is None:
        raise ValidationError(
            f"stage {stage_manifest['stage_id']} approves concept "
            f"{concept_id!r}, which no longer resolves"
        )

    # Stale-stage check: fail closed on any upstream drift since staging.
    current_hashes = _input_hashes(
        workspace_dir,
        concept,
        sorted(stage_manifest["input_hashes"]["slots"]),
        approval_id,
    )
    if current_hashes != stage_manifest["input_hashes"]:
        raise ValidationError(
            f"stage {stage_manifest['stage_id']} is stale: its upstream "
            "inputs changed since staging; discard and re-stage from the "
            "current concept/schedule (stages are never patched)"
        )

    # Byte-pin check: the human approved exactly the staged bytes; a stage
    # whose records were touched after presentation fails closed, like a
    # stale stage (a missing record_hashes block also mismatches and fails).
    # Everything below parses this one snapshot, so the verified bytes are
    # the committed bytes.
    records_dir = stage_dir / "records"
    staged_bytes = _staged_record_bytes(records_dir)
    staged_hashes = {
        rel: _sha256_bytes(data) for rel, data in staged_bytes.items()
    }
    if stage_manifest.get("record_hashes") != staged_hashes:
        raise ValidationError(
            f"stage {stage_manifest['stage_id']} records do not match the "
            "hashes pinned at staging; the human approves exactly the staged "
            "bytes (ADR 0042) — discard and re-stage"
        )
    approval = json.loads(staged_bytes["concept-approval.json"])
    # The single commit-owned delta from the staged bytes: approved_on is
    # provisional at stage time (so the draft validates) and re-stamped to
    # the actual approval day here (ADR 0042). Every other field commits
    # byte-exact.
    approval["approved_on"] = today
    validate_record("concept-approval", approval)

    staged_projects = []
    briefs = {}
    for slug in stage_manifest["project_slugs"]:
        project = json.loads(staged_bytes[f"projects/{slug}/project.json"])
        validate_record("project", project)
        staged_projects.append(project)
        brief_key = f"projects/{slug}/evidence-brief.md"
        if brief_key in staged_bytes:
            briefs[slug] = staged_bytes[brief_key].decode()

    for slug in stage_manifest["project_slugs"]:
        if (workspace_dir / "projects" / slug).exists():
            raise ValidationError(
                f"project folder already exists for slug {slug!r}; a "
                "colliding project landed since staging — re-stage"
            )

    for project in staged_projects:
        project["_slot_claims"] = stage_manifest["project_slots"].get(
            project["project_id"], []
        )
    warnings = _gate_preflight(
        workspace_dir, approval, staged_projects, concept, today
    )
    for project in staged_projects:
        project.pop("_slot_claims", None)

    # Prepare every flip before the first canonical write.
    flipped_concept = _flipped_concept(concept, today)
    slot_ids = approval.get("schedule_slot_ids", [])
    flipped_schedule = None
    if slot_ids:
        slot_projects = {
            slot_id: project_id
            for project_id, slots in stage_manifest["project_slots"].items()
            for slot_id in slots
        }
        flipped_schedule = _flipped_schedule(
            load_json(_schedule_path(workspace_dir)), slot_projects, concept
        )

    approval_path = (
        campaign_dir(workspace_dir, concept["campaign_id"]) / "approvals"
        / f"{approval_id}.json"
    )
    if approval_path.exists():
        raise FileExistsError(f"Approval already exists: {approval_path}")

    # Snapshot the two overwritten files so a failed commit restores them
    # byte-identically; created paths are simply removed on rollback.
    concept_path = _concept_path(workspace_dir, concept)
    original_concept_bytes = concept_path.read_bytes()
    original_schedule_bytes = (
        _schedule_path(workspace_dir).read_bytes()
        if flipped_schedule is not None
        else None
    )

    # Construction order (approve-concept contract): approval -> projects ->
    # evidence briefs -> concept flip -> schedule slots -> validate ->
    # rebuild. A partial approval/project set is invalid (ADR 0029), so any
    # in-process failure before validation completes rolls every write back
    # and re-raises; the stage survives for retry or discard.
    approval_path.parent.mkdir(parents=True, exist_ok=True)
    project_dirs = []
    try:
        write_json_atomic(approval_path, approval)
        for project in staged_projects:
            project_dir = create_project_from_manifest(project, workspace_dir)
            brief = briefs.get(project["project_slug"])
            if brief is not None:
                (project_dir / "evidence-brief.md").write_text(brief)
            project_dirs.append(project_dir)
        write_json_atomic(concept_path, flipped_concept)
        if flipped_schedule is not None:
            write_json_atomic(_schedule_path(workspace_dir), flipped_schedule)

        queue_manifest_path = (
            workspace_dir / "research" / "content-opportunity-queue"
            / "queue.json"
        )
        if queue_manifest_path.exists():
            validate_queue(workspace_dir)
        validate_research(workspace_dir)
        from influencer_os.campaigns import validate_campaign_records

        validate_campaign_records(workspace_dir)
        for project_dir in project_dirs:
            validate_project(project_dir)
    except BaseException as commit_exc:
        # Each restore step runs independently: one failed step must not
        # strand the later ones, and the original commit failure — never a
        # cleanup error — is what propagates (cleanup faults attach as
        # exception notes; any residue is invalid at rest and `validate
        # all` pinpoints it).
        def _attempt(action):
            try:
                action()
            except Exception as cleanup_exc:
                commit_exc.add_note(
                    f"rollback step failed: {cleanup_exc}"
                )

        _attempt(lambda: approval_path.unlink(missing_ok=True))
        for slug in stage_manifest["project_slugs"]:
            # Safe to remove wholesale: the slug-collision check above
            # guarantees none of these folders predate this commit.
            _attempt(lambda slug=slug: shutil.rmtree(
                workspace_dir / "projects" / slug, ignore_errors=True
            ))
        _attempt(lambda: concept_path.write_bytes(original_concept_bytes))
        if original_schedule_bytes is not None:
            _attempt(lambda: _schedule_path(workspace_dir).write_bytes(
                original_schedule_bytes
            ))
        raise
    warnings.extend(rebuild_projections(workspace_dir))

    # The approval is canonical from here: a stage-cleanup fault must read
    # as a committed approval with a warning, not a failed (and seemingly
    # retryable) commit.
    try:
        shutil.rmtree(stage_dir)
    except OSError as cleanup_exc:
        warnings.append(
            f"warning: approval committed but stage cleanup failed: "
            f"{cleanup_exc}; remove {stage_dir} manually"
        )
    return {
        "approval_path": approval_path,
        "concept_approval_id": approval_id,
        "project_dirs": project_dirs,
        "warnings": warnings,
    }
