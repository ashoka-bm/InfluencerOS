# Creator Readiness Validation Implementation Plan

Date: 2026-07-03

Status: **Complete (2026-07-03).** Phase 1 (Planning OS) slice 2 per the
roadmap. The user approved all six decisions below on 2026-07-03 and the
slice landed the same day; the verification record lives in
`docs/os-construction/progress.md`. This plan is retained as the slice
record.

## Goal

Make the creator-setup readiness gate machine-checkable: a workspace claiming
`content_ready`, `generation_ready`, or `active` must actually satisfy the
medium-based blockers in `docs/workflows/creator-setup.md`, enforced
deterministically by `validate workspace`. This completes the
architecture-map marker "full medium-based validator lands with the Phase 1
readiness slice" (workstream 14 built only the generation-ready
visual-asset gate).

## Module Boundary

In scope:

- Status-keyed readiness checks inside `validate_creator_workspace`,
  collecting every failed blocker into one error.
- Foundation-population checks for `context/` and `brand_context/` files
  (closes the "no markdown completeness validation" gap for readiness
  statuses).
- Reference-asset file-existence and prompt-existence checks (closes the
  "no file-existence validation for reference asset paths" gap).
- Medium-to-required-asset-kind mapping driven by
  `creator-profile.json` `content_strategy.content_mediums`.
- Schema pinning of reference-library `path` and `prompt_path` under
  `references/` (same defense-in-depth as the intake `sources/` pin).
- Resolution of `creator-profile.json` `reference_refs` primary asset ids
  against the reference library (established provenance-resolution pattern).
- Doc, skill, and fixture updates listed below.

Out of scope (later slices or explicitly deferred):

- Guided interview command.
- Review/acceptance metadata beyond workspace status: the
  `foundation_review -> content_ready` status transition remains the
  human-acceptance record.
- Provider-neutral prompt file generation command.
- Brand-file word-count caps (remain authoring guidance; see Decision 2).
- Judgment-quality checks (whether the content is any good) — this slice
  checks presence, placement, and lifecycle, not quality.

## Readiness Checks Draft

All checks run inside `validate workspace`, keyed on `status`. `draft` and
`foundation_review` add no new requirements. Failures collect into a single
error listing every blocker, so one run reports the full gap list (the
create-influencer conductor mirrors it into `progress/setup-checklist.md`).

At `content_ready`, `generation_ready`, and `active`:

1. Foundation files populated and mechanically shaped: `context/SOUL.md`, `context/USER.md`,
   `context/MEMORY.md`, `brand_context/identity.md`, `brand_context/soul.md`,
   `brand_context/personal-brand.md`, `brand_context/voice-samples.md` each
   contain non-heading content beyond their `init-creator` scaffold, and none
   contains a `TBD` placeholder token. Rich brand-context files also need the
   required template sections and lower-bound word/sample floors; this catches
   sentence stubs and older thin files without replacing human quality review.
2. Always-loaded context byte caps (documented hard maxes):
   `context/SOUL.md` <= 3,072 bytes, `context/USER.md` <= 1,536 bytes,
   `context/MEMORY.md` <= 2,500 bytes (matching the `memory-write` cap).
3. Source provenance recorded: at least one `source_intakes` entry. A
   generated persona records the user's brief as a `notes` intake during
   create-influencer phase 1.
4. Required asset kinds present: for every medium in
   `content_strategy.content_mediums`, the reference library contains at
   least one non-retired asset of each required kind (any lifecycle status,
   `planned` included — a planned entry is a named obligation):

   | Medium | Required asset kinds |
   | --- | --- |
   | `text` | none (non-visual identity policy lives in the profile) |
   | `image` | `character`, `brand` |
   | `video` | `character`, `location`, `outfit`, `video_style`, `brand` |
   | `audio` | `voice` |
   | `carousel` | `brand`, `video_style` |
   | `story_sequence` | `brand`, `video_style` |

