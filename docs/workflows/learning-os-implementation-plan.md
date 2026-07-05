# Learning OS Implementation Plan (Phase 2)

Last updated: 2026-07-05

Status: **Draft — pending user approval of the Execution Decisions below.**
No Phase 2 code lands until the pending decisions are approved; approved
decisions get recorded in this doc the way the Phase 1 plan recorded its
slice-by-slice execution decisions.

## Goal

Capture performance evidence for published content, distill it into
creator-scoped lessons, and make both retrievable — so future research, idea
scoring, and production planning improve from observed results instead of
starting cold every time.

Phase 2 implements ADRs 0004 (API-primary analytics ingestion), 0005
(performance attribution model), 0006 (creative performance map — consumed,
already produced by Phase 1), 0008 (creator learning memory), 0010 (file-first
with SQL index — extended), and 0011 (semantic lookup projection — built).

## Module Boundary

Inputs (all exist today):

- packaged Projects with Output Packages (`register-output-package`, Phase 1
  slice 7), each carrying a Creative Performance Map,
- the Creator Profile and content schedule,
- the Tier 0 creator memory contract (`context/MEMORY.md` cap via
  `memory-write`; `memory/learnings.md` via `log-learning`).

Outputs (new at-rest records and projections):

- `projects/<project-slug>/published/published-post-records/*.json`
  (PublishedPostRecord),
- `projects/<project-slug>/analytics/*.json` and optional `analytics/raw/`
  (AnalyticsSnapshot),
- `projects/<project-slug>/performance-summary.json` (PerformanceSummary),
- distilled lessons appended to `memory/learnings.md` with evidence links,
- Learning OS rows in `workspace-library/index/influencer-os.sqlite`,
- a curated lookup projection in the same database (see Decision 1).

Not in scope (unchanged deferrals):

- publishing or scheduling integrations (registration records what a human
  already published; it never publishes),
- platform-specific analytics API connectors (designed-for via a shared
  writer seam, built only when explicitly requested — see Decision 3),
- scheduled/cron ingestion (Phase 4),
- provider-backed embedding calls (see Decision 1),
- Command Centre, dashboards, board UI.

## Entry Criteria Verification (2026-07-05)

All three roadmap entry criteria pass today:

1. **Output Package records are stable.** Phase 1 slice 7 plus its review
   hardening landed 2026-07-04; `register-output-package` and at-rest packaged
   project validation are covered by tests (321+ passing at Phase 1 closeout).
2. **Published Post Record and Analytics Snapshot schemas validate.**
   `schemas/published-post-record.schema.json`,
   `schemas/analytics-snapshot.schema.json`,
   `schemas/performance-summary.schema.json` exist since 2026-07-01 with
   validating examples (part of the 43-example green baseline).
3. **Creator Memory policy is implemented.** Tier 0 recall rules are in
   `docs/creator-workspace-structure.md`; the 2,500-byte `context/MEMORY.md`
   cap is enforced by `memory-write`; `log-learning` writes dated per-skill
   entries to learnings files.

## Success Condition — Runnable Exit Criteria

Per the roadmap Acceptance-Criteria Policy, the Phase 2 exit criteria are
rewritten here as runnable checks (workstream-14 pattern). Phase 2 exits when
every check below passes and is recorded in `progress.md`:

1. **Published Post Records can be registered.**
   `python3 -m influencer_os register-published-post <workspace> <project> <record.json>`
   succeeds against a packaged fixture project; the written record passes
   `validate record published-post-record <path>`; a hand-edited invalid
   record at rest fails `validate project` (test).
2. **Analytics Snapshots can be added through manual entry or CSV, with the
   API path proven at the seam.** `add-analytics-snapshot` (manual/derived)
   and `import-analytics-csv` produce records that pass
   `validate record analytics-snapshot`; both paths call one shared writer
   function, and a mock-backed test drives the same writer as an `api`-sourced
   ingestion would (no platform connector is built — Decision 3). A snapshot
   referencing a nonexistent PublishedPostRecord fails validation (test).
3. **Performance Summaries map results to packaging, hook, body retention,
   payoff, and CTA.** The schema's `minItems: 5` stage set is enforced; a
   summary missing a stage or citing unresolvable
   `published_post_record_ids`/`analytics_snapshot_ids` fails `validate
   project` at rest (test).
4. **Distilled Creator Memory links back to evidence.** `log-learning` gains a
   required evidence-refs argument for creator-lesson entries; an entry whose
   evidence IDs do not resolve to real records in the workspace fails the
   write (test); `validate workspace` re-checks the same rule at rest (test).
