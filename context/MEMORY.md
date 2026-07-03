# InfluencerOS Memory

Curated working memory for InfluencerOS as the first-party OS persona.

This file is for durable system-level facts, active threads, and pending decisions about InfluencerOS itself. Keep creator-specific memory inside Creator Workspaces.

Do not store secrets, private creator data, API keys, raw transcripts, or generated media here. Cap: 2,500 bytes, enforced by `python3 -m influencer_os memory-write` and the drift check.

## Active Threads

- Phase 0C parity hardening runs as batches A-G (short-term plan Execution Decisions, 2026-07-02); batches A-D landed by 2026-07-03.
- Phase 1 starts after 0C exits, slice order: intake import, readiness validation, ADR 0020 research module, research/queue workflow, promotion, production planning, output packaging.

## Environment Notes

- Agentic OS architecture reference (authoritative): `/Users/ashokaji/code/External repos/Agentic Academy/agentic-os`
- `/Users/ashokaji/code/agentic-tools/ai-system` is the user's shared global-rules repo; it is NOT the Agentic OS architecture reference (workstream 0).
- OS construction docs: `docs/os-construction/`; verification commands live in `docs/os-construction/progress.md`.

## Pending Decisions

- None. Phase 0C execution decisions are recorded in the short-term plan; do not reopen without user approval.

