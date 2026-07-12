# Provider Boundary

InfluencerOS is planning-first and local-first.

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
- human-in-the-loop ElevenLabs Voice Design prompt files,
- base generation plans.

Requires explicit user approval:

- image generation,
- video generation,
- render jobs,
- audio generation,
- voice generation or saving a generated voice in ElevenLabs,
- Whisper or other API-backed transcription fallback for video understanding,
- external uploads,
- paid provider calls,
- bulk generation batches.

Approval normally names the exact call or batch. A general desire to create
content is not generation approval.

## Creator-setup reference standing approval (ADR 0043, superseded by ADR 0045)

ADR 0045 supersedes ADR 0043 as the current creator-setup image authorization
record. It adds one earlier bounded call: setup auto-generates the Avatar Image
before Visual Continuity Plan approval under a bounded, single-use,
system-derived GenerationApprovalRecord (`max_calls: 1`), with no human
pre-approval; avatar rejection or regeneration returns to exact approval.

The standing authorization carries forward: an approved Visual Continuity Plan
grants standing approval for **one initial generation pass** over exactly its
listed remaining creator-setup reference assets, with **no second
confirmation** immediately before generation. This includes the approved
brand-board reference package. The execution layer still writes a bounded
GenerationApprovalRecord derived from the plan approval so provenance and
single-use dispatch remain intact.

The authorization is bounded to one call per asset. It does not cover a scope
change, regeneration, additional variants, production content, video, voice,
audio, render, upload, a different provider/model than the configured setup
route, or assets added after plan approval. Those actions require a fresh exact
call/batch approval. Before dispatch, surface the provider, model, call count,
and cost note as a notice; do not turn that notice into a second approval prompt
when the package remains inside the approved plan.

## Generation provider registry (ADR 0023)

Generation providers are registered in `influencer_os/providers/registry.py`
and listed by `python3 -m influencer_os list-providers`. Every row is
structurally `approval_model: exact_approval` — the registry fails closed at
import if a row disagrees — and key presence makes a provider *available*,
never *approved*. The dispatch entry points (`dispatch_generation` for projects
and `dispatch_reference_generation` for creator setup) require an approved
GenerationApprovalRecord id as a positional argument, so no code path can
reach an adapter without a recorded human approval. For creator-setup reference
assets, ADR 0043 (carried forward by ADR 0045) allows that record to derive
from the approved Visual Continuity Plan instead of asking for a second
confirmation, and ADR 0045's Avatar Image record is system-derived ahead of
that approval. The
`INFLUENCER_OS_DISABLE_PAID_CONNECTORS` kill switch disables generation
dispatch entirely, even with an approved record.

The setup runtime is explicit and auditable: run
`derive-setup-reference-approvals` with the provider, model, and cost notice,
then consume each emitted record with `dispatch-reference-generation`. The
record freezes the approved plan plus that routing scope and is single-use.
Legacy workspaces can be upgraded idempotently with
`migrate-visual-foundation` before validation.

Per ADR 0023 Decision 3, the only registered adapter is the deterministic
`mock` test double; the first real (paid) provider adapter is chosen
explicitly by the operator and lands as its own approved batch.

## Research-acquisition connectors (ADR 0022)

One bounded carve-out to the "paid provider calls require exact approval" rule
above: the key-gated research-acquisition connectors registered in
`influencer_os/connectors/registry.py` are **standing-approved by API-key
presence** — no per-run prompt. This covers research acquisition only. It is
bounded by a per-run call cap (`INFLUENCER_OS_CONNECTOR_MAX_CALLS`) and a kill
switch (`INFLUENCER_OS_DISABLE_PAID_CONNECTORS=1`), and does not weaken any of
the generation approvals above (image, video, render, audio, transcription
fallback, uploads, bulk batches), which still require exact per-call/batch
approval except for the creator-setup carve-outs (ADR 0043's one-pass
approved-plan references and ADR 0045's system-derived Avatar Image call). A
connector with no key is simply unavailable and the run falls back
to built-in public `WebSearch`/`WebFetch`.

`bradautomates/claude-video` `/watch` is allowed as an external video-understanding research tool only within this boundary. It may use `yt-dlp` and `ffmpeg` locally for public URLs or user-provided local files. It must not use logged-in platform sessions, private URLs, scraping APIs, cookies, or platform API credentials in v1. Ask before first-run setup that installs tools or before processing a video batch.
