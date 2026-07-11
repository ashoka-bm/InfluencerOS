# InfluencerOS

InfluencerOS currently creates researched content ideas and production plans for influencer workspaces, starting with universal short-form video and now including article and thread plans. Product and brand onboarding is an accepted ADR 0026 target, not a shipped runtime capability.

InfluencerOS is also being structured as a local-first Agentic OS adaptation. Root adapter files load the same durable project context for Codex, Claude, OpenClaw/Hermes-style agents, and compatible tools.

The v1 flow (ADR 0020):

```text
Choose Creator
  -> optionally understand real videos from frames and transcripts
  -> plan platform-scoped public research, then capture dated evidence and concise Research Findings
  -> maintain a scored Content Opportunity Queue from findings and evidence
  -> human-approve an Concept Approval for one queue idea
  -> create Projects from the locked promotion
  -> apply a format-compatible social template
  -> create a format-specific production plan
  -> create a base generation plan when needed
  -> register an Output Package from approved/imported artifacts
  -> record manual publication, analytics snapshots, performance summary, and creator lessons
```

InfluencerOS v1 research is platform-scoped across the ADR 0020 platform set. Production stays format-first: it supports universal short-form vertical video, carousel, single-image, story-sequence, article, and thread plans without platform adapters.

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

Creator setup can capture broader creator strategy inputs, including written surfaces such as Substack, LinkedIn, X, blogs, and newsletters. The current production pipeline is format-first and includes text production routes for article and thread projects.

## What V1 Includes

- schema-backed creator setup, research, planning, generation provenance,
  publication evidence, analytics, learning, and Improvement OS records
- producer skills from creator foundation through output packaging and learning
- format-specific production plans for video, carousel, single-image,
  story-sequence, article, and thread work
- exact-approval generation provider routing and standing-approved research
  acquisition routing
- local recall index and semantic lookup projection CLIs

The record inventory is disk-derived: every `schemas/*.schema.json` must have a
same-stem `examples/*.example.json`. `python3 -m influencer_os validate
examples` fails on missing or orphaned pairs, so this README does not duplicate
that inventory.

## What V1 Defers

- platform-specific motion graphics
- caption styling and post-production treatments
- publishing, scheduling, or uploads
- platform analytics API connectors and scheduled analytics feedback loops
- provider-backed generation without explicit human authorization (exact
  approval normally; one bounded creator-setup reference pass under ADR 0043)

## Validate Examples

```bash
python3 -m influencer_os validate examples
```

## Validate A Whole Creator Workspace (Release Gate)

Run every validator over one Creator Workspace in a single command — the
workspace manifest and readiness milestones, research state, content opportunity queue, content
board, and every project under `projects/`:

```bash
python3 -m influencer_os validate all workspace-library/creators/luna-fit
```

`validate all` is the alpha release gate: the scoped commands below
(`validate workspace`, `validate research`, `validate queue`,
`validate board`, `validate calendar`, `validate project`) each enforce their own layer, and only
the composed run proves the full provenance chain. Layers that legitimately
do not exist yet (no queue manifest before the first research run, no board
before `rebuild-board`) are reported as skipped, queue entries without a
manifest fail, and the summary line counts the warnings so advisory findings
cannot scroll away unseen.

## Initialize A Creator Workspace

```bash
python3 -m influencer_os init-creator examples/creator-workspace.example.json
```

This creates a local ignored creator workspace under:

```text
workspace-library/creators/
```

During the current build phase, creator workspaces initialized here are fixtures for testing setup, validation, generation gates, and workflow ergonomics. Do not treat their contents as permanent production data unless the user explicitly promotes a workspace out of test status.

Onboarding a **real** creator is different: follow
`docs/onboard-real-creator-runbook.md` — it covers the one-time fixture wipe,
the backup discipline, connector smoke checks, and the `validate all` release
gate.

After authoring `creator-profile.json` and `references/reference-library.json`, validate the workspace with:

```bash
python3 -m influencer_os validate workspace workspace-library/creators/luna-fit
```

Every creator uses one reusable personal-brand-board template, including
text-only and long-form creators. Author creator-specific exact tokens in
`references/brand/personal-brand-board.json` after Reference Library planning.
The board's profile avatar binds to a prompt-staged or available `brand` or
`character` Reference Asset; production spaces and signature props, when used,
bind to typed Reference Library asset IDs. Then build and validate the editable
HTML projection:

