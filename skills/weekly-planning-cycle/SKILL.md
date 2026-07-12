---
name: weekly-planning-cycle
description: "Use to run the human-initiated Weekly Planning Cycle: focused scheduled-needs research, 2-3 Content Opportunity candidates per Anchor Slot, advisory Concept Review, human topic selection, assignment, and the week's human Concept Approvals (ADR 0044 Decision 9)."
dependencies:
  - create-research-findings
  - manage-opportunity-queue
  - review-concept-promotion
  - approve-concept
---

# Weekly Planning Cycle

You conduct the Weekly Planning Cycle — Stage 4 of the operating cadence
(ADR 0044 Decision 9). It is a human-initiated ritual, never OS-scheduled. It
batches the already-shipped slot, research, opportunity, Campaign Concept,
Concept Approval, and Project machinery. It creates no new record type and no
alternate promotion path.

## Deterministic Block Contract

Each phase names inputs, outputs, schema, provenance, validation, and its human
gate. The block exits only through the existing human Concept Approval Gate.

### Phase A — Focused scheduled-needs research

- Inputs: the week's scheduled Campaign Concepts, coming-week Anchor Slots,
  Creator Profile, and current schedule state.
- Output: focused `scheduled_needs` Research Runs, Findings, and Evidence via
  `Skill(create-research-findings)`; each researched slot advances to
  `research_state.status: candidates_ready` and names its run.
- Schema: the existing research-run, findings/evidence, and
  `schemas/creator-content-schedule.schema.json` contracts.
- Provenance: every completed `scheduled_needs` run names the exact Anchor
  Slot it researched; Findings cite dated Evidence.
- Validation: `python3 -m influencer_os validate research <creator-workspace>`
  and `python3 -m influencer_os validate workspace <creator-workspace>`.
- Human gate: no.

Maintain imminent-development watch notes in the research narrative during
this phase. This is Monitor Note maintenance as conductor prose only: do not
create a Monitor Note record or consume a `triggered` note. The Reactive Slot
consumer is deferred.

### Phase B — Draft candidates per Anchor Slot

- Inputs: each Phase A run, its Findings/Evidence, the slot, and Creator
  Profile.
- Output: 2-3 evidence-backed candidate Content Opportunities per Anchor Slot,
  recorded as that slot's exact
  `research_state.candidate_content_opportunity_ids` packet, via
  `Skill(manage-opportunity-queue)` and
  `python3 -m influencer_os scaffold content-opportunity`.
- Schema: `schemas/content-opportunity.schema.json` and
  `schemas/content-opportunity-queue.schema.json`.
- Provenance: each candidate names the supporting research/evidence and
  material finding ids; the schedule remains `candidates_ready`.
- Validation: `python3 -m influencer_os validate queue <creator-workspace>`.
- Human gate: no.

### Phase C — Advisory Concept Review

- Inputs: one Anchor Slot's complete 2-3 candidate package, including Creator
  Profile, the still-`candidates_ready` schedule, canonical queue entries,
  Research Findings, and Evidence.
- Output: one workspace-level, point-in-time Concept Review Record per Anchor
  Slot via `Skill(review-concept-promotion)` and `scaffold review-record`.
- Schema: `schemas/review-record.schema.json` with `review_role: concept`.
- Provenance: `artifact_refs` resolve the exact pre-selection candidates and
  their canonical queue and research provenance; the record has no
  `research_demand_loop` lineage object.
- Validation: `python3 -m influencer_os validate workspace <creator-workspace>`.
- Human gate: no. Every verdict, including `block`, is advisory and never
  halts the cycle; present it with the candidates to inform Phase D.

### Phase D — Human topic selection

- Inputs: the 2-3 candidates for each Anchor Slot, the advisory Concept Review,
  and any week's scheduled Campaign Concept that can be selected directly.
- Output: each chosen slot becomes `research_state.status: selected` and names
  exactly one `selected_content_opportunity_id` OR
  `selected_campaign_concept_id`, retaining the completed scheduled-needs run.
  When the human directly chooses the slot's pre-existing scheduled Campaign
  Concept, first attach the exact focused run's canonical research package:
  `python3 -m influencer_os refresh-concept-research --concept <campaign-concept-id> --run <research-run-id> --creator-workspace <creator-workspace>`.
  Run that constructor-owned update before marking the slot `selected`; never
  hand-edit the Concept's evidence refs.
