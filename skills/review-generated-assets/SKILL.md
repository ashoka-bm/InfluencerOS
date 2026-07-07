---
name: review-generated-assets
description: Use after generation or import and before packaging for the blocking QualityReview on generation/ media — the record the packaging gate requires.
---

# Review Generated Assets

You own the provider-safety quality gate (ADR 0023 Decision 5;
`docs/gates-and-reviews.md`). The output is one
`projects/<project-slug>/generation/quality-reviews/<quality_review_id>.json`
validating against `schemas/quality-review.schema.json`. This is the ONE
blocking review layer: packaging refuses any generation-sourced media asset
without a passing QualityReview covering it — generated and imported alike
(imported media is where license risk lives). Text roles are exempt.

## Inputs

- `generation/asset-manifest.json` — the assets under review and their
  provenance (approval record, plan prompt, import source/license).
- The production plan and Base Video Generation Plan — the shot sequence
  and technical envelope the assets must honor.
- The Reference Library's approved assets — the identity baseline.
- The Creator Profile boundaries.

Review the actual artifact files on disk, not just their manifest rows.

## The Closed Checklist

Each item is `pass`, `fail`, or `not_applicable` with honest notes:

- `identity_consistency` — the creator's identity (face, build, styling)
  matches the approved character/video-style Reference Library assets.
  `not_applicable` for assets with no persona in frame.
- `continuity_with_plan` — the content matches the plan's shot sequence /
  prompt intent; no invented scenes.
- `technical_conformance` — duration, aspect, and resolution fit the
  universal short-form envelope (or the format's declared target).
- `creator_boundary_compliance` — nothing crosses the Creator Profile's
  boundary rules (claims, topics, disclosure sensitivities).

`overall_verdict` must agree with the items: any `fail` forces `fail`;
`pass` requires zero failing items (validation enforces both). Use
`not_applicable` honestly — it keeps the gate meaningful across formats,
it is not a soft pass.

## Rubric Criteria Results (ADR 0025)

Walk the Production Rubric (OS `context/production-rubric.json` + creator
`production-rubric.json`) alongside the closed checklist. Record a
`rubric_criteria_results` entry per relevant criterion (pass / fail /
not_applicable with a note). Every `blocking` criterion in scope MUST be
addressed — a review that skips one cannot produce passing coverage — and a
failing blocking criterion forbids a passing verdict. Minted and proven
criteria are advisory: record them when they inform the judgment, and log a
rejection against them when they drove one.

## Record Rules

- `scope_asset_ids` name manifest rows (validation resolves them); one
  review may cover a batch.
- Filename equals `quality_review_id`. Never edit a review after packaging
  decisions were made on it; write a new one.
- A failing review is actionable: say in `notes` exactly what to regenerate
  or re-import, then a new approval record covers the redo.

## Validation

```bash
python3 -m influencer_os validate record quality-review <creator-workspace>/projects/<project-slug>/generation/quality-reviews/<id>.json
python3 -m influencer_os validate project <creator-workspace>/projects/<project-slug>
```

## Boundaries

- Never call providers; you judge artifacts that exist.
- Never weaken the gate: this review blocks packaging by design (unlike the
  advisory creative reviews, ADR 0024); only an ADR changes that.
- Do not review creative quality (hook strength, payoff) here — that is
  `review-hook-payoff`; this gate is provider-safety and conformance.

## Friction Logging (ADR 0025)

When the operator rejects a draft, prompt, or asset this skill produced — or
an attempt fails in a way a future run should avoid — log it at the moment of
friction, before moving on:

```bash
python3 -m influencer_os log-incident <creator-workspace> --type rejection \
  --recurrence-key <criterion-id> --criterion <criterion-id> \
  --source-id review-generated-assets --message "<one line: what was rejected and why>"
```

- Cite an existing Production Rubric criterion, or mint one first with
  `mint-criterion` (cite-or-mint). If the reason cannot be articulated yet,
  log with `--unclassified` and a recurrence key naming the cluster.
- Record iteration churn with `--iteration-count` when several attempts
  preceded acceptance.
- Verdicts are durable; never store the rejected material itself.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md review-generated-assets "<lesson>"`,
run from the InfluencerOS repo root: repo paths (`docs/`, `schemas/`,
`context/learnings.md`) resolve from there, never from a Creator
Workspace runtime copy.
