# Reviews And Gates Pipeline Map

Last updated: 2026-07-11

## Purpose

This map shows every control point along the creator-to-output pipeline —
existing human gates, existing built reviews, and the proposed independent
sub-agent reviews (Setup Review, Strategy Review, Concept Review, and the
calibration-first anchor-image QualityReview) — placed by the rule that a
review sits immediately upstream of the approval it informs.

It corrects an earlier operator sketch in three ways: generated visual
reference assets are judged by the blocking QualityReview after the Visual
Continuity Plan approval, not by the pre-`foundation_ready` Setup Review;
Campaign Concept definition moved from the Strategy lane to the Concept lane;
and broad research now appears between `strategy_ready` and
`production_ready`, distinct from rolling focused per-slot research.

The proposed reviews in this map are design intent, not built behavior. The
built controls are the two human pipeline gates, the four readiness
milestones, `review-hook-payoff`, and the blocking QualityReview.

## Map Type

Workflow map with five vertical swimlanes read left to right, flow
top-to-bottom inside each lane:

1. **Creator Setup** (to `foundation_ready`)
2. **Strategy** (to `strategy_ready`)
3. **Research** (to `production_ready`)
4. **Concept** (to the Concept Approval Gate)
5. **Production** (per project, to Output Package)

Color legend: blue = advisory bounded sub-agent review, orange = human gate
or milestone approval, red = blocking review, white = artifact/step.

## Excalidraw Status

- Scene ID: `7piyPGJBmjR` (`https://app.excalidraw.com/s/3g0OtZhQ70R/7piyPGJBmjR`), collection `Main`.
- Local screenshot: `.tmp/reviews-and-gates-pipeline-excalidraw.png` (disposable).
- Last visual verification: 2026-07-11; screenshot inspected (lane layout,
  node color sequence per lane, arrow bindings, elbow cross-lane handoffs)
  and key labels verified through scene search (`Setup Review`,
  `Calibration QualityReview`, `Concept Approval Gate`, `strategy_ready`,
  `Output Package`).
- Renderer caveat: the API screenshot renderer drops text labels (same
  caveat as the 2026-07-01 architecture map); the scene contains editable
  shape labels confirmed via `search_scene_content`. Inspect the board in
  the Excalidraw app for full-text review.

## Source Files Inspected

- `docs/gates-and-reviews.md`
- `docs/pipeline-contract.md`
- `docs/creator-workspace-structure.md`
- `skills/influencer-os/SKILL.md`
- `skills/create-influencer/SKILL.md`
- `schemas/readiness-gates.schema.json`
- `influencer_os/readiness.py`
- Artist OS reference: `~/.claude/skills/artist-os/SKILL.md` (serial
  bounded-sub-agent review pattern and calibration-first precedent)

## Open Questions

- Review Record anchoring for pre-project reviews: workspace-level
  `reviews/` home and `review_role` extension need an ADR (records
  currently require a `project_id`).
- The calibration-first anchor-image pass splits the ADR 0043 bounded
  generation pass into calibration + remainder; needs an ADR amendment.
- Whether milestone flips should mechanically require a Review Record or
  waiver (via the `blockers[]` convention) or stay advisory-only.
