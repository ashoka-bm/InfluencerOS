---
name: review-hook-payoff
description: Use after a production plan is drafted and before the generation-approval gate for the advisory Hook/Payoff Review (ADR 0024) of any of the six plan types.
---

# Review Hook/Payoff

You run the Hook/Payoff Review — an advisory creative Review (ADR 0024).
Follow `docs/gates-and-reviews.md`; the output is one
`projects/<project-slug>/reviews/<review_record_id>.json` validating
against `schemas/review-record.schema.json`.

## Independence

You review an artifact you did not author. Never certify a plan written in
the same conversational turn or by the same authoring run — the conductor
sequences this as a distinct step and feeds you an explicit packet:

- the artifact(s) under review (the production plan; the applied template
  when useful),
- the promoted idea's `hook`, `intended_payoff`, `intended_emotion`, and
  `core_message` from the locked Concept Approval,
- nothing else — not the authoring conversation.

Record how you ran in `reviewer_execution`: `source_skill:
"review-hook-payoff"`, plus `execution_mode: bounded_sub_agent` when a
bounded sub-agent produced the findings, else
`execution_mode: fallback_separated_pass` with a `fallback_reason` saying
why the bounded path was unavailable. Both `execution_mode` and
`source_skill` are schema-required.

## What To Judge

Findings key to the Content Beat Spine (`area`):

- `hook` — does the opening earn attention from the target audience in the
  first beat, and does it plant the question the payoff answers?
- `retain` — does the body sustain the open loop (no dead middle, visible
  progression)?
- `payoff` — is the promised value actually delivered, legible, and does
  it trace to the promotion's `intended_payoff`?
- `cta` — does the CTA (or deliberate loop) follow from the payoff rather
  than interrupt it? An absent CTA is a finding, not an omission.
- `general` — anything real that fits no spine area.

Severity is honest: `none` records a checked-and-fine area; `blocking` is
reserved for a real-world-risk finding (a false claim about a real person,
brand, or product) — a must-acknowledge advisory the human must revise or
waive (`human_waiver`), never an auto-stop.

## Record Rules

- One record per review run: `review_record_id` equals the filename.
- `review_role: hook_payoff`; `artifact_refs` are project-relative paths
  that resolve; `concept_approval_id` matches the project's locked approval.
- `approval_status` is a recommendation: `approve`, `revise`, or `block`.
  It halts nothing (`validate project` proves this); say the recommendation
  out loud to the user instead.
- Every finding gets a `note`; give a `recommended_revision` whenever the
  severity is above `none`.

## Validation

```bash
python3 -m influencer_os validate record review-record <creator-workspace>/projects/<project-slug>/reviews/<review_record_id>.json
python3 -m influencer_os validate project <creator-workspace>/projects/<project-slug>
```

## Boundaries

- Advisory only: never edit the plan, never gate packaging, never call
  providers.
- Do not run Fact-Check or Creator-Fit judgments here; those reviews are
  approved but unbuilt (reviews second slice) — halt and say so if asked.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md review-hook-payoff "<lesson>"`,
run from the InfluencerOS repo root: repo paths (`docs/`, `schemas/`,
`context/learnings.md`) resolve from there, never from a Creator
Workspace runtime copy.
