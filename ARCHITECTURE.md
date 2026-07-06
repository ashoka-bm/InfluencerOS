# Architecture

InfluencerOS v1 is a dry-run-first planning system for researched creator content plans, starting with universal short-form video and now including article and thread production plans.

## Architectural Direction

InfluencerOS uses the repository root as the shared operating system and ignored Creator Workspaces for real creator state. The public repo stores product contracts, schemas, examples, docs, tests, skills, and reusable prompts. Local Creator Workspaces store private creator identity, references, research history, projects, memory, analytics evidence, and progress notes.

InfluencerOS follows the purchased Agentic OS reference at `/Users/ashokaji/code/External repos/Agentic Academy/agentic-os` by default. Any architecture that diverges from that reference must be surfaced and recorded before implementation. See `docs/os-construction/agentic-os-alignment.md`.

The build sequence is:

1. Planning OS: stable creator workspaces, research, ideas, scripts, prompts, production plans, and output package specs.
2. Learning OS: published post records, analytics snapshots, and feedback into future research and idea generation.
3. Generation OS: approved provider-backed image, video, audio, and render generation.

See:

- `docs/os-construction/prd.md`
- `docs/os-construction/roadmap.md`
- `docs/os-construction/repository-map.md`
- `docs/os-construction/agentic-os-alignment.md`
- `docs/os-construction/agentic-os-copy-plan.md`
- `docs/os-construction/agentic-os-parity-plan.md`
- `docs/os-construction/progress.md`
- `docs/os-construction/visual-architecture-maps.md`
- `docs/os-construction/context-matrix.md`
- `docs/os-construction/skill-registry.md`
- `docs/creator-workspace-structure.md`
- `docs/adr/0001-creator-workspaces.md`
- `docs/adr/0002-hybrid-creator-authoring.md`
- `docs/adr/0004-api-primary-analytics-ingestion.md`
- `docs/adr/0005-performance-attribution-model.md`
- `docs/adr/0006-creative-performance-map.md`
- `docs/adr/0007-output-package-platform-adaptations.md`
- `docs/adr/0008-creator-learning-memory.md`
- `docs/adr/0009-schema-first-implementation-order.md`
- `docs/adr/0010-file-first-with-sql-index.md`
- `docs/adr/0011-semantic-lookup-projection.md`
- `docs/adr/0012-project-scoped-content-work.md`
- `docs/adr/0013-creator-setup-readiness-and-reference-lifecycle.md`
- `docs/adr/0020-platform-scoped-research-and-idea-queue.md`
- `docs/adr/0021-research-intelligence-planning-and-yield.md`

## Creator Authoring

Creator identity uses a hybrid authoring flow. A rich master intake, such as an influencer breakdown or interview transcript, may seed the creator workspace. InfluencerOS derives draft workspace files from that intake:

- `creator-profile.json`
- `context/SOUL.md`
- `context/USER.md`
- `context/MEMORY.md`
- `brand_context/identity.md`
- `brand_context/soul.md`
- `brand_context/personal-brand.md`
- reference library requirements

After review, the split workspace files become the maintained source of truth. The original intake can remain archived as provenance, but operational workflows should read the current workspace files.

`context/SOUL.md`, `context/USER.md`, and `context/MEMORY.md` are the tiny always-loaded creator context files. `creator-profile.json` is a typed operational summary, not a full identity dump. It should contain enough structured information for routine automation while pointing to the richer `brand_context/` files and reference assets.

Creator Setup may capture text-first and written-content strategy inputs such as Substack, LinkedIn, X, blog, or newsletter direction. `brand_context/personal-brand.md` is the rich source of truth for content strategy; `creator-profile.json` carries the operational summary used by research and planning.

## First-Party OS Persona

InfluencerOS also treats the repository itself as a first-party persona for system marketing, positioning, documentation, launch content, and process learning.

Root `context/` and `brand_context/` hold this OS persona. Creator-specific context still belongs in ignored Creator Workspaces. Scope-specific skill overrides use `SKILL.local.md`; promote a local rule into the base skill only after repeated feedback shows it should apply system-wide.

