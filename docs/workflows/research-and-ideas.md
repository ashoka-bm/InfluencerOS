# Research And Ideas Workflow

Status: Draft from grilling session
Last updated: 2026-07-02

Implementation draft: `docs/workflows/research-and-ideas-implementation-plan.md`

## Purpose

The Research and Ideas workflow is an exploratory Planning OS module. Its job is
to turn creator-scoped identity, schedule demand, prior learning, current social
evidence, and platform context into useful research findings and a queue of
potential content ideas.

This module does not produce final media and does not publish or schedule posts.
It ends when researched ideas are presented, scored, and stored in an idea queue.
Ideas may be promoted into the creation funnel immediately or later.

This workflow should support platform-scoped research in v1. The initial platform
set is:

- X,
- Instagram,
- TikTok,
- Substack,
- Medium,
- Reddit,
- Facebook,
- LinkedIn.

Production workflows may still mature platform by platform, but research and
idea discovery should not be limited to visual social posts.

See `docs/adr/0020-platform-scoped-research-and-idea-queue.md`.

## Current Boundary Decision

The module boundary is the idea queue, not the production project.

```text
Creator Profile
  + Creator Content Schedule
  + prior creator memory and performance summaries
  + current public social research
  + optional real video understanding
  -> Research Findings
  -> Idea Queue entries
  -> later promotion into Projects
```

The research run may identify multiple strong opportunities. It should not be
limited to a single idea or a single near-term execution goal. The workflow
should look for creator-fit opportunities that can capitalize on current viral
or high-performing content patterns while staying aligned with the creator's
audience, persona, boundaries, and schedule.

## Module Interface

The Research and Ideas module is one deep module with a small public surface.

Inputs, read-only:

- Creator Profile,
- Creator Content Schedule,
- distilled creator memory (learnings, performance summaries, selected
  postmortems),
- public web and social sources.

Public interface records, what other modules may read:

- `research/findings.md`: the rolling Research Findings,
- `research/idea-queue/`: the Idea Queue manifest and entries,
- `research/idea-promotions/`: Idea Promotions, the only handoff into
  production.

Internal records, private to this module:

- `research/runs/`: research runs, evidence, metric snapshots, video
  understanding packs, run summaries,
- `research/intelligence/`: sources, hashtags, search terms, reference
  creators, watchlists,
- `research/stable-findings/`.

Other modules must not read internal records directly. They resolve evidence
IDs through the local recall index when deeper context is needed. This lets the
research module reorganize, compact, and prune its internal storage without
breaking consumers.

Write boundary: research writes only under `research/`. The human-approved
promotion step is the constructor for `projects/<project-id>/`: it writes the
promotion record, `project.json`, and `evidence-brief.md`, then production owns
the project folder. The Content Board, warnings stream, and recall index are
derived projections rebuildable from canonical records.

## Inputs

Required creator inputs:

- `Creator Profile`: stable creator identity, audience, niche, positioning,
  persona, voice, visual identity, pillars, boundaries, and goals.
- `Creator Content Schedule`: a separate creator-scoped record that captures the
  creator's unique cadence, schedule expectations, content mix, open slots,
  pillar targets, and whether the system is on track without drift.

Recommended creator memory inputs:

- distilled creator learnings,
- performance summaries,
- selected postmortems,
- prior Social Research Packs,
- prior Video Understanding Packs,
- prior idea queue outcomes.

Current research inputs:

- public social/web sources,
- scraped or browsed social media evidence,
- public or user-provided real videos when video understanding is useful,
- local creator reference files when needed for fit checks.

## Video Understanding Tool Decision

When real video analysis is useful, InfluencerOS may use the installed
`bradautomates/claude-video` `/watch` workflow as an external acquisition tool.
Its job is to inspect the video source, sample frames, obtain native captions
when available, and provide timestamped evidence for the agent to summarize.

The canonical workflow output is still a `VideoUnderstandingPack`; `/watch`
working files are disposable acquisition artifacts. Store only the distilled
observations needed for research, queue scoring, and production provenance.

Rules:

- Use public URLs or user-provided local files only.
- Prefer native captions and frames; API transcription fallback requires exact
  user approval or prior explicit configuration for this research run.
- Use an ignored output directory such as
  `.tmp/watch/<creator-slug>/<research-run-id>/<source-id>/` when supported.
- Use focused windows for long videos instead of broad sparse scans.
- Do not import the upstream hooks, commands, or hidden automation into
  InfluencerOS v1.

## Platform Scope Decision

Every evidence record should include `platform` and `platform_content_type`.

Example platform content types:

- `x_post`,
- `instagram_reel`,
- `instagram_carousel`,
- `tiktok_video`,
- `substack_article`,
- `medium_article`,
- `reddit_thread`,
- `facebook_post`,
- `linkedin_post`.

A trend or strong source example can be adapted into another format or platform.
For example, a trending Instagram Reel about a news item may become a Substack
article if that better fits the creator strategy and audience. Source platform
and source format inform the evidence; they do not hard-block other output
formats.

Idea queue entries may recommend:

- one primary platform,
- multiple platforms,
- platform-specific variants,
- or a platform-agnostic idea that should be shaped later.

The same idea may have different intended payoffs by platform. For example, a
short video variant may target reach while a Substack variant targets depth,
trust, or audience education. Platform variants must remain coherent with the
creator's character, audience expectations, and content boundaries.

Research findings should use subsections or split files when platform-specific
detail would bloat the rolling summary. The system should lean toward more small
files over one large context-heavy document when that improves retrieval and
agent focus.

## Research Run Workflow

A research run should generally follow this sequence:

1. Load Creator Profile, Creator Content Schedule, rolling findings, research
   intelligence, recent idea queue entries, recent projects, and performance
   summaries.
2. Choose a research mode and scope.
3. Create `research/runs/<research-run-id>/search-plan.json` before browsing.
   The plan records the creator/schedule/intelligence basis, adapters
   considered, query intent, planned queries, planned sources, skipped sources,
   approval gates, and future connector notes.
4. Start from known high-signal creators or sources when available, then branch
   outward into related public sources to understand the current zeitgeist.
5. Browse browser-visible public posts and sources using only adapters marked
   active in `docs/research-adapter-registry.md`.
6. Capture compact evidence records and metric snapshots for sources that
   produce material evidence.
7. Write `source-yield.jsonl` records for checked sources and queries,
   including sources that produced only background context or no useful signal.
8. Analyze topic, format, hook, pacing, platform, and performance patterns.
9. Update existing queue ideas when new evidence changes their scores, urgency,
   staleness, or rationale.
10. Add new queue ideas when the evidence supports them.
11. Update rolling findings and research intelligence only when there is a
    material finding or source-yield learning.
12. Present findings first, then recommended ideas by goal.

Query formulation must stay grounded in creator context. Each planned query's
terms derive from the Creator Profile, schedule signal, rolling findings,
research intelligence, or prior queue entries. Each query records this in a
required `term_basis` — a closed set (`creator_profile`, `content_schedule`,
`rolling_findings`, `research_intelligence`, `prior_queue`, `hypothesis`) that
makes term provenance auditable — with `routing_basis` prose explaining the
choice. Do not seed queries with tool, brand, product, or trend names pulled
from the agent's own training knowledge that are absent from creator context:
that knowledge may be stale, and research is time-sensitive. A term that is a
hypothesis rather than creator-derived must carry the `hypothesis` term_basis so
its yield is judged honestly; the validator enforces the closed set but cannot
verify a claimed basis is truthful, so the honesty is on the author.

Research modes should be separable so they can run independently:

- scheduled needs research,
- wildcard opportunity discovery,
- reference creator watchlist review,
- topic overlap scan,
- urgent trend or news check,
- queue refresh and staleness review.

Runs may combine modes, but v1 should keep them independently runnable so the
system can perform focused work without loading unnecessary context.

Do not create noisy reports. If a run finds nothing important and does not update
findings, queue entries, research intelligence, or metric snapshots, it should
not modify the rolling findings summary. The system may still record operational
run metadata so it is clear the research ran.

The rolling findings document should include `last_updated` for the last
material update. Research run metadata should separately preserve `last_ran` so
the system can distinguish "not checked recently" from "checked recently but no
useful change found."

## Schedule Model Decision

The content schedule should not live directly in `creator-profile.json`.

The Creator Profile remains an operational summary for relatively stable creator
identity. Schedule and planning state should be a separate record so the system
can check whether the correct posts have been created, whether the creator is on
track, and whether the idea queue is drifting away from the intended content mix.

The schedule should include both standing strategy and calendar state.

Expected schedule metadata:

- cadence expectations,
- intentionally irregular publishing dates,
- content mix targets,
- content pillar targets,
- loose content goals and strategic needs,
- optional format or channel targets,
- active campaigns or launches,
- blackout dates or unavailable dates,
- open slots,
- time-sensitive insertions,
- recently published or promoted projects,
- drift checks for under-served or over-served content areas.

Format and channel targets should be extensible beyond visual social posts. For
example, a creator with a Substack account may have article targets. The schedule
should usually express loose content goals first, then let research and strategy
recommend platform and format choices.

The schedule may own exact dates, but those dates should not be mechanically
regular. The system should support sporadic, intentionally uneven publishing
patterns so the creator does not feel predictable. Time-sensitive opportunities
may be added even when they disrupt the existing schedule.

Idea queue entries should be able to reference a recommended schedule slot. They
may also be marked as wildcard opportunities when they sit outside the current
schedule but look worth considering.

Schedule fit should not automatically penalize a hot topic just because the
creator has covered the topic recently. Instead, the workflow should check
whether the new idea is meaningfully distinct from recent posts so the content
does not become repetitive.

V1 should avoid heavy variety rules beyond the creator's broad content mix and
general non-repetition checks. More specific rules should be added later from
observed performance, such as evidence that a certain repeated format or topic
causes performance to drop.

## Idea Queue Decision

Research output should be stored in an idea queue before it becomes production
work.

The queue is the first section of one unified content Kanban board. Queue entries
can be promoted into the creation funnel immediately or later. Promotion advances
the card into project work and creates one or more Projects according to the
production workflow.

