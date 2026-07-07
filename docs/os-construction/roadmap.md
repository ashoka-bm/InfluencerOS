# InfluencerOS Roadmap

Last updated: 2026-07-07

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
- `AGENTS.md` is the canonical adapter; `CLAUDE.md` and `SOUL.md` are thin importers (ADR 0019),
- research-acquisition connectors are standing-approved by API-key presence — bounded by a per-run call cap and a kill switch — while generation-provider calls keep the exact-approval gate (ADR 0022),
- Phase 4 is Improvement OS: feedback automation (event-triggered reflection with falsifiable criteria) replaces temporal scheduling, which is deferred (ADR 0025).
- Creator is a multi-type umbrella entity: a required `creator_type` (`influencer | product | brand`) conditions which foundation documents and persona fields are required, reusing the medium-based blocker mechanism; the `creator_*` ID plumbing and downstream schemas are unchanged and a global rename is deferred (ADR 0026).

## Acceptance-Criteria Policy

Phase 0C exit criteria are runnable checks today (each names a command or test). Phase 1-4 exit criteria are still written as target outcomes; each will be rewritten as a runnable check when that phase is planned, following the workstream-14 pattern in the short-term plan.

## Phase 0: Architecture Foundation And Parity Hardening

Goal: make the repo self-orienting and close enough to Agentic OS that future agents can implement without architectural drift.

Status: complete (2026-07-03). One optional Phase 0B item remains: render the comparison Excalidraw scene.

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

- optionally render the comparison Excalidraw scene (framing reviewed
  2026-07-03; the visual map drafts refresh with that render — the
  file-granular source of truth is `architecture-map.md`, which is maintained
  with each slice).

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

Status: complete (2026-07-04). Slices 1-7 and the research-intelligence
hardening follow-up are complete; scheduled research automation remains
deferred until the manual research-intelligence loop has been exercised against
real creator runs.

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

Implementation slices, in the agreed build order (creators first, then
research, then production). Status through 2026-07-04: slices 1-7 are
complete, and the research-intelligence hardening follow-up is complete.

1. Master intake import workflow.
2. Creator readiness validation.
3. Research and Ideas module schema slice (ADR 0020; includes the promotion
   gate validation moved out of Phase 0C workstream 12).
4. Research Findings and Idea Queue workflow.
5. Idea Promotion to Project workflow.
6. Format-specific production planning, including extending content unit types
   and format routing to text formats (article, thread) per ADR 0020.
7. Output Package registration.

Phase 1 hardening follow-up after slices 6-7, captured from the 2026-07-03
live research runtime eval and completed 2026-07-04:

- The merged research-intelligence hardening slice after format-specific
  production planning and Output Package registration. This slice combines
  `ResearchSearchPlan`, source-yield learning, Agentic OS query-intent routing,
  and engagement-weighted source evaluation. Research runs should record planned
  sources before browsing, then record sources searched but not promoted to
  evidence, why they were low yield, and whether they were useful only as
  background context. Repeated low-yield sources should lower
  `research/intelligence/sources.json` usefulness scores and eventually move to
  `flagged_for_removal` or `retired`. Scheduled research automation remains
  deferred until this manual loop has been exercised against real creator runs.

Post-Phase-1 tooling (ADR 0022, 2026-07-05): the research-acquisition connector
layer (`influencer_os/connectors/` — Reddit/OpenAI, X/xAI, Firecrawl,
LinkedIn/Apify) landed to close the binding constraint the first live loop run
surfaced — built-in `WebSearch`/`WebFetch` cannot reach reddit.com or return
primary-post engagement metrics, capping evidence at `medium` confidence. The
tier is env-gated and dormant until a provider key is present; key presence is
standing approval for that tier only (per-run call cap + kill switch; generation
gates unchanged). This is enabling tooling for the deferred scheduled-research
loop, not a new phase: the loop must still be exercised with a live connector
(run 2, needs `OPENAI_API_KEY`) before any scheduled automation is approved, and
scheduled/unattended acquisition stays deferred to Phase 4 Automation OS.

## Phase 2: Learning OS

Goal: capture performance evidence, distill lessons, and feed future planning.

Status: build slices complete (2026-07-06) — all six slices landed and every
runnable exit criterion passes (see `progress.md`). The implementation plan,
entry-criteria verification, the runnable rewrite of the exit criteria
below, and the four user-approved execution decisions (FTS5 keyword lookup
phased ahead of the reference's local-embedding vector leg, one skill per
step under the existing conductor, manual + neutral-CSV ingestion,
JSON-canonical performance summaries) live in
`docs/workflows/learning-os-implementation-plan.md`. Deliberately deferred
remainders: the analytics API connector builds only on explicit request
(Decision 3), and the lookup vector leg lands with Command Centre
(Decision 1).

Entry criteria:

- Output Package records are stable.
- Phase 2 record schemas validate (Published Post Record, Analytics Snapshot, and Performance Summary).
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

## Creative Direction Workstream (between Phase 2 and Phase 3)

