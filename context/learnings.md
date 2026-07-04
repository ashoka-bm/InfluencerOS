# InfluencerOS Process Learnings

This file stores system-level process and skill learnings for building InfluencerOS.

Creator performance learnings belong in Creator Workspaces, not here.

## General

- Keep Agentic OS copy/adaptation decisions visible before implementing deeper architecture.

## Individual Skills

### influencer-os

- Pending repeated feedback.
- 2026-07-03: Use bradautomates/claude-video /watch as optional external acquisition for Video Understanding Packs; keep Whisper, first-run installs, and batches behind approval, and do not add it to dependencies.

### create-influencer

- Pending repeated feedback.
- 2026-07-03: Nia Sol run review: stale no-generation notes survived an approved generation call; the skill now requires superseding checklist/MEMORY/daily-note claims in the same run as any generation.
- 2026-07-03: Nia Sol run review: checklist grouped wording (completed or prompted) hid which assets existed; scaffold and skill now track per-asset lifecycle status, and generated assets record date/tool/deviations in usage_notes.

### wrap-up

- 2026-07-03: Batch D built the self-improvement loop: log-learning and memory-write CLIs are the deterministic writers behind the wrap-up and memory-write skills.
- 2026-07-03: Phase 0C closed via batches A-G; the exit-criteria run is the wrap-up verification pattern: suite, examples, drift checks, full workflow, stale-path check.

### create-personal-brand
- 2026-07-03: Personal-brand setup owns ICP-grade audience operating signals; keep them in personal-brand.md rather than expanding creator-profile.json.

### create-research-findings
- 2026-07-03: Live research eval showed a need for source-yield learning: after Phase 1 slices 6-7, add the merged research-intelligence hardening slice that tracks searched-but-unused sources, downgrades repeated background-only/low-yield sources in research intelligence, and lands before scheduled research automation.

### create-production-plan
- 2026-07-04: Phase 1 slice 6 established one Project per content unit: content_unit_type must map to exactly one target format, and article/thread plans do not require Base Video Generation Plans.
- 2026-07-04: Within-record production-plan constraints should live in schema when possible; keep cross-field/project-chain checks in validate project, but encode cheap cardinality rules for validate record.

### apply-social-template
- 2026-07-04: Text formats can use social templates as reader-progression structures; applied beats should answer reader questions rather than describe shots or slides.
