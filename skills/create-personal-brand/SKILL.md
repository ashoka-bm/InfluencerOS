---
name: create-personal-brand
description: Use to draft or revise brand_context/personal-brand.md — positioning, audience, content strategy, surfaces, monetization, and boundaries.
---

# Create Personal Brand

Create `brand_context/personal-brand.md` from user input, source files, or a master creator bible.

Use [docs/templates/creator-setup/personal-brand.md](docs/templates/creator-setup/personal-brand.md) as the output shape.

## Purpose

`brand_context/personal-brand.md` answers: what is this creator's market position, audience promise, content strategy, surface strategy, and commercial boundary?

This is the source of truth for Content Strategy. `creator-profile.json` stores the operational summary.

## Size Budget

Target 1,300-2,000 words. Hard maximum 2,500 words unless the user explicitly asks for a full brand strategy bible.

The template owns the section list; `validate workspace` enforces its
required headings and a 500-word floor. The Extract list below is the
content spec. Size guides:

- Runtime Capsule: under 250 words
- Content Pillars: 3-7 pillars, each 4-6 bullets
- Surface Strategy: 2-5 surfaces
- Medium Strategy: only mediums in scope

Do not duplicate full biography, psychology, voice samples, or reference asset inventory. Use links to those files.

## Extract

Pull from the intake:

- positioning and audience promise
- primary and secondary audiences
- niche and category
- audience language, including exact phrases and words to avoid
- jobs-to-be-done
- tried alternatives
- objections
- trigger moments
- trusted sources and audience hangouts
- negative audience
- proof and trust cues
- content surfaces
- content mediums
- platform-to-medium mapping: which selected surfaces require text, image,
  audio, video, carousel, or story-sequence support
- content pillars with priorities
- surface strategy by platform or channel
- medium strategy by text, image, video, audio, carousel, and story sequence
- reference-needs signals by medium, including person/avatar reference image
  availability, recurring locations, recurring collaborators or characters,
  signature objects, wardrobe constants, voice/sonic needs, and publication
  style needs
- voice and editorial rules
- visual brand
- monetization and partnership rules
- disclosure rules
- safety and claims boundaries
- growth goals
- source notes

## Keep Out

Move these elsewhere:

- full biography and recurring-world continuity -> `brand_context/identity.md`
- inner psychology and emotional logic -> `brand_context/soul.md`
- compact automation fields -> `creator-profile.json`
- asset lifecycle records -> `references/reference-library.json`

## Gap Questions

Ask only for gaps that block strategy:

- Which surfaces matter first?
- Which content mediums are in scope?
- Which public platforms imply text, image, audio, video, carousel, or
  story-sequence content?
- What exact audience language should shape strategy?
- Which jobs-to-be-done and tried alternatives define the audience promise?
- Which objections and trigger moments most change the content strategy?
- Who is the negative audience, and which trusted sources and proof and
  trust cues earn belief?
- Which pillars are primary, secondary, or experimental?
- What should research optimize for?
- Which partnerships are prohibited?
- What should the creator not optimize for?
- If image or video is in scope, does the user have a person/avatar reference
  image, and which locations, collaborators, objects, or outfits need visual
  consistency?

## Completion Criteria

Complete when the file follows the template sections, stays inside the size
budget, has no placeholders, and `validate workspace` reports no
personal-brand.md heading or word-floor failures. Drafts require user
acceptance before any readiness status changes; validation is not approval.
