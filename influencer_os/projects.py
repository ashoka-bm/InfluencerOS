import json
import shutil
from pathlib import Path

from influencer_os.research import validate_promotion_gate
from influencer_os.validation import ValidationError, load_json, validate_file, validate_record


PROJECT_DIRECTORIES = [
    "plan",
    "output-package/assets",
    "output-package/upload-ready",
    "output-package/source-refs",
    "output-package/platform-adaptations",
    "published/published-post-records",
    "analytics/snapshots",
    "analytics/raw",
]

PROJECT_SCAFFOLDS = {
    "performance-summary.md": "# Performance Summary\n\n",
    "evidence-brief.md": "# Evidence Brief\n\nSummarize the promoted idea's evidence for production use.\n\n",
}

PROJECT_STATUS_ORDER = {
    "created": 1,
    "planning": 2,
    "ready_for_generation": 3,
    "generated": 4,
    "packaged": 5,
    "published": 6,
    "analyzed": 7,
    "archived": 8,
}

# Optional source_refs cached from the promotion for convenience; each cached
# value must stay consistent with the locked promotion snapshot.
PROMOTION_CACHED_SUBSETS = (
    ("research_finding_ids", "research_finding_ids"),
    ("research_evidence_ids", "evidence_ids"),
    ("metric_snapshot_ids", "metric_snapshot_ids"),
    ("video_understanding_pack_ids", "video_understanding_pack_ids"),
)

PRODUCTION_PLAN_SCHEMAS = {
    "short_form_video": "micro-journey-video-plan",
    "carousel": "carousel-plan",
    "single_image_post": "single-image-post-plan",
    "story_sequence": "story-sequence-plan",
    "article": "article-plan",
    "thread": "thread-plan",
}

PRODUCTION_PLAN_ID_FIELDS = {
    "micro-journey-video-plan": "micro_journey_video_plan_id",
    "carousel-plan": "carousel_plan_id",
    "single-image-post-plan": "single_image_post_plan_id",
    "story-sequence-plan": "story_sequence_plan_id",
    "article-plan": "article_plan_id",
    "thread-plan": "thread_plan_id",
}

# Research pack ids resolve to <workspace>/<directory>/<pack-id>.json records.
RESEARCH_PACK_LOCATIONS = (
    ("video_research_", "research/video-understanding-packs", "video-understanding-pack", "video_understanding_pack_id"),
    ("research_", "research/social-research-packs", "social-research-pack", "social_research_pack_id"),
)

# The ADR 0020 research platform set, used to map distribution surfaces in
# platform_targets (instagram_reels, tiktok) back to research platforms.
RESEARCH_PLATFORMS = (
    "x", "instagram", "tiktok", "substack", "medium", "reddit", "facebook", "linkedin",
)


def init_project(project_manifest_path, creator_workspace):
    project_manifest_path = Path(project_manifest_path)
    creator_workspace = Path(creator_workspace)
    project = load_json(project_manifest_path)
    validate_record("project", project)
    _validate_content_unit_target_format(project)

    _validate_creator_match(project, creator_workspace)
    _resolve_promotion(project, creator_workspace)

    project_dir = creator_workspace / "projects" / project["project_slug"]
    if project_dir.exists():
        raise FileExistsError(f"Project already exists: {project_dir}")

    for directory in PROJECT_DIRECTORIES:
        (project_dir / directory).mkdir(parents=True, exist_ok=True)

    shutil.copyfile(project_manifest_path, project_dir / "project.json")

    for relative_path, content in PROJECT_SCAFFOLDS.items():
        path = project_dir / relative_path
        if not path.exists():
            path.write_text(content)

    return project_dir


