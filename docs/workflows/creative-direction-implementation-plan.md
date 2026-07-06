# Creative Direction Workstream Implementation Plan

Last updated: 2026-07-06

Status: **Complete (2026-07-06).** All four slices executed in the agreed
batch order with per-slice gpt-5.5 adversarial reviews and fix batches; the
six runnable exit criteria pass and the closeout run is recorded in
`docs/os-construction/progress.md`. The architectural decisions were locked
in ADR 0024 (grilling session, 2026-07-06) and the four execution-mechanics
decisions below were user-approved on 2026-07-06 (A: drift-pin test;
B: `hook_category` optional in slice 1; C: seed five presets; D: clean-break
restructure).

Naming note: this workstream is **not** the roadmap's Phase 3 (Generation OS).
Phase 3 remains the provider-safety spine
(`docs/workflows/generation-os-implementation-plan.md`, five decisions still
open, ADR 0023 reserved). The Creative Direction workstream runs on the
creative axis, lands between Phase 2 closeout and Phase 3 execution, and never
touches `influencer_os/providers/` or generation machinery.

## Goal

Make creative intent first-class and continuous across the pipeline: one
canonical content structure (the Content Beat Spine), a light intent layer
(`intended_emotion`, `core_message`) captured at the idea origin and resolved
by reference downstream, an advisory platform→modality→format capability
model, and an advisory creative-review layer — all per ADR 0024, deliberately
lighter than the Artist OS reference material it borrows from.

Supporting analysis: `docs/os-construction/generation-content-cross-os-comparison.md`.
Decision record: `docs/adr/0024-creative-content-model.md`.
Glossary terms (already landed): Content Beat Spine, Intended Emotion, Core
Message, Modality, Format Subtype, Gate, Review, Review Record, Pass, Warning
(`CONTEXT.md`).

## Module Boundary

Inputs (all exist today):

- `idea-queue-entry` / `idea-promotion` (ADR 0020) with `hook` and
  `intended_payoff`,
- `social-template.beat_sequence` (`beat_label`, `beat_job` — free text) and
  `applied-social-template.applied_beats`,
- the six format-specific production plans; `micro-journey-video-plan` carries
  required `opening_hook/setup/escalation/payoff/loop_or_ending/
  intended_viewer_feeling`,
- `creator-profile.content_strategy` (`primary_surfaces` free-text,
  `content_mediums` enum including `carousel`/`story_sequence`),
- `performance-summary.stage_findings` (required, `minItems:5`, enum
  `[packaging, hook, body_retention, payoff, cta]`),
- `project-warning` (the advisory Warning primitive),
- the platform capability research in the comparison doc (dated 2026-07-06,
  advisory soft numbers).

Outputs (new or changed at-rest records and skills):

- spine-typed template beats (`beat_role` enum on `beat_sequence` and
  `applied_beats`),
- `intended_emotion` + `core_message` on `idea-queue-entry` and
  `idea-promotion` (schema-optional, skill-required),
- restructured `micro-journey-video-plan` (spine-shaped beats,
  `intended_emotion`),
- validated `primary_surfaces` (8-platform enum) + pure-modality
  `content_mediums` + optional `format_subtype` on production plans +
  platform-fit advisory warnings,
- `schemas/review-record.schema.json` (lean), `docs/gates-and-reviews.md`,
  and three skills: `review-hook-payoff`, `clear-writing-pass`,
  `human-voice-pass`.

Not in scope (unchanged deferrals per ADR 0024 and AGENTS.md):

- anything under `influencer_os/providers/` or the Phase 3 slices,
- publishing, scheduling, analytics, platform adapters,
- `intent_guardrails`, per-plan `emotional_emphasis`, `long_form_video`
  subtype, `platform_render_target`, audio production-plan schema,
- Fact-Check Review and Creator-Fit Critique (reviews second slice, later),
- blocking creative reviews (promotion to blocking requires its own ADR).

## Entry Criteria Verification (2026-07-06)

1. **Phase 2 Learning OS closed.** Pass — all six slices complete 2026-07-06,
   six runnable exit criteria met, full adversarial review recorded
   (`progress.md`; commits through `38e7e17`). The shared surfaces this
   workstream touches (`idea-queue-entry`, `performance-summary`,
   `rebuild-index`) are no longer being edited by a parallel session.
2. **ADR 0024 recorded and glossary landed.** Pass — `docs/adr/0024`,
   `CONTEXT.md` terms committed (`baf21c8`).
3. **Skill-registry / context-matrix current.** Pass — Phase 2 closeout
   reconciled them; this plan adds rows with the slices that create skills.

## Success Condition — Runnable Exit Criteria

The workstream exits when every check passes and is recorded in `progress.md`:

1. **Spine is the one template vocabulary.** Every `social-template`
   `beat_sequence[]` item and `applied-social-template` `applied_beats[]` item
   carries `beat_role` from the closed enum
   `[hook, retain, payoff, cta, packaging]`; `validate examples` passes; a
   drift check fails on any template whose beats skip `hook` or `payoff`
   (test).
