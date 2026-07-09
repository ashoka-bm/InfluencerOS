import datetime
import json
import re
import shutil
from collections import Counter
from pathlib import Path

from influencer_os.generation import validate_reference_approval_records
from influencer_os.json_io import write_json_atomic
from influencer_os.memory import validate_creator_lessons
from influencer_os.projects import collect_anchored_learning_records
from influencer_os.research import validate_events_ledger, validate_promotions
from influencer_os.rubric import reflection_report
from influencer_os.validation import ROOT, ValidationError, load_json, validate_file, validate_record


DEFAULT_CREATOR_WORKSPACE_ROOT = ROOT / "workspace-library" / "creators"
DEFAULT_SOURCE_SKILLS_DIR = ROOT / "skills"
CREATOR_RUNTIME_SKILLS_DIR = Path(".claude") / "skills"
# Replaced skill folders are backed up here on every sync (latest backup kept),
# so a refresh can never silently destroy creator edits (ADR 0018).
SKILLS_BACKUP_DIR = Path(".claude") / "skills-backup"

# Medium-based readiness: media permissions imply visual output, so a
# media-ready foundation needs approved assets of these kinds.
MEDIA_READY_ASSET_TYPES = {"character", "video_style"}

# Statuses that assert stage readiness; draft stays permissive ("permissive at
# intake, strict at readiness").
READINESS_ENFORCED_STATUSES = {
    "profile_ready",
    "foundation_ready",
    "strategy_ready",
    "production_ready",
    "active",
}

# Foundation files that must be populated beyond their scaffold at readiness.
FOUNDATION_FILES = [
    "context/SOUL.md",
    "context/USER.md",
    "context/MEMORY.md",
    "brand_context/identity.md",
    "brand_context/soul.md",
    "brand_context/personal-brand.md",
    "brand_context/voice-samples.md",
]

# Deterministic floor for "ready" creator foundations. This does not judge
# quality; it catches sentence-stubs and older files that lack the sections
# downstream skills depend on.
FOUNDATION_QUALITY_RULES = {
    "brand_context/identity.md": {
        "min_words": 300,
        "required_headings": (
            "Runtime Capsule",
            "Status",
            "Identity Snapshot",
            "Origin Story",
            "Public Role",
            "Continuity Rules",
            "Contradictions To Avoid",
            "Source Notes",
        ),
    },
    "brand_context/soul.md": {
        "min_words": 350,
        "required_headings": (
            "Runtime Capsule",
            "Status",
            "Soul Snapshot",
            "Values",
            "Belief Matrix",
            "Emotional Logic",
            "Audience Emotional Contract",
            "Source Notes",
        ),
    },
    "brand_context/personal-brand.md": {
        "min_words": 500,
        "required_headings": (
            "Runtime Capsule",
            "Status",
            "Brand Snapshot",
            "Positioning",
            "Audience",
            "Content Strategy",
            "Content Pillars",
            "Surface Strategy",
            "Medium Strategy",
            "Monetization And Partnerships",
            "Boundaries And Safety",
            "Growth Goals",
            "Source Notes",
        ),
    },
    "brand_context/voice-samples.md": {
        "min_words": 200,
        "min_voice_samples": 5,
    },
}

# Documented hard maxes for the always-loaded context files; the MEMORY cap
# matches the memory-write pre-write check.
CONTEXT_BYTE_CAPS = {
    "context/SOUL.md": 3072,
    "context/USER.md": 1536,
    "context/MEMORY.md": 2500,
}

# Deterministic subset of the creator-setup medium-based blockers, expressed
# through the reference-library asset_type enum (readiness slice, decision 4).
# Keyed by the pure modality enum (ADR 0024, Creative Direction slice 3):
# carousel/story_sequence are formats, not modalities — their former brand +
# video_style requirements ride the image modality that produces them.
MEDIUM_REQUIRED_ASSET_KINDS = {
    "text": (),
    "image": ("character", "brand", "video_style"),
    "video": ("character", "location", "outfit", "video_style", "brand", "voice"),
    "audio": ("voice",),
}

VISUAL_MEDIUMS = {"image", "video"}

# Lifecycle order: media generation permissions require required kinds at
# prompted or later; retired assets are excluded from readiness entirely.
ASSET_STATUS_RANK = {
    "planned": 0,
    "prompted": 1,
    "user_provided": 2,
    "generated": 2,
    "approved": 3,
}

