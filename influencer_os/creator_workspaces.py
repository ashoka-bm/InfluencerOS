import json
import shutil
from pathlib import Path

from influencer_os.validation import ROOT, ValidationError, load_json, validate_file, validate_record


DEFAULT_CREATOR_WORKSPACE_ROOT = ROOT / "workspace-library" / "creators"
DEFAULT_SOURCE_SKILLS_DIR = ROOT / "skills"
CREATOR_RUNTIME_SKILLS_DIR = Path(".claude") / "skills"

STANDARD_DIRECTORIES = [
    "context",
    "brand_context",
    "sources/intakes",
    "sources/imports",
    "sources/notes",
    "references/character",
    "references/locations",
    "references/outfits",
    "references/objects",
    "references/video-style",
    "references/voice",
    "references/brand",
    "research/social-research-packs",
    "research/video-understanding-packs",
    "research/sources",
    "projects",
    "memory/daily",
    "progress",
]

MARKDOWN_SCAFFOLDS = {
    "context/SOUL.md": "# SOUL\n\nPurpose: always-loaded creator operating identity. Keep under 3 KB.\n\n",
    "context/USER.md": "# USER\n\nPurpose: always-loaded creator/user profile for routine work. Keep under 1.5 KB.\n\n",
    "context/MEMORY.md": "# MEMORY\n\nPurpose: always-loaded curated active memory. Keep under 2.5 KB.\n\n## Active Threads\n\n## Decisions\n\n## Blockers\n\n",
    "brand_context/identity.md": "# Identity\n\n",
    "brand_context/soul.md": "# Soul\n\n",
    "brand_context/personal-brand.md": "# Personal Brand\n\n",
    "brand_context/voice-samples.md": "# Voice Samples\n\n",
    "memory/MEMORY.md": "# Memory\n\n## Active Threads\n\n## Environment Notes\n\n## Pending Decisions\n\n",
    "memory/learnings.md": "# Learnings\n\n",
    "progress/setup-checklist.md": """# Setup Checklist

## Status

- Workspace status: draft
- Foundation accepted: no

## Required For All Creators

- [ ] Identity file completed
- [ ] Soul file completed
- [ ] Personal brand file completed
- [ ] Niche accepted
- [ ] Target audience accepted
- [ ] Content strategy accepted
- [ ] Content boundaries accepted
- [ ] Source provenance recorded

## Medium-Based Blockers

### Text

- [ ] Brand voice guide completed
- [ ] Publication or article style guidance completed
- [ ] Topic and pillar strategy completed

### Image

- [ ] Three character assets completed or prompted
- [ ] Brand or visual system reference completed
- [ ] Image style guidance completed
- [ ] Required image prompts or approved image references completed

### Video

- [ ] Character identity plate completed
- [ ] Full-body turnaround sheet completed
- [ ] Macro detail card completed
- [ ] Primary location reference completed
- [ ] Outfit or wardrobe reference completed
- [ ] Default video style card completed
- [ ] Shot and motion constraints completed

### Voiceover Or Spoken Audio

- [ ] Voice sample or accepted voice style note completed
- [ ] Pronunciation and tone boundaries completed

### Carousel Or Story Sequence

- [ ] Sequence style guidance completed
- [ ] Slide or frame visual system completed
- [ ] Text overlay policy completed

## Review Notes

""",
    "AGENTS.md": "# Creator Workspace Instructions\n\nAlways load `context/SOUL.md`, `context/USER.md`, and `context/MEMORY.md` first. Lazy-load `brand_context/` files and references only when the task requires detail.\n",
}

JSON_SCAFFOLDS = {
    "creator-profile.json": {},
    "references/reference-library.json": {},
}


def init_creator(manifest_path, workspace_root=DEFAULT_CREATOR_WORKSPACE_ROOT):
    manifest_path = Path(manifest_path)
    workspace_root = Path(workspace_root)
    manifest = load_json(manifest_path)
    validate_record("creator-workspace", manifest)

    workspace_dir = workspace_root / manifest["creator_slug"]
    if workspace_dir.exists():
        raise FileExistsError(f"Creator workspace already exists: {workspace_dir}")

    for directory in STANDARD_DIRECTORIES:
        (workspace_dir / directory).mkdir(parents=True, exist_ok=True)

    shutil.copyfile(manifest_path, workspace_dir / "creator-workspace.json")

    for relative_path, content in MARKDOWN_SCAFFOLDS.items():
        _write_text_if_missing(workspace_dir / relative_path, content)

    for relative_path, data in JSON_SCAFFOLDS.items():
        _write_json_if_missing(workspace_dir / relative_path, data)

    sync_creator_runtime(workspace_dir)

    return workspace_dir


