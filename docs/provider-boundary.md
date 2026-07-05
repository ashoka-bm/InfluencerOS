# Provider Boundary

InfluencerOS is dry-run-first.

Allowed without approval:

- creator-profile review,
- public research,
- inspecting public or user-provided local videos with local frame extraction,
- extracting native captions from public video sources,
- research summaries,
- content ideas,
- micro-journey plans,
- shot lists,
- provider-neutral prompts,
- base generation plans.

Requires explicit user approval:

- image generation,
- video generation,
- render jobs,
- audio generation,
- Whisper or other API-backed transcription fallback for video understanding,
- external uploads,
- paid provider calls,
- bulk generation batches.

Approval must name the exact call or batch. A general desire to create content is not generation approval.

## Research-acquisition connectors (ADR 0022)

One bounded carve-out to the "paid provider calls require exact approval" rule
above: the four key-gated research-acquisition connectors (`reddit_openai`,
`x_xai`, `firecrawl_web`, `linkedin_apify`) are **standing-approved by API-key
presence** — no per-run prompt. This covers research acquisition only. It is
bounded by a per-run call cap (`INFLUENCER_OS_CONNECTOR_MAX_CALLS`) and a kill
switch (`INFLUENCER_OS_DISABLE_PAID_CONNECTORS=1`), and does not weaken any of
the generation approvals above (image, video, render, audio, transcription
fallback, uploads, bulk batches), which still require exact per-call/batch
approval. A connector with no key is simply unavailable and the run falls back
to built-in public `WebSearch`/`WebFetch`.

`bradautomates/claude-video` `/watch` is allowed as an external video-understanding research tool only within this boundary. It may use `yt-dlp` and `ffmpeg` locally for public URLs or user-provided local files. It must not use logged-in platform sessions, private URLs, scraping APIs, cookies, or platform API credentials in v1. Ask before first-run setup that installs tools or before processing a video batch.
