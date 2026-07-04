# Agentic OS Copy And Adaptation Plan

Last updated: 2026-07-03

This audit compares InfluencerOS with the purchased Agentic OS reference at `/Users/ashokaji/code/External repos/Agentic Academy/agentic-os`.

The Agentic Academy repository is the architecture source of truth for Agentic OS. Other local tooling or shared-rule repositories are not the Agentic OS reference for this project.

## Reference Integrity Rerun

Rerun date: 2026-07-01

Reference verified:

```text
/Users/ashokaji/code/External repos/Agentic Academy/agentic-os
```

Files and subsystems inspected in this rerun:

- `AGENTS.md`
- `README.md`
- `docs/context-matrix.md`
- `docs/skill-registry.md`
- `docs/multi-client-guide.md`
- `docs/projects-guide.md`
- `docs/memory-retrieval.md`
- `docs/building-skills.md`
- `command-centre/README.md`
- `command-centre/package.json`
- `.claude/settings.json`
- `.codex/hooks.json`
- `scripts/add-client.sh`
- `scripts/update-clients.sh`
- `cron/jobs/*.md`
- `.claude/skills/*/SKILL.md`
- `.claude/agents/*.md` (added 2026-07-03, workstream 15)
- `.claude/commands/*.md` (added 2026-07-03, workstream 15)

Audit result:

- The previous plan was not wholly invalid: it had already used the purchased Agentic OS for memory, clients, skills, cron, Command Centre, and visual maps.
- The previous source-of-truth framing was wrong and is now corrected: the Agentic Academy repo is the only Agentic OS architecture reference.
- The biggest parity gaps were runtime layout and propagation. These are now resolved: ADR 0017 finalizes the repo-central skill layout (no category prefixes) and adds machine-actionable skill conventions, and ADR 0018 approves the full propagation mechanism as CLI subcommands with content zones gated on their subsystems being un-deferred.

## Scope

This file is a decision aid. It does not approve implementation by itself. New architecture changes still need the divergence test in `docs/os-construction/divergence-test.md` and an ADR or alignment-doc update when they depart from the purchased Agentic OS reference.

Copy policy (user-approved execution decision, 2026-07-02): purchased Agentic OS files are reference-only. Nothing is copied verbatim into this repo; every adopted pattern is re-authored in InfluencerOS vocabulary. "copy exactly" rows adopt the convention, never the file contents.

Reference files inspected:

- InfluencerOS: `AGENTS.md`, `CONTEXT.md`, `README.md`, `ARCHITECTURE.md`, `docs/os-construction/*.md`, `docs/pipeline-contract.md`, `docs/provider-boundary.md`, `skills/influencer-os/SKILL.md`, `schemas/`.
- Purchased Agentic OS: `AGENTS.md`, `CLAUDE.md`, `README.md`, `context/`, `brand_context/`, `docs/context-matrix.md`, `docs/memory-retrieval.md`, `docs/multi-client-guide.md`, `docs/projects-guide.md`, `docs/building-skills.md`, `docs/skill-registry.md`, `command-centre/README.md`, `.claude/skills/`, `.claude/settings.json`, `.codex/hooks.json`, `cron/jobs/`, and `scripts/`.

## Decision Matrix

