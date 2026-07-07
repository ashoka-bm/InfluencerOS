---
name: create-soul
description: Use to draft or revise brand_context/soul.md — the creator's psychology file of values, beliefs, emotional logic, and the audience emotional contract.
---

# Create Soul

Create `brand_context/soul.md` from user input, source files, or a master creator bible.

Use [docs/templates/creator-setup/soul.md](docs/templates/creator-setup/soul.md) as the output shape.

## Purpose

`brand_context/soul.md` answers: what does this creator believe, fear, protect, soften toward, and emotionally promise the audience?

It may include private creative guidance that should influence content but not be quoted directly.

## Size Budget

Target 1,100-1,700 words. Hard maximum 2,200 words unless the user explicitly asks for a long-form psychology bible.

The template owns the section list; `validate workspace` enforces its
required headings and a 350-word floor. Size guides for the largest
sections:

- Runtime Capsule: under 200 words
- Values: 5-8 values
- Belief Matrix: 12-24 beliefs grouped by theme
- Emotional Logic: 5-8 compact rules
- Triggers And Soothers: 5-8 items each
- Behavior Under Stress: 4-6 bullets
- Audience Emotional Contract: 5-8 bullets
- Inner Material Not For Direct Publication: only what materially guides content

Do not copy a full 100+ belief source matrix. Compress it into the beliefs that actually change hooks, angles, refusals, audience promises, or trust boundaries.

## Extract

Pull from the intake:

- archetype, motivation, fear, and emotional center
- values
- belief matrix
- triggers and soothers
- stress behavior
- public tells
- humor, warmth, intimacy, and directness rules
- audience emotional contract
- private-only guidance
- source notes

## Keep Out

Move these elsewhere:

- biography and factual continuity -> `brand_context/identity.md`
- content pillars and platform strategy -> `brand_context/personal-brand.md`
- compact automation fields -> `creator-profile.json`
- media reference records -> `references/reference-library.json`

## Gap Questions

Ask only for gaps that block emotional consistency:

- What does this creator refuse to exploit?
- What should never be published directly?
- What is the public emotional promise?
- How does the creator act under pressure?
- What topics trigger rigidity, withdrawal, anger, or care?

## Completion Criteria

Complete when the file follows the template sections, stays inside the size
budget, has no placeholders, and `validate workspace` reports no soul.md
heading or word-floor failures. Drafts require user acceptance before any
readiness status changes; validation is not approval.
