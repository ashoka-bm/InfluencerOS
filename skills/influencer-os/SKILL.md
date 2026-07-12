---
name: influencer-os
description: Use for InfluencerOS content-creation work — the conductor sequencing research-to-queue, idea promotion into projects, production planning, provider-neutral generation plans, and output packaging, with the human gates between them.
dependencies:
  - create-research-findings
  - manage-opportunity-queue
  - approve-concept
  - apply-social-template
  - create-production-plan
  - review-hook-payoff
  - clear-writing-pass
  - human-voice-pass
  - request-generation-approval
  - import-generated-asset
  - review-generated-assets
  - create-output-package
  - register-published-post
  - ingest-analytics
  - create-performance-summary
  - distill-creator-learning
  - distill-production-learning
---

# InfluencerOS Flow

You are the InfluencerOS workflow conductor. Your job is sequencing and provenance.

## Record Constructors And Anticipation (ADR 0042)

- Never hand-author a record type that has a constructor;
  `python3 -m influencer_os scaffold --list` enumerates them. Author the
  seed (authored fields only, per `docs/record-constructors.md`) and let
  the constructor derive, copy, validate, and write.
- When a creator session opens, start
  `python3 -m influencer_os refresh-workspace <ws>` as a background task
  so validation and the board/index/lookup projections are fresh before
  they are needed.
- When a search plan is written, start
  `python3 -m influencer_os research-fetch --plan <search-plan> --run-dir <staged-run-dir>`
  as a background task: every connector-routable planned fetch runs
  concurrently while the session continues (ADR 0022 caps and kill switch
  apply). In-flight runs live under `system/staging/research-runs/`;
  `complete-run` moves them canonical.
- Before presenting a promotion package, `stage promotion` builds the
  full draft bundle while the human reads; present from the draft and
  `commit-stage` on approval (`approve-concept` owns the flow).
- Never anticipate provider-backed generation, publishing, or scheduling;
  never write canonical records ahead of their human gate.

## V1 Scope

InfluencerOS v1 research is platform-scoped across X, Instagram, TikTok, Substack, Medium, Reddit, Facebook, LinkedIn, and YouTube (the ADR 0020 set, extended by ADR 0027). Production workflows may mature platform by platform. It does not create post-production treatments, publish posts, schedule posts, or call provider-backed generation without explicit approval.

## Phase Order

1. **Creator Profile, Content Strategy, and Strategy Scaffold**: identify or create the creator profile and canonical `content-schedule.json`. Audience and niche are inputs, not agent guesses. Calendar slots establish publishing demand: date or window, platform, format, editorial goal or pillar, funnel role, and derivative relationships. Do not preselect specific premises, hooks, or titles merely to make a month look complete. Before research, slots are a `strategy_scaffold`; rebuild and present `boards/content-calendar.html` for human review, then stop at `strategy_ready`.

   The scaffold must cover the full declared planning period. For every
   `content-strategy.json.monthly_mix` row, its slot count must exactly match
   `target_count_per_month`. Record `planning_period` and explicit schedule
   approval metadata in `content-schedule.json`; a partial calendar cannot
   claim `strategy_ready`.
2. **Video Understanding Pack**: when research uses real videos, inspect frames and transcripts and store timestamp-aware observations before final research synthesis.
3. **Research Intelligence, Findings, and Rolling Slot Revision**: broad research may validate platform strategy, cadence, compliance, and derivative mechanics, but it does not research every post in a monthly schedule. For each upcoming anchor slot, run focused `scheduled_needs` research before shortlisting or promotion, and produce multiple evidence-backed candidates when credible alternatives exist. Replace the slot's generic purpose with a specific topic only after human selection. Derivatives may inherit the selected anchor's subject evidence, but still need native format adaptation; high-stakes factual claims require current primary-source verification for the exact unit. Keep later slots open and repeat on a rolling horizon.
4. **Opportunity Queue**: add or update scored Content Opportunities grounded in findings, evidence, schedule state, and creator fit; assign an opportunity to a Campaign Concept when the campaign direction is known.
5. **Concept Approval Gate**: ask the user to approve the full approval package — including commercial-expression ceilings and the exact Project set — before creating production work. Recommend options if useful, but do not silently approve a concept.
   Staging or constructing production work is mechanically blocked until the
   production readiness milestone is ready or human-waived.
