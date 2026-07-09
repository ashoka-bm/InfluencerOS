# Multi-Entity Onboarding Implementation Plan (ADR 0026)

Last updated: 2026-07-07

Status: **Drafted, awaiting operator go-ahead to execute.** Decision recorded in
`docs/adr/0026-multi-entity-onboarding.md`; scope entered on the roadmap
Post-Phase-4 section. No code has been written.

## Goal

Let the OS onboard products and brands, not only avatar-led influencers, by
adding a required `creator_type` discriminator (`influencer | product | brand`)
that conditions which foundation documents and profile fields are required.
"Creator" is the umbrella term; the `creator_*` ID plumbing and downstream
schemas stay unchanged.

## Non-negotiable guardrails

- The influencer path stays green throughout: no regression to the working
  setup flow, the readiness gates, or the full test suite. `creator_type`
  defaults to `influencer`, so every existing fixture keeps validating.
- No global rename (Creator → Subject). Deferred as an optional cosmetic pass.
- No downstream schema changes in this workstream. Research/ideas/generation/
  analytics are entity-agnostic and untouched.
- Nothing touches `influencer_os/providers/` or any approval gate.

## Design

### Discriminator

Add `creator_type` to `creator-profile.schema.json`: `enum ["influencer",
"product", "brand"]`, required, default `influencer`. Mirror it onto
`creator-workspace.json` if the workspace scaffold needs it before the profile
exists.

### Conditional requirements (extend the ADR 0013 mechanism)

The medium-based blockers already condition required assets on
`content_mediums` via lookup tables (`MEDIUM_REQUIRED_ASSET_KINDS`,
`PRIMARY_REF_REQUIRED_BY_MEDIUM`) plus the status-gated `_validate_readiness_gates`
in `influencer_os/creator_workspaces.py`. Add a parallel type dimension:

- `TYPE_REQUIRED_FOUNDATION_DOCS: {influencer: (...), brand: (...), product: (...)}`
- `TYPE_REQUIRED_PROFILE_FIELDS: {influencer: (persona_summary, voice, visual_identity_summary), brand: (...), product: (...)}`

Persona fields (`persona_summary`, `voice`, `visual_identity_summary`) become
**schema-optional** and are required by the validator only for `influencer`.
`file_refs` / `canonical_files` stop being one fixed `const` set — the required
doc set is resolved from `creator_type`. Because the hand-rolled validator has
no `if/then`, this conditioning lives in Python at readiness, matching the
existing blocker precedent. (Optional future hardening: a `oneOf` discriminated
union keyed on `creator_type` for at-rest strictness.)

### Per-type foundation sets

Shared spine (all types): content strategy, audience/market, boundaries, goals,
voice/tone, positioning.

| Type | Foundation docs | Persona fields | Reference assets |
|---|---|---|---|
| influencer | identity.md, soul.md, personal-brand.md, voice-samples.md | persona_summary, voice, visual_identity_summary | character, wardrobe, camera, locations |
| brand | brand-brief.md, brand-guidelines.md, brand-voice.md | none required | logo lockups, brand style, key visuals |
| product | offering.md + inherited brand context (positioning, guidelines, voice) | none required | product shots, packaging |

`create-identity` and `create-soul` run for `influencer` only.

### Product ↔ brand relationship

`product` may carry an advisory `parent_brand_ref`. In v1 the parent brand's
context is kept **inline** in the product workspace (no cross-workspace
resolution); `parent_brand_ref` is metadata only. Cross-workspace brand
inheritance is a later decision.

## Slices (build order)

1. **Discriminator + optionality.** Add `creator_type` (default `influencer`);
   make persona fields schema-optional; validator defaults untyped fixtures to
   `influencer`. Acceptance: every existing fixture still validates; a profile
   with no `creator_type` is treated as `influencer`; a bad enum value fails.
2. **Type-conditional foundation + readiness enforcement.** Add the per-type
   required tables and enforce them in `_validate_readiness_gates`. Acceptance:
   a `brand`/`product` workspace missing its type-specific docs fails at
   `content_ready`+; an `influencer` still requires identity/soul; a `brand`
   does not require soul/identity/persona fields.
3. **Type-aware setup conductor + subskills.** `create-influencer` becomes a
   type router; add `create-brand-brief`, `create-brand-guidelines`,
   `create-brand-voice`, `create-offering` subskills; register them and add
   context-matrix rows. Acceptance: registry/context drift checks pass; the
   conductor halts if a type-required subskill is missing.
4. **`parent_brand_ref` + fixtures.** Add the advisory product field; add one
   brand fixture and one product fixture that validate and can reach an Output
   Package through the unchanged pipeline. Acceptance: brand and product
   fixtures pass `validate workspace`; a product's `parent_brand_ref` is
   advisory (absent is fine).

## Open questions for the operator

- Naming of the brand/product foundation docs (brand-brief vs brand-strategy;
  offering vs product-brief) — cosmetic, easy to lock at slice 3.
- Whether a `brand` that fronts a spokesperson/persona should be able to opt
  into the influencer persona docs (a `brand` + optional persona overlay) or
  stay strictly non-persona in v1. Recommendation: strictly non-persona in v1;
  add an overlay later only if a real onboarding needs it.
