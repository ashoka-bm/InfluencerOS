# Creator Setup Workflow

Date: 2026-06-29
Status: Draft from Grill With Docs session, aligned with ADR 0013

## Purpose

Creator Setup turns a small user request, rich source material, media references, or any combination of those inputs into a strict Creator Workspace foundation.

The workflow should create or refine:

- `context/SOUL.md`
- `context/USER.md`
- `context/MEMORY.md`
- `creator-workspace.json`
- `creator-profile.json`
- `brand_context/identity.md`
- `brand_context/soul.md`
- `brand_context/personal-brand.md`
- `brand_context/voice-samples.md`
- `references/reference-library.json`
- source files under `sources/`
- provider-neutral reference asset prompts when useful
- `progress/setup-checklist.md`

No provider-backed image, video, audio, render, upload, or paid call may happen during setup without explicit user approval for the exact call or batch.

## Operating Principle

Creator Setup should be permissive at intake and strict at readiness.

A user may begin with almost nothing, such as "generate a persona," a display name, or a niche. The system may then interview the user, recommend defaults, draft missing identity material, and create provider-neutral prompts. However, the creator should not be marked ready for downstream research and content planning until the required foundation has been reviewed or explicitly accepted.

Audience and niche remain creator-profile inputs. The system may transform user-provided words into the ideal stored shape, but it must not redefine the creator's audience or niche without user confirmation.

## Intake Modes

Creator Setup supports all of these entry modes:

- Minimal prompt: a display name, niche, short instruction, or request to generate a persona.
- Guided interview: a Grill With Docs flow that asks questions, gives recommendations, and records decisions.
- Master breakdown: a pasted or imported long-form creator brief.
- Source-file import: uploaded or local documents, notes, interviews, or existing brand files.
- Media-first import: user-provided images, audio, visual references, mood boards, or prior content.
- Hybrid intake: any combination of the above.

## Minimum To Start

The setup workflow may start with only a user instruction. If the user provides less than a display name and niche, the system should generate or recommend those fields as draft material and ask for acceptance before readiness.

Recommended initial questions:

- What is the creator's display name?
- What niche should this creator be known for?
- Who should the creator help, entertain, influence, or attract?
- Where will the creator publish first?
- What content forms should the creator make first?
- Should the creator be synthetic, avatar-led, human-backed, text-first, or mixed?

## Required Foundation Before Readiness

The creator is blocked from readiness when any of these are missing or unreviewed:

- display name
- niche
- target audience
- positioning
- persona summary
- voice
- visual identity or non-visual identity policy
- content pillars
- content boundaries
- disclosure rules when relevant
- content strategy
- platform posture
- creator goals
- identity file
- soul file
- personal brand file
- voice sample file
- reference library with required assets or required asset prompts
- source intake provenance
- explicit review or acceptance state

The files should not use `TBD` placeholders. Missing material should be represented as a blocker in a checklist, progress note, or validation result. If the user wants the LLM to create missing material, the workflow may draft it and then require review or acceptance.

## File Responsibilities

The Create Influencer conductor uses dedicated subskills for each maintained output:

- `create-identity` -> `brand_context/identity.md`
- `create-soul` -> `brand_context/soul.md`
- `create-personal-brand` -> `brand_context/personal-brand.md`
- `create-voice-samples` -> `brand_context/voice-samples.md`
- `create-runtime-context` -> `context/SOUL.md`, `context/USER.md`, `context/MEMORY.md`
- `create-creator-profile` -> `creator-profile.json`
- `create-reference-library` -> `references/reference-library.json` and prompt files

Templates live under `docs/templates/creator-setup/`.

## Target File Sizes

Creator Setup files should be small enough for precise downstream use and large enough to prevent generic output.

