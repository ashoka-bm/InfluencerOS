# Research And Ideas Implementation Plan

Status: **Slices 3 and 4 complete (2026-07-03).** The schema surface of
this plan (implementation-sequence steps 1-6, 11, 12 plus the promotion
gate) landed via the user-approved Execution Decisions below; slice 4
(the Research Findings and Idea Queue workflow — run-scoped consistency
checks, recall index, content board, retention prune, and the
`create-research-findings`/`manage-idea-queue` producer skills) landed via
the Slice 4 Execution Decisions at the end of this plan, batches A-E. The
verification records live in `docs/os-construction/progress.md`. A
post-landing review hardening batch closed the findings recorded in
Post-Review Hardening below (same day). Next: slice 5, `promote-idea`.
Last updated: 2026-07-03

## Goal

Implement the Research and Ideas module as a creator-scoped, platform-scoped
research system that produces:

- concise rolling Research Findings,
- immutable dated research evidence,
- a scored Idea Queue,
- human-approved Idea Promotions,
- Project provenance links,
- Kanban-readable warnings and board cards,
- research intelligence files,
- automation run and system event records for scheduled jobs.

This replaces the old `ContentIdeaSet` / `SelectedContentIdea` pipeline with the
ADR 0020 model.

## Module Boundary

This plan implements the Research and Ideas module surface defined in
`docs/workflows/research-and-ideas.md` (Module Interface) and `ARCHITECTURE.md`
(Module Boundaries): public interface records are Research Findings, the Idea
Queue, and Idea Promotions; runs, evidence, snapshots, and intelligence are
module-internal and resolve through the recall index. Downstream records
reference their immediate upstream record and resolve deeper provenance
transitively through the locked Idea Promotion.

## Success Condition

The first implementation slice is complete when:

- new research-module schemas exist and validate examples,
- the Creator Content Schedule validates and captures cadence expectations,
  content goals, calendar slots, and drift checks,
- creator workspaces have the new research folder layout,
- queue ideas can be stored one file per entry,
- evidence and metric snapshots can be appended as JSONL and validated line by
  line,
- `IdeaPromotion` can create one or more Projects with research provenance,
- promotion refuses to create Projects for formats production does not yet
  support and records the approval intent on the queue entry instead,
- Project source refs no longer depend on `selected_content_idea_id`,
- a rebuildable Content Board projection can show idea and project cards,
- warnings can appear as informational card flags,
- research intelligence files validate and distinguish user-approved core
  references from suggested candidates,
- automation runs and system events can record scheduled research work and
  notification flags (record shapes only; no scheduler, hook, cron, or Telegram
  delivery in this slice),
- retention rules have a runnable owner (a manual `prune` command that research
  runs may invoke),
- deprecated `ContentIdeaSet` and `SelectedContentIdea` records are no longer in
  the intended pipeline.

## Video Understanding Tool Integration

Post-slice integration decision (2026-07-03): `bradautomates/claude-video`
`/watch` is the supported external acquisition tool for the existing Video
Understanding Pack phase.

This does not change the slice 3 schema surface. It fills the already-built
`VideoUnderstandingPack` seam with a concrete tool workflow:

- public URL or user-provided local video,
- native captions when available,
- sampled frames through local tooling,
- optional Whisper fallback only with exact approval/configuration,
- distilled observations stored as `VideoUnderstandingPack` records,
- evidence refs carried into Idea Queue entries, Idea Promotions, Projects, and
  Output Packages through `video_understanding_pack_ids`.

Do not vendor the upstream scripts, hooks, or command launchers in this slice.
If repeated slice 4 usage shows that output import needs to be mechanized, add a
small local import command that maps watched-video reports into
`VideoUnderstandingPack` records instead of copying the whole external plugin.

## Implementation Sequence

1. Add schemas and examples for the full research-module slice.
2. Update `project.schema.json` source refs, statuses, and project paths.
3. Update project examples and validation to use `IdeaPromotion` provenance.
4. Add JSONL validation support for evidence, metric snapshots, and warnings.
5. Add workspace layout helpers for research folders.
6. Add CLI validation targets for research records and creator research state.
7. Add local recall-index records for evidence ID lookup.
8. Add research intelligence files and validation.
9. Add automation run and system event logging records or projections (record
   shapes only; scheduled execution and Telegram delivery stay behind the
   separately approved research automation build-out).
10. Add a manual `prune` CLI that applies the workflow retention rules;
    research runs may invoke it, and unattended scheduled pruning stays
    deferred to the research automation build-out.
11. Mark old idea-set and selected-idea examples as deprecated or move them to a
    compatibility area.
