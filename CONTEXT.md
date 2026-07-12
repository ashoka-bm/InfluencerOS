# InfluencerOS

InfluencerOS is an agent operating system for creating researched content plans and generation-ready packages. The current runtime onboards influencer workspaces; product and brand onboarding is an accepted target that has not shipped yet.

## Language

The Campaign, Content Opportunity, and commercial-expression terms below are
the shipped runtime model (ADRs 0029-0032, landed 2026-07-10, and ADR 0047,
landed 2026-07-12): the campaign,
concept, approval, opportunity, and queue schemas, constructors, and staged
approval commands are implemented, and the idea-queue records they replace
are gone (ADR 0031). Terms explicitly marked Deferred remain compatibility
targets only and must not create obligations in the current implementation.

**InfluencerOS**:
The product and repository that helps a user choose an existing creator profile, research current platform-scoped content patterns, maintain concise Research Findings and a scored Content Opportunity Queue, and turn one approved Campaign Concept into format-specific production plans, starting with the universal short-form base video generation plan.

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
The setup status that says what the creator can safely do next. Readiness statuses are `draft`, `profile_ready`, `foundation_ready`, `strategy_ready`, `production_ready`, `active`, and `archived`. The legacy-named `readiness-gates.json` file stores readiness milestone state, blockers, human waivers, foundation mode, and media permission booleans that decide whether image, video, or spoken-voice content is allowed. Milestones are validated by deterministic checks, but the block exits of the operating cadence are human decisions: `foundation_ready` flips on the human ready check that closes Creator Setup, and `production_ready` is granted by the Strategy block's human final approval (ADR 0044). These block-exit approvals are readiness decisions, not pipeline Gates; only the two human approvals defined under Gate block the content pipeline.

**Project**:
One independently planned publishable content unit created from a Concept Approval and owned by exactly one Campaign Concept. It is the source of truth for exact planned Offer Integration, CTA Intensity, and derived Commercial Pressure; it has one format, one materially stable Hook-Retain-Payoff execution and core asset, and its own lifecycle, output package, publications, analytics, and evaluation. Platform adaptations remain one Project, while a materially changed execution is another.

**Assisted Campaign Attribution (Accepted Target; Deferred)**:
A predeclared secondary contribution from a Project owned by another Campaign Concept. It may inform assisted evaluation but never turns one Project or publication into two independently owned successes.

**Campaign Outcome Attribution (Accepted Target; Deferred)**:
The evidence-qualified classification of an outcome as directly attributed, assisted, or unattributed. Direct attribution requires an observable source such as a tracked link, platform conversion, coupon, or declared response; incomplete journeys remain unattributed rather than receiving invented last-touch or fractional credit.

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

**Content Series**:
A recurring anchor-and-derivative publishing pattern in Content Strategy. It
defines how formats relate and recur, while a Campaign defines why a stream of
work exists and what outcome it pursues. A calendar slot may belong to both a
Content Series and a Campaign.
_Avoid_: operational campaign, objective

**Content Pillar**:
A durable thematic territory the creator intends to own across many campaigns. A Pillar describes what the creator consistently talks about, not whether a particular campaign nurtures, sells, or converts.
_Avoid_: funnel stage, campaign objective

**Campaign**:
A stable identity for a coordinated stream of work with one typed primary objective and, for sales, one primary paid offer. Its lifecycle is `draft`, `active`, `paused`, `completed`, or `archived`; it may run indefinitely through extended Duration Targets, while a material objective or primary-offer change creates a separate Campaign. Immutable Campaign Revisions and Waves are accepted but deferred.
_Avoid_: temporary content batch, objective-changing phase

**Campaign Duration Target**:
The `target_end_date` every Campaign declares at creation — unbounded in either direction, shorter or far longer than a Quarter. It is a measurement hypothesis, never an auto-stop: an active Campaign running past it surfaces an advisory Warning in validation and the campaign projection, and a retro question; the Quarterly Planning Cycle retargets, extends, shortens, or completes against it. A retarget is not a material identity change and never creates a new Campaign (ADR 0047).
_Avoid_: campaign deadline, fixed campaign length

**Campaign Revision (Accepted Target; Deferred)**:
An immutable sequential version of one Campaign's approved measurable target, primary and supporting Audience Segments, primary and supporting Content Pillars, and effective policy scope. Exactly one Revision is current, while every Campaign Wave and Concept Approval retains the Revision that governed it.
_Avoid_: in-place campaign edit

