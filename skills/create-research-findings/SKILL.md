---
name: create-research-findings
description: Use to run a platform-scoped research run and maintain the creator's rolling Research Findings: capture dated JSONL evidence and metric snapshots, update findings.md only on material findings, promote stable findings, and maintain research intelligence.
---

# Create Research Findings

You produce the research layer of the Research and Ideas module: dated,
sourced evidence and a concise rolling findings summary the creator can read.
Follow `docs/workflows/research-and-ideas.md`; records validate against
`schemas/`.

## Inputs

Read (context matrix — Social research row):

- `creator-profile.json` (full): niche, audience, pillars, boundaries.
- `content-schedule.json`: goals, open slots, drift checks.
- `research/findings.md` and `research/stable-findings/`: current state.
- `research/intelligence/`: sources, hashtags, search terms, reference
  creators, watchlist.
- Recent idea queue entries and creator memory summaries when relevant.

Write only under `research/` (plus the board/index projections via CLI). The
idea queue belongs to `manage-idea-queue`; promotion belongs to
`promote-idea`.

## Research Run Lifecycle

1. Choose exactly one run mode: `scheduled_needs`, `wildcard_discovery`,
   `reference_creator_watchlist`, `topic_overlap_scan`, `urgent_trend_check`,
   `queue_refresh`, or `hashtag_search_term_check`. Keep modes independently
   runnable; do not load context the mode does not need.
2. Create `research/runs/<research-run-id>/` — the folder name must equal
   `research_run_id`. Write `research-run.json`
   (`schemas/research-run.schema.json`) and a short `run-summary.md`.
3. Before browsing or capturing evidence, write `search-plan.json`
   (`schemas/research-search-plan.schema.json`). It must state the
   creator/schedule/intelligence basis, adapters considered, query intent,
   planned queries, planned sources, skipped sources, approval gates, and
   future connector notes. Search plans may name planned/deferred adapters, but
   only active public/manual/local adapters may be used in this slice. Ground
   query terms in creator context (profile, schedule, findings, intelligence,
   prior queue) and declare it in each query's required `term_basis`; do not
   seed queries with tool/brand/trend names from your own training knowledge
   that are absent from creator context — that knowledge may be stale and
   research is time-sensitive. A term you are testing rather than deriving from
   creator context must use the `hypothesis` term_basis.
4. Start from known high-signal sources (intelligence files), then branch
   outward. Allowed acquisition (ADR 0022): browser-visible public data plus
   the key-gated research-acquisition connectors below. Still forbidden:
   logged-in sessions, private URLs, scheduled jobs, and external
   notifications.

## Key-Gated Connectors (ADR 0022)

Before planning sources, run `python3 -m influencer_os list-connectors`.
Connectors whose API key is present are **standing-approved** for research
acquisition — no per-run prompt — bounded by a per-run paid-call cap and the
`INFLUENCER_OS_DISABLE_PAID_CONNECTORS` kill switch:

- `reddit_openai` (`reddit_api_or_search`, needs `OPENAI_API_KEY`): Reddit
  threads with real upvotes/comments.
- `x_xai` (`x_api`, needs `XAI_API_KEY`): X posts with inline engagement.
- `firecrawl_web` (`firecrawl_public_web`, needs `FIRECRAWL_API_KEY`): rendered
  public web/JS pages.
- `linkedin_apify` (`linkedin_apify`, needs `APIFY_API_KEY`): public LinkedIn
  profile posts.
- `youtube_data_api` (`youtube_data_api`, needs `YOUTUBE_API_KEY`): public
  YouTube video/channel discovery with visible views, likes, and comments.

Usage inside a run:

- Declare the connector in `search-plan.json` `adapters_considered` with its
  adapter ID, `access_method` (`api_backed`/`scraping_api`),
  `adapter_status: "active"`, and `decision: "use_now"` only when
  `list-connectors` shows it available; otherwise mark it
  `skip_this_run`/`future_connector` and fall back to public web.
- Fetch with
  `python3 -m influencer_os research-fetch <reddit|x|firecrawl|linkedin|youtube-search|youtube-channel> "<topic-url-or-channel>" --out .tmp/<run-id>-<connector>.json`,
  e.g. `python3 -m influencer_os research-fetch youtube-search "<topic>" --days 30 --max-results 10 --out .tmp/<run-id>-youtube.json`
  or `python3 -m influencer_os research-fetch youtube-channel "@<handle-or-UC-id>" --days 30 --out .tmp/<run-id>-youtube-channel.json`.
  The result validates against `schemas/research-fetch-result.schema.json` and
  is a transient candidate list, never canonical state.
- Curate: promote only creator-fit candidates into `evidence.jsonl`; map real
  engagement (`score`/`num_comments`, `likes`/`reposts`/`replies`,
  `views`/`likes`/`comments`) into `metric-snapshots.jsonl` records; judge
  tiers by the Signal Tier Rubric as usual. Record one `source-yield.jsonl`
  line per connector query with the connector's `adapter_id` and access
  method, including low-yield outcomes, and note `capped`/`truncated` results
  honestly.
- Use YouTube for topic/trend discovery, reference-channel latest uploads, and
  public video metadata. Do not treat titles/descriptions as full video
  understanding: if the actual video content matters, create a
  VideoUnderstandingPack through the existing video-understanding boundary
  (no transcripts, YouTube Analytics, or logged-in access via this connector).
