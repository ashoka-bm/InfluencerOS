# Skill Quality Remediation Implementation Plan

Last updated: 2026-07-07

Status: **Complete (2026-07-07).** The operator approved the recommendations
on D1-D7 and all three batches executed the same day, each gated by a
gpt-5.5 adversarial review of the batch diff. Batch 1 (mechanical fixes +
drift pins) landed with a clean review whose two suggestions (pin the fixed
contracts; harden the scalar lint) were applied as a follow-up. Batch 2
(structural de-duplication) had no HIGH findings; the review caught three
conductor requirements orphaned by the strip (novelty angle, cross-platform
travel, template selection) — now explicitly owned by `manage-idea-queue` —
plus two Rules entries still restating operational text and two shared-block
test weaknesses, all fixed. Batch 3 (descriptions + completion criteria) had
no HIGH/MEDIUM findings; its three LOW fixes (fixture confidence vocabulary,
a dropped Reference Library reach clause, four dropped registry trigger
phrases) were applied. Closeout verification: 794 tests pass (785 pre-plan
+ 9 new skill-prose drift tests), 49 examples validate, all 28 frontmatters
parse under strict YAML (js-yaml). Deferred items (behavioral gate evals;
`cancel-generation-approval` CLI) keep their reopen conditions below.

## Goal

Fix the defects found in the 2026-07-07 five-perspective skill review (four
Claude cluster reviews over all 28 `skills/*/SKILL.md` files plus an
independent gpt-5.5 Codex audit, each judged against the operator's
`writing-great-skills` rubric and the AGENTS.md deterministic-workflow-boundary
contract), and pin each fixed defect class with a drift check so it cannot
silently recur. Every HIGH finding below was re-verified against code or
schemas before being recorded here.

The review's core empirical result drives the ordering: **every confirmed
content defect lives inside duplicated prose** (a template list restated
outside its library, interview vocabulary leaked into a record contract, a
path restated away from its schema pin, a doc contract restated and drifted).
None live in single-sourced material. So: mechanical fixes first (cheap,
zero-risk), drift tests with them (TDD, per AGENTS.md), then the structural
de-duplication that removes the drift engine itself.

## Verified Findings Being Fixed

HIGH (each independently verified):

- F1 — 14 of 28 skill frontmatter blocks fail strict YAML parsing (js-yaml:
  "bad indentation of a mapping entry") because the `description:` scalar
  contains an unquoted `: ` mid-sentence. Affected: `influencer-os`,
  `promote-idea`, `manage-idea-queue`, `apply-social-template`,
  `create-research-findings`, `review-hook-payoff`, `review-generated-assets`,
  `clear-writing-pass`, `human-voice-pass`, `create-identity`, `create-soul`,
  `create-personal-brand`, `create-voice-samples`, `create-runtime-context`.
  `memory-write` and `wrap-up` already quote their descriptions correctly.
- F2 — `skills/influencer-os/SKILL.md` §Social Template Requirements lists
  nine inline template IDs; six match nothing in the canonical
  `docs/social-template-library.md` (library IDs carry the `template_`
  prefix). Meanwhile `skills/apply-social-template/SKILL.md` — the skill that
  selects templates — never names the library path at all.
- F3 — `skills/create-reference-library/SKILL.md:115-117` instructs marking
  assets `generated-from-intake` or `system-filled`; neither exists in
  `schemas/reference-library.schema.json` (`asset_status` enum:
  `planned|prompted|user_provided|generated|approved|retired`). Interview
  answer-source vocabulary leaked into the asset record contract.
- F4 — `skills/human-voice-pass/SKILL.md:19` points at
  `context/voice-samples.md`; canonical is `brand_context/voice-samples.md`
  (pinned in `schemas/creator-profile.schema.json`,
  `schemas/creator-workspace.schema.json`, and the scaffold). Root `context/`
  is OS-persona scope, so the wrong path also crosses the AGENTS.md scope
  boundary.
- F5 — `skills/review-hook-payoff/SKILL.md:24-27` specifies the
  `reviewer_execution` block without `source_skill`, which
  `schemas/review-record.schema.json` requires; a first-draft record
  following the skill fails validation.
