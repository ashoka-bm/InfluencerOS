# Operating Cadence Model Map

## Purpose

Visualize the implemented four-block operating cadence (ADRs 0044-0047) plus
the per-Project production pipeline, correcting the pre-0044 whiteboard that
still showed `strategy_ready` as a stage exit and omitted the Quarterly
Planning Cycle.

## Map Type

Workflow map (five vertical columns, one per cadence block plus production;
top-to-bottom flow inside each column, left-to-right handoffs between columns).

## Source Files Inspected

- `docs/adr/0044-operating-cadence-model.md` (four blocks, block contract, RD loop cap)
- `docs/adr/0045-avatar-image-auto-generation.md` (avatar carve-out ordering)
- `docs/adr/0046-independent-review-ladder.md` (four advisory ladder reviews)
- `docs/adr/0047-quarter-plan-records.md` (Quarter Plan, Revisions, Duration Target)
- `docs/gates-and-reviews.md` (two blocking gates; QualityReview placement)
- `docs/pipeline-contract.md` (Applied Social Template, Output Package)
- `influencer_os/creator_workspaces.py` (status ladder incl. `profile_ready`; loop validation)
- `influencer_os/cadence.py` (Quarter anchor, revision contiguity, reference closure)
- `skills/create-influencer/SKILL.md` (setup step order, avatar before Setup Review)
- `skills/quarterly-planning-cycle/SKILL.md`, `skills/weekly-planning-cycle/SKILL.md`
  (phase A-G orders)

Content was additionally cross-checked by the 2026-07-13 spec-conformance
review (8 units, zero confirmed drift findings).

## Excalidraw Scene

- Scene name: `InfluencerOS Operating Cadence (ADR 0044-0047)`
- Scene ID: `bpe2Sec3O5`
- Collection: `Main` (workspace `3g0OtZhQ70R`)
- No share link recorded: scene link sharing is off; open via the workspace.

## Local Screenshot

Disposable verification export only (session scratchpad); not committed, per
the visual-architecture-maps storage rule.

## Last Visual Verification

2026-07-13 — screenshot rendered via `take_screenshot`, inspected, and key
labels (`production_ready`, `QualityReview`, `quarter anchor`,
`Provider Boundary`, `Quarterly Review`, `foundation_ready`) confirmed via
`search_scene_content`.

Renderer caveats: none material. The dashed green loop arrows (Research
Demand re-runs, avatar rejection) bow slightly outside their column
containers by design.

## Legend

- Blue: advisory review (never blocks)
- Orange: human decision / block exit (readiness decision, not a Gate)
- Red: blocking gate or review (Concept Approval Gate, Provider Boundary,
  QualityReview)
- Grey: durable record
- Dashed green: loop / re-run edge

## Open Questions

- `profile_ready` (intake) is summarized inside column 1's first node rather
  than drawn as its own node, to keep the column within the node budget; split
  it out if the setup block gets its own focused map.
- Reactive/news-lane vocabulary (Reactive Slot, Monitor Note consumption) is
  deliberately absent: accepted targets only, no build obligation (ADR 0044
  Decision 10).
