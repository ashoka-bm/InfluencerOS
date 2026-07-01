# Video Understanding Research

InfluencerOS research should not only read trend articles. It should also inspect real social videos and extract reusable creative patterns.

This workflow is modeled after the public MIT-licensed `/watch` workflow from `bradautomates/claude-video`: download or resolve a video, extract sampled frames, obtain captions or a transcript, then analyze what is shown and said with timestamps.

Source reviewed: `https://github.com/bradautomates/claude-video`

## Research Role

Video understanding belongs inside the Social Research phase.

```text
Creator Profile
  -> Research Brief
  -> candidate video search
  -> Video Understanding Pack
  -> Social Research Pack
  -> Content Idea Set
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
8. Synthesize patterns into the Social Research Pack.

## Provider Boundary

Downloading public videos and extracting local frames are local research actions, but they can still be costly or sensitive at scale. Whisper transcription is provider-backed and requires explicit user approval/configuration when used.

InfluencerOS should prefer:

- public URLs or user-provided local files,
- native captions before transcription,
- focused analysis windows for long videos,
- timestamped observations over vague summaries.

## V1 Integration

Do not vendor the `/watch` scripts yet. Start with an adapter contract:

- `VideoUnderstandingPack` schema,
- example observations,
- optional CLI command later to import `/watch` output,
- later adapter to call an installed `/watch` workflow or local equivalent.