| File | Target size | Hard max | Purpose of the budget |
|---|---:|---:|---|
| `context/SOUL.md` | under 3 KB | 3 KB | Always-loaded creator operating identity. |
| `context/USER.md` | under 1.5 KB | 1.5 KB | Always-loaded creator/user profile and file pointers. |
| `context/MEMORY.md` | under 2.5 KB | 2.5 KB | Always-loaded active decisions and blockers. |
| `brand_context/identity.md` | 900-1,400 words | 1,800 words | Preserve durable continuity without duplicating the full source bible. |
| `brand_context/soul.md` | 1,100-1,700 words | 2,200 words | Preserve emotional logic, beliefs, triggers, soothers, and trust rules. |
| `brand_context/personal-brand.md` | 1,300-2,000 words | 2,500 words | Preserve strategy, surfaces, mediums, monetization, and safety boundaries. |
| `brand_context/voice-samples.md` | 700-1,300 words | 1,700 words | Preserve concrete voice examples with metadata. |
| `creator-profile.json` | schema-bound summary | schema-bound summary | Store operational fields only. |
| `references/reference-library.json` | one record per reusable asset | no duplicate variants | Track lifecycle, paths, prompt paths, and usage. |
| Reference `.prompt.md` files | 120-350 words | 500 words | Describe role, controlled variables, avoid list, and downstream use. |
| Reference style cards | 150-400 words | 600 words | Store reusable style guidance without becoming a brand bible. |

If a source brief is rich, compress it by downstream use: keep material that changes continuity, emotional angle, strategy, safety, or reference generation. Keep the full source under `sources/` instead of copying it into the foundation files.

### `creator-profile.json`

The Creator Profile is the operational summary for automation. It should store the structured fields that routine research, idea generation, planning, and output packaging need without copying every detail from the richer files.

It should include:

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
- file references
- primary reference asset IDs

### `brand_context/identity.md`

The Identity file is the continuity record for who the creator is.

It should include:

- biography or origin story
- lore and durable facts
- relationship to audience
- worldview as expressed publicly
- recurring situations, locations, and motifs
- continuity rules
- speech examples
- identity contradictions to avoid
- source notes

Used by the system for:

- creator-fit research interpretation
- idea generation
- script and concept continuity
- reference asset prompts
- contradiction checks

### `brand_context/soul.md`

The Soul File is the psychology and belief record.

It should include:

- values
- belief matrix
- emotional logic
- motivations
- fears, triggers, and soothers
- behavior under stress
- humor and intimacy rules
- voice cadence
- what the creator refuses to do
- audience emotional contract

Used by the system for:

- emotional angle selection
- intended audience response
- hook and payoff design
- tone consistency
- avoiding off-persona ideas

### `brand_context/personal-brand.md`

The Personal Brand File is the strategy record.

It should include:

- positioning
- audience promise
- content strategy
- content pillars
- platform posture
- content formats
- monetization posture
- partnership rules
- disclosure rules
- commercial boundaries
- visual brand
- growth goals
- proof and trust strategy

Used by the system for:

- research scope
- Content Idea Set constraints
- Social Post Format recommendations
- platform-neutral planning
- brand-safety checks
- reference asset requirements

## Content Strategy

Creator Setup should define a content strategy before research begins.

`brand_context/personal-brand.md` is the source of truth for content strategy. `creator-profile.json` stores the structured operational summary, including primary surfaces, content mediums, in-scope formats, out-of-scope formats, research implications, and readiness blocker policy.

The content strategy should answer:

- where the creator posts first
- what content formats are in scope
- what content formats are out of scope
- what topics and content pillars the creator should own
- what audience response the content should create
- how often content strategy should be revisited

Example publishing surfaces include:

- Instagram
- TikTok
- YouTube Shorts
- YouTube long-form
- Substack
- LinkedIn
- X
- blog or website

InfluencerOS v1 still prioritizes universal visual-first social posts and universal short-form vertical video. If a creator is text-first or article-first, Creator Setup should record that strategy and mark visual reference requirements accordingly instead of forcing unnecessary image assets.

Text-first surfaces such as Substack, LinkedIn, X, and blogs are valid creator strategy inputs in v1. They broaden research and planning without requiring provider-backed generation.

## Medium-Based Blockers

Readiness blockers depend on the content strategy.

All creators require:

- `context/SOUL.md`
- `context/USER.md`
- `context/MEMORY.md`
- `brand_context/identity.md`
- `brand_context/soul.md`
- `brand_context/personal-brand.md`
- accepted niche
- accepted target audience
- content strategy
- content boundaries
- source provenance
- whole-foundation user acceptance when the foundation was generated by the LLM

Text-only creators additionally require:

- brand voice guide
- publication or article style guidance
- topic and pillar strategy

Image creators additionally require:

- character or author image policy
- brand or visual system reference
- image style guidance
- required image prompts or approved image references

Video creators additionally require:

- character identity plate
- full-body turnaround sheet
- macro detail card
- primary location reference
- outfit or wardrobe reference
- default video/photo style card
- brand or visual system reference
- shot and motion constraints

