---
name: review-strategy
description: "Use for the Strategy Review trigger: an advisory bounded sub-agent review inside the Strategy block before the human approval granting production_ready (ADR 0046)."
---

# Review Strategy

You run the Strategy Review — an advisory cadence Review (ADR 0046). Follow
`docs/gates-and-reviews.md`; write one workspace-root
`reviews/<review_record_id>.json` validating against
`schemas/review-record.schema.json`.

## Independence

Review an artifact you did not author. The conductor gives you only this
explicit packet, never the authoring conversation:

- drafted `content-strategy.json`,
- approved content-schedule/calendar scaffold,
- broad Research Findings and Research Evidence that validate the strategy,
- Creator Profile.

Run after broad research and before the human final approval that grants
`production_ready`. Record `reviewer_execution.source_skill:
"review-strategy"` and `execution_mode: bounded_sub_agent`. If that path is
unavailable, use `fallback_separated_pass` with a truthful `fallback_reason`.

## What To Judge

Findings use only: `strategy`, `evidence`, `schedule`, `positioning`,
`audience`, and `general`. A finding may set `research_demand: "new"` when it
names specific missing evidence required before approval, or
`"carried_forward"` only when repeating an unresolved Demand from an earlier
review.

## Record Rules

- Set `review_role: strategy`, with the Creator Profile id as the workspace anchor.
- Never include `project_id` or `concept_approval_id`.
- `artifact_refs` are workspace-relative paths that resolve.
- `approval_status` is an advisory recommendation (`approve`, `revise`, or
  `block`) and halts nothing. State the recommendation aloud to the user.

## Slice Boundary

The Strategy-block conductor reorder, the Research Demand loop with its
two-extra-rounds cap, and the `strategy_ready`/`production_ready` checkpoints
land in slice 3 (ADR 0044 Decision 7). This skill only produces the review
record; if asked to run that loop or flip readiness, halt and say so.

## Validation

```bash
python3 -m influencer_os validate record review-record <creator-workspace>/reviews/<review_record_id>.json
python3 -m influencer_os validate workspace <creator-workspace>
```

## Boundaries

- Advisory only: never edit the strategy, never call providers, and never
  treat this Review as a Gate or approval.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md review-strategy "<lesson>"`,
run from the InfluencerOS repo root: repo paths (`docs/`, `schemas/`,
`context/learnings.md`) resolve from there, never from a Creator
Workspace runtime copy.
