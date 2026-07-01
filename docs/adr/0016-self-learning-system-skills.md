# ADR 0016: Self-Learning System Skills

## Status

Accepted

## Context

Self-improvement is the highest-priority capability for InfluencerOS. In the Agentic OS reference the loop ships as two model-invoked system skills, not as automation:

- `meta-wrap-up` reviews deliverables, collects feedback, appends per-skill entries to `context/learnings.md`, edits skills directly, finalizes daily memory, reconciles the skill registry, and promotes durable facts to `context/MEMORY.md`.
- `meta-memory-write` performs bounded, deduplicated writes to `context/MEMORY.md`.

Those skills trigger off their own `description`. The Stop hook and cron jobs only automate *when* they run; they are redundancy on top of the manual skill layer, not the mechanism itself.

InfluencerOS copied the destinations of this loop but not its writer. `context/learnings.md` and `docs/os-construction/process-learnings.md` are empty scaffolds, no `SKILL.local.md` exists on disk, and no skill has a step that writes learnings. As a result the promotion pipeline defined in ADR 0014 cannot fire, because its first step — capture feedback — has no executing agent. This is documented in `docs/os-construction/adversarial-review.md`.

Roadmap Phase 2 "Learning OS" is correctly scoped to creator *performance* learning (`distill-creator-learning`), which genuinely depends on unbuilt Output Package and Analytics schemas. The *system* skill-improvement loop has no such dependency and was incorrectly swept into that deferral. It is deliverable now, local-first, with no hooks, cron, PGLite, or Command Centre.

## Decision

InfluencerOS will implement the self-improvement loop as local-first, model-invoked system skills, independent of hooks and cron.

Add two system skills under repo `skills/` (kebab-case, no category prefix, per ADR 0017):

- `skills/wrap-up/SKILL.md` — adapts `meta-wrap-up`: review deliverables (`git status`), collect feedback, then apply changes: append dated per-skill entries to `context/learnings.md`, record repo-level process lessons in `docs/os-construction/process-learnings.md`, fix `SKILL.md`/`SKILL.local.md` directly when feedback points to a method, finalize the daily memory block, reconcile `docs/os-construction/skill-registry.md` and `docs/os-construction/context-matrix.md`, and promote durable facts to `context/MEMORY.md`. It commits only when the user asks.
- `skills/memory-write/SKILL.md` — adapts `meta-memory-write`: add, replace, or remove one durable fact in `context/MEMORY.md`, deduplicated, within an enforced byte cap, then confirm.

Additional requirements:

- Behavior-changing skills (`influencer-os`, `create-influencer`, and future producer skills) carry a `## Rules` section (dated entries read before each run) and a `## Self-Update` section (edit the applicable `SKILL.local.md` when the user flags an issue).
- Ship at least one worked `SKILL.local.md` example so the override load order is exercisable and testable.
- `AGENTS.md` names the wrap-up trigger so any runtime can invoke the loop by description without a hook.
- The `context/MEMORY.md` cap is enforced by a pre-write byte check.

Hook and cron automation (Stop-hook invocation, skill auto-commit, memory-distill cron) remain deferred. They only automate when these same skills run and can be layered on later without redesign.

This loop is Phase 0/1 system capability. It must not be folded into Phase 2 Learning OS.

## Consequences

- The self-improvement loop becomes functional in v1 without reopening the deferred hooks or cron.
- `context/learnings.md`, `process-learnings.md`, and `SKILL.local.md` stop being dead files; ADR 0014's promotion pipeline gains its missing writer.
- `context/MEMORY.md` stays bounded and durable.
- Future auto-commit and cron distillation can wrap these skills without changing them.
- Creator-scoped performance learning (`distill-creator-learning`) remains a separate Phase 2 concern and is not affected by this decision.