Voiceover or spoken-audio creators additionally require:

- voice sample, if user-provided voice continuity matters
- or accepted voice style note, if synthetic or non-specific voice is acceptable
- pronunciation and tone boundaries

Carousel and story-sequence creators additionally require:

- sequence style guidance
- slide or frame visual system
- text overlay policy

## Reference Asset Requirements

Reference requirements depend on the creator's content strategy and publishing surfaces.

Recommended visual-first minimum before content planning:

- primary character identity plate
- full-body character turnaround sheet
- macro character detail card
- primary location reference
- primary outfit or wardrobe reference
- default video/photo style card
- brand or visual system reference
- voice sample or voice style note when spoken content is in scope

For a text-first creator, the minimum may shift to:

- brand voice guide
- author identity notes
- publication design reference
- article or newsletter style reference
- optional portrait or avatar reference

If the user provides only an interview and one image, the system may extrapolate the missing references as provider-neutral prompts and recommended reference requirements. The missing real assets should remain blockers for provider-backed generation unless the user approves generation or accepts a text-first/non-visual strategy.

## Reference Library Policy

`references/reference-library.json` tracks both real and planned assets. Each asset has an `asset_status`:

- `planned`: the asset is required or recommended but has not been prompted or supplied.
- `prompted`: the asset has a provider-neutral prompt but no generated or imported file yet.
- `user_provided`: the user supplied the asset.
- `generated`: the asset was created through an approved provider-backed generation call.
- `approved`: the asset is accepted for downstream continuity use.
- `retired`: the asset should no longer be used for new work.

Planned or prompted assets should still use stable asset IDs so downstream plans can name what is missing. Provider-backed generation remains blocked until the user approves the exact call or batch.

When an approved generation call runs, record it in the same run: keep `prompt_path` pointing at the prompt used, record the generation date and tool in the asset's `usage_notes` (plus any accepted deviations from the prompt), and leave the asset `generated` — `approved` is a separate human decision after reviewing the output. Update `progress/setup-checklist.md`, `context/MEMORY.md`, and the daily note so no "no generation has been run" claim goes stale. A dedicated provider-run record with structured generation metadata lands with Phase 3 (Generation OS) asset provenance capture.

`progress/setup-checklist.md` tracks each reference asset by its lifecycle status (planned, prompted, generated pending approval, approved) — never a bare "completed", and never grouped wording like "completed or prompted" that hides which assets actually exist.

## Source Import

When user-provided materials are imported, the workflow copies them into `sources/` and records source provenance in `creator-workspace.json` through the CLI:

```bash
python3 -m influencer_os import-intake <source-file> --creator-workspace <workspace-path> --source-type breakdown --notes "Master breakdown provided by user."
```

The command routes the file by `--source-type` and appends a `source_intakes` entry with `extraction_status: "pending"`. As setup advances, record extraction progress (forward-only) with:

```bash
python3 -m influencer_os set-intake-status <workspace-path> <source-id> <drafted|reviewed>
```

`validate workspace` requires every recorded intake path to resolve to a real file.

Placement by source type:

- master breakdowns and interview transcripts (`breakdown`, `interview`): `sources/intakes/`
- imported docs, exports, or handoffs (`import`, `handoff`): `sources/imports/`
- informal notes (`notes`): `sources/notes/`
- original media references: appropriate folders under `references/`, with source linkage from `reference-library.json`

The workflow does not need a path-reference-only system for original external locations. The copied workspace files are the durable local source.

## Provider-Neutral Prompts

Creator Setup may create provider-neutral prompts for needed reference assets. These prompts are planning artifacts, not approval to generate.

The canonical reference-image prompt templates live at:

- `docs/templates/creator-setup/reference-prompts/standard-character-asset-prompts.md`
- `docs/templates/creator-setup/reference-prompts/standard-video-photo-style-prompt.md`
- `docs/templates/creator-setup/reference-prompts/standard-outfit-reference-prompt.md`
- `docs/templates/creator-setup/reference-prompts/standard-location-reference-prompts.md`
- `docs/templates/creator-setup/reference-prompts/standard-object-reference-prompts.md`

Use them unchanged as the reference-image prompt source of truth.

The video/photo style prompts create the reusable `@video_style_reference`. This reference locks stable production grammar: camera source, lens feel, aspect ratio, lighting, framing defaults, movement feel, shot quality, platform finish, and recurring shot families. It does not lock the exact shot list for every future video.

