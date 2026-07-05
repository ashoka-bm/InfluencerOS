# Creator Workspace Structure

Creator Workspaces are ignored local folders for real AI creators. The public repo stores the reusable operating system; `workspace-library/creators/<creator-slug>/` stores private creator state, references, projects, analytics evidence, memory, and progress.

## Current Build/Test Mode

The repo is still in a system-building and workflow-testing phase. Creator Workspaces created during this phase are test fixtures unless the user explicitly promotes one as production creator state.

Fixture workspaces may contain generated personas, generated images, reference prompts, fake research, draft projects, and memory used only to test the operating system. They are expected to be wiped before real creator onboarding starts. Do not preserve, migrate, or optimize around fixture creator data unless the user explicitly asks.

Durable implementation work lives in the public repo: docs, schemas, tests, CLI behavior, skills, templates, examples, and validation rules. `workspace-library/` remains private local state and must not become the source of product truth.

## Principles

- Keep the public repo reusable: schemas, examples, docs, tests, skills, and shared prompts live at the repository root.
- Keep real creator state private once production onboarding begins: creator identities, media references, generated work, platform records, analytics, memory, and progress live under `workspace-library/`, which is gitignored.
- Treat current `workspace-library/` creator contents as disposable fixtures during build/test mode.
- Keep always-loaded context tiny: `context/SOUL.md`, `context/USER.md`, and `context/MEMORY.md` mirror Agentic OS and should be loaded first in routine creator work.
- Keep richer creator detail lazy-loaded: `brand_context/` holds identity, psychology, brand strategy, and voice samples.
- Keep the Creator Profile typed but not bloated: `creator-profile.json` is the operational summary, while `brand_context/` holds richer detail.
- Preserve provenance: source intakes and raw reference files stay available, but downstream records should point to them by stable IDs or paths instead of duplicating their contents.
- Keep project work navigable: idea promotions, evidence briefs, plans, output packages, published records, and analytics live together under `projects/<project-id>/`.
- Separate evidence from lessons: raw analytics stay with the project they measure; durable creator lessons live in `memory/`.

## Repository Root

```text
InfluencerOS/
  AGENTS.md
  CONTEXT.md
  ARCHITECTURE.md
  README.md
  docs/
  schemas/
  examples/
  skills/
  influencer_os/
  tests/
  workspace-library/        # ignored local state
```

## Creator Workspace

```text
workspace-library/creators/<creator-slug>/
  AGENTS.md
  creator-workspace.json
  creator-profile.json
  context/
    SOUL.md
    USER.md
    MEMORY.md
  brand_context/
    identity.md
    soul.md
    personal-brand.md
    voice-samples.md
  sources/
    intakes/
    imports/
    notes/
  references/
    reference-library.json
    character/
    locations/
    outfits/
    objects/
    video-style/
    voice/
    brand/
  content-schedule.json
  research/
    findings.md
    runs/
      <research-run-id>/
        research-run.json
        run-summary.md
        evidence.jsonl
        metric-snapshots.jsonl
        video-understanding-packs/
    intelligence/
      sources.json
      hashtags.json
      search-terms.json
      reference-creators.json
      watchlist.json
    stable-findings/
      <stable-finding-id>.md
    idea-queue/
      queue.json
      entries/
        <idea-queue-entry-id>.json
    idea-promotions/
      <idea-promotion-id>.json
  boards/
    content-board.json
  system/
    project-warnings.jsonl
    creator-events.jsonl
  projects/
    <project-id>/
      project.json
      evidence-brief.md
      plan/
        applied-template.json
        production-plan.json
        generation-plan.json
      output-package/
        output-package.json
        assets/
        upload-ready/
        source-refs/
        platform-adaptations/
      published/
        published-post-records/
      analytics/
        snapshots/
        raw/
      performance-summary.md
  memory/
    MEMORY.md
    learnings.md
    daily/
  .claude/
    skills/
      <skill-name>/
        SKILL.md
        SKILL.local.md
  progress/
```

The structure above is the target production layout. In build/test mode, a workspace that follows this layout is still a fixture unless the user explicitly accepts it as durable creator state.

### Transitional Layout (Phase 0C)

The `research/` tree and the project `evidence-brief.md` above are the ADR 0020
target; they land with the Phase 1 research module slice. Until then,
`init-creator` scaffolds the current transitional layout, and provenance
validation resolves against it:

```text
research/
  social-research-packs/
    <social-research-pack-id>.json       # research_* ids (compatibility records)
  video-understanding-packs/
    <video-understanding-pack-id>.json   # video_research_* ids
  sources/
  runs/
    <research-run-id>/
      research-run.json
      evidence.jsonl                     # one validated ResearchEvidence per line
      metric-snapshots.jsonl             # one validated MetricSnapshot per line
  intelligence/                          # sources/hashtags/search-terms/reference-creators/watchlist
  stable-findings/
    <stable-finding-id>.md               # validated YAML-subset frontmatter
  findings.md                            # rolling summary, validated frontmatter + char limit
  idea-queue/
    queue.json
    entries/
      <idea-queue-entry-id>.json
  idea-promotions/
    <idea-promotion-id>.json             # permanent locked approval snapshots
boards/
  content-board.json                     # rebuildable projection, not source of truth
system/
  project-warnings.jsonl
  creator-events.jsonl
projects/
  <project-id>/
    project.json
    evidence-brief.md
```

