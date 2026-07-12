# ADR 0045: Avatar Image Auto-Generation

## Status

Accepted (operator decision, grilled and human-approved 2026-07-11/12)

## Context

The operating cadence model makes Stage 1 (Creator Setup) a run-once block:
text foundation -> brand foundation -> auto-generated Avatar Image -> Setup
Review (an advisory bounded sub-agent that judges the text foundation and the
avatar together) -> fixes -> human Visual Continuity Plan approval -> remaining
reference-asset generation -> ready check (workspace validation plus the human
`foundation_ready` flip). The Avatar Image glossary term is
committed in `CONTEXT.md`: the one platform-facing identity image every
creator must have, regardless of Representation Model.

ADR 0043 authorizes the creator-setup reference pass only after the human
approves the Visual Continuity Plan. Under that rule no avatar can exist when
the Setup Review runs or when the human decides on the plan, so the reviewer
and the human would judge a described image instead of a rendered one, and
text-first creators would never get an identity image at all. ADR 0042's
anticipation policy separately hard-limits anticipation: "provider-backed
generation calls are never anticipated."

## Decision

1. Every creator gets one Avatar Image regardless of Representation Model.
   When the user has not provided one, Creator Setup auto-generates it with
   no human pre-approval.
2. The intake interview decides what the avatar depicts — a persona face or a
   non-face mark — for text-first creators.
3. Execution still writes a bounded, single-use, system-derived
   GenerationApprovalRecord for the auto-generated avatar. In the shipped
   record contract this is a `batch`-scope record with `max_calls: 1`
   ("single-use" in the plain sense; `single_call` scope forbids `max_calls`),
   carrying a new system-derived `approval_basis` value. Dispatch and
   provenance rules from ADR 0023 remain intact; only the human pre-approval
   on this one record is removed.
4. The human accepts or rejects the avatar at Visual Continuity Plan
   approval. This rides the existing human decision; no new blocking gate is
   added.
5. Rejection and regeneration follow normal exact approval: a fresh exact
   call/batch approval per ADR 0023 for every subsequent avatar generation.
6. The approved Visual Continuity Plan authorizes the remaining
   reference-asset pass, as in ADR 0043.
7. For synthetic and avatar-led creators the Avatar Image doubles as the
   visual-continuity calibration reference for the setup image pass.
8. The Creator Setup ready check that closes Stage 1 is workspace validation
   plus the human `foundation_ready` flip: deterministic validation gathers
   the blockers, and the human decides the milestone. This block-exit decision
   is a readiness decision, not a pipeline Gate.

## Consequences

- The Setup Review judges the text foundation and a rendered avatar together,
  and the human decides on a real image at Visual Continuity Plan approval
  instead of a description.
- Exactly one provider-backed call per creator may run without human
  pre-approval; it stays bounded, recorded, single-use, and auditable through
  its system-derived GenerationApprovalRecord.
- The gate inventory is unchanged: Concept Approval and the Provider Boundary
  remain the only blocking gates, and avatar rejection/regeneration returns to
  the exact-approval path.
- Text-first creators gain a platform-facing identity image whose depiction
  they controlled at intake.
- Shipped contracts change to admit the system-derived record:
  `schemas/generation-approval-record.schema.json` gains a system-derived
  `approval_basis` value; the `influencer_os/validation.py` invariant that
  approved/executing/executed records carry a verbatim
  `user_approval_statement` and `approved_at` is relaxed for that basis only
  (every other basis keeps the fail-closed rule); and the
  `influencer_os/generation.py` derived-approval path no longer requires an
  approved Visual Continuity Plan for this one avatar record, since the
  avatar call precedes that approval.
- Canonical control docs change to carry the carve-out:
  `docs/gates-and-reviews.md` (the Provider Boundary definition and control-
  order step "Provider Boundary before any generation call"),
  `docs/pipeline-contract.md` Gate Rules and `docs/provider-boundary.md`
  (repoint their ADR 0043 citations to this ADR), the `AGENTS.md`
  provider-approval operating rule (cite this ADR and name the avatar
  carve-out), and the CONTEXT.md Provider Boundary and Gate entries.

## Supersedes

This ADR supersedes ADR 0043 as the current creator-setup image authorization
record. It carries ADR 0043's bounded standing authorization forward for the
remaining reference assets listed in the approved Visual Continuity Plan and
narrowly amends it by moving the Avatar Image's first generation ahead of that
approval. It also narrowly amends ADR 0023 Decisions 1 and 2 (the avatar's
first GenerationApprovalRecord is system-derived, with no human pre-approval
and no `user_approval_statement`) and ADR 0042's anticipation-policy hard
limit ("provider-backed generation calls are never anticipated") for this one
bounded call only. All other ADR 0023, ADR 0042, and ADR 0043 decisions remain
active.
