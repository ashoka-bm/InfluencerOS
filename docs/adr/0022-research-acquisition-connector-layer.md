# ADR 0022: Research Acquisition Connector Layer

## Status

Accepted

## Context

InfluencerOS research runs currently acquire evidence only through Claude's
built-in `WebSearch`/`WebFetch`. A live loop-exercise run against the
`remy-vale` fixture (progress log 2026-07-05) showed the binding limit: those
built-ins cannot reach `reddit.com` (blocked in both `WebSearch` allowed
domains and `WebFetch`) and TikTok tag pages fail, so runs can only corroborate
categories from secondary care guides and cap at `medium` confidence with no
primary-post engagement metrics.

The Agentic OS reference (`str-trending-research`, `tool-firecrawl-scraper`,
`tool-linkedin-scraper`, and the `xai_x` path) solves this with key-gated hosted
tools: OpenAI Responses `web_search` domain-locked to reddit.com returns Reddit
threads with upvotes and comments; xAI `x_search` returns X posts with
engagement; Firecrawl renders JS-heavy public pages; Apify scrapes LinkedIn.
These are exactly the `planned` `api_backed`/`scraping_api` adapters named in
`docs/research-adapter-registry.md`, which the registry says require "a separate
implementation decision." This ADR is that decision.

The registry's adapters are documentary permission boundaries today, not code.
This ADR makes the research-acquisition tier real as an env-gated connector
layer that is dormant until a provider key is present, so capability activates
"as soon as the API key is in" without changing any workflow.

Two scope decisions were made by the user (2026-07-05):

- Build the **research-acquisition tier only** (Reddit/OpenAI, X/xAI, Firecrawl,
  LinkedIn/Apify). Generation/utility tools (image-search, screenshot, PDF,
  humanizer, transcription) and publishing (`tool-zernio-social`) are **not**
  built here; publishing remains a v1 non-negotiable deferral.
- **Key presence is standing approval** for that tier's paid calls (frictionless
  activation), instead of a per-run exact-approval prompt.

## Decision

Add `influencer_os/connectors/`: an env-gated research-acquisition connector
layer. Each connector adapts an Agentic OS acquisition pattern (adaptation, not
verbatim copy per the copy policy) and maps provider output into the existing
canonical records — `ResearchEvidence` and `MetricSnapshot` — never a parallel
research store. Connectors surface through the `source-yield.jsonl` /
`search-plan.json` contracts from ADR 0021.

Connector set and env-var contract:

| Connector | Adapter ID | Provider | Env var | Reaches |
| --- | --- | --- | --- | --- |
| `reddit_openai` | `reddit_api_or_search` | OpenAI Responses `web_search` (domain-locked reddit.com) | `OPENAI_API_KEY` | Reddit threads + upvotes/comments |
| `x_xai` | `x_api` | xAI `x_search` | `XAI_API_KEY` | X posts + engagement |
| `firecrawl_web` | `firecrawl_public_web` | Firecrawl scrape/crawl | `FIRECRAWL_API_KEY` | Any public web/JS page, incl. rendered Reddit |
| `linkedin_apify` | `linkedin_apify` | Apify LinkedIn actor | `APIFY_API_KEY` | Public LinkedIn profiles/posts |

Activation contract:

- A connector is **available** only when its env var is set. No key → the
  connector reports `unavailable` and the run falls back to built-in
  `WebSearch`/`WebFetch`, exactly as today.
- Key presence is standing approval for that connector's research-acquisition
  calls; no per-run prompt (the standing-approval divergence below).
- Keys are read from the environment / `.env` only (never hardcoded, logged, or
  committed). `.env` is already gitignored; `.env.example` documents the vars.

Enforcement: the standing-approval split is implemented in the search-plan and
source-yield validators and is pinned to the exact approved connector adapter
IDs using their expected access methods — not to `api_backed`/`scraping_api` at
large. ADR 0027 adds `youtube_data_api` to that approved set. Standing-approved
adapters may be `use_now` when `active` and need not set `approval_required`;
every other gated adapter (`logged_in_browser`, `scheduled_job`, and
unapproved api-backed/scraping adapters) stays fully gated (never `use_now`,
must require approval). Reddit thread enrichment is a free public reddit.com
read and does not draw on the paid call budget; it is bounded separately by a
per-run enrichment cap. Connector output is a workflow-boundary contract
validated by `schemas/research-fetch-result.schema.json`.