Baseline skill source files live under repo `skills/<skill-name>/SKILL.md`. Creator Workspaces receive copied runtime skill folders under `.claude/skills/<skill-name>/` so an agent can safely run from the creator root. `python3 -m influencer_os sync-creator-runtime <creator-workspace>` refreshes copied baseline skills while preserving creator `SKILL.local.md` files and creator-only skill folders.

## First Vertical Slice

```text
Creator Profile
  -> Creator Content Schedule
  -> Video Understanding Pack, when researching real videos
  -> Research Findings
  -> Idea Queue
  -> human-approved Idea Promotion
  -> Project
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
- capture creator content strategy across text, image, video, audio, carousel, and story-sequence mediums,
- research current platform-scoped content patterns across X, Instagram, TikTok, Substack, Medium, Reddit, Facebook, and LinkedIn,
- analyze real videos through frame and transcript evidence when useful,
- maintain concise creator-scoped Research Findings backed by dated evidence,
- maintain a scored creator-scoped Idea Queue,
- wait for explicit human approval before promoting an idea into production,
- apply a compatible social template or production structure to the promoted idea,
- create a format-specific production plan,
- create a provider-neutral base video generation plan,
- register an Output Package from existing approved/imported artifacts or text files.

InfluencerOS v1 does not:

- create platform-specific adapters,
- plan post-production motion graphics,
- publish or schedule posts,
- scrape private social data,
- run analytics feedback loops,
- generate media without explicit approval.

## Module Boundaries

InfluencerOS is built as deep modules with small public surfaces. Each module
exposes a few interface records; everything else is module-internal. A
downstream module references the interface record of the module before it and
resolves deeper provenance transitively (see the Product Invariant in
`AGENTS.md`).

| Module | Inputs (read-only) | Public interface records | Internal records |
| --- | --- | --- | --- |
| Creator Setup | intake sources, references | Creator Profile, Creator Content Schedule, readiness status, `context/` and `brand_context/` files | import scratch, draft notes |
| Research and Ideas | Creator Profile, Creator Content Schedule, distilled creator memory, public sources | Research Findings (`research/findings.md`), Idea Queue (`research/idea-queue/`), Idea Promotion (`research/idea-promotions/`) | research runs, search plans, evidence, metric snapshots, source-yield ledgers, research intelligence, stable findings |
| Production | Idea Promotion, evidence brief, Reference Library | Project, Applied Social Template, format-specific plans, Base Video Generation Plan, Output Package | draft prompts, working notes |
| Learning | Output Package, Published Post Record, Analytics Snapshots | Performance Summary, distilled creator memory | raw analytics exports |
| Operations (execution deferred) | job definitions | AutomationRun, SystemEvent | scheduler state |

Write boundaries:

- Research writes only under `research/`.
- The human-approved Idea Promotion is the constructor for
  `projects/<project-id>/`: the promotion step writes the promotion record,
  `project.json`, and `evidence-brief.md`; production owns everything else
  under the project folder.
- Production writes only under `projects/<project-id>/`.
- `boards/`, `system/`, and the local indexes are derived projections:
  rebuildable from canonical records and never the source of truth.
- Cross-module reads go through public interface records. Module-internal
  records resolve by ID through the local recall index instead of direct file
  reads, so a module can reorganize its internal storage without breaking its
  consumers.

## V1 Format Shortlist

InfluencerOS v1 supports six platform-agnostic production formats:

- `short_form_video`: a vertical hook-to-payoff video.
- `carousel`: a swipeable image sequence, including Instagram carousels and TikTok Photo Mode style posts.
- `single_image_post`: one strong still, graphic, or generated image.
- `story_sequence`: a short ephemeral-feeling sequence of vertical visuals.
- `article`: a long-form written article or newsletter-style post.
- `thread`: an ordered short-form text thread.

Live streams, community posts, polls, and platform-specific variants are deferred until the file-first production loop is proven.

Research and the Idea Queue are platform-scoped from day one (ADR 0020). Promotion may only create Projects for formats production supports; text content unit types and routing joined in Phase 1 slice 6.

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

Research and generation are separated. Research may browse current public sources after writing a search plan, must cite evidence, and must record source-yield outcomes. Provider-backed generation requires explicit approval.

Video understanding research may use public URLs or local files to inspect frames and transcripts. The supported external acquisition tool is the installed `bradautomates/claude-video` `/watch` workflow, when available; it remains outside the repo and only feeds distilled observations into `VideoUnderstandingPack` records. Whisper-style transcription fallback is provider-backed and requires explicit approval/configuration.

## CLI

The CLI supports:

```bash
python3 -m influencer_os validate examples
python3 -m influencer_os validate workspace <creator-workspace>
python3 -m influencer_os validate project <project-path>
python3 -m influencer_os validate record <schema-name> <record-path>
python3 -m influencer_os validate research <creator-workspace>
python3 -m influencer_os validate queue <creator-workspace>
python3 -m influencer_os validate board <creator-workspace>
python3 -m influencer_os init-creator <workspace-manifest> [--workspace-root <dir>]
python3 -m influencer_os import-intake <source-file> --creator-workspace <path> --source-type <type> --notes "<note>" [--source-id <id>] [--imported-on YYYY-MM-DD]
python3 -m influencer_os set-intake-status <creator-workspace> <source-id> <drafted|reviewed>
python3 -m influencer_os sync-creator-runtime <creator-workspace>
python3 -m influencer_os update-creators [--workspace-root <dir>]
python3 -m influencer_os init-project <project-manifest> --creator-workspace <path>
python3 -m influencer_os register-output-package <output-package> --project <project-path> [--asset-root <dir>]
python3 -m influencer_os register-published-post <published-post-record> --project <project-path>
python3 -m influencer_os add-analytics-snapshot <analytics-snapshot> --project <project-path>
python3 -m influencer_os import-analytics-csv <snapshots.csv> --project <project-path>
python3 -m influencer_os init-run <creator-profile>
python3 -m influencer_os rebuild-index <creator-workspace> [--db <sqlite-path>]
python3 -m influencer_os rebuild-board <creator-workspace>
python3 -m influencer_os prune <creator-workspace> [--apply] [--retention-days <n>]
python3 -m influencer_os memory-write <MEMORY.md-path> "<fact>" [--section "<section>"]
python3 -m influencer_os log-learning <learnings-path> <skill-name-or-topic> "<entry>" [--date YYYY-MM-DD] [--evidence <record-id> ...] [--strength <strength>]
```

Validation resolves provenance: `validate project` anchors on the locked Idea Promotion — `source_refs.idea_promotion_id` must resolve to `research/idea-promotions/<id>.json`, the promotion must list the project, cached deeper refs must match the promotion snapshot, and the promotion gate requires a real idea queue entry and at least one production-supported approved format (unresolved evidence warns for human-approved promotions and fails for automated paths), and the project must stay within the promotion's approved surface — `target_formats` ⊆ `approved_formats`, and each `platform_targets` surface that maps to an ADR 0020 research platform must be approved (off-set surfaces like `youtube_shorts` are exempt). `validate research` covers runs, pre-browse search plans, JSONL evidence and metric snapshots, source-yield ledgers, findings frontmatter and char limits, intelligence files, boards, and system projections (project warnings must pair their promoted-work ids and target records that exist and form one consistent chain — the queue entry always, and for promoted work the project's locked promotion must equal the warning's promotion and that promotion's queue entry must equal the warning's entry); `validate queue` checks manifest/entry consistency (each entry listed exactly once), evidence ref resolution, and source finding refs (resolved against the union of findings frontmatter, stable findings, and immutable run outputs, so rotated-out findings still resolve); the promotion gate resolves `research_finding_ids` the same way (warn for human-approved, fail for automated); both pin every record's creator fields to the owning `creator-workspace.json`, and the promotion gate rejects a promotion whose queue entry belongs to a different creator. `validate project` also requires reference assets and video packs to exist in the owning workspace, packaged projects must cross-match their output package against the project, applied template, and plan records, and `validate workspace` requires every `source_intakes` path to resolve to a real file inside the workspace (paths are schema-pinned under `sources/`; symlink escapes are rejected after `resolve()`). `register-output-package` copies upload-ready files from a mirrored asset root, writes `output-package/output-package.json`, marks the project `packaged`, and rolls those writes back if final project validation fails. `register-published-post` records a manual publication: the record's chain ids, `assets_used` upload-asset ids, and caption/description path must match the registered package; it writes `published/published-post-records/<ppr-id>.json`, moves the project `packaged` → `published` on the first live-attesting record, rolls back on failure, and `validate project` re-checks every registration invariant at rest (filename-matches-id, live-record/status reconciliation both directions, no duplicate `(platform, platform_post_id)`/`public_url` identities, null thumbnails only for text-format packages, and the package staying `upload_ready` at every status from `packaged` onward). `add-analytics-snapshot` and `import-analytics-csv` ingest AnalyticsSnapshots through one shared writer seam (ADR 0004): the snapshot must cite a live published post record on the same platform, chain ids must match the project and package, `hours_since_publish` is derived from the record timestamps when omitted (a pre-publication snapshot is rejected), `raw_source_ref`/`retention_curve_ref` must resolve to real files under `analytics/raw/` without escaping the project, and the CSV import is all-or-nothing; `validate project` re-checks every ingestion invariant at rest. Reference-library `path`/`prompt_path` values are schema-pinned under `references/`, and `creator-profile.json` `reference_refs` must resolve to real library assets. `validate workspace` is status-keyed: at `content_ready`, `generation_ready`, or `active` it enforces the medium-based readiness blockers (foundation population, context byte caps, intake provenance, required asset kinds per content medium, lifecycle asset/prompt file existence) and reports every failed blocker in one error. `import-intake` copies a setup source under `sources/` by type and records the provenance entry; `set-intake-status` moves its extraction status forward only (`pending` → `drafted` → `reviewed`). `memory-write` enforces the 2,500-byte `MEMORY.md` cap before writing; `update-creators` backs up each replaced skill folder to `.claude/skills-backup/`. `log-learning` writes per-skill entries to OS learnings files and, when the target is a Creator Workspace `memory/learnings.md`, evidence-linked creator lessons (ADR 0008): `--evidence` and `--strength` are required, every evidence id must resolve to a schema-valid workspace performance-chain record anchored to its project manifest (performance summary, published post record, analytics snapshot, project, or output package — a planted id-field-only JSON does not resolve), a `multi_post_pattern` strength must be supported by cited evidence identifying at least two distinct published posts, the entry is one parseable line under a single `## Creator Lessons` section (`- YYYY-MM-DD [strength]: lesson (evidence: id, ...)`; duplicate section headings are rejected), and `validate workspace` re-checks every at-rest lesson entry the same way — a hand-edited dangling evidence id, unsupported strength claim, or duplicated section fails workspace validation. `rebuild-index` rebuilds one creator's rows in the shared local recall index (ADR 0010: `workspace-library/index/influencer-os.sqlite`), mapping evidence and metric-snapshot ids to JSONL path and line, finding ids to `findings.md` or stable-finding files, and queue entries, promotions, video packs, projects, published post records, analytics snapshots, performance summaries, and board cards to their source files with content hashes (the Phase 2 learning scans mirror the writer layout — `published/published-post-records/`, `analytics/snapshots/`, `performance-summary.json` — so `analytics/raw/` payloads are never scanned); the index is a rebuildable projection, never a validation dependency — validation stays file-first. `rebuild-board` derives `boards/content-board.json` from canonical records: idea queue entries become parent cards and projects become child cards linked through their locked Idea Promotion, card ids are deterministic (`card_<source_record_id>`), active project warnings badge exactly the card they target (promoted-work warnings badge the project card, queue-level warnings badge the idea card, resolved warnings badge nothing), and `columns` plus `manual_order` are preserved projection metadata. `validate board` fails a board whose cards disagree with canonical records or whose `manual_order` does not list every card exactly once. `prune` applies the research retention rules: it removes unreferenced evidence past the retention window (default 30 days) and the metric snapshots belonging to it, never touches anything a queue entry, promotion, or project references, and records removals on the run manifest as `pruned_evidence_ids`/`pruned_metric_snapshot_ids` so the original `outputs` declaration stays intact (outputs reconciliation expects JSONL contents to equal outputs minus pruned). Dry-run by default; only `--apply` deletes.

