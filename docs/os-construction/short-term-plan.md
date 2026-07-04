# Short-Term Plan: Parity Hardening

Last updated: 2026-07-03

Status: **Complete (2026-07-03).** All workstreams 0-15 landed via execution batches A-G; the verification record and exit-criteria run live in `docs/os-construction/progress.md`. This plan is retained as the Phase 0C record. Next work: Phase 1 slice 1 (master intake import) per the roadmap.

## Goal

Prepare InfluencerOS for implementation by making the current repo closely match the Agentic OS file-first architecture, with Command Centre deferred.

This is the next handoff plan for another agent.

## Success Condition

Parity hardening is complete when:

- the Agentic OS reference path is verified as `/Users/ashokaji/code/External repos/Agentic Academy/agentic-os`,
- the copy/adaptation plan is checked against that reference, not any other local tooling repository,
- copied creator runtime skills are implemented and documented,
- creator runtime sync preserves `SKILL.local.md` and creator-only skills,
- every existing skill is registered,
- every registered skill has context-matrix coverage through either an explicit skill row or a named workflow row,
- root and creator memory policies are explicit,
- creator override rules are reflected in workspace docs,
- project output layout is deterministic,
- tests or checks catch adapter, registry, context, and schema drift,
- progress docs record the verification commands and results.

## Resolved Since Last Update (2026-07-01)

The Agentic OS parity review (`docs/os-construction/adversarial-review.md`) produced four decisions, now recorded as ADRs. Do not reopen these; implement them:

- Skill layout is finalized (ADR 0017): repo-central, no category prefixes, per-skill `references/`, machine-actionable `dependencies` frontmatter, `## Rules`/`## Self-Update`.
- Creator Workspace propagation mechanism is approved (ADR 0018): CLI subcommands; skills propagate now; scripts/settings/hooks/cron stay gated until un-deferred.
- The self-improvement loop is built local-first as system skills (ADR 0016), not deferred to Phase 2.
- The adapter model follows the reference (ADR 0019): `AGENTS.md` canonical, `CLAUDE.md`/`SOUL.md` thin importers, `context/SOUL.md` the sole identity.

Workstreams 9-15 below implement these plus the review's determinism and drift-check fix-batch. Each is issue-ready with a deterministic acceptance check.

## Execution Decisions (2026-07-02)

Phase 0C executes as seven batches, guardrails first so later batches
self-verify:

- Batch A: WS 1, 3, 4, 8 (drift-check guardrails).
- Batch B: WS 13 (validator hardening).
- Batch C: WS 12 plus the WS 6 path-pinning residue and the WS 14 readiness
  validator (the WS 14 exit-criteria rewrite already landed in the roadmap).
- Batch D: WS 9 plus WS 7 and the WS 5 override-doc residue.
- Batch E: WS 10.
- Batch F: WS 11.
- Batch G: WS 15 plus doc closeout and the full exit-criteria run.

User-approved decisions for execution; do not reopen without user approval:

- Validator (WS 13): extend the hand-rolled validator with a scoped subset —
  intra-file `$ref` to `#/definitions`, `oneOf`, `anyOf`, `allOf` — and make it
  fail-closed: an unrecognized validation keyword is an error, never a silent
  skip. No third-party dependency. Schema shapes need not mirror the reference;
  architecture parity is the bar, schema parity is not.
- Memory cap (WS 9, WS 7): `context/MEMORY.md` is capped at 2,500 characters,
  matching the reference `meta-memory-write`. The same cap applies at root and
  creator scope.
- Producer skills (WS 10): the six Phase 1 producer skills stay unbuilt in
  Phase 0C. The conductor marks them `[PLANNED]` with a halt instruction —
  never silently improvise a missing phase. Each marker is an open build
  obligation that must be reconciled and built in its Phase 1 slice, tracked by
  the skill-registry Missing Future Skills table and the roadmap Phase 1 slice
  list.
- Copy policy (WS 15): purchased Agentic OS files are reference-only; nothing
  is copied verbatim into this repo. Record the rule in the copy plan.
- Subagent pattern (WS 15): classify reference `.claude/agents/` and
  `.claude/commands/` as defer; write the ADR only when a Phase 1 producer
  skill actually adopts the pattern.
- PRD-to-issues conversion: skipped. This plan's workstreams are the
  issue-ready tracker; a parallel issue list would be a second source of truth
  that can drift.

## Required Read Order

1. `AGENTS.md`
2. `CONTEXT.md`
3. `docs/os-construction/prd.md`
4. `docs/os-construction/roadmap.md`
5. `docs/os-construction/agentic-os-parity-plan.md`
6. `docs/os-construction/agentic-os-copy-plan.md`
7. `docs/os-construction/context-matrix.md`
8. `docs/os-construction/skill-registry.md`
9. `docs/creator-workspace-structure.md`
10. `docs/pipeline-contract.md`