# Asset lifecycle statuses whose `path` must exist on disk.
ASSET_STATUSES_REQUIRING_FILE = {"user_provided", "generated", "approved"}
ASSET_STATUSES_APPROVED_FOR_MEDIA = {"user_provided", "approved"}
CONVERSION_ASSET_READY_STATUSES = {"approved", "published_or_ready"}
ONBOARDING_STATUS_ORDER = {
    "draft": 0,
    "profile_ready": 1,
    "foundation_ready": 2,
    "strategy_ready": 3,
    "production_ready": 4,
    "active": 5,
    "archived": 6,
}

# Primary reference_refs fields must name assets of these kinds.
PRIMARY_REF_EXPECTED_TYPES = {
    "primary_character_asset_ids": "character",
    "primary_location_asset_ids": "location",
    "primary_video_style_asset_id": "video_style",
}

# Mediums that make a primary reference_refs field mandatory at readiness.
PRIMARY_REF_REQUIRED_BY_MEDIUM = {
    "primary_character_asset_ids": {"image", "video"},
    "primary_location_asset_ids": {"video"},
    "primary_video_style_asset_id": {"image", "video"},
}

INTAKE_ID_PATTERN = re.compile(r"source_[a-zA-Z0-9_-]+")

PLACEHOLDER_PATTERN = re.compile(r"\bTBD\b")
SECTION_HEADING_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
VOICE_SAMPLE_HEADING_PATTERN = re.compile(r"^#{2,3}\s+(?:\d+\.\s+|Sample:)", re.MULTILINE)
WORD_PATTERN = re.compile(r"\b[\w][\w'-]*\b")

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
    "research/runs",
    "research/intelligence",
    "research/stable-findings",
    "conversion-assets",
    "research/idea-queue/entries",
    "research/idea-promotions",
    "boards",
    "system",
    "system/reflection-runs",
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

Track each reference asset by its reference-library lifecycle status —
planned, prompted, generated (awaiting user approval), or approved. Never
mark an asset "completed"; name its status.

### Text

- [ ] Brand voice guide completed
- [ ] Publication or article style guidance completed
- [ ] Topic and pillar strategy completed

### Image

- [ ] Character identity plate — planned
- [ ] Full-body turnaround sheet — planned
- [ ] Macro detail card — planned
- [ ] Brand or visual system reference — planned
- [ ] Image style guidance completed

### Video

- [ ] Character identity plate — planned
- [ ] Full-body turnaround sheet — planned
- [ ] Macro detail card — planned
- [ ] Primary location reference — planned
- [ ] Outfit or wardrobe reference — planned
- [ ] Default video style card — planned
- [ ] ElevenLabs Voice Design prompt package — planned
- [ ] Shot and motion constraints completed

### Voiceover Or Spoken Audio

- [ ] ElevenLabs Voice Design prompt package — planned
- [ ] Imported or approved voice reference before spoken generation — planned
- [ ] Pronunciation and tone boundaries completed

### Carousel Or Story Sequence

- [ ] Sequence style guidance completed
- [ ] Slide or frame visual system — planned
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

    _write_json_if_missing(workspace_dir / "readiness-gates.json", _initial_readiness_gates(manifest))
    _write_json_if_missing(workspace_dir / "channels.json", _initial_channels(manifest))
    _write_json_if_missing(workspace_dir / "content-strategy.json", _initial_content_strategy(manifest))

    # Creator-scope Production Rubric (ADR 0025): scaffolded valid and empty;
    # criteria arrive by seeding from boundaries and by the Rubric Ratchet.
    _write_json_if_missing(
        workspace_dir / "production-rubric.json",
        {
            "rubric_id": f"rubric_{manifest['creator_slug'].replace('-', '_')}",
            "scope": "creator",
            "creator_profile_id": manifest["creator_profile_id"],
            "creator_slug": manifest["creator_slug"],
            "criteria": [],
        },
    )

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
    # exists() follows symlinks and reports False for a broken one, so check
    # is_symlink() too or the copy would write through the link.
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Intake destination already exists: {destination}")
    if not destination.resolve().is_relative_to(workspace_dir.resolve()):
        raise ValueError(
            f"Intake destination must stay inside the workspace: {relative_destination}"
        )

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


def _slug_id(slug):
    return slug.replace("-", "_")


def _initial_gate(status="not_started", blocker="Awaiting setup."):
    return {
        "status": status,
        "approved_on": None,
        "approved_by": None,
        "blockers": [blocker] if blocker else [],
        "waivers": [],
    }


