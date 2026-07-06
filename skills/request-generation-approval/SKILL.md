---
name: request-generation-approval
description: Use at the Generation Approval Gate to assemble the exact provider call or bounded batch from the Base Video Generation Plan (or a Reference Library asset plan) for the user to approve, then record the approval as a GenerationApprovalRecord. The gate stays human; this skill only packages what the human approves.
---

# Request Generation Approval

You own conductor phase 10 packaging (ADR 0023). The output is one
`GenerationApprovalRecord` under `projects/<project-slug>/generation/approval-records/`
(or `references/approval-records/` for Reference Library assets), validating
against `schemas/generation-approval-record.schema.json`.

## The Boundary Rule

A general desire to create content is **not** generation approval
(`docs/provider-boundary.md`). Approval must name the exact call or batch.
Key presence is never approval. You never dispatch; you record what the human
approved, and `dispatch_generation` refuses anything else.

## Assembling The Request

Present, before writing anything:

- the exact provider (`list-providers` for availability) and model,
- the plan being executed: `plan_ref` into the Base Video Generation Plan
  (or the reference asset entry for Reference Library scope),
- every requested asset: `asset_id`, `asset_kind`, the `prompt_ref` into the
  plan's prompt sequence, intended filename,
- the scope: `single_call`, or `batch` with an explicit bounded `max_calls`,
- the cost note (provider pricing reality, or "mock; zero cost").

Ask for approval of exactly that package. If the user changes anything,
re-present; approval covers the presented package only.

## Recording

- Capture the user's approval **verbatim** in `user_approval_statement`
  and set `approved_at`; status `approved`. If the user is still deciding,
  a `draft` record carries no statement.
- Write via the CLI so refs are resolved (plan exists, project status
  `ready_for_generation` or later, reference asset resolves):

```bash
python3 -m influencer_os record-generation-approval <creator-workspace>/projects/<project-slug> <record.json>
# or, for a Reference Library asset:
python3 -m influencer_os record-generation-approval <creator-workspace> <record.json>
```

- Records are single-use (ADR 0023 Decision 2): dispatch flips an
  `approved` record to `executing` before the first call and `executed`
  after the last, and refuses a second run (a leftover `executing` record
  means a crashed dispatch — investigate, never re-run it). Re-generation
  after a failed or unsatisfying result needs a new record — pre-fill it
  from the plan to keep this cheap.
- Every requested asset's `prompt_ref` must point into the approved
  `plan_ref` file; a prompt from anywhere else is unapproved content and
  both the writer and dispatch refuse it.
- Never edit a recorded approval; cancel (`status: cancelled` via a new
  write is not allowed — ask the user, then supersede with a new record and
  mark the old one cancelled in the same session) and record fresh.

## Boundaries

- Never call a provider, never mark a record `executed` (only dispatch
  does), never approve on the user's behalf, never treat key presence or
  prior approvals as covering a new call.
- Batch caps are bounded: refuse open-ended "generate as many as needed"
  requests; ask for a number.

## Friction Logging (ADR 0025)

When the operator rejects a draft, prompt, or asset this skill produced — or
an attempt fails in a way a future run should avoid — log it at the moment of
friction, before moving on:

```bash
python3 -m influencer_os log-incident <creator-workspace> --type rejection \
  --recurrence-key <criterion-id> --criterion <criterion-id> \
  --source-id request-generation-approval --message "<one line: what was rejected and why>"
```

- Cite an existing Production Rubric criterion, or mint one first with
  `mint-criterion` (cite-or-mint). If the reason cannot be articulated yet,
  log with `--unclassified` and a recurrence key naming the cluster.
- Record iteration churn with `--iteration-count` when several attempts
  preceded acceptance.
- Verdicts are durable; never store the rejected material itself.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md request-generation-approval "<lesson>"`.
