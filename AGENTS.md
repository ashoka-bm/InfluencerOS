# InfluencerOS Agent Rules

These rules apply to agents building or running InfluencerOS.

## Source Of Truth

Read `CONTEXT.md` before changing product language.

Use these product docs as durable references:

- `ARCHITECTURE.md`
- `docs/pipeline-contract.md`
- `docs/provider-boundary.md`
- `skills/influencer-os/SKILL.md`
- `schemas/`

## Product Invariant

Every Content Idea, Micro-Journey Video Plan, Base Video Generation Plan, and Output Record must trace back to:

- Creator Profile,
- current Social Research Pack evidence,
- the chosen Content Idea,
- the Applied Social Template when one is used,
- the intended audience response,
- the Micro-Journey Video Plan,
- the Base Video Generation Plan when generation is planned,
- and the Output Record when an Output Artifact exists.

## Operating Rules

- InfluencerOS v1 targets universal short-form vertical video. Do not add platform-specific adapters, post-production treatments, publishing, scheduling, or analytics unless explicitly requested.
- Audience and niche are creator-profile inputs. Do not invent or redefine them unless the user asks.
- Research is time-sensitive. Date the research, cite sources, and keep trend claims tied to evidence.
- Do not make provider-backed image, video, audio, or render calls without explicit user approval for the exact call or approved batch.
- Drafting research packs, ideas, plans, prompts, shot lists, and generation plans is allowed without provider approval.
- Do not commit user-provided media, generated works, private creator references, secrets, or API keys.
- Prefer the smallest change that advances the first slice.

## Git Rules

- Do not commit unless the user asks.
- Prefer branch prefixes `feature/`, `fix/`, `chore/`, or `refactor/`.
- Never force-push a shared branch without explicit approval.