def _initial_readiness_gates(manifest):
    slug_id = _slug_id(manifest["creator_slug"])
    return {
        "readiness_gates_id": f"readiness_gates_{slug_id}",
        "creator_profile_id": manifest["creator_profile_id"],
        "creator_slug": manifest["creator_slug"],
        "updated_on": manifest["created_on"],
        "gates": {
            "profile": _initial_gate("in_progress", "Profile has not been approved."),
            "foundation": {
                **_initial_gate(
                    "not_started",
                    "Reference requirements have not been approved or waived.",
                ),
                "mode": None,
            },
            "strategy": _initial_gate("not_started", "Content strategy has not been created."),
            "production": _initial_gate("not_started", "Content schedule has not been created."),
        },
        "permissions": {
            "creator_image_generation_allowed": False,
            "creator_video_generation_allowed": False,
            "spoken_voice_generation_allowed": False,
        },
    }


def _initial_channels(manifest):
    slug_id = _slug_id(manifest["creator_slug"])
    return {
        "channels_id": f"channels_{slug_id}",
        "creator_profile_id": manifest["creator_profile_id"],
        "creator_slug": manifest["creator_slug"],
        "updated_on": manifest["created_on"],
        "channels": [
            {
                "channel_id": f"channel_{slug_id}_placeholder",
                "platform": "instagram",
                "intended_handle": None,
                "public_url": None,
                "account_status": "not_created",
                "production_drafting_allowed": False,
                "publishing_export_blocked": True,
                "production_approved": False,
                "notes": "Placeholder channel; replace during profile setup.",
            }
        ],
    }


def _initial_content_strategy(manifest):
    slug_id = _slug_id(manifest["creator_slug"])
    return {
        "content_strategy_id": f"content_strategy_{slug_id}",
        "creator_profile_id": manifest["creator_profile_id"],
        "creator_slug": manifest["creator_slug"],
        "updated_on": manifest["created_on"],
        "strategy_status": "planned",
        "monthly_mix": [
            {
                "monthly_mix_id": f"monthly_mix_{slug_id}_placeholder",
                "platform": "instagram",
                "variant_id": f"variant_{slug_id}_placeholder",
                "target_count_per_month": 0,
                "cadence_note": "Placeholder mix; replace during strategy setup.",
            }
        ],
        "post_families": [
            {
                "family_id": f"family_{slug_id}_placeholder",
                "name": "Placeholder",
                "purpose": "Placeholder family; replace during strategy setup.",
                "variants": [
                    {
                        "variant_id": f"variant_{slug_id}_placeholder",
                        "platform": "instagram",
                        "format_id": "format_short_form_video",
                        "modality": "video",
                        "role": "Placeholder variant.",
                    }
                ],
            }
        ],
        "content_campaigns": [],
        "conversion_paths": [],
        "cadence_principles": ["Replace during strategy setup."],
    }


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
    _ensure_no_symlink_components(target_skills_dir, workspace_dir, "creator runtime skills directory")
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
        _ensure_no_symlink_components(target_skill_dir, workspace_dir, "creator runtime skill directory")

        if local_override.exists():
            preserved_override = local_override.read_bytes()
            preserved_overrides += 1

        if target_skill_dir.exists():
            backup_dir = workspace_dir / SKILLS_BACKUP_DIR / source_skill_dir.name
            _ensure_no_symlink_components(backup_dir, workspace_dir, "creator runtime skill backup directory")
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


