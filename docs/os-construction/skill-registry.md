# InfluencerOS Skill Registry

This registry lists InfluencerOS skills, trigger conditions, writes, and local override policy.

Core skill source files live under repo `skills/`. Creator Workspaces receive copied runtime skill folders under `.claude/skills/`. Creator-specific overrides live beside the copied runtime skill as `SKILL.local.md`. System persona overrides may live beside the core source skill as `SKILL.local.md`.

## Registration Rules

- Skill folder name should be kebab-case.
- `SKILL.md` is the core rule set.
- `SKILL.local.md` is scope-specific and must not replace the core file.
- Every new skill needs a row in this registry and context coverage in `docs/os-construction/context-matrix.md`.
- New behavior-changing skills need tests, examples, or a review checklist.
- Skills that call providers must name the approval gate.

## Context Coverage Rule

Context coverage can be explicit or workflow-based:

- explicit coverage: the context matrix has a row for the individual skill,
- workflow coverage: the registry row names a workflow that has a context-matrix row,
- deferred coverage: the registry marks the skill as future or deferred and says when coverage will be added.

Setup subskills are covered by the `Creator setup` workflow row until they need separate load rules.

## Core Workflow Skills

| Skill | Triggers on | Reads | Writes | Override support |
| --- | --- | --- | --- | --- |
| `influencer-os` | content creation flow, research-to-queue, idea promotion to project | Creator Profile, research, project records, context matrix | planning records, generation plans, output records | yes |
| `create-influencer` | create creator, setup creator, new influencer | intake, references, templates | Creator Workspace files, including the one ADR 0045 Avatar Image approval/dispatch and fresh exact-user avatar regeneration route | yes |
| `create-research-findings` | research run requests, refresh findings, trend/watchlist/hashtag checks | Creator Profile, content schedule, findings, research intelligence | search-plan seed; staged in-flight runs under `system/staging/research-runs/` via `scaffold search-plan`/`research-fetch --plan`, moved to `research/runs/` by `complete-run` (ADR 0042); `research/findings.md`, `research/stable-findings/`, `research/intelligence/` | yes |
| `manage-opportunity-queue` | add/update/score content opportunities, queue refresh, staleness review | findings, evidence refs, Creator Profile, content schedule | `research/content-opportunity-queue/` via `scaffold content-opportunity`, queue-level `system/project-warnings.jsonl`, board/index via CLI | yes |
| `approve-concept` | approve concept into production, set commercial-expression ceilings, create the exact project set | campaign concept, campaign, findings, evidence refs, Creator Profile, content schedule | approval bundle seed; `system/staging/` drafts via `stage approval`, then `campaigns/<campaign-id>/approvals/`, `projects/<project-slug>/`, concept/slot flips, and board/index via `commit-stage` (ADR 0031/0042) | yes |
| `manage-idea-queue` | deprecated legacy alias; halt and redirect | none | none | yes |
| `promote-idea` | deprecated legacy alias; halt and redirect | none | none | yes |
| `apply-social-template` | apply template, choose production structure, adapt promoted idea beats | Project, locked promotion, queue entry, evidence brief, Creator Profile, template library | `projects/<project-slug>/plan/applied-template.json` | yes |
| `create-production-plan` | create production plan, route project by format, draft generation plan | Project, applied template, locked promotion, evidence brief, Creator Profile, references, research evidence | `projects/<project-slug>/plan/production-plan.json`; `plan/generation-plan.json` for short-form video | yes |
| `create-output-package` | register output package, package upload-ready assets, mark project packaged | Project, applied template, production plan, generation plan when present, locked promotion, Reference Library | `projects/<project-slug>/output-package/`, Project status via `register-output-package` | yes |
| `register-published-post` | record a manual publication, register published post, mark project published | Project, registered Output Package, operator publication facts | `projects/<project-slug>/published/published-post-records/`, Project status via `register-published-post` | yes |
| `ingest-analytics` | add analytics snapshot, import analytics CSV, record post performance | Project, registered Output Package, live Published Post Records, operator platform exports | `projects/<project-slug>/analytics/` via `add-analytics-snapshot`/`import-analytics-csv` | yes |
| `create-performance-summary` | author performance summary, map results to attribution stages, post postmortem | Project, Creative Performance Map, Published Post Records, AnalyticsSnapshots, production plan | `projects/<project-slug>/performance-summary.json` (agent-authored; `validate project` is the enforcement seam) | yes |
| `distill-creator-learning` | distill creator lessons, update creator memory from performance, consolidate lessons across posts | PerformanceSummary records and their evidence chain, `memory/learnings.md`, `context/MEMORY.md` | evidence-linked lessons in `memory/learnings.md` via `log-learning --evidence --strength`; optional promoted fact in `context/MEMORY.md` via `memory-write` (2,500-byte cap) | yes |
| `distill-production-learning` | reflection due, bracket friction events, distill production learning, close improvement claims | `check-reflection` output, unprocessed friction events, OS + creator rubrics, target `SKILL.md` files, open claims via `check-claims` | human-approved skill updates + `context/learnings.md` via `log-learning`; claims via `record-improvement-claim`; criteria via `mint-criterion`; reflection run under `system/reflection-runs/` | yes |
| `review-hook-payoff` | review hook and payoff, creative review of a drafted plan, advisory plan review | review packet: drafted plan, applied template, locked promotion intent fields (never the authoring conversation) | `projects/<project-slug>/reviews/<review_record_id>.json` (advisory ReviewRecord; never blocks) | yes |
| `review-creator-setup` | setup review, review creator foundation, review avatar and visual continuity | explicit foundation, Avatar Image/reference entry, and draft Visual Continuity Plan packet (never the authoring conversation) | `reviews/<review_record_id>.json` (advisory workspace-level ReviewRecord; never blocks) | yes |
| `review-strategy` | strategy review, review creator strategy, advisory strategy review | re-approved research-informed strategy and schedule, broad Research Findings/Evidence, Creator Profile, and on repeats the prior Review Record plus unresolved Demand set (never the authoring conversation) | `reviews/<review_record_id>.json` (advisory workspace-level ReviewRecord with capped Demand-loop lineage; never blocks) | yes |
| `clear-writing-pass` | clear writing pass, declutter draft text, tighten copy | drafted article/thread/caption/plan text | none (returns rewritten text + change trace in conversation; no record) | yes |
| `human-voice-pass` | human voice pass, strip AI tells, make it sound like the creator | drafted text, Creator Profile voice constraints, voice samples, brand context | none (returns rewritten text + change trace in conversation; no record) | yes |
| `request-generation-approval` | request exact production approval, or derive the one-pass creator-setup reference authorization from an approved Visual Continuity Plan | Base Video Generation Plan or approved setup reference package, provider registry via `list-providers`, provider boundary | `projects/<project-slug>/generation/approval-records/` (or `references/approval-records/`) via `record-generation-approval` | yes |
| `import-generated-asset` | import generated media, bring in an external export, register user-provided media | operator provenance answers (source, tool, license), project manifest or Reference Library | `generation/assets/` + `generation/asset-manifest.json` row (or reference asset path + source block) via `import-generated-asset` | yes |
| `review-generated-assets` | quality review generated assets, run the packaging quality gate, check identity/continuity/conformance/boundaries | asset manifest + artifact files, production and generation plans, Reference Library approved assets, Creator Profile boundaries | `projects/<project-slug>/generation/quality-reviews/<quality_review_id>.json` (BLOCKING gate for packaged generation media) | yes |

