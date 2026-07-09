# Creator Setup Workflow

Date: 2026-06-29
Status: Draft from Grill With Docs session, aligned with ADR 0013

## Purpose

Creator Setup turns a small user request, rich source material, media references, or any combination of those inputs into a strict Creator Workspace foundation.

At the start of setup, explain the job in plain language: onboarding a new
influencer means building the reusable creator foundation that keeps future
content consistent. The foundation covers identity, audience, voice, content
strategy, platform posture, boundaries, reference assets, provider-neutral
prompts, and readiness status. Setup is allowed to be flexible while collecting
inputs, but it is only complete when the required files and medium-specific
reference materials are present, approved, or prompt-staged behind the provider
approval gate.

The workflow should create or refine:

- `context/SOUL.md`
- `context/USER.md`
- `context/MEMORY.md`
- `creator-workspace.json`
- `creator-profile.json`
- `readiness-gates.json`
- `channels.json`
- `content-strategy.json`
- `brand_context/identity.md`
- `brand_context/soul.md`
- `brand_context/personal-brand.md`
- `brand_context/voice-samples.md`
- `references/visual-continuity-plan.json`
- `references/reference-library.json`
- `conversion-assets/*.json` when strategy references a lead magnet, offer, or
  other conversion mechanism
- `content-schedule.json` when the workspace is being moved to production
  readiness
- `boards/content-calendar.html` as the rebuildable human-review projection of
  `content-schedule.json`
- source files under `sources/`
- provider-neutral reference asset prompts when useful
- `progress/setup-checklist.md`

No provider-backed image, video, audio, render, upload, or paid call may happen during setup without explicit user approval for the exact call or batch.

## Operating Principle

Creator Setup should be permissive at intake and strict at readiness.

A user may begin with almost nothing, such as "generate a persona," a display name, or a niche. The system may then interview the user, recommend defaults, draft missing identity material, and create provider-neutral prompts. However, the creator should not be marked ready for downstream research and content planning until the required foundation has been reviewed or explicitly accepted.

Audience and niche remain creator-profile inputs. The system may transform user-provided words into the ideal stored shape, but it must not redefine the creator's audience or niche without user confirmation.

## Setup State Reconciliation

Creator setup must not maintain parallel state in prose. Before answering
"where are we?", resuming a creator setup, or advancing a readiness milestone,
read these files first:

- `creator-workspace.json`
- `readiness-gates.json`
- `channels.json`
- `content-strategy.json`
- `references/visual-continuity-plan.json`
- `conversion-assets/*.json`
- `content-schedule.json`, when present
- `boards/content-calendar.html`, when present
- `references/brand/personal-brand-board.json` and `.html`, for visual creators
- `progress/setup-checklist.md`
- `context/MEMORY.md`

Machine-readable files own state:

- `readiness-gates.json` owns the profile, foundation, strategy, and production
  readiness milestone statuses.
- `content-strategy.json` owns platform roles, monthly mix, cadence principles,
  related-post chains, campaigns, and conversion paths.
- `references/visual-continuity-plan.json` owns candidate prop,
  product/brand-object, and production-space analysis, the presented
  recommendations, per-candidate user decisions, and Visual Continuity Plan
  approval.
- `conversion-assets/*.json` owns lead magnet, offer, newsletter asset,
  waitlist, opt-in page, and partner asset status.
- `content-schedule.json` owns calendar readiness.
- `boards/content-calendar.html` is a derived review projection. It never owns
  schedule state and must be rebuilt after every canonical calendar change.
- `references/brand/personal-brand-board.json` owns exact palette, typography,
  identity, imagery, template, and QA tokens. It is authored after Reference
  Library planning; production spaces bind to `location` assets and signature
  props bind to `object` assets by stable ID. Its HTML sibling is a rebuildable
  projection from the package-owned template.
- Markdown explains decisions, blockers, and review notes. It must mirror the
  canonical records instead of inventing additional milestone names or stale blockers.

After any user approval, accepted generation batch, conversion-asset review, or
calendar update, run a same-turn state sync pass:

1. update the canonical JSON record;
2. remove stale blocker language from rich context files, progress notes,
   `AGENTS.md`, and `CLAUDE.md`;
3. write the next readiness milestone into `progress/setup-checklist.md` and `context/MEMORY.md`;
4. for a visual-brand update, run
   `python3 -m influencer_os rebuild-brand-board <workspace-path>`, present the
   HTML for a distinct brand-system review, then run
   `python3 -m influencer_os validate brand-board <workspace-path>`;