A project's `source_refs.idea_promotion_id` must resolve to
`research/idea-promotions/<id>.json` in the owning Creator Workspace; deeper
provenance (queue entry, findings, evidence, metric snapshots, video packs)
resolves transitively through that locked promotion, and any cached copies on
the project must match it. A video pack id in project or output-package
`source_refs` must resolve to `<directory>/<pack-id>.json`, and every
`reference_asset_id` must exist in `references/reference-library.json`;
`validate project` fails on a dangling reference. `validate research` and
`validate queue` cover the research records and pin every record's
`creator_profile_id`/`creator_slug` to the owning `creator-workspace.json`
(the research module is creator-scoped), and the promotion gate warns on
unresolved evidence (evidence ids, metric snapshot ids, and video pack ids
alike) for human-approved promotions while failing any future automated
promotion path and rejecting a promotion whose queue entry belongs to a
different creator.

Shared local indexes may live outside individual creator folders:

```text
workspace-library/index/
  influencer-os.sqlite
  semantic/
```

The SQL database is an index and query layer over workspace files. It is not the canonical home for creator identity, output packages, published records, analytics, or memory.

The semantic index is a low-context retrieval projection over selected narrative and summary files. It should index distilled learnings and performance summaries, not raw analytics by default.

## Propagation And Gated Zones (ADR 0018)

- `init-creator` scaffolds the workspace, copies baseline skills into `.claude/skills/`, and writes thin `AGENTS.md`/`CLAUDE.md` wrappers (the workspace contract lives in its `AGENTS.md`; `CLAUDE.md` imports it).
- `sync-creator-runtime <workspace>` refreshes one workspace's baseline skill copies; `update-creators` refreshes every workspace under the root. Both preserve `SKILL.local.md` files, creator-only skills, and all creator state, and back up each replaced skill folder to `.claude/skills-backup/<skill-name>/` (latest backup kept) so a refresh can never silently destroy creator edits.
- Gated zones — scripts, settings, hooks, cron — are deferred and inert: no such content is propagated into a Creator Workspace until each subsystem is explicitly un-deferred.

## Creator Memory And Recall (Tier 0)

Tier 0 is the always-loaded layer plus file-first recall. It needs no SQL or semantic index.

- `context/MEMORY.md` is the curated always-loaded creator memory. Cap: 2,500 bytes, enforced by the pre-write check in `python3 -m influencer_os memory-write`; consolidate before the cap is breached. Sections: Active Threads, Decisions, Blockers.
- `memory/learnings.md` stores distilled creator lessons via `python3 -m influencer_os log-learning`. Every distilled lesson must link back to its evidence (project, published post record, or analytics snapshot IDs); the evidence itself stays in the owning project.
- `memory/daily/` holds dated session notes (`YYYY-MM-DD.md`). Lazy-loaded; finalized by the `wrap-up` skill when a session worked in this workspace.
- Loaded by default in creator work: `context/SOUL.md`, `context/USER.md`, `context/MEMORY.md`. Everything else is lazy-loaded per `docs/os-construction/context-matrix.md`.
- Indexed later (Phase 2): `memory/learnings.md` and performance summaries feed the SQL and semantic indexes. Raw analytics are never indexed into default semantic memory.
- Root OS memory (repo `context/MEMORY.md`, same cap) and creator memory are separate scopes. Facts about one creator never go to root memory, and OS facts never go to a Creator Workspace.

## File Responsibilities

`AGENTS.md` is optional local creator operating context. It should not redefine the shared OS; it should tell agents to always load `context/SOUL.md`, `context/USER.md`, and `context/MEMORY.md` first, then lazy-load richer files only when needed.

`context/SOUL.md` is the tiny always-loaded creator operating identity. It defines how agents should behave as the creator, the default stance, voice capsule, visual capsule, and where to load more detail. Target: under 3 KB.

`context/USER.md` is the tiny always-loaded creator/user profile. It defines display name, niche, primary audience, surfaces, mediums, status, working preferences, and key file pointers. Target: under 1.5 KB.

`context/MEMORY.md` is the tiny always-loaded active memory. It stores current decisions, blockers, recent notes, and active setup/project context only. Durable lessons belong in `memory/learnings.md`. Target: under 2.5 KB.

`creator-workspace.json` is the workspace manifest. It should record the creator slug, workspace version, source intake provenance, key file paths, and schema versions.

`creator-profile.json` is the operational summary for automation. It should include stable IDs, audience, niche, positioning, persona summary, voice summary, visual identity summary, boundaries, goals, and pointers to richer files and references.

`brand_context/identity.md` is the long-form identity record: biography, lore, relationship to audience, recurring facts, continuity rules, and voice examples.

`brand_context/soul.md` is the personality and belief record: psychology, values, belief matrix, triggers, soothers, cadence, emotional logic, and behavior under stress.