- Schema: `schemas/creator-content-schedule.schema.json`.
- Provenance: the selected id and `research_run_ids` preserve the topic-choice
  chain on the Anchor Slot. A directly selected Concept also cites that exact
  run, so the next Approval can snapshot the refreshed evidence package while
  older immutable Approvals retain their original evidence snapshot.
- Validation: `python3 -m influencer_os validate workspace <creator-workspace>`.
- Human gate: YES — topic choice for each Anchor Slot.

### Phase E — Assign selected new opportunities

- Inputs: each selected new Content Opportunity and its intended owning
  Campaign, Audience Segment, and Content Pillar.
- Output: assign it through
  `python3 -m influencer_os scaffold campaign-concept`; the constructor stamps
  `source_content_opportunity_id` and updates the opportunity to `assigned`.
  If the human selected one of the week's scheduled Campaign Concepts
  directly, no assignment occurs.
- Schema: existing Campaign Concept and Content Opportunity contracts.
- Provenance: the new Campaign Concept points to the selected opportunity; a
  directly selected Concept is already named on the slot.
- Validation: `python3 -m influencer_os validate research <creator-workspace>`.
- Human gate: no; execute only the Phase D choice.

This is the reconciliation settlement: candidate opportunities are ordinary
ADR 0031 Content Opportunities and enter production only through the shipped
assignment path. There is no weekly promotion record or second assignment
model.

### Phase F — Human Concept Approvals

- Inputs: the assigned or directly selected Campaign Concepts, their complete
  approval packages, slot claims, evidence, and the advisory Concept Review.
- Output: the week's existing Concept Approvals and exact Project set via
  `Skill(approve-concept)` using stage, present, and commit.
- Schema: existing Concept Approval and Project schemas; no weekly-finalization
  schema exists.
- Provenance: the shipped slot gate reconciles each claimed slot to either the
  approved Concept or its `source_content_opportunity_id`, backed by the exact
  completed `scheduled_needs` run.
- Validation: `approve-concept` prevalidates the staged bundle and commit; then
  `python3 -m influencer_os validate workspace <creator-workspace>`.
- Human gate: YES — this is the block's human exit and reuses the existing
  Concept Approval Gate. It is not a new Gate and has no fast path.

### Phase G — Ready check

- Inputs: approved slots, Concept Approvals, Projects, and canonical schedule.
- Output: no new record. Confirm approved slots are filled, every approval and
  Project resolves through its Campaign Concept and research chain, and no
  coming-week staleness Warning remains for those slots.
- Schema: no new schema; checks the existing schedule, approval, and Project
  records.
- Provenance: resolve each Project through Concept Approval, Campaign Concept,
  slot selection, scheduled-needs run, Findings/Evidence, and Creator Profile.
- Validation: `python3 -m influencer_os validate workspace <creator-workspace>`
  must exit 0 and the approved slots' Weekly Planning Cycle warnings must be
  cleared.
- Human gate: no.

## Slice Boundary

This conductor only batches shipped machinery. It introduces no new record,
schema, constructor, CLI verb, reconciliation path, or provider call. Reactive
Slot, Reactive Campaign, and fast-path approval mechanics are deferred. If any
is requested, halt and explain that a new approved slice is required.

## Rules

- No provider calls anywhere in the cycle.
- Use existing constructors and skill-owned commands; never hand-author
  Content Opportunities, Campaign Concepts, Concept Approvals, or Projects.
- Produce 2-3 evidence-backed candidates for every Anchor Slot before topic
  selection.
- Run one Concept Review over every candidate for each Anchor Slot while that
  slot is still `candidates_ready`, before human topic selection or assignment.
- Preserve ADR 0031: no Concept Approval without an owning Campaign Concept.
- Concept Review is advisory; a `block` recommendation never auto-stops.
- Never build or simulate Reactive Slot, Reactive Campaign, Monitor Note
  records, triggered-note consumption, or a fast-path approval flow.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md weekly-planning-cycle "<lesson>"`,
run from the InfluencerOS repo root: repo paths (`docs/`, `schemas/`,
`context/learnings.md`) resolve from there, never from a Creator
Workspace runtime copy.
