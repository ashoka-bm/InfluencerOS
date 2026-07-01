# Handoff: Project Production And Learning Workflow

Date: 2026-06-29
Repo: `/Users/ashokaji/code/fullstock/InfluencerOS`

## Purpose

Use this handoff to start a focused Grill Me With Docs session for Project Production and Learning.

This handoff intentionally covers two related workflows:

1. Project Production: turning a selected idea into an output package.
2. Learning: capturing publication, analytics, performance summaries, and durable lessons.

Learning sits on top of all workflows. If research, creator setup, production, packaging, publishing, or analytics reveal improvements, those findings should be recorded and used to improve future decisions.

## Current Architecture Context

Production is Phase 1: Planning OS and Phase 3: Generation OS when provider-backed generation is eventually added.

Learning is Phase 2: Learning OS.

Relevant project structure:

```text
projects/<project-id>/
  project.json
  idea/
  plan/
  output-package/
    output-package.json
    assets/
    upload-ready/
    source-refs/
    platform-adaptations/
  published/
    published-post-records/
  analytics/
    snapshots/
    raw/
  performance-summary.md
```

Relevant schemas:

- `project.schema.json`
- `output-package.schema.json`
- `published-post-record.schema.json`
- `analytics-snapshot.schema.json`
- `performance-summary.schema.json`
- format-specific plan schemas
- `base-video-generation-plan.schema.json`

Key ADRs:

- `docs/adr/0004-api-primary-analytics-ingestion.md`
- `docs/adr/0005-performance-attribution-model.md`
- `docs/adr/0006-creative-performance-map.md`
- `docs/adr/0007-output-package-platform-adaptations.md`
- `docs/adr/0008-creator-learning-memory.md`
- `docs/adr/0012-project-scoped-content-work.md`

## Decisions Already Made

- Output Packages use a universal core with optional platform adaptations.
- Every Output Package must include a Creative Performance Map.
- Published Post Records are records of what actually happened after upload.
- Analytics attach to Published Post Records, not directly to Output Packages.
- Analytics ingestion is API-primary but supports manual and CSV fallback.
- Analytics must support performance attribution across packaging, hook, body retention, payoff, and CTA.
- Durable creator memory stores distilled lessons plus linked performance summaries.
- Raw analytics stay structured and queryable; summaries and lessons are semantic lookup material.
- Provider-backed generation remains gated by explicit approval.

## Open Questions For Grilling

### Project Production

- What exact records are required before output packaging can begin?
- What should each plan type contain for video, carousel, single image, story sequence, and non-video social posts?
- What should go into `assets/` versus `upload-ready/` versus `source-refs/`?
- How should LinkedIn posts, Instagram videos, YouTube Shorts, carousels, and other formats differ?
- How should platform adaptations be generated and reviewed?
- What quality gate marks an output package as upload-ready?
- How should provider-generated assets be approved, imported, or rejected?

### Learning Overlay

- What analytics are required for each platform or format?
- What metrics judge packaging, hook, body retention, payoff, and CTA?
- How should missing platform metrics be represented?
- When should a performance summary be created?
- What qualifies as a durable lesson versus a weak signal?
- How should learnings update creator memory without overfitting?
- How should learnings feed back into creator setup, research, idea generation, and production?

## Desired Output Of The Grilling Session

Produce workflow specs, likely:

- `docs/workflows/project-production.md`
- `docs/workflows/learning-loop.md`

The specs should define:

- required inputs,
- production steps,
- output package contents,
- upload-ready file conventions,
- publishing record rules,
- analytics ingestion rules,
- performance summary rules,
- durable learning rules,
- metadata that must be indexed in SQL or semantic lookup.

Update schemas only if the workflow reveals missing required metadata.