def _ensure_no_symlink_components(path, workspace_dir, label):
    workspace_dir = Path(workspace_dir)
    path = Path(path)
    try:
        relative = path.relative_to(workspace_dir)
    except ValueError:
        raise ValueError(f"{label} must stay inside the workspace: {path}") from None

    current = workspace_dir
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"{current} is a symlink; {label} must be a real workspace path")


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
    _validate_workspace_record(workspace_dir, manifest, "readiness_gates", "readiness-gates")
    _validate_workspace_record(workspace_dir, manifest, "channels", "channels")
    _validate_workspace_record(workspace_dir, manifest, "content_strategy", "content-strategy")
    _validate_workspace_record(workspace_dir, manifest, "reference_library", "reference-library")

    creator_profile = load_json(workspace_dir / manifest["canonical_files"]["creator_profile"])
    readiness_gates = load_json(workspace_dir / manifest["canonical_files"]["readiness_gates"])
    channels = load_json(workspace_dir / manifest["canonical_files"]["channels"])
    content_strategy = load_json(workspace_dir / manifest["canonical_files"]["content_strategy"])
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
    for label, record in (
        ("readiness gates", readiness_gates),
        ("channels", channels),
        ("content strategy", content_strategy),
    ):
        if record["creator_profile_id"] != manifest["creator_profile_id"]:
            raise ValueError(
                f"{label} creator_profile_id does not match workspace manifest: "
                f"{record['creator_profile_id']!r} != {manifest['creator_profile_id']!r}"
            )
        if record["creator_slug"] != manifest["creator_slug"]:
            raise ValueError(
                f"{label} creator_slug does not match workspace manifest: "
                f"{record['creator_slug']!r} != {manifest['creator_slug']!r}"
            )

    duplicate_asset_ids = sorted(
        asset_id
        for asset_id, count in Counter(
            asset["asset_id"] for asset in reference_library["assets"]
        ).items()
        if count > 1
    )
    if duplicate_asset_ids:
        raise ValueError(
            "Duplicate reference library asset ids: " + ", ".join(duplicate_asset_ids)
        )

    _resolve_reference_refs(creator_profile, reference_library)
    _validate_source_intakes(workspace_dir, manifest)
    _validate_readiness_gates(
        workspace_dir,
        manifest,
        creator_profile,
        reference_library,
        readiness_gates,
        channels,
        content_strategy,
    )
    # Slice 5 review follow-up: Phase 2 learning records must anchor to a
    # schema-valid project manifest at rest, not only in the recall-index
    # scan — the validators stay the strictest check, and both callers
    # share this one function so the rules cannot drift.
    collect_anchored_learning_records(workspace_dir)
    # At-rest parity for the log-learning creator-lesson writer (Phase 2
    # exit criterion 4): hand-edited lessons fail the same evidence rules.
    validate_creator_lessons(workspace_dir)
    # Promotion records validate on the workspace path too (Creative
    # Direction slice 1 review finding): the promotion gate — including the
    # ADR 0024 intent carry-forward check — must be reachable from
    # `validate workspace`, not only `validate research`. No-op when the
    # workspace has no promotions yet.
    promotion_warnings, _, _ = validate_promotions(workspace_dir)
    # Reference-scoped generation approvals (ADR 0023): records under
    # references/approval-records/ validate, and a reference asset whose
    # source_ref claims an approval record must resolve to one. No-op when
    # the workspace has no generation approvals.
    validate_reference_approval_records(workspace_dir, reference_library)
    # Friction ledger and Production Rubric (ADR 0025): the Rubric Ratchet is
    # reachable from `validate workspace`, not only `validate research` —
    # both paths call the one shared seam. No-op when neither exists.
    validate_events_ledger(
        workspace_dir,
        {
            "creator_profile_id": manifest["creator_profile_id"],
            "creator_slug": manifest["creator_slug"],
        },
    )

    warnings = list(promotion_warnings)
    # Reflection trigger (ADR 0025): advisory only, by construction — the
    # report is computed after every failing check above, and a crossed
    # threshold appends a warning, never raises.
    warnings.extend(
        reflection_report(
            workspace_dir,
            scope={
                "creator_profile_id": manifest["creator_profile_id"],
                "creator_slug": manifest["creator_slug"],
            },
        )["warnings"]
    )
    # Audio is a selectable modality with no v1 production-plan schema
    # (ADR 0024): dangling by design, so selecting it warns instead of
    # silently implying supported standalone-audio production.
    if "audio" in creator_profile["content_strategy"]["content_mediums"]:
        warnings.append(
            "warning: content_mediums includes 'audio', which has no "
            "production plan schema yet; standalone-audio production is not "
            "supported in v1 (ADR 0024)"
        )

    return {
        "creator_slug": manifest["creator_slug"],
        "creator_profile_id": manifest["creator_profile_id"],
        "workspace_path": workspace_dir,
        "checked_paths": sorted(set(required_paths)),
        "warnings": warnings,
    }


def _validate_source_intakes(workspace_dir, manifest):
    duplicate_ids = sorted(
        source_id
        for source_id, count in Counter(
            entry["source_id"] for entry in manifest["source_intakes"]
        ).items()
        if count > 1
    )
    if duplicate_ids:
        raise ValueError("Duplicate source intake ids: " + ", ".join(duplicate_ids))
    duplicate_paths = sorted(
        path
        for path, count in Counter(
            entry["path"] for entry in manifest["source_intakes"]
        ).items()
        if count > 1
    )
    if duplicate_paths:
        raise ValueError("Duplicate source intake paths: " + ", ".join(duplicate_paths))

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


def _resolve_reference_refs(creator_profile, reference_library):
    assets_by_id = {asset["asset_id"]: asset for asset in reference_library["assets"]}
    refs = creator_profile["reference_refs"]
    problems = []
    for field, expected_type in PRIMARY_REF_EXPECTED_TYPES.items():
        for asset_id in _named_primary_ids(refs, field):
            asset = assets_by_id.get(asset_id)
            if asset is None:
                problems.append(f"{field} names {asset_id!r}, which is not in the reference library")
            elif asset["asset_type"] != expected_type:
                problems.append(
                    f"{field} names {asset_id!r}, which is a {asset['asset_type']} asset, "
                    f"not {expected_type}"
                )
    if problems:
        raise ValidationError(
            "creator-profile reference_refs do not resolve: " + "; ".join(problems)
        )