```bash
python3 -m influencer_os rebuild-brand-board workspace-library/creators/luna-fit
python3 -m influencer_os validate brand-board workspace-library/creators/luna-fit
```

Validation is status-keyed: a `draft` workspace stays permissive, while a workspace claiming `profile_ready`, `foundation_ready`, `strategy_ready`, `production_ready`, or `active` must pass the corresponding readiness checks. Deprecated `content_ready` and `generation_ready` fixtures validate only far enough to emit a migration warning. Failures report the full blocker list in one run.

After authoring or changing `content-schedule.json`, rebuild the interactive
human-review projection and verify that it still matches the canonical source:

```bash
python3 -m influencer_os rebuild-calendar workspace-library/creators/luna-fit
python3 -m influencer_os validate calendar workspace-library/creators/luna-fit
```

The generated file is `boards/content-calendar.html`. It is a rebuildable view,
not a second schedule record.

Creator Workspaces run copied baseline skills from `.claude/skills/`. Refresh those copied runtime skills after root skill changes with:

```bash
python3 -m influencer_os sync-creator-runtime workspace-library/creators/luna-fit
```

Refresh all repository-owned global Codex skills after changing files under
`skills/`, then verify that the runtime copies have not drifted:

```bash
python3 -m influencer_os sync-codex-skills
python3 -m influencer_os check-codex-skills
```

The repository remains authoritative. The sync backs up replaced skill folders
under `~/.codex/skills-backup/` and preserves `SKILL.local.md` overrides.

Legacy workspaces created before slot-first research provenance became required
must be migrated explicitly:

```bash
python3 -m influencer_os migrate-slot-research workspace-library/creators/luna-fit
```

Filled slots migrate only when one active promotion, its queue entry, and a
shared scheduled research run provide an unambiguous chain. Ambiguous legacy
state fails before any record is written and must be resolved manually.

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

After adding the plan records, validate the project with:

```bash
python3 -m influencer_os validate project workspace-library/creators/luna-fit/projects/tiny-reset-after-laptop-day
```

Project validation anchors on the locked Concept Approval: `source_refs.concept_approval_id` must resolve to `campaigns/<campaign-id>/approvals/<id>.json` in the owning workspace, the promotion must list the project and point to a real content opportunity entry, and any cached deeper refs must match the promotion snapshot. Referenced reference assets must exist in the reference library, video pack IDs must resolve to `research/video-understanding-packs/<pack-id>.json` records, the project content unit must map to exactly one matching target format, text projects validate against article/thread plan schemas without a generation plan, and a packaged project's output package must match the project, applied template, and plan records.

## Register An Output Package

Register an upload-ready package after the plan records and final/imported files exist:

```bash
python3 -m influencer_os register-output-package path/to/output-package.json --project workspace-library/creators/luna-fit/projects/tiny-reset-after-laptop-day --asset-root path/to/staged-assets
```

`--asset-root` should mirror the package's `upload_ready[].path` values, such as `output-package/upload-ready/final-video.mp4`. Omit it only when those files are already staged inside the project. The command copies upload-ready files, writes `output-package/output-package.json`, marks the project `packaged`, and rolls back those writes if `validate project` fails.

## Register A Published Post

After a human manually publishes the packaged content on a platform, record the publication:

```bash
python3 -m influencer_os register-published-post path/to/published-post-record.json --project workspace-library/creators/luna-fit/projects/tiny-reset-after-laptop-day
```

The record must match the registered Output Package: chain ids, `assets_used` upload-asset ids, and the caption/description path must all resolve to what the package declares. The command writes the record under `published/published-post-records/` and moves the project `packaged` → `published` on the first record whose `publication_status` attests a live post (`scheduled`/`failed` records register without the status change). It records a publication that already happened; it never publishes, uploads, or schedules.

## Ingest Analytics

Add performance snapshots for a published post — manual entry from a full JSON record, or bulk import from the neutral InfluencerOS CSV template ([analytics-snapshot-template.csv](docs/templates/analytics/analytics-snapshot-template.csv)):

