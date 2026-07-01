---
name: create-identity
description: Use to turn creator intake material into identity.md: biography, origin, public role, continuity facts, recurring world, voice examples, and contradiction checks.
---

# Create Identity

Create `brand_context/identity.md` from user input, source files, or a master creator bible.

Use [docs/templates/creator-setup/identity.md](../../docs/templates/creator-setup/identity.md) as the output shape.

## Purpose

`brand_context/identity.md` answers: who is this creator, what is durably true about them, and what continuity must future agents preserve?

It is not the place for the full psychology model, brand strategy, content calendar, or reference asset inventory.

## Size Budget

Target 900-1,400 words. Hard maximum 1,800 words unless the user explicitly asks for a long-form identity bible.

Keep:

- Runtime Capsule: under 200 words
- Identity Snapshot: 6-9 bullets
- Origin Story: 2-4 short paragraphs
- Current Circumstances: 5-8 bullets
- Formative Moments: 3-5 items, each with the content behavior it creates
- Recurring World: 8-15 compact bullets
- Continuity Rules: 6-12 bullets
- Contradictions To Avoid: 6-12 bullets

Do not preserve every source detail. Preserve only facts that affect continuity, content behavior, relationship boundaries, visual recurrence, or contradiction checks.

## Extract

Pull from the intake:

- display name, pronouns, public age or age range
- origin, education, career, family, and current circumstances
- formative moments
- public role and relationship to audience
- recurring places, objects, rituals, motifs, phrases, and sign-offs
- public worldview
- pointer to `brand_context/voice-samples.md`
- continuity rules and contradictions to avoid
- source notes

## Keep Out

Move these elsewhere:

- deep motivations, fears, triggers, soothers -> `brand_context/soul.md`
- platform strategy, pillars, monetization, partnerships -> `brand_context/personal-brand.md`
- operational summaries -> `creator-profile.json`
- concrete voice examples -> `brand_context/voice-samples.md`
- image, voice, location, wardrobe asset records -> `references/reference-library.json`

## Gap Questions

Ask only for gaps that block continuity:

- What facts must never change?
- What can be invented by the LLM?
- Which relationships are public?
- What privacy rules apply?
- What claims require proof?

## Completion Criteria

Complete when the file follows the template sections, stays inside the size budget, has no placeholders, source notes are present, and an agent can use it to avoid breaking biography, public role, relationships, and recurring-world continuity.
