# InfluencerOS Architecture Map

Last updated: 2026-07-05

This is the whole-system blueprint at file granularity: where every file lives, what it owns, and which function or skill calls which other function or skill. It records **structure and call flow, not file internals**. Internals (schema fields, skill prose, function bodies) are defined in the files themselves and built in dedicated TDD passes.

It is the source of truth for the creation-flow call graph. `repository-map.md` records file ownership and the record data-flow; this file records the skill and CLI call graphs.

## Status Legend

- **[BUILT]** — exists on disk and works today.
- **[PLANNED]** — approved and placed here; internals built in a later TDD pass.
- **[DEFERRED]** — intentionally not built in v1 (roadmap Deferred / PRD Out of Scope).
- **[GATED]** — a zone that exists structurally but stays inert until its subsystem is un-deferred.

## System Layers

```text
Root adapters              AGENTS.md (canonical) + CLAUDE.md, SOUL.md (thin importers)   [BUILT; restructure per ADR 0019]
First-party OS persona     context/  (SOUL/USER/MEMORY/learnings)                        [BUILT]
First-party OS brand       brand_context/  (positioning/voice/icp/samples/assets)        [BUILT; stubs]
Durable planning docs      docs/os-construction/ + docs/adr/                             [BUILT]
Workflow contracts         schemas/ + docs/pipeline-contract.md                          [BUILT]
Skills (source)            skills/<skill-name>/SKILL.md (+ references/, SKILL.local.md)  [BUILT + PLANNED]
Runtime CLI                influencer_os/ (cli + helpers + validation)                   [BUILT]
Research connectors        influencer_os/connectors/ (env-gated acquisition tier)        [BUILT — ADR 0022; dormant until key]
Creator Workspaces         workspace-library/creators/<slug>/ (ignored, runnable root)   [BUILT scaffold]
Self-improvement loop      skills/wrap-up, skills/memory-write + memory CLI              [BUILT — ADR 0016]
Propagation                CLI: init-creator, sync-creator-runtime, update-creators      [BUILT — ADR 0018]
Drift checks               tests/test_drift_checks.py                                    [BUILT; runtime-sync check lands in WS11]
Deferred subsystems        hooks, cron, Command Centre, .claude/agents, anywhere-access  [DEFERRED / GATED]
```

## File Map

### Root adapters (always loaded)

| Path | Role | Status |
| --- | --- | --- |
| `AGENTS.md` | Canonical operating contract: rules, source-of-truth list, durable read order, product invariant. All runtimes read it. | [BUILT] |
| `CLAUDE.md` | Thin Claude wrapper: imports `AGENTS.md`; Claude-specific runtime notes only. | [BUILT; restructure per ADR 0019] |
| `SOUL.md` | Thin OpenClaw/Hermes wrapper: imports `AGENTS.md`; adapter, not identity. | [BUILT; restructure per ADR 0019] |
| `README.md` | Human entry point. | [BUILT] |
| `CONTEXT.md` | Product vocabulary source of truth. | [BUILT] |
| `ARCHITECTURE.md` | Durable architecture direction. | [BUILT] |

### First-party OS persona context

| Path | Role | Status |
| --- | --- | --- |
| `context/SOUL.md` | Sole OS identity document (persona). | [BUILT] |
| `context/USER.md` | OS operator profile. | [BUILT] |
| `context/MEMORY.md` | OS working memory, byte-capped; written by `memory-write`. | [BUILT] |
| `context/learnings.md` | Append-only per-skill learnings; written by `wrap-up`. | [BUILT; empty until `wrap-up` runs] |
| `brand_context/*.md` | OS positioning, voice, icp, samples, assets. | [BUILT; stubs] |

### Durable planning docs (`docs/os-construction/`)

