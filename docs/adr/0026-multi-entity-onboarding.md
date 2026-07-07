# ADR 0026: Multi-Entity Onboarding (Influencer, Product, Brand)

## Status

Accepted (operator-approved 2026-07-07).

## Context

InfluencerOS was scoped to avatar-led creators. The PRD problem statement reads
"avatar-led creator content planning," and `CONTEXT.md` defines Creator as "the
avatar, influencer, persona, or account identity." The operator now wants to
onboard **products** and **brands** as well, so the OS can produce marketing
material for offerings and companies, not only persona-led accounts.

Products and brands need different foundation documents than an avatar persona.
An entity-assumption audit (2026-07-07) found the persona assumption baked in at
three depths:

1. **Schema-required persona fields** — `creator-profile.schema.json` requires
   `persona_summary` (archetype, traits, behavioral tells), `voice` (cadence,
   signature phrases), and `visual_identity_summary` (with mandatory
   `wardrobe_constants`, `camera_style`, `recurring_locations` minItems:1). A
   product cannot satisfy these without fabricating a wardrobe and psychology.
2. **Four hard-coded foundation docs** — `identity.md` (lore), `soul.md`
   (psychology), `personal-brand.md`, `voice-samples.md` are `const` values in
   both `creator-profile.schema.json` (`file_refs`) and
   `creator-workspace.schema.json` (`canonical_files`).
3. **41 of ~50 schemas pinned to `creator_profile_id` / `creator_slug`** — the
   entire research → ideas → project → generation → analytics chain threads
   this ID. This is entity-agnostic plumbing: a product also has an ID,
   research, ideas, and projects.

There is no entity-type discriminator today (only an unused interview question).
The relevant precedent is the **medium-based blocker** system (ADR 0013): it
conditions *which foundation docs are required* on a declared property (content
modality) via a per-property required-doc table plus a status-gated readiness
validator in `influencer_os/creator_workspaces.py`.

Broadening scope toward products/brands moves **toward** the Agentic OS
reference, which serves generic clients; InfluencerOS had narrowed that
"client" to "creator/avatar" (ADR 0001). The divergence is therefore mild, but
it touches entity architecture and the PRD's stated non-goal ("without drifting
into a generic content tool"), so it requires this ADR under the divergence
test.

## Decision

**1. "Creator" becomes the umbrella term.** A Creator is any onboarded marketing
subject: an avatar-led **influencer**, a **product**, or a **brand**/company.
The `creator_*` ID vocabulary, the `workspace-library/creators/<slug>/` path,
the CLI command names, and all 41 downstream schemas stay unchanged. A global
rename (Creator → Subject/Account) is explicitly **out of scope** and deferred
as an optional, purely cosmetic pass; the risk of renaming across 41 schema ID
fields and the 739-test pipeline is not justified by the naming gain.

**2. Add a required `creator_type` discriminator** to `creator-profile.json`:
enum `["influencer", "product", "brand"]`. It defaults to `influencer` for
back-compat with existing fixtures.

**3. Foundation-document and persona-field requirements become conditional on
`creator_type`,** enforced with the ADR 0013 mechanism — a per-type required
table plus the status-gated readiness validator — **not** a schema `if/then`
(the hand-rolled validator has no `if/then`). The persona fields
(`persona_summary`, persona `voice`, `visual_identity_summary`) become
schema-optional and are required by the validator only for `influencer`.
`canonical_files` / `file_refs` stop being one fixed const set and vary by type.

**4. Per-type foundation sets:**

- **influencer** (unchanged): `identity.md` (lore), `soul.md` (psychology),
  `personal-brand.md`, `voice-samples.md`; the persona/voice/visual-identity
  profile fields; avatar visual-continuity reference assets (character,
  wardrobe, camera, locations).
- **brand** (company/organization): `brand-brief.md` (mission, category,
  positioning, value proposition, market and competitors), `brand-guidelines.md`
  (logo, palette, typography, visual system, imagery rules), `brand-voice.md`
  (voice and tone — the brand analog of `voice-samples.md`). No `identity.md` or
  `soul.md`. Brand visual reference assets (logo lockups, brand style, key
  visuals). `personal-brand.md` is superseded by `brand-brief.md` for this type.
- **product** (a specific offering): `offering.md` (features, benefits, USPs,
  use cases, pricing tier, proof points) plus inherited brand context
  (positioning, guidelines, voice) and product visual reference assets (product
  shots, packaging). An optional `parent_brand_ref` may name a brand-type
  profile; for this ADR the parent brand's context is kept **inline** in the
  product workspace (no cross-workspace resolution), with `parent_brand_ref` as
  advisory metadata. Cross-workspace brand inheritance is a later decision.

**5. The shared spine (required for all three types):** content strategy
(primary surfaces, content mediums, in-scope formats, pillars), audience/market,
content boundaries, goals, voice/tone, positioning.

**6. The downstream pipeline runs unchanged.** Research, ideas, promotion,
production plans, generation, packaging, and analytics are entity-agnostic.
Skills interpret `creator_fit` as fit-to-subject and `niche` / `target_audience`
as category / market for product and brand types. No downstream schema changes
are made in this ADR. A follow-up ADR may add product/market research vocabulary
if the influencer-shaped field names prove too persona-specific against real
runs.

**7. Phasing.** The influencer path is unchanged and remains fully usable now;
real influencer onboarding proceeds immediately. Product/brand support ships as
a build slice (see the multi-entity onboarding implementation plan).

## Consequences

- Products and brands can be onboarded without faking persona psychology,
  wardrobe, or lore.
- The 739-test pipeline and the 41-schema `creator_*` ID plumbing stay intact;
  risk is contained to the setup path (profile schema, foundation-doc set, setup
  skills) and the readiness validator.
- The setup conductor `create-influencer` becomes type-aware (a router over
  type-specific foundation subskills); new subskills produce brand/product
  foundation docs. `create-identity` and `create-soul` run for influencers only.
- Type-conditional required docs are enforced in Python at readiness rather than
  at rest by schema `if/then`, so schema-level strictness is weaker for the
  conditional fields; mitigated by extending the readiness validator and drift
  checks. Optional future hardening: a `oneOf` discriminated union keyed on
  `creator_type` in the profile schema.
- The product name "InfluencerOS" and the `creator_*` vocabulary are now
  umbrella terms spanning influencers, products, and brands. A cosmetic rename
  stays deferred.
- `CONTEXT.md`, the PRD scope, the roadmap, and progress are updated to reflect
  multi-entity scope.
