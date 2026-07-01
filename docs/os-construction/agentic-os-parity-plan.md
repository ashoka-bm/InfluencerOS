# Agentic OS Parity Plan

Last updated: 2026-07-01

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

Run a file-by-file parity audit against the Agentic OS baseline and classify each gap.

| Agentic OS pattern | Current InfluencerOS state | Gap | Next action |
| --- | --- | --- | --- |
| Root adapters | Present: `AGENTS.md`, `CLAUDE.md`, `SOUL.md`. | Need drift check. | Add lightweight adapter read-order check. |
| Root context | Present: `context/`. | Needs memory budget and write rules. | Add context memory policy. |
| Root brand context | Present: `brand_context/`. | Needs stronger templates/examples. | Expand only when doing OS marketing content. |
| Context matrix | Present. | Needs Creator Workspace path specificity. | Harden matrix. |
| Skill registry | Present. | Needs all skill rows and triggers verified. | Audit `skills/` against registry. |
| Skill runtime layout | Repo source `skills/`; creator runtime copies under `.claude/skills/`. | Implemented for copied skills; category-prefix convention remains future. | Keep copied skill runtime; decide category prefixes before adding many new skills. |
| Skill local overrides | Documented and copied runtime path exists. | Needs broader drift checks. | Add checks that runtime sync preserves `SKILL.local.md`. |
| Multi-client architecture | Adapted to creators. | Skill propagation implemented; scripts/settings/hooks/cron still deferred. | Revisit broader propagation only with explicit approval. |
| Projects/output consolidation | Partially defined. | Needs exact project folder layout. | Define selected idea through output package folders. |
| Memory tiers | ADRs exist. | Tier 0 creator recall not operational. | Implement creator `MEMORY.md`, distilled learnings, progress load rules. |
| Semantic recall | Contracted. | Not implemented. | Defer until Tier 0 and project layout are stable. |
| Cron/scheduled workflows | Deferred. | Need job-definition pattern later. | Copy markdown job pattern in Automation OS phase. |
| Hooks | Deferred. | Need explicit future approval. | Do not add in v1 without new ADR. |
| Command Centre | Deferred. | None for v1. | Revisit after Automation OS. |
| Provider boundaries | Present and stricter. | Needs provider registry later. | Add only when real adapters are introduced. |

## Recommended Next Step

Run a focused parity hardening pass, not a rebuild.

Order:

1. Harden context matrix and skill registry against actual files.
2. Define exact project output layout.
3. Implement Tier 0 creator recall rules.
4. Add adapter/context/skill registry/runtime sync drift checks.
5. Then move into first Planning OS implementation slice.

## Success Criteria

InfluencerOS is ready for implementation when:

- every existing skill is registered,
- every registered skill has context-matrix coverage through an explicit skill row or the workflow row that invokes it,
- copied creator runtime skills are implemented and verified,
- root and creator memory policies are explicit,
- creator override rules are reflected in workspace docs,
- project output layout is deterministic,
- tests or checks catch adapter, registry, and schema drift.
