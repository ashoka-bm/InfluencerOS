"""Small fail-closed readiness guards for production entry points."""

from pathlib import Path

from influencer_os.validation import ValidationError, load_json, validate_record


def require_production_ready(creator_workspace):
    workspace_dir = Path(creator_workspace)
    manifest = load_json(workspace_dir / "creator-workspace.json")
    validate_record("creator-workspace", manifest)
    readiness = load_json(workspace_dir / "readiness-gates.json")
    validate_record("readiness-gates", readiness)

    if manifest["status"] not in {"production_ready", "active"}:
        raise ValidationError(
            "production work requires creator workspace status "
            f"'production_ready' or 'active'; found {manifest['status']!r}"
        )
    milestone = readiness["milestones"]["production"]
    if milestone["status"] not in {"ready", "waived"}:
        raise ValidationError(
            "production work requires explicit production readiness: the "
            "production milestone must be ready or waived"
        )
    return manifest
