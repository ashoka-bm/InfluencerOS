"""Composed full-chain validation (the alpha release gate).

``validate all <creator-workspace>`` runs every validator over one Creator
Workspace so the Product Invariant is enforced by a single command instead of
a hand-chained sequence: the workspace manifest and readiness milestones, research
state, the opportunity queue, campaign records, rebuildable board/calendar projections when present, and every project under
``projects/``. Layer errors carry the failing layer's name.

The queue and board layers are lifecycle-aware: a workspace that has not
started research has no queue manifest yet, and a board exists only after
``rebuild-board``. Missing-because-not-started is a recorded skip — but queue
entries without a manifest are an inconsistency and fail, because skipping
them would leave every entry unvalidated.
"""

from pathlib import Path

from influencer_os.boards import board_path_for, validate_board
from influencer_os.calendars import calendar_path_for, validate_calendar
from influencer_os.creator_workspaces import validate_creator_workspace
from influencer_os.projects import validate_project
from influencer_os.research import (
    collect_project_manifests,
    validate_queue,
    validate_research,
)
from influencer_os.validation import ValidationError


def _run_layer(layer, func, *args):
    try:
        return func(*args)
    except (ValidationError, FileNotFoundError, ValueError) as exc:
        raise ValidationError(f"[{layer}] {exc}") from None


def validate_all(workspace_path):
    """Validate one Creator Workspace end to end. Returns the per-layer
    summaries, recorded skips, and the deduplicated warnings from every
    layer (the same promotion warning surfaces on several layers; it is
    reported once, in first-seen order)."""
    workspace_dir = Path(workspace_path)
    layers = []
    skipped = []
    warnings = []

    result = _run_layer("workspace", validate_creator_workspace, workspace_dir)
    warnings.extend(result.get("warnings", []))
    layers.append(("workspace", f"{len(result['checked_paths'])} workspace paths"))

    result = _run_layer("research", validate_research, workspace_dir)
    warnings.extend(result.get("warnings", []))
    layers.append(("research", f"{len(result['checked_paths'])} research records"))

    queue_dir = workspace_dir / "research" / "content-opportunity-queue"
    manifest_path = queue_dir / "queue.json"
    entries_dir = queue_dir / "entries"
    entry_paths = sorted(entries_dir.glob("*.json")) if entries_dir.exists() else []
    if manifest_path.exists():
        result = _run_layer("queue", validate_queue, workspace_dir)
        warnings.extend(result.get("warnings", []))
        layers.append(("queue", f"{result['entry_count']} queue entries"))
    elif entry_paths:
        raise ValidationError(
            f"[queue] {len(entry_paths)} opportunity entries exist without a "
            f"queue manifest: {manifest_path} is missing"
        )
    else:
        skipped.append(("queue", "no queue manifest yet"))

    from influencer_os.campaigns import validate_campaign_records

    if (workspace_dir / "campaigns").exists() or manifest_path.exists():
        result = _run_layer(
            "campaigns", validate_campaign_records, workspace_dir
        )
        layers.append(
            ("campaigns", f"{len(result['checked_paths'])} campaign records")
        )
    else:
        skipped.append(("campaigns", "no campaigns yet"))

    board_path = board_path_for(workspace_dir)
    if board_path.exists():
        result = _run_layer("board", validate_board, workspace_dir)
        layers.append(("board", f"{result['card_count']} board cards"))
    else:
        skipped.append(("board", "no content board yet (run rebuild-board)"))

    calendar_path = calendar_path_for(workspace_dir)
    if calendar_path.exists():
        result = _run_layer("calendar", validate_calendar, workspace_dir)
        layers.append(("calendar", f"{result['post_count']} scheduled posts"))

    manifests = _run_layer("projects", collect_project_manifests, workspace_dir)
    projects_dir = workspace_dir / "projects"
    if projects_dir.exists():
        manifest_dirs = {path.parent for path, _record in manifests.values()}
        orphans = sorted(
            str(path.relative_to(workspace_dir))
            for path in projects_dir.iterdir()
            if path.is_dir() and path not in manifest_dirs
        )
        if orphans:
            raise ValidationError(
                f"[projects] project folders without a project.json manifest: {orphans}"
            )
    project_count = 0
    for project_id, (project_manifest_path, _record) in sorted(manifests.items()):
        result = _run_layer(
            f"project {project_id}", validate_project, project_manifest_path.parent
        )
        warnings.extend(result.get("warnings", []))
        project_count += 1
    layers.append(("projects", f"{project_count} projects"))

    return {
        "workspace_path": workspace_dir,
        "layers": layers,
        "skipped": skipped,
        "project_count": project_count,
        "warnings": list(dict.fromkeys(warnings)),
    }