The queue should behave like a Kanban flow. Ideas move through explicit statuses
until a human-approved promotion triggers the next workflow.

Candidate statuses:

- `new`: captured from research and not yet reviewed,
- `reviewed`: inspected and retained as a plausible opportunity,
- `shortlisted`: strong candidate for near-term execution,
- `promoted`: approved and advanced into project work,
- `rejected`: intentionally not worth pursuing,
- `expired`: stale because the supporting trend or evidence no longer performs,
- `needs_more_research`: promising but not yet supported by enough evidence.

The unified board should allow an idea card to move from queue states into
project states. After promotion, the idea should not remain as a separate active
queue card. Its promoted status should point to the resulting `IdeaPromotion` and
Project records.

Human approval is required before an idea is promoted into the creation funnel.
Automation may recommend promotion, update scores, flag stale ideas, or suggest
queue movement, but v1 should not silently create production work.

When a human approves promotion, the system may create a `Project` immediately.
Promotion approval should cover the whole package: the idea, intended content
goal, target format or formats, relevant schedule slot or content need, and the
research evidence being carried forward.

One queue idea may promote into multiple Projects when the idea can support more
than one content unit, such as a short-form video plus a carousel.

Promotion may only create Projects for content unit types and formats that
production currently supports. An idea approved for a not-yet-supported format
stays in the queue with its approval intent recorded, and the agent must
surface that production support is pending rather than silently creating an
invalid Project. Article and thread Projects are production-supported as of
Phase 1 slice 6.

Promoted Projects should preserve traceability to the research that sparked
them. The project should keep:

- references to the original research evidence IDs,
- a compact project-local evidence brief,
- copied reusable creative elements needed for production, such as hooks,
  first-frame patterns, structure notes, example links, and avoid notes.

The project does not need to copy every raw metric snapshot or full source
record. Those remain in the research records unless the project needs them for a
specific production or later learning purpose.

## Schema Migration Decision

`ContentIdeaSet` should be removed from the intended pipeline entirely.

The superseded `content-idea-set` and `selected-content-idea` schemas and
examples were removed after the replacement research module shipped. They are
not compatibility routes and must not re-enter the intended workflow.

`SelectedContentIdea` should be replaced by `IdeaPromotion`. Promotion starts
from an `IdeaQueueEntry`, and the human-approved promotion package may
immediately create one or more Projects.

`IdeaPromotion` is a permanent record. It preserves the approval event, approved
idea package, intended payoff, target platforms and formats, schedule context,
evidence references, and project IDs created from the promotion.

Expected `IdeaPromotion` fields:

- `idea_promotion_id`,
- `idea_queue_entry_id`,
- `creator_profile_id`,
- `approved_by`,
- `approved_on`,
- `approval_note`, optional,
- `intended_payoff`,
- `approved_platforms`,
- `approved_formats`,
- `schedule_slot_ids`, optional for wildcard ideas,
- `research_finding_ids`,
- structured `evidence_refs` covering research run, evidence, metric snapshot,
  and video understanding pack IDs,
- score snapshot at approval time,
- creative elements to carry forward,
- `project_ids_created`,
- `promotion_status`.

For v1, `approved_by` may be `user`. Later automation may allow agent approval
behind a separate policy.

Approval locks the promoted package. Later research updates should not mutate
the permanent `IdeaPromotion` record.

If the source queue idea, supporting research, or score trajectory changes before
the promoted Project is finished and published, the unfinished Project should
receive a warning. The warning should not automatically rewrite the project; it
should surface that the idea's research status, urgency, or expected performance
has changed.

The score snapshot at approval time is permanent. Later workflow records may
compare current scores against the approval snapshot so agents can show whether
the opportunity improved or weakened before publication.

Human promotion does not require a rationale. The system can store an optional
approval note, but it should not block promotion when the user simply approves.

## Project Warning Decision

Project warnings should be stored separately from the core Project record in a
Kanban-readable event stream, such as `project-warnings.jsonl`.

Warnings are informational in v1. They do not block publishing, require human
acknowledgement, or trigger automation. The agent should surface the warning and
present the option to re-plan, refresh research, change scope, or continue.

The warning record should still be structured for future Kanban views, blocking
rules, and automation triggers.

Recommended warning fields:

- warning ID,
- project ID,
- idea promotion ID,
- idea queue entry ID,
- warning type,
- severity,
- message,
- detected on,
- source evidence or score IDs,
- suggested actions,
- resolved or obsolete status, optional.

The idea queue entry ID is always required. Project ID and idea promotion ID
are required only when the warning targets promoted work; queue-level warnings,
such as a stronger variant replacing an unpromoted idea, attach to the queue
entry alone. This keeps the board free to show warning flags on parent idea
cards as well as child project cards.

Initial warning types:

- source trend went stale,
- urgency window expired,
- evidence strength dropped,
- creator fit concern discovered,
- schedule slot no longer fits,
- platform payoff changed,
- reference source deleted or unavailable,
- queue idea replaced by stronger variant.

Future rules may promote warnings into blocking gates or automation triggers,
such as notifying the user when viral potential rises above a configured
threshold. V1 should only record and display warnings.

