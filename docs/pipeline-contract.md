# Pipeline Contract

InfluencerOS v1 is a typed planning pipeline.

## Pipeline

```text
creator.profile
  -> video.understanding_pack, when researching real videos
  -> social.research_pack
  -> social.post_format_shortlist
  -> content.idea_set
  -> content.selected_idea
  -> format-specific template application
  -> format-specific production plan
  -> output.record, when generation or import creates an artifact
```

## Local Run Layout

The CLI initializes dry-run state under `workspace-library/runs/<run-id>/`.

```text
run.json
events.jsonl
records/
  creator-profile.json
```

`workspace-library/` is ignored by git. The repository stores product contracts, schemas, examples, and tests; run state stays local.

## Local Creator Layout

Real creator state lives under `workspace-library/creators/<creator-slug>/`.

```text
AGENTS.md
creator-workspace.json
creator-profile.json
context/SOUL.md
context/USER.md
context/MEMORY.md
brand_context/identity.md
brand_context/soul.md
brand_context/personal-brand.md
sources/
references/
  character/
  locations/
  outfits/
  objects/
  video-style/
research/
projects/
memory/
progress/
.claude/skills/
  <skill-name>/
    SKILL.md
    SKILL.local.md
```

The Creator Profile is the typed contract for automation. The identity file, soul file, personal brand file, and reference library preserve richer creator continuity. Projects, output packages, published records, analytics, and memory stay creator-scoped so the Learning OS can improve future ideas without blending creator identities.

Creator runtime skills live under `.claude/skills/<skill-name>/SKILL.md` inside the Creator Workspace. They are copied from repo `skills/<skill-name>/SKILL.md` so an agent can run from the creator root. Creator-specific overrides live beside them as `SKILL.local.md`. Runtime sync refreshes copied baseline skills while preserving local overrides and creator-only skills.

`creator-profile.json` should be an operational summary: strong enough for routine research, ideas, scripts, plans, and output packaging, but not a full structured copy of every identity, psychology, brand, and reference detail.

## Creator Authoring Flow

Creator workspaces may start from a master intake document. The import flow drafts the typed Creator Profile, identity file, soul file, personal brand file, and reference library requirements. Once reviewed, those split files become the maintained source of truth.

The original intake should be retained only as provenance when needed, with source path, import date, and extraction notes.

## Analytics Ingestion

The Learning OS uses API-primary analytics ingestion with manual and CSV fallback. Every ingestion path writes normalized Analytics Snapshot records under the relevant Creator Workspace.

```text
output package
  -> published post record
  -> analytics snapshot
  -> learning distillation
  -> future research and idea generation
```

Every Output Package must include a Creative Performance Map. It maps packaging, hook, body retention, payoff, and CTA stages to source references, intended effects, primary metrics, and optional variants. It should point to raw files and records instead of duplicating their contents.

Output Packages use a universal core with optional platform adaptations. Platform adaptations may specify platform, format, title, caption or description, thumbnail or first-frame asset, hashtags or tags, posting-time recommendation, platform-specific CTA, crop, duration, and Creative Performance Map variants.

Missing platform metrics must be recorded as absent or null, never inferred. Raw API payloads and exports may be preserved locally when useful, but secrets and access tokens must never be stored in analytics records.

Analytics Snapshots must preserve enough dimensions for performance attribution:

- packaging performance: impressions, reach, thumbnail or first-frame exposure, click-through rate, title or caption variant, thumbnail asset ID,
- hook performance: first-frame pattern, opening hook, three-second retention, early drop-off, swipe-away or skip signals,
- body performance: average view duration, retention curve points, midpoint retention, replay behavior,
- payoff performance: completion rate, loop/replay rate, shares, saves, comments, sentiment themes, follows or subscribers,
- CTA performance: clicks, profile visits, link clicks, conversions, opt-ins, purchases, or other declared CTA results,
- context controls: platform, format, publish time, creator, audience target, topic, content pillar, duration, trend source, and distribution notes.

## Learning Memory

Raw Analytics Snapshots remain creator-scoped evidence. Durable creator memory stores distilled lessons plus short performance summaries that link back to Output Packages, Published Post Records, Analytics Snapshots, and source material.

Future research and idea generation should use distilled lessons by default. Agents may inspect raw analytics when diagnosing performance, verifying a lesson, or planning an intentional test.

## Local SQL Index

Creator workspace files are canonical. The local SQL database is an index and query layer, not the only copy of product records.

