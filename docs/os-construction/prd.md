# PRD: InfluencerOS Agentic Operating System

Last updated: 2026-07-02

## Problem Statement

The repo needs to become a dependable Agentic OS adaptation for creator content planning — avatar-led influencers and, per ADR 0026, products and brands — without drifting into a generic content tool, a platform publisher, or a partial reimplementation of Agentic OS.

The user has already purchased and installed an Agentic OS reference. InfluencerOS should copy that architecture closely unless the domain requires an explicit adaptation. Any deviation from Agentic OS must be surfaced, documented, and approved by the user before implementation.

The immediate problem is uncertainty: the repo has useful InfluencerOS-specific schemas, skills, CLI helpers, and planning docs, but it is not yet clear enough for another agent to implement safely without introducing drift. The next agent needs a long-term product plan, a short-term parity-hardening plan, deterministic acceptance criteria, and clear boundaries for what to copy, adapt, defer, and reject.

## Solution

InfluencerOS will be built as a local-first, file-first Agentic OS adaptation for creating researched, subject-fit content plans and generation-ready output packages. "Creator" is the umbrella term for the onboarded subject; per ADR 0026 a Creator may be an avatar-led influencer, a product, or a brand, distinguished by a `creator_type` discriminator that conditions the required foundation documents.

The system will copy Agentic OS closely in structure:

- root adapters,
- first-party OS persona context,
- brand context,
- context matrix,
- skill registry,
- progressive-disclosure skills,
- `SKILL.local.md` overrides,
- file-first memory,
- project/output consolidation,
- scheduled-workflow definitions (deferred with temporal scheduling, ADR 0025),
- memory-capture conventions later, with hooks deferred until explicitly approved,
- visual architecture maps.

The system will adapt Agentic OS where the domain requires it:

- creators replace generic clients,
- Creator Workspaces replace client workspaces,
- schemas are first-class workflow contracts,
- provider-backed generation requires stricter exact approval,
- creator memory is provenance-linked and creator-scoped,
- platform publishing/scheduling is not part of v1,
- Command Centre is deferred until the file-first OS is stable.

The system will enforce alignment through durable planning docs, ADRs, visual maps, a divergence test, a parity plan, context and skill registries, validation commands, and eventually drift checks.

## User Stories