## Unified Kanban Decision

The creator should eventually have one unified board rather than separate idea
and project boards. The idea queue is the first part of that board; promoted
ideas continue into project execution.

Recommended board progression:

- `new`,
- `reviewed`,
- `shortlisted`,
- `needs_more_research`,
- `promoted`,
- `created`,
- `planning`,
- `ready_for_generation`,
- `generated`,
- `packaged`,
- `published`,
- `analyzed`,
- `archived`,
- `rejected`,
- `expired`.

`ready_for_generation` is an approval gate in the sense that it marks readiness,
but it must not automatically call providers. Provider-backed generation still
requires explicit approval for the exact call or batch.

Warnings should appear as flags or badges on board cards rather than becoming
new workflow statuses. For v1, do not add `paused` or `needs_attention` project
states unless later evidence shows warnings are not enough.

The former Project status `idea_selected` was removed when `IdeaPromotion`
replaced `SelectedContentIdea` as the production-entry record.

The Kanban board should have a first-class `ContentBoard` / `ContentCard`
projection for UI use. The projection should be creator-specific and rebuildable
from canonical records. It is not the source of truth for research, approvals,
projects, or analytics.

Card model:

- idea queue entries appear as parent idea cards,
- each Project created from an IdeaPromotion appears as its own child project
  card,
- one parent idea card may have multiple child project cards,
- child cards keep their own stable IDs,
- card IDs are derived deterministically from the source record ID (for
  example `card_<idea_queue_entry_id>` and `card_<project_id>`), so canonical
  records never store card IDs and board rebuilds preserve manual order,
- the parent card keeps links to the queue entry and promotion,
- child cards keep links to their Project records,
- warning flags can appear on parent or child cards.

Board ordering should be manually editable later. Manual order should be stored
as board projection metadata so it can be preserved without mutating canonical
research or project records.

`Project.source_refs` should shift from `selected_content_idea_id` to provenance
that can include:

- `idea_queue_entry_id`,
- `research_finding_ids`,
- `research_evidence_ids`,
- relevant metric snapshot or trajectory IDs,
- reference asset IDs,
- source platform and platform content type.

The next implementation should create the research module schema slice all at
once. The canonical schema list, storage shape, and field drafts live in
`docs/workflows/research-and-ideas-implementation-plan.md`; this document
records the decisions and rationale, not a second copy of the slice list.

Use one file per idea queue entry so agents and Kanban views can load or update
specific ideas without pulling the entire queue into context. Use JSONL for
append-heavy evidence, snapshots, and warnings. Use Markdown for the rolling
Research Findings body because it is primarily a creator-readable synthesis.

## Research Findings Decision

Research findings are a primary product of the module, not just hidden support
for idea generation.

The creator should be able to read the findings to understand what is doing
well, what is weakening, which styles and video types are showing up, and where
there are useful overlaps between the topics the creator covers.

The durable research output should include:

- a short rolling creator-scoped Research Findings summary,
- immutable dated research-run evidence records,
- promoted stable research records when a finding becomes durable creator
  strategy,
- reusable research intelligence, such as good places to look, hashtags,
  competitor/reference creators, search terms, and trend watchlists.

The rolling summary should be updated every time new research is done, but it
must stay concise. It should have a character limit so the system is forced to
keep only high-signal findings. Dated research-run records preserve the evidence
trail that does not fit in the rolling summary.

Recommended rolling summary limit: 8,000 to 12,000 characters. This is long
enough to carry several topic clusters and short enough to avoid context bloat.
If the summary regularly exceeds the limit, older or less actionable findings
should be demoted to dated evidence records, stable research records, or
research intelligence files.

When a video or other content artifact is created from research, it must keep a
link to the research evidence that sparked it. If that content performs well,
the Learning OS should be able to credit the research source, pattern, search
term, competitor reference, or finding that led to the successful idea.

Candidate finding categories:

- top content,
- top-performing content,
- rising patterns,
- declining patterns,
- content styles,
- video types,
- hook patterns,
- first-frame patterns,
- pacing or structure patterns,
- topic overlaps,
- audience response signals,
- creator-fit opportunities,
- avoid notes.

Finding time horizons:

- stable: durable patterns that can guide creator strategy over time,
- active trend: current pattern worth using while it is still performing,
- fast-moving viral shape: urgent format or meme-like structure that needs quick
  execution,
- news or event reaction: highly time-sensitive opportunity,
- evergreen: slower opportunity that can remain useful without immediate
  production.

Old findings should not be silently overwritten. Immutable dated records remain
available for audit. The rolling summary should merge what matters now, mark
trend movement, and point to the latest supporting evidence. Stable findings may
be promoted into more permanent records when repeated research proves their
value.

The removed `ContentIdeaSet` concept is not a workflow output. Its canonical
replacements are:

- `ResearchFindings`: the synthesized, dated, evidence-backed view of what is
  happening in the creator's relevant social space,
- `IdeaQueue`: the durable backlog of scored content opportunities derived from
  those findings.

If a top-five presentation is still useful, it should be a view over the idea
queue, not the canonical record.

