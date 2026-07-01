# ADR 0008: Creator Learning Memory

## Status

Accepted

## Context

The Learning OS needs prior performance to influence future research, ideas, scripts, plans, and output packages. Raw analytics are useful for audit and debugging, but they are noisy and can reflect platform quirks, timing, distribution, small sample sizes, or one-off events.

If every raw metric becomes default memory, future content generation may overfit to weak signals. If only abstract lessons are stored, agents lose the trail back to evidence.

## Decision

Durable creator memory will store distilled lessons plus linked performance summaries.

Raw Analytics Snapshots, API payloads, exports, and detailed metrics stay in creator-scoped analytics files. After review, the Learning OS produces:

- concise durable lessons for future content creation,
- short performance summaries or postmortems,
- links back to the relevant Output Package, Published Post Record, Analytics Snapshots, and source material.

Future workflows should use distilled lessons by default. Agents may inspect raw analytics and linked performance summaries when diagnosing performance, checking evidence, or planning a deliberate test.

## Consequences

- Future content generation benefits from performance history without being polluted by one-off metrics.
- Lessons remain traceable to raw evidence.
- Creator memory remains scoped to the creator workspace.
- Cross-creator learning can be added later as an explicit aggregation step, not as accidental memory blending.
