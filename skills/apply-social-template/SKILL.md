---
name: apply-social-template
description: Use after a human-approved Idea Promotion creates a Project and before production planning: choose a format-compatible social template or production structure, adapt it to the promoted idea, and write the AppliedSocialTemplate record.
---

# Apply Social Template

You own conductor phase 7: Applied Social Template or Production Structure.
The output is `projects/<project-slug>/plan/applied-template.json`,
validated by `schemas/applied-social-template.schema.json`.

## Inputs

Read (context matrix — Template application row):

- The Project manifest and its locked `source_refs.idea_promotion_id`.
- The locked Idea Promotion, queue entry, evidence brief, and current
  Research Findings needed to understand the payoff.
- Creator Profile and relevant brand context for audience, boundaries, and
  voice fit.
- Social template library entries or an existing creator-specific structure
  when one is already approved.

Write only `plan/applied-template.json` inside the Project.

## Selection Rules

- Use the Project's single `target_formats[0]` as `target_format_id`.
- Pick a structure that improves retention, clarity, or reader progression
  for the promoted idea; do not use a template only because it exists.
- If several structures would materially change the meaning, burden, or
  target format, present the options and ask before writing.
- If the user already approved a specific structure in the promotion package,
  use it unless it conflicts with the Project's format or creator boundaries.
- Text formats may still use the same high-level structures as visual posts;
  the applied beats should describe reader progression rather than shots or
  slides.

## Record Rules

- `idea_promotion_id` must equal the Project's locked upstream promotion.
- `target_format_id` must equal the Project target format.
- `applied_beats` must map every important template beat to the promoted
  idea. Each beat answers a concrete viewer or reader question.
- `application_rationale` should explain why this structure fits the payoff,
  not restate the premise.

## Validation

After writing the record:

```bash
python3 -m influencer_os validate record applied-social-template <creator-workspace>/projects/<project-slug>/plan/applied-template.json
python3 -m influencer_os validate project <creator-workspace>/projects/<project-slug>
```

`validate project` may still fail until the downstream production plan exists;
fix template-specific failures before handing off to `create-production-plan`.

## Boundaries

- Do not write the production plan.
- Do not create or edit an Idea Promotion.
- Do not call image, video, audio, render, upload, or paid providers.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md apply-social-template "<lesson>"`.
