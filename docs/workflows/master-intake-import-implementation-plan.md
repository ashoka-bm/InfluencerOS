# Master Intake Import Implementation Plan

Date: 2026-07-03

Status: **Complete (2026-07-03).** Phase 1 (Planning OS) slice 1 per the
roadmap. The user approved all four decisions below on 2026-07-03 and the
slice landed the same day; the verification record lives in
`docs/os-construction/progress.md`. This plan is retained as the slice
record.

## Goal

Give Creator Setup a deterministic command that imports a master intake (or
any other setup source material) into a Creator Workspace: the file is copied
into `sources/`, and a `source_intakes` provenance entry is recorded in
`creator-workspace.json` (ADR 0002).

This closes the first entry in the creator-setup Known Schema And CLI Gaps
list ("no master intake import command") and gives the `create-influencer`
conductor's phase 1 (Intake and provenance) a CLI seam instead of prose.

## Module Boundary

In scope:

- `import-intake` CLI command: copy one source file into the workspace and
  append a schema-valid `source_intakes` entry with
  `extraction_status: "pending"`.
- `set-intake-status` CLI command: move one intake's `extraction_status`
  forward (`pending` -> `drafted` -> `reviewed`) so the drafting and review
  steps of Creator Setup record their progress deterministically.
- Provenance resolution in `validate workspace`: every
  `source_intakes[].path` must resolve to a real file inside the workspace
  (same fail-closed pattern as the Phase 0C project provenance checks).
- Doc, skill, and fixture updates listed below.

Out of scope (stays in later slices or later phases):

- Guided interview command.
- LLM derivation of the draft foundation files from the intake. That is the
  `create-influencer` conductor's job (subskills already exist); this slice
  only gives it the import seam.
- Markdown completeness validation and reference-asset file-existence
  validation (slice 2: creator readiness validation).
- Provider-neutral prompt file generation command.
- Any workspace `status` transition. Import never changes workspace status;
  acceptance stays a human gate.

## Workflow Contract

Deterministic boundary per `AGENTS.md`:

- Inputs: an existing Creator Workspace; one existing source file; a
  `--source-type` from the schema enum (`breakdown`, `interview`, `handoff`,
  `import`, `notes`); required `--notes`; optional `--source-id`; optional
  `--imported-on` (defaults to today).
- Outputs: the file copied under the type-mapped `sources/` subdirectory; one
  new `source_intakes` entry in `creator-workspace.json` with
  `extraction_status: "pending"`.
- Schema: existing `creator-workspace.schema.json` `source_intakes` items.
  (Initially unchanged; after the adversarial review the `path` field was
  schema-pinned under `sources/` — see Adversarial Review below.)