`brand_context/personal-brand.md` is the brand strategy record: positioning, content pillars, platform posture, monetization, disclosure rules, commercial boundaries, and growth goals.

`brand_context/voice-samples.md` stores 5-10 gold-standard creator voice examples with source, content mode, reason, and confidence. It is separate so agents can skip concrete examples unless style fidelity matters.

`sources/` stores original creator inputs such as breakdowns, interviews, handoffs, pasted briefs, imports, and raw notes.

`references/` stores reusable visual and audio continuity assets. `reference-library.json` gives each asset a stable ID, status, role, file path, source, creation date, and allowed usage. Planned or prompted assets may be tracked before the final media file exists so setup can explain generation blockers.

`content-schedule.json` is the Creator Content Schedule: cadence expectations, content goals, calendar slots, and drift checks. It is separate from `creator-profile.json` because schedule state changes more often than creator identity. Research reads it as an input; it is not a research-module record.

`research/` stores Research Findings, dated Research Runs, Research Evidence, Metric Snapshots, research intelligence, Idea Queue entries, and Idea Promotions. Other modules read only the module's public records (`findings.md`, `idea-queue/`, `idea-promotions/`); run evidence and intelligence files are research-internal and resolve by ID through the local recall index.

`boards/content-board.json` is the rebuildable Content Board projection for Kanban views. It is derived from canonical queue, promotion, and project records and is never the source of truth. Card IDs are derived deterministically from source record IDs so rebuilds preserve manual order.

`system/` holds creator-scoped operational projections: `project-warnings.jsonl` and `creator-events.jsonl`. Like the board, they are Kanban-readable projections and event streams, not canonical planning records.

`projects/` stores content work that has moved past Idea Promotion. A project is one approved content unit moving through planning, packaging, publication, analytics, and learning. It may be a video, carousel, single image post, story sequence, article, thread, or multi-platform package.

`projects/<project-id>/project.json` is the project manifest. It should record project ID, creator ID, Idea Promotion refs, Idea Queue refs, research evidence refs, target format, status, key dates, and pointers to project records.

`projects/<project-id>/evidence-brief.md` stores the compact evidence brief carried forward from Idea Promotion. The full source material remains resolvable through research evidence refs and the local recall index.

`projects/<project-id>/plan/` stores Applied Social Templates, format-specific production plans, and provider-neutral generation plans.

`projects/<project-id>/output-package/` stores one upload-ready Output Package. `output-package.json` contains the universal core, platform adaptations, source refs, and required Creative Performance Map. `assets/` holds local materials. `upload-ready/` holds the exact files and text a person needs to upload. `source-refs/` may hold copies or pointers needed to audit how the package was created. `python3 -m influencer_os register-output-package` is the write gate for this folder: it copies upload-ready files, writes the package record, marks the Project `packaged`, validates, and rolls back its writes on failure.

`projects/<project-id>/published/` stores Published Post Records that link the Output Package to real platform publications. `python3 -m influencer_os register-published-post` is the write gate for `published/published-post-records/`: it validates the record against the registered Output Package (chain ids, upload-asset ids, caption path), writes it, moves the Project `packaged` → `published` on the first record attesting a live post, and rolls back on failure. It records a publication a human already performed; it never publishes.

`projects/<project-id>/analytics/` stores API, manual, CSV, or derived Analytics Snapshots for the project's Published Post Records. `raw/` may preserve safe raw exports or API payloads.

`projects/<project-id>/performance-summary.md` stores the short postmortem that links back to raw analytics, Published Post Records, and the Output Package.

`memory/` stores durable creator memory. `learnings.md` contains distilled creator lessons. `MEMORY.md` is a curated working scratchpad. `daily/` can hold dated local notes when useful.

`.claude/skills/<skill-name>/SKILL.md` is the copied runtime skill for creator-root execution. It is synced from repo `skills/<skill-name>/SKILL.md`.

`.claude/skills/<skill-name>/SKILL.local.md` stores creator-specific skill overrides. It may add local preferences, known creator constraints, and repeated feedback for that creator. It must not replace the copied baseline skill or introduce provider, publishing, scheduling, hooks, cron, or architecture behavior that the shared OS has not approved. Promote a local rule to the root baseline skill only after repeated feedback shows it applies system-wide.

`progress/` stores local build notes, status files, checklists, and operator-facing progress logs. It is private workspace state, not a public product contract.

`progress/setup-checklist.md` is scaffolded during creator initialization. It tracks foundation acceptance and medium-based blockers so agents do not move into research, planning, or generation before Creator Setup is complete for the intended content strategy.

## Public vs Private

Public repo:

- schemas,
- example records with fictional/sample creators,
- reusable prompts,
- skill files,
- CLI code,
- tests,
- architecture docs and ADRs.

Private Creator Workspace:

- real creator identity files,
- source intakes,
- visual/audio references,
- generated or imported media,
- projects and output packages,
- platform publication records,
- analytics,
- memory,
- progress notes,
- `.env` or tool-managed auth when a creator needs separate credentials.
