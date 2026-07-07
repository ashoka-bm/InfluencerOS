import json
import tempfile
import unittest
from pathlib import Path

from tests.test_user_journey import (
    ROOT,
    frontmatter,
    run_cli,
    seed_creator_setup_outputs,
    seed_project_outputs,
    set_workspace_status,
    write_json,
)


RUN_ID = "research_run_luna_fit_2026_07_03_001"
PROJECT_SLUG = "tiny-reset-after-laptop-day"
PROJECT_ID = "project_luna_tiny_reset_001"
PROMOTION_ID = "idea_promotion_luna_fit_001"
ENTRY_ID = "idea_queue_entry_luna_fit_001"


def load_example(example_name):
    return json.loads((ROOT / "examples" / f"{example_name}.example.json").read_text())


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


def write_guided_setup_records(workspace_dir):
    progress_dir = workspace_dir / "progress"
    progress_dir.mkdir(parents=True, exist_ok=True)
    (progress_dir / "setup-interview.md").write_text(
        """# Setup Interview And Approval Record

Date: 2026-07-07
Run type: disposable normal-user E2E fixture
Onboarding path: Generate From Basic Information

Validation supports readiness, but validation alone is not approval.

| Question | Recommendation | Rationale | Answer | Answer source | Acceptance status |
| --- | --- | --- | --- | --- | --- |
| Which onboarding path should this disposable run use? | Generate From Basic Information. | The run checks whether a newcomer can reach a complete foundation from minimal seed facts. | Generate From Basic Information. | user_provided | accepted |
| What niche and audience should be treated as inputs? | Desk-worker mobility for laptop-heavy workers. | Audience and niche are creator-profile inputs, not agent guesses. | Desk-worker mobility for remote and hybrid laptop-heavy workers. | user_provided | accepted |
| How should missing visual references be handled? | Use existing fixture references and do not request provider generation. | The E2E validates planning and gates without paid/provider calls. | Use fixture references only; no provider call is approved. | user_provided | accepted |
| Is the whole foundation approved for readiness? | Approve the foundation and keep provider generation blocked. | The foundation files are complete and the provider boundary remains visible. | Approved for readiness; image, video, audio, render, upload, and paid calls remain unapproved. | user_provided | accepted |
"""
    )
    (progress_dir / "setup-checklist.md").write_text(
        """# Setup Checklist

## Status

- Workspace status: generation_ready.
- Foundation accepted: yes, per explicit operator approval recorded in `progress/setup-interview.md`; validation is supporting evidence only.
- Provider generation approval: not approved.

## Provider Boundary

Stop before image, video, audio, render, upload, or paid provider calls.
"""
    )
    (progress_dir / "phase-checklist.md").write_text(
        """# E2E Phase Checklist

| Phase | Required next artifact | Validation command | Step type | Status |
| --- | --- | --- | --- | --- |
| Creator setup | Setup interview and creator foundation | `python3 -m influencer_os validate workspace <workspace>` | Human gate | Complete. |
| Research findings | Search plan, public-web evidence, metric snapshot, source yield, findings | `python3 -m influencer_os validate research <workspace>` | Dry-run drafting step | Complete. |
| Idea queue | Scored idea queue entry | `python3 -m influencer_os validate queue <workspace>` | Dry-run drafting step | Complete. |
| Idea promotion | Human-approved promotion package | `python3 -m influencer_os validate queue <workspace>` | Human gate | Complete. |
| Production planning | Applied template, production plan, generation plan | `python3 -m influencer_os validate project <project>` | Dry-run drafting step | Complete. |
| Advisory creative review | Hook/payoff review record | `python3 -m influencer_os validate project <project>` | Advisory review | Complete. |
| Generation approval | Exact GenerationApprovalRecord | `python3 -m influencer_os list-providers` | Provider boundary | Blocked. |
| Release check | Full composed workspace validation | `python3 -m influencer_os validate all <workspace>` | Dry-run validation step | Complete. |
"""
    )