12. Update docs, skill instructions, and tests to use the new vocabulary, and
    reconcile `docs/os-construction/skill-registry.md` and
    `docs/os-construction/context-matrix.md` per the AGENTS.md skill rules.

## Creator Workspace Layout

```text
workspace-library/creators/<creator-slug>/
  content-schedule.json
  research/
    findings.md
    runs/
      <research-run-id>/
        research-run.json
        run-summary.md
        evidence.jsonl
        metric-snapshots.jsonl
        video-understanding-packs/
    intelligence/
      sources.json
      hashtags.json
      search-terms.json
      reference-creators.json
      watchlist.json
    stable-findings/
      <stable-finding-id>.md
    idea-queue/
      queue.json
      entries/
        <idea-queue-entry-id>.json
    idea-promotions/
      <idea-promotion-id>.json
  boards/
    content-board.json
  system/
    project-warnings.jsonl
    creator-events.jsonl
  projects/
    <project-id>/
      project.json
      evidence-brief.md
```

The exact `system/` location can move if the broader operations subsystem chooses
a different creator-scoped projection path.

## Schema Draft

### Creator Content Schedule

File: `schemas/creator-content-schedule.schema.json`

Required fields:

- `creator_content_schedule_id`
- `creator_profile_id`
- `creator_slug`
- `updated_on`
- `cadence_expectations`
- `content_goals`
- `calendar_slots`
- `drift_checks`

Optional fields:

- `blackout_dates`
- `active_campaigns`
- `time_sensitive_insertions`
- `recently_published_refs`

Important nested fields:

- `content_goals[]`: `goal_id`, `name`, `description`, `target_mix`,
  `preferred_platforms`, `preferred_formats`
- `calendar_slots[]`: `slot_id`, `target_date`, `date_flexibility`,
  `content_goal_id`, `topic_cluster`, `status`
- `drift_checks`: `under_served`, `over_served`, `recent_repetition_notes`

Notes:

- Exact dates are allowed, but cadence should support intentionally irregular
  publishing.
- Format and platform targets are optional guidance, not hard quotas.
- The schedule is a creator-planning record read by research, not a
  research-module record. It stores no board card IDs; board links resolve the
  other way, from cards to slot IDs.

### Research Run

File: `schemas/research-run.schema.json`

Required fields:

- `research_run_id`
- `creator_profile_id`
- `started_on`
- `completed_on`
- `mode`
- `scope`
- `platforms`
- `material_update`
- `outputs`

Enums:

- `mode`: `scheduled_needs`, `wildcard_discovery`,
  `reference_creator_watchlist`, `topic_overlap_scan`, `urgent_trend_check`,
  `queue_refresh`, `hashtag_search_term_check`

Important nested fields:

- `outputs`: `finding_ids`, `idea_queue_entry_ids`, `evidence_ids`,
  `metric_snapshot_ids`, `research_intelligence_updates`
- `run_status`: `completed`, `completed_no_material_update`, `failed`
- `error`, optional

### Research Evidence

File: `schemas/research-evidence.schema.json`

Storage: JSONL in `evidence.jsonl`, one validated object per line.

Required fields:

- `evidence_id`
- `research_run_id`
- `creator_profile_id`
- `source_url`
- `platform`
- `platform_content_type`
- `captured_on`
- `source_relationship`
- `source_summary`
- `topic_tags`
- `content_pillar_ids`
- `signal_summary`
- `reusable_elements`
- `confidence`
- `limitations`

Important nested fields:

- `source_account`: `handle`, `display_name`, `url`
- `visible_metrics`: `views`, `likes`, `comments`, `shares`, `saves`,
  `reposts`, `other`
- `reusable_elements`: `hook`, `thumbnail_or_first_frame`,
  `structure_or_pacing`, `format_notes`, `copyable_moves`, `avoid_notes`

Enums:

- `source_relationship`: `adjacent_creator`, `general_trend`, `farther_field`
- `confidence`: `low`, `medium`, `high`

### Metric Snapshot

File: `schemas/metric-snapshot.schema.json`

Storage: JSONL in `metric-snapshots.jsonl`, one validated object per line.

Required fields:

- `metric_snapshot_id`
- `evidence_id`
- `research_run_id`
- `creator_profile_id`
- `captured_on`
- `platform`
- `visible_metrics`

Optional fields:

- `posted_on`
- `observed_age`
- `velocity_estimate`
- `reference_creator_baseline`
- `outperformance_note`

### Research Findings

File: `schemas/research-findings.schema.json`

Storage: YAML frontmatter metadata for `research/findings.md`.