| Path | Role | Status |
| --- | --- | --- |
| `prd.md` · `roadmap.md` · `short-term-plan.md` · `progress.md` | Product plan and status. | [BUILT] |
| `repository-map.md` | File ownership + record data-flow. | [BUILT] |
| `architecture-map.md` | This file: file map + skill/CLI call graphs. | [BUILT] |
| `agentic-os-alignment.md` · `agentic-os-copy-plan.md` · `agentic-os-parity-plan.md` | Parity governance. | [BUILT] |
| `divergence-test.md` · `visual-architecture-maps.md` | Divergence gate + map standard. | [BUILT] |
| `context-matrix.md` · `skill-registry.md` | Context load rules + skill registry. | [BUILT] |
| `process-learnings.md` | Repo-level process learnings; written by `wrap-up`. | [BUILT; empty until `wrap-up` runs] |
| `adversarial-review.md` | Ranked divergence ledger from the parity review. | [BUILT] |
| `maps/` | Excalidraw map records. | [BUILT] |
| `docs/adr/0001–0024` | Architectural decisions (0020 research module; 0021 research intelligence; 0022 research-acquisition connectors; 0023 generation provider boundary; 0024 creative content model). | [BUILT] |

### Workflow contracts

| Path | Role | Status |
| --- | --- | --- |
| `schemas/*.schema.json` | JSON Schema contract per durable record (incl. `visual-continuity-plan` and `research-fetch-result`). | [BUILT] |
| `examples/*.example.json` | Valid example per schema; CLI/test fixtures. | [BUILT] |
| `docs/pipeline-contract.md` | Typed step-to-step pipeline contract. | [BUILT] |
| `docs/provider-boundary.md` | Provider approval boundary (generation exact-approval; research-acquisition standing approval per ADR 0022). | [BUILT] |
| `docs/research-adapter-registry.md` | Research acquisition adapter/connector permission registry (ADR 0021/0022). | [BUILT] |
| `docs/creator-workspace-structure.md` | Workspace layout + local-state policy. | [BUILT] |

### Skills (`skills/<skill-name>/`)

Source layout per ADR 0017: repo-central, kebab-case, no category prefixes, optional per-skill `references/`, `SKILL.local.md` overrides, machine-actionable `dependencies` frontmatter. The ADR-0017 conventions are **[BUILT]** as of workstreams 9–10: both conductors and both system skills declare `dependencies` frontmatter, both conductors carry `## Rules`/`## Self-Update`, and a worked `skills/influencer-os/SKILL.local.md` exists. Producer skill status is per-row below: the research, queue, promotion, template, production-plan, and output-package producers landed in Phase 1 slices 4–7; the publication-registration and analytics-ingestion producers landed in Phase 2 slices 1–2, and the remaining [PLANNED] learning producers belong to Phase 2 slices 3–4.

| Skill | Category | Role | Status |
| --- | --- | --- | --- |
| `influencer-os` | conductor | Content-creation conductor (10 phases; `dependencies` + `## Phase Owners` declared). | [BUILT] |
| `create-influencer` | conductor | Creator-setup conductor (13 phases). | [BUILT] |
| `create-identity` | setup | `brand_context/identity.md`. | [BUILT] |
| `create-soul` | setup | `brand_context/soul.md`. | [BUILT] |
| `create-personal-brand` | setup | `brand_context/personal-brand.md`. | [BUILT] |
| `personal-brand-board` | setup | Creator-specific token spec plus reusable HTML mini-style-guide projection. | [BUILT] |
| `create-voice-samples` | setup | `brand_context/voice-samples.md`. | [BUILT] |
| `create-creator-profile` | setup | `creator-profile.json`. | [BUILT] |
| `create-runtime-context` | setup | `context/SOUL.md`,`USER.md`,`MEMORY.md`. | [BUILT] |
| `create-reference-library` | setup | User-reviewed `references/visual-continuity-plan.json`, selected `references/reference-library.json` assets + prompts. | [BUILT] |
| `elevenlabs-voice-design` | setup | Human-in-the-loop ElevenLabs Voice Design prompt files under `references/voice/`; no provider call. | [BUILT] |
| `create-research-findings` | planning | Concise Research Findings backed by dated evidence. | [BUILT — Phase 1 slice 4] |
| `manage-idea-queue` | planning | Scored Idea Queue entries. | [BUILT — Phase 1 slice 4] |
| `promote-idea` | planning | Human-approved Idea Promotion and project creation. | [BUILT — Phase 1 slice 5] |
| `apply-social-template` | planning | Applied Social Template or production structure for the promoted idea. | [BUILT — Phase 1 slice 6] |
| `create-production-plan` | planning | Routes promoted idea to a format-specific plan. | [BUILT — Phase 1 slice 6] |
| `create-output-package` | planning | Output Package + provenance. | [BUILT — Phase 1 slice 7] |
| `register-published-post` | learning | PublishedPostRecord + Project published status. | [BUILT — Phase 2 slice 1] |
| `ingest-analytics` | learning | AnalyticsSnapshots from manual/CSV entry. | [BUILT — Phase 2 slice 2] |
| `create-performance-summary` | learning | PerformanceSummary from analytics evidence. | [BUILT — Phase 2 slice 3] |
| `distill-creator-learning` | learning | Performance evidence → Creator Memory. | [BUILT — Phase 2 slice 4] |
| `distill-production-learning` | improvement | Friction events → approved skill updates with falsifiable claims (ADR 0025). | [BUILT — Phase 4 slice 3] |
| `wrap-up` | system | Session-end learnings, skill self-fix, registry reconcile, memory promote. | [BUILT — ADR 0016] |
| `memory-write` | system | Bounded, deduped `context/MEMORY.md` writes (2,500-byte cap via CLI). | [BUILT — ADR 0016] |

