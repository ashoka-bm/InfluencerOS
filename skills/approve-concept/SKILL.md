---
name: approve-concept
description: Use to approve a Campaign Concept into production — the human-approval gate. Presents the full approval package, writes the locked ConceptApproval with commercial-expression ceilings, creates the exact Project set, and flips the concept and claimed slots.
---

# Approve Concept

You own the Concept Approval Gate and Project Creation (conductor phases
5-6). Follow `docs/workflows/research-and-ideas.md`; approvals validate
against `schemas/concept-approval.schema.json` and projects against
`schemas/project.schema.json`. Approval is the only handoff from a
Campaign Concept into production, and it is the constructor for
`projects/<project-slug>/` (ADR 0029/0031).

Records here are constructor-built (ADR 0042,
`docs/record-constructors.md`): you author a **seed** of judgment fields
only; `stage approval` assembles, copies, and prevalidates the full draft
bundle, and `commit-stage` writes it at the approval gate. Never
hand-author the approval or project JSON.

## Inputs

Read (context matrix — Concept approval row):

- The Campaign Concept being approved (full) and its owning
  `campaigns/<campaign-id>/campaign.json`, plus `research/findings.md` and
  evidence through the concept's structured refs.
- The source Content Opportunity when the concept was assigned from one.
- `creator-profile.json` (full) and `content-schedule.json`: fit, goals,
  and the slot(s) each project fills.

Write only `campaigns/<campaign-id>/approvals/`, the flipped concept,
`projects/<project-slug>/` (via the bundle), claimed
`content-schedule.json` slot statuses and ownership refs, and the
board/index projections via CLI.

## The Approval Gate

Human approval is required before any concept enters the creation funnel.
Automation may recommend approval; it must never approve (v1 `approved_by`
is always `user`).

Present the full package before writing anything:

- the concept: title, hypothesis, audience tension, promise,
  `intended_payoff`, and the intent pair (`intended_emotion`,
  `core_message`),
- the owning campaign, its objective, and the concept's selected audience
  segment, content pillar, and commercial functions (primary +
  supporting),
- approved platforms and approved formats — split production-supported
  formats from not-yet-supported ones,
- the commercial-expression ceilings: `max_offer_integration` and
  `max_cta_intensity` (ADR 0030) — and each project's exact planned
  `commercial_expression` at or below them, with its derived Commercial
  Pressure tier,
- the schedule slot(s) each project fills, or that the work is unslotted,
- the research carried forward: the concept's structured evidence refs
  (including `video_understanding_pack_ids` when real videos backed the
  concept) and `source_finding_ids`,
- the exact Project set to be created: slug, content unit type, target
  formats, platform targets, per-project slot claims.

Approval covers the whole package; if anything changes afterward, discard
the stage, re-stage, and present again. Approval never requires a
rationale — record `approval_note` only when the user volunteers one.

## Stage, Present, Commit

1. **Author the bundle seed** (authored fields only —
   `docs/record-constructors.md` §2): `approved_platforms`,
   `approved_formats`, `max_offer_integration`, `max_cta_intensity`,
   optional `approval_note`, and one embedded project seed per content
   unit (`project_slug`, `content_unit_type`, `platform_targets`,
   `learning_goal`, `acceptance_criteria`, `commercial_expression` — one
   Concept-approved `commercial_function` plus exact `offer_integration`
   and `cta_intensity` —, optional `schedule_slot_ids` (each slot hosts
   one project), `reference_asset_ids`, `constraints`, `notes`, and the
   authored `evidence_brief` markdown). Derive `learning_goal` and
   `acceptance_criteria` from the intended payoff and measurement
   expectation.
2. **Stage while the human reads**:
   `python3 -m influencer_os stage approval --concept <campaign_concept_id> --seed <seed.json> --creator-workspace <ws>`.
   The constructor copies the concept's evidence and ADR 0024 intent trio
   verbatim (a concept missing `intended_emotion`/`core_message` blocks
   staging — add them with the user first), requires the concept to be
   `ready_for_approval` or `active`, allocates the approval and project
   ids, prevalidates the whole bundle through the real gate, and writes
   drafts under `system/staging/` only. Nothing canonical is touched.
3. **Present from the draft**: the package you present is the staged
   records — the human approves exactly the bytes that commit will write.
4. **Commit on approval**:
   `python3 -m influencer_os commit-stage <stage-id> --creator-workspace <ws>`.
   This stamps `approved_by: user` / `approved_on`, writes the approval
   and projects in construction order, installs the evidence briefs,
   flips the concept to `active`, stamps the claimed slots (`filled` plus
   `campaign_id`, `campaign_concept_id`, `project_id`), validates, and
   rebuilds the board and index — one command, no re-authoring.