def _named_primary_ids(refs, field):
    value = refs.get(field)
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)


def _stage_at_least(status, threshold):
    return ONBOARDING_STATUS_ORDER[status] >= ONBOARDING_STATUS_ORDER[threshold]


def _validate_readiness_gates(
    workspace_dir,
    manifest,
    creator_profile,
    reference_library,
    readiness_gates,
    channels,
    content_strategy,
):
    status = manifest["status"]
    if status not in READINESS_ENFORCED_STATUSES:
        return

    blockers = []
    active_assets = [
        asset for asset in reference_library["assets"] if asset["asset_status"] != "retired"
    ]

    if _stage_at_least(status, "profile_ready"):
        blockers.extend(_profile_stage_blockers(creator_profile, readiness_gates, channels))

    if _stage_at_least(status, "foundation_ready"):
        blockers.extend(_foundation_stage_blockers(workspace_dir, readiness_gates))
        blockers.extend(_foundation_blockers(workspace_dir))

        if not manifest["source_intakes"]:
            blockers.append(
                "no source intake recorded; import at least one setup source with import-intake"
            )

        kinds_present = {asset["asset_type"] for asset in active_assets}

        required_kinds = {}
        for medium in creator_profile["content_strategy"]["content_mediums"]:
            for kind in MEDIUM_REQUIRED_ASSET_KINDS[medium]:
                required_kinds.setdefault(kind, set()).add(medium)

        for kind in sorted(required_kinds):
            if kind not in kinds_present:
                mediums = ", ".join(sorted(required_kinds[kind]))
                blockers.append(
                    f"reference library has no {kind} asset (required by mediums: {mediums})"
                )

        blockers.extend(_voice_design_prompt_blockers(creator_profile, active_assets))
        blockers.extend(_asset_file_blockers(workspace_dir, active_assets))
        blockers.extend(_asset_source_ref_blockers(workspace_dir, manifest, active_assets))
        blockers.extend(
            _primary_ref_blockers(
                status,
                creator_profile,
                {asset["asset_id"]: asset for asset in reference_library["assets"]},
            )
        )

        blockers.extend(
            _media_permission_blockers(readiness_gates, creator_profile, active_assets)
        )

    if _stage_at_least(status, "strategy_ready"):
        blockers.extend(
            _strategy_stage_blockers(
                workspace_dir, readiness_gates, content_strategy, creator_profile
            )
        )

    if _stage_at_least(status, "production_ready"):
        blockers.extend(_production_stage_blockers(workspace_dir, readiness_gates))

    if blockers:
        raise ValidationError(
            f"Readiness blockers for status {status!r}:\n- " + "\n- ".join(blockers)
        )


def _profile_stage_blockers(creator_profile, readiness_gates, channels):
    blockers = []
    profile_gate = readiness_gates["gates"]["profile"]
    if profile_gate["status"] not in {"ready", "waived"}:
        blockers.append("profile gate is not ready or waived in readiness-gates.json")

    selected = set(creator_profile["content_strategy"]["primary_surfaces"])
    registered = {channel["platform"] for channel in channels["channels"]}
    missing = sorted(selected - registered)
    if missing:
        blockers.append(
            "selected channel(s) missing from channels.json: " + ", ".join(missing)
        )
    return blockers


def _foundation_stage_blockers(workspace_dir, readiness_gates):
    blockers = []
    foundation_gate = readiness_gates["gates"]["foundation"]
    if foundation_gate["status"] not in {"ready", "waived"}:
        blockers.append("foundation gate is not ready or waived in readiness-gates.json")
    if foundation_gate["mode"] not in {"media_ready", "prompt_ready"}:
        blockers.append("foundation gate mode must be media_ready or prompt_ready")
    if foundation_gate["mode"] == "media_ready" and foundation_gate["status"] != "ready":
        blockers.append("media_ready foundation gate must be ready, not waived")
    return blockers


def _approved_assets_by_type(assets, asset_type):
    return [
        asset
        for asset in assets
        if asset["asset_type"] == asset_type
        and asset["asset_status"] in ASSET_STATUSES_APPROVED_FOR_MEDIA
        and (asset_type != "voice" or not _is_elevenlabs_voice_design_prompt_asset(asset))
    ]


