# ADR 0017: Skill Layout Finalization

## Status

Accepted

Extends ADR 0014 and ADR 0015.

## Context

The repo's planning docs conflicted about whether the repo-central `skills/<skill-name>/` layout is provisional or already decided (recorded in `docs/os-construction/adversarial-review.md`). This ADR removes that ambiguity.

The Agentic OS reference stores skills under `.claude/skills/{category}-{skill}/` with:

- category prefixes (`mkt-`, `str-`, `ops-`, `viz-`, `meta-`, `tool-`, `vid-`, `00-`),
- a self-contained package per skill (`SKILL.md`, optional `SKILL.local.md`, `references/`, `assets/`, `scripts/`),
- machine-actionable frontmatter (`name`, `version`, `description`, `allowed-tools`, `dependencies`, `metadata`),
- a `## Dependencies` table and, for orchestrators, a phase→owner table with explicit `Skill(skill: "...")` and `Agent(tool: "...")` invocations (see `docs/building-skills.md` and `.claude/skills/00-social-content/SKILL.md`).

ADR 0014 and ADR 0015 already established repo-central `skills/<skill-name>/SKILL.md` as the baseline source, copied into each Creator Workspace under `.claude/skills/` with `SKILL.local.md` overrides at both scopes. What was missing versus the reference: per-skill `references/`, the `## Rules`/`## Self-Update` pattern, machine-actionable frontmatter and dependency declarations, and a worked `SKILL.local.md` example. Category prefixes were never adopted, and the skill registry already baked plain kebab-case names.

## Decision

Repo-central `skills/<skill-name>/SKILL.md` is the final v1 source layout, not provisional.

Adopt these Agentic OS conventions:

- Each skill may carry a per-skill `skills/<skill-name>/references/` folder for progressive disclosure; deep guidance moves out of the thin `SKILL.md`. Shared cross-skill material stays under `docs/`.
- Each `SKILL.md` frontmatter declares machine-actionable fields mirroring the reference: `name`, `description`, `allowed-tools`, and `dependencies` (skills it invokes). Conductor skills add a `## Dependencies` table and a phase→owner table with explicit `Skill(skill: "...")` invocations.
- Behavior-changing skills carry `## Rules` and `## Self-Update`; overrides live in `SKILL.local.md` at repo scope (`skills/<skill-name>/SKILL.local.md`) and creator scope (`.claude/skills/<skill-name>/SKILL.local.md`).
- Ship at least one worked `SKILL.local.md` example.

Recorded divergence from the reference:

- InfluencerOS does not adopt Agentic OS category prefixes and does not relocate skills to `.claude/skills/{category}-{skill}/` at the repo root. Skill names stay plain kebab-case; category grouping lives in the skill-registry `category` column instead. Reason: the repo-central source layout in ADR 0015 is simpler for a single-product OS, and the runtime copy into Creator Workspaces already provides the `.claude/skills/` execution root.

## Consequences

- The provisional-versus-decided conflict is resolved; agents can treat `skills/<skill-name>/` as final.
- Skills become self-contained and machine-actionable; the conductor call graph can be declared in frontmatter and verified.
- The category-prefix divergence is explicit and approved, so it stops reading as drift.
- Skill-registry and context-matrix rows must record the `category` and `dependencies` for each skill.
