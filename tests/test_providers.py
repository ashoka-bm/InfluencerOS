"""Phase 3 (Generation OS): provider boundary, approval workflow, dispatch.

Guard rules 8-9 (ADR 0023): no code path may dispatch a generation call
without an approved GenerationApprovalRecord id, and the suite never
instantiates a real provider adapter — the deterministic mock is the only
adapter, so these tests are CI-safe and free by construction.
"""

import inspect
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from influencer_os.generation import record_generation_approval
from influencer_os.projects import validate_project
from influencer_os.providers import dispatch as dispatch_module
from influencer_os.providers.dispatch import (
    GenerationDispatchError,
    dispatch_generation,
)
from influencer_os.providers.registry import (
    EXACT_APPROVAL,
    PROVIDERS,
    provider_status,
)
from influencer_os.validation import ValidationError, validate_record
from tests.test_cli import rewrite_json, scaffold_project_workspace


ROOT = Path(__file__).resolve().parents[1]

BASE_CONFIG = {"DISABLE_PAID_CONNECTORS": False}
KILLED_CONFIG = {"DISABLE_PAID_CONNECTORS": True}


def load_example(name):
    return json.loads((ROOT / "examples" / f"{name}.example.json").read_text())


def write_json(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + "\n")


def scaffold_generation_ready_project(temp_dir):
    """A planning-complete project flipped to ready_for_generation."""
    workspace_dir, project_dir = scaffold_project_workspace(temp_dir)
    rewrite_json(
        project_dir / "project.json",
        lambda project: project.update(status="ready_for_generation"),
    )
    return workspace_dir, project_dir


def stage_approval_record(temp_dir, mutate=None):
    record = load_example("generation-approval-record")
    if mutate is not None:
        mutate(record)
    record_path = Path(temp_dir) / "approval-request.json"
    write_json(record_path, record)
    return record_path, record


class ProviderRegistryTests(unittest.TestCase):
    def test_every_provider_is_exact_approval(self):
        # The inverse of the ADR 0022 research-connector carve-out: no
        # generation provider row can express standing approval.
        for row in PROVIDERS:
            self.assertEqual(row["approval_model"], EXACT_APPROVAL)

    def test_registry_fails_closed_on_standing_approval_row(self):
        from influencer_os.providers.registry import _validate_registry

        bad = {"provider_id": "sneaky", "capabilities": ["image"], "key": None,
               "cost_notes": "", "approval_model": "standing", "summary": ""}
        PROVIDERS.append(bad)
        try:
            with self.assertRaisesRegex(ValueError, "structurally 'exact_approval'"):
                _validate_registry()
        finally:
            PROVIDERS.remove(bad)

    def test_key_presence_never_marks_a_provider_approved(self):
        # Availability rows carry no approval state at all; approval lives
        # only in per-call GenerationApprovalRecords.
        for row in provider_status(BASE_CONFIG):
            self.assertEqual(row["approval_model"], EXACT_APPROVAL)
            self.assertNotIn("approved", row)
            self.assertNotIn("standing", str(row.get("reason", "")))

    def test_mock_provider_is_available_without_keys(self):
        rows = {r["provider_id"]: r for r in provider_status(BASE_CONFIG)}
        self.assertTrue(rows["mock"]["available"])

    def test_kill_switch_disables_every_provider(self):
        for row in provider_status(KILLED_CONFIG):
            self.assertFalse(row["available"])
            self.assertIn("kill switch", row["reason"])