5. for a calendar update, run
   `python3 -m influencer_os rebuild-calendar <workspace-path>` and present
   `boards/content-calendar.html` for review;
6. run `python3 -m influencer_os validate calendar <workspace-path>` when the
   calendar exists;
7. run `python3 -m influencer_os validate workspace <workspace-path>`.

The validator rejects readiness states that still contain known stale setup
phrases such as a pending portrait approval after the foundation milestone is ready.
It also enforces that `strategy_ready` references existing conversion asset records and
`production_ready` has a valid content schedule whose promoted conversion assets are approved. A workspace with approved
foundation and approved strategy, but a drafted lead magnet and no schedule, is
not production-ready; its next step is lead magnet review, then calendar
creation.

## Intake Modes

Creator Setup presents three user-facing entry paths:

1. **Load Existing Files**: use a pasted or imported master breakdown, existing
   brand files, notes, interview transcripts, previous creator files,
   user-provided media references, mood boards, or prior content. Import source
   files into `sources/`, extract the foundation, then interview only for
   missing or ambiguous decisions.
2. **Guided Interview**: run a Grill With Docs style Decision Interview. Ask one
   question at a time, include a recommended answer, and record the user answer
   or system-filled answer.
3. **Generate From Basic Information**: accept minimal inputs such as display
   name, niche, audience, target platforms, or a short prompt. The system drafts
   the missing foundation and reference plan, then asks for whole-foundation
   acceptance before readiness.

Hybrid intake is normal: the user may load files and still answer interview
questions, or provide basic information first and then attach references. In all
paths, the user can ask the system to fill blanks from the available context.
System-filled answers remain part of the review set and cannot silently satisfy
accepted niche or audience requirements.

## Decision Interview

The Decision Interview is a bounded question tree used whenever intake is
incomplete.

Each question should include:

- the question;
- the recommended answer;
- why that recommendation fits the current intake;
- the answer source: `user_provided`, `imported`, `generated_from_intake`, or
  `system_filled`;
- the decision status: accepted, revised, skipped, or needs review.

Ask only for decisions that affect foundation quality, content strategy,
reference requirements, safety boundaries, or readiness. If the user asks the
system to answer, fill the field and continue. If the user asks for only the
next question, do not expand into a broad form.

Recommended question order:

- display name, niche, audience, positioning, and representation model;
- primary public platforms and content mediums;
- content boundaries, claims rules, disclosure, and privacy constraints;
- voice, phrases, examples, and publication style;
- visual identity, reference image availability, and image generation policy;
- recurring filming locations, collaborators or other characters, signature
  objects, outfits, and other continuity anchors;
- cadence or first-use goals when they affect setup readiness.

## Minimum To Start

The setup workflow may start with only a user instruction. If the user provides less than a display name and niche, the system should generate or recommend those fields as draft material and ask for acceptance before readiness.

Recommended initial questions:

- What is the creator's display name?
- What niche should this creator be known for?
- Who should the creator help, entertain, influence, or attract?
- Where will the creator publish first?
- What content forms should the creator make first?
- Should the creator be synthetic, avatar-led, human-backed, text-first, or mixed?
- Do you have a reference image for the person/avatar? If image or video is in
  scope, the system should strongly recommend one while allowing a generated
  identity prompt instead.

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
- a user-approved Visual Continuity Plan before any object or location prompt
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
- `create-reference-library` -> `references/visual-continuity-plan.json`, then
  `references/reference-library.json` and prompt files after user approval

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
| `references/visual-continuity-plan.json` | one row per credible prop, product/brand-object, or space candidate | focused review set | Evaluate brand, atmosphere, brand expression, recurrence, continuity, risk, and user selection before prompt creation. |
| `references/reference-library.json` | one record per reusable asset | no duplicate variants | Track lifecycle, paths, prompt paths, and usage. |
| Reference `.prompt.md` files | 120-350 words | 500 words | Describe role, controlled variables, avoid list, and downstream use. |
| Reference style cards | 150-400 words | 600 words | Store reusable style guidance without becoming a brand bible. |

If a source brief is rich, compress it by downstream use: keep material that changes continuity, emotional angle, strategy, safety, or reference generation. Keep the full source under `sources/` instead of copying it into the foundation files.

