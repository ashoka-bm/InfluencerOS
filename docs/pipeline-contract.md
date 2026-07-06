# Pipeline Contract

InfluencerOS v1 is a typed planning pipeline.

## Pipeline

```text
creator.profile
  -> creator.content_schedule
  -> video.understanding_pack, when researching real videos
  -> research.findings
  -> idea.queue
  -> idea.promotion, when the user approves a promotion package
  -> project
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

During the current build phase, local run and creator data are disposable test fixtures unless the user explicitly promotes them. The operator expects to wipe fixture data before real creator onboarding.

## Local Creator Layout

Real creator state lives under `workspace-library/creators/<creator-slug>/`.

```text
AGENTS.md
creator-workspace.json
creator-profile.json
content-schedule.json
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
boards/
system/
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

`register-output-package` is the local file-first registration gate. It copies
upload-ready files from a mirrored asset root into the Project, writes
`output-package/output-package.json`, marks the Project `packaged`, and then
runs project validation; failed validation rolls back the package write and
status change. Text packages (`format_article`, `format_thread`) may record
`thumbnail_or_first_frame_asset_id: null`; visual packages must point that
field to an upload-ready asset. Once a Project is `packaged`, `validate
project` re-checks that the package format matches the Project content unit
and that every `upload_ready[].path` resolves to an existing local file.

`register-published-post` is the publication-registration gate (Phase 2 slice
1). It records a publication a human already performed — never publishing —
by validating a PublishedPostRecord against the registered Output Package
(project/creator/package ids, `assets_used` upload-asset ids, and the
caption/description path must all be declared by the package), writing it
under `published/published-post-records/`, and moving the Project `packaged`
→ `published` on the first record whose `publication_status` attests a live
post (`scheduled`/`failed` records register without the transition). Text
packages publish without a thumbnail: `thumbnail_or_first_frame_asset_id`
may be `null` for `format_article`/`format_thread` records, mirroring the
Output Package rule. At rest, `validate project` re-checks every
registration invariant: record filenames must match their ids, a
`published` Project must carry at least one live record, live records on a
sub-`published` Project fail, no two records may claim the same
`(platform, platform_post_id)` or `public_url` identity, and the Output
Package must stay `upload_ready` at every status from `packaged` onward.

`add-analytics-snapshot` and `import-analytics-csv` are the ingestion gates
(Phase 2 slice 2). Every path — manual entry, the neutral InfluencerOS CSV
template, and any future API connector — writes through one shared seam: the
snapshot must cite a registered Published Post Record whose status attests a
live post, `platform` must match that record, chain ids must match the
Project and package, `hours_since_publish` derives from the record
timestamps when omitted (a snapshot timestamped before publication is
rejected), and `raw_source_ref`/`retention_curve_ref` must resolve to real
files under `analytics/raw/` inside the project. The CSV import is
all-or-nothing. At rest, `validate project` re-checks every ingestion
invariant, including filename-matches-id per snapshot.

`performance-summary.json` is the interpretive Learning OS record (Phase 2
slice 3): one per Project at the project root, authored by the
`create-performance-summary` skill rather than a CLI write gate, so
`validate project` is its enforcement seam. When present, its
`evidence_refs` must resolve inside the project — `output_package_id` to
the registered package, every `published_post_record_id` and
`analytics_snapshot_id` to records on disk, each cited snapshot's parent
post among the cited posts (no cross-post metric attribution), and every
`source_material_ref` a contained project-relative existing file — and its
`stage_findings` must
cover packaging, hook, body retention, payoff, and CTA exactly once each
(record semantics reject a duplicated or missing stage). The summary
attaches at rest with no dedicated Project status; a `published` Project
whose snapshots have matured past 72 hours (the slowest platform reporting
lag) without a summary draws an advisory warning, never a failure.
Interpretations are anchored to the Performance Benchmark Rubric and the
stage-remediation mapping carried in the skill.

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

