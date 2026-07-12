# InfluencerOS Progress

Last updated: 2026-07-12

This file tracks repo-level product progress. It is public project state. Private creator-specific progress belongs under `workspace-library/creators/<creator-slug>/progress/`.

## Current Build/Test Data Policy

InfluencerOS is being built and tested before real creator onboarding. Current Creator Workspace contents under `workspace-library/` are disposable fixtures unless the user explicitly promotes a workspace as production creator state.

This includes generated personas, generated reference images, prompts, research notes, draft projects, workspace memory, and setup progress. The operator expects to wipe this test data before using the system for real creators. Durable progress is the operating system work recorded in this repo: docs, schemas, tests, CLI behavior, skills, templates, examples, and validation rules.

## Documentation Updates

- Completed the operating cadence model, ADRs 0044-0047 (2026-07-12): six slices landed on `main` — Avatar Image mechanics with the ADR 0045 single-use approval carve-out (b35c522, bb4dcaf; setup call-graph fix c4b30d9), the Review Record contract with `review-creator-setup` and `review-strategy` (b4dbe48), the Strategy block restructure with an enforced Research Demand loop cap (f575f39), Campaign Duration Target (1d2e8bc), Quarter Plan/Revision record contracts (91c099a) plus the Quarterly Review and `quarterly-planning-cycle` skills (7bd361d), and Weekly Planning Cycle constructors/validation with the `weekly-planning-cycle` and `review-concept-promotion` skills (a73a7ef, 28c67d8). Open design questions were settled and recorded as "Settlement (implementation)" notes in ADRs 0044 (weekly Opportunity->Concept reconciliation uses the shipped ADR 0031 assignment model; no new promotion path), 0046 (unresolved Research Demands live as `research_demand`-flagged findings on the terminal Review Record), and 0047 (computed past-target signal, referential closure in `validate_cadence_records`, `lesson_refs` unresolved by design, required `terminal_review_record_id`). Verification: the suite grew 1,034 -> 1,130 tests, all green; `validate examples` grew 54 -> 57 records. The stale `workspace-library/` fixture rebuild is deferred to its own session.
- Hardened ADR 0047 slice 5b after review (2026-07-12): Quarterly Reviews now require complete plan/research packets and computable capped Demand-loop lineage; every approved Quarter Plan requires its exact terminal Quarterly Review; Campaign, Concept, PerformanceSummary, and terminal-review closure validates schema, creator scope, and path/id agreement before the constructor writes. Re-confirmation accepts only active Concepts. The quarterly conductor now creates the approved plan before its proposed Revisions, executes approved lifecycle/Duration Target/schedule/Revision changes, and finishes with a ready check. Verification: 1,098 unit tests pass and 57 examples validate; fresh temporary workspaces cover the workspace seam, and stale `workspace-library/` fixtures were untouched.
- Completed the routing and lean-architecture cleanup (2026-07-09): removed the superseded Content Idea Set / Selected Content Idea schemas, examples, and obsolete system map; made the connector route table own both CLI choices and dispatch; made generation records own asset containment and manifest construction; loaded environment keys from both research and generation registries; and removed fragile schema/connector counts from current docs. Verification: the full suite passes and 53 schema examples validate.
- Added `docs/workflow-creator-to-video.html` (2026-07-09): a focused visual map of the create-influencer-to-created-video path. It shows each workflow step, the related skills/schemas/templates/workspace records, both human gates, and the exact stopping condition for "video created" before quality review and output packaging.
- Hardened object reference planning (2026-07-09): traced Adira's grouped prop output to one Reference Asset and prompt that explicitly requested eight distinct objects, then made object references atomic across the creator-setup workflow, `create-reference-library`, and the canonical object prompt template. Added a drift regression requiring one distinct prop per asset, prompt, provider request, and output image; multi-angle sheets may show only repeated views of the same object.
- Implemented ADR 0046 slice 2 (2026-07-12): workspace-anchored Setup and Strategy Review Records now validate at rest under `reviews/`, retain advisory-only warnings, and are kept distinct from project reviews. The Review Record contract now carries scope-specific areas and a machine-readable `research_demand` marker; Quarterly and Concept reviews remain fail-closed until their conductors ship.

## Phase Map

### Phase 0: Architecture Foundation

Goal: Make the repo self-orienting for future agents before deeper implementation.

Status: Complete (2026-07-03). Phase 0C parity hardening exited with all roadmap criteria passing; see Current Verification below.

Completed:

- Root context adapters for Codex, Claude, and OpenClaw/Hermes-style contexts.
- OS construction docs moved under `docs/os-construction/` so build-time planning stays separate from runtime workflow contracts.
- Handoff-ready PRD with problem statement, user stories, implementation decisions, testing decisions, phase plan, and out-of-scope boundaries.
- Roadmap with phase exit criteria.
- Repository map with file ownership and creation-flow call map.
- Agentic OS alignment document with adopted patterns and accepted divergences.
- Agentic OS copy/adaptation audit.
- Agentic OS parity plan: adapt current repo toward close parity; do not restart; defer Command Centre.
- PRD rewritten in handoff-ready `to-prd` structure.
- Short-term parity hardening plan added.
- Agentic OS divergence test for architecture-impacting changes.
- Excalidraw visual architecture map standard and `docs/os-construction/maps/` location.
- First-party OS persona context in root `context/` and `brand_context/`.
- Context matrix, skill registry, and process learning docs.
- ADR 0014 for first-party OS persona and skill overrides.
- Markdown draft for the overall InfluencerOS architecture map.
- Markdown draft for the Agentic OS vs InfluencerOS comparison map.
- Excalidraw scene for the overall InfluencerOS architecture map.
- Corrected the Agentic OS source of truth to `/Users/ashokaji/code/External repos/Agentic Academy/agentic-os` across root adapters and construction docs.
- Re-ran the copy/adaptation audit against the purchased Agentic OS reference and identified two Phase 0C decisions: skill runtime layout and Creator Workspace propagation/sync behavior.
- Accepted and implemented copied creator runtime skills: repo `skills/` remains source, Creator Workspaces receive `.claude/skills/` runtime copies, and `sync-creator-runtime` preserves local overrides and creator-only skills.
- Ran an adversarial Agentic OS parity review; recorded the ranked divergence ledger in `docs/os-construction/adversarial-review.md`.
- Recorded ADR 0016 (self-learning system skills), ADR 0017 (skill-layout finalization), ADR 0018 (workspace propagation scripts), and ADR 0019 (adapter model).
- Authored `docs/os-construction/architecture-map.md`: the file-granular map with the true skill and CLI call graphs, marking BUILT vs PLANNED vs DEFERRED.
- Restructured the always-loaded adapters per ADR 0019: `AGENTS.md` canonical, `CLAUDE.md` and `SOUL.md` thin importers, the read order defined once, and the dual-SOUL collision resolved.
- Reconciled `agentic-os-alignment.md` and `agentic-os-copy-plan.md` with the four new decisions and relabeled the repository-map record data-flow.
- Added parity-review workstreams 9-15 to `docs/os-construction/short-term-plan.md`.
- Recorded the Phase 0C execution decisions and batch order in the short-term plan: validator subset with fail-closed unknown keywords, 2,500-character memory cap at root and creator scope, `[PLANNED]` halt markers with a Phase 1 build obligation for the producer skills, reference-only copy policy, subagent-pattern deferral, and no PRD-to-issues conversion.
- Added drift checks (`tests/test_drift_checks.py`, Batch A / workstreams 1, 3, 4, 8): adapter read order and imports per ADR 0019, bidirectional skill-registry coverage including future-table enforcement, and context-matrix coverage against known workflow rows.
- Hardened the validator (Batch B / workstream 13): fail-closed schema subset with intra-file `$ref` to `#/definitions`, `oneOf`, `anyOf`, and `allOf`; unknown keywords, type names, formats, and unsupported construct forms raise `SchemaDefinitionError` instead of silently passing; example coverage is derived from disk so every schema requires a matching example and vice versa.
- Addressed the second adversarial re-review round (2026-07-03): packaged output packages must now reference every project plan record — omitting the Base Video Generation Plan when generation is planned fails validation (the provenance chain must be complete, not merely free of dangling IDs); the validator's shape guard now covers the `type` keyword (an empty list is falsy and silently skipped type validation entirely; non-string members and empty strings are also `SchemaDefinitionError`s); and the Phase 0C exit note no longer states a stale suite count.
- Addressed the post-closeout adversarial re-review (2026-07-03): packaged projects now cross-check `creator_profile_id` and `production_plan_ids` against the project and its plan records (dangling or foreign IDs fail); the validator fail-closes on malformed keyword values, not just unknown keyword names (a string `enum` or a string `additionalProperties` is now a `SchemaDefinitionError`, with negative tests); the adversarial review ledger gained a Resolution Status section mapping every major finding to the batch and commit that closed it; the architecture-map determinism boundary table replaced stale `[TO ADD]` markers with built statuses and explicit `[PHASE 1 — ADR 0020 slice]` markers; and the full CLI (including `update-creators`, `validate record`, `memory-write`, `log-learning`) is now documented in `README.md`, `ARCHITECTURE.md`, and the repository map.
- Closed out Phase 0C (Batch G / workstream 15): inspected the reference `.claude/agents/` (four typed subagents) and `.claude/commands/` (`/start-here`, `/archive-gsd`) and added copy-plan rows (subagents: defer, ADR only on adoption by a Phase 1 producer; commands: do not copy now); recorded the reference-only copy policy in the copy plan; updated the architecture-map subagent decision to reference the classification; refreshed the parity plan's gap audit (all success criteria met 2026-07-03); reviewed the comparison map framing against the copy plan and decisions; and re-ran every roadmap Phase 0C exit criterion end to end.
- Built the propagation mechanism (Batch F / workstream 11, ADR 0018): `update-creators` refreshes baseline skill copies across every Creator Workspace with a backup-protected sync (replaced skill folders are copied to `.claude/skills-backup/<skill-name>/` before refresh) while preserving `SKILL.local.md` files, creator-only skills, and all creator state; `init-creator` writes thin workspace `AGENTS.md`/`CLAUDE.md` wrappers; `creator-workspace.schema.json` now requires the `.claude/skills/` directory (closing the missing-directory gap); and gated zones (scripts, settings, hooks, cron) are documented as inert with a test asserting no gated-zone content is scaffolded.
- Formalized the conductor call graph (Batch E / workstream 10, ADR 0017): both conductors declare `dependencies` frontmatter; `skills/influencer-os/SKILL.md` carries a `## Dependencies` table and a `## Phase Owners` table naming an owner skill per producing phase with explicit `Skill(skill: "...")` invocations; the six Phase 1 producers and `distill-creator-learning` are `[PLANNED]` halt markers per the execution decisions (halt and surface the missing skill, never improvise); a drift check fails if a conductor names a skill neither on disk nor `[PLANNED]`-marked, requires the halt rule, requires registration, and diffs conductor frontmatter against the `architecture-map.md` call graph. The architecture map's call-graph fence was renumbered to the conductor's actual phases and stale BUILT/PLANNED statuses from batches A-D were refreshed.
- Built the self-improvement loop (Batch D / workstreams 9, 7, and the workstream 5 residue, ADR 0016): `skills/wrap-up` and `skills/memory-write` exist with registry and context-matrix rows; `python3 -m influencer_os log-learning` appends dated, deduplicated per-skill entries to `context/learnings.md`; `python3 -m influencer_os memory-write` performs deduplicated `MEMORY.md` writes and refuses any write past the 2,500-byte cap; both conductors carry `## Rules` and `## Self-Update`; a worked `skills/influencer-os/SKILL.local.md` exists; Tier 0 creator recall rules are defined in `docs/creator-workspace-structure.md`; and drift checks now enforce the root memory cap, the conductor sections, and the local-override example. Root `context/MEMORY.md` was refreshed, fixing the stale line that named the wrong repo as the Agentic OS source of truth.
- Landed the determinism fixes (Batch C / workstreams 12, 14, and the workstream 6 residue): `project.schema.json` requires `acceptance_criteria` (optional `constraints`/`dependencies`); output-package `source_refs` require `applied_social_template_id` and `video_understanding_pack_ids`; project and output-package provenance IDs resolve to real workspace records (`references/reference-library.json` assets and `research/<kind>/<pack-id>.json` files) with dangling references failing validation; a packaged project cross-checks its output package against the applied template; `validate record <schema> <path>` validates any mid-pipeline record; and a `generation_ready` workspace fails validation without at least one approved `character` or `video_style` asset. The transitional research/idea layout is documented in `docs/creator-workspace-structure.md`.

Remaining:

- Optional: render the comparison map Excalidraw scene (framing reviewed 2026-07-03).

### Phase 1: Planning OS

Goal: Create stable creator workspaces and produce researched, creator-fit, upload-ready content packages without requiring provider-backed generation.

Status: Complete (2026-07-04). Slices 1 (master intake import), 2 (creator readiness validation), 3 (ADR 0020 research module schema slice), 4 (Research Findings and Idea Queue workflow, batches A-E), and 5 (Idea Promotion to Project workflow, batches A-C) landed 2026-07-03; slices 6 (format-specific production planning) and 7 (Output Package registration) landed 2026-07-04; research-intelligence hardening landed 2026-07-04 before scheduled research automation. The deferred scheduled research automation work belongs to Phase 4 unless explicitly reopened earlier.

Completed:

- Root OS plus ignored Creator Workspace architecture.
- Hybrid creator authoring from rich intake into split workspace files.
- Creator Profile v2 as operational summary.
- Project-scoped content work under `projects/<project-id>/`.
- Universal Output Package plus platform adaptations.
- Creative Performance Map required in every Output Package.
- Schema contracts and examples through Output Package.
- `init-creator` CLI support.
- Workspace validation CLI support.
- Tests for creator workspace scaffolding and validation.
- `init-project` CLI support.
- Project validation CLI support.
- Tests for project scaffolding and validation.
- Master intake import (slice 1, 2026-07-03, per `docs/workflows/master-intake-import-implementation-plan.md`): `import-intake` copies a setup source into the type-mapped `sources/` folder and appends a schema-valid `source_intakes` entry (`pending`, deterministic ids, fail-closed on duplicate destinations/ids); `set-intake-status` moves extraction status forward only (`pending` → `drafted` → `reviewed`); `validate workspace` resolves every intake path to a real file; `skills/create-influencer` phase 1 now invokes the commands; `examples/sources/luna-fit-breakdown.example.md` backs the example manifest's declared intake; 13 tests in `tests/test_intake_import.py`.
- Addressed the slice 1 adversarial review (2026-07-03; findings recorded in the slice plan): intake provenance is now contained to the workspace — `validate workspace` rejects absolute `source_intakes` paths and `..` escapes after `resolve()` with a dedicated containment error (both reproduced as accepted before the fix); and the validator's `date` format now requires a real calendar date via `datetime.date.fromisoformat` on top of the YYYY-MM-DD shape check, so `2026-99-99` fails everywhere `format: "date"` appears, including `import-intake --imported-on`. Four negative tests added.
- Schema-pinned intake containment (2026-07-03 follow-up): `creator-workspace.schema.json` restricts `source_intakes[].path` to `^sources/(intakes|imports|notes)/[^/]+$`, so escapes fail declaratively wherever the record is validated; the behavioral `resolve()` check remains as the second layer and now specifically catches symlinked intakes that resolve outside the workspace (negative test with an in-workspace symlink to an outside file).
- Creator readiness validation (slice 2, 2026-07-03, per `docs/workflows/creator-readiness-validation-implementation-plan.md`): `validate workspace` is status-keyed — at `content_ready`/`generation_ready`/`active` it enforces the medium-based blockers and collects every failure into one error (foundation files populated beyond their scaffolds, required brand-context sections, lower-bound word/sample floors, no `TBD` placeholders, context byte caps 3072/1536/2500, at least one source intake, required asset kinds per `content_strategy.content_mediums`, lifecycle-appropriate asset/prompt file existence with symlink-safe containment); `generation_ready` additionally requires required visual kinds at `prompted` or later plus the workstream-14 approved-visual gate; `reference_refs` primary ids resolve at every status; reference-library `path`/`prompt_path` are schema-pinned under `references/`; the example library gained prompted `outfit` and `brand` entries; 27 tests in `tests/test_readiness_validation.py` plus schema-pin tests. Closes the reference-asset file-existence and markdown-completeness gaps in `docs/workflows/creator-setup.md`.

- Addressed the slice 2 adversarial review (2026-07-03; findings recorded in the slice plan): primary `reference_refs` now resolve through an id-to-asset map with kind enforcement at every status (a brand asset can no longer be the video-style primary), mediums make their primary fields mandatory at readiness, retired primaries are blockers and `generation_ready` requires primaries at `prompted` or later, `primary_video_style_asset_id` became schema-optional for text-first creators; non-retired asset `source_ref` values must resolve to a recorded intake id or a workspace-contained existing file; and the text-first test strips medium-specific visual assets and primaries while retaining the universal profile-avatar asset and approved brand board, proving the text-first path. Both findings reproduced before the fix; eight negative tests and one schema test added. The universal avatar/board requirement was added on 2026-07-10.

- ADR 0020 research module schema slice (slice 3, 2026-07-03, per the user-approved Execution Decisions in `docs/workflows/research-and-ideas-implementation-plan.md`, batches A-D): 18 new schemas and luna-fit examples landed as one coherent set (content schedule, research run, JSONL evidence and metric snapshots, findings and stable-finding frontmatter, five intelligence files, idea queue entry and manifest, idea promotion, project warning, content board, automation-run and system-event record shapes); the validator gained a fail-closed `date-time` format; an enum drift check pins every research schema's platform/content-type enum to the canonical ADR 0020 constants; `influencer_os/research.py` validates JSONL line by line, findings frontmatter (scoped YAML subset, no third-party dependency) with the summary char limit, queue manifest/entry consistency with evidence resolution, and the promotion gate (a promotion must point to a real queue entry; unresolved evidence warns for human-approved promotions and fails for automated paths) via `validate research` and `validate queue`; the project schema migrated to the new status ladder (`created` → `planning` → `ready_for_generation` → `generated` → `packaged` → ...) with `source_refs` anchored on `idea_promotion_id` (cached deeper refs must match the locked promotion), the `idea/` folder replaced by `evidence-brief.md`, and the applied template, four production plans, and output package swapped `selected_content_idea_id` for `idea_promotion_id`; `init-creator` scaffolds the research/boards/system layout with `boards/` and `system/` schema-pinned; `content-idea-set` and `selected-content-idea` are marked deprecated compatibility artifacts; the three live fixture workspaces were migrated and repaired to validate (missing `claude_skills` keys, missing thin `CLAUDE.md` wrappers, one misfiled media intake). Steps 7-10 of the implementation sequence (recall index, board rebuild, prune) defer to slice 4.

