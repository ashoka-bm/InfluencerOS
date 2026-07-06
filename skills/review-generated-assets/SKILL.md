---
name: review-generated-assets
description: Use after generation or import and before packaging to run the blocking QualityReview on generation/ media: walk the closed checklist (identity consistency, continuity with plan, technical conformance, creator boundary compliance) against the asset manifest, plan, and Reference Library, and write the QualityReview record the packaging gate requires.
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

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md review-generated-assets "<lesson>"`.
