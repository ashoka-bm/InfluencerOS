# ADR 0018: Creator Workspace Propagation Scripts

## Status

Accepted

Resolves the open propagation decision deferred in ADR 0015.

## Context

The Agentic OS reference propagates the operating system into each client workspace with dedicated scripts:

- `scripts/add-client.sh` creates `clients/{slug}/` and copies `.claude/skills/`, `.claude/settings.json`, `.claude/hooks/` and `hooks_info/`, `scripts/` (with local proxy wrappers), `cron/templates/`, `.env`, and a seeded `context/learnings.md`, then generates a client `AGENTS.md` and a `CLAUDE.md` wrapper.
- `scripts/update-clients.sh` syncs shared skills and scripts from the root into every client workspace (the root→client refresh, preserving client data, client-only skills, and `SKILL.local.md`). This is the analog for InfluencerOS's creator refresh. (`scripts/update.sh` with `scripts/lib/pull.sh` is a separate *upstream* refresh that InfluencerOS does not need.)

ADR 0015 approved skills-only copying (`init-creator` copies baseline skills; `sync-creator-runtime` refreshes them while preserving creator `SKILL.local.md` and creator-only skills) and deferred scripts, settings, hooks, cron templates, and Command Centre files, leaving "script/settings/hooks/cron propagation" as an open alignment decision.

The user has ruled to build the propagation mechanism now, for full parity with the reference. One constraint: hooks and cron themselves remain deferred (roadmap Deferred sections), so there is currently nothing in those zones to propagate.

InfluencerOS implements operations as a Python CLI (`influencer_os/`), not bash `scripts/`. The propagation mechanism is therefore built as CLI subcommands, not `.sh` files. This is a pre-existing, sensible divergence recorded here rather than reversed.

## Decision

Build the InfluencerOS propagation mechanism as Python CLI subcommands mirroring the semantics of the reference's client scripts.

Mechanism (implemented in a later TDD pass; specified here):

- Extend `init-creator` (the `add-client` analog) to create the workspace and copy the propagatable set.
- Add `update-creators` and extend `sync-creator-runtime` (the `update-clients.sh` analog) to refresh propagated files with a backup-protected, conflict-safe merge that preserves creator `SKILL.local.md`, creator-only skills, `context/`, `brand_context/`, `projects/`, `memory/`, `progress/`, and `.env`.
- Add `influencer_os/` helpers (the `scripts/lib/` analog) for shared copy, backup, and diff-report logic.

Propagation zones:

- Propagate now: baseline skills into `.claude/skills/`, and the workspace `AGENTS.md`/`CLAUDE.md` wrappers and directory structure per `docs/creator-workspace-structure.md`.
- Propagate when the zone exists (gated, not permanently deferred): scripts, settings, hooks, and cron templates. The subcommands are structured to carry these zones, but each zone stays inert until its own subsystem is un-deferred by a separate approval. This closes the propagation mechanism decision without contradicting the standing hooks/cron deferral, because there is no hook or cron content to copy yet.

Fix required alongside this decision: the workspace scaffold and `creator-workspace.schema.json` must include the `.claude/skills/` directory that ADR 0015 and `docs/creator-workspace-structure.md` already mandate.

## Consequences

- Creator Workspaces gain a real, parity-level sync mechanism and remain runnable as their own roots.
- The mechanism is forward-compatible: enabling hooks, cron, or settings later fills existing zones without redesign.
- The standing hooks/cron deferral is preserved; only the propagation *mechanism* is approved now, not new automation content.
- The open alignment decision moves from open to accepted; `agentic-os-alignment.md` is updated accordingly.
- The propagation-as-CLI-subcommands divergence from bash `scripts/` is explicit and approved.