- Addressed the slice 3 post-landing review (2026-07-03; findings recorded in the slice plan): the promotion gate and queue validation now resolve `video_understanding_pack_ids` (a promotion citing a nonexistent video pack warned nothing before — the Product Invariant's video-evidence trace was unenforced); the enum drift check extends to `project.schema.json`'s cached `source_platforms`/`source_platform_content_types` copies (previously the only unpinned embeddings); project warnings enforce the ADR 0020 pairing rule (`project_id` and `idea_promotion_id` together for promoted work, neither for queue-level warnings); the raw run-JSONL id scan reports file and line on malformed JSON instead of a bare decode error reachable from `validate queue`/`validate project`; run folder names must match `research_run_id` (the entries/promotions filename==id pattern); queue manifest `status_counts` are verified against entry statuses; JSONL splitting no longer breaks on raw U+2028/U+2029 inside JSON strings; and 16 tests pin the previously untested failure paths (promotion resolution and cached-ref mismatches in `projects.py`, invalid-JSON JSONL, stable-finding schema failures).

- Addressed the slice 3 second review round (2026-07-03; findings and the declined snapshot-consistency check recorded in the slice plan): `validate research` and `validate queue` enforce creator scoping — they require the owning `creator-workspace.json` and pin every record's `creator_profile_id`/`creator_slug` to it (a workspace previously validated with schedule, run, evidence, queue, and promotion records all claiming `creator_other`); the promotion gate rejects a promotion whose queue entry belongs to a different creator, protecting the `validate project` path too; `multi_platform_package` left the project `content_unit_type` enum until the production build-out adds its plan schema (a `created` project using it validated, then dead-ended at `planning` with no production plan schema); and the README opening flow, platform statement, and schema inventory now teach the ADR 0020 pipeline instead of the deprecated five-ideas flow. Seven creator-scope tests and a schema negative test added.

- Landed the approval surface decisions (2026-07-03, per the user-approved Approval Surface Decisions in the slice plan): the format vocabulary is a closed enum across `approved_formats`, `format_recommendations`, `target_formats`, `preferred_formats`, and `format_id` (five schemas), pinned by the enum drift check alongside the platform and content-type enums, with a code drift check tying `PRODUCTION_SUPPORTED_FORMATS` to `PRODUCTION_PLAN_SCHEMAS`; the promotion gate hard-fails a promotion approving no production-supported format, mechanizing the slice success condition that was previously a workflow rule; and projects must stay within the locked promotion's approved surface — `target_formats` ⊆ `approved_formats` directly, and `platform_targets` via mapped subset (a distribution surface that maps to an ADR 0020 research platform must be approved; off-set surfaces like `youtube_shorts` stay exempt because the universal format travels there; closing the surface vocabulary defers to the production build-out).

- Integrated `bradautomates/claude-video` `/watch` as the supported external acquisition tool for the existing Video Understanding Pack phase (2026-07-03): `/watch` remains outside the repo and is not a required producer skill; it may inspect public URLs or user-provided local videos, write working files under ignored local storage such as `.tmp/watch/...`, and feed distilled timestamp-aware observations into `VideoUnderstandingPack` records. Native captions and local frame extraction are allowed research actions; Whisper/API transcription fallback, first-run dependency installs, and video batches require explicit approval. Upstream hooks, commands, and hidden automation are not copied into InfluencerOS v1.

- Addressed the watch integration review (2026-07-03; verified against the upstream repo): the documented `/watch` invocations and the conductor tool boundary now pass and name `--no-whisper`, because the upstream default falls back to Whisper automatically on caption-less videos and prompts for API-key setup on first run — the two actions the provider boundary gates behind explicit approval; the record-mapping table uses exact schema paths (`sources[].observations.*` per source; `cross_video_patterns` and `creator_fit_findings` at the pack top level); and the alignment doc gained the external-tool Adopted Patterns row the divergence test cites, so future external-tool decisions can pass under an existing listed pattern.

- Slice 4 batch A (2026-07-03, per the user-approved Slice 4 Execution Decisions in `docs/workflows/research-and-ideas-implementation-plan.md`): the three run-scoped consistency checks deferred from the slice 3 review are enforced file-first, with the recall index staying a pure projection. Every evidence and metric-snapshot JSONL record's `research_run_id` must match its containing run folder; a run's `outputs.evidence_ids` and `outputs.metric_snapshot_ids` must reconcile exactly, both directions, with the run's JSONL contents; and structured evidence refs resolve run-scoped — the evidence and metric snapshots must live in the run the ref names (`resolve_evidence_ref`, shared by `validate queue` and the promotion gate), with cross-run duplicate ids failing closed because they make resolution ambiguous. Queue refs hard-fail on mismatch; the promotion gate folds mismatches into the existing unresolved-refs handling (warn for human-approved, fail for automated). The human-approved-warning test was rebuilt on a never-existed ref because deleting a run's evidence file is now a hard outputs-reconciliation error, not a warnable state. The prune-vs-outputs-reconciliation interaction is recorded in the slice plan as an open batch D decision.

- Slice 4 batch B (2026-07-03): the local recall index landed as `influencer_os/recall_index.py` plus the `rebuild-index <creator-workspace> [--db <path>]` CLI command. One shared SQLite at the ADR 0010 path (`workspace-library/index/influencer-os.sqlite`); a rebuild deletes and reinserts only the named creator's rows, so rebuilds are idempotent and scoped. Rows carry the ADR 0010 provenance minimum (record id/type, creator profile id and slug, project id when applicable, workspace-relative source path, JSONL line number when applicable, sha256 content hash, indexed timestamp). Resolves every draft record kind — evidence and metric snapshots to path+line, finding ids to `findings.md` or stable-finding files (dual residence allowed by design), queue entries, promotions, projects, board cards — plus video understanding packs, added beyond the draft list because the structured evidence-ref shape names them. Bare-id ambiguity fails closed for every type except findings; malformed JSONL fails closed with path:line; a workspace outside the `creators/` layout must pass `--db` explicitly. The index stays a pure projection: no validation path reads it.

- Slice 4 batch C (2026-07-03): the Content Board projection landed as `influencer_os/boards.py` with `rebuild-board <creator-workspace>` and `validate board <creator-workspace>`. Cards are fully derived from canonical records: idea queue entries become parent cards, projects become child cards linked through their locked Idea Promotion (a project whose promotion or queue entry is missing fails the rebuild), card ids are deterministic (`card_<source_record_id>`), and active project warnings badge exactly the card they target — promoted-work warnings badge the project card, queue-level warnings badge the idea card, resolved warnings badge nothing, badges are unique severities ranked urgent → important → info. `columns` and `manual_order` are preserved projection metadata: rebuilds keep the existing arrangement, append new cards in canonical order, and drop stale ids. `validate board` fails a board whose cards disagree with canonical records, whose `manual_order` does not list every card exactly once, or whose board id does not derive from the workspace creator. Fixture correction: the example board had the promoted-work warning badging the parent idea card; the badge moved to the targeted project card per the ADR 0020 pairing rule (the example warning carries `project_id` + `idea_promotion_id`).

- Slice 4 batch D (2026-07-03, per the user-approved pruned-ids decision recorded in the slice plan): `prune <creator-workspace> [--apply] [--retention-days <n>]` landed as `influencer_os/prune.py`. Evidence is prunable only when it is older than the retention window (default 30 days), its id is unreferenced by every queue entry, promotion, and project source-ref cache, and none of its metric snapshots are referenced; its snapshots prune with it, and stale queue entries are never touched (staleness stays auditable). Dry-run by default — only `--apply` deletes, and an applied prune re-runs `validate research` as a post-check. Removals are recorded on the run manifest as optional `pruned_evidence_ids`/`pruned_metric_snapshot_ids` (new schema fields) while `outputs` stays untouched; outputs reconciliation now expects JSONL contents to equal outputs minus pruned, pruned ids must be declared and absent, so a run can still never misdeclare what it produced. Kept JSONL lines are rewritten byte-identical (original raw text, not reserialized). Metric-snapshot trajectory compaction stays deferred per the slice decisions.

- Slice 4 batch E (2026-07-03), closing the slice: the `create-research-findings` and `manage-idea-queue` producer skills landed under `skills/`, encoding the workflow doc's rules — run modes and the run lifecycle (folder==id, run-scoped records, exact outputs declaration), evidence-quality and platform-scoping rules, the material-update discipline (`last_ran` vs `last_updated`, char-limited topic-cluster findings with a Watch Now section), stable-finding promotion, intelligence updates with the user-approval gate for core reference creators, the eight-score queue-entry contract with structured run-scoped evidence refs, the variant and wildcard rules, auditable staleness, queue-level warnings, manifest consistency, and the projection maintenance commands. `manage-idea-queue` carries a hard no-promotion boundary: promotion stays the human-approval gate owned by `promote-idea` (slice 5), and the conductor halts there until it exists. Registry rows moved from Missing Future Skills to Core Workflow Skills, context-matrix Skill Coverage rows added (Social research / Idea generation), conductor dependency and phase-owner statuses plus the architecture-map skill table and call graph flipped to [BUILT], and `update-creators` propagated 13 runtime skills to all three fixture workspaces.

- Addressed the slice 4 review (2026-07-03; three P2 findings, all confirmed): `create-research-findings` now says a no-material run still updates `last_ran` in the findings frontmatter while leaving the body, `last_updated`, and finding fields unchanged (the previous "leaves findings.md alone" wording contradicted the workflow contract and would have produced valid-but-stale `last_ran` dates schema validation cannot catch); the same skill now requires all five run `outputs` arrays present and exact — `finding_ids`, `idea_queue_entry_ids`, and `research_intelligence_updates` were previously unmentioned, so a run touching findings or intelligence could validate while hiding that provenance behind empty arrays; and project warnings now fail closed on dangling targets via `check_project_warning_target_refs` (shared by `validate research` and board derivation) — the queue entry must always exist, and the project and promotion must exist for promoted-work warnings. Before the fix a warning naming a nonexistent target validated and silently vanished from the board projection. The base research test scaffold gained the example project (the example warning targets it), and three tests that delete warning targets now clear the warnings stream first so their intended failures fire.

- Addressed the slice 4 second review round (2026-07-03; two P2 and one P3, all confirmed): finding refs now resolve — queue `source_finding_ids` hard-fail and promotion `research_finding_ids` warn/fail (human/automated) against `collect_finding_ids`, the union of findings frontmatter, stable findings, and immutable run `outputs.finding_ids`; the union matters because findings legitimately rotate out of the char-limited rolling summary, so a rotated finding still resolves through the run that produced it while a ghost id fails (a bogus `finding_luna_fit_ghost` previously passed `validate queue` and `validate research`, leaving the Product Invariant's findings trace unenforced). Promoted-work warnings now check chain consistency, not just existence: the project's locked `source_refs.idea_promotion_id` must equal the warning's promotion and that promotion's `idea_queue_entry_id` must equal the warning's entry — before the fix a mismatched tuple validated and badged the wrong project card. And the queue manifest rejects duplicate `entry_refs` (the ref dict silently collapsed duplicates, letting `status_counts` count collapsed values).

- Slice 5 batch A (2026-07-03, per the user-approved Slice 5 Execution Decisions in `docs/workflows/research-and-ideas-implementation-plan.md`): promotion link consistency is enforced at rest, file-first, both directions. An `active` promotion requires its queue entry to be `promoted` and to back-link it in `linked_idea_promotion_ids` (`check_promotion_entry_links`, shared by the gate and `validate queue`); `superseded`/`cancelled` promotions impose no entry requirement, so the cancel-revert lifecycle validates. A `promoted` entry requires at least one resolvable linked promotion and exactly one active among them (zero means the entry should have reverted; two means scope expansion skipped the supersede rule), a non-promoted entry may link no active promotion, every `linked_idea_promotion_ids`/`linked_project_ids` value must resolve, and a linked promotion must name that entry. A promotion's `project_ids_created` must resolve to real projects whose `source_refs.idea_promotion_id` points back (the project-side closure already existed in `_resolve_promotion`). Project resolution now goes through `collect_project_manifests` — scanning `projects/*/project.json` by the manifest's `project_id` with duplicates failing closed — which also fixed the latent bug where `check_project_warning_target_refs` assumed id-named project folders and would have rejected any `init-project`-built (slug-foldered) project a warning targeted.

- Slice 5 batch B (2026-07-03): the `promote-idea` producer skill landed under `skills/`, owning conductor phases 5-6 — full-package presentation before any write (idea, payoff, platforms, formats split supported/pending, slots or wildcard, findings and structured evidence refs, score snapshot, creative elements, and the exact Projects to be created), explicit human approval of exactly that package (`approved_by: user`, no automated path), the locked promotion snapshot with `project_ids_created` declared up front, the construction order (promotion → `init-project` → evidence brief → entry/manifest flip → schedule slots → validate + rebuild), Projects only for production-supported formats with the `approval_intent_note` path when none is supported, schedule slots set to `filled` when claimed, and the supersede/cancel lifecycle rules (scope expansion supersedes, cancel reverts the entry when no active promotion remains, projects archive manually). Registry and context-matrix rows (new Idea promotion workflow row) landed in the same commit because the drift checks pin them to the skill folder.

- Slice 5 batch C (2026-07-03), closing the slice: conductor dependency and phase-owner statuses (phases 5-6), the architecture-map skill table and call graph, and the repository-map flow flipped to [BUILT]; `manage-idea-queue`'s halt text now hands off to the built gate instead of halting on a missing skill; `update-creators` propagated 14 runtime skills to all three fixture workspaces; the slice plan status and this progress record close the slice.

- Addressed the slice 5 review (2026-07-03; one P1 and two P2 findings, all confirmed by reproduction; decisions recorded in the slice plan): the promotion-to-project path is now closed entry-level — a `promoted` entry must link at least one resolvable project, every linked project's locked promotion must be among the entry's linked promotions, and every linked promotion's `project_ids_created` must appear in the entry's `linked_project_ids` (entry-level rather than a promotion-level minimum because an active supersede-expansion promotion legitimately creates no new project; before the fix an active supported-format promotion with `project_ids_created: []`, no project folders, and no entry links passed both validators). Schedule slot claims are enforced for active promotions — claimed `schedule_slot_ids` must resolve to real slots in `content-schedule.json`, claimed slots must be `filled`, and a slot may be claimed by at most one active promotion; superseded/cancelled promotions keep historical claims unchecked because the schedule is mutable planning state (the example schedule slot flipped from `open` to `filled`, fixing the shipped fixture that contradicted the skill rule). And the `promote-idea` skill's `init-project` invocation gained the required `--creator-workspace` flag — the documented form would have failed in argparse mid-construction, right after the promotion snapshot was written — pinned by a new drift test on the skill's command line.

- Addressed the five-slice review (2026-07-03; a whole-of-Phase-1 audit of slices 1-5 run after slice 5 closed, with every finding reproduced before its fix; records in the three slice plan docs): `import-intake` refuses symlinked destinations and escaping resolved paths before any write (a pre-planted broken symlink wrote through to a file outside the workspace); `validate workspace` fails duplicate intake ids/paths and duplicate reference-library asset ids at every status; fully anchored `^...$` schema patterns validate whole-string (closing the trailing-newline tolerance) and the intake/reference path pins reject dot segments; promotion checks were unified across the validator paths — `validate queue` now runs the full gate set (creator scope, filename==id, slot claims, warnings channel) and `validate research` runs the entry-side queue consistency, closing four reproduced queue-path bypasses and putting the slice 5 closure on the research path that `prune --apply` actually re-runs; `applied-social-template.target_format_id` joined the closed format enum with a plan-layer surface check (`format_interpretive_dance` previously passed `validate project`); within-run duplicate JSONL ids fail closed (they validated green but bricked `rebuild-index`); metric snapshots must snapshot evidence in their own run and evidence refs must cite snapshots of their own evidence; promotions require at least one evidence ref (Product Invariant trace); `prune --apply` pre-flights `validate research` before mutating; slot claims schema-validate the schedule (clean error instead of a `KeyError` from the `validate project` path); video pack refs resolve by the record's own id; stable findings follow filename==id with recall-index uniqueness; `validate project` pins the chain to the workspace creator; the approved-visual gate test isolates the gate; and the stale docs were refreshed (this file's verification script ran `validate queue` before the project existed, the architecture map's counts/ADR range/producer-status prose, and the slice 1 merged test names).

- Slice 6 (2026-07-04), format-specific production planning: `article-plan` and `thread-plan` schemas and examples landed; the closed format vocabulary now includes `format_article` and `format_thread`; `project.schema.json` accepts `article` and `thread` content unit types while keeping `multi_platform_package` deferred; `PRODUCTION_PLAN_SCHEMAS`, `PRODUCTION_PLAN_ID_FIELDS`, and `PRODUCTION_SUPPORTED_FORMATS` route article/thread projects as production-supported; project validation requires each Project's `content_unit_type` to map to exactly one matching target format; text Projects validate without `plan/generation-plan.json`; `apply-social-template` and `create-production-plan` producer skills landed and were wired through the conductor, registry, context matrix, architecture map, repository map, README, and pipeline contract.

- Addressed the slice 6 review follow-up (2026-07-04): `project.schema.json` now declares `target_formats.maxItems: 1` and documents the content-unit pairing invariant, so `validate record project` no longer gives a false green for multi-format project manifests; `_requires_generation_plan` keys off `content_unit_type` only, relying on the project invariant to keep target formats paired; and `AGENTS.md` now reflects that article/thread text formats are production-supported.

- Slice 7 (2026-07-04), Output Package registration: `register-output-package <output-package.json> --project <project-dir> [--asset-root <dir>]` landed as the local file-first write gate. It validates the Project and Output Package, requires package/project creator and promotion refs to match, copies `upload_ready` files from a mirrored asset root into `projects/<project-slug>/output-package/upload-ready/`, writes `output-package/output-package.json`, advances the Project to `packaged`, and rolls back the package/status/asset writes if final `validate project` fails. Output Package semantics now require upload asset refs to resolve, keep visual package thumbnail/first-frame refs mandatory, and allow `thumbnail_or_first_frame_asset_id: null` for article/thread text packages. The `create-output-package` producer skill landed under `skills/`, moved from Missing Future Skills into the Core Workflow Skills registry, gained Output packaging context coverage, and the conductor/architecture/repository docs flipped it to [BUILT].

- Addressed the slice 7 adversarial review (2026-07-04; one medium, one low, and one nit, all confirmed by reproduction): packaged project validation now re-checks the Output Package `universal_core.format_id` against the Project `content_unit_type`, so hand-edited packages cannot contradict the Project format at rest; `validate project` enforces that every packaged `upload_ready[].path` resolves to an existing local file, making `packaged` mean upload-ready deliverables exist; and registration rollback removes empty nested upload-ready directories created during a failed package write.

- Research-intelligence hardening (2026-07-04): added `ResearchSearchPlan`,
  `ResearchSourceYield`, and `docs/research-adapter-registry.md`, requiring
  completed research runs to record source-selection intent before browsing and
  source-yield outcomes after browsing. The slice adapts Agentic OS query
  routing and engagement-weighted source evaluation while preserving
  InfluencerOS schema-backed evidence/provenance. Heavy connectors remain
  planned/deferred: logged-in social access, scraping APIs, API-backed search,
  scheduled research, notifications, and YouTube as a first-class platform
  require separate pre-go-live decisions.

- Creator setup onboarding UX refinement (2026-07-04): `create-influencer`
  now starts with a plain-language onboarding briefing and exactly three entry
  paths: load existing files, guided interview, or generate from basic
  information, while keeping system-filled blanks in the review set. The setup
  workflow, personal-brand guidance, and reference-library skill now map public
  platforms to text/image/audio/video/carousel/story-sequence mediums and make
  medium-specific reference requirements explicit, including person reference
  image recommendation, recurring video locations, recurring collaborators, and
  identity-attached objects.

Deferred:

- Scheduled research automation remains deferred until the manual
  research-intelligence loop has been exercised against real creator runs. This
  is not a Phase 1 exit blocker.

### Phase 2: Learning OS

Goal: Capture publication records and analytics, attribute performance to creative stages, distill lessons, and make those lessons available through SQL and semantic lookup.

Status: Build slices complete — slices 1-6 landed 2026-07-05/06; remaining Phase 2 surfaces are explicitly deferred (analytics API connector on request per Decision 3; vector lookup leg with Command Centre per Decision 1).

Completed:

- API-primary analytics ingestion decision with manual and CSV fallback.
- Performance Attribution model for packaging, hook, body retention, payoff, and CTA.
- Durable creator memory policy: distilled lessons plus linked performance summaries.
- Schema contracts and examples through Performance Summary.
- Published Post Record registration (`register-published-post` CLI + skill, slice 1).
- Analytics Snapshot ingestion (`add-analytics-snapshot`/`import-analytics-csv` through one shared writer seam + `ingest-analytics` skill, slice 2).
- Performance Summary contract and interpretive skill with the Benchmark Rubric and stage-remediation mapping (slice 3).
- Learning distillation: `distill-creator-learning` skill + evidence-linked creator lessons via `log-learning --evidence --strength`, at-rest re-checked by `validate workspace` (slice 4).
- SQL recall-index extension to the three Phase 2 record types (slice 5).
- Semantic lookup projection: FTS5 keyword leg per Decision 1 (`semantic_lookup.py`, `rebuild-lookup`/`query-lookup`, creator-scoped, allowlist-only, reference chunker/reranker adapted; slice 6).

Remaining:

- Platform analytics API connector, only when explicitly requested (Decision 3; the shared writer seam is mock-proven).
- Vector leg of the lookup projection follows the reference exactly when Command Centre is un-deferred (Decision 1 phasing).

### Creative Direction Workstream (between Phase 2 and Phase 3)

Goal: Make creative intent first-class and continuous — the Content Beat Spine as the one template vocabulary, intent captured at the idea origin and resolved by reference, an advisory platform→modality→format capability model, and an advisory creative-review layer (ADR 0024).

Status: Complete (2026-07-06). All four slices landed with per-slice gpt-5.5 adversarial reviews and fix batches; the six runnable exit criteria pass (see Current Verification).

Completed:

- Slice 1 — Content Beat Spine + intent at the idea origin: required `beat_role` (`hook|retain|payoff|cta|packaging`) on `social-template.beat_sequence[]` and `applied-social-template.applied_beats[]` with optional `hook_category` (11-value taxonomy, hook-role beats only, Decision B); spine semantics (templates and applied templates must land hook + payoff; hook_category placement) in the validator; optional `intended_emotion`/`core_message` on `idea-queue-entry` and `idea-promotion` (schema-optional, skill-required) with a verbatim carry-forward check in the promotion gate; five named-framework presets seeded as validating records under `docs/templates/social-templates/` (PAS, Before/After-Bridge, Listicle, Myth→Truth, "I Tried X" — Decision C); `manage-idea-queue` captures intent via the "So What?" chain and `promote-idea` copies it verbatim; drift pins for the spine enums.
- Slice 1 review fixes: `validate workspace` now runs promotion validation (and surfaces its warnings), making the carry-forward check reachable from the exit criterion's named path; `apply-social-template` documents the beat_role contract.
- Slice 2 — carry-through and performance alignment: `micro-journey-video-plan` restructured to the spine as a clean break (Decision D: `hook`, `retain{setup,escalation}`, `payoff`, `cta_or_loop`, `intended_emotion`); `validate project` fails a production plan whose `intended_emotion` overrides the locked promotion (intent resolves by reference); performance summaries must record an unplanned CTA as `result: "not_used"` (`minItems:5` holds), aligned to the applied template's `beat_role` beats; fixtures migrated.
- Slice 2 review fixes: plan records validate whenever they exist (a premature plan on a `created` project cannot dodge the no-override check); applied templates must cover hook + payoff so those stage findings always attribute; `validate_promotions` collects the research corpus once per sweep; stale micro-journey wording purged from the HTML map.
- Slice 3 — platform, modality, and subtype sharpening: `primary_surfaces` constrained to the canonical 8-platform enum (Decision A: canonical constant in `validation.py`, drift-pinned across every schema and code copy); `content_mediums` reduced to the pure modality enum `[text,image,video,audio]` with the medium-based readiness blockers re-keyed; audio selectable with a standalone-audio advisory warning ("no audio plan schema yet"); optional `format_subtype` seeded on article/carousel/thread plans; `init-project` appends an advisory `platform_fit` ProjectWarning (`native|subtype|analog|none`, dated 2026-07-06 capability map in code, numeric limits doc-side only) that never blocks.
- Slice 3 review fixes: the platform-fit advisory is best-effort (cannot fail `init-project`) and idempotent per project; the off-surface test asserts the appended warning passes full at-rest research validation.
- Slice 4 — reviews first slice: lean `review-record.schema.json` (spine-keyed findings, `reviewer_execution` independence fields, `human_waiver` requiring a blocking finding, fallback_reason pairing); `docs/gates-and-reviews.md` as the canonical control contract (Gate/Review/Pass/Warning, control order, advisory rule + must-acknowledge real-world-risk carve-out, blocking-promotion ADR checklist) added to the AGENTS.md source-of-truth list; skills `review-hook-payoff` (advisory ReviewRecord), `clear-writing-pass` and `human-voice-pass` (bounded rewrites with change trace, no record) with registry, context-matrix, and conductor rows; `project_paths` gains `reviews/`; `validate project` checks review records at rest and surfaces an unwaived `block` as a warning only — the advisory probe test proves a block halts nothing (and `validate project` is the packaging preflight, so packaging cannot be halted by construction).
- Guard rules held: no creative Review, Pass, or Warning blocks any pipeline step (per-slice advisory probes); nothing touched `influencer_os/providers/` (which still does not exist) or any generation-approval surface.

### Phase 3: Generation OS

Goal: Generate or import media assets from approved providers, assemble final output packages, and preserve provenance and approval boundaries.

Status: Complete (2026-07-06). ADR 0023 recorded (the five execution decisions approved on their plan recommendations via the operator's directive to implement all of Phase 3); all five slices landed with three batch-boundary gpt-5.5 adversarial reviews and fix batches; the five runnable exit criteria pass (see Current Verification). Per Decision 3, the mock adapter is the only installed adapter — the first real (paid) provider adapter remains a separate operator-chosen batch.

Completed:

- Slice 1 — provider registry and adapter boundary: `influencer_os/providers/` as the sibling of the ADR 0022 connector tier under the opposite approval model — every registry row is structurally `approval_model: exact_approval` (import fails closed otherwise), key presence is availability never approval, `dispatch_generation` is the only adapter entry point and requires an approved GenerationApprovalRecord id positionally, and the `INFLUENCER_OS_DISABLE_PAID_CONNECTORS` kill switch overrides everything; `list-providers` CLI; deterministic mock adapter only.
- Slice 2 — generation approval records: `generation-approval-record` schema (ladder `draft -> approved -> executing -> executed | cancelled`, `single_call`/bounded `batch` scopes, verbatim `user_approval_statement`, per-status field semantics, results must equal the approved request exactly); `record-generation-approval` CLI resolves refs before writing (project at `ready_for_generation`+, plan/prompt refs inside the project, reference assets resolving) and refuses overwrites; `request-generation-approval` skill packages the exact call/batch while the gate stays human; `project_paths` gains `generation/`; at-rest parity in `validate project` and `validate workspace` (reference-scope approvals under `references/approval-records/`).
- Batch 1 review fixes: env-read kill switch (config injection can never re-enable), one shared record→project binding contract (writer, dispatch, at-rest), two-phase `approved -> executing -> executed` consumption with leftover `executing` records refusing re-dispatch and warning at rest, bare-filename containment, prompt_refs must point into the approved plan_ref.
- Slice 3 — import-generated-asset: external/user media enters `generation/assets/` with a full-provenance manifest row (tool-image-search-style source/license/attribution/warnings; unknown license captured as a warning, never guessed); `--reference-asset` route updates the Reference Library source block and lifecycle per ADR 0013; copy rolled back if the ledger append fails.
- Slice 4 — asset provenance ledger: `generation-asset-manifest` schema (generated rows bind approval + plan prompt + provider call; imported rows carry import origin; shapes mutually exclusive); dispatch appends rows before consuming the approval; `validate project` reconciles assets ↔ ledger bidirectionally (orphan files, dangling artifacts, tampered content hashes, unexecuted or non-listing approvals all fail); `output-package.upload_ready[]` media require `generation_manifest_ref` once `generation_status` leaves `planned_not_generated`, resolved to ledger rows at rest; `rebuild-index` projects approval records and manifest assets through the shared validation seams.
- Batch 2 review fixes: O_EXCL-locked compare-and-swap for `approved -> executing` (concurrent dispatch cannot double-consume), symlink/containment hardening across the generation tree and reference-import destinations, flat assets dir (no hidden subdirectory files), manifest rows must restate the approved request (kind/prompt/provider/model), packaged role→kind lineage, `generation_status` must agree with referenced row origins.
- Slice 5 — quality gate: `quality-review` schema (closed four-check checklist — identity consistency, continuity with plan, technical conformance, creator boundary compliance — each exactly once; verdict must agree with the items); `review-generated-assets` skill owns the one BLOCKING review layer; `register-output-package` and `validate project` refuse packaged generation-sourced media without a passing QualityReview (text roles exempt); a `generated` project with ledger assets and no review draws an advisory warning; `docs/gates-and-reviews.md` updated — the blocking layer reserved by ADR 0024 now exists.
- Guard rules held every slice: no code path dispatches without an approved record (probed), the suite never instantiates a real provider adapter (mock only, CI-safe, zero paid calls), and generation approval gates were never weakened — key presence remains research-tier-only standing approval (ADR 0022 carve-out unchanged).

Deliberately open (by decision, not omission): the first real provider adapter (Decision 3 — operator's pick, its own approved batch); scheduled/unattended generation stays Phase 4.

Status: Deferred.

Completed:

- Provider boundary documented.
- Output Package supports generated or imported assets.
- Reference Library supports reusable character, location, outfit, object, video style, voice, and brand assets.

Remaining:

- Provider adapter boundary.
- Generation approval workflow.
- Image/video/audio/render provider integrations.
- Asset provenance capture.
- Quality checks before packaging.

### Phase 4: Improvement OS

Goal: Close the Performance Delta loop (Creative Performance Map predictions
vs measured analytics, feeding Creator Memory) and the Production Quality
loop (creation friction feeding skill and routine updates), with a
falsifiable criterion at every step.

Status: Complete (2026-07-06). Rescoped from "Automation OS" (ADR 0025) after
the Phase 4 readiness grilling session — temporal scheduling moved to the
roadmap Deferred section. All five slices landed as three gpt-5.5-reviewed
batches with fix batches; the six runnable exit criteria pass (see Current
Verification). Blocking-criterion promotions remain future per-criterion ADRs
per the gates-and-reviews checklist.

Completed:

- Slice 1 — Production Rubric substrate: `production-rubric` records with
  scoped binary criteria (ids double as recurrence keys; maturity
  minted/proven/blocking/retired; blocking requires a resolvable ADR ref),
  friction fields on the system-event ledger (a rejection cites exactly one
  of a criterion or unclassified — the Rubric Ratchet, enforced at the
  writer and at rest through one shared seam), `log-incident` and
  `mint-criterion` CLI, OS rubric seeded from the quality-review categories,
  workspace rubric scaffolded by `init-creator` and required by the
  workspace schema, friction-logging rules in the four producing skills,
  enum drift pins.
- Slice 2 — event-driven reflection trigger: reflection runs reuse the
  dormant automation-run schema as declare-then-attest for reflection
  itself (claimed event_ids reconcile both directions; failed runs must
  attest none), unprocessed-friction thresholds (recurrence K, total N,
  unclassified rubric-gap U; workspace-tunable, drift-pinned) surface
  advisory warnings from `validate workspace` and `check-reflection` —
  advisory by construction.
- Slice 3 — improvement claims + `distill-production-learning`: claims name
  target skill, criterion, baseline evidence, and a violation ceiling;
  writes fail closed (criterion/evidence/skill/supersedes all resolve;
  baseline must be the claim's own friction); violations counted
  mechanically, a human closes (D5); the skill owns Loop B end-to-end and is
  registered across conductor/registry/matrix/architecture map; `wrap-up`
  gained the friction audit and claim close-out.
- Slice 4 — falsifiable predictions: optional per-stage `prediction`
  (metric, comparator, threshold) on the Creative Performance Map, scored
  confirmed/refuted/unmeasurable in performance summaries; pairing
  fail-closed both directions in the summary↔package seam; measured values
  must come from a cited snapshot's matching metric (stage-keyed lookup);
  visual and text fixtures probed.
- Slice 5 — criteria maturity ladder: `rubric_criteria_results` beside the
  closed quality checklist; unknown criteria fail closed; a failing blocking
  criterion forbids a passing verdict at the seam while advisory criteria
  gate nothing (never-blocks probe); blocking coverage is required for
  passing coverage, criteria collected with the owning workspace's scope and
  a missing creator rubric fails closed; the proven→blocking promotion path
  is documented in `docs/gates-and-reviews.md`.
- Review fixes: batch 1 (failed-run claims escaping reconciliation,
  unresolved blocking_adr, optional rubric pin, multiline ledger messages +
  maxLength joining the fail-closed validator subset), batch 2 (unbound
  prediction scoring including a unit-mismatched exemplar; unbound claim
  baselines), batch 3 (advisory rubric fails forcing failing verdicts
  through the packaging gate; unscoped/skippable criteria collection).

Deliberately deferred (by decision, not omission): cross-creator OS-scope
criterion aggregation, creator-scoped claims, a closed prediction-metric
vocabulary, and a board surface for reflection-due (plan §Deliberately
Deferred Remainders); temporal scheduling per ADR 0025.

### Post-Phase-4: Live Testing And Multi-Entity Onboarding

Goal: exercise the completed OS against real data, and broaden onboarding from
avatar-led influencers to products and brands.

Status: opened 2026-07-07. All four build phases (0–4) plus Creative Direction
are complete and were validated against disposable fixtures and the
deterministic mock generation adapter only; nothing has yet run against real
creator data or a real (paid) provider.

Two parallel tracks (see the roadmap Post-Phase-4 section):

- Track 1 — Live testing (influencers first): the influencer path works today.
  Onboard real influencers, wire ADR 0022 research API keys (`.env`), exercise
  the manual research-intelligence loop against real data (ADR 0022 "run 2"),
  and decide the first real provider adapter (Generation OS Decision 3).
- Track 2 — Multi-entity onboarding (ADR 0026): add a required `creator_type`
  discriminator (`influencer | product | brand`) that conditions the required
  foundation documents, reusing the medium-based blocker mechanism. "Creator"
  becomes the umbrella term; the `creator_*` plumbing and downstream schemas
  are unchanged. Build slices are tracked in
  `docs/workflows/multi-entity-onboarding-implementation-plan.md`.

Completed:

- ADR 0026 recorded (2026-07-07); `CONTEXT.md`, PRD scope, and the roadmap
  updated to multi-entity umbrella scope. No code changes yet.
- ADR 0027 YouTube Data API research connector (2026-07-07): `youtube` joined
  the canonical research platform set (with `youtube_video`/`youtube_short`/
  `youtube_comment` content types across all pinned schema enum copies),
  `youtube_data_api` is standing-approved and key-gated (`YOUTUBE_API_KEY`),
  and `research-fetch youtube-search` emits validated fetch results. Live
  smoke fetch validated against the real API (3 candidates, 2 paid calls).
  Transcripts/analytics/publishing stay out of scope; video-content analysis
  keeps the VideoUnderstandingPack boundary. Verification: 747 tests pass,
  49 examples validate.
- Skill quality remediation (2026-07-07): a five-perspective review of all
  28 `skills/*/SKILL.md` files (four Claude cluster reviews + a gpt-5.5
  audit against the operator's writing-great-skills rubric) found seven
  verified content defects — all inside duplicated prose — and one
  repo-wide mechanical defect (14 frontmatters invalid under strict YAML).
  Executed as three gpt-5.5-review-gated batches per
  `docs/workflows/skill-quality-remediation-implementation-plan.md`:
  mechanical fixes + 9 new skill-prose drift tests (frontmatter scalar
  lint, path existence, vocabulary-vs-enum, template IDs, CLI forms,
  shared-block byte-identity), conductor/parent de-duplication
  (`influencer-os` 248→187 lines; producer record shapes live only with
  their owners), and the description/completion-criteria pass (all 28
  descriptions trimmed to registry-aligned trigger clauses; setup
  subskills now name their machine checks and the acceptance gate).
  Verification: 794 tests pass, 49 examples validate, all 28 frontmatters
  parse under js-yaml.

## Implemented Schema Contracts

- `creator-workspace.schema.json`
- `creator-profile.schema.json` v2
- `reference-library.schema.json`
- `project.schema.json`
- `output-package.schema.json`
- `published-post-record.schema.json`
- `analytics-snapshot.schema.json`
- `performance-summary.schema.json`
- Research, idea, template, and format-specific production records, including
  `micro-journey-video-plan.schema.json`, `carousel-plan.schema.json`,
  `single-image-post-plan.schema.json`, `story-sequence-plan.schema.json`,
  `article-plan.schema.json`, and `thread-plan.schema.json`.

## Current Verification

Phase 4 (Improvement OS) closeout run (2026-07-06) — the six runnable exit
criteria plus the fixture sweep and live CLI probes:

```bash
python3 -m unittest discover -s tests                       # 739 tests OK
python3 -m influencer_os validate examples                  # 49 records
python3 -m unittest tests.test_improvement_os               # EC 1-6 (61 tests)
python3 -m unittest tests.test_drift_checks                 # enum/threshold pins
for w in workspace-library/creators/*/; do python3 -m influencer_os validate workspace "$w"; done
python3 -m influencer_os check-reflection <creator-workspace>   # reporting only
python3 -m influencer_os check-claims                           # reporting only
# scheduler scan: no cron/scheduler files ship (EC6) — PASS 2026-07-06
```

Phase 3 (Generation OS) closeout run (2026-07-06) — the five runnable exit
criteria plus a live full-workflow replay (approval → mock dispatch → import
→ quality review → packaging) on the luna-fit fixture creator:

```bash
python3 -m unittest discover -s tests
python3 -m influencer_os validate examples
python3 -m influencer_os list-providers
python3 -m unittest tests.test_providers            # exit criteria 1-5
for w in workspace-library/creators/*/; do python3 -m influencer_os validate workspace "$w"; done
python3 -m influencer_os validate project workspace-library/creators/remy-vale/projects/pothos-drowning-rescue
# full replay: .tmp/generation-os/closeout.sh (ALL PHASE 3 EXIT CRITERIA GREEN, 2026-07-06)
```

Creative Direction closeout run (2026-07-06) — the six exit criteria
demonstrated on the luna-fit fixture creator plus the workspace-library
sweep and a full-workflow replay (idea → promotion → template → plan →
performance summary → block-status review validating advisory):

```bash
python3 -m unittest discover -s tests
python3 -m influencer_os validate examples
python3 -m unittest tests.test_creative_direction tests.test_drift_checks   # exit criteria 1-6
for w in workspace-library/creators/*/; do python3 -m influencer_os validate workspace "$w"; done
python3 -m influencer_os validate project workspace-library/creators/remy-vale/projects/pothos-drowning-rescue
# full replay + advisory probe: .tmp/creative-direction/closeout.sh (ALL EXIT CRITERIA GREEN, 2026-07-06)
```

Latest verified commands:

```bash
python3 -m unittest discover -s tests
python3 -m influencer_os validate examples
python3 -m unittest tests.test_drift_checks -v
.tmp/slice6-verify.sh
if rg -n 'workspace-library/creators/<creator-slug>/skills|Skill Runtime And Propagation Decision|Resolve skill runtime layout|Creator Workspace propagation/sync decisions|needs decision|Reject for v1' docs/os-construction docs/creator-workspace-structure.md docs/pipeline-contract.md ARCHITECTURE.md AGENTS.md README.md -g '!docs/os-construction/adversarial-review.md' -g '!docs/os-construction/progress.md'; then exit 1; else exit 0; fi
```

Full workflow verification (projects anchor on the locked Idea Promotion, and
the research module validates end to end):

```bash
python3 -m unittest discover -s tests
python3 -m influencer_os validate examples
python3 -m influencer_os init-creator examples/creator-workspace.example.json --workspace-root .tmp/creators
cp examples/creator-profile.example.json .tmp/creators/luna-fit/creator-profile.json
cp examples/reference-library.example.json .tmp/creators/luna-fit/references/reference-library.json
cp examples/sources/luna-fit-breakdown.example.md .tmp/creators/luna-fit/sources/intakes/luna-fit-breakdown.md
cp examples/video-understanding-pack.example.json .tmp/creators/luna-fit/research/video-understanding-packs/video_research_luna_fit_001.json
cp examples/creator-content-schedule.example.json .tmp/creators/luna-fit/content-schedule.json
mkdir -p .tmp/creators/luna-fit/research/runs/research_run_luna_fit_2026_07_03_001
cp examples/research-run.example.json .tmp/creators/luna-fit/research/runs/research_run_luna_fit_2026_07_03_001/research-run.json
cp examples/research-search-plan.example.json .tmp/creators/luna-fit/research/runs/research_run_luna_fit_2026_07_03_001/search-plan.json
python3 -c "import json; print(json.dumps(json.load(open('examples/research-evidence.example.json'))))" > .tmp/creators/luna-fit/research/runs/research_run_luna_fit_2026_07_03_001/evidence.jsonl
python3 -c "import json; print(json.dumps(json.load(open('examples/metric-snapshot.example.json'))))" > .tmp/creators/luna-fit/research/runs/research_run_luna_fit_2026_07_03_001/metric-snapshots.jsonl
python3 -c "import json; print(json.dumps(json.load(open('examples/research-source-yield.example.json'))))" > .tmp/creators/luna-fit/research/runs/research_run_luna_fit_2026_07_03_001/source-yield.jsonl
mkdir -p .tmp/creators/luna-fit/research/intelligence .tmp/creators/luna-fit/research/stable-findings .tmp/creators/luna-fit/system
cp examples/research-sources.example.json .tmp/creators/luna-fit/research/intelligence/sources.json
cp examples/research-hashtags.example.json .tmp/creators/luna-fit/research/intelligence/hashtags.json
cp examples/research-search-terms.example.json .tmp/creators/luna-fit/research/intelligence/search-terms.json
cp examples/reference-creators.example.json .tmp/creators/luna-fit/research/intelligence/reference-creators.json
cp examples/research-watchlist.example.json .tmp/creators/luna-fit/research/intelligence/watchlist.json
python3 - <<'PY'
import json
from pathlib import Path

def frontmatter(data):
    lines = ["---"]
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            lines.extend(f"  - {item}" for item in value)
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n"

root = Path(".tmp/creators/luna-fit")
findings = json.load(open("examples/research-findings.example.json"))
stable = json.load(open("examples/stable-finding.example.json"))
(root / "research/findings.md").write_text(
    frontmatter(findings)
    + "\n## Desk resets\n\nLunch-break resets are outperforming baselines this week.\n"
)
(root / "research/stable-findings/stable_finding_luna_fit_001.md").write_text(
    frontmatter(stable) + "\nDesk resets are a durable topic cluster for Luna.\n"
)
PY
cp examples/idea-queue.example.json .tmp/creators/luna-fit/research/idea-queue/queue.json
cp examples/idea-queue-entry.example.json .tmp/creators/luna-fit/research/idea-queue/entries/idea_queue_entry_luna_fit_001.json
cp examples/idea-promotion.example.json .tmp/creators/luna-fit/research/idea-promotions/idea_promotion_luna_fit_001.json
python3 -c "import json; print(json.dumps(json.load(open('examples/project-warning.example.json'))))" > .tmp/creators/luna-fit/system/project-warnings.jsonl
python3 -c "import json; print(json.dumps(json.load(open('examples/system-event.example.json'))))" > .tmp/creators/luna-fit/system/creator-events.jsonl
echo "# Interview Notes (synthetic)" > .tmp/luna-interview.md
python3 -m influencer_os import-intake .tmp/luna-interview.md --creator-workspace .tmp/creators/luna-fit --source-type interview --notes "Follow-up interview transcript."
python3 -m influencer_os set-intake-status .tmp/creators/luna-fit source_luna_fit_interview_001 drafted
python3 -m influencer_os validate workspace .tmp/creators/luna-fit
# The project must exist before research/queue validation: the example
# promotion lists it in project_ids_created, and the slice 5 closure check
# (five-slice review: enforced on both validator paths) rejects a promotion
# whose created projects are missing.
python3 -m influencer_os init-project examples/project.example.json --creator-workspace .tmp/creators/luna-fit
cp examples/applied-social-template.example.json .tmp/creators/luna-fit/projects/tiny-reset-after-laptop-day/plan/applied-template.json
cp examples/micro-journey-video-plan.example.json .tmp/creators/luna-fit/projects/tiny-reset-after-laptop-day/plan/production-plan.json
cp examples/base-video-generation-plan.example.json .tmp/creators/luna-fit/projects/tiny-reset-after-laptop-day/plan/generation-plan.json
python3 -m influencer_os validate research .tmp/creators/luna-fit
python3 -m influencer_os validate queue .tmp/creators/luna-fit
python3 -m influencer_os validate project .tmp/creators/luna-fit/projects/tiny-reset-after-laptop-day
python3 -m influencer_os validate record output-package examples/output-package.example.json
mkdir -p .tmp/package-assets/output-package/upload-ready
python3 -c "import json, pathlib; package=json.load(open('examples/output-package.example.json')); root=pathlib.Path('.tmp/package-assets'); [((root / asset['path']).parent.mkdir(parents=True, exist_ok=True), (root / asset['path']).write_text(asset['upload_asset_id'] + '\n')) for asset in package['upload_ready']]"
python3 -m influencer_os register-output-package examples/output-package.example.json --project .tmp/creators/luna-fit/projects/tiny-reset-after-laptop-day --asset-root .tmp/package-assets
python3 -m influencer_os validate project .tmp/creators/luna-fit/projects/tiny-reset-after-laptop-day
python3 -m influencer_os rebuild-board .tmp/creators/luna-fit
python3 -m influencer_os validate board .tmp/creators/luna-fit
python3 -m influencer_os rebuild-index .tmp/creators/luna-fit --db .tmp/creators/index.sqlite
python3 -m influencer_os prune .tmp/creators/luna-fit
python3 -m influencer_os update-creators --workspace-root .tmp/creators
```

Latest validation result (2026-07-06 full Phase 2 review):

```text
Ran 527 tests in 10.658s
OK
Validated 43 example records.
Drift checks: 22 tests pass.
Stale-path/doc scan: no stale old creator-skill runtime paths found outside
historical adversarial-review/progress notes.
Phase 2 replay: .tmp/slice6-verify.sh passed end to end — creator init through
publication registration, analytics snapshot ingestion, performance summary,
creator lesson, recall-index rebuild/delete-and-rebuild, semantic lookup
rebuild/query/delete-and-rebuild, board validation, and prune dry-run.

Historical verification trail:
Ran 96 tests in 1.385s
OK
Validated 20 example records.
Full workflow verification above re-run end to end after the Batch C changes.
Batch D dogfood: log-learning appended a real dated entry to
context/learnings.md; context/MEMORY.md at 1,330/2,500 bytes.
Batch E mutation probe: removing a dependency from the conductor frontmatter
makes the call-graph drift check fail naming the missing skill.
Drift checks: 10 tests pass; planting an unregistered skills/ folder makes the
registry and matrix checks fail, confirming the checks catch real drift.
Validator hardening: 18 new tests cover $ref/oneOf/anyOf/allOf enforcement,
fail-closed unknown keywords/formats/types, and disk-derived example coverage
(a schema without an example now fails validation).
No stale old creator-skill runtime paths found outside historical adversarial-review notes.
Phase 0C exit (2026-07-03): every roadmap exit criterion re-run end to end and
passing — the full test suite (86 tests at the exit run; grown by the
post-closeout re-review fixes since), 20 example records, 18 drift checks, full
workspace/project/record workflow incl. update-creators (11 skills synced,
11 backed up), and the stale-path check.
Phase 1 slice 1 (2026-07-03): 107 tests pass (13 new in
tests/test_intake_import.py); 20 example records validate; the full workflow
verification above re-run end to end with the import-intake dogfood
(source_luna_fit_interview_001 imported, moved to drafted, workspace
validated with 25 checked paths); `rg -n "no master intake import command"
docs/workflows/creator-setup.md` finds nothing.
Slice 1 adversarial fixes (2026-07-03): 113 tests pass (4 new negative
tests); both review probes re-run against the fixes — an escaping or
absolute intake path is rejected with the containment error, and
import-intake --imported-on 2026-99-99 fails with "not a real calendar
date".
Schema pinning follow-up (2026-07-03): 114 tests pass; traversal, absolute,
wrong-directory, and nested intake paths fail record validation at the
schema seam; a symlinked intake resolving outside the workspace fails the
behavioral containment check; 20 example records validate.
Phase 1 slice 2 (2026-07-03): 132 tests pass (16 new in
tests/test_readiness_validation.py plus reference-library schema-pin
tests); 20 example records validate; dogfood run — the verification
workspace flipped to content_ready without population fails listing all 13
blockers in one error, and validates after foundation text and
asset/prompt files are placed; the full workflow verification (draft
status) passes unchanged.
Slice 2 adversarial fixes (2026-07-03): 140 tests pass; both review probes
re-run against the fixes — a video creator with empty/mistyped primary
reference_refs and a workspace with dangling asset source_ref values are
rejected with readiness blockers.
Phase 1 slice 3 (2026-07-03): 161 tests pass (11 research-validation tests,
4 promotion-gate tests, the date-time format tests, and the research enum
drift check among them); 38 example records validate (18 new); the full
workflow verification above re-run end to end — workspace (27 checked
paths), research state (6 records), idea queue (1 entry), and the
promotion-anchored project (10 checked paths) all validate with zero
promotion-gate warnings, since the fixture run evidence resolves; the three
live fixture workspaces validate after migration.
Slice 3 review hardening (2026-07-03): 177 tests pass (16 added, all
review findings reproduced as failing probes before the fix — an
unresolvable video pack ref, a lone `project_id` warning, a mismatched
run folder, stale `status_counts`, malformed run JSONL, and the six
promotion failure paths in `projects.py`); 38 example records and the
three live fixture workspaces still validate unchanged.
Slice 3 second review round (2026-07-03): 184 tests pass (8 added); the
reviewer's probe — a workspace whose schedule, run, queue, and promotion
records all claim `creator_other` — is rejected by `validate research`
and `validate queue`; a `multi_platform_package` project is rejected at
the schema; 38 example records and the three live fixture workspaces
still validate unchanged.
Approval surface decisions (2026-07-03): 189 tests pass (5 added — the
closed format enum across five schemas, the no-supported-format gate,
the unapproved target-format and platform-surface project checks, and
the code-constant drift pins); 38 example records and the three live
fixture workspaces still validate unchanged.
Video understanding tool integration (2026-07-03): 189 tests pass; drift
checks pass (21 tests); 38 example records validate. The integration is
documentation/skill-boundary only: `/watch` is supported as an external
acquisition tool for Video Understanding Packs, with no vendored scripts,
hooks, command launchers, or provider-backed transcription by default.
Watch integration review fixes (2026-07-03): docs-only; 189 tests still
pass, drift checks pass (21 tests). Upstream flag facts (`--no-whisper`,
`--out-dir`, `--start`/`--end`, MIT license, auto Whisper fallback and
first-run setup prompt) verified against the upstream repo.
Slice 4 batch A (2026-07-03): 199 tests pass (10 added, each check
reproduced failing before the fix); drift checks pass (21 tests); the
three live fixture workspaces pass `validate research` under the new
run-scoped checks (`validate queue` stays not-applicable — no fixture
workspace has an idea queue yet; queues arrive with this slice's
workflow).
Slice 4 batch B (2026-07-03): 208 tests pass (9 added in
`tests/test_recall_index.py`); drift checks pass (21 tests);
`rebuild-index` runs cleanly against the three live fixture workspaces
at the default ADR 0010 path (0 rows each — correct: no fixture has
research runs, queues, or projects yet).
Slice 4 batch C (2026-07-03): 222 tests pass (14 added in
`tests/test_boards.py`); drift checks pass (21 tests); 38 example
records validate after the board-badge fixture correction; the
derivation reproduces the example board fixture exactly, and
`rebuild-board` + `validate board` run cleanly against a live fixture
workspace (empty board, 0 cards).
Slice 4 batch D (2026-07-03): 232 tests pass (10 added in
`tests/test_prune.py` — retention, protection, dry-run isolation,
idempotence, pruned-ids reconciliation positive and negative); drift
checks pass (21 tests); a pruned workspace passes `validate research`
and `validate queue`; `prune` dry-runs cleanly against a live fixture
workspace (nothing to prune).
Slice 4 batch E (2026-07-03): 232 tests pass; the three registry/matrix
drift failures that fired when the skill folders landed were closed by
the registry, matrix, conductor, and architecture-map updates (the
drift checks work); `update-creators` synced 13 runtime skills into all
three fixture workspaces with zero overrides lost. Slice 4 complete.
Slice 4 review fixes (2026-07-03): 234 tests pass (2 added — dangling
queue-entry and project warning targets); drift checks pass (21 tests);
the three live fixture workspaces still pass `validate research`;
updated skill files re-synced to all fixtures.
Slice 4 second review round (2026-07-03): 241 tests pass (7 added —
dangling and rotated finding refs for queue and promotion, warning
chain-consistency mismatches, duplicate manifest refs; each reproduced
failing first); drift checks pass (21 tests); the three live fixture
workspaces still pass `validate research`.
Slice 5 batch A (2026-07-03): 254 tests pass (13 added in
`PromotionLinkConsistencyTests` — 12 reproduced failing first, plus the
positive cancel-revert pin; the slug-foldered project regression test
proved the latent warning-target bug before the fix); drift checks pass
(21 tests); 38 example records validate (the example
entry→promotion→project chain was already bidirectionally consistent);
the three live fixture workspaces still pass `validate research`.
Slice 5 batch B (2026-07-03): 254 tests pass; the skill folder landed
with its registry row (moved out of Missing Future Skills) and the new
Idea promotion context-matrix row in one commit, keeping the
registry/matrix drift checks green.
Slice 5 batch C (2026-07-03): 254 tests pass; drift checks pass with
the conductor and architecture-map statuses flipped to [BUILT];
`update-creators` synced 14 runtime skills into all three fixture
workspaces with zero overrides lost. Slice 5 complete.
Slice 5 review fixes (2026-07-03): 262 tests pass (8 added — 6 closure
and slot negatives reproduced failing first, the positive
historical-slot-claim pin, and the skill CLI-invocation drift test); the
P1 zero-project repro now fails `validate queue`; the CLI project test
scaffold gained `content-schedule.json` (scaffolds mirror real
workspaces — the promotion claims a slot, so the workspace carries the
schedule); 38 example records validate after the slot fixture flip; the
three live fixture workspaces still pass `validate research`; updated
skill re-synced to all fixtures.
Five-slice review fixes (2026-07-03): 287 tests pass (25 added — every
behavioral finding reproduced as a failing probe before its fix: symlink
write-through and duplicate ids for slices 1-2, six pattern-seam
negatives, six queue-path parity probes, six record-linkage probes, the
off-target template format, the foreign-chain project pin, and the prune
pre-flight); drift checks pass (22 tests, enum pins extended to
applied-social-template with no-enum-drop detection); 38 example records
validate; the three live fixture workspaces pass `validate workspace`
and `validate research`; the reordered full workflow verification above
re-run end to end, now covering rebuild-board, validate board,
rebuild-index (8 records), and prune dry-run alongside the original
commands (14 skills synced).
Slice 6 (2026-07-04): 292 tests pass (5 added for text format schema
support, promotion-gate support, article/thread project validation
without generation plans, and the unit-type/target-format mismatch);
drift checks pass (22 tests); 40 example records validate; the three
live fixture workspaces pass `validate workspace` and `validate
research`; `update-creators` synced 16 runtime skills into all three
fixture workspaces with zero overrides lost. Full workflow verification
re-run in `.tmp/slice6-verify`: workspace, research, queue, project,
output-package record, board, recall index (8 records), prune dry-run,
and copied-runtime sync all pass.
Slice 7 (2026-07-04): 303 tests pass (11 added for output-package
registration, rollback on package/project mismatch, text-package
registration without a generation plan, nullable text thumbnails, and
upload asset-ref, adaptation-format, at-rest package/project format,
at-rest upload-ready file presence, and rollback directory cleanup
semantics); drift checks pass (22 tests); 40 example
records validate. Full workflow verification re-run in
`.tmp/slice7-verify`: workspace, research, queue, project,
`register-output-package`, packaged project validation, rebuild-board,
and validate-board all pass. `update-creators` synced 17 runtime skills
into all three fixture workspaces with zero overrides lost.
Slice 7 review fixes (2026-07-04): 307 tests pass (4 added for
output-package registration hardening); 40 example records validate.
`register-output-package` now rejects symlinked package and upload-ready
write targets before writing outside the project, rejects `draft` packages
without marking the Project `packaged`, and requires platform adaptation
caption/description paths to resolve to declared `upload_ready` files. The
example output package now declares the YouTube description file it
references.
Phase 1 closeout verification (2026-07-04): 321 tests pass; 42 example
records validate; drift checks pass (22 tests); the stale-path check passes.
The full Planning OS workflow replayed in `.tmp/phase1-verify`: creator
initialization, intake import/status transition, workspace validation,
research run with `search-plan.json` and `source-yield.jsonl`, research
intelligence files, findings/stable findings, idea queue, human-approved
promotion, project creation, applied template, production plan, provider-neutral
generation plan, output package registration with upload-ready assets, packaged
project validation, board rebuild/validation, recall-index rebuild, prune
dry-run, and copied-runtime sync all pass. The replay checked 27 workspace
paths, 17 research records, 1 queue entry, 11 packaged project paths, 2 board
cards, and 11 recall-index records.
Phase 1 user-journey regression (2026-07-04): `tests/test_user_journey.py`
codifies the normal local-first Planning OS path from new Creator Workspace
setup through packaged Project output, using CLI gates for user-facing workflow
boundaries and fixture file writes only for authored artifacts that are
currently produced by human/agent skills rather than generation providers.
Research-hardening review (2026-07-04): reviewed 26d52df against the Agentic
OS reference and landed three follow-up batches. Batch A closed three
source-yield at-rest validation gaps (bidirectional yield_stats
reconciliation, source-yield duplicate-id guard, gated access-method
rejection) and accepted ADR 0021. Batch B added the Signal Tier Rubric
anchoring visible_metric_signal/confidence and a Synthesis Discipline
(corroboration breadth plus a contradiction pass), recorded in
agentic-os-alignment.md. Batch C added an advisory thin-evidence WARN in
validate research and an anti-contamination query-grounding rule. 327 tests
pass; drift checks and example validation clean.
Review follow-ups (2026-07-04): closed two P2 findings on the above work —
the thin-evidence WARN now derives "material" from run outputs (not only the
mutable material_update flag), the example search-plan routing_basis is
creator-grounded, and a required per-query term_basis enum makes query-term
provenance auditable at rest. 330 tests pass; drift checks and example
validation clean.
Manual research-loop exercise, run 1 (2026-07-05): ran a real second research
run for the remy-vale fixture creator (research_run_remy_vale_2026_07_05_001,
mode scheduled_needs) to exercise the Next Work Queue item 1 loop end to end —
search-plan before browsing, evidence + source-yield after, findings synthesis,
then validate/rebuild-index/prune. The loop held: search-plan and both new
records validate, `validate research` and `validate workspace` pass (13 research
records, 27 workspace paths), `rebuild-index` rebuilt 11 recall rows, prune
dry-run found nothing eligible. The run targeted the schedule's under-served
"low-light plant picks" cluster and added finding_remy_vale_low_light_picks
(low-to-medium confidence). Two loop learnings for the pre-automation gate:
(1) the thin-evidence WARN correctly fired (material update, 1 of 4 sources
yielded) and forced the finding to be re-labeled thin-evidence rather than
"well-corroborated" — the gate does real work; (2) the binding constraint on
evidence quality is source access, not planning: Reddit was unreachable for the
second consecutive run (the tooling cannot fetch reddit.com) and the TikTok tag
page failed, so runs can currently reach only secondary care guides and discover
surfaces, which caps confidence at medium with no primary-post metrics. Before
scheduled research automation is worth approving, the research adapter seam needs
a Reddit-capable (and ideally logged-in platform) connector; automating the
current loop would just schedule thin-evidence runs. No repo code changed; all
run artifacts live under the untracked remy-vale workspace fixture.
```

Research-acquisition connector layer (2026-07-05): ADR 0022 accepted and
implemented across batches A-D. The env-gated connector tier mirrors the
Agentic OS str-trending-research acquisition path (stdlib-only, mock-hook
testing): reddit_openai (OpenAI Responses web_search + direct reddit.com JSON
engagement enrichment), x_xai (x_search, inline engagement), firecrawl_web
(v2/scrape), and linkedin_apify (harvestapi actor). Key presence is standing
approval for the research tier only (per-run call cap + kill switch; generation
gates unchanged). A high-effort code review of batches A-B produced 10
confirmed findings, all fixed in batch B.5 — including the policy/mechanism
split where the search-plan and source-yield validators still rejected
api_backed/scraping_api adapters that ADR 0022 standing-approves (validators
now split standing-approved vs fully-gated methods), restored recency windows,
budget/depth resizing (free reddit enrichment decoupled from the paid cap),
parse hardening, env precedence, an in-process model cache, and a
schema-validated fetch-result contract (schemas/research-fetch-result). CLI:
`list-connectors` and `research-fetch` (validates output before emitting).
The create-research-findings skill documents the connector step; 17 runtime
skills synced to all four fixture workspaces. Verification: 372 tests pass,
43 example records validate, drift checks pass (22), fixture workspaces
validate. No live provider calls were made; first live validation happens when
a real key lands in .env.

Phase 2 planning (2026-07-05): the Learning OS implementation plan landed at
`docs/workflows/learning-os-implementation-plan.md` — entry criteria verified,
exit criteria rewritten as runnable checks, six slices sequenced, four
execution decisions user-approved (FTS5 keyword lookup phased ahead of the
reference's local-embedding vector leg; conductor + one skill per step;
manual + neutral-CSV ingestion; JSON-canonical performance summaries), and a
reference review of the Agentic OS memory schema and mkt-content-analytics
skill folded into slices 2, 3, and 6 (benchmark rubric, stage-remediation
mapping, heading-aware chunking, authority/recency rerank, no-leak scoping).

Phase 2 slice 1 (2026-07-05): Published Post Record registration.
`register-published-post` CLI + `skills/register-published-post/SKILL.md`
landed with the conductor/registry/matrix/architecture-map rows in the same
batch (three remaining Phase 2 skills marked [PLANNED] with the halt rule).
The writer validates the record against the registered Output Package
(chain ids, `assets_used` upload-asset ids, caption/description path),
rejects symlinked write targets, rolls back on failure, and moves the
Project `packaged -> published` on the first record whose
`publication_status` attests a live post (`scheduled`/`failed` register
without the transition). `validate project` re-checks every registration
invariant at rest via the shared `_validate_published_post_matches` seam:
filename-matches-id, chain matching, and live-record/status reconciliation
in both directions (published status without a live record fails; a live
record on a sub-published project fails). Verification: 406 tests pass (14
added in `tests/test_published_posts.py` — happy path, below-packaged
rejection, package mismatch without partial write, dangling asset ref,
undeclared caption path, duplicate id, symlinked records dir, non-live
no-flip, and six at-rest hand-edit probes); 43 example records validate;
drift checks pass; all four fixture workspaces validate after
`update-creators` synced 18 runtime skills with zero overrides lost. Full
workflow replay in `.tmp/slice1-verify`: creator init through
`register-published-post`, record/project/workspace validation,
rebuild-board, validate board, and rebuild-index all pass with the project
ending `published`. Exit criterion 1 of the Phase 2 plan is met.

Slice 1 review fixes (2026-07-05): three findings, all fixed with failing
probes first. (P1) Text-format projects could not honestly register
publications — the PublishedPostRecord schema required a string thumbnail
while article/thread Output Packages allow null; the schema now mirrors the
package's nullable union and the match seam enforces the same text-only
gate (`TEXT_FORMAT_IDS`), proven by a packaged-article fixture. (P2) The
packaged-requires-upload-ready invariant keyed on `status == "packaged"`
and lapsed once a project published; it now keys on `_status_at_least`, so
a hand-edited draft package fails at rest at every status from packaged
onward. (P2) Duplicate platform publications under different record ids now
fail: no two records may claim the same `(platform, platform_post_id)` or
`public_url`; the writer rolls back a duplicate and the at-rest validator
rejects hand-added ones, while a legitimate second-platform record still
registers. 412 tests pass (6 added); 43 examples validate; 18 runtime
skills synced to all four fixture workspaces. Two process learnings
recorded (schema-mirror nullability, status-equality invariants).

Phase 2 slice 2 (2026-07-05): Analytics Snapshot ingestion.
`add-analytics-snapshot` (manual/derived JSON) and `import-analytics-csv`
(neutral InfluencerOS template at
`docs/templates/analytics/analytics-snapshot-template.csv`, 35 columns,
all-or-nothing) landed with `skills/ingest-analytics/SKILL.md` and its
registry/matrix/conductor/architecture-map rows in the same batch. Every
path writes through one shared seam (`write_analytics_snapshot`, ADR 0004)
— proven by a mocked api-sourced record driving the same function — so a
future API connector drops in without a second invariant set. The seam
pins each snapshot to a registered Published Post Record whose status
attests a live post, requires platform match, fills chain ids from the
project (CSV rows cannot mistype them), derives `hours_since_publish` from
the record timestamps when omitted (rejecting pre-publication snapshots),
maps blank CSV cells to null (absent, never guessed), and requires
`raw_source_ref`/`retention_curve_ref` to resolve to real files under
`analytics/raw/` with escape rejection. `validate project` re-checks every
ingestion invariant at rest, including filename-matches-id. The skill
carries the reference-derived platform caveats (YouTube 2–3 day lag,
LinkedIn personal click gap). Verification: 433 tests pass (21 added in
`tests/test_analytics.py` — manual/CSV/API-mock paths, derivation,
liveness, platform mismatch, raw-ref escape/missing probes, transactional
CSV rollback, template and schema drift pins, and three at-rest hand-edit
probes); 43 examples validate; drift checks pass; 19 runtime skills synced
to all four fixture workspaces, all validating. Full workflow replay in
`.tmp/slice2-verify`: publication registration, manual + CSV ingestion,
project/workspace/board validation, and index rebuild all pass. Exit
criterion 2 of the Phase 2 plan is met.

Phase 2 slice 3 (2026-07-05): Performance Summary contract and skill.
`projects/<project-slug>/performance-summary.json` is now the canonical
schema-validated summary record (plan Decision 4): the `performance-summary.md`
scaffold is gone, the `project_paths` const, example manifest, fixture,
layout doc, and ADR 0012 amendment all carry the `.json` name, and the
summary attaches at rest once authored — no write CLI, no new Project
status. `validate project` is the enforcement seam: `evidence_refs` must
resolve inside the project (`output_package_id` to the registered package,
every `published_post_record_id`/`analytics_snapshot_id` to records on
disk), chain ids must match, containment is symlink-safe, and record
semantics now reject duplicated attribution stages
(`validate_unique_stages`) so the five stages appear exactly once each. A
`published` project with a snapshot at least 72h post-publish (the slowest
platform reporting lag) and no summary draws an advisory WARN derived from
at-rest snapshot data (hours recorded, else timestamp-derived), never a
flag. `skills/create-performance-summary/SKILL.md` (interpretive, Decision
2) landed with its registry/matrix/conductor/architecture-map rows in the
same batch and carries the Performance Benchmark Rubric plus the
stage-remediation mapping adapted from the reference
`mkt-content-analytics` skill (recorded in `agentic-os-alignment.md`),
evidence-strength honesty rules (ADR 0008), and the `index_allowed` call.
Verification: 455 tests pass (16 added in
`tests/test_performance_summary.py` — valid summary, dangling
package/post/snapshot refs, chain-id mismatches, duplicate-stage probes,
schema hand-edit, unpackaged rejection, symlink escape, four WARN probes,
CLI stderr surfacing); 43 examples validate; drift checks pass; 20 runtime
skills synced to all four fixture workspaces, all validating. Full
workflow replay in `.tmp/slice3-verify`: no WARN below maturity, WARN
fires at 96h, summary authored and validated, WARN clears, index/board
rebuilds and workspace/research validation stay green. Exit criterion 3 of
the Phase 2 plan is met.

Phase 2 slice 4 (2026-07-06): Learning distillation. The
`distill-creator-learning` skill exists (interpretive, Decision 2), closing
the last Phase 0C WS 10 `[PLANNED]` obligation: the conductor's dependency
and phase-owner rows, the architecture-map producer table and call graph,
the registry (row moved out of Missing Future Skills, now empty), and the
context-matrix coverage row all flipped to `[BUILT — Phase 2 slice 4]` in
the same batch. `log-learning` gained the creator-lesson mode (exit
criterion 4): when the target is a Creator Workspace `memory/learnings.md`
(detected by the manifest beside `memory/`), `--evidence` and `--strength`
are required, every evidence id must resolve to a workspace
performance-chain record (performance summary, published post record,
analytics snapshot, project, output package — any other prefix fails
closed), and the entry is one parseable line under `## Creator Lessons`
grouped by `### <topic>` headings
(`- YYYY-MM-DD [strength]: lesson (evidence: id, ...)`); the strength
vocabulary is pinned to the PerformanceSummary `distilled_lessons` enum by
a drift test (ADR 0008 scope honesty). `validate workspace` re-checks
every at-rest lesson the same way — a hand-edited dangling evidence id,
unknown strength marker, impossible date, or unparseable bullet inside the
Creator Lessons section fails validation; content outside that section is
not policed. OS-scope `log-learning` is unchanged, and passing
`--evidence` against a non-workspace learnings file is rejected rather
than silently dropped. The promotion path to `context/MEMORY.md` reuses
the capped `memory-write` writer (cap refusal already tested).
Verification: 482 tests pass (22 added in `tests/test_creator_lessons.py`
— write/dedup/topic-scoping, unresolvable-evidence and unsupported-prefix
rejection at write, four CLI probes, at-rest hand-edit probes for dangling
ids, strength, format, and out-of-section tolerance, workspace-detection
unit, strength enum pin); 43 examples validate; drift checks pass; 21
runtime skills synced to all four fixture workspaces via `update-creators`
with zero overrides lost, all validating. Full workflow replay in
`.tmp/slice4-verify`: register-published-post → add-analytics-snapshot
(maturity WARN fires) → summary authored (WARN clears) → creator lesson
distilled via `log-learning --evidence --strength` → missing-evidence and
dangling-evidence writes rejected → durable fact promoted via
`memory-write` (191/2,500 bytes) → `validate workspace` green, hand-edited
dangling evidence fails at rest, restored copy green → board/index/prune
green. Exit criterion 4 of the Phase 2 plan is met.

Slice 4 review fixes (2026-07-06): three findings, each reproduced by the
reviewer before the fix and pinned by a failing probe. (P2) Evidence
resolution trusted any JSON carrying the right id field — a planted
`projects/fake-project/performance-summary.json` containing only
`{"performance_summary_id": ...}` resolved as evidence and validated at
rest; candidates now resolve only when they validate against their schema
(record semantics included) and are anchored to a schema-valid
`project.json` in the same project folder, with per-record files also
required to carry their id as the filename. (P2) `multi_post_pattern` was
only enum-checked while the skill contract calls it a multiple-post
claim; the writer and `validate workspace` now count the distinct
published posts the cited evidence identifies (direct post ids,
snapshots' parent posts, a summary's cited post list — project/package
ids identify none) and refuse the strength below two. (P3) Section-scoped
checks read the first `## Creator Lessons` heading, so a second section's
content escaped validation; duplicate headings are now rejected by both
the writer and the at-rest validator. 489 tests pass (7 probes added:
spoofed-record write and at-rest, multi-post write reject/accept and
at-rest hand-edit, duplicate-section write and at-rest); 43 examples
validate; the skill contract, workspace-structure, ARCHITECTURE, and
pipeline-contract docs teach all three rules.

Phase 2 slice 5 (2026-07-06): Recall index extension. `rebuild-index` now
projects the three Phase 2 learning records — published post records,
analytics snapshots, and performance summaries — into the shared recall
index with the same provenance columns (workspace-relative source path,
sha256 content hash, `indexed_on`) and bare-id uniqueness guarantee as
every existing type (all three joined `UNIQUE_RECORD_TYPES`, so a
duplicated id across files fails the rebuild closed). The scans mirror
the writer layout exactly — `published/published-post-records/*.json`,
`analytics/snapshots/*.json`, and `performance-summary.json` per project
folder (the original plan's `analytics/*.json` wording predated the slice 2
`snapshots/` subfolder) — so `analytics/raw/` payloads are excluded by
construction: the scan never names that folder. Each row carries the
record's required `project_id`. The recall-index test scaffold now
renames the example project into the slug-named folder `init-project`
actually builds (process-learning 2026-07-03: scaffolds copy the CLI's
layout). No skill surface changed, so no runtime sync was needed.
Verification: 493 tests pass (4 added — duplicate published-post id
across projects, duplicate snapshot id across files, raw-payload
exclusion probe with a planted raw snapshot copy, delete-and-rebuild row
equivalence; the resolution test extended with the three new record
kinds and the cross-creator scoping test with a foreign
analytics-snapshot row); 43 examples validate; drift checks pass; all
four fixture workspaces validate. Full workflow replay in
`.tmp/slice5-verify` (`.tmp/slice5-verify.sh`): creator init through
packaging, `register-published-post` → `add-analytics-snapshot` (with
real `analytics/raw/` files the snapshot's raw refs must resolve to) →
summary authored → creator lesson via `log-learning --evidence` →
`rebuild-index` resolves all three Phase 2 ids with zero `analytics/raw`
rows → deleting the database and rebuilding reproduces identical rows
modulo `indexed_on` → board validation and prune green. Exit criterion 5
of the Phase 2 plan is met.

Slice 5 review fixes (2026-07-06): two findings, the P2 confirmed by the
reviewer's reproduction, fixed with failing probes first. (P2) The Phase 2
index scans accepted any JSON under the expected paths that carried the
right id field — a planted
`projects/fake-project/analytics/snapshots/analytics_snapshot_fake.json`
containing only `analytics_snapshot_id` and a nonexistent `project_id`
still emitted an analytics-snapshot row, repeating the slice 4
id-string-vs-record class one day after it was recorded as a process
learning. The scans now mirror the hardened memory-module evidence
resolver: every Phase 2 candidate must validate against its schema
(record semantics included), per-record files must carry their id as the
filename, the sibling `project.json` must exist and validate as a project
manifest, and the record's `project_id` must equal the manifest's —
failing the rebuild closed with the offending path, consistent with the
index's existing posture (Phase 1 scan behavior is unchanged; those ids
are cross-checked by the research/queue validators). The duplicate-id
probes were reworked to anchor their planted duplicates in a second
schema-valid project, proving the duplicate check still fires on fully
anchored records. (P3) This file's `Last updated` header had rotted to
2026-07-05 while recording 2026-07-06 work; corrected. 498 tests pass (5
added — schema-rejection probe inside an anchored project, the reviewer's
unanchored-folder reproduction, filename==id, manifest project_id
mismatch, valid-record-without-manifest); 43 examples validate; the
`.tmp/slice5-verify.sh` replay stays green end to end (writer-built
records all anchor). One process learning recorded (sweep recorded
learning classes against every new seam of the same shape).

Slice 5 review follow-up (2026-07-06): closing the review exposed an
inversion — after the P2 fix, `rebuild-index` was the *only* command
rejecting learning records in unanchored project folders; the fake-project
plant passed both `validate workspace` and `validate research` (verified
by reproduction), so a projection had become stricter than the validators
it must never substitute for. The anchoring walk moved to one shared
function, `collect_anchored_learning_records` in `projects.py` (the owner
of the project layout contract), called by both the recall-index scan and
`validate workspace` at rest — guard rule 1 (writer/projection invariants
re-checked at rest) and guard rule 3 (multi-path checks share one
function) applied together. Phase 1 index scans deliberately stay
lightweight: those record types are already schema-validated,
filename-pinned, and creator-scoped by `validate research`/`validate
queue` (verified by a planted id-only queue entry failing at rest), so
index-side re-validation would create a second drift-prone path for
invariants the primary validators own. 501 tests pass (3 added — anchored
records pass workspace validation, the unanchored plant fails it, a
manifest-mismatched summary fails it; the slice 4 spoofed-record at-rest
probe now asserts both layers: the lessons rule on its own seam and the
earlier workspace-level anchoring rejection); 43 examples validate; the
replay and all four fixture workspaces stay green.

Phase 2 slice 6 (2026-07-06): Semantic lookup projection — the ADR 0011
FTS5 keyword leg per Decision 1. New module
`influencer_os/semantic_lookup.py` plus `rebuild-lookup` and
`query-lookup` CLI commands, projecting into the existing
`workspace-library/index/influencer-os.sqlite` (stdlib `sqlite3`, FTS5
presence probed and failed closed, no new dependencies, no provider
calls). The four reference design details adopted per the plan's
Reference Review: heading-aware deterministic chunking with 1-based line
provenance (soft 1200 / hard 2000 / 150-char overlap, ported from
chunker.ts); longest-prefix authority weights (learnings 1.5,
performance summaries 1.3, brand context 1.2, findings/stable findings
1.0; tunable per creator via optional `context/lookup-config.json`,
absent file → defaults, malformed file → fail closed); the three-stage
rerank in application code over FTS5 candidates (relevance x authority x
recency decay with 14-day half-life, 0.7 dampening floor, 0.3
floor-ratio gate, undated rows never decay — reranker.ts, so the future
vector leg only swaps the candidate generator); and normalized-sha256
source change detection (unchanged sources keep their rows; an authority
change also re-indexes). One adaptation recorded in
`agentic-os-alignment.md`: FTS5 BM25 scores are corpus-dependent and can
cross zero on tiny corpora, so relevance maps through a sigmoid into
(0, 1) — the keyword analogue of the reference's non-negative cosine
similarity, keeping authority boosts meaningful and the floor gate from
dropping every hit. Indexed sources walk an explicit allowlist
(`brand_context/identity.md`/`soul.md`/`personal-brand.md`,
`research/findings.md`, `research/stable-findings/*.md`,
`memory/learnings.md`, and `semantic_lookup.summary_text` from
schema-valid manifest-anchored PerformanceSummary records — the shared
`collect_anchored_learning_records` seam — where `index_allowed` is
true); `analytics/`, raw exports, transcripts, and media are unreachable
by construction, and review follow-up rejects symlinked lookup source
files or symlinked allowlist directories so allowed paths cannot alias
denied material. Creator scoping follows the reference `scope.ts`
discipline: every row carries `creator_slug`, queries require one,
filter in SQL, and use a creator-local FTS table so BM25 statistics are
not influenced by another creator's corpus, with dedicated no-leak tests
(creator A's query never returns creator B's rows even on shared terms,
and creator B's indexed text does not change creator A's relevance
scores) and a rebuild-one-creator-never-touches-another probe. Queries
are never
persisted: `query-lookup` opens the database read-only and a test pins
the database bytes unchanged across a query. JSON-sourced chunks cite
the record (heading = summary id, no line numbers) instead of fake
summary-text line positions. Verification: 523 tests pass (22 added
across chunker determinism/provenance/window-overlap, rerank stages,
BM25 sigmoid monotonicity, FTS5 term sanitization against operator
injection, allowlist coverage, symlink fail-closed behavior,
`index_allowed: false` exclusion, raw-marker absence, no-leak,
creator-local relevance scoring, delete-and-rebuild equivalence,
change-detection skip/re-chunk, config override and fail-closed, CLI
happy/error paths); 43 examples validate; drift checks pass; all four
fixture workspaces validate and `update-creators` synced 21 skills with
zero overrides lost. Full workflow replay in `.tmp/slice6-verify`
(`.tmp/slice6-verify.sh`, extending the slice 5 script): creator init
through publication, analytics, summary, lesson → `rebuild-lookup`
indexes exactly the allowlist with zero analytics content →
`query-lookup desk resets` returns cited `source_path:line` hits with
the creator lesson outranking findings on authority → deleting the
database and rebuilding both projections reproduces identical rows
modulo `indexed_on`. Exit criterion 6 of the Phase 2 plan is met; no
skill surface changed (Decision 2 scopes Phase 2 skills to slices 1-4),
so the registry and context matrix carry no new rows.

Slice 3 review fixes (2026-07-05): two findings, both fixed with failing
probes first. (P2) `published_post_record_ids` and `analytics_snapshot_ids`
resolved independently, so a summary could cite one post while citing
another post's snapshots — misattributing metrics to the wrong URL/assets
in multi-publication projects; each cited snapshot's parent post must now
itself be cited. (P3) `source_material_refs` was schema-required but never
validated, so `../../outside` and missing paths passed as provenance;
each ref must now be a relative path resolving to an existing file inside
the project, symlink-safe (same containment class as raw refs). 460 tests
pass (5 added); 43 examples validate; the slice replay stays green; the
skill contract and pipeline contract teach both rules. Two process
learnings recorded (validate the join between related id lists; every
ref-shaped field gets an unresolvable probe in its shipping slice).

Slice 2 review fixes (2026-07-05): three findings, all fixed with failing
probes first. (P1) The pre-publication rejection lived inside
hours-derivation, so a snapshot with supplied `hours_since_publish` and a
`snapshot_at` before publication ingested cleanly; the timestamp-ordering
check moved into the shared match seam, so it now fires on every path and
at rest (hand-edit probe added). (P2) CSV parsing accepted `nan`/`inf` via
`float()`, the validator's min/max comparisons are silently false against
NaN, and `json.dumps` re-emits non-standard NaN — closed at three layers:
the CSV parser rejects non-finite numbers, the validator's number branch
rejects them fail-closed across all schemas, and `_write_json` uses
`allow_nan=False`. (P2) Raw-ref containment resolved against the project
root, so a symlink inside `analytics/raw/` pointing at another project
file passed; containment now resolves against `analytics/raw/` itself
(write-time and at-rest symlink probes added). 439 tests pass (6 added);
43 examples validate. Three process learnings recorded
(derivation-branch checks, NaN fail-closed, narrowest containment root).

Full Phase 2 review (2026-07-06): reviewed all six Learning OS slices against
the PRD, roadmap, Learning OS implementation plan, architecture map,
repository map, context matrix, skill registry, pipeline contract, workspace
layout docs, skills, schemas, runtime modules, and tests. Alignment is good:
publication registration, analytics ingestion, Performance Summary authoring,
creator-lesson distillation, recall-index extension, and semantic lookup all
landed on the documented file-first seams with writer/at-rest parity and the
two remaining Phase 2 surfaces explicitly deferred. One P2 defect was found
and fixed with a failing probe first: a pre-publication AnalyticsSnapshot could
bypass timestamp ordering when `snapshot_at` was naive and `published_at` was
timezone-aware while `hours_since_publish` was supplied; the shared analytics
match seam now rejects mixed timezone awareness before trusting the timestamp
or hours value. Documentation cleanup in the same review aligned the Learning
OS plan's as-built snapshot path (`analytics/snapshots/*.json`), the
`register-published-post <record> --project <project-dir>` command form, the
roadmap Phase 2 schema criterion, and the v1 boundary language in README and
ARCHITECTURE. Verification: 527 tests pass (1 added), 43 examples validate,
22 drift checks pass, the stale-path scan passes, and `.tmp/slice6-verify.sh`
passes end to end.

Guided E2E fixture repair (2026-07-07): reviewed the disposable
`workspace-library/creators/e2e-luna-fit-2026-07-07` run data after the
normal-user E2E/sub-agent exercise. The fixture validated, but the review found
five data-quality gaps and fixed them in-place: validation-based foundation
approval was replaced with an explicit `progress/setup-interview.md` approval
record; a phase checklist now names phase, next artifact, validation command,
and gate type; public-web Mayo/NIH/CCOHS source provenance now stays
`public_web` through research evidence, metric snapshots, source-yield records,
research search terms, and the project source cache instead of being mislabeled
as YouTube evidence; promotion wording now records explicit approval after
reviewing the package instead of preauthorization; an advisory hook/payoff
ReviewRecord exists before generation approval; the project and board now sit
at `ready_for_generation`; and `.DS_Store` noise was removed from the ignored
fixture. The schema layer was hardened so public-web provenance validates for
`MetricSnapshot.platform` and `ResearchSearchTerms.items[].platform`, with drift
pins and regression tests. Verification: `python3 -m unittest discover -s tests`
passes (787 tests), `python3 -m influencer_os validate examples` validates 49
example records, and `python3 -m influencer_os validate all
workspace-library/creators/e2e-luna-fit-2026-07-07` passes with 5 layers, 0
skipped, 0 warnings.

Guided E2E regression test (2026-07-07): added
`tests/test_guided_e2e.py`, a temp-workspace newcomer journey test distinct
from the existing seeded packaging pipeline test. The test initializes a
creator, records `progress/setup-interview.md`, `progress/setup-checklist.md`,
and `progress/phase-checklist.md`, imports and reviews intake provenance,
creates public-web research evidence/metrics/source-yield/intelligence,
records explicit idea-promotion approval, creates a project with applied
template, production plan, provider-neutral generation plan, and advisory
Hook/Payoff ReviewRecord, rebuilds the board, and asserts `validate all`
finishes with 5 layers, 0 skipped, 0 warnings while no GenerationApprovalRecord
or OutputPackage exists. Building the test exposed one remaining schema gap:
`ResearchSources.items[].platform` also needed `public_web`; the enum, drift
pin, and schema regression test were added alongside the guided E2E. Verification:
`python3 -m unittest discover -s tests` passes (789 tests), `python3 -m
influencer_os validate examples` validates 49 examples, and the repaired
disposable E2E fixture still passes `validate all` with 5 layers, 0 skipped,
0 warnings.

Repository hardening review fixes (2026-07-07): closed the six review findings
from the repository hardening pass. `research-fetch` now requires `--run-dir`
and persists `connector-budget.json`, so the paid connector cap is per research
run, not per command. Runtime skill sync now rejects symlinked `.claude/skills`,
backup, and target skill directories before copying or deleting. Canonical JSON
record writes now use a shared same-directory atomic replace helper, and the
generation dispatch status transitions use it under the existing lock.
`research-fetch-result` candidates are now bounded and explicitly shaped;
YouTube candidates omit absent optional thumbnail URLs. The repo now has
`pyproject.toml` and a GitHub Actions workflow for the unit-test plus
example-validation floor. YouTube standing-approval wording in ADR 0022 and
validator comments now matches ADR 0027. Verification: `python3 -m unittest
discover -s tests` passes (799 tests), `python3 -m influencer_os validate
examples` validates 49 examples, and `python3 -m compileall -q influencer_os
tests` passes.

Onboarding readiness and strategy-calendar hardening (2026-07-09): completed
ADR 0028's forward behavior and closed two independent review rounds. The
legacy-named `readiness-gates.json` now models deterministic `milestones`
without colliding with the two human-owned pipeline Gates. Workspace validation
enforces human milestone approval metadata, prompt-ready media prohibition,
channel publish/drafting consistency, creator- and strategy-scoped schedules,
nonempty goal-resolving slots, explicit production platforms, campaign/variant
refs, and conversion-asset lifecycle/use/platform approval. Strategy readiness
permits planned/drafted conversion assets while production fails closed. The
portable calendar projection is a documented plan task; validation re-renders
and compares the complete HTML so visible tampering fails. Deprecated workspace
statuses remain readable only to emit migration warnings. Verification: 856
unit tests pass, 53 examples validate, compilation and whitespace checks pass;
registry/context-matrix drift tests pass. No provider-backed calls were made.

Visual continuity selection hardening (2026-07-09): added the schema-backed
Visual Continuity Plan between accepted creator context and the Reference
Library. Props and production spaces are now scored for distinct brand and
Atmosphere Roles, presented as a complete user-review package, and promoted
only after explicit approval; candidate evidence refs resolve inside the
workspace, nonvisual plans retain their internal validation, visual
`foundation_ready` status requires approval, and undeclared prompt files under
any `references/` subfolder cannot bypass the pre-approval boundary. Adira's
ignored Creator Workspace contains the first 13-candidate pending review plan;
no provider generation ran and no candidate was silently approved.
Verification: 877 unit tests pass, 55 examples validate, compilation and
whitespace checks pass.

Lean routing and ownership cleanup (2026-07-09): removed the superseded
`init-run` / Social Research Pack path, including its schema, example,
scaffold, resolver branch, tests, and current operational documentation. The
Creator Workspace research route is now the sole supported entry. Generic
creator-scope checks moved to `creator_scope.py`; generic JSONL validation
moved to `validation.py`; Improvement OS now owns friction-ledger validation
and reflection reconciliation, eliminating the Research/Rubric ownership
cycle. Current product language distinguishes shipped influencer onboarding
from ADR 0026's planned product/brand target, and the influencer appearance
choice is now named Representation Model. Manual record inventories were
replaced with disk-derived authority, and shared integration builders moved
from `test_cli.py` to `tests/support.py`. The generation/Project seam was left
unchanged. Verification: 870 unit tests pass, 52 examples validate,
compilation and both review axes pass with no remaining findings.

Lead-magnet skill landed and integrated (2026-07-09): `create-lead-magnet`
(strategy → production bridge) produces the `conversion-asset` record, body
copy to a heading contract, a per-creator resolved theme
(`references/brand/<slug>-theme.css`), and a rendered PDF from the bundled
offline HTML/CSS template; optional creator photos reuse an explicitly reviewed
crop from the approved identity plate, and generated reference imagery stays behind
the provider boundary. Proven end-to-end on the margot-calder fixture
(operator-approved render; record advanced to `approved`). Integration audit
closed the gaps: `create-influencer` now dispatches the skill at phase 12
(dependencies, hierarchy, and architecture-map call graph updated), the
context matrix gained the row.
Margot's workspace still fails full workspace validation for pre-existing
reasons (deprecated `foundation_review` status; missing `channels.json`,
`content-strategy.json`, `readiness-gates.json`) — queued as a backfill task.
Verification: unit tests pass, examples validate, drift checks pass. No
provider-backed calls were made.

Adversarial hardening (2026-07-09): Part A now lists only its existing Markdown
file, conversion records carry accepted-strategy provenance, and approved/ready
states require explicit user-approval metadata. Creator setup routes only
`lead_magnet` assets to this PDF workflow and halts on unsupported conversion
types. Disposable render bundles moved to root `.tmp/`; the default skeleton is
generic, text-only, and offline. Shared Chrome discovery removed duplicated
helper logic, and portrait crops now require an explicit reviewed rectangle.

## Next Work Queue

Personal brand board integration (2026-07-09): added the
`personal-brand-board` setup skill, `personal-brand-board` schema/example,
creator-specific canonical JSON at `references/brand/personal-brand-board.json`,
one package-owned editable HTML template, and `rebuild-brand-board` / `validate
brand-board` CLI seams. Visual creator readiness now requires a current board
with explicit board-specific approval; generated brand mood imagery remains a
supporting reference. Mara Vale was migrated to the shared template without a
provider call and left honestly at `profile_ready` with the new board marked
`draft_for_review`. Verification: 54 examples validate; brand-board, readiness,
drift, guided E2E, and Planning OS journey tests pass. The full 849-test run has
9 unrelated failures in concurrent onboarding/calendar work already present in
the dirty worktree.

Brand-board visual semantics correction (2026-07-09): user review found that
`visual_territories` mixed locations, portraits, props, and layout references,
and that content-pillar images were decorative rather than explanatory. The
schema/template now use `production_spaces`: actual recurring filming/photo
locations with purpose, best-use formats, continuity notes, and required correct
location imagery. Props remain Reference Library assets, and pillar cards are
typographic so unrelated images cannot be inserted. Mara now shows only her
Research Desk and Walking-Note Route in wider context.

Signature-props extension (2026-07-09): added a separate optional board section
for recurring identity-bearing objects. Each prop requires its correct approved
object image, narrative role, suitable uses, and continuity notes. Props remain
Reference Library objects and never mix with production spaces. Mara’s Black
Research Notebook is the first migrated example.

Brand-board call-chain hardening (2026-07-09): moved
`personal-brand-board` after Reference Library planning/resolution and before
readiness validation in `create-influencer`. Production spaces now require
typed `location` asset IDs and signature props require typed `object` asset IDs;
unresolved categories fail closed, planned/prompted assets render intentional
placeholders, and Reference Library changes stale the HTML projection. Mara's
board was migrated to these links, rebuilt, visually checked, and validated
without changing its `draft_for_review` approval state. Verification: 66 focused
brand-board, drift, lifecycle, and provenance tests pass; 54 examples validate;
compileall passes.

1. Exercise the manual research-intelligence loop against real creator runs before approving any scheduled research automation. **Run 2 (live connector smoke, ADR 0022) completed 2026-07-07** with `INFLUENCER_OS_CONNECTOR_MAX_CALLS=3` per connector: `reddit_openai` discovery works live (12-17 candidates per topic, 1 paid call, parsed shapes match the mirrored parser), but reddit.com answers the free direct-JSON enrichment reads with HTTP 403 "Blocked" — the enrichment leg never attaches engagement metrics live. Found and fixed in the same batch: `enriched_count` counted attempts, not successes, so the fetch result claimed full enrichment while attaching nothing; it now counts only candidates with engagement attached and notes the failures (regression test `test_blocked_enrichment_counts_zero_and_notes_failure`). `youtube_data_api` works live (5 candidates, 2 paid calls, engagement present). `firecrawl_web` works on public article URLs but reddit.com also blocks it (HTTP 403 at the Firecrawl layer). `x_xai` fails with HTTP 403 `permission-denied` — the xAI team account has no credits; operator action: purchase credits at console.x.ai, then re-run one bounded fetch. `linkedin_apify` untested (no `APIFY_API_KEY`). Consequence for research quality: Reddit evidence currently carries discovery relevance but no visible metrics, so evidence strength for Reddit sources stays capped until an alternative engagement path (e.g. authenticated Reddit API) is approved in its own ADR. **Remaining before any automation decision:** exercise the full manual research-intelligence loop (run → findings → intelligence updates) against a real creator using the working connectors.
2. Phase 2 Learning OS — **build slices complete** per `docs/workflows/learning-os-implementation-plan.md`: slices 1 (published-post registration), 2 (analytics snapshot ingestion), 3 (Performance Summary contract + `create-performance-summary` skill), 4 (`distill-creator-learning` skill + `log-learning --evidence` creator-lesson mode), 5 (recall index extension to the three Phase 2 record types), and 6 (semantic lookup projection, FTS5 keyword leg per Decision 1: `rebuild-lookup`/`query-lookup`) complete 2026-07-06. All six runnable exit criteria are met; remaining Phase 2 items are explicitly deferred (analytics API connector on request per Decision 3; vector lookup leg with Command Centre per Decision 1).
3. Optional: render the comparison map Excalidraw scene.

## Decision Log

See `docs/adr/` for accepted architecture decisions.