def register_output_package(project_path, output_package_path, asset_root=None):
    project_dir = Path(project_path)
    output_package_path = Path(output_package_path)
    asset_root = Path(asset_root) if asset_root is not None else None
    project_manifest_path = project_dir / "project.json"
    package_destination = project_dir / "output-package" / "output-package.json"

    if package_destination.exists():
        raise FileExistsError(f"Output package already registered: {package_destination}")
    if not project_manifest_path.exists():
        raise FileNotFoundError(f"Missing project manifest: {project_manifest_path}")
    if not output_package_path.exists():
        raise FileNotFoundError(f"Missing output package record: {output_package_path}")
    if asset_root is not None and not asset_root.exists():
        raise FileNotFoundError(f"Missing asset root: {asset_root}")

    project = load_json(project_manifest_path)
    validate_record("project", project)
    _validate_content_unit_target_format(project)
    if _status_at_least(project, "packaged"):
        raise FileExistsError(f"Project is already packaged: {project_dir}")

    # Preflight the current project before mutating it; this checks promotion,
    # creator, template, plan, and generation-plan requirements for the
    # project's current planning status.
    validate_project(project_dir)

    output_package = load_json(output_package_path)
    validate_record("output-package", output_package)
    _validate_output_package_matches_project(output_package, project)
    upload_asset_paths = _upload_ready_relative_paths(output_package)

    original_project_text = project_manifest_path.read_text()
    copied_targets = []
    try:
        for relative_path in upload_asset_paths:
            target = project_dir / relative_path
            source = target if asset_root is None else asset_root / relative_path
            if not source.exists():
                raise FileNotFoundError(f"Missing upload-ready asset: {source}")
            _ensure_contained_file(source, asset_root or project_dir, "upload-ready asset source")
            _ensure_contained_target(target, project_dir, "upload-ready asset destination")
            if source.resolve() == target.resolve():
                continue
            if target.exists():
                raise FileExistsError(f"Upload-ready asset already exists: {target}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            copied_targets.append(target)

        package_destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(output_package_path, package_destination)

        project["status"] = "packaged"
        _write_json(project_manifest_path, project)

        validate_project(project_dir)
    except Exception:
        project_manifest_path.write_text(original_project_text)
        if package_destination.exists():
            package_destination.unlink()
        for target in copied_targets:
            if target.exists():
                target.unlink()
        raise

    return {
        "output_package_id": output_package["output_package_id"],
        "project_id": project["project_id"],
        "project_path": project_dir,
        "output_package_path": package_destination,
        "copied_assets": copied_targets,
    }


def validate_project(project_path):
    project_dir = Path(project_path)
    project_manifest_path = project_dir / "project.json"
    if not project_manifest_path.exists():
        raise FileNotFoundError(f"Missing project manifest: {project_manifest_path}")

    project = load_json(project_manifest_path)
    validate_record("project", project)
    _validate_content_unit_target_format(project)

    expected_root = f"projects/{project['project_slug']}/"
    if project["project_paths"]["root"] != expected_root:
        raise ValueError(f"Project root path does not match project_slug: {project['project_paths']['root']!r}")

    required_paths = ["project.json"]
    required_paths.extend(project["project_paths"][key] for key in ["plan", "output_package", "published", "analytics", "performance_summary", "evidence_brief"])
    required_paths.extend(_required_record_paths(project))

    missing = []
    for relative_path in required_paths:
        if not (project_dir / relative_path).exists():
            missing.append(relative_path)

    if missing:
        raise FileNotFoundError(f"Missing project paths: {', '.join(sorted(missing))}")

    workspace_dir = _locate_workspace(project_dir)
    # Pin the project to the owning workspace creator; the promotion and
    # queue entry pin to the project below, so the whole chain is scoped.
    _validate_creator_match(project, workspace_dir)
    promotion = _resolve_promotion(project, workspace_dir)
    warnings = validate_promotion_gate(workspace_dir, promotion)
    _validate_cached_promotion_refs(project, promotion)
    _resolve_source_refs(project["source_refs"], workspace_dir, "Project source_refs")
    _validate_project_records(project_dir, project, workspace_dir)

    return {
        "project_id": project["project_id"],
        "project_slug": project["project_slug"],
        "project_path": project_dir,
        "checked_paths": sorted(set(required_paths)),
        "warnings": warnings,
    }


def _write_json(path, record):
    path.write_text(json.dumps(record, indent=2) + "\n")


def _validate_output_package_matches_project(output_package, project):
    if output_package["project_id"] != project["project_id"]:
        raise ValueError(
            "Output package project_id does not match project: "
            f"{output_package['project_id']!r} != {project['project_id']!r}"
        )
    if output_package["creator_profile_id"] != project["creator_profile_id"]:
        raise ValueError(
            "Output package creator_profile_id does not match project: "
            f"{output_package['creator_profile_id']!r} != {project['creator_profile_id']!r}"
        )
    expected_format_id = _format_id_for_content_unit(project["content_unit_type"])
    actual_format_id = output_package["universal_core"]["format_id"]
    if actual_format_id != expected_format_id:
        raise ValueError(
            "Output package universal_core.format_id does not match project content_unit_type: "
            f"{actual_format_id!r} != {expected_format_id!r}"
        )
    if output_package["source_refs"]["idea_promotion_id"] != project["source_refs"]["idea_promotion_id"]:
        raise ValueError(
            "Output package idea_promotion_id does not match project source_refs: "
            f"{output_package['source_refs']['idea_promotion_id']!r} != "
            f"{project['source_refs']['idea_promotion_id']!r}"
        )


def _upload_ready_relative_paths(output_package):
    paths = []
    seen = set()
    for asset in output_package["upload_ready"]:
        relative_path = _safe_project_relative_path(
            asset["path"],
            required_prefix=("output-package", "upload-ready"),
            context=f"upload_ready path for {asset['upload_asset_id']}",
        )
        if relative_path in seen:
            raise ValueError(f"Duplicate upload-ready path: {asset['path']!r}")
        seen.add(relative_path)
        paths.append(relative_path)
    return paths


def _safe_project_relative_path(raw_path, required_prefix, context):
    relative_path = Path(raw_path)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"{context} must be a relative path inside the project: {raw_path!r}")
    if tuple(relative_path.parts[: len(required_prefix)]) != tuple(required_prefix):
        expected = "/".join(required_prefix)
        raise ValueError(f"{context} must live under {expected}/: {raw_path!r}")
    if relative_path.name in ("", ".", ".."):
        raise ValueError(f"{context} must name a file: {raw_path!r}")
    return relative_path