The evidence link is enforced, not aspirational: a creator lesson is written through `log-learning --evidence --strength` (the `distill-creator-learning` skill), the write fails when an evidence id does not resolve to a real workspace record, and `validate workspace` re-checks every at-rest lesson entry the same way. The strength marker (`single_post_signal` / `multi_post_pattern` / `weak_signal`) carries the ADR 0008 don't-overfit judgment and is pinned to the PerformanceSummary `distilled_lessons` enum.

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
| Content Idea Set (deprecated) | `schemas/content-idea-set.schema.json` | `examples/content-idea-set.example.json` |
| Selected Content Idea (deprecated) | `schemas/selected-content-idea.schema.json` | `examples/selected-content-idea.example.json` |
| Social Template | `schemas/social-template.schema.json` | `examples/social-template.example.json` |
| Applied Social Template | `schemas/applied-social-template.schema.json` | `examples/applied-social-template.example.json` |
| Micro-Journey Video Plan | `schemas/micro-journey-video-plan.schema.json` | `examples/micro-journey-video-plan.example.json` |
| Carousel Plan | `schemas/carousel-plan.schema.json` | `examples/carousel-plan.example.json` |
| Single Image Post Plan | `schemas/single-image-post-plan.schema.json` | `examples/single-image-post-plan.example.json` |
| Story Sequence Plan | `schemas/story-sequence-plan.schema.json` | `examples/story-sequence-plan.example.json` |
| Article Plan | `schemas/article-plan.schema.json` | `examples/article-plan.example.json` |
| Thread Plan | `schemas/thread-plan.schema.json` | `examples/thread-plan.example.json` |
| Base Video Generation Plan | `schemas/base-video-generation-plan.schema.json` | `examples/base-video-generation-plan.example.json` |
| Creator Content Schedule | `schemas/creator-content-schedule.schema.json` | `examples/creator-content-schedule.example.json` |
| Research Run | `schemas/research-run.schema.json` | `examples/research-run.example.json` |
| Research Search Plan | `schemas/research-search-plan.schema.json` | `examples/research-search-plan.example.json` |
| Research Evidence (JSONL) | `schemas/research-evidence.schema.json` | `examples/research-evidence.example.json` |
| Metric Snapshot (JSONL) | `schemas/metric-snapshot.schema.json` | `examples/metric-snapshot.example.json` |
| Research Source Yield (JSONL) | `schemas/research-source-yield.schema.json` | `examples/research-source-yield.example.json` |
| Research Findings (frontmatter) | `schemas/research-findings.schema.json` | `examples/research-findings.example.json` |
| Stable Finding (frontmatter) | `schemas/stable-finding.schema.json` | `examples/stable-finding.example.json` |
| Research Sources | `schemas/research-sources.schema.json` | `examples/research-sources.example.json` |
| Research Hashtags | `schemas/research-hashtags.schema.json` | `examples/research-hashtags.example.json` |
| Research Search Terms | `schemas/research-search-terms.schema.json` | `examples/research-search-terms.example.json` |
| Reference Creators | `schemas/reference-creators.schema.json` | `examples/reference-creators.example.json` |
| Research Watchlist | `schemas/research-watchlist.schema.json` | `examples/research-watchlist.example.json` |
| Idea Queue Entry | `schemas/idea-queue-entry.schema.json` | `examples/idea-queue-entry.example.json` |
| Idea Queue Manifest | `schemas/idea-queue.schema.json` | `examples/idea-queue.example.json` |
| Idea Promotion | `schemas/idea-promotion.schema.json` | `examples/idea-promotion.example.json` |
| Project Warning (JSONL) | `schemas/project-warning.schema.json` | `examples/project-warning.example.json` |
| Content Board | `schemas/content-board.schema.json` | `examples/content-board.example.json` |
| Automation Run | `schemas/automation-run.schema.json` | `examples/automation-run.example.json` |
| System Event | `schemas/system-event.schema.json` | `examples/system-event.example.json` |

The implemented record chain now covers creator setup, the ADR 0020 research module (schedule, runs, search plans, evidence, metric snapshots, source-yield ledgers, findings, intelligence, idea queue, promotions, warnings, board, automation-run and system-event record shapes), project planning anchored on locked Idea Promotions, output packaging, publication records, analytics snapshots, and performance summaries.

The deprecated Content Idea Set and Selected Content Idea records are out of the
intended pipeline (ADR 0020); their schemas remain only as compatibility
artifacts. Projects reference `idea_promotion_id`, and deeper research
provenance resolves transitively through the locked promotion.

## Format-Specific Production Plans

After `AppliedSocialTemplate`, route by `target_format_id`:

- `format_short_form_video` -> `MicroJourneyVideoPlan`, then `BaseVideoGenerationPlan`.
- `format_carousel` -> `CarouselPlan`.
- `format_single_image_post` -> `SingleImagePostPlan`.
- `format_story_sequence` -> `StorySequencePlan`.
- `format_article` -> `ArticlePlan`.
- `format_thread` -> `ThreadPlan`.

## Gate Rules

The user must explicitly approve an idea promotion package before the system
creates production work. The agent may recommend queue ideas and rank them by
goal, but it must not silently promote an idea into the creation funnel.

The agent may recommend a social template for the chosen idea. If the user does not care which template is used, the agent may apply its recommended template and record the rationale. If multiple reasonable structures would change the post meaning, format, or production burden, ask before locking the Applied Social Template.

Provider-backed generation requires explicit approval for the exact call or batch.

## V1 Research Rule

Social trends change quickly. Research output should preserve dated evidence and
update a concise rolling Research Findings summary only when there is a material
finding.

Each research run should record:

- run date and time,
- research mode and scope,
- pre-browse search plan with query intent, candidate sources, and allowed access method,
- platform and platform content type,
- sources and public URLs,
- visible metrics captured at research time,
- source-yield outcomes for checked sources and queries,
- observed patterns,
- evidence strength and limitations,
- fit notes for the Creator Profile,
- links to queue ideas affected by the run.

When research includes real videos, create a Video Understanding Pack before
synthesizing findings or queue updates. It stores timestamp-aware observations
about hooks, first frames, visual structure, transcript framing, template
signals, and creator-fit findings.

The supported external acquisition tool for that step is the installed
`bradautomates/claude-video` `/watch` workflow, or a local equivalent with the
same boundary. `/watch` working files are temporary; the canonical pipeline
record is the Video Understanding Pack. Native captions and local frame
extraction are allowed research actions. Whisper or other API-backed
transcription fallback requires exact approval/configuration, and upstream
hooks or command launchers are not part of InfluencerOS v1.
