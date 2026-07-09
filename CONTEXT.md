# InfluencerOS

InfluencerOS is an agent operating system for creating researched content plans and generation-ready packages. The current runtime onboards influencer workspaces; product and brand onboarding is an accepted target that has not shipped yet.

## Language

**InfluencerOS**:
The product and repository that helps a user choose an existing creator profile, research current platform-scoped content patterns, maintain concise Research Findings and a scored Idea Queue, and turn one promoted idea into format-specific production plans, starting with the universal short-form base video generation plan.

**Creator**:
The current runtime term for an onboarded influencer identity, not the human operator behind it. ADR 0026 also reserves Creator as the future umbrella term for an influencer, product, or brand/company. The `creator_*` vocabulary, workspace path, and CLI commands remain stable when that target ships.

**Creator Type (Accepted Target; Not Yet Shipped)**:
The planned discriminator that says which kind of subject a Creator is: `influencer`, `product`, or `brand`. When implemented, it will determine which foundation documents and profile fields are required through the existing status-gated readiness mechanism (ADR 0013, ADR 0026). The current schemas and setup implementation do not carry or route on this discriminator.

**Representation Model**:
The current onboarding choice describing how an influencer appears publicly: synthetic, avatar-led, human-backed, text-first, or mixed. It affects media and reference needs, but it is not the planned Creator Type discriminator.

**Influencer**:
The Creator Type for an avatar, persona, or account identity. Its foundation is persona-led: Identity (lore), Soul File (psychology), Personal Brand File, Voice Samples File, and avatar visual-continuity references (character plates, wardrobe, camera, locations).

**Brand (Accepted Target; Not Yet Shipped)**:
The Creator Type for a company or organization. Its foundation is a Brand Brief (mission, category, positioning, value proposition, market and competitors), Brand Guidelines (logo, palette, typography, visual system, imagery rules), and a Brand Voice guide. It has no persona psychology or lore; positioning and values replace Soul.

**Product (Accepted Target; Not Yet Shipped)**:
The Creator Type for a specific offering. Its foundation is an Offering document (features, benefits, USPs, use cases, pricing tier, proof points) plus inherited brand context (positioning, guidelines, voice) and product visual references (product shots, packaging). A product may name a `parent_brand_ref`; in v1 the parent brand's context is kept inline in the product workspace (ADR 0026).

**Creator Profile**:
The structured operational identity record for the current influencer runtime. It carries the shared spine (niche, audience, positioning, content strategy, boundaries, goals) and requires persona fields such as persona summary, voice cadence, and visual identity. It does not yet carry Creator Type; ADR 0026's future product/brand route will add the discriminator and type-specific foundations. InfluencerOS treats niche and audience as inputs, not as guesses.

**Creator Workspace**:
The ignored local folder for one creator's private identity, references, research history, projects, memory, analytics evidence, and progress. It lives under `workspace-library/creators/<creator-slug>/`.

**Creator Setup**:
The strict foundation workflow that turns minimal instructions, guided interview answers, source files, media references, or a generated persona request into a Creator Workspace. Setup is permissive at intake and strict at readiness.

**Creator Readiness**:
The setup status that says what the creator can safely do next. Readiness statuses are `draft`, `profile_ready`, `foundation_ready`, `strategy_ready`, `production_ready`, `active`, and `archived`. The legacy-named `readiness-gates.json` file stores readiness milestone state, blockers, human waivers, foundation mode, and media permission booleans that decide whether image, video, or spoken-voice content is allowed. These milestones are deterministic checks, not pipeline Gates; only the two human approvals defined under Gate can block production authorization.

**Project**:
One selected content idea that moves into production as a publishable content unit or package. A Project may produce a video, carousel, single image post, story sequence, or multi-platform output package; it does not imply a posting cadence.

**Identity**:
The human-readable long-form identity document for one creator. It captures biography, lore, relationship to audience, recurring facts, voice examples, and continuity rules that are too rich for the typed Creator Profile.

**Soul File**:
The human-readable psychology and belief document for one creator. It captures values, belief matrix, emotional logic, triggers, soothers, voice cadence, and behavioral consistency.

**Personal Brand File**:
The human-readable brand strategy document for one creator. It captures positioning, platform posture, monetization rules, disclosure rules, visual brand, commercial boundaries, and growth goals.