## Non-Negotiable Rules

- Follow Agentic OS architecture unless a user-approved override exists.
- Any new deviation must pass the divergence test and be recorded in an ADR or alignment doc.
- Keep Command Centre deferred.
- Keep provider-backed calls behind exact approval.
- Keep creator state under `workspace-library/`.
- Do not commit secrets, creator media, generated works, private creator references, or API keys.
- Prefer docs, schemas, and validation checks before runtime automation.

## Implementation Seams

Use the highest existing seam:

- files on disk,
- CLI validation,
- schema validation,
- unit tests.

Avoid testing private helper details unless no higher seam exists.

## Workstream 0: Reference Source Integrity Check

Problem: planning can drift if agents compare InfluencerOS against the wrong repository.

Tasks:

- Verify the Agentic OS reference exists at `/Users/ashokaji/code/External repos/Agentic Academy/agentic-os`.
- Confirm `AGENTS.md`, `CLAUDE.md`, `SOUL.md`, `ARCHITECTURE.md`, `agentic-os-alignment.md`, `agentic-os-copy-plan.md`, and `divergence-test.md` all name that path as the reference.
- Re-read the purchased Agentic OS files named in `agentic-os-copy-plan.md` before changing copy/adaptation classifications.
- Treat any other local tooling or shared-rule repository as non-authoritative for Agentic OS architecture unless the user explicitly approves it.

Acceptance criteria:

- `rg` finds no stale Agentic OS reference path in durable docs.
- The copy/adaptation plan names only the purchased Agentic OS repo as the architecture reference.
- Progress records the verification command.

## Workstream 1: Adapter Drift Check

Problem: root adapters can silently diverge.

Tasks:

- Define the canonical read order once.
- Add a lightweight test or script that checks `AGENTS.md`, `CLAUDE.md`, and `SOUL.md` all reference the required construction docs.
- Keep the check simple and file-based.

Acceptance criteria:

- The check fails if a required doc is missing from an adapter.
- The check passes on the current repo.
- The progress doc records the command.

## Workstream 2: Copied Creator Runtime Skills

Problem: Agentic OS copies and syncs runtime system files into client workspaces so each client can be opened as its own root. InfluencerOS needs the same behavior for creator-root skill execution.

Tasks:

- Keep repo `skills/` as the baseline skill source.
- Copy baseline skills into each Creator Workspace under `.claude/skills/`.
- Add a creator runtime sync path that refreshes copied baseline skills.
- Preserve creator `SKILL.local.md` files during sync.
- Preserve creator-only skill folders during sync.
- Keep scripts, settings, hooks, cron templates, and Command Centre files deferred unless separately approved.

Acceptance criteria:

- The chosen skill runtime layout is recorded in `agentic-os-alignment.md` and ADR 0015.
- `init-creator` creates copied runtime skill folders.
- `sync-creator-runtime` refreshes baseline skill copies.
- `sync-creator-runtime` preserves `SKILL.local.md` and creator-only skills.
- `agentic-os-copy-plan.md`, `context-matrix.md`, `skill-registry.md`, and `creator-workspace-structure.md` agree with the decision.

## Workstream 3: Skill Registry Hardening

Problem: skills can exist without registry rows or context rules.

Tasks:

- Scan `skills/`.
- Ensure every skill has a row in `docs/os-construction/skill-registry.md`.
- Ensure every skill has context-matrix coverage through either an explicit skill row, a named workflow row, or an explicit reason it is deferred.
- Add missing trigger phrases, reads, writes, and override support.

Acceptance criteria:

- Every `skills/*/SKILL.md` is represented in the registry.
- Every represented skill maps to a context-matrix workflow or explicit skill row.
- Every future/planned skill is clearly marked as future, not installed.
- Registry rows distinguish core, setup, Planning OS, Learning OS, Generation OS, and Automation OS skills.

## Workstream 4: Context Matrix Hardening

Problem: the current matrix is useful but not exact enough for implementation.

Tasks:

- Expand OS scope rows for architecture planning, marketing/content, process learning, routine code work, and skill updates.
- Expand Creator scope rows for setup, research, idea generation, template application, production planning, generation planning, output packaging, and learning distillation.
- Add exact workspace paths for creator context, brand context, projects, memory, skills, and overrides.
- Add clear load rules for full, summary, lazy, writes, and never.

Acceptance criteria:

- A future agent can tell which files to load for each workflow without asking.
- Creator-specific context and OS-level context are never confused.
- Private creator data is never required in tracked repo docs.

## Workstream 5: Creator Workspace Override Layout

Problem: `SKILL.local.md` overrides are accepted but not fully reflected in Creator Workspace docs.

Tasks:

- Update Creator Workspace structure to include creator-specific `.claude/skills/<skill-name>/SKILL.local.md`.
- Define what may and may not go in a local override.
- Define promotion criteria from local override to core skill.
- Define where local skill feedback is recorded.

Acceptance criteria:

- Workspace docs show the override path.
- The promotion rule is unambiguous.
- Creator-specific overrides cannot silently modify core skills.

## Workstream 6: Project Output Layout

Problem: output consolidation is partially defined, but the exact project folder layout needs to be deterministic.

Tasks:

- Define the canonical path for each record from Idea Promotion through Output Package.
- Define where draft notes, source refs, assets, upload-ready files, published records, analytics, raw exports, performance summaries, and learnings live.
- Ensure docs match schemas and examples.

Acceptance criteria:

- A future agent can create a project without inventing folders.
- Output Package provenance has a predictable place.
- Published records, analytics, performance summaries, and creator learnings are separated.

## Workstream 7: Tier 0 Creator Recall Rules

Problem: memory contracts exist, but operational Tier 0 recall rules are not complete.

Tasks:

- Define creator `context/MEMORY.md` budget and write rules.
- Define creator `memory/learnings.md` and daily note rules.
- Define what is loaded by default and what is indexed later.
- Keep raw analytics out of default semantic memory.

Acceptance criteria:

- Creator memory is scoped to one Creator Workspace.
- Root OS memory and creator memory are separate.
- Distilled learnings link back to evidence.
- No memory palace terminology is introduced.

## Workstream 8: Drift Checks

Problem: docs, skills, schemas, and examples can drift.

Tasks:

- Add checks for adapter read order.
- Add checks for skill registry coverage.
- Add checks for context matrix coverage.
- Keep existing unit tests and schema validation as the baseline.

Acceptance criteria:

- `python3 -m unittest discover -s tests` passes.
- `python3 -m influencer_os validate examples` passes.
- New drift checks pass.
- Progress docs record the commands and results.

## Workstream 9: Self-Improvement System Skills (ADR 0016)

Problem: the self-learning loop copied its destination files but not the skill that writes them, so it is non-functional.

Tasks:

- Add `skills/wrap-up/SKILL.md` (adapt `meta-wrap-up`): review deliverables, collect feedback, append per-skill learnings, fix skills directly, reconcile registry/matrix, promote durable facts.
- Add `skills/memory-write/SKILL.md` (adapt `meta-memory-write`): bounded, deduped `context/MEMORY.md` writes.
- Add `## Rules` and `## Self-Update` sections to `influencer-os` and `create-influencer`.
- Add one worked `SKILL.local.md` example.
- Name the wrap-up trigger in `AGENTS.md` (already added) so any runtime invokes it by description; no hook.

Acceptance criteria:

- `skills/wrap-up/SKILL.md` and `skills/memory-write/SKILL.md` exist and have registry + context-matrix rows.
- A wrap-up run appends a dated entry under a per-skill section of `context/learnings.md` (test asserts the file gains an entry).
- `memory-write` refuses a write that would push `context/MEMORY.md` past its byte cap (test).
- `grep` finds `## Rules` and `## Self-Update` in both conductor skills.
- At least one `SKILL.local.md` exists on disk; the override load order (base then local) is documented and exercised.

## Workstream 10: Machine-Actionable Conductor Call Graph (ADR 0017)

Problem: the content conductor names no owning skill per phase and implies six skills that do not exist, so its call graph has no verifiable skill-to-skill edges.

Tasks:

- Add `dependencies` frontmatter, a `## Dependencies` table, and a phase-to-owner table with explicit `Skill(skill: "...")` invocations to `skills/influencer-os/SKILL.md` (mirror the reference `00-social-content`).
- Scaffold the six planning/learning producer skills, or have the conductor halt and surface the missing skill at that phase (never pretend it ran).
- Keep `architecture-map.md` and the conductor frontmatter in agreement.

Acceptance criteria:

- `influencer-os/SKILL.md` declares `dependencies` and a phase-to-owner table naming a skill per producing phase.
- A drift check fails if a conductor names a skill that is neither present on disk nor marked `[PLANNED]` with a halt instruction.
- The call graph in `architecture-map.md` matches the conductor frontmatter (consistency check).

## Workstream 11: Propagation Build-Out (ADR 0018)

Problem: only skills-only sync exists; the approved full propagation mechanism must be built.