**Campaign Objective**:
The one OS-typed primary outcome category that defines Campaign identity and benchmark cohort, paired with a specific measurable outcome. The initial vocabulary is `awareness`, `audience_growth`, `trust_nurture`, `lead_generation`, `paid_conversion`, `customer_retention`, and `reactivation`; supporting benefits may be recorded but never act as equal primary objectives.
_Avoid_: tactic, format, metric name

**Audience Segment**:
A named subset of the creator's target audience with a distinct context, need, or buying state. A Campaign declares one primary Segment and optional supporting Segments, and every Campaign Concept targets exactly one Segment from that approved set.
_Avoid_: arbitrary per-post audience

**Campaign Wave (Accepted Target; Deferred)**:
A bounded tactical period within one Campaign with one emphasis, cadence, Pressure target, and measurement plan. Exactly one Wave may be active per Campaign; parallel Concepts and experiments run inside it, and an unchanged Campaign Concept may continue into later Waves through new Approvals.
_Avoid_: objective change, campaign replacement

**Campaign Concept**:
A stable, testable message, framing, or commercial hypothesis owned by exactly one Campaign and expressed through multiple Projects with different hooks, formats, examples, and CTAs. It selects exactly one Audience Segment and one Content Pillar from the Campaign's approved primary or supporting sets. Its lifecycle is `draft`, `researching`, `ready_for_approval`, `active`, or `retired`; first completed Approval activates it, while a material change to tension, promise, audience, or hypothesis creates a linked Concept.
_Avoid_: loose idea, post idea

**Content Opportunity Queue**:
The creator-scoped backlog of researched Content Opportunities that do not yet belong to a Campaign. It preserves wildcard discoveries without creating placeholder Campaigns or nullable Campaign Concepts.
_Avoid_: campaign queue, placeholder campaign

**Content Opportunity**:
A researched direction with evidence and potential creator fit that has not yet been assigned to a Campaign. Its lifecycle is `new`, `researching`, `ready`, `assigned`, or `closed`; assignment records the resulting Campaign Concept, while closure records a reason such as rejected, expired, or duplicate.
_Avoid_: Campaign Concept with no campaign

**Concept Approval**:
An immutable human-approved snapshot of a Campaign Concept that authorizes an exact set of named Projects under maximum Offer Integration and CTA Intensity. Its Evidence refs are the exact ordered historical prefix captured from the append-only Concept Evidence list, and each created Project retains that snapshot's ordered Evidence IDs as a durable witness; deletion, reordering, duplication, rewriting, or injection invalidates the Approval. An unchanged Concept may receive multiple Approvals as production scope expands; later Approvals never rewrite or revoke prior authorization. A future Campaign Wave or Campaign Revision may be attached without changing this base contract.
_Avoid_: editable concept state

**Commercial Function**:
The job content is expected to perform for a Campaign. The initial vocabulary is `problem_awareness`, `demand_creation`, `trust_building`, `authority_building`, `objection_resolution`, `proof`, `lead_capture`, and `direct_conversion`. A Campaign Concept declares one primary Function for evaluation and may declare supporting Functions; each Project declares one execution Function from that approved set. Commercial Function is independent of how visibly an offer appears.

**Offer Integration**:
How prominently an offer appears in a Project: absent, embedded, contextual, or central. A Concept Approval sets the allowed ceiling and each Project declares its exact planned level; it is distinct from CTA Intensity so content can contribute to selling without behaving like a direct-response advertisement.

**CTA Intensity**:
The strength of the action requested from the audience: none, soft, or direct. A Concept Approval sets the allowed ceiling and each Project declares its exact planned level; CTA Intensity combines with Offer Integration to determine experienced Commercial Pressure.

**Commercial Pressure**:
The audience-facing sales pressure `none`, `low`, `moderate`, or `high`, derived from Offer Integration and CTA Intensity through one OS-wide matrix. Creators may set limits on Pressure but cannot redefine its inputs or derivation; it is never manually assigned and remains distinct from the content's underlying Commercial Function.

**Audience Touch**:
One planned or published content unit on one platform for Commercial Pressure accounting. Every high-pressure publication counts, while supporting credit is earned once per distinct Project-platform pair; a carousel or Story sequence is one Touch regardless of slides or frames, and a cross-platform release creates one Touch on each platform.
_Avoid_: asset, frame, slide

**Pressure Policy (Accepted Target; Deferred)**:
A versioned set of creator-baseline or Campaign-specific Commercial Pressure target bands. The initial 3:1 supporting-to-high-pressure mix is a default prior; the combined creator-platform band remains the final audience-experience constraint, departures require an explicit portfolio experiment, and evidence may recommend future policy versions without rewriting historical approvals.

