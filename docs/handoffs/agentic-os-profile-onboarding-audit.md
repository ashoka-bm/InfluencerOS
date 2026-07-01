# Audit: Agentic OS Profile Onboarding Lessons

Date: 2026-06-30
Source handoff: `/private/tmp/agentic-os-profile-onboarding-handoff.md`
External repo reviewed: `/Users/ashokaji/code/External repos/Agentic Academy/agentic-os`

## What Was Reviewed

- `.claude/commands/start-here.md`
- `CLAUDE.md`
- `.claude/skills/mkt-brand-voice/SKILL.md`
- `.claude/skills/mkt-brand-voice/references/voice-profile-template.md`
- `.claude/skills/mkt-brand-voice/references/assets-template.md`
- `.claude/skills/mkt-positioning/SKILL.md`
- `.claude/skills/mkt-positioning/references/positioning-output.md`
- `.claude/skills/mkt-icp/SKILL.md`
- `.claude/skills/mkt-icp/references/icp-template.md`
- `scripts/add-client.sh`
- `scripts/update-clients.sh`
- `docs/multi-client-guide.md`
- generated `brand_context/` examples

## Useful Patterns To Reuse

Agentic OS separates profile material into small execution files:

- `voice-profile.md`: reusable voice system
- `samples.md`: concrete examples
- `positioning.md`: strategic angle
- `icp.md`: audience profile
- `assets.md`: visual identity and asset links

The strongest pattern is token discipline:

- runtime instructions do not load brand files by default;
- skills lazy-load only the context they need;
- sample sentences live outside the main profile;
- inferred sections are marked as draft or confidence-limited;
- templates require every canonical section, even when values are unknown;
- update mode avoids rebuilding existing foundations silently.

## Main Agentic OS Gap

The handoff's client onboarding issue is real.

`scripts/add-client.sh` copies skills, settings, hooks, scripts, and cron templates, but does not copy `.claude/commands/`. The generated client `CLAUDE.md` imports only local `AGENTS.md`; it does not mirror root runtime startup behavior. The docs say a client automatically walks through brand foundation setup, but the generated workspace may not have the command/runtime machinery needed for `/start-here`.

If fixing Agentic OS directly, likely changes are:

- copy `.claude/commands/` in `add-client.sh`;
- sync `.claude/commands/` in `update-clients.sh`;
- add a client creation regression test;
- make client startup behavior write to client-local `brand_context/`, not root.

## InfluencerOS Changes Made From This Audit

InfluencerOS should follow the same small-file discipline, adapted to creators:

- `identity.md`: durable public continuity and recurring world
- `soul.md`: psychology, values, belief matrix, emotional logic
- `personal-brand.md`: content strategy, surfaces, pillars, monetization, boundaries
- `voice-samples.md`: concrete examples, now separate from identity
- `creator-profile.json`: compact operational summary
- `references/reference-library.json`: real and planned reference assets

Added token-efficiency improvements:

- runtime capsule sections at the top of identity, soul, and personal brand templates;
- source status, confidence, foundation acceptance, and blocker fields;
- `voice-samples.md` as a canonical file;
- `create-voice-samples` as a dedicated subskill;
- schema and scaffold support for `voice-samples.md`.

## Remaining Recommendation

Keep the rich master intake, such as `adira.md`, as archived source material. Do not make it the maintained runtime artifact. The maintained workspace should be a small set of focused files, each loaded only when the current task needs that dimension.
