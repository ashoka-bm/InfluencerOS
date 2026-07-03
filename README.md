# InfluencerOS

InfluencerOS creates universal short-form video ideas and base generation plans for avatar-led social media creators.

InfluencerOS is also being structured as a local-first Agentic OS adaptation. Root adapter files load the same durable project context for Codex, Claude, OpenClaw/Hermes-style agents, and compatible tools.

The v1 flow:

```text
Choose Creator
  -> optionally understand real videos from frames and transcripts
  -> synthesize current social research
  -> use a minimal visual social post format shortlist
  -> produce five creator-fit visual social ideas
  -> choose one idea
  -> apply a format-compatible social template
  -> create a format-specific production plan
  -> create a base generation plan when needed
```

InfluencerOS v1 is platform-agnostic. It targets short vertical videos that can work across Instagram Reels, TikTok, and YouTube Shorts without a platform adapter.

See [docs/os-construction/progress.md](docs/os-construction/progress.md) for the current phase map and build status.

## Current Build/Test Data Policy

InfluencerOS is currently in a system-building and workflow-testing phase. Any creator workspaces, generated personas, reference prompts, generated media, research notes, projects, memory, or progress files under `workspace-library/` are disposable test data unless the user explicitly says otherwise.

The durable work is the operating system itself: docs, schemas, tests, CLI behavior, skills, templates, examples, and validation rules. Before real creator onboarding starts, the operator expects to wipe the test creator data and start from clean, accepted creator foundations.

## Start Here

- [CONTEXT.md](CONTEXT.md): product vocabulary and naming source of truth.
- [docs/os-construction/prd.md](docs/os-construction/prd.md): purpose, scope, requirements, and deterministic acceptance criteria.
- [docs/os-construction/roadmap.md](docs/os-construction/roadmap.md): phase order and exit criteria.
- [docs/os-construction/short-term-plan.md](docs/os-construction/short-term-plan.md): next handoff plan for parity hardening.
- [docs/os-construction/repository-map.md](docs/os-construction/repository-map.md): where files live and how the creation flow is organized.
- [docs/os-construction/agentic-os-alignment.md](docs/os-construction/agentic-os-alignment.md): how this repo copies or diverges from the Agentic OS reference.
- [docs/os-construction/agentic-os-copy-plan.md](docs/os-construction/agentic-os-copy-plan.md): audit of what to copy, adapt, defer, or reject from Agentic OS.
- [docs/os-construction/agentic-os-parity-plan.md](docs/os-construction/agentic-os-parity-plan.md): plan for adapting toward close Agentic OS parity without restarting.
- [docs/os-construction/divergence-test.md](docs/os-construction/divergence-test.md): pass/fail check for architecture-impacting divergence.
- [docs/os-construction/visual-architecture-maps.md](docs/os-construction/visual-architecture-maps.md): Excalidraw mapping standard for system and workflow diagrams.
- [docs/os-construction/context-matrix.md](docs/os-construction/context-matrix.md): what context each workflow should load.
- [docs/os-construction/skill-registry.md](docs/os-construction/skill-registry.md): skill triggers, writes, and override policy.
- [ARCHITECTURE.md](ARCHITECTURE.md): durable architecture direction.

Creator setup can capture broader creator strategy inputs, including written surfaces such as Substack, LinkedIn, X, blogs, and newsletters. The current production pipeline still starts with the platform-agnostic visual social formats documented in the schemas and workflow docs.

## What V1 Includes

- Creator Workspace schema
- Creator Profile schema
- Reference Library schema
- Creator Setup workflow
- Create Influencer conductor skill
- Creator Setup subskills and templates
- Voice samples template for creator setup
- Project schema
- Output Package schema
- Published Post Record schema
- Analytics Snapshot schema
- Performance Summary schema
- Social Research Pack schema
- Video Understanding Pack schema
- Social Post Format schema
- five-idea Content Idea Set schema
- Selected Content Idea schema
- Social Template and Applied Social Template schemas
- Micro-Journey Video Plan schema
- Carousel Plan schema
- Single Image Post Plan schema
- Story Sequence Plan schema
- Base Video Generation Plan schema
- conductor skill for the first slice

