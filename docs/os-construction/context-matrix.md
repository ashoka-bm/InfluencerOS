# InfluencerOS Context Matrix

Load only the context needed for the workflow.

InfluencerOS has two context scopes:

- **OS scope**: the repository's first-party persona and process memory.
- **Creator scope**: one ignored Creator Workspace under `workspace-library/creators/<creator-slug>/`.

## Matrix Key

| Mark | Meaning |
| --- | --- |
| `start` | loaded at session or workflow start when relevant |
| `full` | read the full file |
| `summary` | read only enough to understand the current decision |
| `writes` | may create or update this file |
| `lazy` | load only when the step needs it |
| `never` | do not load by default |

## OS Scope

| Workflow | `context/SOUL.md` | `context/USER.md` | `context/MEMORY.md` | `context/learnings.md` | `brand_context/` | `docs/os-construction/` |
| --- | --- | --- | --- | --- | --- | --- |
| Architecture planning | summary | summary | full | lazy | lazy | full |
| Agentic OS divergence test | summary | summary | full | lazy | lazy | full |
| InfluencerOS marketing/content | full | summary | summary | lazy | full | summary |
| Skill/process improvement | summary | summary | full | full | lazy | summary |
| Routine code/test work | lazy | lazy | lazy | lazy | never | summary |

## Creator Scope

| Workflow | Creator Profile | Identity | Soul | Personal Brand | Voice Samples | References | Research | Project Records | Creator Memory |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Creator setup | writes | writes | writes | writes | writes | writes | lazy | never | writes |
| Social research | full | summary | summary | full | lazy | lazy | writes | lazy | summary |
| Idea generation | full | summary | summary | summary | lazy | summary | full | lazy | summary |
| Idea promotion | full | summary | summary | summary | lazy | summary | writes | writes | summary |
| Template application | full | lazy | lazy | summary | lazy | lazy | full | full | lazy |
| Production planning | full | full | full | summary | full | full | full | full | summary |
| Generation planning | full | full | full | summary | full | full | full | full | lazy |
| Output packaging | full | lazy | lazy | summary | lazy | full | summary | full | lazy |
| Publication registration | summary | never | never | never | never | lazy | never | writes | never |
| Analytics ingestion | summary | never | never | never | never | never | never | writes | never |
| Learning distillation | full | lazy | lazy | summary | lazy | lazy | summary | full | writes |

## Skill Coverage

Skill context can be covered by an individual skill row or by the workflow row that invokes the skill.

Current workflow coverage:

| Skill | Context coverage |
| --- | --- |
| `influencer-os` | Social research, idea generation, idea promotion, template application, production planning, generation planning, output packaging, publication registration, analytics ingestion, learning distillation |
| `create-influencer` | Creator setup |
| `create-research-findings` | Social research |
| `manage-idea-queue` | Idea generation |
| `promote-idea` | Idea promotion |
| `apply-social-template` | Template application |
| `create-production-plan` | Production planning, generation planning |
| `create-output-package` | Output packaging |
| `register-published-post` | Publication registration |
| `ingest-analytics` | Analytics ingestion |
| `create-creator-profile` | Creator setup |
| `create-identity` | Creator setup |
| `create-soul` | Creator setup |
| `create-personal-brand` | Creator setup |
| `create-voice-samples` | Creator setup |
| `create-reference-library` | Creator setup |
| `create-runtime-context` | Creator setup |
| `wrap-up` | Skill/process improvement |
| `memory-write` | Skill/process improvement |

## External Tool Coverage

| Tool | Context coverage |
| --- | --- |
| `watch` (`bradautomates/claude-video`) | Social research / Video Understanding Pack; use the Social research workflow row and write only distilled observations to `research/` |

## Skill Override Rule

Core skill source files live in repo `skills/<skill-name>/SKILL.md`.

Creator runtime copies live in each Creator Workspace:

```text
workspace-library/creators/<creator-slug>/.claude/skills/<skill-name>/SKILL.md
```

Creator-specific overrides live beside the copied runtime skill:

```text
workspace-library/creators/<creator-slug>/.claude/skills/<skill-name>/SKILL.local.md
```

For InfluencerOS itself as the first-party persona, OS-specific overrides live under:

```text
skills/<skill-name>/SKILL.local.md
```

When invoking a skill from a Creator Workspace, load the copied runtime `SKILL.md` first, then any matching `SKILL.local.md`. Local rules override base rules for that creator only.

Promote a local rule into the base skill only when repeated feedback shows it should apply system-wide.