Specific shots such as a walking shot, a desk explanation, a kitchen counter detail, or a gym side angle are chosen in the Micro-Journey Video Plan and Base Video Generation Plan for a specific piece of content. Creator Setup should only preserve shot families that are durable persona habits.

When image or video is in scope, stage prompt work in this order:

1. User supplies one or more person reference images.
2. Create or accept the default video/photo style card, including recurring shot families only when they are stable persona habits.
3. Create the three character reference assets from the standard character prompts: identity plate, full-body turnaround sheet, and macro detail card.
4. Create outfit references from person + outfit references.
5. Create location references from person + location references.
6. Create object references from person + object references.

Provider-neutral prompts should live in separate markdown files near the asset they describe, such as:

- `references/character/<asset-slug>.prompt.md`
- `references/locations/<asset-slug>.prompt.md`
- `references/outfits/<asset-slug>.prompt.md`
- `references/voice/<asset-slug>.prompt.md`
- `references/brand/<asset-slug>.prompt.md`
- `references/video-style/<asset-slug>.prompt.md`

`references/reference-library.json` should point to the prompt file with `prompt_path` when an asset is `planned` or `prompted`.

Prompts should specify:

- creator identity continuity
- asset role
- composition
- setting
- wardrobe or brand constraints
- style boundaries
- negative constraints
- source material used
- intended downstream use

Generation requires a separate approval gate naming the exact image, video, audio, or render batch.

## Readiness Gate

A creator can be marked ready for research and content planning only when all of these are true:

- `creator-workspace.json` validates.
- `creator-profile.json` validates.
- `references/reference-library.json` validates or the workflow has an accepted alternate reference policy.
- `context/SOUL.md`, `context/USER.md`, `context/MEMORY.md`, and the `brand_context/` foundation files are populated without placeholders.
- Niche and target audience are explicit accepted inputs.
- Content strategy and platform posture are accepted.
- Required visual or non-visual reference requirements match the content strategy.
- Source intake provenance is recorded.
- Provider-backed generation has not been implied by setup.
- A human has reviewed or accepted the generated foundation.

For an LLM-generated persona, the user may approve the whole generated foundation once. The workflow does not require separate approval for each file unless the user asks for that stricter review.

Workspace readiness statuses:

- `draft`: setup has started but required foundation material is missing.
- `foundation_review`: the foundation has been drafted and is waiting for user review or acceptance.
- `content_ready`: the creator can enter research and content planning for the accepted content strategy.
- `generation_ready`: the creator has the reference assets or asset prompts needed for the intended generation medium, but actual provider calls still require approval.
- `active`: the creator is in normal use.
- `archived`: the creator is no longer active.

`creator-workspace.json` stores the machine-readable status. `progress/setup-checklist.md` should explain medium-specific blockers and review notes.

The deterministic subset of these gates is enforced by `python3 -m influencer_os validate workspace <workspace-path>`: a workspace claiming `content_ready`, `generation_ready`, or `active` fails validation with the full blocker list until the medium-based blockers are met. Judgment-level review (whether the foundation is any good) stays human.

## Known Schema And CLI Gaps

The current implementation can scaffold the Creator Workspace, but it does not yet perform the full setup workflow.

Likely gaps:

- no guided interview command
- no explicit review or acceptance metadata beyond workspace status (source intakes track `pending`/`drafted`/`reviewed` via `set-intake-status`; the whole-foundation acceptance state does not)
- no provider-neutral prompt file generation command

Closed gaps:

- master intake import: `import-intake` copies setup sources into `sources/` and records `source_intakes` provenance; `validate workspace` resolves intake paths (Phase 1 slice 1, 2026-07-03).
- reference-asset file existence and foundation completeness: `validate workspace` enforces the medium-based readiness blockers at `content_ready`, `generation_ready`, and `active` — populated foundation files without `TBD` placeholders, always-loaded context byte caps, at least one source intake, required asset kinds per declared content medium, and lifecycle-appropriate asset/prompt file existence with workspace containment (Phase 1 slice 2, 2026-07-03; see `docs/workflows/creator-readiness-validation-implementation-plan.md`).

## Next Grilling Questions

1. Should the templates become validation targets, or remain authoring guidance only?
2. Should the Create Influencer workflow get a CLI command after the templates stabilize?
3. Should generated text-first creators still have an optional avatar/portrait recommendation by default?