5. **SQL index rebuilds from files.** `rebuild-index` indexes
   published-post-record, analytics-snapshot, and performance-summary rows
   with the same unique-id and provenance guarantees as existing types;
   deleting the database and rebuilding reproduces identical rows (test).
6. **Semantic lookup indexes only curated decision-support material.**
   `rebuild-lookup` indexes only permitted sources (Decision 1); a probe test
   asserts that raw analytics JSON, raw exports, and `analytics/raw/` payloads
   are never present in the lookup projection; a PerformanceSummary with
   `semantic_lookup.index_allowed: false` is excluded (test).

Standing checks that must stay green through every slice:

- `python3 -m unittest discover -s tests`
- `python3 -m influencer_os validate examples`
- drift checks (registry, context matrix, adapter, conductor call graph,
  enum pins)
- fixture workspaces pass `validate workspace` and `validate research`
- `update-creators` syncs runtime skills with zero overrides lost

## Implementation Sequence

Roadmap slice order, unchanged. Slices 1–3 are mechanical record/CLI work;
slice 4 is the agent-judgment skill; slices 5–6 are projections.

### Slice 1: Published Post Record Registration

The bridge from "packaged" to "measured": a human publishes manually, then
records the fact.

- CLI `register-published-post`: validates the record, requires the target
  Project to be `packaged` (or already `published` for multi-platform
  additions), verifies `output_package_id`/`project_id`/`creator_profile_id`
  match the owning project chain, verifies `assets_used` IDs and the
  caption/description path resolve to declared Output Package upload-ready
  assets, writes to `published/published-post-records/`, and moves Project
  status `packaged -> published` on the first record.
- At-rest parity: `validate project` re-checks every registration invariant
  on a `published` project (process-learning 2026-07-04: mutator-only
  invariants are not enough).
- Write hardening inherited from `register-output-package`: reject symlinked
  write targets; rollback on partial failure.
- Tests: happy path, package/project mismatch, dangling asset ref, at-rest
  hand-edit probe, duplicate `published_post_record_id`, non-packaged
  project rejection.

### Slice 2: Analytics Snapshot Ingestion

- One shared writer function (module seam) used by every ingestion path —
  the multi-path drift lesson from Phase 1 queue/promotion checks, applied
  from day one.
- CLI `add-analytics-snapshot`: manual/derived entry from a JSON file;
  validates, resolves `published_post_record_id` to a real record, checks
  `platform` matches the PublishedPostRecord, computes `hours_since_publish`
  when omitted and `published_at` is known, writes under `analytics/`.
- CLI `import-analytics-csv`: parses the neutral InfluencerOS CSV template
  (Decision 3) — one row per snapshot, null-safe for absent metrics (ADR
  0004: missing metrics are recorded absent, never guessed) — and feeds the
  shared writer.
- `analytics/raw/`: optional safe raw payload storage; the importer records
  `raw_source_ref` relative paths; a validation check rejects `raw_source_ref`
  paths that escape the project (symlink/containment class).
- At-rest parity in `validate project`: snapshot chain integrity
  (snapshot -> PublishedPostRecord -> Output Package -> Project), metric
  bounds already in-schema, duplicate snapshot ids.
- Tests: manual path, CSV path (including null metrics and a malformed row),
  shared-writer API mock, dangling `published_post_record_id`, platform
  mismatch, raw-ref escape probe, at-rest hand-edit probe.

### Slice 3: Performance Summary Contract

The mechanical half of summarization: record placement, validation, and
provenance. Interpretation happens in slice 4's skill.

