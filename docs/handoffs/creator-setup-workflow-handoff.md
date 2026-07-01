# Handoff: Creator Setup Workflow

Date: 2026-06-29
Repo: `/Users/ashokaji/code/fullstock/InfluencerOS`

## Purpose

Use this handoff to start a focused Grill Me With Docs session for the Creator Setup workflow.

The goal of that session is to define exactly how a creator workspace is populated from minimal user input, rich user-provided materials, or both.

## Current Architecture Context

Creator setup is Phase 1: Planning OS.

The current workspace model is:

```text
workspace-library/creators/<creator-slug>/
  AGENTS.md
  creator-workspace.json
  creator-profile.json
  identity.md
  soul.md
  personal-brand.md
  sources/
  references/
  research/
  projects/
  memory/
  progress/
```

The CLI can already scaffold this from a `creator-workspace.json` manifest:

```bash
python3 -m influencer_os init-creator examples/creator-workspace.example.json
python3 -m influencer_os validate workspace workspace-library/creators/luna-fit
```

Implemented schemas relevant to creator setup:

- `creator-workspace.schema.json`
- `creator-profile.schema.json`
- `reference-library.schema.json`

Key ADRs:

- `docs/adr/0001-creator-workspaces.md`
- `docs/adr/0002-hybrid-creator-authoring.md`
- `docs/adr/0003-creator-profile-operational-summary.md`
- `docs/adr/0010-file-first-with-sql-index.md`
- `docs/adr/0011-semantic-lookup-projection.md`

## Decisions Already Made

- The repo root is the shared OS; real creator state lives in ignored Creator Workspaces.
- Creator authoring is hybrid: a master intake can seed draft files, then split workspace files become the maintained source of truth.
- `creator-profile.json` is an operational summary, not a full identity dump.
- The rich files are `identity.md`, `soul.md`, and `personal-brand.md`.
- Reference assets are tracked through `references/reference-library.json`.
- Provider-backed generation of reference images, video, audio, or renders requires explicit approval.

## Open Questions For Grilling

- What is the minimum user input needed to create a useful first-draft creator?
- What should the system ask for, infer, draft, or leave blank?
- What fields must be user-supplied and never invented, especially audience and niche?
- What belongs in `identity.md` versus `soul.md` versus `personal-brand.md`?
- What reference assets are required before the creator can produce content?
- What reference assets are optional or can be generated later?
- How should user-provided materials be imported into `sources/` and traced into profile/reference records?
- What quality gate marks a creator as ready for research and content planning?

## Desired Output Of The Grilling Session

Produce a workflow spec, likely `docs/workflows/creator-setup.md`, that defines:

- intake modes,
- required and optional inputs,
- file population rules,
- reference asset requirements,
- approval gates,
- validation/checklist rules,
- metadata that must be carried forward.

Update schemas only if the workflow reveals missing required metadata.