def _voice_design_prompt_blockers(creator_profile, active_assets):
    mediums = set(creator_profile["content_strategy"]["content_mediums"])
    if not mediums.intersection({"audio", "video"}):
        return []

    if any(_is_elevenlabs_voice_design_prompt_asset(asset) for asset in active_assets):
        return []

    return [
        "audio/video foundation requires a staged ElevenLabs Voice Design prompt "
        "asset at references/voice/<creator-slug>-elevenlabs-voice-design.prompt.md"
    ]


def _is_elevenlabs_voice_design_prompt_asset(asset):
    path = asset.get("path", "")
    return (
        asset["asset_type"] == "voice"
        and ASSET_STATUS_RANK.get(asset["asset_status"], -1) >= ASSET_STATUS_RANK["prompted"]
        and asset.get("prompt_path") == path
        and path.startswith("references/voice/")
        and path.endswith("-elevenlabs-voice-design.prompt.md")
    )


def _media_permission_blockers(readiness_gates, creator_profile, active_assets):
    blockers = []
    permissions = readiness_gates["permissions"]
    refs = creator_profile["reference_refs"]
    assets_by_id = {asset["asset_id"]: asset for asset in active_assets}

    primary_character_assets = [
        assets_by_id[asset_id]
        for asset_id in _named_primary_ids(refs, "primary_character_asset_ids")
        if asset_id in assets_by_id
    ]
    approved_primary_characters = [
        asset
        for asset in primary_character_assets
        if asset["asset_status"] in ASSET_STATUSES_APPROVED_FOR_MEDIA
    ]

    if (
        permissions["creator_image_generation_allowed"]
        or permissions["creator_video_generation_allowed"]
    ) and not approved_primary_characters:
        blockers.append(
            "creator_image_generation_allowed/creator_video_generation_allowed "
            "requires approved visual identity reference(s)"
        )

    if permissions["creator_video_generation_allowed"]:
        video_style_id = refs.get("primary_video_style_asset_id")
        video_style = assets_by_id.get(video_style_id)
        if not video_style or video_style["asset_status"] not in ASSET_STATUSES_APPROVED_FOR_MEDIA:
            blockers.append(
                "creator_video_generation_allowed requires an approved primary video_style reference"
            )

    if permissions["spoken_voice_generation_allowed"] and not _approved_assets_by_type(
        active_assets, "voice"
    ):
        blockers.append(
            "spoken_voice_generation_allowed requires an approved/imported voice reference; "
            "an ElevenLabs Voice Design prompt package is not generated audio"
        )

    if readiness_gates["gates"]["foundation"]["mode"] == "media_ready":
        visual_required = set()
        for medium in creator_profile["content_strategy"]["content_mediums"]:
            if medium in VISUAL_MEDIUMS:
                visual_required.update(MEDIUM_REQUIRED_ASSET_KINDS[medium])
        for kind in sorted(visual_required):
            if not _approved_assets_by_type(active_assets, kind):
                blockers.append(
                    f"media_ready foundation requires an approved {kind} asset"
                )
    return blockers


def _strategy_stage_blockers(workspace_dir, readiness_gates, content_strategy, creator_profile):
    blockers = []
    strategy_gate = readiness_gates["gates"]["strategy"]
    if strategy_gate["status"] not in {"ready", "waived"}:
        blockers.append("strategy gate is not ready or waived in readiness-gates.json")
    if content_strategy["strategy_status"] != "approved":
        blockers.append("content-strategy.json must have strategy_status 'approved'")

    blockers.extend(_strategy_variant_ref_blockers(content_strategy))

    conversion_assets, conversion_asset_blockers = _load_conversion_assets(
        workspace_dir, creator_profile
    )
    blockers.extend(conversion_asset_blockers)
    for asset_id in sorted(_strategy_conversion_asset_ids(content_strategy)):
        asset = conversion_assets.get(asset_id)
        if asset is None:
            blockers.append(f"content-strategy.json references missing conversion asset {asset_id}")
        elif asset["status"] not in CONVERSION_ASSET_READY_STATUSES:
            blockers.append(
                f"conversion asset {asset_id} is {asset['status']!r}; expected approved or published_or_ready"
            )
    return blockers


def _strategy_variant_ref_blockers(content_strategy):
    blockers = []
    declared_variant_ids = {
        variant["variant_id"]
        for family in content_strategy["post_families"]
        for variant in family["variants"]
    }

    for mix in content_strategy["monthly_mix"]:
        variant_id = mix["variant_id"]
        if variant_id not in declared_variant_ids:
            blockers.append(
                f"monthly_mix {mix['monthly_mix_id']} references missing variant {variant_id}"
            )

    for campaign in content_strategy["content_campaigns"]:
        anchor_variant = campaign["anchor_variant"]
        if anchor_variant not in declared_variant_ids:
            blockers.append(
                f"content_campaign {campaign['campaign_id']} references missing anchor_variant {anchor_variant}"
            )
        for variant_id in campaign["derivative_variants"]:
            if variant_id not in declared_variant_ids:
                blockers.append(
                    f"content_campaign {campaign['campaign_id']} references missing derivative variant {variant_id}"
                )
    return blockers