- F6 — `skills/request-generation-approval/SKILL.md:58-60` cancellation rule
  simultaneously forbids and requires editing the old approval record.
  Ground truth (`influencer_os/generation.py`): records are write-once; the
  procedure is flip the old record's `status` to `cancelled` (the one
  permitted mutation; valid only while no execution fields exist) and record
  a fresh approval.
- F7 — `skills/create-output-package/SKILL.md:47` — "Every package must
  include exactly useful entries for all five stages" does not parse, and the
  schema (`minItems: 5`, no per-stage uniqueness) cannot disambiguate the
  intended rule for the skill's central artifact.

MEDIUM (systemic, fixed by the same batches):

- F8 — Stale platform scope: `skills/influencer-os/SKILL.md:30` V1 scope
  sentence and `AGENTS.md:83` ("the ADR 0020 platform set") both omit
  YouTube, added by ADR 0027 and present in `RESEARCH_PLATFORMS`
  (`influencer_os/validation.py:109`).
- F9 — Missing schema pointers: `create-output-package`,
  `register-published-post`, `ingest-analytics` (manual path), and
  `distill-production-learning` (`<claim.json>`) each require authoring a
  JSON record without naming its schema/example, though all exist on disk.
  `create-performance-summary` is the house pattern to copy.
- F10 — Conductor duplication: `influencer-os` restates the record
  requirements owned by `manage-idea-queue` and `create-production-plan`, and
  the provenance rule owned by `create-research-findings` (which itself
  states it three times). `create-influencer` restates the medium→reference
  mapping and staging sequence owned by `create-reference-library` (three
  sites), and its interview mechanics twice plus once in `## Rules`. F2 and
  F3 are the drift this duplication already produced.
- F11 — Self-Update boilerplate duplicated verbatim across ~17 skills and
  Friction Logging across 4, with a latent path bug: cwd-relative
  `context/learnings.md` resolves to a wrong-scope stray inside copied
  creator-workspace runtime skills. Setup skills' `../../docs/...` relative
  links break the same way in runtime copies (`sync_creator_runtime` copies
  only the skill folder).
- F12 — `## Rules` means "dated corrections ledger" in some skills,
  "standing rules" in `distill-production-learning`, and is absent in others;
  `wrap-up` step 3b assumes the ledger form exists everywhere. Three skills
  carry no-op "Baseline established; no corrections recorded yet" entries
  above real corrections.
- F13 — `distill-production-learning` declares a `memory-write` dependency
  its body never routes to (frontmatter is machine-actionable per ADR 0017
  and pinned to `docs/os-construction/architecture-map.md` by a drift check,
  so the fix must touch both). `memory-write` carries a dead
  `dependencies: []`.
- F14 — Descriptions systematically carry a non-trigger identity tail
  restating the body (rubric: descriptions carry triggers; identity tails are
  pure context load on every turn). Vocabulary clash in
  `create-voice-samples` (invents `source_extracted`; template and parent use
  different enums). Fuzzy or conditional completion criteria in
  `create-creator-profile` (a direct `validate record creator-profile` check
  exists but is not named), `create-soul`, `create-personal-brand`.

## Decisions To Approve

Do not start a batch until its decisions are approved. Recommendations
follow the operator's standing style (problem + recommendation).

- **D1 — YAML fix style.** Options: (a) quote the 14 description scalars
  as-is (minimal diff, zero invocation-behavior change); (b) rewrite
  descriptions to remove the colon-clauses now. Recommendation: **(a)** in
  Batch 1. The colon-clauses are the identity tails F14 wants trimmed anyway,
  but trimming changes invocation behavior and belongs in Batch 3 where it
  gets its own review.
- **D2 — Frontmatter guard mechanics.** The repo is stdlib-only (no
  third-party deps; drift tests parse frontmatter by regex). Options: (a) a
  targeted lint test — the `description:` scalar must be quoted when it
  contains `: `; (b) add a YAML parser dependency for a true parse test.
  Recommendation: **(a)**; it catches the entire observed failure class
  without breaking the no-dependency posture.
