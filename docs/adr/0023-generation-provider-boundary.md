# ADR 0023: Generation Provider Boundary — Registry, Approval Records, Provenance Ledger, Quality Gate

## Status

Accepted

Amended by ADR 0043 for one initial generation pass over the creator-setup
reference assets listed in an approved Visual Continuity Plan. Dispatch still
uses a bounded, single-use GenerationApprovalRecord; the amendment removes the
duplicate second confirmation, not the record or provenance boundary.

## Context

Phase 3 (Generation OS) needs a provider adapter boundary that can never
bypass the exact-approval gate, an approval record for every provider call or
batch, per-asset provenance from every generated or imported asset back to
its plan and approval, and a quality gate between generation and packaging.
The Agentic OS reference has none of this machinery (each generation skill
self-contains its provider calls with no registry, approval records, cost
gating, or consistent provenance — reference review recorded in
`docs/workflows/generation-os-implementation-plan.md`), so this ADR records
the concrete shape of the already-approved standing override ("provider-backed
generation has stricter exact approval gates") plus copy-plan row 75 ("add a
provider registry only when real adapters are introduced") — not a new
divergence.

The five execution decisions were surfaced as problem + recommendation in the
implementation plan on 2026-07-05. On 2026-07-06 the operator directed
"implement all of phase three based on the planning that we have done"; that
directive is the approval, adopting each decision's recommendation, including
Decision 3's recommendation that no real (paid) provider adapter ships by
default.

## Decision

1. **Provider boundary package (Decision 1):** a sibling
   `influencer_os/providers/` package — separate from the ADR 0022
   `influencer_os/connectors/` research tier — that imports the shared
   `connectors/env.py` helpers but has its own registry whose rows
   structurally cannot express standing approval (`approval_model` is the
   constant `exact_approval`), and whose dispatch signature requires an
   approved GenerationApprovalRecord id. Key presence is **never** approval
   for generation. The existing
   `INFLUENCER_OS_DISABLE_PAID_CONNECTORS` kill switch also disables
   generation dispatch; a generation-specific switch splits out only if the
   operator asks for independent control.

2. **Approval record semantics (Decision 2):** one file per approval under
   `projects/<slug>/generation/approval-records/`, status ladder
   `draft -> approved -> executed | cancelled`, single-use for
   `single_call` and a bounded `max_calls` for `batch`, the verbatim
   `user_approval_statement` captured on the record, and
   `resulting_asset_ids` written back at execution. Re-generation after a
   failed or unsatisfying result requires a new record.

3. **v1 real provider adapters (Decision 3):** none by default. Slices 1–5
   ship with a deterministic mock adapter only; every exit criterion is
   reachable with zero paid calls. The first real adapter is chosen
   explicitly by the operator and lands as its own approved batch following
   the adapter contract. This choice is deliberately NOT made by this ADR.

4. **Provenance granularity (Decision 4):** one project-scoped
   `generation/asset-manifest.json` ledger (JSON-canonical, schema-validated,
   index-projectable per ADR 0010), adopting the reference's two best
   patterns as fields: viz-image-gen's prompt/reasoning/iteration content for
   generated rows and tool-image-search's source/license/attribution/warnings
   for imported rows. Reference Library assets route the same approval +
   provenance path with `source.source_ref` pointing at the approval record.
   No per-asset sidecar files.

5. **Quality gate strictness (Decision 5):** the QualityReview gate is
   **blocking** for every media asset that flows from `generation/` into
   `upload_ready` — generated and imported alike (imported media is where
   license risk lives). Text roles (title/caption/description) are exempt.
   Checklist items may be `not_applicable` to keep the gate honest across
   formats. This is the only blocking review layer; creative reviews stay
   advisory (ADR 0024). Relaxing to WARN, if ever needed, is a one-line
   validator change recorded as a process learning.

## Considered Options

- **Extending `influencer_os/connectors/` instead of a sibling package:**
  rejected — mixing standing-approval and exact-approval rows in one registry
  lets a classification bug silently weaken the generation gate.
- **Reusable approvals or an append-only approval log:** rejected — a
  reusable approval invites scope creep; a log diverges from every existing
  record pattern. Per-record single-use files are cheap by design.
- **Shipping a default real adapter (reference wires OpenAI/Gemini/HeyGen):**
  rejected — which providers to pay for is an operator decision and AGENTS.md
  forbids unrequested adapters.
- **Per-asset sidecar provenance files / free-form markdown logs:** rejected
  in favor of one reconcilable, index-projectable ledger.
- **Feedback-only quality review (the reference's post-generation pattern):**
  rejected — the blocking designer-audit pattern is the one worth porting;
  provenance and license risk make imported media a blocking concern too.

## Consequences

- `influencer_os/providers/` exists from Phase 3 slice 1 onward; guard rule:
  no code path may dispatch a generation call without an approved
  GenerationApprovalRecord id, probed by tests every slice that touches the
  package. The test suite never instantiates a real provider adapter.
- Consumption is a two-phase compare-and-swap (slice 1-2 review hardening):
  dispatch flips `approved -> executing` before the first adapter call and
  `executing -> executed` after the last, so a crash or concurrent dispatch
  can never replay calls against one approval; a leftover `executing` record
  refuses re-dispatch and surfaces as a validation warning. The kill switch
  is read from the real environment on every dispatch — an injected config
  can restrict further but never re-enable.
- New schemas: `generation-approval-record`, `generation-asset-manifest`,
  `quality-review`; `project.schema.json` `project_paths` gains the pinned
  `generation/` subtree; `output-package.schema.json` `upload_ready[]` gains
  `generation_manifest_ref` (required for media roles once generation status
  leaves `planned_not_generated`).
- The Creative Direction workstream's advisory review layer (ADR 0024) and
  this blocking provider-safety layer stay cleanly separate; the QualityReview
  is the blocking review `docs/gates-and-reviews.md` reserves for Phase 3.
- Scheduled or unattended generation stays deferred to Phase 4; publishing,
  platform adapters, and post-production stay out of scope.
