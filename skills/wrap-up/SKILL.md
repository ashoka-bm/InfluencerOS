---
name: wrap-up
description: "End-of-session self-improvement loop. Triggers when the user signals session end (\"thanks\", \"that's it\", \"done for today\", \"wrap up\", \"we're done\") or when a session produced deliverables. Does NOT trigger for a mid-conversation \"thanks\" that clearly means \"thanks, now do X\"."
dependencies:
  - memory-write
---

# Wrap-Up

End-of-session checklist. Review what was done, collect feedback, apply fixes, verify, commit.

## Outcome

- Dated per-skill entries appended to `context/learnings.md`.
- Repo-level process lessons recorded in `docs/os-construction/process-learnings.md`.
- Direct fixes applied to any skill that needs them (`SKILL.md` or the applicable `SKILL.local.md`).
- `docs/os-construction/skill-registry.md` and `docs/os-construction/context-matrix.md` reconciled with the skills on disk; drift checks pass.
- Durable facts promoted to the right `MEMORY.md` within its 2,500-byte cap.
- Session work committed per the `AGENTS.md` Git Rules.

## Context Needs

| File | Load level | How it shapes this skill |
| --- | --- | --- |
| `context/learnings.md` | `## Individual Skills` sections for skills used this session | Prior lessons and dedup targets |
| `context/MEMORY.md` | Full | Promotion target for durable OS-level facts |
| `docs/os-construction/skill-registry.md` | Full | Reconciliation source of truth |
| `docs/os-construction/context-matrix.md` | Skill Coverage table | Reconciliation source of truth |
| Active Creator Workspace `context/MEMORY.md` and `memory/` | Only when the session worked inside one | Creator-scoped promotion and daily-note targets |

## Step 1: Review Deliverables

1. Run `git status` and `git diff --stat`.
2. List every file created or modified, grouped by location: `docs/`, `schemas/` + `examples/`, `skills/`, `influencer_os/` + `tests/`, and anything else.
3. Flag anything that must never be committed: `workspace-library/`, creator media, generated works, secrets, `.env`.

## Step 2: Collect Feedback

Default to one question: **"Anything to note before I wrap up?"**

### 2a: Friction Audit (ADR 0025)

If this session produced or reviewed drafts, prompts, or generated assets in
a Creator Workspace, check for friction that went unlogged: rejections or
churn the session saw but never recorded via `log-incident`. Log them now
(cite-or-mint; `--unclassified` when the reason resists articulation). Then
run `python3 -m influencer_os check-claims` — for any open claim whose
window has elapsed, prompt the user to close it (confirm or refute; a
refuted claim's fix reopens via a superseding claim).

Expand to what-worked / what-didn't / which-skill-misbehaved only when several skills ran this session or the user wants to give detailed feedback.

## Step 3: Apply Changes

### 3a: Log Learnings

For each skill with feedback, append a dated entry with the deterministic writer:

```bash
python3 -m influencer_os log-learning context/learnings.md <skill-name> "<one-line lesson>"
```

The writer dedups repeated lessons and keeps per-skill sections. Cross-skill or repo-process lessons go to `docs/os-construction/process-learnings.md` instead.

### 3b: Fix Skills Directly

If feedback points to a specific skill issue, edit the skill now — do not only log it:

- System-wide correction → fix the offending step in `skills/<skill-name>/SKILL.md` and add a dated entry to its `## Rules` (create the section, with its reading instruction, if the skill has none). Entries are changelog pointers — name the change and the section that owns it; the rule text itself lives once in the body.
- Scope-specific correction (one creator, or the OS persona) → record it in the applicable `SKILL.local.md` instead.
- After fixing, log what changed via `log-learning` so the change has a record.

### 3c: Session Notes

- Worked inside a Creator Workspace → finalize that workspace's `memory/daily/{YYYY-MM-DD}.md` note: goal, deliverables, decisions, open threads. No placeholders.
- OS-level work (docs, schemas, code) → update `docs/os-construction/progress.md` instead; the repo has no root daily log by design.

### 3d: Reconcile Registry And Matrix

Compare `skills/*/SKILL.md` folders against the skill registry and context matrix, then prove it:

```bash
python3 -m unittest tests.test_drift_checks
```

A new skill without a registry row, a stale row, or a future-table row for a built skill fails the check — fix the docs until it passes.

### 3e: Promote Durable Facts

Promote session facts worth keeping via the bounded writer (dedup + 2,500-byte cap enforced):

```bash
python3 -m influencer_os memory-write context/MEMORY.md "<fact>" --section "Active Threads"
```

OS-level facts go to root `context/MEMORY.md`; creator facts go to that workspace's `context/MEMORY.md`. Never mix scopes. If the writer refuses on the cap, consolidate stale entries first. Skip silently if nothing durable surfaced.

## Step 4: Verify And Commit

1. Run `python3 -m unittest discover -s tests` and `python3 -m influencer_os validate examples`.
2. Commit and push per the `AGENTS.md` Git Rules (trunk-based, imperative subject, one logical change per commit); Step 1's never-commit flags apply.

## Session Summary

Close with:

```
--- Session Summary ---
Deliverables: {files, one line each}
Learnings logged: {skill: lesson}
Skills modified: {skill: change, or "None"}
Registry sync: {what changed, or "No drift detected"}
Memory: {N}/2,500 bytes{, promotions made, or "No durable facts promoted"}
Committed: {hash} — {subject}
---
```

## Rules

*Dated corrections from feedback. Read before every run; newest last.*


## Self-Update

If the user flags an issue with the wrap-up process itself — wrong commit scope, missed files, bad summary — add a dated entry to `## Rules` above and fix the offending step immediately. Don't just log it; fix the skill so it doesn't repeat.

## Graceful Degradation

- No feedback given → log "No feedback — routine session" for the skills used, still reconcile and commit.
- No deliverables (discussion-only session) → note that in the summary; skip 3a-3c.
- Drift checks fail on something outside this session's scope → surface it to the user; do not silently widen the commit.
