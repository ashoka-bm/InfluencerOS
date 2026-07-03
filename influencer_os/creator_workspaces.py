import datetime
import json
import shutil
from pathlib import Path

from influencer_os.validation import ROOT, ValidationError, load_json, validate_file, validate_record


DEFAULT_CREATOR_WORKSPACE_ROOT = ROOT / "workspace-library" / "creators"
DEFAULT_SOURCE_SKILLS_DIR = ROOT / "skills"
CREATOR_RUNTIME_SKILLS_DIR = Path(".claude") / "skills"
# Replaced skill folders are backed up here on every sync (latest backup kept),
# so a refresh can never silently destroy creator edits (ADR 0018).
SKILLS_BACKUP_DIR = Path(".claude") / "skills-backup"

# Medium-based readiness: generation implies visual output, so a
# generation_ready workspace needs at least one approved asset of these kinds.
GENERATION_READY_ASSET_TYPES = {"character", "video_style"}

# Source-type routing from the creator-setup Source Import rules: master-intake
# material (breakdowns, interviews) lands in intakes/, external docs in
# imports/, informal notes in notes/.
INTAKE_DESTINATIONS = {
    "breakdown": "sources/intakes",
    "interview": "sources/intakes",
    "handoff": "sources/imports",
    "import": "sources/imports",
    "notes": "sources/notes",
}

# Extraction lifecycle is forward-only; skipping "drafted" is allowed.
EXTRACTION_STATUS_ORDER = {"pending": 0, "drafted": 1, "reviewed": 2}

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
    "AGENTS.md": """# Creator Workspace Instructions

Always load `context/SOUL.md`, `context/USER.md`, and `context/MEMORY.md` first. Lazy-load `brand_context/` files and references only when the task requires detail.

Runtime skills are copies under `.claude/skills/`. Creator-specific overrides live beside each copied skill as `SKILL.local.md`; they survive `sync-creator-runtime` and `update-creators` refreshes, and each replaced skill folder is backed up to `.claude/skills-backup/`.

Gated zones (scripts, settings, hooks, cron) are deferred and inert: no such content is propagated into this workspace until the subsystem is explicitly un-deferred (ADR 0018).
""",
    "CLAUDE.md": """# Creator Workspace Claude Adapter

Thin adapter (ADR 0019 pattern): the workspace operating contract lives in `AGENTS.md`. Read it first and follow it.

@AGENTS.md
""",
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


def import_intake(workspace_path, source_file, source_type, notes, source_id=None, imported_on=None):
    workspace_dir = Path(workspace_path)
    manifest_path = workspace_dir / "creator-workspace.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing creator workspace manifest: {manifest_path}")
    manifest = load_json(manifest_path)
    validate_record("creator-workspace", manifest)

    source_file = Path(source_file)
    if not source_file.is_file():
        raise FileNotFoundError(f"Missing intake source file: {source_file}")
    if source_type not in INTAKE_DESTINATIONS:
        raise ValueError(
            f"Unknown source type {source_type!r}; expected one of {sorted(INTAKE_DESTINATIONS)}"
        )

    relative_destination = f"{INTAKE_DESTINATIONS[source_type]}/{source_file.name}"
    destination = workspace_dir / relative_destination
    if destination.exists():
        raise FileExistsError(f"Intake destination already exists: {destination}")

    existing_ids = {entry["source_id"] for entry in manifest["source_intakes"]}
    if source_id is None:
        source_id = _next_intake_id(manifest["creator_slug"], source_type, existing_ids)
    elif source_id in existing_ids:
        raise ValueError(f"Source intake id already recorded: {source_id!r}")

    entry = {
        "source_id": source_id,
        "source_type": source_type,
        "path": relative_destination,
        "imported_on": imported_on or datetime.date.today().isoformat(),
        "extraction_status": "pending",
        "notes": notes,
    }
    updated_manifest = dict(manifest)
    updated_manifest["source_intakes"] = manifest["source_intakes"] + [entry]
    validate_record("creator-workspace", updated_manifest)

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_file, destination)
    _write_manifest(manifest_path, updated_manifest)

    return {
        "workspace_path": workspace_dir,
        "source_id": source_id,
        "source_type": source_type,
        "destination": destination,
        "extraction_status": "pending",
    }


