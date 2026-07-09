"""Creator Workspace scope loading and record-scope checks."""

from pathlib import Path

from influencer_os.validation import ValidationError, load_json, validate_record


def load_workspace_scope(workspace_dir):
    """Load the creator identity that owns records inside a workspace."""
    manifest_path = Path(workspace_dir) / "creator-workspace.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing creator workspace manifest: {manifest_path}")
    manifest = load_json(manifest_path)
    try:
        validate_record("creator-workspace", manifest)
    except ValidationError as exc:
        raise ValidationError(f"{manifest_path}: {exc}") from None
    return {
        "creator_profile_id": manifest["creator_profile_id"],
        "creator_slug": manifest["creator_slug"],
    }


def check_creator_scope(record, scope, context=None):
    """Pin the creator fields a record carries to its owning workspace."""
    for field, expected in scope.items():
        value = record.get(field)
        if value is not None and value != expected:
            prefix = f"{context}: " if context else ""
            raise ValidationError(
                f"{prefix}{field} {value!r} does not match the owning "
                f"creator workspace ({expected!r})"
            )
