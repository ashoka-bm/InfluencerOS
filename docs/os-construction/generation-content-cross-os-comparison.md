# Cross-OS Comparison: The Generation / Content Stage

_InfluencerOS vs. Agentic OS (reference) vs. Artist OS (inspiration). Compiled 2026-07-06._

Status: **analysis + recommendations, not yet approved.** Recommendations are surfaced as
problem + recommendation for batch-gated execution. No schema, skill, or ADR change is
implied by this document existing. Where a claim is verified against files on disk it is
marked; per-platform format norms and the "hook/emotion/trigger/payoff" operator idea are
noted where they are synthesis-derived rather than dated evidence.

## 0. The framing that matters most: two different "generation" axes

The operator's questions and the current Phase 3 plan are about **two different things**,
and conflating them is the main risk.

- **Provider-safety / provenance axis** — IOS's planned "Phase 3 (Generation OS)": a
  provider registry, `GenerationApprovalRecord`, an asset-manifest ledger, and a blocking
  `QualityReview`. Its job is to gate paid provider calls, record where every asset came
  from, and refuse unsafe/unapproved generation. **Almost entirely unbuilt** (verified on
  disk: no `influencer_os/providers/`; none of `generation-approval-record.schema.json`,
  `quality-review.schema.json`, `asset-manifest.schema.json`; no matching CLIs — only
  schema constants in `base-video-generation-plan`/`output-package`/`reference-library` and
  policy prose in `docs/provider-boundary.md`).
- **Creative / content-direction axis** — the operator's actual questions:
  platform→modality→format taxonomy, intended emotion / core message, marketing content
  formulas (hook / emotion / trigger / payoff / CTA), and creative reviews (does the hook
  land, does it sound human). This axis is **upstream** of Phase 3 and partly ships already
  in Phase 1 (6-format shortlist, `social-template.beat_sequence`,
  `micro-journey-video-plan` hook/setup/escalation/payoff, `soul.md` emotional contract) and
  Phase 2 (`performance-summary` `[packaging, hook, body_retention, payoff, cta]`).

**Conclusion: do not fold the creative questions into Phase 3.** Phase 3 spends money and
should stay a lean safety spine. The creative work lands as Phase 1/2 schema extensions plus
one new lightweight creative-direction module, gated by human approval and *advisory*
content reviews — deliberately lighter than Artist OS, which is inspiration, not a
dependency. Keep the two axes as sibling concerns, exactly as the two paid-call worlds
(research connectors, standing-by-key; generation providers, exact-approval) are already
kept separate.

## 1. Comparison matrix

| Dimension | InfluencerOS | Agentic OS (reference) | Artist OS (inspiration) |
| --- | --- | --- | --- |
| Primary organizing axis for creation | Idea/format-first for production (6 formats); platform-scoped only for *research* (ADR 0020) | Platform-first at distribution, idea-first at creation; platform is a late output adapter | Medium-first (image/video/audio/text from artist intent); platform demoted to a coarse `publication_use` enum |
| Platform→modality→format tree | None on disk; platform + format live as parallel free-text arrays with no cross-constraint; creator active-platforms not a validated enum | No persisted tree; `(format, platform)` template pairs live in skill markdown tables | Deliberately none; README forbids platform limits and format grammar deciding medium |
| Format granularity | 6 coarse formats; article/thread/carousel collapse real subtypes (op-ed, LinkedIn article vs post, IG reel vs carousel) | ~3 creation formats + rich per-platform posting packages | ~40 named Cultural Format Structures with expected-parts + length standards |
| Emotion / intent model | Light, shipped: `intended_payoff` (required) + `intended_viewer_feeling` + per-shot `emotional_job`; durable `soul.md`. **No `intended_emotion`/`core_message` on live idea records** | Procedural prose: "So What?" chain, Schwartz awareness level, positioning angle, 7-dim rubric. No schema | Fully typed 4-record chain (Meaning→Brief→BeatPlan→MediumPlan): `why_it_matters`, must_preserve/may_transform/avoid, 8 core-tension pairs, per-beat feeling + numeric tension, hard Meaning Gate |
| Marketing formula skeleton | Real but split across two vocabularies: `social-template.beat_sequence` (free-text) + `micro-journey-video-plan` hardcoded hook/setup/escalation/payoff/loop. **No named TRIGGER stage; CTA usually absent from the template contract** | Most proven library, all prose: 10 named script frameworks (PAS, Before/After, Myth-Bust…) as timed HOOK→body→PAYOFF→CTA + an 8-category hook taxonomy | Heaviest: `beat_role` 16-enum + `expectation_turn` + numeric tension. Also ships a LIGHT micro-journey recipe: "hook → trigger emotion → forge one mental link" |
| Learning loop (formula → performance) | **Only system that closes it**: `performance-summary.stage_findings` enum `[packaging, hook, body_retention, payoff, cta]` (required, `minItems:5`) + `distilled_lessons.applies_to`. But not yet joined to template beat labels | Freeform learnings to `context/learnings.md`; no stage attribution | Critic reviews, but no post-publication performance attribution |
| Reviews / quality gates | Rigorous human approval + at-rest structural `validate`; `ProjectWarning` advisory only. **No content-quality review, no ReviewRecord.** `QualityReview` planned-only | Reviews as pipeline stages: blocking `ssc-designer` audits, auto-applied humanizer (0–10), advisory fact-checker. No review record type | First-class `ReviewRecord` (approve/revise/block, `drift[]`, emotional-tension review); mandatory independent sub-agent at every boundary; Clear-Writing + Human-Voice passes that never block |
| Provider/generation safety | Strongest design, entirely unbuilt: planned positional-arg dispatch seam + `approval_model` const `exact_approval` + kill switch; two-model split (research standing-by-key vs generation exact-approval) | Per-skill honor system ("show plan, ask first"); runtime `.env` key detection; static `requires_services` catalog | Runtime `assert_generation_approval` guard on disk that adapters MUST pass; conductor-only provider authority; sub-agents structurally barred |
| Implementation reality (generation stage) | **Least implemented despite strongest design** | Generation skills BUILT, calling real providers | Machinery BUILT (guard file, schemas, gate enum) |
| Cost gating at approval time | None; binary approve + batch `max_calls` cap only | Soft HeyGen credit pre-flight + optional test mode | `estimated_cost`/`actual_cost` in Output Record; approvals must name cost-bearing scope |

