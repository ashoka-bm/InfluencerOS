# InfluencerOS Roadmap

Last updated: 2026-07-03

This roadmap defines phase order, exit criteria, and implementation priorities. Progress status lives in `docs/os-construction/progress.md`.

## Build/Test Data Policy

Until the user declares real onboarding has started, Creator Workspace contents under `workspace-library/` are disposable fixtures for validating the OS. Build work should optimize the system contracts, skills, validation, and workflow ergonomics, not preserve current test creator data as if it were permanent.

## North Star

InfluencerOS should become a close Agentic OS adaptation for avatar-led creator content planning.

Default rule:

```text
Follow Agentic OS unless a user-approved override exists.
```

Approved standing overrides:

- creators replace generic clients,
- Creator Workspaces replace client workspaces,
- schemas are first-class workflow contracts,
- provider-backed generation has stricter exact approval gates,
- creator memory is provenance-linked and creator-scoped,
- platform publishing/scheduling is not v1,
- Command Centre is deferred,
- self-improvement runs as local-first system skills (ADR 0016),
- skills stay repo-central with no category prefixes (ADR 0017),
- Creator Workspace propagation is built as CLI subcommands with gated content zones (ADR 0018),
- `AGENTS.md` is the canonical adapter; `CLAUDE.md` and `SOUL.md` are thin importers (ADR 0019).

## Acceptance-Criteria Policy

Phase 0C exit criteria are runnable checks today (each names a command or test). Phase 1-4 exit criteria are still written as target outcomes; each will be rewritten as a runnable check when that phase is planned, following the workstream-14 pattern in the short-term plan.

## Phase 0: Architecture Foundation And Parity Hardening

Goal: make the repo self-orienting and close enough to Agentic OS that future agents can implement without architectural drift.

Status: in progress.

### Phase 0A: Foundation Docs

Completed:

- root adapter files exist for the main agent contexts,
- PRD defines purpose, scope, and deterministic acceptance criteria,
- roadmap defines phases and exit criteria,
- repository map identifies file ownership,
- Agentic OS alignment and accepted divergences are documented,
- Agentic OS copy/adaptation audit exists,
- Agentic OS parity plan exists,
- divergence test exists,
- visual architecture map standard exists,
- first-party OS persona context exists,
- skill registry and context matrix exist,
- README and AGENTS link to durable planning docs.

### Phase 0B: Visual Architecture

Completed:

- Agentic OS baseline architecture map exists in the Agentic OS repo.
- InfluencerOS target architecture map exists.
- Agentic OS vs InfluencerOS comparison draft exists.

Remaining:

- review comparison framing,
- optionally render comparison Excalidraw scene,
- update maps after parity hardening changes.

### Phase 0C: Parity Hardening

Complete (2026-07-03). All exit criteria below pass; `docs/os-construction/progress.md` records the run.

Exit criteria (each maps to a command or test; nothing exits on "documented"):

- `python3 -m unittest discover -s tests` and `python3 -m influencer_os validate examples` pass.
- Every `skills/*/SKILL.md` has a skill-registry row and context-matrix coverage, enforced by a registry drift check.
- The adapter drift check passes: `CLAUDE.md` and `SOUL.md` import `AGENTS.md` and restate no divergent read order (ADR 0019).
- Root and creator memory policies are explicit and the `context/MEMORY.md` byte cap is enforced by a check.
- The workspace scaffold and `creator-workspace.schema.json` include `.claude/skills/` and the override layout.
- Project output layout is deterministic: `python3 -m influencer_os validate project <path>` passes for a scaffolded project and `project.schema.json` pins the project paths.
- The self-improvement skills (`wrap-up`, `memory-write`) exist and a run appends to `context/learnings.md` (ADR 0016).
- The content conductor declares a machine-actionable call graph (ADR 0017), enforced by a drift check that fails if it names a skill not on disk and not marked `[PLANNED]` with a halt instruction, and that diffs its `dependencies` frontmatter against `architecture-map.md`.
- The workstream-12 determinism fixes pass their tests (project `acceptance_criteria`, output-package provenance refs, provenance resolution, generic record validation). The ADR 0020 research schema slice and promotion gate are Phase 1 work, not 0C exit criteria.

See `docs/os-construction/short-term-plan.md`.

## Phase 1: Planning OS

Goal: produce researched, creator-fit content plans and output package specs without provider-backed generation.

Entry criteria:

- Phase 0C parity hardening is complete.
- Creator Workspace structure is deterministic.
- Skill registry and context matrix are current.
- Provider boundary is visible in every generation-adjacent workflow.

Exit criteria:

