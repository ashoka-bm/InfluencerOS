---
name: quarterly-planning-cycle
description: "Use to run the human-initiated Quarterly Planning Cycle: retrospective, per-Campaign research, next-Quarter Campaign Concepts, the advisory Research Demand loop, and the one human approval that produces a Quarter Plan (ADR 0044 Decision 8, ADR 0047)."
dependencies:
  - review-quarter-plan
  - create-research-findings
  - distill-creator-learning
---

# Quarterly Planning Cycle

You conduct the Quarterly Planning Cycle — Stage 3 of the operating cadence
(ADR 0044). It is a human-initiated ritual, never OS-scheduled: the overdue-
Quarter Warning surfaced by `validate workspace` is state staleness, not a
trigger. The cycle runs the uniform block contract — draft, research-and-review
loop, one human final approval, execute, ready check — and produces exactly one
Quarter Plan record. No new record type; no provider calls.

The Quarter Plan is built ONLY through
`python3 -m influencer_os scaffold quarter-plan` (ADR 0042); never hand-author
the record. The constructor anchors the Quarter to the creator's
`production_ready` date, derives the window, validates, and writes.

## Deterministic Block Contract

Each phase names inputs, outputs, schema, provenance link, validation command,
and whether it is a human gate.

### Phase A — Retrospective

- Inputs: every PerformanceSummary in the closing Quarter window
  (`projects/*/performance-summary.json`) plus distilled creator lessons in
  `memory/learnings.md`. Optionally refresh the lessons via
  `Skill(distill-creator-learning)` before reading.
- Output: retrospective findings, `performance_summary_ids`, and free-text
  `lesson_refs` written into the Quarter Plan seed.
- Schema: `schemas/quarter-plan.schema.json` (`retrospective`).
- Provenance: `performance_summary_ids` resolve to real PerformanceSummaries at
  rest; `lesson_refs` are free-text provenance pointers into `memory/learnings.md`
  and are not resolved by validation.
- Validation: `python3 -m influencer_os validate workspace <creator-workspace>`.
- Human gate: no.

### Phase B — Per-Campaign research

- Inputs: the closing Quarter's active Campaigns and their Content Pillars.
- Output: Research Findings and Research Evidence validating the next Quarter's
  direction, via `Skill(create-research-findings)`.
- Schema: research-findings and research-evidence (owned by that skill).
- Provenance: findings cite dated, sourced evidence.
- Validation: `python3 -m influencer_os validate research <creator-workspace>`.
- Human gate: no.

### Phase C — Draft the next-Quarter plan content

- Inputs: retrospective findings, per-Campaign research, current Campaigns.
- Outputs, each built through a constructor, never hand-authored:
  - Campaign Concept set — new Concepts via
    `python3 -m influencer_os scaffold campaign-concept`; unchanged active
    Concepts are re-confirmed with disposition `re_confirmed`, NOT recreated
    (ADR 0047 D3).
  - Campaign lifecycle decisions — pause, complete, archive, or continue
    (the default decision home, ADR 0047 D4).
  - Campaign Duration Target changes — retargets through the Quarter Plan.
  - Schedule shape for the next Quarter.
  - Any Foundation/Strategy Revision proposals. Derive each proposed id from
    the next constructor sequence (`foundation_revision_<creator>_NNN` or
    `strategy_revision_<creator>_NNN`) and put that id in the draft packet, but
    do NOT construct the Revision yet. Revisions require the approved Quarter
    Plan and are constructed in Phase F. The Quarter Plan stamps only the
    already-current governing Revision ids.
- Schema: `schemas/quarter-plan.schema.json`.
- Provenance: every `campaign_concept_id`, `campaign_id`, and
  `performance_summary_id` in the plan resolves to a record on disk (enforced at
  rest by cadence validation).
- Validation: `python3 -m influencer_os validate workspace <creator-workspace>`.
- Human gate: no (drafting only).

### Phase D — Research Demand loop

- Inputs: the draft Quarter Plan content packet.
- Output: one Quarterly Review Record per round via
  `Skill(review-quarter-plan)`. The loop closes when a Review issues no new
  Research Demands; run at most two extra research rounds. Remaining Demands
  become open questions on the human approval — the Review never blocks.