## 2. Similarities and differences

**Where all three already agree (validates our direction):**

- Dry-run / planning-first: each produces a provider-neutral plan and treats the paid call
  as a distinct, later, human-gated step.
- Explicit human approval naming the exact call/batch; all three reject "a general desire to
  create content" as approval.
- The same creative spine: **attention/hook → emotional middle → payoff** (AOS "3s hook +
  CTA"; ART "hook → trigger emotion → one mental link"; IOS hook→…→payoff).
- Intended feeling is a first-class planning field; durable persona/voice is separated from
  per-piece intent (IOS `soul.md` vs per-idea payoff; ART Meaning vs MediumPlan; AOS
  `brand_context` vs per-campaign copy).
- A reusable named-formula library, with structure/beats separated from the format
  container.
- **None** of the three hard-binds platform→modality→format at creation time; all keep
  platform and format as separate concerns. (So an *advisory* map is the shared instinct,
  not a hard tree.)

**Where they diverge:**

- Implementation vs. design: ART and AOS have BUILT generation machinery; IOS has the
  strongest *design* and the weakest *implementation*.
- Enforcement: AOS = honor system; ART = runtime guard function on disk; IOS = planned
  structural seam that does not exist yet.
- Emotion typing depth & timing: ART types emotion/arc across 4 schemas and captures it
  FIRST behind a gate; IOS uses ~3 free-text strings and names emotion LATE (production
  plan); `target_emotion` actually regressed out of the live pipeline under ADR 0020.
- Reviews: ART has a first-class blocking-capable `ReviewRecord` with enforced reviewer
  independence; AOS mixes blocking design audits with advisory content passes; IOS has no
  content-quality review at all.
- Learning loop: **only IOS** attributes performance to formula stages.
- Missing stages in IOS's formula contract: no named TRIGGER stage anywhere; CTA absent from
  the template/applied-beat contract despite `performance-summary` already scoring `cta`.
- Text-quality passes: ART has Clear-Writing + Human-Voice; AOS has humanizer + fact-checker;
  IOS has neither, despite now supporting article/thread text.

## 3. What to borrow, by source

- **From Agentic OS:** the 8-category hook taxonomy; the 10 named script frameworks (PAS,
  Before/After, Myth→Truth, "I Tried X", Listicle) as spine presets with topic-type→formula
  selection; the `(format, platform)` render-target pattern instead of exploding the format
  enum; the "re-invoke reviewer once with explicit feedback" loop; humanizer as an editorial
  pass.
- **From Artist OS (borrow-and-simplify):** the two-field `expectation_turn` as the TRIGGER
  stage (drop the numeric tension); the `must_preserve / may_transform / avoid` triad as an
  *optional* light guardrail; `ReviewRecord` shape and reviewer-independence rule; the
  Clear-Writing + Human-Voice editorial passes (non-blocking); the runtime
  `assert_generation_approval` guard; `estimated_cost`/`actual_cost` fields; the ~40
  Cultural Format Structures as a subtype seed with length norms as targets.
- **Explicitly NOT borrowed from Artist OS:** `beat_role` 16-enum, before/after/value-shift,
  numeric `tension_profile`, `minimum_tension_criteria`, `story_mode` ladder, Story Gate.
  Record as a deliberate divergence so future agents don't "restore parity."

## 4. Where to land — sequenced, batch-gated menu

Presented as a menu, not a bundle. **NOW = three small, high-leverage items** on records
already on disk; NEXT and LATER are held for their own approvals.

### NOW (small, creative layer — Phase 1/2 record extensions)

1. **Name emotion + message at idea capture.** Add two required short strings to the *live*
   records `IdeaQueueEntry` and `IdeaPromotion`: `intended_emotion` (the feeling the viewer
   walks away with) and `core_message` (the single point). Keep `intended_payoff`. Optionally
   revive `novelty_angle` (stranded on the deprecated `ContentIdeaSet`). Fixes the ADR 0020
   regression where `target_emotion` fell out of the live pipeline. _Note: this is a breaking
   change for existing fixtures — cheap since fixtures are disposable, but the validate/
   fixture-refresh churn is real; decide required-vs-optional at introduction._
2. **Adopt the five-stage Content Beat Spine** (§5) as one shared beat vocabulary reused by
   `social-template.beat_sequence` and `applied-social-template.applied_beats`. Adds the
   missing **TRIGGER** and **CTA** stages. Far lighter than ART beats by design.
3. **Close the learning loop.** Map the spine to the shipped `performance-summary` enum
   (HOOK→hook, EMOTION+TRIGGER→body_retention, PAYOFF→payoff, CTA→cta; packaging stays the
   pre-hook stage) and store the applied spine labels on the production plan. _Small decision,
   not free: `stage_findings` is required with `minItems:5`, so a performance record must
   still carry all five stages — an unused CTA needs an expressible "not_used" `result`, not
   an omitted stage._

### NEXT (small–medium, still creative layer)

4. **Typed hook-category enum** on the HOOK stage (port AOS's 8 categories) so the loop can
   learn which hook types win per creator/niche.
5. **`active_platforms` enum on the creator profile + an advisory capability map** (§6).
   Validate + warn, never block (honors ADR 0020's "source format must not constrain output
   format" and ART's anti-over-constraint stance). _First slice: `active_platforms` enum +
   advisory map + a SMALL article/thread subtype seed only — defer `platform_render_target`
   and `grounding_tier` layers._
6. **Format-subtype layer** seeded from ART Cultural Format Structures (op-ed, feature,
   explainer, personal essay, thought-leadership, newsletter dispatch; x-thread vs
   substack-note), carried as a `format_subtype` + optional `platform_render_target` rather
   than multiplying the format enum. Also clean `content_mediums` into a pure modality enum
   and resolve audio (add an audio-plan schema or drop audio until production supports it).
7. **Advisory hook/payoff review + `ReviewRecord` shape** (borrow ART, keep **advisory-only**
   for v1 — do not introduce a new blocking creative gate; reserve blocking for provider
   safety). An independent reviewer re-states the intended payoff and judges whether the plan
   delivers it. Keys directly to the product invariant's "intended payoff."
8. **Human-Voice Pass + Clear-Writing Pass** for article/thread text, as bounded *editorial*
   passes that rewrite + return a change trace, emit no `ReviewRecord`, and never block.
9. **One canonical `docs/gates-and-reviews.md`** map (mirroring ART) so new skills don't
   invent ad-hoc gates. Low effort; IOS has no single review/gate contract today.

### LATER (Phase 3 provider-safety spine — keep lean, do not merge with the above)

10. When Phase 3 executes: build **import-first** (slice 3 needs no provider and delivers
    real provenance/license capture); ship a single `assert_generation_approval` runtime
    guard every adapter (incl. mock) must pass (stronger than the positional-arg seam alone);
    add `estimated_cost`/`actual_cost` and surface the estimate at approval time — **without**
    ever relaxing exact-approval into a cost-threshold auto-approve; record the two-model
    split in ADR 0023 with a probe test; split `QualityReview` into a pre-generation intent
    check + post-generation review, run by an independent reviewer, single blocking gate.
11. **Carry the payoff invariant into `GenerationApprovalRecord`** — reuse the spine's
    hook/payoff as a light "meaning kernel" so batch/multi-variant generation can't drift off
    the intended payoff. Cheap bridge between the creative and safety axes.

## 5. Proposed formula — the Content Beat Spine

One lightweight, format-general, five-stage construct used everywhere a formula is expressed.
Reconciles the operator's hook/emotion/trigger/payoff idea with the shipped
`performance-summary` dimensions. (CTA-as-a-named-stage is synthesis-derived, motivated by the
already-shipped `cta` performance dimension and the operator's "product placement" note.)

Controlled `beat_role` enum; each stage keeps `viewer_question_answered` and a required
`intended_feeling`:

1. **HOOK** — the first move (~1–3s / first slide / first line) that stops the scroll and
   signals "this is for you." Carries a typed `hook_category` enum (identity_call_out,
   pattern_interrupt, contrarian, result_first, curiosity_gap, direct_challenge, confession,
   timeliness — from AOS).
2. **EMOTION** — the felt state the hook provokes and the piece rides (curiosity, tension,
   desire, recognition, delight), named as one `intended_viewer_feeling`.
3. **TRIGGER** — the open loop / promise / turn that makes staying feel necessary.
   Operationalized as ART's `expectation_turn` in **minimal two-field form only**:
   `{ promise_or_open_loop, why_staying_pays_off }`. No numeric tension.
4. **PAYOFF** — the answer/reveal/result/transformation that satisfies the hook's promise.
5. **CTA** — the single next action or loop-back (save, follow, comment keyword, product
   placement). Optional-but-named, so short pieces can loop back and product placement gets a
   first-class home **without any publishing/analytics feature**.

Performance mapping (learning loop): HOOK→hook, EMOTION+TRIGGER→body_retention, PAYOFF→payoff,
CTA→cta; packaging = pre-hook thumbnail/caption. Seed the template library with the AOS named
frameworks as spine presets.

## 6. Proposed taxonomy — platform → modality → format (ADVISORY)

Grounded in the shipped ADR 0020 8-platform set and the existing 6-format shortlist; format
subtypes seeded from Artist OS. **Advisory — validate + warn, never a hard per-Project
constraint.** Per-platform norms below are synthesis-derived starting points pending dated
research (only the IG 20-item carousel cap is currently cited, in `docs/social-post-formats.md`).

- **Level 1 — PLATFORM:** `creator.content_strategy.active_platforms` (new validated enum,
  reuse ADR 0020 set: x, instagram, tiktok, substack, medium, reddit, facebook, linkedin).
- **Level 2 — MODALITY:** `content_mediums` cleaned to a pure enum: text | image | video |
  audio (carousel/story_sequence move DOWN to the format level).
- **Level 3 — FORMAT:** the 6 production formats, each optionally carrying a `format_subtype`
  (from ART) and a `platform_render_target` (AOS pattern) for aspect/item-caps/LinkedIn-PDF
  semantics — instead of exploding the format enum.

Illustrative advisory map (starting point, not dated evidence):

```
substack   text  -> article (newsletter_dispatch | personal_essay | explainer | op_ed) | thread (substack_note)
linkedin   text  -> article (thought_leadership | framework_post | op_ed) | thread (post-style)
           image -> carousel (document/PDF) | single_image_post
instagram  image -> single_image_post | carousel (<=20 items) | story_sequence
           video -> short_form_video (reel)
tiktok     video -> short_form_video ;  image -> carousel (photo mode)
x          text  -> thread (x_thread) | article (note) ;  image -> single | carousel ;  video -> short_form
medium     text  -> article (feature | list | explainer | op_ed)
reddit     text  -> thread | article (explainer)
facebook   image -> single | carousel ;  video -> short_form
```

## 7. Open decisions (problem → recommendation)

1. **Formula stage set.** Problem: template beat labels are free text and can't join the
   shipped performance stages. Recommendation: adopt the fixed five-stage spine as a
   controlled enum + the performance alias. Reconcile the optional-CTA / `minItems:5`
   mismatch by expressing "not_used" in the performance `result`.
2. **Emotion at capture.** Problem: `target_emotion` regressed into the deprecated
   `ContentIdeaSet`; message is scattered. Recommendation: add required `intended_emotion` +
   `core_message` to `IdeaQueueEntry` + `IdeaPromotion`; decide required-vs-optional given
   fixture churn.
3. **Platform→format binding strength.** Recommendation: **advisory** (validate + warn), not
   a hard constraint.
4. **Format-subtype depth.** Recommendation: seed a small set under article/thread + a
   `platform_render_target`; decide how many subtypes for v1.
5. **`content_mediums` cleanup + audio.** Recommendation: pure modality enum; either add an
   audio-plan schema or drop audio until production supports it.
6. **Review blocking-ness.** Recommendation: creative reviews **advisory-only** for v1;
   blocking reserved for the provider-safety `QualityReview`.
7. **Divergence ADR.** Recommendation: record that IOS deliberately keeps the light 3-string
   emotion model + 5-stage spine and does NOT adopt ART Beat Plan / tension / story_mode /
   Story Gate — write it before schema work so future agents don't restore parity.
8. **Phase 3 sequencing.** Recommendation: do NOT interleave creative work into Phase 3;
   land creative extensions on Phase 1/2 records now; keep Phase 3 lean and after Phase 2
   closeout.

# Part II — Refined four-axis analysis (2026-07-06 deep dive)

_Supersedes §§4–7 above where they conflict. Adds dated/cited platform research and pressure-
tests the proposed formula. Analysis only — no build. Corrections from an adversarial review
pass are already applied (see "Build-readiness caveats" at the end of Part II)._

**Research snapshot: 2026-07-06.** The platform capability map below is time-sensitive
research. Several ceilings could not be confirmed against official help pages (researchers hit
HTTP 403 on Substack and X docs), and platform features drift fast. **Every numeric limit here
is an advisory soft-warning pending re-verification, never a validation threshold.** Re-verify
before relying on any specific number.

## II-A. Marketing-formula spine — pressure-tested (refines §5)

The first-pass 5-stage spine (`HOOK → EMOTION → TRIGGER → PAYOFF → CTA`) was pressure-tested
against 10 frameworks (AIDA, PAS, Before-After-Bridge, StoryBrand SB7, short-form
Hook-Value-Payoff-CTA, Hormozi Hook-Retain-Reward, MrBeast open-loop, the 3s hook rule, the
Sugarman curiosity-gap lineage, and AOS's 10 named UGC formats). **Two structural corrections
make it lighter and better-aligned to the shipped schemas:**

- **EMOTION is not a peer stage — it's a cross-cutting attribute.** No proven framework has an
  "emotion" stage; every one treats feeling as the currency flowing through every beat. IOS's
  own shipped `micro-journey-video-plan` agrees — one top-level `intended_viewer_feeling` plus
  a per-shot `emotional_job`, not a feeling stage. Demoting EMOTION also lightens the model.
- **"TRIGGER" is the right concept, wrong name → rename to RETAIN.** As you defined it (open
  loop / promise / turn that makes staying feel necessary), it's real and well-attested —
  Hormozi's *Retain*, MrBeast's *open-loop*, the *curiosity gap*, AOS's *Value/Tension* body
  beat. But "trigger" reads as an instantaneous stimulus (that belongs in the hook); you mean a
  *sustained body beat*. **RETAIN** also reuses the already-shipped `performance-summary` stage
  name `body_retention` — one vocabulary across spine, templates, and the learning loop, free.

**Refined spine: `HOOK → RETAIN → PAYOFF → CTA`, with EMOTION as a cross-cutting attribute.**
4 content stages + 1 attribute — lighter than the first pass *and* lighter than Artist OS's
5-beat recipe.

1. **HOOK** (~first 3s / first slide / first line): stop the scroll and plant the open
   question. Carries a `hook_category` enum (~11 entries: the 8 AOS categories — identity
   call-out, pattern-interrupt, contrarian, result-first, curiosity-gap, direct-challenge,
   confession, timeliness — plus problem/solution, reveal/teaser, bold-promise).
2. **RETAIN** (the body beat, formerly TRIGGER): quick setup, then open a loop / make a promise
   / deliver the turn so leaving feels like a loss. **SETUP/CONTEXT folds into the front of
   this beat** (not a 6th stage). Proof/credibility and PAS-style agitation live here as
   sub-functions when the format needs them.
3. **PAYOFF**: close the loop; deliver the reward/insight/result. Credibility is an attribute
   of the payoff, not its own stage.
4. **CTA**: the next action — defined broadly to include soft product placement / offer /
   bio-link. The offer rides the CTA; it does not get its own stage.

**Learning-loop mapping:** `HOOK→hook`, `RETAIN→body_retention`, `PAYOFF→payoff`, `CTA→cta`;
`packaging` stays the pre-hook stage the spine omits but the schema scores. Because
`stage_findings` is required with `minItems:5`, a piece with no CTA expresses `result:"not_used"`
on the `cta` stage rather than omitting it. _Open question flagged by review: the
`performance-summary` stages are video-shaped; confirm the 4-stage spine maps cleanly onto
text/image formats (a Substack article's "body_retention" is read-completion, not watch-time)._

Borrow: AOS's 10 named frameworks as spine **presets** (topic-type → formula) + its hook
taxonomy; from ART, only the *concept* behind RETAIN (`{promise_or_open_loop,
why_staying_pays_off}`) — drop the numeric tension. Sources: hivedigital, gmass (BAB),
innatemarketinggenius (SB7), realmarketingsolutions (short-form 4-step), itsmostly (Hormozi),
openfair (MrBeast), trivision (3s rule), driveeditor (curiosity gap), AOS `mkt-ugc-scripts` /
`mkt-copywriting`.

## II-B. Emotion / intent model — refined (refines §4)

Artist OS types emotion across 4 records because artist provenance is sacred. IOS generates
net-new marketing content — there's no original to preserve — so it needs far less. **Borrow
three constructs, simplify each to one field or a small optional object, leave the tension
machinery behind.**

**Borrow-and-simplify (3):**

1. **`intended_emotion`** — one short phrase (~2–5 words, e.g. "relieved it's not their
   fault"). A like-for-like successor to the `target_emotion` that `content-idea-set` carried
   and its `IdeaQueueEntry` replacement silently dropped under ADR 0020. Highest-value borrow.
2. **`core_message`** — one sentence: the claim the audience walks away repeating. Elicited via
   AOS's "So What?" chain; persist only the sentence. Replaces the weak, scattered per-format
   hints (`article-plan.thesis`, `thread-plan.throughline`, none of which carry emotion).
3. **`payoff_guardrails`** — one *optional* object, two short arrays: `must_land` and `avoid`.
   Collapsed from ART's `must_preserve / may_transform / avoid` triad — **`may_transform` is
   dropped entirely** (in IOS everything unpinned is transformable; there's no original to
   preserve, so it collapses to `must_land` + `avoid`).

**Leave behind (do NOT adopt):** numeric tension (`core_tension_pairs`, `tension_intensity`,
`minimum_tension_criteria`), the 16-role beat vocabulary + `expectation_turn` structure,
`story_mode` ladder, the `key_emotional_movements` graph, and the hard Meaning Gate. _(ART
schema line refs from the deep read are in the external repo and were not re-verified here.)_
IOS already has one gate that matters — `IdeaPromotion` — and emotion/message ride through it
as fields, **not a second blocking approval.**

**Where emotion drops out today, and the continuous flow:** `IdeaQueueEntry` has
`hook`+`intended_payoff` but no emotion/message (the ADR 0020 regression); `IdeaPromotion`
forwards payoff but not emotion/message; only `micro-journey-video-plan` (1 of 6 plans)
re-introduces feeling locally, authored fresh because nothing upstream exists to inherit;
`base-video-generation-plan` carries none of it, so emotion vanishes as shots become free-text
prompts; `output-package.creative_performance_map[].intended_effect` and
`performance-summary.stage_findings` reconstruct a version at measurement time, never traced
from origin. Fix = capture once at `IdeaQueueEntry`, carry by reference through `IdeaPromotion`
→ all six plans (video already ≈ has it via `intended_viewer_feeling`) → `base-video-generation-
plan` → map into the existing `intended_effect` at packaging (no new field there) → score at
`performance-summary`.

**Field set:** `intended_emotion` + `core_message` on `IdeaQueueEntry` and `IdeaPromotion`;
`core_message` (+ alias `intended_viewer_feeling`) on the video plan; both on the other five
plans and on `base-video-generation-plan`; optional `payoff_guardrails{must_land, avoid}` on the
entry. **Correction from review: default these to OPTIONAL at introduction** (not required as the
deep-read table first proposed) — required strings on `IdeaQueueEntry`/`IdeaPromotion` are a
breaking change for fixtures; introduce optional, tighten to required in a later slice once the
capture skills populate them. Also resolve whether the video plan's `intended_viewer_feeling` is
*renamed* (breaking) or gets a *parallel* `intended_emotion` field.

## II-C. Platform → modality → format taxonomy — refined & cited (refines §6)

**Status: ADVISORY — validate-and-warn, never a hard gate** (honors ADR 0020 lines 44–45,
verified: "the source format should inform the evidence, but should not constrain the output
format"). A `none`/`analog` verdict warns the planner about native fit; it never blocks
Promotion or Project creation. A Reddit thread may become a Reel; a Reel may become a Substack
essay.

**Three levels:**

- **Level 1 — PLATFORM:** an `active_platforms` field on `creator.content_strategy`. **Correction
  from review: reuse the already-shipped 8-platform enum** (`x, instagram, tiktok, substack,
  medium, reddit, facebook, linkedin`) — verified present in `idea-queue-entry` and ~10 other
  schemas. There is no shared `$def` today (the enum is copy-pasted across schemas); the clean
  move is to factor it into a shared `$def` rather than mint an 11th copy.
- **Level 2 — MODALITY:** clean `content_mediums` (today
  `[text, image, video, audio, carousel, story_sequence]`) to a **pure modality enum
  `[text, image, video, audio]`**. `carousel`/`story_sequence` are FORMATS (already exist as
  `format_carousel`/`format_story_sequence`) — keeping them in `content_mediums` double-encodes
  the format axis. Leave `social-post-format.artifact_kind` as the separate format-shaped axis;
  **do not merge modality and artifact_kind.**
- **Level 3 — FORMAT:** the 6 formats, each optionally carrying `format_subtype` + a
  `platform_render_target` (aspect / item-cap / access-gate) — metadata only, **not** new
  production-plan schemas.

**Advisory capability map** (`native` = first-class object; `subtype` = distinct authored craft
in a shared container; `analog` = maps by convention, warn; `none` = no native surface, warn.
All numbers are 2026-07-06 soft-warnings, `(verify)`):

| IOS format | native | subtype/analog notes | none (warn) |
|---|---|---|---|
| short_form_video | IG Reel (9:16), TikTok, LinkedIn, X, FB (all video → Reels ~mid-2025), Substack video | Reddit = analog (no vertical feed); a `long_form_video` subtype rides the *same* container (TikTok up to 60 min, X Premium longer) | Medium (embeds only) |
| carousel | IG (up to ~20 items), TikTok Photo Mode, LinkedIn (**2 subtypes: document/PDF deck + multi-image**), Reddit gallery, FB | **X = analog: fixed ≤4 grid, NON-swipeable — warn "no swipe payoff"**; Substack = Note gallery (small) | Medium |
| single_image_post | IG, LinkedIn, X, FB, Reddit (title required) | TikTok = analog (Photo Mode edge); Substack = single-image Note | Medium |
| story_sequence | **only IG + Facebook** (both Meta, 24h) | — | **X, TikTok, LinkedIn, Reddit, Substack, Medium** (TikTok & LinkedIn built and killed Stories) |
| article | Substack (essay/feature/newsletter subtypes), Medium, LinkedIn (Article + Newsletter), X (**tier-gated**: Article needs Premium+, plain long-post needs Premium, free = 280 chars), Reddit self-post | FB = analog (long status, truncates) | TikTok, Instagram |
| thread | **true chain only on X**; single-throughline post on LinkedIn / TikTok | Reddit, FB, Substack (manual Note series) = analog | Medium, Instagram |

**Audio** is a *real modality but a single-platform capability*: of the 8, only **Substack** has
first-class creator audio (podcast RSS, transcripts, paid feeds). The other 7 never had it or
killed it (LinkedIn Audio Events, Reddit Talk). So audio **earns a modality slot but NO
production-plan schema in v1** — "dangling by design": selecting audio maps to `new` with a "no
audio plan schema yet" warning rather than silently creating an invalid Project. A future
`audio_podcast_episode` schema would be Substack-scoped.

**`format_subtype` seed (~12, optional metadata):** article → `essay` / `reported_feature` /
`newsletter_dispatch` / `rich_longform`; carousel → `designed_slides` (LinkedIn PDF) /
`photo_set` / `fixed_grid` (X); thread → `chain` / `single_post`; short_form_video → `clip` /
`long_form_video`. _Review caveat: confirm `long_form_video` stays metadata only and does not
become a de-facto new production plan (roadmap hasn't asked for one)._

## II-D. Reviews — refined (refines §7)

A small **Creative-Review Layer** of 5 reviews/passes, **advisory by default** (reusing the
shipped `ProjectWarning` primitive), kept cleanly separate from the *planned* Phase 3
provider-safety gate.

1. **Hook/Payoff Review** — emits ReviewRecord, *advisory*. Checks the hook earns attention, the
   payoff is delivered and traces to the `IdeaQueueEntry.intended_payoff`, the body sustains
   retention (no dead middle), and the CTA follows from the payoff. Runs after a plan is drafted,
   before the generation-approval gate, on all six plan types.
2. **Creator-Fit / Voice-Consistency Critique** — emits ReviewRecord, *advisory*. Flags
   niche/audience drift, unsupported claims, persona breaks against the Creator Profile + the
   traceability chain.
3. **Fact-Check Pass** — emits ReviewRecord, *advisory*. Verifies claims against **dated Research
   Evidence first, web second** (enforces the AGENTS.md dated-evidence rule).
4. **Clear-Writing Pass** — rewrite, emits NO record, *advisory*. Removes clutter/filler in
   article/thread/caption text; bounded edit depth; never a verdict, never a gate.
5. **Human-Voice Pass** — rewrite, emits NO record, *advisory*. Strips AI tells **checked against
   the Creator Profile voice** so the fix restores the creator's actual voice.

**Advisory-vs-blocking stance (v1):** every creative review and editorial pass is advisory — it
surfaces findings / a ReviewRecord / a rewrite and **never halts the pipeline on its own.** An
`approval_status: revise|block` is a strong recommendation to the human, not an auto-stop.
**Correction from review:** the deep read wired a "blocking escalation channel" into the Phase 3
QualityReview — but **that gate does not exist yet** (`schemas/quality-review.schema.json` is
absent; the generation plan calls it a not-yet-built slice-2 deliverable). So in v1 a reviewer's
real-world-risk flag (false claim about a real person/brand/product) is a **loud advisory the
human must acknowledge** — its realization as a hard block is **explicitly deferred to Phase 3**
and not designed now. Emit ReviewRecords from day one even while advisory (cheap; seeds the
Learning OS). Promoting any creative review to blocking later requires an ADR.

**Reviewer independence (local-first adaptation):** a producer skill must not self-certify its
own artifact; the conductor sequences review as a distinct step with a fresh, explicit packet.
Preferred = a bounded reviewer sub-agent; the local-first fallback = a fresh-context separated
review pass run by the conductor as its own turn. Record
`execution_mode: bounded_sub_agent | fallback_separated_pass` on every ReviewRecord. Only the
human waives a blocking finding.

**New schema (proposed, trimmed from ART):** `schemas/review-record.schema.json` — `review_role`
(IOS enum), `reviewer_execution`, `artifact_under_review`, `upstream_context` (IOS provenance
refs, **not** Artist Meaning), `matched[]` / `drifted[]` (severity `none…blocking`), `findings[]`,
`recommended_revision`, `approval_status (approve|revise|block)`, `human_waiver`. **Drop ART's
required `emotional_tension_review`;** keep an optional lighter `intended_payoff_review`. Plus a
canonical **`docs/gates-and-reviews.md`** so skills stop inventing ad-hoc gates.

**Separation from the (planned) Phase 3 QualityReview:** creative reviews gate *dry-run,
provider-neutral* artifacts (plans/prompts/captions, allowed without provider approval) and are
advisory; the QualityReview will gate *post-generation upload-ready media* and will block
packaging. No double-gating: a creative claim-risk can only advise; if it reaches generated
media it's re-adjudicated by the (future) blocking QualityReview. **Note the QualityReview is
planned, not shipped** — describe it in the future tense until Phase 3 builds it.

## II-E. Updated open decisions (problem → recommendation)

1. **Formula stages.** The 5-stage spine fails the pressure-test on two stages. → Adopt
   `HOOK → RETAIN → PAYOFF → CTA` (4) with EMOTION as a cross-cutting attribute; RETAIN reuses
   `body_retention`; reconcile `minItems:5` via `result:"not_used"` on unused `cta`.
2. **Emotion/message at capture.** → Add `intended_emotion` + `core_message` to `IdeaQueueEntry`
   + `IdeaPromotion` (+ optional `payoff_guardrails{must_land, avoid}`), **default optional at
   introduction**, tighten later. Resolve the video-plan `intended_viewer_feeling` rename-vs-
   parallel question.
3. **Platform binding strength.** → Advisory validate-and-warn only.
4. **`active_platforms` enum.** → Reuse the shipped 8-platform enum; factor it into a shared
   `$def` rather than add a parallel copy.
5. **`content_mediums` cleanup + audio.** → Pure modality enum `[text, image, video, audio]`;
   move carousel/story_sequence to the format level; keep audio selectable but build no audio-
   plan schema in v1.
6. **Format-subtype depth.** → Optional `format_subtype` (~12 seed) + optional
   `platform_render_target`; do not multiply the 6-format enum; keep `long_form_video` metadata-
   only.
7. **Review blocking-ness.** → All 5 creative reviews/passes advisory in v1 (reuse
   `ProjectWarning`); the only future auto-block is the Phase 3 QualityReview; real-world-risk
   flags are loud advisories now, realization deferred to Phase 3.
8. **Reviewer execution mode.** → Prefer bounded sub-agent; fallback to a fresh-context
   separated pass; record `execution_mode` on the ReviewRecord.
9. **Divergence ADR.** → Record that IOS keeps the light emotion model (3 fields + 1 optional
   guardrail), the 4-stage RETAIN spine, and advisory-only creative reviews, and does NOT adopt
   ART Beat Plan / numeric tension / story_mode / Story Gate / `emotional_tension_review`.
10. **Phase 3 sequencing.** → Do NOT interleave creative work into Phase 3; land the creative
    extensions on Phase 1/2 records now; keep Phase 3 the lean provider-safety spine after
    Phase 2 closeout.

## II-F. Build-readiness caveats (before any of the above is coded)

These are prerequisites the analysis surfaced; none are done yet:

- **Skill-registry reconciliation.** New review skills / capture skills must be checked against
  `docs/os-construction/skill-registry.md` and `context-matrix.md` *before* schema work
  (AGENTS.md), and any creator-runtime copies refreshed via `sync-creator-runtime`.
- **Traceability invariant.** A new `ReviewRecord` and the new emotion/message fields must
  satisfy the AGENTS.md product invariant (each record references its immediate upstream);
  decide what `validate` enforces on the new links.
- **Required-vs-optional / migration.** Introduce new fields optional-first; new required fields
  are breaking changes for fixtures (disposable, but real validate/refresh churn).
- **Platform map is dated research.** Re-verify the 2026-07-06 numbers before relying on any;
  keep them advisory soft-warnings, never validation thresholds. Set a re-verify cadence.
- **Surface size.** The reviews layer (ReviewRecord + 5 reviews + gates doc + execution modes) is
  a large surface for one slice — sequence it (e.g. ReviewRecord + Hook/Payoff + Fact-Check
  first) per "smallest change that advances the first slice."

## 8. Sources

Two workflow passes, 2026-07-06. Pass 1: five-dimension cross-repo read + web research on content
frameworks + adversarial critique. Pass 2: eight per-platform dated web-research agents +
formula pressure-test + emotion/reviews deep reads + consolidation + adversarial critique. Repos:
`InfluencerOS`, `agentic-os` (reference), `Artist generation` (inspiration). Load-bearing IOS
facts verified against files on disk: `performance-summary.schema.json` `minItems:5` + stage enum;
absent `influencer_os/providers/`, `quality-review.schema.json`, `generation-approval-record.schema.json`,
`review-record.schema.json`; the shipped 8-platform enum in `idea-queue-entry` (+ ~10 schemas, no
shared `$def`); `content_mediums` double-encoding formats; the dropped `target_emotion`; the
idea/plan emotion-field distribution. Platform capability numbers are dated 2026-07-06 web
research and are advisory pending re-verification.
