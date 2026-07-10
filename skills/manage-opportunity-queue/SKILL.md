---
name: manage-opportunity-queue
description: Use to add evidence-linked Content Opportunities to the creator's scored queue, rescore or mark entries stale as research changes, and present opportunities by goal. Never assigns or approves — assignment creates a Campaign Concept and approval is approve-concept's human gate.
---

# Manage Content Opportunity Queue

You maintain the creator-scoped backlog of researched Content
Opportunities — wildcard research output that no Campaign owns yet
(ADR 0031). Follow `docs/workflows/research-and-ideas.md`; entries
validate against `schemas/content-opportunity.schema.json` and the
manifest against `schemas/content-opportunity-queue.schema.json`.

## Inputs

Read (context matrix — Idea generation row):

- `research/findings.md` and stable findings (full): what current research
  shows.
- Evidence through structured refs (resolve deeper context via the recall
  index or `research/runs/`).
- `creator-profile.json` (full) and `content-schedule.json`: fit, goals,
  open slots, non-repetition context.

Write only `research/content-opportunity-queue/` and queue-level warnings
in `system/project-warnings.jsonl`, plus the board/index projections via
CLI.

## Entry Rules

- New opportunities are constructed, never hand-authored: write a seed of
  authored fields and run
  `python3 -m influencer_os scaffold content-opportunity --seed <seed.json> --creator-workspace <creator-workspace>`
  (docs/record-constructors.md §6). The constructor allocates the id,
  stamps `status: new`, and upserts the queue manifest in the same
  invocation.
- Every entry carries all eight scores, 0-100 plus rationale:
  `evidence_strength`, `viral_potential`, `audience_nurture_value`,
  `creator_fit`, `schedule_fit`, `production_readiness`, `urgency`,
  `measurement_clarity`. Numbers sort; rationales prevent false precision.
- Every entry states an `intended_payoff` — the first clear statement of
  what success would mean — and a `hook`, premise, topic cluster, platform
  and format recommendations, and `schedule_fit_type`.
- Every new entry also captures the intent pair (ADR 0024; schema-optional,
  skill-required — never skip them on a new entry):
  - `intended_emotion`: the feeling the audience walks away with, one
    short phrase.
  - `core_message`: the one sentence the audience should repeat to someone
    else.
  Derive both with a "So What?" chain: state the idea, ask "so what?"
  until the answer stops changing — the last stable answer is the core
  message, and the feeling it leaves is the intended emotion. Assignment
  copies these onto the Campaign Concept verbatim; they are captured here,
  once.
- `evidence_refs` use the structured shape
  (`research_run_id`, `evidence_id`, `metric_snapshot_ids`,
  `video_understanding_pack_ids`); each ref must resolve inside the run it
  names. Include `video_understanding_pack_ids` whenever real videos backed
  the idea, and `source_finding_ids` when material findings exist.
- Variant rule: keep platform variants inside one entry when execution is
  materially the same; split into separate entries when platform or format
  execution materially differs.
- Wildcard behavior is a schedule field (`schedule_fit_type: wildcard`),
  not a status. Check that new opportunities are meaningfully distinct from
  recent posts instead of mechanically penalizing recently covered hot
  topics.
- Capture the novelty angle and, when the idea travels across platforms,
  why it adapts, inside `premise_summary` or `production_notes` — the
  schema has no dedicated fields for them. Template and structure
  selection happens at `apply-social-template` after approval, never on
  the queue entry.

## Status Flow

`new` → `reviewed` → `shortlisted` | `needs_more_research`; terminal queue
states are `rejected` and `expired`; `assigned` is set by concept
assignment (the campaign-concept constructor), never by this skill.

- Update scores, `score_deltas`, urgency, and rationale when new research
  changes the supporting evidence; flag thin evidence explicitly.
- Stale opportunities stay auditable: set `stale_on`, adjust status and
  rationale. Never delete an entry.
- When evidence weakens or a stronger variant appears for an unassigned
  opportunity, append a queue-level warning to
  `system/project-warnings.jsonl` (no `project_id`/`concept_approval_id` —
  those pair only on approved work).

## Manifest And Projections

- Keep `research/content-opportunity-queue/queue.json` exact: `entry_refs`
  lists every entry file with its current status, and `status_counts`
  (when present) matches entry statuses. The scaffold constructor keeps
  both sides consistent; manual rescoring edits must too.
- After queue changes:

```bash
python3 -m influencer_os validate queue <creator-workspace>
python3 -m influencer_os rebuild-board <creator-workspace>
python3 -m influencer_os rebuild-index <creator-workspace>
```

## Presentation

Present findings first, then recommended opportunities organized by goal.
Rankings are goal-specific (best viral candidate, best nurture, best
fast-moving, best schedule filler, best low-lift, best experiment) — never
one universal rank. A time-sensitive opportunity may be recommended on
medium creator fit, but say the tradeoff out loud and how the creator can
speak about it without drifting from persona or boundaries.

## Hard Boundary: No Assignment, No Approval

This skill never creates a `CampaignConcept`, a `ConceptApproval`, or a
`Project`, never sets an entry to `assigned`, and never writes outside the
queue, warnings stream, and projections. Assignment happens through the
campaign-concept constructor with the user's direction, and approval is a
human gate owned by `approve-concept`: recommend candidates and hand off
at the gate.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md manage-opportunity-queue "<lesson>"`,
run from the InfluencerOS repo root: repo paths (`docs/`, `schemas/`,
`context/learnings.md`) resolve from there, never from a Creator
Workspace runtime copy.
