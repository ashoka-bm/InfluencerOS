---
name: create-lead-magnet
description: Use to create a creator's lead magnet — a conversion asset (asset_type lead_magnet) rendered as an on-brand PDF from the bundled template — after strategy is defined and before the pre-research strategy scaffold is built.
dependencies:
  - create-reference-library
  - request-generation-approval
  - import-generated-asset
  - review-generated-assets
---

# Create Lead Magnet

Produce a creator's lead magnet as a `conversion-asset` record (`asset_type: lead_magnet`) plus a rendered PDF, themed to the creator's brand and built from the bundled offline HTML/CSS template.

Author records against [schemas/conversion-asset.schema.json](schemas/conversion-asset.schema.json). Build the deliverable from the bundled assets:

- `assets/template.css` — structural stylesheet. Never edited per creator. Derives the colour ramp (`color-mix`) and type scale (`pow`) from the theme tokens. Needs a 2024+ Chromium renderer.
- `assets/skeleton.html` — the generic 8-page conversion skeleton. Copy it, replace placeholders from the body `.md`, keep the classes.
- `assets/theme.template.css` — the ~17 per-creator tokens to resolve, tagged `[AUTO]` vs `[DECIDE]`.
- `assets/body.template.md` — the structured body heading contract.
- `assets/render.mjs` — optional `puppeteer-core` headless-Chrome → PDF helper; the dependency-free path is Chrome “Print → Save as PDF”.
- `assets/crop-portrait.mjs` — optionally crops an explicitly reviewed rectangle from an identity plate; requires `puppeteer-core` and never guesses plate geometry.
- `assets/chrome-paths.mjs` + `assets/browser-runtime.mjs` — shared browser-boundary helpers used by both executable scripts.

## Purpose

The lead magnet answers: what does the creator give away to capture email, and does the artifact look unmistakably like this creator? This skill owns design, brand theming, imagery selection, and assembly of strategy-approved copy into the body contract. It must not invent strategy, claims, or creator voice.

## When To Run

The lead magnet is the **strategy → production bridge**, in two parts with distinct review checkpoints. Do not collapse them into one call. These reviews are lifecycle acceptance, not additional pipeline Gates.

- **Part A — record + draft (during strategy).** Only for a strategy reference whose intended `asset_type` is `lead_magnet`, create `conversion-assets/<slug>-lead-magnet.json` (`status: drafted`) and a drafted body `.md`. Part A `file_refs` = `["conversion-assets/<slug>-lead-magnet.md"]`; do not list a PDF that does not exist. `strategy_ready` validation blocks if `content-strategy.json` references a conversion asset whose record is missing.
- **Part B — render + human approval (before the calendar).** After strategy is accepted, resolve the theme and render the PDF. Then present the body and rendered PDF to the user for conversion-asset review. Only explicit user approval advances `drafted → approved`; rendering or validation never implies approval. Part B adds the rendered PDF to `file_refs` only after the file exists. Only an approved asset may be promoted by calendar slots.

Sequence: `foundation_ready` → strategy defined (record + draft) → **lead magnet rendered & approved** → `content-schedule.json` strategy-scaffold slots reference the approved asset with `conversion_use` + `platform` → `rebuild-calendar` → `strategy_ready` → research → revise or confirm the schedule as `research_informed` → calendar review → `production_ready`. Planning/theming/text/render work is allowed in `prompt_ready` foundation mode; only creator-likeness image generation is gated (see Imagery Hard Rules).

## Inputs

- `content-strategy.json` — the immediate upstream record. Copy its `content_strategy_id` into `source_content_strategy_id`; conversion paths and campaigns retain their reverse references to the asset ID.
- `creator-profile.json` + `brand_context/personal-brand.md` — voice, positioning, visual direction, and disclosure/compliance rules.
- `references/brand/personal-brand-board.json` — canonical exact visual tokens for every creator.
- An approved identity-plate Reference Asset only when the user wants creator imagery. Text-first creators require no identity plate; use the generic text-only skeleton by default.

## Outputs And Paths

`file_refs` on a conversion-asset record are schema-locked to **flat** paths (`^conversion-assets/[^/]+$`). Use this convention:

```text
workspace-library/creators/<creator-slug>/
  conversion-assets/
    <slug>-lead-magnet.json          # the record (asset_type: lead_magnet)
    <slug>-lead-magnet.md            # body copy — file_ref #1 (exists from Part A)
    <slug>-lead-magnet.pdf           # rendered deliverable — file_ref #2 after Part B render
  references/brand/
    <slug>-theme.css                 # RESOLVED tokens — the reusable source of truth for all future assets

<repo>/.tmp/lead-magnets/<creator-slug>/<asset-slug>/
  index.html                         # disposable copy of skeleton.html
  theme.css                          # disposable copy of the accepted reusable theme
  template.css                       # disposable structural stylesheet
  assets/                            # optional approved imagery/crops used for this render
```

Keep disposable render intermediates under root `.tmp/`, never inside the Creator Workspace. Never put the temporary bundle in `file_refs`. Part A lists only the existing Markdown; Part B adds the existing PDF. The structural assets are OS-owned and are copied into `.tmp/` only for rendering.

## The Conversion-Asset Record

