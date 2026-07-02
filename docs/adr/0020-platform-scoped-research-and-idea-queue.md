# ADR 0020: Platform-Scoped Research And Idea Queue

## Status

Accepted

## Context

InfluencerOS initially framed v1 around universal visual social posts. That
remains useful for early production planning, but the research workflow needs a
wider input surface.

Creators may operate across X, Instagram, TikTok, Substack, Medium, Reddit,
Facebook, LinkedIn, and later platforms. Useful content opportunities can appear
on one platform and be adapted into another format. For example, a trending
Instagram Reel can spark a Substack article, or a Reddit discussion can become a
short-form video topic.

The previous `ContentIdeaSet` concept also made the research workflow too narrow
by treating five ideas as the main output. The creator needs the research itself:
what is working, what is weakening, which creators or posts are high signal, and
where platform/topic/format overlaps are creating opportunities.

## Decision

InfluencerOS v1 research will be platform-scoped rather than visual-post-only.

The initial platform set is:

- X,
- Instagram,
- TikTok,
- Substack,
- Medium,
- Reddit,
- Facebook,
- LinkedIn.

Every researched source should record its platform and platform content type,
such as `x_post`, `instagram_reel`, `tiktok_video`, `substack_article`,
`reddit_thread`, or `linkedin_post`.

Research findings and idea generation may adapt a trend from its source platform
into another creator-fit format. The source format should inform the evidence,
but it should not constrain the output format.

The Research and Ideas workflow will use two primary outputs:

- `ResearchFindings`: a concise rolling creator-scoped summary backed by dated
  evidence records,
- `IdeaQueue`: a creator-scoped Kanban-style backlog of scored opportunities.

`ContentIdeaSet` is removed from the intended pipeline. Existing
`content-idea-set` schemas and examples may remain temporarily as deprecated
compatibility artifacts until `ResearchFindings` and `IdeaQueue` are
implemented, but new workflow design should not depend on them.

A top-five idea list can exist as a presentation view over the queue, but not as
the canonical product boundary.

The old `SelectedContentIdea` concept should be replaced by `IdeaPromotion`.
Promotion starts from an `IdeaQueueEntry`, not from a `ContentIdeaSet`. An
`IdeaPromotion` is a permanent approval record. A human-approved promotion
package may immediately create one or more Projects.

Project provenance should point to the promoted idea queue entry, relevant
research finding IDs, and evidence IDs rather than only a selected content idea
ID.

Idea queue entries may recommend one primary platform, multiple platforms, or
platform-specific variants depending on the creator's strategy. The same idea
may have different intended payoffs on different platforms, as long as the
variants remain coherent with the creator's persona, audience, and boundaries.

Creator content schedules should define loose content goals and strategic needs
rather than rigid platform quotas by default. The system may recommend how many
posts to make and which platforms to use based on the creator strategy, current
research, and schedule state.

Research storage should favor context control:

- split platform or topic findings into subsections or files when needed,
- preserve immutable evidence records for audit,
- keep the rolling creator-readable findings summary concise,
- keep creator-specific research intelligence local to the creator workspace in
  v1.

Creator-specific research intelligence is part of this module. It stores
sources, hashtags, search terms, reference creators, and watchlists that improve
future research runs. Research runs may suggest updates, but adding or removing
user-approved core reference creators requires user approval.

Scheduled research jobs may update findings, evidence snapshots, queue scores,
staleness, warnings, badges, and notifications. They must not promote ideas into
production in v1. Notifications should be lightweight system events plus Kanban
flags or badges, with Telegram as an initial external delivery surface.

The research schema slice defines the `AutomationRun` and `SystemEvent` record
shapes and creator-scoped projections only. Running scheduled jobs, hooks,
cron, and Telegram delivery are a separate, explicitly approved build-out
(research-only scheduled jobs may arrive before Automation OS per the PRD, but
they land after the manual research workflow works).

Human approval is required before queue ideas are promoted into the creation
funnel. Promotion may immediately create one or more Projects.

Promotion may only create Projects for content unit types and formats that
production currently supports. Research and the Idea Queue cover the full
platform set from day one, but production matures in build-order steps: visual
formats first, text formats (article, thread) in the production build-out step.
An idea approved for a not-yet-supported format stays in the queue with its
approval intent recorded, and the agent must surface that production support is
pending instead of silently creating an invalid Project.

The next schema implementation slice should define the research module as a
whole instead of landing isolated records one at a time. The slice should include
schemas for creator content schedule, research run, research evidence, metric
snapshot, research findings, research intelligence, idea queue, idea promotion,
project warning, content board, automation run, and system event.

This slice is Phase 1 (Planning OS) work. It follows the agreed build order:
creator setup first, then the research module, then the production build-out
that adds text formats. It is not a Phase 0C parity-hardening exit criterion.
`docs/workflows/research-and-ideas-implementation-plan.md` is the canonical
schema and storage list; other documents should point to it rather than
maintain their own copies.

## Consequences

- Research can discover opportunities across the creator's full platform
  surface, not only visual social video.
- Production workflows can still mature incrementally, but research will not be
  artificially blocked by current production format support.
- Schemas and docs that center `ContentIdeaSet` as the required output must be
  revised or deprecated.
- Evidence records must include platform and platform content type.
- The idea queue becomes the durable boundary between research and production.
- `Project.source_refs` and downstream provenance validation need to shift from
  selected-content-idea-only references to queue, finding, and evidence
  references.
- Scheduled research automation is in scope only as research and notification
  work; automated idea promotion remains out of scope for v1.
- Platform-specific payoff and A/B testing become possible while still requiring
  persona and audience coherence.
- Broader platform support increases schema and workflow complexity, so context
  control through split files and concise summaries is required.
