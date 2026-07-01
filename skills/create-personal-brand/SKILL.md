---
name: create-personal-brand
description: Use to turn creator intake material into personal-brand.md: positioning, audience, content strategy, pillars, surface strategy, monetization, disclosure, and boundaries.
---

# Create Personal Brand

Create `brand_context/personal-brand.md` from user input, source files, or a master creator bible.

Use [docs/templates/creator-setup/personal-brand.md](../../docs/templates/creator-setup/personal-brand.md) as the output shape.

## Purpose

`brand_context/personal-brand.md` answers: what is this creator's market position, audience promise, content strategy, surface strategy, and commercial boundary?

This is the source of truth for Content Strategy. `creator-profile.json` stores the operational summary.

## Size Budget

Target 1,300-2,000 words. Hard maximum 2,500 words unless the user explicitly asks for a full brand strategy bible.

Keep:

- Runtime Capsule: under 250 words
- Brand Snapshot: compact bullets, not prose
- Audience: primary, secondary, pains, desires, sophistication, boundaries
- Content Strategy: concrete surfaces, mediums, priorities, intended audience response, research implications, revisit cadence
- Content Pillars: 3-7 pillars, each 4-6 bullets
- Surface Strategy: 2-5 surfaces
- Medium Strategy: only mediums in scope
- Monetization And Partnerships: allowed/prohibited categories and acceptance tests
- Boundaries And Safety: claims, privacy, disclosure, and legal/medical/financial limits
- Growth Goals: what to optimize for and what not to optimize for

Do not duplicate full biography, psychology, voice samples, or reference asset inventory. Use links to those files.

## Extract

Pull from the intake:

- positioning and audience promise
- primary and secondary audiences
- niche and category
- content surfaces
- content mediums
- content pillars with priorities
- surface strategy by platform or channel
- medium strategy by text, image, video, audio, carousel, and story sequence
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
- Which pillars are primary, secondary, or experimental?
- What should research optimize for?
- Which partnerships are prohibited?
- What should the creator not optimize for?

## Completion Criteria

Complete when the file follows the template sections, stays inside the size budget, and research, idea generation, format selection, brand safety, monetization checks, and medium-based blockers can be derived from the file.
