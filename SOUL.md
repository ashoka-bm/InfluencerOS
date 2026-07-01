# InfluencerOS Soul Adapter (OpenClaw / Hermes)

Thin runtime adapter for OpenClaw/Hermes-style agents. This file is an **adapter, not an identity**: the operating contract lives in `AGENTS.md`, and the first-party OS identity lives in `context/SOUL.md`. Read `AGENTS.md` first and follow it.

@AGENTS.md

The purchased Agentic OS architecture reference lives at `/Users/ashokaji/code/External repos/Agentic Academy/agentic-os`.

## Adapter Notes

- The durable read order is defined once in `AGENTS.md`. Do not maintain a second copy here.
- Identity, voice, and boundaries for the InfluencerOS persona are in `context/SOUL.md`, not here.
- Surface any proposed divergence from the Agentic OS reference before implementing it (see `AGENTS.md` and `docs/os-construction/divergence-test.md`).
- When the user signals wrap-up or a session produced deliverables, run the `wrap-up` skill (ADR 0016).
