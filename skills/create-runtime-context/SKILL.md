---
name: create-runtime-context
description: Use to create tiny always-loaded creator context files: context/SOUL.md, context/USER.md, and context/MEMORY.md.
---

# Create Runtime Context

Create the always-loaded context files after the rich foundation files exist.

Use:

- `docs/templates/creator-setup/context/SOUL.md`
- `docs/templates/creator-setup/context/USER.md`
- `docs/templates/creator-setup/context/MEMORY.md`

## Purpose

These files mirror the Agentic OS always-loaded context layer.

- `context/SOUL.md`: how agents should behave as this creator.
- `context/USER.md`: the smallest useful creator/user profile.
- `context/MEMORY.md`: active decisions, blockers, and recent notes.

Rich material belongs in `brand_context/`, `references/`, `sources/`, or `memory/learnings.md`.

## Size Budgets

- `context/SOUL.md`: under 3 KB.
- `context/USER.md`: under 1.5 KB.
- `context/MEMORY.md`: under 2.5 KB.

## Inputs

Read:

- `creator-profile.json`
- `brand_context/identity.md`
- `brand_context/soul.md`
- `brand_context/personal-brand.md`
- `brand_context/voice-samples.md`
- `references/reference-library.json`
- `progress/setup-checklist.md`

## Rules

- Write short bullets, not essays.
- Include pointers to rich files instead of duplicating them.
- Do not use placeholders. Missing material becomes a blocker in `context/MEMORY.md`.
- Treat these files as loaded every session; every line must earn its tokens.

## Completion Criteria

Complete when all three files exist, stay within size budget, contain no placeholders, and point agents to the lazy-loaded files needed for deeper work.