**Pressure Profile (Accepted Target; Deferred)**:
A rebuildable aggregate of pressure-tier distribution, offer and CTA patterns, sequencing, and audience or conversion outcomes over a declared scope. Standard per-platform windows are the most recent 5 Audience Touches, most recent 20, current Campaign Wave, and Campaign or selected Campaign Revision range; custom windows are supplemental, and component measures remain available beside the Pressure Indicator.

**Pressure Projection**:
The initial rebuildable per-platform view over the current Creator Content
Schedule horizon. It reports known Project-linked Touches by pressure tier,
the Pressure Indicator, the share of known Touches at high pressure, and the
number of unresolved pre-Project slots. It warns above 25% high pressure but
never treats unresolved slots as low pressure or blocks work.

**Pressure Indicator**:
A versioned 0–100 projection that initially maps `none`, `low`, `moderate`, and `high` to weights 0, 1, 2, and 3, then normalizes their weighted mean by the maximum weight. Raw profile components remain canonical; changing weights or formula rebuilds the projection and never changes Audience Touch classifications or historical policy snapshots.

**Pressure Experiment (Accepted Target; Deferred)**:
A human-approved, bounded test of a proposed Pressure target outside the effective creator-platform policy. It declares its hypothesis, scope, target band, maximum Audience Touch count, expiration date, one primary success measure, at least one audience-harm guardrail, and stop conditions; direct harm measures are preferred, unavailable measures use marked proxies, and missing data is unmeasurable rather than zero. It ends at the first duration boundary reached, and automation may recommend or stop a test but cannot approve or extend it.
_Avoid_: override flag, permanent exception

**Cross-Creator Pressure Benchmark (Accepted Target; Deferred)**:
A shared benchmark built from each creator's de-identified outcome changes relative to their own baseline, aggregated initially by platform and Campaign objective. Raw content, audience data, creator identity, and Creator Workspace records never enter the benchmark; additional cohort dimensions require enough data to avoid sparse comparisons.

**Pressure Evidence Maturity (Accepted Target; Deferred)**:
The human-readable confidence ladder `observed`, `directional`, `repeatable`, and `candidate_default` for cross-creator Pressure findings. Initial thresholds are one measurable experiment; three experiments across two creators; six across three; and ten across five, with consistent direction and no unresolved repeated audience-harm signal. Maturity may recommend a policy version but never changes policy without human approval.

**Channel Registry**:
The creator's selected and optional publishing channels. `channels.json` records platform, role, account or handle readiness, content mediums, expected format IDs, and whether a real handle is required before publishing/export. Selected channels drive the reference requirements for `foundation_ready`.

**Conversion Asset**:
A lead magnet, offer, newsletter asset, checklist, waitlist, landing page, or other conversion mechanism referenced by strategy or calendar slots. Conversion assets live under `conversion-assets/*.json`, name their immediate upstream Content Strategy, and record explicit user approval before entering an approved lifecycle state. `strategy_ready` requires referenced records to exist, while a production slot that promotes one requires it to be approved or published-ready.

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

**Planning Cycle**:
A recurring human-initiated ceremony that runs research, advisory Reviews, and record updates, and ends in human final approval. Both cycles are shipped: the Quarterly Planning Cycle and the Weekly Planning Cycle. A Planning Cycle contains Reviews; it is not itself a Review.
_Avoid_: quarterly review, weekly review (as ceremony names)

**Quarter**:
A creator-relative planning horizon of thirteen weeks, anchored at the creator's `production_ready` date and rolling thereafter. Quarters are per-creator, not calendar-aligned.

**Quarterly Planning Cycle**:
The once-per-Quarter Planning Cycle: a retrospective over the closing Quarter's performance and learnings, per-Campaign research, next-Quarter Campaign Concepts and schedule shape, and any amendment proposals for the locked setup and strategy foundations. Human-initiated, never clock-scheduled; an expired Quarter surfaces as a Warning. Conducted by the shipped `quarterly-planning-cycle` skill, which produces one approved Quarter Plan through `scaffold quarter-plan`, executes its approved lifecycle, Duration Target, schedule, and Revision changes, then performs a ready check.

**Weekly Planning Cycle**:
The once-per-week Planning Cycle that finalizes the coming week's slots. Conducted by the shipped `weekly-planning-cycle` skill: focused `scheduled_needs` research on scheduled Campaign Concepts and Anchor Slots, 2-3 candidate Content Opportunities per Anchor Slot, one advisory Concept Review per Anchor Slot, human topic selection, constructor-owned research refresh while the slot is still `candidates_ready` when a scheduled Concept is selected directly, ADR 0031 assignment when a new Opportunity is selected, human Concept Approvals, and a ready check. It reuses the shipped slot gate and creates no new promotion path or record type.

