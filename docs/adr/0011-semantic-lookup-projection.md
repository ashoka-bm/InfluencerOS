# ADR 0011: Semantic Lookup Projection

## Status

Accepted

## Context

InfluencerOS agents need low-context access to useful prior knowledge. When planning new content, an agent should be able to ask questions such as:

- what has worked for this creator on similar topics,
- which hooks retained viewers,
- which thumbnails or first frames earned clicks,
- which formats drove saves or shares,
- what prior research and performance summaries say about this audience.

Raw analytics are structured evidence, but they are too noisy and too large to place directly into default semantic memory. Distilled lessons and performance summaries are better retrieval targets.

## Decision

InfluencerOS will maintain a semantic lookup projection alongside the structured SQL index.

The canonical source remains creator workspace files. The SQL index supports structured queries and joins. The semantic lookup projection supports low-context retrieval over selected narrative and summary files.

The semantic lookup projection should index:

- identity files,
- soul files,
- personal brand files,
- research summaries,
- distilled creator learnings,
- performance summaries,
- selected postmortems,
- other curated decision-support notes.

It should not index raw analytics, raw API payloads, raw exports, full transcripts, private comments, secrets, or large generated media by default.

Agents should use both lookup modes:

- SQL for exact filters, counts, joins, missing records, publish status, and metric comparisons.
- Semantic lookup for precedent, patterns, lessons, audience interpretation, and similar-topic recall.

## Consequences

- Agents can retrieve useful prior context without loading entire creator workspaces.
- Raw analytics remain auditable and structured without polluting semantic memory.
- Distillation becomes important: performance summaries and creator learnings are the bridge between raw metrics and semantic recall.
- The semantic index must preserve creator scoping so one creator's memory does not bleed into another's decisions.
