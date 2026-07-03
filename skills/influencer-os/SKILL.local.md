# influencer-os — OS Persona Local Override

Worked `SKILL.local.md` example (ADR 0014, ADR 0016). Scope: first-party InfluencerOS persona work only — content planned for InfluencerOS's own channels. Load order: the base `SKILL.md` loads first, then this file; local rules override base rules for this scope only. Creator-specific overrides live in each Creator Workspace at `.claude/skills/influencer-os/SKILL.local.md`, never here.

## Local Rules

- 2026-07-03: When the creator is the InfluencerOS first-party persona, read root `context/` and `brand_context/` (ADR 0014) instead of a Creator Workspace, and never scaffold a workspace for it.
- 2026-07-03: First-party content ideas may reference the OS roadmap, but never expose private creator data or Creator Workspace contents.

## Promotion

Promote a local rule into the base `SKILL.md` `## Rules` only when repeated feedback shows it applies system-wide; log the promotion via `python3 -m influencer_os log-learning context/learnings.md influencer-os "<what was promoted and why>"`.