def set_intake_status(workspace_path, source_id, new_status):
    workspace_dir = Path(workspace_path)
    manifest_path = workspace_dir / "creator-workspace.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing creator workspace manifest: {manifest_path}")
    manifest = load_json(manifest_path)
    validate_record("creator-workspace", manifest)

    if new_status not in EXTRACTION_STATUS_ORDER:
        ordered = sorted(EXTRACTION_STATUS_ORDER, key=EXTRACTION_STATUS_ORDER.get)
        raise ValueError(f"Unknown extraction status {new_status!r}; expected one of {ordered}")

    matches = [entry for entry in manifest["source_intakes"] if entry["source_id"] == source_id]
    if not matches:
        raise ValueError(f"Unknown source intake id: {source_id!r}")
    entry = matches[0]

    previous_status = entry["extraction_status"]
    if EXTRACTION_STATUS_ORDER[new_status] <= EXTRACTION_STATUS_ORDER[previous_status]:
        raise ValueError(
            f"Extraction status only moves forward: {previous_status!r} -> {new_status!r} is not allowed"
        )

    entry["extraction_status"] = new_status
    validate_record("creator-workspace", manifest)
    _write_manifest(manifest_path, manifest)

    return {
        "workspace_path": workspace_dir,
        "source_id": source_id,
        "previous_status": previous_status,
        "extraction_status": new_status,
    }


def _next_intake_id(creator_slug, source_type, existing_ids):
    prefix = f"source_{creator_slug.replace('-', '_')}_{source_type}"
    sequence = 1
    while f"{prefix}_{sequence:03d}" in existing_ids:
        sequence += 1
    return f"{prefix}_{sequence:03d}"


def _write_manifest(manifest_path, manifest):
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


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
    backed_up_skills = 0
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
            backup_dir = workspace_dir / SKILLS_BACKUP_DIR / source_skill_dir.name
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            backup_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(target_skill_dir, backup_dir)
            backed_up_skills += 1
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
        "backed_up_skills": backed_up_skills,
    }


def update_creators(workspace_root=DEFAULT_CREATOR_WORKSPACE_ROOT, source_skills_dir=DEFAULT_SOURCE_SKILLS_DIR):
    workspace_root = Path(workspace_root)
    if not workspace_root.exists():
        raise FileNotFoundError(f"Missing creator workspace root: {workspace_root}")

    results = []
    for workspace_dir in sorted(workspace_root.iterdir()):
        if not workspace_dir.is_dir():
            continue
        if not (workspace_dir / "creator-workspace.json").exists():
            continue
        results.append(sync_creator_runtime(workspace_dir, source_skills_dir=source_skills_dir))
    return results


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

    required_paths = ["creator-workspace.json", "AGENTS.md", "CLAUDE.md", str(CREATOR_RUNTIME_SKILLS_DIR)]
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

    _validate_source_intakes(workspace_dir, manifest)
    _validate_readiness_gates(manifest, reference_library)

    return {
        "creator_slug": manifest["creator_slug"],
        "creator_profile_id": manifest["creator_profile_id"],
        "workspace_path": workspace_dir,
        "checked_paths": sorted(set(required_paths)),
    }


def _validate_source_intakes(workspace_dir, manifest):
    workspace_root = workspace_dir.resolve()
    escaping = []
    missing = []
    for entry in manifest["source_intakes"]:
        raw_path = entry["path"]
        resolved = (workspace_dir / raw_path).resolve()
        if Path(raw_path).is_absolute() or not resolved.is_relative_to(workspace_root):
            escaping.append(raw_path)
        elif not resolved.is_file():
            missing.append(raw_path)
    if escaping:
        raise ValueError(
            f"Source intake paths must stay inside the workspace: {', '.join(sorted(escaping))}"
        )
    if missing:
        raise FileNotFoundError(f"Missing source intake files: {', '.join(sorted(missing))}")


def _validate_readiness_gates(manifest, reference_library):
    if manifest["status"] != "generation_ready":
        return
    approved_visual_assets = [
        asset
        for asset in reference_library["assets"]
        if asset["asset_type"] in GENERATION_READY_ASSET_TYPES
        and asset["asset_status"] == "approved"
    ]
    if not approved_visual_assets:
        raise ValidationError(
            "generation_ready workspace requires at least one approved visual asset of kind "
            f"{sorted(GENERATION_READY_ASSET_TYPES)!r} in references/reference-library.json"
        )


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