2. **Intent is captured at origin and survives promotion.** A new
   `IdeaQueueEntry` written by `manage-idea-queue` carries `intended_emotion`
   and `core_message`; `promote-idea` copies both onto the `IdeaPromotion`
   verbatim; `validate workspace` fails a promotion whose values contradict
   its source entry (carry-forward probe test). Schemas keep both fields
   optional (fixtures unaffected); the skills always populate them.
3. **Plans resolve intent by reference.** `micro-journey-video-plan` is
   spine-shaped (`hook`, `retain`, `payoff`, `cta_or_loop`,
   `intended_emotion`) and `validate project` resolves every production
   plan's `idea_promotion_id` to a promotion carrying intent when the source
   entry had it; no plan stores an overriding copy (test).
4. **Learning loop speaks spine.** `create-performance-summary` attributes
   each `stage_findings` stage to the applied template's `beat_role` beats;
   an unused CTA is expressed as a `cta` stage finding with
   `result: "not_used"`, never an omitted stage (`minItems:5` still
   validates) (test).
5. **Platform model is validated and advisory.** `primary_surfaces` validates
   against the 8-platform enum; `content_mediums` validates against
   `[text, image, video, audio]`; a drift-pin test asserts every platform
   enum copy across schemas is identical; choosing a format not native to the
   creator's surfaces yields a `ProjectWarning` (`platform_fit` type) and
   never blocks promotion or project creation (tests).
6. **Reviews first slice works and cannot block.** `review-hook-payoff`
   writes a validating `ReviewRecord` with findings keyed to
   `[hook, retain, payoff, cta, general]` and recorded
   `reviewer_execution.execution_mode`; a `block` status on a creative
   ReviewRecord does not stop `validate project` or packaging (advisory probe
   test); `clear-writing-pass`/`human-voice-pass` return rewritten text plus
   a change trace and write no ReviewRecord; `docs/gates-and-reviews.md`
   exists and a registry drift check covers the three new skills (tests).

Standing checks green through every slice: unittest discovery,
`validate examples`, drift checks, fixture workspace validation,
`update-creators` sync.

## Implementation Sequence

ADR 0024's batch order, smallest first. Each slice is its own approved batch.

### Slice 1: Content Beat Spine + intent at the idea origin

- `beat_role` enum (`hook | retain | payoff | cta | packaging`) added to
  `social-template.beat_sequence[]` and
  `applied-social-template.applied_beats[]` (required on items; existing
  fixture templates migrated — small set, disposable).
- `intended_emotion` + `core_message` added optional to `idea-queue-entry`
  and `idea-promotion`; `manage-idea-queue` and `promote-idea` skills updated
  to always capture/carry them (schema-optional, skill-required; AOS
  "So What?" chain as the elicitation technique in the skill text).
- Carry-forward validation: promotion values must match the source entry.
- Template library re-seeded: existing templates get `beat_role` typing;
  preset expansion per Decision C.
- Docs: architecture-map rows; no new skills (registry rows unchanged).

### Slice 2: Carry-through and performance alignment

- `micro-journey-video-plan` restructured to the spine (Decision D):
  `opening_hook`→`hook`, `setup`+`escalation`→`retain`,
  `loop_or_ending`→`cta_or_loop`, `intended_viewer_feeling`→
  `intended_emotion`; per-shot `emotional_job` unchanged (it is the per-beat
  emotion attribute the spine expects).
- Resolve-by-reference checks in `validate project` (exit criterion 3).
- `create-performance-summary` skill updated to attribute stage findings to
  applied `beat_role` beats and to write `result: "not_used"` for absent CTA.
- Fixture refresh for the restructured plan; `rebuild-index` untouched
  (no new record types).

### Slice 3: Platform, modality, and subtype sharpening

- `primary_surfaces` constrained to the 8-platform enum; single-source
  mechanics per Decision A.
- `content_mediums` reduced to `[text, image, video, audio]`;
  Medium-Based Blocker logic re-keyed to four modalities; audio stays
  selectable, standalone-audio production warns (`no audio plan schema yet`).
- Optional `format_subtype` on the article/carousel/thread plans with the
  seed `[essay, reported_feature, newsletter_dispatch]` /
  `[designed_slides, photo_set]` / `[chain, single_post]`.
- Platform-fit advisory: a `platform_fit` `ProjectWarning`
  (`native | subtype | analog | none`) computed when a production plan picks
  a format, keyed off the capability map; map numbers stay doc-side advisory
  (dated 2026-07-06), never validation thresholds.
- Fixture refresh for profile strategy blocks.

### Slice 4: Reviews first slice

- `schemas/review-record.schema.json` (lean, per ADR 0024): refs +
  `review_role` + `findings[]` (`area` in
  `[hook, retain, payoff, cta, general]`, severity
  `none|low|medium|high|blocking`, note, recommended revision) +
  `approval_status` + `reviewer_execution {execution_mode, source_skill,
  fallback_reason}` + `human_waiver` + `created_at`.