| Component | Agentic OS reference behavior | Current or target InfluencerOS behavior | Classification | Rationale | Recommended next action | Decision status |
| --- | --- | --- | --- | --- | --- | --- |
| Root context adapters | Purchased Agentic OS uses `AGENTS.md` as canonical, `CLAUDE.md` as wrapper, and `context/SOUL.md` / `context/USER.md` for agent identity and user profile. | ADR 0019: `AGENTS.md` is canonical; `CLAUDE.md` and root `SOUL.md` are thin wrappers that import it; the read order is defined once in `AGENTS.md`; `context/SOUL.md` is the sole identity. | adapt for InfluencerOS | The adapter pattern fits InfluencerOS. Root `SOUL.md` is a cross-agent (Hermes/OpenClaw) importer, not a second identity; a drift check enforces that adapters import `AGENTS.md` and never restate a divergent read order. | Restructure adapters per ADR 0019 and add the read-order drift check. | accepted in ADR 0019 |
| Static context files | Purchased Agentic OS separates `context/`, `brand_context/`, docs, skills, projects, command centre, cron, and scripts. | Repo docs hold static product truth: `CONTEXT.md`, `ARCHITECTURE.md`, `docs/os-construction/`, `docs/pipeline-contract.md`, schemas, examples, and tests. Root `context/` and `brand_context/` hold first-party InfluencerOS persona context. Creator state stays outside tracked source. | adapt for InfluencerOS | InfluencerOS needs schemas and pipeline contracts as first-class static context. It also needs the repo itself to act as an OS persona/client when marketing the system. | Keep static product context in repo docs and schemas. Keep root persona files product-owned, not copied verbatim from the purchased Agentic OS. | accepted |
| Brand/business context | Purchased Agentic OS keeps business voice, positioning, ICP, samples, and assets in root or client `brand_context/`, loaded by a context matrix. | InfluencerOS uses root `brand_context/` for the first-party OS persona and creator-scoped `brand_context/identity.md`, `soul.md`, `personal-brand.md`, and `voice-samples.md` inside ignored Creator Workspaces. | adapt for InfluencerOS | The repo can market itself as a first-party persona, while each creator still needs private brand continuity. Root brand context is public OS context; creator brand context remains private. | Keep both scopes in the context matrix and make workflow load rules explicit so OS-level and creator-level brand context cannot blend. | accepted |
| Memory levels and recall | Purchased Agentic OS uses Tier 0 `MEMORY.md` plus today's log, Tier 1 semantic recall, `.aos.md` stop-hook captures, daily logs, learnings, raw transcripts, and deferred deeper transcript search. | InfluencerOS has contracted creator memory, raw analytics evidence, distilled lessons, SQL index, and semantic lookup projection. Operational recall is not built. | adapt for InfluencerOS | Copying the full memory system would import broad agent-session memory, but InfluencerOS needs creator-scoped learning tied to output records and analytics. | Implement Tier 0 first inside Creator Workspaces: `context/MEMORY.md`, distilled learnings, and progress notes. Defer hooks and transcripts until the Planning OS is stable. | proposed |
| Semantic search, memory palace, exact recall | Purchased Agentic OS has PGLite/Postgres + pgvector semantic recall using BGE-M3, hybrid keyword/vector search, scope isolation, and audit rows. It defers expanded chunks and raw transcript deep-search. No explicit "memory palace" or "exact recall" subsystem was found. | InfluencerOS uses SQL index for exact structured lookup, semantic lookup projection for meaning-based recall, and Creator Memory for distilled creator lessons. It does not use "memory palace" in v1. | adapt for InfluencerOS | The SQL + semantic projection split matches InfluencerOS better than importing a general session-memory database wholesale. Avoiding "memory palace" keeps recall language tied to concrete mechanisms. | Keep terminology in ADR 0014 and avoid adding memory-palace scope unless a future ADR approves it. | accepted |
| Skills and progressive disclosure | Purchased Agentic OS registers `.claude/skills/{category}-{skill}/`, `SKILL.local.md`, context matrix rows, learnings sections, optional dependency rules, setup scripts, and a `_catalog/` install state. Skill folder names use category prefixes and frontmatter names must match folder names. | InfluencerOS keeps baseline source skills under repo `skills/` and copies them into each Creator Workspace under `.claude/skills/` for client-root execution. Creator overrides live beside copied runtime skills as `SKILL.local.md`. | adapt for InfluencerOS | This copies the Agentic OS client-root runtime model while preserving the repo's current source layout. ADR 0017 finalizes the repo-central layout and declines category prefixes; skills add per-skill `references/`, machine-actionable `dependencies` frontmatter, and `## Rules`/`## Self-Update`. | Keep `sync-creator-runtime` conservative; adopt the ADR 0017 skill conventions. | accepted in ADR 0017 |
| Skill systems and orchestrators | Purchased Agentic OS routes tasks through skills, handles built-in operations by scripts, and has optional GSD for phased execution. | `skills/influencer-os/SKILL.md` is the creation conductor. Setup has subskills. Pipeline records provide deterministic handoffs. | adapt for InfluencerOS | InfluencerOS needs conductors tied to schema-backed records, not generic business-output folders. | Keep one conductor per major workflow: creator setup, content creation, learning, generation. Each conductor must name inputs, outputs, validation, and gates. | accepted |
| Project/client separation | Purchased Agentic OS uses root shared methodology and `clients/<slug>/` for client-specific brand context, memory, projects, cron jobs, secrets, client-only skills, and local overrides. `add-client.sh` copies skills, scripts, settings, hooks, cron templates, learnings, and `.env`; `update-clients.sh` syncs shared skills/scripts/settings/hooks/templates while preserving client data, client-only skills, installed skill state, and `SKILL.local.md`. | InfluencerOS uses ignored `workspace-library/creators/<creator-slug>/` folders with creator profile, context, brand context, references, research, projects, memory, progress, and copied `.claude/skills/` runtime skill folders. It syncs baseline skills while preserving local overrides and creator-only skills. | adapt for InfluencerOS | Creators replace clients and creator state must stay private. ADR 0018 approves the full propagation mechanism as CLI subcommands (`init-creator`, `sync-creator-runtime`, `update-creators`); skills and workspace structure propagate now, and scripts/settings/hooks/cron are carried as inert zones until each is un-deferred. | Build the propagation subcommands per ADR 0018; keep hooks/cron content deferred. | accepted in ADR 0018 |
| Output consolidation | Purchased Agentic OS saves single-task outputs under category folders and planned project outputs under `projects/briefs/<project>/`. It shows absolute paths and can copy binaries to Downloads. | InfluencerOS stores creator outputs under `workspace-library/creators/<creator-slug>/projects/<project-id>/` and uses Output Package records with provenance. | adapt for InfluencerOS | The "outputs live with the project" rule applies, but InfluencerOS needs schema-backed Output Packages and provenance, not date-named markdown deliverables. | Define the exact project folder layout for idea, plan, generation, artifact, package, publication, analytics, and memory records. | proposed |
| Scheduled workflows | Purchased Agentic OS has `cron/jobs/`, templates, logs, status files, client-aware proxy scripts, a managed cron runtime, leader lock, and recurring memory jobs. | InfluencerOS defers Automation OS until Planning, Learning, and Generation are stable. Scheduled research, project creation, and analytics ingestion are Phase 4. | do not copy now | Cron would add operational complexity before the core content pipeline is stable. | Keep automation deferred. Later, copy the markdown job definition pattern, status/log separation, client/creator scoping, and leader-lock requirement before copying runtime automation. | accepted |
| Access from anywhere, hosted access, and channels | Purchased Agentic OS supports local Command Centre and optional hosted memory API/Postgres. The README frames hosted team memory as optional. | InfluencerOS explicitly defers hosted or anywhere-access execution. Local-first workflows are canonical for v1. | do not copy | The user direction and PRD defer remote execution. Hosted access can bypass approval and privacy boundaries if added too early. | Record this as deferred until after Phase 4. Revisit only with explicit user approval and a provider/security ADR. | accepted |
| Command Centre and dashboards | Purchased Agentic OS includes a Next.js Command Centre for tasks, clients, cron, memory, docs, skills, and settings. | InfluencerOS will defer Command Centre until the file-first OS, Creator Workspaces, skills, memory, and workflow contracts are stable. | defer | Command Centre is desirable later, but building it now would expand scope into UI, runtime, task queues, and security before the core OS is proven. | Do not copy Command Centre in Phase 0 or Planning OS. Revisit after Automation OS design. | accepted |
| Tests and validation | Purchased Agentic OS has command-centre tests, memory tests, cron tests, update/sync tests, launcher tests, and setup tests. | InfluencerOS has unit tests, schema validation, CLI validation, example records, and progress docs that record verification. | adapt for InfluencerOS | InfluencerOS validation should stay schema- and workflow-centered. Adapter drift checks can be added, but command-centre/memory/cron tests should wait for those subsystems. The missing near-term test category is parity drift: source path, adapter coverage, skill registry coverage, and context matrix coverage. | Add lightweight markdown/reference checks for construction docs. Keep current unit and schema tests as the main verification floor. | proposed |
| Docs, roadmap, and progress conventions | Purchased Agentic OS keeps project, context, skill, memory, client, and update docs. | InfluencerOS already has `docs/os-construction/roadmap.md`, `progress.md`, `repository-map.md`, alignment, divergence test, and visual map standards. | copy exactly | The convention of durable roadmap/progress/repo-map docs is a direct fit. InfluencerOS already adapts names under `docs/os-construction/`. | Keep progress current after architecture or implementation passes. Add `NEXT-ACTIONS.md` only if the work queue outgrows `progress.md`. | accepted |
| Provider and external service boundaries | Purchased Agentic OS registers services, API keys, fallbacks, and `.env.example`. | InfluencerOS has `docs/provider-boundary.md`: planning is allowed, provider-backed image/video/audio/render/upload/paid calls require exact approval. | adapt for InfluencerOS | InfluencerOS needs a stricter boundary because generated media can be paid, private, or irreversible. | Add a provider registry only when real adapters are introduced. Until then, keep exact-call approval as the rule. | accepted |
| Self-learning and skill feedback loops | Purchased Agentic OS asks for feedback after major deliverables and logs it to `context/learnings.md` per skill. It also has scheduled learning-health checks and supports local skill overrides. | InfluencerOS splits first-party OS process learnings, creator-specific learnings, and scope-specific skill overrides. Core skills are promoted only after repeated feedback proves the rule is system-wide. | adapt for InfluencerOS | Creator performance learning and agent skill improvement must stay separate, but InfluencerOS itself also needs persona-level memory and process learning. | ADR 0016 adds the `wrap-up` and `memory-write` system skills that actually write `context/learnings.md`, `process-learnings.md`, `SKILL.local.md`, and `context/MEMORY.md`; Creator Memory stays inside Creator Workspaces (Phase 2). | accepted in ADR 0016 |
| Visual architecture maps | Purchased Agentic OS includes a visual architecture map and visual workflow references. | InfluencerOS defines a visual architecture map standard and stores construction map records under `docs/os-construction/maps/`. | adapt for InfluencerOS | The map pattern is useful, but InfluencerOS already chose its own Excalidraw map standard and storage location. | Create the first overall system map, then creator workspace, content pipeline, and skill orchestrator maps. | proposed |
| Root standards and operating rules | Purchased Agentic OS has root operating rules, setup/update scripts, and reference docs for using the OS. | InfluencerOS inherits global coding rules and adds product rules in `AGENTS.md`. | adapt for InfluencerOS | Product rules should stay repo-specific while the Agentic OS architecture remains the default reference. | Keep root `AGENTS.md` aligned with Agentic OS architecture and avoid restating standards unless InfluencerOS needs a stronger rule. | accepted |
| Inventories | Purchased Agentic OS keeps registries inside docs and app state. | InfluencerOS currently maps schemas, docs, skills, and runtime modules, but does not have machine-readable inventories. | adapt for InfluencerOS | Full environment inventories are outside product scope, but a schema/skill/workflow registry may reduce drift. | Add inventories only when drift appears. Start with docs tables before YAML unless automation needs machine-readable data. | proposed |
| Hooks and automatic capture | Purchased Agentic OS uses Claude/Codex hooks for memory capture, session sync, branch guards, workflow guards, and notifications. | InfluencerOS has no hooks. It relies on manual docs, CLI validation, and explicit approval gates. | do not copy | Hooks would add hidden behavior and risk provider or privacy boundary violations before the product workflows are stable. | Do not add hooks in v1. Reconsider only for validation or memory capture after explicit approval. | accepted |
| Installation and update machinery | Purchased Agentic OS has installer, updater, client sync, memory setup, cron setup, command-centre launchers, and backup/update safety behavior. | InfluencerOS is a product repo, not an installable Agentic OS distribution. It now has creator runtime skill sync, but no installer/updater distribution machinery. | adapt for InfluencerOS | Installer/updater machinery solves a different problem. The needed subset is creator skill sync for local creator-root execution. | Keep `sync-creator-runtime`; do not copy install/update scripts in Phase 0. | accepted |
| `.claude/agents/` typed subagents | Purchased Agentic OS ships four typed subagents (`ssc-designer`, `ssc-image-generator`, `ssc-template-builder`, `l2s-content-packager`) that orchestrators spawn via `Agent(...)` for heavy sub-tasks; each declares name/description/tools frontmatter and returns a structured result. | InfluencerOS has no subagents; the content conductor routes to producer skills, with remaining unbuilt producers still behind `[PLANNED]` halt markers. | defer | The pattern remains a candidate for future heavy producer skills, but adopting it is a divergence-test event that needs its own ADR (user-approved execution decision, 2026-07-02). | Revisit when a producer actually needs typed subagent delegation; write the adoption ADR only if that build reaches for the pattern. `architecture-map.md` records the same status. | accepted (defer) |
| `.claude/commands/` slash commands | Purchased Agentic OS ships `/start-here` (first-run onboarding guard and entry point) and `/archive-gsd` (GSD project archival). | InfluencerOS has no slash commands; onboarding is the `create-influencer` conductor triggered by description, and GSD-style phased-execution tooling is not part of this product. | do not copy now | Commands are runtime-specific launchers, not architecture. InfluencerOS skills trigger by description per the skill registry. | Keep description-based skill triggering. Reconsider a `/start-here`-style entry command only if first-run onboarding friction is observed; `archive-gsd` has no InfluencerOS analog. | accepted |

