---
name: personal-brand-board
description: Create or revise every InfluencerOS creator's required tokenized personal brand board, profile-avatar binding, and editable mini style guide, including text-only and long-form creators.
---

# Personal Brand Board

Create the canonical creator-specific spec at:

```text
references/brand/personal-brand-board.json
```

Run this skill for every creator after Reference Library planning, when the
profile-avatar asset and any location or object assets have stable IDs. Populate the board from the accepted Creator Profile,
`brand_context/personal-brand.md`, voice samples, and
`references/reference-library.json`. Validate against
`schemas/personal-brand-board.schema.json`; use
`examples/personal-brand-board.example.json` as the shape reference.

## Contract

Include:

- `approval_status`: keep `draft_for_review` until the human explicitly approves this board;
- strategy: name, handle, tagline, descriptor, summary, audience, promise, differentiator;
- 3–6 brand adjectives and anti-adjectives;
- 6–8 named palette tokens with exact hex, unique roles, and usage percentages totaling 100%;
- typography roles for display, subhead, body, and caption/data, each with a name, valid CSS stack ending in a generic family, real sample, and size/weight note;
- wordmark, handle, submark, and avatar guidance;
- `avatar_asset_id` resolving to a `brand` or `character` Reference Asset whose
  status is at least `prompted`; use a person/avatar image when identity-bearing,
  or a symbol, monogram, product, or brand mark when no face is appropriate;
- 0–6 production spaces: actual recurring locations for filming or photography,
  each with its purpose, suitable formats, continuity notes, and a
  `reference_asset_id` resolving to a Reference Library `location` asset;
- 0–6 signature props: recurring identity-bearing objects kept separate from
  production spaces, each with its role, suitable uses, continuity notes, and
  a `reference_asset_id` resolving to a Reference Library `object` asset;
- 3–6 content templates that demonstrate actual layout behavior;
- voice cues and tonal sliders;
- 4–6 content pillars rendered as typographic information cards, without
  decorative or merely adjacent reference images;
- accessibility, production, and source/asset QA notes.

Use exact operational values. Color names without hex codes and generic directions such as “clean sans” are incomplete.

## Reusable Rendering

Never author a creator-specific HTML layout. InfluencerOS owns one shared template at:

```text
influencer_os/templates/personal-brand-board.html
```

After writing the spec, run:

```bash
python3 -m influencer_os rebuild-brand-board <creator-workspace>
python3 -m influencer_os validate brand-board <creator-workspace>
```

The generated editable projection is:

```text
references/brand/personal-brand-board.html
```

Production spaces and signature props never accept free-form image paths. The
renderer resolves their typed `reference_asset_id` links. Available
user-provided, generated, or approved media must be a supported image inside
the Creator Workspace; planned or prompted assets render intentional labeled
placeholders. Other optional blank image fields also render placeholders.

Text-only and long-form creators may use zero production spaces. When the
section is present, production-space images are required because it exists to show the
actual spaces in wider context. Do not place portraits, props, layout boards,
or generic lifestyle images there. Signature props remain Reference Library
objects but may also be surfaced in their own board section when they recur
across content; never mix them into the production-space section.

## Approval And Readiness

Present the rendered HTML for a distinct human brand-system review. Approval of a batch of character/location/reference images does not approve the personal brand board.

Do not advance any creator to `foundation_ready` until the profile-avatar asset
is prompt-staged or available and the canonical spec plus current rendered
projection validate with `approval_status: approved`. A generated mood image or
brand inspiration sheet is supporting material, not the production brand system.

The JSON and HTML artifacts require no provider approval. An approved Visual
Continuity Plan grants standing approval for one initial generation pass over
its listed creator-setup reference assets with no second confirmation. Scope
changes, regeneration, production content, video, voice, render, upload, and
later-added assets remain exact-approved.

## Rules

- 2026-07-09: Replaced ambiguous visual territories with actual production
  spaces after Mara Vale feedback; content pillars no longer accept decorative
  images. Every displayed image must depict the subject named by its section.
- 2026-07-09: Added an optional, separately rendered signature-props section
  after Mara Vale feedback; props remain reusable object references and never
  substitute for production spaces.
- 2026-07-09: Moved brand-board creation after Reference Library planning and
  replaced production-space/prop image paths with typed `reference_asset_id`
  links. This mechanically prevents unrelated images and keeps prompt-ready
  creators usable through intentional placeholders.
- 2026-07-10: Made the board universal for text-only and long-form creators,
  replaced the free-form avatar image path with typed `avatar_asset_id`, and
  allowed zero production spaces when no filming or photography world exists.
