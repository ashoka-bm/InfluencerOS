# InfluencerOS Process Learnings

This file stores system-level process and skill learnings for building InfluencerOS.

Creator performance learnings belong in Creator Workspaces, not here.

## General

- Keep Agentic OS copy/adaptation decisions visible before implementing deeper architecture.

## Individual Skills

### influencer-os

- Pending repeated feedback.
- 2026-07-03: Use bradautomates/claude-video /watch as optional external acquisition for Video Understanding Packs; keep Whisper, first-run installs, and batches behind approval, and do not add it to dependencies.
- 2026-07-09: Object reference planning must fan out every distinct prop into its own Reference Asset, prompt, provider request, and output image; multi-angle sheets may repeat only the same single object.

### create-influencer

- Pending repeated feedback.
- 2026-07-03: Nia Sol run review: stale no-generation notes survived an approved generation call; the skill now requires superseding checklist/MEMORY/daily-note claims in the same run as any generation.
- 2026-07-03: Nia Sol run review: checklist grouped wording (completed or prompted) hid which assets existed; scaffold and skill now track per-asset lifecycle status, and generated assets record date/tool/deviations in usage_notes.
- 2026-07-04: Creator setup onboarding should begin with a briefing and three paths: load existing files, guided interview, or generate from basic information; system-filled blanks stay in review.
- 2026-07-09: Creator setup should run as Creator Foundation -> Strategy -> Post Production. For image/video/voice channels, profile approval is not enough; require stable visual and voice references or an explicit waiver before strategy calendars and post production.
- 2026-07-09: 2026-07-09: A no-voiceover policy prohibits spoken generation; it never waives spoken_voice_generation_allowed or substitutes for approved voice evidence.
- 2026-07-09: Delegate visual-continuity candidate analysis and approval to create-reference-library before reference prompt staging or foundation readiness.
- 2026-07-09: Use Representation Model for synthetic/avatar-led/human-backed/text-first/mixed; reserve Creator Type for ADR 0026's planned influencer/product/brand discriminator.

### wrap-up

- 2026-07-03: Batch D built the self-improvement loop: log-learning and memory-write CLIs are the deterministic writers behind the wrap-up and memory-write skills.
- 2026-07-03: Phase 0C closed via batches A-G; the exit-criteria run is the wrap-up verification pattern: suite, examples, drift checks, full workflow, stale-path check.
- 2026-07-04: No feedback — routine session.
- 2026-07-04: No feedback - routine session after Phase 1 closeout verification.
- 2026-07-06: No feedback - routine session after Phase 2 full review.
- 2026-07-07: No feedback - routine session after repository hardening fixes.
- 2026-07-09: No feedback - routine session after creator-to-video workflow visualization.
- 2026-07-09: 2026-07-09: No feedback — routine session after onboarding readiness and calendar review remediation.
- 2026-07-09: No feedback — routine session after lean routing and ownership cleanup.

### create-personal-brand
- 2026-07-03: Personal-brand setup owns ICP-grade audience operating signals; keep them in personal-brand.md rather than expanding creator-profile.json.
- 2026-07-04: Personal-brand setup should capture platform-to-medium mapping and reference-needs signals before reference-library planning.

### create-research-findings
- 2026-07-03: Live research eval showed a need for source-yield learning: after Phase 1 slices 6-7, add the merged research-intelligence hardening slice that tracks searched-but-unused sources, downgrades repeated background-only/low-yield sources in research intelligence, and lands before scheduled research automation.
- 2026-07-04: Research-intelligence hardening now requires search-plan.json before browsing, source-yield.jsonl after browsing, and sources.json yield_stats for completed runs.
- 2026-07-04: Quality determination is now anchored: assign visible_metric_signal/confidence from the Signal Tier Rubric, require corroboration-breadth plus a contradiction pass in synthesis, ground query terms in creator context (not model knowledge), and expect a thin-evidence WARN when a material run promotes few checked sources (docs/workflows/research-and-ideas.md).
- 2026-07-05: ADR 0022 connectors are standing-approved by API-key presence; declare a connector adapter as use_now in search-plan only when 'list-connectors' shows it available, else mark it future_connector/skip_this_run and fall back to public web.

### create-production-plan
- 2026-07-04: Phase 1 slice 6 established one Project per content unit: content_unit_type must map to exactly one target format, and article/thread plans do not require Base Video Generation Plans.
- 2026-07-04: Within-record production-plan constraints should live in schema when possible; keep cross-field/project-chain checks in validate project, but encode cheap cardinality rules for validate record.

### apply-social-template
- 2026-07-04: Text formats can use social templates as reader-progression structures; applied beats should answer reader questions rather than describe shots or slides.

### create-output-package
- 2026-07-04: Use register-output-package as the only Output Package write gate; it copies upload-ready files, advances the Project to packaged, and relies on validate project for provenance closure.
- 2026-07-04: Keep Output Package writer checks mirrored in validate project so packaged records remain auditable after hand edits.

### tdd
- 2026-07-04: Phase 1 user-journey tests should exercise CLI gates end to end and seed only authored artifacts that skills currently produce.
- 2026-07-09: 2026-07-09: Readiness fixes stayed reliable when each review finding became a public-seam regression before implementation.

### create-reference-library
- 2026-07-04: Reference planning should derive required assets from platform-to-medium mapping and explicitly handle person reference images, recurring locations, collaborators, and identity-attached objects.
- 2026-07-09: Fan out grouped source language into one Reference Asset and isolated output image per distinct physical prop; schema-valid grouped prompts are still incomplete.
- 2026-07-09: Evaluate prop and production-space candidates for brand effectiveness, present the full package for explicit user selection, and block asset or prompt promotion until approval.
- 2026-07-09: Treat generated brand or carousel imagery as supporting references only; exact palette, typography, and layout tokens belong to the canonical personal brand board.

### personal-brand-board
- 2026-07-09: Keep one package-owned HTML template and populate it from each creator's schema-valid JSON spec so visual identity stays exact, reusable, and drift-checkable.
- 2026-07-09: Standardize visual-world sections as actual production spaces with correct location images; keep props in the reference library and render content pillars without decorative imagery.
- 2026-07-09: Surface recurring identity-bearing objects in a dedicated optional signature-props section with correct object imagery, purpose, uses, and continuity rules; never mix props with production spaces.
- 2026-07-09: Invoke the board only after Reference Library planning; bind production spaces and props by typed asset ID so incorrect image categories fail validation and prompt-ready references render intentional placeholders.
