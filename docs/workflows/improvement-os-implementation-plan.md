# Improvement OS Implementation Plan (Phase 4)

Last updated: 2026-07-06

Status: **Execution-ready draft — pending approval of execution decisions
D1–D6.** Phase 4 was rescoped from "Automation OS" to Improvement OS by the
2026-07-06 grilling session (ADR 0025). The record designs below are written
on the D1–D6 recommendations; approving D1–D6 (or amending them) is the
single gate before Batch 1 starts. Record approval by updating this status
line, matching the Phase 3 precedent.

## Goal

Close the two feedback loops that make the OS improve instead of repeat, with
a falsifiable criterion at every step:

- **Loop A — Performance Delta:** evaluate the theory of what was created
  (Creative Performance Map predictions) against what analytics actually
  measured, per Content Beat Spine stage, feeding Creator Memory and the next
  research/idea cycle. Creator-scoped learning.
- **Loop B — Production Quality:** capture creation friction (weak prompts,
  rejected drafts, failed assets) as durable recurrence-keyed events, bracket
  recurrences, and convert them into skill/routine updates that carry
  falsifiable improvement claims. OS-scoped learning.

The shared discipline (ADR 0025): declare-then-attest capture, the Rubric
Ratchet (every rejection cites or mints a binary criterion), event-triggered
reflection (never clock-triggered), and improvement claims verified against
subsequent runs. Nothing improves on vibes.

## Locked Decisions (operator, 2026-07-06 grilling session)

Do not reopen without operator approval.

1. **Rescope:** Phase 4 is Improvement OS. Temporal scheduling (job
   definitions, dry-run runners, live cron) is deferred with its own reopen
   conditions (roadmap Deferred section; ADR 0025).
2. **Two loops, sequenced by data dependency:** shared substrate first, then
   Loop B (needs only real creation attempts), then Loop A comparison
   semantics (needs real analytics — but prediction capture starts early).
3. **Capture:** mechanical traces + structured skill-reported events with
   recurrence keys on the existing system-event ledger. No session-thread
   mining. Verdicts durable, rejected drafts ephemeral.
4. **Trust model:** declare-then-attest with mechanical at-rest
   reconciliation against disk; self-reporting is trusted, and the human
   review rides the reflection trigger (distillation proposes, human
   approves).
5. **Falsifiability:** binary rubric criteria for Loop B; quantified
   predictions scored confirmed/refuted/unmeasurable for Loop A; improvement
   claims with expected violation-rate changes for skill updates.
6. **Rubric seeding:** near-empty — the four quality-review categories plus
   creator boundaries; the ratchet grows the rest.

## Entry Criteria Verification (2026-07-06)

Planning OS reliable (Phase 1 complete 2026-07-04); Learning OS ingests and
distills (Phase 2 slices 1–6 complete 2026-07-06); provider approval gates
cannot be bypassed (Phase 3 closed 2026-07-06 with gate-hardening probes).
Repo health at plan time: 653 tests OK, 47 examples validate, tree clean at
`67f948a`.

## Execution Decisions — To Be Approved

The designs below assume each recommendation; an amendment changes the
matching design section.

- **D1 — Rubric storage.** One `production-rubric` schema with a required
  file-level `scope`. OS-scope criteria live in `context/production-rubric.json`
  (beside `context/learnings.md`, the OS-scope learning home); creator-scope
  criteria live at the workspace root `production-rubric.json` (beside
  `creator-profile.json` and `content-schedule.json`). Criterion ids are
  unique across both files; a duplicate id fails closed (ambiguous
  resolution).
- **D2 — Event shapes.** Extend the dormant `system-event` schema with
  optional `recurrence_key`, `criterion_id`, `iteration_count`, and
  `unclassified` rather than adding a new ledger. Semantics for the new
  `rejection`/`incident` event types are enforced in the shared event seam
  (writer and at-rest sweep call one function).
- **D3 — Trigger thresholds.** Code-constant defaults `RECURRENCE_K = 3`,
  `UNPROCESSED_N = 10`, `UNCLASSIFIED_N = 3`, overridable per workspace via
  an optional `reflection_thresholds` object on `creator-workspace.json`.
- **D4 — Prediction shape.** Optional `prediction` object
  (`metric`, `comparator`, `threshold`) on Creative Performance Map stage
  entries; per-stage `prediction_result` on performance-summary
  `stage_findings`. Backward compatible; pairing is fail-closed (below).
- **D5 — Claim verification mechanics.** Violation counts are computed
  mechanically from ledger events; a human closes each claim (confirm or
  refute). At-rest validation checks shape and refs; the computed suggestion
  is reporting, not mutation.
- **D6 — Review cadence.** Batch-boundary gpt-5.5 adversarial reviews with
  fix batches (three reviews across three batches); hold shared-file edits
  while a review is pending (recorded process learning).