- Schema: `schemas/review-record.schema.json` (role `quarterly`).
- Provenance: the terminal Review id is stamped as the plan's
  `terminal_review_record_id`.
- Validation: `python3 -m influencer_os validate workspace <creator-workspace>`.
- Human gate: no (advisory Review).

### Phase E — One human final approval

- Inputs: the whole draft Quarter Plan plus any open Research Demands.
- Output: the human final approval recorded as `approval.approved_by: user`,
  then the approved plan is constructed with
  `python3 -m influencer_os scaffold quarter-plan --seed <seed.json> --creator-workspace <creator-workspace>`.
  This does NOT replace Concept Approvals — Projects are still promoted only
  by Concept Approvals in the Weekly cycle.
- Schema: `schemas/quarter-plan.schema.json` (`approval`).
- Provenance: `terminal_review_record_id` names the Quarterly Review that gated
  the plan.
- Validation: the constructor validates; then
  `python3 -m influencer_os validate workspace <creator-workspace>`.
- Human gate: YES — the block's single human exit.

### Phase F — Execute the approved plan

- Inputs: the approved Quarter Plan and the exact decisions it records.
- Outputs:
  - Apply each approved Campaign lifecycle decision and Duration Target change
    to its existing canonical `campaigns/<campaign-id>/campaign.json` record.
  - Apply the approved schedule shape to the canonical strategy/schedule
    records; do not create a second schedule source of truth.
  - Construct each approved Revision proposal now, never before the Quarter
    Plan exists, using
    `python3 -m influencer_os scaffold foundation-revision --seed <seed.json> --creator-workspace <creator-workspace>`
    or
    `python3 -m influencer_os scaffold strategy-revision --seed <seed.json> --creator-workspace <creator-workspace>`.
    Each Revision seed names the approved `quarter_plan_id`; the constructor's
    derived Revision id must exactly equal the proposal id recorded by the
    plan. A mismatch halts execution as an integrity error.
- Schema: `schemas/campaign.schema.json`,
  `schemas/creator-content-schedule.schema.json`, and the applicable
  Foundation/Strategy Revision schema.
- Provenance: the approved Quarter Plan is the decision record; each Revision
  points back through `quarter_plan_id`.
- Validation: validate each changed record at its public record seam, then run
  `python3 -m influencer_os validate workspace <creator-workspace>`.
- Human gate: no; execution may apply only the already-approved decisions.

### Phase G — Ready check

- Inputs: the approved Quarter Plan and all canonical records changed in Phase F.
- Output: no new record. Confirm every lifecycle decision, Duration Target
  change, schedule-shape change, and proposed Revision is applied exactly once;
  confirm every constructed Revision id matches its proposal id.
- Schema: no new schema; this checks the records named above.
- Provenance: resolve every executed change back to the approved Quarter Plan.
- Validation:
  `python3 -m influencer_os validate workspace <creator-workspace>` must pass;
  rebuildable Campaign and calendar projections must reflect the approved
  changes. Do not declare the cycle ready while any approved change is absent.
- Human gate: no.

## Slice Boundary

This conductor runs the loop, holds the human approval, executes that approval,
and performs the ready check. The Quarterly Review verdict is advisory and
halts nothing. Weekly-cycle work — opportunity-queue promotion and Concept
Approvals — is out of scope (slice 6).

## Rules

- No provider calls anywhere in the cycle.
- Build every record through its constructor (`scaffold ...`); never hand-author.
- Re-confirm unchanged active Concepts; do not recreate them.
- The overdue-Quarter Warning is state, never a trigger; a human starts the cycle.
- A `block` recommendation from the Quarterly Review is advice, not an auto-stop.
- 2026-07-12: Phase C/E/F/G now place the approved Quarter Plan before its
  proposed Revision constructors and require execution plus a ready check.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md quarterly-planning-cycle "<lesson>"`,
run from the InfluencerOS repo root: repo paths (`docs/`, `schemas/`,
`context/learnings.md`) resolve from there, never from a Creator
Workspace runtime copy.
