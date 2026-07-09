---
name: create-lead-magnet
description: Use to create a creator's lead magnet — a conversion asset (asset_type lead_magnet) rendered as an on-brand PDF from the bundled template — during the strategy-to-production bridge, after strategy is defined and before the content calendar is built.
dependencies:
  - create-reference-library
  - request-generation-approval
  - import-generated-asset
  - review-generated-assets
---

# Create Lead Magnet

Produce a creator's lead magnet as a `conversion-asset` record (`asset_type: lead_magnet`) plus a rendered PDF, themed to the creator's brand and built from the bundled, dependency-free HTML/CSS template.

Author records against [schemas/conversion-asset.schema.json](schemas/conversion-asset.schema.json). Build the deliverable from the bundled assets:

- `assets/template.css` — structural stylesheet. Never edited per creator. Derives the colour ramp (`color-mix`) and type scale (`pow`) from the theme tokens. Needs a 2024+ Chromium renderer.
- `assets/skeleton.html` — the 8-page conversion skeleton (worked example). Copy it, replace copy from the body `.md`, keep the classes.
- `assets/theme.template.css` — the ~17 per-creator tokens to resolve, tagged `[AUTO]` vs `[DECIDE]`.
- `assets/body.template.md` — the structured body heading contract.
- `assets/render.mjs` — optional headless-Chrome → PDF helper (zero-dep path is Chrome "Print → Save as PDF").
- `assets/crop-portrait.mjs` — crops a single headshot out of the identity plate (non-generative).

## Purpose

The lead magnet answers: what does the creator give away to capture email, and does the artifact look unmistakably like this creator? This skill owns **design, brand theming, and imagery selection** — not the copy, which comes from strategy and the creator's voice. The value is a magnet that looks bespoke to the creator, not a templated PDF.

## When To Run

The lead magnet is the **strategy → production bridge**, in two parts with two distinct gates. Do not collapse them into one call.

- **Part A — record + draft (during strategy).** When the strategy references a lead magnet, offer, or other conversion mechanism, create `conversion-assets/<slug>-lead-magnet.json` (`status: drafted`) and a drafted body `.md`. `strategy_ready` validation blocks if `content-strategy.json` references a conversion asset whose record is missing; a drafted body also clears the readiness-gates blocker "Lead magnet draft is still missing."
- **Part B — render + approve (before the calendar).** After strategy is accepted, resolve the theme, render the PDF, and advance the record `drafted → approved`. Only an `approved` asset may be promoted by calendar slots, and `production_ready` is blocked until the promoted asset is at least `approved` and `content-schedule.json` exists.

Sequence: `foundation_ready` → strategy defined (record + draft) → **lead magnet rendered & approved** → `content-schedule.json` slots reference the approved asset with `conversion_use` + `platform` → `rebuild-calendar` → `production_ready`. Planning/theming/text/render work is allowed in `prompt_ready` foundation mode; only creator-likeness image generation is gated (see Imagery Hard Rules).

## Inputs

- `content-strategy.json` — conversion path, funnel stage, campaigns, platforms. Source of the CTA framing and which platforms to name.
- `creator-profile.json` + `brand_context/personal-brand.md` — bio (meet-the-creator block), voice, disclosure/compliance rules.
- `references/brand/<slug>-brand-system.md` — palette words, typography posture, imagery rules. Source for theme resolution.
- `references/character/<slug>-identity-plate.png` — the creator's approved face. The only source for the creator photo.

## Outputs And Paths

`file_refs` on a conversion-asset record are schema-locked to **flat** paths (`^conversion-assets/[^/]+$`). Use this convention:

```text
workspace-library/creators/<slug>/
  conversion-assets/
    <slug>-lead-magnet.json          # the record (asset_type: lead_magnet)
    <slug>-lead-magnet.md            # body copy — file_ref #1 (exists from Part A)
    <slug>-lead-magnet.pdf           # rendered deliverable — file_ref #2 (Part B)
    <slug>-lead-magnet/              # nested WORKING bundle — on disk only, NOT in file_refs
      index.html                     #   copy of skeleton.html, content filled, hrefs to siblings
      theme.css                      #   copy of the resolved theme
      css/template.css               #   copy of the structural template
      assets/<slug>-portrait.png     #   the identity-plate crop (+ any approved reference images)
  references/brand/
    <slug>-theme.css                 # RESOLVED tokens — the reusable source of truth for all future assets
```

`file_refs` = `["conversion-assets/<slug>-lead-magnet.md", "conversion-assets/<slug>-lead-magnet.pdf"]` — both flat, both schema-valid. Never put a nested path in `file_refs`; the validator runs the schema first and rejects it. The structural `template.css`, `skeleton.html`, and `render.mjs` are OS-level (they travel with this skill) — copy them into the working bundle to render; do not treat them as per-creator state.

## The Conversion-Asset Record

Required fields (see schema): `conversion_asset_id` (`^conversion_asset_...`), `creator_profile_id`, `creator_slug`, `asset_type: lead_magnet`, `status`, `title`, `created_on`, `updated_on`, `file_refs`, `approved_uses`, `platforms` (enum), `funnel_stage` (enum), `notes`. Lifecycle: `planned → drafted → approved → published_or_ready → retired`. Do **not** widen the schema (it is `additionalProperties:false`, minimal by ADR 0028); all body copy lives in the `.md` file_ref. Populate `funnel_stage`/`approved_uses`/`platforms` from `content-strategy.json`.

