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
   outward. Browser-visible public data only: no logged-in sessions, private
   URLs, scraping APIs, cookies, platform API credentials, scheduled jobs, or
   external notifications.
5. Capture one `evidence.jsonl` line per real post/article/creator inspected
   when it produces material evidence (`schemas/research-evidence.schema.json`)
   and metric snapshots in `metric-snapshots.jsonl`
   (`schemas/metric-snapshot.schema.json`). Every record carries this run's
   `research_run_id` and a `platform` + `platform_content_type` from the closed
   enums.
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
- Store summaries and short quoted snippets (hooks), never full captions or
  transcripts by default.
- Assign `visible_metric_signal` (source-yield) and `confidence` (evidence)
  from the Signal Tier Rubric in `docs/workflows/research-and-ideas.md`, not
  from raw numbers, so two runs judge the same post the same way. Prefer
  active engagement (saves/shares/comments) over passive reach; virality is
  not credibility, so an isolated or `farther_field` hit does not earn
  `high` on metrics alone, and open-web/trend claims cap at `medium` until
  they resolve to a primary post.
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
- Public research needs no approval; Whisper/API transcription fallback,
  first-run tool installs, and video batches require explicit user approval.
- Fix validation failures before presenting results; never leave the
  workspace invalid.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md create-research-findings "<lesson>"`.
