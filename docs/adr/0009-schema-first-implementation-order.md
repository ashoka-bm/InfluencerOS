# ADR 0009: Schema-First Implementation Order

## Status

Accepted

## Context

InfluencerOS is moving from a dry-run planning slice toward a Planning OS with creator workspaces and a later Learning OS. The next implementation phase needs typed contracts before workflow and CLI behavior can be reliable.

## Decision

InfluencerOS will implement the next schema slice before workflow or CLI expansion.

The implementation order is:

1. `creator-workspace.schema.json`
2. `creator-profile.schema.json` v2
3. `reference-library.schema.json`
4. `output-package.schema.json`
5. `published-post-record.schema.json`
6. `analytics-snapshot.schema.json`
7. `performance-summary.schema.json`

Creator foundation schemas come first. Output and learning-loop schemas follow once creator identity and references are stable.

## Consequences

- Workflow and CLI work can validate against stable contracts.
- Creator workspace import can target known files and record shapes.
- Output, publishing, analytics, and learning records can preserve provenance from the beginning.
- The first implementation pass should avoid provider-backed generation and platform API calls; it should define records and validation only.

## Later Update

ADR 0020 supersedes the next Planning OS research schema slice. The research
module should now land as one coherent slice covering Creator Content Schedule,
Research Run, Research Evidence, Metric Snapshot, Research Findings, Research
Intelligence, Idea Queue, Idea Promotion, Project Warning, Content Board,
Automation Run, and System Event records.
