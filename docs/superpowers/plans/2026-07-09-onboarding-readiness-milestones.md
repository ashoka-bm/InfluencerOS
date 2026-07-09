# Onboarding Readiness Milestones Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement ADR 0028's forward-looking onboarding readiness milestones in schemas and workspace validation.

**Architecture:** Keep the file-first workspace model. `creator-workspace.json` owns the stage enum and canonical file paths; `readiness-gates.json`, `channels.json`, `content-strategy.json`, and `conversion-assets/*.json` own mutable onboarding state. Validation blocks false stage claims and warns for operational incompleteness.

**Tech Stack:** Python stdlib, hand-rolled JSON Schema subset in `influencer_os/validation.py`, `unittest`, JSON fixtures under `examples/`.

---

### Task 1: Stage Status Schema And Examples

**Files:**
- Modify: `schemas/creator-workspace.schema.json`
- Modify: `examples/creator-workspace.example.json`
- Test: `tests/test_readiness_validation.py`

- [x] Write a failing test proving new status `profile_ready` is accepted and unknown old statuses are rejected; retain only `content_ready` and `generation_ready` so workspace validation can emit the ADR-required migration warning.
- [x] Run `python3 -m unittest tests.test_readiness_validation.OnboardingReadinessMilestoneTests -v` and confirm it fails on the schema enum.
- [x] Replace old status enum values with `draft`, `profile_ready`, `foundation_ready`, `strategy_ready`, `production_ready`, `active`, `archived`.
- [x] Keep the example workspace as a draft scaffold and add canonical paths for new onboarding files.
- [x] Re-run the targeted test.

### Task 2: New Minimal Schemas

**Files:**
- Create: `schemas/readiness-gates.schema.json`
- Create: `schemas/channels.schema.json`
- Create: `schemas/content-strategy.schema.json`
- Create: `schemas/conversion-asset.schema.json`
- Create examples for each under `examples/`
- Test: `tests/test_schema_validation.py`

- [x] Add examples first and run `python3 -m unittest tests.test_schema_validation.SchemaValidationTests.test_examples_validate_against_schemas -v`; it should fail because schemas/examples are missing or invalid.
- [x] Add minimal schemas matching ADR 0028 decisions.
- [x] Re-run schema validation.

### Task 3: Workspace Readiness Validation

**Files:**
- Modify: `influencer_os/creator_workspaces.py`
- Test: `tests/test_readiness_validation.py`

- [x] Add failing tests for `profile_ready`, `foundation_ready`, `strategy_ready`, and `production_ready` blockers.
- [x] Implement validation of new canonical files and stage-specific blockers.
- [x] Ensure `prompt_ready` permits strategy but blocks creator image/video/spoken generation permissions unless references allow them.
- [x] Re-run targeted readiness tests.

### Task 4: Docs And Skill Wiring

**Files:**
- Modify: `CONTEXT.md`
- Modify: `docs/creator-workspace-structure.md`
- Modify: `docs/pipeline-contract.md`
- Modify: `docs/os-construction/architecture-map.md`
- Modify: `docs/os-construction/context-matrix.md`
- Modify: `docs/os-construction/skill-registry.md`
- Modify: `skills/create-influencer/SKILL.md`

- [x] Update vocabulary and file maps for the new onboarding records.
- [x] Update create-influencer output contract and readiness milestone language.
- [x] Run drift/schema tests.

### Task 5: Verify

**Files:** none

- [x] Run `python3 -m unittest discover -s tests`.
- [x] Run `python3 -m influencer_os validate examples`.

### Task 6: Interactive Calendar Projection

**Files:**
- Create: `influencer_os/calendars.py`
- Create: `influencer_os/templates/content-calendar.html`
- Modify: `influencer_os/cli.py`
- Test: `tests/test_content_calendar.py`

- [x] Add a portable HTML review projection generated from the canonical schedule.
- [x] Add `rebuild-calendar` and `validate calendar` CLI seams.
- [x] Reject stale or visibly tampered projections by comparing a deterministic re-render.
