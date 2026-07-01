---
name: create-reference-library
description: Use to create references/reference-library.json and provider-neutral prompt files for character, location, outfit, object, video style, voice, and brand assets.
---

# Create Reference Library

Create `references/reference-library.json` and prompt files from creator setup materials.

Use [docs/templates/creator-setup/reference-library.template.json](../../docs/templates/creator-setup/reference-library.template.json) and validate against [schemas/reference-library.schema.json](../../schemas/reference-library.schema.json).

## Purpose

The Reference Library answers: what reusable continuity assets exist, what assets are still planned, and what prompts or files should downstream generation use?

It tracks both real assets and planned assets.

## Asset Status

Use:

- `planned`: needed, no prompt or file yet
- `prompted`: provider-neutral prompt exists, no generated or imported file yet
- `user_provided`: user supplied the asset
- `generated`: created through an approved provider-backed generation call
- `approved`: accepted for downstream continuity use
- `retired`: no longer used for new work

## Required Asset Families

Select based on content strategy:

- character: identity plate, full-body turnaround sheet, macro detail card
- location: recurring spaces
- outfit: wardrobe constants
- object: meaningful props
- video_style: camera source, lens feel, aspect ratio, lighting, framing defaults, movement feel, platform finish, recurring shot families
- voice: samples or voice style notes
- brand: visual system, typography, colors, layout posture

## Size Budget

Target sizes:

- `references/reference-library.json`: one record per reusable asset; avoid duplicate variants unless they have distinct downstream use.
- Each `.prompt.md`: 120-350 words for ordinary assets; up to 500 words only for complex location or character prompts.
- Each style card `.md`: 150-400 words.

Prompts should be operational, not essays. Include role, source refs, controlled variables, avoid list, and downstream use.

## Video And Photo Style

When image or video is in scope, create a reusable `video_style` asset before finalizing the other visual prompts.

Use:

- `docs/templates/creator-setup/reference-prompts/standard-video-photo-style-prompt.md` for the compact style card prompt.

The locked style reference should become `@video_style_reference`.

It controls:

- camera source and recurring camera setup
- lens feel and image quality
- aspect ratio and platform framing
- lighting style and color temperature
- default shot distances and camera heights
- movement feel and stabilization
- skin, texture, finish, and realism rules

It must not control:

- person identity
- outfit design
- room layout
- prop or object design
- the full shot list for a specific video

Keep specific shot lists in project planning. Creator Setup may define recurring shot families only when they are stable persona habits, such as talking head, mirror fit check, desk tutorial, walking vlog, countertop detail, or gym side angle.

## Reference Image Sequence

When image or video is in scope, plan reference images in this order:

1. **User person image intake**: the user supplies one or more person images. Store or reference them as source material before planning generated character assets.
2. **Video/photo style**: use the standard video/photo style prompt unchanged to lock `@video_style_reference`.
3. **Character package**: use `docs/templates/creator-setup/reference-prompts/standard-character-asset-prompts.md` unchanged to create the three character assets: identity plate, full-body turnaround sheet, and macro detail card.
4. **Outfit references**: use `docs/templates/creator-setup/reference-prompts/standard-outfit-reference-prompt.md` unchanged for wardrobe references based on person + outfit inputs.
5. **Location references**: use `docs/templates/creator-setup/reference-prompts/standard-location-reference-prompts.md` unchanged for repeatable creator spaces.
6. **Object references**: use `docs/templates/creator-setup/reference-prompts/standard-object-reference-prompts.md` unchanged for props, products, and signature objects.

Do not rewrite these standard prompts inside the skill. Copy or adapt only the variable slots into creator-specific `.prompt.md` files while preserving the reference-scope rules.

## Character Asset Hard Rules

The first three character assets are identity-locking assets, not lifestyle images.

For identity plate, turnaround sheet, and macro detail card:

- use a flat matte neutral gray background;
- use clean studio lighting;
- use no environment, props, lifestyle setting, or location texture;
- do not apply the creator's `@video_style_reference`, location style, or brand aesthetic except for realism and accurate identity;
- do not transfer background, lighting, camera angle, or other people from the user-provided reference image.

If generated output violates these rules, keep it as `generated` or `prompted` but do not mark it `approved`. Regenerate with a stricter character prompt before generation readiness.

## Prompt Files

Provider-neutral prompts live beside the asset they describe:

- `references/character/<asset-slug>.prompt.md`
- `references/locations/<asset-slug>.prompt.md`
- `references/outfits/<asset-slug>.prompt.md`
- `references/objects/<asset-slug>.prompt.md`
- `references/video-style/<asset-slug>.prompt.md`
- `references/voice/<asset-slug>.prompt.md`
- `references/brand/<asset-slug>.prompt.md`

Point to the prompt with `prompt_path`.

## Gap Questions

Ask only for gaps that block the intended medium:

- Is the creator text-only, image, video, audio, carousel, or story-sequence?
- Is a real face required, optional, or prohibited?
- What visual traits must remain stable?
- What locations recur?
- Is voice continuity required?
- Which assets can be generated versus user-provided only?

## Provider Boundary

Drafting reference records and prompts is allowed. Generating reference images, video, audio, or renders requires explicit approval for the exact call or batch.

## Completion Criteria

Complete when every medium required by the content strategy has either approved assets or planned/prompted assets with stable IDs, source refs, usage notes, prompt paths where needed, the character/outfit/location/object prompt family has been staged when visual generation is in scope, and character identity assets obey the neutral-background hard rules before being marked `approved`.