class DispatchSeamTests(unittest.TestCase):
    def test_dispatch_requires_approval_record_id_positionally(self):
        # The no-approval-no-call rule is enforced by shape: the parameter
        # exists and has no default.
        signature = inspect.signature(dispatch_generation)
        parameter = signature.parameters["approval_record_id"]
        self.assertIs(parameter.default, inspect.Parameter.empty)

    def test_no_public_dispatch_path_skips_the_approval_record(self):
        # Probe the package surface: every public callable in the dispatch
        # module that can trigger generation requires an approval record id.
        for name, member in vars(dispatch_module).items():
            if name.startswith("_") or not inspect.isfunction(member):
                continue
            if "generat" not in name:
                continue
            parameters = inspect.signature(member).parameters
            self.assertIn(
                "approval_record_id",
                parameters,
                f"public generation path {name} takes no approval_record_id",
            )
            self.assertIs(parameters["approval_record_id"].default, inspect.Parameter.empty)

    def test_dispatch_refuses_without_approval_record(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(GenerationDispatchError, "no approval record"):
                dispatch_generation(temp_dir, "gen_approval_missing", config=BASE_CONFIG)

    def test_kill_switch_refuses_even_with_a_record_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(GenerationDispatchError, "kill switch"):
                dispatch_generation(temp_dir, "gen_approval_any", config=KILLED_CONFIG)


class ApprovalRecordSemanticsTests(unittest.TestCase):
    def test_example_validates(self):
        validate_record("generation-approval-record", load_example("generation-approval-record"))

    def test_scope_requires_exactly_one_target(self):
        record = load_example("generation-approval-record")
        record["reference_asset_id"] = "asset_luna_identity_plate"
        with self.assertRaisesRegex(ValidationError, "exactly one of"):
            validate_record("generation-approval-record", record)
        del record["project_id"]
        del record["reference_asset_id"]
        with self.assertRaisesRegex(ValidationError, "exactly one of"):
            validate_record("generation-approval-record", record)

    def test_single_call_approves_exactly_one_asset(self):
        record = load_example("generation-approval-record")
        record["requested_assets"] = record["requested_assets"] * 2
        record["requested_assets"][1] = {
            **record["requested_assets"][1],
            "asset_id": "gen_asset_luna_tiny_reset_video_002",
        }
        with self.assertRaisesRegex(ValidationError, "exactly one asset"):
            validate_record("generation-approval-record", record)

    def test_batch_requires_and_honors_max_calls(self):
        record = load_example("generation-approval-record")
        record["scope"] = "batch"
        with self.assertRaisesRegex(ValidationError, "bounded max_calls"):
            validate_record("generation-approval-record", record)
        record["max_calls"] = 1
        validate_record("generation-approval-record", record)
        record["requested_assets"] = record["requested_assets"] + [
            {**record["requested_assets"][0], "asset_id": "gen_asset_extra"}
        ]
        with self.assertRaisesRegex(ValidationError, "exceed the approved batch cap"):
            validate_record("generation-approval-record", record)

    def test_draft_carries_no_approval_fields(self):
        record = load_example("generation-approval-record")
        record["status"] = "draft"
        with self.assertRaisesRegex(ValidationError, "draft carries no"):
            validate_record("generation-approval-record", record)
        del record["user_approval_statement"]
        del record["approved_at"]
        validate_record("generation-approval-record", record)

    def test_executed_requires_results_within_request(self):
        record = load_example("generation-approval-record")
        record["status"] = "executed"
        with self.assertRaisesRegex(ValidationError, "executed_at and non-empty"):
            validate_record("generation-approval-record", record)
        record["executed_at"] = "2026-07-06T16:10:00"
        record["resulting_asset_ids"] = ["gen_asset_never_requested"]
        with self.assertRaisesRegex(ValidationError, "not in[\\s\\S]*approved request"):
            validate_record("generation-approval-record", record)


class RecordGenerationApprovalTests(unittest.TestCase):
    def test_happy_path_records_and_validates_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_generation_ready_project(temp_dir)
            record_path, record = stage_approval_record(temp_dir)
            destination = record_generation_approval(project_dir, record_path)
            self.assertTrue(destination.exists())
            validate_project(project_dir)

    def test_refuses_before_ready_for_generation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)  # planning
            record_path, _ = stage_approval_record(temp_dir)
            with self.assertRaisesRegex(ValidationError, "ready_for_generation"):
                record_generation_approval(project_dir, record_path)

    def test_refuses_dangling_plan_ref(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_generation_ready_project(temp_dir)
            record_path, _ = stage_approval_record(
                temp_dir,
                mutate=lambda record: record.update(plan_ref="plan/no-such-plan.json"),
            )
            with self.assertRaisesRegex(ValidationError, "does not resolve"):
                record_generation_approval(project_dir, record_path)

    def test_refuses_unknown_provider(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_generation_ready_project(temp_dir)
            record_path, _ = stage_approval_record(
                temp_dir,
                mutate=lambda record: record.update(provider_id="not_registered"),
            )
            with self.assertRaisesRegex(ValidationError, "unknown generation provider"):
                record_generation_approval(project_dir, record_path)

    def test_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_generation_ready_project(temp_dir)
            record_path, _ = stage_approval_record(temp_dir)
            record_generation_approval(project_dir, record_path)
            with self.assertRaises(FileExistsError):
                record_generation_approval(project_dir, record_path)

    def test_at_rest_hand_edit_with_dangling_plan_ref_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_generation_ready_project(temp_dir)
            record_path, record = stage_approval_record(temp_dir)
            destination = record_generation_approval(project_dir, record_path)
            rewrite_json(
                destination,
                lambda r: r.update(plan_ref="plan/no-such-plan.json"),
            )
            with self.assertRaisesRegex(ValidationError, "does not resolve"):
                validate_project(project_dir)


class DispatchConsumptionTests(unittest.TestCase):
    def approve_and_dispatch(self, temp_dir, mutate=None):
        _, project_dir = scaffold_generation_ready_project(temp_dir)
        record_path, record = stage_approval_record(temp_dir, mutate=mutate)
        record_generation_approval(project_dir, record_path)
        return project_dir, record["generation_approval_record_id"]

    def test_mock_dispatch_executes_and_consumes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir, record_id = self.approve_and_dispatch(temp_dir)
            calls = dispatch_generation(project_dir, record_id, config=BASE_CONFIG)
            self.assertEqual(len(calls), 1)
            artifact = calls[0]["artifact_path"]
            self.assertTrue(Path(artifact).exists())
            stored = json.loads(
                (project_dir / "generation" / "approval-records" / f"{record_id}.json").read_text()
            )
            self.assertEqual(stored["status"], "executed")
            self.assertEqual(stored["resulting_asset_ids"], [calls[0]["asset_id"]])
            # Single-use: a second dispatch on the consumed record refuses.
            with self.assertRaisesRegex(GenerationDispatchError, "already consumed"):
                dispatch_generation(project_dir, record_id, config=BASE_CONFIG)

    def test_dispatch_refuses_draft_and_cancelled(self):
        for status, message in (("draft", "is a draft"), ("cancelled", "is cancelled")):
            with tempfile.TemporaryDirectory() as temp_dir:
                def mutate(record, status=status):
                    record["status"] = status
                    if status == "draft":
                        record.pop("user_approval_statement", None)
                        record.pop("approved_at", None)
                project_dir, record_id = self.approve_and_dispatch(temp_dir, mutate=mutate)
                with self.assertRaisesRegex(GenerationDispatchError, message):
                    dispatch_generation(project_dir, record_id, config=BASE_CONFIG)


class ListProvidersCliTests(unittest.TestCase):
    def test_list_providers_reports_exact_approval(self):
        result = subprocess.run(
            [sys.executable, "-m", "influencer_os", "list-providers"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("approval_model=exact_approval", result.stdout)
        self.assertIn("mock", result.stdout)
        self.assertNotIn("standing", result.stdout)


if __name__ == "__main__":
    unittest.main()
