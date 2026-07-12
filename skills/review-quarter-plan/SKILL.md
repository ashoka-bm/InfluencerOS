---
name: review-quarter-plan
description: "Use for the Quarterly Review trigger: an advisory bounded sub-agent review of the draft Quarter Plan inside the Quarterly Planning Cycle, before the one human approval over the whole plan (ADR 0046)."
---

# Review Quarter Plan

You run the Quarterly Review — an advisory cadence Review (ADR 0046). Follow
`docs/gates-and-reviews.md`; write one workspace-root
`reviews/<review_record_id>.json` validating against
`schemas/review-record.schema.json`. The `quarterly` branch requires the
complete reviewed plan packet and `research_demand_loop` lineage.

## Independence

Review an artifact you did not author. The conductor
(`quarterly-planning-cycle`) gives you only this explicit packet, never the
authoring conversation:

- the draft Quarter Plan content: retrospective findings, per-Campaign
  research, and the next-Quarter Campaign Concept set,
- the Research Evidence and Research Findings that validate that content,
- Creator Profile.

Run inside the research-and-review loop that precedes the one human approval
over the whole Quarter Plan record. Record
`reviewer_execution.source_skill: "review-quarter-plan"` and
`execution_mode: bounded_sub_agent`. If that path is unavailable, use
`fallback_separated_pass` with a truthful `fallback_reason`.

## What To Judge

Findings use only the workspace area vocabulary: `strategy`, `evidence`,
`schedule`, `positioning`, `audience`, and `general`. Those cover the
retrospective (`general`/`evidence`), the per-Campaign research
(`evidence`/`strategy`), and the next-Quarter Concept set (`strategy`). A
finding may set `research_demand: "new"` when it names specific missing
evidence required before approval, or `"carried_forward"` when repeating an
unresolved Demand the conductor supplied from a prior round; do not let an
earlier open question disappear silently.

## Record Rules

- Set `review_role: quarterly`, with the Creator Profile id as the workspace anchor.
- Never include `project_id` or `concept_approval_id`.
- `artifact_refs` are workspace-relative paths that resolve and include the
  Creator Profile, this exact Quarter Plan's draft and Campaign Concept set,
  current Research Findings, and its Research Evidence packet. Repeat rounds
  also include the immediately prior Quarterly Review Record.
- Set `research_demand_loop.extra_research_round` to 0, 1, or 2. Round 0 has
  no prior id; rounds 1 and 2 name the immediately prior same-role Review.
- `approval_status` is an advisory recommendation (`approve`, `revise`, or
  `block`) and halts nothing. State the recommendation aloud to the user.

## Slice Boundary

This skill only emits the Quarterly Review record. The
`quarterly-planning-cycle` conductor runs the Research Demand loop and holds
the one human approval over the Quarter Plan. If asked to run that loop, build
the Quarter Plan, or record the approval yourself, halt and say so.

## Validation

```bash
python3 -m influencer_os validate record review-record <creator-workspace>/reviews/<review_record_id>.json
python3 -m influencer_os validate workspace <creator-workspace>
```

## Rules

- Advisory only: never edit the Quarter Plan, never call providers, and never
  treat this Review as a Gate or approval.
- Judge only the supplied packet; never open the authoring conversation.
- A `block` recommendation is advice to the human, not an auto-stop.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md review-quarter-plan "<lesson>"`,
run from the InfluencerOS repo root: repo paths (`docs/`, `schemas/`,
`context/learnings.md`) resolve from there, never from a Creator
Workspace runtime copy.
