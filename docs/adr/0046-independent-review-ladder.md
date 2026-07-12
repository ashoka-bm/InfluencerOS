# ADR 0046: Independent Review Ladder

## Status

Accepted (operator decision, grilled and human-approved 2026-07-11/12).
Extends ADR 0024 and the control contract in `docs/gates-and-reviews.md`.

## Context

ADR 0024 defined the control vocabulary — Gate (human, blocking), Review
(advisory, emits a Review Record), Pass, Warning — and the first advisory
reviews. Everything shipped so far is project-scoped:
`schemas/review-record.schema.json` requires `project_id`, records live at
`projects/<slug>/reviews/`, and `review_role` covers only `hook_payoff`,
`creator_fit`, and `fact_check`.

The operating cadence model approved in this batch organizes creator
operations into four blocks — Creator Setup, Strategy, the Quarterly Planning
Cycle, and the Weekly Planning Cycle — each following one block contract:
draft, a research-and-review loop, human final approval, execution, ready
check. Every block needs an independent advisory judgment before its human
approval, and three of the four judge workspace-level artifacts (foundations,
strategy, Quarter Plans) that no Project owns. The loop also needs a bounded
convention for demanding missing evidence, and routine internal review,
validation, and drafting runs need a named authorization so they are never
confused with provider-gated work.

## Decision

1. **Four ladder reviews.** Establish an independent review ladder of four
   advisory reviews, one per cadence block, each run as a bounded sub-agent
   review per the `docs/gates-and-reviews.md` reviewer-independence contract
   (an independent reviewer fed an explicit packet, never the authoring
   conversation; `reviewer_execution` recorded):
   - **Setup Review** — inside Creator Setup: judges the text foundation and
     the auto-generated Avatar Image together, before fixes and the human
     Visual Continuity Plan approval.
   - **Strategy Review** — inside the Strategy block: judges the drafted
     creator strategy after the broad research that validates it, inside the
     research-and-review loop that precedes the human final approval granting
     `production_ready`.
   - **Quarterly Review** — the advisory judgment inside the Quarterly
     Planning Cycle: judges the draft Quarter Plan content (retrospective
     findings, per-Campaign research, the next-Quarter Campaign Concept set)
     inside the loop that precedes the one human approval over the whole
     Quarter Plan record.
   - **Concept Review** — inside the Weekly Planning Cycle: judges the
     promotion packages (the evidence-backed candidate Content Opportunities
     per Anchor Slot) before the human Concept Approvals promote the week's
     Projects.

   All four are advisory Reviews: they emit Review Records and never block.

2. **Workspace-level Review Record anchoring.** Extend the review-record
   contract with new `review_role` values for the ladder reviews and with
   workspace-level anchoring — the schema currently requires `project_id`,
   which workspace-scoped reviews cannot supply. Workspace-level Review
   Records get a home at the Creator Workspace root.

3. **Research Demand finding type and loop convention.** A Research Demand is
   a Review finding that names specific missing evidence the artifact needs
   before approval. In every block's research-and-review loop, reviews may
   emit Research Demands; the loop closes when a review issues no new
   Research Demands; at most two extra research rounds run; any leftover
   Demands attach to the block's human final approval as open questions.

4. **Standing internal sub-agent authorization.** Add to the operating rules
   a standing authorization for internal sub-agent work: reviews, validation,
   and drafting passes. It never covers provider calls, Gates, or waivers —
   those remain human-owned.

5. **Two-layer rule and promotion rule preserved.** The two-layer rule stays
   intact: every ladder review lives in the creative-advisory layer, and the
   blocking provider-safety `QualityReview` is untouched. Promoting any
   ladder review to blocking requires its own ADR, per the
   `docs/gates-and-reviews.md` promotion rule.

## Consequences

- `schemas/review-record.schema.json` and `docs/gates-and-reviews.md` change:
  new `review_role` values, `project_id` no longer required for
  workspace-anchored roles, and a workspace-root storage location beside the
  existing project-scoped one.
- The findings contract extends beyond the anchoring change: findings gain a
  machine-readable Research Demand marker (so "issues no new Research
  Demands" is computable from the Review Record, not from prose), and the
  workspace-level ladder reviews get an area vocabulary of their own in place
  of the project-scoped Content Beat Spine areas
  (hook/retain/payoff/cta/general).
- Each cadence block gets an independent judged read before its human final
  approval; no ladder review blocks, and the Gate inventory of
  `docs/gates-and-reviews.md` (Concept Approval, Provider Boundary) is
  unchanged — a block's human final approval is its exit, not a new Gate.
- Research Demands bound the loop: no block iterates indefinitely, and
  unresolved evidence gaps surface as explicit open questions on the human
  approval instead of disappearing.
- Standing internal sub-agent authorization removes per-run confirmation for
  advisory internal work while leaving every provider call, Gate, and waiver
  with the human.
- Quarterly Review and Concept Review land with the Planning Cycles, which
  are accepted targets, not yet shipped; Setup Review and Strategy Review
  land with the setup and strategy block work. This ADR creates the contract,
  not a build obligation beyond it.

## Open question settled

**Settlement (implementation):** Unresolved Research Demands get no new field
on approval records; instead, they remain findings flagged
`research_demand: "new"` or `research_demand: "carried_forward"` on the
terminal Review Record: the last record that
closes a block's research-and-review loop, either by issuing no new Demands or
by reaching the two-extra-round cap. A block has open questions at approval
time exactly when that terminal record carries one or more such findings;
the human approval references it and the conductor surfaces its remaining
Demands, avoiding
schema changes to the heterogeneous approval records.

For the two shipped ladder exits, the existing approval records carry the
terminal review reference: Visual Continuity Plan `selection_review` records
the Setup Review id, while the production readiness milestone records the
Strategy Review id. Workspace validation resolves both references under the
workspace review root and checks their roles.