- `docs/gates-and-reviews.md`: the canonical control contract — gate order,
  two layers (creative-advisory vs future provider-safety-blocking),
  advisory rule + must-acknowledge real-world-risk carve-out, independence +
  execution modes, ReviewRecord contract, waiver rule, "new blocking review
  requires an ADR" checklist.
- Skills: `review-hook-payoff` (Review; independent packet-fed step),
  `clear-writing-pass` and `human-voice-pass` (Passes; bounded rewrites with
  change trace, no record) — each with same-batch skill-registry,
  context-matrix, and conductor rows; creator runtimes refreshed via
  `sync-creator-runtime`.
- Review records live under `projects/<slug>/reviews/`; at-rest validation
  (dangling refs, unknown roles) in `validate project`; advisory probe test
  proves a `block` status halts nothing.

## Schema Deltas

- `social-template` / `applied-social-template`: `beat_role` enum on beat
  items (slice 1).
- `idea-queue-entry` / `idea-promotion`: optional `intended_emotion`,
  `core_message` (slice 1).
- `micro-journey-video-plan`: spine restructure — breaking, fixtures
  refreshed (slice 2).
- `creator-profile`: `primary_surfaces` enum, `content_mediums` reduced
  (slice 3, breaking for fixtures).
- `article-plan` / `carousel-plan` / `thread-plan`: optional `format_subtype`
  (slice 3).
- `project-warning`: `platform_fit` warning type (slice 3).
- New: `review-record.schema.json` + examples + drift-pin coverage (slice 4).
- `project.schema.json`: `project_paths` gains `reviews/` (slice 4, first
  writer).

## Guard Rules Carried Into Every Slice

The Phase 2 guard rules apply verbatim (writer/at-rest parity, sibling
guards, one shared writer, unresolvable-ref probes, inventory-doc sweeps,
skill folders land with registry/matrix rows, advisory gates key on durable
outputs). This workstream adds:

10. No creative Review, Pass, or Warning may block a pipeline step; every
    slice that adds one ships the advisory probe test proving it.
11. Nothing in this workstream imports from or modifies
    `influencer_os/providers/` (which must not exist until Phase 3) or any
    generation-approval surface.

## Execution Decisions (APPROVED 2026-07-06)

### Decision A: Platform-enum single-source mechanics — drift-pin test, not cross-file `$ref`

Problem: the grilling locked "one canonical 8-platform enum via a shared
`$def`," but no schema in the repo uses cross-file `$ref` today and the
validator is custom Python; introducing `$ref` resolution is new machinery.

Approved: keep per-file enums but add a drift-pin test asserting every
platform enum copy (≈10 schemas + the new `primary_surfaces`) is identical to
one canonical constant in `influencer_os/validation.py`. Same guarantee,
smallest change, matches the existing drift-check house pattern. Revisit
`$ref` only if schema count grows.

### Decision B: `hook_category` — include in slice 1 as optional

Problem: the AOS-derived hook taxonomy (8 categories + 3 web-validated) was
recommended in the comparison but never locked in the grilling.

Approved: add `hook_category` as an **optional** enum on `hook`-role beats in
slice 1 (one field, no new record). It costs nothing while unused and is what
lets the Learning OS eventually rank hook styles per creator.

### Decision C: Template preset seeding — five presets in slice 1

Problem: the comparison recommends seeding the template library with proven
named frameworks as spine presets; volume is unbounded if left open.

Approved (user chose the larger seed over the recommended three): seed five
in slice 1 — PAS, Before/After-Bridge, Listicle, Myth→Truth, and "I Tried X"
— typed with `beat_role`, alongside migrating the existing templates; grow
further from real usage.

### Decision D: Micro-journey restructure — clean break, no aliases

Problem: the spine restructure of `micro-journey-video-plan` can be a clean
break (rename/merge fields) or keep legacy fields as aliases for
compatibility.

Approved: clean break (`setup`+`escalation` → one `retain` object;
`intended_viewer_feeling` → `intended_emotion`), fixtures refreshed in the
same slice. Fixtures are disposable build data (roadmap policy); aliases
would preserve the double vocabulary ADR 0024 exists to remove.

## Coordination

- Phase 2 is closed; no parallel-session contention expected on
  `idea-queue-entry` / `performance-summary`. Re-verify HEAD before each
  slice commit (concurrent-session hygiene).
- Phase 3 (Generation OS) planning is untouched; its five decisions and
  ADR 0023 remain open and are not blocked by this workstream. The reviews
  slice references the future QualityReview only in `gates-and-reviews.md`
  prose, future tense.

## Migration Notes

- Breaking fixture changes land with their slice (template beats, micro-
  journey restructure, profile strategy block); fixtures are disposable
  (roadmap Build/Test Data Policy).
- No data migration for real creators exists yet (none onboarded).

## Verification Cadence

Each slice ends with the standing checks plus a full-workflow replay in
`.tmp/` (idea → promotion → applied template → plan → performance summary →
review, extended per slice), recorded in `progress.md`. The workstream
closeout run demonstrates exit criteria 1–6 green on one fixture creator.
