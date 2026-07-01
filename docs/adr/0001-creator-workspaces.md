# ADR 0001: Root OS With Creator Workspaces

## Status

Accepted

## Context

InfluencerOS is intended to become a public system for operating a stable of AI creators. The repository should contain the reusable operating system: schemas, examples, docs, tests, skills, prompt templates, and workflow contracts.

Real creators need richer and more private material than the public repo should hold: identity files, personality notes, brand files, visual references, generated assets, run history, published post records, analytics, platform account data, and local progress notes.

Agentic OS uses a root operating system with isolated client workspaces. InfluencerOS should use the same separation, adapted to creator identity and content production.

## Decision

InfluencerOS will use the repository root as the shared operating system and ignored per-creator workspaces as the local/private creator boundary.

The default local layout is defined in `docs/creator-workspace-structure.md`. At a high level:

```text
workspace-library/creators/{creator-slug}/
  AGENTS.md
  creator-workspace.json
  creator-profile.json
  context/
    SOUL.md
    USER.md
    MEMORY.md
  brand_context/
    identity.md
    soul.md
    personal-brand.md
    voice-samples.md
  sources/
  references/
  research/
  projects/
  memory/
  progress/
```

`creator-profile.json` is the typed automation contract. The markdown files and reference folders provide richer human-readable and media-backed continuity. System docs, schemas, examples, and tests remain in the public repo. Real creator workspaces remain under `workspace-library/`, which is ignored by git.

## Consequences

- The Creator Profile stays machine-stable and can reference richer creator artifacts by ID or path.
- Each creator keeps separate memory, research history, output records, published records, and analytics.
- Cross-creator learning can be added later without blurring individual creator identity.
- Provider-backed generation remains a later phase and still requires explicit approval.
- The Learning OS can be modeled before generation is automated by allowing imported/manual output records and published post records.
