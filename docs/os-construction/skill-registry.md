# InfluencerOS Skill Registry

This registry lists InfluencerOS skills, trigger conditions, writes, and local override policy.

Core skill source files live under repo `skills/`. Creator Workspaces receive copied runtime skill folders under `.claude/skills/`. Creator-specific overrides live beside the copied runtime skill as `SKILL.local.md`. System persona overrides may live beside the core source skill as `SKILL.local.md`.

## Registration Rules

- Skill folder name should be kebab-case.
- `SKILL.md` is the core rule set.
- `SKILL.local.md` is scope-specific and must not replace the core file.
- Every new skill needs a row in this registry and context coverage in `docs/os-construction/context-matrix.md`.
- New behavior-changing skills need tests, examples, or a review checklist.
- Skills that call providers must name the approval gate.

## Context Coverage Rule

Context coverage can be explicit or workflow-based:

- explicit coverage: the context matrix has a row for the individual skill,
- workflow coverage: the registry row names a workflow that has a context-matrix row,
- deferred coverage: the registry marks the skill as future or deferred and says when coverage will be added.

Setup subskills are covered by the `Creator setup` workflow row until they need separate load rules.

## Core Workflow Skills

| Skill | Triggers on | Reads | Writes | Override support |
| --- | --- | --- | --- | --- |
| `influencer-os` | content creation flow, research-to-queue, idea promotion to project | Creator Profile, research, project records, context matrix | planning records, generation plans, output records | yes |
| `create-influencer` | create creator, setup creator, new influencer | intake, references, templates | Creator Workspace files | yes |

## Creator Setup Subskills

| Skill | Triggers on | Writes |
| --- | --- | --- |
| `create-creator-profile` | draft creator profile | `creator-profile.json` |
| `create-identity` | draft identity | `brand_context/identity.md` |
| `create-soul` | draft creator soul | `brand_context/soul.md` |
| `create-personal-brand` | draft personal brand | `brand_context/personal-brand.md` |
| `create-voice-samples` | extract or curate voice samples | `brand_context/voice-samples.md` |
| `create-reference-library` | plan visual/audio references | `references/reference-library.json` |
| `create-runtime-context` | create tiny runtime context | `context/SOUL.md`, `context/USER.md`, `context/MEMORY.md` |

## Missing Future Skills

| Skill | Purpose | Timing |
| --- | --- | --- |
| `create-research-findings` | produce concise rolling findings backed by dated evidence | Planning OS |
| `manage-idea-queue` | create and update scored Idea Queue entries | Planning OS |
| `promote-idea` | record human-approved Idea Promotion and create project records | Planning OS |
| `apply-social-template` | adapt a selected template to an idea | Planning OS |
| `create-production-plan` | route promoted idea to format-specific plan | Planning OS |
| `create-output-package` | register package and provenance | Planning OS |
| `distill-creator-learning` | convert performance evidence into creator memory | Learning OS |
| `wrap-up` | capture learnings, self-correct skills, reconcile this registry, promote memory | System — ADR 0016 (Phase 0C) |
| `memory-write` | bounded, deduped `context/MEMORY.md` writes | System — ADR 0016 (Phase 0C) |

Coverage for these planned skills is deferred per the Context Coverage Rule until they are built; context-matrix rows land with their build workstream (WS9 for the system skills, WS10 for the producer skills). Per ADR 0017 this registry gains `category` and `dependencies` columns in workstream 10; the columns above are the pre-ADR-0017 set.
