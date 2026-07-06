"""Generation provider boundary (ADR 0023, Phase 3).

The sibling of the ADR 0022 research-connector tier, under the opposite
approval model: every generation provider is `approval_model: exact_approval`
— key presence is never approval — and the only dispatch entry point requires
an approved GenerationApprovalRecord id as a positional argument, so the
no-approval-no-call rule is enforced by shape, not convention.
"""
