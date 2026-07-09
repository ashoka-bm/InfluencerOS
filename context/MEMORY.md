# InfluencerOS Memory

Curated working memory for InfluencerOS as the first-party OS persona.

This file is for durable system-level facts, active threads, and pending decisions about InfluencerOS itself. Keep creator-specific memory inside Creator Workspaces.

Do not store secrets, private creator data, API keys, raw transcripts, or generated media here. Cap: 2,500 bytes, enforced by `python3 -m influencer_os memory-write` and the drift check.

## Active Threads

- Phases 0-3 and Creative Direction are complete; closeout details live in `docs/os-construction/progress.md`.
- Visual creators require a separately approved tokenized personal brand board after Reference Library planning and before foundation readiness; production spaces/props bind to typed location/object asset IDs and render placeholders while assets remain prompt-ready.
- Research-acquisition connectors (ADR 0022 + 0027, influencer_os/connectors/) pull Reddit/X/Firecrawl/LinkedIn/YouTube evidence; env-gated and dormant until a provider key is set. Key presence is standing approval for the research tier only (call cap + kill switch); generation calls keep exact approval. Exercise the manual research-intelligence loop against real creator runs before scheduled automation.
- The first real (paid) generation provider adapter is deliberately unpicked (ADR 0023 Decision 3): the operator chooses it, and it lands as its own approved batch following the adapter contract. Scheduled/unattended generation stays Phase 4.
- validate all <creator-workspace> is the alpha release gate (composed workspace/research/queue/board/projects run); the runbook for real onboarding is docs/onboard-real-creator-runbook.md. ADR 0022 run 2 (2026-07-07): reddit discovery + youtube + firecrawl work live; reddit.com blocks free enrichment reads (metrics missing); xAI needs credits; Apify unkeyed.

## Environment Notes

- Agentic OS architecture reference (authoritative): `/Users/ashokaji/code/External repos/Agentic Academy/agentic-os`
- `/Users/ashokaji/code/agentic-tools/ai-system` is the user's shared global-rules repo; it is NOT the Agentic OS architecture reference (workstream 0).
- OS construction docs: `docs/os-construction/`; verification commands live in `docs/os-construction/progress.md`.

## Pending Decisions

- First real generation provider adapter (operator's pick, ADR 0023 Decision 3). All other phase execution decisions are recorded in their plans/ADRs; do not reopen without user approval.
