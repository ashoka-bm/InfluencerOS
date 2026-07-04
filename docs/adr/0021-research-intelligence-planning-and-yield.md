# ADR 0021: Research Intelligence Planning And Yield

## Status

Accepted

## Context

InfluencerOS has schema-backed research evidence, metric snapshots, findings,
idea queue entries, promotions, projects, and output provenance. The current
weak point is upstream and feedback-loop research intelligence: an agent can
explain source selection after the fact, but source choice and source yield are
not captured as validated first-class run artifacts.

The Agentic OS reference has stronger acquisition tooling and source routing.
Examples include `str-trending-research` for Reddit/X/web trend research,
query-intent tables in `research-methodology.md`, engagement-weighted synthesis
in `synthesis-guide.md`, `tool-youtube` for YouTube transcripts and metadata,
`tool-image-search` for source routing, `tool-web-screenshot`, and
Firecrawl-style scraping fallback in brand voice extraction.

InfluencerOS should adapt those practices without importing heavy connectors
prematurely. Logged-in platform access, scraping APIs, API-backed search,
scheduled jobs, and notifications require separate auth, cost, provider,
privacy, and retention decisions. YouTube is also not currently in the ADR 0020
research platform set.

## Decision

Add two run-local records:

```text
research/runs/<research-run-id>/search-plan.json
research/runs/<research-run-id>/source-yield.jsonl
```

`ResearchSearchPlan` records:

- creator and run identity,
- mode, scope, and planned/attempted platforms,
- the creator/schedule/intelligence basis for the run,
- adapters considered,
- query intent and routing basis,
- planned saved sources,
- skipped sources and skipped adapters,
- approval gates,
- future connector notes.

`ResearchSourceYield` records one checked source or query outcome:

- source key, source kind, platform, adapter, and access method,
- outcome and yield reason,
- evidence, metric, finding, and idea refs when the source produced material,
- engagement basis,
- recommended intelligence action.

Extend `research/intelligence/sources.json` with aggregate `yield_stats`,
reconciled from source-yield records for `source_intel_*` references.

Search-plan platforms are planned or attempted platforms. Research-run
platforms remain the run manifest's declared research platforms. Validation
requires `research-run.json.platforms` to be a subset of
`search-plan.json.platforms`, not an exact match.

Do not activate API-backed search, logged-in social access, scraping APIs,
scheduled research, external notifications, or YouTube as a first-class platform
in this slice.

## Consequences

- Every completed research run can answer why particular websites, platforms,
  and search terms were chosen before evidence was captured.
- Every completed research run can also answer which checked sources produced
  evidence, which were only background, and which were low-yield.
- Future connectors can be added by activating adapter IDs and mapping their
  output into `ResearchEvidence`, `MetricSnapshot`, `VideoUnderstandingPack`,
  and `ResearchSourceYield`.
- Existing queue, promotion, project, and output provenance remains unchanged.
- Research validation becomes stricter because completed runs must include a
  search plan and source-yield ledger.
- Existing fixtures and live test Creator Workspaces with completed research
  runs must gain `search-plan.json`, `source-yield.jsonl`, and source
  `yield_stats`.

## Agentic OS Divergence Test

- Agentic OS reference behavior: source-acquisition skills contain explicit
  tool-specific routing, query-intent patterns, engagement-aware scoring, and
  saved research briefs or tool outputs under project folders.
- InfluencerOS decision: adapt those practices into schema-backed pre-run
  planning and post-run yield records while keeping canonical research evidence
  in Creator Workspaces.
- Classification: adaptation.
- Reason: InfluencerOS needs deterministic creator-scoped provenance, source
  learning, and approval gates more than generic research briefs.
- Status: accepted; implementation landed 2026-07-04 with the research
  validation suite passing.