1. As the repo owner, I want every agent thread to load the same product direction, so that the repo does not drift between sessions.
2. As the repo owner, I want InfluencerOS to follow Agentic OS by default, so that we reuse the purchased architecture instead of reinventing it.
3. As the repo owner, I want every deviation from Agentic OS to require a documented user-approved decision, so that architectural changes are intentional.
4. As the repo owner, I want Command Centre deferred, so that we prove the file-first OS before adding a UI/runtime surface.
5. As the repo owner, I want a long-term roadmap, so that agents can work in the right phase order.
6. As the repo owner, I want a short-term implementation plan, so that another agent can start without reconstructing this conversation.
7. As a future implementation agent, I want a PRD with explicit requirements, so that I can implement without guessing product scope.
8. As a future implementation agent, I want a parity plan, so that I know whether to copy, adapt, defer, or reject each Agentic OS pattern.
9. As a future implementation agent, I want a divergence test, so that I know when to stop and ask for an architecture decision.
10. As a future implementation agent, I want a context matrix, so that I load only the context needed for each workflow.
11. As a future implementation agent, I want a skill registry, so that skills are routed and updated consistently.
12. As a future implementation agent, I want `SKILL.local.md` override rules, so that creator-specific changes do not corrupt core skills.
13. As a future implementation agent, I want core skills protected from local feedback, so that repeated local preferences are promoted only when they apply system-wide.
14. As a future implementation agent, I want root OS persona context, so that InfluencerOS can create content for itself as a first-party brand/persona.
15. As a future implementation agent, I want creator-specific memory separated from OS-level process memory, so that creator learnings do not blend with system learnings.
16. As a future implementation agent, I want Creator Workspaces to mirror Agentic OS client workspaces where appropriate, so that creator state stays private and navigable.
17. As a creator operator, I want a creator workspace per creator, so that identity, references, memory, projects, analytics, and progress remain separated.
18. As a creator operator, I want creator setup to produce typed and human-readable files, so that automation and creative continuity both work.
19. As a creator operator, I want niche and audience treated as inputs, so that the system does not invent creator strategy.
20. As a creator operator, I want current research dated and sourced, so that trend claims stay tied to evidence.
21. As a creator operator, I want real video analysis stored separately when used, so that observations can be audited.
22. As a creator operator, I want rolling Research Findings backed by dated evidence, so that I can see what is working, weakening, and worth watching without loading every raw source.
23. As a creator operator, I want a scored Idea Queue, so that researched opportunities can be compared, updated, and held before production.
24. As a creator operator, I want human-approved Idea Promotions, so that the system can create one or more Projects without silently choosing production direction.
25. As a creator operator, I want provider-neutral generation plans before media generation, so that we can review before paying or calling external providers.
26. As a creator operator, I want explicit human authorization before image,
video, audio, render, upload, paid, or irreversible calls. An approved Visual
Continuity Plan may authorize one bounded initial pass over its listed
creator-setup reference images; other calls require exact approval.
27. As a creator operator, I want output packages to preserve provenance, so that every artifact traces back to creator profile, research, idea, template, plan, and generation plan.
28. As a creator operator, I want analytics and performance summaries stored as evidence, so that future learning is grounded.
29. As a creator operator, I want distilled creator memory, so that future plans improve without loading raw analytics by default.
30. As a creator operator, I want SQL lookup and semantic lookup to be separate, so that exact record queries and meaning-based recall do different jobs.
31. As a future agent, I want visual architecture maps, so that the whole system and each workflow can be inspected quickly.
32. As a future agent, I want the Agentic OS baseline map, so that InfluencerOS can be compared against the source architecture.
33. As a future agent, I want the InfluencerOS target map, so that implementation work can align to the intended system.
34. As a future agent, I want the comparison map, so that I can see what is copied, adapted, deferred, or rejected.
35. As a future agent, I want tests or drift checks for adapters, context matrix, skill registry, schemas, and examples, so that documentation and code cannot silently diverge.
36. As a future agent, I want Phase 0 to end with a parity-hardened foundation, so that Phase 1 can implement product behavior instead of still debating architecture.
37. As a future agent, I want Phase 1 to avoid provider-backed media generation, so that the first slice can be validated locally.
38. As a future agent, I want Phase 2 to capture performance evidence, so that learning is built from real outputs and analytics.
39. As a future agent, I want Phase 3 to add generation only after approval and provenance are stable, so that generated assets remain auditable.
40. As a future agent, I want Phase 4 automation to wait until planning, learning, and generation are stable, so that scheduled jobs do not amplify broken workflows.
41. As a future agent, I want anywhere access deferred, so that local privacy, secrets, and approval gates are solved first.

## Implementation Decisions

