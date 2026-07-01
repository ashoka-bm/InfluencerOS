# ADR 0012: Project-Scoped Content Work

## Status

Accepted

## Context

The Creator Workspace originally separated `ideas/`, `plans/`, `outputs/`, `published/`, and `analytics/` as top-level folders. That mirrors pipeline stages, but it becomes hard to navigate when a creator has many posts.

Users need to quickly find the upload-ready materials for one post or content package. Agents also need a stable place to connect the selected idea, plan, output package, publication records, analytics, and performance summary.

## Decision

Creator work that moves past selection will be grouped under `projects/<project-id>/`.

A Project is one selected content idea that moves into production as a publishable content unit or package. It is not assumed to be a video and does not imply any posting cadence. A Project may produce a short-form video, carousel, single image post, story sequence, or later a multi-platform content package.

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
- A single project holds the audit trail from selected idea through analytics.
- Analytics can attach to platform-specific Published Post Records inside the project.
- Research and reference assets remain reusable across projects.
