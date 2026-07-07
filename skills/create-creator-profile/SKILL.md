---
name: create-creator-profile
description: Use to create creator-profile.json as the schema-backed operational summary from accepted runtime context, brand_context files, and reference-library.json.
---

# Create Creator Profile

Create `creator-profile.json` only after the foundation files are drafted or accepted.

Use [docs/templates/creator-setup/creator-profile.template.json](docs/templates/creator-setup/creator-profile.template.json) and validate against [schemas/creator-profile.schema.json](schemas/creator-profile.schema.json).

## Purpose

`creator-profile.json` is the operational summary for automation. It is not the full identity, soul, or brand file.

## Inputs

Read:

- `context/SOUL.md`, `context/USER.md`, and `context/MEMORY.md`, when present
- `brand_context/identity.md`
- `brand_context/soul.md`
- `brand_context/personal-brand.md`
- `brand_context/voice-samples.md`
- `references/reference-library.json`, when available
- source intake notes when a field is ambiguous

## Populate

Include:

- stable IDs and slug
- display name
- niche
- target audience
- positioning
- persona summary
- voice summary
- visual identity summary or non-visual identity policy
- content pillars
- content boundaries
- disclosure rules
- platform posture
- content strategy summary
- goals
- file refs
- reference refs

## Gap Questions

Ask only for schema-blocking gaps:

- What is the accepted niche?
- What is the accepted target audience?
- Which surfaces and mediums are in scope?
- Is `brand_context/voice-samples.md` present and marked with sample confidence?
- Which reference assets are primary?
- Which boundaries must automation always see?

## Completion Criteria

Complete when
`python3 -m influencer_os validate record creator-profile <creator-workspace>/creator-profile.json`
passes and every `file_refs` and `reference_refs` path exists in the
workspace. Drafts require user acceptance before any readiness status
changes; validation is not approval.
