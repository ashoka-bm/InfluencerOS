"""Generation OS record writers and at-rest checks (ADR 0023, Phase 3).

Slice 2: the GenerationApprovalRecord writer. The record is the gate's
artifact: `dispatch_generation` refuses without an approved one, and this
writer refuses to record an approval whose refs do not resolve — the human
must have seen a real plan for a real project (or a real reference asset).
"""

import json
from pathlib import Path

from influencer_os.providers.registry import get_provider
from influencer_os.validation import ValidationError, load_json, validate_record


PROJECT_APPROVALS_DIR = "generation/approval-records"
REFERENCE_APPROVALS_DIR = "references/approval-records"


def record_generation_approval(target_path, record_path):
    """Validate and write a GenerationApprovalRecord.

    Project scope: ``target_path`` is the project directory; the record's
    project_id must match, the owning workspace's creator must match, the
    project must be at ``ready_for_generation`` or later, and ``plan_ref``
    must resolve inside the project. Reference scope: ``target_path`` is the
    creator workspace; ``reference_asset_id`` must resolve in the Reference
    Library. Records are write-once — supersede by cancelling and writing a
    new one, never by editing.
    """
    from influencer_os.projects import (
        PROJECT_STATUS_ORDER,
        _ensure_contained_file,
        _locate_workspace,
    )

    target_path = Path(target_path)
    record = load_json(record_path)
    validate_record("generation-approval-record", record)
    record_id = record["generation_approval_record_id"]

    try:
        get_provider(record["provider_id"])
    except KeyError as exc:
        raise ValidationError(str(exc)) from None

    if "project_id" in record:
        project_dir = target_path
        manifest_path = project_dir / "project.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Missing project manifest: {manifest_path}")
        project = load_json(manifest_path)
        if project["project_id"] != record["project_id"]:
            raise ValidationError(
                f"generation approval {record_id} targets project "
                f"{record['project_id']!r} but {project_dir} is "
                f"{project['project_id']!r}"
            )
        if project["creator_profile_id"] != record["creator_profile_id"]:
            raise ValidationError(
                f"generation approval {record_id} creator does not match the "
                f"project: {record['creator_profile_id']!r} != "
                f"{project['creator_profile_id']!r}"
            )
        if PROJECT_STATUS_ORDER[project["status"]] < PROJECT_STATUS_ORDER["ready_for_generation"]:
            raise ValidationError(
                f"generation approval {record_id}: project status "
                f"{project['status']!r} is before 'ready_for_generation'; "
                "finish planning before approving generation"
            )
        _resolve_plan_ref(project_dir, record_id, record["plan_ref"])
        destination_dir = project_dir / PROJECT_APPROVALS_DIR
    else:
        workspace_dir = target_path
        library_path = workspace_dir / "references" / "reference-library.json"
        if not library_path.exists():
            raise FileNotFoundError(f"Missing reference library: {library_path}")
        library = load_json(library_path)
        asset_ids = {asset["asset_id"] for asset in library["assets"]}
        if record["reference_asset_id"] not in asset_ids:
            raise ValidationError(
                f"generation approval {record_id}: reference_asset_id "
                f"{record['reference_asset_id']!r} does not resolve in the "
                "Reference Library"
            )
        if library["creator_profile_id"] != record["creator_profile_id"]:
            raise ValidationError(
                f"generation approval {record_id} creator does not match the "
                "Reference Library owner"
            )
        destination_dir = workspace_dir / REFERENCE_APPROVALS_DIR

    destination = destination_dir / f"{record_id}.json"
    if destination.exists():
        raise FileExistsError(
            f"Generation approval already recorded: {destination}; supersede "
            "by cancelling it and recording a new approval"
        )
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    return destination


def _resolve_plan_ref(project_dir, record_id, plan_ref):
    """plan_ref names the plan file the human approved; the fragment after
    '#' (a prompt pointer) is prose for the human, the file must exist."""
    from influencer_os.projects import _ensure_contained_file

    file_part = plan_ref.split("#", 1)[0]
    relative = Path(file_part)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValidationError(
            f"generation approval {record_id}: plan_ref must be a relative "
            f"path inside the project: {plan_ref!r}"
        )
    plan_path = Path(project_dir) / relative
    if not plan_path.exists():
        raise ValidationError(
            f"generation approval {record_id}: plan_ref does not resolve to "
            f"a file: {plan_ref!r}"
        )
    _ensure_contained_file(plan_path, project_dir, f"generation approval {record_id} plan_ref")


def validate_project_generation_records(project_dir, project):
    """At-rest checks for generation/approval-records/*.json (slice 2)."""
    approvals_dir = Path(project_dir) / PROJECT_APPROVALS_DIR
    records_by_id = {}
    if not approvals_dir.exists():
        return records_by_id
    for record_path in sorted(approvals_dir.glob("*.json")):
        record = load_json(record_path)
        try:
            validate_record("generation-approval-record", record)
        except ValidationError as exc:
            raise ValidationError(f"{record_path}: {exc}") from None
        record_id = record["generation_approval_record_id"]
        if record_id != record_path.stem:
            raise ValidationError(
                f"{record_path}: filename does not match "
                f"generation_approval_record_id {record_id!r}"
            )
        if record.get("project_id") != project["project_id"]:
            raise ValidationError(
                f"generation approval {record_id} does not target this "
                f"project: {record.get('project_id')!r} != "
                f"{project['project_id']!r}"
            )
        if record["creator_profile_id"] != project["creator_profile_id"]:
            raise ValidationError(
                f"generation approval {record_id} creator does not match the "
                "project"
            )
        _resolve_plan_ref(project_dir, record_id, record["plan_ref"])
        records_by_id[record_id] = record
    return records_by_id


def validate_reference_approval_records(workspace_dir, reference_library):
    """At-rest checks for references/approval-records/*.json plus the
    Reference Library parity rule: a source_ref that claims an approval
    record (gen_approval_*) must resolve to one (slice 2/3)."""
    workspace_dir = Path(workspace_dir)
    approvals_dir = workspace_dir / REFERENCE_APPROVALS_DIR
    asset_ids = {asset["asset_id"] for asset in reference_library["assets"]}
    records_by_id = {}
    if approvals_dir.exists():
        for record_path in sorted(approvals_dir.glob("*.json")):
            record = load_json(record_path)
            try:
                validate_record("generation-approval-record", record)
            except ValidationError as exc:
                raise ValidationError(f"{record_path}: {exc}") from None
            record_id = record["generation_approval_record_id"]
            if record_id != record_path.stem:
                raise ValidationError(
                    f"{record_path}: filename does not match "
                    f"generation_approval_record_id {record_id!r}"
                )
            if "reference_asset_id" not in record:
                raise ValidationError(
                    f"generation approval {record_id}: records under "
                    f"{REFERENCE_APPROVALS_DIR} must be reference-scoped"
                )
            if record["reference_asset_id"] not in asset_ids:
                raise ValidationError(
                    f"generation approval {record_id}: reference_asset_id "
                    f"{record['reference_asset_id']!r} does not resolve in "
                    "the Reference Library"
                )
            records_by_id[record_id] = record

    for asset in reference_library["assets"]:
        source_ref = asset.get("source", {}).get("source_ref", "")
        if source_ref.startswith("gen_approval_") and source_ref not in records_by_id:
            raise ValidationError(
                f"reference asset {asset['asset_id']} claims approval record "
                f"{source_ref!r} but no such record exists under "
                f"{REFERENCE_APPROVALS_DIR}"
            )
    return records_by_id