Required fields:

- `research_findings_id`
- `creator_profile_id`
- `last_updated`
- `last_ran`
- `summary_char_limit`
- `active_platforms`
- `active_topic_clusters`
- `source_run_ids`
- `finding_ids`

Body rules:

- Markdown body should stay under `summary_char_limit`.
- Organize by topic cluster first, with platform notes inside.
- Include a short `Watch Now` section.
- Each material finding should include a stable `finding_id`.
- Stale findings appear only when strategically important.

### Research Intelligence

Files:

- `schemas/research-sources.schema.json`
- `schemas/research-hashtags.schema.json`
- `schemas/research-search-terms.schema.json`
- `schemas/reference-creators.schema.json`
- `schemas/research-watchlist.schema.json`

Storage:

```text
research/intelligence/
  sources.json
  hashtags.json
  search-terms.json
  reference-creators.json
  watchlist.json
```

Required shared fields per item:

- item ID,
- creator profile ID,
- platform scope when applicable,
- usefulness score, 0-100,
- status,
- added on,
- updated on,
- last evaluated on,
- source or rationale.

Reference creator fields:

- `reference_creator_id`
- `handle`
- `display_name`
- `platforms`
- `relationship`: `adjacent_creator`, `general_trend`, `farther_field`
- `user_approved_core_reference`
- `usefulness_score`
- `measurement_rationale`
- `audience_overlap_note`
- `recent_signal_note`

Rules:

- Research runs may suggest additions, updates, and removals.
- Adding or removing user-approved core reference creators requires user
  approval.
- Hashtags and search terms are platform-scoped.
- Usefulness can fall to zero; user-approved watchlist items should be presented
  for removal instead of silently deleted.

### Idea Queue Entry

File: `schemas/idea-queue-entry.schema.json`

Storage: one JSON file per entry in `research/idea-queue/entries/`.

Required fields:

- `idea_queue_entry_id`
- `creator_profile_id`
- `status`
- `title`
- `hook`
- `premise_summary`
- `intended_payoff`
- `topic_cluster`
- `platform_recommendations`
- `format_recommendations`
- `schedule_fit_type`
- `evidence_refs`
- `scores`
- `created_on`
- `updated_on`

Optional fields:

- `source_finding_ids`
- `content_pillar_ids`
- `score_deltas` (versus the initial score snapshot; meaningless at creation,
  so not required)
- `urgency_window`
- `creator_fit_notes`
- `production_notes`
- `avoid_notes`
- `stale_on`
- `linked_idea_promotion_ids`
- `linked_project_ids`

The queue entry stores no `content_card_id`. Board card IDs are derived
deterministically from the source record ID, so canonical records stay free of
projection state.

Enums:

- `status`: `new`, `reviewed`, `shortlisted`, `needs_more_research`,
  `promoted`, `rejected`, `expired`
- `schedule_fit_type`: `scheduled_slot`, `wildcard`, `content_goal_fit`,
  `unscheduled`

Required scores, each 0-100 plus rationale:

- `evidence_strength`
- `viral_potential`
- `audience_nurture_value`
- `creator_fit`
- `schedule_fit`
- `production_readiness`
- `urgency`
- `measurement_clarity`

Reference shape:

```json
{
  "research_run_id": "research_run_example",
  "evidence_id": "evidence_example",
  "metric_snapshot_ids": ["metric_snapshot_example"],
  "video_understanding_pack_ids": ["video_research_example"]
}
```

`video_understanding_pack_ids` is optional and present when real videos were
analyzed, preserving the Product Invariant's video-evidence trace through
promotion and production.

Variant rule:

- Keep platform variants inside one queue entry when execution is materially the
  same.
- Split into separate queue entries when platform or format execution materially
  differs.

### Idea Queue Manifest

File: `schemas/idea-queue.schema.json`

Storage: `research/idea-queue/queue.json`

Required fields:

- `idea_queue_id`
- `creator_profile_id`
- `updated_on`
- `entry_refs`

Purpose:

- Fast board loading.
- Status counts.
- Manual or computed grouping metadata.

### Idea Promotion

File: `schemas/idea-promotion.schema.json`

Storage: one JSON file per promotion in `research/idea-promotions/`.

Required fields:

- `idea_promotion_id`
- `idea_queue_entry_id`
- `creator_profile_id`
- `approved_by`
- `approved_on`
- `intended_payoff`
- `approved_platforms`
- `approved_formats`
- `research_finding_ids` (may be empty when the idea came from evidence without
  a material findings update)