Run state is local and ignored under `workspace-library/runs/`.

Creator state is local and ignored under `workspace-library/creators/`.

```text
workspace-library/creators/<creator-slug>/
  AGENTS.md
  creator-workspace.json
  creator-profile.json
  content-schedule.json
  context/
    SOUL.md
    USER.md
    MEMORY.md
  brand_context/
    identity.md
    soul.md
    personal-brand.md
    voice-samples.md
  .claude/
    skills/
      <skill-name>/
        SKILL.md
        SKILL.local.md
  sources/
  references/
  research/
  boards/
  system/
  projects/
  memory/
  progress/
```

## Learning OS

The Learning OS is API-primary but not API-only. Platform ingestion connectors should write normalized Analytics Snapshot records into the relevant Creator Workspace. Manual entry and CSV import write the same record shape for cases where platform APIs are unavailable, incomplete, or not yet configured.

Analytics attaches to Published Post Records, and Published Post Records attach to Output Packages. The feedback loop should distill raw metrics into creator-scoped learnings before those learnings influence future research and idea generation.

Analytics must support performance attribution. The system should preserve stage-level dimensions for packaging, hook, body retention, payoff, and CTA performance so future content can improve the specific creative decision that underperformed.

Every Output Package must include a lightweight Creative Performance Map. It links packaging, hook, body retention, payoff, and CTA decisions to source references, intended effects, primary judging metrics, and optional variants. The map points to raw creative material instead of duplicating it.