## Record And Surface Designs

Field names inside existing schemas were verified against the schemas on
2026-07-06; per the recorded learning ("the writer layout is the contract"),
re-derive exact shapes from the schema and writer code at build time if this
plan and the code ever disagree.

### `production-rubric.schema.json` (new, + example)

- File-level: `rubric_id`, `scope` (`os` | `creator`), `creator_profile_id`
  (required when scope is `creator`, must match the owning workspace; absent
  for `os`), `criteria[]`.
- Criterion: `criterion_id` (doubles as the recurrence key; pinned pattern
  `^[a-z0-9_.]+$`), `statement` (phrased answerable yes/no), `status`
  (`minted` | `proven` | `blocking` | `retired`), `origin`
  (`seed` | `rejection` | `distillation`), `minted_on` (date),
  `minted_from_event_id` (optional, must resolve to a ledger event when
  present), `quality_review_category` (optional, the four quality-review
  check names), `blocking_adr` (required iff `status == "blocking"`, must
  resolve to a real `docs/adr/*.md` file), `notes`.
- Closed vocabularies (`scope`, `status`, `origin`, comparator below) get
  enum drift pins like the platform/format enums.

### `system-event` extensions (existing schema, additive)

- New optional fields: `recurrence_key` (same pattern as `criterion_id`),
  `criterion_id`, `iteration_count` (integer ≥ 1), `unclassified` (boolean).
- Event-type semantics (shared seam, writer + at-rest sweep):
  - `event_type: "rejection"` requires `recurrence_key` and exactly one of
    `criterion_id` or `unclassified: true` (the Rubric Ratchet at rest).
  - `event_type: "incident"` requires `recurrence_key`; `criterion_id`
    optional.
  - A present `criterion_id` must resolve against the union of the OS and
    owning-creator rubric files; a citation of a nonexistent or `retired`
    criterion fails validation.
- The canonical `examples/system-event.example.json` becomes a rejection
  event modeling the new fields (recorded learning: the exemplar must model
  the rule).

### `improvement-claim.schema.json` (new, + example)

- `claim_id` (filename == id), `created_on`, `target_skill` (must exist as
  `skills/<name>/SKILL.md` — drift-checked), `criterion_id` (must resolve),
  `baseline` (`window_description`, `violation_count`),
  `expectation` (`window_runs`, `max_violations`),
  `evidence_event_ids[]` (must resolve to ledger events), `status`
  (`open` | `confirmed` | `refuted` | `withdrawn`), `closed_on`
  (required when status leaves `open`), `closed_by` (`user` — human closes,
  D5), `supersedes_claim_id` (optional; a refuted claim's follow-up links its
  predecessor), `notes`.
- Location: `context/improvement-claims/<claim_id>.json` (OS scope; Loop B
  claims target skills, which are OS state; creator lessons keep flowing
  through the existing `log-learning --evidence` path).

### Reflection runs (reuse of the dormant `automation-run` schema)

- A reflection run is the declare-then-attest record for reflection itself:
  `system/reflection-runs/<automation_run_id>.json` with
  `job_id: "reflection"`, `job_type: "reflection"`, `event_ids` = exactly the
  ledger events this reflection processed, `material_update` = whether any
  proposal was made, `run_status` from the existing enum.
- Watermark semantics: an event is **unprocessed** until a completed
  reflection run lists it. Reconciliation is both-direction and fail-closed:
  a run claiming a nonexistent event id fails; an event claimed by two runs
  fails.

### Predictions (Loop A; `output-package` + `performance-summary`)

- Creative Performance Map stage entries gain optional `prediction`:
  `{metric (string, minLength 1), comparator (">=" | "<=" | ">" | "<"),
  threshold (number, finite)}`.
- `performance-summary.stage_findings[]` items gain optional
  `prediction_result` (`confirmed` | `refuted` | `unmeasurable`),
  `measured_value` (number | null), `prediction_result_reason` (required iff
  `unmeasurable`).
- Pairing rule, enforced in the shared summary↔package match seam and at
  rest (recorded learning: a conditional obligation invites the condition to
  be lied about): when the summarized package's map stage carries a
  prediction, the summary's matching stage finding must carry
  `prediction_result`; `confirmed`/`refuted` require `measured_value` and
  must agree with the comparator arithmetic (mechanically recomputed);
  non-finite numbers are already rejected validator-wide.

### Quality gate extension (slice 5; `quality-review`)

- The closed four-check `checklist` stays untouched. A new optional
  `rubric_criteria_results[]` rides beside it:
  `{criterion_id, result (pass | fail | not_applicable), notes}`.
