# Improvement OS Implementation Plan (Phase 4)

Last updated: 2026-07-06

Status: **Draft — pending execution approval.** Phase 4 was rescoped from
"Automation OS" to Improvement OS by the 2026-07-06 grilling session (ADR
0025); the locked scoping decisions from that session are recorded below. The
execution decisions D1–D6 are surfaced for approval; no Phase 4 code lands
until they are approved.

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

## Module Boundary

Inputs (all exist today):

- the dormant `system-event` and `automation-run` schemas and the empty
  `system/creator-events.jsonl` ledger (ADR 0020 slice 3) — the event
  substrate,
- the Creative Performance Map (ADR 0006) with per-stage `intended_effect`
  and `primary_metrics` — the theory record, currently prose-only,
- `create-performance-summary` (Phase 2 slice 3), which already reads the map
  as "what the package predicted,"
- the quality-review record and its closed four-check checklist (Phase 3
  slice 5) — the seed categories and the eventual blocking destination,
- `log-learning --evidence --strength`, `wrap-up`, `memory-write`, and
  `SKILL.local.md` promotion (ADR 0016/0014) — the distillation machinery,
- the ProjectWarning/badge pattern and `rebuild-board` — the advisory
  surfacing seam for the reflection trigger,
- the three existing declare-then-attest pairs (search plan → source yield,
  run outputs reconciliation, approval-record exact equality) — the pattern
  to generalize, not reinvent.

Outputs (new at-rest records, extensions, CLI):

- a Production Rubric record (binary criteria; scope: OS-level vs
  creator-level; criterion id = recurrence key; maturity: minted → proven →
  blocking),
- rejection/incident event shapes on the system-event ledger (criterion ref,
  recurrence key, iteration count, unclassified variant),
- a `log-incident` (or `log-rejection`) CLI writer,
- reflection-trigger threshold checks surfacing advisory warnings/badges,
- an improvement-claim record bound to a skill update, with
  confirmed/refuted status computed from subsequent events,
- optional quantified `prediction` fields on Creative Performance Map stage
  entries, and per-stage confirmed/refuted/unmeasurable in performance
  summaries,
- a criteria promotion path into the blocking quality checklist, guarded by
  the gates-and-reviews ADR checklist.

Not in scope (unchanged deferrals; hard boundaries):

- any live scheduler, cron install, or unattended execution (Locked Decision
  1); scheduled jobs, if ever reopened, cannot promote ideas, create
  projects, or call providers without human approval (PRD Out of Scope),
- session-transcript capture or mining (Locked Decision 3),
- weakening any gate: generation keeps exact approval; promotion stays
  human-owned; nothing Improvement OS adds may block the pipeline until a
  criterion is promoted through the documented ADR checklist (ADR 0024
  advisory rule holds),
- platform analytics API connectors (Phase 2 Decision 3 unchanged), Command
  Centre, dashboards, publishing.

## Entry Criteria Verification (2026-07-06)

The roadmap's three entry criteria, verified at rescope time: Planning OS
reliable (Phase 1 complete 2026-07-04), Learning OS ingests and distills
(Phase 2 slices 1–6 complete 2026-07-06), provider approval gates cannot be
bypassed (Phase 3 closed 2026-07-06 with gate-hardening probes). Repo health:
653 tests OK, 47 examples validate, tree clean at `bbdd39e`.

## Execution Decisions — To Be Approved

- **D1 — Rubric storage.** Problem: criteria have two scopes. Recommendation:
  one `production-rubric` schema with a required `scope` field; OS-level
  criteria in a root rubric file, creator-level criteria in a per-workspace
  rubric file; `validate workspace` checks the creator file, a drift check
  covers the root file.
- **D2 — Event shapes.** Problem: new record types vs extending
  `system-event`. Recommendation: extend the existing dormant `system-event`
  schema (optional `recurrence_key`, `criterion_id`, `iteration_count`,
  event-type vocabulary for rejection/incident/unclassified) — the ledger,
  validation, and examples already exist; first writers activate them.
- **D3 — Trigger thresholds.** Recommendation: defaults of K=3 same-key
  recurrences and N=10 unprocessed events, stored as workspace-configurable
  values, surfaced as advisory warnings by the existing at-rest validation
  and board-badge seams.
