---
name: create-reference-library
description: Use to plan references/reference-library.json and provider-neutral prompt files for the creator's continuity assets.
dependencies:
  - elevenlabs-voice-design
---

# Create Reference Library

Create `references/reference-library.json` and prompt files from creator setup materials.

Use [docs/templates/creator-setup/reference-library.template.json](docs/templates/creator-setup/reference-library.template.json) and validate against [schemas/reference-library.schema.json](schemas/reference-library.schema.json).

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

When a generation call runs, record the generation date, tool, and any
accepted prompt deviations in the asset's `usage_notes`, keep `prompt_path`,
and leave the asset `generated` until the user explicitly approves the look.
Plan drafts require user acceptance before any readiness status changes;
validation is not approval.

## Required Asset Families

Select based on content strategy:

- character: identity plate, full-body turnaround sheet, macro detail card
- location: recurring spaces
- outfit: wardrobe constants
- object: meaningful props
- video_style: camera source, lens feel, aspect ratio, lighting, framing defaults, movement feel, platform finish, recurring shot families
- voice: ElevenLabs Voice Design prompt packages and approved/imported voice samples
- brand: supporting brand imagery and reference assets; the canonical exact
  palette, typography, name system, and layout examples live in
  `references/brand/personal-brand-board.json` and are owned by
  `personal-brand-board`

The downstream personal brand board binds production spaces to `location`
assets and signature props to `object` assets by stable `asset_id`. Plan those
entries before invoking `personal-brand-board`; do not duplicate their file
paths as free-form board data.

## Platform And Medium Derivation

Before drafting the library, derive required asset families from the accepted
public platforms and content mediums in `brand_context/personal-brand.md` and
`creator-profile.json`.

Use this mapping as setup guidance:

| Medium | Required reference material |
| --- | --- |
| text | voice samples, editorial rules, publication style, audience language, topic/pillar strategy, disclosure rules |
| image | person/avatar policy, recommended user person reference image or generated identity prompt, character/headshot assets, image style, brand visual system, recurring outfit/object references when identity-bearing |
| audio or music | ElevenLabs Voice Design prompt package for synthetic spoken continuity, imported/approved voice sample before spoken generation, pronunciation/tone boundaries, sonic identity notes, rights/disclosure constraints |
| video | image requirements plus default video/photo style, recurring locations, wardrobe/outfit references, recurring collaborators or characters, signature objects, recurring shot-family notes, ElevenLabs Voice Design prompt package |
| carousel or story_sequence | brand visual system, slide/frame visual system, text overlay policy, optional character/location references if the creator appears |

Do not treat a generated brand mood image, abstract carousel sheet, or prompt as
the production brand system. Supporting brand images may be registered here,
but visual creator readiness also requires the separately validated and
human-approved personal brand board.

Ask for public platforms early because they suggest likely mediums, but let the
accepted content strategy decide the blockers. Do not create platform-specific
publishing, scheduling, analytics, or adapter assets during setup.

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

### Atomic Object Reference Rule

Every distinct prop, product, or signature object gets its own Reference Asset,
prompt file, planned output path, generation request, and resulting reference
image. Before drafting object prompts, expand any grouped source phrase or
semantic family (for example, "desk tools" or "family objects") into one
stable asset per physical object.

An object reference sheet may show multiple angles or macro details only when
every section depicts the same single target object. It must not combine
different props, include a collection or arrangement, or add supporting
objects for styling. If a prompt names more than one distinct object, split it
before it can be presented for generation approval. Lifestyle and
character-use prompts may combine a person, location, or wardrobe reference
with exactly one target object; they do not replace that object's isolated
reference image.

Strongly recommend a user-provided person reference image for any image or video
creator. If the user does not provide one, create a planned or prompted
character identity asset instead — `asset_status` stays `planned` or
`prompted`, with the intake derivation recorded in `source`
(`source_type: derived`) and `usage_notes` — until the user approves a real
generated result.

For video creators:

- create one location asset or prompt per recurring filming space, such as a
  studio, bedroom, kitchen, office, car, gym, or outdoor route;
- create character assets or prompts for recurring collaborators, foils,
  partners, family members, or fictional characters who regularly appear;
- create object assets or prompts only for identity-attached items that need
  visual consistency across videos, such as a signature microphone, notebook,
  product, instrument, mug, mascot, tool, or wearable;
- split every selected object into its own asset and prompt even when several
  objects share one story, role, location, or source passage;
- keep one-off props in downstream project plans instead of the reference
  library.

## Character Asset Hard Rules

The first three character assets are identity-locking assets, not lifestyle images.

For identity plate, turnaround sheet, and macro detail card:

- use a flat matte neutral gray background;
- use clean studio lighting;
- use no environment, props, lifestyle setting, or location texture;
- do not apply the creator's `@video_style_reference`, location style, or brand aesthetic except for realism and accurate identity;
- do not transfer background, lighting, camera angle, or other people from the user-provided reference image.

If generated output violates these rules, keep it as `generated` or `prompted` but do not mark it `approved`. Regenerate with a stricter character prompt before allowing media generation permissions or `foundation_ready` in `media_ready` mode.

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

## ElevenLabs Voice Design Prompt Staging

When audio or video is an accepted creator medium, use
`elevenlabs-voice-design` to create:

```text
references/voice/<creator-slug>-elevenlabs-voice-design.prompt.md
```

Register the prompt file as a `voice` reference asset with
`asset_status: prompted`. `foundation_ready` for audio/video creators requires
this staged ElevenLabs prompt package; a generic voice note is not enough. This
is a human-in-the-loop prompt package only: the human copies it into ElevenLabs,
evaluates generated voice options, and brings any selected sample or voice id
back through the approved import/provider boundary. Do not call ElevenLabs,
generate audio, or mark the voice asset `generated` or `approved` from the
prompt file alone.

An approved or selected audio sample is always a second `voice` asset. Keep the
Voice Design prompt asset at `asset_status: prompted` with its `.prompt.md`
`path`. Give the sample its own asset id and audio `path`, set `prompt_path` to
the Voice Design prompt, and use `user_provided`, `generated`, or `approved` as
the sample's lifecycle status. Never replace prompt-file bytes with audio.

## Gap Questions

Ask only for gaps that block the intended medium:

- Which public platforms matter first?
- Is the creator text-only, image, video, audio, carousel, or story-sequence?
- Is a real face required, optional, or prohibited?
- Does the user have a person/avatar reference image they want the creator based
  on?
- What visual traits must remain stable?
- What locations recur?
- Who else appears regularly with the creator?
- Which objects are identity-attached enough to require consistency?
- Is voice continuity required?
- Which assets can be generated versus user-provided only?

## Provider Boundary

Drafting reference records and prompts is allowed, including ElevenLabs Voice
Design prompt files. Generating reference images, video, audio, voices, or
renders requires explicit approval for the exact call or batch.

## Completion Criteria

Complete when every medium required by the selected channels and content strategy has either approved assets or planned/prompted assets with stable IDs, source refs, usage notes, prompt paths where needed, the character/outfit/location/object prompt family has been staged when visual generation is in scope, and character identity assets obey the neutral-background hard rules before being marked `approved`. `media_ready` foundation mode and image/video generation permissions require approved or user-provided media references, not merely planned entries.

For object assets, completion additionally requires one distinct prop per
Reference Asset and per planned reference image; a grouped multi-prop prompt is
incomplete even when it validates against the schema.
