# ADR 0004: API-Primary Analytics Ingestion

## Status

Accepted

## Context

InfluencerOS needs a Learning OS that improves future research, ideas, scripts, plans, and output packages from observed post performance.

Analytics may arrive from platform APIs, manual entry, CSV exports, or later scheduled jobs. Platform APIs are the desired automation path, but availability, auth, metric names, and permissions vary by platform and may change over time.

## Decision

InfluencerOS will use API-primary analytics ingestion with a shared normalized record model.

The system should be designed around platform ingestion connectors first, but every connector writes the same creator-scoped Analytics Snapshot records. Manual entry and CSV import are first-class fallback writers into that same model.

Analytics records live under the relevant Project inside the Creator Workspace:

```text
workspace-library/creators/{creator-slug}/projects/{project-id}/analytics/
```

Analytics must attach to a Published Post Record, which attaches to an Output Package. Missing platform metrics must be recorded as absent or null, never guessed.

Each Analytics Snapshot should preserve:

- snapshot timestamp,
- source type: `api`, `manual`, `csv`, or `derived`,
- platform,
- platform post ID or URL,
- hours since publish when known,
- normalized metrics such as views, impressions, likes, comments, shares, saves, completion, retention, clicks, follows, and subscribers when available,
- raw source reference when safe to store,
- notes and known caveats.

Raw exports and API payloads may be stored locally when useful, but they must not contain tokens or secrets.

## Consequences

- API ingestion can be built early without locking the Learning OS to one platform.
- Manual entry remains available when APIs are unavailable, incomplete, delayed, or too costly to integrate.
- The learning layer can consume one normalized Analytics Snapshot model regardless of source.
- Later cron or scheduled ingestion can reuse the same connectors and records.
- The public repo should define schemas and connector contracts; real credentials and creator analytics stay in ignored Creator Workspaces or `.env`.
