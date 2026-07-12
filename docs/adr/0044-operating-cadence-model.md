# ADR 0044: Operating Cadence Model

## Status

Accepted (operator decision, grilled and human-approved 2026-07-11/12).

## Context

InfluencerOS had onboarding readiness milestones (ADR 0028) and event-triggered
improvement loops (ADR 0025), but no defined operating cadence: no rule for how
setup and strategy get amended once accepted, no recurring ceremony that
consumes PerformanceSummaries and distilled creator lessons (Improvement OS
Loop A captured them but nothing was scheduled to read them), and no defined
rhythm that turns an accepted strategy into each week's Concept Approvals.

A grilling session produced an operating cadence model of four blocks under one
uniform contract. The glossary terms it introduces (Planning Cycle, Quarter,
Quarterly Planning Cycle, Weekly Planning Cycle, Quarter Plan, Foundation
Revision, Strategy Revision, Research Demand, Reactive Slot, Monitor Note,
Avatar Image, Campaign Duration Target) are committed in `CONTEXT.md` as
accepted targets. This umbrella ADR records the model; stage-level detail
follows the same contract.

## Decision

1. **Four blocks.** The operating cadence is four blocks: Stage 1 Creator Setup
   (runs once, then locked), Stage 2 Strategy (runs once, then locked), Stage 3
   Quarterly Planning Cycle (once per Quarter), and Stage 4 Weekly Planning
   Cycle (weekly).
2. **Uniform block contract.** Every block runs: draft -> research-and-review
   loop -> human final approval -> execute -> ready check. Reviews inside a
   block are advisory bounded sub-agent reviews per the
   `docs/gates-and-reviews.md` reviewer-independence contract; the human final
   approval is the block's exit. A block exit is a readiness or plan decision,
   not a pipeline Gate: the Gate inventory of `docs/gates-and-reviews.md`
   (Concept Approval, Provider Boundary) is unchanged. One recorded exception
   to the contract's ordering: Stage 1's Avatar Image auto-generation is the
   single execution step that precedes its block's review and human final
   approval, per ADR 0045.
3. **Research Demand loop.** A Review may emit Research Demands — findings
   naming specific missing evidence. The loop closes when a Review issues no
   new Research Demands, capped at two extra research rounds; any remaining
   Demands attach to the human approval as open questions. The finding
   contract and loop convention are owned by ADR 0046.
4. **Creator-relative Quarter.** A Quarter is a creator-relative planning
   horizon of thirteen weeks, anchored at the creator's `production_ready` date
   and rolling thereafter. Quarters are per-creator, not calendar-aligned.
5. **Cycles are human-initiated; staleness is a Warning.** Planning Cycles are
   human-initiated rituals, never OS-scheduled. An overdue Quarter surfaces
   only as an advisory Warning that states staleness — state observation, not
   cron. In the Weekly Planning Cycle, slots inside the coming week that are
   still unresearched or `candidates_ready` draw a Warning. This narrowly
   amends ADR 0025 Decision 4: improvement automation stays event-triggered
   ("no clock, no scheduler" holds for the OS), while the Quarterly Planning
   Cycle is the one calendar-shaped reflection ritual, run by the human.
6. **Lock-and-amend.** Stages 1 and 2 produce locked baselines. Amendments
   happen only through a Quarterly Planning Cycle and produce versioned
   Foundation Revisions and Strategy Revisions: immutable sequential versions,
   exactly one current, prior Quarters retaining the Revision that governed
   them. Readiness milestones never regress when a Revision lands. The
   Revision record contract is owned by ADR 0047.
7. **Strategy block exit is `production_ready`.** The Strategy block runs
   creator strategy -> calendar scaffold (the internal human checkpoint on the
   scaffold projection stays) -> broad research validating the strategy ->
   updates -> Strategy Review -> the Research Demand loop -> human final
   approval, which is `production_ready`. `strategy_ready` becomes an internal
   checkpoint inside the block, no longer a separate onboarding page or stage
   boundary.
8. **Quarterly Planning Cycle produces one Quarter Plan.** The cycle runs a
   retrospective over the closing Quarter (consuming PerformanceSummaries and
   distilled creator lessons — the scheduled consumer Improvement OS Loop A
   lacked), per-Campaign research, next-Quarter Campaign Concepts, and the
   Research Demand loop, ending in one human approval over the whole Quarter
   Plan record: retrospective findings, the Campaign Concept set (new plus
   re-confirmed — unchanged active Concepts are re-confirmed, not recreated,
   under the existing multiple-Approvals-per-Concept rule), Campaign lifecycle
   decisions (the default home for pause/complete/archive; ad hoc human
   changes mid-Quarter are allowed and recorded by the next Quarter Plan),
   Campaign Duration Target changes, schedule shape, and Revision proposals.
   The Quarter Plan record contract is owned by ADR 0047.
9. **Weekly Planning Cycle produces only existing Concept Approvals.** The
   weekly block runs focused `scheduled_needs` research on the week's scheduled
   Campaign Concepts, verifies or adjusts them, drafts 2-3 evidence-backed
   candidate Content Opportunities per Anchor Slot, runs the advisory Concept
   Review over the promotion packages, and ends in the human Concept Approvals
   that promote the week's Projects. No new record type: the finalization is
   the batch of existing Concept Approvals. Weekly research maintains
   watchlist Monitor Notes.
10. **News lane is accepted-target vocabulary only.** Reactive Slot, Monitor
    Note, and the Reactive Campaign are accepted targets with no
    build obligations in this batch. A fast-path Concept Approval never skips
    the human gate; speed comes from the Reactive Campaign,
    pre-chosen templates, and the reserved slot.

