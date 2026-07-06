---
name: create-performance-summary
description: Use after a published Project has mature AnalyticsSnapshots to author the PerformanceSummary that maps observed results to the five attribution stages (packaging, hook, body retention, payoff, CTA). Interprets evidence against the Performance Benchmark Rubric; never invents metrics.
---

# Create Performance Summary

You own the performance-summary step of the Learning OS. The output is one
schema-valid `projects/<project-slug>/performance-summary.json` per Project —
the interpretive record that turns raw snapshots into stage-level findings,
distilled lessons, and recommended next actions.

This is a judgment skill, not a CLI wrapper: you author the record directly
and `validate project` is the enforcement seam. There is no summary write
command.

## Inputs

Read (context matrix — Performance summary row):

- The Project's Creative Performance Map (inside the registered Output
  Package) — what the package *predicted* each stage would do.
- Every Published Post Record and every AnalyticsSnapshot for the project.
- The production plan and applied template when interpreting why a stage
  behaved as it did.
- Lazily, `memory/learnings.md` — only to judge whether a result repeats an
  existing lesson (informing `evidence_strength`), never to import old
  conclusions as new findings.

Write only `performance-summary.json` at the project root. Never mutate
Project status, snapshots, published records, or the package.

## Summary Contract

- `evidence_refs` must resolve inside this project: `output_package_id` to
  the registered package, every `published_post_record_id` and
  `analytics_snapshot_id` to records on disk. Cite every snapshot you
  actually used — provenance is the point.
- `stage_findings` covers each of the five stages exactly once: packaging,
  hook, body_retention, payoff, cta. A duplicated or missing stage fails
  validation.
- Wait for mature data: snapshots younger than the platform reporting lag
  (YouTube lags 2–3 days) support only `confidence: low` findings. Say in
  `result` when a stage is judged from provisional data. `validate project`
  WARNs once a published project has snapshots at least 72h post-publish
  and no summary.
- A metric the platform never reported (`null`) is *unmeasured*: write the
  stage finding as unmeasured with `confidence: low`, never as zero or as a
  guessed value.

## Performance Benchmark Rubric

Anchor `stage_findings` interpretations to this closed rubric (adapted from
the Agentic OS `mkt-content-analytics` reference; recorded in
`docs/os-construction/agentic-os-alignment.md`), the way the Signal Tier
Rubric anchors research confidence. Judge against the band, then against
the creator's own baseline once 3+ posts exist — a "good" absolute number
that underperforms the creator's norm is a decline, and vice versa.

| Metric | Needs work | Good | Great | Excellent |
| --- | --- | --- | --- | --- |
| Click-through rate (YouTube-class packaging) | <4% | 4–6% | 6–10% | 10%+ |
| Retention (avg % of video watched) | <40% | 40–50% | 50–60% | 60%+ |
| Engagement rate (LinkedIn) | <2% | 2–5% | 5–10% | 10%+ |
| Engagement rate (Instagram/TikTok-class) | <3% | 3–6% | 6–10% | 10%+ |

Platforms without a rubric row (X, Substack, Medium, Reddit, Facebook —
ADR 0020 set): interpret against the creator's own recorded baselines and
say the band is unanchored; do not borrow another platform's thresholds
silently.

## Stage Remediation Mapping

When a stage underperforms, `recommended_next_actions` come from this
mapping — the observed metric names the creative decision to revisit:

| Signal | Stage | Remediation direction |
| --- | --- | --- |
| Low CTR | packaging | title/caption framing, packaging specificity |
| High impressions, low clicks | packaging | thumbnail or first-frame |
| Early retention drop (3s / early drop-off) | hook | opening hook, first-frame pattern, structure |
| Mid-video retention sag | body_retention | pacing, tighten the demonstration |
| Low completion / no rewatch | payoff | payoff visibility, loop-friendliness |
| Limited reach | packaging / cta | hashtags, distribution, posting time |
| Views without profile visits / link clicks | cta | CTA clarity, CTA-to-content fit |

Recommendations must trace to a cited metric; do not recommend fixing a
stage whose metrics were unmeasured — recommend measuring it.

## Lessons And Evidence Strength

- `distilled_lessons[].evidence_strength` is honest scope: one post's
  result is `single_post_signal`; claim `multi_post_pattern` only when the
  cited evidence spans multiple published posts; use `weak_signal` when
  data is provisional or incomplete (ADR 0008: don't overfit to one post).
- Lessons are creator-relative: phrase what this creator should keep or
  change, not generic platform advice.

## Semantic Lookup Call

- `semantic_lookup.summary_text` is the retrievable narrative: 2–4
  sentences a future low-context agent can act on without opening the
  snapshots.
- Set `index_allowed: false` when the summary text contains anything that
  should not surface in cross-workflow recall (sensitive creator context,
  partner terms, unreleased plans). Raw metrics stay out of the lookup by
  construction either way.

## Authoring Steps

1. Read the package's Creative Performance Map, the published records, and
   all snapshots; note which metrics are null and which snapshots are
   provisional.
2. Author `performance-summary.json` against
   `schemas/performance-summary.schema.json` (example:
   `examples/performance-summary.example.json`).
3. Validate:

```bash
python3 -m influencer_os validate record performance-summary <creator-workspace>/projects/<project-slug>/performance-summary.json
python3 -m influencer_os validate project <creator-workspace>/projects/<project-slug>
```

## Boundaries

- Never invent, extrapolate, or average metrics that were not recorded in
  snapshots; interpretation is allowed, fabrication is not.
- One summary per Project; revise the existing file rather than writing a
  parallel record. No markdown twin — the JSON is canonical (Decision 4).
- Do not append lessons to `memory/learnings.md` or promote facts to
  `context/MEMORY.md` here; that is `distill-creator-learning` (Phase 2
  slice 4).

## Rules

*Dated corrections from wrap-up feedback (ADR 0016). Read before every run; newest last.*

- 2026-07-05: Baseline established; no corrections recorded yet.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md create-performance-summary "<lesson>"`.