### Runtime CLI (`influencer_os/`)

| Path | Role | Status |
| --- | --- | --- |
| `cli.py` | Command surface; routes to helpers (`register-output-package`, `list-connectors`, `research-fetch` included), holds no product rules. | [BUILT] |
| `validation.py` | Fail-closed schema subset (`$ref`/`oneOf`/`anyOf`/`allOf`); disk-derived example coverage. | [BUILT — WS13] |
| `creator_workspaces.py` | `init-creator`, `import-intake`/`set-intake-status` (source intake provenance), `sync-creator-runtime`, `update-creators` (backup-protected), readiness milestones. | [BUILT — WS11; intake commands Phase 1 slice 1] |
| `projects.py` | Project scaffolding + validation + promotion-anchored provenance resolution. | [BUILT — WS12 + Phase 1 slice 3] |
| `research.py` | Search-plan, JSONL, source-yield, and frontmatter validation; `validate research`/`validate queue` (incl. run-scoped consistency), promotion gate. | [BUILT — Phase 1 slice 3; run-scoped checks slice 4 batch A; intelligence hardening 2026-07-04] |
| `recall_index.py` | Rebuildable SQLite recall-index projection (ADR 0010); `rebuild-index` per-creator rebuilds covering research, project, board, and Phase 2 learning records (schema-validated and manifest-anchored via the shared `projects.py` seam that `validate workspace` also runs at rest; `analytics/raw/` never scanned); never a validation dependency. | [BUILT — Phase 1 slice 4 batch B; Phase 2 slice 5 extension] |
| `semantic_lookup.py` | FTS5 semantic lookup projection (ADR 0011 keyword leg): `rebuild-lookup` chunks the creator-scoped allowlist (brand context, findings, stable findings, learnings, index-allowed performance summaries; `analytics/` unreachable by construction and symlinked lookup sources rejected) with heading/line provenance, authority weights, sha256 change detection; `query-lookup` reranks creator-local BM25 x authority x recency behind a hard creator-scope no-leak boundary, read-only, queries never persisted; never a validation dependency. | [BUILT — Phase 2 slice 6] |
| `boards.py` | Content Board projection: `rebuild-board` (cards derived, columns/manual order preserved) + `validate board` agreement check. | [BUILT — Phase 1 slice 4 batch C] |
| `prune.py` | Retention pruning: dry-run default, `--apply` deletes unreferenced out-of-window evidence + snapshots, pruned ids recorded on the run manifest. | [BUILT — Phase 1 slice 4 batch D] |
| `memory.py` | Bounded `memory-write` + `log-learning` writers; evidence-linked creator lessons with at-rest validation. | [BUILT — ADR 0016; creator lessons Phase 2 slice 4] |
| `runs.py` | Dry-run init + run records. | [BUILT] |
| `generation.py` | Generation OS writers + at-rest checks (ADR 0023): approval-record writer with shared record↔project binding, asset import (project + reference routes), manifest ledger appends and bidirectional reconciliation, content-bound quality-review coverage. | [BUILT — Phase 3 slices 2-5] |
| `providers/` | Generation provider boundary (ADR 0023): `registry.py` (structural `exact_approval` rows, import fails closed), `dispatch.py` (the only adapter entry point; approval-record-gated, O_EXCL-locked two-phase consumption, kill-switch hard stop, mock adapter). Powers `list-providers`. | [BUILT — Phase 3 slice 1 + review hardening] |
| `connectors/` | Env-gated research-acquisition tier (ADR 0022): `env.py` (key detection, kill switch, call cap), `http.py` (stdlib client), `registry.py`/`fetch.py` (availability + dispatch), `models.py`/`parse.py` (canonical mapping to `ResearchEvidence`/`MetricSnapshot`), and connectors `openai_reddit.py` (+`reddit_enrich.py`), `xai_x.py`, `firecrawl_web.py`, `linkedin_apify.py`. Powers `list-connectors` + `research-fetch`; output validated by `research-fetch-result.schema.json`. | [BUILT — ADR 0022; dormant until provider key] |

