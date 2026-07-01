import shutil
from pathlib import Path

from influencer_os.validation import ValidationError, load_json, validate_file, validate_record


PROJECT_DIRECTORIES = [
    "idea",
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
    "performance-summary.md": "# Performance Summary\n\n"
}

PROJECT_STATUS_ORDER = {
    "idea_selected": 1,
    "planned": 2,
    "packaged": 3,
    "published": 4,
    "analyzed": 5,
    "archived": 6,
}

PRODUCTION_PLAN_SCHEMAS = {
    "short_form_video": "micro-journey-video-plan",
    "carousel": "carousel-plan",
    "single_image_post": "single-image-post-plan",
    "story_sequence": "story-sequence-plan",
}


def init_project(project_manifest_path, creator_workspace):
    project_manifest_path = Path(project_manifest_path)
    creator_workspace = Path(creator_workspace)
    project = load_json(project_manifest_path)
    validate_record("project", project)

    _validate_creator_match(project, creator_workspace)

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


def validate_project(project_path):
    project_dir = Path(project_path)
    project_manifest_path = project_dir / "project.json"
    if not project_manifest_path.exists():
        raise FileNotFoundError(f"Missing project manifest: {project_manifest_path}")

    project = load_json(project_manifest_path)
    validate_record("project", project)

    expected_root = f"projects/{project['project_slug']}/"
    if project["project_paths"]["root"] != expected_root:
        raise ValueError(f"Project root path does not match project_slug: {project['project_paths']['root']!r}")

    required_paths = ["project.json"]
    required_paths.extend(project["project_paths"][key] for key in ["idea", "plan", "output_package", "published", "analytics", "performance_summary"])
    required_paths.extend(_required_record_paths(project))

    missing = []
    for relative_path in required_paths:
        if not (project_dir / relative_path).exists():
            missing.append(relative_path)

    if missing:
        raise FileNotFoundError(f"Missing project paths: {', '.join(sorted(missing))}")

    _validate_project_records(project_dir, project)

    return {
        "project_id": project["project_id"],
        "project_slug": project["project_slug"],
        "project_path": project_dir,
        "checked_paths": sorted(set(required_paths)),
    }


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
    if _status_at_least(project, "idea_selected"):
        required.append("idea/selected-content-idea.json")
    if _status_at_least(project, "planned"):
        required.extend([
            "plan/applied-template.json",
            "plan/production-plan.json",
        ])
        if _requires_generation_plan(project):
            required.append("plan/generation-plan.json")
    if _status_at_least(project, "packaged"):
        required.append("output-package/output-package.json")
    return required


def _status_at_least(project, status):
    return PROJECT_STATUS_ORDER[project["status"]] >= PROJECT_STATUS_ORDER[status]


def _requires_generation_plan(project):
    return (
        project["content_unit_type"] == "short_form_video"
        or "format_short_form_video" in project.get("target_formats", [])
    )


def _validate_project_records(project_dir, project):
    selected_idea = None
    applied_template = None
    production_plan = None

    if _status_at_least(project, "idea_selected"):
        selected_idea = _validate_project_record(
            project_dir / "idea" / "selected-content-idea.json",
            "selected-content-idea",
        )
        if selected_idea["selected_content_idea_id"] != project["source_refs"]["selected_content_idea_id"]:
            raise ValueError(
                "Selected idea id does not match project source_refs: "
                f"{selected_idea['selected_content_idea_id']!r} != {project['source_refs']['selected_content_idea_id']!r}"
            )

    if _status_at_least(project, "planned"):
        applied_template = _validate_project_record(
            project_dir / "plan" / "applied-template.json",
            "applied-social-template",
        )
        production_plan_schema = _production_plan_schema(project)
        production_plan = _validate_project_record(
            project_dir / "plan" / "production-plan.json",
            production_plan_schema,
        )

        if applied_template["selected_content_idea_id"] != project["source_refs"]["selected_content_idea_id"]:
            raise ValueError(
                "Applied template selected_content_idea_id does not match project source_refs: "
                f"{applied_template['selected_content_idea_id']!r} != {project['source_refs']['selected_content_idea_id']!r}"
            )
        if production_plan["selected_content_idea_id"] != project["source_refs"]["selected_content_idea_id"]:
            raise ValueError(
                "Production plan selected_content_idea_id does not match project source_refs: "
                f"{production_plan['selected_content_idea_id']!r} != {project['source_refs']['selected_content_idea_id']!r}"
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
