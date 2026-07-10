---
name: promote-idea
description: Use to promote an Idea Queue Entry into production — the human-approval gate. Presents the full promotion package, writes the locked IdeaPromotion, creates Projects for supported formats, and flips the entry.
---

# Promote Idea

You own the Idea Promotion Gate and Project Creation (conductor phases 5-6).
Follow `docs/workflows/research-and-ideas.md`; promotions validate against
`schemas/idea-promotion.schema.json` and projects against
`schemas/project.schema.json`. Promotion is the only handoff from research
into production, and it is the constructor for `projects/<project-slug>/`.

Records here are constructor-built (ADR 0042,
`docs/record-constructors.md`): you author a **seed** of judgment fields
only; `stage promotion` assembles, copies, and prevalidates the full draft
bundle, and `commit-stage` writes it at the approval gate. Never hand-author
the promotion or project JSON.

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

- the idea: title, hook, premise, `intended_payoff`, and the intent pair
  (`intended_emotion`, `core_message`) from the entry,
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

Approval covers the whole package; if anything changes afterward, discard
the stage, re-stage, and present again. Approval never requires a
rationale — record `approval_note` only when the user volunteers one.

## Stage, Present, Commit

1. **Author the bundle seed** (authored fields only —
   `docs/record-constructors.md` §2): `approved_platforms`,
   `approved_formats`, `schedule_slot_ids` (omit for wildcards),
   `creative_elements_to_carry_forward`, optional `approval_note`, and one
   embedded project seed per content unit (`project_slug`,
   `content_unit_type`, `platform_targets`, `learning_goal`,
   `acceptance_criteria`, optional `reference_asset_ids`, `constraints`,
   `notes`, and the authored `evidence_brief` markdown — the hook, why the
   evidence says it works, reusable elements, avoid notes, source
   evidence ids). Derive `learning_goal` and `acceptance_criteria` from
   the intended payoff and measurement expectation.
2. **Stage while the human reads**:
   `python3 -m influencer_os stage promotion --entry <idea_queue_entry_id> --seed <seed.json> --creator-workspace <ws>`.
   The constructor copies the locked snapshot verbatim from the entry
   (scores → `score_snapshot`, `evidence_refs`, `source_finding_ids` →
   `research_finding_ids`, and the ADR 0024 intent pair — an entry missing
   `intended_emotion`/`core_message` blocks staging; add them with the
   user first), allocates the promotion and project ids, prevalidates the
   whole bundle through the real gate, and writes drafts under
   `system/staging/` only. Nothing canonical is touched.
3. **Present from the draft**: the package you present is the staged
   records — the human approves exactly the bytes that commit will write.
4. **Commit on approval**:
   `python3 -m influencer_os commit-stage <stage-id> --creator-workspace <ws>`.
   This stamps `approved_by: user` / `approved_on`, writes promotion and
   projects in construction order, installs the evidence briefs, flips
   the entry, queue manifest, and claimed slots, validates, and rebuilds
   the board and index — one command, no re-authoring.
5. **On rejection or changes**: delete the stage directory (or leave it —
   it is disposable draft state), adjust the seed, and re-stage. A stage
   whose upstream entry/slots changed since staging fails the commit
   closed; re-stage from current state.

## Creating Projects

- One Project per content unit; one promotion may create several — one
  embedded project seed each.
- Create Projects only for production-supported approved formats
  (`PRODUCTION_SUPPORTED_FORMATS`; the `content_unit_type` is the format
  minus its `format_` prefix). The constructor derives `target_formats`,
  ids, dates, paths, and the cached promotion refs; `platform_targets`
  must map only to approved research platforms.
- A later standalone project against an already-locked promotion that
  pre-lists it uses `python3 -m influencer_os scaffold project --seed <seed.json> --creator-workspace <ws>`.
- Platform fit is advisory (ADR 0024): if the project's format is not
  native to the creator's primary surfaces, project construction appends
  a `platform_fit` ProjectWarning. Mention it to the user; it never
  blocks promotion or project creation.

## Unsupported Formats

- If no approved format is production-supported, do not write a
  promotion — the gate hard-fails it. Record a dated
  `approval_intent_note` on the queue entry, keep its queue status, and
  surface that production support is pending.
- If only some approved formats are supported, the promotion records all
  of them, Projects are created for the supported ones, and you say
  plainly which formats wait on the production build-out.

## Flipping The Entry And Slots

`commit-stage` owns every flip; you never hand-edit them. Know the
invariants it enforces:

- Entry: status `promoted`, the promotion id appended to
  `linked_idea_promotion_ids`, created project ids appended to
  `linked_project_ids`, `updated_on` stamped. A completed promotion must
  leave the entry linking at least one Project — a promotion that creates
  no production work is invalid state, not a deferral. Never delete the
  entry.
- Queue manifest: the entry's ref status and `status_counts` stay exact.
- Slots: each claimed slot flips to `filled`; the schedule stores no
  promotion ids (the link resolves promotion → slot).
- Slot gate (checked at stage time, so a bad claim fails before
  presentation): each direct slot must be `research_state.status:
  selected` with `selected_idea_queue_entry_id` equal to the promoted
  entry, backed by a completed `scheduled_needs` run that names that
  exact slot and appears in the promotion's evidence refs. A derivative
  may use `inherits_anchor` to such a slot. Broad strategy research never
  satisfies this gate. Wildcard ideas omit `schedule_slot_ids`.

## Lifecycle

- Scope expansion (new formats or platforms) happens by a new promotion
  that supersedes the old one. Staging refuses an entry with an active
  promotion, so the order is: present the new package for approval, set
  the old promotion's `promotion_status` to `superseded` (a lifecycle
  status edit, not record authoring), then stage and commit the new
  bundle in the same approved step. The entry links both; exactly one
  linked promotion may be `active`.
- Cancellation sets `promotion_status: cancelled`; revert the entry to
  `shortlisted` when no active promotion remains, keeping the links for
  audit. Projects from a cancelled promotion are archived manually
  (project status `archived`), never deleted.
- Never edit a locked promotion's package fields; supersede instead.

## Validation And Projections

`commit-stage` runs the research/queue/project validators and rebuilds the
board and index itself; a clean commit needs no follow-up commands. If it
reports a projection warning (rebuild fault), or you need to re-check the
workspace later:

```bash
python3 -m influencer_os validate all <creator-workspace>
python3 -m influencer_os refresh-workspace <creator-workspace>
```

## Hard Boundaries

- Never write an `IdeaPromotion` or a `Project` without explicit human
  approval of the presented package in this run.
- Never create a Project for a format production does not support.
- Never set `approved_by` to anything but `user` in v1; there is no
  automated promotion path.
- Provider-backed generation stays behind its own exact-approval gate
  downstream; promotion approves production work, not provider calls.

## Rules

*Dated corrections (ADR 0016); newest last.*

- 2026-07-10: Promotion bundles are constructor-built (ADR 0042). Author
  seeds, stage while the human reads, present from the draft, commit on
  approval — see §Stage, Present, Commit. Hand-authoring promotion or
  project JSON is retired.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md promote-idea "<lesson>"`,
run from the InfluencerOS repo root: repo paths (`docs/`, `schemas/`,
`context/learnings.md`) resolve from there, never from a Creator
Workspace runtime copy.
