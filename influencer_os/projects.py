import datetime
import json
import shutil
import sys
from pathlib import Path

from influencer_os.research import validate_promotion_gate
from influencer_os.validation import (
    RESEARCH_PLATFORMS,
    TEXT_FORMAT_IDS,
    ValidationError,
    load_json,
    validate_file,
    validate_record,
)


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

# Publication statuses that attest a post went live on the platform (an
# "updated" or "deleted" post was necessarily published first). "scheduled"
# and "failed" records document attempts and never move a Project past
# packaged.
PUBLICATION_LIVE_STATUSES = frozenset({"published", "updated", "deleted"})

# A published project whose analytics have matured past the slowest platform
# reporting lag (YouTube lags 2-3 days — Phase 2 plan Reference Review)
# should carry a PerformanceSummary. Advisory WARN only, derived from
# durable at-rest snapshot data, never from a mutable flag.
PERFORMANCE_SUMMARY_DUE_HOURS = 72

# Phase 2 learning records live inside the owning project folder. The globs
# mirror the writer layout exactly; `analytics/raw/` payloads are never
# scanned because only the snapshots/ subfolder is named. The final flag
# marks per-record files whose filename must equal their id (the fixed
# performance-summary.json name is exempt).
LEARNING_RECORD_SCANS = (
    ("published/published-post-records/*.json",
     "published_post_record_id", "published-post-record", True),
    ("analytics/snapshots/*.json",
     "analytics_snapshot_id", "analytics-snapshot", True),
    ("performance-summary.json",
     "performance_summary_id", "performance-summary", False),
)


def collect_anchored_learning_records(workspace_dir):
    """Walk every project folder and return (path, record_type, id_field,
    record) for each Phase 2 learning record, failing closed when a record
    does not schema-validate, does not carry its id as the filename, or does
    not anchor to a schema-valid sibling project manifest with a matching
    project_id (process-learning 2026-07-06: existence of an id is not
    existence of a record). One function shared by `validate workspace` at
    rest and the recall-index scan, so the two checks cannot drift (slice 5
    review follow-up)."""
    projects_dir = Path(workspace_dir) / "projects"
    results = []
    if not projects_dir.is_dir():
        return results
    for project_dir in sorted(
        path for path in projects_dir.iterdir() if path.is_dir()
    ):
        learning_files = [
            (record_path, id_field, record_type, filename_is_id)
            for pattern, id_field, record_type, filename_is_id
            in LEARNING_RECORD_SCANS
            for record_path in sorted(project_dir.glob(pattern))
        ]
        if not learning_files:
            continue
        manifest_path = project_dir / "project.json"
        if not manifest_path.exists():
            raise ValidationError(
                f"{project_dir}: learning records exist but no "
                "project.json manifest anchors them"
            )
        manifest = load_json(manifest_path)
        try:
            validate_record("project", manifest)
        except ValidationError as exc:
            raise ValidationError(
                f"{manifest_path}: not a valid project manifest to "
                f"anchor learning records: {exc}"
            ) from None
        for record_path, id_field, record_type, filename_is_id in learning_files:
            record = _load_anchored_learning_record(
                record_path, record_type, id_field, filename_is_id,
                manifest["project_id"],
            )
            results.append((record_path, record_type, id_field, record))
    return results


def _load_anchored_learning_record(record_path, record_type, id_field,
                                   filename_is_id, anchor_project_id):
    record = load_json(record_path)
    try:
        validate_record(record_type, record)
    except ValidationError as exc:
        raise ValidationError(
            f"{record_path}: not a valid {record_type} record: {exc}"
        ) from None
    record_id = record[id_field]
    if filename_is_id and record_path.stem != record_id:
        raise ValidationError(
            f"{record_path}: filename must equal its {id_field} "
            f"({record_id!r})"
        )
    if record["project_id"] != anchor_project_id:
        raise ValidationError(
            f"{record_path}: project_id {record['project_id']!r} does not "
            f"match the owning manifest ({anchor_project_id!r})"
        )
    return record

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

