---
name: distill-production-learning
description: Use when a reflection-due warning fires (check-reflection / validate workspace) to bracket friction events into human-approved skill updates carrying falsifiable ImprovementClaims, and to close improvement claims whose windows elapsed. Owns Loop B of the Improvement OS (ADR 0025) — creator lessons stay with distill-creator-learning.
---

# Distill Production Learning

You own the production-quality feedback loop (ADR 0025 Loop B). The input is
unprocessed friction on a creator's event ledger; the output is
human-approved skill/routine updates that each carry a falsifiable
ImprovementClaim, plus the reflection-run record attesting exactly which
events were processed. Nothing improves on vibes: every proposed change
names the criterion it targets and the violation ceiling that would refute
it.

## Trigger

Run when `python3 -m influencer_os check-reflection <creator-workspace>` (or
a `validate workspace` warning) reports a crossed threshold: a recurrence
key at K+, the unprocessed total at N+, or the unclassified rubric-gap
signal. Never run on a clock; the trigger is evidence (ADR 0025).

## Inputs

- `check-reflection` output: unprocessed counts and per-recurrence-key
  totals.
- The unprocessed friction events on
  `<creator-workspace>/system/creator-events.jsonl`.
- The OS rubric (`context/production-rubric.json`) and the creator rubric
  (`<creator-workspace>/production-rubric.json`).
- The target skills' `SKILL.md` files and `context/learnings.md`.
- Open claims via `python3 -m influencer_os check-claims`.

## Distillation Steps

1. **Bracket.** Group unprocessed friction events by `recurrence_key`.
   Recurrence is the signal: one event is noise, K+ of the same key is a
   rule waiting to be written.
2. **Classify the unclassified.** For unclassified-rejection clusters,
   propose a criterion that names the taste (`mint-criterion`, origin
   `distillation`, `--from-event` the representative event). If it still
   cannot be articulated, leave the events unprocessed — do not invent.
3. **Propose, never apply.** For each bracketed cluster, draft the smallest
   skill or routine change that would prevent the recurrence, and the
   ImprovementClaim that would falsify it: target skill, criterion,
   baseline (the bracketed events), expectation (`max_violations` over a
   named window). Present all proposals to the human together.
4. **Apply only approved changes.** Edit the approved skills' Rules or
   guidance sections; log each via
   `python3 -m influencer_os log-learning context/learnings.md <skill> "<change>"`.
5. **Record each claim** with
   `python3 -m influencer_os record-improvement-claim <claim.json>` —
   author against `schemas/improvement-claim.schema.json` (complete
   example: `examples/improvement-claim.example.json`); evidence event ids
   are the bracketed events; the writer resolves them against the
   workspace.
6. **Attest the reflection run last.** Write
   `<creator-workspace>/system/reflection-runs/<automation_run_id>.json`
   (automation-run schema, `job_type: "reflection"`) whose `event_ids` list
   exactly the events processed in steps 2-5 — processed means a human
   decision was made about them, including "explicitly dismissed". Events
   nobody decided on stay unclaimed and keep counting toward the trigger. A
   run that crashed or was abandoned is recorded `failed` with
   `event_ids: []` and `last_error`.
7. **Verify:** `python3 -m influencer_os validate workspace <creator-workspace>`
   must pass; the warnings you started from should be gone or reduced.

## Claim Close-Out

On later runs, read `check-claims`: the count is mechanical, the verdict is
human (D5). Confirm a claim whose window elapsed within its ceiling; refute
one that exceeded it — a refuted claim's fix is reopened via a new claim
with `supersedes_claim_id`. Set `status`, `closed_on`, `closed_by: user`.

## Boundaries

- OS-scoped learning only: skill files, routines, OS learnings, claims.
  Creator lessons (what content works for this creator) belong to
  `distill-creator-learning`.
- Every skill-file write needs explicit human approval of that exact change
  (ADR 0016 discipline); claims record what was approved, never a plan.
- Never delete or rewrite ledger events; the ledger is append-only history.
- Never store rejected material in criteria, claims, or learnings —
  verdicts are durable, drafts are ephemeral.
- Blocking-criterion promotion is out of scope here: proven criteria reach
  the blocking checklist only through the gates-and-reviews ADR checklist.

## Standing Rules

- Bracket before proposing: no single-event skill edits unless the event is
  severity `urgent`.
- Every proposed update carries a claim; an update with no falsifiable
  claim is a vibe, not a fix.
- The reflection run's `event_ids` must equal the set actually decided on.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md distill-production-learning "<lesson>"`,
run from the InfluencerOS repo root: repo paths (`docs/`, `schemas/`,
`context/learnings.md`) resolve from there, never from a Creator
Workspace runtime copy.
