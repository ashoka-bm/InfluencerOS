"""Generation OS record writers and at-rest checks (ADR 0023, Phase 3).

Slice 2: the GenerationApprovalRecord writer — the gate's artifact:
`dispatch_generation` refuses without an approved one, and the writer
refuses an approval whose refs do not resolve.

Slices 3-4: the import path and the asset-manifest ledger — every file
under `generation/assets/` gets exactly one manifest row binding it to its
approval record (generated) or import origin (imported/user-provided).
"""

import datetime
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from influencer_os.providers.registry import get_provider
from influencer_os.validation import ValidationError, load_json, validate_record


PROJECT_APPROVALS_DIR = "generation/approval-records"
REFERENCE_APPROVALS_DIR = "references/approval-records"
ASSETS_DIR = "generation/assets"
MANIFEST_PATH = "generation/asset-manifest.json"

UNKNOWN_LICENSE_WARNING = "license-unknown: no license information was provided; verify usage rights before publishing"


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


def load_asset_manifest(project_dir, project=None):
    """The project's manifest ledger, created empty from the project
    manifest on first use."""
    manifest_path = Path(project_dir) / MANIFEST_PATH
    if manifest_path.exists():
        return load_json(manifest_path)
    if project is None:
        project = load_json(Path(project_dir) / "project.json")
    return {
        "project_id": project["project_id"],
        "creator_profile_id": project["creator_profile_id"],
        "rows": [],
    }


def append_manifest_rows(project_dir, rows, project=None):
    """Append rows to the ledger atomically (validate-then-replace): a
    failed append can never leave a truncated or half-written ledger."""
    project_dir = Path(project_dir)
    manifest = load_asset_manifest(project_dir, project=project)
    manifest["rows"] = manifest["rows"] + list(rows)
    validate_record("generation-asset-manifest", manifest)
    manifest_path = project_dir / MANIFEST_PATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        dir=manifest_path.parent, prefix=".asset-manifest.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w") as stream:
            stream.write(json.dumps(manifest, indent=2, allow_nan=False) + "\n")
        os.replace(temp_name, manifest_path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise
    return manifest


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_artifact_filename(filename, context):
    name = Path(filename).name
    if name != filename or name in (".", "..") or not name:
        raise ValidationError(
            f"{context}: filename must be a bare file name, got {filename!r}"
        )
    return name


def import_generated_asset(
    project_path,
    source_file,
    asset_id,
    asset_kind,
    origin="imported",
    filename=None,
    source=None,
    tool_or_provider=None,
    license_text=None,
    creator=None,
    attribution=None,
    warnings=(),
    notes=None,
):
    """Copy an externally generated or user-provided media file into
    `generation/assets/` with a full-provenance manifest row (ADR 0023,
    slice 3). Unknown license is captured as a warning, never guessed.
    """
    project_dir = Path(project_path)
    manifest_path = project_dir / "project.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing project manifest: {manifest_path}")
    project = load_json(manifest_path)
    if origin not in ("imported", "user_provided"):
        raise ValidationError(
            f"import origin must be 'imported' or 'user_provided', got {origin!r}; "
            "generated assets enter through dispatch_generation"
        )

    source_path = Path(source_file)
    if not source_path.is_file():
        raise FileNotFoundError(f"Missing import source file: {source_path}")

    target_name = _safe_artifact_filename(
        filename or source_path.name, f"import-generated-asset {asset_id}"
    )
    assets_dir = project_dir / ASSETS_DIR
    destination = assets_dir / target_name
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Import target already exists: {destination}")

    manifest = load_asset_manifest(project_dir, project=project)
    if any(row["asset_id"] == asset_id for row in manifest["rows"]):
        raise ValidationError(
            f"asset id {asset_id!r} already has a manifest row; import under "
            "a new asset id"
        )

    import_source = {
        "source": source or f"local file {source_path.name} supplied by the operator",
    }
    if tool_or_provider:
        import_source["tool_or_provider"] = tool_or_provider
    if license_text:
        import_source["license"] = license_text
    if creator:
        import_source["creator"] = creator
    if attribution:
        import_source["attribution"] = attribution
    collected_warnings = list(warnings)
    if not license_text and UNKNOWN_LICENSE_WARNING not in collected_warnings:
        collected_warnings.append(UNKNOWN_LICENSE_WARNING)
    if collected_warnings:
        import_source["warnings"] = collected_warnings

    assets_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, destination)
    try:
        row = {
            "asset_id": asset_id,
            "origin": origin,
            "asset_kind": asset_kind,
            "import_source": import_source,
            "artifact_path": f"{ASSETS_DIR}/{target_name}",
            "content_hash": _sha256_file(destination),
            "recorded_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }
        if notes:
            row["notes"] = notes
        append_manifest_rows(project_dir, [row], project=project)
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return destination


def import_reference_asset(
    workspace_path,
    source_file,
    reference_asset_id,
    origin="user_provided",
    approval_record_id=None,
):
    """Reference Library parity for the import path (ADR 0013/0023): copy
    the file to the asset's declared path and update its lifecycle status
    and source block. A generated-elsewhere import may cite the approval
    record that authorized it via ``approval_record_id``."""
    workspace_dir = Path(workspace_path)
    library_path = workspace_dir / "references" / "reference-library.json"
    if not library_path.exists():
        raise FileNotFoundError(f"Missing reference library: {library_path}")
    library = load_json(library_path)

    asset = next(
        (a for a in library["assets"] if a["asset_id"] == reference_asset_id), None
    )
    if asset is None:
        raise ValidationError(
            f"reference asset {reference_asset_id!r} does not resolve in the "
            "Reference Library"
        )
    if origin not in ("imported", "user_provided"):
        raise ValidationError(
            f"import origin must be 'imported' or 'user_provided', got {origin!r}"
        )

    source_path = Path(source_file)
    if not source_path.is_file():
        raise FileNotFoundError(f"Missing import source file: {source_path}")

    if approval_record_id is not None:
        approval_path = (
            workspace_dir / REFERENCE_APPROVALS_DIR / f"{approval_record_id}.json"
        )
        if not approval_path.exists():
            raise ValidationError(
                f"approval record {approval_record_id!r} does not resolve "
                f"under {REFERENCE_APPROVALS_DIR}"
            )

    destination = workspace_dir / asset["path"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, destination)

    asset["asset_status"] = "generated" if origin == "imported" else "user_provided"
    asset["source"] = {
        "source_type": origin,
        "source_ref": approval_record_id
        or f"imported from local file {source_path.name}",
    }
    validate_record("reference-library", library)
    library_path.write_text(json.dumps(library, indent=2, allow_nan=False) + "\n")
    return destination


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