### Tests (`tests/`) — parity + contract

| Path | Role | Status |
| --- | --- | --- |
| `test_schema_validation.py` | All examples validate; coverage derived from disk; fail-closed subset tests. | [BUILT — WS13] |
| `test_cli.py` | CLI behavior incl. provenance resolution and readiness milestones. | [BUILT] |
| `test_recall_index.py` | Index resolution per record kind (incl. Phase 2 learning records), idempotent per-creator rebuilds, fail-closed ambiguity, raw-analytics exclusion, delete-and-rebuild equivalence, default ADR 0010 path. | [BUILT — Phase 1 slice 4 batch B; Phase 2 slice 5 extension] |
| `test_boards.py` | Board derivation (cards, badges, parent/child), metadata preservation, agreement validation, CLI. | [BUILT — Phase 1 slice 4 batch C] |
| `test_prune.py` | Retention rules (dry-run, apply, protection, idempotence) + pruned-ids reconciliation. | [BUILT — Phase 1 slice 4 batch D] |
| `test_memory.py` | Bounded memory/learnings writers + CLI. | [BUILT — ADR 0016] |
| adapter read-order drift check | Fails if `CLAUDE.md`/`SOUL.md` stop importing `AGENTS.md` or restate a divergent read order. | [BUILT — `test_drift_checks.py`] |
| skill-registry drift check | Bidirectional coverage; future table may not name on-disk skills. | [BUILT — `test_drift_checks.py`] |
| context-matrix coverage check | Every on-disk skill has coverage naming known workflows. | [BUILT — `test_drift_checks.py`] |
| conductor call-graph drift check | Dependencies exist or are `[PLANNED]` with a halt rule; frontmatter matches this map. | [BUILT — WS10] |
| workspace-structure check | `init-creator` produces the documented tree incl. `.claude/skills/` (schema entry lands in WS11). | [BUILT — `test_cli.py`] |
| project-output-layout check | Project scaffolding deterministic; paths pinned in `project.schema.json`. | [BUILT — WS12] |
| Tier-0 memory policy check | Root `context/MEMORY.md` byte cap enforced. | [BUILT — `test_drift_checks.py`] |
| source-intake provenance check | `source_intakes` paths are schema-pinned under `sources/(intakes\|imports\|notes)/`; `validate workspace` additionally fails on missing files and symlink escapes after `resolve()`; intake import and forward-only status transitions covered. | [BUILT — `test_intake_import.py`, Phase 1 slice 1] |
| creator readiness check | Status-keyed onboarding and medium-based blockers collected into one error: selected channels at `profile_ready`; foundation population + required Markdown sections + lower-bound word/sample floors + `TBD` scan + context byte caps; intake provenance; required asset kinds per content medium; staged ElevenLabs Voice Design prompt package for audio/video creators; lifecycle asset/prompt existence with containment; typed + medium-required primary `reference_refs`; explicit creator-media permissions; approved strategy plus existing conversion-asset records at `strategy_ready`; and creator-scoped, goal-consistent, nonempty `content-schedule.json` slots with approved promoted conversion assets at `production_ready`. Asset paths remain schema-pinned under `references/`. | [BUILT — `test_readiness_validation.py`, ADR 0028] |
| connector layer | Env detection + kill switch + call cap, availability gating, canonical-record mapping, per-connector parsing (mock-hooked; no live calls), and `research-fetch-result` schema validation. | [BUILT — `test_connectors.py`, ADR 0022] |