5. Asset file existence by lifecycle status: `user_provided`, `generated`,
   and `approved` assets must have an existing `path`; `prompted` assets must
   declare a `prompt_path` and it must exist; `planned` assets may omit
   `prompt_path`, but a declared one must exist; `retired` assets are exempt.
   Existence checks also apply the workspace-containment rule (resolve-based,
   symlink-safe), mirroring the intake check.

At `generation_ready` (in addition to the above):

6. Every required kind for the visual mediums (`image`, `video`, `carousel`,
   `story_sequence`) must be present at `prompted` or later — `planned` is no
   longer sufficient, matching the status definition ("has the reference
   assets or asset prompts needed").
7. The existing workstream-14 gate stays: at least one `approved` asset of
   kind `character` or `video_style`.

At `active`: content_ready-level checks only (an active text-first creator
never passes through `generation_ready`).

All statuses (not readiness-keyed):

8. `creator-profile.json` `reference_refs` primary asset ids resolve to
   assets in the reference library (dangling ids fail validation).
9. Schema: `reference-library.schema.json` pins `path` and `prompt_path`
   with `^references/[a-z0-9-]+/[^/]+$`.

## Workflow Contract

- Inputs: the Creator Workspace on disk — manifest status, creator profile
  content strategy, reference library, foundation markdown files, source
  intakes.
- Outputs: none written; `validate workspace` passes or fails with the full
  blocker list. `progress/setup-checklist.md` stays the human-readable
  mirror, maintained by the create-influencer conductor.
- Schema/template: existing schemas plus the `references/` path pin; the
  scaffold texts in `creator_workspaces.MARKDOWN_SCAFFOLDS` define the
  "unpopulated" baseline.
- Provenance links: reference_refs resolution and the existing intake checks.
- Validation: `python3 -m influencer_os validate workspace <path>`.
- Approval gate: unchanged — status transitions stay human decisions; this
  slice only verifies that a claimed status is backed by real material.

## Fixture Impact

- `examples/creator-workspace.example.json` has `status: "draft"`, so
  `validate examples` and the full-workflow verification are unaffected by
  the readiness checks.
- `examples/reference-library.example.json` gains `outfit` and `brand`
  entries (as `prompted`, with `prompt_path`s) so the example library
  satisfies the video mapping, and its existing paths already match the
  schema pin.
- `tests/test_cli.py` `ReadinessGateTests` scaffold `generation_ready`
  workspaces; they gain a helper that populates foundation files with sample
  text and places asset/prompt files so the new checks pass, plus negative
  variants per check.
- If `examples/creator-profile.example.json` `reference_refs` ids do not all
  resolve against the example library, either the profile or the library
  example is corrected (they should already agree).

## Test Plan

Behavior tests (new `tests/test_readiness_validation.py`):

1. A `draft` workspace with scaffold-only foundation files validates
   (no readiness checks fire).
2. A `content_ready` workspace with populated files, an intake, and mapped
   asset kinds validates.
3. Each blocker fails individually at `content_ready`: scaffold-only file,
   sentence-stub foundation file, missing required foundation sections, too few
   voice samples, `TBD` token, oversized `context/` file, zero intakes, missing
   required kind for a declared medium.
4. One failing run reports multiple blockers in a single error.
5. Asset existence: an `approved` asset with a missing `path` fails; a
   `prompted` asset without `prompt_path` fails; a `planned` asset without
   `prompt_path` passes; a `retired` asset with a dead path passes.
6. A symlinked asset path resolving outside the workspace fails containment.
7. `generation_ready`: a required kind still at `planned` fails; the
   workstream-14 approved-visual gate still enforced (existing tests keep
   passing).
8. An `active` text-first creator with no visual assets validates.
9. Dangling `reference_refs` primary asset id fails at any status.
10. Schema: escaping or misplaced `path`/`prompt_path` values fail record
    validation (mirroring the intake schema tests).

## Success Condition

The slice is done when every check below passes and is recorded in
`docs/os-construction/progress.md`:

- `python3 -m unittest discover -s tests` passes, including the new tests.
- `python3 -m influencer_os validate examples` passes.
- The full-workflow verification passes unchanged (draft-status workspace).
- A dogfood run: flipping the verification workspace to `content_ready`
  without populating foundation files fails listing the blockers; after
  populating files and assets per the checks, it validates.
- `rg -n "no file-existence validation for reference asset paths|no markdown completeness validation" docs/workflows/creator-setup.md`
  finds nothing (both gaps move to the Closed gaps list).

This completes the roadmap Phase 1 exit criterion "Creator readiness gates
work" as a runnable check, together with slice 1's intake criterion.

## Adversarial Review (2026-07-03)

Post-landing review of the slice commit found two confirmed issues and one
test gap, all reproduced, fixed, and covered by negative tests the same day:

- P1 — primary reference ids resolved without kind or requiredness checks:
  a `content_ready` video creator validated with empty
  `primary_character_asset_ids`/`primary_location_asset_ids` and a `brand`
  asset named as the video-style primary. Fixed: `reference_refs` ids now
  resolve through an id-to-asset map with type enforcement at every status;
  at readiness statuses, mediums make their primary fields mandatory
  (`image`/`video` require character primaries, `video` requires a location
  primary, `video`/`carousel`/`story_sequence` require a video-style
  primary), retired primaries are blockers, and `generation_ready` requires
  primaries at `prompted` or later. `primary_video_style_asset_id` became
  schema-optional so text-first creators without visual assets can validate.
- P2 — asset `source.source_ref` provenance could dangle: every asset
  pointing at `sources/intakes/does-not-exist.md` still validated at
  `content_ready`. Fixed: non-retired assets' `source_ref` must be either a
  recorded intake `source_id` or a workspace-contained existing file (same
  resolve-based containment as intake and asset paths); free-text refs are
  no longer accepted for non-retired assets.
- Test gap — the text-first test kept all visual assets in place. Reworked:
  it now strips the library to a single voice asset, empties the character
  and location primaries, and drops the video-style primary, proving the
  non-visual path end to end.

## Approved Decisions (User-Approved 2026-07-03)

Do not reopen these without user approval:

1. Enforcement shape: all readiness checks live inside `validate workspace`,
   keyed on status, collecting every failed blocker into one error.
   Recommendation: accept — no new command; one run yields the complete
   blocker list for the setup checklist.
2. Foundation completeness = populated (non-scaffold, non-heading content) +
   no `TBD` token + hard byte caps on the three `context/` files. Brand-file
   word-count targets stay authoring guidance, not validation.
   Recommendation: accept — byte caps are documented hard maxes; word counts
   are soft targets and would punish good long-form foundations.
3. `content_ready` and above require at least one `source_intakes` entry;
   generated personas record the user brief as a `notes` intake.
   Recommendation: accept — keeps provenance discipline universal.
4. The medium-to-required-asset-kinds mapping table as drafted (text maps to
   no required assets; video maps to the five-kind set; carousel and
   story_sequence map to `brand` + `video_style`; audio maps to `voice`).
   Recommendation: accept — it is the deterministic subset of the
   creator-setup blocker lists expressible through the asset-type enum.
5. Status ladder strictness: kinds may be `planned` at `content_ready`; must
   be `prompted` or later at `generation_ready`; `active` enforces
   content_ready-level checks only. Recommendation: accept — matches the
   documented status definitions.
6. Reference-asset hardening: schema-pin `path`/`prompt_path` under
   `references/`, enforce lifecycle-appropriate file existence with
   symlink-safe containment, and resolve `reference_refs` primary ids.
   Recommendation: accept — extends the slice 1 adversarial-review pattern
   to the reference library before Phase 3 builds generation on top of it.