**Anchor Slot**:
A calendar slot carrying an anchor content unit — one that needs its own focused research and human topic selection rather than inheriting another slot's. Derivative slots point to one Anchor Slot and inherit its selected subject evidence while still needing native format adaptation.
_Avoid_: derivative slot (as a synonym)

**Quarter Plan**:
The record a Quarterly Planning Cycle produces: the retrospective findings over the closing Quarter, the next Quarter's Campaign Concept set (new and re-confirmed), Campaign lifecycle decisions, Campaign Duration Target changes, the schedule shape, and any Foundation or Strategy Revision proposals. One human approval covers the whole plan, and every approved plan names the terminal Quarterly Review that judged its complete draft packet. Proposed Revisions are constructed after that plan so they can point back to it. The Quarterly Planning Cycle is the default home for Campaign pause/complete/archive decisions; an ad hoc human change mid-Quarter is recorded by the next Quarter Plan.

**Reactive Slot (Accepted Target; Not Yet Shipped)**:
A reserved open calendar slot for timely, news-driven content, allocated by the Content Strategy and filled through a fast-path Concept Approval when a watched development breaks. The human gate is not skipped; speed comes from the Reactive Campaign, pre-chosen templates, and the reserved slot.

**Reactive Campaign (Accepted Target; Not Yet Shipped)**:
The standing Campaign that owns news-driven timely content. Approved once with the Content Strategy and re-confirmed each Quarter Plan; its Concepts fill Reactive Slots through fast-path Concept Approvals.
_Avoid_: news campaign, standing reactive campaign

**Monitor Note (Accepted Target; Not Yet Shipped)**:
A watchlist annotation flagging an expected imminent development worth waiting for — a release, announcement, or event. The shipped Weekly Planning Cycle maintains imminent-development watch notes in research narrative as conductor prose only; there is no Monitor Note record type. Triggered-note consumption remains unbuilt because its Reactive Slot consumer is deferred.

**Foundation Revision**:
An immutable sequential version of the locked creator setup foundation (profile, identity, soul, brand, references). Exactly one Revision is current; a Revision is proposed and approved only through a Quarterly Planning Cycle, and readiness milestones never regress when one lands.
_Avoid_: in-place foundation edit

**Strategy Revision**:
An immutable sequential version of the locked Content Strategy and schedule shape. Exactly one Revision is current; a Revision is proposed and approved only through a Quarterly Planning Cycle, and prior Quarters retain the Revision that governed them.
_Avoid_: in-place strategy edit

**Research Demand**:
A Review finding that names specific missing evidence the artifact needs before approval. The shipped machine-readable Review Record marker is `research_demand: "new"` or `"carried_forward"`, distinguishing a new Demand from a repeated unresolved one. The Strategy block's loop cap and conductor wiring are live: each Strategy Review records its prior-review lineage and an `extra_research_round` of 0, 1, or 2; Research Demands drive the research-and-review loop, which closes when a Review issues no new Research Demands or reaches round 2, and remaining Demands attach to the human approval as open questions.

**Setup Review**:
The advisory bounded sub-agent Review inside Creator Setup that judges the text foundation and the auto-generated Avatar Image together, before fixes and the human Visual Continuity Plan approval (ADR 0046).

**Strategy Review**:
The advisory bounded sub-agent Review inside the Strategy block that judges the drafted creator strategy after the broad research validating it, before the human final approval that grants `production_ready` (ADR 0046).

**Quarterly Review**:
The advisory bounded sub-agent Review inside the Quarterly Planning Cycle that judges the draft Quarter Plan content (ADR 0046). Shipped as the `review-quarter-plan` skill (review_role `quarterly`). It is a Review inside the cycle, never a name for the ceremony itself: the ceremony is the Quarterly Planning Cycle.

**Concept Review**:
The advisory bounded sub-agent Review inside the Weekly Planning Cycle that judges one Anchor Slot's explicit 2-3-candidate packet before human topic selection or assignment (ADR 0046). Shipped as the `review-concept-promotion` skill (review_role `concept`) and written through `scaffold review-record`; it carries no `research_demand_loop`. The named Anchor Slot's `research_state.candidate_content_opportunity_ids` is the canonical packet boundary, and the seed artifact refs must match it exactly, so candidates from another Anchor Slot are never discovered or counted merely because a multi-slot run supports both. Its constructor validates the mutable `candidates_ready` packet fail closed. Once written, it is a point-in-time audit record: later slot selection and Opportunity assignment do not invalidate it. Advisory only — distinct from Concept Approval, the human Gate that blocks.

