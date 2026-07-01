# ADR 0007: Output Package Platform Adaptations

## Status

Accepted

## Context

InfluencerOS v1 has a universal short-form bias: create content that can travel across TikTok, Instagram Reels, and YouTube Shorts without becoming platform-locked too early.

The Learning OS still needs platform context. Packaging and performance differ by surface: YouTube Shorts may care more about title and thumbnail behavior, while TikTok and Instagram may expose stronger first-frame, caption, retention, save, and share signals.

## Decision

Output Packages will use a universal core with optional platform adaptations.

The universal core contains the platform-neutral concept, source refs, final assets, caption or description base, title base when relevant, Creative Performance Map, provenance, and upload-ready materials.

Platform adaptations may add or override platform-specific fields such as:

- platform,
- platform format,
- title,
- caption or description,
- thumbnail or first-frame asset,
- hashtags or tags,
- posting-time recommendation,
- platform-specific CTA,
- platform-specific asset crop or duration,
- platform-specific Creative Performance Map variants.

Platform-native package records are deferred unless a future workflow needs a platform-specific artifact that cannot reasonably be represented as an adaptation.

## Consequences

- Planning remains reusable across platforms.
- Publishing and analytics retain enough platform-specific context.
- Cross-platform performance comparisons can still connect back to one core creative idea.
- Platform-specific work can be added incrementally without breaking the universal v1 pipeline.
