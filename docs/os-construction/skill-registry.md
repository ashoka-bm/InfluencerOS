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

## System Skills

| Skill | Triggers on | Reads | Writes | Override support |
| --- | --- | --- | --- | --- |
| `wrap-up` | session end signals, wrap-up requests, sessions that produced deliverables | git status, `context/learnings.md`, this registry, context matrix | `context/learnings.md`, `docs/os-construction/process-learnings.md`, skill files, `context/MEMORY.md` | yes |
| `memory-write` | remember this, note that, save to memory, update memory, forget about | target `MEMORY.md` | target `MEMORY.md` (2,500-byte cap via `python3 -m influencer_os memory-write`) | yes |

## External Tool Integrations

These are not repo-owned skills and must not be added to conductor
`dependencies` frontmatter.

| Tool | Used by workflow | Purpose | Boundary |
| --- | --- | --- | --- |
| `watch` (`bradautomates/claude-video`) | Social research / Video Understanding Pack | Inspect public or user-provided local videos, sample frames, obtain native captions, and provide timestamped evidence for `VideoUnderstandingPack` records | external optional tool; no vendoring; Whisper/API fallback, first-run dependency installs, and batches require explicit approval |

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

Coverage for these planned skills is deferred per the Context Coverage Rule until they are built; the producer skills are built in their Phase 1 slices — the workstream-10 conductor call graph marks them `[PLANNED]` with a halt rule, and each marker is an open build obligation. Per ADR 0017 the machine-actionable source for skill dependencies is each skill's `dependencies` frontmatter (enforced against `docs/os-construction/architecture-map.md` by the call-graph drift check), not a duplicated registry column; skill categories are expressed by this registry's section tables (core workflow, creator setup, system, future).
