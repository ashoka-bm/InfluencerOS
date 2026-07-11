# ADR 0042: Seed-Based Record Constructors With Staged Pre-Approval Drafts

## Status

Accepted (user approved 2026-07-10)

## Context

Skills currently instruct the model to author every canonical JSON record in
full, then hand the finished file to the CLI (`init-project` copies the
manifest verbatim). Dissecting `examples/project.example.json` (60 lines):
roughly 25 lines are fully deterministic (the `project_paths` block is
identical for every project, `status` is fixed at init, `created_on` is
today, the id follows a pattern), another ~15 lines are verbatim copies from
upstream records, and only ~15 lines are genuinely authored. The
`promote-idea` skill makes the copying explicit — "copy the entry's current
scores verbatim into `score_snapshot`", "copy the entry's `intended_emotion`
and `core_message` onto the promotion verbatim" — and validation fails
records whose copies diverge. The IdeaPromotion `score_snapshot` (eight
score-plus-rationale objects with prose rationales) is the largest verbatim
copy in the system.

Model-authored boilerplate has three costs, multiplied by every creator,
campaign, and project as records are created and recreated:

- Output tokens: the model emits every byte of every record, including
  bytes carrying zero new information.
- Retry loops: a typo in a copied field or path fails validation and forces
  the model to re-emit the whole record.
- Wall-clock serialization: each post-write step (`validate`,
  `rebuild-board`, `rebuild-index`) and each connector fetch
  (`research-fetch` runs one synchronous connector call per invocation) is a
  separate model round-trip wrapping a fast local script.

There is also structural dead time: while the human reads a promotion
package, nothing is prepared, and after approval the model re-emits as JSON
the same content it just presented in chat — authored twice, paid twice.
Run/plan header drift (`migrations.py` reconciles diverging
`schedule_slot_ids` between research runs and search plans) is a direct
symptom of two hand-authored records sharing fields no machine enforces at
write time.

The schema surface (51 record types) is still growing, so per-record
authoring cost compounds with every schema addition.

## Decision

Add a deterministic record-construction tier to `influencer_os`, in four
parts. Skills author **seeds** — only genuinely authored fields — and
constructors assemble, validate, and write the full records.

### 1. Seed-based constructors

`python3 -m influencer_os scaffold <record-type> --seed <seed.json>
--creator-workspace <ws>` builds the complete record:

- **Derived fields** are computed: ids from the type's pattern plus the
  next free sequence (a seed may pin an id explicitly), dates, initial
  statuses, constant path blocks, format defaults.
- **Copied fields** are pulled from the upstream record on disk, never
  transcribed by the model: `scaffold idea-promotion --entry <id>` lifts
  `score_snapshot`, `evidence_refs`, `intended_payoff`, `intended_emotion`,
  and `core_message` directly from the entry, making the verbatim-copy
  invariants mechanically true.
- The record is schema-validated before writing, written atomically, and
  the type's standard post-write pipeline (targeted `validate` plus
  projection rebuilds) runs in the same invocation — one model turn instead
  of several.
- `scaffold --list` enumerates the types that have constructors.

Field classifications and seed shapes live in
`docs/record-constructors.md`; a fixture test binds each constructor to its
schema (canonical seed must scaffold to a valid record), so schema evolution
forces the constructor to keep up while seeds — and skill prose — stay
unchanged.

### 2. Stage and commit for gated bundles

For record sets behind a human gate (the promotion bundle: IdeaPromotion,
Projects, evidence-brief skeletons, entry and slot flips):

- `stage promotion --entry <id> --seed <seed.json>` builds the entire draft
  set under `<ws>/system/staging/<stage-id>/`, prevalidated, together with
  content hashes of the upstream inputs it was derived from. Staging
  touches no canonical paths; workspace validation ignores (or
  draft-checks) the staging directory; discarding a stage costs nothing.
- The skill authors the seed **once**, stages it, and presents the package
  to the human **from the staged draft** (present-from-draft). The human
  approves exactly the bytes that will be committed.
- `commit-stage <stage-id>` re-verifies the input hashes (a stale stage —
  the entry or schedule changed since staging — fails closed and must be
  re-staged, never patched), stamps the approval fields (`approved_on`,
  `approved_by`), writes records into canonical paths in the required
  construction order, flips the entry and schedule slots, updates the queue
  manifest, and runs validation plus projection rebuilds. Approval becomes
  one cheap command with no re-authoring.

The approval gate is unchanged: no canonical IdeaPromotion or Project
exists before explicit human approval in the run. Drafting without approval
is already permitted by the operating rules; staging is drafting with a
deterministic commit path.