def seed_guided_public_web_research(workspace_dir):
    research = workspace_dir / "research"
    run_dir = research / "runs" / RUN_ID

    schedule = load_example("creator-content-schedule")
    write_json(workspace_dir / "content-schedule.json", schedule)

    run = load_example("research-run")
    run["platforms"] = ["public_web"]
    run["scope"] = "Public-web dry-run evidence for a guided newcomer E2E desk reset."
    run["outputs"]["research_intelligence_updates"] = [
        "Public-web source evidence is useful for safety grounding but does not prove native social trend velocity."
    ]
    write_json(run_dir / "research-run.json", run)

    plan = load_example("research-search-plan")
    plan["platforms"] = ["public_web"]
    plan["scope"] = "Find public-web source evidence for one guided E2E desk reset idea."
    plan["adapters_considered"] = [
        {
            "adapter_id": "public_web_browser",
            "access_method": "public_web",
            "adapter_status": "active",
            "auth_required": False,
            "approval_required": False,
            "decision": "use_now",
            "reason": "Public-web pages are enough to ground this dry-run idea without provider calls.",
        }
    ]
    plan["planned_queries"] = [
        {
            "query_id": "query_guided_e2e_desk_stretches",
            "platform": "public_web",
            "query_intent": "how_to",
            "query": "desk stretches workplace mobility",
            "source_type": "search_term",
            "purpose": "Find reputable desk-stretch guidance for the safe movement premise.",
            "expected_signal": "Institutional or public-health article guidance, not social metrics.",
            "routing_basis": "The query derives from the accepted creator niche and first-use goal.",
            "term_basis": ["creator_profile"],
        }
    ]
    plan["planned_sources"] = [
        {
            "source_plan_id": "source_plan_guided_e2e_mayo",
            "platform": "public_web",
            "url": "https://www.mayoclinic.org/healthy-lifestyle/adult-health/in-depth/office-stretches/art-20046041",
            "source_ref": "source_intel_luna_fit_001",
            "source_type": "direct_url",
            "reason": "Reputable public-web desk stretch guidance.",
        }
    ]
    plan["skipped_sources"] = [
        {
            "name": "TikTok logged-in exploration",
            "platform": "tiktok",
            "reason": "Logged-in social browsing is outside this guided dry run.",
        }
    ]
    plan["approval_gates"] = [
        {
            "gate_id": "approval_gate_guided_e2e_provider_generation",
            "required_before": "api_backed_search",
            "reason": "This guided dry run avoids API-backed acquisition even when connectors are configured.",
        }
    ]
    plan["future_connector_notes"] = [
        "A live run can add platform-native metrics later; this guided fixture stays public-web only."
    ]
    write_json(run_dir / "search-plan.json", plan)

    evidence = load_example("research-evidence")
    evidence.update(
        source_url="https://www.mayoclinic.org/healthy-lifestyle/adult-health/in-depth/office-stretches/art-20046041",
        platform="public_web",
        platform_content_type="institutional_article",
        source_relationship="general_trend",
        source_summary="Mayo Clinic desk-stretch guidance supports gentle workplace movement framing.",
        signal_summary="Source-quality support for a safe desk reset premise; not native social performance evidence.",
        confidence="medium",
        limitations="Public health guidance, not platform performance evidence; no social engagement metrics.",
    )
    evidence.pop("source_account", None)
    evidence.pop("visible_metrics", None)
    write_jsonl(run_dir / "evidence.jsonl", [evidence])

    metric = load_example("metric-snapshot")
    metric.update(
        platform="public_web",
        visible_metrics={
            "other": "No social engagement metrics captured; public web source only."
        },
        observed_age="Public page available as of capture date.",
        velocity_estimate="unknown",
        reference_creator_baseline="not applicable",
        outperformance_note="No platform performance claim.",
    )
    metric.pop("posted_on", None)
    write_jsonl(run_dir / "metric-snapshots.jsonl", [metric])

    source_yield = load_example("research-source-yield")
    source_yield.update(
        source_key="source_intel_luna_fit_001",
        source_kind="saved_source",
        platform="public_web",
        adapter_id="public_web_browser",
        access_method="public_web",
        source_plan_id="source_plan_guided_e2e_mayo",
        url="https://www.mayoclinic.org/healthy-lifestyle/adult-health/in-depth/office-stretches/art-20046041",
        yield_reason="Reputable public-web guidance directly supports the safe desk reset premise.",
        engagement_basis={
            "visible_metric_signal": "unknown",
            "cross_platform_validation": False,
            "creator_fit": "high",
            "notes": "No native social metrics; promoted for safety grounding and creator fit.",
        },
        recommended_intelligence_action="add_candidate",
    )
    write_jsonl(run_dir / "source-yield.jsonl", [source_yield])

    findings = load_example("research-findings")
    findings_path = research / "findings.md"
    findings_path.parent.mkdir(parents=True, exist_ok=True)
    findings_path.write_text(
        frontmatter(findings)
        + "\n## Desk resets\n\nPublic-web evidence supports a safe desk reset premise without claiming native social trend velocity.\n"
    )
    stable = load_example("stable-finding")
    stable_path = research / "stable-findings" / "stable_finding_luna_fit_001.md"
    stable_path.parent.mkdir(parents=True, exist_ok=True)
    stable_path.write_text(frontmatter(stable) + "\nDesk resets remain a durable topic cluster.\n")

    intelligence = research / "intelligence"
    sources = load_example("research-sources")
    sources["items"][0].update(
        url="https://www.mayoclinic.org/healthy-lifestyle/adult-health/in-depth/office-stretches/art-20046041",
        platform="public_web",
        usefulness_score=72,
        rationale="Reputable public-web desk-stretch source for guided E2E safety grounding.",
    )
    sources["items"][0]["yield_stats"] = {
        "checked_count": 1,
        "promoted_to_evidence_count": 1,
        "background_use_count": 0,
        "low_yield_count": 0,
        "last_checked_on": "2026-07-03",
        "last_useful_on": "2026-07-03",
        "usefulness_basis": "One checked public-web run produced source evidence, a metric snapshot, a finding, and an idea queue entry.",
    }
    write_json(intelligence / "sources.json", sources)
    for example, filename in (
        ("research-hashtags", "hashtags.json"),
        ("reference-creators", "reference-creators.json"),
        ("research-watchlist", "watchlist.json"),
    ):
        write_json(intelligence / filename, load_example(example))
    terms = load_example("research-search-terms")
    terms["items"][0]["platform"] = "public_web"
    terms["items"][0]["rationale"] = "Public-web discovery term for guided E2E source evidence."
    write_json(intelligence / "search-terms.json", terms)

    entry = load_example("idea-queue-entry")
    entry["scores"]["evidence_strength"]["rationale"] = (
        "Public-web source evidence grounds the safety premise; no native social metrics were captured."
    )
    entry["scores"]["viral_potential"]["rationale"] = (
        "The hook is saveable, but the guided fixture does not claim trend velocity."
    )
    entry["evidence_refs"][0]["video_understanding_pack_ids"] = []
    write_json(research / "idea-queue" / "entries" / f"{ENTRY_ID}.json", entry)
    write_json(research / "idea-queue" / "queue.json", load_example("idea-queue"))

    promotion = load_example("idea-promotion")
    promotion["evidence_refs"][0]["video_understanding_pack_ids"] = []
    promotion["score_snapshot"]["evidence_strength"]["rationale"] = (
        "Public-web source evidence grounds the safety premise; no native social metrics were captured."
    )
    promotion["approval_note"] = (
        "Explicit guided E2E operator approval after reviewing the promotion package."
    )
    write_json(research / "idea-promotions" / f"{PROMOTION_ID}.json", promotion)

    write_jsonl(workspace_dir / "system" / "project-warnings.jsonl", [load_example("project-warning")])
    write_jsonl(workspace_dir / "system" / "creator-events.jsonl", [load_example("system-event")])