## Creator Setup Subskills

| Skill | Triggers on | Writes |
| --- | --- | --- |
| `create-creator-profile` | draft creator profile | `creator-profile.json` |
| `create-identity` | draft identity | `brand_context/identity.md` |
| `create-soul` | draft creator soul | `brand_context/soul.md` |
| `create-personal-brand` | draft personal brand | `brand_context/personal-brand.md` |
| `personal-brand-board` | create the required exact visual identity tokens and profile-avatar system for every creator after reference planning | `references/brand/personal-brand-board.json` plus shared-template HTML projection; avatar and any production spaces/props link to typed Reference Library assets |
| `create-voice-samples` | extract or curate voice samples | `brand_context/voice-samples.md` |
| `create-reference-library` | evaluate and present visual continuity candidates, then plan approved visual/audio references | `references/visual-continuity-plan.json`, `references/reference-library.json` |
| `create-lead-magnet` | create an `asset_type: lead_magnet` PDF referenced by accepted strategy; other conversion-asset types halt as unsupported | `conversion-assets/<slug>-lead-magnet.{json,md,pdf}`, `references/brand/<slug>-theme.css`; temporary render bundle under root `.tmp/` |
| `elevenlabs-voice-design` | stage ElevenLabs voice design prompt | `references/voice/<asset-slug>.prompt.md`; resulting approved audio is registered separately and links back through `prompt_path` |
| `create-runtime-context` | create tiny runtime context | `context/SOUL.md`, `context/USER.md`, `context/MEMORY.md` |

## System Skills

| Skill | Triggers on | Reads | Writes | Override support |
| --- | --- | --- | --- | --- |
| `wrap-up` | session end signals, wrap-up requests, sessions that produced deliverables | git status, `context/learnings.md`, this registry, context matrix | `context/learnings.md`, `docs/os-construction/process-learnings.md`, skill files, `context/MEMORY.md` | yes |
| `memory-write` | remember this, note that, save to memory, update memory, forget about | target `MEMORY.md` | target `MEMORY.md` (2,500-byte cap via `python3 -m influencer_os memory-write`) | yes |

## External Tool Integrations

These are not repo-owned skills and must not be added to conductor
`dependencies` frontmatter.

| Tool | Used by workflow | Purpose | Boundary |
| --- | --- | --- | --- |
| `watch` (`bradautomates/claude-video`) | Social research / Video Understanding Pack | Inspect public or user-provided local videos, sample frames, obtain native captions, and provide timestamped evidence for `VideoUnderstandingPack` records | external optional tool; no vendoring; Whisper/API fallback, first-run dependency installs, and batches require explicit approval |

## Missing Future Skills

| Skill | Purpose | Timing |
| --- | --- | --- |

None — every previously planned skill is built (`distill-creator-learning` closed the last Phase 0C WS 10 obligation in Phase 2 slice 4). When a future skill is planned, add its row here; coverage is deferred per the Context Coverage Rule until it is built in its slice, and the conductor call graph marks it `[PLANNED]` with a halt rule. Per ADR 0017 the machine-actionable source for skill dependencies is each skill's `dependencies` frontmatter (enforced against `docs/os-construction/architecture-map.md` by the call-graph drift check), not a duplicated registry column; skill categories are expressed by this registry's section tables (core workflow, creator setup, system, future).
