# ADR 0028: Onboarding Stage Gates And Strategy Calendar

## Status

Accepted

## Context

Creator setup currently uses broad workspace statuses such as `content_ready`
and `generation_ready`. The Mara Vale setup exposed a domain ambiguity:
approving a profile is not the same thing as finishing the creator foundation
for an image/video influencer. If recommended channels include Instagram,
YouTube, TikTok, or other visual/spoken surfaces, the setup must also produce
stable identity references, visual continuity references, and a voice readiness
decision before downstream strategy and production can be reliable.

The onboarding experience should feel like a staged creator setup flow:

1. profile page;
2. creator foundation page;
3. strategy page;
4. production/calendar page.

Each page should correspond to an explicit milestone, not an implicit
interpretation of `content_ready`.

## Current Accepted Decisions

### Decision 1: Replace Broad Workspace Status Milestones

The workspace status enum should change to clearer onboarding milestones:

- `draft`
- `profile_ready`
- `foundation_ready`
- `strategy_ready`
- `production_ready`
- `active`
- `archived`

`profile_ready` means the creator profile is accepted and includes the social
channels/surfaces the creator intends to use. Those channels determine the
reference requirements for `foundation_ready`.

`foundation_ready` means the medium/channel-required references are complete:
for visual/video channels, stable identity images and visual references; for
audio/video channels, a staged ElevenLabs Voice Design prompt package. Actual
spoken generation still requires an approved/imported voice sample or voice id
brought back through the provider-boundary path.

`strategy_ready` means the creator has an accepted strategy with monthly content
mix, conversion path, related-post relationships, and monetization mechanism.
It does not require fixed publication dates.

`production_ready` means the strategy has been turned into calendar slots and
the operational assets needed to create posts are available. Lead magnets that
posts convert to must exist before posts that promote them are produced.

### Decision 2: Channels Belong In Profile Readiness

The accepted profile must include the social channels/surfaces the creator will
use. Those surfaces are not just strategy preferences; they define what
references are required to finish the creator foundation.

Example: recommending Instagram Reels and YouTube Shorts makes visual identity,
video style, and ElevenLabs Voice Design prompt references foundation
requirements, not optional polish.

### Decision 3: Strategy Is Monthly Mix And Conversion Model

The strategy stage should define:

- platforms and format families;
- monthly quantity targets per platform/format;
- conversion path and lead magnet;
- how posts relate to each other, such as a Substack article followed by Reels,
  carousels, or LinkedIn posts that route back to it;
- game-theory cadence principles so the system avoids a rigid visible schedule.

The strategy stage should not force fixed dates. Fixed dates belong to
production/calendar planning.

### Decision 4: Calendarization Moves To Production Readiness

Production readiness turns the accepted strategy into actual calendar slots.
This stage should also gather or confirm channel handles/accounts, with an
option to skip when the user has not created the actual channels yet.

Lead magnets and other conversion assets must be created before posts that
drive traffic to them.

### Decision 5: Channel Account State Lives In A Separate Registry

The Creator Profile should declare intended channels/surfaces because those
choices are part of `profile_ready` and drive foundation requirements. Concrete
account readiness should live in a separate channel registry, tentatively
`channels.json` or `account-registry.json`.

The registry should track operational account state without polluting the core
creator identity:

- platform;
- intended handle;
- public URL;
- account status: `not_created`, `created`, `connected`, or `skipped`;
- production approval;
- notes;
- login/auth handled outside the repo.

The registry must never store secrets. Authentication remains in `.env` or
tool-managed auth.

### Decision 6: Foundation Readiness Is Mode-Aware, But Generation Permissions Are Strict

`foundation_ready` may be reached in one of two modes:

- `media_ready`: required reference files exist and are approved.
- `prompt_ready`: provider-neutral prompts/specs exist and the user explicitly
  accepts that some media references have not been generated or imported yet.

However, `prompt_ready` does not authorize creator-image/video generation or
spoken voice production. It only allows planning, strategy, text work, and
non-media setup to proceed.

