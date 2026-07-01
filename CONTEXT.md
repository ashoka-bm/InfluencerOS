# InfluencerOS

InfluencerOS is an agent operating system for creating short-form video concepts and generation plans for synthetic or avatar-led social media creators.

## Language

**InfluencerOS**:
The product and repository that helps a user choose an existing creator profile, research current social video patterns, generate creator-fit video ideas, and turn one chosen idea into a universal short-form base video generation plan.

**Creator**:
The avatar, influencer, persona, or account identity that content is being created for. In v1, creator means the public-facing avatar/profile, not the human operator behind it.

**Creator Profile**:
The structured identity record for the creator. It includes niche, audience, persona, visual identity, boundaries, recurring traits, and creator goals. InfluencerOS treats niche and audience as inputs, not as guesses.

**Creator Workspace**:
The ignored local folder for one creator's private identity, references, research history, projects, memory, analytics evidence, and progress. It lives under `workspace-library/creators/<creator-slug>/`.

**Creator Setup**:
The strict foundation workflow that turns minimal instructions, guided interview answers, source files, media references, or a generated persona request into a Creator Workspace. Setup is permissive at intake and strict at readiness.

**Creator Readiness**:
The setup status that says what the creator can safely do next. Readiness statuses include draft, foundation review, content ready, generation ready, active, and archived.

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
The creator's planned publishing direction: primary surfaces, content mediums, in-scope formats, out-of-scope formats, topic and pillar strategy, intended audience response, and research implications. `brand_context/personal-brand.md` is the rich source of truth; `creator-profile.json` stores the operational summary.

**Reference Library**:
The creator's reusable visual and audio continuity assets, such as character identity plates, turnaround sheets, macro detail cards, locations, outfits, props, video style cards, shot-family references, and voice samples.

**Reference Asset**:
One reusable or planned continuity item in the Reference Library. A Reference Asset may be planned, prompted, user-provided, generated, approved, or retired.

**Medium-Based Blocker**:
A Creator Setup blocker that applies only when a content medium requires it. Text-first creators need identity, soul, and brand context; image and video creators also need visual references; voiceover creators need a voice sample or accepted voice style note.

**Social Research Pack**:
A dated, sourced packet of current social video patterns, hooks, formats, creator references, and trend evidence. It supports idea generation but does not override the Creator Profile.

**Video Understanding Pack**:
A dated evidence record created when InfluencerOS inspects real videos. It stores source URLs or local files, analysis method, hook observations, first-frame patterns, visual structure, transcript framing, template signals, and creator-fit findings.

**Social Post Format**:
A platform-agnostic content container such as short-form video, carousel, single image post, or story sequence. The format says what kind of artifact is being made before a format-specific template is applied.

**Content Idea Set**:
Five platform-agnostic visual social ideas that fit the Creator Profile and are grounded in the Social Research Pack.

**Selected Content Idea**:
The idea explicitly chosen by the user for planning. The agent must not choose it on the user's behalf.

**Social Template**:
A reusable visual post structure such as hook-problem-solution, before-process-payoff, hook-steps-payoff, or identity-signal. It improves retention, clarity, and emotional movement without defining the content idea itself.

**Applied Social Template**:
The selected template as adapted to one chosen Content Idea. It states the structural beats, why the template fits, and how each beat maps onto the idea.

**Micro-Journey Video Plan**:
The hook-to-payoff structure for one universal short-form video. It names the hook, setup, escalation, payoff, visual movement, target emotion, and shot logic.

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
The line between dry-run planning and external generation. Drafting plans is allowed; image/video/render generation requires explicit user approval.
