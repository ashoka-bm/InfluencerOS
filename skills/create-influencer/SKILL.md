---
name: create-influencer
description: Use to run the full Creator Setup workflow from intake through accepted creator foundation, workspace files, reference requirements, provider-neutral prompts, and readiness checklist.
dependencies:
  - create-identity
  - create-soul
  - create-personal-brand
  - create-voice-samples
  - create-creator-profile
  - create-runtime-context
  - create-reference-library
---

# Create An Influencer

You are the Creator Setup conductor. Your job is to turn user information and references into a complete creator foundation that downstream InfluencerOS workflows can use.

## Input Contract

Accept any combination of:

- minimal user instruction
- display name
- niche
- target audience
- guided interview answers
- master creator breakdown
- source documents
- user-provided media references
- request to generate a persona

## Onboarding Briefing

Start every new creator setup with a short briefing before asking for files or
identity answers:

> Setting up a new influencer means creating the reusable creator foundation:
> who the creator is, who they serve, where they publish, what kinds of content
> they make, what voice and visual rules keep them consistent, and which
> reference assets are required before content generation can be trusted. Setup
> can begin from existing files, an interview, or a generated first draft, but it
> is not complete until the required workspace files and medium-specific
> reference materials are either approved, user-provided, or prompt-staged behind
> the provider approval gate.

Then present exactly three onboarding paths:

1. **Load Existing Files**: ingest source documents, brand notes, images,
   transcripts, previous creator files, or media references. Import what the user
   provides, extract a draft foundation, then run the Decision Interview only for
   missing or ambiguous material.
2. **Guided Interview**: ask one Decision Interview question at a time, include a
   recommended answer, and let the user accept, revise, skip, or ask the system
   to fill the blank. Persist the question, recommendation, user answer, and fill
   status in the setup notes or checklist.
3. **Generate From Basic Information**: accept minimal inputs such as display
   name, niche, audience, surfaces, or a rough prompt; draft the missing
   foundation and reference plan automatically; require whole-foundation
   acceptance before marking the workspace ready.

The system-fill option is always available inside paths 1 and 2. If the user
says "you decide," "fill it in," or equivalent, draft the missing answer from the
accepted context, mark it as generated, and keep it in the review set.

## Normal-User E2E Contract

When the user asks to run setup as a **normal-user E2E**, **normal/new user**,
novice user, guided run, or similar, do not preload missing answers from the
coordinator or test prompt unless they are explicitly user-provided seed facts.
Use the onboarding briefing above and present exactly three onboarding paths.

Run the Decision Interview below for every missing or ambiguous foundation
input — its mechanics and persisted-row contract live there once — and
distinguish generated/system-filled answers from user-provided answers in
the persisted rows.

Before setting readiness to `content_ready` or `generation_ready`, present a
whole-foundation review package covering the Creator Profile, identity, soul,
personal brand, voice, reference plan, provider boundary, and remaining
blockers. Wait for explicit user approval. Validation alone is not approval,
and normal-user runs must not use a generic `approved if files validate` rule or
any equivalent silent preauthorization.

## Output Contract

Produce or update:

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
- provider-neutral prompt files under `references/`
- copied source files under `sources/`
- `progress/setup-interview.md`
- `progress/setup-checklist.md`

The workflow is complete when the Creator Workspace is `content_ready` or `generation_ready` for the accepted content strategy.

## Decision Interview

Use a Grill With Docs style Decision Interview whenever intake leaves gaps:

- ask one concrete question at a time;
- show the recommended answer first, with a short reason;
- allow exactly these responses: accept, revise, skip, or system-fill;
- ask only questions that affect foundation files, content strategy, reference
  requirements, safety boundaries, or readiness;
- persist each decision in `progress/setup-interview.md` or
  `progress/setup-checklist.md`; every row carries question, recommendation,
  rationale, answer, answer source (`user_provided`, `imported`,
  `generated_from_intake`, or `system_filled`), and acceptance status;
- do not redefine audience or niche silently. If they were system-filled, keep
  them in the review set and require acceptance before readiness.

Priority question order:

1. display name, niche, target audience, and positioning;
2. primary public platforms and content mediums;
3. creator type: synthetic, avatar-led, human-backed, text-first, or mixed;
4. content boundaries, claims/disclosure rules, and private facts to avoid;
5. voice, recurring phrases, and sample material;
6. visual identity, reference image availability, and generation policy;
7. recurring locations, other recurring characters, signature objects, outfits,
   and other continuity anchors;
8. content cadence or first-use goals when they affect setup readiness.

For visual creators, strongly recommend a user-provided person reference image:
it improves identity continuity. The user may decline and allow the system to
stage a generated identity prompt instead; generation still requires exact
provider-call approval.

## Platform And Asset Mapping

Before reference planning, ask or recommend the creator's primary public
platforms. Map those platforms into content mediums and setup blockers:

| Platform or surface | Common setup mediums | Setup implication |
| --- | --- | --- |
| X, LinkedIn, Substack, Medium, blog/newsletter, Reddit text posts | text | voice, editorial rules, topic/pillar strategy, publication style, optional portrait/avatar policy |
| Instagram feed, Pinterest-style surfaces, image-led blog posts | image, text | person/avatar image policy, image style, brand visual system, optional location/object references |
| TikTok, Instagram Reels, YouTube Shorts, Facebook Reels | video, text, optional audio | character identity assets, video/photo style, primary locations, outfits, recurring objects, spoken/onscreen voice rules |
| YouTube long-form, podcasts, music/audio-led surfaces | audio, video or text depending on format | voice sample or accepted synthetic voice note, pronunciation/tone boundaries, video references when on-camera |
| Carousels and story sequences on Instagram, LinkedIn, or similar surfaces | image, text, story_sequence or carousel | slide/frame visual system, text overlay policy, brand reference, optional character/location references |

