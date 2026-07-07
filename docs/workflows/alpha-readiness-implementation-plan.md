# Alpha Readiness Implementation Plan

Last updated: 2026-07-07

Status: **Drafted, awaiting operator approval of the decisions below.**
Produced by the 2026-07-07 pre-alpha review (three independent audit passes:
code gaps, operational readiness, contract enforcement), with every finding
re-verified against the code before entering this plan.

## Goal

Close the gaps that stand between the completed Phase 0-4 build and the first
real-creator alpha run (roadmap Post-Phase-4 Track 1), and define the runnable
release gate an alpha candidate must pass.

## Success Condition

Alpha readiness is achieved when:

- one composed command (`validate all <creator-workspace>`) enforces the full
  provenance chain — workspace, research, queue, board, and every project —
  and a test proves the previously-possible false green now fails,
- a day-1 real-creator runbook exists covering env setup, fixture wipe,
  onboarding, the validation gate, and backup expectations,
- each keyed research connector has completed one bounded live smoke run
  (ADR 0022 "run 2") with the parsed output reviewed by the operator,
- the full suite passes (currently 756 tests) and `validate examples` stays
  green.

## Verified Findings (2026-07-07 review)

What the review confirmed as solid — no work needed:

- No stubs, TODOs, or `[PLANNED]` halt markers remain; every conductor
  dependency exists on disk; the skill-registry Missing Future Skills table is
  empty.
- The provider exact-approval gate has no bypass: `dispatch_generation` is the
  sole adapter entry, requires an approved `GenerationApprovalRecord`,
  compares executed assets structurally to the approval, and is not wired to
  any CLI subcommand.
- The ADR 0022 per-run call cap (`CallBudget`, default 12) and kill switch
  (`INFLUENCER_OS_DISABLE_PAID_CONNECTORS`) are enforced at every paid fetch
  and fail closed.
- `.env` loading, `.env.example`, and `.gitignore` coverage of `.env` and
  `workspace-library/` are correct.
- Schema/example parity is exact (49/49) and enforced from disk.
- The Loop A prediction confirm/refute arithmetic is behaviorally tested
  (`tests/test_improvement_os.py` covers dishonest-confirmed,
  dishonest-refuted, invented measurements, and unmeasurable dodges). An
  earlier audit note claiming it was untested was wrong.

What needs work, in severity order:

1. **No composed validation (blocker).** `validate workspace` never invokes
   `validate_project` or the queue-consistency checks; full provenance
   requires manually chaining `validate workspace` + `validate research` +
   `validate queue` + `validate project` per project. A project whose
   upstream queue entry has dangling evidence passes `validate project` in
   isolation.
2. **Fixture/real-data cohabitation (blocker-adjacent, operational).** Real
   creators and the four disposable fixtures share
   `workspace-library/creators/`, the tree is gitignored, no wipe command or
   documented wipe procedure exists, and real workspaces would have no backup.
3. **Connectors have only ever parsed mocks.** All five connectors are
   implemented, but ADR 0022 run 2 (first live-response validation of the
   parsers) is still open. Keys are present for four of five.
4. **No day-1 runbook.** Onboarding knowledge is complete but scattered
   (conductor skill, `docs/workflows/creator-setup.md`, ~10 README sections),
   and every documented entry point frames output as disposable fixtures.
5. **Promotion-level unresolved evidence refs are warning-only** for
   user-approved promotions — and the schema pins `approved_by` to `"user"`,
   so the fail branch is currently unreachable. This is the documented
   workstream-12 decision ("the human saw the evidence"), and warnings do
   reach stderr; it is surfaced here as a policy confirmation, not a bug.
6. **Minor:** project validation ignores `promotion_status` (a project locked
   to a superseded/cancelled promotion still validates); `runs.py` has no
   tests; a single end-to-end journey test; `EXCALIDRAW_API_TOKEN` missing
   from `.env.example`.

Out of scope for this plan (tracked elsewhere):

- First real (paid) generation provider adapter — a separate operator-chosen
  batch per ADR 0023 Decision 3. Only on the alpha critical path if alpha
  must produce real media.
- Multi-entity onboarding (Track 2) — own plan in
  `docs/workflows/multi-entity-onboarding-implementation-plan.md`, no code
  yet, not needed for an influencers-only alpha.

## Decisions To Approve

Do not execute a batch before its decision is approved.

- **D1 — Composed validation shape.** Recommended: add a new `validate all
  <creator-workspace>` target that composes the existing validators
  (workspace, research, queue, board when present, and `validate_project`
  for every `projects/*/project.json`), collects warnings from every layer,
  and fails on the first layer error. Existing targets keep their current
  semantics so no tests or docs change meaning. Alternative: make
  `validate workspace` itself deep (rejected as the default because it
  changes the semantics every existing caller and test relies on).
- **D2 — Promotion unresolved-ref policy.** Recommended: keep the documented
  warn-only behavior for human-approved promotions (evidence is already
  hard-checked at the queue-entry layer before promotion, and a locked
  promotion is a historical snapshot), and have `validate all` print the
  aggregated warning count in its summary line so warnings cannot scroll away
  unseen. Alternative: hard-fail dangling refs on active promotions only —
  approve explicitly if wanted, since it reverses a recorded decision.