5. **On rejection or changes**: delete the stage directory (or leave it —
   it is disposable draft state), adjust the seed, and re-stage. A stage
   whose upstream concept/slots changed since staging fails the commit
   closed; re-stage from current state.

## Creating Projects

- One Project per content unit; one approval authorizes an exact set —
  one embedded project seed each. A partial approval/project set is
  invalid state (ADR 0029).
- Create Projects only for production-supported approved formats
  (`PRODUCTION_SUPPORTED_FORMATS`; the `content_unit_type` is the format
  minus its `format_` prefix). The constructor derives `target_formats`,
  ids, dates, paths, and the cached approval-chain refs;
  `platform_targets` must map only to approved research platforms.
- Each project's `commercial_expression` must use a Concept-approved
  commercial function and sit at or below the approval's ceilings; the
  offer-integration/CTA pair must be a valid pressure-matrix cell
  (ADR 0030). Escalation requires a new Concept Approval, never an edit.
- A later standalone project against an already-locked approval that
  pre-lists it uses `python3 -m influencer_os scaffold project --seed <seed.json> --creator-workspace <ws>`.
- Platform fit is advisory (ADR 0024): if the project's format is not
  native to the creator's primary surfaces, project construction appends
  a `platform_fit` ProjectWarning. Mention it to the user; it never
  blocks approval or project creation.

## Unsupported Formats

- If no approved format is production-supported, do not write an
  approval — the gate hard-fails it. Record the pending intent on the
  concept (`notes`) and surface that production support is pending.
- If only some approved formats are supported, the approval records all
  of them, Projects are created for the supported ones, and you say
  plainly which formats wait on the production build-out.

## Flipping The Concept And Slots

`commit-stage` owns every flip; you never hand-edit them. Know the
invariants it enforces:

- Concept: status `active`, `updated_on` stamped. An active approval
  requires an active concept, and the approval carries the concept's
  evidence and intent verbatim.
- Slots: each claimed slot flips to `filled` and gains its ownership refs
  (`campaign_id`, `campaign_concept_id`, `project_id`); all populated
  refs must agree with the approval chain.
- Slot gate (checked at stage time, so a bad claim fails before
  presentation): each direct slot must be `research_state.status:
  selected` with a selection naming this concept — either
  `selected_campaign_concept_id` equal to the concept, or
  `selected_content_opportunity_id` equal to the concept's source
  opportunity — backed by a completed `scheduled_needs` run that names
  that exact slot and appears in the approval's evidence refs. A
  derivative may use `inherits_anchor` to such a slot. Broad strategy
  research never satisfies this gate. Unslotted work omits per-project
  `schedule_slot_ids`.

## Lifecycle

- One unchanged concept may receive later approvals for additional
  projects — stage a new bundle; earlier approvals stay `active` as the
  provenance lock for their projects. Slot claims stay unique across
  active approvals.
- A materially changed hypothesis is a new linked concept
  (`builds_on`/`refines`/`contrasts_with`/`replaces`), never an edit to
  the approved one.
- Cancellation sets `approval_status: cancelled`; retire the concept and
  unassign its source opportunity when no active approval or live work
  remains, keeping records for audit. Projects from a cancelled approval
  are archived manually (project status `archived`), never deleted.
- Never edit a locked approval's package fields; supersede instead
  (`approval_status: superseded` on the old, new bundle in the same
  approved step).

## Validation And Projections

`commit-stage` runs the research/queue/campaign/project validators and
rebuilds the board and index itself; a clean commit needs no follow-up
commands. If it reports a projection warning (rebuild fault), or you need
to re-check the workspace later:

```bash
python3 -m influencer_os validate all <creator-workspace>
python3 -m influencer_os refresh-workspace <creator-workspace>
```

## Hard Boundaries

- Never write a `ConceptApproval` or a `Project` without explicit human
  approval of the presented package in this run.
- Never create a Project for a format production does not support.
- Never set `approved_by` to anything but `user` in v1; there is no
  automated approval path.
- Never author Commercial Pressure — it is derived from the exact
  expression values (ADR 0030). Never plan expression above the
  presented ceilings.
- Provider-backed generation stays behind its own exact-approval gate
  downstream; concept approval approves production work, not provider
  calls.

## Rules

*Dated corrections (ADR 0016); newest last.*

- 2026-07-10: This skill replaces `promote-idea` at the ADR 0031 cutover:
  the gate now approves Campaign Concepts with commercial-expression
  ceilings and an exact Project set. Approval bundles are
  constructor-built (ADR 0042) — author seeds, stage while the human
  reads, present from the draft, commit on approval.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md approve-concept "<lesson>"`,
run from the InfluencerOS repo root: repo paths (`docs/`, `schemas/`,
`context/learnings.md`) resolve from there, never from a Creator
Workspace runtime copy.