def sync_creator_runtime(workspace_path, source_skills_dir=DEFAULT_SOURCE_SKILLS_DIR):
    workspace_dir = Path(workspace_path)
    manifest_path = workspace_dir / "creator-workspace.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing creator workspace manifest: {manifest_path}")

    source_skills_dir = Path(source_skills_dir)
    if not source_skills_dir.exists():
        raise FileNotFoundError(f"Missing source skills directory: {source_skills_dir}")

    target_skills_dir = workspace_dir / CREATOR_RUNTIME_SKILLS_DIR
    target_skills_dir.mkdir(parents=True, exist_ok=True)

    synced = []
    preserved_overrides = 0
    for source_skill_dir in sorted(source_skills_dir.iterdir()):
        if not source_skill_dir.is_dir():
            continue
        if not (source_skill_dir / "SKILL.md").exists():
            continue

        target_skill_dir = target_skills_dir / source_skill_dir.name
        local_override = target_skill_dir / "SKILL.local.md"
        preserved_override = None

        if local_override.exists():
            preserved_override = local_override.read_bytes()
            preserved_overrides += 1

        if target_skill_dir.exists():
            shutil.rmtree(target_skill_dir)
        shutil.copytree(
            source_skill_dir,
            target_skill_dir,
            ignore=shutil.ignore_patterns("SKILL.local.md"),
        )

        if preserved_override is not None:
            (target_skill_dir / "SKILL.local.md").write_bytes(preserved_override)

        synced.append(source_skill_dir.name)

    return {
        "workspace_path": workspace_dir,
        "skills_path": target_skills_dir,
        "synced_skills": synced,
        "preserved_overrides": preserved_overrides,
    }


def validate_creator_workspace(workspace_path):
    workspace_dir = Path(workspace_path)
    manifest_path = workspace_dir / "creator-workspace.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing creator workspace manifest: {manifest_path}")

    manifest = load_json(manifest_path)
    validate_record("creator-workspace", manifest)

    expected_root_suffix = f"workspace-library/creators/{manifest['creator_slug']}/"
    if manifest["root_path"] != expected_root_suffix:
        raise ValueError(f"Manifest root_path does not match creator_slug: {manifest['root_path']!r}")

    required_paths = ["creator-workspace.json", "AGENTS.md", str(CREATOR_RUNTIME_SKILLS_DIR)]
    required_paths.extend(manifest["canonical_files"].values())
    required_paths.extend(manifest["directories"].values())
    required_paths.extend(["context/SOUL.md", "context/USER.md", "context/MEMORY.md", "memory/MEMORY.md", "memory/learnings.md", "progress/setup-checklist.md"])

    missing = []
    for relative_path in required_paths:
        candidate = workspace_dir / relative_path
        if not candidate.exists():
            missing.append(relative_path)

    if missing:
        raise FileNotFoundError(f"Missing workspace paths: {', '.join(sorted(missing))}")

    _validate_workspace_record(workspace_dir, manifest, "creator_profile", "creator-profile")
    _validate_workspace_record(workspace_dir, manifest, "reference_library", "reference-library")

    creator_profile = load_json(workspace_dir / manifest["canonical_files"]["creator_profile"])
    reference_library = load_json(workspace_dir / manifest["canonical_files"]["reference_library"])

    if creator_profile["creator_profile_id"] != manifest["creator_profile_id"]:
        raise ValueError(
            "Creator profile id does not match workspace manifest: "
            f"{creator_profile['creator_profile_id']!r} != {manifest['creator_profile_id']!r}"
        )
    if creator_profile["creator_slug"] != manifest["creator_slug"]:
        raise ValueError(
            "Creator profile slug does not match workspace manifest: "
            f"{creator_profile['creator_slug']!r} != {manifest['creator_slug']!r}"
        )
    if creator_profile["workspace_ref"] != manifest["creator_workspace_id"]:
        raise ValueError(
            "Creator profile workspace_ref does not match workspace manifest: "
            f"{creator_profile['workspace_ref']!r} != {manifest['creator_workspace_id']!r}"
        )
    if reference_library["creator_profile_id"] != manifest["creator_profile_id"]:
        raise ValueError(
            "Reference library creator_profile_id does not match workspace manifest: "
            f"{reference_library['creator_profile_id']!r} != {manifest['creator_profile_id']!r}"
        )

    return {
        "creator_slug": manifest["creator_slug"],
        "creator_profile_id": manifest["creator_profile_id"],
        "workspace_path": workspace_dir,
        "checked_paths": sorted(set(required_paths)),
    }


def _write_text_if_missing(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content)


def _write_json_if_missing(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(json.dumps(data, indent=2) + "\n")


def _validate_workspace_record(workspace_dir, manifest, manifest_key, schema_name):
    relative_path = manifest["canonical_files"][manifest_key]
    record_path = workspace_dir / relative_path
    try:
        validate_file(schema_name, record_path)
    except ValidationError as exc:
        raise ValidationError(f"Invalid workspace record {relative_path}: {exc}") from exc
