# ADR 0027: YouTube Data API Research Connector

## Status

Accepted

## Context

InfluencerOS previously named `youtube_data_api` as a planned adapter because
YouTube was not in the ADR 0020 research platform set and API-backed adapters
needed explicit auth, quota, retention, and approval decisions. The operator has
now configured `YOUTUBE_API_KEY` and approved using the YouTube Data API for
lightweight public research acquisition.

The connector is useful for topic and trend research because it can search
recent videos, resolve channels and handles, inspect latest uploads, and capture
public video statistics. It does not provide owned-channel analytics, publishing,
scheduling, or a simple public transcript path.

## Decision

Activate `youtube_data_api` as a key-gated research-acquisition connector:

- provider: YouTube Data API v3
- env var: `YOUTUBE_API_KEY`
- access method: `api_backed`
- standing approval: key presence, bounded by the existing connector call cap
  and kill switch
- canonical platform: `youtube`
- content types: `youtube_video`, `youtube_short`, `youtube_comment`

The connector may be used inside explicit, user-initiated research runs. It
maps provider responses into transient `ResearchFetchResult` candidates, which
the `create-research-findings` skill curates into `ResearchEvidence`,
`MetricSnapshot`, and `ResearchSourceYield` records.

The first implementation supports video search and channel latest-upload
fetches. Comment fetching may be added behind the same adapter when needed for
audience-language research. Transcripts remain outside this connector and must
use the VideoUnderstandingPack boundary when video content analysis is needed.

## Consequences

- YouTube can now contribute public trend/topic evidence with visible metrics.
- Research schemas and validators must include `youtube` as a research platform.
- The standing-approval exemption remains exact: only `youtube_data_api` with
  `api_backed` is approved. Logged-in access, YouTube Analytics API, captions
  downloads, scheduled jobs, and publishing remain out of scope.
- Quota usage is bounded by the existing call budget and must be summarized in
  run output through `calls_used`, `source-yield.jsonl`, and `run-summary.md`.