**Avatar Image (ADR 0045)**:
The one platform-facing identity image every creator must have, regardless of Representation Model. Setup generates it automatically when the user has not provided one; the intake interview decides what it depicts (a persona face or a non-face mark) for text-first creators. For synthetic and avatar-led creators it doubles as the visual-continuity calibration reference for the setup image pass. The human accepts or rejects it at Visual Continuity Plan approval; a rejected image regenerates only on a fresh exact-user, reference-scoped approval. The Plan's standing pass explicitly excludes the Avatar Image (ADR 0045).
_Avoid_: anchor image, profile picture

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

**Idea Queue (Replaced By Content Opportunity Queue, ADR 0031)**:
The legacy creator-scoped backlog name for researched content opportunities. The initial Campaign implementation migrates it to Content Opportunity Queue and retains no permanent dual-write compatibility.

**Idea Queue Entry (Replaced By Content Opportunity, ADR 0031)**:
The legacy record for one researched direction. The initial Campaign implementation migrates unassigned records to Content Opportunities and assigned production directions into Campaign Concepts with source provenance.

**Idea Promotion (Replaced By Concept Approval, ADR 0031)**:
The legacy human-approval record that authorizes Projects. The initial Campaign implementation migrates it to Concept Approval and updates downstream references without retaining a second approval hierarchy.

**Social Template**:
A reusable visual post structure such as hook-problem-solution, before-process-payoff, hook-steps-payoff, or identity-signal. Each template is a named arrangement of the Content Beat Spine. It improves retention, clarity, and emotional movement without defining the content idea itself.

**Applied Social Template**:
The selected template as adapted to one approved Project. It states the structural beats, why the template fits, and how each beat maps onto the concept's idea.

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
The line between local planning and external generation. Drafting plans is
allowed. An approved Visual Continuity Plan authorizes one initial generation
pass over exactly its listed creator-setup reference images, and Creator Setup
auto-generates the one Avatar Image on a bounded, single-use, system-derived
approval record with no human pre-approval (ADR 0045); every other image,
video, render, voice, regeneration, upload, and changed-scope call requires
exact approval.

**Gate**:
A human approval that can block the pipeline until granted. InfluencerOS has
two: Concept Approval (moving a Campaign Concept into production) and the
Provider Boundary generation approval. Gates are always human-owned. Creator
Setup may reuse the approved Visual Continuity Plan as the authorization for its
one bounded initial reference-image pass; this is not automatic approval. The
one bounded creator-setup Avatar Image call is a recorded carve-out from the
Provider Boundary (ADR 0045): it runs on a system-derived record with no human
pre-approval, and the human accepts or rejects the avatar at Visual Continuity
Plan approval. Block-exit human final approvals in the operating cadence are
readiness or plan decisions, not additional Gates.

**Review**:
An advisory expert judgment of a drafted artifact that produces a Review Record and may recommend approve, revise, or block. In v1 a Review never halts the pipeline on its own; its recommendation is surfaced to the human, who decides. Reviews are distinct from Gates, which block, and from Passes, which rewrite.

**Review Record**:
The record a Review produces (lean v1 shape, `schemas/review-record.schema.json`). It is project-anchored for creative reviews or workspace-anchored by Creator Profile for ladder reviews, and names the artifact refs under review, reviewing role, scope-appropriate findings, reviewer execution, and an advisory status of approve, revise, or block. Review Records are point-in-time audit records: mutable packet preconditions are enforced when a constructor writes them, while at-rest validation checks only durable schema, filename-to-record-id identity, owning-workspace Creator identity, scope, internal consistency, symlink-safe containment, and referential integrity. Only a human may waive a blocking finding. Matched/drifted tracking is deferred until the Creator-Fit Critique ships.

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
The event-driven signal that reflection is due: when recurrence counts or unprocessed-event thresholds are crossed, an advisory warning is surfaced and badged. Improvement *automation* is triggered by what happened, never by the clock; the human-initiated Quarterly Planning Cycle is the one calendar-shaped reflection ritual, and it is run by the human, not scheduled by the OS — an overdue cycle surfaces only as a Warning.

**Improvement Claim**:
The falsifiable statement attached to a distilled skill or routine update, naming the criterion it targets and the expected violation-rate change, verified against subsequent runs. A refuted claim reopens the fix; a confirmed claim closes it.

**Performance Delta**:
The per-stage comparison of what a Creative Performance Map predicted against what analytics measured, scored confirmed, refuted, or unmeasurable. Refuted predictions are learning, not failures — they are the Performance Delta loop's raw material.