- **D3 — Cancellation procedure (F6).** Options: (a) rewrite the skill text
  to the guarded status-flip procedure the code already supports; (b) add a
  `cancel-generation-approval` CLI writer. Recommendation: **(a)** now;
  record (b) as a reopen condition if cancellation friction shows up in
  Loop B events.
- **D4 — Runtime-copy path convention (F11).** Runtime skill copies travel
  without `docs/` or `schemas/`, so single-sourcing shared blocks into a repo
  doc would break exactly the copied-runtime scenario. Recommendation: keep
  Self-Update and Friction Logging blocks inline per skill, but (i) reword
  paths to be explicitly repo-root ("the InfluencerOS repo root
  `context/learnings.md`"), (ii) replace `../../` links with bare
  repo-root-relative paths plus a one-line resolution rule, and (iii) add a
  drift test asserting the shared blocks are byte-identical across the skills
  that carry them, so a protocol change is a mechanically-verified sweep
  rather than 17 hand edits.
- **D5 — `## Rules` convention (F12).** Recommendation: dated entries become
  changelog pointers ("2026-07-07: tightened X — see §Y") instead of full
  restatements; the body owns each rule's text once. `wrap-up` step 3b gains
  "create the section if absent"; `distill-production-learning`'s standing
  rules get a different heading; the "Baseline established" placeholder lines
  are deleted.
- **D6 — Conductor scope (F10).** Recommendation: strip `influencer-os` to
  sequencing, gates, the phase-checklist contract, video-understanding
  boundary (its one inline-owned phase), and pointers — deleting the Idea
  Queue Requirements, Micro-Journey Requirements, Non-Video Production Plan
  Requirements, and Social Template Requirements sections in favor of
  one-line pointers to the owning producer skills; merge the Dependencies and
  Phase Owners tables and drop the all-`[BUILT]` status markers (the halt
  rule stays, as the contract for any future `[PLANNED]` row). Same move for
  `create-influencer`: children own section specs; the parent keeps routing,
  gates, and the interview contract stated once. Several drift tests pin
  exact conductor phrases — pins are updated in the same commit as the prose
  they pin.
- **D7 — `distill-production-learning` dependency (F13).** Options: (a)
  remove `memory-write` from frontmatter and the architecture-map call graph;
  (b) add an explicit approved memory-promotion step to the body.
  Recommendation: **(a)** — memory promotion is owned by `wrap-up` and
  `distill-creator-learning`; the body's silence is correct today.

## Batches

Each batch: TDD where a drift test can pin the fix (test red → fix → green),
one logical change per commit, full `python3 -m unittest discover tests` +
`python3 -m influencer_os validate examples` green before commit, and a
gpt-5.5 adversarial review of the batch diff before moving on (house pattern
from the Phase 3/4 plans).

### Batch 1 — Mechanical fixes + their drift pins (D1, D2, D3, D7)

Zero structural change; every edit is a one-place correction to prose that
contradicts code, schema, or canon.

1. New drift tests (red first): frontmatter description-quoting lint (D2);
   prose pointer-existence check (every `docs/`, `schemas/`, `examples/`
   path named in skill prose exists on disk — catches F4); template-ID check
   (every `template_`-prefixed ID or starter-template token named in any
   skill exists in `docs/social-template-library.md` — catches F2);
   `asset_status` vocabulary check (skill prose recommends only enum values —
   catches F3); conductor platform-sentence check (names every
   `RESEARCH_PLATFORMS` entry — catches F8); generalized CLI-snippet check
   (every `python3 -m influencer_os …` snippet in every skill names a real
   subcommand; extends the existing per-skill pins fleet-wide).
2. F1: quote the 14 descriptions (D1a).
3. F4: `human-voice-pass` path → `brand_context/voice-samples.md`, hedge
   dropped.
4. F3: `create-reference-library:115-117` → status stays `planned`/
   `prompted`; intake provenance goes to `source.source_type: derived` +
   `usage_notes`.
5. F5: add `source_skill` to `review-hook-payoff`'s record instructions.
6. F6: rewrite the cancellation rule per D3a: "Approval records are
   write-once. To change one: ask the user, flip the old record's `status`
   to `cancelled` (the only permitted edit; valid only while the record has
   no execution fields), then record a fresh approval."
7. F7: verify the actual enforcement in `influencer_os/projects.py` /
   `register-output-package`, then reword line 47 to state exactly that rule
   (expected: one entry per stage, five stages).
8. F8: add YouTube to the conductor's V1 scope sentence (cite ADR 0027
   extending ADR 0020) and fix `AGENTS.md:83` the same way.