Strict downstream permissions:

- Creating images or video that show the creator requires approved visual
  identity references for the creator.
- Creating consistent creator video requires approved visual identity
  references plus required video/photo style and any recurring visual
  references used by the format.
- Creating spoken voiceover, talking-head audio, or synthetic spoken content
  requires an approved/imported voice sample or voice id brought back through
  the provider-boundary path. A no-voiceover policy can block spoken generation,
  but does not replace the foundation ElevenLabs Voice Design prompt requirement
  for audio/video creators.
- If those requirements are missing, the system may create text-only scripts,
  shot plans, prompts, or strategy artifacts, but must not produce the missing
  media.

### Decision 7: Readiness Gates Use A Separate Canonical Record

Readiness gate state should live in a separate canonical record, tentatively
`readiness-gates.json`, referenced from `creator-workspace.json`.

This record is operational state, not identity. It should be the source of truth
for onboarding UI pages and validator gating:

- profile readiness;
- foundation readiness and mode;
- strategy readiness;
- production readiness;
- blockers;
- waivers;
- permissions such as visual generation allowed and spoken generation allowed.

`creator-profile.json` should not carry this mutable operational gate state. It
may expose only the accepted channels/surfaces that determine downstream
requirements.

### Decision 8: Gate State Vocabulary And Media Permissions

Each onboarding gate in `readiness-gates.json` should use the same status
vocabulary:

- `not_started`
- `in_progress`
- `blocked`
- `ready`
- `waived`

Each gate may record:

- `approved_on`;
- `approved_by`;
- `blockers`;
- `waivers`.

The foundation gate additionally records mode:

- `media_ready`
- `prompt_ready`
- `null`

Media permissions are explicit booleans, separate from gate readiness:

- `creator_image_generation_allowed`;
- `creator_video_generation_allowed`;
- `spoken_voice_generation_allowed`.

This separation allows a creator to proceed with strategy in `prompt_ready`
mode while still blocking generated creator images, creator video, or spoken
voice production until the required references exist.

### Decision 9: Lead Magnets Are Conversion Assets

Lead magnets and other conversion mechanisms should use a new record family
under `conversion-assets/`, rather than being embedded only in strategy docs or
treated as ordinary social posts.

Conversion assets include:

- lead magnets;
- opt-in pages;
- email sequences;
- paid consult-prep kits;
- offer pages;
- partner or referral landing assets.

Suggested lifecycle:

- `planned`;
- `drafted`;
- `approved`;
- `published_or_ready`;
- `retired`.

Strategy records and production calendar slots should reference conversion
assets by id. Posts that route to a lead magnet must not be produced until the
referenced conversion asset exists and is at least `approved` for that use.

### Decision 10: Split Strategy From Calendar

Stage 3 strategy and Stage 4 calendarization should be separate records:

- `content-strategy.json`: platform roles, monthly content mix, post families,
  related-post chains, conversion paths, conversion assets, and game-theory
  cadence principles.
- `content-schedule.json`: production/calendar slots, actual target dates or
  flexible windows, slot statuses, and the projects/posts that fill them.

The existing `content-schedule.json` concept remains the operational calendar
record. Strategy should not be forced into fixed dates.

### Decision 11: Channel Handles Are Optional For Production Creation, Blocking For Publishing

`production_ready` may allow creation of posts, projects, packages, and calendar
slots even when real channel handles/accounts are missing, if the user explicitly
skips account setup for now.

However, missing handles/accounts block publish/export readiness for the
affected platforms. The channel registry should distinguish:

- production can draft for this platform;
- publishing/export is blocked until account status is `created` or
  `connected`;
- the user intentionally skipped account setup for now.

This keeps creator production moving without pretending real-channel readiness
exists.

### Decision 12: No Bulk Migration Of Old Test Creator Workspaces

Existing creator workspaces are treated as test content unless explicitly
reopened. Do not build a bulk migration obligation for old creator workspaces as
part of this change.

