# Gates And Reviews

The canonical control contract for InfluencerOS (ADR 0024, Creative Direction slice 4). This doc defines the vocabulary, the order of controls along the pipeline, which controls may block, and the record contract reviews write. Glossary terms live in `CONTEXT.md`.

## Control Vocabulary

- **Gate** — human, blocking. A gate stops the pipeline until a person decides. V1 has exactly two: the Concept Approval Gate (`approve-concept`) and the Provider Boundary (exact approval for provider-backed generation calls, with the ADR 0045 creator-setup carve-out: the one bounded Avatar Image call runs under a system-derived single-use approval record).
- **Review** — advisory, emits a Review Record. A judged read of an artifact with findings keyed to the Content Beat Spine. Never blocks.
- **Pass** — advisory editorial rewrite, emits no record. Returns rewritten text plus a change trace; the author decides what to keep. Never blocks, never issues a verdict.
- **Warning** — non-blocking signal (`ProjectWarning` records and validator warning strings). Surfaces a concern; changes nothing.

## Control Order Along The Pipeline

1. Concept Approval Gate — **human gate (blocking)**.
2. Platform-fit advisory at project creation — **Warning** (`platform_fit`, never blocks).
3. Plan drafting (template → production plan).
4. Hook/Payoff Review after a plan is drafted — **Review (advisory)**, all six plan types.
5. Clear-Writing Pass and Human-Voice Pass on drafted text — **Passes (advisory)**.
6. Provider Boundary before any generation call — **human gate (blocking)**, excepting the one bounded system-derived Avatar Image call at creator setup (ADR 0045).
7. Provider-safety `QualityReview` between generation and packaging — the one **blocking** review layer (ADR 0023 Decision 5, built in Phase 3 slice 5): `register-output-package` and `validate project` refuse a packaged media asset that flows from `generation/` without a passing QualityReview covering it — generated and imported alike; text roles are exempt. Owned by `review-generated-assets`; records live at `projects/<slug>/generation/quality-reviews/`.

## Two Layers, One Rule

- **Creative-advisory layer (v1):** every creative Review and Pass is advisory. An `approval_status` of `revise` or `block` is a strong recommendation to the human, not an auto-stop. `validate project` surfaces an unwaived `block` as a warning string and still passes; packaging and registration proceed.
- **Provider-safety layer (Phase 3, built):** the `QualityReview` blocks packaging for generation-sourced media (closed checklist: identity consistency, continuity with plan, technical conformance, creator boundary compliance; verdict must agree with the items). Nothing in the creative layer may be promoted into it implicitly — a creative review becoming blocking still requires its own ADR.

**Real-world-risk carve-out:** a finding that the content makes a false claim about a real person, brand, or product is a **must-acknowledge advisory** — the reviewer sets `severity: blocking`, and the human must either revise the artifact or record a `human_waiver` on the Review Record. It is still not a hard block in v1; its realization as one is explicitly deferred to Phase 3.

**Promotion rule:** making any creative Review blocking requires its own ADR.

**Criteria maturity ladder (ADR 0025):** Production Rubric criteria mature
`minted -> proven -> blocking` (with `retired` for criteria that no longer
apply). Minted and proven criteria are advisory everywhere — they gate
nothing. Promotion to `blocking` follows the same ADR checklist as a
blocking review: the criterion gains a `blocking_adr` reference that must
resolve to the recorded decision (validated at the rubric load seam), and
from then on a QualityReview yields passing coverage for generation-sourced
media only if its `rubric_criteria_results` address every blocking criterion
in scope — a `fail` on one forbids a passing verdict. Reviews written before
a promotion stay valid records but stop counting as passing coverage: what
is required changed, not what was checked then. The checklist for such an ADR: name the review, the exact failure class that blocks, the waiver path, the falsifiable evidence that advisory mode was insufficient, and the divergence-test result.

## Reviewer Independence And Execution Modes

The authoring skill may not certify its own artifact. A review runs as a distinct step fed an explicit packet (the artifact plus its named upstream refs), never the authoring conversation.

- Preferred: `bounded_sub_agent` — a fresh sub-agent receives only the packet.
- Local-first fallback: `fallback_separated_pass` — the conductor runs the review as its own fresh-context turn and records why the bounded path was unavailable (`fallback_reason`).

Every Review Record captures `reviewer_execution.execution_mode` and `source_skill`.

## Review Record Contract

`schemas/review-record.schema.json` (lean v1; `matched[]`/`drifted[]` wait for Creator-Fit):

- refs: `project_id`, `creator_profile_id`, optional `concept_approval_id`, `artifact_refs` (project-relative paths that must resolve),
- `review_role`: `hook_payoff` (built) | `creator_fit` | `fact_check` (both later),
- `findings[]`: `area` in `hook | retain | payoff | cta | general`, `severity` in `none | low | medium | high | blocking`, `note`, optional `recommended_revision`,
- `approval_status`: `approve | revise | block` (advisory),
- `reviewer_execution`: `execution_mode`, `source_skill`, `fallback_reason` (required on fallback runs),
- optional `human_waiver` (`waived_by: user`, date, reason) — only a human waives a blocking finding, and a waiver requires a blocking finding to exist,
- `created_at`.

Records live at `projects/<project-slug>/reviews/<review_record_id>.json`; `validate project` validates them at rest (schema, filename pin, project/creator scope, promotion consistency, artifact resolution) and proves the advisory rule with a probe test: a `block` status halts nothing.

## Built Reviews And Passes (v1 First Slice)

- `review-hook-payoff` — Review. Checks the hook earns attention, the payoff is delivered and traces to the promoted idea's `intended_payoff`, the body sustains retention, and the CTA follows from the payoff.
- `clear-writing-pass` — Pass. Removes clutter and filler from drafted text; bounded edit depth; change trace; no record.
- `human-voice-pass` — Pass. Strips AI tells against the creator's actual voice (Creator Profile + voice samples); change trace; no record.

Fact-Check Review and Creator-Fit Critique are approved but unbuilt (reviews second slice); the conductor halts if asked to run them.
