# Guided E2E and Public-Web Provenance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the Luna Fit E2E review findings into durable behavior: guided normal-user setup must ask, log, and gate decisions explicitly, and background public-web research must validate without being mislabeled as social or YouTube evidence.

**Architecture:** Keep the change at the existing schema, validator, drift-test, and skill-document seams. Extend the canonical research provenance vocabulary with `public_web` and public-web content types, while keeping production target platforms in `platform_targets` and promotion approvals as social/distribution surfaces. Use textual drift checks to pin guided onboarding and conductor phase obligations because these behaviors currently live in skills.

**Tech Stack:** Python `unittest`, repository JSON-schema subset validator, Markdown skill contracts.

---

### Task 1: Pin Guided Normal-User Onboarding Behavior

**Files:**
- Modify: `tests/test_drift_checks.py`
- Modify: `skills/create-influencer/SKILL.md`

- [x] **Step 1: Add a drift test for normal-user setup guidance**

Add a test that reads `skills/create-influencer/SKILL.md` and asserts the skill names the normal/new-user mode, one-question-at-a-time interview, recommended answer rationale, accept/revise/skip/system-fill choices, `progress/setup-interview.md` or `progress/setup-checklist.md`, answer source values, explicit foundation approval, and generated-vs-user-provided distinction.

- [x] **Step 2: Add a drift test against silent foundation preapproval**

Add a test that asserts the skill forbids generic validation-based approval language for normal-user runs and requires explicit user approval before `content_ready` or `generation_ready`.

- [x] **Step 3: Update the create-influencer skill contract**

Add a dated `## Rules` entry and a normal-user E2E interaction contract. Preserve the existing Generate From Basic Information path, but require missing inputs to be asked one at a time, logged with source/fill status, and reviewed as a whole foundation package before readiness advances.

- [x] **Step 4: Run the drift tests**

Run: `python3 -m unittest tests.test_drift_checks`

Expected: PASS.

### Task 2: Add Honest Public-Web Research Provenance

**Files:**
- Modify: `tests/test_drift_checks.py`
- Modify: `tests/test_schema_validation.py`
- Modify: `tests/test_research_validation.py`
- Modify: `schemas/*.schema.json` files that carry the pinned research platform/content-type enums
- Modify: `influencer_os/validation.py`
- Modify: `influencer_os/projects.py` only if platform-fit handling requires separating source provenance from target platforms

- [x] **Step 1: Add public-web schema tests**

Add tests proving a `ResearchEvidence` record can use `platform: public_web` and `platform_content_type: institutional_article` or `research_article`, and a Project `source_refs` cache can name `public_web` without claiming `youtube_video`.

- [x] **Step 2: Add research validation coverage**

Add a workspace-level validation test with a public-web evidence record, source-yield record, and no metric snapshots for that evidence. Confirm `validate_research()` passes and the source-yield `metric_snapshot_ids` list may be empty.

- [x] **Step 3: Extend canonical enums**

Add `public_web` to the canonical research platform enum and add `public_web_page`, `institutional_article`, and `research_article` to the canonical content-type enum. Update every pinned schema copy and drift constants together.

- [x] **Step 4: Preserve target-platform semantics**

Keep `platform_targets` as distribution targets. Do not require `public_web` as a production target and do not include it in platform-fit expectations for content format support.

- [x] **Step 5: Run targeted schema/research tests**

Run: `python3 -m unittest tests.test_schema_validation tests.test_research_validation tests.test_drift_checks`

Expected: PASS.

### Task 3: Update Research and Conductor Skill Guidance

**Files:**
- Modify: `skills/create-research-findings/SKILL.md`
- Modify: `skills/influencer-os/SKILL.md`
- Modify: `tests/test_drift_checks.py`

- [x] **Step 1: Pin research provenance guidance**

Add drift coverage that `create-research-findings` forbids labeling public-web/manual citation evidence as YouTube, distinguishes source evidence from distribution targets, asks whether to proceed when only background/public-web evidence exists, and avoids fake metric snapshots.

- [x] **Step 2: Pin conductor phase contract**

Add drift coverage that `influencer-os` requires a phase checklist with current phase, next artifact, validation command, human gate/dry-run/provider boundary classification, and advisory creative review after production planning.

- [x] **Step 3: Update skill rules**

Add dated `## Rules` entries and concise instructions to both skills for the public-web provenance correction, advisory creative review offer, and phase checklist/next-artifact contract.

- [x] **Step 4: Run drift tests**

Run: `python3 -m unittest tests.test_drift_checks`

Expected: PASS.

### Task 4: Validate and Commit

**Files:**
- All modified files above

- [x] **Step 1: Run required targeted tests**

Run:

```bash
python3 -m unittest tests.test_schema_validation tests.test_research_validation tests.test_user_journey tests.test_drift_checks
python3 -m influencer_os validate examples
```

Expected: PASS.

- [x] **Step 2: Run full tests**

Run:

```bash
python3 -m unittest discover -s tests
```

Expected: PASS, or report exact unrelated failures.

- [x] **Step 3: Commit one logical change**

Run:

```bash
git status --short
git add docs/superpowers/plans/2026-07-07-guided-e2e-public-web-provenance.md tests/test_drift_checks.py tests/test_schema_validation.py tests/test_research_validation.py schemas influencer_os/validation.py influencer_os/projects.py skills/create-influencer/SKILL.md skills/create-research-findings/SKILL.md skills/influencer-os/SKILL.md
git commit -m "fix guided e2e provenance contracts"
```

Expected: Commit created locally; do not push.
