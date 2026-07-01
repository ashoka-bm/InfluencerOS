# ADR 0014: First-Party OS Persona And Skill Overrides

## Status

Accepted

## Context

The initial architecture treated InfluencerOS as the operating system only. The Agentic OS reference also treats the root system as a client-like persona with its own context, brand context, memory, learnings, skills, and local overrides.

InfluencerOS needs the same capability because the system itself may need marketing, positioning, documentation, launch content, and process memory at the operator level. At the same time, individual creators need their own separated memory, brand context, and skill adaptations.

If all feedback is written into one global learning file, creator-specific lessons can pollute system skills. If every client-specific change edits the core skill file, the core skill will drift toward one creator's needs.

## Decision

InfluencerOS will support two context scopes:

- first-party OS persona context in root `context/` and `brand_context/`,
- creator-specific context inside ignored Creator Workspaces.

Root `context/` stores InfluencerOS system persona memory:

- `context/SOUL.md`,
- `context/USER.md`,
- `context/MEMORY.md`,
- `context/learnings.md`.

Root `brand_context/` stores reviewed positioning, voice, ICP, samples, and assets for InfluencerOS itself.

Creator context remains under:

```text
workspace-library/creators/<creator-slug>/
```

Core skills remain under repo `skills/`. Scope-specific overrides use `SKILL.local.md`:

```text
skills/<skill-name>/SKILL.local.md
workspace-library/creators/<creator-slug>/skills/<skill-name>/SKILL.local.md
```

When invoking a skill, load the base `SKILL.md` first and then the applicable `SKILL.local.md`. Local rules override base rules only in that scope.

Promote a local rule into the base skill only after repeated feedback shows it should apply across the system.

InfluencerOS will not use "memory palace" in v1. Use:

- `SQL index` for exact structured lookup,
- `semantic lookup projection` for meaning-based recall,
- `Creator Memory` for distilled creator lessons.

## Consequences

- InfluencerOS can create content for itself without pretending it is a creator workspace.
- Creator memories stay separated.
- Skill improvement can happen locally before changing core skills.
- Base skills stay stable and reusable.
- Agents must check the context matrix and skill registry before adding or changing skills.
- Root context files must never store secrets, private creator data, API keys, raw transcripts, or generated media.