```bash
python3 -m influencer_os add-analytics-snapshot path/to/analytics-snapshot.json --project workspace-library/creators/luna-fit/projects/tiny-reset-after-laptop-day
python3 -m influencer_os import-analytics-csv path/to/snapshots.csv --project workspace-library/creators/luna-fit/projects/tiny-reset-after-laptop-day
```

Every ingestion path writes through one shared seam: the snapshot must cite a live published post record on the same platform, missing platform metrics stay `null` (never guessed), `hours_since_publish` is derived from the timestamps when omitted, and raw exports referenced by the record must exist under the project's `analytics/raw/`. The CSV import is all-or-nothing. No platform APIs are called; API connectors remain a designed seam awaiting an explicit request.

## Author A Performance Summary

Once snapshots have matured (72h+ post-publish), the `create-performance-summary` skill authors `projects/<project-slug>/performance-summary.json` — the interpretive record mapping observed results to the five attribution stages (packaging, hook, body retention, payoff, CTA), anchored to the skill's Performance Benchmark Rubric. There is no write command; validation is the enforcement seam:

```bash
python3 -m influencer_os validate record performance-summary workspace-library/creators/luna-fit/projects/tiny-reset-after-laptop-day/performance-summary.json
python3 -m influencer_os validate project workspace-library/creators/luna-fit/projects/tiny-reset-after-laptop-day
```

Evidence refs must resolve to the project's registered package, published post records, and snapshots; each stage appears exactly once; a published project with mature snapshots and no summary draws an advisory warning.

## Validate Research State

Validate a creator's research records (runs, JSONL evidence and metric snapshots, findings frontmatter and char limit, intelligence files, board and system projections, and concept approvals with the promotion gate), then the content opportunity queue's manifest/entry consistency and evidence resolution:

```bash
python3 -m influencer_os validate research workspace-library/creators/luna-fit
python3 -m influencer_os validate queue workspace-library/creators/luna-fit
```

The promotion gate requires every promotion to point to a real content opportunity entry and to approve at least one production-supported format; unresolved evidence refs warn for human-approved promotions and fail for any future automated promotion path. Projects stay within the locked promotion's approved surface: target formats must be approved, and platform targets that map to a research platform must be approved. Since ADR 0027 added `youtube` to the research platform set, `youtube_shorts` maps to `youtube` and requires it in the promotion's approved platforms; only surfaces that map to no research platform remain exempt.

## Video Understanding Tool

When research uses real videos, the supported external acquisition tool is
`bradautomates/claude-video` `/watch` when installed. Use it to inspect public
URLs or user-provided local files, then store the distilled observations as a
Video Understanding Pack. Keep `/watch` working files in ignored local storage
such as `.tmp/watch/...`; do not commit downloaded videos, frames, audio clips,
or transcripts. Whisper/API transcription fallback, first-run dependency
installs, and video batches require explicit approval.

## Research Acquisition Connectors

An env-gated research-acquisition connector tier (ADR 0022) can pull evidence
that built-in `WebSearch`/`WebFetch` cannot reach — Reddit threads and X posts
with engagement metrics, JS-rendered public pages, public LinkedIn posts, and
public YouTube videos with view/like/comment counts. Each connector is
**available only when its provider key is set** in `.env` (`OPENAI_API_KEY`,
`XAI_API_KEY`, `FIRECRAWL_API_KEY`, `APIFY_API_KEY`, `YOUTUBE_API_KEY`); with no
key it reports `unavailable` and research falls back to the built-ins. List
availability without making any provider call:

```bash
python3 -m influencer_os list-connectors
```

Run a single fetch inside an explicit, user-initiated research run. Output maps
to canonical `ResearchEvidence`/`MetricSnapshot` records and is validated against
`schemas/research-fetch-result.schema.json` before it is emitted:

```bash
python3 -m influencer_os research-fetch reddit "low-light houseplants" --run-dir <research-run-dir> --days 30
python3 -m influencer_os research-fetch x "creatine timing" --run-dir <research-run-dir> --depth deep --out .tmp/x-fetch.json
python3 -m influencer_os research-fetch firecrawl https://example.com/post --run-dir <research-run-dir>
python3 -m influencer_os research-fetch linkedin https://www.linkedin.com/in/<profile> --run-dir <research-run-dir> --max-posts 5
python3 -m influencer_os research-fetch youtube-search "desk stretch routine" --run-dir <research-run-dir> --days 30 --max-results 10 --out .tmp/youtube-fetch.json
python3 -m influencer_os research-fetch youtube-channel "@deskwellness" --run-dir <research-run-dir> --days 30 --max-results 10 --out .tmp/youtube-channel.json
```

