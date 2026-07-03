# InfluencerOS Architecture Map

Last updated: 2026-07-03

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
Workflow contracts         schemas/ (20) + docs/pipeline-contract.md                     [BUILT]
Skills (source)            skills/<skill-name>/SKILL.md (+ references/, SKILL.local.md)  [BUILT + PLANNED]
Runtime CLI                influencer_os/ (cli + helpers + validation)                   [BUILT]
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
| `docs/adr/0001–0019` | Architectural decisions (0016–0019 added this pass). | [BUILT] |

### Workflow contracts

| Path | Role | Status |
| --- | --- | --- |
| `schemas/*.schema.json` (20) | JSON Schema contract per durable record. | [BUILT] |
| `examples/*.example.json` (20) | Valid example per schema; CLI/test fixtures. | [BUILT] |
| `docs/pipeline-contract.md` | Typed step-to-step pipeline contract. | [BUILT] |
| `docs/provider-boundary.md` | Provider approval boundary. | [BUILT] |
| `docs/creator-workspace-structure.md` | Workspace layout + local-state policy. | [BUILT] |

### Skills (`skills/<skill-name>/`)

Source layout per ADR 0017: repo-central, kebab-case, no category prefixes, optional per-skill `references/`, `SKILL.local.md` overrides, machine-actionable `dependencies` frontmatter. The ADR-0017 conventions are **[BUILT]** as of workstreams 9–10: both conductors and both system skills declare `dependencies` frontmatter, both conductors carry `## Rules`/`## Self-Update`, and a worked `skills/influencer-os/SKILL.local.md` exists. Producer skills below remain [PLANNED].

| Skill | Category | Role | Status |
| --- | --- | --- | --- |
| `influencer-os` | conductor | Content-creation conductor (10 phases; `dependencies` + `## Phase Owners` declared). | [BUILT] |
| `create-influencer` | conductor | Creator-setup conductor (13 phases). | [BUILT] |
| `create-identity` | setup | `brand_context/identity.md`. | [BUILT] |
| `create-soul` | setup | `brand_context/soul.md`. | [BUILT] |
| `create-personal-brand` | setup | `brand_context/personal-brand.md`. | [BUILT] |
| `create-voice-samples` | setup | `brand_context/voice-samples.md`. | [BUILT] |
| `create-creator-profile` | setup | `creator-profile.json`. | [BUILT] |
| `create-runtime-context` | setup | `context/SOUL.md`,`USER.md`,`MEMORY.md`. | [BUILT] |
| `create-reference-library` | setup | `references/reference-library.json` + prompts. | [BUILT] |
| `create-research-findings` | planning | Concise Research Findings backed by dated evidence. | [BUILT — Phase 1 slice 4] |
| `manage-idea-queue` | planning | Scored Idea Queue entries. | [BUILT — Phase 1 slice 4] |
| `promote-idea` | planning | Human-approved Idea Promotion and project creation. | [PLANNED — Phase 1] |
| `apply-social-template` | planning | Applied Social Template or production structure for the promoted idea. | [PLANNED — Phase 1] |
| `create-production-plan` | planning | Routes promoted idea to a format-specific plan. | [PLANNED — Phase 1] |
| `create-output-package` | planning | Output Package + provenance. | [PLANNED — Phase 1] |
| `distill-creator-learning` | learning | Performance evidence → Creator Memory. | [PLANNED — Phase 2] |
| `wrap-up` | system | Session-end learnings, skill self-fix, registry reconcile, memory promote. | [BUILT — ADR 0016] |
| `memory-write` | system | Bounded, deduped `context/MEMORY.md` writes (2,500-byte cap via CLI). | [BUILT — ADR 0016] |

### Runtime CLI (`influencer_os/`)