## Evidence Quality Decision

The workflow should prefer direct evidence from real posts and real performance.
External articles naming trends are weak evidence unless they point to actual
posts, creators, or measurable platform behavior.

High-signal evidence includes:

- real post URLs,
- creator/account names,
- posting date or observed age,
- visible likes, comments, shares, saves, views, reposts, or other available
  engagement,
- engagement velocity when posting date and current metrics are available,
- creator-relative outperformance, where a post significantly beats that
  creator's normal content,
- repeated high-performing patterns across multiple creators,
- topic overlap with the target creator's niche and content pillars,
- format or video-type details,
- hooks, first frames, pacing, and structure from real examples.

Weak evidence includes:

- generic trend articles without links to real posts,
- unsupported claims about what is viral,
- isolated examples with no visible performance context,
- patterns that perform only outside the creator's plausible topic/persona
  range.

The system should name creators and provide links to high-performing posts when
those examples are central to the finding. Competitor/reference tracking is in
scope when it is grounded in public evidence and used to learn from patterns,
not to copy exact creative expression.

### Signal Tier Rubric

`visible_metric_signal` (on each source-yield record) and `confidence` (on each
evidence record) are the two quality dials the workflow leaves to agent
judgment. They must be assigned the same way across runs, so anchor them to this
rubric rather than to raw numbers. The rubric is heuristic on purpose: the eight
platforms differ too much for fixed thresholds, and creator-relative
outperformance is a stronger signal than any absolute count.

Read `visible_metric_signal` as the engagement of the observed post in context:

- `strong` — clearly beats the source account's or reference creator's own
  baseline, or is unmistakably high for the platform and format, and the lift
  shows in active engagement (saves, shares, comments), not views alone.
- `moderate` — above baseline or solidly mid-pack; real interest, not a
  standout.
- `weak` — at or below baseline, or low for the platform and format.
- `none` — negligible traction, or an old post with no live interest.
- `unknown` — metrics are not visible; record this honestly, never guess.

Prefer active signals over passive reach: a high view count with near-zero
saves, shares, or comments is at most `moderate`. When no baseline can be
established, say so in the record and cap the tier at `moderate` unless the
absolute number is unmistakable for that platform. A post outside the run's
recency window drops one tier unless it is evidence of a durable pattern, in
which case it belongs in a stable finding, not a trend.

Read `confidence` (evidence-level trust) as that metric signal tempered by
corroboration, recency, creator fit, and stated limitations:

- `high` — a `moderate`-or-better signal that is current, on the creator's
  plausible topic range, and either corroborated across at least two independent
  sources or creators or a clear creator-relative outperformer with visible
  active engagement. A single isolated example, or a `farther_field` source,
  does not reach `high` on metrics alone — virality is not credibility.
- `medium` — a real but thin signal: one solid source, weaker corroborated
  metrics, or a slightly off-domain fit. Open-web or trend-article claims cap at
  `medium` unless they resolve to an actual primary post.
- `low` — weak or absent metrics, a lone anecdote, an unverified claim, stale
  material, or a pattern off the creator's lane. Flag it; never hide it behind a
  confident finding.

This rubric adapts the Agentic OS `str-trending-research` engagement-weighting
tiers into InfluencerOS's agent-authored, creator-relative form. It deliberately
does not import that skill's weighted-sum score or batch normalization: a
creator-relative baseline plus the source-yield learning loop is the chosen
model (ADR 0021), and this rubric only makes the existing enums repeatable.

## Finding Organization

Research findings should be organized primarily by topic and topic overlap. Each
finding should also capture:

- format or content type,
- video type when relevant,
- example creators and links,
- available performance evidence,
- creator-relative performance when available,
- target creator fit,
- likely way the influencer can speak about it,
- urgency or time horizon,
- confidence and staleness status.

Performance goals can be attached to ideas and queue entries, but they should
not be the primary organization model for research findings.

Candidate finding statuses:

- `emerging`,
- `active`,
- `saturated`,
- `declining`,
- `stale`,
- `thin_evidence`.

## Synthesis Discipline

Findings are synthesized from captured evidence, not from prior knowledge. Every
claim in a finding must trace to an evidence line captured in this or an earlier
run; a claim that cannot be attributed is not a finding yet.

