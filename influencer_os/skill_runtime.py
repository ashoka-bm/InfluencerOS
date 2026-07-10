"""Synchronize repository-owned skills into the global Codex runtime."""

import shutil
from pathlib import Path

from influencer_os.validation import ROOT, ValidationError


DEFAULT_SOURCE_SKILLS_DIR = ROOT / "skills"
DEFAULT_CODEX_SKILLS_DIR = Path.home() / ".codex" / "skills"


def _source_skill_dirs(source_skills_dir):
    source_root = Path(source_skills_dir)
    if not source_root.exists():
        raise FileNotFoundError(f"Missing source skills directory: {source_root}")
    return [
        path
        for path in sorted(source_root.iterdir())
        if path.is_dir() and (path / "SKILL.md").exists()
    ]


def _owned_files(skill_dir):
    return {
        path.relative_to(skill_dir): path.read_bytes()
        for path in sorted(skill_dir.rglob("*"))
        if path.is_file() and path.name != "SKILL.local.md"
    }


def codex_skill_drift(
    target_root=DEFAULT_CODEX_SKILLS_DIR,
    source_skills_dir=DEFAULT_SOURCE_SKILLS_DIR,
):
    """Return source-owned global skill files that are missing or different."""
    target_root = Path(target_root)
    drift = []
    for source_skill in _source_skill_dirs(source_skills_dir):
        target_skill = target_root / source_skill.name
        if not target_skill.exists():
            drift.append(f"{source_skill.name}: missing")
            continue
        if target_skill.is_symlink():
            if target_skill.resolve() != source_skill.resolve():
                drift.append(f"{source_skill.name}: target is a foreign symlink")
            continue
        source_files = _owned_files(source_skill)
        target_files = _owned_files(target_skill)
        for relative_path in sorted(set(source_files) | set(target_files)):
            if relative_path not in target_files:
                drift.append(f"{source_skill.name}/{relative_path}: missing")
            elif relative_path not in source_files:
                drift.append(f"{source_skill.name}/{relative_path}: extra")
            elif target_files[relative_path] != source_files[relative_path]:
                drift.append(f"{source_skill.name}/{relative_path}: changed")
    return drift


def validate_codex_skill_drift(
    target_root=DEFAULT_CODEX_SKILLS_DIR,
    source_skills_dir=DEFAULT_SOURCE_SKILLS_DIR,
):
    drift = codex_skill_drift(
        target_root=target_root, source_skills_dir=source_skills_dir
    )
    if drift:
        raise ValidationError("Codex skill drift: " + "; ".join(drift))
    return {
        "target_root": Path(target_root),
        "skill_count": len(_source_skill_dirs(source_skills_dir)),
    }


def sync_codex_skills(
    target_root=DEFAULT_CODEX_SKILLS_DIR,
    source_skills_dir=DEFAULT_SOURCE_SKILLS_DIR,
):
    """Replace source-owned global skill copies, preserving local overrides."""
    target_root = Path(target_root)
    if target_root.is_symlink():
        raise ValueError(f"{target_root} is a symlink; Codex skill root must be real")
    target_root.mkdir(parents=True, exist_ok=True)
    source_skills = _source_skill_dirs(source_skills_dir)
    for source_skill in source_skills:
        target_skill = target_root / source_skill.name
        if (
            target_skill.is_symlink()
            and target_skill.resolve() != source_skill.resolve()
        ):
            raise ValueError(
                f"{target_skill} is a foreign symlink; Codex skill target must "
                "resolve to its canonical source"
            )
    backup_root = target_root.parent / "skills-backup"
    synced = []
    backed_up = 0
    preserved_overrides = 0
    for source_skill in source_skills:
        target_skill = target_root / source_skill.name
        if target_skill.is_symlink():
            synced.append(source_skill.name)
            continue
        override = target_skill / "SKILL.local.md"
        override_bytes = override.read_bytes() if override.exists() else None
        if override_bytes is not None:
            preserved_overrides += 1
        if target_skill.exists():
            backup = backup_root / source_skill.name
            if backup.exists():
                shutil.rmtree(backup)
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(target_skill, backup)
            shutil.rmtree(target_skill)
            backed_up += 1
        shutil.copytree(
            source_skill,
            target_skill,
            ignore=shutil.ignore_patterns("SKILL.local.md"),
        )
        if override_bytes is not None:
            (target_skill / "SKILL.local.md").write_bytes(override_bytes)
        synced.append(source_skill.name)
    validate_codex_skill_drift(
        target_root=target_root, source_skills_dir=source_skills_dir
    )
    return {
        "target_root": target_root,
        "synced_skills": synced,
        "backed_up_skills": backed_up,
        "preserved_overrides": preserved_overrides,
    }
