---
name: memory-write
description: "Saves one durable fact to a MEMORY.md file via the bounded CLI writer (2,500-byte cap). Triggers on \"remember this\", \"note that\", \"save this to memory\", \"update memory\", \"forget about X\". Does NOT trigger for learnings updates (wrap-up's job) or one-off in-conversation reminders."
---

# Memory Write

Saves durable facts to a `MEMORY.md` file — the curated always-loaded memory read at session start.

## Outcome

- One durable fact added to, updated in, or removed from the right `MEMORY.md`.
- The 2,500-byte cap holds (pre-write check; consolidation before the cap is breached).
- Confirmation shown: `Saved — will be active from next session.`

## Scope And Sections

Pick the file by whose fact it is — never mix scopes:

| Scope | File | Sections |
| --- | --- | --- |
| InfluencerOS (OS persona, repo work) | `context/MEMORY.md` | Active Threads, Environment Notes, Pending Decisions |
| One creator | `workspace-library/creators/<creator-slug>/context/MEMORY.md` | Active Threads, Decisions, Blockers |

## Step 1: Determine Action

| User phrasing | Action |
| --- | --- |
| "remember this", "note that", "save this", "add to memory" | **add** |
| "update memory about X", "X is now Y" | **replace** |
| "forget about X", "remove X from memory" | **remove** |

If ambiguous, ask before proceeding.

## Step 2: Add via the Bounded Writer

For **add**, use the deterministic writer — it dedups and enforces the cap:

```bash
python3 -m influencer_os memory-write <path-to-MEMORY.md> "<one-line fact>" --section "<section>"
```

- Duplicate fact → the writer skips and reports it; reply `Already saved — no change needed.`
- Over the cap → the writer refuses. Consolidate first (merge similar lines, drop resolved threads, tighten verbose entries), then retry. If still over, ask the user what to drop.
- Unknown section → the writer lists the available sections; do not invent new sections — ask the user where the fact belongs.

## Step 3: Replace Or Remove

**replace** and **remove** are manual edits with guardrails:

- **replace** → edit the matching line in place; prefer replace over add when a similar entry exists.
- **remove** → show the user the exact line and ask "Remove this?" first; delete only after explicit confirmation.
- After any manual edit, re-check the cap: `wc -c < <path-to-MEMORY.md>` must be ≤ 2,500. The root file is also enforced by the drift check (`tests/test_drift_checks.py`).

## Step 4: Confirm

- add/replace → `Saved — will be active from next session.`
- remove → `Removed — will be active from next session.`
- dedup skip → `Already saved — no change needed.`

## Rules

*Dated corrections from feedback. Read before every run; newest last.*

- 2026-07-03: Never store secrets, API keys, private creator data, raw transcripts, or generated media in any MEMORY.md — reference env var names only (e.g. `PROVIDER_API_KEY in .env`).
- 2026-07-03: Creator facts never go to root `context/MEMORY.md`; OS facts never go to a Creator Workspace.

## Self-Update

If the user flags an issue with how memory is written — wrong section, wrong scope, missed dedup, bad consolidation — add a dated entry to `## Rules` above and fix the step immediately. Don't just log it; fix the skill so it doesn't repeat.

## Graceful Degradation

- Target `MEMORY.md` missing → the writer refuses; scaffold it first (root file exists in-repo; creator files come from `init-creator` / `create-runtime-context`).
- File malformed → ask the user before doing anything destructive.
- Ambiguous section target → ask; don't guess.
