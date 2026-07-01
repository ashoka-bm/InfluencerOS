# ADR 0010: File-First Source Of Truth With SQL Index

## Status

Accepted

## Context

InfluencerOS needs to remain portable and public-repo-friendly while supporting many creators, projects, output packages, published records, analytics snapshots, and learning summaries.

Agentic OS uses source files as durable memory and a vector SQL database as a searchable projection. InfluencerOS should use the same principle, but with structured creative and analytics records in addition to semantic memory.

## Decision

InfluencerOS will use creator workspace files as the durable source of truth and a rebuildable local SQL database as an index/query layer.

Canonical records live in Creator Workspaces under `workspace-library/creators/<creator-slug>/`. The local SQL database may index those records for fast lookup, dashboard views, analytics comparison, ingestion status, and workflow queries.

The default local database path is:

```text
workspace-library/index/influencer-os.sqlite
```

SQL rows must preserve source file provenance:

- source file path,
- source record ID,
- source record type,
- content hash,
- indexed timestamp,
- creator ID or slug,
- project ID when applicable.

The SQL index should be rebuildable from workspace files. It must not be the only copy of creator identity, output packages, published records, analytics snapshots, or learning summaries.

InfluencerOS also maintains a semantic lookup projection for selected human-readable files, such as identity files, soul files, personal brand files, distilled learnings, performance summaries, and research summaries. Raw analytics should not be indexed semantically by default.

## Consequences

- Creator workspaces stay portable, inspectable, and easy to back up.
- SQL can support practical queries such as upload-ready packages, publish status, analytics comparisons, and connector job state.
- Database corruption or schema migration risk is lower because the index can be rebuilt.
- The public repo can ship schemas and indexer logic without shipping real creator data.
- Future dashboards and API connectors have a stable data access layer without replacing file-backed records.
- Agents retain low-context semantic lookup for prior lessons, similar-topic performance, and creator-specific decision support.