## Resolved Immediate Decisions

1. The next implementation pass is Phase 0C parity hardening, not product workflow implementation.
2. The first visual architecture pass includes the Agentic OS baseline, the InfluencerOS target architecture, and the comparison draft. The comparison can get its own Excalidraw scene after the markdown comparison is reviewed.

## Decisions From Reference Rerun

1. Skill runtime layout: finalized in ADR 0017 — repo `skills/` is the baseline source; Creator Workspaces get copied runtime skills under `.claude/skills/`; skills add per-skill `references/` and machine-actionable `dependencies` frontmatter.
2. Creator Workspace propagation: resolved in ADR 0018 — the full propagation mechanism is approved as CLI subcommands; skills and structure propagate now; scripts, settings, hooks, and cron content stay gated until un-deferred.
3. Sync/update tooling: `sync-creator-runtime` refreshes baseline copied skills while preserving `SKILL.local.md` and creator-only skills; `update-creators` adds backup-protected batch refresh (ADR 0018).
4. Skill naming: decided in ADR 0017 — no category prefixes; plain kebab-case names grouped by the skill-registry section tables.
5. Workstream 15 (2026-07-03): `.claude/agents/` and `.claude/commands/` inspected and classified above; the reference-only copy policy is recorded in the Scope section; the subagent pattern stays deferred with its ADR written only on adoption.