- InfluencerOS will not restart from scratch. The current repo will be adapted toward close Agentic OS parity.
- Command Centre is deferred. It should not be implemented until file-first context, Creator Workspaces, skills, memory, and workflow contracts are stable.
- Agentic OS is the default architectural reference. Any deviation requires a user-approved override recorded in an ADR or alignment document.
- Root adapters are `AGENTS.md`, `CLAUDE.md`, and `SOUL.md`.
- Root `context/` and `brand_context/` represent InfluencerOS as a first-party OS persona/client.
- Creator-specific context belongs under ignored Creator Workspaces.
- Creator Workspaces are the InfluencerOS adaptation of Agentic OS client workspaces.
- Core skills live in the repo. Scope-specific overrides use `SKILL.local.md`.
- Local skill rules are promoted into core skills only after repeated feedback shows the rule applies system-wide.
- Self-improvement runs as local-first system skills (`wrap-up`, `memory-write`) triggered by description, not hooks (ADR 0016).
- Skills stay repo-central with plain kebab-case names and no category prefixes; conductors declare machine-actionable `dependencies` and phase-to-owner call graphs (ADR 0017).
- Creator Workspace propagation is built as CLI subcommands; skills propagate now and scripts/settings/hooks/cron templates stay gated until their subsystem is approved (ADR 0018).
- `AGENTS.md` is the canonical adapter; `CLAUDE.md` and `SOUL.md` are thin importers and `context/SOUL.md` is the sole identity (ADR 0019).
- Research and idea generation use platform-scoped Research Findings, Idea Queue, and Idea Promotion instead of Content Idea Set and Selected Content Idea records (ADR 0020).
- Accepted post-v1 target (not yet shipped): the onboarded entity becomes multi-type. "Creator" is the umbrella term; a required `creator_type` discriminator (`influencer | product | brand`) will condition which foundation documents and persona fields are required, reusing the medium-based blocker mechanism. The `creator_*` ID plumbing and downstream schemas remain unchanged; a global rename is deferred (ADR 0026).
- Product behavior is schema-backed. Each workflow stage must have explicit inputs, outputs, provenance, validation, and gates.
- The highest implementation seam is the file-first workspace plus validation CLI. Prefer tests at that seam over low-level helper tests.
- Provider calls are not part of planning. Provider-backed generation, render, upload, paid, and irreversible actions require exact user approval.
- InfluencerOS will not use "memory palace" as v1 language. Use SQL index, semantic lookup projection, and Creator Memory.
- Raw analytics remain evidence. Distilled creator learnings become default future context.
- Platform-specific adapters, publishing, post-production treatments, hosted execution, hooks, and Command Centre are deferred unless explicitly reopened by the user. Scheduled research jobs are allowed as read-only research and notification automation; they cannot promote ideas or call providers in v1.

## Testing Decisions

The primary testing seam is the repo-level file contracts and CLI validation.

Good tests should verify external behavior:

- adapter files point to the same durable read order,
- every registered skill exists on disk,
- every skill has context-matrix coverage through an explicit skill row or the workflow row that invokes it,
- Creator Workspace scaffolding creates the documented structure,
- creator project scaffolding creates deterministic folders and record paths,
- schema examples validate,
- provider approval gates are represented in plans without making provider calls,
- output packages preserve required provenance,
- drift checks fail when docs/registry/schema examples disagree.

Existing prior art:

- unit tests under `tests/`,
- schema validation through `python3 -m influencer_os validate examples`,
- CLI workspace/project validation commands,
- example JSON records under `examples/`,
- schema contracts under `schemas/`.

New test/check targets:

- adapter read-order drift check,
- skill registry drift check,
- context matrix coverage check,
- Creator Workspace structure check,
- project output layout check,
- Tier 0 memory policy check.

## Long-Term Phases

### Phase 0: Architecture Foundation And Agentic OS Parity

Goal: make the repo self-orienting and close enough to Agentic OS that future agents can implement without drift.

Required outcomes:

- PRD, roadmap, parity plan, comparison map, and progress docs are current.
- Root adapters load the same durable context.
- Root OS persona context and brand context exist.
- Creator Workspace structure is documented.
- Skill registry and context matrix cover actual skills.
- Divergence test is mandatory for architecture-impacting changes.
- Visual maps exist or are queued for overall architecture, Agentic OS baseline, and comparison.
- Short-term parity hardening is complete.

### Phase 1: Planning OS

Goal: produce researched, creator-fit content plans and output package specs without provider-backed generation.

Required outcomes:

- Creator setup works from reviewed intake.
- Creator readiness gates work.
- Creator Content Schedule records capture loose goals, irregular calendar slots, and drift checks.
- Research Runs are dated, sourced, platform-scoped, and tied to real evidence.
- Video Understanding Packs exist when real videos are analyzed.
- Research Findings stay concise, creator-scoped, and backed by dated evidence.
- Idea Queue entries are scored, evidence-linked, and update as research changes.
- Human-approved Idea Promotions replace selected-idea records and may create one or more Projects.
- Projects route promoted ideas to templates or production structures and format-specific production plans.
- Base Video Generation Plans remain provider-neutral.
- Output Package records validate and preserve provenance.