The target sizes remain authoring guidance. Ready-state validation enforces a lower deterministic floor: the rich brand-context files must be meaningfully populated, carry the required template sections, avoid `TBD`, and provide enough voice samples to support style fidelity. Human review still decides whether the substance is strong.

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
- primary and secondary audience definitions
- audience language, jobs-to-be-done, tried alternatives, objections, and trigger moments
- trusted sources, audience hangouts, negative audience, and proof and trust cues
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

### Platform-To-Medium Mapping

The setup flow should ask or recommend public platforms first, then map those
platforms to the content mediums the creator must support. The accepted mediums
drive readiness blockers.

| Platform or surface | Likely content mediums | Setup effect |
|---|---|---|
| X, LinkedIn, Substack, Medium, blog/newsletter, Reddit text posts | text | Requires voice, publication style, audience language, topic/pillar strategy, and disclosure rules. |
| Instagram feed, Pinterest-style surfaces, image-led blog posts | image, text | Requires image style, brand visual system, person/avatar policy, and any recurring outfit/object references. |
| TikTok, Instagram Reels, YouTube Shorts, Facebook Reels | video, text, optional audio | Requires character identity references, video/photo style, location references, wardrobe rules, recurring object policy, ElevenLabs Voice Design prompt package, and spoken or onscreen voice rules. |
| YouTube long-form, podcasts, music/audio-led surfaces | audio, video or text depending on format | Requires ElevenLabs Voice Design prompt package; spoken generation later requires an imported/approved voice reference; on-camera video also requires visual references. |
| Carousels and story sequences on Instagram, LinkedIn, or similar surfaces | image, text, carousel or story_sequence | Requires slide/frame visual system, text overlay policy, brand reference, and optional character/location references. |

Do not add platform-specific publishing adapters during setup. Platform choices
only determine strategy, research scope, format support, and reference needs.

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

- ElevenLabs Voice Design prompt package before `foundation_ready`
- imported/approved voice reference before spoken generation
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
- ElevenLabs Voice Design prompt package for audio/video creators

For a text-first creator, the minimum may shift to:

- brand voice guide
- author identity notes
- publication design reference
- article or newsletter style reference
- optional portrait or avatar reference

If the user provides only an interview and one image, the system may extrapolate the missing references as provider-neutral prompts and recommended reference requirements. The missing real assets should remain blockers for provider-backed generation unless the user approves generation or accepts a text-first/non-visual strategy.

The setup checklist should make the reference material requirement explicit by
medium:

- **Text**: voice examples, editorial rules, publication style, audience
  language, topic/pillar strategy, and disclosure rules.
- **Image**: person/avatar reference policy, recommended user-provided reference
  image or generated identity prompt, character/headshot identity assets, image
  style, brand visual system, and recurring outfit or object references when
  they are identity-bearing.
- **Audio or music**: ElevenLabs Voice Design prompt package, imported/approved
  voice reference before spoken generation, pronunciation/tone boundaries, sonic
  identity notes, and rights/disclosure constraints.
- **Video**: all image requirements plus default video/photo style, primary
  filming locations, recurring shot families, wardrobe/outfit references,
  recurring collaborators or characters, signature objects, and ElevenLabs Voice
  Design prompt package.

For video, each recurring location should have its own reference asset or
prompt. A bedroom, kitchen, studio, gym, car, office, or outdoor route are
different continuity spaces, not variants of one generic location. Each
recurring character or collaborator should have a character reference strategy.
Each identity-attached object that should appear consistently should have an
object reference or prompt; casual one-off props should stay in downstream
project planning.

Object references are atomic: each distinct prop, product, packaging form, or
organization-owned object gets its own Reference Asset, prompt file, planned
output path, generation request, and reference image. A multi-angle sheet may
repeat the same object from several views, but it must not contain different
objects. Grouped source language such as "family objects" or "desk tools" must
be expanded into one asset per physical object before prompt drafting or
generation approval.

## Visual Continuity Selection Review

The full candidate-analysis, presentation, user-decision, promotion, and
prompt-staging contract is owned by `skills/create-reference-library/SKILL.md`.
Creator Setup must run that contract before object or location reference work,
and a visual workspace cannot become `foundation_ready` until its Visual
Continuity Plan is user-approved. This workflow intentionally does not maintain
a second copy of the scoring or recommendation rules.

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
5. Draft and present the Visual Continuity Plan candidate review.
6. Record the user's final selection and approve the plan.
7. Create Anchor Space references only from accepted production-space candidates.
8. Create Signature Prop or Signature Object references only from accepted
   prop/product-object candidates.

At step 8, fan out any list of objects before writing prompts. Do not represent
multiple distinct props, products, or brand objects with one asset id, one
prompt, or one output image.

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