## Body Copy — Heading Contract

Author `<slug>-lead-magnet.md` from `assets/body.template.md`. The `##`/`###` headings map 1:1 to `skeleton.html` slots (`## Overview` → intro, `## Buckets` → three-lens block, `## Questions` with `### per item` → the checklist body, `## Checklist` → cheat-sheet, `## CTA` → CTA page). Copy comes from strategy and the creator's voice — do not invent claims, and honour the creator's disclosure/compliance rules (a per-footer disclaimer is mandatory). Then copy `skeleton.html` to the working bundle and replace its content to match, keeping every class.

## Brand Tokens — Resolve The Theme

Copy `assets/theme.template.css` to `references/brand/<slug>-theme.css` and resolve the ~17 tokens from THIS creator's brand data. When `references/brand/personal-brand-board.json` exists, it is the canonical owner of exact palette hexes, typography families, and layout tokens — resolve those values from the board rather than re-deriving them, and treat the brand-system doc as the source for posture, voice register, and imagery treatment only. `[AUTO]` tokens derive from the brand system (colour roles from palette words, font roles from typography posture, `--ratio` from voice register, `--sig-border` and imagery treatment from imagery rules). `[DECIDE]` tokens need a judgment or a computed value (exact hexes, concrete font families, `--font-mono`, `--color-accent-contrast` — compute black/white for ≥4.5:1 on the accent — and the exact treatment numbers).

Draft the theme, then get **user acceptance before advancing readiness** — validation is not approval. **Never copy another creator's theme file as a starting point** — resolve from this creator's brand system. If the creator's brand mandates real skin / no saturation tricks, keep imagery treatment light (near-full-colour); only use a heavy duotone when the brand's imagery direction allows it.

## Imagery Hard Rules

- **The creator photo is the creator's APPROVED identity plate, reused — never a new generation.** Run `crop-portrait.mjs` to lift the front headshot from the plate (the plate is a turnaround sheet). Cropping is a non-generative transform and needs no new approval. Generating a fresh face for a real creator is a hard error — it breaks the personal brand.
- The identity plate must be `approved` (not merely `generated`) before it is embedded. If it is still `generated`, drive its approval first (see `create-reference-library` / `review-generated-assets`).
- Never embed a private source contact sheet (those are `semantic_index_allowed:false`, do-not-publish).
- **Reference / atmosphere images are generated → they go through the provider boundary.** Draft a provider-neutral prompt (brand imagery `allow`/`bans` → positive style + negative list), then `request-generation-approval` → `record-generation-approval` → dispatch (mock adapter by default; paid connectors gated by `INFLUENCER_OS_DISABLE_PAID_CONNECTORS`) → `import-generated-asset` → blocking `review-generated-assets`. Store them as **reference-library assets** (creator-scoped, reusable across that creator's posts), not one-off files. If a reference image shows the creator, use the identity plate as `@person_reference`.
- Externally generated media (e.g. a Codex/gpt-5.5 image call) is valid but enters as `origin: imported` via `import-generated-asset` and still passes the blocking review — it does not bypass the gate.
- Keep default lead-magnet imagery brand-safe / non-creator so Part B can render even in `prompt_ready` foundation mode.

## Render

Zero-dependency: open the working bundle's `index.html` in Chrome → Print → Save as PDF (Margins: None, Background graphics ON). Automated: `npm i puppeteer-core` once, then `node assets/render.mjs <bundle>/index.html conversion-assets/<slug>-lead-magnet.pdf`. Either way the four settings that matter are baked in: `printBackground`, `preferCSSPageSize`, wait for `document.fonts.ready`, and `print-color-adjust: exact` (in the CSS, on wrappers). Each `.page` is exactly one Letter sheet.

## State Sync And Validation

After Part A: `python3 -m influencer_os validate record conversion-asset <record-path>`. After Part B: set `status: approved`, update `updated_on`, clear the stale "Lead magnet draft is still missing" blocker in `readiness-gates.json`, update `progress/` + `context/MEMORY.md`, then `python3 -m influencer_os validate workspace <workspace>`. The calendar step (`rebuild-calendar` / `create-production-plan`) runs after the asset is `approved`.

## Provider Boundary

Drafting the record, resolving the theme, cropping the approved identity plate, and rendering the PDF are all allowed. Generating reference/atmosphere images requires explicit approval for the exact call or batch, and any generated or imported image must pass `review-generated-assets` before it is placed.

## Environment Notes

- macOS has no `timeout` command — do not wrap CLI calls in it.
- If generating images via Codex, the default model may need a newer CLI than installed; pin a supported image model (e.g. `-m gpt-5.5`). Enter results via `import-generated-asset`.
- Rendering needs a 2024+ Chromium (for `color-mix` + `pow`). For other engines, precompute the ramp and type-scale into the theme instead of deriving in CSS.

## Completion Criteria

Complete when: the `conversion-asset` record exists and validates against the schema; the body `.md` is authored to the heading contract; `references/brand/<slug>-theme.css` is resolved and user-accepted; the creator photo is a crop of the approved identity plate (never a generation) and any reference imagery has passed the provider boundary + review; the PDF is rendered and listed in `file_refs`; and — for production — the record is `approved`, readiness blockers are cleared, and `validate workspace` passes for the intended milestone.
