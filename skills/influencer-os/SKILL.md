---
name: influencer-os
description: Use for InfluencerOS work: choosing a creator profile, researching current platform-scoped content opportunities, updating research findings and the idea queue, promoting approved ideas into projects, creating production plans, creating provider-neutral generation plans, and registering output packages.
dependencies:
  - create-research-findings
  - manage-idea-queue
  - promote-idea
  - apply-social-template
  - create-production-plan
  - review-hook-payoff
  - clear-writing-pass
  - human-voice-pass
  - request-generation-approval
  - create-output-package
  - register-published-post
  - ingest-analytics
  - create-performance-summary
  - distill-creator-learning
---

# InfluencerOS Flow

You are the InfluencerOS workflow conductor. Your job is sequencing and provenance.

## V1 Scope

InfluencerOS v1 research is platform-scoped across X, Instagram, TikTok, Substack, Medium, Reddit, Facebook, and LinkedIn. Production workflows may mature platform by platform. It does not create post-production treatments, publish posts, schedule posts, or call provider-backed generation without explicit approval.

## Phase Order

1. **Creator Profile, Content Strategy, and Schedule**: identify or create the creator profile and creator content schedule. Audience and niche are inputs, not agent guesses. Use accepted content strategy and schedule state to scope research and medium-specific blockers.
2. **Video Understanding Pack**: when research uses real videos, inspect frames and transcripts and store timestamp-aware observations before final research synthesis.
3. **Research Intelligence and Findings**: create a run-local search plan before browsing, capture dated public evidence, record source-yield outcomes after browsing, then synthesize current platform-scoped patterns relevant to the creator. Date and cite the research, but update the rolling findings only when there is a material finding or source-intelligence learning.
4. **Idea Queue**: add or update scored idea queue entries grounded in findings, evidence, schedule state, and creator fit.
5. **Idea Promotion Gate**: ask the user to approve the full promotion package before creating production work. Recommend options if useful, but do not silently promote an idea.
6. **Project Creation**: when approved, create one or more Projects from the promoted queue entry. Create Projects only for formats production currently supports; if an approved format is not yet supported, record the approval intent on the queue entry, surface that production support is pending, and do not create an invalid Project.
7. **Applied Social Template or Production Structure**: choose the format-compatible structure that best pulls the viewer through the promoted idea.
8. **Format-Specific Production Plan**: route the promoted idea by target format and platform needs.
9. **Base Generation Plan**: create a provider-neutral generation plan when the selected format needs generated assets.
10. **Generation Approval Gate**: stop before image, video, audio, render, upload, or paid provider calls unless the user explicitly approves the exact call or batch.

## Dependencies

Producer skills this conductor routes to (mirrors the `dependencies` frontmatter; kept in agreement with `docs/os-construction/architecture-map.md` by a drift check):

| Skill | Produces | Status |
| --- | --- | --- |
| `create-research-findings` | Research Findings backed by dated evidence | [BUILT — Phase 1 slice 4] |
| `manage-idea-queue` | Scored Idea Queue entries | [BUILT — Phase 1 slice 4] |
| `promote-idea` | Human-approved Idea Promotion + Projects | [BUILT — Phase 1 slice 5] |
| `apply-social-template` | Applied Social Template | [BUILT — Phase 1 slice 6] |
| `create-production-plan` | Format-specific production plan + Base Video Generation Plan | [BUILT — Phase 1 slice 6] |
| `review-hook-payoff` | Advisory Hook/Payoff ReviewRecord (never blocks) | [BUILT — Creative Direction slice 4] |
| `clear-writing-pass` | Clarity rewrite + change trace (no record) | [BUILT — Creative Direction slice 4] |
| `human-voice-pass` | Creator-voice rewrite + change trace (no record) | [BUILT — Creative Direction slice 4] |
| `request-generation-approval` | GenerationApprovalRecord packaging the exact approved call/batch (gate stays human) | [BUILT — Phase 3 slice 2] |
| `create-output-package` | Output Package + provenance | [BUILT — Phase 1 slice 7] |
| `register-published-post` | PublishedPostRecord + Project published status | [BUILT — Phase 2 slice 1] |
| `ingest-analytics` | AnalyticsSnapshots from manual/CSV entry | [BUILT — Phase 2 slice 2] |
| `create-performance-summary` | PerformanceSummary from analytics evidence | [BUILT — Phase 2 slice 3] |
| `distill-creator-learning` | Creator Memory lessons from performance evidence | [BUILT — Phase 2 slice 4] |