def _ensure_contained_file(path, root, context):
    root = Path(root).resolve()
    resolved = Path(path).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"{context} escapes root: {path}")
    if not resolved.is_file():
        raise FileNotFoundError(f"{context} is not a file: {path}")


def _ensure_contained_target(path, root, context):
    root = Path(root).resolve()
    resolved_parent = Path(path).parent.resolve()
    if not resolved_parent.is_relative_to(root):
        raise ValueError(f"{context} escapes project: {path}")


def _validate_creator_match(project, creator_workspace):
    manifest_path = Path(creator_workspace) / "creator-workspace.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing creator workspace manifest: {manifest_path}")

    creator_manifest = load_json(manifest_path)
    validate_record("creator-workspace", creator_manifest)

    if project["creator_profile_id"] != creator_manifest["creator_profile_id"]:
        raise ValueError(
            "Project creator_profile_id does not match creator workspace: "
            f"{project['creator_profile_id']!r} != {creator_manifest['creator_profile_id']!r}"
        )


def _required_record_paths(project):
    required = []
    if _status_at_least(project, "planning"):
        required.extend([
            "plan/applied-template.json",
            "plan/production-plan.json",
        ])
        if _requires_generation_plan(project):
            required.append("plan/generation-plan.json")
    if _status_at_least(project, "packaged"):
        required.append("output-package/output-package.json")
    return required


