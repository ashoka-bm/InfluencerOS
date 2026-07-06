---
name: import-generated-asset
description: Use when media generated outside InfluencerOS (a provider web UI export, a user-supplied file) needs to enter a Project or the Reference Library with full provenance. Wraps the import-generated-asset CLI; captures origin, tool, and license honestly — an unknown license is recorded as a warning, never guessed.
---

# Import Generated Asset

You wrap `python3 -m influencer_os import-generated-asset` (ADR 0023
slice 3). Every imported file gets a `generation/asset-manifest.json` row —
or, on the reference route, an updated Reference Library source block — so
provenance never depends on memory.

## Project Imports

```bash
python3 -m influencer_os import-generated-asset \
  <creator-workspace>/projects/<project-slug> <local-file> \
  --asset-id gen_asset_<...> --asset-kind image|video|audio|render \
  --origin imported|user_provided \
  --source "<where this came from>" --tool "<tool/provider if known>" \
  --license "<usage rights if known>" [--creator ...] [--attribution ...] \
  [--warning "<provenance caveat>"] [--notes ...]
```

- Ask the operator where the file came from and what rights apply; record
  their answers verbatim. If the license is unknown, say so and let the CLI
  record the `license-unknown` warning — never invent rights.
- `origin: imported` = made by an external tool/provider;
  `origin: user_provided` = the operator's own media. Generated-by-dispatch
  assets never come through this path.

## Reference Library Imports

```bash
python3 -m influencer_os import-generated-asset <creator-workspace> <local-file> \
  --reference-asset asset_<...> [--origin imported|user_provided] \
  [--approval-record gen_approval_<...>]
```

The file lands at the asset's declared `path`, and its `asset_status` and
`source` block update per ADR 0013. Cite `--approval-record` when a recorded
generation approval authorized the asset's creation.

## Validation

```bash
python3 -m influencer_os validate project <creator-workspace>/projects/<project-slug>
python3 -m influencer_os validate workspace <creator-workspace>
```

## Boundaries

- Never call a provider; this path is for media that already exists.
- Never commit imported media (`workspace-library/` stays untracked).
- Quality review still gates packaging: imported media needs a passing
  QualityReview before it can ship in an Output Package.

## Self-Update

When corrected twice the same way, record the lesson via
`python3 -m influencer_os log-learning context/learnings.md import-generated-asset "<lesson>"`.