5. Capture one `evidence.jsonl` line per real post/article/creator inspected
   when it produces material evidence (`schemas/research-evidence.schema.json`)
   and metric snapshots in `metric-snapshots.jsonl`
   (`schemas/metric-snapshot.schema.json`). Every record carries this run's
   `research_run_id` and a `platform` + `platform_content_type` from the closed
   enums. Source evidence is not the same as target distribution platforms:
   public-web pages, institutional articles, research articles, and manual
   citations may use `platform: "public_web"` with
   `platform_content_type` such as `public_web_page`,
   `institutional_article`, or `research_article`.
6. Write one `source-yield.jsonl` line per checked source or query outcome
   (`schemas/research-source-yield.schema.json`). Include low-yield and
   background-only attempts so future runs can avoid repeated source waste.
7. Declare the run's `outputs` exactly — all five arrays are present and
   precise. `evidence_ids` and `metric_snapshot_ids` list precisely the ids
   written to this run's JSONL files (validation reconciles both
   directions); `finding_ids`, `idea_queue_entry_ids`, and
   `research_intelligence_updates` list every finding, queue entry, and
   intelligence file this run created or updated. An empty array is correct
   only when the run truly touched none — leaving one empty after a change
   hides provenance.
8. When real videos matter, create a Video Understanding Pack before final
   synthesis (see the `influencer-os` Video Understanding Requirements and
   tool boundary; run `/watch` with `--no-whisper` unless the user approved
   the exact transcription fallback).

## Evidence Quality

- Prefer real post URLs, named accounts, posting dates or observed ages,
  visible metrics, and creator-relative outperformance over trend articles.
- Never label public-web pages, institutional sources, research articles, or
  manual citation evidence as YouTube just to satisfy schema. Use public-web
  source provenance and keep target distribution platforms separate in planning
  records.
- Store summaries and short quoted snippets (hooks), never full captions or
  transcripts by default.
- Assign `visible_metric_signal` (source-yield) and `confidence` (evidence)
  from the Signal Tier Rubric in `docs/workflows/research-and-ideas.md`, not
  from raw numbers, so two runs judge the same post the same way. Prefer
  active engagement (saves/shares/comments) over passive reach; virality is
  not credibility, so an isolated or `farther_field` hit does not earn
  `high` on metrics alone, and open-web/trend claims cap at `medium` until
  they resolve to a primary post.
- Do not create metric snapshots for sources with no real visible metrics. If
  only background/public-web evidence exists and no native platform metrics were
  captured, ask the user whether to proceed with background-only evidence before
  promoting findings or ideas.
- Mark `confidence` and `limitations` honestly; flag thin evidence instead
  of hiding it behind confident findings.

## Findings Discipline

- `last_ran` in the `findings.md` frontmatter updates on every run;
  `last_updated` only when a material finding changes the rolling summary.
  A no-material run still updates `last_ran` but leaves the body,
  `last_updated`, and finding fields unchanged — that is what keeps "not
  checked recently" distinguishable from "checked, nothing new".
- Keep the `findings.md` body under `summary_char_limit`. Organize by topic
  cluster first with platform notes inside; keep a short `Watch Now` section
  for time-sensitive opportunities.
- Every material finding gets a stable `finding_id` listed in the
  frontmatter. Stale or declining material moves out of the rolling summary
  unless strategically important.
- Synthesize from captured evidence, not prior knowledge: every claim traces
  to an evidence line. State corroboration breadth (how many independent
  sources, creators, and platforms carry the pattern) and record any
  counter-signal — see the Synthesis Discipline in
  `docs/workflows/research-and-ideas.md`. If everything agrees perfectly,
  suspect over-simplification rather than total consensus.
- Promote a finding to `research/stable-findings/<stable-finding-id>.md`
  (`schemas/stable-finding.schema.json`) only when repeated research proves
  it durable.

## Research Intelligence

- Suggest additions, updates, and removals with usefulness scores and
  rationale; hashtags and search terms stay platform-scoped.
- Adding or removing a user-approved core reference creator requires user
  approval. Present zero-usefulness user-approved items as removal
  candidates; never silently delete them.

## Maintenance

After writing records:

```bash
python3 -m influencer_os validate research <creator-workspace>
python3 -m influencer_os rebuild-index <creator-workspace>
python3 -m influencer_os prune <creator-workspace>
```

`prune` is dry-run by default; include its report in the run summary and
pass `--apply` only when the user has approved the cleanup. It never touches
evidence a queue entry, promotion, or project references.

## Rules

- Date the research and cite sources; trend claims stay tied to evidence.
- Audience and niche are creator-profile inputs, never invented here.
- Public research needs no approval; ADR 0022 key-gated connectors are
  standing-approved by key presence. Whisper/API transcription fallback,
  first-run tool installs, logged-in access, and video batches still require
  explicit user approval.
- Fix validation failures before presenting results; never leave the
  workspace invalid.
- 2026-07-07: Never label public-web or manual citation evidence as YouTube.
  Record public-web source evidence separately from target distribution
  platforms, avoid metric snapshots where there are no real visible metrics,
  and ask the user whether to proceed when only background/public-web evidence
  exists.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md create-research-findings "<lesson>"`.