- **D3 — Fixture wipe and real-data safety.** Recommended: document the
  manual wipe (`rm -rf` of each named fixture under
  `workspace-library/creators/`, then `rebuild-index`) and a backup
  expectation (operator-owned rsync/Time Machine of `workspace-library/`) in
  the runbook — no new CLI. Alternative: a `wipe-creator <slug>` subcommand
  with confirmation; declined by default as new destructive surface right
  before alpha.
- **D4 — Connector live smoke runs (paid).** Approve one bounded
  `research-fetch` per keyed connector (OpenAI/Reddit, xAI/X, Firecrawl,
  YouTube) with `INFLUENCER_OS_CONNECTOR_MAX_CALLS=3`, operator reviewing
  each parsed fetch-result before the connector is trusted for alpha
  research. This is ADR 0022 run 2. Apify stays dormant until a key exists.
- **D5 — Promotion-status rule at project validation.** Recommended: defer
  the behavior change; record the "historical snapshot" interpretation in
  `docs/pipeline-contract.md` so it is a rule, not an accident. Alternative:
  warn (not fail) when a project's locked promotion is no longer active.

## Batches

### Batch 1 — Composed validation (`validate all`) [needs D1, D2]

The blocker. Implementation:

- `influencer_os/creator_workspaces.py` (or a small `validate_all` helper
  module): compose `validate_creator_workspace`, `validate_research`,
  `validate_queue`, `validate_board` (when `boards/content-board.json`
  exists), and `validate_project` over `collect_project_manifests`. Return
  merged warnings; raise on the first error with the failing layer named.
- `influencer_os/cli.py`: add `all` to the `validate` target choices; print
  per-layer progress and a final summary including the warning count (D2).
- Docs: `README.md` validation section, `docs/pipeline-contract.md` release
  gate, `ARCHITECTURE.md` CLI list, repository map.

Tests (write the red test first):

- Reproduce the false green: scaffold a workspace where a project's upstream
  queue entry carries a dangling evidence ref; assert `validate project`
  alone passes and `validate all` fails naming the queue layer.
- Green path: the luna-fit example workspace scaffold passes `validate all`.
- Warning surfacing: a human-approved promotion with an unresolved ref passes
  `validate all` and the summary reports one warning (pins D2).
- CLI wiring: `validate all <path>` exit codes and stderr routing.

### Batch 2 — Day-1 runbook and env hygiene [needs D3]

- New `docs/onboard-real-creator-runbook.md` (linked from README and
  AGENTS source-of-truth list): prerequisites (`.env` keys, cap, kill
  switch), the fixture wipe procedure and its irreversibility warning, the
  backup expectation, the `create-influencer` conductor entry point, the
  intake → readiness → research → promotion → production sequence with the
  exact commands, and the `validate all` release gate from Batch 1.
- Add `EXCALIDRAW_API_TOKEN` to `.env.example` with a comment.
- Drift-proofing: extend the existing stale-path scan/drift checks to cover
  the runbook's named commands if cheap; otherwise note the runbook in the
  doc-refresh rule of the wrap-up skill.

Tests: drift check that the runbook file exists and names `validate all`
(same pattern as existing skill-command drift pins); no behavior change
otherwise.

### Batch 3 — Connector live smoke, ADR 0022 run 2 [needs D4; paid]

Operator-attended execution, not code:

- For each keyed connector, run one `research-fetch` with
  `INFLUENCER_OS_CONNECTOR_MAX_CALLS=3` against a real topic for a real or
  staging creator; review the parsed fetch-result JSON for shape drift
  against the mirrored parsers.
- Record the outcome per connector (worked / parser drift found) in
  `docs/os-construction/progress.md` Next Work Queue item 1, closing run 2.
- Any parser drift found becomes its own fix batch with a captured-payload
  regression test (sanitized, no secrets).

### Batch 4 — Minor hardening [needs D5; optional, can ship any time]

- Record the promotion-status interpretation per D5 in
  `docs/pipeline-contract.md`.
- Add the missing `prediction_holds` comparator edge tests (`>`, `<`,
  unknown-comparator raise) — one small test each.
- Optional: extend `tests/test_user_journey.py` with a second journey that
  exercises the analytics → performance-summary → distillation leg
  end-to-end; add basic `runs.py` coverage.

## Execution Order

Batch 1 → Batch 2 → Batch 3, with Batch 4 free-floating. Batches 1 and 2 are
pure local changes (commit-and-push per repo rules). Batch 3 spends API
credits and runs attended. The fixture wipe itself (the destructive step in
the runbook) is performed by the operator, not by an agent, at the moment
real onboarding starts.

## Verification

After each batch: `python3 -m unittest discover -s tests` and
`python3 -m influencer_os validate examples`. After Batch 1 additionally run
`validate all` against a scaffolded example workspace. After Batch 3 record
the smoke-run evidence in progress.md.
