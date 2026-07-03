# Repository Map

This map shows where each part of InfluencerOS should live. It describes file ownership and workflow calls, not implementation details.

## Root Files

| Path | Role |
| --- | --- |
| `AGENTS.md` | Canonical Codex and repo agent instructions. |
| `CLAUDE.md` | Claude adapter that points to the same repo context. |
| `SOUL.md` | OpenClaw/Hermes-style agent identity adapter. |
| `README.md` | Human entry point: what the repo does, current flow, commands, and docs. |
| `CONTEXT.md` | Product vocabulary and naming source of truth. |
| `ARCHITECTURE.md` | Durable architecture direction. |
| `context/` | First-party InfluencerOS OS persona memory and learnings. |
| `brand_context/` | First-party InfluencerOS positioning, voice, ICP, samples, and assets. |

## Durable Planning Docs

| Path | Role |
| --- | --- |
| `docs/os-construction/prd.md` | Product requirements, scope, acceptance criteria, and phase requirements. |
| `docs/os-construction/roadmap.md` | Phase roadmap with deterministic exit criteria. |
| `docs/os-construction/short-term-plan.md` | Next handoff plan for parity hardening. |
| `docs/os-construction/progress.md` | Current progress and latest verification record. |
| `docs/os-construction/repository-map.md` | Construction map for file ownership and record data-flow. |
| `docs/os-construction/architecture-map.md` | File-granular file map plus skill and CLI call graphs. |
| `docs/os-construction/agentic-os-alignment.md` | How InfluencerOS copies or diverges from Agentic OS. |
| `docs/os-construction/agentic-os-copy-plan.md` | Audit of what to copy, adapt, defer, or reject from Agentic OS. |
| `docs/os-construction/agentic-os-parity-plan.md` | Plan for adapting toward close Agentic OS parity without restarting. |
| `docs/os-construction/divergence-test.md` | Manual and automatable check for Agentic OS divergence. |
| `docs/os-construction/visual-architecture-maps.md` | Standard for Excalidraw architecture and workflow maps. |
| `docs/os-construction/context-matrix.md` | Context loading matrix for OS and Creator Workspace scopes. |
| `docs/os-construction/skill-registry.md` | Skill trigger, write, and override registry. |
| `docs/os-construction/process-learnings.md` | Repo-level process and skill improvement learnings. |
| `docs/os-construction/adversarial-review.md` | Ranked divergence ledger from the Agentic OS parity review. |
| `docs/os-construction/maps/` | Markdown records for created architecture maps. |
| `docs/pipeline-contract.md` | Typed step-to-step pipeline contract. |
| `docs/provider-boundary.md` | Approval boundary for provider-backed work. |
| `docs/creator-workspace-structure.md` | Creator workspace layout and local state policy. |
| `docs/adr/` | Architectural decisions. |
| `docs/workflows/` | Human-readable workflow specs. |
| `docs/templates/` | Templates copied into creator workspaces or generated records. |
| `docs/handoffs/` | Durable handoff notes from prior planning or implementation passes. |

## Runtime Code

| Path | Role |
| --- | --- |
| `influencer_os/cli.py` | CLI command surface (`validate` incl. `research`/`queue` targets, `init-creator`, `import-intake`, `set-intake-status`, `sync-creator-runtime`, `update-creators`, `init-project`, `init-run`, `memory-write`, `log-learning`). It should call workflow helpers, not hold product rules. |
| `influencer_os/validation.py` | Fail-closed schema subset validation and disk-derived example coverage. |
| `influencer_os/creator_workspaces.py` | Creator Workspace scaffolding, source intake import and provenance, sync/update propagation, validation, and readiness gates. |
| `influencer_os/projects.py` | Project scaffolding, validation, and promotion-anchored provenance resolution. |
| `influencer_os/research.py` | Research-module validation: JSONL records, findings frontmatter (scoped YAML subset), queue consistency, and the idea-promotion gate. |
| `influencer_os/memory.py` | Bounded `memory-write` and `log-learning` writers (ADR 0016). |
| `influencer_os/runs.py` | Dry-run initialization and run records. |

## Contracts

| Path | Role |
| --- | --- |
| `schemas/` | JSON Schema contracts for every durable record. |
| `examples/` | Valid example records for schemas and CLI tests. |
| `tests/` | Unit tests for CLI, scaffolding, and schema behavior. |

## Skills

| Path | Role |
| --- | --- |
| `skills/influencer-os/SKILL.md` | Main conductor skill for the creation flow. |
| `skills/create-influencer/SKILL.md` | Creator setup conductor. |
| `skills/create-creator-profile/SKILL.md` | Creator Profile drafting. |
| `skills/create-identity/SKILL.md` | Rich identity drafting. |
| `skills/create-soul/SKILL.md` | Creator psychology and behavior drafting. |
| `skills/create-personal-brand/SKILL.md` | Brand strategy drafting. |
| `skills/create-voice-samples/SKILL.md` | Voice sample extraction and curation. |
| `skills/create-reference-library/SKILL.md` | Reference Library planning. |
| `skills/create-runtime-context/SKILL.md` | Tiny always-loaded creator context files. |

Baseline source skills live under repo `skills/<skill-name>/SKILL.md` (kebab-case, no category prefix, optional per-skill `references/` and `SKILL.local.md` per ADR 0017). `init-creator` copies those skills into each Creator Workspace under `.claude/skills/<skill-name>/SKILL.md`; `sync-creator-runtime` refreshes copied runtime skills while preserving creator `SKILL.local.md` files and creator-only skill folders; `update-creators` runs a backup-protected batch refresh (ADR 0018). The full skill roster, including planned producer skills and the `wrap-up`/`memory-write` system skills, is in `architecture-map.md`.

## Local State

Local state is ignored and must stay out of git.

```text
workspace-library/
  creators/
    <creator-slug>/
      AGENTS.md
      creator-workspace.json
      creator-profile.json
      context/
        SOUL.md
        USER.md
        MEMORY.md
      brand_context/
      .claude/
        skills/
          <skill-name>/
            SKILL.md
            SKILL.local.md
      sources/
      references/
      research/
      projects/
      memory/
      progress/
  runs/
  index/
```

## Creation Flow Record Data-Flow

This section shows the record data-flow through the creation flow: which record produces which. The skill-to-skill and CLI call graphs are in `architecture-map.md`.

The full creation flow uses a conductor-plus-skills structure.

```text
skills/influencer-os/SKILL.md
  -> load Creator Workspace and Creator Profile
  -> call video understanding workflow when real videos are used
  -> call social research workflow
  -> create Social Research Pack
  -> create Social Post Format Shortlist
  -> create Content Idea Set with exactly five ideas
  -> stop for Selected Content Idea
  -> create Applied Social Template
  -> route by target_format_id
      -> Micro-Journey Video Plan
      -> Carousel Plan
      -> Single Image Post Plan
      -> Story Sequence Plan
  -> create Base Video Generation Plan when needed
  -> stop at Generation Approval Gate
  -> create Output Package when an artifact exists
```

Runtime helpers should follow the same direction:

```text
influencer_os/cli.py
  -> creator_workspaces.py
  -> projects.py
  -> runs.py
  -> validation.py
  -> schemas/
```

## Boundary Rule

Every workflow step may be flexible internally, but its boundary must be deterministic:

- named input records,
- named output record,
- schema or template,
- validation command or review checklist,
- provenance links,
- explicit human approval gate when required.