def _resolve_promotion(project, workspace_dir):
    promotion_id = project["source_refs"]["idea_promotion_id"]
    promotion_path = Path(workspace_dir) / "research" / "idea-promotions" / f"{promotion_id}.json"
    if not promotion_path.exists():
        raise ValidationError(
            f"Project idea_promotion_id {promotion_id!r} does not resolve to "
            f"research/idea-promotions/{promotion_id}.json"
        )
    promotion = _validate_project_record(promotion_path, "idea-promotion")
    if promotion["idea_promotion_id"] != promotion_id:
        raise ValidationError(
            f"Idea promotion file {promotion_path} has idea_promotion_id "
            f"{promotion['idea_promotion_id']!r}, expected {promotion_id!r}"
        )
    if promotion["creator_profile_id"] != project["creator_profile_id"]:
        raise ValueError(
            "Idea promotion creator_profile_id does not match project: "
            f"{promotion['creator_profile_id']!r} != {project['creator_profile_id']!r}"
        )
    if project["project_id"] not in promotion["project_ids_created"]:
        raise ValueError(
            f"Idea promotion {promotion_id} does not list project "
            f"{project['project_id']!r} in project_ids_created"
        )
    _validate_approval_surface(project, promotion)
    return promotion


def _research_platform_for_surface(surface):
    for platform in RESEARCH_PLATFORMS:
        if surface == platform or surface.startswith(f"{platform}_"):
            return platform
    return None


def _validate_approval_surface(project, promotion):
    """A project stays within the locked promotion's approved surface.

    Formats share one vocabulary and must be a subset. platform_targets are
    distribution surfaces: a surface that maps to an ADR 0020 research
    platform must be approved; surfaces off the research set (youtube_*) are
    legitimate targets for the universal format and stay exempt until the
    surface vocabulary is closed in the production build-out.
    """
    unapproved_formats = sorted(
        set(project["target_formats"]) - set(promotion["approved_formats"])
    )
    if unapproved_formats:
        raise ValueError(
            "Project target_formats are not in the locked promotion's "
            f"approved_formats: {unapproved_formats}"
        )
    unapproved_surfaces = sorted(
        surface
        for surface in project.get("platform_targets", [])
        if (platform := _research_platform_for_surface(surface)) is not None
        and platform not in promotion["approved_platforms"]
    )
    if unapproved_surfaces:
        raise ValueError(
            "Project platform_targets map to research platforms the locked "
            f"promotion does not approve: {unapproved_surfaces}"
        )


def _validate_cached_promotion_refs(project, promotion):
    source_refs = project["source_refs"]
    cached_entry_id = source_refs.get("idea_queue_entry_id")
    if cached_entry_id is not None and cached_entry_id != promotion["idea_queue_entry_id"]:
        raise ValueError(
            "Cached idea_queue_entry_id does not match the locked promotion: "
            f"{cached_entry_id!r} != {promotion['idea_queue_entry_id']!r}"
        )

    promotion_evidence_ids = {ref["evidence_id"] for ref in promotion["evidence_refs"]}
    promotion_metric_ids = set()
    promotion_video_pack_ids = set()
    for ref in promotion["evidence_refs"]:
        promotion_metric_ids.update(ref.get("metric_snapshot_ids", []))
        promotion_video_pack_ids.update(ref.get("video_understanding_pack_ids", []))
    promotion_sets = {
        "research_finding_ids": set(promotion["research_finding_ids"]),
        "evidence_ids": promotion_evidence_ids,
        "metric_snapshot_ids": promotion_metric_ids,
        "video_understanding_pack_ids": promotion_video_pack_ids,
    }
    for cached_field, promotion_key in PROMOTION_CACHED_SUBSETS:
        cached = set(source_refs.get(cached_field, []))
        extra = sorted(cached - promotion_sets[promotion_key])
        if extra:
            raise ValueError(
                f"Cached {cached_field} name records the locked promotion does not carry: {extra}"
            )


def _status_at_least(project, status):
    return PROJECT_STATUS_ORDER[project["status"]] >= PROJECT_STATUS_ORDER[status]


