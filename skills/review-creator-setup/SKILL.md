---
name: review-creator-setup
description: "Use for the Setup Review trigger: an advisory bounded sub-agent review inside Creator Setup before the human Visual Continuity Plan approval (ADR 0046)."
---

# Review Creator Setup

You run the Setup Review — an advisory cadence Review (ADR 0046). Follow
`docs/gates-and-reviews.md`; write one workspace-root
`reviews/<review_record_id>.json` validating against
`schemas/review-record.schema.json`.

## Independence

Review an artifact you did not author. The conductor gives you only this
explicit packet, never the authoring conversation:

- text foundation: `creator-profile.json`, `brand_context/identity.md`,
  `brand_context/soul.md`, and `brand_context/personal-brand.md` (including
  positioning and audience),
- the auto-generated Avatar Image: its Reference Library entry and image asset,
- the draft Visual Continuity Plan.

Run before fixes and the human Visual Continuity Plan approval. Record
`reviewer_execution.source_skill: "review-creator-setup"` and
`execution_mode: bounded_sub_agent`. If that path is unavailable, use
`fallback_separated_pass` with a truthful `fallback_reason`.

## What To Judge

Findings use only the workspace vocabulary: `foundation`, `positioning`,
`audience`, `visual_identity`, `evidence`, and `general`. A finding may set
`research_demand: "new"` when it names specific missing evidence required
before approval, or `"carried_forward"` only when repeating an unresolved
Demand from an earlier review.

## Record Rules

- Set `review_role: setup`, with the Creator Profile id as the workspace anchor.
- Never include `project_id` or `concept_approval_id`.
- `artifact_refs` are workspace-relative paths that resolve.
- `approval_status` is an advisory recommendation (`approve`, `revise`, or
  `block`) and halts nothing. State the recommendation aloud to the user.

## Validation

```bash
python3 -m influencer_os validate record review-record <creator-workspace>/reviews/<review_record_id>.json
python3 -m influencer_os validate workspace <creator-workspace>
```

## Boundaries

- Advisory only: never edit the foundation, never call providers, and never
  trigger Avatar Image regeneration.
- Do not treat this Review as a Gate or approval.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md review-creator-setup "<lesson>"`,
run from the InfluencerOS repo root: repo paths (`docs/`, `schemas/`,
`context/learnings.md`) resolve from there, never from a Creator
Workspace runtime copy.
