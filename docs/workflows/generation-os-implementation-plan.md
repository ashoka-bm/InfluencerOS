# Generation OS Implementation Plan (Phase 3)

Last updated: 2026-07-05

Status: **Complete (2026-07-06).** The operator's 2026-07-06 directive to
"implement all of phase three based on the planning that we have done"
approved the five execution decisions below on their recommendations —
including Decision 3's recommendation that no real (paid) provider adapter
ships by default — recorded in ADR 0023
(`docs/adr/0023-generation-provider-boundary.md`). All five slices executed
with three batch-boundary gpt-5.5 adversarial reviews and fix batches; the
five runnable exit criteria pass and the closeout run is recorded in
`docs/os-construction/progress.md`. The first real provider adapter remains
a separate operator-chosen batch (Decision 3).

## Goal

Generate or import media through approved providers while preserving
provenance: a provider adapter boundary that can never bypass the
exact-approval gate, an approval record for every provider call or batch,
provenance from every generated or imported asset back to its plan and
approval, and a quality gate between generation and packaging.

Phase 3 implements the roadmap's Generation OS phase and executes the
already-accepted copy-plan decision (row 75): "Add a provider registry only
when real adapters are introduced." It builds on ADR 0013 (reference asset
lifecycle), ADR 0007 (output package platform adaptations), ADR 0012
(project-scoped work), and adapts the ADR 0022 connector-layer mechanics under
the opposite approval model.

A deliberate property of this plan: **every slice is buildable and testable
with zero paid provider calls.** Slices 1–5 ship the registry, approval
workflow, import path, provenance chain, and quality gate against a
deterministic mock adapter and imported fixtures. The first real provider
adapter is its own user-approved batch (Decision 3) and can land any time
after slice 2 without reopening the machinery.

## Module Boundary

Inputs (all exist today):

- provider-neutral Base Video Generation Plans
  (`base-video-generation-plan.schema.json`, Phase 1 slice 6), carrying
  `generation_status: planned_not_generated` and
  `approval_required_before_generation: const true`,
- format-specific production plans and their upstream provenance chain
  (Project -> Idea Promotion -> findings/evidence),
- the Reference Library (`reference-library.schema.json`) with its
  already-built asset lifecycle
  (`planned/prompted/user_provided/generated/approved/retired`) and
  `source.source_type` provenance enum,
- Output Package registration (`register-output-package`, Phase 1 slice 7)
  with `provider_boundary.generation_status` and `upload_ready` assets,
- the provider boundary policy (`docs/provider-boundary.md`) and the ADR 0022
  connector layer as the registry/env-gating template.

Outputs (new at-rest records, projections, and one runtime package):

- `influencer_os/providers/` — the generation provider adapter boundary
  (registry, availability, dispatch; exact-approval enforced structurally),
- `projects/<project-slug>/generation/approval-records/*.json`
  (GenerationApprovalRecord),
- `projects/<project-slug>/generation/assets/` plus
  `projects/<project-slug>/generation/asset-manifest.json`
  (per-asset provenance ledger for generated and imported assets),
- `projects/<project-slug>/generation/quality-reviews/*.json`
  (QualityReview),
- Reference Library generation parity: reference assets generated or imported
  through the same approval + provenance path, with `source.source_ref`
  pointing at the approval record,
- Generation OS rows in `workspace-library/index/influencer-os.sqlite`
  (extends `rebuild-index`; lands after Phase 2 slice 5 patterns).

Not in scope (unchanged deferrals):

- publishing, scheduling, platform adapters, post-production treatments,
  analytics (AGENTS.md operating rules; Phase 2 owns analytics),
