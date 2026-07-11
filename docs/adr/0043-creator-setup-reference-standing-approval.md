# ADR 0043: Creator-Setup Reference Standing Approval

## Status

Accepted

## Context

ADR 0023 made every generation call depend on an approved, single-use
GenerationApprovalRecord. Creator Setup later added a separate Visual Continuity
Plan review that already presents and records the exact reusable reference
package. Asking the user to approve that package and then approve the same image
batch again adds friction without adding a new decision.

On 2026-07-10 the operator asked to make Codex image-generation gates less
severe and accepted the recommended two-tier policy: setup references receive a
bounded standing authorization from the approved visual plan; production and
changed work remain exact-approved.

## Decision

1. An approved Visual Continuity Plan grants standing approval for one initial
   generation pass over exactly its listed creator-setup reference assets. No
   second confirmation is required immediately before those calls.
2. The authorization is bounded to one call per listed asset. The provider,
   model, call count, and cost note are surfaced as a notice before execution.
3. The execution layer still creates a reference-scoped, bounded, single-use
   GenerationApprovalRecord derived from the plan approval. Dispatch and
   provenance rules from ADR 0023 remain intact.
4. Any scope change, regeneration, additional variant, later-added asset,
   provider/model change, production content, video, voice, audio, render, or
   upload requires fresh exact call/batch approval.
5. Silence, profile/foundation approval, brand-board approval, or API-key
   presence never substitutes for the approved Visual Continuity Plan.

## Consequences

- Creator Setup has one human visual-package decision instead of two duplicate
  prompts.
- Generation remains human-authorized, bounded, auditable, and single-use.
- `request-generation-approval` may derive the reference-scoped approval record
  from the plan decision without re-prompting.
- Production generation and regeneration retain ADR 0023's exact approval gate.

## Supersedes

This ADR narrowly amends ADR 0023 Decision 1 and Decision 2 for the first pass of
creator-setup reference images only. All other ADR 0023 decisions remain active.