def _requires_generation_plan(project):
    # content_unit_type is the anchor; _validate_content_unit_target_format()
    # keeps target_formats paired to it before record requirements are checked.
    return project["content_unit_type"] == "short_form_video"


def _format_id_for_content_unit(content_unit_type):
    return f"format_{content_unit_type}"


def _validate_content_unit_target_format(project):
    expected = _format_id_for_content_unit(project["content_unit_type"])
    target_formats = set(project["target_formats"])
    if target_formats != {expected}:
        raise ValueError(
            "Project content_unit_type must map to exactly one matching "
            f"target format: {project['content_unit_type']!r} requires "
            f"target_formats [{expected!r}], got {sorted(target_formats)}"
        )


def _locate_workspace(project_dir):
    projects_dir = project_dir.parent
    workspace_dir = projects_dir.parent
    if projects_dir.name != "projects" or not (workspace_dir / "creator-workspace.json").exists():
        raise FileNotFoundError(
            "Cannot locate creator workspace manifest above project: "
            f"{project_dir} (expected <workspace>/projects/<project-slug>/)"
        )
    return workspace_dir


def _resolve_source_refs(source_refs, workspace_dir, context):
    _resolve_reference_assets(source_refs.get("reference_asset_ids", []), workspace_dir, context)
    _resolve_research_packs(source_refs.get("research_pack_ids", []), workspace_dir, context)
    _resolve_research_packs(source_refs.get("video_understanding_pack_ids", []), workspace_dir, context)


def _resolve_reference_assets(asset_ids, workspace_dir, context):
    if not asset_ids:
        return
    library_path = workspace_dir / "references" / "reference-library.json"
    library = _validate_project_record(library_path, "reference-library")
    known_asset_ids = {asset["asset_id"] for asset in library["assets"]}
    dangling = sorted(set(asset_ids) - known_asset_ids)
    if dangling:
        raise ValidationError(
            f"{context}: reference_asset_ids do not resolve to reference library assets: {dangling}"
        )


def _resolve_research_packs(pack_ids, workspace_dir, context):
    for pack_id in pack_ids:
        directory, schema_name, id_field = _research_pack_location(pack_id, context)
        pack_path = workspace_dir / directory / f"{pack_id}.json"
        if not pack_path.exists():
            raise ValidationError(
                f"{context}: research pack {pack_id!r} does not resolve to {directory}/{pack_id}.json"
            )
        record = _validate_project_record(pack_path, schema_name)
        if record[id_field] != pack_id:
            raise ValidationError(
                f"{context}: research pack file {pack_path} has {id_field} "
                f"{record[id_field]!r}, expected {pack_id!r}"
            )


def _research_pack_location(pack_id, context):
    for prefix, directory, schema_name, id_field in RESEARCH_PACK_LOCATIONS:
        if pack_id.startswith(prefix):
            return directory, schema_name, id_field
    raise ValidationError(f"{context}: unrecognized research pack id prefix: {pack_id!r}")