- scheduled or unattended generation (Phase 4 Automation OS),
- weakening any generation approval gate: key presence is **never** standing
  approval for generation (ADR 0022's carve-out is research-acquisition only),
- typed subagents for generation producers (copy-plan row 82 stays deferred
  unless a Phase 3 skill actually reaches for the pattern; that adoption is
  its own divergence-test event and ADR),
- Command Centre, dashboards, board UI.

## Entry Criteria Verification (2026-07-05)

The roadmap's three entry criteria, verified against the repo today:

1. **Planning OS produces stable provider-neutral Base Video Generation
   Plans.** Pass — Phase 1 slice 6 landed 2026-07-04 with schema, examples,
   and at-rest project validation.
2. **Output Package provenance is stable.** Pass — Phase 1 slice 7 plus review
   hardening landed 2026-07-04; `source_refs` resolution is validated at rest.
3. **Provider approval policy is represented in records and UI/CLI prompts.**
   Pass at the policy level: `approval_required_before_generation: const true`
   (base-video-generation-plan, output-package),
   `provider_calls_require_approval: const true` (reference-library,
   creator-workspace), and `docs/provider-boundary.md`. The approval *record*
   does not exist yet — that is Phase 3 slice 2's deliverable, not an entry
   gap.

Note: Phase 3 entry does **not** depend on Phase 2 artifacts. Planning now is
safe; execution sequencing relative to Phase 2 is a coordination decision
(below), not an entry-criteria question.

## Success Condition — Runnable Exit Criteria

Per the roadmap Acceptance-Criteria Policy, the Phase 3 exit criteria are
rewritten as runnable checks (workstream-14 pattern). Phase 3 exits when every
check below passes and is recorded in `progress.md`:

1. **Provider adapter boundary exists.**
   `python3 -m influencer_os list-providers` reports each registered
   generation provider with capability, key presence, and
   `approval_model: exact_approval` — never `standing`. A probe test asserts
   the providers package exposes no code path that dispatches without an
   approved GenerationApprovalRecord id, and that key presence alone never
   marks a generation provider auto-approved (the inverse of the ADR 0022
   research-connector test).
2. **Approval workflow records exact calls or batches.**
   `record-generation-approval <project-dir> <request.json>` writes a
   validating GenerationApprovalRecord naming the exact provider, model,
   prompt/plan refs, scope (`single_call` or `batch` with a bounded call
   count), and the verbatim user approval statement. Dispatch (mock adapter in
   tests) refuses a missing, unapproved, consumed, or cancelled record (test).
   A hand-edited at-rest record with a dangling plan ref fails
   `validate project` (test).
3. **Generated and imported assets store provenance.**
   Every file under `generation/assets/` has an asset-manifest row binding
   asset -> approval record (generated) or import origin (imported) -> plan
   prompt ref -> resulting artifact path. `import-generated-asset` records
   origin, tool/provider when known, license/attribution fields when
   applicable. An asset on disk without a manifest row, or a manifest row
   whose refs do not resolve, fails `validate project` (test). Reference
   Library parity: a `generated` reference asset whose `source.source_ref`
   does not resolve to an approval record fails `validate workspace` (test).
4. **Quality checks run before packaging.**
   `create-output-package`/`register-output-package` fail when an
   upload-ready media asset originating from `generation/` lacks a passing
   QualityReview covering the closed checklist (Decision 5); the same
   invariant re-checked at rest — a hand-edited passing review flipped to
   failing makes `validate project` fail on the packaged project (test).
5. **Output Packages reference final artifacts.**
   On a fixture project driven mock-generation -> quality review ->
   packaging, every `upload_ready` media asset resolves through the asset
   manifest to its approval record and plan; `validate project` passes
   end-to-end and the full-workflow replay script covers the chain (test).

Standing checks that must stay green through every slice: the same list as
the Phase 2 plan (unittest discovery, `validate examples`, drift checks,
fixture workspace validation, `update-creators` sync).

## Implementation Sequence

Roadmap slice order, refined. Slices 1–2 are the boundary and the gate;
slice 3 is the immediately-useful import path (no adapter needed); slice 4
binds provenance and projections; slice 5 closes the loop into packaging.

### Slice 1: Provider Registry And Adapter Boundary

- New package `influencer_os/providers/` (Decision 1): `registry.py`
  (provider rows: id, capability image/video/audio/render, env key, cost
  notes, `approval_model: exact_approval` const), availability detection
  reusing the ADR 0022 `env.py` helpers (shared, not duplicated), and a
  dispatch seam that **requires an approval-record id as a positional
  argument** — the no-approval-no-call rule enforced by shape, not
  convention.
- One deterministic `mock` adapter (test double, writes fixture bytes +
  echo metadata); no real provider adapter in this slice (Decision 3).
- CLI `list-providers` mirroring `list-connectors` semantics.
- Kill switch honored: `INFLUENCER_OS_DISABLE_PAID_CONNECTORS=1` (or a
  dedicated generation switch — settled in Decision 1) disables dispatch
  even with an approved record.
- Docs: `docs/provider-boundary.md` gains the registry section;
  architecture-map and copy-plan row 75 status updated.
- Tests: registry availability matrix, no-standing-approval probe,
  dispatch-refuses-without-approval, kill-switch probe.

### Slice 2: Generation Approval Record Schema And Workflow

- New schema `generation-approval-record.schema.json` (Decision 2): id,
  project or reference-library scope, exact provider id + model, plan and
  prompt refs, scope `single_call | batch` with `max_calls` for batches,
  requested asset kinds/counts, verbatim `user_approval_statement`,
  `approved_at`, status ladder `draft -> approved -> executed | cancelled`,
  `resulting_asset_ids` filled at execution, single-use consumption rule.
- CLI `record-generation-approval`: validates refs resolve (plan exists,
  project status `ready_for_generation` or later; reference-library scope
  resolves the asset entry), writes under `generation/approval-records/`.
- Skill `skills/request-generation-approval/SKILL.md` (interpretive):
  assembles the exact call/batch from the Base Video Generation Plan for
  the user to approve — restating the provider-boundary rule that a general
  desire to create content is not approval; same-batch registry,
  context-matrix, conductor, and architecture-map rows.
- Conductor phase 10 ("Generation Approval Gate") rewires from a bare manual
  gate to this skill + record; the gate stays human — the skill only
  packages what the human approves.
- At-rest parity in `validate project`: dangling plan/prompt refs, duplicate
  approval ids, executed records with empty `resulting_asset_ids`.
- Tests: happy path, unapproved-dispatch refusal, batch cap, consumption
  (second dispatch on a `single_call` record fails), cancelled record,
  at-rest hand-edit probes.

### Slice 3: Import-Generated-Asset Workflow

Covers the near-term reality: assets generated outside InfluencerOS
(provider web UIs, user-supplied media) enter with full provenance and no
adapter dependency.

- CLI `import-generated-asset`: copies a local file into
  `generation/assets/` (containment/symlink checks inherited from
  `register-output-package` hardening), writes the manifest row (Decision 4)
  with `origin: imported | user_provided`, tool/provider when known, and the
  license/attribution fields adapted from the reference `tool-image-search`
  manifest (source, creator, license, warnings) when applicable.
- Reference Library parity: `--reference-asset <id>` routes the same import
  into `references/<kind>/` and updates the asset's `source` block and
  `asset_status` per ADR 0013.
- Skill `skills/import-generated-asset/SKILL.md` (thin wrapper,
  `create-output-package` pattern); same-batch registry/matrix/conductor
  rows.
- Never committed: imported media stays under `workspace-library/` (git
  rules unchanged).
- Tests: import happy path, containment escape probe, manifest row
  integrity, reference-asset route, unknown-license warning captured not
  guessed.

### Slice 4: Asset Provenance Capture And Projections

- Asset manifest contract finalized (Decision 4):
  `generation/asset-manifest.json` ledger; every generated-path execution
  (mock adapter now, real adapters later) appends rows atomically with
  approval-record id, plan prompt ref, provider call metadata (provider,
  model, params hash, timestamps), and artifact path + content hash.
- `validate project` chain checks both directions: every asset file has a
  row; every row's refs resolve (approval record, plan, artifact on disk) —
  the bidirectional reconciliation guard from Phase 2.
- Output Package binding: `upload_ready` media assets sourced from
  `generation/` carry a manifest ref so packaging resolves provenance
  transitively (schema delta below).
- `rebuild-index` extension for the three new record types, following the
  Phase 2 slice 5 pattern (unique ids, delete-and-rebuild equivalence,
  cross-creator scoping). **Coordination point: lands after Phase 2 slice 5
  merges.**
- Tests: ledger append atomicity, bidirectional reconciliation, orphan file
  probe, index rebuild equivalence.

### Slice 5: Quality Review Checklist And Packaging Gate

- New schema `quality-review.schema.json` (Decision 5): review id, scope
  (asset ids or whole batch), the closed checklist — identity consistency
  against approved Reference Library assets, continuity against the plan's
  shot sequence, technical conformance (duration/aspect/resolution for the
  universal short-form target), creator boundary compliance (Creator Profile
  boundaries) — each item pass/fail/not_applicable with reviewer notes,
  overall verdict, reviewed_at.
- Skill `skills/review-generated-assets/SKILL.md` (interpretive): walks the
  checklist against the manifest and plan; blocking verdict semantics per
  Decision 5. The reference's blocking designer-audit pattern, adapted to
  records.
- Packaging gate: `create-output-package`/`register-output-package` enforce
  a passing review for generated/imported media (exit criterion 4); at-rest
  parity in `validate project`.
- Advisory WARN: a project in `generated` status with manifest assets but no
  quality review (durable at-rest signal, not a flag).
- Full-workflow replay extension in `.tmp/`: ... -> production plan ->
  **record-generation-approval -> mock generation / import-generated-asset
  -> review-generated-assets -> create-output-package** -> register ->
  (Phase 2 chain when merged) -> board -> prune.

## Creator Workspace Layout (Phase 3 additions in context)

```text
workspace-library/creators/<creator-slug>/
  projects/<project-slug>/
    plan/
      generation-plan.json               # Phase 1 (input)
    generation/                          # NEW (Phase 3)
      approval-records/                  # slice 2 writes here
        gen_approval_<...>.json
      assets/                            # slices 1/3 write here (mock/import)
        <artifact files>
      asset-manifest.json                # slice 4 ledger
      quality-reviews/                   # slice 5 writes here
        quality_review_<...>.json
    output-package/                      # Phase 1; slice 5 gates packaging
  references/                            # ADR 0013; slice 3 import parity
    reference-library.json               # source.source_ref -> approval record
```

`docs/creator-workspace-structure.md` and `project.schema.json`
`project_paths` gain the `generation/` subtree in slice 2 (first writer).

## Schema Deltas

- New: `generation-approval-record.schema.json` (slice 2),
  `generation-asset-manifest.schema.json` (slice 4),
  `quality-review.schema.json` (slice 5) — each with examples and drift-pin
  coverage the change it ships.
- `output-package.schema.json`: `upload_ready[]` gains an optional
  `generation_manifest_ref` (required when
  `provider_boundary.generation_status != planned_not_generated` for media
  roles — validator-enforced, shape stays backward-compatible) (slice 4).
- `project.schema.json`: `project_paths` adds the pinned `generation/`
  paths; no new statuses — `ready_for_generation -> generated` is the only
  Phase 3 transition and both already exist.
- `reference-library.schema.json`: no shape change expected;
  `source.source_ref` semantics documented to accept an approval-record id
  (slice 3).
- `base-video-generation-plan.schema.json`: no shape change;
  `generation_status` moves `planned_not_generated -> generated | imported`
  through the slice 2/3 writers only.

## Guard Rules Carried Into Every Slice

The Phase 2 plan's seven standing guard rules apply verbatim (writer/at-rest
parity, sibling guards on new record directories, one shared writer for
multi-path flows, unresolvable-ref probes shipped with each new ref type,
inventory-doc sweeps on schema changes, skill folders land with their
registry/matrix rows, advisory gates key on durable outputs). Phase 3 adds:

8. No code path may dispatch a generation provider call without an approved
   GenerationApprovalRecord id; tests probe the package surface for bypasses
   every slice that touches `influencer_os/providers/`.
9. Paid-call safety in tests: the test suite never instantiates a real
   provider adapter; CI-safe by construction (mock adapter only).

## Execution Decisions (APPROVED 2026-07-06)

Surfaced as problem + recommendation per the working agreement; approved on
their recommendations by the operator's 2026-07-06 directive to implement all
of Phase 3 and recorded in ADR 0023.

### Decision 1: Provider boundary package — separate `providers/`, not an extension of `connectors/`

Problem: ADR 0022 built `influencer_os/connectors/` with standing approval by
key presence. Generation needs the same registry/env/dispatch mechanics under
the opposite approval model. Extending `connectors/` reuses more code but
puts standing-approval and exact-approval rows in one registry where a
classification bug silently weakens the generation gate.

Recommendation: a sibling `influencer_os/providers/` package that imports the
shared `env.py` helpers but has its own registry whose rows structurally
cannot express standing approval (`approval_model` is a const), and whose
dispatch signature requires an approval-record id. Reuse the existing kill
switch initially; split a generation-specific switch only if the user wants
independent control.

### Decision 2: Approval record semantics — per-record files, single-use, verbatim approval