9. F9: add the four missing schema/example pointers (house pattern from
   `create-performance-summary`); add the `docs/social-template-library.md`
   pointer to `apply-social-template` Inputs; add the QualityReview
   precondition line to `create-output-package` (any manifest media asset
   needs a passing QualityReview before registration — mirrors the gate
   `review-generated-assets` already states).
10. F13 per D7a: remove the unused `memory-write` dependency from
    `distill-production-learning` frontmatter and the architecture-map call
    graph in the same commit (drift check pins them together); drop
    `memory-write`'s dead `dependencies: []`.

Exit criteria: all new drift tests green; full suite green; a strict YAML
parse of all 28 frontmatters succeeds (one-off verification, since the
in-repo guard is the lint).

### Batch 2 — Structural de-duplication (D4, D5, D6)

1. F10 per D6: strip `influencer-os` (~248 → ~140 lines) and prune
   `create-influencer`'s three duplication sites (interview mechanics ×2 →
   ×1; per-medium requirements ×2 → pointer to `create-reference-library`;
   template list union → children's pointers). Update the pinned-phrase
   drift tests in the same commits.
2. F11 per D4: reword Self-Update paths to explicit repo-root; replace
   `../../` links with repo-root-relative paths; add the byte-identical
   shared-block drift test.
3. F12 per D5: convert dated `## Rules` restatements to changelog pointers;
   delete the three "Baseline established" no-ops; fix `wrap-up` step 3b
   ("create the section if absent") and retitle
   `distill-production-learning`'s standing rules; collapse
   `create-research-findings`' provenance rule to one home (Evidence
   Quality) with pointers.

Exit criteria: suite green; no producer record-requirement text remains in a
conductor; `grep -c` of the Self-Update block returns identical bytes across
carriers; registry and context matrix reconciled (wrap-up skill, ADR 0016).

### Batch 3 — Description pass + completion criteria (F14)

1. Trim every description to trigger clauses (+ genuine reach clauses, e.g.
   `distill-production-learning`'s Loop A/Loop B routing sentence), removing
   identity tails; keep alignment with the skill-registry trigger column.
2. Fix the `create-voice-samples` vocabulary clash (template's
   source/confidence split; parent's canonical answer-source enum;
   `source_extracted` deleted).
3. Sharpen the weak completion criteria: `create-creator-profile` gains the
   direct `validate record creator-profile` check; `create-soul` /
   `create-personal-brand` keep only checkable clauses; each setup child
   gains the one-line acceptance-gate sentence ("drafts require user
   acceptance before readiness changes; validation is not approval").
4. Reorder `review-generated-assets` (Rubric Criteria Results adjacent to
   the Closed Checklist, Validation last) and `create-performance-summary`
   (Authoring Steps to the top, Prediction Scoring folded into the Summary
   Contract).

Exit criteria: suite green; description-quoting lint still green; a
spot-check invocation eval (below) on the three renamed/trimmed descriptions
shows no trigger regression.

### Deferred (reopen conditions, not scheduled)

- Behavioral gate evals — agent-in-the-loop prompts asserting: the promotion
  and generation gates halt under "skip the approvals" pressure; no
  `approved` GenerationApprovalRecord exists without an explicit approval
  statement; a failing quality-review item forces `overall_verdict: fail`
  and packaging refusal; `wrap-up` does not fire on mid-conversation
  "thanks". Reopen when a harness for skill-level evals exists or a gate
  regression is observed in real runs.
- `cancel-generation-approval` CLI writer (D3b). Reopen on recurring
  cancellation friction events.

## Verification

Per batch: `python3 -m unittest discover tests`,
`python3 -m influencer_os validate examples`, gpt-5.5 adversarial review of
the diff, one logical change per commit. Plan closeout: wrap-up run (ADR
0016) recording learnings and reconciling the skill registry and context
matrix; progress recorded in `docs/os-construction/progress.md`.
