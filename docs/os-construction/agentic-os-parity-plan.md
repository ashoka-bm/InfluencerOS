# Agentic OS Parity Plan

Last updated: 2026-07-03

## Decision

Do not restart InfluencerOS.

Adapt the current repository toward closer Agentic OS parity, with Command Centre deferred.

## Rationale

The current repo already has the pieces that are expensive to recreate:

- root adapters,
- first-party OS persona context,
- construction docs,
- copy/adaptation audit,
- divergence test,
- context matrix,
- skill registry,
- schema contracts,
- examples,
- CLI validation,
- Creator Workspace direction,
- provider boundary,
- visual map standards.

Starting over would mostly recreate these files and risk losing the InfluencerOS-specific contracts that already fit the product.

The problem is not wrong foundation. The problem is incomplete parity with the Agentic OS runtime patterns.

## Parity Target

InfluencerOS should stay close to Agentic OS in these areas:

- root adapters,
- first-party OS context,
- brand context,
- context matrix,
- skill registry,
- progressive-disclosure skills,
- `SKILL.local.md` overrides,
- file-first memory,
- project/output consolidation,
- scheduled-workflow definitions,
- memory-capture conventions, with hooks deferred until explicitly approved,
- visual architecture maps.

InfluencerOS should intentionally differ in these areas:

- creators replace clients as the primary workspace unit,
- schemas are first-class contracts,
- provider-backed generation has stricter approval gates,
- creator memory must be provenance-linked and creator-scoped,
- platform publishing/scheduling is not v1,
- hooks are not v1 without a new ADR and user approval,
- Command Centre is deferred.

## Deferred From Agentic OS

Command Centre, hooks, cron, hosted access, and anywhere-access execution are deferred until the file-first OS, Creator Workspaces, skills, memory, and workflow contracts are stable. Hooks also require a separate ADR and explicit user approval because hidden automation can cross privacy, provider, or approval boundaries.

Do not build:

- dashboard,
- task queue UI,
- autonomous chat UI,
- settings UI,
- Command Centre SQLite operational DB,
- hosted/team memory UI,
- automatic memory-capture hooks,
- branch/session/workflow hooks,
- cron jobs.

Until then, CLI and docs are enough.

## Adapt Or Restart Test

Restart only if at least two of these are true after the parity audit:

- existing repo layout blocks Agentic OS-style context and skill loading,
- schemas and workflow contracts cannot coexist with Agentic OS-style skills,
- Creator Workspace layout cannot support local overrides and memory isolation,
- current CLI structure prevents file-first source of truth,
- tests cannot validate the adapted architecture without large rewrites.

Current assessment: none of these are true.

## Immediate Gap Audit

Gap audit updated 2026-07-03 after Phase 0C batches A-F closed the parity workstreams.

| Agentic OS pattern | Current InfluencerOS state | Gap | Next action |
| --- | --- | --- | --- |
| Root adapters | Present: `AGENTS.md` canonical, `CLAUDE.md`/`SOUL.md` thin importers (ADR 0019). | None — adapter drift check built (`tests/test_drift_checks.py`). | Keep the check green. |
| Root context | Present: `context/` with a 2,500-byte `MEMORY.md` cap enforced by `memory-write` and a drift check. | None. | Keep the cap check green. |
| Root brand context | Present: `brand_context/`. | Stubs only. | Expand only when doing OS marketing content. |
| Context matrix | Present with workspace paths and skill coverage. | None — coverage enforced by a drift check. | Keep the check green. |
| Skill registry | Present; bidirectional coverage enforced, future table may not name on-disk skills. | None. | Keep the check green. |
| Skill runtime layout | Repo source `skills/`; creator runtime copies under `.claude/skills/` (ADR 0017: no category prefixes). | None. | — |
| Skill local overrides | Documented; worked `skills/influencer-os/SKILL.local.md` exists; sync preservation tested. | None. | — |
| Multi-client architecture | Adapted to creators; `init-creator`/`sync-creator-runtime`/`update-creators` built with backups (ADR 0018). | Scripts/settings/hooks/cron zones stay inert by design. | Revisit gated zones only with explicit approval. |
| Projects/output consolidation | Project paths pinned in `project.schema.json`; provenance IDs resolve to real records. | None for the transitional layout; ADR 0020 layout lands in Phase 1. | Build the research module slice in Phase 1. |
| Memory tiers | Tier 0 rules defined (`docs/creator-workspace-structure.md`); writers built (`memory-write`, `log-learning`). | Operational creator usage begins with Phase 1 creator work. | Use the writers in Phase 1 workflows. |
| Semantic recall | Contracted. | Not implemented. | Defer until Tier 0 usage and project layout are proven in Phase 1-2. |
| Cron/scheduled workflows | Deferred. | Need job-definition pattern later. | Copy markdown job pattern in Automation OS phase. |
| Hooks | Deferred. | Need explicit future approval. | Do not add in v1 without new ADR. |
| Command Centre | Deferred. | None for v1. | Revisit after Automation OS. |
| Subagents (`.claude/agents/`) | Classified defer (copy plan, workstream 15). | None for v1. | ADR only if a Phase 1 producer adopts the pattern. |
| Provider boundaries | Present and stricter. | Needs provider registry later. | Add only when real adapters are introduced. |

## Recommended Next Step

The parity hardening pass is complete (Phase 0C batches A-G; see
`docs/os-construction/progress.md` for the verification record). Next: the
first Planning OS implementation slice — master intake import — in the
roadmap's Phase 1 slice order.

## Success Criteria

InfluencerOS is ready for implementation when:

- every existing skill is registered — met (drift check),
- every registered skill has context-matrix coverage through an explicit skill row or the workflow row that invokes it — met (drift check),
- copied creator runtime skills are implemented and verified — met (tests),
- root and creator memory policies are explicit — met (byte cap + Tier 0 rules),
- creator override rules are reflected in workspace docs — met,
- project output layout is deterministic — met (schema-pinned paths + validation),
- tests or checks catch adapter, registry, and schema drift — met (`tests/test_drift_checks.py`).

All criteria met 2026-07-03.