| Path | Role | Status |
| --- | --- | --- |
| `cli.py` | Command surface; routes to helpers, holds no product rules. | [BUILT] |
| `validation.py` | Fail-closed schema subset (`$ref`/`oneOf`/`anyOf`/`allOf`); disk-derived example coverage. | [BUILT — WS13] |
| `creator_workspaces.py` | `init-creator`, `import-intake`/`set-intake-status` (source intake provenance), `sync-creator-runtime`, `update-creators` (backup-protected), readiness gates. | [BUILT — WS11; intake commands Phase 1 slice 1] |
| `projects.py` | Project scaffolding + validation + promotion-anchored provenance resolution. | [BUILT — WS12 + Phase 1 slice 3] |
| `research.py` | JSONL + frontmatter validation, `validate research`/`validate queue` (incl. run-scoped consistency), promotion gate. | [BUILT — Phase 1 slice 3; run-scoped checks slice 4 batch A] |
| `recall_index.py` | Rebuildable SQLite recall-index projection (ADR 0010); `rebuild-index` per-creator rebuilds; never a validation dependency. | [BUILT — Phase 1 slice 4 batch B] |
| `boards.py` | Content Board projection: `rebuild-board` (cards derived, columns/manual order preserved) + `validate board` agreement check. | [BUILT — Phase 1 slice 4 batch C] |
| `prune.py` | Retention pruning: dry-run default, `--apply` deletes unreferenced out-of-window evidence + snapshots, pruned ids recorded on the run manifest. | [BUILT — Phase 1 slice 4 batch D] |
| `memory.py` | Bounded `memory-write` + `log-learning` writers. | [BUILT — ADR 0016] |
| `runs.py` | Dry-run init + run records. | [BUILT] |

### Tests (`tests/`) — parity + contract

| Path | Role | Status |
| --- | --- | --- |
| `test_schema_validation.py` | All examples validate; coverage derived from disk; fail-closed subset tests. | [BUILT — WS13] |
| `test_cli.py` | CLI behavior incl. provenance resolution and readiness gates. | [BUILT] |
| `test_recall_index.py` | Index resolution per record kind, idempotent per-creator rebuilds, fail-closed ambiguity, default ADR 0010 path. | [BUILT — Phase 1 slice 4 batch B] |
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
| creator readiness check | Status-keyed medium-based blockers collected into one error: foundation population + required Markdown sections + lower-bound word/sample floors + `TBD` scan + context byte caps, intake provenance, required asset kinds per content medium, lifecycle asset/prompt existence with containment, typed + medium-required primary `reference_refs` (kind-checked at every status; non-retired and prompted-or-later at generation_ready), and asset `source_ref` resolution to a recorded intake id or contained workspace file; asset paths schema-pinned under `references/`. | [BUILT — `test_readiness_validation.py`, Phase 1 slice 2] |

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
  Phase 5  Idea Promotion Gate          -> Skill(promote-idea) + user approval                    [PLANNED]
  Phase 6  Project Creation             -> Skill(promote-idea) (a promotion creates Projects)     [PLANNED]
  Phase 7  Applied Template/Structure   -> Skill(apply-social-template)                            [PLANNED]
  Phase 8  Format-Specific Prod Plan    -> Skill(create-production-plan) --routes by target_format_id-->
             format_short_form_video -> MicroJourneyVideoPlan (+ BaseVideoGenerationPlan)
             format_carousel         -> CarouselPlan
             format_single_image_post-> SingleImagePostPlan
             format_story_sequence   -> StorySequencePlan                                         [PLANNED]
  Phase 9  Base Video Generation Plan  -> Skill(create-production-plan) (provider-neutral)        [PLANNED]
  Phase 10 Generation Approval Gate    owner: user (exact-call approval)                          [BUILT gate]
  (post)   Output Package             -> Skill(create-output-package)                             [PLANNED]
  (learn)  Creator Memory             -> Skill(distill-creator-learning)                          [PLANNED — Phase 2]

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
  Phase 8  Reference planning -> Skill(create-reference-library)
  Phases 1,9-13  intake, prompt staging, readiness, acceptance gate, generation gate (inline)
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
  -> creator_workspaces.py   (workspace scaffold/sync/update/validate + readiness gates)
  -> projects.py             (project scaffold/validate + provenance resolution)
  -> memory.py               (bounded memory-write + log-learning writers)
  -> runs.py                 (dry-run init)
  -> validation.py           (fail-closed schema subset incl. $ref/oneOf/anyOf/allOf)
  -> schemas/                (JSON Schema contracts)
