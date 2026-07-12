# ADR 0025: Phase 4 Is Improvement OS — Feedback Loops Before Temporal Scheduling

## Status

Accepted (operator decision, 2026-07-06).

Decision 4 amended by ADR 0044: the human-initiated Quarterly Planning Cycle
is permitted calendar-shaped reflection; automation stays event-triggered.

## Context

Phase 4 was "Automation OS": scheduled creator operations (research refresh,
project creation, analytics ingestion) after planning, learning, and
generation stabilized. When Phase 3 closed (2026-07-06), all three Phase 4
entry criteria passed — but three facts made the temporal framing low-value:

- The operator decided v1 ships no live scheduler (local-first holds; cron
  stays deferred).
- The scheduled-research capability is gated behind the manual
  research-intelligence loop being exercised with a live connector (ADR 0022
  "run 2", needs `OPENAI_API_KEY`) against real creator data — neither exists
  yet.
- Current Creator Workspaces are disposable fixtures; there are no real
  creator operations to schedule.

A grilling session on 2026-07-06 surfaced the actual binding need. The
operator named two feedback loops the OS must close, and the requirement that
improvement iterate against clear true/false statements, "removing the
ambiguity in what is good and what is bad":

1. **Performance Delta loop** — evaluate the theory of what was created
   against how it actually performed, feeding Creator Memory and the next
   research/idea cycle.
2. **Production Quality loop** — learn from creation friction (weak prompts,
   failed or rejected assets) and update skills and routines so asset quality
   rises over time.

Both need capture, distillation-with-compaction (anti context-rot), and a
trigger — and the operator's own words closed the scheduling question: "we
don't necessarily need to schedule that, but it needs to be triggered
somehow." The automation primitive the OS needs first is **event-triggered
reflection**, not clock-triggered execution.

Key existing substrate discovered during the session: the `system-event` and
`automation-run` schemas landed in ADR 0020 slice 3 but nothing writes them;
the Creative Performance Map (ADR 0006) already records per-stage
`intended_effect` and `primary_metrics` (the theory), but as prose that can
never be scored true or false; the declare-then-attest shape already exists
locally in three places (ResearchSearchPlan → ResearchSourceYield, run
`outputs` reconciliation, GenerationApprovalRecord exact-request equality).

## Decision

Rescope Phase 4 as **Improvement OS**. Temporal scheduling (markdown job
definitions, dry-run runners, any live scheduler) moves to the roadmap's
Deferred section with its own reopen conditions. Historical docs that say
"Phase 4 Automation OS" refer to this phase.

The phase closes the two loops under one discipline — nothing improves on
vibes; every judgment must be reducible to a criterion that can be cited,
counted, and refuted:

1. **Declare-then-attest is the general capture discipline.** Intent recorded
   before work, attestation after, mechanical reconciliation against durable
   side effects at rest. Intent-vs-attestation deltas are learning signal;
   attestation-vs-disk deltas are integrity failures and fail closed.
2. **Capture is structured events, never thread mining.** Mechanical traces
   wherever a writer already touches disk, plus skill-reported incident and
   rejection events with recurrence keys on the existing system-event ledger.
   Session transcripts are not imported: verdicts are durable, rejected
   drafts stay ephemeral.
3. **The Rubric Ratchet converts taste into criteria.** A Production Rubric
   of binary, scoped (OS-level craft vs creator-level boundary) criteria;
   every rejection must cite an existing criterion or mint a new one;
   unclassified rejections are allowed but their accumulation signals a
   rubric gap. Criterion ids double as recurrence keys, so bracketing
   recurring problems is counting.
4. **Reflection is event-triggered.** Threshold crossings (same-key
   recurrences, unprocessed events, unclassified accumulation) surface an
   advisory warning; the human review rides this trigger — distillation
   proposes, the human approves what lands in skill files (ADR 0016 loop,
   mechanically triggered). No clock, no scheduler.
5. **Skill updates carry falsifiable improvement claims.** Each distilled
   update names its target criterion and expected violation-rate change and
   is verified against subsequent runs; a refuted claim reopens the fix.
6. **Predictions become falsifiable.** The Creative Performance Map's
   per-stage intent gains an optional quantified prediction (metric,
   comparator, threshold); performance summaries score each stage confirmed,
   refuted, or unmeasurable. Refuted guesses are the learning.
7. **Criteria mature on a ladder — advisory → proven → blocking.** Promotion
   into the blocking quality checklist follows the gates-and-reviews ADR
   checklist; until promoted, everything Improvement OS adds is advisory and
   can never halt the pipeline.
8. **The rubric starts near-empty.** Seeded only from the existing
   quality-review categories and creator boundaries; the ratchet grows the
   rest from real rejections, not pre-authored guesses.

Scoping guards carried forward from the 2026-07-06 decisions: no live
scheduler ships in v1; scheduled jobs, if ever reopened, cannot promote
ideas, create projects, or call providers without human approval (PRD Out of
Scope); the live-connector research precondition continues to gate any future
scheduled-research capability.

## Consequences

- The draft automation-os implementation plan (uncommitted) is superseded by
  `docs/workflows/improvement-os-implementation-plan.md`.
- The dormant `system-event`/`automation-run` schemas gain their first
  writers; the events ledger becomes the incident/rejection substrate.
- Loop B (Production Quality) is exercisable as soon as real generation runs
  begin — it needs creation attempts, not audience data. Loop A's comparison
  semantics activate when real analytics exist, but prediction capture starts
  early so deltas have a baseline.
- Phase 2 Learning OS built capture → distill → store → retrieve; Improvement
  OS closes the loop by making learning change behavior (skills, criteria,
  predictions) under falsifiable claims.
- "Automation OS" skill-registry categories and historical ADR/plan mentions
  are left as history; live docs (roadmap, PRD, progress, README) now say
  Improvement OS.
