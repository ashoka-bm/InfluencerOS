# ADR 0015: Copied Creator Runtime Skills

## Status

Accepted

## Context

Agentic OS is designed so a user can open Claude or Codex inside a client folder and treat that folder as the working root. To support that, Agentic OS copies runtime system files into each client workspace and syncs shared skill updates while preserving local overrides.

InfluencerOS needs the same operating model for Creator Workspaces. A creator workspace should be runnable as its own root so work for one creator does not depend on loading another creator's context or the full repository root.

ADR 0014 established root baseline skills and scoped `SKILL.local.md` overrides. It did not fully define whether Creator Workspaces receive copied runtime skill files.

## Decision

InfluencerOS will use copied creator runtime skills.

The repository root remains the source of truth for baseline skills:

```text
skills/<skill-name>/SKILL.md
```

Each Creator Workspace receives a runtime copy under:

```text
workspace-library/creators/<creator-slug>/.claude/skills/<skill-name>/SKILL.md
```

Creator-specific overrides live beside the copied runtime skill:

```text
workspace-library/creators/<creator-slug>/.claude/skills/<skill-name>/SKILL.local.md
```

When a Creator Workspace is initialized, InfluencerOS copies all repo baseline skills into `.claude/skills/`.

When a Creator Workspace runtime is synced, InfluencerOS refreshes copied baseline `SKILL.md` files from repo `skills/` while preserving:

- creator `SKILL.local.md` files,
- creator-only skill folders,
- creator context,
- creator brand context,
- creator projects,
- creator memory,
- creator progress,
- creator `.env` or tool-managed auth.

Hooks, cron templates, settings sync, script sync, and Command Centre runtime files remain deferred unless separately approved.

Root OS persona overrides may still live beside the root baseline skill:

```text
skills/<skill-name>/SKILL.local.md
```

Promote a creator-local rule into the root baseline skill only after repeated feedback shows the rule applies system-wide.

## Consequences

- Agents can run from inside a Creator Workspace root without reaching back into unrelated creator state.
- Baseline skill updates can be propagated into creators while creator-specific adaptations survive.
- Creator workspaces become closer to Agentic OS client workspaces.
- The sync command must be conservative and must not delete creator-only skills or private creator data.
- Future work can add script, settings, hooks, or cron propagation only through explicit architecture approval.