### 3. Anticipation policy

Deterministic local work runs as early as its inputs are known:

- **Session open** for a creator: workspace validation and
  index/lookup/board rebuilds run eagerly (background), so projections are
  always fresh instead of rebuilt on demand.
- **Search plan written**: `research-fetch --plan <search-plan>` fans out
  all planned connector fetches concurrently inside one Python process
  (thread pool over connectors), replacing one-fetch-per-invocation model
  orchestration. Started as a background task, results land on disk while
  the session continues. ADR 0022 standing approval, per-run call caps, and
  the kill switch apply unchanged.
- **Package presented**: the promotion bundle is staged while the human
  reads (the high-certainty speculation point). Speculation happens at
  decision points, not for every queue entry.

Hard limits: provider-backed generation calls are never anticipated (the
ADR 0023's approval-record dispatch gate is untouched; ADR 0043 later allowed
setup-reference records to derive from plan approval); canonical paths are never
written pre-gate; stale staged work is discarded, never reconciled.

### 4. Skill contract

For any record type with a constructor, skills author seeds and invoke the
constructor; they never hand-author the full record. Skill documents shrink
from field-by-field authoring instructions to seed-field guidance. Skill
and registry updates ship with each constructor slice (ADR 0016 process).

## Agentic OS divergence test

```text
Agentic OS divergence test:
- Proposed change: skills author seed fields only; deterministic CLI
  constructors assemble, validate, and write canonical records, with staged
  pre-approval drafts committed at the existing human gates and
  deterministic anticipation of local work.
- Agentic OS reference: reference patterns adopted so far have the agent
  author record files directly; no constructor or staging tier is copied or
  contradicted.
- InfluencerOS decision: add an internal deterministic construction tier.
  Record contents, schemas, workflow boundaries, provenance requirements,
  and approval gates are unchanged; what changes is who assembles the
  bytes, not what is approved or stored.
- Classification: internal tooling adaptation; no product-scope divergence;
  approval model unchanged (generation stays exact-approval, research
  acquisition stays ADR 0022 standing approval).
- Decision record: this ADR (0042).
- Status: pass (user approved 2026-07-10).
```

## Scope

First slice (in scope):

- Constructors and seed specs for the three highest-churn shapes: the
  Project manifest, the IdeaPromotion bundle (promotion + projects + entry
  and slot flips, via stage/commit), and the ResearchSearchPlan with its
  run-completion counterpart (the run record derives shared header fields
  from the plan, eliminating the drift class `migrate_slot_research`
  reconciles).
- `research-fetch --plan` concurrent fan-out.
- Session-open projection refresh.

Out of scope (unchanged by this ADR):

- Records that are mostly authored content (research findings, evidence
  briefs, production plans): little boilerplate, no constructor.
- A generic template engine over all 51 schemas — constructors are added
  per type when churn justifies them.
- Any anticipation of provider generation calls, publishing, scheduling, or
  unattended/cron execution (v1 deferrals stand).
- Migration of existing fixture records; constructors apply to new records.

## Consequences

- Output tokens per scaffolded record drop roughly 60–75% (seed versus full
  record); the promotion flow additionally stops authoring its content
  twice.
- Copied-field validation failures become impossible by construction,
  removing their retry loops; provenance copies required by the product
  invariant are machine-exact.
- Post-write pipelines and fan-out fetches collapse many model round-trips
  into one, which is where the wall-clock savings actually are; staging
  converts human-review dead time into preparation time.
- New maintenance surface: constructors must track their schemas. The
  fixture test makes a schema change that breaks construction a test
  failure, not a runtime surprise.
- `<ws>/system/staging/` becomes a defined non-canonical area that
  workspace validation must exclude; commit-stage owns the construction
  order that skills previously sequenced by hand.
- Skills get shorter and less error-prone; the cost of future schema growth
  shifts from every model-authored record to one Python constructor change.

## Alternatives considered

- **Fill-in template files the model completes**: rejected — the model
  still emits every byte of the finished record, so output-token savings
  are marginal, and the template file itself grows with every schema
  change.
- **Model-orchestrated parallelism** (skills instructing background shell
  calls per fetch): rejected — orchestration becomes model-dependent and
  non-deterministic; concurrency belongs inside the CLI where the workflow
  boundary is.
- **Status quo** (hand-authored records): rejected — per-record cost
  compounds with schema growth and multi-creator, multi-campaign scale, and
  verbatim-copy drift keeps generating validation churn and migrations.