## Readiness Milestone

A creator can be marked ready for research and content planning only when all of these are true:

- `creator-workspace.json` validates.
- `creator-profile.json` validates.
- `references/reference-library.json` validates or the workflow has an accepted alternate reference policy.
- `context/SOUL.md`, `context/USER.md`, `context/MEMORY.md`, and the `brand_context/` foundation files are populated without placeholders.
- Niche and target audience are explicit accepted inputs.
- Content strategy and platform posture are accepted.
- Required visual or non-visual reference requirements match the content strategy.
- Every selected content medium has its required reference materials
  user-provided, approved, or prompt-staged with stable reference asset IDs.
- Source intake provenance is recorded.
- Provider-backed generation has not been implied by setup.
- A human has reviewed or accepted the generated foundation.

For an LLM-generated persona, the user may approve the whole generated foundation once. The workflow does not require separate approval for each file unless the user asks for that stricter review.

Workspace readiness statuses:

- `draft`: setup has started but required foundation material is missing.
- `profile_ready`: the creator profile is accepted and selected channels are recorded.
- `foundation_ready`: channel-derived foundation requirements are ready, either in `prompt_ready` mode with stable prompts or `media_ready` mode with approved/user-provided media.
- `strategy_ready`: the monthly platform mix, cadence principles, conversion paths, related-post chains, and required conversion assets are accepted.
- `production_ready`: the strategy has been translated into content calendar slots and the required lead magnets or conversion assets are ready for use.
- `active`: the creator is in normal use.
- `archived`: the creator is no longer active.

`creator-workspace.json` stores the milestone status. The legacy-named `readiness-gates.json`
stores readiness status, blockers, human waivers, foundation mode, and media permission
booleans. `channels.json` records selected social channels and handle/account
readiness. `content-strategy.json` records the machine-readable monthly mix and
conversion relationships. `progress/setup-checklist.md` should explain
medium-specific blockers and review notes.

Before marking `production_ready`, the operator must review the current
`boards/content-calendar.html`. Generate it only from the validated canonical
schedule:

```bash
python3 -m influencer_os rebuild-calendar <workspace-path>
python3 -m influencer_os validate calendar <workspace-path>
python3 -m influencer_os validate workspace <workspace-path>
```

The calendar validator deterministically re-renders from
`creator-profile.json` and `content-schedule.json`; a stale or edited projection fails
with an instruction to rebuild it. The projection itself is not a readiness
dependency, so canonical schedule state remains authoritative.

The deterministic readiness checks are enforced by `python3 -m influencer_os validate workspace <workspace-path>`: a workspace claiming `profile_ready`, `foundation_ready`, `strategy_ready`, `production_ready`, or `active` fails validation with the full blocker list until the stage requirements, medium-based blockers, and foundation-quality floors are met. The quality floors are intentionally mechanical: required sections, minimum word counts below the target budgets, no `TBD`, context byte caps, enough voice samples, selected-channel checks, ElevenLabs Voice Design prompt staging for audio/video creators, media permission checks, approved strategy records, existing strategy conversion-asset records, and approved production-slot conversion assets. Judgment-level review stays human; these checks are not pipeline Gates.

## Known Schema And CLI Gaps

The current implementation can scaffold the Creator Workspace, but it does not yet perform the full setup workflow.

Likely gaps:

- no guided interview command
- no guided UI for stage approvals beyond writing `readiness-gates.json` and running validation
- no provider-neutral prompt file generation command

Closed gaps:

- master intake import: `import-intake` copies setup sources into `sources/` and records `source_intakes` provenance; `validate workspace` resolves intake paths (Phase 1 slice 1, 2026-07-03).
- reference-asset file existence, foundation completeness, and onboarding readiness milestones: `validate workspace` enforces the readiness blockers at `profile_ready`, `foundation_ready`, `strategy_ready`, `production_ready`, and `active` — selected channels, populated foundation files with required sections and lower-bound word/sample floors, no `TBD` placeholders, always-loaded context byte caps, at least one source intake, required asset kinds per declared content medium, lifecycle-appropriate asset/prompt file existence with workspace containment, media generation permission requirements, approved strategy records, conversion-asset provenance and production approval, and content-schedule integrity.

## Next Grilling Questions

1. Should the templates become validation targets, or remain authoring guidance only?
2. Should the Create Influencer workflow get a CLI command after the templates stabilize?
3. Should generated text-first creators still have an optional avatar/portrait recommendation by default?
