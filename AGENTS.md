# InfluencerOS Agent Rules

These rules apply to agents building or running InfluencerOS.

## Source Of Truth

Read `CONTEXT.md` before changing product language.

Use these product docs as durable references:

- `docs/os-construction/prd.md`
- `docs/os-construction/roadmap.md`
- `docs/os-construction/short-term-plan.md`
- `docs/os-construction/repository-map.md`
- `docs/os-construction/architecture-map.md`
- `docs/os-construction/agentic-os-alignment.md`
- `docs/os-construction/agentic-os-copy-plan.md`
- `docs/os-construction/agentic-os-parity-plan.md`
- `docs/os-construction/divergence-test.md`
- `docs/os-construction/visual-architecture-maps.md`
- `docs/os-construction/context-matrix.md`
- `docs/os-construction/skill-registry.md`
- `docs/os-construction/process-learnings.md`
- `docs/os-construction/adversarial-review.md`
- `ARCHITECTURE.md`
- `docs/pipeline-contract.md`
- `docs/provider-boundary.md`
- `skills/influencer-os/SKILL.md`
- `schemas/`

## Read Order

For architecture, roadmap, workflow, or product-scope work, read:

1. `CONTEXT.md`
2. `docs/os-construction/prd.md`
3. `docs/os-construction/roadmap.md`
4. `docs/os-construction/short-term-plan.md`
5. `docs/os-construction/repository-map.md`
6. `docs/os-construction/architecture-map.md`
7. `docs/os-construction/agentic-os-alignment.md`
8. `docs/os-construction/agentic-os-copy-plan.md`
9. `docs/os-construction/agentic-os-parity-plan.md`
10. `docs/os-construction/divergence-test.md`
11. `docs/os-construction/visual-architecture-maps.md`
12. `docs/os-construction/context-matrix.md`
13. `docs/os-construction/skill-registry.md`
14. `ARCHITECTURE.md`
15. `docs/pipeline-contract.md`

## Product Invariant

Every Content Idea, Micro-Journey Video Plan, Base Video Generation Plan, and Output Record must trace back to:

- Creator Profile,
- current Social Research Pack evidence,
- Video Understanding Pack evidence when real videos were analyzed,
- the chosen Content Idea,
- the Applied Social Template when one is used,
- the intended audience response,
- the Micro-Journey Video Plan,
- the Base Video Generation Plan when generation is planned,
- and the Output Record when an Output Artifact exists.

## Operating Rules

- Treat `/Users/ashokaji/code/External repos/Agentic Academy/agentic-os` as the Agentic OS architecture reference. If InfluencerOS needs to diverge from that reference, surface the divergence and record the architectural decision before coding it.
- Treat v1 as local-first. Command Centre, hosted execution, hooks, cron, and anywhere-access are deferred until explicitly approved.
- Keep workflow boundaries deterministic: name the inputs, outputs, schema or template, provenance links, validation, and approval gate.
- Use test-driven, context-driven, and domain-driven development for behavior changes.
- Treat root `context/` and `brand_context/` as InfluencerOS first-party OS persona context. Treat Creator Workspace context as creator-specific and private.
- Before adding or changing skills, check `docs/os-construction/skill-registry.md` and `docs/os-construction/context-matrix.md`.
- Root `skills/<skill-name>/SKILL.md` files are the baseline skill source. Creator Workspaces run copied skills from `.claude/skills/<skill-name>/SKILL.md`; refresh them with `python3 -m influencer_os sync-creator-runtime <creator-workspace>` and preserve creator `SKILL.local.md` files.
- InfluencerOS v1 targets universal short-form vertical video. Do not add platform-specific adapters, post-production treatments, publishing, scheduling, or analytics unless explicitly requested.
- Audience and niche are creator-profile inputs. Do not invent or redefine them unless the user asks.
- Research is time-sensitive. Date the research, cite sources, and keep trend claims tied to evidence.
- Do not make provider-backed image, video, audio, or render calls without explicit user approval for the exact call or approved batch.
- Drafting research packs, ideas, plans, prompts, shot lists, and generation plans is allowed without provider approval.
- Do not commit user-provided media, generated works, private creator references, secrets, or API keys.
- Prefer the smallest change that advances the first slice.
- When a session produces deliverables or the user signals wrap-up, run the `wrap-up` skill to capture learnings, self-correct skills, and reconcile the skill registry and context matrix (ADR 0016).

## Git Rules

- Do not commit unless the user asks.
- Prefer branch prefixes `feature/`, `fix/`, `chore/`, or `refactor/`.
- Never force-push a shared branch without explicit approval.
