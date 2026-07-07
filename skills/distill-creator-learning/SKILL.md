---
name: distill-creator-learning
description: Use after PerformanceSummary records exist to distill durable, evidence-linked creator lessons into memory/learnings.md and optionally promote a proven fact to the workspace context/MEMORY.md.
dependencies:
  - memory-write
---

# Distill Creator Learning

You own the learning-distillation step of the Learning OS. The output is
dated, evidence-linked creator lessons in the workspace's
`memory/learnings.md` — the durable memory future research, idea scoring,
and production planning read by default — plus, rarely, one promoted fact
in `context/MEMORY.md`.

This is a judgment skill wrapped around a validated writer: you author the
lesson, and `log-learning --evidence` plus `validate workspace` are the
enforcement seams. Raw metrics stay in the owning project; only distilled
judgment moves to memory (ADR 0008).

## Inputs

Read (context matrix — Learning distillation row):

- One or more PerformanceSummary records
  (`projects/<project-slug>/performance-summary.json`) — the
  `distilled_lessons`, `stage_findings`, and `semantic_lookup` narrative
  are your primary material.
- Their evidence chain when judging scope: the cited Published Post
  Records and AnalyticsSnapshots, and the project's Creative Performance
  Map.
- `memory/learnings.md` — existing lessons, to consolidate instead of
  duplicate and to upgrade strength when a pattern repeats.
- `context/MEMORY.md` — current promoted facts, before proposing another.

Write only through the CLIs below. Never edit performance summaries,
snapshots, published records, or Project status here.

## Lesson Contract

Every creator lesson is one entry under `## Creator Lessons` in
`memory/learnings.md`, written via the CLI:

```bash
python3 -m influencer_os log-learning <creator-workspace>/memory/learnings.md \
  "<topic>" "<one-line lesson>" \
  --evidence <record-id> [<record-id> ...] \
  --strength single_post_signal|multi_post_pattern|weak_signal \
  [--date YYYY-MM-DD]
```

- `<topic>` is the applies-to grouping (e.g. `hooks`, `packaging`,
  `posting time`) — reuse the PerformanceSummary `applies_to` vocabulary
  and existing topic headings before inventing a new one.
- `--evidence` ids must resolve to schema-valid workspace records
  anchored to their project manifest: performance summaries, published
  post records, analytics snapshots, projects, or output packages. Cite
  the PerformanceSummary you distilled from at minimum; the deeper chain
  resolves through it. The write fails on a dangling or spoofed id, and
  `validate workspace` re-fails a hand-edited one at rest.
- The writer enforces the parseable entry format
  (`- YYYY-MM-DD [strength]: lesson (evidence: id, ...)`); duplicates
  within a topic are no-ops.

## Evidence Strength Judgment

`--strength` is honest scope, mirroring the PerformanceSummary enum
(ADR 0008 — don't overfit to one post):

- `single_post_signal`: the evidence spans one published post, however
  strong the result. Most first lessons live here.
- `multi_post_pattern`: only when cited evidence spans multiple published
  posts — multiple PerformanceSummaries, or one summary whose cited
  records cover distinct posts. When a new summary repeats an existing
  `single_post_signal` lesson, write the consolidated lesson as
  `multi_post_pattern` citing both summaries rather than adding a
  near-duplicate. This is enforced, not advisory: the writer and
  `validate workspace` count the distinct published posts the cited
  evidence identifies (direct post ids, snapshots' parent posts, a
  summary's cited post list — project/package ids identify none) and
  refuse `multi_post_pattern` below two.
- `weak_signal`: provisional or incomplete data (pre-latency snapshots,
  unmeasured stages, confounded timing). Never dress a weak signal up as
  a pattern.

Lessons are creator-relative: phrase what this creator should keep or
change next time, not generic platform advice. Do not copy a summary's
`distilled_lessons` verbatim when consolidation across summaries produces
a sharper lesson — but never write a lesson no cited record supports.

## Promotion To Always-Loaded Memory

`context/MEMORY.md` is the 2,500-byte always-loaded layer; promotion is
the exception, not the default. Promote only a `multi_post_pattern`
lesson the creator will need in nearly every future session, phrased as
one line:

```bash
python3 -m influencer_os memory-write <creator-workspace>/context/MEMORY.md \
  "<one-line durable fact>" --section "Decisions"
```

The cap is enforced before every write; when a promotion would exceed it,
consolidate existing entries first or skip the promotion — never trim
someone else's entry silently. The full lesson with its evidence links
stays in `memory/learnings.md` either way.

## Distillation Steps

1. Read the new PerformanceSummary records and list candidate lessons
   from `distilled_lessons` and stage findings.
2. Check `memory/learnings.md` for overlapping lessons; decide per
   candidate: new entry, consolidated upgrade, or skip.
3. Write each lesson via `log-learning --evidence --strength` with the
   owning topic.
4. Optionally promote at most one durable `multi_post_pattern` fact via
   `memory-write`.
5. Verify:

```bash
python3 -m influencer_os validate workspace <creator-workspace>
```

## Boundaries

- Creator-scoped only: lessons from one creator's evidence never go to
  another workspace or to root OS memory (repo `context/MEMORY.md`).
- No raw metrics in memory: cite record ids, don't inline snapshot
  numbers a future agent would treat as current.
- Distillation never mutates its inputs; diagnosing a surprising result
  belongs in `create-performance-summary` revisions, not here.
- This skill runs on request or at the conductor's learning phase; no
  cron, hooks, or scheduled distillation (deferred to Phase 4).

## Rules

*Dated corrections from wrap-up feedback (ADR 0016). Read before every run; newest last.*


## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md distill-creator-learning "<lesson>"`,
run from the InfluencerOS repo root: repo paths (`docs/`, `schemas/`,
`context/learnings.md`) resolve from there, never from a Creator
Workspace runtime copy.