**Halt rule (ADR 0016/0017):** when a phase's owner skill is marked `[PLANNED]` and its folder does not exist under `skills/`, halt at that phase, tell the user which skill is missing and which roadmap slice builds it, and stop. Never improvise the phase from base knowledge and never pretend the skill ran. Each `[PLANNED]` marker is an open build obligation tracked in `docs/os-construction/skill-registry.md` (Missing Future Skills) and the roadmap phase slice lists.

## Phase Owners

| Phase | Owner | Invocation | Status |
| --- | --- | --- | --- |
| 1. Creator Profile, Content Strategy, Schedule | `influencer-os` (inline) | — | [BUILT] |
| 2. Video Understanding Pack | `influencer-os` (inline, v1) | — | [BUILT] |
| 3. Research Findings | `create-research-findings` | `Skill(skill: "create-research-findings")` | [BUILT] |
| 4. Idea Queue | `manage-idea-queue` | `Skill(skill: "manage-idea-queue")` | [BUILT] |
| 5. Idea Promotion Gate | `promote-idea` + user approval | `Skill(skill: "promote-idea")` | [BUILT] |
| 6. Project Creation | `promote-idea` (a promotion creates Projects) | `Skill(skill: "promote-idea")` | [BUILT] |
| 7. Applied Social Template or Production Structure | `apply-social-template` | `Skill(skill: "apply-social-template")` | [BUILT] |
| 8. Format-Specific Production Plan | `create-production-plan` | `Skill(skill: "create-production-plan")` | [BUILT] |
| 9. Base Generation Plan | `create-production-plan` (provider-neutral) | `Skill(skill: "create-production-plan")` | [BUILT] |
| 9b. Creative review (advisory, after plan drafting) | `review-hook-payoff`; editorial rewrites via `clear-writing-pass` / `human-voice-pass` | `Skill(skill: "review-hook-payoff")`, `Skill(skill: "clear-writing-pass")`, `Skill(skill: "human-voice-pass")` | [BUILT — Creative Direction slice 4] |
| 10. Generation Approval Gate | user (exact-call approval); `request-generation-approval` packages the exact call/batch as a GenerationApprovalRecord | `Skill(skill: "request-generation-approval")` | [BUILT gate + record — Phase 3 slice 2] |
| Post-pipeline: Output Package | `create-output-package` | `Skill(skill: "create-output-package")` | [BUILT] |
| Post-pipeline: Publication registration | `register-published-post` | `Skill(skill: "register-published-post")` | [BUILT — Phase 2 slice 1] |
| Post-pipeline: Analytics ingestion | `ingest-analytics` | `Skill(skill: "ingest-analytics")` | [BUILT — Phase 2 slice 2] |
| Post-pipeline: Performance summary | `create-performance-summary` | `Skill(skill: "create-performance-summary")` | [BUILT — Phase 2 slice 3] |
| Post-pipeline: Learning distillation | `distill-creator-learning` | `Skill(skill: "distill-creator-learning")` | [BUILT — Phase 2 slice 4] |

## Video Understanding Requirements

When analyzing videos for research, store:

- source URL or local path,
- analysis method,
- transcript source,
- opening hook,
- first-frame pattern,
- visual structure,
- spoken or text framing,
- template signals,
- replicable moves,
- avoid notes.

Preferred acquisition tool: use an installed `watch` skill/plugin from
`bradautomates/claude-video`, or a local equivalent, when available. The tool is
not a repo-owned producer dependency and must not be added to this skill's
`dependencies` frontmatter.

Tool boundary:

- Use `/watch` or the installed `watch` skill only to inspect public URLs or
  user-provided local files.