The YouTube connector uses public YouTube Data API video/channel metadata and
visible statistics only. It does not fetch transcripts, call YouTube Analytics,
publish, schedule, or use logged-in access (ADR 0027).

YouTube smoke check:

```bash
python3 -m influencer_os list-connectors
mkdir -p .tmp/youtube-smoke-run
python3 -m influencer_os research-fetch youtube-search "desk stretch routine" --run-dir .tmp/youtube-smoke-run --days 30 --max-results 3 --out .tmp/youtube-smoke.json
python3 -m influencer_os validate record research-fetch-result .tmp/youtube-smoke.json
```

Expected: `youtube_data_api` is available when `YOUTUBE_API_KEY` is set, and the
fetch result validates. The `.tmp/` output is transient candidate data; curate
only useful candidates into research records.

Key presence is standing approval for this research tier only — no per-run
prompt — bounded by a per-run call cap (`INFLUENCER_OS_CONNECTOR_MAX_CALLS`) and
a global kill switch (`INFLUENCER_OS_DISABLE_PAID_CONNECTORS=1`). Generation
provider calls (image/video/audio/render) keep the exact-approval gate except
for ADR 0043's one bounded pass over approved creator-setup references. There is
no scheduled/unattended path; scheduled automation stays
deferred (Temporal Scheduling, ADR 0025).

## Validate Any Record

Validate one mid-pipeline record against any schema in `schemas/`:

```bash
python3 -m influencer_os validate record output-package examples/output-package.example.json
```

## Rebuild The Recall Index

Rebuild one creator's rows in the shared local recall index (a rebuildable
SQLite projection per ADR 0010 at `workspace-library/index/influencer-os.sqlite`;
validation never depends on it):

```bash
python3 -m influencer_os rebuild-index workspace-library/creators/luna-fit
```

## Rebuild And Query The Semantic Lookup

Rebuild one creator's semantic lookup projection (the ADR 0011 FTS5 keyword
leg in the same database: heading-aware chunks over brand context, findings,
stable findings, creator learnings, and index-allowed performance-summary
narratives — never raw analytics; symlinked lookup sources fail closed), then
search it creator-scoped with creator-local FTS scoring; results cite
`source_path:line` and queries are never persisted:

```bash
python3 -m influencer_os rebuild-lookup workspace-library/creators/luna-fit
python3 -m influencer_os query-lookup workspace-library/creators/luna-fit hook retention
```

## Rebuild The Content Board

Rebuild the Kanban-readable Content Board projection from canonical records
(content opportunity entries become parent cards, projects become child cards, active
warnings become severity badges; `columns` and `manual_order` survive
rebuilds), then check an existing board against canonical records:

```bash
python3 -m influencer_os rebuild-board workspace-library/creators/luna-fit
python3 -m influencer_os validate board workspace-library/creators/luna-fit
```

## Prune Research Retention

Apply the research retention rules (dry-run by default; deletes only with
`--apply`). Prune removes unreferenced evidence older than the retention
window plus its metric snapshots, never touches records a queue entry,
promotion, or project references, and records removals on the run manifest
(`pruned_evidence_ids`) so the run's original `outputs` stay intact:

```bash
python3 -m influencer_os prune workspace-library/creators/luna-fit
python3 -m influencer_os prune workspace-library/creators/luna-fit --apply
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

Append an evidence-linked creator lesson to a Creator Workspace `memory/learnings.md` (the `distill-creator-learning` skill's writer; every evidence id must resolve to a workspace record, and `validate workspace` re-checks lessons at rest):

```bash
python3 -m influencer_os log-learning <creator-workspace>/memory/learnings.md "hooks" \
  "One-line creator lesson." \
  --evidence performance_summary_<id> --strength single_post_signal
```

## Test

```bash
python3 -m unittest discover -s tests
```