Guardrails so standing approval is not unbounded:

- A per-run call cap (`INFLUENCER_OS_CONNECTOR_MAX_CALLS`, default small) bounds
  spend per research run; exceeding it stops that connector and is recorded as a
  low-yield `source-yield` outcome, not a crash.
- A global kill switch (`INFLUENCER_OS_DISABLE_PAID_CONNECTORS=1`) disables the
  whole paid tier regardless of keys, for cost or offline safety.
- Connectors run only inside an explicit, user-initiated research run; there is
  no scheduled/unattended path (that stays deferred to Automation OS).
- Usage (provider, call count, adapter id) is summarized in the run summary;
  request/response bodies and keys are never logged.

## Agentic OS divergence test

```text
Agentic OS divergence test:
- Proposed change: Add an env-gated research-acquisition connector layer whose
  paid calls are standing-approved by API-key presence rather than per-run exact
  approval.
- Agentic OS reference: str-trending-research (openai_reddit.py, xai_x.py),
  tool-firecrawl-scraper, tool-linkedin-scraper. Agentic OS activates these on
  key presence with no exact-approval gate.
- InfluencerOS decision: Adopt the connector tooling (adaptation). Diverge from
  the InfluencerOS exact-approval invariant for the research-acquisition tier
  only: key presence is standing approval, bounded by per-run call caps and a
  kill switch. The generation provider gate (image/video/audio/render) is
  unchanged and still requires exact per-call/batch approval.
- Classification: adaptation (tooling) + divergence (approval model).
- Decision record: this ADR (0022); Accepted Divergences row in
  agentic-os-alignment.md; provider-boundary.md carve-out.
- Status: pass (user approved 2026-07-05).
```

## Scope

In scope: Reddit/OpenAI, X/xAI, Firecrawl, LinkedIn/Apify research-acquisition
connectors; env detection; canonical-record mapping; cost guardrails; CLI to
list/inspect connector availability and to fetch within a run.

Out of scope (unchanged by this ADR):

- Generation/render/audio provider calls — still behind exact approval
  (provider-boundary.md; not weakened here).
- Publishing (`tool-zernio-social`) and any posting/scheduling — v1 deferral.
- Generation/utility tools (image-search, screenshot, PDF, humanizer,
  standalone transcription) — later phases.
- YouTube transcript/caption downloads, owned-channel analytics, logged-in
  access, and video-content understanding; ADR 0027 approves only public
  YouTube Data API research metadata, while actual video understanding stays
  with the `/watch` boundary.
- TikTok discovery — no Agentic OS tool provides it; Firecrawl may render a
  public TikTok page as a partial fallback, but no dedicated TikTok connector is
  added.
- Scheduled/unattended acquisition — deferred to Automation OS.

## Consequences

- Reddit and X evidence can carry real engagement metrics, lifting confidence
  above the current secondary-source ceiling and populating `MetricSnapshot`.
- Capability is drop-in: adding a key activates a connector with no code or
  workflow change.
- The exact-approval invariant is now tier-split: strong for generation, key-
  gated standing approval for research acquisition. This is the one intentional
  weakening, bounded by caps and a kill switch and recorded here.
- New optional third-party dependencies (OpenAI, xAI, Firecrawl, Apify) enter
  the tree; each is optional and only imported when its key is present, and each
  is `npm audit`/dependency-reviewed before adoption. Where feasible connectors
  call provider HTTP endpoints via stdlib rather than pulling heavy SDKs.
- Cross-provider dependency (OpenAI/xAI) is accepted for research acquisition
  only; it does not extend to generation.

## Alternatives considered

- Per-run exact approval even with a key present: rejected by the user as too
  much friction for routine research; caps + kill switch give cost safety
  without the prompt.
- Firecrawl-only (one scraper for everything): weaker signal — no native
  Reddit/X engagement metrics, which is the specific gap the loop-exercise hit.
- Wait for a hosted/Automation-OS phase: rejected; the manual loop needs real
  source access now, before scheduled research is worth approving.

## Supersession Note

ADR 0027 adds `youtube_data_api` to the standing-approved research-acquisition
connector set. The same guardrails apply: key presence is standing approval only
for explicit research acquisition runs, bounded by the connector call cap and
kill switch. YouTube Analytics, publishing, scheduled jobs, captions downloads,
and logged-in access remain out of scope.
