---
name: register-published-post
description: Use after a human has manually published a packaged Project's Output Package on a platform to record the publication as a PublishedPostRecord and move the Project to published. Records what already happened; never publishes, uploads, or schedules.
---

# Register Published Post

You own the publication-registration step of the Learning OS. The output is
`projects/<project-slug>/published/published-post-records/<ppr-id>.json`.

Registration is a recording act: the operator already published the post
manually. This skill files the evidence and never touches a platform.

## Inputs

Read (context matrix — Publication registration row):

- Project manifest and the registered Output Package
  (`output-package/output-package.json`), including its `upload_ready`
  asset ids and paths.
- The operator's account of the publication: platform, account, publish
  time, public URL, platform post id, and which upload-ready assets were
  used.

Write only under the Project's `published/published-post-records/` folder
and the Project manifest status.

## Record Contract

- `project_id`, `creator_profile_id`, and `output_package_id` must match the
  Project and its registered Output Package.
- `assets_used.thumbnail_or_first_frame_asset_id` and every
  `assets_used.primary_media_asset_ids` entry must be `upload_asset_` ids the
  package's `upload_ready` declares. Text packages (`format_article`,
  `format_thread`) may record `thumbnail_or_first_frame_asset_id: null`;
  visual packages must name a real asset (mirrors the Output Package rule).
- `assets_used.caption_or_description_path` must be a declared
  `upload_ready[].path`.
- `publication_status` is honest state: `published`, `updated`, or `deleted`
  attest a post that went live; `scheduled` and `failed` document attempts
  and never move the Project past `packaged`.
- Missing platform facts (`public_url`, `platform_post_id`) are `null`,
  never guessed.
- One record per platform publication; a multi-platform release registers
  one record per platform post. Two records may not claim the same
  platform post identity — a duplicate `(platform, platform_post_id)` pair
  or a duplicate `public_url` fails validation regardless of record id.

## Registration Command

Stage the PublishedPostRecord JSON, then register:

```bash
python3 -m influencer_os register-published-post <published-post-record.json> --project <creator-workspace>/projects/<project-slug>
```

The command requires the Project to be `packaged` (or already `published`
for additional platform records), validates the record against the
registered package, writes it under `published/published-post-records/`,
and moves the Project `packaged -> published` on the first record whose
`publication_status` attests a live post. If validation fails, it restores
the previous Project status and removes the record it wrote. At rest,
`validate project` re-checks every registration invariant.

## Validation

After registration:

```bash
python3 -m influencer_os validate record published-post-record <creator-workspace>/projects/<project-slug>/published/published-post-records/<ppr-id>.json
python3 -m influencer_os validate project <creator-workspace>/projects/<project-slug>
```

## Boundaries

- Never publish, upload, schedule, or call platform APIs; this skill records
  a publication that already happened.
- Do not register a record for a post that is not actually live unless its
  `publication_status` says so (`scheduled`/`failed`).
- Do not create Analytics Snapshots here; ingestion is the next workflow.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md register-published-post "<lesson>"`.
