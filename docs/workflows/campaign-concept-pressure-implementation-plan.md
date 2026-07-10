# Campaign, Concept, And Pressure Implementation Plan

Last updated: 2026-07-10

Status: **Approved design; implementation not started.** Decisions are locked
in ADRs 0029-0032. This plan is the stopping point for design and the execution
contract for the first implementation.

## Goal

Replace the loose idea-to-project handoff with a stable hierarchy that can
group and evaluate related work without overbuilding analytics:

```text
Content Pillar
  -> Campaign
    -> Campaign Concept
      -> Concept Approval
        -> Project
```

Research may also produce an unassigned Content Opportunity. Assignment turns
that opportunity into a Campaign Concept; it does not create a placeholder
Campaign.

## Success Condition

The first implementation is complete when a creator can plan a calendar slot,
run focused research, create or assign a Campaign Concept, approve an exact
multi-format Project set, produce each Project through the existing pipeline,
and inspect Campaign/Concept progress plus an advisory per-platform Pressure
Projection. Every canonical reference validates, legacy idea records are gone
from the active model, and no deferred analytics machinery is required.

## Canonical Records And Ownership

Creator workspace layout:

```text
content-strategy.json                     # contains Content Series
content-schedule.json                     # planning slots
research/
  content-opportunity-queue/
    queue.json
    entries/<content-opportunity-id>.json
campaigns/
  <campaign-id>/
    campaign.json
    concepts/<campaign-concept-id>.json
    approvals/<concept-approval-id>.json
projects/
  <project-slug>/
    project.json
    ...existing project records...
```

Initial ID families are `content_opportunity_*`, `campaign_*`,
`campaign_concept_*`, `concept_approval_*`, and `content_series_*`.

Canonical immediate provenance is intentionally narrow:

- Campaign Concept names its owning `campaign_id` and optional source
  `content_opportunity_id` plus research evidence.
- Concept Approval names its `campaign_concept_id`, exact authorized Project
  IDs, associated schedule slot IDs, commercial-expression ceilings, evidence
  refs, approval timestamp, and approving human.
- Project names one immediate `concept_approval_id`. Its Campaign Concept and
  Campaign are resolved transitively; cached IDs, if retained for indexing,
  must match that chain.
- A calendar slot may name `content_series_id`, `campaign_id`, and
  `campaign_concept_id` before Project creation. After creation it also names
  `project_id`; validation requires all populated ownership refs to agree.
- Offer Integration, CTA Intensity, and Commercial Pressure are not duplicated
  on calendar slots. Before a Project exists, the slot is reported as
  unresolved rather than assigned assumed pressure.

Concept Approval and its Projects are created as one transactional operation:
Project IDs are allocated into the approval snapshot, then all records are
validated and committed together. A partial approval/project set is invalid.

## Campaign Contract

A Campaign has one stable typed primary objective, one primary Audience
Segment, one primary Content Pillar, and optional supporting Segments and
Pillars. A paid-conversion Campaign also has one primary paid offer and may
name supporting free assets. Awareness or nurture Campaigns may have no paid
offer.

Initial objectives:

```text
awareness | audience_growth | trust_nurture | lead_generation |
paid_conversion | customer_retention | reactivation
```

Campaign lifecycle:

```text
draft | active | paused | completed | archived
```

Activation records human approval metadata but is not a new formal production
Gate. Changing the primary objective or primary paid offer creates a new
Campaign. Revision and Wave records are deferred.

## Campaign Concept Contract

A Campaign Concept is one testable hypothesis. It selects one Campaign-approved
Audience Segment and one Campaign-approved Content Pillar, then declares one
primary and optional supporting Commercial Functions.

Initial Commercial Functions:

```text
problem_awareness | demand_creation | trust_building | authority_building |
objection_resolution | proof | lead_capture | direct_conversion
```

Hooks, formats, examples, CTA wording, and platform adaptations vary at the
Project level. A material change to the audience tension, promise, target
Segment, or hypothesis creates a new linked Concept using `builds_on`,
`refines`, `contrasts_with`, or `replaces`.

Concept lifecycle:

```text
draft | researching | ready_for_approval | active | retired
```

One unchanged Concept may receive later Concept Approvals for additional
Projects. Every Project still has exactly one owning Concept and Campaign.

## Project Boundary

One Project is one independently planned publishable content unit with one
materially stable Hook-Retain-Payoff execution and core asset. The same core
creative published across platforms remains one Project when changes are
limited to crop, caption, title, thumbnail, duration trim, or platform CTA.
A materially different hook, structure, payoff, or core asset is a separate
Project, even when it serves the same Concept.

Each Project selects one execution Commercial Function from its Concept's
approved primary/supporting set and stores exact planned Offer Integration and
CTA Intensity at or below its Approval ceilings. Escalation requires a new
Concept Approval.

## Commercial Expression And Pressure

Offer Integration:

```text
absent | embedded | contextual | central
```

CTA Intensity:

```text
none | soft | direct
```

Commercial Pressure is derived, never authored:

| Offer Integration | none CTA | soft CTA | direct CTA |
| --- | --- | --- | --- |
| absent | none | low | invalid |
| embedded | low | low | invalid |
| contextual | low | moderate | high |
| central | moderate | high | high |

