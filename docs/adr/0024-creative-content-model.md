# ADR 0024: Creative Content Model — Content Beat Spine, Light Intent Layer, Advisory Reviews

## Status

Accepted

Extended by ADR 0046: workspace-level Review Records with new review roles,
and the Research Demand research-review loop.

## Context

InfluencerOS's roadmap "Phase 3 (Generation OS)" is a provider-safety and
provenance layer (provider registry, generation approval records, asset-manifest
ledger, blocking quality gate). A 2026-07-06 cross-OS comparison against Agentic
OS (the architectural reference) and Artist OS (a storytelling-first inspiration,
not a dependency) surfaced that the operator's content questions —
platform→modality→format taxonomy, intended emotion and message, a marketing
content formula, and creative reviews — live on a **different axis**: creative
content direction. That axis is mostly upstream of Phase 3 and is largely
unbuilt. Pieces exist (the 6-format shortlist, `social-template.beat_sequence`,
`micro-journey-video-plan` hook/payoff, the `performance-summary`
`[packaging, hook, body_retention, payoff, cta]` learning stages), but the model
is inconsistent across formats, drops emotion before generation, and speaks no
shared vocabulary between planning and measurement.

This decision was reached through a grilling session
(`docs/os-construction/generation-content-cross-os-comparison.md` is the
supporting analysis). Artist OS was mined for constructs to borrow-and-simplify,
not to copy: the operator explicitly wants a model lighter than Artist OS.

## Decision

Build a **Creative Direction workstream** — deliberately distinct from the
roadmap's Phase 3 Generation OS — on the creative axis, never touching the
provider-safety machinery (`influencer_os/providers/`).

### 1. Content Beat Spine