def write_advisory_review(project_dir):
    review = load_example("review-record")
    review.update(
        review_record_id="review_guided_e2e_hook_payoff_001",
        project_id=PROJECT_ID,
        creator_profile_id="creator_luna_fit",
        idea_promotion_id=PROMOTION_ID,
        created_at="2026-07-07T18:20:00",
    )
    review["artifact_refs"] = [
        "plan/applied-template.json",
        "plan/production-plan.json",
        "plan/generation-plan.json",
    ]
    review["findings"] = [
        {
            "area": "hook",
            "severity": "none",
            "note": "The opening names the two-minute workday constraint immediately.",
        },
        {
            "area": "payoff",
            "severity": "low",
            "note": "The payoff is modest and clear, but the final posture contrast should stay visible.",
            "recommended_revision": "Keep the end shot visually close enough to read relaxed shoulders.",
        },
    ]
    review["reviewer_execution"] = {
        "execution_mode": "fallback_separated_pass",
        "source_skill": "review-hook-payoff",
        "fallback_reason": "Deterministic guided E2E fixture review.",
    }
    write_json(project_dir / "reviews" / f"{review['review_record_id']}.json", review)


class GuidedNewcomerE2ETests(unittest.TestCase):
    def test_guided_newcomer_run_records_gates_progress_and_honest_provenance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            run_root = Path(temp_dir)
            creators_root = run_root / "creators"
            workspace_dir = creators_root / "luna-fit"
            project_dir = workspace_dir / "projects" / PROJECT_SLUG

            run_cli(
                "init-creator",
                ROOT / "examples" / "creator-workspace.example.json",
                "--workspace-root",
                creators_root,
            )
            seed_creator_setup_outputs(workspace_dir)
            write_guided_setup_records(workspace_dir)
            intake_source = run_root / "guided-basic-intake.md"
            intake_source.write_text(
                "# Guided Basic Intake\n\nUse Luna Fit for a disposable normal-user E2E.\n"
            )
            run_cli(
                "import-intake",
                intake_source,
                "--creator-workspace",
                workspace_dir,
                "--source-type",
                "interview",
                "--source-id",
                "source_luna_fit_guided_e2e_001",
                "--imported-on",
                "2026-07-07",
                "--notes",
                "Guided E2E basic-information intake.",
            )
            run_cli(
                "set-intake-status",
                workspace_dir,
                "source_luna_fit_guided_e2e_001",
                "reviewed",
            )
            set_workspace_status(workspace_dir, "generation_ready")
            run_cli("validate", "workspace", workspace_dir)

            seed_guided_public_web_research(workspace_dir)
            run_cli(
                "init-project",
                ROOT / "examples" / "project.example.json",
                "--creator-workspace",
                workspace_dir,
            )
            project = json.loads((project_dir / "project.json").read_text())
            project["status"] = "ready_for_generation"
            project["source_refs"]["source_platforms"] = ["public_web"]
            project["source_refs"]["source_platform_content_types"] = [
                "institutional_article"
            ]
            project["source_refs"]["video_understanding_pack_ids"] = []
            project["acceptance_criteria"].append(
                "An advisory hook/payoff review record exists before generation approval."
            )
            project["notes"] = (
                "Guided E2E project with explicit promotion approval and generation still blocked."
            )
            write_json(project_dir / "project.json", project)
            seed_project_outputs(project_dir)
            write_advisory_review(project_dir)

            run_cli("validate", "research", workspace_dir)
            run_cli("validate", "queue", workspace_dir)
            run_cli("validate", "project", project_dir)
            run_cli("rebuild-board", workspace_dir)
            run_cli("validate", "board", workspace_dir)
            result = run_cli("validate", "all", workspace_dir)

            interview = (workspace_dir / "progress" / "setup-interview.md").read_text()
            checklist = (workspace_dir / "progress" / "phase-checklist.md").read_text()
            promotion = json.loads(
                (workspace_dir / "research" / "idea-promotions" / f"{PROMOTION_ID}.json").read_text()
            )
            project = json.loads((project_dir / "project.json").read_text())
            board = json.loads((workspace_dir / "boards" / "content-board.json").read_text())
            evidence_lines = (workspace_dir / "research" / "runs" / RUN_ID / "evidence.jsonl").read_text()
            review_files = list((project_dir / "reviews").glob("review_*.json"))

            self.assertIn("Question | Recommendation | Rationale", interview)
            self.assertIn("user_provided", interview)
            self.assertIn("accepted", interview)
            self.assertIn("Validation supports readiness, but validation alone is not approval", interview)
            self.assertNotIn("approved if files validate", interview.lower())
            self.assertNotIn("pre-authorized", interview.lower())

            self.assertIn("Human gate", checklist)
            self.assertIn("Dry-run drafting step", checklist)
            self.assertIn("Provider boundary", checklist)
            self.assertIn("validate all", checklist)

            self.assertEqual(promotion["approval_note"], "Explicit guided E2E operator approval after reviewing the promotion package.")
            self.assertNotIn("pre-authorized", json.dumps(promotion).lower())
            self.assertIn('"platform": "public_web"', evidence_lines)
            self.assertNotIn("youtube_video", evidence_lines)
            self.assertEqual(project["source_refs"]["source_platforms"], ["public_web"])
            self.assertEqual(project["status"], "ready_for_generation")
            self.assertTrue(review_files)
            self.assertFalse(any((project_dir / "generation" / "approval-records").glob("*.json")))
            self.assertFalse((project_dir / "output-package" / "output-package.json").exists())
            self.assertIn("Layers passed: 5; skipped: 0; warnings: 0.", result.stdout)
            project_cards = [card for card in board["cards"] if card["card_type"] == "project"]
            self.assertEqual(project_cards[0]["status"], "ready_for_generation")
