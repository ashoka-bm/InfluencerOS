# ADR 0012: Project-Scoped Content Work

## Status

Accepted

## Context

The Creator Workspace originally separated `ideas/`, `plans/`, `outputs`, `published`, and `analytics` as top-level folders. That mirrors pipeline stages, but it becomes hard to navigate when a creator has many posts.

Users need to quickly find the upload-ready materials for one post or content package. Agents also need a stable place to connect the approved idea promotion, plan, output package, publication records, analytics, and performance summary.

## Decision

Creator work that moves past idea promotion will be grouped under `projects/<project-id>/`.

A Project is one approved content unit that moves into production as a publishable unit or package. It is not assumed to be a video and does not imply any posting cadence. A Project may produce a short-form video, carousel, single image post, story sequence, article, thread, or later a multi-platform content package.

Project-scoped folders include:

- `idea/`
- `plan/`
- `output-package/`
- `published/`
- `analytics/`
- `performance-summary.md`

Creator-level `research/` and `references/` remain top-level because they can feed many projects.

## Consequences

- Upload-ready materials are easier to find under one project folder.
- A single project holds the audit trail from idea promotion through analytics.
- Analytics can attach to platform-specific Published Post Records inside the project.
- Research and reference assets remain reusable across projects.

## Later Update

ADR 0020 replaces the `SelectedContentIdea` handoff with `IdeaPromotion`. A
Project now moves into production from a human-approved Idea Promotion, which
points back to an Idea Queue Entry, Research Findings, Research Evidence, Metric
Snapshots, and relevant reference assets. The project-scoped folder decision
still stands, but the upstream provenance language should be read through ADR
0020.

The `idea/` project folder is dropped with that change. The Idea Promotion
record lives in the research module under
`research/idea-promotions/<idea-promotion-id>.json`; the Project carries its
provenance in `project.json` source refs plus a compact `evidence-brief.md`.
Project-scoped folders are now `plan/`, `output-package/`, `published/`,
`analytics/`, and `performance-summary.md`.