Output Packages use a universal core with optional platform adaptations. The core preserves the shared creative package; adaptations capture platform-specific titles, captions, thumbnails, first frames, CTAs, crops, timing recommendations, and stage-level variants.

Durable creator memory stores distilled lessons plus linked performance summaries. Raw analytics stay inspectable in creator-scoped files, but future workflows should use distilled lessons by default unless they are diagnosing performance or planning a deliberate test.

## Local Indexes

Creator workspace files are the durable source of truth. A local SQL database may index workspace records for fast lookup, dashboards, analytics comparison, ingestion state, and workflow queries. The default index path is `workspace-library/index/influencer-os.sqlite`.

The SQL index must be rebuildable from workspace files and must preserve source file provenance. InfluencerOS also maintains a semantic lookup projection for low-context agent recall over selected human-readable decision material such as identity files, soul files, personal brand files, research summaries, distilled learnings, and performance summaries. Raw analytics are structured evidence and should not be semantically indexed by default.

Agents should use SQL for exact filters, joins, publish status, missing records, and metric comparisons. They should use semantic lookup for precedent, similar-topic recall, durable lessons, audience interpretation, and creative decision support.

## Format-Specific Production Plans

The first implemented production records are:

- `MicroJourneyVideoPlan` for `format_short_form_video`,
- `CarouselPlan` for `format_carousel`,
- `SingleImagePostPlan` for `format_single_image_post`,
- `StorySequencePlan` for `format_story_sequence`.

## Schema Slices

Implemented workspace, project, and Learning OS schemas:

- `creator-workspace.schema.json`
- `creator-profile.schema.json` v2
- `reference-library.schema.json`
- `project.schema.json`
- `output-package.schema.json`
- `published-post-record.schema.json`
- `analytics-snapshot.schema.json`
- `performance-summary.schema.json`

Workflow and CLI expansion should follow these contracts.
