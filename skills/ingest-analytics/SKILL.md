---
name: ingest-analytics
description: Use after a Project has registered Published Post Records to ingest platform performance data as AnalyticsSnapshots through manual entry or the neutral InfluencerOS CSV template. Records observed metrics honestly; never calls platform APIs.
---

# Ingest Analytics

You own the analytics-ingestion step of the Learning OS. The output is one or
more `projects/<project-slug>/analytics/snapshots/<snapshot-id>.json` records
(plus optional safe raw exports under `analytics/raw/`).

Every ingestion path writes through one shared seam (ADR 0004): manual
entry, CSV import, and any future API connector produce the same normalized
AnalyticsSnapshot. Missing platform metrics are recorded as `null`, never
guessed.

## Inputs

Read (context matrix — Analytics ingestion row):

- Project manifest, registered Output Package, and the live Published Post
  Record the snapshot measures.
- The operator's platform export, dashboard reading, or manual notes.

Write only under the Project's `analytics/` folder. Never mutate Project
status, the package, or published records.

## Snapshot Contract

- `published_post_record_id` must resolve to a registered record whose
  `publication_status` attests a live post; you cannot measure a post that
  never went live.
- `platform` must match that published post record.
- Chain ids (`project_id`, `creator_profile_id`, `output_package_id`) must
  match the Project; the CSV path fills them automatically.
- `hours_since_publish` may be left `null`: it is derived from
  `snapshot_at` minus the record's `published_at` when both parse. A
  snapshot timestamped before publication is rejected.
- Use comparable timestamp forms: if both `snapshot_at` and the
  PublishedPostRecord's `published_at` parse, they must either both include
  timezone offsets or both be naive. Mixed timezone awareness is rejected
  before trusting `hours_since_publish`.
- `raw_source_ref` and `retention_curve_ref` must point to real files under
  `analytics/raw/` inside the project; raw exports must never contain
  tokens or secrets.
- Attribution stage notes (packaging, hook, body_retention, payoff, cta)
  are required prose: state what the numbers show or why a stage is
  unmeasured.

## Platform Data Caveats

Record these in snapshot `notes` so a summary never over-reads early data:

- YouTube analytics lag 2–3 days; treat snapshots younger than 72 hours as
  provisional and say so.
- LinkedIn personal accounts expose no click metrics; record `clicks: null`,
  not zero.
- Platforms expose different metric sets; a metric the platform does not
  report is `null` (absent), never `0` (observed zero).

## Commands

Manual or derived entry from a full JSON record:

```bash
python3 -m influencer_os add-analytics-snapshot <analytics-snapshot.json> --project <creator-workspace>/projects/<project-slug>
```

Bulk import from the neutral InfluencerOS CSV template
(`docs/templates/analytics/analytics-snapshot-template.csv` — map your
platform export onto its columns once; blank cells become `null`):

```bash
python3 -m influencer_os import-analytics-csv <snapshots.csv> --project <creator-workspace>/projects/<project-slug>
```

The CSV import is all-or-nothing: every row is parsed first, and a failing
row rolls back the rows this import already wrote. At rest,
`validate project` re-checks every ingestion invariant.

## Validation

After ingestion:

```bash
python3 -m influencer_os validate record analytics-snapshot <creator-workspace>/projects/<project-slug>/analytics/snapshots/<snapshot-id>.json
python3 -m influencer_os validate project <creator-workspace>/projects/<project-slug>
```

## Boundaries

- Never call platform analytics APIs; the API path exists as a designed seam
  only, and building a connector requires an explicit user request
  (Decision 3 of the Phase 2 plan).
- Never invent, extrapolate, or average metrics the platform did not report.
- Do not write Performance Summaries here; that is the next workflow.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md ingest-analytics "<lesson>"`.