# The advisory platform → format capability map (ADR 0024, Creative
# Direction slice 3). Fit classifications transcribed from the dated
# 2026-07-06 capability research in
# docs/os-construction/generation-content-cross-os-comparison.md §II-C.
# Numeric platform limits (item caps, tier gates) deliberately stay
# doc-side and are never validation thresholds. Guides, never gates: a
# non-native best fit yields a platform_fit ProjectWarning and blocks
# nothing.
PLATFORM_FORMAT_FIT = {
    "format_short_form_video": {
        "instagram": "native", "tiktok": "native", "linkedin": "native",
        "x": "native", "facebook": "native", "substack": "native",
        "reddit": "analog", "medium": "none",
    },
    "format_carousel": {
        "instagram": "native", "tiktok": "native", "linkedin": "native",
        "reddit": "native", "facebook": "native",
        "x": "analog", "substack": "analog", "medium": "none",
    },
    "format_single_image_post": {
        "instagram": "native", "linkedin": "native", "x": "native",
        "facebook": "native", "reddit": "native",
        "tiktok": "analog", "substack": "analog", "medium": "none",
    },
    "format_story_sequence": {
        "instagram": "native", "facebook": "native",
        "x": "none", "tiktok": "none", "linkedin": "none",
        "reddit": "none", "substack": "none", "medium": "none",
    },
    "format_article": {
        "substack": "native", "medium": "native", "linkedin": "native",
        "x": "native", "reddit": "native",
        "facebook": "analog", "tiktok": "none", "instagram": "none",
    },
    "format_thread": {
        "x": "native",
        "linkedin": "subtype", "tiktok": "subtype",
        "reddit": "analog", "facebook": "analog", "substack": "analog",
        "medium": "none", "instagram": "none",
    },
}

PLATFORM_FIT_RANK = {"native": 3, "subtype": 2, "analog": 1, "none": 0}


def init_project(project_manifest_path, creator_workspace):
    project_manifest_path = Path(project_manifest_path)
    creator_workspace = Path(creator_workspace)
    project = load_json(project_manifest_path)
    validate_record("project", project)
    _validate_content_unit_target_format(project)

    _validate_creator_match(project, creator_workspace)
    promotion = _resolve_promotion(project, creator_workspace)

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

    # Advisory only — computed after the project exists, and best-effort:
    # no failure in the advisory path may block creation (ADR 0024:
    # platform guides, never gates; slice 3 review finding).
    try:
        _emit_platform_fit_warning(creator_workspace, project, promotion)
    except Exception as exc:  # noqa: BLE001 — advisory path must not raise
        print(
            f"warning: platform-fit advisory could not be recorded: {exc}",
            file=sys.stderr,
        )

    return project_dir


def _platform_fit_for_surfaces(format_id, surfaces):
    """The creator's best advisory fit for a format across their primary
    surfaces, per the dated capability map. Unknown formats or surfaces
    yield no verdict (None) rather than a false 'none'."""
    fit_by_platform = PLATFORM_FORMAT_FIT.get(format_id)
    if not fit_by_platform:
        return None
    fits = [
        fit_by_platform[surface]
        for surface in surfaces
        if surface in fit_by_platform
    ]
    if not fits:
        return None
    return max(fits, key=PLATFORM_FIT_RANK.__getitem__)