Problem: "approval workflow records exact calls or batches" needs a concrete
consumption model. A reusable approval invites scope creep ("I approved this
once"); an append-only project log diverges from every existing record
pattern.

Recommendation: one file per approval under `generation/approval-records/`,
status ladder `draft -> approved -> executed | cancelled`, single-use for
`single_call`, bounded `max_calls` for `batch`, verbatim
`user_approval_statement` captured, and `resulting_asset_ids` written back at
execution. Re-generation after a failed or unsatisfying result requires a new
record (cheap by design; the skill pre-fills from the plan).

### Decision 3: v1 real provider adapters — none by default; operator picks the first

Problem: the reference wires OpenAI/Gemini for images and HeyGen for avatar
video, but which providers InfluencerOS should pay for is an operator
decision, and AGENTS.md forbids unrequested adapters. The machinery does not
need a real adapter to reach exit criteria (mock + import cover them).

Recommendation: slices 1–5 ship with the mock adapter only. The first real
adapter (candidates: an image provider, an avatar/video provider, or the
already-connected Higgsfield MCP surface) is chosen by the user and lands as
its own approved batch after slice 2, following the adapter contract. This
decision intentionally requires user input; there is no default.

### Decision 4: Provenance granularity — project-scoped manifest ledger, JSON-canonical

Problem: the reference records provenance inconsistently (excellent `.log.md`
in viz-image-gen and `manifest.json` in tool-image-search; nothing in
viz-nano-banana/hyperframes) and has no queryable inventory.

Recommendation: one `generation/asset-manifest.json` ledger per project
(plus Reference Library `source` blocks for reference assets) —
schema-validated JSON, index-projectable (ADR 0010), adopting the reference's
best two patterns as fields: viz-image-gen's reasoning/prompt/iteration
content for generated rows, tool-image-search's source/license/attribution/
warnings for imported rows. No per-asset sidecar files; the ledger is the
single place `validate project` reconciles against disk.

### Decision 5: Quality gate strictness — blocking for all generated and imported upload-ready media

Problem: the reference's designer audits are blocking, but its post-generation
review is feedback-only. Should packaging hard-fail without a passing quality
review, and does that apply to imported (user-provided) media too?

Recommendation: blocking for every media asset that flows from `generation/`
into `upload_ready` — generated and imported alike (imported media is where
license risk lives). Text roles (title/caption/description) are exempt.
`not_applicable` checklist items keep the gate honest for formats where a
check has no meaning. If this proves too strict in practice, relaxing to WARN
is a one-line validator change recorded in a process learning.

## Reference Review (2026-07-05)

Review of the Agentic OS reference's generation subsystems, done before plan
approval so Phase 3 adapts the reference instead of reinventing it. Reviewed:
`viz-image-gen`, `viz-nano-banana`, `viz-ugc-heygen`, `viz-hyperframes`,
`viz-stitch-design`, `vid-clip-extractor`, `vid-clip-selection`,
`vid-ffmpeg-edit`, `tool-image-search`, `tool-transcription`,
`tool-video-upload`, the `00-social-content` orchestrator's generation
phases, and `.claude/skills/_catalog/catalog.json`.

### The reference has no provider registry, approval records, or cost gating

Each generation skill self-contains its provider calls: keys are checked per
skill from `.env` at runtime, there is no adapter abstraction, no fallback
chains, no budget or cost-estimate gate anywhere. `viz-ugc-heygen` pre-flight
checks HeyGen credits but never asks "proceed at this cost"; image generation
executes silently once the visual direction is approved. The catalog
(`_catalog/catalog.json`) is a static discovery index (`requires_services`
lists env keys), not a runtime registry.

Consequently, Phase 3's registry + approval-record machinery is the
**standing approved override** ("provider-backed generation has stricter
exact approval gates", roadmap North Star) plus the accepted copy-plan row 75
("add a provider registry only when real adapters are introduced") — not a
new divergence. ADR 0023 records the concrete shape, not a new departure.

### Portable patterns adopted into slices

1. **Intent-approval gates before generation** (viz-image-gen Visual
   Breakdown approval; viz-ugc-heygen avatar/voice + script approval):
   adopted as the `request-generation-approval` skill's interaction shape —
   the human sees exactly what will be generated before any call (slice 2).
2. **Per-asset provenance log** (viz-image-gen `.log.md`: prompt, backend
   choice, references consulted, iteration history): adopted as manifest-row
   fields, JSON-canonical instead of free-form markdown (slice 4,
   Decision 4).
3. **License-aware import manifest** (tool-image-search `manifest.json`:
   source, tier, license, creator, attribution, warnings like
   `scraped-no-license-guarantee`): the reference's best-in-class provenance,
   adopted for imported-asset rows (slice 3).
4. **Blocking audits between plan and render** (`ssc-designer`'s four
   blocking audits; "the orchestrator must not show a slide plan to the user
   if the designer reports any failing audit"): adopted as the blocking
   QualityReview gate between generation and packaging (slice 5,
   Decision 5).
5. **Runtime key detection with graceful degradation** (skills warn and
   offer alternatives instead of crashing): adopted in `list-providers`
   availability semantics (slice 1), consistent with `list-connectors`.

### Reference gaps Phase 3 deliberately closes

Recorded so the divergence rationale is durable: fragmented provenance (two
of six generation skills record nothing), no central asset inventory, no
import-vs-generated distinction at approval time, and quality review that is
feedback-only after generation. Each maps to a slice above. The
`tool-video-upload`/publishing surfaces were noted and remain out of scope
(publishing is not v1).

### Subagent pattern: still deferred

The reference dispatches `ssc-image-generator`/`ssc-designer` as typed
subagents. Copy-plan row 82 keeps this deferred; slice skills are producer
skills in the ADR 0017 layout. If a Phase 3 build genuinely reaches for typed
subagent delegation, that is a divergence-test event with its own ADR — not
assumed by this plan.

## Coordination With Phase 2 In Flight

Phase 2 (Learning OS) is executing in a parallel session. Phase 3 planning
does not depend on Phase 2 artifacts, but two execution surfaces overlap:

- **`rebuild-index` / index modules** — Phase 2 slice 5 extends them; Phase 3
  slice 4 extends them again. Phase 3 slice 4 must land after Phase 2
  slice 5 and follow its established pattern.
- **Registry/matrix/conductor/architecture-map rows** — both phases append
  rows to the same docs; merge conflicts are likely if interleaved.

Recommendation embedded in this plan's status line: approve decisions now,
record ADR 0023, and open Phase 3 slice 1 after Phase 2 closeout (roadmap
order). If the user wants to interleave, slices 1–3 touch no Phase 2 surface
and could start earlier with careful rebasing; that is a user call, not a
default.

## Migration Notes

- No migration: no generation records exist in any fixture workspace; all
  fixture plans sit at `generation_status: planned_not_generated`.
- Fixture workspaces are disposable build/test data (roadmap policy); slices
  add fixture records forward.
- No committed media: mock-adapter artifacts in tests are tiny fixture bytes
  under `.tmp/` or `workspace-library/` fixtures, never tracked.

## Verification Cadence

Each slice ends with the standing checks plus the full-workflow replay in
`.tmp/` (extended per slice 5 above), recorded in
`docs/os-construction/progress.md`. The Phase 3 closeout run demonstrates the
mock end-to-end chain and the import chain on one fixture creator, with the
exit-criteria commands listed and green.
