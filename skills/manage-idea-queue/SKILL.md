---
name: manage-idea-queue
description: Use to create and maintain the creator's scored Idea Queue: add evidence-linked entries from research findings, rescore and stale entries as research changes, keep the queue manifest and Content Board consistent, and present ideas by goal. Never promotes.
---

# Manage Idea Queue

You maintain the creator-scoped Kanban backlog of researched content
opportunities. Follow `docs/workflows/research-and-ideas.md`; entries
validate against `schemas/idea-queue-entry.schema.json` and the manifest
against `schemas/idea-queue.schema.json`.

## Inputs

Read (context matrix — Idea generation row):

- `research/findings.md` and stable findings (full): what current research
  shows.
- Evidence through structured refs (resolve deeper context via the recall
  index or `research/runs/`).
- `creator-profile.json` (full) and `content-schedule.json`: fit, goals,
  open slots, non-repetition context.

Write only `research/idea-queue/` and queue-level warnings in
`system/project-warnings.jsonl`, plus the board/index projections via CLI.

## Entry Rules

- One JSON file per entry at
  `research/idea-queue/entries/<idea-queue-entry-id>.json`; the filename
  must equal `idea_queue_entry_id`.
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
  message, and the feeling it leaves is the intended emotion. Downstream
  plans resolve these by reference; they are captured here, once.
- `evidence_refs` use the structured shape
  (`research_run_id`, `evidence_id`, `metric_snapshot_ids`,
  `video_understanding_pack_ids`); each ref must resolve inside the run it
  names. Include `video_understanding_pack_ids` whenever real videos backed
  the idea, and `source_finding_ids` when material findings exist.
- Variant rule: keep platform variants inside one entry when execution is
  materially the same; split into separate entries when platform or format
  execution materially differs.
- Wildcard behavior is a schedule field (`schedule_fit_type: wildcard`),
  not a status. Check that new ideas are meaningfully distinct from recent
  posts instead of mechanically penalizing recently covered hot topics.

## Status Flow

`new` → `reviewed` → `shortlisted` | `needs_more_research`; terminal queue
states are `rejected` and `expired`; `promoted` is set by the promotion
workflow, never by this skill.

- Update scores, `score_deltas`, urgency, and rationale when new research
  changes the supporting evidence; flag thin evidence explicitly.
- Stale ideas stay auditable: set `stale_on`, adjust status and rationale.
  Never delete an entry.
- When evidence weakens or a stronger variant appears for an unpromoted
  idea, append a queue-level warning to `system/project-warnings.jsonl`
  (no `project_id`/`idea_promotion_id` — those pair only on promoted work).

## Manifest And Projections

- Keep `research/idea-queue/queue.json` exact: `entry_refs` lists every
  entry file with its current status, and `status_counts` (when present)
  matches entry statuses.
- After queue changes:

```bash
python3 -m influencer_os validate queue <creator-workspace>
python3 -m influencer_os rebuild-board <creator-workspace>
python3 -m influencer_os rebuild-index <creator-workspace>
```

## Presentation

Present findings first, then recommended ideas organized by goal.
Rankings are goal-specific (best viral candidate, best nurture, best
fast-moving, best schedule filler, best low-lift, best experiment) — never
one universal rank. A time-sensitive idea may be recommended on medium
creator fit, but say the tradeoff out loud and how the creator can speak
about it without drifting from persona or boundaries.

## Hard Boundary: No Promotion

This skill never creates an `IdeaPromotion` or a `Project`, never sets an
entry to `promoted`, and never writes outside the queue, warnings stream,
and projections. Promotion is a human-approval gate owned by
`promote-idea`: recommend candidates and hand off at the gate.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md manage-idea-queue "<lesson>"`.