### Phase 2: Learning OS

Goal: capture publication and performance evidence, distill lessons, and feed future planning.

Required outcomes:

- Published Post Records can be registered.
- Analytics Snapshots can be added through API, CSV, or manual entry.
- Performance Summaries map results to packaging, hook, body retention, payoff, and CTA.
- Distilled Creator Memory links back to evidence.
- SQL index rebuilds from files.
- Semantic lookup indexes curated decision-support material only.

### Phase 3: Generation OS

Goal: generate or import media through approved providers while preserving provenance.

Required outcomes:

- Provider adapter boundary exists.
- Approval workflow records exact calls or batches.
- Generated/imported assets store provenance.
- Quality checks run before packaging.
- Output Packages reference final artifacts.

### Phase 4: Improvement OS

Rescoped 2026-07-06 (ADR 0025) from "Automation OS": feedback automation
replaced temporal scheduling, which is deferred.

Goal: close the Performance Delta and Production Quality feedback loops with
falsifiable criteria, so each research, idea, and production cycle is
conditioned on what prior cycles actually did.

Required outcomes:

- Production Rubric criteria are binary and citable, and grow by the Rubric
  Ratchet: every rejection cites an existing criterion or mints a new one.
- Creation friction is captured as durable recurrence-keyed events; rejected
  drafts stay ephemeral.
- Reflection is event-triggered by thresholds, never clock-scheduled, and
  never blocks the pipeline.
- Skill updates carry falsifiable improvement claims verified on subsequent
  runs.
- Creative Performance Map predictions are quantifiable and scored
  confirmed, refuted, or unmeasurable per stage.
- A human approves every skill-file write; criteria block only after
  promotion through the gates-and-reviews ADR checklist.

Scheduled jobs (research refresh, analytics ingestion, project creation)
moved to the deferred Temporal Scheduling scope. If ever reopened, they
cannot promote ideas or create production work without human approval.

### Deferred: Command Centre And Anywhere Access

Goal: add dashboard, hosted, or channel-based execution only after local file-first operation is stable.

Required outcomes when reopened:

- local-first workflows remain canonical,
- remote execution preserves provenance and approval gates,
- secrets use `.env` or tool-managed auth,
- remote channels cannot bypass provider or approval boundaries.

## Short-Term Next Step Plan

The next implementation pass is **Parity Hardening**, not feature implementation.

1. Harden context matrix and skill registry against actual files.
2. Define exact Creator Workspace skill override and project output layout.
3. Implement Tier 0 creator recall rules.
4. Add adapter/context/skill registry drift checks.
5. Update maps and progress docs.
6. Then start the first Planning OS implementation slice.

This short-term plan is detailed in `docs/os-construction/short-term-plan.md`. The 2026-07-01 Agentic OS parity review (`docs/os-construction/adversarial-review.md`) added workstreams 9-15 there: self-learning system skills, a machine-actionable conductor call graph, propagation build-out, determinism fixes, validator/coverage hardening, acceptance-criteria determinism, and copy-plan coverage.

## Out of Scope

- Restarting the repo from scratch.
- Command Centre implementation.
- Hosted execution or anywhere-access channels.
- Platform publishing, platform post scheduling, or uploads.
- Platform-specific post-production adapters.
- Automated idea promotion or project creation from scheduled jobs.
- Provider-backed image, video, audio, or render calls without exact approval.
- Raw analytics as default semantic memory.
- Memory palace terminology.
- Generic installer/updater machinery from Agentic OS.
- Editing core skill files for one creator's local preference.

## Further Notes

The issue tracker and triage labels were not available in this thread, so this PRD was written into the repo planning docs instead of published to an issue tracker.

The next agent should start with the short-term plan and complete parity hardening before implementing Planning OS behavior.