6. **Project Creation**: when approved, create one or more Projects from the promoted queue entry. Create Projects only for formats production currently supports; if an approved format is not yet supported, record the approval intent on the queue entry, surface that production support is pending, and do not create an invalid Project.
7. **Applied Social Template or Production Structure**: choose the format-compatible structure that best pulls the viewer through the promoted idea.
8. **Format-Specific Production Plan**: route the promoted idea by target format and platform needs.
9. **Base Generation Plan**: create a provider-neutral generation plan when the selected format needs generated assets.
10. **Generation Approval Gate**: stop before image, video, audio, render, upload, or paid provider calls unless authorized. For creator-setup reference assets only, an approved Visual Continuity Plan authorizes one initial bounded generation pass with no second confirmation (ADR 0043). All production generation, scope changes, and regeneration require explicit exact call/batch approval.

## Phase Checklist Contract

During E2E, guided, or normal-user runs, maintain a phase checklist in the
conversation or under `progress/`. Each checklist update must name:

- current phase;
- required next artifact;
- validation command;
- whether the next step is a human gate, dry-run drafting step, or provider
  boundary.

For the pre-research Phase 1 scaffold review, the required sequence is:

1. validate `content-schedule.json` against `creator-content-schedule`;
2. rebuild `boards/content-calendar.html` from canonical records;
3. present that projection at the human schedule-review checkpoint;
4. write accepted changes to `content-schedule.json`, keep
   `research_basis.status: strategy_scaffold`, and rebuild;
5. run `validate calendar` and `validate workspace` before claiming
   `strategy_ready`.

After broad Phase 3 research, attach completed baseline runs in
`research_basis.research_run_ids` when they materially inform the cadence. This
global basis does not imply that every slot has post-level research. For each
anchor, require a resolvable focused research run on the queue candidates before
promotion; only the selected candidate may lock the slot's topic and title.

Every calendar slot carries `research_state`:

- `unresearched`: generic editorial purpose; no run, selection, or anchor refs.
- `candidates_ready`: focused run ids exist, but no idea is selected.
- `selected`: focused run ids plus the human-selected queue entry id.
- `inherits_anchor`: derivative slot points to one anchor slot and carries no
  duplicate direct research refs.

A focused search plan and its completed run must both name the exact slot in
`schedule_slot_ids`. On human selection, update the slot to `selected`, write
the queue entry id, and lock the topic/title while leaving calendar status open.
Only promotion sets the claimed slot to `filled`.

After production planning, offer or run the advisory creative review phase
before presenting prompts as ready for generation approval. The advisory
creative review does not replace the human generation approval gate.

## Dependencies

Producer skills this conductor routes to are exactly the `dependencies`
frontmatter (kept in agreement with
`docs/os-construction/architecture-map.md` by a drift check). Each
producer's own skill file states what it reads, writes, and validates; the
Phase Owners table below maps every phase to its owner and invocation.

**Halt rule (ADR 0016/0017):** when a phase's owner skill is marked `[PLANNED]` and its folder does not exist under `skills/`, halt at that phase, tell the user which skill is missing and which roadmap slice builds it, and stop. Never improvise the phase from base knowledge and never pretend the skill ran. Each `[PLANNED]` marker is an open build obligation tracked in `docs/os-construction/skill-registry.md` (Missing Future Skills) and the roadmap phase slice lists.

## Phase Owners

| Phase | Owner | Invocation |
| --- | --- | --- |
| 1. Creator Profile, Content Strategy, Schedule | `influencer-os` (inline) | — |
| 2. Video Understanding Pack | `influencer-os` (inline, v1) | — |
| 3. Research Findings | `create-research-findings` | `Skill(skill: "create-research-findings")` |
| 4. Opportunity Queue | `manage-opportunity-queue` | `Skill(skill: "manage-opportunity-queue")` |
| 5. Concept Approval Gate | `approve-concept` + user approval | `Skill(skill: "approve-concept")` |
| 6. Project Creation | `approve-concept` (an approval creates its exact Project set) | `Skill(skill: "approve-concept")` |
| 7. Applied Social Template or Production Structure | `apply-social-template` | `Skill(skill: "apply-social-template")` |
| 8. Format-Specific Production Plan | `create-production-plan` | `Skill(skill: "create-production-plan")` |
| 9. Base Generation Plan | `create-production-plan` (provider-neutral) | `Skill(skill: "create-production-plan")` |
| 9b. Creative review (advisory, after plan drafting) | `review-hook-payoff`; editorial rewrites via `clear-writing-pass` / `human-voice-pass` | `Skill(skill: "review-hook-payoff")`, `Skill(skill: "clear-writing-pass")`, `Skill(skill: "human-voice-pass")` |
| 10. Generation Approval Gate | user (exact-call approval); `request-generation-approval` packages the exact call/batch as a GenerationApprovalRecord | `Skill(skill: "request-generation-approval")` |
| 10b. External media import (no provider call) | `import-generated-asset` | `Skill(skill: "import-generated-asset")` |
| 10c. Quality gate (blocking, before packaging) | `review-generated-assets` | `Skill(skill: "review-generated-assets")` |
| Post-pipeline: Output Package | `create-output-package` | `Skill(skill: "create-output-package")` |
| Post-pipeline: Publication registration | `register-published-post` | `Skill(skill: "register-published-post")` |
| Post-pipeline: Analytics ingestion | `ingest-analytics` | `Skill(skill: "ingest-analytics")` |
| Post-pipeline: Performance summary | `create-performance-summary` | `Skill(skill: "create-performance-summary")` |
| Post-pipeline: Learning distillation | `distill-creator-learning` | `Skill(skill: "distill-creator-learning")` |
| Post-pipeline: Production reflection (on reflection-due warning) | `distill-production-learning` | `Skill(skill: "distill-production-learning")` |

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