Goal: make creative intent first-class and continuous — the Content Beat
Spine as the one template vocabulary, `intended_emotion`/`core_message`
captured at the idea origin and resolved by reference, an advisory
platform→modality→format capability model, and an advisory creative-review
layer.

Status: complete (2026-07-06). All four slices landed with per-slice
adversarial reviews and fix batches; the six runnable exit criteria pass and
the closeout run is recorded in `docs/os-construction/progress.md`. The
workstream never touched `influencer_os/providers/` or generation machinery;
Phase 3 below is independent of it.

Entry criteria (verified 2026-07-06):

- Phase 2 Learning OS build slices are complete and reviewed.
- ADR 0024 is recorded and the glossary terms are in `CONTEXT.md`.

Exit criteria (runnable checks in the implementation plan):

- Template beats carry the closed `beat_role` spine enum.
- Intent fields are captured at the idea origin and survive promotion
  verbatim (schema-optional, skill-required).
- Production plans resolve intent by reference; the micro-journey plan is
  spine-shaped.
- Performance summaries attribute stage findings to applied spine beats.
- `primary_surfaces`/`content_mediums` validate against the canonical enums
  and platform fit warns without blocking.
- The Hook/Payoff Review and both editorial Passes work and cannot block.

Implementation slices, in the agreed batch order:

1. Content Beat Spine + intent fields at the idea origin.
2. Carry-through and performance alignment (micro-journey restructure).
3. Platform, modality, and subtype sharpening.
4. Reviews first slice (Review Record, gates-and-reviews contract,
   Hook/Payoff Review, Clear-Writing and Human-Voice Passes).

## Phase 3: Generation OS

Goal: generate or import media through approved providers while preserving provenance.

Status: complete (2026-07-06). ADR 0023 recorded; all five slices landed
with batch-boundary adversarial reviews and fix batches, and the five
runnable exit criteria pass (closeout run in
`docs/os-construction/progress.md`). Per Decision 3, the deterministic mock
adapter is the only installed adapter — the first real (paid) provider
adapter remains a separate operator-chosen batch following the adapter
contract, and scheduled/unattended generation stays deferred to Phase 4.

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

## Phase 4: Improvement OS

Rescoped 2026-07-06 (ADR 0025) from "Automation OS": the binding need is
feedback automation — each cycle conditioned on evidence from prior cycles —
not temporal automation (clock-triggered jobs), which moved to the Deferred
section below. Historical docs that say "Phase 4 Automation OS" refer to this
phase.

Goal: close the two feedback loops that make the OS improve instead of
repeat — the Performance Delta loop (Creative Performance Map predictions vs
measured analytics, feeding Creator Memory) and the Production Quality loop
(creation friction feeding skill and routine updates) — with a falsifiable
criterion at every step.

Status: complete (2026-07-06). All five slices landed as three
gpt-5.5-reviewed batches with fix batches; the six runnable exit criteria
pass (closeout run in `docs/os-construction/progress.md`). Per the locked
decisions, blocking-criterion promotions remain future per-criterion ADRs,
and temporal scheduling stays in the Deferred section below.

Entry criteria (verified 2026-07-06):

- Planning OS is reliable.
- Learning OS can ingest and distill evidence.
- Provider approval gates cannot be bypassed.

Exit criteria (target outcomes; the runnable rewrite lives in the
implementation plan per the Acceptance-Criteria Policy):

- Production Rubric criteria are binary, scoped, and the Rubric Ratchet is
  enforced at rest: every rejection cites or mints a criterion.
- Creation friction is captured as durable recurrence-keyed events; rejected
  drafts stay ephemeral.
- A reflection trigger surfaces "reflection due" as an advisory warning from
  event thresholds — event-driven, never clock-driven, never blocking.
- Distilled skill updates carry falsifiable improvement claims verified
  against subsequent runs.
- Creative Performance Map predictions can be quantified and performance
  summaries score each stage confirmed, refuted, or unmeasurable.
- Criteria reach the blocking quality checklist only through the
  gates-and-reviews ADR checklist.

Implementation slices, in the agreed build order:

1. Rubric substrate: Production Rubric records, rejection/incident events on
   the system-event ledger with recurrence keys, `log-incident` CLI,
   cite-or-mint validation.
2. Reflection trigger: at-rest event-threshold checks surfacing advisory
   warnings and board badges, including the unclassified-rejection gap
   signal.
3. Distillation with improvement claims: proposal → human approval → skill
   update, with claim status computed from subsequent runs.
4. Falsifiable predictions: Creative Performance Map prediction fields and
   per-stage confirmed/refuted/unmeasurable in performance summaries.
5. Criteria maturity ladder: advisory → proven → promoted into the blocking
   quality checklist via the gates-and-reviews ADR checklist.

## Post-Phase-4: Live Testing And Multi-Entity Onboarding

