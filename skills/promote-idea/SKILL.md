---
name: promote-idea
description: Use to promote a human-approved Idea Queue Entry into production: present the full promotion package for explicit approval, write the locked IdeaPromotion record, create one or more Projects for production-supported formats, flip the entry, and keep the manifest and projections consistent. Owns the human-approval gate.
---

# Promote Idea

You own the Idea Promotion Gate and Project Creation (conductor phases 5-6).
Follow `docs/workflows/research-and-ideas.md`; promotions validate against
`schemas/idea-promotion.schema.json` and projects against
`schemas/project.schema.json`. Promotion is the only handoff from research
into production, and it is the constructor for `projects/<project-slug>/`.

## Inputs

Read (context matrix — Idea promotion row):

- The queue entry being promoted (full), plus `research/findings.md` and
  evidence through the entry's structured refs.
- `creator-profile.json` (full) and `content-schedule.json`: fit, goals,
  and the slot(s) the idea fills.

Write only `research/idea-promotions/`, the promoted entry and queue
manifest, `projects/<project-slug>/` (via `init-project`), claimed
`content-schedule.json` slot statuses, and the board/index projections via
CLI.

## The Approval Gate

Human approval is required before any idea enters the creation funnel.
Automation may recommend promotion; it must never promote (v1 `approved_by`
is always `user`).

Present the full package before writing anything:

- the idea: title, hook, premise, and `intended_payoff`,
- approved platforms and approved formats — split production-supported
  formats from not-yet-supported ones,
- the schedule slot(s) the idea fills, or that it is a wildcard,
- the research carried forward: finding ids, structured evidence refs
  (including `video_understanding_pack_ids` when real videos backed the
  idea), and the current eight-score snapshot,
- creative elements to carry forward (hooks, first-frame patterns,
  structure notes, avoid notes),
- the exact Projects to be created: slug, content unit type, target
  formats, platform targets.

Approval covers the whole package; if anything changes afterward, present
it again. Approval never requires a rationale — record `approval_note`
only when the user volunteers one.

## Writing The Promotion

- One JSON file at `research/idea-promotions/<idea_promotion_id>.json`;
  the filename must equal `idea_promotion_id`.
- The promotion is a permanent locked snapshot: copy the entry's current
  scores verbatim into `score_snapshot`, its `evidence_refs` structured
  shape, and its `source_finding_ids` into `research_finding_ids`
  (empty is allowed when the idea came from evidence without a material
  findings update). Later research must never rewrite these.
- `approved_by: user`, `approved_on` today, `promotion_status: active`,
  and `project_ids_created` listing the planned project ids up front —
  the projects are constructed immediately after, and a project's
  `init-project` gate requires its promotion to already list it.

Construction order: promotion → `init-project` each project →
evidence brief → entry and manifest flip → schedule slots → validate and
rebuild. Validation link checks assume the finished state, so complete
the sequence before validating.

## Creating Projects

- One Project per content unit; one promotion may create several.
- Create Projects only for production-supported approved formats
  (`PRODUCTION_SUPPORTED_FORMATS`; the `content_unit_type` is the format
  minus its `format_` prefix).
- Author the project manifest: status `created`, `target_formats` a
  subset of `approved_formats`, `platform_targets` mapping only to
  approved research platforms, `learning_goal` and `acceptance_criteria`
  derived from the intended payoff and measurement expectation, and
  `source_refs.idea_promotion_id` as the single upstream ref (cached
  deeper refs are optional and must stay subsets of the locked
  promotion).
- Run `python3 -m influencer_os init-project <manifest> --creator-workspace <creator-workspace>`,
  then replace the scaffolded `evidence-brief.md` with a compact
  production-facing brief: the hook, why the evidence says it works, the
  reusable elements to copy, avoid notes, and the source evidence ids.

## Unsupported Formats

- If no approved format is production-supported, do not write a
  promotion — the gate hard-fails it. Record a dated
  `approval_intent_note` on the queue entry, keep its queue status, and
  surface that production support is pending.
- If only some approved formats are supported, the promotion records all
  of them, Projects are created for the supported ones, and you say
  plainly which formats wait on the production build-out.

## Flipping The Entry

- Set the entry status to `promoted`; append the promotion id to
  `linked_idea_promotion_ids` and the created project ids to
  `linked_project_ids`; update `updated_on`.
- A completed promotion must leave the entry linking at least one
  Project — the validators enforce this closure, so a promotion that
  creates no production work is invalid state, not a deferral.
- Keep `research/idea-queue/queue.json` exact: the entry's ref status and
  `status_counts` must match. Never delete the entry.

## Schedule Slots

- For scheduled ideas, record the claimed `schedule_slot_ids` on the
  promotion and set each claimed slot's status to `filled` in
  `content-schedule.json`. The schedule stores no promotion ids; the link
  resolves promotion → slot.
- Wildcard ideas omit `schedule_slot_ids`.

## Lifecycle

- Scope expansion (new formats or platforms) happens by a new promotion
  that supersedes the old one: present and write the new package, then
  set the old promotion's `promotion_status` to `superseded`. The entry
  links both; exactly one linked promotion may be `active`.
- Cancellation sets `promotion_status: cancelled`; revert the entry to
  `shortlisted` when no active promotion remains, keeping the links for
  audit. Projects from a cancelled promotion are archived manually
  (project status `archived`), never deleted.
- Never edit a locked promotion's package fields; supersede instead.

## Validation And Projections

After the sequence completes:

```bash
python3 -m influencer_os validate research <creator-workspace>
python3 -m influencer_os validate queue <creator-workspace>
python3 -m influencer_os validate project <creator-workspace>/projects/<project-slug>
python3 -m influencer_os rebuild-board <creator-workspace>
python3 -m influencer_os rebuild-index <creator-workspace>
```

## Hard Boundaries

- Never write an `IdeaPromotion` or a `Project` without explicit human
  approval of the presented package in this run.
- Never create a Project for a format production does not support.
- Never set `approved_by` to anything but `user` in v1; there is no
  automated promotion path.
- Provider-backed generation stays behind its own exact-approval gate
  downstream; promotion approves production work, not provider calls.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md promote-idea "<lesson>"`.
