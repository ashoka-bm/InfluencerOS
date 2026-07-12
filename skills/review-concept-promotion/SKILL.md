---
name: review-concept-promotion
description: "Use for the Concept Review trigger: an advisory bounded sub-agent review of all weekly candidate packages before human topic selection inside the Weekly Planning Cycle (ADR 0046)."
---

# Review Concept Promotion

You run the Concept Review — an advisory cadence Review inside the Weekly
Planning Cycle (ADR 0046). Follow `docs/gates-and-reviews.md`; write exactly
one workspace-root `reviews/<review_record_id>.json` validating against
`schemas/review-record.schema.json` through `scaffold review-record`. This is a
bounded judgment over one Anchor Slot's pre-selection candidate package,
never a Gate or an authoring pass.

## Independence

Review an artifact you did not author. The `weekly-planning-cycle` conductor
gives you only the explicit packet for the coming week's Anchor Slots, never
the authoring conversation:

- `creator-profile.json` and `content-schedule.json`,
- the 2-3 candidate Content Opportunity queue-entry files under review for
  one named Anchor Slot,
- the Research Evidence and Research Findings that support those candidates.

Record `reviewer_execution.source_skill: "review-concept-promotion"` and
`execution_mode: bounded_sub_agent`. If a bounded sub-agent is unavailable,
use `fallback_separated_pass` with a truthful `fallback_reason`.

## What To Judge

Judge whether each promotion package is evidence-backed, strategically fitted
to its owning Campaign direction, useful to the intended audience, and clear
enough for the human topic choice. Findings use only the workspace areas
`evidence`, `strategy`, `audience`, and `general`.

A finding MAY carry `research_demand: "new"` or `"carried_forward"` to expose
missing evidence. The Concept Review record itself never carries a
`research_demand_loop`: the weekly block has no multi-round lineage object,
and remaining Demands are surfaced verbally at Concept Approval.

## Record Rules

- Set `review_role: concept` and anchor by `creator_profile_id`.
- Never include `project_id`, `concept_approval_id`, or
  `research_demand_loop`.
- Author a seed, never the full record. The seed's `anchor_slot_id` is a
  creation-time scope pin; the constructor derives the record id, Creator
  Profile id, `review_role: concept`, and timestamp.
- `artifact_refs` are workspace-relative, must resolve, and must include
  `creator-profile.json`, `content-schedule.json`, `research/findings.md`, all
  2-3 canonical `research/content-opportunity-queue/entries/*.json` candidates
  named by the Anchor Slot's `research_state.candidate_content_opportunity_ids`,
  and the Evidence supporting every candidate. The constructor requires the
  refs to match that exact slot packet, and requires those candidates to be
  `shortlisted`, tracked by the canonical queue, and linked to that
  `candidates_ready` slot's run. Persisted
  validation treats the result as a point-in-time audit and does not compare
  it to later mutable slot or queue status. No weekly packet record or
  directory is introduced.
- `approval_status` is advisory (`approve`, `revise`, or `block`). A `block`
  recommendation halts nothing and must be presented to the human.

## Slice Boundary

Emit only the Concept Review Record. Never select or assign an opportunity,
edit slot research state, approve a Campaign Concept, create a Project, or
call a provider. The conductor owns orchestration and the human Concept
Approval Gate remains owned by `approve-concept`.

## Validation

```bash
python3 -m influencer_os scaffold review-record --seed <concept-review-seed.json> --creator-workspace <creator-workspace>
python3 -m influencer_os validate record review-record <creator-workspace>/reviews/<review_record_id>.json
python3 -m influencer_os validate workspace <creator-workspace>
```

## Rules

- Advisory only: never treat this Review as a Gate or approval.
- Judge only the supplied packet; never open the authoring conversation.
- Never assign opportunities, approve concepts, create Projects, or call
  providers.
- A `block` recommendation is advice to the human, not an auto-stop.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md review-concept-promotion "<lesson>"`,
run from the InfluencerOS repo root: repo paths (`docs/`, `schemas/`,
`context/learnings.md`) resolve from there, never from a Creator
Workspace runtime copy.
