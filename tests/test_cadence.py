"""Quarterly cadence record contracts (ADR 0047 core, part A)."""

import datetime
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from influencer_os.cadence import (
    coming_week_staleness_warnings,
    scaffold_foundation_revision,
    scaffold_quarter_plan,
    scaffold_strategy_revision,
)
from influencer_os.creator_workspaces import validate_creator_workspace
from influencer_os import constructors
from influencer_os.validation import (
    ValidationError,
    validate_examples,
    validate_file,
    validate_record,
)
from tests.support import scaffold_project_workspace, write_strategy_review_fixture
from tests.test_readiness_validation import (
    place_asset_files,
    place_brand_board_space_files,
    populate_foundation,
    rebuild_brand_board,
    write_channels,
    write_content_strategy,
    write_conversion_asset,
    write_readiness_milestones,
)


ROOT = Path(__file__).resolve().parents[1]

QUARTER_SEED = {
    "retrospective": {
        "findings": [],
        "performance_summary_ids": [],
        "lesson_refs": [],
    },
    "campaign_concept_set": [],
    "campaign_lifecycle_decisions": [],
    "campaign_duration_target_changes": [],
    "schedule_shape": {
        "anchor_slots_per_week": 2,
        "reactive_capacity": "one optional slot",
    },
    "revision_proposals": [],
    "terminal_review_record_id": "review_luna_quarterly_001",
    "approval": {"approved_by": "user", "approved_on": "2026-07-12"},
    "notes": "Keep the first Quarter deliberately light.",
}

FOUNDATION_SEED = {
    "quarter_plan_id": "quarter_plan_luna_fit_001",
    "amended_areas": ["identity", "brand"],
    "rationale": "Clarify the creator's public role after the first Quarter.",
    "notes": "The locked setup baseline remains preserved as version zero.",
}

STRATEGY_SEED = {
    "quarter_plan_id": "quarter_plan_luna_fit_001",
    "amended_areas": ["content_strategy", "schedule_shape"],
    "rationale": "Shift the mix toward the formats that retained attention.",
    "notes": "No readiness milestone regresses.",
}


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, record):
    Path(path).write_text(json.dumps(record, indent=2) + "\n")


def set_production_milestone(workspace, *, status="ready", approved_on=None):
    path = Path(workspace) / "readiness-gates.json"
    readiness = read_json(path)
    readiness["milestones"]["production"]["status"] = status
    readiness["milestones"]["production"]["approved_on"] = approved_on
    readiness["milestones"]["production"]["approved_by"] = (
        "user" if approved_on else None
    )
    readiness["milestones"]["production"]["terminal_review_record_id"] = (
        "review_luna_strategy_001" if status == "ready" else None
    )
    readiness["milestones"]["production"]["waivers"] = (
        [
            {
                "waiver_id": "waiver_luna_production_001",
                "reason": "Exercise fail-closed Quarter anchoring.",
                "approved_on": approved_on,
                "approved_by": "user",
            }
        ]
        if status == "waived"
        else []
    )
    write_json(path, readiness)