- Canonical record: `projects/<project-slug>/performance-summary.json`
  (Decision 4; the layout doc's `.md` naming is corrected to match).
- `validate project` at rest: a summary's `evidence_refs` must resolve —
  `output_package_id` to the project's package, every
  `published_post_record_id` and `analytics_snapshot_id` to records on disk;
  all five stages present exactly once each (schema allows duplicates within
  `minItems: 5`; the validator closes that gap).
- Advisory WARN: a `published` project with analytics snapshots older than a
  threshold but no performance summary (mirrors the thin-evidence WARN
  pattern: derived from durable at-rest outputs, not a flag).
- Tests: valid summary, dangling evidence ref, duplicated stage, WARN probe.

### Slice 4: Learning Distillation (`distill-creator-learning` skill)

Reconciles the conductor's `[PLANNED — Phase 2]` marker and the skill
registry's Missing Future Skills row — the open build obligation from
Phase 0C WS 10.

- New skill `skills/distill-creator-learning/SKILL.md` (Decision 2): reads the
  packaged project's Creative Performance Map, PublishedPostRecords, and
  AnalyticsSnapshots; produces the PerformanceSummary record (stage findings,
  distilled lessons, `semantic_lookup.index_allowed` + `summary_text`) and
  appends evidence-linked lessons to `memory/learnings.md`; optionally
  promotes a durable fact to `context/MEMORY.md` via `memory-write` (cap
  enforced). Includes `## Rules` and `## Self-Update` sections, `dependencies`
  frontmatter, and evidence-strength guidance (`single_post_signal` vs
  `multi_post_pattern` per ADR 0008 — don't overfit to one post).
- `log-learning` extension: a `--evidence` argument required for creator
  lesson entries; IDs are validated against workspace records at write time
  and re-checked by `validate workspace` at rest (exit criterion 4).
- Conductor + registry + context matrix reconciliation in the same batch as
  the skill folder (process-learning 2026-07-03: registry drift checks pin
  them to one commit).
- Runtime sync: `update-creators` distributes the new skill to fixture
  workspaces.
- Tests: skill-registry/context-matrix drift stays green, learnings append
  with resolvable evidence, unresolvable-evidence rejection (write and
  at-rest), MEMORY.md cap refusal still holds.

### Slice 5: Recall Index Extension

- Extend `rebuild-index` scans to `published/published-post-records/*.json`,
  `analytics/*.json`, and `performance-summary.json`; add the three types to
  `UNIQUE_RECORD_TYPES`.
- Provenance columns unchanged (path, hash, timestamps — ADR 0010).
- Reconciliation both directions where aggregates exist (process-learning
  2026-07-04): index rows must trace to files, and a full rebuild after
  deleting the database is byte-identical modulo timestamps.
- Tests: new-type rows present, duplicate-id detection across files,
  delete-and-rebuild equivalence, cross-creator scoping (one creator's
  rebuild never touches another's rows).

### Slice 6: Semantic Lookup Projection

- Implementation per Decision 1 (recommended: SQLite FTS5 table in the same
  `influencer-os.sqlite`, stdlib `sqlite3`, no new dependencies, no provider
  calls).
- Indexed sources (ADR 0011 allowlist, creator-scoped):
  - `brand_context/identity.md`, `brand_context/soul.md`,
    `brand_context/personal-brand.md`,
  - `research/findings.md` and stable findings,
  - PerformanceSummary `summary_text` where `index_allowed` is true,
  - `memory/learnings.md` entries.
- Never indexed (deny by construction, not by filter): raw analytics
  snapshots, `analytics/raw/`, API payloads, transcripts, media, secrets.
  The indexer walks an explicit allowlist of paths; it never walks
  `analytics/`.
- CLI: `rebuild-lookup` (per-creator, mirrors `rebuild-index` semantics) and
  `query-lookup <creator> <terms>` returning source-path-cited matches.
- Creator scoping: every row carries `creator_slug`; queries require one.
- Tests: allowlist coverage, `index_allowed: false` exclusion, raw-analytics
  absence probe, creator-scope isolation, delete-and-rebuild.

## Creator Workspace Layout (Phase 2 additions in context)

```text
workspace-library/creators/<creator-slug>/
  projects/<project-slug>/
    output-package/                  # Phase 1
    published/
      published-post-records/       # slice 1 writes here
        ppr_<...>.json
    analytics/                       # slice 2 writes here
      analytics_snapshot_<...>.json
      raw/                           # optional safe exports
    performance-summary.json         # slice 3 contract, slice 4 authors
  memory/
    learnings.md                     # slice 4 appends evidence-linked lessons
  context/MEMORY.md                  # slice 4 may promote via memory-write

workspace-library/index/influencer-os.sqlite   # slices 5-6 project into this
```

All paths already exist in the workspace scaffold and
`docs/creator-workspace-structure.md`; slice 3 corrects the
`performance-summary.md` -> `performance-summary.json` naming there.

## Schema Deltas

The three Phase 2 schemas already exist and validate. Expected deltas are
small and land with their owning slice:

- `performance-summary`: no shape change; validator-level stage-uniqueness
  check (slice 3).
- `published-post-record` / `analytics-snapshot`: no planned shape change;
  any gap found while wiring registration/ingestion is fixed in the same
  slice with example + fixture updates and an inventory-doc sweep
  (process-learning 2026-07-04).
- `project.schema.json`: no new statuses — `published` already exists and
  `packaged -> published` is the only Phase 2 transition. Learning artifacts
  attach at rest without a dedicated status; the slice 3 advisory WARN covers
  "published but never summarized".
- Enum drift pins: any new closed vocabulary (e.g. CSV column set) gets a
  drift pin the same change it ships (process-learning 2026-07-03).

## Guard Rules Carried Into Every Slice

Process-learnings applied as standing plan rules:

1. Every writer-enforced invariant is re-checked by the at-rest validator for
   that record state (2026-07-04).
2. Every new record directory or ledger inherits sibling guards: duplicate-id
   detection, containment/symlink checks on write targets, bidirectional
   reconciliation for any derived aggregate (2026-07-04/05).
3. Multi-path writes (manual/CSV/API-seam) go through one shared function
   from the first slice (2026-07-03).
4. Fixture probes exercise the unresolvable case for every new ref type in
   the same change that adds the ref (2026-07-03).
5. Schema or record-set changes trigger an inventory-doc sweep:
   `pipeline-contract.md` record table, `ARCHITECTURE.md`, README,
   architecture maps (2026-07-04).
6. Skill folders land in the same batch as their registry and context-matrix
   rows (2026-07-03).
7. Advisory gates key on durable at-rest outputs, never on a mutable
   declarative flag (2026-07-04).

## Pending Execution Decisions

Surfaced for user approval before any slice executes. Each has a
recommendation; approved outcomes get recorded here as User-Approved with a
date, following the Phase 1 plan convention.

### Decision 1: Semantic lookup implementation

Problem: ADR 0011 requires a semantic lookup projection, but true embeddings
need either provider calls (approval-gated, recurring cost, network
dependency) or a local embedding model (heavy dependency; the repo is
deliberately stdlib-only).

Recommendation: v1 lookup is a SQLite FTS5 full-text projection in the
existing index database — stdlib-only, deterministic, rebuildable, satisfies
every ADR 0011 scoping rule. Embedding-based retrieval is recorded as a
deliberate future upgrade behind explicit approval (the projection's sources
and scoping rules are the durable contract; the ranking backend can be
swapped without schema or layout changes). If accepted, note the divergence
in `agentic-os-alignment.md` (reference uses vector SQL).

### Decision 2: Phase 2 skill surface

Problem: the registry obligates exactly one future skill
(`distill-creator-learning`), but Phase 2 has four workflows. Phase 1 gave
each producing phase an owner skill; mirroring that would add three thin
skills for mechanical CLI wraps.

Recommendation: one new skill. Registration (slice 1) and ingestion (slice 2)
are deterministic CLI operations with no judgment — CLI-only, documented in
the conductor's post-pipeline phase table. `distill-creator-learning` owns
both interpretation steps: authoring the PerformanceSummary and distilling
lessons into memory (they share one evidence read and ADR 0008 treats them as
one distillation act). The conductor's post-pipeline section maps:
publication registration -> CLI, analytics ingestion -> CLI, performance
summary + learning distillation -> `distill-creator-learning`.

### Decision 3: Analytics ingestion scope for v1

Problem: ADR 0004 is API-primary by design, but the AGENTS.md rule forbids
platform-specific adapters unless explicitly requested, and platform
analytics APIs need auth, quotas, and per-platform metric mapping.

Recommendation: v1 builds manual entry plus a neutral InfluencerOS CSV
template (our own documented column contract; the operator exports from a
platform and maps columns once — no per-platform parsers). The shared writer
seam is built and mock-tested so a platform API connector can drop in later
under the ADR 0022 connector pattern when explicitly requested. Exit
criterion 2 is worded accordingly.

### Decision 4: Performance summary canonical form

Problem: `docs/creator-workspace-structure.md` names
`performance-summary.md`, but the record schema is JSON and every other
mid-pipeline record is a schema-validated JSON file.

Recommendation: `performance-summary.json` is canonical (schema-validated,
index-projectable); the layout doc is corrected in slice 3. The
`semantic_lookup.summary_text` field already carries the human-readable
narrative, so no parallel markdown file is needed.

## Migration Notes

- No migration: no Phase 2 records exist in any fixture workspace yet.
- Fixture workspaces are disposable build/test data (roadmap policy); slices
  add fixture records forward, never migrate.
- The four example records under `examples/` are already green; slices extend
  them only if a schema delta lands.

## Verification Cadence

Each slice ends with the standing checks (tests, `validate examples`, drift
checks, fixture `validate workspace`/`validate research`, runtime sync) plus
a full-workflow replay in `.tmp/` extending the Phase 1 closeout script:
creator init -> intake -> research -> queue -> promotion -> project ->
production plan -> output package -> **register-published-post ->
add-analytics-snapshot / import-analytics-csv -> distill (summary + lessons)
-> rebuild-index -> rebuild-lookup -> query-lookup** -> board -> prune.
Progress and results are recorded in `docs/os-construction/progress.md`
(process-learning 2026-07-03: re-run the documented script end to end
whenever a cross-record check lands).
