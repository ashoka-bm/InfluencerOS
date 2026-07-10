"""Seed-based constructors, staged bundles, and plan fan-out (ADR 0042).

The canonical-seed tests are the fixture contract from
docs/record-constructors.md: a seed of authored fields must scaffold to a
record byte-equal (or field-equal) to the repository example, proving the
constructor owns every derived and copied field. A schema change that
breaks construction fails here, not at runtime.
"""

import datetime
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock

from influencer_os import cli
from influencer_os.connectors import plan_fetch
from influencer_os.connectors.fetch import ConnectorUnavailable
from influencer_os.constructors import (
    complete_run,
    scaffold_project,
    scaffold_search_plan,
)
from influencer_os.creator_workspaces import init_creator
from influencer_os.full_validation import validate_all
from influencer_os.projects import validate_project
from influencer_os.staging import commit_stage, stage_concept_approval
from influencer_os.validation import ValidationError, load_json
from tests.support import (
    ROOT,
    populate_approval_records,
    populate_video_understanding_packs,
    populate_workspace_records,
    scaffold_project_workspace,
)


def _example(name):
    return json.loads((ROOT / "examples" / name).read_text())


def _rewrite_json(path, mutate):
    record = json.loads(path.read_text())
    mutate(record)
    path.write_text(json.dumps(record, indent=2) + "\n")


def _promotion_ready_workspace(temp_dir):
    """Fixture workspace with the promotion records in place but the
    fixture project not yet created (its promotion id is unclaimed). Rooted
    under creators/ so the default projection index path resolves."""
    workspace_dir = init_creator(
        ROOT / "examples" / "creator-workspace.example.json",
        workspace_root=Path(temp_dir) / "creators",
    )
    populate_workspace_records(workspace_dir)
    populate_video_understanding_packs(workspace_dir)
    populate_approval_records(workspace_dir)
    return workspace_dir


def _project_seed_from_example():
    example = _example("project.example.json")
    return {
        "project_slug": example["project_slug"],
        "content_unit_type": example["content_unit_type"],
        "platform_targets": example["platform_targets"],
        "learning_goal": example["learning_goal"],
        "acceptance_criteria": example["acceptance_criteria"],
        "constraints": example["constraints"],
        "notes": example["notes"],
        "reference_asset_ids": example["source_refs"]["reference_asset_ids"],
        "commercial_expression": example["commercial_expression"],
        "concept_approval_id": example["source_refs"]["concept_approval_id"],
    }


def _search_plan_seed_from_example():
    example = _example("research-search-plan.example.json")
    return {
        "mode": example["mode"],
        "scope": example["scope"],
        "platforms": example["platforms"],
        "schedule_slot_ids": example["schedule_slot_ids"],
        "decision_basis": example["decision_basis"],
        "adapters_considered": example["adapters_considered"],
        "planned_queries": example["planned_queries"],
        "planned_sources": example["planned_sources"],
        "skipped_sources": example["skipped_sources"],
        "approval_gates": example["approval_gates"],
        "future_connector_notes": example["future_connector_notes"],
    }


class ScaffoldProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = _promotion_ready_workspace(self.temp.name)

    def test_canonical_seed_reproduces_example_manifest(self):
        result = scaffold_project(
            _project_seed_from_example(),
            self.workspace,
            now=datetime.datetime(2026, 6, 29, 12, 0, 0),
        )
        manifest = load_json(result["project_dir"] / "project.json")
        # The example is a mid-lifecycle record (status planning); a fresh
        # construction differs only in its initial status.
        self.assertEqual(
            manifest, {**_example("project.example.json"), "status": "created"}
        )

    def test_project_id_comes_from_unclaimed_promotion_listing(self):
        result = scaffold_project(_project_seed_from_example(), self.workspace)
        self.assertEqual(result["project_id"], "project_luna_tiny_reset_001")
        validate_project(result["project_dir"])
        self.assertTrue(
            (result["project_dir"] / "evidence-brief.md").exists()
        )
        self.assertTrue(
            (result["project_dir"] / "generation" / "assets").is_dir()
        )

    def test_seed_rejects_constructor_owned_fields(self):
        seed = _project_seed_from_example()
        seed["status"] = "created"
        with self.assertRaises(ValidationError) as caught:
            scaffold_project(seed, self.workspace)
        self.assertIn("non-seed fields", str(caught.exception))

    def test_seed_missing_authored_field_fails(self):
        seed = _project_seed_from_example()
        del seed["learning_goal"]
        with self.assertRaises(ValidationError) as caught:
            scaffold_project(seed, self.workspace)
        self.assertIn("missing authored fields", str(caught.exception))


class ScaffoldSearchPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def test_canonical_seed_reproduces_example_plan(self):
        workspace_dir = init_creator(
            ROOT / "examples" / "creator-workspace.example.json",
            workspace_root=Path(self.temp.name),
        )
        populate_workspace_records(workspace_dir)
        (workspace_dir / "content-schedule.json").write_text(
            (ROOT / "examples" / "creator-content-schedule.example.json").read_text()
        )
        result = scaffold_search_plan(
            _search_plan_seed_from_example(),
            workspace_dir,
            now=datetime.datetime(2026, 7, 3, 8, 55, 0),
        )
        self.assertEqual(
            result["research_run_id"], "research_run_luna_fit_2026_07_03_001"
        )
        self.assertEqual(
            result["run_dir"],
            workspace_dir / "system" / "staging" / "research-runs"
            / "research_run_luna_fit_2026_07_03_001",
        )
        plan = load_json(result["search_plan_path"])
        self.assertEqual(plan, _example("research-search-plan.example.json"))

    def test_run_id_sequences_past_existing_runs(self):
        workspace_dir = _promotion_ready_workspace(self.temp.name)
        result = scaffold_search_plan(
            _search_plan_seed_from_example(),
            workspace_dir,
            now=datetime.datetime(2026, 7, 3, 8, 55, 0),
        )
        self.assertEqual(
            result["research_run_id"], "research_run_luna_fit_2026_07_03_002"
        )

    def test_unknown_schedule_slot_fails_early(self):
        workspace_dir = _promotion_ready_workspace(self.temp.name)
        seed = _search_plan_seed_from_example()
        seed["schedule_slot_ids"] = ["slot_luna_nonexistent"]
        with self.assertRaises(ValidationError) as caught:
            scaffold_search_plan(seed, workspace_dir)
        self.assertIn("do not exist", str(caught.exception))


class CompleteRunTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = init_creator(
            ROOT / "examples" / "creator-workspace.example.json",
            workspace_root=Path(self.temp.name),
        )
        populate_workspace_records(self.workspace)
        (self.workspace / "content-schedule.json").write_text(
            (ROOT / "examples" / "creator-content-schedule.example.json").read_text()
        )
        entry_path = (
            self.workspace / "research" / "content-opportunity-queue" / "entries"
            / "content_opportunity_luna_fit_001.json"
        )
        entry_path.parent.mkdir(parents=True, exist_ok=True)
        entry_path.write_text(
            (ROOT / "examples" / "content-opportunity.example.json").read_text()
        )
        result = scaffold_search_plan(
            _search_plan_seed_from_example(),
            self.workspace,
            now=datetime.datetime(2026, 7, 3, 8, 55, 0),
        )
        self.run_dir = result["run_dir"]
        self.run_id = result["research_run_id"]

    def _write_ledgers(self):
        for example_name, filename in (
            ("research-evidence.example.json", "evidence.jsonl"),
            ("metric-snapshot.example.json", "metric-snapshots.jsonl"),
        ):
            record = _example(example_name)
            (self.run_dir / filename).write_text(json.dumps(record) + "\n")
        source_yield = _example("research-source-yield.example.json")
        source_yield["source_key"] = "ad_hoc_complete_run_fixture"
        source_yield.pop("source_plan_id", None)
        (self.run_dir / "source-yield.jsonl").write_text(
            json.dumps(source_yield) + "\n"
        )

    def test_run_record_derives_from_plan_and_ledgers(self):
        self._write_ledgers()
        result = complete_run(
            self.run_id,
            self.workspace,
            material_update=True,
            finding_ids=["finding_luna_fit_desk_reset_lunch"],
            intelligence_updates=["Desk-reset demand confirmed this week."],
            now=datetime.datetime(2026, 7, 3, 9, 40, 0),
        )
        canonical_dir = self.workspace / "research" / "runs" / self.run_id
        self.assertEqual(result["run_dir"], canonical_dir)
        self.assertFalse(self.run_dir.exists())
        run_record = load_json(canonical_dir / "research-run.json")
        plan = _example("research-search-plan.example.json")
        self.assertEqual(run_record["run_status"], "completed")
        self.assertEqual(run_record["started_on"], plan["created_on"])
        self.assertEqual(run_record["completed_on"], "2026-07-03T09:40:00")
        for shared in ("mode", "scope", "schedule_slot_ids", "platforms",
                       "creator_profile_id"):
            self.assertEqual(run_record[shared], plan[shared])
        self.assertEqual(
            run_record["outputs"]["evidence_ids"], ["evidence_luna_fit_001"]
        )
        self.assertEqual(
            run_record["outputs"]["metric_snapshot_ids"],
            ["metric_snapshot_luna_fit_001"],
        )
        self.assertEqual(
            run_record["outputs"]["content_opportunity_ids"],
            ["content_opportunity_luna_fit_001"],
        )
        self.assertEqual(
            run_record["outputs"]["finding_ids"],
            ["finding_luna_fit_desk_reset_lunch"],
        )

    def test_completed_run_requires_source_yield_ledger(self):
        with self.assertRaises(ValidationError) as caught:
            complete_run(self.run_id, self.workspace, material_update=True)
        self.assertIn("source-yield.jsonl", str(caught.exception))

    def test_failed_run_completes_without_ledgers(self):
        result = complete_run(
            self.run_id,
            self.workspace,
            material_update=False,
            error="provider outage before any fetch",
        )
        run_record = load_json(result["run_dir"] / "research-run.json")
        self.assertEqual(run_record["run_status"], "failed")
        self.assertFalse(run_record["material_update"])
        self.assertEqual(
            run_record["error"], "provider outage before any fetch"
        )


class StageConceptApprovalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = _promotion_ready_workspace(self.temp.name)
        # De-approve the fixture: the concept is pre-gate, no approval
        # exists, the claimed slot is open (research already selected).
        (
            self.workspace / "campaigns" / "campaign_luna_fit_001" / "approvals"
            / "concept_approval_luna_fit_001.json"
        ).unlink()
        self.concept_path = (
            self.workspace / "campaigns" / "campaign_luna_fit_001" / "concepts"
            / "campaign_concept_luna_fit_001.json"
        )
        _rewrite_json(
            self.concept_path,
            lambda concept: concept.update(status="ready_for_approval"),
        )
        self.entry_path = (
            self.workspace / "research" / "content-opportunity-queue" / "entries"
            / "content_opportunity_luna_fit_001.json"
        )
        _rewrite_json(
            self.workspace / "content-schedule.json",
            lambda schedule: schedule["calendar_slots"][0].update(
                status="open"
            ),
        )
        self.seed = {
            "approved_platforms": ["instagram", "tiktok", "youtube"],
            "approved_formats": ["format_short_form_video"],
            "max_offer_integration": "embedded",
            "max_cta_intensity": "soft",
            "projects": [
                {
                    "project_slug": "tiny-reset-after-laptop-day",
                    "content_unit_type": "short_form_video",
                    "platform_targets": [
                        "youtube_shorts", "instagram_reels", "tiktok"
                    ],
                    "learning_goal": (
                        "Test whether a visible workday constraint plus a tiny "
                        "relief routine improves early retention."
                    ),
                    "acceptance_criteria": [
                        "A validated micro-journey production plan exists for "
                        "the short-form video format."
                    ],
                    "commercial_expression": {
                        "commercial_function": "lead_capture",
                        "offer_integration": "embedded",
                        "cta_intensity": "soft",
                    },
                    "schedule_slot_ids": ["slot_luna_2026_07_09_midweek"],
                    "evidence_brief": (
                        "# Evidence Brief\n\nHook: the slumped exhale. "
                        "Evidence: evidence_luna_fit_001.\n"
                    ),
                }
            ],
        }

    def test_stage_builds_prevalidated_bundle_without_canonical_writes(self):
        result = stage_concept_approval(
            self.seed, self.workspace, "campaign_concept_luna_fit_001"
        )
        approval = result["approval"]
        concept = load_json(self.concept_path)
        self.assertEqual(
            approval["concept_approval_id"], "concept_approval_luna_fit_001"
        )
        self.assertEqual(approval["evidence_refs"], concept["evidence_refs"])
        self.assertEqual(
            approval["intended_payoff"], concept["intended_payoff"]
        )
        self.assertEqual(
            approval["schedule_slot_ids"], ["slot_luna_2026_07_09_midweek"]
        )
        self.assertEqual(
            approval["project_ids_created"],
            ["project_luna_fit_tiny_reset_after_laptop_day_001"],
        )
        self.assertTrue(
            (result["stage_dir"] / "records" / "concept-approval.json").exists()
        )
        # Nothing canonical was written.
        self.assertFalse(
            (
                self.workspace / "campaigns" / "campaign_luna_fit_001" / "approvals"
                / "concept_approval_luna_fit_001.json"
            ).exists()
        )
        self.assertFalse(
            (self.workspace / "projects" / "tiny-reset-after-laptop-day").exists()
        )
        self.assertEqual(
            load_json(self.concept_path)["status"], "ready_for_approval"
        )

    def test_commit_stage_writes_bundle_and_flips_state(self):
        staged = stage_concept_approval(
            self.seed, self.workspace, "campaign_concept_luna_fit_001"
        )
        result = commit_stage(staged["stage_id"], self.workspace)
        self.assertTrue(result["approval_path"].exists())
        project_dir = (
            self.workspace / "projects" / "tiny-reset-after-laptop-day"
        )
        self.assertIn(
            "slumped exhale", (project_dir / "evidence-brief.md").read_text()
        )
        concept = load_json(self.concept_path)
        self.assertEqual(concept["status"], "active")
        schedule = load_json(self.workspace / "content-schedule.json")
        slot = schedule["calendar_slots"][0]
        self.assertEqual(slot["status"], "filled")
        self.assertEqual(slot["campaign_id"], "campaign_luna_fit_001")
        self.assertEqual(
            slot["campaign_concept_id"], "campaign_concept_luna_fit_001"
        )
        self.assertEqual(
            slot["project_id"],
            "project_luna_fit_tiny_reset_after_laptop_day_001",
        )
        self.assertFalse(staged["stage_dir"].exists())
        validate_all(self.workspace)

    def test_stale_stage_fails_closed(self):
        staged = stage_concept_approval(
            self.seed, self.workspace, "campaign_concept_luna_fit_001"
        )
        _rewrite_json(
            self.concept_path,
            lambda concept: concept.update(promise="A different promise now."),
        )
        with self.assertRaises(ValidationError) as caught:
            commit_stage(staged["stage_id"], self.workspace)
        self.assertIn("stale", str(caught.exception))
        self.assertFalse(
            (
                self.workspace / "campaigns" / "campaign_luna_fit_001" / "approvals"
                / "concept_approval_luna_fit_001.json"
            ).exists()
        )
        self.assertTrue(staged["stage_dir"].exists())

    def test_mutated_staged_record_fails_commit(self):
        # ADR 0042: the human approves exactly the staged bytes; a staged
        # record edited after presentation must never commit, even when the
        # edit is schema-valid and upstream inputs are unchanged.
        staged = stage_concept_approval(
            self.seed, self.workspace, "campaign_concept_luna_fit_001"
        )
        _rewrite_json(
            staged["stage_dir"] / "records" / "projects"
            / "tiny-reset-after-laptop-day" / "project.json",
            lambda project: project.update(
                learning_goal="Unapproved goal injected after presentation."
            ),
        )
        with self.assertRaises(ValidationError) as caught:
            commit_stage(staged["stage_id"], self.workspace)
        self.assertIn("pinned at staging", str(caught.exception))
        self.assertFalse(
            (
                self.workspace / "campaigns" / "campaign_luna_fit_001" / "approvals"
                / "concept_approval_luna_fit_001.json"
            ).exists()
        )
        self.assertFalse(
            (self.workspace / "projects" / "tiny-reset-after-laptop-day").exists()
        )

    def test_added_staged_record_fails_commit(self):
        staged = stage_concept_approval(
            self.seed, self.workspace, "campaign_concept_luna_fit_001"
        )
        (staged["stage_dir"] / "records" / "extra.json").write_text("{}\n")
        with self.assertRaises(ValidationError) as caught:
            commit_stage(staged["stage_id"], self.workspace)
        self.assertIn("pinned at staging", str(caught.exception))

    def test_stage_fails_closed_on_dangling_evidence_refs(self):
        # A fresh approval never enters canon with dangling provenance:
        # the human-approved leniency is for at-rest re-validation of
        # historical approvals only, never the staged-commit gate.
        _rewrite_json(
            self.concept_path,
            lambda concept: concept["evidence_refs"][0].update(
                evidence_id="evidence_luna_fit_pruned_999"
            ),
        )
        seed = json.loads(json.dumps(self.seed))
        seed["projects"][0]["schedule_slot_ids"] = []
        with self.assertRaises(ValidationError) as caught:
            stage_concept_approval(
                seed, self.workspace, "campaign_concept_luna_fit_001"
            )
        self.assertIn("unresolved evidence refs", str(caught.exception))

    def test_failed_commit_rolls_back_every_canonical_write(self):
        # ADR 0029: a partial approval/project set never rests canonical.
        # Inject a failure on the second project write and require the
        # approval, first project, concept flip, and slot flip all undone.
        seed = json.loads(json.dumps(self.seed))
        seed["projects"].append(
            {
                **seed["projects"][0],
                "project_slug": "second-reset-variation",
                "schedule_slot_ids": [],
                "evidence_brief": "# Evidence Brief\n\nSecond variation.\n",
            }
        )
        staged = stage_concept_approval(
            seed, self.workspace, "campaign_concept_luna_fit_001"
        )
        from influencer_os import staging

        real_create = staging.create_project_from_manifest
        created = []

        def fail_on_second(project, creator_workspace):
            if created:
                raise OSError("injected: disk full mid-commit")
            created.append(project["project_id"])
            return real_create(project, creator_workspace)

        with mock.patch.object(
            staging, "create_project_from_manifest", fail_on_second
        ):
            with self.assertRaises(OSError):
                commit_stage(staged["stage_id"], self.workspace)

        self.assertFalse(
            (
                self.workspace / "campaigns" / "campaign_luna_fit_001"
                / "approvals" / "concept_approval_luna_fit_001.json"
            ).exists()
        )
        self.assertFalse(
            (self.workspace / "projects" / "tiny-reset-after-laptop-day").exists()
        )
        self.assertFalse(
            (self.workspace / "projects" / "second-reset-variation").exists()
        )
        self.assertEqual(
            load_json(self.concept_path)["status"], "ready_for_approval"
        )
        slot = load_json(self.workspace / "content-schedule.json")[
            "calendar_slots"
        ][0]
        self.assertEqual(slot["status"], "open")
        self.assertNotIn("project_id", slot)
        # The stage survives for retry; the workspace validates clean.
        self.assertTrue(staged["stage_dir"].exists())
        validate_all(self.workspace)
        commit_stage(staged["stage_id"], self.workspace)
        validate_all(self.workspace)

    def test_active_concept_accepts_a_later_additional_approval(self):
        # One unchanged concept may receive later approvals for additional
        # projects (campaign-concept-pressure plan).
        workspace = _promotion_ready_workspace(
            tempfile.mkdtemp(dir=self.temp.name)
        )
        seed = json.loads(json.dumps(self.seed))
        seed["projects"][0]["schedule_slot_ids"] = []
        result = stage_concept_approval(
            seed, workspace, "campaign_concept_luna_fit_001"
        )
        self.assertEqual(
            result["approval"]["concept_approval_id"],
            "concept_approval_luna_fit_002",
        )

    def test_stage_rejects_draft_concept(self):
        _rewrite_json(
            self.concept_path,
            lambda concept: concept.update(status="draft"),
        )
        with self.assertRaises(ValidationError) as caught:
            stage_concept_approval(
                self.seed, self.workspace, "campaign_concept_luna_fit_001"
            )
        self.assertIn("ready_for_approval", str(caught.exception))

    def test_stage_rejects_duplicate_bundle_slugs(self):
        seed = dict(self.seed)
        seed["projects"] = [self.seed["projects"][0], self.seed["projects"][0]]
        with self.assertRaises(ValidationError) as caught:
            stage_concept_approval(
                seed, self.workspace, "campaign_concept_luna_fit_001"
            )
        self.assertIn("twice", str(caught.exception))

    def test_stage_rejects_existing_project_folder_slug(self):
        (self.workspace / "projects" / "tiny-reset-after-laptop-day").mkdir(
            parents=True
        )
        with self.assertRaises(ValidationError) as caught:
            stage_concept_approval(
                self.seed, self.workspace, "campaign_concept_luna_fit_001"
            )
        self.assertIn("already exists", str(caught.exception))

    def test_stage_requires_intent_pair_on_concept(self):
        _rewrite_json(
            self.concept_path,
            lambda concept: concept.pop("intended_emotion"),
        )
        with self.assertRaises(ValidationError) as caught:
            stage_concept_approval(
                self.seed, self.workspace, "campaign_concept_luna_fit_001"
            )
        self.assertIn("intent pair", str(caught.exception))
    def test_multi_format_bundle_creates_exact_project_set(self):
        # Runnable exit criterion 1 (campaign-concept-pressure plan): one
        # approved concept transactionally creates a Substack article, two
        # Instagram posts, one Reel, and two Stories — six projects, one
        # owning concept, individually valid production paths.
        def project_seed(slug, unit, platforms):
            return {
                "project_slug": slug,
                "content_unit_type": unit,
                "platform_targets": platforms,
                "learning_goal": f"Test the {unit} angle of the reset concept.",
                "acceptance_criteria": [
                    f"A validated production plan exists for the {unit} format."
                ],
                "commercial_expression": {
                    "commercial_function": "lead_capture",
                    "offer_integration": "embedded",
                    "cta_intensity": "soft",
                },
            }

        seed = {
            "approved_platforms": ["instagram", "tiktok", "youtube",
                                   "substack"],
            "approved_formats": [
                "format_article", "format_single_image_post",
                "format_short_form_video", "format_story_sequence",
            ],
            "max_offer_integration": "embedded",
            "max_cta_intensity": "soft",
            "projects": [
                project_seed("reset-article", "article", ["substack"]),
                project_seed("reset-post-one", "single_image_post",
                             ["instagram"]),
                project_seed("reset-post-two", "single_image_post",
                             ["instagram"]),
                project_seed("reset-reel", "short_form_video",
                             ["instagram_reels"]),
                project_seed("reset-story-one", "story_sequence",
                             ["instagram_stories"]),
                project_seed("reset-story-two", "story_sequence",
                             ["instagram_stories"]),
            ],
        }
        staged = stage_concept_approval(
            seed, self.workspace, "campaign_concept_luna_fit_001"
        )
        self.assertEqual(len(staged["approval"]["project_ids_created"]), 6)
        result = commit_stage(staged["stage_id"], self.workspace)
        self.assertEqual(len(result["project_dirs"]), 6)
        approval = load_json(result["approval_path"])
        for project_dir in result["project_dirs"]:
            manifest = load_json(project_dir / "project.json")
            self.assertEqual(
                manifest["source_refs"]["concept_approval_id"],
                approval["concept_approval_id"],
            )
            self.assertEqual(
                manifest["source_refs"]["campaign_concept_id"],
                "campaign_concept_luna_fit_001",
            )
            validate_project(project_dir)
        validate_all(self.workspace)