## What V1 Defers

- platform-specific motion graphics
- caption styling and post-production treatments
- publishing, scheduling, or uploads
- analytics feedback loops
- provider-backed generation without explicit approval

## Validate Examples

```bash
python3 -m influencer_os validate examples
```

## Initialize A Creator Workspace

```bash
python3 -m influencer_os init-creator examples/creator-workspace.example.json
```

This creates a local ignored creator workspace under:

```text
workspace-library/creators/
```

During the current build phase, creator workspaces initialized here are fixtures for testing setup, validation, generation gates, and workflow ergonomics. Do not treat their contents as permanent production data unless the user explicitly promotes a workspace out of test status.

After authoring `creator-profile.json` and `references/reference-library.json`, validate the workspace with:

```bash
python3 -m influencer_os validate workspace workspace-library/creators/luna-fit
```

Validation is status-keyed: a `draft` workspace stays permissive, while a workspace claiming `content_ready`, `generation_ready`, or `active` must pass the medium-based readiness blockers (populated foundation files without `TBD` placeholders, context byte caps, recorded source intake, required reference-asset kinds per declared content medium, and lifecycle-appropriate asset/prompt files on disk). Failures report the full blocker list in one run.

Creator Workspaces run copied baseline skills from `.claude/skills/`. Refresh those copied runtime skills after root skill changes with:

```bash
python3 -m influencer_os sync-creator-runtime workspace-library/creators/luna-fit
```

Refresh every Creator Workspace at once (each replaced skill folder is backed up to `.claude/skills-backup/`, and `SKILL.local.md` files, creator-only skills, and creator state are preserved):

```bash
python3 -m influencer_os update-creators
```

## Import Setup Sources

Import a master breakdown, interview transcript, or other setup source into a Creator Workspace. The file is copied under `sources/` by type (`breakdown`/`interview` → `intakes/`, `handoff`/`import` → `imports/`, `notes` → `notes/`) and a `source_intakes` provenance entry is recorded in `creator-workspace.json` with `extraction_status: "pending"`:

```bash
python3 -m influencer_os import-intake path/to/master-breakdown.md --creator-workspace workspace-library/creators/luna-fit --source-type breakdown --notes "Master breakdown provided by user."
```

Record extraction progress as setup advances (`drafted` when foundation drafts are derived, `reviewed` after human review; forward-only):

```bash
python3 -m influencer_os set-intake-status workspace-library/creators/luna-fit source_luna_fit_breakdown_001 drafted
```

Intake paths are schema-pinned under `sources/`, and `validate workspace` requires every recorded intake path to resolve to a real file inside the workspace (symlink escapes are rejected).

## Initialize A Project

```bash
python3 -m influencer_os init-project examples/project.example.json --creator-workspace workspace-library/creators/luna-fit
```

After adding the selected idea and plan records, validate the project with:

```bash
python3 -m influencer_os validate project workspace-library/creators/luna-fit/projects/tiny-reset-after-laptop-day
```

Project validation resolves provenance against the owning workspace: referenced reference assets must exist in the reference library, research pack IDs must resolve to `research/<kind>/<pack-id>.json` records, and a packaged project's output package must match the project, applied template, and plan records.

## Validate Any Record

Validate one mid-pipeline record against any schema in `schemas/`:

```bash
python3 -m influencer_os validate record output-package examples/output-package.example.json
```

## Memory And Learnings

Add one durable fact to a `MEMORY.md` file (deduplicated; refuses writes past the 2,500-byte cap):

```bash
python3 -m influencer_os memory-write context/MEMORY.md "One durable fact." --section "Active Threads"
```

Append a dated, deduplicated per-skill learning entry (the `wrap-up` skill's writer):

```bash
python3 -m influencer_os log-learning context/learnings.md influencer-os "One-line lesson."
```

## Initialize A Dry Run

```bash
python3 -m influencer_os init-run examples/creator-profile.example.json
```

This creates a local ignored run folder under:

```text
workspace-library/runs/
```

The initialized run contains:

```text
run.json
events.jsonl
records/creator-profile.json
```

## Test

```bash
python3 -m unittest discover -s tests
```