def _production_stage_blockers(workspace_dir, readiness_gates):
    blockers = []
    production_gate = readiness_gates["gates"]["production"]
    if production_gate["status"] not in {"ready", "waived"}:
        blockers.append("production gate is not ready or waived in readiness-gates.json")
    schedule_path = workspace_dir / "content-schedule.json"
    if not schedule_path.exists():
        blockers.append("content-schedule.json is required for production_ready")
    else:
        try:
            validate_file("creator-content-schedule", schedule_path)
        except ValidationError as exc:
            blockers.append(f"Invalid content-schedule.json: {exc}")
    return blockers


def _strategy_conversion_asset_ids(content_strategy):
    asset_ids = set()
    for campaign in content_strategy["content_campaigns"]:
        asset_ids.update(campaign["conversion_asset_ids"])
    for path in content_strategy["conversion_paths"]:
        asset_ids.update(path["conversion_asset_ids"])
    return asset_ids


def _load_conversion_assets(workspace_dir, creator_profile):
    assets = {}
    blockers = []
    for path in sorted((workspace_dir / "conversion-assets").glob("*.json")):
        validate_file("conversion-asset", path)
        record = load_json(path)
        asset_id = record["conversion_asset_id"]
        if record["creator_profile_id"] != creator_profile["creator_profile_id"]:
            blockers.append(
                f"conversion asset {asset_id} creator_profile_id does not match workspace creator"
            )
        if record["creator_slug"] != creator_profile["creator_slug"]:
            blockers.append(
                f"conversion asset {asset_id} creator_slug does not match workspace creator"
            )
        blockers.extend(_conversion_asset_file_ref_blockers(workspace_dir, record))
        assets[record["conversion_asset_id"]] = record
    return assets, blockers


def _conversion_asset_file_ref_blockers(workspace_dir, conversion_asset):
    blockers = []
    conversion_root = (workspace_dir / "conversion-assets").resolve()
    asset_id = conversion_asset["conversion_asset_id"]
    for raw_path in conversion_asset["file_refs"]:
        path = Path(raw_path)
        resolved = (workspace_dir / path).resolve()
        if path.is_absolute() or not resolved.is_relative_to(conversion_root):
            blockers.append(
                f"conversion asset {asset_id} file_refs path must stay inside conversion-assets/: {raw_path!r}"
            )
        elif not resolved.is_file():
            blockers.append(
                f"conversion asset {asset_id} file_refs path does not resolve to a workspace file: {raw_path!r}"
            )
    return blockers


def _foundation_blockers(workspace_dir):
    blockers = []
    for relative_path in FOUNDATION_FILES:
        content = (workspace_dir / relative_path).read_text()
        scaffold_lines = {
            line.strip() for line in MARKDOWN_SCAFFOLDS.get(relative_path, "").splitlines()
        }
        populated = any(
            line.strip() and not line.lstrip().startswith("#") and line.strip() not in scaffold_lines
            for line in content.splitlines()
        )
        if not populated:
            blockers.append(f"{relative_path} is not populated beyond its scaffold")
        if PLACEHOLDER_PATTERN.search(content):
            blockers.append(f"{relative_path} contains a TBD placeholder")
        byte_cap = CONTEXT_BYTE_CAPS.get(relative_path)
        if byte_cap is not None and len(content.encode("utf-8")) > byte_cap:
            blockers.append(f"{relative_path} exceeds its {byte_cap}-byte cap")
        if populated:
            blockers.extend(_foundation_quality_blockers(relative_path, content))
    return blockers


def _foundation_quality_blockers(relative_path, content):
    rules = FOUNDATION_QUALITY_RULES.get(relative_path)
    if rules is None:
        return []

    blockers = []
    min_words = rules.get("min_words")
    if min_words is not None:
        word_count = len(WORD_PATTERN.findall(content))
        if word_count < min_words:
            blockers.append(
                f"{relative_path} is too thin for ready status "
                f"({word_count} words; minimum {min_words})"
            )

    required_headings = rules.get("required_headings", ())
    if required_headings:
        present_headings = {
            heading.strip().lower() for heading in SECTION_HEADING_PATTERN.findall(content)
        }
        missing = [
            heading for heading in required_headings if heading.lower() not in present_headings
        ]
        if missing:
            blockers.append(
                f"{relative_path} missing required section(s): {', '.join(missing)}"
            )

    min_voice_samples = rules.get("min_voice_samples")
    if min_voice_samples is not None:
        sample_count = len(VOICE_SAMPLE_HEADING_PATTERN.findall(content))
        if sample_count < min_voice_samples:
            blockers.append(
                f"{relative_path} has {sample_count} voice sample(s); "
                f"minimum {min_voice_samples}"
            )

    return blockers