- Provenance links: the `source_intakes` entry is the provenance record —
  source id, type, workspace-relative path, import date, extraction status,
  notes (ADR 0002 consequence: "record the source intake path, date, and
  extraction notes").
- Validation: the updated manifest is schema-validated before any write;
  `validate workspace` resolves every intake path to a real file.
- Approval gate: none for import itself (local file copy, no provider calls).
  The human gates stay where they are: `set-intake-status reviewed` records
  extraction review, and workspace status transitions record foundation
  acceptance.

## CLI Draft

```bash
python3 -m influencer_os import-intake <source-file> \
  --creator-workspace <workspace-path> \
  --source-type breakdown \
  --notes "Master breakdown provided by user." \
  [--source-id source_luna_fit_breakdown_002] \
  [--imported-on 2026-07-03]
```

Behavior:

1. Load and schema-validate `creator-workspace.json`.
2. Verify the source file exists and is a regular file.
3. Map `--source-type` to a destination directory (see mapping below);
   destination filename is the source basename.
4. Fail-closed preconditions, checked before any write: the destination path
   must not already exist; the source id must not already be in
   `source_intakes`. No overwrite flag in v1.
5. Auto-generate the source id when `--source-id` is omitted:
   `source_<creator_slug_with_underscores>_<source_type>_<NNN>` where `NNN`
   is the next zero-padded sequence number across existing entries. No
   randomness, no timestamps beyond the `imported_on` date field.
6. Build the updated manifest in memory, validate it against the schema,
   then copy the file and write the manifest.
7. Print the source id, the destination path, and the next-phase hint
   (`Next phase: derive foundation drafts (create-influencer)`).

Source-type to destination mapping (from the creator-setup Source Import
section):

| `source_type` | Destination |
| --- | --- |
| `breakdown` | `sources/intakes/` |
| `interview` | `sources/intakes/` |
| `handoff` | `sources/imports/` |
| `import` | `sources/imports/` |
| `notes` | `sources/notes/` |

Interview transcripts are master-intake material per the creator-setup intake
modes, so they land beside breakdowns.

```bash
python3 -m influencer_os set-intake-status <workspace-path> <source-id> <drafted|reviewed>
```

Behavior: statuses are ordered `pending < drafted < reviewed`; a move is
allowed only to a strictly higher status (skipping `drafted` is allowed).
Unknown source ids and backward moves fail with a clear error. The manifest
is schema-validated before the write.

## Validation Changes

`validate_creator_workspace` gains one check: every `source_intakes[].path`
must exist inside the workspace. Missing intake files fail validation naming
the missing paths. This runs on real workspaces (`validate workspace`), not
on the bare example JSON, matching how existing workspace checks work.

Hardened after the 2026-07-03 adversarial review (see Adversarial Review
below): the check also rejects absolute paths and `..` escapes after
`resolve()` (containment failure is a distinct error from a missing file),
and the validator's `date` format now requires a real calendar date via
`datetime.date.fromisoformat`, not just the YYYY-MM-DD shape.

## Adversarial Review (2026-07-03)

Post-landing review of the slice commits found two confirmed issues, both
reproduced, fixed, and covered by negative tests the same day:

- P1 — intake provenance was not contained to the workspace:
  `validate workspace` accepted `source_intakes[].path` values like
  `../../outside-intake.md` or absolute paths, breaking the local-first
  provenance contract. Fixed in `_validate_source_intakes` with a
  resolve-based containment check; escaping paths fail with a dedicated
  error. Tests: `test_validate_workspace_rejects_intake_path_escaping_the_workspace`,
  `test_validate_workspace_rejects_absolute_intake_path`.
- P2 — `--imported-on` accepted impossible calendar dates (`2026-99-99`):
  the validator's `date` format was shape-only. Fixed at the validator seam
  so every `format: "date"` field in every schema is calendar-checked, with
  the shape regex retained (3.11+ `fromisoformat` alone would loosen it).
  Tests: `test_impossible_calendar_date_fails_before_any_write`,
  `test_date_format_rejects_impossible_calendar_dates`.

Follow-up (2026-07-03, user-approved): P1 containment is also enforced
declaratively. `creator-workspace.schema.json` pins `source_intakes[].path`
with `^sources/(intakes|imports|notes)/[^/]+$`, so traversal, absolute
paths, wrong directories, and nested paths fail at the schema seam in any
context that validates the record — not only in `validate workspace`. The
behavioral `resolve()` containment check remains as the second layer for
schema-conforming paths that escape via symlinks
(`test_validate_workspace_rejects_symlinked_intake_escaping_the_workspace`);
schema-seam coverage lives in
`test_workspace_intake_paths_are_pinned_under_sources`.

## Skill And Doc Changes

- `skills/create-influencer/SKILL.md` phase 1 (Intake and provenance) names
  the commands: import each source with `import-intake`; record extraction
  progress with `set-intake-status`. No dependency-frontmatter change, so the
  call-graph drift check is unaffected.
- `docs/workflows/creator-setup.md`: the Source Import section names the
  command; the Known Schema And CLI Gaps list drops "no master intake import
  command".
- `docs/os-construction/progress.md`: record the verification commands and
  results when the slice lands.
- `README.md`, `ARCHITECTURE.md`, and `docs/os-construction/repository-map.md`:
  document the two new commands — the full CLI is documented in all three
  places as of the 2026-07-03 post-closeout pass.
- No skill-registry or context-matrix changes: no new skill is added, and the
  Creator setup workflow row already covers these writes.
- Real creator workspaces pick up the skill edit via
  `python3 -m influencer_os update-creators` (workspaces are gitignored; the
  user runs this when they have live creators).

## Fixture Impact

`examples/creator-workspace.example.json` declares an intake at
`sources/intakes/luna-fit-breakdown.md`, but no such file exists in the
scaffolded verification workspace, so the new provenance check would fail the
existing full-workflow verification. Fix as part of this slice:

- Add `examples/sources/luna-fit-breakdown.example.md` — a short, clearly
  synthetic master breakdown for the luna-fit example creator.
- The full-workflow verification copies it to
  `.tmp/creators/luna-fit/sources/intakes/luna-fit-breakdown.md` before
  `validate workspace`, and dogfoods the new command by importing a second
  source via `import-intake`.

## Test Plan

Behavior tests at the CLI/function seam (new `tests/test_intake_import.py`,
plus updates to existing workspace-validation tests):

1. `import-intake` copies the file to the type-mapped folder and appends a
   schema-valid entry with `extraction_status == "pending"`; the workspace
   validates afterward.
2. Each `source_type` routes to its mapped destination directory.
3. Auto-generated source ids are deterministic and increment; an explicit
   `--source-id` is respected.
4. A duplicate destination filename fails before any write; the manifest is
   unchanged.
5. A duplicate source id fails before any write.
6. `--imported-on` is respected; omitted, the entry carries today's date.
7. `set-intake-status` moves `pending -> drafted -> reviewed`; a backward
   move fails; an unknown source id fails.
8. `validate workspace` fails when a `source_intakes[].path` names a missing
   file, and names the path in the error.

## Success Condition

The slice is done when every check below passes and is recorded in
`docs/os-construction/progress.md`:

- `python3 -m unittest discover -s tests` passes, including the new tests.
- `python3 -m influencer_os validate examples` passes.
- The updated full-workflow verification passes end to end, including an
  `import-intake` call and the intake-path provenance check.
- `rg -n "no master intake import command" docs/workflows/creator-setup.md`
  finds nothing (the phrase survives only as history in this plan and the
  progress log).

This slice is the first runnable piece of the roadmap Phase 1 exit criterion
"Creator Workspace setup works from a reviewed intake"; the criterion becomes
fully runnable when slice 2 (creator readiness validation) lands.

## Approved Decisions (User-Approved 2026-07-03)

Do not reopen these without user approval:

1. Scope: include `set-intake-status` alongside `import-intake`.
   Recommendation: yes — it completes the provenance lifecycle
   (`pending`/`drafted`/`reviewed`) at the same deterministic seam and is
   small; without it the drafting and review steps go back to hand-editing
   JSON.
2. Provenance resolution: add the intake-path existence check to
   `validate workspace`. Recommendation: yes — matches the Phase 0C
   fail-closed provenance pattern; requires the fixture fix above.
3. Source-type destination mapping as tabled above, with `interview` landing
   in `sources/intakes/` and `handoff` in `sources/imports/`.
   Recommendation: accept.
4. Command name `import-intake`. Recommendation: accept — mirrors the
   roadmap slice name and the `source_intakes` schema field.