**Voice Samples File**:
The creator's compact set of gold-standard voice examples. It stores exact samples, source context, content mode, reason, and confidence separately from identity, soul, and brand strategy so agents load examples only when style fidelity matters.

**Content Strategy**:
The creator's planned publishing direction: platform roles, monthly format mix, intentionally irregular cadence principles, related-post chains, conversion paths, lead magnet or offer references, topic and pillar strategy, intended audience response, and research implications. `content-strategy.json` is the machine-readable strategy record; `brand_context/personal-brand.md` remains the rich narrative source; `creator-profile.json` stores the operational summary.

**Channel Registry**:
The creator's selected and optional publishing channels. `channels.json` records platform, role, account or handle readiness, content mediums, expected format IDs, and whether a real handle is required before publishing/export. Selected channels drive the reference requirements for `foundation_ready`.

**Conversion Asset**:
A lead magnet, offer, newsletter asset, checklist, waitlist, landing page, or other conversion mechanism referenced by strategy or calendar slots. Conversion assets live under `conversion-assets/*.json`; `strategy_ready` requires referenced records to exist, while a production slot that promotes one requires it to be approved or published-ready.

**Reference Library**:
The creator's reusable visual and audio continuity assets, such as character identity plates, turnaround sheets, macro detail cards, locations, outfits, props, video style cards, shot-family references, ElevenLabs Voice Design prompt packages, and approved/imported voice samples.

**Reference Asset**:
One reusable or planned continuity item in the Reference Library. A Reference Asset may be planned, prompted, user-provided, generated, approved, or retired.

**Visual Continuity Plan**:
The reviewed creator-setup record that evaluates candidate props, product/brand objects, and production spaces for brand meaning, atmosphere, brand expression, recurrence, visual usefulness, continuity sensitivity, and risk before any candidate becomes a Reference Asset.

**Signature Prop**:
A user-approved, identity-attached object whose consistent appearance materially strengthens creator recognition or brand meaning across multiple pieces. Generic set dressing and one-off scene objects are not Signature Props.
_Avoid_: recurring object, meaningful prop

**Signature Object**:
A user-approved product, packaging form, or organization-owned object whose consistent appearance materially strengthens product or brand recognition across multiple pieces. It is the product/organization counterpart to a Signature Prop.

**Anchor Space**:
A user-approved recurring production environment with a specific brand and atmosphere role whose visual continuity matters across multiple pieces. A place mentioned in creator lore or used for one scene is not automatically an Anchor Space.
_Avoid_: production space, recurring location

**Supporting Visual Motif**:
A repeatable visual cue that contributes atmosphere or brand expression but does not need a fixed Reference Asset. It may vary between projects without harming continuity.

**Atmosphere Role**:
The specific feeling, identity signal, or brand meaning that a candidate object or space contributes when it appears on screen.

**Medium-Based Blocker**:
A Creator Setup blocker that applies only when a content medium requires it. Text-first creators need identity, soul, and brand context; image and video creators also need visual references; audio/video creators need a staged ElevenLabs Voice Design prompt package before `foundation_ready`; spoken generation requires an approved/imported voice reference.

**Research Findings**:
The concise rolling creator-scoped summary of what current research shows. It is
backed by dated evidence records and should stay short enough for practical
review. It highlights what is working, weakening, emerging, stale, and worth
watching across the creator's relevant platforms and topics.

**Research Evidence**:
One compact sourced record from a real post, article, thread, creator account,
or other public source. It stores the source URL, platform, platform content
type, captured timestamp, visible metrics when available, topic tags, pattern
notes, evidence strength, and limitations.

**Metric Snapshot**:
A timestamped capture of visible metrics for one Research Evidence source. It
allows the system to observe velocity and trend movement over time without
duplicating the full source record.

**Creator Content Schedule**:
A creator-scoped planning record that captures cadence expectations,
intentionally irregular publishing dates, content goals, platform or format
targets when useful, open slots, time-sensitive insertions, and drift checks. It
is separate from the Creator Profile because schedule state changes more often
than creator identity. It references the accepted Content Strategy; slots may
name their strategy campaign/variant and must name the approved use and platform
when they promote a Conversion Asset.

**Video Understanding Pack**:
A dated evidence record created when InfluencerOS inspects real videos. It stores source URLs or local files, analysis method, hook observations, first-frame patterns, visual structure, transcript framing, template signals, and creator-fit findings.