def _primary_ref_blockers(status, creator_profile, assets_by_id):
    refs = creator_profile["reference_refs"]
    mediums = set(creator_profile["content_strategy"]["content_mediums"])
    blockers = []
    for field, requiring_mediums in PRIMARY_REF_REQUIRED_BY_MEDIUM.items():
        applicable = sorted(mediums & requiring_mediums)
        if applicable and not _named_primary_ids(refs, field):
            blockers.append(
                f"reference_refs {field} is empty, but mediums {applicable} require it"
            )
    for field in PRIMARY_REF_EXPECTED_TYPES:
        for asset_id in _named_primary_ids(refs, field):
            asset = assets_by_id[asset_id]
            if asset["asset_status"] == "retired":
                blockers.append(f"primary reference {asset_id} is retired")
            elif (
                _stage_at_least(status, "foundation_ready")
                and ASSET_STATUS_RANK[asset["asset_status"]] < ASSET_STATUS_RANK["prompted"]
            ):
                blockers.append(
                    f"primary reference {asset_id} is still planned; "
                    "foundation_ready requires prompted or later"
                )
    return blockers


def _asset_source_ref_blockers(workspace_dir, manifest, assets):
    workspace_root = workspace_dir.resolve()
    intake_ids = {entry["source_id"] for entry in manifest["source_intakes"]}
    blockers = []
    for asset in assets:
        source_ref = asset["source"]["source_ref"]
        if INTAKE_ID_PATTERN.fullmatch(source_ref):
            if source_ref not in intake_ids:
                blockers.append(
                    f"{asset['asset_id']} source_ref names unrecorded intake {source_ref!r}"
                )
            continue
        if source_ref.startswith("gen_approval_"):
            # A generation-approval ref resolves through
            # references/approval-records/ (ADR 0023), not the filesystem;
            # validate_reference_approval_records owns dangling-ref failures.
            if not (
                workspace_dir / "references" / "approval-records" / f"{source_ref}.json"
            ).is_file():
                blockers.append(
                    f"{asset['asset_id']} source_ref names unrecorded "
                    f"generation approval {source_ref!r}"
                )
            continue
        resolved = (workspace_dir / source_ref).resolve()
        if Path(source_ref).is_absolute() or not resolved.is_relative_to(workspace_root):
            blockers.append(f"{asset['asset_id']} source_ref escapes the workspace: {source_ref}")
        elif not resolved.is_file():
            blockers.append(
                f"{asset['asset_id']} source_ref does not resolve to a workspace file "
                f"or recorded intake: {source_ref}"
            )
    return blockers


def _asset_file_blockers(workspace_dir, assets):
    workspace_root = workspace_dir.resolve()
    blockers = []
    for asset in assets:
        status = asset["asset_status"]
        if status in ASSET_STATUSES_REQUIRING_FILE:
            blockers.extend(
                _asset_path_blockers(workspace_dir, workspace_root, asset, "path", asset["path"])
            )
        if status == "prompted" and "prompt_path" not in asset:
            blockers.append(f"{asset['asset_id']} is prompted but declares no prompt_path")
        prompt_path = asset.get("prompt_path")
        if prompt_path:
            blockers.extend(
                _asset_path_blockers(workspace_dir, workspace_root, asset, "prompt_path", prompt_path)
            )
    return blockers


def _asset_path_blockers(workspace_dir, workspace_root, asset, field, raw_path):
    resolved = (workspace_dir / raw_path).resolve()
    if Path(raw_path).is_absolute() or not resolved.is_relative_to(workspace_root):
        return [f"{asset['asset_id']} {field} escapes the workspace: {raw_path}"]
    if not resolved.is_file():
        return [f"{asset['asset_id']} {field} is missing: {raw_path}"]
    return []


def _write_text_if_missing(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content)


def _write_json_if_missing(path, data):
    if not path.exists():
        write_json_atomic(path, data)


def _validate_workspace_record(workspace_dir, manifest, manifest_key, schema_name):
    relative_path = manifest["canonical_files"][manifest_key]
    record_path = workspace_dir / relative_path
    try:
        validate_file(schema_name, record_path)
    except ValidationError as exc:
        raise ValidationError(f"Invalid workspace record {relative_path}: {exc}") from exc