- Enforcement for generation-sourced packaged media: every `blocking`
  criterion in scope (OS + owning creator) must appear; any `fail` forbids a
  passing `overall_verdict` (extends the existing verdict-agreement rule);
  missing blocking coverage fails at `register-output-package` and at rest
  (writer-enforced invariants re-checked by the standing validator).

### CLI surface

- `log-incident <creator-workspace> --type rejection|incident
  --recurrence-key <key> [--criterion <id> | --unclassified]
  [--iteration-count <n>] [--project <id>] --message "..."` — validates
  through the shared event seam, then appends to
  `system/creator-events.jsonl`.
- `mint-criterion <creator-workspace> | --os --id <id> --statement "..."
  [--category <quality-review-check>]` — adds a `minted` criterion; refuses
  duplicate ids across both scopes.
- `check-reflection <creator-workspace>` — reports unprocessed counts,
  per-key recurrence counts, unclassified accumulation, and threshold
  crossings; reporting only, mutates nothing.
- `check-claims` — reports each open claim's mechanically computed
  suggestion (D5); the human closes by editing the record.
- `validate workspace` — gains the advisory reflection-due warnings (printed,
  never failing) plus the new at-rest checks named per slice below.

### Skills

- **New producer `distill-production-learning`** (slice 3): triggered by a
  reflection-due warning; reads unprocessed events, brackets by
  `recurrence_key`, proposes skill/routine updates each carrying an
  improvement claim, applies only human-approved writes, logs via
  `log-learning`, and writes the reflection-run record last (attesting
  exactly the processed `event_ids`). Registry row, context-matrix row, and
  conductor post-pipeline owner row (beside `distill-creator-learning`) land
  in the same commit — the drift checks pin them.
- **Rules additions** (slice 1): `review-generated-assets`,
  `request-generation-approval`, `create-production-plan`, and
  `create-output-package` gain a Rules line requiring rejection/incident
  logging via `log-incident` at the moment of friction (cite or mint).
- **`wrap-up`** (slice 3): gains an audit step — check for friction the
  session left unlogged, and prompt close-out of open claims whose windows
  have elapsed.
- **`create-output-package` / `create-performance-summary`** (slice 4):
  prediction guidance and scoring rules respectively.

## Success Condition — Runnable Exit Criteria

Phase 4 exits when every check below passes and is recorded in
`progress.md`:

1. **The Rubric Ratchet is enforced at rest.** `log-incident` and
   `validate workspace` accept a valid rejection citing a real criterion and
   a valid unclassified rejection; a rejection citing a nonexistent or
   retired criterion fails both the writer and the at-rest sweep (shared
   seam); duplicate criterion ids across scope files fail closed.
2. **The reflection trigger fires and cannot block.** With ≥ K same-key
   unprocessed events on a fixture ledger, `validate workspace` emits the
   advisory reflection-due warning and `check-reflection` reports the
   crossing; a probe asserts validation success is unaffected (advisory
   only), including for the unclassified gap signal.
3. **Improvement claims are falsifiable in practice.** Tests drive one claim
   to confirmed and one to refuted from fixture events via the mechanical
   count; a claim with a dangling `criterion_id`, `target_skill`, or
   `evidence_event_ids` entry fails validation.
4. **Predictions score true/false.** `validate record output-package`
   accepts quantified predictions; the summary↔package pairing is
   fail-closed; comparator arithmetic is mechanically recomputed; tests
   cover a visual and a text fixture (one fixture per format class).
5. **Declare-then-attest reconciles mechanically.** Reflection-run
   `event_ids` reconcile both directions against the ledger; every new
   ref-shaped field ships with an unresolvable-fixture probe in the same
   slice.
6. **The deferral and blocking discipline hold.** A scan asserts no
   scheduler/cron scripts exist; every `blocking` criterion carries a
   resolvable `blocking_adr`; a probe asserts `minted`/`proven` criteria and
   every other Improvement OS surface never halt a pipeline step.

## Implementation Slices

### Slice 1 — Rubric substrate

Deliverables: `production-rubric.schema.json` + example; the two rubric
files (OS seeded from the four quality-review categories, fixture creators
seeded from their boundaries, origin `seed`); `system-event` extensions with
the updated exemplar; the shared event seam (rejection/incident semantics,
cite-or-mint resolution); `log-incident` and `mint-criterion`;
`creator-workspace.schema.json` pins the workspace rubric path and
`init-creator` scaffolds it; Rules additions to the four producing skills;
enum drift pins.

Tests: schema round-trips; cite-nonexistent fails (writer and at-rest —
same-seam parity test); cite-retired fails; unclassified validates;
duplicate-id-across-scopes fails; ledger duplicate-event-id guard still
holds; the three fixture workspaces validate after seeding.

### Slice 2 — Reflection trigger

Deliverables: reflection-run reading/watermark semantics over the dormant
`automation-run` schema (`system/reflection-runs/` pinned in the workspace
schema and scaffolded); threshold constants + `reflection_thresholds`
workspace override; advisory warnings in `validate workspace`;
`check-reflection`.

