---
name: create-influencer
description: Use to run the full Creator Setup workflow from intake through accepted creator foundation, workspace files, reference requirements, provider-neutral prompts, and readiness checklist.
---

# Create An Influencer

You are the Creator Setup conductor. Your job is to turn user information and references into a complete creator foundation that downstream InfluencerOS workflows can use.

## Input Contract

Accept any combination of:

- minimal user instruction
- display name
- niche
- target audience
- guided interview answers
- master creator breakdown
- source documents
- user-provided media references
- request to generate a persona

If the user starts with minimal input, interview them and recommend defaults. If they ask the system to generate the foundation, draft it and require one whole-foundation acceptance before marking it content-ready.

## Output Contract

Produce or update:

- `context/SOUL.md`
- `context/USER.md`
- `context/MEMORY.md`
- `creator-workspace.json`
- `creator-profile.json`
- `brand_context/identity.md`
- `brand_context/soul.md`
- `brand_context/personal-brand.md`
- `brand_context/voice-samples.md`
- `references/reference-library.json`
- provider-neutral prompt files under `references/`
- copied source files under `sources/`
- `progress/setup-checklist.md`

The workflow is complete when the Creator Workspace is `content_ready` or `generation_ready` for the accepted content strategy.

## Subskills

Run these internal phases in order:

1. **Intake and provenance**: copy source files into `sources/` and record source intake metadata.
2. **Identity generation**: use `create-identity` to create `brand_context/identity.md` as the continuity and production-bible file.
3. **Soul generation**: use `create-soul` to create `brand_context/soul.md` as the psychology, belief, emotional logic, and audience-contract file.
4. **Personal brand generation**: use `create-personal-brand` to create `brand_context/personal-brand.md` as the content strategy, platform posture, monetization, disclosure, and brand-safety file.
5. **Voice samples**: use `create-voice-samples` to create `brand_context/voice-samples.md` as the concrete example file.
6. **Operational summary**: use `create-creator-profile` to create `creator-profile.json` from the accepted foundation.
7. **Runtime context**: use `create-runtime-context` to create the tiny always-loaded `context/SOUL.md`, `context/USER.md`, and `context/MEMORY.md`.
8. **Reference planning**: use `create-reference-library` to create `references/reference-library.json` entries for required real or planned assets.
9. **Reference prompt staging**: if image or video is in scope, stage prompts in this order: user person image -> default video/photo style -> three character assets -> outfits -> locations -> objects. Use the canonical prompt templates under `docs/templates/creator-setup/reference-prompts/` unchanged.
10. **Prompt drafting**: create separate provider-neutral `.prompt.md` files for missing images, locations, outfits, voice, and brand assets.
11. **Readiness check**: update `progress/setup-checklist.md` with medium-based blockers.
12. **Acceptance gate**: ask for whole-foundation approval before marking the creator `content_ready`.
13. **Generation gate**: stop before provider-backed generation unless the user approves the exact call or batch.

## Medium-Based Blockers

All creators require tiny runtime context, identity, soul, personal brand, niche, audience, content strategy, boundaries, provenance, and acceptance.

Text-first creators require brand voice, publication style, and topic/pillar strategy.

Image creators require image policy, brand or visual system reference, image style guidance, and image prompts or approved references.

Video creators require character identity plate, location reference, outfit or wardrobe reference, default video/photo style card, brand reference, and shot/motion constraints.

The default video/photo style card is a reusable `@video_style_reference`. It locks the creator's camera source, lens feel, aspect ratio, lighting, framing defaults, movement feel, and social-native finish. It may include recurring shot families, but specific shot lists belong to downstream project planning.

Voiceover creators require a voice sample or accepted synthetic voice style note plus pronunciation and tone boundaries.

Carousel and story-sequence creators require sequence style, slide or frame visual system, and text overlay policy.

## Provider Boundary

Drafting files, reference requirements, prompts, shot lists, and generation plans is allowed. Image, video, audio, render, upload, bulk generation, or paid provider calls require explicit user approval for the exact call or batch.

## Templates

Use these output shapes:

- `docs/templates/creator-setup/identity.md`
- `docs/templates/creator-setup/soul.md`
- `docs/templates/creator-setup/personal-brand.md`
- `docs/templates/creator-setup/voice-samples.md`
- `docs/templates/creator-setup/context/SOUL.md`
- `docs/templates/creator-setup/context/USER.md`
- `docs/templates/creator-setup/context/MEMORY.md`
- `docs/templates/creator-setup/creator-profile.template.json`
- `docs/templates/creator-setup/reference-library.template.json`
- `docs/templates/creator-setup/reference-prompts/standard-character-asset-prompts.md`
- `docs/templates/creator-setup/reference-prompts/standard-video-photo-style-prompt.md`
- `docs/templates/creator-setup/reference-prompts/standard-outfit-reference-prompt.md`
- `docs/templates/creator-setup/reference-prompts/standard-location-reference-prompts.md`
- `docs/templates/creator-setup/reference-prompts/standard-object-reference-prompts.md`

## Rules

*Dated corrections from wrap-up feedback (ADR 0016). Read before every run; newest last.*

- 2026-07-03: Baseline established; no corrections recorded yet.

## Self-Update

When the user flags an issue with this skill mid-run or at wrap-up:

- Scope-specific correction (one creator, or the OS persona) → record it in the applicable `SKILL.local.md`: the creator's runtime copy, or `skills/create-influencer/SKILL.local.md` for the OS persona.
- System-wide correction → add a dated entry to `## Rules` above and fix the offending step in this file.
- Log the change via `python3 -m influencer_os log-learning context/learnings.md create-influencer "<what changed>"` so it has a record.
- Promote a local rule into this base file only when repeated feedback shows it applies system-wide (ADR 0014).