- Prefer native captions and sampled frames. Run with Whisper disabled (pass
  `--no-whisper`; the upstream default falls back to Whisper on caption-less
  videos) unless the user explicitly approves the exact transcription fallback
  or has already configured it for this research run.
- Ask before installing global tooling, running first-run setup that installs
  dependencies, or processing batches of videos.
- Use ignored working storage such as
  `.tmp/watch/<creator-slug>/<research-run-id>/<source-id>/` via `--out-dir`
  when the tool supports it.
- Summarize the observed evidence into a `VideoUnderstandingPack`; do not store
  downloaded videos, frame folders, audio clips, or full transcripts as
  canonical records by default.
- Delete disposable working files after the pack is created unless the user is
  actively asking follow-up questions about the same video.

## Idea Queue Requirements

Each queue idea must include:

- hook,
- premise,
- intended payoff,
- source platform and platform content type when derived from a source pattern,
- recommended platform or platform variants,
- recommended format or format variants,
- audience reason,
- creator fit,
- intended emotion and core message (ADR 0024),
- trend evidence,
- evidence reference IDs from Research Findings, Research Evidence, Metric Snapshots, and Video Understanding Packs when used,
- novelty angle,
- production complexity,
- why it can travel or adapt across platforms when applicable,
- recommended template or structure IDs when relevant,
- scores for evidence strength, viral potential, audience nurture value, creator fit, schedule fit, production readiness, urgency, and measurement clarity.

## V1 Social Post Formats

- `format_short_form_video`: vertical hook-to-payoff video.
- `format_carousel`: swipeable visual sequence.
- `format_single_image_post`: one strong still, graphic, or generated image.
- `format_story_sequence`: short vertical visual sequence with an ephemeral/story feel.
- `format_article`: long-form text article or newsletter-style post.
- `format_thread`: ordered short-form text thread.

## Social Template Requirements

Templates should improve retention and clarity without turning every idea into the same post. Use the template after idea selection, because one idea can support multiple structures and formats.

Useful starter templates:

- `hook_problem_solution`,
- `before_process_payoff`,
- `constraint_countdown_result`,
- `myth_truth_demo`,
- `mistake_fix_result`,
- `three_steps_payoff`,
- `expectation_reality`,
- `challenge_attempt_result`,
- `reveal_explain_apply`.

## Micro-Journey Requirements

The plan is spine-shaped (ADR 0024) and should include:

- hook,
- one retain beat holding setup and escalation/demonstration,
- payoff,
- CTA or loop behavior (`cta_or_loop`),
- intended emotion (matching the locked promotion's `intended_emotion`),
- shot outline,
- continuity requirements,
- base-video constraints.

## Non-Video Production Plan Requirements

Carousel plans should define slide-level visual beats, a first-slide hook, creator continuity, and generation notes.

Single image post plans should define the central visual idea, composition, avatar or scene requirements, text overlay policy, and generation prompt.

Story sequence plans should define frame-level moments, sequence arc, lightweight text or sticker notes, creator continuity, and generation notes.

Article plans should define the title, deck, thesis, section outline, evidence
to use, voice/style constraints, CTA, and review notes.

Thread plans should define the opening post, throughline, ordered posts,
evidence to use, voice/style constraints, CTA, and review notes.

## Provider Boundary

Drafting ideas, prompts, plans, shot lists, and generation plans is allowed. Calling a provider is not allowed without explicit approval.

## Rules

*Dated corrections from wrap-up feedback (ADR 0016). Read before every run; newest last.*

- 2026-07-03: Baseline established; no corrections recorded yet.

## Self-Update

When the user flags an issue with this skill mid-run or at wrap-up:

- Scope-specific correction (one creator, or the OS persona) → record it in the applicable `SKILL.local.md`: the creator's runtime copy, or `skills/influencer-os/SKILL.local.md` for the OS persona.
- System-wide correction → add a dated entry to `## Rules` above and fix the offending step in this file.
- Log the change via `python3 -m influencer_os log-learning context/learnings.md influencer-os "<what changed>"` so it has a record.
- Promote a local rule into this base file only when repeated feedback shows it applies system-wide (ADR 0014).
