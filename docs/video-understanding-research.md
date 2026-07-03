# Video Understanding Research

InfluencerOS research should not only read trend articles. It should also inspect real social videos and extract reusable creative patterns.

This workflow is modeled after, and may use, the public MIT-licensed `/watch` workflow from `bradautomates/claude-video`: download or resolve a video, extract sampled frames, obtain captions or a transcript, then analyze what is shown and said with timestamps.

Source reviewed: `https://github.com/bradautomates/claude-video`

## Integration Status

`bradautomates/claude-video` is an approved external research tool for creating Video Understanding Pack evidence.

Do not vendor the `/watch` scripts into this repo yet. Use an installed `watch` skill/plugin, or a local equivalent that follows the same boundary, as an acquisition tool. The canonical InfluencerOS artifact is still `VideoUnderstandingPack`, validated by `schemas/video-understanding-pack.schema.json`.

Do not copy the upstream hook or command surfaces into InfluencerOS. Hooks, cron, hidden automation, and command launchers stay deferred under the Agentic OS parity decisions.

## Research Role

Video understanding belongs inside the Social Research phase.

```text
Creator Profile
  -> Research Brief
  -> candidate video search
  -> Video Understanding Pack
  -> Research Findings
  -> Idea Queue
```

The Video Understanding Pack is evidence. It does not choose the creator's content direction by itself. It helps identify:

- hooks that appear repeatedly,
- first-frame and first-3-second patterns,
- visual structures,
- spoken or captioned framing,
- pacing,
- format and template signals,
- creator-fit opportunities,
- things to avoid.

## External Workflow Shape

For each selected public or local video:

1. Resolve source URL or local path.
2. Download public video when needed.
3. Extract duration-aware sampled frames.
4. Pull native captions when available.
5. Optionally use Whisper fallback when captions are missing and the user has approved/configured that provider path.
6. Analyze frames and transcript together.
7. Store observations as a Video Understanding Pack.
8. Synthesize patterns into Research Findings and Idea Queue updates.

When using `/watch`, pass an explicit output directory under ignored local state, for example:

```bash
/watch <public-url-or-local-path> --out-dir .tmp/watch/<creator-slug>/<research-run-id>/<source-id>
```

Use focused windows for long videos instead of broad sparse scans:

```bash
/watch <public-url-or-local-path> --start 0:00 --end 0:30 --out-dir .tmp/watch/<creator-slug>/<research-run-id>/<source-id>
```

If the installed surface does not expose a slash command, invoke the installed `watch` skill or its bundled script with the same options. Keep downloaded videos, frames, audio snippets, and intermediate transcripts out of tracked source and out of canonical Creator Workspace records unless a downstream workflow explicitly needs a retained source artifact.

## Provider Boundary

Downloading public videos and extracting local frames are local research actions, but they can still be costly or sensitive at scale. Whisper transcription is provider-backed and requires explicit user approval/configuration when used.

InfluencerOS should prefer:

- public URLs or user-provided local files,
- native captions before transcription,
- focused analysis windows for long videos,
- timestamped observations over vague summaries.

Run with Whisper disabled unless the user has approved the exact transcription fallback or has already configured it for this research run. Do not use logged-in platform sessions, private URLs, scraping APIs, cookies, or platform API credentials for v1 video understanding.

Ask before installing global tools, running first-run setup that installs dependencies, or processing a batch of videos. A single public URL or local file can be analyzed as normal research when the required local tools are already available and no provider-backed fallback is used.

## V1 Integration

The v1 adapter contract is:

- `VideoUnderstandingPack` schema,
- example observations,
- installed external `watch` workflow or local equivalent for acquisition,
- optional CLI command later to import `/watch` output,
- later first-party adapter only if repeated usage shows the external skill boundary is too loose.

## Record Mapping

Map `/watch` output into `VideoUnderstandingPack` fields as follows:

| `/watch` evidence | `VideoUnderstandingPack` field |
| --- | --- |
| input URL or local file | `sources[].url_or_path`, `sources[].source_type` |
| video title or filename | `sources[].title` |
| frame sampling mode and focused window | `sources[].analysis_method.frames_sampled`, `focused_range` |
| transcript source | `sources[].analysis_method.transcript_source` (`captions`, `whisper`, `none`, or `unknown`) |
| first few timestamped frames and transcript | `observations.opening_hook`, `first_frame_pattern`, `visual_structure`, `spoken_or_text_framing` |
| repeated structure signals | `observations.template_signals`, `cross_video_patterns` |
| useful but non-copying moves | `observations.replicable_moves` |
| creator mismatch or imitation risks | `observations.avoid_notes`, `creator_fit_findings` |

Store summaries and timestamp-aware observations. Do not store full transcripts or full frame manifests by default.

## Agentic OS Divergence Test

Agentic OS divergence test:

- Proposed change: support an external video-understanding research tool for the existing Video Understanding Pack phase.
- Agentic OS reference: Agentic OS supports modular skills and external services through explicit skill/tool boundaries.
- InfluencerOS decision: adapt the pattern by using `bradautomates/claude-video` only as optional acquisition tooling; canonical records and approval gates stay in InfluencerOS.
- Classification: adaptation.
- Decision record: this file, `skills/influencer-os/SKILL.md`, `docs/provider-boundary.md`, and the Phase 1 progress note.
- Status: pass.