**Social Post Format**:
A platform-agnostic content container such as short-form video, carousel, single image post, or story sequence. The format says what kind of artifact is being made before a format-specific template is applied.

**Modality**:
What a piece of content is fundamentally made of: text, image, video, or audio. Modality is distinct from a piece's Social Post Format (its container) and from the platform it is published to. A creator declares the modalities they work in; each format belongs to a primary modality (a carousel is image, a thread is text).

**Format Subtype**:
An optional refinement of a Social Post Format that names the specific craft being made — for example an op-ed, reported feature, or newsletter dispatch for an article; designed slides or a photo set for a carousel; or a reply chain versus a single throughline post for a thread. It is advisory, chosen at production time, and never forces a piece to be classified.

**Idea Queue**:
The creator-scoped Kanban-style backlog of researched content opportunities.
Queue entries are scored, tied to research findings and evidence, and may be
updated as trends heat up or go stale.

**Idea Queue Entry**:
One potential content idea in the Idea Queue. It records the premise, intended
payoff, platform or format recommendations, source findings, evidence links,
scores, status, urgency, schedule fit, and promotion readiness.

**Idea Promotion**:
The human-approved act of moving one Idea Queue Entry into the creation funnel.
Promotion may immediately create one or more Projects and must preserve links to
the research findings, evidence, metrics, and reusable creative elements that
sparked the idea.

**Social Template**:
A reusable visual post structure such as hook-problem-solution, before-process-payoff, hook-steps-payoff, or identity-signal. Each template is a named arrangement of the Content Beat Spine. It improves retention, clarity, and emotional movement without defining the content idea itself.

**Applied Social Template**:
The selected template as adapted to one promoted Idea Queue Entry. It states the structural beats, why the template fits, and how each beat maps onto the idea.

**Content Beat Spine**:
The canonical four-stage structure every piece of content follows: Hook, Retain, Payoff, and CTA. Hook stops the scroll and opens a question; Retain sustains attention through setup and an open loop, promise, or turn; Payoff resolves the promise; CTA invites the next action, including soft product placement. Emotion is not a stage but a cross-cutting attribute: each beat names the feeling it drives. The spine is the shared vocabulary that Social Templates arrange, format-specific production plans instantiate, and the Creative Performance Map and Performance Attribution score (Hook, Retain as body retention, Payoff, CTA, plus the pre-hook Packaging stage they also track).

**Intended Emotion**:
The single feeling a piece of content is meant to leave its audience with, named as a short phrase. It is the canonical, format-neutral term for the audience's emotional takeaway and supersedes the earlier "target emotion" and the video-specific "intended viewer feeling." Captured once when an idea is formed and carried by reference through promotion and every format-specific plan, where each Content Beat Spine beat expresses how it drives that emotion.

**Core Message**:
The one point the audience should walk away able to repeat, stated as a single sentence. It is the canonical, format-neutral term for a piece's central claim; format-specific elaborations such as an article thesis or a thread throughline refine it but do not replace it. Like Intended Emotion, it is captured at idea time and carried through to the payoff.

**Micro-Journey Video Plan**:
The Content Beat Spine instantiated for one universal short-form video. It names the hook, the retain beat (absorbing what were formerly the separate setup and escalation beats), the payoff, the visual movement, the emotion each beat drives, and the shot logic.

**Carousel Plan**:
The slide-by-slide production plan for a swipeable image sequence. Each slide carries one visual beat.

**Single Image Post Plan**:
The production plan for one strong still, graphic, or generated image.

**Story Sequence Plan**:
The frame-by-frame plan for a short vertical visual sequence with an ephemeral story feel.

**Base Video Generation Plan**:
The provider-neutral plan for generating the core video assets. It focuses on avatar consistency, setting, action, continuity, shot sequence, and prompts. It does not include platform-specific motion graphics or posting strategy in v1.

**Output Package**:
The upload-ready set of materials for a finished post. Depending on format, it may include images, video files, title, caption, description, thumbnail, alt text, asset manifest, and source provenance.

**Creative Performance Map**:
The lightweight required map inside an Output Package that connects packaging, hook, body retention, payoff, and CTA decisions to source references, intended effects, and judging metrics.

