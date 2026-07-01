# ADR 0019: Adapter Model — Canonical AGENTS, Thin Importers, SOUL as Identity

## Status

Accepted

## Context

The always-loaded adapter files were found to drift from the Agentic OS reference and from each other (recorded in `docs/os-construction/adversarial-review.md`):

- `AGENTS.md`, `CLAUDE.md`, and `SOUL.md` each restate a 13-item read order. The lists are maintained by hand and can diverge; the alignment doc's claim that the three "point to the same product docs" is not enforced.
- `CLAUDE.md` does not import `AGENTS.md`. In the reference, `CLAUDE.md` is a thin wrapper that imports `@AGENTS.md`, so there is one source of rules and no duplication.
- There is a dual-SOUL naming collision. Root `SOUL.md` is described as an OpenClaw/Hermes runtime adapter, while `context/SOUL.md` is the first-party OS persona identity. In the reference, `AGENTS.md` is the shared canonical contract (Codex reads it directly), `CLAUDE.md` is a thin wrapper, and `SOUL.md` is the agent identity at `context/SOUL.md` — not a per-runtime adapter.

The owner's stated model ("`claude.md` / `agents.md` / `soul.md` are the same file for Claude / Codex / Hermes") diverges from the reference on two points: the reference has no separate `CODEX.md`, and `SOUL.md` is identity, not an adapter. The owner has ruled to follow the reference.

## Decision

Adopt the reference adapter model.

- `AGENTS.md` is the single canonical operating contract: rules, source of truth, the durable read order, and the product invariant. Every runtime (Claude, Codex, OpenClaw/Hermes) reads it.
- `CLAUDE.md` becomes a thin wrapper: import `AGENTS.md` (`@AGENTS.md`) plus only Claude-specific runtime notes. It no longer restates the read order.
- Root `SOUL.md` becomes a thin OpenClaw/Hermes runtime wrapper that imports `AGENTS.md`, explicitly labeled as an adapter, not an identity. It no longer restates the read order.
- `context/SOUL.md` remains the sole identity document (first-party OS persona). The collision is resolved by role separation: root `SOUL.md` = runtime adapter; `context/SOUL.md` = identity.
- The durable read order is defined once, in `AGENTS.md`. `CLAUDE.md` and root `SOUL.md` reference it by import, never by copy.
- Specify an adapter drift check (implemented in the drift-check pass) that fails if `CLAUDE.md` or root `SOUL.md` stop importing `AGENTS.md` or restate a divergent read order.

## Consequences

- One canonical source of rules; adapters cannot silently diverge.
- The dual-SOUL collision is resolved; identity lives only in `context/SOUL.md`.
- Claude, Codex, and Hermes all resolve to the same contract, meeting the owner's three-runtime need through thin importers instead of three divergent copies.
- `agentic-os-alignment.md` updates: the "thin root adapters" row moves from an unverified claim to an enforced, drift-checked invariant.
- The read-order duplication is removed from `CLAUDE.md` and root `SOUL.md` when the adapter-foundation restructure lands.
