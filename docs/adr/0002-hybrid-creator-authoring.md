# ADR 0002: Hybrid Creator Authoring

## Status

Accepted

## Context

Creator identity can begin as a rich breakdown, brief, or interview transcript. Examples include long-form influencer breakdowns that combine niche, audience, biography, psychology, visual identity, content boundaries, platform posture, and monetization rules.

That format is useful for creation, but it is too large and ambiguous to serve as the only operational source of truth. InfluencerOS also needs a typed `creator-profile.json` for automation and focused markdown files for human review.

## Decision

InfluencerOS will use hybrid creator authoring.

An initial master intake may be pasted, imported, or drafted as a rich creator breakdown. InfluencerOS then derives draft creator workspace files:

- `creator-profile.json`
- `context/SOUL.md`
- `context/USER.md`
- `context/MEMORY.md`
- `brand_context/identity.md`
- `brand_context/soul.md`
- `brand_context/personal-brand.md`
- reference library requirements

After review, the split workspace files become the maintained source of truth. The original intake may remain as an archived source artifact, but future workflows should read the current workspace files rather than reinterpreting the original breakdown every time.

## Consequences

- Rich creative briefs can be used without forcing every detail into a schema.
- Automation gets a stable typed Creator Profile.
- Human-facing identity, psychology, and brand docs stay readable and editable.
- The system can compare future content against focused files instead of searching one oversized source document.
- Import tooling should preserve provenance by recording the source intake path, date, and extraction notes.
