"""Quarterly cadence record contracts (ADR 0047 core, part A)."""

import datetime
import json
import tempfile
import unittest
from pathlib import Path

from influencer_os.cadence import (
    scaffold_foundation_revision,
    scaffold_quarter_plan,
    scaffold_strategy_revision,
)
from influencer_os.creator_workspaces import validate_creator_workspace
from influencer_os.validation import ValidationError, validate_examples
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
            scaffold_quarter_plan(governed_seed, workspace)
            validate_creator_workspace(workspace)

            unknown_seed = dict(QUARTER_SEED)
            unknown_seed["governing_foundation_revision_id"] = (
                "foundation_revision_luna_fit_999"
            )
            with self.assertRaises(ValidationError):
                scaffold_quarter_plan(unknown_seed, workspace)

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