**Published Post Record**:
The record that links an Output Package to a real platform publication. It stores where and when the post was published, the public URL or platform identifier, and the creator/account context.

**Analytics Snapshot**:
A dated measurement record for a Published Post Record. It stores platform metrics and qualitative notes so later research and idea generation can learn from prior performance.

**Performance Attribution**:
The interpretation layer that maps analytics back to creative decisions. It separates packaging, hook, body retention, payoff, and CTA performance so the Learning OS can tell what likely worked.

**Universal Short-Form Video**:
The v1 output target: vertical, short, hook-first, visually legible without platform context, and suitable for Instagram Reels, TikTok, and YouTube Shorts without requiring platform-specific planning.

**Provider Boundary**:
The line between local planning and external generation. Drafting plans is allowed; image/video/render generation requires explicit user approval.

**Gate**:
A human approval that can block the pipeline until granted. InfluencerOS has two: Idea Promotion (moving an idea into production) and the Provider Boundary generation approval (authorizing a paid provider call). Gates are always human-owned; nothing auto-approves them.

**Review**:
An advisory expert judgment of a drafted artifact that produces a Review Record and may recommend approve, revise, or block. In v1 a Review never halts the pipeline on its own; its recommendation is surfaced to the human, who decides. Reviews are distinct from Gates, which block, and from Passes, which rewrite.

**Review Record**:
The record a Review produces (lean v1 shape, `schemas/review-record.schema.json`). It names the artifact refs under review, the reviewing role, spine-keyed findings with severity and recommended revisions, how the reviewer ran (`reviewer_execution`), and an advisory status of approve, revise, or block. Only a human may waive a blocking finding. Matched/drifted tracking is deferred until the Creator-Fit Critique ships.

**Pass**:
A bounded editorial rewrite of an artifact, such as a Clear Writing Pass or a Human Voice Pass, that returns improved text and a change trace. A Pass emits no Review Record, makes no judgment, and never blocks.

**Warning**:
A durable, non-blocking advisory signal attached to a record. The Project Warning is the primary example; platform-fit advisories, raised when a chosen format is not native to a creator's platform, are surfaced as Warnings.

**Feedback Automation**:
Automation where each cycle is conditioned on evidence from prior cycles, triggered by events and thresholds rather than the clock. Contrast with temporal automation (clock-scheduled jobs), which is deferred in v1. Phase 4 Improvement OS builds feedback automation only (ADR 0025).

**Declare-Then-Attest**:
The capture discipline for auditable work: a record of intent written before the work, an attestation of what actually happened written after, and a mechanical at-rest reconciliation of the attestation against durable side effects. Research runs (search plan then source yield, exact declared outputs) and generation approvals (results must equal the approved request) already follow it. Intent-versus-attestation deltas are learning signal; attestation-versus-disk deltas are integrity failures and fail closed.

**Production Rubric**:
The growing list of binary quality criteria that removes ambiguity about what good means. Each criterion is answerable yes/no about a specific artifact, carries a scope (OS-level craft rules or creator-level boundaries), and its id doubles as the recurrence key for counting violations. Criteria mature from advisory to proven to promoted into the blocking quality checklist.

**Rubric Ratchet**:
The rule that converts taste into criteria: every rejection of a draft, prompt, or asset must cite an existing Production Rubric criterion or mint a new one. Rejections that cannot be articulated are logged unclassified; accumulating unclassified rejections signals a rubric gap rather than being ignored.

**Rejection Event**:
A durable, recurrence-keyed system event recording that a draft, prompt, or asset was rejected and why — the cited criterion plus a one-line reason. Verdicts are durable; the rejected material itself stays ephemeral and is never committed.

**Reflection Trigger**:
The event-driven signal that reflection is due: when recurrence counts or unprocessed-event thresholds are crossed, an advisory warning is surfaced and badged. Improvement work is triggered by what happened, never by the clock; the human review rides this trigger — distillation proposes, the human approves.

**Improvement Claim**:
The falsifiable statement attached to a distilled skill or routine update, naming the criterion it targets and the expected violation-rate change, verified against subsequent runs. A refuted claim reopens the fix; a confirmed claim closes it.

**Performance Delta**:
The per-stage comparison of what a Creative Performance Map predicted against what analytics measured, scored confirmed, refuted, or unmeasurable. Refuted predictions are learning, not failures — they are the Performance Delta loop's raw material.