Tasks:

- Extend `init-creator` (add-client analog) to copy the propagatable set and write workspace `AGENTS.md`/`CLAUDE.md` wrappers.
- Add `update-creators` and extend `sync-creator-runtime` with a backup-protected, conflict-safe batch refresh.
- Add `influencer_os/` helpers for shared copy/backup/diff logic.
- Carry inert zones (scripts/settings/hooks/cron) that stay empty until un-deferred.

Acceptance criteria:

- `update-creators` refreshes baseline skills and preserves `SKILL.local.md`, creator-only skills, and creator state (test).
- `init-creator` scaffolds `.claude/skills/` and matches `docs/creator-workspace-structure.md` (test).
- `creator-workspace.schema.json` includes the `.claude/skills/` directory (closes the missing-directory gap).
- Gated zones are documented as inert and no hook/cron content is copied.

## Workstream 12: Determinism Fixes

Problem: upstream and project boundaries lack schema or resolved provenance.

Tasks and acceptance criteria (each acceptance item is a test):

- Add required `acceptance_criteria` (plus optional `constraints`, `dependencies`) to `project.schema.json`; a project without it fails validation.
- Add `applied_social_template_id` and `video_understanding_pack_ids` to `output-package.schema.json` `source_refs`; a package missing a required provenance ref fails validation. Research provenance resolves transitively through the Project's Idea Promotion.
- Extend project/workspace validation to resolve provenance IDs to real records; a dangling reference fails validation.
- Add a generic `validate record <schema> <path>` CLI and validate each mid-pipeline record in the run flow.

Completed in Phase 1 (Planning OS): the full ADR 0020 research schema slice and
the promotion gate validation (an Idea Promotion must point to a real Idea Queue
Entry and resolvable evidence refs; unresolved human-approved refs warn, while
future automated promotion paths fail). See
`docs/workflows/research-and-ideas-implementation-plan.md`.

## Workstream 13: Validator And Coverage Hardening

Problem: the hand-rolled validator ignores `$ref`/`oneOf`/`anyOf`/`allOf`, and schema-example coverage is a hardcoded list.

Tasks:

- Make `validation.py` honor `$ref`/`oneOf`/`anyOf`/`allOf`, or adopt a real JSON Schema library.
- Derive the schema-example coverage set from disk, not a hardcoded list.

Acceptance criteria:

- A schema that uses `$ref`/`oneOf` fails validation when its constraint is violated (test).
- Adding a new `schemas/*.schema.json` + `examples/*.example.json` pair is covered automatically (test enumerates `schemas/` from disk).

## Workstream 14: Acceptance-Criteria Determinism

Problem: phase exit criteria and readiness gates are written as process verbs with no objective pass/fail.

Tasks:

- Rewrite Phase 0C exit criteria and Creator Readiness gates as runnable checks; remove the self-satisfying "or are explicitly deferred" clause.
- Add a medium-based readiness validator.

Acceptance criteria:

- Each Phase 0C exit criterion names a command or test that passes/fails it.
- A readiness rule is defined in `creator-workspace.schema.json` (or the readiness-validator spec): at `status == generation_ready`, `references/reference-library.json` must contain at least one approved visual asset of a required kind (e.g. `character` or `video-style`). A `generation_ready` workspace missing that asset fails validation (test).

## Workstream 15: Copy-Plan Coverage

Problem: the copy plan never inspected the reference `.claude/agents/` and `.claude/commands/` subsystems.

Tasks:

- Inspect `.claude/agents/` and `.claude/commands/` in the reference and add copy/adapt/defer/reject rows to `agentic-os-copy-plan.md`.
- If adopting the subagent pattern for producer skills, record it in an ADR (see the subagent decision in `architecture-map.md`).

Acceptance criteria:

- The copy plan has rows for `.claude/agents/` and `.claude/commands/`.
- The `architecture-map.md` subagent decision references the outcome.

## Deliverables

Required:

- Updated `docs/os-construction/context-matrix.md`.
- Updated `docs/os-construction/skill-registry.md`.
- Updated `docs/creator-workspace-structure.md`.
- Updated `docs/os-construction/agentic-os-parity-plan.md` if gaps change.
- Updated `docs/os-construction/progress.md`.
- Tests or scripts for drift checks, if implemented.

Optional:

- Excalidraw comparison scene.
- ADR for hooks/cron if the agent believes they should move earlier.

## Handoff Notes

Do not start Planning OS implementation until parity hardening is done.

The first implementation slice after parity hardening should be chosen from:

- master intake import workflow,
- Tier 0 creator recall,
- project/output package layout helpers,
- Research Findings and Idea Queue workflow.