## Open question settled (slice 6)

**Settlement (implementation):** The Weekly Planning Cycle introduces no new
promotion path. Candidate Content Opportunities per Anchor Slot are ordinary
ADR 0031 Content Opportunities promoted through the shipped assignment model:
the human-selected Opportunity is assigned to an owning Campaign Concept via
`scaffold campaign-concept`, then `approve-concept` stages and commits the
Concept Approval. Alternatively, an Anchor Slot owned by one of the week's
scheduled Campaign Concepts may select that Concept directly. The shipped
`approve-concept` slot gate is the reconciliation seam: it accepts either the
approved Concept id or the approved Concept's `source_content_opportunity_id`,
backed by the exact completed `scheduled_needs` run. The ADR 0031 invariant
"no Concept Approval without an owning Campaign Concept" is preserved.

Concept Review ships as `review-concept-promotion` with workspace review areas
and fail-closed packet and queue-provenance validation. It writes one existing
Review Record per Anchor Slot through `scaffold review-record`, covering all 2-3
candidates while the schedule is still `candidates_ready`, before human topic
selection or assignment. The constructor enforces those mutable packet
preconditions; the persisted record is a point-in-time audit whose at-rest
validation does not depend on later slot or queue status. Its findings may carry Research Demand
markers, but the record carries no `research_demand_loop` lineage object:
weekly planning has no multi-round loop, the terminal ConceptApproval record is
unchanged, and this slice introduces no record type. Monitor Note maintenance
is research-narrative conductor prose only; Reactive Slot, Reactive Campaign,
triggered-note consumption, and fast-path approval remain deferred.

- **Settlement (implementation — Concept Review wiring):** `concept` is a
  built workspace-scoped Review role whose required source skill is
  `review-concept-promotion`; it remains advisory.
- **Settlement (implementation — area and packet contract):** Concept Review
  reuses workspace areas (`evidence`, `strategy`, `audience`, `general`), and
  its skill requires resolved Creator Profile, schedule, all candidate
  Opportunity queue entries for one named Anchor Slot, Research Findings, and
  Evidence refs without inventing a weekly packet artifact or record type.
- **Settlement (implementation — coming week):** the staleness Warning window
  is `[today, today + 6 days]` inclusive and applies only to open/reserved slots
  still `unresearched` or `candidates_ready`.
- **Settlement (implementation — conductor dependencies):** the Stage 4
  conductor depends exactly on `create-research-findings`,
  `manage-opportunity-queue`, `review-concept-promotion`, and `approve-concept`;
  Campaign Concept assignment remains the `scaffold campaign-concept`
  constructor rather than a skill dependency.

## Consequences

- The two-layer control rule (advisory creative, blocking provider-safety) and
  the promotion rule in `docs/gates-and-reviews.md` stay intact; every review
  this model adds is advisory.
- Onboarding collapses to two locked blocks and two recurring cycles; the
  four-page stage framing of ADR 0028 gives way to block exits, with
  `strategy_ready` internal to the Strategy block.
- The Quarterly retrospective gives PerformanceSummaries and distilled creator
  lessons their scheduled consumer, closing the gap ADR 0025's Loop A left
  open — without adding a scheduler.
- The Weekly Planning Cycle ships on existing records; no new approval
  hierarchy or finalization record type is introduced.
- Foundation and Strategy Revisions make locked baselines amendable without
  in-place edits or readiness regression.
- News-lane terms exist in the glossary only; nothing in the current
  implementation may treat them as obligations.

## Amends

- **ADR 0028 Decision 1:** the workspace status enum is unchanged, but
  `strategy_ready` survives with amended meaning: it remains a recorded
  workspace status and is now an internal checkpoint inside the Strategy
  block, not a separate onboarding page or stage boundary. Its Decision 1
  claim that strategy "does not require fixed publication dates" gives way to
  Decision 17's relocated scaffold check below.
- **ADR 0028 Decision 3:** broad research validating the strategy moves inside
  the Strategy block, before the Strategy Review and the human final approval.
- **ADR 0028 Decision 4:** `production_ready` is the Strategy block's exit
  (the human final approval); the calendar scaffold and its internal human
  checkpoint sit inside the block rather than a separate calendarization
  stage.
- **ADR 0028 Decisions 7 and 8:** the `strategy` readiness milestone and its
  recorded state survive, but the milestones that close a block are no longer
  purely deterministic checks: `foundation_ready` flips on the human ready
  check that closes Creator Setup (ADR 0045), and `production_ready` is
  granted by the Strategy block's human final approval. These block-exit
  approvals remain readiness decisions, not pipeline Gates.
- **ADR 0028 Decision 17:** the blocking stage-claim check for the schedule
  scaffold relocates with the calendar scaffold: an approved
  `content-schedule.json` is now required at `strategy_ready` (inside the
  Strategy block) instead of first appearing at `production_ready`.
- **ADR 0028 Decision 10:** strategy and schedule records remain split, but
  quarter-level planning now owns their evolution — schedule shape belongs to
  the Quarter Plan, and strategy changes land as Strategy Revisions through
  the Quarterly Planning Cycle.
- **ADR 0025 Decision 4:** reflection automation remains event-triggered; the
  human-initiated Quarterly Planning Cycle is the one calendar-shaped ritual,
  and an overdue Quarter surfaces only as an advisory Warning.

All other ADR 0028 and ADR 0025 decisions remain active.
