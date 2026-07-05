# Research Adapter Registry

InfluencerOS research adapters are acquisition boundaries. They decide how a
run may inspect public or private sources before distilled observations become
`ResearchEvidence`, `MetricSnapshot`, `VideoUnderstandingPack`, or
`ResearchSourceYield` records.

This registry is intentionally broader than the active v1 implementation.
Planned adapters are named now so future connector work can plug into the
existing `ResearchSearchPlan` and `ResearchSourceYield` contracts instead of
redesigning research provenance.

## Status Values

- `active`: allowed in normal manual research runs today.
- `planned`: intended before go-live, but requires a separate implementation
  decision.
- `deferred`: intentionally not available in v1 without explicit approval.
- `unavailable`: known but not usable in the current environment.

## Access Methods

- `public_web`: search or fetch public web pages without credentials.
- `browser_visible`: inspect content visible without login/session credentials.
- `external_video_understanding`: use an approved external acquisition tool such
  as `/watch`.
- `user_provided_local`: inspect a local file provided by the user.
- `manual_paste`: user supplies source text or transcript.
- `api_backed`: call a provider/platform API.
- `scraping_api`: call a scraping or browser-rendering provider.
- `logged_in_browser`: inspect content through a logged-in platform session.
- `scheduled_job`: run acquisition unattended.

## Active Adapters

| Adapter ID | Access method | Auth | Approval | Use |
| --- | --- | --- | --- | --- |
| `public_web_search` | `public_web` | no | no | Search public web pages and public platform pages visible without credentials. |
| `instagram_public_browser` | `browser_visible` | no | no | Inspect public Instagram pages/posts visible without login. |
| `tiktok_public_browser` | `browser_visible` | no | no | Inspect public TikTok pages/videos visible without login. |
| `x_public_web` | `public_web` | no | no | Inspect public X/Twitter pages or search-result snippets visible without login. |
| `reddit_public_web` | `public_web` | no | no | Inspect public Reddit threads and comments visible without login. |
| `substack_public_web` | `public_web` | no | no | Inspect public Substack posts/notes. |
| `medium_public_web` | `public_web` | no | no | Inspect public Medium articles. |
| `facebook_public_browser` | `browser_visible` | no | no | Inspect public Facebook pages/posts visible without login. |
| `linkedin_public_browser` | `browser_visible` | no | no | Inspect public LinkedIn pages/posts visible without login. |
| `watch_public_video` | `external_video_understanding` | no | conditional | Inspect public or user-provided videos through the approved `/watch`-style boundary; Whisper/API fallback, first-run installs, and batches require explicit approval. |
| `user_provided_local_video` | `user_provided_local` | no | no | Inspect local files supplied by the user when local tooling is already available. |
| `manual_source_paste` | `manual_paste` | no | no | Use pasted source text when platform access is unavailable. |

## Key-Gated Research-Acquisition Connectors (ADR 0022)

Built as the `influencer_os/connectors/` layer. Each is **active when its env
key is present** and **unavailable otherwise** (the run falls back to built-in
`WebSearch`/`WebFetch`). Under ADR 0022, key presence is standing approval for
that connector's research-acquisition calls — no per-run prompt — bounded by a
per-run call cap and a global kill switch. This standing-approval carve-out
covers research acquisition only; generation calls stay behind exact approval.

| Adapter ID | Connector | Access method | Env key | Maps output into |
| --- | --- | --- | --- | --- |
| `reddit_api_or_search` | `reddit_openai` | `api_backed` | `OPENAI_API_KEY` | `ResearchEvidence` + `MetricSnapshot` (upvotes/comments) |
| `x_api` | `x_xai` | `api_backed` | `XAI_API_KEY` | `ResearchEvidence` + `MetricSnapshot` (likes/reposts/replies) |
| `firecrawl_public_web` | `firecrawl_web` | `scraping_api` | `FIRECRAWL_API_KEY` | `ResearchEvidence` (rendered public pages) |
| `linkedin_apify` | `linkedin_apify` | `api_backed` | `APIFY_API_KEY` | `ResearchEvidence` + `MetricSnapshot` (post reactions) |

Activation env vars:

- `INFLUENCER_OS_CONNECTOR_MAX_CALLS` — per-run cap on paid provider calls
  (default small); exceeding it stops that connector as a low-yield outcome.
- `INFLUENCER_OS_DISABLE_PAID_CONNECTORS=1` — kill switch that disables the whole
  paid tier regardless of keys.

Keys live in the environment / `.env` only (gitignored); see `.env.example`.

## Planned / Deferred Adapters

| Adapter ID | Access method | Auth | Approval | Activation requirement |
| --- | --- | --- | --- | --- |
| `youtube_public_video` | `external_video_understanding` | no | conditional | Decide whether YouTube is a first-class research platform or a video-source adapter. |
| `youtube_data_api` | `api_backed` | yes | yes | Add env/key policy, quota policy, retention rules, and ADR 0020 platform decision if treated as a platform. |
| `instagram_logged_in_browser` | `logged_in_browser` | yes | yes | Add account ownership, private-data exclusion, session storage, and audit policy. |
| `tiktok_logged_in_browser` | `logged_in_browser` | yes | yes | Add account ownership, private-data exclusion, session storage, and audit policy. |
| `scheduled_research_refresh` | `scheduled_job` | varies | yes | Add Automation OS job definition, approval boundaries, and notification policy. |

## Query Intent Patterns

These adapt the Agentic OS `str-trending-research` routing tables:

- `recommendations`: best/top/recommended options; prefer Reddit, X/web
  discussions, and sources with visible community validation.
- `news`: current events or announcements; prefer fresh public web, X/web,
  official sources, and Reddit reaction.
- `how_to`: methods or techniques; prefer Reddit, public tutorials, and
  practical creator examples.
- `general_discussion`: audience language, objections, and sentiment; prefer
  Reddit and public comment-rich sources.
- `trend_scan`: current social formats, hooks, and recurring motifs; prefer
  public social pages and evidence with visible metrics.
- `creator_watchlist`: known high-signal creators from research intelligence.
- `hashtag_check`: platform-scoped hashtag pages or public search result pages.
- `queue_refresh`: evidence that changes existing idea urgency, score,
  staleness, or rationale.

## Yield Rules

- Every completed research run must create `search-plan.json` before browsing
  and `source-yield.jsonl` after browsing.
- Search plans may name planned/deferred adapters, but only `active` adapters
  (including key-gated connectors whose env key is present) may have
  `decision: "use_now"`.
- The four ADR 0022 key-gated research-acquisition connectors are standing-
  approved by key presence (bounded by the call cap and kill switch). Logged-in
  access, provider transcription, batch video, scheduled execution, and external
  notifications still require explicit approval before use.
- Source-yield records should capture both useful and low-yield attempts.
- `research/intelligence/sources.json` aggregate `yield_stats` must reconcile
  with `source-yield.jsonl` records that reference `source_intel_*` IDs.
- A future connector must map output into existing canonical records rather
  than creating a parallel research store.
- YouTube remains a planned adapter until ADR 0020 is updated or a new ADR
  declares it a video-source adapter outside the research platform enum.