Forward behavior should use the new statuses and readiness records. If an old
creator workspace is deliberately opened in the future, migrate that workspace
one by one using validation-based migration:

- never auto-promote above what files prove;
- if ambiguous, set the conservative stage and list blockers in
  `readiness-gates.json`;
- delete old test content instead of preserving it when no human wants it.

### Decision 13: Old Test Workspace Deletion Is Separate Cleanup

Do not delete old creator workspaces as part of the stage-gate implementation.
Deletion is a separate explicit cleanup pass or issue. The implementation should
remain focused on forward behavior and non-destructive schema/validator changes.

### Decision 14: New Records Use Minimal V1 Schemas With Stable IDs

The new onboarding records should be minimal in v1, but use stable IDs and
extension points so they can support a UI later without repeated migrations.

V1 records:

- `readiness-gates.json`: gate statuses, blockers, waivers, foundation mode,
  and media permission booleans.
- `channels.json`: intended channels, handles/URLs, account status,
  production-drafting permission, publishing/export blocking state, and skip
  notes.
- `content-strategy.json`: monthly content mix, post families, related-post
  chains, conversion paths, conversion asset refs, and cadence principles.
- `conversion-assets/*.json`: conversion asset type, status, source files,
  approved use, linked platform/funnel use, and lifecycle notes.

Avoid rich UI-only nesting until real onboarding use proves it is needed.

### Decision 15: Strategy Uses Hybrid Post Families With Platform Variants

`content-strategy.json` should model post families as conceptual families with
platform-format variants.

Example:

- family: `claim_teardown`
- variants:
  - `instagram_reel`
  - `youtube_short`
  - `linkedin_text`
  - `substack_section`

This allows strategy to reason about related content while still giving monthly
mix and calendarization enough platform-specific detail. It also supports
one-to-many relationships, such as one Substack article spawning Reels,
carousels, and LinkedIn posts.

### Decision 16: Strategy Models Related Posts As Content Campaigns

`content-strategy.json` should model related-post chains as strategy-level
`content_campaigns`, not prose and not concrete posts/projects.

Minimal v1 campaign fields:

- `campaign_id`;
- `name`;
- `anchor_variant`;
- `derivative_variants`;
- `conversion_asset_ids`;
- `monthly_target`;
- `relationship_rule`;
- `cadence_note`.

Example: one Substack anchor article can define derivative Instagram Reels,
Instagram carousels, and LinkedIn posts that route to the same conversion
asset. Calendarization later turns the campaign pattern into slots.

### Decision 17: Validation Blocks Stage Claims, Warnings Flag Incomplete Operations

Validation should block status advancement when a workspace claims a stage that
its files do not support. Operational incompleteness that does not invalidate
the claimed stage should warn.

Blocking validation failures:

- `profile_ready` without selected channels/surfaces.
- `foundation_ready` without `readiness-gates.json`.
- `foundation_ready` with media permissions that contradict available
  references.
- creator image/video generation allowed without approved visual identity
  references.
- audio/video `foundation_ready` without a staged ElevenLabs Voice Design prompt
  asset.
- spoken voice generation allowed without an approved/imported voice reference.
- `strategy_ready` without `content-strategy.json`.
- strategy references missing conversion assets.
- `production_ready` without `content-schedule.json`.
- calendar slots or planned posts promote conversion assets that are not
  approved or ready for that use.

Warning validation findings:

- real channel handles are missing when the channel is explicitly marked
  skipped.
- a foundation is `prompt_ready` and therefore cannot generate creator media
  yet.
- no production calendar slots exist before `production_ready`.
- old workspaces still use deprecated statuses.

## Follow-Up Questions

1. Which operational warnings should become blocking checks once real creator
   publishing/export workflows exist?

## Consequences To Validate

- No bulk migration is required for old fixture workspaces. If a real old
  workspace is deliberately reopened, migrate it one by one based on what its
  files validate.
- Validators should enforce different blockers at each new stage.
- Skills should stop treating post production as the natural next step after
  profile approval.
- The UI can map one page to each onboarding milestone.