class PlanFetchTests(unittest.TestCase):
    def test_jobs_respect_plan_use_now_decisions(self):
        plan = _example("research-search-plan.example.json")
        jobs, skipped = plan_fetch.plan_fetch_jobs(plan)
        self.assertEqual(
            [(job["id"], job["mode"]) for job in jobs],
            [("query_luna_fit_youtube_001", "youtube-search")],
        )
        skipped_ids = {skip["id"] for skip in skipped}
        # tiktok has no connector; reddit's connector adapter is not
        # use_now in this plan; the instagram source is browser-path.
        self.assertEqual(
            skipped_ids,
            {"query_luna_fit_001", "query_luna_fit_002",
             "source_plan_luna_fit_001"},
        )

    def test_fetch_for_plan_writes_validated_results(self):
        plan = _example("research-search-plan.example.json")
        canned = _example("research-fetch-result.example.json")
        budget = plan_fetch.LockedCallBudget(10)
        with tempfile.TemporaryDirectory() as run_dir:
            with mock.patch.object(
                plan_fetch.connector_fetch, "fetch_for_mode",
                return_value=canned,
            ) as fetch_mock:
                summary = plan_fetch.fetch_for_plan(
                    plan, run_dir, config={}, budget=budget
                )
            self.assertEqual(summary["fetched"], 1)
            self.assertEqual(fetch_mock.call_count, 1)
            outcome = summary["jobs"][0]
            self.assertEqual(outcome["status"], "fetched")
            self.assertTrue(outcome["result_path"].exists())
            self.assertEqual(load_json(outcome["result_path"]), canned)

    def test_unavailable_connector_degrades_to_outcome(self):
        plan = _example("research-search-plan.example.json")
        budget = plan_fetch.LockedCallBudget(10)
        with tempfile.TemporaryDirectory() as run_dir:
            with mock.patch.object(
                plan_fetch.connector_fetch, "fetch_for_mode",
                side_effect=ConnectorUnavailable("YOUTUBE_API_KEY missing"),
            ):
                summary = plan_fetch.fetch_for_plan(
                    plan, run_dir, config={}, budget=budget
                )
            self.assertEqual(summary["fetched"], 0)
            self.assertEqual(summary["jobs"][0]["status"], "unavailable")

    def test_locked_budget_never_overspends_concurrently(self):
        budget = plan_fetch.LockedCallBudget(50)
        with ThreadPoolExecutor(max_workers=16) as executor:
            outcomes = list(
                executor.map(lambda _n: budget.spend(), range(200))
            )
        self.assertEqual(sum(outcomes), 50)
        self.assertEqual(budget.used, 50)


class ConstructorCliTests(unittest.TestCase):
    def test_scaffold_list(self):
        self.assertEqual(cli.main(["scaffold", "--list"]), 0)

    def test_refresh_workspace_on_valid_fixture(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _project_dir = scaffold_project_workspace(
                Path(temp_dir) / "creators"
            )
            self.assertEqual(
                cli.main(["refresh-workspace", str(workspace_dir)]), 0
            )


if __name__ == "__main__":
    unittest.main()