```

## Determinism Boundary Table

Each creation-flow boundary must have: input record(s) → output record + schema → deterministic acceptance criterion → validation → gate. Phase 0C built everything not marked with a later slice; the ADR 0020 record shapes and validation landed with Phase 1 slice 3 (workflow skills land in slices 4-5).

| Boundary | Input(s) | Output + schema | Acceptance criterion | Validation | Gate |
| --- | --- | --- | --- | --- | --- |
| Creator setup | intake | Creator Workspace + Profile (`creator-workspace`, `creator-profile`) | readiness status matches medium-based blockers | `validate workspace`: full medium-based readiness validator at `content_ready`/`generation_ready`/`active` (foundation population, required sections, lower-bound word/sample floors, context byte caps, intake provenance, required asset kinds per medium, lifecycle file existence) plus the generation-ready visual-asset gate [BUILT — WS14 + Phase 1 slice 2] | status transitions stay human |
| Video understanding | public URLs or local real videos | `video-understanding-pack` | dated, source-linked; `/watch` or local equivalent only feeds distilled observations | `validate record video-understanding-pack` [BUILT — WS12] | exact approval for Whisper/API transcription fallback, batch processing, or first-run dependency installs |
| Research run | profile + schedule (+ VUP) | `research-run`, `research-evidence`, `metric-snapshot` | dated, sourced, platform-scoped, evidence-linked | `validate research` incl. JSONL line validation [BUILT — Phase 1 slice 3] | none |
| Research findings | research evidence | `research-findings` frontmatter + `findings.md` | concise, topic-organized, source-linked | frontmatter + char limit via `validate research` [BUILT — Phase 1 slice 3] | none |
| Idea queue | findings + evidence + schedule | `idea-queue-entry` + `idea-queue` manifest | scored, evidence-linked, statused | `validate queue`: manifest/entry consistency + evidence ref resolution [BUILT — Phase 1 slice 3] | none |
| Idea promotion | queue entry | `idea-promotion` | human-approved locked snapshot | promotion gate: real queue entry required; unresolved evidence warns (human-approved) / fails (automated) [BUILT — Phase 1 slice 3] | user approves |
| Applied template | promoted idea | `applied-social-template` | beats map to idea | `validate record applied-social-template` [BUILT — WS12] | template gate |
| Production plan | applied template | format plan (4 schemas) | routed by `target_format_id` | schema + routing check | none |
| Base generation plan | video plan | `base-video-generation-plan` | provider-neutral | schema | none |
| Output package | plan + artifact | `output-package` | full provenance chain enforced by schema (template + VUP ids required); IDs resolve to records; packaged projects cross-check project, creator, idea, template, and plan IDs | schema + provenance resolver [BUILT — WS12 + re-review fixes] | generation approval |

## Subagent Decision (open)

The reference ships a `.claude/agents/` subsystem (e.g. `ssc-designer`, `ssc-image-generator`) invoked via `Agent(tool: "...", inputs: {...})` — orchestrators delegate heavy sub-tasks to typed subagents that return structured objects. The copy plan classified this subsystem in workstream 15 (2026-07-03): **defer** — revisit when the first Phase 1 producer skill is built, and write the adoption ADR only if that build actually reaches for the pattern (adoption is a divergence-test event). It remains a candidate for the [PLANNED] producer skills (e.g. a research subagent, an idea-generation subagent). Placed here so the option is visible, not silently omitted.
