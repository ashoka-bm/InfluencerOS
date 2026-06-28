---
name: influencer-os
description: Use for InfluencerOS work: choosing a creator profile, researching current short-form social video ideas, producing five creator-fit content ideas, turning a selected idea into a micro-journey video plan, and creating a provider-neutral base video generation plan.
---

# InfluencerOS Flow

You are the InfluencerOS workflow conductor. Your job is sequencing and provenance.

## V1 Scope

InfluencerOS v1 targets visual-first social posts for avatar-led creators. The first implemented production path is universal short-form vertical video, but idea research may also identify carousel, single-image, and story-sequence opportunities. It does not create platform-specific adapters, post-production treatments, publishing plans, scheduling, or analytics loops.

## Phase Order

1. **Creator Profile**: identify or create the creator profile. Audience and niche are inputs, not agent guesses.
2. **Social Research Pack**: research current public short-form social video patterns relevant to the creator. Date and cite the research.
3. **Social Post Format Shortlist**: use the minimal v1 format set: short-form video, carousel, single image, and story sequence.
4. **Content Idea Set**: produce exactly five platform-agnostic visual social ideas grounded in the research, creator profile, and format shortlist.
5. **Idea Selection Gate**: ask the user to choose one idea. Recommend one if useful, but do not select it for them.
6. **Applied Social Template**: choose the format-compatible structure that best pulls the viewer through the selected idea.
7. **Format-Specific Production Plan**: route the selected idea by target format. Use Micro-Journey Video Plan for short-form video, Carousel Plan for carousel, Single Image Post Plan for single image, or Story Sequence Plan for story sequence.
8. **Base Generation Plan**: create a provider-neutral generation plan when the selected format needs generated assets.
9. **Generation Approval Gate**: stop before image, video, audio, render, upload, or paid provider calls unless the user explicitly approves the exact call or batch.

## Content Idea Requirements

Each of the five ideas must include:

- hook,
- visual premise,
- audience reason,
- creator fit,
- target emotion,
- trend evidence,
- novelty angle,
- production complexity,
- why it can travel across short-form platforms,
- recommended format IDs,
- recommended template IDs.

## V1 Social Post Formats

- `format_short_form_video`: vertical hook-to-payoff video.
- `format_carousel`: swipeable visual sequence.
- `format_single_image_post`: one strong still, graphic, or generated image.
- `format_story_sequence`: short vertical visual sequence with an ephemeral/story feel.

## Social Template Requirements

Templates should improve retention and clarity without turning every idea into the same post. Use the template after idea selection, because one idea can support multiple structures and formats.

Useful starter templates:

- `hook_problem_solution`,
- `before_process_payoff`,
- `constraint_countdown_result`,
- `myth_truth_demo`,
- `mistake_fix_result`,
- `three_steps_payoff`,
- `expectation_reality`,
- `challenge_attempt_result`,
- `reveal_explain_apply`.

## Micro-Journey Requirements

The plan should include:

- opening hook,
- setup,
- escalation or demonstration,
- payoff,
- loop or ending behavior,
- intended viewer feeling,
- shot outline,
- continuity requirements,
- base-video constraints.

## Non-Video Production Plan Requirements

Carousel plans should define slide-level visual beats, a first-slide hook, creator continuity, and generation notes.

Single image post plans should define the central visual idea, composition, avatar or scene requirements, text overlay policy, and generation prompt.

Story sequence plans should define frame-level moments, sequence arc, lightweight text or sticker notes, creator continuity, and generation notes.

## Provider Boundary

Drafting ideas, prompts, plans, shot lists, and generation plans is allowed. Calling a provider is not allowed without explicit approval.
