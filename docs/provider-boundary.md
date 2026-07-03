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

`bradautomates/claude-video` `/watch` is allowed as an external video-understanding research tool only within this boundary. It may use `yt-dlp` and `ffmpeg` locally for public URLs or user-provided local files. It must not use logged-in platform sessions, private URLs, scraping APIs, cookies, or platform API credentials in v1. Ask before first-run setup that installs tools or before processing a video batch.