All four build phases (0–4) plus the Creative Direction workstream are
complete. The full local-first pipeline — intake → research → ideas →
promotion → production planning → generation (mock adapter) → packaging →
publishing/analytics → learning → improvement loops — has been validated
against disposable fixtures and a deterministic mock generation adapter only.
The next stage is exercising it against reality.

Status: in progress (opened 2026-07-07).

Two parallel tracks:

### Track 1 — Live testing (influencers first)

The influencer path works today. Onboard one or more real influencers, wire
the ADR 0022 research-acquisition API keys (`.env`, standing-approved by key
presence, per-run call cap + kill switch), exercise the manual
research-intelligence loop against real data (ADR 0022 "run 2"), and produce
marketing material end to end. This is the first contact between the OS and
real creator data and the first real (paid) provider adapter decision
(Generation OS Decision 3).

The 2026-07-07 pre-alpha review and the gap-closing batches (composed
`validate all` release gate, day-1 runbook, connector smoke runs) live in
`docs/workflows/alpha-readiness-implementation-plan.md`.

### Track 2 — Multi-entity onboarding (product/brand support, ADR 0026)

Goal: onboard products and brands, not only avatar-led influencers, via a
`creator_type` discriminator that conditions the required foundation
documents. "Creator" becomes the umbrella term; the `creator_*` plumbing and
the 41 downstream schemas are unchanged.

Entry criteria:

- ADR 0026 recorded (done, 2026-07-07).
- The influencer path stays green throughout (no regression to the working
  setup flow or the 739-test pipeline).

Exit criteria (target outcomes; runnable rewrite lands in the implementation
plan):

- `creator-profile.json` carries a required `creator_type`
  (`influencer | product | brand`), defaulting to `influencer` for existing
  fixtures.
- Foundation-document and persona-field requirements are conditional on
  `creator_type`, enforced at readiness by the same mechanism as the
  medium-based blockers; persona fields are required for `influencer` only.
- Brand foundation docs (brand brief, brand guidelines, brand voice) and
  product foundation docs (offering + inherited brand context) are produced by
  type-aware setup skills; `create-identity`/`create-soul` run for influencers
  only.
- A product may carry an advisory `parent_brand_ref`; parent-brand context is
  inline in v1 (no cross-workspace resolution).
- The downstream research/ideas/generation/analytics pipeline is unchanged; a
  brand or product workspace validates and can produce an Output Package.

Implementation slices (build order to be detailed in
`docs/workflows/multi-entity-onboarding-implementation-plan.md`):

1. `creator_type` discriminator + schema-optional persona fields + validator
   default.
2. Type-conditional foundation-doc table + readiness enforcement (extend the
   ADR 0013 blocker mechanism).
3. Type-aware setup conductor + brand/product foundation subskills.
4. Product `parent_brand_ref` (advisory) + a brand and a product fixture
   validating end to end.

## Deferred: Temporal Scheduling (former Automation OS scope)

Goal: clock-triggered creator operations — scheduled research refresh,
scheduled analytics ingestion, markdown job definitions, and any live
scheduler.

Status: deferred (operator decision, 2026-07-06; ADR 0025).

The scoping decisions: v1 stays local-first with no live scheduler; the
scheduled-research capability additionally stays gated behind the manual
research-intelligence loop being exercised with a live connector (ADR 0022
"run 2", needs `OPENAI_API_KEY`) against real creator data. Scheduled jobs,
if reopened, may never promote ideas, create projects, or call providers
without human approval (PRD Out of Scope).

Reopen when:

- the Improvement OS feedback loops are stable,
- real creator data exists and the live-connector research loop has run,
- the user explicitly approves a scheduler scope in its own ADR.

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

## Deferred: Kanban Board UI

Goal: an operable Kanban interface over the Content Board projection.

Status: deferred (user decision, 2026-07-03).

The data contract ships first: `boards/content-board.json` (deterministic
card ids, parent idea / child project cards, warning badges, `manual_order`
projection metadata) and the `rebuild-board` / `validate board` commands land
in Phase 1 slice 4, so a UI can arrive later without schema changes or data
migration. Canonical records never store board state, so no rework is
implied by deferring.

Do not build in the current phase:

- board web/desktop UI,
- drag-to-status mutation surfaces,
- a UI-side promotion button (promotion is the human-approval gate and must
  produce a locked `IdeaPromotion`, never a status drag).

Optional intermediate once real queue data exists (post slice 5): a
disposable read-only local HTML viewer over `content-board.json` to pressure
test the board shape before Phase 2 hardens around it.

Reopen when:

- Phase 1 slices are complete and record semantics have stopped moving,
- real creator queue data exists,
- the user explicitly approves the UI scope (mutations must flow through
  canonical records plus `rebuild-board`, keeping the UI a reader, not a
  second writer).

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

Hooks (session-end memory capture, skill auto-commit) and cron jobs (memory distill/curate/index) are deferred in v1. They only automate skills and checks that already run manually, so their absence removes no v1 capability (see PRD Out of Scope and ADR 0016). Reopen hooks with explicit approval; cron belongs to the deferred Temporal Scheduling scope (ADR 0025).
