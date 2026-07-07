---
name: create-output-package
description: Use after a Project has an AppliedSocialTemplate and format-specific production plan to register an OutputPackage, copy upload-ready files into the project, preserve provenance, and mark the Project packaged without publishing or calling providers.
---

# Create Output Package

You own the post-planning Output Package step. The output is
`projects/<project-slug>/output-package/output-package.json` plus the
upload-ready files named by that record.

## Inputs

Read (context matrix — Output packaging row):

- Project manifest, evidence brief, Applied Social Template, production
  plan, and Base Video Generation Plan when the Project is short-form video.
- Locked Idea Promotion and the project source refs needed to preserve
  provenance.
- Creator Profile, Reference Library, and any approved/imported final assets
  or text files that will become upload-ready material.

Write only under the Project's `output-package/` folder and the Project
manifest status. Do not publish, schedule, upload, or call providers.

## Package Contract

- `project_id`, `creator_profile_id`, and `source_refs.idea_promotion_id`
  must match the Project.
- `universal_core.format_id` must match the Project's single target format.
- `source_refs.applied_social_template_id` must equal
  `plan/applied-template.json`.
- `source_refs.production_plan_ids` must include every plan record required
  by the Project: the format-specific production plan, plus the Base Video
  Generation Plan for short-form video.
- Carry `video_understanding_pack_ids` and `reference_asset_ids` only when
  they resolve in the creator workspace.
- `upload_ready[].path` values must live under
  `output-package/upload-ready/`; the registration command copies those
  files from a mirrored asset root.
- Text packages (`format_article`, `format_thread`) may use `null` for
  `thumbnail_or_first_frame_asset_id`; visual packages must point to an
  upload-ready asset.

## Creative Performance Map

Every package must include exactly useful entries for all five stages:

- `packaging`
- `hook`
- `body_retention`
- `payoff`
- `cta`

Each entry links a creative decision or file path to the intended effect and
primary metrics. Do not invent analytics results; this map is a future
measurement plan, not a performance report.

## Registration Command

Stage the Output Package JSON and mirrored upload-ready files, then register:

```bash
python3 -m influencer_os register-output-package <output-package.json> --project <creator-workspace>/projects/<project-slug> --asset-root <asset-root>
```

`<asset-root>` must contain the files at the same relative paths named by
`upload_ready[].path`, for example:

```text
<asset-root>/output-package/upload-ready/final-video.mp4
<asset-root>/output-package/upload-ready/caption.md
```

If the files are already staged inside the Project at those exact paths, omit
`--asset-root`.

The command refuses to overwrite an existing package, copies upload-ready
files, writes `output-package/output-package.json`, sets the Project status to
`packaged`, and runs `validate project`. If validation fails, it restores the
previous Project status and removes the package files it wrote. At rest,
`validate project` must keep passing for a packaged Project; it checks the
Output Package format against the Project content unit and requires every
`upload_ready[].path` to exist locally.

## Validation

After registration:

```bash
python3 -m influencer_os validate record output-package <creator-workspace>/projects/<project-slug>/output-package/output-package.json
python3 -m influencer_os validate project <creator-workspace>/projects/<project-slug>
```

## Boundaries

- Registration is not provider approval. If the package depends on generated
  media that does not exist yet, stop before registration.
- Do not publish, upload, schedule, or create Published Post Records.
- Do not move a Project past `packaged`; publication and analytics belong to
  Phase 2 workflows.

## Predictions (ADR 0025)

Each Creative Performance Map stage may quantify its intended effect with an
optional `prediction` (`metric`, `comparator`, `threshold`) — the theory the
performance summary will score confirmed or refuted. Predict when a baseline
exists (prior analytics, a stable finding); early guesses are allowed and
refuted guesses are learning, but never predict a metric the platform cannot
report. A predicted stage MUST be scored in the performance summary, so only
predict what you are prepared to measure.

## Friction Logging (ADR 0025)

When the operator rejects a draft, prompt, or asset this skill produced — or
an attempt fails in a way a future run should avoid — log it at the moment of
friction, before moving on:

```bash
python3 -m influencer_os log-incident <creator-workspace> --type rejection \
  --recurrence-key <criterion-id> --criterion <criterion-id> \
  --source-id create-output-package --message "<one line: what was rejected and why>"
```

- Cite an existing Production Rubric criterion, or mint one first with
  `mint-criterion` (cite-or-mint). If the reason cannot be articulated yet,
  log with `--unclassified` and a recurrence key naming the cluster.
- Record iteration churn with `--iteration-count` when several attempts
  preceded acceptance.
- Verdicts are durable; never store the rejected material itself.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md create-output-package "<lesson>"`.