Default path:

```text
workspace-library/index/influencer-os.sqlite
```

Indexed rows should preserve source path, record ID, record type, content hash, indexed timestamp, creator ID or slug, and project ID when applicable. The index must be rebuildable from workspace files.

## Semantic Lookup

InfluencerOS also maintains a semantic lookup projection for low-context agent recall. It indexes curated decision-support material such as identity files, soul files, personal brand files, research summaries, distilled learnings, performance summaries, and selected postmortems.

Raw analytics, raw API payloads, raw exports, secrets, private comments, and large generated media should not be semantically indexed by default.

Agents should combine SQL and semantic lookup: SQL for exact metric and record queries; semantic lookup for prior lessons, similar-topic performance patterns, audience interpretation, and creative precedent.

## Record Types

| Record type | Schema | Example |
| --- | --- | --- |
| Creator Workspace | `schemas/creator-workspace.schema.json` | `examples/creator-workspace.example.json` |
| Creator Profile | `schemas/creator-profile.schema.json` | `examples/creator-profile.example.json` |
| Reference Library | `schemas/reference-library.schema.json` | `examples/reference-library.example.json` |
| Project | `schemas/project.schema.json` | `examples/project.example.json` |
| Output Package | `schemas/output-package.schema.json` | `examples/output-package.example.json` |
| Published Post Record | `schemas/published-post-record.schema.json` | `examples/published-post-record.example.json` |
| Analytics Snapshot | `schemas/analytics-snapshot.schema.json` | `examples/analytics-snapshot.example.json` |
| Performance Summary | `schemas/performance-summary.schema.json` | `examples/performance-summary.example.json` |
| Social Research Pack | `schemas/social-research-pack.schema.json` | `examples/social-research-pack.example.json` |
| Video Understanding Pack | `schemas/video-understanding-pack.schema.json` | `examples/video-understanding-pack.example.json` |
| Social Post Format | `schemas/social-post-format.schema.json` | `examples/social-post-format.example.json` |
| Content Idea Set | `schemas/content-idea-set.schema.json` | `examples/content-idea-set.example.json` |
| Selected Content Idea | `schemas/selected-content-idea.schema.json` | `examples/selected-content-idea.example.json` |
| Social Template | `schemas/social-template.schema.json` | `examples/social-template.example.json` |
| Applied Social Template | `schemas/applied-social-template.schema.json` | `examples/applied-social-template.example.json` |
| Micro-Journey Video Plan | `schemas/micro-journey-video-plan.schema.json` | `examples/micro-journey-video-plan.example.json` |
| Carousel Plan | `schemas/carousel-plan.schema.json` | `examples/carousel-plan.example.json` |
| Single Image Post Plan | `schemas/single-image-post-plan.schema.json` | `examples/single-image-post-plan.example.json` |
| Story Sequence Plan | `schemas/story-sequence-plan.schema.json` | `examples/story-sequence-plan.example.json` |
| Base Video Generation Plan | `schemas/base-video-generation-plan.schema.json` | `examples/base-video-generation-plan.example.json` |

The implemented record chain now covers creator setup, research, project planning, output packaging, publication records, analytics snapshots, and performance summaries.

## Format-Specific Production Plans

After `AppliedSocialTemplate`, route by `target_format_id`:

- `format_short_form_video` -> `MicroJourneyVideoPlan`, then `BaseVideoGenerationPlan`.
- `format_carousel` -> `CarouselPlan`.
- `format_single_image_post` -> `SingleImagePostPlan`.
- `format_story_sequence` -> `StorySequencePlan`.

## Gate Rules

The user must explicitly choose the Selected Content Idea. The agent may recommend an idea, but it must not record selection on the user's behalf.

The agent may recommend a social template for the chosen idea. If the user does not care which template is used, the agent may apply its recommended template and record the rationale. If multiple reasonable structures would change the post meaning, format, or production burden, ask before locking the Applied Social Template.

Provider-backed generation requires explicit approval for the exact call or batch.

## V1 Research Rule

Social trends change quickly. Each Social Research Pack must record:

- research date,
- research scope,
- sources,
- observed patterns,
- trend confidence,
- fit notes for the Creator Profile.

When research includes real videos, create a Video Understanding Pack before synthesizing the final Social Research Pack. It stores timestamp-aware observations about hooks, first frames, visual structure, transcript framing, template signals, and creator-fit findings.