- `evidence_refs`
- `score_snapshot`
- `creative_elements_to_carry_forward`
- `project_ids_created`
- `promotion_status`

Optional fields:

- `approval_note` (approval never requires a rationale)
- `schedule_slot_ids` (absent for wildcard ideas)

Enums:

- `approved_by`: `user` for v1
- `promotion_status`: `active`, `superseded`, `cancelled`

Rules:

- Promotion is a permanent locked approval snapshot; the schedule and findings
  context it names is captured here because those records mutate later.
- Human approval does not require a rationale.
- One promotion can create multiple Projects.
- Create an `IdeaPromotion` only when at least one approved format is
  production-supported; otherwise record the approval intent on the queue entry
  and keep the idea in the queue until the format lands.
- Approved formats that are not yet production-supported are recorded in the
  promotion but create no Project until the production build-out adds them.

### Project Warning

File: `schemas/project-warning.schema.json`

Storage: JSONL in `project-warnings.jsonl`, one validated object per line.

Required fields:

- `project_warning_id`
- `idea_queue_entry_id`
- `warning_type`
- `severity`
- `message`
- `detected_on`
- `suggested_actions`

Conditional fields:

- `project_id` and `idea_promotion_id`: required when the warning targets
  promoted work; absent for queue-level warnings such as
  `stronger_variant_found` on an unpromoted idea, so warning flags can appear
  on parent idea cards as well as child project cards

Optional fields:

- `source_evidence_ids`
- `source_score_ids`
- `resolved_status`

Enums:

- `warning_type`: `source_trend_stale`, `urgency_window_expired`,
  `evidence_strength_dropped`, `creator_fit_concern`,
  `schedule_slot_no_longer_fits`, `platform_payoff_changed`,
  `reference_source_unavailable`, `stronger_variant_found`
- `severity`: `info`, `important`, `urgent`

Rules:

- Informational only in v1.
- No acknowledgement required.
- No blocking or automatic triggers.

### Automation Run

File: `schemas/automation-run.schema.json`

Storage: operations subsystem path, with creator-scoped projections when
applicable.

Required fields:

- `automation_run_id`
- `job_id`
- `job_type`
- `started_on`
- `completed_on`
- `run_status`
- `creator_profile_id`, nullable
- `material_update`
- `linked_research_run_ids`
- `event_ids`

Optional fields:

- `last_error`
- `threshold_config`
- `notification_summary`

Rules:

- Every scheduled or recurring job writes an `AutomationRun`.
- Research automations also create or update `ResearchRun` records.
- V1 automation may update findings, queue, warnings, badges, and notifications;
  it must not promote ideas.
- This slice lands the record shape only. No scheduler, hook, or cron runs
  until the research automation build-out is explicitly approved; the record
  exists first so manual runs and future automation share one audit shape.

### System Event

File: `schemas/system-event.schema.json`

Storage: append-only OS-level log, with creator-scoped projections such as
`system/creator-events.jsonl`.

Required fields:

- `event_id`
- `occurred_on`
- `event_type`
- `severity`
- `message`
- `source_type`
- `source_id`

Enums:

- `severity`: `info`, `important`, `urgent` (aligned with Project Warning)

Optional fields:

- `creator_profile_id`
- `creator_slug`
- `project_id`
- `idea_queue_entry_id`
- `content_card_id`
- `linked_record_refs`
- `delivery_channel`
- `delivery_status`

Rules:

- User-facing notifications are event log entries plus Kanban flags.
- No notification acknowledgement is required in v1.
- Telegram is the intended first external channel, but delivery lands with the
  research automation build-out, not this slice.
- Threshold settings may be global and creator-specific.

### Content Board

File: `schemas/content-board.schema.json`

Storage: `boards/content-board.json`

Required fields:

- `content_board_id`
- `creator_profile_id`
- `updated_on`
- `columns`
- `cards`
- `manual_order`

Important nested fields:

- `cards[]`: `content_card_id`, `card_type`, `status`, `parent_card_id`,
  `source_record_type`, `source_record_id`, `warning_badges`, `child_card_ids`
- `card_type`: `idea`, `project`

Rules:

- Rebuildable projection, not source of truth.
- Idea queue entries are parent cards.
- Projects are child cards.
- Card IDs are derived deterministically from source record IDs (for example
  `card_<idea_queue_entry_id>` and `card_<project_id>`). Canonical records
  never store card IDs, and rebuilds reproduce the same card IDs so manual
  order survives.
- Manual order is projection metadata.

### Project Schema Changes

Update `schemas/project.schema.json`.

Status changes:

- Replace `idea_selected` with `created`.
- Rename `planned` to `planning` (breaking change to current examples and
  tests; update them in the same step).
