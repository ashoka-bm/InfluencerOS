# ADR 0013: Creator Setup Readiness And Reference Asset Lifecycle

## Status

Accepted

## Context

Creator Setup can begin from minimal input, a guided interview, a master breakdown, user-provided files, media references, or a request to generate a persona. That flexibility is useful, but downstream research, planning, and generation need a stricter foundation.

Different creator strategies also require different blockers. A text-first creator may need a strong identity, soul file, and brand context, while a video creator needs visual continuity references. Voiceover work needs voice material or an accepted voice style note.

The existing Creator Profile and Reference Library schemas did not explicitly model content strategy, readiness levels, or planned reference assets.

## Decision

Creator Setup will be permissive at intake and strict at readiness.

The Creator Profile will include a structured `content_strategy` summary. `brand_context/personal-brand.md` remains the richer source of truth for strategy, while `creator-profile.json` stores the operational summary needed for research and planning.

Creator Workspace readiness uses these statuses:

- `draft`
- `foundation_review`
- `content_ready`
- `generation_ready`
- `active`
- `archived`

Readiness blockers are medium-based. Text-first creators need completed identity, soul, and brand context. Image and video creators also need visual reference requirements. Voiceover creators need voice references or accepted voice style guidance.

Reference Library assets may represent real or planned assets. Each asset has an `asset_status` so agents can distinguish planned, prompted, user-provided, generated, approved, and retired assets.

Provider-neutral prompts for planned reference assets live in separate markdown files under `references/`, and `reference-library.json` may point to them with `prompt_path`.

Creator Setup is exposed as a conductor skill, `create-influencer`, with clear inputs and outputs. It coordinates identity, soul, personal brand, operational profile, reference planning, provider-neutral prompts, setup checklist, and approval gates.

A generated persona becomes acceptable as one foundation only after the user approves the whole generated foundation. Agents do not need separate approval for each file unless the user asks for that stricter review.

## Consequences

- Setup can support broad creator strategies, including text-first surfaces such as Substack and LinkedIn.
- Research can use content strategy to target the right topics, formats, and surfaces.
- Agents can identify which blockers apply to text, image, video, audio, carousel, and story-sequence workflows.
- Provider-neutral prompts can be tracked before generated files exist.
- The onboarding flow can be tested as a self-contained module with a stable input and output contract.
- Provider-backed generation remains human-gated. ADR 0043 later made an
  approved Visual Continuity Plan the authorization for one initial bounded
  setup-reference pass; other calls retain exact approval.