Required fields (see schema): `conversion_asset_id`, `creator_profile_id`, `creator_slug`, `source_content_strategy_id`, `asset_type: lead_magnet`, `status`, `approval`, `title`, dates, `file_refs`, `approved_uses`, `platforms`, `funnel_stage`, and `notes`. Keep `approval.status: pending` with null actor/date until the user reviews the final artifact; approved/ready states require `user_approved`, `approved_by: user`, and an approval date. Lifecycle: `planned → drafted → approved → published_or_ready → retired`. All body copy lives in the `.md` file ref.

## Body Copy — Heading Contract

Author `<slug>-lead-magnet.md` from `assets/body.template.md`. The `##`/`###` headings map 1:1 to `skeleton.html` slots (`## Overview` → intro, `## Buckets` → three-lens block, `## Questions` with `### per item` → the checklist body, `## Checklist` → cheat-sheet, `## CTA` → CTA page). Copy comes from strategy and the creator's voice — do not invent claims, and honour the creator's disclosure/compliance rules (a per-footer disclaimer is mandatory). Then copy `skeleton.html` to the working bundle and replace its content to match, keeping every class.

## Brand Tokens — Resolve The Theme

Copy `assets/theme.template.css` to `references/brand/<slug>-theme.css` and resolve the tokens from this creator's `personal-brand.md`. When `references/brand/personal-brand-board.json` exists, it owns exact palette, typography, and layout tokens; reuse them. Otherwise derive a restrained accessible theme from the accepted Personal Brand File and present the result for acceptance. `[DECIDE]` values include exact colours, system font stacks, contrast, and treatment numbers.

Draft the theme, then get user acceptance before rendering. Never copy another creator's theme. If the brand mandates real skin or no saturation tricks, keep treatment light; use heavy duotone only when accepted visual direction allows it.

## Imagery Hard Rules

- Creator imagery is optional. The generic skeleton contains none.
- **When used, the creator photo is an explicitly reviewed crop from an approved identity plate—never a new generation.** Inspect the plate, choose an exact `x y width height` rectangle, and run `crop-portrait.mjs <plate> <out> <x> <y> <width> <height>`. Cropping is non-generative; never infer a fixed plate layout.
- The identity plate must be `approved` (not merely `generated`) before it is embedded. If it is still `generated`, drive its approval first (see `create-reference-library` / `review-generated-assets`).
- Never embed a private source contact sheet (those are `semantic_index_allowed:false`, do-not-publish).
- **Reference / atmosphere images are generated → they go through the provider boundary.** Draft a provider-neutral prompt (brand imagery `allow`/`bans` → positive style + negative list), then `request-generation-approval` → `record-generation-approval` → dispatch (mock adapter by default; paid connectors gated by `INFLUENCER_OS_DISABLE_PAID_CONNECTORS`) → `import-generated-asset` → blocking `review-generated-assets`. Store them as **reference-library assets** (creator-scoped, reusable across that creator's posts), not one-off files. If a reference image shows the creator, use the identity plate as `@person_reference`.
- Externally generated media (e.g. a Codex/gpt-5.5 image call) is valid but enters as `origin: imported` via `import-generated-asset` and still passes the blocking review — it does not bypass the gate.
- Keep default lead-magnet imagery brand-safe / non-creator so Part B can render even in `prompt_ready` foundation mode.

## Render

Dependency-free manual path: open `.tmp/.../index.html` in Chrome → Print → Save as PDF (Margins: None, Background graphics ON). Optional automation requires `puppeteer-core`: `node assets/render.mjs <bundle>/index.html conversion-assets/<slug>-lead-magnet.pdf`. The template uses system font stacks and makes no network requests.

## State Sync And Validation

After Part A: validate the record and workspace at the intended strategy milestone. After rendering, add the PDF ref but keep `status: drafted`; present the body and PDF. Only explicit user approval advances the record to `approved`. Then update `updated_on`, reconcile readiness/checklist/memory state, and validate the workspace. Calendar work runs only after approval.

## Provider Boundary

Drafting the record, resolving the theme, cropping the approved identity plate, and rendering the PDF are all allowed. Generating reference/atmosphere images requires explicit approval for the exact call or batch, and any generated or imported image must pass `review-generated-assets` before it is placed.

## Environment Notes

- macOS has no `timeout` command — do not wrap CLI calls in it.
- If generating images via Codex, the default model may need a newer CLI than installed; pin a supported image model (e.g. `-m gpt-5.5`). Enter results via `import-generated-asset`.
- Rendering needs a 2024+ Chromium (for `color-mix` + `pow`). For other engines, precompute the ramp and type-scale into the theme instead of deriving in CSS.

## Completion Criteria

Complete when the record validates and names its source strategy; the body follows the heading contract; the theme is accepted; the PDF exists and is listed only after render; optional imagery is approved and traceable; the user has explicitly approved the final body/PDF before `status: approved`; and workspace validation passes for the intended milestone.

## Rules

- 2026-07-09: Part A may reference only files that already exist; lifecycle approval must be explicit and schema-valid at the standalone record boundary; non-lead conversion types halt; disposable render state belongs in root `.tmp/`; browser-backed helpers require success-path boundary tests.