class CadenceRecordContractTests(unittest.TestCase):
    def fresh_workspace(self, temp_dir):
        workspace, _ = scaffold_project_workspace(temp_dir)
        manifest_path = workspace / "creator-workspace.json"
        manifest = read_json(manifest_path)
        manifest["status"] = "production_ready"
        write_json(manifest_path, manifest)
        populate_foundation(workspace)
        place_asset_files(workspace)
        write_readiness_milestones(
            workspace,
            strategy_status="ready",
            production_status="ready",
        )
        (workspace / "research" / "findings.md").unlink()
        write_strategy_review_fixture(workspace)
        write_channels(workspace)
        write_content_strategy(workspace, status="approved")
        schedule_path = workspace / "content-schedule.json"
        schedule = read_json(schedule_path)
        schedule["research_basis"] = {
            "status": "research_informed",
            "research_run_ids": ["research_run_luna_fit_2026_07_03_001"],
        }
        write_json(schedule_path, schedule)
        write_conversion_asset(workspace)
        board_path = (
            workspace / "references" / "brand" / "personal-brand-board.json"
        )
        board_path.write_text(
            (ROOT / "examples" / "personal-brand-board.example.json").read_text()
        )
        place_brand_board_space_files(workspace)
        rebuild_brand_board(workspace)
        self.write_quarterly_review_fixture(workspace)
        return workspace

    def test_new_examples_validate_without_schema_orphans(self):
        validated = {schema for schema, _ in validate_examples()}
        self.assertTrue(
            {"quarter-plan", "foundation-revision", "strategy-revision"}
            <= validated
        )

    def test_quarter_plan_derives_window_from_production_ready_date(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            approved_on = read_json(
                workspace / "readiness-gates.json"
            )["milestones"]["production"]["approved_on"]

            result = scaffold_quarter_plan(
                QUARTER_SEED, workspace, now=datetime.datetime(2026, 7, 12)
            )
            plan = read_json(result["path"])

            self.assertEqual(plan["quarter_number"], 1)
            self.assertEqual(plan["quarter_start_date"], approved_on)
            expected_end = (
                datetime.date.fromisoformat(approved_on)
                + datetime.timedelta(weeks=13)
            ).isoformat()
            self.assertEqual(plan["quarter_end_date"], expected_end)
            self.assertEqual(plan["production_ready_anchor_date"], approved_on)

    def test_quarter_anchor_fails_closed_without_ready_approval_date(self):
        for status, approved_on in (
            ("not_started", None),
            ("waived", "2026-07-09"),
            ("ready", None),
        ):
            with self.subTest(status=status, approved_on=approved_on):
                with tempfile.TemporaryDirectory() as temp_dir:
                    workspace = self.fresh_workspace(temp_dir)
                    set_production_milestone(
                        workspace, status=status, approved_on=approved_on
                    )
                    with self.assertRaises(ValidationError):
                        scaffold_quarter_plan(QUARTER_SEED, workspace)

    def test_revision_constructors_allocate_immutable_contiguous_versions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            scaffold_quarter_plan(QUARTER_SEED, workspace)

            foundation = [
                scaffold_foundation_revision(FOUNDATION_SEED, workspace),
                scaffold_foundation_revision(FOUNDATION_SEED, workspace),
            ]
            strategy = [
                scaffold_strategy_revision(STRATEGY_SEED, workspace),
                scaffold_strategy_revision(STRATEGY_SEED, workspace),
            ]

            self.assertEqual(
                [read_json(item["path"])["version"] for item in foundation],
                [1, 2],
            )
            self.assertEqual(
                [read_json(item["path"])["version"] for item in strategy],
                [1, 2],
            )
            self.assertEqual(
                [item["id"] for item in foundation],
                [
                    "foundation_revision_luna_fit_001",
                    "foundation_revision_luna_fit_002",
                ],
            )
            self.assertEqual(
                [item["id"] for item in strategy],
                [
                    "strategy_revision_luna_fit_001",
                    "strategy_revision_luna_fit_002",
                ],
            )
            self.assertTrue(all(Path(item["path"]).is_file() for item in foundation + strategy))

    def test_duplicate_or_gapped_revision_versions_fail_at_rest(self):
        for invalid_version in (1, 3):
            with self.subTest(invalid_version=invalid_version):
                with tempfile.TemporaryDirectory() as temp_dir:
                    workspace = self.fresh_workspace(temp_dir)
                    scaffold_quarter_plan(QUARTER_SEED, workspace)
                    first = scaffold_foundation_revision(
                        FOUNDATION_SEED, workspace
                    )
                    duplicate = read_json(first["path"])
                    duplicate["foundation_revision_id"] = (
                        f"foundation_revision_luna_fit_{invalid_version + 10:03d}"
                    )
                    duplicate["version"] = invalid_version
                    path = (
                        workspace
                        / "revisions"
                        / "foundation"
                        / f"{duplicate['foundation_revision_id']}.json"
                    )
                    write_json(path, duplicate)
                    with self.assertRaises(ValidationError):
                        validate_creator_workspace(workspace)

    def test_overdue_quarter_is_advisory_and_recent_anchor_is_not(self):
        today = datetime.date.today()
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            set_production_milestone(
                workspace,
                approved_on=(today - datetime.timedelta(weeks=40)).isoformat(),
            )
            warnings = validate_creator_workspace(workspace)["warnings"]
            self.assertTrue(any("overdue Quarter" in item for item in warnings))

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            set_production_milestone(
                workspace,
                approved_on=(today - datetime.timedelta(weeks=5)).isoformat(),
            )
            warnings = validate_creator_workspace(workspace)["warnings"]
            self.assertFalse(any("overdue Quarter" in item for item in warnings))

    def test_governing_revision_references_must_resolve(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            scaffold_quarter_plan(QUARTER_SEED, workspace)
            revision = scaffold_foundation_revision(FOUNDATION_SEED, workspace)

            governed_seed = dict(QUARTER_SEED)
            governed_seed["governing_foundation_revision_id"] = revision["id"]
            governed_seed["terminal_review_record_id"] = (
                self.write_quarterly_review_fixture(
                    workspace,
                    review_id="review_luna_quarterly_002",
                    packet_plan_id="quarter_plan_luna_fit_002",
                )
            )
            scaffold_quarter_plan(governed_seed, workspace)
            validate_creator_workspace(workspace)

            unknown_seed = dict(QUARTER_SEED)
            unknown_seed["governing_foundation_revision_id"] = (
                "foundation_revision_luna_fit_999"
            )
            with self.assertRaises(ValidationError):
                scaffold_quarter_plan(unknown_seed, workspace)

    def test_approved_plan_precedes_and_authorizes_proposed_revisions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            seed = dict(QUARTER_SEED)
            seed["revision_proposals"] = [
                {
                    "revision_type": "foundation",
                    "revision_id": "foundation_revision_luna_fit_001",
                }
            ]

            plan = scaffold_quarter_plan(seed, workspace)
            revision = scaffold_foundation_revision(FOUNDATION_SEED, workspace)

            self.assertEqual(plan["id"], "quarter_plan_luna_fit_001")
            self.assertEqual(
                revision["id"], "foundation_revision_luna_fit_001"
            )
            validate_creator_workspace(workspace)

    def drop_performance_summary(self, workspace):
        """Copy the committed PerformanceSummary example into the fresh
        workspace's project, aligned to that project/creator."""
        project_dir = workspace / "projects" / "tiny-reset-after-laptop-day"
        summary = json.loads(
            (ROOT / "examples" / "performance-summary.example.json").read_text()
        )
        summary["project_id"] = "project_luna_tiny_reset_001"
        summary["creator_profile_id"] = "creator_luna_fit"
        write_json(project_dir / "performance-summary.json", summary)
        return summary["performance_summary_id"]

    def write_quarterly_review_fixture(
        self,
        workspace,
        *,
        role="quarterly",
        review_id=None,
        extra_round=0,
        prior_review_record_id=None,
        research_demand=None,
        demand_note="The draft Quarter Plan needs one more evidence check.",
        packet_plan_id="quarter_plan_luna_fit_001",
    ):
        """Write a workspace-root reviews/ Quarterly Review record, anchored
        to the Creator Profile with minimal valid findings."""
        review = json.loads(
            (ROOT / "examples" / "review-record.example.json").read_text()
        )
        review.pop("project_id", None)
        review.pop("concept_approval_id", None)
        review_id = review_id or f"review_luna_{role}_001"
        packet_dir = (
            workspace / "quarter-plans" / "packets" / packet_plan_id
        )
        packet_dir.mkdir(parents=True, exist_ok=True)
        write_json(packet_dir / "draft-quarter-plan.json", {"draft": True})
        write_json(packet_dir / "campaign-concept-set.json", {"concepts": []})
        finding = {
            "area": "strategy",
            "severity": "none",
            "note": demand_note,
        }
        if research_demand is not None:
            finding["research_demand"] = research_demand
        artifact_refs = [
            "creator-profile.json",
            f"quarter-plans/packets/{packet_plan_id}/draft-quarter-plan.json",
            f"quarter-plans/packets/{packet_plan_id}/campaign-concept-set.json",
            "research/findings.md",
            "research/runs/research_run_luna_fit_2026_07_03_001/evidence.jsonl",
        ]
        if prior_review_record_id is not None:
            artifact_refs.append(f"reviews/{prior_review_record_id}.json")
        review.update(
            review_record_id=review_id,
            review_role=role,
            artifact_refs=artifact_refs,
            findings=[finding],
            research_demand_loop={
                "extra_research_round": extra_round,
                "prior_review_record_id": prior_review_record_id,
            },
        )
        review["reviewer_execution"]["source_skill"] = "review-quarter-plan"
        reviews_dir = workspace / "reviews"
        reviews_dir.mkdir(exist_ok=True)
        write_json(reviews_dir / f"{review_id}.json", review)
        return review_id

    def write_concept_review_fixture(
        self,
        workspace,
        *,
        review_id="review_luna_concept_001",
        source_skill="review-concept-promotion",
        approval_status="approve",
        severity="none",
        research_demand=None,
        research_demand_loop=False,
        persist=True,
    ):
        """Write a workspace-root Concept Review over a resolved weekly packet."""
        review = json.loads(
            (ROOT / "examples" / "review-record.example.json").read_text()
        )
        review.pop("project_id", None)
        review.pop("concept_approval_id", None)
        review.pop("research_demand_loop", None)
        finding = {
            "area": "evidence",
            "severity": severity,
            "note": "The weekly promotion package is evidence-backed.",
        }
        if research_demand is not None:
            finding["research_demand"] = research_demand
        if research_demand_loop:
            review["research_demand_loop"] = {
                "extra_research_round": 0,
                "prior_review_record_id": None,
            }
        schedule_path = workspace / "content-schedule.json"
        schedule = read_json(schedule_path)
        schedule["calendar_slots"][0].update(
            status="open",
            research_state={
                "status": "candidates_ready",
                "research_run_ids": [
                    "research_run_luna_fit_2026_07_03_001"
                ],
                "candidate_content_opportunity_ids": [
                    "content_opportunity_luna_fit_002",
                    "content_opportunity_luna_fit_003",
                    "content_opportunity_luna_fit_004",
                ],
            },
        )
        write_json(schedule_path, schedule)
        approval_path = (
            workspace
            / "campaigns"
            / "campaign_luna_fit_001"
            / "approvals"
            / "concept_approval_luna_fit_001.json"
        )
        approval = read_json(approval_path)
        approval["schedule_slot_ids"] = []
        write_json(approval_path, approval)

        queue_dir = workspace / "research" / "content-opportunity-queue"
        source_entry = read_json(
            queue_dir / "entries" / "content_opportunity_luna_fit_001.json"
        )
        candidate_refs = []
        for suffix in ("002", "003", "004"):
            candidate = dict(source_entry)
            candidate_id = f"content_opportunity_luna_fit_{suffix}"
            candidate["content_opportunity_id"] = candidate_id
            candidate["status"] = "shortlisted"
            candidate.pop("linked_campaign_concept_ids", None)
            write_json(queue_dir / "entries" / f"{candidate_id}.json", candidate)
            candidate_refs.append(
                f"research/content-opportunity-queue/entries/{candidate_id}.json"
            )
        queue = read_json(queue_dir / "queue.json")
        queue["entry_refs"].extend(
            {
                "content_opportunity_id": Path(ref).stem,
                "status": "shortlisted",
            }
            for ref in candidate_refs
        )
        queue["status_counts"] = {"assigned": 1, "shortlisted": 3}
        write_json(queue_dir / "queue.json", queue)

        review.update(
            review_record_id=review_id,
            review_role="concept",
            artifact_refs=[
                "creator-profile.json",
                "content-schedule.json",
                "research/findings.md",
                *candidate_refs,
                "research/runs/research_run_luna_fit_2026_07_03_001/evidence.jsonl",
            ],
            findings=[finding],
            approval_status=approval_status,
        )
        review["reviewer_execution"]["source_skill"] = source_skill
        if persist:
            constructors.scaffold_review_record(
                self.concept_review_seed(
                    review,
                    anchor_slot_id=schedule["calendar_slots"][0]["slot_id"],
                ),
                workspace,
                now=datetime.datetime(2026, 7, 12, 10, 0),
            )
        return review

    def concept_review_seed(self, review, *, anchor_slot_id):
        return {
            "anchor_slot_id": anchor_slot_id,
            "artifact_refs": list(review["artifact_refs"]),
            "findings": list(review["findings"]),
            "approval_status": review["approval_status"],
            "reviewer_execution": dict(review["reviewer_execution"]),
            "review_record_id": review["review_record_id"],
        }

    def test_concept_review_validates_as_workspace_scoped_built_review(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            review = self.write_concept_review_fixture(workspace)

            validate_record("review-record", review)
            result = validate_creator_workspace(workspace)

            self.assertEqual(result["creator_profile_id"], "creator_luna_fit")

    def test_concept_review_rejects_candidate_not_tracked_by_queue(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            review = self.write_concept_review_fixture(workspace)
            (workspace / "reviews" / "review_luna_concept_001.json").unlink()
            queue_path = (
                workspace
                / "research"
                / "content-opportunity-queue"
                / "queue.json"
            )
            queue = read_json(queue_path)
            queue["entry_refs"] = [
                ref
                for ref in queue["entry_refs"]
                if ref["content_opportunity_id"]
                != "content_opportunity_luna_fit_003"
            ]
            queue["status_counts"] = {"assigned": 1, "shortlisted": 2}
            write_json(queue_path, queue)
            anchor_slot_id = read_json(
                workspace / "content-schedule.json"
            )["calendar_slots"][0]["slot_id"]

            with self.assertRaisesRegex(
                ValidationError, "queue.*track|queue provenance|entry_refs"
            ):
                constructors.scaffold_review_record(
                    self.concept_review_seed(
                        review, anchor_slot_id=anchor_slot_id
                    ),
                    workspace,
                )

    def test_concept_review_accepts_explicit_two_candidate_anchor_packet(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            review = self.write_concept_review_fixture(workspace)
            omitted_ref = (
                "research/content-opportunity-queue/entries/"
                "content_opportunity_luna_fit_004.json"
            )
            review["artifact_refs"].remove(omitted_ref)
            (workspace / "reviews" / "review_luna_concept_001.json").unlink()
            schedule_path = workspace / "content-schedule.json"
            schedule = read_json(schedule_path)
            anchor_slot_id = schedule["calendar_slots"][0]["slot_id"]
            schedule["calendar_slots"][0]["research_state"][
                "candidate_content_opportunity_ids"
            ].remove(Path(omitted_ref).stem)
            write_json(schedule_path, schedule)

            result = constructors.scaffold_review_record(
                self.concept_review_seed(
                    review, anchor_slot_id=anchor_slot_id
                ),
                workspace,
            )

            self.assertEqual(result["review_record_id"], review["review_record_id"])

    def test_historical_concept_review_survives_topic_selection_and_assignment(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            self.write_concept_review_fixture(workspace)
            schedule_path = workspace / "content-schedule.json"
            schedule = read_json(schedule_path)
            schedule["calendar_slots"][0]["research_state"] = {
                "status": "selected",
                "research_run_ids": [
                    "research_run_luna_fit_2026_07_03_001"
                ],
                "selected_content_opportunity_id": (
                    "content_opportunity_luna_fit_002"
                ),
            }
            write_json(schedule_path, schedule)
            chosen_path = (
                workspace
                / "research"
                / "content-opportunity-queue"
                / "entries"
                / "content_opportunity_luna_fit_002.json"
            )
            chosen = read_json(chosen_path)
            chosen["status"] = "assigned"
            write_json(chosen_path, chosen)

            result = validate_creator_workspace(workspace)

            self.assertEqual(result["creator_profile_id"], "creator_luna_fit")
            self.assertTrue(
                (workspace / "reviews" / "review_luna_concept_001.json").exists()
            )

    def test_new_concept_review_requires_candidates_ready_anchor_packet(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            review = self.write_concept_review_fixture(workspace)
            (workspace / "reviews" / "review_luna_concept_001.json").unlink()
            schedule_path = workspace / "content-schedule.json"
            schedule = read_json(schedule_path)
            anchor_slot_id = schedule["calendar_slots"][0]["slot_id"]
            schedule["calendar_slots"][0]["research_state"] = {
                "status": "selected",
                "research_run_ids": [
                    "research_run_luna_fit_2026_07_03_001"
                ],
                "selected_content_opportunity_id": (
                    "content_opportunity_luna_fit_002"
                ),
            }
            write_json(schedule_path, schedule)

            with self.assertRaisesRegex(ValidationError, "candidates_ready"):
                constructors.scaffold_review_record(
                    self.concept_review_seed(
                        review, anchor_slot_id=anchor_slot_id
                    ),
                    workspace,
                    now=datetime.datetime(2026, 7, 12, 10, 30),
                )

            self.assertFalse(
                (workspace / "reviews" / "review_luna_concept_001.json").exists()
            )

    def test_new_concept_review_is_scoped_to_its_anchor_slot(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            review = self.write_concept_review_fixture(workspace)
            (workspace / "reviews" / "review_luna_concept_001.json").unlink()
            schedule_path = workspace / "content-schedule.json"
            schedule = read_json(schedule_path)
            anchor_slot_id = schedule["calendar_slots"][0]["slot_id"]
            second_run_id = "research_run_luna_fit_2026_07_03_002"
            unrelated = dict(schedule["calendar_slots"][0])
            unrelated.update(
                slot_id="slot_luna_unrelated_candidates_ready",
                target_date="2026-07-16",
                research_state={
                    "status": "candidates_ready",
                    "research_run_ids": [second_run_id],
                },
            )
            schedule["calendar_slots"].append(unrelated)
            write_json(schedule_path, schedule)
            first_run_dir = (
                workspace
                / "research"
                / "runs"
                / "research_run_luna_fit_2026_07_03_001"
            )
            second_run_dir = workspace / "research" / "runs" / second_run_id
            shutil.copytree(first_run_dir, second_run_dir)
            run = read_json(second_run_dir / "research-run.json")
            run.update(
                research_run_id=second_run_id,
                schedule_slot_ids=[unrelated["slot_id"]],
                outputs={
                    "finding_ids": [],
                    "content_opportunity_ids": [],
                    "evidence_ids": ["evidence_luna_fit_002"],
                    "metric_snapshot_ids": [],
                    "research_intelligence_updates": [],
                },
            )
            write_json(second_run_dir / "research-run.json", run)
            plan = read_json(second_run_dir / "search-plan.json")
            plan.update(
                research_search_plan_id=(
                    "research_search_plan_luna_fit_2026_07_03_002"
                ),
                research_run_id=second_run_id,
                schedule_slot_ids=[unrelated["slot_id"]],
            )
            write_json(second_run_dir / "search-plan.json", plan)
            evidence = json.loads(
                (second_run_dir / "evidence.jsonl").read_text().splitlines()[0]
            )
            evidence.update(
                research_run_id=second_run_id,
                evidence_id="evidence_luna_fit_002",
            )
            (second_run_dir / "evidence.jsonl").write_text(
                json.dumps(evidence) + "\n"
            )
            (second_run_dir / "metric-snapshots.jsonl").write_text("")
            source_yield = json.loads(
                (second_run_dir / "source-yield.jsonl").read_text().splitlines()[0]
            )
            source_yield.update(
                research_source_yield_id=(
                    "research_source_yield_luna_fit_002"
                ),
                research_run_id=second_run_id,
                evidence_ids=["evidence_luna_fit_002"],
                metric_snapshot_ids=[],
                finding_ids=[],
                content_opportunity_ids=[],
            )
            (second_run_dir / "source-yield.jsonl").write_text(
                json.dumps(source_yield) + "\n"
            )

            result = constructors.scaffold_review_record(
                self.concept_review_seed(review, anchor_slot_id=anchor_slot_id),
                workspace,
                now=datetime.datetime(2026, 7, 12, 10, 30),
            )

            self.assertEqual(result["review_record_id"], review["review_record_id"])

    def test_shared_run_keeps_each_anchor_slots_explicit_candidate_packet_separate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            review = self.write_concept_review_fixture(workspace)
            review_path = workspace / "reviews" / "review_luna_concept_001.json"
            review_path.unlink()
            schedule_path = workspace / "content-schedule.json"
            schedule = read_json(schedule_path)
            anchor_slot_id = schedule["calendar_slots"][0]["slot_id"]
            second_slot = dict(schedule["calendar_slots"][0])
            second_slot.update(
                slot_id="slot_luna_shared_run_packet_002",
                target_date="2026-07-16",
            )
            schedule["calendar_slots"].append(second_slot)
            write_json(schedule_path, schedule)
            run_dir = (
                workspace
                / "research"
                / "runs"
                / "research_run_luna_fit_2026_07_03_001"
            )
            for filename in ("research-run.json", "search-plan.json"):
                run_record = read_json(run_dir / filename)
                run_record["schedule_slot_ids"].append(second_slot["slot_id"])
                write_json(run_dir / filename, run_record)

            queue_dir = workspace / "research" / "content-opportunity-queue"
            source_entry = read_json(
                queue_dir / "entries" / "content_opportunity_luna_fit_002.json"
            )
            queue = read_json(queue_dir / "queue.json")
            second_candidate_refs = []
            for suffix in ("005", "006", "007"):
                candidate = dict(source_entry)
                candidate_id = f"content_opportunity_luna_fit_{suffix}"
                candidate["content_opportunity_id"] = candidate_id
                write_json(queue_dir / "entries" / f"{candidate_id}.json", candidate)
                second_candidate_refs.append(
                    "research/content-opportunity-queue/entries/"
                    f"{candidate_id}.json"
                )
                queue["entry_refs"].append(
                    {
                        "content_opportunity_id": candidate_id,
                        "status": "shortlisted",
                    }
                )
            queue["status_counts"] = {"assigned": 1, "shortlisted": 6}
            write_json(queue_dir / "queue.json", queue)
            second_slot["research_state"] = {
                **second_slot["research_state"],
                "candidate_content_opportunity_ids": [
                    Path(ref).stem for ref in second_candidate_refs
                ],
            }
            schedule["calendar_slots"][1] = second_slot
            write_json(schedule_path, schedule)

            contaminated_review = dict(review)
            contaminated_review["artifact_refs"] = [
                ref
                for ref in review["artifact_refs"]
                if "content-opportunity-queue/entries/" not in ref
            ] + second_candidate_refs

            with self.assertRaisesRegex(
                ValidationError, "named Anchor Slot.*candidate packet"
            ):
                constructors.scaffold_review_record(
                    self.concept_review_seed(
                        contaminated_review, anchor_slot_id=anchor_slot_id
                    ),
                    workspace,
                    now=datetime.datetime(2026, 7, 12, 10, 30),
                )

            result = constructors.scaffold_review_record(
                self.concept_review_seed(review, anchor_slot_id=anchor_slot_id),
                workspace,
                now=datetime.datetime(2026, 7, 12, 10, 30),
            )

            self.assertEqual(result["review_record_id"], review["review_record_id"])

    def test_standalone_concept_review_validation_pins_filename_and_workspace_creator(self):
        for tamper in ("filename", "creator"):
            with self.subTest(tamper=tamper):
                with tempfile.TemporaryDirectory() as temp_dir:
                    workspace = self.fresh_workspace(temp_dir)
                    self.write_concept_review_fixture(workspace)
                    review_path = (
                        workspace / "reviews" / "review_luna_concept_001.json"
                    )
                    if tamper == "filename":
                        tampered_path = review_path.with_name(
                            "review_luna_concept_copied.json"
                        )
                        review_path.rename(tampered_path)
                    else:
                        review = read_json(review_path)
                        review["creator_profile_id"] = "creator_copied_audit"
                        write_json(review_path, review)
                        tampered_path = review_path

                    with self.assertRaisesRegex(
                        (ValidationError, ValueError),
                        "filename does not match review_record_id|does not match workspace",
                    ):
                        validate_file("review-record", tampered_path)

    def test_standalone_ladder_review_validation_pins_filename_and_workspace_creator(self):
        for tamper in ("filename", "creator"):
            with self.subTest(tamper=tamper):
                with tempfile.TemporaryDirectory() as temp_dir:
                    workspace = self.fresh_workspace(temp_dir)
                    review_id = self.write_quarterly_review_fixture(workspace)
                    review_path = workspace / "reviews" / f"{review_id}.json"
                    if tamper == "filename":
                        tampered_path = review_path.with_name(
                            "review_luna_quarterly_copied.json"
                        )
                        review_path.rename(tampered_path)
                    else:
                        review = read_json(review_path)
                        review["creator_profile_id"] = "creator_copied_audit"
                        write_json(review_path, review)
                        tampered_path = review_path

                    with self.assertRaisesRegex(
                        (ValidationError, ValueError),
                        "filename does not match review_record_id|does not match workspace",
                    ):
                        validate_file("review-record", tampered_path)

    def test_concept_review_constructor_rejects_symlinked_reviews_directory_before_write(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            review = self.write_concept_review_fixture(workspace, persist=False)
            reviews_dir = workspace / "reviews"
            shutil.rmtree(reviews_dir)
            outside_reviews = Path(temp_dir) / "outside-reviews"
            outside_reviews.mkdir()
            reviews_dir.symlink_to(outside_reviews, target_is_directory=True)
            anchor_slot_id = read_json(
                workspace / "content-schedule.json"
            )["calendar_slots"][0]["slot_id"]

            with self.assertRaisesRegex((ValidationError, ValueError), "symlink"):
                constructors.scaffold_review_record(
                    self.concept_review_seed(
                        review, anchor_slot_id=anchor_slot_id
                    ),
                    workspace,
                )

            self.assertEqual(list(outside_reviews.iterdir()), [])

    def test_concept_review_constructor_cli_writes_the_point_in_time_record(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            review = self.write_concept_review_fixture(workspace)
            review_path = workspace / "reviews" / "review_luna_concept_001.json"
            review_path.unlink()
            anchor_slot_id = read_json(
                workspace / "content-schedule.json"
            )["calendar_slots"][0]["slot_id"]
            seed_path = Path(temp_dir) / "concept-review-seed.json"
            write_json(
                seed_path,
                self.concept_review_seed(
                    review, anchor_slot_id=anchor_slot_id
                ),
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "scaffold",
                    "review-record",
                    "--seed",
                    str(seed_path),
                    "--creator-workspace",
                    str(workspace),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(review_path.exists())

    def test_concept_review_artifact_symlink_escape_fails_workspace_and_cli(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            review = self.write_concept_review_fixture(workspace)
            candidate_ref = next(
                ref
                for ref in review["artifact_refs"]
                if ref.endswith("content_opportunity_luna_fit_002.json")
            )
            candidate_path = workspace / candidate_ref
            outside = Path(temp_dir) / "outside-candidate.json"
            outside.write_text(candidate_path.read_text())
            candidate_path.unlink()
            candidate_path.symlink_to(outside)

            with self.assertRaisesRegex((ValidationError, ValueError), "escapes"):
                validate_creator_workspace(workspace)

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "validate",
                    "record",
                    "review-record",
                    str(workspace / "reviews" / "review_luna_concept_001.json"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("escapes", result.stderr)

    def test_concept_review_rejects_research_demand_loop(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            review = self.write_concept_review_fixture(
                workspace, research_demand_loop=True, persist=False
            )

            with self.assertRaisesRegex(
                ValidationError, "research_demand_loop is only allowed"
            ):
                validate_record("review-record", review)

    def test_concept_review_requires_its_source_skill(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            review = self.write_concept_review_fixture(
                workspace, source_skill="review-quarter-plan", persist=False
            )

            with self.assertRaisesRegex(
                ValidationError, "review-concept-promotion"
            ):
                validate_record("review-record", review)

    def test_concept_review_block_is_advisory_workspace_warning(self):
        for approval_status, severity in (
            ("block", "none"),
            ("approve", "blocking"),
        ):
            with self.subTest(
                approval_status=approval_status, severity=severity
            ):
                with tempfile.TemporaryDirectory() as temp_dir:
                    workspace = self.fresh_workspace(temp_dir)
                    self.write_concept_review_fixture(
                        workspace,
                        approval_status=approval_status,
                        severity=severity,
                    )

                    warnings = validate_creator_workspace(workspace)["warnings"]

                    self.assertTrue(
                        any(
                            "review review_luna_concept_001 (concept)" in warning
                            and (
                                "recommends block" in warning
                                or "blocking-severity" in warning
                            )
                            for warning in warnings
                        )
                    )

    def test_concept_review_findings_may_carry_research_demand_markers(self):
        for marker in ("new", "carried_forward"):
            with self.subTest(marker=marker):
                with tempfile.TemporaryDirectory() as temp_dir:
                    workspace = self.fresh_workspace(temp_dir)
                    review = self.write_concept_review_fixture(
                        workspace, research_demand=marker
                    )

                    validate_record("review-record", review)
                    validate_creator_workspace(workspace)

    def test_coming_week_slot_staleness_is_advisory_and_bounded(self):
        today = datetime.date.today()
        cases = (
            ("unresearched", "open", 0, True),
            ("candidates_ready", "open", 6, True),
            ("selected", "open", 2, False),
            ("selected", "filled", 2, False),
            ("unresearched", "open", 7, False),
        )
        for research_status, slot_status, day_offset, should_warn in cases:
            with self.subTest(
                research_status=research_status,
                slot_status=slot_status,
                day_offset=day_offset,
            ):
                with tempfile.TemporaryDirectory() as temp_dir:
                    workspace = self.fresh_workspace(temp_dir)
                    schedule_path = workspace / "content-schedule.json"
                    schedule = read_json(schedule_path)
                    slot = dict(schedule["calendar_slots"][0])
                    slot["slot_id"] = "slot_luna_weekly_probe"
                    for field in (
                        "campaign_id",
                        "campaign_concept_id",
                        "project_id",
                        "variant_id",
                        "content_series_id",
                    ):
                        slot.pop(field, None)
                    slot["target_date"] = (
                        today + datetime.timedelta(days=day_offset)
                    ).isoformat()
                    slot["status"] = slot_status
                    if research_status == "unresearched":
                        slot["research_state"] = {
                            "status": "unresearched",
                            "research_run_ids": [],
                        }
                    elif research_status == "candidates_ready":
                        slot["research_state"] = {
                            "status": "candidates_ready",
                            "research_run_ids": [
                                "research_run_luna_fit_2026_07_03_001"
                            ],
                        }
                    else:
                        slot["research_state"] = {
                            "status": "selected",
                            "research_run_ids": [
                                "research_run_luna_fit_2026_07_03_001"
                            ],
                            "selected_campaign_concept_id": (
                                "campaign_concept_luna_fit_001"
                            ),
                        }
                    schedule["calendar_slots"].append(slot)
                    write_json(schedule_path, schedule)

                    warnings = validate_creator_workspace(workspace)["warnings"]
                    slot_warnings = [
                        warning
                        for warning in warnings
                        if slot["slot_id"] in warning
                        and "Weekly Planning Cycle" in warning
                    ]
                    self.assertEqual(bool(slot_warnings), should_warn)

    def test_coming_week_warning_ignores_workspace_without_schedule(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertEqual(coming_week_staleness_warnings(temp_dir), [])

    def test_approved_quarter_plan_requires_terminal_quarterly_review(self):
        plan = json.loads(
            (ROOT / "examples" / "quarter-plan.example.json").read_text()
        )
        plan.pop("terminal_review_record_id", None)
        with self.assertRaisesRegex(ValidationError, "terminal_review_record_id"):
            from influencer_os.validation import validate_record

            validate_record("quarter-plan", plan)

    def resolving_quarter_seed(self, summary_id):
        seed = dict(QUARTER_SEED)
        seed["retrospective"] = {
            "findings": ["Constraint-visible packaging kept outperforming."],
            "performance_summary_ids": [summary_id],
            "lesson_refs": ["memory/learnings.md#visible-constraint-hook"],
        }
        seed["campaign_concept_set"] = [
            {
                "campaign_concept_id": "campaign_concept_luna_fit_001",
                "disposition": "re_confirmed",
            }
        ]
        seed["campaign_lifecycle_decisions"] = [
            {"campaign_id": "campaign_luna_fit_001", "decision": "continue"}
        ]
        seed["campaign_duration_target_changes"] = [
            {
                "campaign_id": "campaign_luna_fit_001",
                "target_end_date": "2027-07-01",
            }
        ]
        return seed

    def test_resolving_quarter_plan_references_validate_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            summary_id = self.drop_performance_summary(workspace)
            scaffold_quarter_plan(
                self.resolving_quarter_seed(summary_id), workspace
            )
            result = validate_creator_workspace(workspace)
            self.assertEqual(result["creator_profile_id"], "creator_luna_fit")

    def test_reconfirmed_concept_must_be_active_and_rejection_writes_no_plan(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            summary_id = self.drop_performance_summary(workspace)
            concept_path = (
                workspace
                / "campaigns"
                / "campaign_luna_fit_001"
                / "concepts"
                / "campaign_concept_luna_fit_001.json"
            )
            concept = read_json(concept_path)
            concept["status"] = "draft"
            write_json(concept_path, concept)

            with self.assertRaisesRegex(ValidationError, "re_confirmed.*active"):
                scaffold_quarter_plan(
                    self.resolving_quarter_seed(summary_id), workspace
                )
            self.assertEqual(list((workspace / "quarter-plans").glob("*.json")), [])

    def test_dangling_reference_kinds_fail_closed_naming_plan_and_id(self):
        dangling = {
            "campaign_concept_set": (
                [{"campaign_concept_id": "campaign_concept_bogus_999",
                  "disposition": "new"}],
                "campaign_concept_bogus_999",
            ),
            "campaign_lifecycle_decisions": (
                [{"campaign_id": "campaign_bogus_999", "decision": "pause"}],
                "campaign_bogus_999",
            ),
            "campaign_duration_target_changes": (
                [{"campaign_id": "campaign_bogus_999",
                  "target_end_date": "2027-07-01"}],
                "campaign_bogus_999",
            ),
            "performance_summary_ids": (
                ["performance_summary_bogus_999"],
                "performance_summary_bogus_999",
            ),
        }
        for field, (value, dangling_id) in dangling.items():
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as temp_dir:
                    workspace = self.fresh_workspace(temp_dir)
                    summary_id = self.drop_performance_summary(workspace)
                    seed = self.resolving_quarter_seed(summary_id)
                    if field == "performance_summary_ids":
                        seed["retrospective"] = dict(seed["retrospective"])
                        seed["retrospective"]["performance_summary_ids"] = value
                    else:
                        seed[field] = value
                    with self.assertRaises(ValidationError) as ctx:
                        scaffold_quarter_plan(seed, workspace)
                    message = str(ctx.exception)
                    self.assertIn("quarter_plan_luna_fit_001", message)
                    self.assertIn(dangling_id, message)
                    self.assertEqual(
                        list((workspace / "quarter-plans").glob("*.json")), []
                    )

    def test_free_text_lesson_refs_do_not_trigger_closure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            summary_id = self.drop_performance_summary(workspace)
            seed = self.resolving_quarter_seed(summary_id)
            seed["retrospective"]["lesson_refs"] = [
                "an unkeyed distilled lesson line with no record id"
            ]
            scaffold_quarter_plan(seed, workspace)
            validate_creator_workspace(workspace)

    def test_malformed_or_wrong_scope_placeholders_cannot_close_references(self):
        cases = ("campaign", "concept", "performance_summary")
        for record_kind in cases:
            with self.subTest(record_kind=record_kind):
                with tempfile.TemporaryDirectory() as temp_dir:
                    workspace = self.fresh_workspace(temp_dir)
                    summary_id = self.drop_performance_summary(workspace)
                    seed = self.resolving_quarter_seed(summary_id)
                    if record_kind == "campaign":
                        placeholder_id = "campaign_placeholder_001"
                        (workspace / "campaigns" / placeholder_id).mkdir()
                        seed["campaign_lifecycle_decisions"] = [
                            {"campaign_id": placeholder_id, "decision": "pause"}
                        ]
                    elif record_kind == "concept":
                        placeholder_id = "campaign_concept_placeholder_001"
                        path = (
                            workspace
                            / "campaigns"
                            / "campaign_luna_fit_001"
                            / "concepts"
                            / f"{placeholder_id}.json"
                        )
                        write_json(path, {"campaign_concept_id": placeholder_id})
                        seed["campaign_concept_set"] = [
                            {
                                "campaign_concept_id": placeholder_id,
                                "disposition": "new",
                            }
                        ]
                    else:
                        summary_path = (
                            workspace
                            / "projects"
                            / "tiny-reset-after-laptop-day"
                            / "performance-summary.json"
                        )
                        summary = read_json(summary_path)
                        summary["creator_profile_id"] = "creator_wrong_scope"
                        write_json(summary_path, summary)

                    with self.assertRaises(ValidationError):
                        scaffold_quarter_plan(seed, workspace)
                    self.assertEqual(
                        list((workspace / "quarter-plans").glob("*.json")), []
                    )

    def test_terminal_quarterly_review_link_resolves_and_pins_role(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            summary_id = self.drop_performance_summary(workspace)
            review_id = self.write_quarterly_review_fixture(workspace)
            seed = self.resolving_quarter_seed(summary_id)
            seed["terminal_review_record_id"] = review_id
            scaffold_quarter_plan(seed, workspace)
            self.assertEqual(
                validate_creator_workspace(workspace)["creator_profile_id"],
                "creator_luna_fit",
            )

    def test_terminal_review_link_fails_when_missing_or_wrong_role(self):
        # Missing review id.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            summary_id = self.drop_performance_summary(workspace)
            seed = self.resolving_quarter_seed(summary_id)
            seed["terminal_review_record_id"] = "review_luna_quarterly_404"
            with self.assertRaises(ValidationError):
                scaffold_quarter_plan(seed, workspace)
            self.assertEqual(list((workspace / "quarter-plans").glob("*.json")), [])

        # A valid Quarterly Review of a different plan packet cannot close this plan.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            summary_id = self.drop_performance_summary(workspace)
            review_id = self.write_quarterly_review_fixture(
                workspace, packet_plan_id="quarter_plan_luna_fit_999"
            )
            seed = self.resolving_quarter_seed(summary_id)
            seed["terminal_review_record_id"] = review_id
            with self.assertRaisesRegex(ValidationError, "reviewed plan packet"):
                scaffold_quarter_plan(seed, workspace)
            self.assertEqual(list((workspace / "quarter-plans").glob("*.json")), [])

        # Present review but the wrong role.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            summary_id = self.drop_performance_summary(workspace)
            review_id = self.write_quarterly_review_fixture(
                workspace, role="concept"
            )
            seed = self.resolving_quarter_seed(summary_id)
            seed["terminal_review_record_id"] = review_id
            with self.assertRaises(ValidationError):
                scaffold_quarter_plan(seed, workspace)
            self.assertEqual(list((workspace / "quarter-plans").glob("*.json")), [])

    def test_terminal_quarterly_review_enforces_bounded_demand_lineage(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            summary_id = self.drop_performance_summary(workspace)
            self.write_quarterly_review_fixture(
                workspace, research_demand="new"
            )
            with self.assertRaisesRegex(ValidationError, "continue.*loop"):
                scaffold_quarter_plan(
                    self.resolving_quarter_seed(summary_id), workspace
                )
            self.assertEqual(list((workspace / "quarter-plans").glob("*.json")), [])

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            summary_id = self.drop_performance_summary(workspace)
            first = self.write_quarterly_review_fixture(
                workspace,
                review_id="review_luna_quarterly_round_0",
                research_demand="new",
                demand_note="Need a source for the Campaign direction.",
            )
            terminal = self.write_quarterly_review_fixture(
                workspace,
                review_id="review_luna_quarterly_round_1",
                extra_round=1,
                prior_review_record_id=first,
                research_demand="carried_forward",
                demand_note="A different, unissued demand.",
            )
            seed = self.resolving_quarter_seed(summary_id)
            seed["terminal_review_record_id"] = terminal
            with self.assertRaisesRegex(ValidationError, "carried_forward"):
                scaffold_quarter_plan(seed, workspace)
            self.assertEqual(list((workspace / "quarter-plans").glob("*.json")), [])

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            summary_id = self.drop_performance_summary(workspace)
            note = "Need a source for the Campaign direction."
            first = self.write_quarterly_review_fixture(
                workspace,
                review_id="review_luna_quarterly_round_0",
                research_demand="new",
                demand_note=note,
            )
            second = self.write_quarterly_review_fixture(
                workspace,
                review_id="review_luna_quarterly_round_1",
                extra_round=1,
                prior_review_record_id=first,
                research_demand="new",
                demand_note=note,
            )
            terminal = self.write_quarterly_review_fixture(
                workspace,
                review_id="review_luna_quarterly_round_2",
                extra_round=2,
                prior_review_record_id=second,
                research_demand="carried_forward",
                demand_note=note,
            )
            seed = self.resolving_quarter_seed(summary_id)
            seed["terminal_review_record_id"] = terminal
            scaffold_quarter_plan(seed, workspace)

    def test_canonical_documented_seeds_scaffold_and_workspace_validates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = self.fresh_workspace(temp_dir)
            scaffold_quarter_plan(QUARTER_SEED, workspace)
            scaffold_foundation_revision(FOUNDATION_SEED, workspace)
            scaffold_strategy_revision(STRATEGY_SEED, workspace)

            result = validate_creator_workspace(workspace)
            self.assertEqual(result["creator_profile_id"], "creator_luna_fit")


if __name__ == "__main__":
    unittest.main()