## Recommended Implementation Order

1. Skill runtime layout and Creator Workspace propagation are resolved (ADR 0017, ADR 0018); implement the skill conventions and propagation subcommands test-first.
2. Finish Phase 0 by using this audit to update `agentic-os-alignment.md` with accepted decisions that are not already recorded.
3. Harden the Creator Workspace context matrix for skills and workflows.
4. Implement Tier 0 creator recall: tiny creator context, distilled learnings, progress notes, and documented load rules.
5. Tighten output consolidation: define the project folder layout and validation commands for every record from selected idea through Output Package.
6. Build or update visual architecture maps: overall system, creator workspace boundary, content pipeline, and skill orchestrator.
7. Design the SQL index and semantic lookup projection after the file layout and Tier 0 recall are stable.
8. Defer cron, hooks, hosted memory, Command Centre, and anywhere access until Planning OS and Learning OS are operational.

## Highest-Risk Divergences

- Memory scope: the purchased Agentic OS assumes broad session memory and optional hosted team memory. InfluencerOS must keep memory creator-scoped and provenance-linked, or creator identities and performance lessons can blend.
- Automation timing: cron and hooks are powerful but too early. They can run stale research, write private state, or cross provider boundaries without the deterministic gates being proven first.
- Output model: Agentic OS markdown output folders are convenient, but InfluencerOS needs schema-backed records and Output Packages. Copying generic output folders would weaken traceability.
- Skill feedback: product performance learning and agent skill improvement should not share one undifferentiated `learnings.md`.
- Hosted access: remote execution must not arrive before secrets, provider approval, creator privacy, and workspace isolation are designed.