def _emit_platform_fit_warning(creator_workspace, project, promotion):
    """Append a platform_fit ProjectWarning when the project's format is not
    native to any of the creator's primary surfaces (Creative Direction
    slice 3). Purely advisory: this appends a record and changes nothing
    else. Skips silently when the profile or its strategy block is missing
    or pre-enum (legacy fixtures)."""
    profile_path = Path(creator_workspace) / "creator-profile.json"
    if not profile_path.exists():
        return
    try:
        profile = load_json(profile_path)
        surfaces = profile["content_strategy"]["primary_surfaces"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return
    surfaces = [surface for surface in surfaces if surface in RESEARCH_PLATFORMS]
    if not surfaces:
        return

    format_id = _format_id_for_content_unit(project["content_unit_type"])
    fit = _platform_fit_for_surfaces(format_id, surfaces)
    if fit is None or fit == "native":
        return

    warning_id = f"project_warning_platform_fit_{project['project_id']}"
    warnings_path = Path(creator_workspace) / "system" / "project-warnings.jsonl"
    # Idempotent: a re-run for the same project must not append a duplicate
    # warning id (slice 3 review finding).
    if warnings_path.exists():
        for line in warnings_path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                existing = json.loads(line)
            except json.JSONDecodeError:
                continue
            if existing.get("project_warning_id") == warning_id:
                return

    warning = {
        "project_warning_id": warning_id,
        "idea_queue_entry_id": promotion["idea_queue_entry_id"],
        "idea_promotion_id": promotion["idea_promotion_id"],
        "project_id": project["project_id"],
        "warning_type": "platform_fit",
        "fit_level": fit,
        "severity": "info",
        "message": (
            f"{format_id} is not native to the creator's primary surfaces "
            f"({', '.join(surfaces)}); best advisory fit is {fit!r} per the "
            "dated capability map. Guides, never gates."
        ),
        "detected_on": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "suggested_actions": [
            "Confirm the format choice is deliberate for these surfaces.",
            "Consider a surface-native format or an additional primary surface.",
        ],
        "resolved_status": "open",
    }
    validate_record("project-warning", warning)
    warnings_path.parent.mkdir(parents=True, exist_ok=True)
    with warnings_path.open("a") as stream:
        stream.write(json.dumps(warning) + "\n")


def register_output_package(project_path, output_package_path, asset_root=None):
    project_dir = Path(project_path)
    output_package_path = Path(output_package_path)
    asset_root = Path(asset_root) if asset_root is not None else None
    project_manifest_path = project_dir / "project.json"
    package_destination = project_dir / "output-package" / "output-package.json"

    if package_destination.exists() or package_destination.is_symlink():
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
    if output_package["status"] != "upload_ready":
        raise ValueError(
            "Output package must have status 'upload_ready' before registration; "
            f"got {output_package['status']!r}"
        )
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
            if target.exists() or target.is_symlink():
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
        for target in copied_targets:
            _remove_empty_parents(
                target.parent,
                stop=project_dir / "output-package" / "upload-ready",
            )
        raise

    return {
        "output_package_id": output_package["output_package_id"],
        "project_id": project["project_id"],
        "project_path": project_dir,
        "output_package_path": package_destination,
        "copied_assets": copied_targets,
    }


def register_published_post(project_path, record_path):
    """Record a human publication of a packaged project's Output Package.

    Registration never publishes anything: it validates and files a
    PublishedPostRecord under published/published-post-records/ and moves the
    Project packaged -> published on the first record whose
    publication_status attests a live post.
    """
    project_dir = Path(project_path)
    record_path = Path(record_path)
    project_manifest_path = project_dir / "project.json"
    package_path = project_dir / "output-package" / "output-package.json"

    if not project_manifest_path.exists():
        raise FileNotFoundError(f"Missing project manifest: {project_manifest_path}")
    if not record_path.exists():
        raise FileNotFoundError(f"Missing published post record: {record_path}")

    project = load_json(project_manifest_path)
    validate_record("project", project)
    if project["status"] not in ("packaged", "published"):
        raise ValueError(
            "Published post registration requires a packaged (or already "
            f"published) project; got status {project['status']!r}"
        )

    # Preflight the project (including any already-registered published
    # records) before mutating it.
    validate_project(project_dir)

    record = load_json(record_path)
    validate_record("published-post-record", record)
    output_package = load_json(package_path)
    _validate_published_post_matches(record, project, output_package)

    record_id = record["published_post_record_id"]
    destination = project_dir / "published" / "published-post-records" / f"{record_id}.json"
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Published post record already registered: {destination}")
    _ensure_contained_target(destination, project_dir, "published post record destination")

    original_project_text = project_manifest_path.read_text()
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(record_path, destination)

        if (
            project["status"] == "packaged"
            and record["publication_status"] in PUBLICATION_LIVE_STATUSES
        ):
            project["status"] = "published"
            _write_json(project_manifest_path, project)

        validate_project(project_dir)
    except Exception:
        project_manifest_path.write_text(original_project_text)
        if destination.exists() or destination.is_symlink():
            destination.unlink()
        raise

    return {
        "published_post_record_id": record_id,
        "project_id": project["project_id"],
        "project_status": project["status"],
        "record_path": destination,
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

    # performance_summary is deliberately absent: the summary record attaches
    # at rest only once authored (Phase 2 slice 3); its presence is validated
    # below and its absence on a mature published project is an advisory WARN.
    required_paths = ["project.json"]
    required_paths.extend(project["project_paths"][key] for key in ["plan", "output_package", "published", "analytics", "evidence_brief"])
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
    warnings.extend(_validate_project_records(project_dir, project, workspace_dir, promotion))

    return {
        "project_id": project["project_id"],
        "project_slug": project["project_slug"],
        "project_path": project_dir,
        "checked_paths": sorted(set(required_paths)),
        "warnings": warnings,
    }


def _write_json(path, record):
    # allow_nan=False: NaN/Infinity are not valid JSON; refuse to persist
    # them even if a caller slipped past validation.
    path.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")


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
    # Every status at or past packaged (published, analyzed, archived) keeps
    # requiring an upload-ready package; the invariant must not lapse when
    # the project moves on.
    if _status_at_least(project, "packaged") and output_package["status"] != "upload_ready":
        raise ValueError(
            "Packaged (or later) projects must carry an upload-ready Output Package: "
            f"got {output_package['status']!r} at project status {project['status']!r}"
        )


def _validate_published_post_matches(record, project, output_package):
    """Shared writer/at-rest checks pinning a PublishedPostRecord to its chain.

    Called by register_published_post at write time and by
    _validate_published_records at rest so the two paths cannot drift.
    """
    if record["project_id"] != project["project_id"]:
        raise ValueError(
            "Published post record project_id does not match project: "
            f"{record['project_id']!r} != {project['project_id']!r}"
        )
    if record["creator_profile_id"] != project["creator_profile_id"]:
        raise ValueError(
            "Published post record creator_profile_id does not match project: "
            f"{record['creator_profile_id']!r} != {project['creator_profile_id']!r}"
        )
    if record["output_package_id"] != output_package["output_package_id"]:
        raise ValueError(
            "Published post record output_package_id does not match the registered package: "
            f"{record['output_package_id']!r} != {output_package['output_package_id']!r}"
        )

    known_asset_ids = {asset["upload_asset_id"] for asset in output_package["upload_ready"]}
    declared_paths = {asset["path"] for asset in output_package["upload_ready"]}
    assets_used = record["assets_used"]

    used_asset_ids = set(assets_used["primary_media_asset_ids"])
    thumbnail_id = assets_used["thumbnail_or_first_frame_asset_id"]
    if thumbnail_id is None:
        # Mirror the output-package rule: only text formats publish without a
        # thumbnail or first frame; visual formats must name a real asset.
        package_format_id = output_package["universal_core"]["format_id"]
        if package_format_id not in TEXT_FORMAT_IDS:
            raise ValueError(
                "Published post record thumbnail_or_first_frame_asset_id is "
                f"required for {package_format_id!r} packages"
            )
    else:
        used_asset_ids.add(thumbnail_id)
    dangling_ids = sorted(used_asset_ids - known_asset_ids)
    if dangling_ids:
        raise ValueError(
            "Published post record assets_used name upload assets the "
            f"registered package does not declare: {dangling_ids}"
        )
    if assets_used["caption_or_description_path"] not in declared_paths:
        raise ValueError(
            "Published post record caption_or_description_path is not a "
            f"declared upload-ready path: {assets_used['caption_or_description_path']!r}"
        )


def _validate_published_records(project_dir, project, output_package):
    """At-rest checks for published/published-post-records/ (slice 1 parity).

    Every writer-enforced registration invariant is re-checked here so a
    hand-edited record or status cannot validate at rest. Returns the
    validated records keyed by id so analytics validation can resolve
    published_post_record_id references without re-reading files.
    """
    records_dir = Path(project_dir) / "published" / "published-post-records"
    record_paths = sorted(records_dir.glob("*.json")) if records_dir.is_dir() else []

    if record_paths and output_package is None:
        raise ValueError(
            "Published post records require a packaged project with a "
            f"registered Output Package: {records_dir}"
        )

    live_count = 0
    seen_platform_post_ids = {}
    seen_public_urls = {}
    records_by_id = {}
    for record_path in record_paths:
        _ensure_contained_file(record_path, project_dir, "published post record")
        record = _validate_project_record(record_path, "published-post-record")
        record_id = record["published_post_record_id"]
        if record_path.stem != record_id:
            raise ValueError(
                f"Published post record filename must match its id: "
                f"{record_path.name} carries {record_id!r}"
            )
        _validate_published_post_matches(record, project, output_package)

        # One record per platform post: two records may not claim the same
        # platform post identity under different record ids.
        platform_post_id = record["platform_post_id"]
        if platform_post_id is not None:
            post_key = (record["platform"], platform_post_id)
            if post_key in seen_platform_post_ids:
                raise ValueError(
                    "Published post records duplicate a platform post: "
                    f"{record_id!r} and {seen_platform_post_ids[post_key]!r} "
                    f"both claim {record['platform']!r} post {platform_post_id!r}"
                )
            seen_platform_post_ids[post_key] = record_id
        public_url = record["public_url"]
        if public_url is not None:
            if public_url in seen_public_urls:
                raise ValueError(
                    "Published post records duplicate a public URL: "
                    f"{record_id!r} and {seen_public_urls[public_url]!r} "
                    f"both claim {public_url!r}"
                )
            seen_public_urls[public_url] = record_id

        if record["publication_status"] in PUBLICATION_LIVE_STATUSES:
            live_count += 1
        records_by_id[record_id] = record

    if _status_at_least(project, "published") and live_count == 0:
        raise ValueError(
            "Project status is published but published/published-post-records/ "
            "carries no record attesting a live publication"
        )
    if not _status_at_least(project, "published") and live_count > 0:
        raise ValueError(
            "Project carries live published post records but its status is "
            f"below published: {project['status']!r}"
        )
    return records_by_id


def _parse_record_timestamp(value):
    """Parse an ISO timestamp (Z-suffixed or offset), else None."""
    if not isinstance(value, str):
        return None
    try:
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _validate_analytics_snapshot_matches(record, project, output_package, published_records):
    """Shared writer/at-rest checks pinning an AnalyticsSnapshot to its chain.

    Called by write_analytics_snapshot at write time and by
    _validate_analytics_records at rest so the two paths cannot drift.
    """
    if record["project_id"] != project["project_id"]:
        raise ValueError(
            "Analytics snapshot project_id does not match project: "
            f"{record['project_id']!r} != {project['project_id']!r}"
        )
    if record["creator_profile_id"] != project["creator_profile_id"]:
        raise ValueError(
            "Analytics snapshot creator_profile_id does not match project: "
            f"{record['creator_profile_id']!r} != {project['creator_profile_id']!r}"
        )
    if record["output_package_id"] != output_package["output_package_id"]:
        raise ValueError(
            "Analytics snapshot output_package_id does not match the registered package: "
            f"{record['output_package_id']!r} != {output_package['output_package_id']!r}"
        )

    ppr_id = record["published_post_record_id"]
    published_record = published_records.get(ppr_id)
    if published_record is None:
        raise ValueError(
            "Analytics snapshot published_post_record_id does not resolve to a "
            f"registered published post record: {ppr_id!r}"
        )
    if published_record["publication_status"] not in PUBLICATION_LIVE_STATUSES:
        raise ValueError(
            "Analytics snapshots may only measure posts that went live; "
            f"{ppr_id!r} has publication_status "
            f"{published_record['publication_status']!r}"
        )
    if record["platform"] != published_record["platform"]:
        raise ValueError(
            "Analytics snapshot platform does not match its published post record: "
            f"{record['platform']!r} != {published_record['platform']!r}"
        )

    # A snapshot timestamped before publication is dishonest regardless of
    # whether hours_since_publish was supplied or derived; check whenever
    # both timestamps parse (write time and at rest).
    snapshot_at = _parse_record_timestamp(record["snapshot_at"])
    published_at = _parse_record_timestamp(published_record["published_at"])
    if snapshot_at is not None and published_at is not None:
        if (snapshot_at.tzinfo is None) != (published_at.tzinfo is None):
            raise ValueError(
                "Analytics snapshot_at and published_at must use matching "
                "timezone awareness before hours_since_publish can be trusted: "
                f"{record['snapshot_at']!r} vs {published_record['published_at']!r}"
            )
        if snapshot_at < published_at:
            raise ValueError(
                "Analytics snapshot_at is earlier than the published post's "
                f"published_at: {record['snapshot_at']!r} < "
                f"{published_record['published_at']!r}"
            )


def _analytics_raw_refs(record):
    """The record's optional analytics/raw/ file references."""
    refs = []
    if record["raw_source_ref"] is not None:
        refs.append(("raw_source_ref", record["raw_source_ref"]))
    curve_ref = record["attribution_metrics"]["body_retention"]["retention_curve_ref"]
    if curve_ref is not None:
        refs.append(("attribution_metrics.body_retention.retention_curve_ref", curve_ref))
    return refs


def _validate_analytics_raw_refs(project_dir, record):
    """Raw refs must stay inside analytics/raw/ and resolve to real files.

    Containment is checked against analytics/raw/ itself, not the project
    root: a symlink placed inside raw/ that points at another project file
    (or outside the project) resolves outside raw/ and is rejected.
    """
    raw_root = Path(project_dir) / "analytics" / "raw"
    for field, raw_ref in _analytics_raw_refs(record):
        relative_path = _safe_project_relative_path(
            raw_ref,
            required_prefix=("analytics", "raw"),
            context=f"Analytics snapshot {field}",
        )
        raw_path = Path(project_dir) / relative_path
        if not raw_path.exists():
            raise FileNotFoundError(
                f"Analytics snapshot {field} does not resolve to a file: {raw_ref!r}"
            )
        _ensure_contained_file(raw_path, raw_root, f"Analytics snapshot {field}")


def _validate_analytics_records(project_dir, project, output_package, published_records):
    """At-rest checks for analytics/snapshots/ (slice 2 parity).

    Every writer-enforced ingestion invariant is re-checked here so a
    hand-edited snapshot cannot validate at rest. Returns the validated
    snapshots keyed by id so performance-summary validation can resolve
    analytics_snapshot_id references without re-reading files.
    """
    snapshots_dir = Path(project_dir) / "analytics" / "snapshots"
    snapshot_paths = sorted(snapshots_dir.glob("*.json")) if snapshots_dir.is_dir() else []

    if snapshot_paths and output_package is None:
        raise ValueError(
            "Analytics snapshots require a packaged project with a "
            f"registered Output Package: {snapshots_dir}"
        )

    snapshots_by_id = {}
    for snapshot_path in snapshot_paths:
        _ensure_contained_file(snapshot_path, project_dir, "analytics snapshot")
        record = _validate_project_record(snapshot_path, "analytics-snapshot")
        record_id = record["analytics_snapshot_id"]
        if snapshot_path.stem != record_id:
            raise ValueError(
                f"Analytics snapshot filename must match its id: "
                f"{snapshot_path.name} carries {record_id!r}"
            )
        _validate_analytics_snapshot_matches(record, project, output_package, published_records)
        _validate_analytics_raw_refs(project_dir, record)
        snapshots_by_id[record_id] = record
    return snapshots_by_id


def _validate_performance_summary(project_dir, project, output_package, published_records, analytics_records, applied_template=None):
    """At-rest checks for performance-summary.json (slice 3).

    The summary attaches at rest once authored (no dedicated status); when
    present, every evidence ref must resolve to this project's registered
    records. Record-shape rules — including the exactly-once attribution
    stage set — are enforced by the schema plus record semantics
    (validate_unique_stages/validate_required_stages) via
    _validate_project_record. When absent on a published project with
    mature analytics, an advisory WARN fires. Returns warning strings.
    """
    summary_path = Path(project_dir) / "performance-summary.json"
    if not summary_path.exists() and not summary_path.is_symlink():
        return _performance_summary_warnings(project, published_records, analytics_records)

    _ensure_contained_file(summary_path, project_dir, "performance summary")
    summary = _validate_project_record(summary_path, "performance-summary")
    if output_package is None:
        raise ValueError(
            "Performance summary requires a packaged project with a "
            f"registered Output Package: {summary_path}"
        )
    if summary["project_id"] != project["project_id"]:
        raise ValueError(
            "Performance summary project_id does not match project: "
            f"{summary['project_id']!r} != {project['project_id']!r}"
        )
    if summary["creator_profile_id"] != project["creator_profile_id"]:
        raise ValueError(
            "Performance summary creator_profile_id does not match project: "
            f"{summary['creator_profile_id']!r} != {project['creator_profile_id']!r}"
        )

    evidence_refs = summary["evidence_refs"]
    if evidence_refs["output_package_id"] != output_package["output_package_id"]:
        raise ValueError(
            "Performance summary output_package_id does not match the registered package: "
            f"{evidence_refs['output_package_id']!r} != {output_package['output_package_id']!r}"
        )
    dangling_posts = sorted(set(evidence_refs["published_post_record_ids"]) - set(published_records))
    if dangling_posts:
        raise ValueError(
            "Performance summary published_post_record_ids do not resolve to "
            f"registered published post records: {dangling_posts}"
        )
    dangling_snapshots = sorted(set(evidence_refs["analytics_snapshot_ids"]) - set(analytics_records))
    if dangling_snapshots:
        raise ValueError(
            "Performance summary analytics_snapshot_ids do not resolve to "
            f"ingested analytics snapshots: {dangling_snapshots}"
        )

    # A cited snapshot's parent post must itself be cited: resolving the two
    # id lists independently would let a multi-publication project attribute
    # one post's metrics to another post's URL and assets (P2 review
    # finding, 2026-07-05).
    cited_posts = set(evidence_refs["published_post_record_ids"])
    misattributed = sorted(
        snapshot_id
        for snapshot_id in evidence_refs["analytics_snapshot_ids"]
        if analytics_records[snapshot_id]["published_post_record_id"] not in cited_posts
    )
    if misattributed:
        raise ValueError(
            "Performance summary cites analytics snapshots whose published "
            f"post record is not among the cited published_post_record_ids: {misattributed}"
        )

    _validate_summary_source_material_refs(project_dir, evidence_refs["source_material_refs"])
    _validate_summary_spine_alignment(summary, applied_template)
    return []


def _validate_summary_spine_alignment(summary, applied_template):
    """The learning loop speaks spine (ADR 0024, Creative Direction slice 2).

    Stage findings attribute to the applied template's beat_role beats. When
    the applied template planned no cta beat, the cta stage finding must
    record the absence as `result: "not_used"` — never a judged result for a
    stage that was never planned, and never an omitted stage (minItems:5
    still holds). A planned cta beat that was dropped in publication may
    legitimately still read `not_used`, so only the unplanned direction is
    enforced.
    """
    if applied_template is None:
        return
    applied_roles = {
        beat.get("beat_role") for beat in applied_template.get("applied_beats", [])
    }
    if "cta" in applied_roles:
        return
    for finding in summary.get("stage_findings", []):
        if finding.get("stage") == "cta" and finding.get("result") != "not_used":
            raise ValidationError(
                "Performance summary cta stage finding must record "
                "result 'not_used' when the applied template planned no "
                f"cta-role beat, got {finding.get('result')!r}"
            )


def _validate_summary_source_material_refs(project_dir, refs):
    """source_material_refs are provenance, so they must be auditable: each
    ref must be a relative path resolving to an existing file inside the
    project, symlink-safe (P3 review finding, 2026-07-05).
    """
    for ref in refs:
        relative_path = Path(ref)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(
                "Performance summary source_material_refs must be relative "
                f"paths inside the project: {ref!r}"
            )
        path = Path(project_dir) / relative_path
        if not path.exists():
            raise FileNotFoundError(
                "Performance summary source_material_ref does not resolve "
                f"to a file: {ref!r}"
            )
        _ensure_contained_file(
            path, project_dir, f"Performance summary source_material_ref {ref!r}"
        )


def _performance_summary_warnings(project, published_records, analytics_records):
    """The published-but-never-summarized advisory WARN (slice 3).

    Fires when at least one snapshot has matured past the slowest platform
    reporting lag, so an early snapshot alone never nags for a summary the
    data cannot support yet. hours_since_publish is authoritative when
    recorded; otherwise it derives from the timestamps, and underivable
    snapshots do not count as mature.
    """
    if not _status_at_least(project, "published"):
        return []
    for record in analytics_records.values():
        hours = record["hours_since_publish"]
        if hours is None:
            hours = _derive_hours_since_publish(
                record, published_records[record["published_post_record_id"]]
            )
        if hours is not None and hours >= PERFORMANCE_SUMMARY_DUE_HOURS:
            return [
                f"warning: project {project['project_id']} is published with "
                f"analytics at least {PERFORMANCE_SUMMARY_DUE_HOURS}h "
                "post-publish but has no performance-summary.json; author one "
                "via the create-performance-summary skill"
            ]
    return []


def write_analytics_snapshot(project_path, record):
    """The shared ingestion seam (ADR 0004): every path — manual entry, CSV
    import, and any future API connector — writes through this function so
    the ingestion invariants cannot drift per path.
    """
    project_dir = Path(project_path)
    project_manifest_path = project_dir / "project.json"
    package_path = project_dir / "output-package" / "output-package.json"

    if not project_manifest_path.exists():
        raise FileNotFoundError(f"Missing project manifest: {project_manifest_path}")

    project = load_json(project_manifest_path)
    validate_record("project", project)
    if not _status_at_least(project, "published"):
        raise ValueError(
            "Analytics ingestion requires a published project; "
            f"got status {project['status']!r}"
        )

    # Preflight the project (including already-ingested snapshots) before
    # writing.
    validate_project(project_dir)

    validate_record("analytics-snapshot", record)
    output_package = load_json(package_path)
    published_records = _load_published_records_by_id(project_dir)
    _validate_analytics_snapshot_matches(record, project, output_package, published_records)

    if record["hours_since_publish"] is None:
        record = dict(record)
        record["hours_since_publish"] = _derive_hours_since_publish(
            record, published_records[record["published_post_record_id"]]
        )

    _validate_analytics_raw_refs(project_dir, record)

    record_id = record["analytics_snapshot_id"]
    destination = project_dir / "analytics" / "snapshots" / f"{record_id}.json"
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Analytics snapshot already ingested: {destination}")
    _ensure_contained_target(destination, project_dir, "analytics snapshot destination")

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        _write_json(destination, record)
        validate_project(project_dir)
    except Exception:
        if destination.exists() or destination.is_symlink():
            destination.unlink()
        raise

    return {
        "analytics_snapshot_id": record_id,
        "published_post_record_id": record["published_post_record_id"],
        "hours_since_publish": record["hours_since_publish"],
        "snapshot_path": destination,
    }


def add_analytics_snapshot(project_path, record_path):
    """Manual/derived ingestion: a full schema-shaped record authored as JSON."""
    record_path = Path(record_path)
    if not record_path.exists():
        raise FileNotFoundError(f"Missing analytics snapshot record: {record_path}")
    return write_analytics_snapshot(project_path, load_json(record_path))


def _load_published_records_by_id(project_dir):
    records_dir = Path(project_dir) / "published" / "published-post-records"
    records = {}
    for record_path in sorted(records_dir.glob("*.json")) if records_dir.is_dir() else []:
        record = load_json(record_path)
        records[record["published_post_record_id"]] = record
    return records


def _derive_hours_since_publish(record, published_record):
    """Compute hours_since_publish from the two timestamps when parseable.

    Ordering is already enforced by _validate_analytics_snapshot_matches
    (which runs before derivation on every path), so the difference is
    never negative here.
    """
    snapshot_at = _parse_record_timestamp(record["snapshot_at"])
    published_at = _parse_record_timestamp(published_record["published_at"])
    if snapshot_at is None or published_at is None:
        return None
    if (snapshot_at.tzinfo is None) != (published_at.tzinfo is None):
        return None
    return round((snapshot_at - published_at).total_seconds() / 3600, 2)


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


def _validate_project_records(project_dir, project, workspace_dir, promotion=None):
    applied_template = None
    production_plan = None
    generation_plan = None
    output_package = None

    # Plan records are required at planning+ but validated whenever they
    # exist (slice 2 review finding): a plan written prematurely on a
    # `created` project must satisfy the same contracts, not wait for the
    # status flip to be checked.
    plans_required = _status_at_least(project, "planning")
    applied_template_path = project_dir / "plan" / "applied-template.json"
    production_plan_path = project_dir / "plan" / "production-plan.json"
    generation_plan_path = project_dir / "plan" / "generation-plan.json"

    if plans_required or applied_template_path.exists():
        applied_template = _validate_project_record(
            applied_template_path,
            "applied-social-template",
        )
    if plans_required or production_plan_path.exists():
        production_plan = _validate_project_record(
            production_plan_path,
            _production_plan_schema(project),
        )

    if applied_template is not None:
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

    if production_plan is not None:
        if production_plan["idea_promotion_id"] != project["source_refs"]["idea_promotion_id"]:
            raise ValueError(
                "Production plan idea_promotion_id does not match project source_refs: "
                f"{production_plan['idea_promotion_id']!r} != {project['source_refs']['idea_promotion_id']!r}"
            )
        # Intent is resolved by reference (ADR 0024): the canonical
        # intended_emotion lives on the locked promotion, and a plan that
        # carries the field must restate it verbatim, never override it.
        # A plan-only value is the legacy path for promotions that predate
        # intent capture.
        if promotion is not None:
            promotion_emotion = promotion.get("intended_emotion")
            plan_emotion = production_plan.get("intended_emotion")
            if (
                promotion_emotion is not None
                and plan_emotion is not None
                and plan_emotion != promotion_emotion
            ):
                raise ValueError(
                    "Production plan intended_emotion overrides the locked "
                    f"promotion: {plan_emotion!r} != {promotion_emotion!r}; "
                    "intent is resolved by reference, never overridden"
                )

    if applied_template is not None and production_plan is not None:
        if production_plan["applied_social_template_id"] != applied_template["applied_social_template_id"]:
            raise ValueError(
                "Production plan applied_social_template_id does not match applied template: "
                f"{production_plan['applied_social_template_id']!r} != {applied_template['applied_social_template_id']!r}"
            )

    if _requires_generation_plan(project) and (
        plans_required or generation_plan_path.exists()
    ):
        generation_plan = _validate_project_record(
            generation_plan_path,
            "base-video-generation-plan",
        )
        if (
            production_plan is not None
            and generation_plan["micro_journey_video_plan_id"] != production_plan["micro_journey_video_plan_id"]
        ):
            raise ValueError(
                "Generation plan micro_journey_video_plan_id does not match production plan: "
                f"{generation_plan['micro_journey_video_plan_id']!r} != {production_plan['micro_journey_video_plan_id']!r}"
            )

    if _status_at_least(project, "packaged"):
        output_package = _validate_project_record(
            project_dir / "output-package" / "output-package.json",
            "output-package",
        )
        _validate_output_package_matches_project(output_package, project)
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
        _validate_upload_ready_files(project_dir, output_package)
        _resolve_source_refs(output_package["source_refs"], workspace_dir, "OutputPackage source_refs")

    published_records = _validate_published_records(project_dir, project, output_package)
    analytics_records = _validate_analytics_records(project_dir, project, output_package, published_records)
    return _validate_performance_summary(
        project_dir,
        project,
        output_package,
        published_records,
        analytics_records,
        applied_template=applied_template,
    )


def _validate_project_record(record_path, schema_name):
    try:
        validate_file(schema_name, record_path)
    except ValidationError as exc:
        raise ValidationError(f"Invalid project record {record_path}: {exc}") from exc
    return load_json(record_path)


def _validate_upload_ready_files(project_dir, output_package):
    for relative_path in _upload_ready_relative_paths(output_package):
        path = Path(project_dir) / relative_path
        if not path.exists():
            raise FileNotFoundError(f"Missing upload-ready asset: {path}")
        _ensure_contained_file(path, project_dir, "upload-ready asset")


def _remove_empty_parents(path, stop):
    path = Path(path)
    stop = Path(stop)
    while path != stop and path.is_relative_to(stop):
        try:
            path.rmdir()
        except OSError:
            return
        path = path.parent


def _production_plan_schema(project):
    try:
        return PRODUCTION_PLAN_SCHEMAS[project["content_unit_type"]]
    except KeyError as exc:
        raise ValueError(
            f"No production plan schema is defined for content_unit_type {project['content_unit_type']!r}"
        ) from exc