### Deferred / gated subsystems

| Subsystem | Agentic OS location | InfluencerOS status | Un-defer trigger |
| --- | --- | --- | --- |
| Hooks | `.claude/hooks/` | [DEFERRED] | Explicit approval; memory-capture/skill-auto-commit only automate skills that already run manually. |
| Cron | `cron/jobs/` | [DEFERRED] | Phase 4 Automation OS. |
| Command Centre | `command-centre/` | [DEFERRED] | After file-first OS is stable + explicit scope approval. |
| Subagents | `.claude/agents/` | [DEFERRED — classified defer, copy plan WS15] | See "Subagent decision" below; adoption ADR written only when a Phase 1 producer reaches for it. |
| Anywhere-access | hosted APIs | [DEFERRED] | After Phase 4 + provider/security ADR. |
| Propagation content zones | scripts/settings/hooks/cron in `add-client.sh` | [GATED — ADR 0018] | Each fills when its subsystem is un-deferred. |

## Creation-Flow Call Graph (skill → skill)

The content conductor owns the pipeline. Per ADR 0017 each conductor declares a `## Dependencies` table and a phase→owner map with explicit `Skill(skill: "...")` invocations (mirroring the reference `00-social-content` orchestrator). Producer skills marked [PLANNED] are approved but unbuilt; until built, the conductor must halt at that phase and surface the missing skill (never pretend it ran).