- Add: `ready_for_generation`, `generated`. Keep: `packaged`, `published`,
  `analyzed`, `archived`.

Source refs should require:

- `idea_promotion_id` (the single upstream interface ref; queue entry,
  findings, evidence, and metric snapshots resolve transitively through the
  locked promotion)
- `reference_asset_ids` (production-time continuity assets; may be empty at
  creation)

Optional source refs, cached from the promotion for convenience only:

- `idea_queue_entry_id`
- `research_finding_ids`
- `research_evidence_ids`
- `metric_snapshot_ids`
- `video_understanding_pack_ids`
- `evidence_brief_path`
- `source_platforms`
- `source_platform_content_types`

Project path changes:

- Remove the `idea/` path constant (the `SelectedContentIdea` folder is gone;
  see ADR 0012's later update).
- Add an `evidence_brief` path constant for `evidence-brief.md`.

Content unit types:

- `content_unit_type` keeps the visual-first enum in this slice. Text unit
  types (`article`, `thread`) land in the production build-out step, together
  with their format routing. Until then the promotion gate blocks Projects for
  unsupported formats.

## Validation And CLI Draft

Add validation capabilities:

- validate schema examples for all new schemas,
- validate JSONL line by line,
- validate `findings.md` frontmatter,
- validate creator research workspace layout,
- validate idea queue entry references resolve through the local index when
  available,
- warn, not fail, on unresolved evidence for human-approved promotions,
- fail unresolved evidence for any future automated promotion path.

Candidate CLI commands:

```bash
python3 -m influencer_os validate examples
python3 -m influencer_os validate research <creator-workspace>
python3 -m influencer_os validate queue <creator-workspace>
python3 -m influencer_os validate board <creator-workspace>
python3 -m influencer_os rebuild-index <creator-workspace>
python3 -m influencer_os rebuild-board <creator-workspace>
python3 -m influencer_os prune <creator-workspace>
```

`prune` applies the retention rules from the workflow doc (30-day default for
unpromoted weak leads, preserve everything a promotion references, compact
metric snapshots into trajectories). It runs manually or inside a research run;
nothing schedules it in this slice.

## Recall Index Draft

SQLite remains the default local index backend.

The recall index should resolve:

- `evidence_id` to file path and JSONL line/offset,
- `metric_snapshot_id` to file path and JSONL line/offset,
- `finding_id` to `findings.md` section or stable finding metadata,
- `idea_queue_entry_id` to file path,
- `idea_promotion_id` to file path,
- `project_id` to file path,
- `content_card_id` to projection record.

Minimum indexed columns:

- record ID,
- record type,
- creator profile ID,
- creator slug,
- project ID when applicable,
- source path,
- line number or record offset when applicable,
- content hash,
- indexed timestamp.

## Migration Notes

- Do not delete old schemas immediately.
- Mark `content-idea-set` and `selected-content-idea` as deprecated in docs and
  examples.
- Update docs and skills to stop teaching the old five-idea pipeline.
- Update project examples after `IdeaPromotion` exists.
- Keep `SocialResearchPack` and `VideoUnderstandingPack` only if they remain
  useful as compatibility or specialized evidence records; the new research
  module should not depend on `ContentIdeaSet`.

## Resolved Design Questions

- Canonical records (`IdeaQueueEntry`, `Project`, `CreatorContentSchedule`) do
  not store board card IDs. Card IDs are derived deterministically from source
  record IDs, so the board stays a rebuildable projection.
- Project provenance is transitive: `source_refs` require only
  `idea_promotion_id` (plus production-time `reference_asset_ids`); deeper refs
  are optional cached copies.
- Automation and notification work in this slice is record shapes only;
  scheduling and Telegram delivery are a separately approved build-out.

## Execution Decisions (User-Approved 2026-07-03)

Phase 1 slice 3 executes this plan's schema surface; the four Open
Implementation Questions are resolved here. Do not reopen without user
approval.

Correction (2026-07-03, during execution): `youtube_short` and
`youtube_video` are dropped from the seeded content-type enum below — YouTube
is not in the ADR 0020 research platform set, so those values could never be
paired with a valid `platform`. They join the enum when YouTube joins the
platform set. `x_thread` is added alongside `x_post`.

1. Slice split: slice 3 lands implementation-sequence steps 1-6, 11, and 12
   (all module schemas and examples as one coherent set per ADR 0020, the
   project schema migration, JSONL and frontmatter validation, workspace
   layout, CLI validation targets, deprecation, and doc/registry/matrix
   reconciliation) plus the promotion-gate validation moved out of Phase 0C
   workstream 12. Steps 7-10 (recall index, board rebuild command, prune
   command) defer to slice 4, where the Research Findings and Idea Queue
   workflow first exercises them. AutomationRun and SystemEvent land as
   record shapes only, per ADR 0020.
2. Downstream provenance swap: `applied-social-template`, the four
   format-specific production plans, and `output-package` replace
   `selected_content_idea_id` with `idea_promotion_id` in the same slice, and
   the project cross-record checks compare that field against
   `project.source_refs.idea_promotion_id`. Leaving the old field in
   downstream records would keep `SelectedContentIdea` in the intended
   pipeline, which the success condition forbids.
3. Warning projections (open question 1): creator-scoped projections live at
   `system/project-warnings.jsonl` and `system/creator-events.jsonl` under
   the Creator Workspace, as drafted. The caveat stands: the operations
   subsystem may relocate `system/` later.
4. Stable findings (open question 2): Markdown-only with validated YAML
   frontmatter (`stable-finding.schema.json` covering id, creator, dates,
   source run/finding refs) — the same pattern as `findings.md`. No JSON
   sidecars; a second file per finding is a drift surface.
5. Enum naming (open question 3): `platform` is the closed ADR 0020 set —
   `x`, `instagram`, `tiktok`, `substack`, `medium`, `reddit`, `facebook`,
   `linkedin`. `platform_content_type` is a closed, curated snake_case enum
   seeded from the ADR examples (`x_post`, `instagram_reel`,
   `instagram_post`, `instagram_story`, `instagram_carousel`,
   `tiktok_video`, `substack_article`, `substack_note`, `medium_article`,
   `reddit_thread`, `reddit_comment`, `facebook_post`, `facebook_reel`,
   `linkedin_post`, `linkedin_article`, `youtube_short`, `youtube_video`);
   extending it is a deliberate schema change. Because the validator resolves
   only intra-file `$ref`, each schema repeats the enums, and a drift test
   asserts every occurrence matches one canonical constant.
6. Examples (open question 4): continue the `luna-fit` sample creator so
   research examples chain to the existing profile, workspace, and project
   examples. All sample data is disposable build/test fixture data per the
   build test data policy.

Execution batches, guardrails first:

- Batch A: all new schemas plus examples (steps 1, plus the
  `stable-finding` frontmatter schema); enum drift test.
- Batch B: JSONL line validation, `findings.md`/stable-finding frontmatter
  validation, and the `validate research` / `validate queue` CLI targets.
- Batch C: project schema migration (statuses, source refs, paths),
  downstream provenance swap, promotion-gate validation (a promotion must
  name a real queue entry; unresolved evidence refs warn for human-approved
  promotions and fail for future automated paths), and `init-project`
  updates including the `evidence-brief.md` scaffold.
- Batch D: workspace layout helpers (research folders, board, system
  projections), deprecation markers for `content-idea-set` and
  `selected-content-idea`, doc/skill vocabulary updates, registry and
  context-matrix reconciliation, and the full exit-criteria run recorded in
  `docs/os-construction/progress.md`.

## Post-Review Hardening (User-Approved 2026-07-03)

An adversarial post-landing review (schema-vs-plan conformance plus a code
correctness pass) confirmed the slice landed per the Execution Decisions and
surfaced the gaps below; one approved batch closed them the same day.

Fixed:

1. The promotion gate and `validate queue` now resolve
   `video_understanding_pack_ids` in `evidence_refs` (against
   `research/video-understanding-packs/` and
   `research/runs/<run-id>/video-understanding-packs/`). Before the fix a
   promotion citing a nonexistent video pack validated silently, leaving the
   Product Invariant's video-evidence trace unenforced at the research layer.
2. The enum drift check now pins `project.schema.json`'s cached
   `source_platforms`/`source_platform_content_types` enum copies —
   previously the only embeddings outside the drift test's scan, despite
   Execution Decision 5 requiring every occurrence pinned.
3. Project warnings enforce the pairing rule this plan states: `project_id`
   and `idea_promotion_id` appear together when a warning targets promoted
   work, and neither for queue-level warnings. The schema cannot express the
   semantic trigger, so the check lives in JSONL validation with `path:line`
   context.
4. The raw run-JSONL id scan (`collect_research_record_ids`, reachable from
   `validate queue` and `validate project` without prior schema validation)
   reports file and line on malformed JSON and on records missing their id
   field, instead of surfacing a bare `json.loads` error.
5. Run folder names must match `research_run_id`, matching the filename==id
   rule entries and promotions already enforce.
6. Queue manifest `status_counts`, when present, must match entry statuses
   (explicit zero counts are allowed; omitting a present status fails).
7. JSONL splitting uses newline-only splitting; `splitlines()` broke records
   on raw U+2028/U+2029, which are legal inside JSON strings.
8. Sixteen tests pin previously untested failure paths: the six promotion
   resolution/cached-ref failure modes in `projects.py`, invalid-JSON JSONL
   lines, stable-finding schema failures, and each fix above.

Deferred to slice 4 (with the recall index, which subsumes most of them):

- per-record `research_run_id` checked against the containing run folder,
- `evidence_refs[].research_run_id` resolution (today refs resolve through a
  global id pool across runs),
- reconciling `research-run.json` `outputs` id lists against the run's JSONL
  contents.

Open question — RESOLVED by the Approval Surface Decisions below: the locked
promotion constrains project targets, `approved_formats` is a closed enum,
and the production-support rule is a mechanical gate check.

### Approval Surface Decisions (User-Approved 2026-07-03)

The two open questions from the review rounds were decided together and
landed as one batch before slice 4:

1. Format vocabulary is a closed enum. `approved_formats`,
   `format_recommendations`, `target_formats`, `preferred_formats`, and
   `format_id` all pin to the canonical v1 list (`format_short_form_video`,
   `format_carousel`, `format_single_image_post`, `format_story_sequence`)
   with drift-test enforcement, following the platform-enum precedent. The
   enum is the full known vocabulary, not just production-supported formats:
   the plan explicitly lets a promotion record not-yet-supported approved
   formats as long as one is supported, so text formats join the enum (not a
   separate list) at the production build-out. A code drift check ties
   `PRODUCTION_SUPPORTED_FORMATS` to `PRODUCTION_PLAN_SCHEMAS` and the
   canonical enum.
2. The promotion gate mechanically enforces the success condition: a
   promotion approving no production-supported format fails validation
   (record the approval intent on the queue entry instead). Hard fail, not a
   warning — such a promotion should not exist.
3. The locked promotion constrains project targets. `target_formats` must be
   a subset of `approved_formats` (shared vocabulary, direct check). For
   `platform_targets` the vocabularies differ — they are distribution
   surfaces (`instagram_reels`, `youtube_shorts`), not research platforms —
   so the check is a mapped subset: a surface that maps to an ADR 0020
   research platform (`instagram_reels` → `instagram`) must be approved,
   while surfaces off the research set (`youtube_*`) stay exempt because the
   universal format legitimately travels there. Known caveat: an
   unrecognized surface string is exempt too; closing the surface vocabulary
   into its own enum belongs to the production build-out. Scope expansion
   happens by superseding the promotion with a new approval, not by editing
   project targets past the check.

### Second Review Round (User-Approved 2026-07-03)

A second external review surfaced four findings; one approved batch closed
them the same day.

Fixed:

1. Creator scoping is now enforced: `validate research` and `validate queue`
   load the owning `creator-workspace.json` (failing when it is missing) and
   pin every record's `creator_profile_id` — and `creator_slug` where the
   schema carries it — to the workspace's creator. Before the fix a workspace
   validated with schedule, run, evidence, queue, and promotion records all
   claiming a different creator. Records whose schemas carry no creator field
   (project warnings) are exempt; system events check their optional fields
   when present.
2. The promotion gate rejects a promotion whose queue entry belongs to a
   different creator (checked entry-vs-promotion inside the gate so the
   `validate project` call path is protected too, independent of workspace
   scope loading).
3. `multi_platform_package` is removed from the project `content_unit_type`
   enum: it had no production plan schema, so a `created` project using it
   validated and then dead-ended at `planning`. Same rule as the youtube
   enum correction — the value joins the enum when the production build-out
   adds its plan schema. The concept remains valid CONTEXT.md vocabulary.
4. The README's opening flow and "What V1 Includes" list now teach the ADR
   0020 pipeline (platform-scoped research → Research Findings → scored Idea
   Queue → human-approved Idea Promotion → Projects) instead of the
   deprecated five-ideas/choose-one flow, and describe v1 as
   platform-scoped research with format-first universal short-form
   production rather than "platform-agnostic".

Declined with rationale:

- Enforcing that a promotion's snapshot (evidence refs, scores) stays
  consistent with the source queue entry's current contents. The promotion
  is deliberately a permanent locked approval snapshot because the records
  it names mutate afterward (entry scores drift, evidence accrues); equality
  checks against the live entry would reject exactly the drift the snapshot
  design anticipates. Entry ownership is checked (fix 2); snapshot content
  is not re-derived.

## Slice 4 Execution Decisions (User-Approved 2026-07-03)

Slice 4 is the Research Findings and Idea Queue workflow: the
`create-research-findings` and `manage-idea-queue` producer skills,
implementation-sequence steps 7-10 (recall index, board rebuild, prune), and
the three run-scoped consistency checks deferred from the slice 3 review.
Five decisions were approved individually. Do not reopen without user
approval.

1. Index layout: one shared SQLite at
   `workspace-library/index/influencer-os.sqlite`, per ADR 0010.
   `rebuild-index <creator-workspace>` deletes and reinserts only that
   creator's rows, so rebuilds stay scoped while cross-creator lookup stays
   possible. Indexed columns follow the ADR 0010 provenance minimum: record
   id, record type, creator profile id, creator slug, project id when
   applicable, source path, line number or record offset when applicable,
   content hash, indexed timestamp.
2. Validation is file-first. The three deferred run-scoped consistency
   checks (per-record `research_run_id` vs the containing run folder,
   `evidence_refs[].research_run_id` resolution instead of the global id
   pool, and `research-run.json` `outputs` reconciliation against the run's
   JSONL contents) land in `validate research`/`validate queue` reading
   canonical files directly. The recall index is a pure rebuildable
   projection and never a validation dependency, so validation has no
   stale-index failure mode.
3. CLI surface is projection/maintenance only: `rebuild-index`,
   `rebuild-board`, `validate board`, and `prune`. Skills author canonical
   records directly and the validators gate them. Mechanical write helpers
   (for example `append-evidence`) join later only if repeated slice usage
   shows agents fumbling a mechanical step — the same trigger rule as the
   deferred `/watch` import command.
4. `prune` is dry-run by default and deletes only with `--apply`. It removes
   unpromoted, unreferenced evidence past the 30-day retention window and
   never touches records referenced by a queue entry, promotion, or project
   (test-pinned). Stale queue entries are kept for auditability per the
   workflow doc. Metric-snapshot trajectory compaction is deferred until a
   real snapshot corpus exists; this slice adds no trajectory schema.
5. Scope stops at the queue. `manage-idea-queue` creates, updates, scores,
   and stales entries and keeps the manifest and board consistent; it never
   writes an `IdeaPromotion` or a `Project`. Promotion is slice 5
   (`promote-idea`) per the roadmap order, and the human-approval gate is
   untouched this slice.

Execution batches, guardrails first, TDD per batch:

- Batch A: the three run-scoped consistency checks in `validate research`
  and `validate queue`, each gap reproduced by a failing test first.
- Batch B: the recall index — SQLite layer per ADR 0010 plus
  `rebuild-index`; idempotent-rebuild and id-resolution tests.
- Batch C: the board — `rebuild-board` (deterministic card ids, manual order
  survives rebuild) and `validate board` (the board must agree with
  canonical records).
- Batch D: `prune` with the retention rules and preservation tests.
- Batch E: the two producer skills encoding the workflow doc's run-mode,
  material-update, evidence-quality, and intelligence-approval rules;
  registry, context-matrix, architecture-map, and conductor status flips;
  runtime propagation to fixture workspaces; docs and the progress and
  verification records.

Success condition: all batches land with the pre-slice test suite green plus
new negative tests per batch; the three consistency checks fail crafted bad
fixtures and pass the live fixture workspaces; `rebuild-index` and
`rebuild-board` are idempotent and deterministic; `prune --apply` provably
never removes promotion-referenced evidence; both producer skills flip to
built everywhere the drift checks look.

Batch A landing note (2026-07-03): outputs reconciliation is exact set
equality in both directions — a run manifest may neither omit ids present in
its JSONL files nor declare ids absent from them. This interacts with batch
D: `prune` deletes evidence lines, so batch D must decide how a pruned run
stays valid (rewrite the run manifest's outputs lists, record pruned ids, or
relax the declared-but-pruned direction). Open until batch D; surface it as
a decision before coding prune.

Batch D decision (user-approved 2026-07-03): record pruned ids. The run
manifest gains optional `pruned_evidence_ids` / `pruned_metric_snapshot_ids`
fields that `prune --apply` appends to; `outputs` is never rewritten, so the
manifest keeps its original account of what the run produced. Reconciliation
becomes exact against outputs minus pruned: pruned ids must be declared in
outputs, must be absent from the JSONL files, and JSONL contents must equal
the remainder. Rewriting outputs (loses the audit record) and relaxing the
declared-but-absent direction (lets runs misdeclare outputs forever) were
both declined.