Pressure Indicator v1 maps `none`, `low`, `moderate`, and `high` to 0, 1, 2,
and 3, then normalizes the mean to 0-100. The UI always retains tier counts;
the score never replaces source classifications.

The initial Pressure Projection uses all Project-linked Audience Touches in
the current schedule horizon, grouped per platform. A Story sequence or
carousel is one Touch on its platform; the same Project planned on two
platforms creates one Touch on each. It reports:

- known Touch count and counts by tier,
- Pressure Indicator,
- `high / known` share,
- unresolved pre-Project slot count and coverage,
- an advisory warning when known high-pressure share exceeds 25%.

Unknown slots are never counted as low. The warning does not block Campaign
activation, Concept Approval, Project creation, or publication.

## Research And Calendar Flow

```text
strategy scaffold + calendar slots
  -> slot-scoped research
  -> Content Opportunity, when no Campaign owns the direction
     OR draft Campaign Concept, when Campaign scope is already known
  -> Concept research package
  -> Concept Approval with exact Project set
  -> Projects
  -> existing template, plan, generation, package, publish, analytics flow
```

Broad research may populate the Content Opportunity Queue. Focused slot
research should answer the need of the slot and preserve its research-run and
evidence refs. Related slots may become Projects under the same Concept; they
do not become one Project merely because they share a topic.

## Evaluation Projections

Campaign and Concept evaluation are rebuildable projections, not new canonical
evaluation records. The Content Board expands:

```text
Content Pillar -> Campaign -> Campaign Concept -> Project
```

The first projection may aggregate only facts already present: lifecycle and
delivery counts, scheduled and published Projects, Commercial Function and
Pressure mix, publication metrics, Performance Summary findings, and progress
against the Campaign's declared measurable outcome. Missing analytics remain
unknown. No inferred conversion credit, fractional attribution, or duplicated
success is allowed.

## Clean Migration

The implementation replaces, rather than aliases, legacy terms:

- `IdeaQueueEntry` becomes `ContentOpportunity`.
- `IdeaPromotion` becomes `ConceptApproval`.
- `content_strategy.content_campaigns` becomes `content_series`; its old
  records are recurring publishing patterns, not operational Campaigns.
- Calendar strategy-campaign references become Content Series references;
  operational Campaign references are added separately.

Unassigned queue entries migrate mechanically. A promoted record cannot be
assigned an invented Campaign: disposable fixture workspaces are rebuilt;
durable records require an explicit mapping to Campaign and Concept. Migration
runs a preflight report and makes no writes when required mappings are absent.
No permanent dual-write, aliases, or fallback readers remain after cutover.

## Implementation Sequence

### Slice 1: Records and pure rules

- Add Campaign, Campaign Concept, Concept Approval, Content Opportunity, and
  queue schemas/examples plus constructors.
- Add pure Commercial Pressure derivation and validation with exhaustive matrix
  tests.
- Extend Project with immediate approval provenance and exact commercial fields.

### Slice 2: Strategy, schedule, and migration

- Rename Content Strategy campaigns to Content Series and update schedule refs.
- Add pre-Project Campaign/Concept ownership and post-creation Project refs to
  calendar slots.
- Implement preflighted clean migration and update fixture workspaces.

### Slice 3: Workflow and validation

- Replace idea-management and promotion paths with opportunity assignment,
  Concept authoring, and transactional Concept Approval/Project creation.
- Route slot-scoped research through the new records.
- Update repository and copied creator-runtime skills, validation, recall/index
  allowlists, CLI commands, docs, and drift pins together.

### Slice 4: Projections and closeout

- Rebuild the hierarchical Content Board and calendar Pressure Projection.
- Add rebuildable Campaign/Concept evaluation summaries from existing records.
- Run end-to-end, migration, validation, drift, and full regression tests.

## Runnable Exit Criteria

1. One approved Concept can transactionally create a Substack Project, two
   Instagram post Projects, one Reel Project, and two Story Projects, all with
   one owning Concept and individually valid production paths.
2. A slot-scoped research run resolves to either a Content Opportunity or a
   Campaign-owned Concept with complete evidence provenance.
3. Validators reject cross-Campaign Concepts, unapproved Project functions,
   expression above Approval ceilings, invalid pressure combinations, dangling
   slot refs, and partial approval/project writes.
4. Every pressure-matrix combination is tested; calendar projection reports
   per-platform tier counts, score, high share, unknown coverage, and advisory
   warning behavior deterministically.
5. Migration is all-or-nothing, requires explicit ownership for durable
   promoted records, and leaves no canonical idea or strategy-campaign terms.
6. Campaign and Concept projections rebuild solely from canonical records and
   never fabricate missing outcomes or attribution.
7. Example validation, workspace validation, skill drift checks, focused tests,
   and the full test suite pass.

## Explicitly Deferred

Campaign Revisions, Campaign Waves, Pressure Policies and Profiles, Pressure
Experiments, cross-creator benchmarks, evidence-maturity automation, adaptive
recommendations, assisted or advanced outcome attribution, mandatory rolling
windows, and automated audience-harm stopping. The MVP stores stable source
facts so these can be added later without changing Project ownership or
historical commercial-expression records.