def _validate_project_records(project_dir, project, workspace_dir):
    applied_template = None
    production_plan = None
    generation_plan = None

    if _status_at_least(project, "planning"):
        applied_template = _validate_project_record(
            project_dir / "plan" / "applied-template.json",
            "applied-social-template",
        )
        production_plan_schema = _production_plan_schema(project)
        production_plan = _validate_project_record(
            project_dir / "plan" / "production-plan.json",
            production_plan_schema,
        )

        if applied_template["idea_promotion_id"] != project["source_refs"]["idea_promotion_id"]:
            raise ValueError(
                "Applied template idea_promotion_id does not match project source_refs: "
                f"{applied_template['idea_promotion_id']!r} != {project['source_refs']['idea_promotion_id']!r}"
            )
        # The template targets a format for this project, and the project's
        # target_formats already stay within the locked promotion's approved
        # surface, so this keeps the plan layer inside the approval too.
        if applied_template["target_format_id"] not in project["target_formats"]:
            raise ValueError(
                "Applied template target_format_id is not among the project's "
                f"target_formats: {applied_template['target_format_id']!r} "
                f"not in {sorted(project['target_formats'])}"
            )
        if production_plan["idea_promotion_id"] != project["source_refs"]["idea_promotion_id"]:
            raise ValueError(
                "Production plan idea_promotion_id does not match project source_refs: "
                f"{production_plan['idea_promotion_id']!r} != {project['source_refs']['idea_promotion_id']!r}"
            )
        if production_plan["applied_social_template_id"] != applied_template["applied_social_template_id"]:
            raise ValueError(
                "Production plan applied_social_template_id does not match applied template: "
                f"{production_plan['applied_social_template_id']!r} != {applied_template['applied_social_template_id']!r}"
            )

        if _requires_generation_plan(project):
            generation_plan = _validate_project_record(
                project_dir / "plan" / "generation-plan.json",
                "base-video-generation-plan",
            )
            if generation_plan["micro_journey_video_plan_id"] != production_plan["micro_journey_video_plan_id"]:
                raise ValueError(
                    "Generation plan micro_journey_video_plan_id does not match production plan: "
                    f"{generation_plan['micro_journey_video_plan_id']!r} != {production_plan['micro_journey_video_plan_id']!r}"
                )

    if _status_at_least(project, "packaged"):
        output_package = _validate_project_record(
            project_dir / "output-package" / "output-package.json",
            "output-package",
        )
        if output_package["project_id"] != project["project_id"]:
            raise ValueError(
                "Output package project_id does not match project: "
                f"{output_package['project_id']!r} != {project['project_id']!r}"
            )
        if output_package["source_refs"]["idea_promotion_id"] != project["source_refs"]["idea_promotion_id"]:
            raise ValueError(
                "Output package idea_promotion_id does not match project source_refs: "
                f"{output_package['source_refs']['idea_promotion_id']!r} != "
                f"{project['source_refs']['idea_promotion_id']!r}"
            )
        if output_package["source_refs"]["applied_social_template_id"] != applied_template["applied_social_template_id"]:
            raise ValueError(
                "Output package applied_social_template_id does not match applied template: "
                f"{output_package['source_refs']['applied_social_template_id']!r} != "
                f"{applied_template['applied_social_template_id']!r}"
            )
        if output_package["creator_profile_id"] != project["creator_profile_id"]:
            raise ValueError(
                "Output package creator_profile_id does not match project: "
                f"{output_package['creator_profile_id']!r} != {project['creator_profile_id']!r}"
            )
        plan_id_field = PRODUCTION_PLAN_ID_FIELDS[_production_plan_schema(project)]
        known_plan_ids = {production_plan[plan_id_field]}
        if generation_plan is not None:
            known_plan_ids.add(generation_plan["base_video_generation_plan_id"])
        referenced_plan_ids = set(output_package["source_refs"]["production_plan_ids"])
        unknown_plan_ids = sorted(referenced_plan_ids - known_plan_ids)
        if unknown_plan_ids:
            raise ValueError(
                "Output package production_plan_ids do not match the project's plan records: "
                f"{unknown_plan_ids}"
            )
        missing_plan_ids = sorted(known_plan_ids - referenced_plan_ids)
        if missing_plan_ids:
            raise ValueError(
                "Output package production_plan_ids omit project plan records "
                f"(the provenance chain must be complete): {missing_plan_ids}"
            )
        _resolve_source_refs(output_package["source_refs"], workspace_dir, "OutputPackage source_refs")


def _validate_project_record(record_path, schema_name):
    try:
        validate_file(schema_name, record_path)
    except ValidationError as exc:
        raise ValidationError(f"Invalid project record {record_path}: {exc}") from exc
    return load_json(record_path)


def _production_plan_schema(project):
    try:
        return PRODUCTION_PLAN_SCHEMAS[project["content_unit_type"]]
    except KeyError as exc:
        raise ValueError(
            f"No production plan schema is defined for content_unit_type {project['content_unit_type']!r}"
        ) from exc