## Record Requirements

Producer skills own their record shapes; consult them instead of restating
field lists here:

- Content Opportunity entry rules (fields, intent pair, evidence refs,
  the eight scores): `manage-opportunity-queue`.
- Format-specific plan shapes — the micro-journey spine and every non-video
  and text format: `create-production-plan`.
- Source-evidence provenance discipline (public-web and institutional
  evidence stays `public_web`, separate from target distribution
  platforms): `create-research-findings`, Evidence Quality.

## V1 Social Post Formats

- `format_short_form_video`: vertical hook-to-payoff video.
- `format_carousel`: swipeable visual sequence.
- `format_single_image_post`: one strong still, graphic, or generated image.
- `format_story_sequence`: short vertical visual sequence with an ephemeral/story feel.
- `format_article`: long-form text article or newsletter-style post.
- `format_thread`: ordered short-form text thread.

## Social Template Requirements

Templates should improve retention and clarity without turning every idea into the same post. Use the template after idea selection, because one idea can support multiple structures and formats.

Canonical template IDs and beat sequences live in
`docs/social-template-library.md` (seeded preset records under
`docs/templates/social-templates/`); `apply-social-template` owns selection
and adaptation. Do not restate template IDs here.

## Provider Boundary

Drafting ideas, prompts, plans, shot lists, and generation plans is allowed. Calling a provider is not allowed without explicit approval.

## Rules

*Dated corrections from wrap-up feedback (ADR 0016). Entries are changelog
pointers — the named section owns the rule text. Read before every run;
newest last.*

- 2026-07-07: Added the phase-checklist and advisory-creative-review
  contract — see §Phase Checklist Contract.
- 2026-07-07: Tightened source-evidence provenance (public-web stays
  `public_web`) — rule owned by `create-research-findings`, Evidence
  Quality; pointer in §Record Requirements.
- 2026-07-09: A pre-research schedule is a `strategy_scaffold`, not a
  production calendar. `production_ready` requires a human-reviewed,
  `research_informed` schedule linked to at least one completed research run.
- 2026-07-10: A monthly calendar establishes publishing demand, not a month of
  presumed ideas. Broad strategy research cannot stand in for focused research
  on each anchor slot; research, selection, and topic locking happen on a
  rolling horizon, with derivatives inheriting only relevant anchor evidence.
- 2026-07-09: Object reference prompts are atomic — one distinct prop per
  Reference Asset, prompt, provider request, and reference image; rule owned by
  `create-reference-library`, Atomic Object Reference Rule.
- 2026-07-10: Constructor-built records and anticipation points (ADR 0042)
  — see §Record Constructors And Anticipation. Seeds replace hand-authored
  records wherever `scaffold --list` names the type; deterministic local
  work starts at its earliest knowledge point.

## Self-Update

When the user flags an issue with this skill mid-run or at wrap-up:

- Scope-specific correction (one creator, or the OS persona) → record it in the applicable `SKILL.local.md`: the creator's runtime copy, or `skills/influencer-os/SKILL.local.md` for the OS persona.
- System-wide correction → add a dated entry to `## Rules` above and fix the offending step in this file.
- Log the change via `python3 -m influencer_os log-learning context/learnings.md influencer-os "<what changed>"` so it has a record (run from the InfluencerOS repo root; `context/learnings.md` is the OS ledger, never a Creator Workspace file).
- Promote a local rule into this base file only when repeated feedback shows it applies system-wide (ADR 0014).
