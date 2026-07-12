# ADR 0047: Quarter Plan Records

## Status

Accepted (operator decision, grilled and human-approved 2026-07-11/12).

## Context

The approved operating cadence model locks Creator Setup and Strategy as
one-time baselines and moves all recurring planning into two human-initiated
Planning Cycles. The Quarterly Planning Cycle needs a durable record of what
each cycle decided, and the locked baselines need a versioned amendment path
that does not reopen onboarding.

A Quarter is creator-relative: thirteen weeks anchored at the creator's
`production_ready` date and rolling thereafter, per-creator and not
calendar-aligned. The cycle is a human-initiated ritual, never OS-scheduled;
an overdue Quarter surfaces only as an advisory Warning (state staleness, not
cron), consistent with ADR 0025's event-not-clock stance. Its retrospective
consumes PerformanceSummaries and distilled creator lessons — the scheduled
consumer Improvement OS Loop A (ADR 0025) lacked.

ADR 0029 fixed the Campaign hierarchy and lifecycles but left Campaign
pause/complete/archive decisions without a default decision home, gave
Campaigns no duration expression, and deferred Campaign Revisions. The
glossary terms this ADR relies on (Quarter, Quarterly Planning Cycle, Quarter
Plan, Foundation Revision, Strategy Revision, Campaign Duration Target,
Research Demand) are committed in the CONTEXT.md Language section as accepted
targets.

## Decision

1. **Quarter Plan record.** Each Quarterly Planning Cycle produces one Quarter
   Plan record containing: the retrospective findings over the closing
   Quarter, the next Quarter's Campaign Concept set (new and re-confirmed),
   Campaign lifecycle decisions, Campaign Duration Target changes, the
   schedule shape, and any Foundation Revision or Strategy Revision proposals.
2. **One approval covers the whole plan.** A single human final approval over
   the Quarter Plan record closes the cycle. Research Demands left open after
   the cycle's research-and-review loop attach to that approval as open
   questions. This approval does not replace the Concept Approval Gate:
   Projects are still promoted only by Concept Approvals.
3. **Re-confirmation, not recreation.** Unchanged active Campaign Concepts
   carried into the next Quarter are re-confirmed in the Quarter Plan, not
   recreated. Re-confirmation rides the existing rule that an unchanged
   Concept may receive multiple Concept Approvals; a material change to
   tension, promise, audience, or hypothesis still creates a linked Concept
   per ADR 0029.
4. **Campaign lifecycle decision home.** The Quarterly Planning Cycle is the
   default home for Campaign pause, complete, and archive decisions. Ad hoc
   human lifecycle changes remain allowed mid-Quarter and are recorded by the
   next Quarter Plan.
5. **Foundation Revisions and Strategy Revisions.** Amendments to the locked
   Stage 1 and Stage 2 baselines happen only through a Quarterly Planning
   Cycle and produce versioned records: a Foundation Revision versions the
   locked creator setup foundation; a Strategy Revision versions the locked
   Content Strategy and schedule shape. Revisions are immutable and
   sequentially versioned, exactly one Revision is current, and prior Quarters
   retain the Revision that governed them. Readiness milestones never regress
   when a Revision lands.
6. **Campaign Duration Target.** Every Campaign declares a Duration Target — a
   target end date — at creation. It is required, unbounded in either
   direction, and a measurement hypothesis, never an auto-stop: a Campaign
   running past its target surfaces an advisory Warning and a retrospective
   question in the next cycle. Retargets happen through the Quarter Plan; a
   retarget is not a material identity change and never creates a new
   Campaign.
## Consequences

- Harmonization with the Creator Content Schedule contract (ADR-added
  reconciliation, not a separately grilled decision): the Quarter is a
  per-creator planning horizon, not a schedule window. The monthly
  `planning_period` contract — one declared monthly period with `monthly_mix`
  validation and explicit human approval metadata, landing in this batch — is
  unchanged. The Quarter Plan's schedule shape governs planning above that
  contract; schedule-shape amendments to the locked strategy land as Strategy
  Revisions.

- Campaign lifecycle transitions gain a durable, audited decision home;
  mid-Quarter ad hoc changes stay legal and are reconciled by the next plan.
- The Quarter Plan retrospective becomes the scheduled consumer of
  PerformanceSummaries and distilled creator lessons, closing the ADR 0025
  Loop A gap.
- The locked Stage 1/2 baselines become amendable without regressing
  readiness: lock-and-amend replaces in-place edits.
- Duration Targets stay advisory measurement hypotheses; nothing in this ADR
  adds a blocking gate, keeping the gates-and-reviews two-layer rule intact.
- Quarter Plan, Foundation Revision, Strategy Revision, and Campaign Duration
  Target are accepted targets: record contracts for the upcoming
  implementation, with the glossary already committed in CONTEXT.md.

## Amends

This ADR narrowly amends ADR 0029 by adding the required Campaign Duration
Target at Campaign creation and by naming the Quarterly Planning Cycle as the
default Campaign lifecycle decision home. All other ADR 0029 decisions —
hierarchy, lifecycles, objective vocabulary, identity-change rules — remain
active, and Campaign Revisions and Waves remain separately deferred.

Together with ADR 0044, this ADR also amends ADR 0028 Decision 10: strategy
and schedule records remain split, but Strategy Revisions (Decision 5) now own
the evolution of the locked Content Strategy and schedule shape, and the
Quarter Plan carries the schedule shape each cycle.