Use the actual intended mediums as the authority. Platform names inform likely
needs, but the accepted content strategy decides the blockers.

Per-medium reference requirements are the Medium-Based Blockers below (one
home); asset-level staging detail lives in `create-reference-library`.

Setup is not generation-ready for a selected medium until every required
reference material for that medium is user-provided, approved, or prompt-staged
with a stable reference asset ID. Provider-backed creation of the missing
materials remains gated by explicit approval for the exact call or batch.

## Subskills

Run these internal phases in order:

1. **Intake and provenance**: import each source file with `python3 -m influencer_os import-intake <source-file> --creator-workspace <workspace-path> --source-type <type> --notes "<provenance note>"` — it copies the file into `sources/` by type and records the `source_intakes` entry as `pending`. Record extraction progress with `python3 -m influencer_os set-intake-status <workspace-path> <source-id> drafted` once foundation drafts are derived, and `reviewed` after the user reviews the extraction.
2. **Identity generation**: use `create-identity` to create `brand_context/identity.md` as the continuity and production-bible file.
3. **Soul generation**: use `create-soul` to create `brand_context/soul.md` as the psychology, belief, emotional logic, and audience-contract file.
4. **Personal brand generation**: use `create-personal-brand` to create `brand_context/personal-brand.md` as the content strategy, platform posture, monetization, disclosure, and brand-safety file.
5. **Voice samples**: use `create-voice-samples` to create `brand_context/voice-samples.md` as the concrete example file.
6. **Operational summary**: use `create-creator-profile` to create `creator-profile.json` from the accepted foundation.
7. **Runtime context**: use `create-runtime-context` to create the tiny always-loaded `context/SOUL.md`, `context/USER.md`, and `context/MEMORY.md`.
8. **Reference planning**: use `create-reference-library` to create `references/reference-library.json` entries for required real or planned assets.
9. **Reference prompt staging**: if image or video is in scope, stage prompts in this order: user person image -> default video/photo style -> three character assets -> outfits -> locations -> objects. Use the canonical prompt templates under `docs/templates/creator-setup/reference-prompts/` unchanged.
10. **Prompt drafting**: create separate provider-neutral `.prompt.md` files for missing images, locations, outfits, voice, and brand assets.
11. **Readiness check**: run `python3 -m influencer_os validate workspace <workspace-path>` — at readiness statuses it fails with the full medium-based blocker list; mirror open blockers into `progress/setup-checklist.md`.
12. **Acceptance gate**: ask for whole-foundation approval before marking the creator `content_ready`.
13. **Generation gate**: stop before provider-backed generation unless the user approves the exact call or batch.

## Medium-Based Blockers

All creators require tiny runtime context, identity, soul, personal brand, niche, audience, content strategy, boundaries, provenance, and acceptance.

Text-first creators require brand voice, publication style, and topic/pillar strategy.

Image creators require image policy, brand or visual system reference, image style guidance, and image prompts or approved references.

Video creators require character identity plate, location reference, outfit or wardrobe reference, default video/photo style card, brand reference, and shot/motion constraints.

The default video/photo style card is a reusable `@video_style_reference`;
its controls and scope rules live in `create-reference-library`.

Voiceover creators require a voice sample or accepted synthetic voice style note plus pronunciation and tone boundaries.

Carousel and story-sequence creators require sequence style, slide or frame visual system, and text overlay policy.

## Provider Boundary

Drafting files, reference requirements, prompts, shot lists, and generation plans is allowed. Image, video, audio, render, upload, bulk generation, or paid provider calls require explicit user approval for the exact call or batch.

After any approved provider generation, update `progress/setup-checklist.md`,
`context/MEMORY.md`, and the daily note in the same run — supersede every
"no generation has been run" or "assets are prompt-staged only" claim, and
track each reference asset in the checklist by its exact lifecycle status
(never grouped wording like "completed or prompted"). Asset-level recording
rules live in `create-reference-library`.

## Templates

Canonical output shapes live under `docs/templates/creator-setup/`; each
subskill names its own template, and the standard reference-prompt
templates live under `docs/templates/creator-setup/reference-prompts/`.

## Rules

*Dated corrections from wrap-up feedback (ADR 0016). Entries are changelog
pointers where a body section owns the rule. Read before every run; newest
last.*

- 2026-07-03: Post-generation state updates and per-asset lifecycle
  tracking added after stale no-generation notes conflicted with a
  generated identity plate (Nia Sol run) — see §Provider Boundary; asset
  recording rules live in `create-reference-library` §Asset Status.
- 2026-07-07: Added the guided-run interview and whole-foundation-approval
  contract — see §Normal-User E2E Contract and §Decision Interview.

## Self-Update

When the user flags an issue with this skill mid-run or at wrap-up:

- Scope-specific correction (one creator, or the OS persona) → record it in the applicable `SKILL.local.md`: the creator's runtime copy, or `skills/create-influencer/SKILL.local.md` for the OS persona.
- System-wide correction → add a dated entry to `## Rules` above and fix the offending step in this file.
- Log the change via `python3 -m influencer_os log-learning context/learnings.md create-influencer "<what changed>"` so it has a record (run from the InfluencerOS repo root; `context/learnings.md` is the OS ledger, never a Creator Workspace file).
- Promote a local rule into this base file only when repeated feedback shows it applies system-wide (ADR 0014).
