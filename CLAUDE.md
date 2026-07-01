# InfluencerOS Claude Guide

Thin Claude adapter. The canonical operating contract — rules, source-of-truth list, durable read order, and product invariant — lives in `AGENTS.md`. Read it first and follow it.

@AGENTS.md

The purchased Agentic OS architecture reference lives at `/Users/ashokaji/code/External repos/Agentic Academy/agentic-os`. Repo-specific rules live in `AGENTS.md`.

## Claude-Specific Notes

- The durable read order is defined once in `AGENTS.md`. Do not maintain a second copy here.
- The non-negotiables (Agentic OS alignment unless an approved divergence, local-first v1, deterministic workflow boundaries, exact-approval provider gates, no unrequested platform adapters/publishing/scheduling/analytics) are in the `AGENTS.md` Operating Rules. Follow them.
- When the user signals wrap-up or a session produced deliverables, run the `wrap-up` skill to capture learnings and reconcile the skill registry (ADR 0016).