- **D4 — Prediction shape.** Recommendation: optional `prediction` object on
  each Creative Performance Map stage entry (`metric`, `comparator`,
  `threshold`), backward-compatible; performance summaries emit per-stage
  `confirmed | refuted | unmeasurable`.
- **D5 — Claim verification mechanics.** Recommendation: violation counts are
  computed mechanically from events; a human closes the claim (confirm or
  reopen) at wrap-up — mirrors "distillation proposes, human approves."
- **D6 — Review cadence.** Recommendation: batch-boundary gpt-5.5 adversarial
  reviews with fix batches, as in Phase 3; hold shared-file edits while a
  review is pending (recorded process learning).

## Success Condition — Runnable Exit Criteria

Per the roadmap Acceptance-Criteria Policy, Phase 4 exits when every check
below passes and is recorded in `progress.md`:

1. **The Rubric Ratchet is enforced at rest.** `validate workspace` accepts a
   workspace with a rubric and rejection events; a rejection event citing a
   nonexistent criterion fails validation; an unclassified rejection
   validates and counts toward the gap signal (positive + negative tests).
2. **The reflection trigger fires and cannot block.** With ≥K same-key events
   on the ledger, validation surfaces an advisory reflection-due warning and
   the board badges it; a probe test asserts no Improvement OS surface halts
   any pipeline step.
3. **Improvement claims are falsifiable in practice.** A skill-update
   improvement claim validates; its status is computed from subsequent-run
   events; a test drives one claim to confirmed and one to refuted (refuted
   reopens).
4. **Predictions score true/false.** `validate record output-package` accepts
   quantified predictions; `create-performance-summary`'s record carries
   per-stage confirmed/refuted/unmeasurable; tests cover a visual and a text
   fixture (recorded learning: one fixture per format class).
5. **Declare-then-attest reconciles mechanically.** Attestation-vs-disk
   mismatches fail closed at the seams this phase adds (unresolvable-ref
   probes for every new ref-shaped field, per the recorded learning classes).
6. **The deferral holds.** A scan asserts no scheduler/cron scripts exist in
   the repo; criteria reach the blocking checklist only through the
   gates-and-reviews ADR checklist (drift check).

## Implementation Slices

1. **Rubric substrate.** `production-rubric` schema + examples (D1), the
   system-event extensions (D2), `log-incident` CLI, cite-or-mint validation,
   seed rubric from quality-review categories + creator boundaries. Registry,
   context-matrix, and architecture-map rows land in the same commit.
2. **Reflection trigger.** Threshold checks (D3) surfacing advisory warnings
   and board badges, including the unclassified-accumulation gap signal; the
   advisory probe.
3. **Distillation with improvement claims.** Claim record + writer, claim
   status computation from events (D5), wrap-up/distill integration, human
   approval before any skill-file write.
4. **Falsifiable predictions (Loop A).** Creative Performance Map
   `prediction` fields (D4), per-stage scoring in performance summaries,
   both-fixture tests.
5. **Criteria maturity ladder.** The proven-criterion promotion path into the
   blocking quality checklist, guarded by the gates-and-reviews ADR
   checklist; drift check that no other blocking path exists.

Every slice is buildable and testable on fixtures with zero paid calls. Loop
B goes live with the first real generation runs; Loop A's scoring goes live
with the first real analytics — prediction capture accrues from slice 4
onward so deltas have material to compare.

## Guard Rules (hold every slice)

- Nothing added by this phase blocks any pipeline step; blocking arrives only
  via criterion promotion under the documented ADR checklist.
- No scheduler, cron, hooks, or unattended execution ships.
- Verdicts durable, drafts ephemeral: no rejected creative material is
  committed; events carry criterion + one-line reason, not payloads.
- Provider and promotion gates are untouched.
- Apply the recorded learning classes to every new seam: id-vs-record,
  unresolvable-ref probes, containment roots, both-direction reconciliation,
  writer-enforced invariants re-checked at rest, status-conditioned checks
  written as "at or past," shared seams for multi-path checks.

## ADR

ADR 0025 (`docs/adr/0025-improvement-os-feedback-loops.md`) records the
rescope, the locked decisions, and the discipline. D1–D6 approval is recorded
by updating this plan's status line, matching the Phase 3 precedent.