```text
skills/influencer-os/SKILL.md  (content conductor; `dependencies` frontmatter + `## Phase Owners` [BUILT — WS10])
  Phase 1  Creator Profile, Strategy, Schedule             owner: influencer-os (inline)         [BUILT]
  Phase 2  Video Understanding Pack (when real videos)     owner: influencer-os (inline, v1)     [BUILT]
  Phase 3  Research Findings           -> Skill(create-research-findings)                         [BUILT]
  Phase 4  Idea Queue                   -> Skill(manage-idea-queue)                                [BUILT]
  Phase 5  Idea Promotion Gate          -> Skill(promote-idea) + user approval                    [BUILT]
  Phase 6  Project Creation             -> Skill(promote-idea) (a promotion creates Projects)     [BUILT]
  Phase 7  Applied Template/Structure   -> Skill(apply-social-template)                            [BUILT]
  Phase 8  Format-Specific Prod Plan    -> Skill(create-production-plan) --routes by target_format_id-->
             format_short_form_video -> MicroJourneyVideoPlan (+ BaseVideoGenerationPlan)
             format_carousel         -> CarouselPlan
             format_single_image_post-> SingleImagePostPlan
             format_story_sequence   -> StorySequencePlan
             format_article          -> ArticlePlan
             format_thread           -> ThreadPlan                                                [BUILT]
  Phase 9  Base Video Generation Plan  -> Skill(create-production-plan) (provider-neutral)        [BUILT]
  Phase 9b Creative review (advisory)  -> Skill(review-hook-payoff) (ReviewRecord, never blocks)  [BUILT — CD slice 4]
             editorial Passes          -> Skill(clear-writing-pass) / Skill(human-voice-pass)     [BUILT — CD slice 4]
  Phase 10 Generation Approval Gate    owner: user -> Skill(request-generation-approval)          [BUILT gate + record — P3 slice 2]
             (packages the exact call/batch as a GenerationApprovalRecord; dispatch refuses without one)
  Phase 10b External media import      -> Skill(import-generated-asset) (no provider call)        [BUILT — P3 slice 3]
  Phase 10c Quality gate (BLOCKING)    -> Skill(review-generated-assets) (before packaging)       [BUILT — P3 slice 5]
  (post)   Output Package             -> Skill(create-output-package)                             [BUILT]
  (post)   Publication registration   -> Skill(register-published-post)                           [BUILT — Phase 2 slice 1]
  (learn)  Analytics ingestion        -> Skill(ingest-analytics)                                  [BUILT — Phase 2 slice 2]
  (learn)  Performance summary        -> Skill(create-performance-summary)                        [BUILT — Phase 2 slice 3]
  (learn)  Creator Memory             -> Skill(distill-creator-learning)                          [BUILT — Phase 2 slice 4]
  (improve) Production reflection     -> Skill(distill-production-learning) (on reflection-due)   [BUILT — Phase 4 slice 3]

  Until a [PLANNED] owner exists on disk, the conductor halts at that phase and surfaces the
  missing skill (halt rule in skills/influencer-os/SKILL.md ## Dependencies).
```

```text
skills/create-influencer/SKILL.md  (setup conductor)   [BUILT — all owners exist]
  Phase 2  Identity          -> Skill(create-identity)
  Phase 3  Soul              -> Skill(create-soul)
  Phase 4  Personal brand    -> Skill(create-personal-brand)
  Phase 5  Voice samples     -> Skill(create-voice-samples)
  Phase 6  Operational summary -> Skill(create-creator-profile)
  Phase 7  Runtime context   -> Skill(create-runtime-context)
  Phase 8  Visual continuity analysis + user approval -> Skill(create-reference-library)
  Phase 9  Selected reference planning, prompt staging, and resolution -> Skill(create-reference-library)
             voice prompt staging is owned by create-reference-library via elevenlabs-voice-design
  Phase 10 Brand board       -> Skill(personal-brand-board) (visual creators; typed Reference Library links)
  Phases 1,11-14 intake, records, readiness, milestone acceptance, generation gate (inline)
```

## Self-Improvement Loop Call Graph (ADR 0016)

```text
trigger: user signals wrap-up / session end (by skill description; NO hook in v1)
skills/wrap-up/SKILL.md
  -> review deliverables (git status)
  -> collect feedback
  -> append per-skill entry     -> context/learnings.md
  -> record process lesson      -> docs/os-construction/process-learnings.md
  -> fix method directly        -> edit target SKILL.md / SKILL.local.md
  -> reconcile registry+matrix  -> docs/os-construction/skill-registry.md, context-matrix.md
  -> promote durable fact       -> Skill(memory-write)
  -> verify (tests + validate examples), then commit per AGENTS.md Git Rules

skills/memory-write/SKILL.md
  -> add/replace/remove one fact in context/MEMORY.md, deduped, within byte cap -> confirm
```

Automation (Stop-hook invocation, skill-auto-commit, memory-distill cron) is [DEFERRED]; it only automates *when* these skills run.

## Propagation Call Graph (ADR 0018 — Python CLI, not bash)

```text
influencer_os/cli.py
  init-creator <manifest>            -> creator_workspaces.init_creator()
       creates workspace-library/creators/<slug>/ ; copies baseline skills -> .claude/skills/ ;
       writes AGENTS.md + CLAUDE.md wrappers + structure  [propagate NOW]
  sync-creator-runtime <workspace>   -> creator_workspaces.sync_runtime()
       refresh copied baseline SKILL.md ; preserve SKILL.local.md, creator-only skills,
       context/brand/projects/memory/progress/.env  [BUILT]
  update-creators [--workspace-root] -> creator_workspaces.update_creators()
       backup-protected batch refresh; replaced skill folders backed up to
       .claude/skills-backup/ (mirrors update-clients.sh)  [BUILT — WS11]
  gated zones carried but inert: scripts, settings, hooks, cron templates  [GATED]
```

Freshly-initialized workspaces contain `.claude/skills/` because `init-creator` wires `sync-creator-runtime`; any local workspace created before that wiring may lack it and should be re-initialized. The `[BUILT scaffold]` tag refers to the scaffolding capability, not to any specific committed workspace (workspace state is git-ignored).

## Runtime Helper Call Graph

```text
influencer_os/cli.py
  -> creator_workspaces.py   (workspace scaffold/sync/update/validate + readiness milestones)
  -> brand_boards.py         (token spec + Reference Library -> editable brand-board projection)
  -> calendars.py            (content-schedule -> interactive calendar projection)
  -> projects.py             (project scaffold/validate + provenance resolution)
  -> memory.py               (bounded memory-write + log-learning writers)
  -> runs.py                 (dry-run init)
  -> validation.py           (fail-closed schema subset incl. $ref/oneOf/anyOf/allOf)
  -> connectors/             (list-connectors availability; research-fetch dispatch, ADR 0022)
  -> schemas/                (JSON Schema contracts)
```

## Research-Acquisition Connector Call Graph (ADR 0022)

```text
influencer_os/cli.py
  list-connectors [--env-file <path>]  -> connectors.registry.connector_status()
       reports each connector available|unavailable from env (env.py: key present,
       kill switch off, per-run call cap) — no provider call
  research-fetch <connector> <target> --run-dir <research-run-dir> [--depth|--days|--from-date|--to-date|--max-posts|--out|--env-file]
       -> connectors.fetch dispatch (fetch_reddit | fetch_x | fetch_firecrawl |
         fetch_linkedin) -> connector module (openai_reddit | xai_x |
         firecrawl_web | linkedin_apify) -> http.py provider call
       -> parse.py / models.py map provider output to ResearchEvidence + MetricSnapshot
       -> validate against research-fetch-result.schema.json BEFORE emitting
  guardrails: standing approval by key presence pinned to the four ADR 0022
    adapter IDs (not api_backed/scraping_api at large);
    per-run call cap (INFLUENCER_OS_CONNECTOR_MAX_CALLS) and kill switch
    (INFLUENCER_OS_DISABLE_PAID_CONNECTORS); free reddit.com enrichment bounded
    separately; runs only inside an explicit user-initiated fetch (no scheduled path).
  no key -> connector reports unavailable; run falls back to built-in WebSearch/WebFetch.
```

## Determinism Boundary Table

Each creation-flow boundary must have: input record(s) → output record + schema → deterministic acceptance criterion → validation → gate. Phase 0C built everything not marked with a later slice; the ADR 0020 record shapes and validation landed with Phase 1 slice 3 (workflow skills land in slices 4-5).

| Boundary | Input(s) | Output + schema | Acceptance criterion | Validation | Gate |
| --- | --- | --- | --- | --- | --- |
| Creator setup | intake | Creator Workspace + Profile + onboarding records (`creator-workspace`, `creator-profile`, `readiness-gates`, `channels`, `content-strategy`, `conversion-asset`) | readiness status matches selected channels, foundation mode, ElevenLabs voice prompt staging for audio/video, media permissions, approved strategy, conversion-asset provenance, and production calendar | `validate workspace`: full onboarding readiness validator at `profile_ready`/`foundation_ready`/`strategy_ready`/`production_ready`/`active` (selected channels, foundation population, required sections, lower-bound word/sample floors, context byte caps, intake provenance, required asset kinds per medium, lifecycle file existence, ElevenLabs Voice Design prompt asset, media permission assets, approved strategy, creator-scoped schedule integrity, approved slot conversion assets) [BUILT — ADR 0028] | readiness transitions stay human; not a pipeline Gate |
| Video understanding | public URLs or local real videos | `video-understanding-pack` | dated, source-linked; `/watch` or local equivalent only feeds distilled observations | `validate record video-understanding-pack` [BUILT — WS12] | exact approval for Whisper/API transcription fallback, batch processing, or first-run dependency installs |
| Research run | profile + schedule (+ VUP) | `research-run`, `research-evidence`, `metric-snapshot` | dated, sourced, platform-scoped, evidence-linked | `validate research` incl. JSONL line validation [BUILT — Phase 1 slice 3] | none |
| Research acquisition (connector) | search plan + query | `research-fetch-result` → mapped `research-evidence` + `metric-snapshot` | provider output maps to canonical records; per-run call cap honored; no key → unavailable + built-in fallback | `research-fetch` validates against `research-fetch-result.schema.json` before emitting [BUILT — ADR 0022] | standing approval by key presence (api_backed/scraping_api only); kill switch + call cap bound it |
| Research findings | research evidence | `research-findings` frontmatter + `findings.md` | concise, topic-organized, source-linked | frontmatter + char limit via `validate research` [BUILT — Phase 1 slice 3] | none |
| Idea queue | findings + evidence + schedule | `idea-queue-entry` + `idea-queue` manifest | scored, evidence-linked, statused; intent pair (`intended_emotion`, `core_message`) captured at origin (schema-optional, skill-required) | `validate queue`: manifest/entry consistency + evidence ref resolution [BUILT — Phase 1 slice 3; intent fields — Creative Direction slice 1] | none |
| Idea promotion | queue entry | `idea-promotion` | human-approved locked snapshot; intent pair carried verbatim from the entry | promotion gate: real queue entry required; unresolved evidence warns (human-approved) / fails (automated); intent carry-forward fails on drop/invent/rewrite [BUILT — Phase 1 slice 3 + Creative Direction slice 1] | user approves |
| Applied template | promoted idea | `applied-social-template` | beats map to idea; every beat carries a Content Beat Spine `beat_role` (ADR 0024); templates must land `hook` + `payoff` | `validate record applied-social-template`; spine semantics in `validate record social-template` [BUILT — WS12 + Creative Direction slice 1] | template gate |
| Production plan | applied template | format plan (6 schemas) | routed by `target_format_id` and one content unit per Project; article/carousel/thread may carry optional `format_subtype`; micro-journey `intended_emotion` must match the locked promotion (resolve-by-reference) | schema + routing check + intent no-override [BUILT — Phase 1 slice 6 + Creative Direction slices 2-3] | none |
| Platform fit (advisory) | project format + creator `primary_surfaces` | `project-warning` (`platform_fit`, `fit_level: native\|subtype\|analog\|none`) | non-native best fit warns at `init-project`; never blocks promotion or project creation (ADR 0024) | `platform_fit` semantics in record validation; capability map coverage drift check [BUILT — Creative Direction slice 3] | none (advisory) |
| Creative review (advisory) | drafted plan + promotion intent packet | `review-record` at `projects/<slug>/reviews/` | findings keyed to spine areas; `block` is a recommendation surfaced as a warning, never a halt; independence via `reviewer_execution.execution_mode` | schema + at-rest checks in `validate project` + advisory probe test [BUILT — Creative Direction slice 4] | none (advisory; contract in `docs/gates-and-reviews.md`) |
| Generation provider boundary | approved GenerationApprovalRecord + registry row | provider adapter call via `dispatch_generation` | every registry row is structurally `exact_approval`; dispatch requires an approved record id positionally; kill switch overrides everything; mock adapter only (ADR 0023 Decision 3) | registry import-time validation + dispatch refusal tests + `list-providers` [BUILT — Phase 3 slice 1] | exact human approval per call/batch |
| Base generation plan | video plan | `base-video-generation-plan` | provider-neutral; required for short-form video only | schema + project requirement check [BUILT — Phase 1 slice 6] | none |
| Output package | plan + artifact | `output-package` | full provenance chain enforced by schema (template + VUP ids required); IDs resolve to records; packaged projects cross-check project, creator, idea, template, plan IDs, upload-ready asset refs, and text-package nullable thumbnail rules | `register-output-package` + schema + provenance resolver [BUILT — WS12 + re-review fixes + Phase 1 slice 7] | generation approval |

## Subagent Decision (open)

The reference ships a `.claude/agents/` subsystem (e.g. `ssc-designer`, `ssc-image-generator`) invoked via `Agent(tool: "...", inputs: {...})` — orchestrators delegate heavy sub-tasks to typed subagents that return structured objects. The copy plan classified this subsystem in workstream 15 (2026-07-03): **defer** — revisit when the first Phase 1 producer skill is built, and write the adoption ADR only if that build actually reaches for the pattern (adoption is a divergence-test event). It remains a candidate for the [PLANNED] producer skills (e.g. a research subagent, an idea-generation subagent). Placed here so the option is visible, not silently omitted.