- Creator Workspace setup works from a reviewed intake.
- Creator readiness gates work.
- Creator Content Schedule records capture loose goals, irregular calendar slots, and drift checks.
- Research Runs are dated, sourced, platform-scoped, and tied to real evidence.
- Video Understanding Packs exist when real videos are analyzed.
- Research Findings stay concise, creator-scoped, and backed by dated evidence.
- Idea Queue entries are scored, evidence-linked, and update as research changes.
- Human-approved Idea Promotions may create one or more Projects.
- Projects route promoted ideas to format-specific production plans.
- Base Video Generation Plans are provider-neutral.
- Output Package records validate and preserve provenance.

Likely implementation slices, in the agreed build order (creators first, then
research, then production):

1. Master intake import workflow.
2. Creator readiness validation.
3. Research and Ideas module schema slice (ADR 0020; includes the promotion
   gate validation moved out of Phase 0C workstream 12).
4. Research Findings and Idea Queue workflow.
5. Idea Promotion to Project workflow.
6. Format-specific production planning, including extending content unit types
   and format routing to text formats (article, thread) per ADR 0020. Until
   this slice lands, promotion may only create Projects for supported formats.
7. Output Package registration.

## Phase 2: Learning OS

Goal: capture performance evidence, distill lessons, and feed future planning.

Entry criteria:

- Output Package records are stable.
- Published Post Record and Analytics Snapshot schemas validate.
- Creator Memory policy is implemented.

Exit criteria:

- Published Post Records can be registered.
- Analytics Snapshots can be added through API, CSV, or manual entry.
- Performance Summaries map results to packaging, hook, body retention, payoff, and CTA.
- Distilled Creator Memory links back to evidence.
- SQL index rebuilds from files.
- Semantic lookup indexes only curated decision-support material.

Likely implementation slices:

1. Published Post Record registration.
2. Analytics Snapshot import/manual entry.
3. Performance Summary generation.
4. Learning distillation into Creator Memory.
5. SQL index rebuild.
6. Semantic lookup projection.

## Phase 3: Generation OS

Goal: generate or import media through approved providers while preserving provenance.

Entry criteria:

- Planning OS produces stable provider-neutral Base Video Generation Plans.
- Output Package provenance is stable.
- Provider approval policy is represented in records and UI/CLI prompts.

Exit criteria:

- Provider adapter boundary exists.
- Approval workflow records exact calls or batches.
- Generated and imported assets store provenance.
- Quality checks run before packaging.
- Output Packages reference final artifacts.

Likely implementation slices:

1. Provider registry.
2. Approval record schema or workflow.
3. Import-generated-asset workflow.
4. Asset provenance capture.
5. Quality review checklist.

## Phase 4: Automation OS

Goal: add repeatable scheduled creator operations after planning, learning, and generation are stable.

Entry criteria:

- Planning OS is reliable.
- Learning OS can ingest and distill evidence.
- Provider approval gates cannot be bypassed.

Exit criteria:

- Scheduled research refresh is defined.
- Scheduled project creation is defined.
- Scheduled analytics ingestion is defined.
- Human approval gates block risky, paid, destructive, or irreversible actions.
- Any publishing or scheduling integration is explicitly approved.

Likely implementation slices:

1. Markdown job definition pattern adapted from Agentic OS.
2. Scheduled research refresh dry run.
3. Scheduled analytics ingestion dry run.
4. Human approval gate for scheduled actions.

## Deferred: Command Centre

Goal: add a dashboard/control panel only after the file-first OS is stable.

Status: deferred.

Do not build in the current phase:

- dashboard,
- task queue UI,
- autonomous chat UI,
- settings UI,
- Command Centre SQLite operational DB,
- hosted/team memory UI.

Reopen when:

- file-first workflows are stable,
- Creator Workspaces are stable,
- skills and memory are stable,
- automation is designed,
- user explicitly approves Command Centre scope.

## Deferred: Anywhere Access

Goal: access and run InfluencerOS from hosted or remote channels.

Status: deferred.

Exit criteria when reopened:

- local-first workflows remain canonical,
- remote execution has the same file, provenance, and approval boundaries,
- secrets and credentials use tool-managed auth or `.env`,
- remote channels cannot bypass approval gates.

## Deferred: Hooks And Cron

Goal: automatic capture and scheduled jobs.

Status: deferred.

Hooks (session-end memory capture, skill auto-commit) and cron jobs (memory distill/curate/index) are deferred in v1. They only automate skills and checks that already run manually, so their absence removes no v1 capability (see PRD Out of Scope and ADR 0016). Reopen hooks with explicit approval; cron belongs to Phase 4 Automation OS.
