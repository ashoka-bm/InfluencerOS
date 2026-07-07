---
name: create-production-plan
description: Use after an AppliedSocialTemplate exists to route a Project to its exact format-specific production plan schema, including article and thread text plans, and to draft a provider-neutral BaseVideoGenerationPlan only when short-form video generation is planned.
---

# Create Production Plan

You own conductor phases 8-9: Format-Specific Production Plan and Base
Generation Plan. The output always includes
`projects/<project-slug>/plan/production-plan.json`; short-form video also
requires `projects/<project-slug>/plan/generation-plan.json`.

## Inputs

Read (context matrix — Production planning and Generation planning rows):

- Project manifest, evidence brief, Applied Social Template, and locked Idea
  Promotion.
- Creator Profile, identity, soul, personal brand, voice samples, and
  reference library as needed for creator continuity.
- Research Findings, evidence refs, metric snapshots, and Video
  Understanding Packs when they affected the promoted idea.

Write only under the Project's `plan/` folder.

## Routing Contract

The Project is one content unit. Its `content_unit_type` must map to exactly
one target format:

| `content_unit_type` | `target_format_id` | Plan schema |
| --- | --- | --- |
| `short_form_video` | `format_short_form_video` | `micro-journey-video-plan` plus `base-video-generation-plan` |
| `carousel` | `format_carousel` | `carousel-plan` |
| `single_image_post` | `format_single_image_post` | `single-image-post-plan` |
| `story_sequence` | `format_story_sequence` | `story-sequence-plan` |
| `article` | `format_article` | `article-plan` |
| `thread` | `format_thread` | `thread-plan` |

If a Project's unit type and target format do not match, stop and fix the
Project or supersede the promotion. Do not route around the mismatch.

## Format Rules

- Short-form video: create a Micro-Journey Video Plan shaped by the
  Content Beat Spine (ADR 0024) — `hook`, one `retain` beat holding
  `setup` and `escalation`, `payoff`, `cta_or_loop`, and
  `intended_emotion` — plus shot logic, continuity requirements, and a
  provider-neutral Base Video Generation Plan. The generation plan is a
  reviewable plan, not provider approval.
- Carousel: create slide-level visual beats, first-slide hook, creator
  continuity, and generation notes.
- Single image post: create central visual idea, composition, avatar or scene
  requirements, text overlay policy, and generation prompt.
- Story sequence: create frame-level moments, sequence arc, text/sticker
  notes, creator continuity, and generation notes.
- Article: create the working title, deck, thesis, section plan, evidence to
  use, voice/style constraints, CTA, and review notes. No Base Video
  Generation Plan is required.
- Thread: create the opening post, throughline, ordered posts, evidence to
  use, voice/style constraints, CTA, and review notes. No Base Video
  Generation Plan is required.
- Article, carousel, and thread plans may carry an optional
  `format_subtype` (article: `essay` / `reported_feature` /
  `newsletter_dispatch`; carousel: `designed_slides` / `photo_set`;
  thread: `chain` / `single_post`). Set it when the subtype changes the
  authoring craft; omit it otherwise.

## Provenance Rules

- `idea_promotion_id` must equal the Project's locked upstream promotion.
- `applied_social_template_id` must equal the applied template in the same
  Project.
- Carry forward the creative elements, evidence IDs, and avoid notes from the
  promotion and evidence brief. Do not invent trend claims.
- Intent is resolved by reference (ADR 0024): the promotion's
  `intended_emotion` and `core_message` are canonical. Where a plan schema
  carries `intended_emotion` (micro-journey), restate the promotion's value
  verbatim — `validate project` fails an overriding copy. Never add intent
  fields to plans that lack them.
- Preserve creator boundaries; text plans must not introduce medical,
  financial, legal, or disclosure-sensitive claims without source support and
  explicit review notes.

## Validation

After writing the plan records:

```bash
python3 -m influencer_os validate record <plan-schema> <creator-workspace>/projects/<project-slug>/plan/production-plan.json
python3 -m influencer_os validate project <creator-workspace>/projects/<project-slug>
```

For short-form video, also validate the provider-neutral generation plan:

```bash
python3 -m influencer_os validate record base-video-generation-plan <creator-workspace>/projects/<project-slug>/plan/generation-plan.json
```

## Provider Boundary

Drafting plans, prompts, shot lists, article outlines, and thread copy plans
is allowed. Provider-backed image, video, audio, render, upload, paid, or
irreversible calls require exact user approval for the call or batch.

## Friction Logging (ADR 0025)

When the operator rejects a draft, prompt, or asset this skill produced — or
an attempt fails in a way a future run should avoid — log it at the moment of
friction, before moving on:

```bash
python3 -m influencer_os log-incident <creator-workspace> --type rejection \
  --recurrence-key <criterion-id> --criterion <criterion-id> \
  --source-id create-production-plan --message "<one line: what was rejected and why>"
```

- Cite an existing Production Rubric criterion, or mint one first with
  `mint-criterion` (cite-or-mint). If the reason cannot be articulated yet,
  log with `--unclassified` and a recurrence key naming the cluster.
- Record iteration churn with `--iteration-count` when several attempts
  preceded acceptance.
- Verdicts are durable; never store the rejected material itself.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md create-production-plan "<lesson>"`,
run from the InfluencerOS repo root: repo paths (`docs/`, `schemas/`,
`context/learnings.md`) resolve from there, never from a Creator
Workspace runtime copy.