State corroboration breadth explicitly. Each material finding records how many
independent sources, creators, and platforms carry the pattern. A pattern seen
across two or more independent creators or platforms is a stronger, higher-
confidence finding than a single post: set
`engagement_basis.cross_platform_validation` on the source-yield records that
show it, and note the breadth in the finding itself ("seen across 3 sources /
2 platforms").

Mine for contradictions. Actively look for sources that disagree or where the
pattern underperforms, and record the counter-signal. If real searching turns up
none, say so; if everything agrees perfectly, suspect that the synthesis is
over-simplified rather than that consensus is total. Contradictions are
high-value — they are often the most interesting finding and a content angle in
their own right. Make it explicit in the finding's prose whether a pattern is
broadly corroborated, a single-source signal, or contested, so the creator can
weight it.

This synthesis discipline adapts the Agentic OS `str-trending-research`
`synthesis-guide.md` (engagement-weighted, cross-validated synthesis with a
consensus/contradiction pass and an attribute-to-source self-check) into
InfluencerOS's schema-backed findings. It stays agent-authored — no score term
is computed for corroboration — consistent with the ADR 0021 no-formula stance.

## Storage Format Decision

Use sparse Markdown for creator-readable synthesis and structured records for
evidence that agents need to query, score, diff, or trace into production.

Recommended creator research layout:

```text
workspace-library/creators/<creator-slug>/research/
  findings.md
  runs/
    <research-run-id>/
      research-run.json
      search-plan.json
      run-summary.md
      evidence.jsonl
      metric-snapshots.jsonl
      source-yield.jsonl
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
```

`findings.md` is the rolling live summary. It should be short, edited in place,
and organized for quick creator review. It is not the complete evidence store.

Recommended `findings.md` frontmatter:

```yaml
research_findings_id: findings_<creator_slug>
creator_profile_id: creator_<id>
last_updated: <timestamp of last material update>
last_ran: <timestamp of last research run>
summary_char_limit: 12000
active_platforms:
  - instagram
  - tiktok
active_topic_clusters:
  - <topic cluster>
source_run_ids:
  - research_run_<id>
finding_ids:
  - finding_<id>
```

`last_updated` changes only when material findings change. `last_ran` may change
when research runs but finds nothing worth adding.

Each material finding in the Markdown body should have a stable `finding_id`.
The ID adds some authoring overhead, but it is necessary for traceability from
findings to queue ideas, promotions, projects, and later performance learning.

The body should be organized by topic cluster first, with platform notes inside
each cluster. It should include a short `Watch Now` section for urgent or
time-sensitive opportunities.

Stale or declining findings should appear in `findings.md` only when they are
important warnings or when a long-running finding is disappearing and that change
matters strategically. Otherwise, stale material should move out of the rolling
summary.

Each research run should preserve immutable evidence separately. The run can
include a short Markdown summary for review, but the important durable pieces are
structured evidence and metric snapshots.

Schema-backed records are most useful for:

- source URLs and creator/account names,
- captured visible metrics,
- post dates or observed ages,
- research timestamps,
- evidence strength,
- trend status and staleness,
- links from findings to queue ideas,
- links from queue ideas to future production records,
- metric snapshots over time.

Markdown is most useful for:

- the rolling creator-readable summary,
- short research-run interpretation,
- stable findings that become durable creator strategy.

The reusable research intelligence should be split into multiple files rather
than one large file so future runs can load only the needed context. For example,
a topic search can load search terms and watchlists without loading every
historical source note.

High-performing post examples should store URLs and raw visible metrics captured
at research time. Screenshots are not required for v1. Repeated snapshots of the
same post are allowed and useful when the system is watching fast-moving content
hourly or daily.

Research analytics should remain creator-specific in v1. Global cross-creator
research intelligence may be added later as an explicit promotion path after the
creator-specific system proves useful.

Research storage must have retention and pruning rules. Evidence files should
not grow forever. Outdated low-value source records, stale watchlist entries,
and old metric snapshots should be archived, compacted, or deleted according to
their role. The system should preserve links for ideas and projects that were
actually promoted, but it does not need to keep every weak or expired research
lead indefinitely.

Retention rules:

- unpromoted short-lived trend evidence may be deleted when it is no longer
  relevant,
- unpromoted weak research leads have a default retention window of 30 days,
- evidence that sparked a promoted idea, video, post, or project must be
  preserved with that downstream work,
- preserved evidence may live in or be copied into the project files so future
  learning can connect published performance back to the original research,
- slowly moving trends may be compacted into summaries instead of deleted,
- high-frequency metric snapshots should be kept while a watched post is active,
  then compressed into a short performance trajectory,
- `findings.md` should contain active and stable findings; stale or declining
  material should move out of the rolling summary unless it remains strategically
  useful,
- pruning runs inside research runs and through a manual prune command in v1;
  unattended scheduled pruning arrives with the research automation build-out.

## Evidence Capture Decision

For each researched post, video, or social source, capture a compact structured
evidence record.

Recommended fields:

- source ID,
- source URL,
- platform,
- creator or account handle,
- source relationship: `adjacent_creator`, `general_trend`, or `farther_field`,
- post title, caption summary, or visible text summary,
- short quoted snippets when useful, especially hooks,
- posted date or observed age when visible,
- captured timestamp,
- visible metrics at capture time,
- topic tags,
- content pillar fit,
- format or content type,
- hook or first-frame pattern,
- structure or pacing pattern,
- why it is high signal,
- what to learn from it,
- what not to copy,
- confidence and limitations.

Do not store full captions or full transcripts by default. Store summaries and
short quoted snippets that explain the research signal. Full transcripts should
only be stored when explicitly needed for a downstream workflow.

Metric snapshots should be tied to the same stable `source_id` so performance
velocity can be observed over time.

Creator-relative performance should usually be based on a small sampled baseline
of the reference creator's recent posts. If outperformance is obvious from
visible data, the record may mark the baseline as estimated and explain why.

Each creator should develop a small set of high-signal reference creators,
typically three to ten across relevant adjacent fields. These accounts should be
stored in creator-scoped research intelligence and reviewed over time.

In v1, research uses browser-visible public data only. Paid scraping, private
data access, external scraping APIs, platform APIs, and bulk automated collection
are out of scope unless a later workflow explicitly adds them behind approval.

## Presentation Decision

The research module should present different idea options and organize them by
expected usefulness. Scoring should consider the AI influencer's current
audience, persona, schedule, and the strength of the research evidence.

Ideas should not all optimize for virality. Some ideas may be designed for reach
and discovery, while others may be designed for nurturing the current audience,
trust-building, retention, authority, product education, or another declared
goal.

## Scoring Requirements

Each idea should expose enough scoring and rationale to make promotion decisions
clear. Scores should be recomputed or updated when new research changes the
supporting evidence.

Candidate scores:

- evidence strength: how convincing and current the supporting research is,
- viral potential: how likely the idea is to spread beyond the existing audience,
- audience nurture value: how well the idea serves current followers,
- creator fit: how strongly the idea matches persona, niche, voice, visuals, and
  boundaries,
- schedule fit: how well the idea fills an open schedule need or content mix gap,
- production readiness: how feasible it is to execute with current assets and
  planning state,
- urgency: how quickly the idea must be acted on before the opportunity decays,
- measurement clarity: how clearly success can be judged after publication.

The workflow should explicitly flag thin research rather than hiding weak
evidence behind confident ideas. `validate research` backs this with an
advisory warning: when a completed run declares a material update but only a
small share of its checked sources produced evidence, it emits a
thin-evidence WARN (never a failure — thin research is allowed, it just must
not read as well-corroborated).

Ideas may become stale automatically when newer research shows that the
supporting pattern is no longer performing. Stale ideas should remain auditable
instead of being deleted. Their scores, status, and rationale should update to
show why they are no longer favored.

## Measurement Expectation

Each queued idea should include a clear intended payoff so future production,
publishing, analytics, and learning can judge whether it worked.

The payoff should connect the idea to a measurable purpose, such as reach,
completion, shares, saves, comments, follows, trust-building, audience education,
product interest, or another creator-specific outcome.

The intended payoff does not need to be a final analytics model at queue time.
It is the first clear statement of what success would mean for the idea. The
promotion package should include or confirm this payoff before project creation.

## Scorecard Decision

Each idea queue entry should include every score in the scoring model.

Scores use a 0-100 numeric scale plus a short rationale. The number supports
sorting, filtering, and dashboards. The rationale explains the judgment and
prevents false precision.

Required scores:

- `evidence_strength`,
- `viral_potential`,
- `audience_nurture_value`,
- `creator_fit`,
- `schedule_fit`,
- `production_readiness`,
- `urgency`,
- `measurement_clarity`.

There should not be only one universal rank. Ranking should be goal-specific,
such as:

- best viral candidate,
- best audience nurture candidate,
- best fast-moving opportunity,
- best schedule filler,
- best low-lift production candidate,
- best strategic experiment.

Urgency may heavily affect ranking. A time-sensitive opportunity can be
recommended even when creator fit is only medium, but the promotion package must
make that tradeoff explicit and explain how the creator should speak about the
topic without drifting from persona or boundaries.

## Idea Queue Entry Decision

Each idea queue entry should be stored as one focused JSON file.

Expected queue entry fields:

- `idea_queue_entry_id`,
- `creator_profile_id`,
- status,
- title,
- hook,
- premise summary,
- intended payoff,
- topic cluster,
- content pillar,
- platform recommendations,
- platform variants,
- format recommendations,
- format variants,
- schedule recommendation,
- schedule fit type,
- source finding IDs,
- source evidence IDs,
- source metric snapshot or trajectory IDs,
- current scores,
- score deltas from the initial score snapshot,
- urgency window,
- creator fit notes,
- production notes,
- avoid notes,
- created, updated, and stale timestamps,
- linked idea promotion IDs,
- linked project IDs.

A queue idea may contain multiple platform variants when the idea and execution
are materially the same across platforms. For example, one front-facing video
that can run on Instagram, TikTok, and Facebook can remain one queue entry with
platform variants.

Split an idea into separate queue entries when the platform execution or format
is materially different. For example, one stock-market topic may become a video
on one platform and a photo post or text post on another; those should be
separate queue entries because production requirements, payoff, and performance
signals differ.

Wildcard behavior should be represented through schedule fields, not as a
separate status. Use `schedule_fit_type`, such as `scheduled_slot`, `wildcard`,
or another schedule relation defined by the Creator Content Schedule.

Evidence IDs are enough for source attribution as long as lookup remains easy.
The production funnel must be able to resolve evidence IDs into source material,
example links, hooks, structure notes, and avoid notes when reproducing the idea
faithfully.

## Evidence Lookup Decision

Evidence references should be structured objects rather than bare strings.

Recommended reference shape:

```json
{
  "research_run_id": "research_run_<id>",
  "evidence_id": "evidence_<id>",
  "metric_snapshot_ids": ["metric_snapshot_<id>"],
  "video_understanding_pack_ids": ["video_research_<id>"]
}
```

`video_understanding_pack_ids` is optional and present when real videos were
analyzed, so the Product Invariant's video-evidence trace survives promotion
into production.

Every evidence ID should resolve through the local recall/index layer to:

- source file path,
- line number, record offset, or JSONL record locator,
- source URL,
- platform and platform content type,
- captured metrics,
- extracted reusable elements.

The current accepted index ADR names a local SQLite index. The research module
requires a local recall index that can resolve evidence IDs reliably. SQLite
remains the default unless later implementation work proves another local
database is a better fit.

Project planning should warn, not fail, when a human-approved promotion contains
evidence IDs that cannot resolve. If future automation promotes ideas without
human approval, unresolved evidence should fail the automated promotion or
planning step.

Promoted Projects should include a compact evidence brief so production can
proceed without loading old research-run files by default. The brief should carry
the key reusable concepts, such as:

- topic,
- hook,
- thumbnail or first-frame concept,
- format or structure,
- source examples,
- extracted reusable moves,
- avoid notes,
- intended payoff,
- key metrics or score snapshot.

Full research records should remain recallable through the evidence references
when deeper production or learning context is needed.

## Research Intelligence Decision

Reusable research intelligence should help each future run get better at finding
high-signal creator-specific evidence.

Research intelligence files:

```text
research/intelligence/
  sources.json
  hashtags.json
  search-terms.json
  reference-creators.json
  watchlist.json
```

Research runs may automatically suggest additions, updates, or removals for
research intelligence. However, core high-signal reference creators are
user-approved. Adding a creator to the core watchlist or removing one from it
requires user approval.

Reference creators may have usefulness scores when the system can explain the
measurement clearly. Candidate factors include:

- repeated high-performing posts in relevant topics,
- audience overlap with the target creator,
- creator-relative outperformance,
- useful format or hook patterns,
- signal quality over recent research runs,
- rate of producing usable idea queue entries.

Watchlist entries do not need individual polling frequencies in v1. Separate
cron jobs or scheduled workflows should handle different research modes, such as
checking the whole reference creator watchlist, checking popular hashtags, or
running an urgent trend scan.

Hashtags and search terms should be platform-scoped. A hashtag or query can be
useful on one platform and noisy on another.

Noisy or low-performing sources do not need negative scores. Their usefulness can
fall to zero. If a zero-usefulness item is user-approved or part of a watchlist,
the system should present it to the user as a removal candidate rather than
silently deleting it.

## Automation And Logging Decision

Scheduled research jobs belong to the broader memory and operations subsystem
that handles recurring work. In v1, these jobs are research-only and read-only
with respect to production. They may update research findings, research
intelligence, metric snapshots, idea queue scores, staleness, warnings, badges,
and notifications. They must not promote ideas into production.

Initial automation jobs:

- reference creator watchlist check,
- hashtag and search-term trend check,
- queue refresh and staleness review,
- metric snapshot refresh for watched posts,
- schedule gap scan,
- urgent trend or news scan.

Jobs may notify the user when configured thresholds are crossed, such as viral
potential rising above 85. Notifications should also create or update a
Kanban-visible badge or flag so the board and external notification channel stay
aligned.

Notifications do not need a separate durable notification record in v1. Use
system event log entries plus Kanban flags or badges. Notifications do not
require acknowledgement.

Threshold notification settings may exist globally and per creator. Creator
settings can override or extend global defaults.

Initial notification surfaces:

- Kanban board flags or badges,
- Telegram.

User-facing notifications should be concise summaries. Full details should live
in the linked automation run, research run, warning, evidence, queue entry, or
project record.

Each recurring job should track:

- job ID,
- job type,
- creator scope when applicable,
- last ran,
- last material update,
- last error,
- enabled or disabled status,
- threshold configuration when applicable.

Use a generic `AutomationRun` record for every scheduled or recurring job run.
When an automation performs research, it should also create or update the
appropriate `ResearchRun` records. This keeps research evidence inside the
research module while still allowing the operations subsystem to track all
automations consistently.

System event logging should exist at the OS level and should be searchable across
creators. The recommended model is:

- one append-only system event log for cross-system debugging,
- creator ID or creator slug on events when the event is creator-scoped,
- optional creator-scoped projections or filtered logs for workspace-local review.

The system-wide log is the source for debugging automation failures and OS-level
behavior. Creator-scoped projections help agents work from a creator workspace
without loading unrelated system history.

## Open Questions

- What exact fields belong in the separate Creator Content Schedule record?
- What exact fields belong in `ResearchFindings`?
- What exact fields belong in `IdeaQueue` and `IdeaQueueEntry`?
- What exact schema is needed for `evidence.jsonl` and
  `metric-snapshots.jsonl`?
- What exact fields belong in `IdeaPromotion`?
- What source evidence must be captured before synthesis?
- What scoring scale should be used, and should scores be numeric, categorical,
  or both?
- Which scores are required for every idea versus optional by goal?
- What metadata must transfer from a queued idea into `Project` and the later
  Creative Performance Map?