Tests: K-recurrence fires and under-K stays silent; unprocessed-N and
unclassified-N fire; overrides respected; both-direction event_ids
reconciliation negatives (dangling id, double-claimed event); the advisory
probe (a firing trigger cannot fail validation).

### Slice 3 — Distillation with improvement claims

Deliverables: `improvement-claim.schema.json` + example;
`context/improvement-claims/` location with filename==id; the
`distill-production-learning` skill (with registry, context-matrix, and
conductor rows in the same commit); `check-claims`; `wrap-up` audit and
close-out additions.

Tests: claim lifecycle to confirmed and to refuted via fixture events;
dangling `criterion_id`/`target_skill`/`evidence_event_ids` fail
(unresolvable-fixture probes); `closed_on` required when status leaves open;
reflection-run written by the skill attests exactly the processed events;
skill-on-disk drift for `target_skill`.

### Slice 4 — Falsifiable predictions (Loop A)

Deliverables: `prediction` on map stage entries; `prediction_result` /
`measured_value` / `prediction_result_reason` on `stage_findings`; the
pairing rule in the shared summary↔package match seam and at rest; updated
output-package and performance-summary exemplars in the same change; skill
guidance updates.

Tests: comparator arithmetic drives confirmed and refuted; a predicted stage
without `prediction_result` fails; unmeasurable without reason fails;
measured_value disagreement with the recomputed comparator fails; visual and
text fixtures; non-finite threshold rejected.

### Slice 5 — Criteria maturity ladder

Deliverables: `rubric_criteria_results[]` on quality-review; blocking
coverage + verdict-agreement enforcement at `register-output-package` and at
rest; `blocking_adr` drift check; `docs/gates-and-reviews.md` documents the
proven → blocking promotion path (ADR checklist per promotion; this plan
ships the path, not any promotion).

Tests: missing blocking coverage fails registration and at rest; a failing
blocking criterion forbids a passing verdict; `blocking_adr` must resolve;
the never-blocks probe for `minted`/`proven` criteria.

## Sequencing And Review Cadence (D6)

- **Batch 1:** slices 1–2 → gpt-5.5 adversarial review → fix batch.
- **Batch 2:** slices 3–4 (disjoint file sets, still sequential within the
  batch) → review → fix batch.
- **Batch 3:** slice 5 → review → fix batch → full exit-criteria closeout
  run recorded in `progress.md`.

Every slice is buildable and testable on fixtures with zero paid calls. Loop
B goes live with the first real generation runs; Loop A's scoring goes live
with the first real analytics — prediction capture accrues from slice 4
onward so deltas have material to compare.

## Deliberately Deferred Remainders (by decision, not omission)

- Cross-creator aggregation of OS-scope criterion counts (via a recall-index
  event projection) — per-workspace triggering suffices until multiple real
  creators exist.
- Creator-scoped improvement claims — creator lessons keep the existing
  `log-learning --evidence` path.
- A closed `prediction.metric` vocabulary — learn the real metric set from
  live analytics before pinning an enum.
- A board surface for reflection-due — the board has no workspace-level
  card; revisit with real queue data.

## Risks And Mitigations

- **Self-report adherence:** skills may skip `log-incident`. Mitigated by
  the Rules lines, the wrap-up audit step, the unclassified gap signal, and
  the mechanical traces that exist regardless (failed reviews, leftover
  `executing` approvals, repeated approval records per plan).
- **Rubric bloat:** the `retired` status plus reflection-time curation keep
  the criteria list bounded; the rubric is itself subject to the compaction
  discipline.
- **Threshold mistuning:** defaults are conservative and workspace-tunable
  (D3); tuning is configuration, not schema change.
- **Exemplar drift:** every schema change updates its example in the same
  change (recorded learning), and example coverage is enforced from disk.

## Guard Rules (hold every slice)

- Nothing added by this phase blocks any pipeline step; blocking arrives
  only via criterion promotion under the documented ADR checklist.
- No scheduler, cron, hooks, or unattended execution ships.
- Verdicts durable, drafts ephemeral: no rejected creative material is
  committed; events carry criterion + one-line reason, not payloads.
- Provider and promotion gates are untouched.
- Apply the recorded learning classes to every new seam: id-vs-record,
  unresolvable-ref probes, containment roots, both-direction
  reconciliation, writer-enforced invariants re-checked at rest,
  status-conditioned checks written as "at or past," shared seams for
  multi-path checks.

## ADR

ADR 0025 (`docs/adr/0025-improvement-os-feedback-loops.md`) records the
rescope, the locked decisions, and the discipline. D1–D6 approval is
recorded by updating this plan's status line, matching the Phase 3
precedent.