The canonical content structure is a four-stage spine: **HOOK → RETAIN →
PAYOFF → CTA**, with **emotion as a cross-cutting per-beat attribute, not a
stage**. `RETAIN` (formerly the operator's "trigger") absorbs the
micro-journey's former `setup`/`escalation` beats. The spine maps onto the
already-shipped `performance-summary` stages (`HOOK→hook`,
`RETAIN→body_retention`, `PAYOFF→payoff`, `CTA→cta`; `packaging` stays the
pre-hook stage). An unused CTA is expressed as `result: not_used` so the
`stage_findings` `minItems:5` record still validates. Social Templates are named
arrangements of the spine; format-specific plans instantiate it.

### 2. Light intent layer

Two canonical, format-neutral fields — **`intended_emotion`** (the feeling the
audience walks away with) and **`core_message`** (the one sentence they repeat)
— supersede the video-specific `intended_viewer_feeling` and the deprecated
`target_emotion`. They are **captured at the idea origin** (`IdeaQueueEntry`) so
they inform prioritization, carried as a **single canonical value on
`IdeaPromotion`**, and **resolved by reference** (not overridden) by child plans.
Introduced **schema-optional but skill-required** (backward-compatible now,
tightened to required later). An optional per-idea `intent_guardrails`
(`must_land`/`avoid`) is **deferred**.

### 3. Platform → modality → format taxonomy (advisory)

- **Level 1 (platform):** sharpen the existing `content_strategy.primary_surfaces`
  into the validated 8-platform enum via a shared `$def` (no new
  `active_platforms` field; one platform concept).
- **Binding is advisory:** platform **guides, does not gate**. Off-platform
  format choices raise a non-blocking `ProjectWarning` (`native / subtype /
  analog / none`); nothing blocks promotion or project creation (honors ADR 0020).
- **Level 2 (modality):** reduce `content_mediums` to a pure modality enum
  `[text, image, video, audio]`; `carousel`/`story_sequence` live only at the
  format level; `artifact_kind` stays the separate format axis.
- **Audio** stays a selectable modality (covers voiceover and a Substack podcast
  focus) with **no v1 production-plan schema** — standalone audio warns; a future
  `audio_podcast_episode` schema would be Substack-scoped.
- **Level 3 (format subtype):** an optional `format_subtype` on the production
  plan, seeded small (article: `essay`/`reported_feature`/`newsletter_dispatch`;
  carousel: `designed_slides`/`photo_set`; thread: `chain`/`single_post`).
  `long_form_video` and `platform_render_target` are **deferred**.

### 4. Reviews (advisory)

- Canonical control vocabulary: **Gate** (human, blocking — Idea Promotion, the
  Provider Boundary), **Review** (advisory, emits a Review Record), **Pass**
  (editorial rewrite, no record), **Warning** (non-blocking signal).
- Creative Reviews and Passes are **advisory in v1**; only human Gates block (and,
  later, the Phase 3 provider-safety `QualityReview`). A real-world-risk finding
  (false claim about a real person/brand/product) is a **must-acknowledge
  advisory**, not a hard block; promoting any creative Review to blocking requires
  its own ADR.
- Five reviews, typed correctly (Fact-Check is a Review, not a Pass): Hook/Payoff
  Review, Creator-Fit Critique, Fact-Check Review, Clear-Writing Pass, Human-Voice
  Pass. **First slice:** the `review-record.schema.json` + a canonical
  `docs/gates-and-reviews.md` + the Hook/Payoff Review + both editorial Passes.
  Fact-Check and Creator-Fit follow later.
- **Reviewer independence:** the authoring skill may not certify its own artifact;
  review runs as a distinct step fed an explicit packet (not the full
  conversation). Prefer a bounded sub-agent, fall back to a fresh-context
  separated pass; record `execution_mode`. Only a human waives a blocking finding.
- **Lean v1 Review Record:** refs + `review_role` + `findings[]` keyed to spine
  areas (`hook/retain/payoff/cta/general`) + `approval_status` +
  `reviewer_execution` + `human_waiver`. `matched[]`/`drifted[]` are deferred to
  when Creator-Fit ships.

### 5. What is borrowed-and-simplified from Artist OS, and what is rejected

Borrowed and simplified: intended-feeling → one `intended_emotion` phrase;
`why_it_matters` → one `core_message` sentence; the Review Record shape; the
reviewer-independence rule (with a local-first fallback); the Clear-Writing and
Human-Voice passes. **Explicitly rejected** (so future agents do not "restore
parity"): the `beat_role` 16-enum, numeric `tension_profile` /
`minimum_tension_criteria`, `story_mode` ladder, the hard Story/Meaning Gate, the
required `emotional_tension_review`, and the `may_transform` guardrail (IOS
generates net-new content — there is no original to preserve).

## Considered Options

- **The operator's original five-stage spine** (`HOOK → EMOTION → TRIGGER →
  PAYOFF → CTA`): rejected because no proven framework models emotion as a peer
  stage, and "trigger" reads as an instant stimulus rather than a sustained body
  beat. Demoting emotion and renaming trigger→retain is lighter and matches the
  shipped `body_retention` stage.
- **Platform as a hard gate** (a Substack-only creator can only make written
  content): rejected — creators cross-post and platforms change; guide-not-gate
  honors ADR 0020.
- **A new `active_platforms` field:** rejected as a synonym for the existing
  `primary_surfaces`.
- **Schema-required intent fields immediately / per-plan emotion override /
  heavier blocking reviews / the fuller Review Record up front:** all rejected in
  favor of the smaller, backward-compatible, advisory-first change.

## Consequences

- Breaking (but low-cost, since fixtures are disposable) schema changes:
  `primary_surfaces` free-text → enum; `content_mediums` loses
  `carousel`/`story_sequence`; `intended_viewer_feeling` → `intended_emotion`.
- The plan→measure→learn loop finally closes on one vocabulary: planned spine
  stages align token-for-token with `performance-summary` stages.
- Sequencing: this workstream lands **after Phase 2 (Learning OS) closes** — Phase
  2 slices are implemented and awaiting final adversarial review — to avoid
  colliding on the shared `IdeaQueueEntry` and `performance-summary` records. It
  stays **off the provider-safety axis**; Phase 3 remains the lean spine (ADR 0023,
  reserved).
- Internal batch order (smallest-first): (1) spine + intent fields at the idea
  origin; (2) carry-through to plans + performance-summary alignment; (3)
  platform/taxonomy sharpening; (4) reviews first slice.
- Before any build: reconcile new skills/records against
  `docs/os-construction/skill-registry.md` and `context-matrix.md`, and confirm
  the new Review Record and intent fields satisfy the AGENTS.md traceability
  invariant.
