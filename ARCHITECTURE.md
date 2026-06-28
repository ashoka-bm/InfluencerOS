# Architecture

InfluencerOS v1 is a dry-run-first planning system for universal short-form creator videos.

## First Vertical Slice

```text
Creator Profile
  -> Social Research Pack
  -> Social Post Format Shortlist
  -> Content Idea Set, exactly five ideas
  -> Selected Content Idea
  -> Applied Social Template
  -> Format-Specific Production Plan
  -> Base Generation Plan, when needed
  -> optional Generation Approval Gate
  -> Output Record, when an artifact exists
```

No provider-backed generation call is required for the first slice.

## Product Boundary

InfluencerOS v1 does:

- use existing creator profiles,
- research current short-form social video patterns,
- use a minimal visual social post format shortlist,
- generate five creator-fit video ideas,
- wait for explicit idea selection,
- apply a format-compatible social template to the chosen idea,
- create a format-specific production plan,
- create a provider-neutral base video generation plan.

InfluencerOS v1 does not:

- create platform-specific adapters,
- plan post-production motion graphics,
- publish or schedule posts,
- scrape private social data,
- run analytics feedback loops,
- generate media without explicit approval.

## V1 Format Shortlist

InfluencerOS v1 starts with four visual-first social post formats:

- `short_form_video`: a vertical hook-to-payoff video.
- `carousel`: a swipeable image sequence, including Instagram carousels and TikTok Photo Mode style posts.
- `single_image_post`: one strong still, graphic, or generated image.
- `story_sequence`: a short ephemeral-feeling sequence of vertical visuals.

Live streams, community posts, polls, and platform-specific variants are deferred until the first visual production loop is proven.

## Default Video Envelope

All v1 video ideas and plans target a universal short-form envelope:

- vertical short-form video,
- one complete idea,
- hook-first,
- visually legible without platform context,
- suitable for Instagram Reels, TikTok, and YouTube Shorts,
- no reliance on platform-specific UI, stickers, or effects,
- safe room for captions or overlays later if needed.

## Data Flow

The pipeline is typed. Each major step produces a schema-backed record before the next step begins.

```text
Step input records
  -> agent transformation
  -> step output record
  -> schema validation
  -> next step input records
```

Research and generation are separated. Research may browse current public sources and must cite them. Provider-backed generation requires explicit approval.

## Format-Specific Production Plans

The first implemented production records are:

- `MicroJourneyVideoPlan` for `format_short_form_video`,
- `CarouselPlan` for `format_carousel`,
- `SingleImagePostPlan` for `format_single_image_post`,
- `StorySequencePlan` for `format_story_sequence`.
