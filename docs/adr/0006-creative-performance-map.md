# ADR 0006: Creative Performance Map

## Status

Accepted

## Context

InfluencerOS needs to learn which parts of a post worked without overloading every output with duplicated metadata.

Each Output Package already has source material: scripts, prompts, production plans, reference assets, thumbnails, first frames, platform adaptations, and final artifacts. Analytics can later show whether packaging, hook, retention, payoff, or CTA performed well, but the system needs a stable way to connect those metrics back to the relevant creative decisions.

## Decision

Every Output Package must include a lightweight Creative Performance Map.

The Creative Performance Map links each major creative stage to:

- source references for the creative material,
- the intended effect of that stage,
- the primary metrics that should judge it,
- optional variant IDs when split tests or platform variants exist,
- brief notes when needed.

The required stages are:

- packaging,
- hook,
- body retention,
- payoff,
- CTA.

The map should not duplicate the raw creative material. It should point to the source files, records, or asset IDs that created the post.

Example stage entry:

```json
{
  "stage": "hook",
  "creative_decision_ref": "script.md#opening-hook",
  "intended_effect": "reduce first-three-second drop-off",
  "primary_metrics": ["retention_3s_pct", "early_drop_off_pct"],
  "variant_id": null,
  "notes": "Contrarian money myth hook"
}
```

## Consequences

- The Learning OS can attribute analytics to creative decisions without storing a heavy experiment document for every post.
- Split tests and platform variants can be represented at the stage level.
- Raw files remain the source for creative detail.
- Analytics interpretation can inspect source refs when a stage performs unusually well or poorly.
