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
        with self.assertRaisesRegex(
            ValidationError, "must[\\s\\S]*equal the approved requested_assets"
        ):
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

    def test_injected_config_cannot_reenable_the_kill_switch(self):
        # Batch-1 review finding: the hard stop reads the real environment on
        # every dispatch; config injection can only restrict further.
        import os
        from unittest import mock

        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir, record_id = self.approve_and_dispatch(temp_dir)
            with mock.patch.dict(
                os.environ, {"INFLUENCER_OS_DISABLE_PAID_CONNECTORS": "1"}
            ):
                with self.assertRaisesRegex(GenerationDispatchError, "kill switch"):
                    dispatch_generation(project_dir, record_id, config=BASE_CONFIG)

    def test_dispatch_refuses_forged_record_for_other_project(self):
        # Batch-1 review finding: a hand-written approved record targeting a
        # different project refuses at dispatch, not only at rest.
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_generation_ready_project(temp_dir)
            record = load_example("generation-approval-record")
            record["project_id"] = "project_somebody_else_001"
            write_json(
                project_dir
                / "generation"
                / "approval-records"
                / f"{record['generation_approval_record_id']}.json",
                record,
            )
            with self.assertRaisesRegex(GenerationDispatchError, "targets project"):
                dispatch_generation(
                    project_dir,
                    record["generation_approval_record_id"],
                    config=BASE_CONFIG,
                )

    def test_dispatch_refuses_premature_project_status(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)  # planning
            record = load_example("generation-approval-record")
            write_json(
                project_dir
                / "generation"
                / "approval-records"
                / f"{record['generation_approval_record_id']}.json",
                record,
            )
            with self.assertRaisesRegex(GenerationDispatchError, "ready_for_generation"):
                dispatch_generation(
                    project_dir,
                    record["generation_approval_record_id"],
                    config=BASE_CONFIG,
                )

    def test_dispatch_refuses_traversal_filename(self):
        # Batch-1 review finding: a forged filename cannot write outside
        # generation/assets/.
        with tempfile.TemporaryDirectory() as temp_dir:
            def mutate(record):
                record["requested_assets"][0]["filename"] = "escape.bin"
            project_dir, record_id = self.approve_and_dispatch(temp_dir, mutate=mutate)
            # Forge the traversal AFTER recording (the schema now rejects it
            # at write time), then confirm dispatch still refuses.
            record_path = (
                project_dir / "generation" / "approval-records" / f"{record_id}.json"
            )
            record = json.loads(record_path.read_text())
            record["requested_assets"][0]["filename"] = "../../escape.bin"
            record_path.write_text(json.dumps(record, indent=2) + "\n")
            with self.assertRaisesRegex(
                GenerationDispatchError, "does not validate|bare file name"
            ):
                dispatch_generation(project_dir, record_id, config=BASE_CONFIG)

    def test_dispatch_refuses_executing_record(self):
        # Two-phase consumption (batch-1 review finding): a crashed dispatch
        # leaves `executing`, which never re-runs.
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir, record_id = self.approve_and_dispatch(temp_dir)
            record_path = (
                project_dir / "generation" / "approval-records" / f"{record_id}.json"
            )
            record = json.loads(record_path.read_text())
            record["status"] = "executing"
            record_path.write_text(json.dumps(record, indent=2) + "\n")
            with self.assertRaisesRegex(GenerationDispatchError, "mid-execution|crashed"):
                dispatch_generation(project_dir, record_id, config=BASE_CONFIG)
            # And at rest it warns instead of silently passing.
            result = validate_project(project_dir)
            self.assertTrue(
                any("executing" in warning for warning in result["warnings"])
            )

    def test_prompt_ref_must_point_into_the_approved_plan(self):
        # Batch-1 review finding: a prompt from another file is unapproved
        # content; the writer refuses it.
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_generation_ready_project(temp_dir)
            record_path, _ = stage_approval_record(
                temp_dir,
                mutate=lambda record: record["requested_assets"][0].update(
                    prompt_ref="plan/production-plan.json#hook"
                ),
            )
            with self.assertRaisesRegex(
                ValidationError, "does not point into the approved plan_ref"
            ):
                record_generation_approval(project_dir, record_path)

    def test_executed_results_must_cover_the_request_exactly(self):
        record = load_example("generation-approval-record")
        record["status"] = "executed"
        record["executed_at"] = "2026-07-06T16:10:00"
        record["resulting_asset_ids"] = [
            "gen_asset_luna_tiny_reset_video_001",
            "gen_asset_luna_tiny_reset_video_001",
        ]
        with self.assertRaisesRegex(ValidationError, "duplicate resulting"):
            validate_record("generation-approval-record", record)
        record["scope"] = "batch"
        record["max_calls"] = 2
        record["requested_assets"] = record["requested_assets"] + [
            {**record["requested_assets"][0], "asset_id": "gen_asset_second"}
        ]
        record["resulting_asset_ids"] = ["gen_asset_luna_tiny_reset_video_001"]
        with self.assertRaisesRegex(ValidationError, "exactly"):
            validate_record("generation-approval-record", record)

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


class ManifestSemanticsTests(unittest.TestCase):
    def test_example_validates(self):
        validate_record("generation-asset-manifest", load_example("generation-asset-manifest"))

    def test_generated_row_requires_approval_binding(self):
        manifest = load_example("generation-asset-manifest")
        del manifest["rows"][0]["approval_record_id"]
        with self.assertRaisesRegex(ValidationError, "missing.*approval_record_id"):
            validate_record("generation-asset-manifest", manifest)

    def test_imported_row_requires_import_source(self):
        manifest = load_example("generation-asset-manifest")
        del manifest["rows"][1]["import_source"]
        with self.assertRaisesRegex(ValidationError, "requires import_source"):
            validate_record("generation-asset-manifest", manifest)

    def test_row_shapes_are_mutually_exclusive(self):
        manifest = load_example("generation-asset-manifest")
        manifest["rows"][1]["approval_record_id"] = "gen_approval_luna_tiny_reset_001"
        with self.assertRaisesRegex(ValidationError, "must not carry generated-row"):
            validate_record("generation-asset-manifest", manifest)

    def test_duplicate_asset_ids_and_paths_fail(self):
        manifest = load_example("generation-asset-manifest")
        manifest["rows"].append(dict(manifest["rows"][1]))
        with self.assertRaisesRegex(ValidationError, "duplicate asset ids"):
            validate_record("generation-asset-manifest", manifest)

    def test_artifact_path_outside_assets_dir_fails(self):
        manifest = load_example("generation-asset-manifest")
        manifest["rows"][1]["artifact_path"] = "output-package/assets/smuggled.png"
        with self.assertRaisesRegex(ValidationError, "does not match"):
            validate_record("generation-asset-manifest", manifest)


class ImportGeneratedAssetTests(unittest.TestCase):
    def stage_source(self, temp_dir, name="export.png", content=b"imported-bytes\n"):
        source = Path(temp_dir) / name
        source.write_bytes(content)
        return source

    def test_import_happy_path_writes_manifest_row(self):
        from influencer_os.generation import import_generated_asset, load_asset_manifest

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_generation_ready_project(temp_dir)
            source = self.stage_source(temp_dir)
            destination = import_generated_asset(
                project_dir,
                source,
                "gen_asset_luna_import_001",
                "image",
                source="Provider web UI export",
                tool_or_provider="external-image-tool",
                license_text="operator-generated, full rights",
            )
            self.assertTrue(destination.exists())
            manifest = load_asset_manifest(project_dir)
            self.assertEqual(len(manifest["rows"]), 1)
            row = manifest["rows"][0]
            self.assertEqual(row["origin"], "imported")
            self.assertEqual(row["artifact_path"], "generation/assets/export.png")
            self.assertNotIn("warnings", row["import_source"])
            validate_project(project_dir)

    def test_unknown_license_is_captured_not_guessed(self):
        from influencer_os.generation import (
            UNKNOWN_LICENSE_WARNING,
            import_generated_asset,
            load_asset_manifest,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_generation_ready_project(temp_dir)
            source = self.stage_source(temp_dir)
            import_generated_asset(
                project_dir, source, "gen_asset_luna_import_002", "image"
            )
            row = load_asset_manifest(project_dir)["rows"][0]
            self.assertNotIn("license", row["import_source"])
            self.assertIn(UNKNOWN_LICENSE_WARNING, row["import_source"]["warnings"])

    def test_containment_escape_filename_refused(self):
        from influencer_os.generation import import_generated_asset

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_generation_ready_project(temp_dir)
            source = self.stage_source(temp_dir)
            with self.assertRaisesRegex(ValidationError, "bare file name"):
                import_generated_asset(
                    project_dir,
                    source,
                    "gen_asset_luna_import_003",
                    "image",
                    filename="../../../escape.png",
                )

    def test_duplicate_asset_id_refused_and_copy_rolled_back(self):
        from influencer_os.generation import import_generated_asset

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_generation_ready_project(temp_dir)
            source = self.stage_source(temp_dir)
            import_generated_asset(project_dir, source, "gen_asset_dup", "image")
            with self.assertRaisesRegex(ValidationError, "already has a manifest row"):
                import_generated_asset(
                    project_dir, source, "gen_asset_dup", "image", filename="second.png"
                )
            self.assertFalse(
                (project_dir / "generation" / "assets" / "second.png").exists()
            )

    def test_reference_route_updates_source_block(self):
        from influencer_os.generation import import_reference_asset

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_generation_ready_project(temp_dir)
            source = self.stage_source(temp_dir, name="identity.png")
            destination = import_reference_asset(
                workspace_dir,
                source,
                "asset_luna_identity_plate",
                origin="user_provided",
            )
            self.assertTrue(destination.exists())
            library = json.loads(
                (workspace_dir / "references" / "reference-library.json").read_text()
            )
            asset = next(
                a for a in library["assets"] if a["asset_id"] == "asset_luna_identity_plate"
            )
            self.assertEqual(asset["asset_status"], "user_provided")
            self.assertEqual(asset["source"]["source_type"], "user_provided")

    def test_reference_route_dangling_approval_refused(self):
        from influencer_os.generation import import_reference_asset

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_generation_ready_project(temp_dir)
            source = self.stage_source(temp_dir)
            with self.assertRaisesRegex(ValidationError, "does not resolve"):
                import_reference_asset(
                    workspace_dir,
                    source,
                    "asset_luna_identity_plate",
                    origin="imported",
                    approval_record_id="gen_approval_never_recorded",
                )


class ProvenanceLedgerTests(unittest.TestCase):
    def test_dispatch_appends_generated_manifest_rows(self):
        from influencer_os.generation import load_asset_manifest

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_generation_ready_project(temp_dir)
            record_path, record = stage_approval_record(temp_dir)
            record_generation_approval(project_dir, record_path)
            calls = dispatch_generation(
                project_dir, record["generation_approval_record_id"], config=BASE_CONFIG
            )
            manifest = load_asset_manifest(project_dir)
            self.assertEqual(len(manifest["rows"]), 1)
            row = manifest["rows"][0]
            self.assertEqual(row["origin"], "generated")
            self.assertEqual(
                row["approval_record_id"], record["generation_approval_record_id"]
            )
            self.assertEqual(row["provider_call"]["provider_id"], "mock")
            validate_project(project_dir)

    def test_orphan_asset_file_fails_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_generation_ready_project(temp_dir)
            assets_dir = project_dir / "generation" / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)
            (assets_dir / "smuggled.bin").write_bytes(b"no provenance\n")
            with self.assertRaisesRegex(ValidationError, "no (asset manifest|manifest row)"):
                validate_project(project_dir)

    def test_manifest_row_with_missing_artifact_fails_at_rest(self):
        from tests.test_cli import seed_generation_fixtures

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            seed_generation_fixtures(project_dir)
            (project_dir / "generation" / "assets" / "tiny-reset-thumb-001.png").unlink()
            with self.assertRaisesRegex(ValidationError, "does not resolve"):
                validate_project(project_dir)

    def test_tampered_artifact_fails_hash_check(self):
        from tests.test_cli import seed_generation_fixtures

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            seed_generation_fixtures(project_dir)
            (project_dir / "generation" / "assets" / "tiny-reset-thumb-001.png").write_bytes(
                b"tampered\n"
            )
            with self.assertRaisesRegex(ValidationError, "does not match the recorded hash"):
                validate_project(project_dir)

    def test_generated_row_requires_executed_resolving_approval(self):
        from tests.test_cli import rewrite_json as rewrite, seed_generation_fixtures

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            seed_generation_fixtures(project_dir)
            approval_path = (
                project_dir
                / "generation"
                / "approval-records"
                / "gen_approval_luna_tiny_reset_001.json"
            )

            def revert(record):
                record["status"] = "approved"
                record.pop("executed_at", None)
                record.pop("resulting_asset_ids", None)
            rewrite(approval_path, revert)
            with self.assertRaisesRegex(ValidationError, "not executed"):
                validate_project(project_dir)

    def test_packaged_media_ref_must_resolve_to_a_row(self):
        from tests.test_analytics import scaffold_published_project

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            package_path = project_dir / "output-package" / "output-package.json"
            rewrite_json(
                package_path,
                lambda package: package["upload_ready"][0].update(
                    generation_manifest_ref="gen_asset_never_manifested"
                ),
            )
            with self.assertRaisesRegex(ValueError, "does not[\\s\\S]*resolve to an asset-manifest row"):
                validate_project(project_dir)

    def test_generated_package_requires_media_refs(self):
        package = load_example("output-package")
        del package["upload_ready"][0]["generation_manifest_ref"]
        with self.assertRaisesRegex(ValidationError, "must[\\s\\S]*carry generation_manifest_ref"):
            validate_record("output-package", package)

    def test_planned_package_needs_no_refs(self):
        package = load_example("output-package")
        for asset in package["upload_ready"]:
            asset.pop("generation_manifest_ref", None)
        package["provider_boundary"]["generation_status"] = "planned_not_generated"
        package["provider_boundary"]["provider_calls_made"] = False
        validate_record("output-package", package)

    def test_rebuild_index_covers_generation_records(self):
        from influencer_os.recall_index import rebuild_index, resolve_record_id
        from tests.test_cli import seed_generation_fixtures

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, project_dir = scaffold_project_workspace(temp_dir)
            seed_generation_fixtures(project_dir)
            db_path = Path(temp_dir) / "index.sqlite"
            rebuild_index(workspace_dir, db_path=db_path)
            approval_rows = resolve_record_id(db_path, "gen_approval_luna_tiny_reset_001")
            self.assertEqual(len(approval_rows), 1)
            self.assertEqual(approval_rows[0]["record_type"], "generation-approval-record")
            asset_rows = resolve_record_id(db_path, "gen_asset_luna_tiny_reset_video_001")
            self.assertEqual(len(asset_rows), 1)
            self.assertEqual(asset_rows[0]["record_type"], "generation-asset")


class Batch2HardeningTests(unittest.TestCase):
    def test_concurrent_dispatch_lock_refuses_second_entrant(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_generation_ready_project(temp_dir)
            record_path, record = stage_approval_record(temp_dir)
            record_generation_approval(project_dir, record_path)
            record_id = record["generation_approval_record_id"]
            lock_path = (
                project_dir
                / "generation"
                / "approval-records"
                / f"{record_id}.lock"
            )
            lock_path.write_text("")  # simulate a concurrent holder
            with self.assertRaisesRegex(GenerationDispatchError, "locked by another"):
                dispatch_generation(project_dir, record_id, config=BASE_CONFIG)
            lock_path.unlink()
            dispatch_generation(project_dir, record_id, config=BASE_CONFIG)

    def test_symlinked_assets_dir_refused_everywhere(self):
        from influencer_os.generation import import_generated_asset

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_generation_ready_project(temp_dir)
            assets_dir = project_dir / "generation" / "assets"
            outside = Path(temp_dir) / "outside-assets"
            outside.mkdir()
            assets_dir.rmdir()
            assets_dir.symlink_to(outside)

            source = Path(temp_dir) / "export.png"
            source.write_bytes(b"bytes\n")
            with self.assertRaisesRegex(ValidationError, "symlink"):
                import_generated_asset(project_dir, source, "gen_asset_x", "image")

            record_path, record = stage_approval_record(temp_dir)
            record_generation_approval(project_dir, record_path)
            with self.assertRaisesRegex(GenerationDispatchError, "symlink"):
                dispatch_generation(
                    project_dir,
                    record["generation_approval_record_id"],
                    config=BASE_CONFIG,
                )
            with self.assertRaisesRegex(ValidationError, "symlink"):
                validate_project(project_dir)

    def test_nested_assets_subdirectory_fails_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_generation_ready_project(temp_dir)
            hidden = project_dir / "generation" / "assets" / "subdir"
            hidden.mkdir(parents=True)
            (hidden / "hidden.bin").write_bytes(b"invisible\n")
            with self.assertRaisesRegex(ValidationError, "must be flat"):
                validate_project(project_dir)

    def test_manifest_row_contradicting_request_fails(self):
        from tests.test_cli import rewrite_json as rewrite, seed_generation_fixtures

        for mutate, message in (
            (lambda row: row.update(asset_kind="image"), "contradicts the approved request"),
            (lambda row: row.update(plan_prompt_ref="plan/generation-plan.json#prompt_sequence[1]"),
             "does not match the approved prompt_ref"),
            (lambda row: row["provider_call"].update(model="other-model"),
             "contradict the approval record"),
        ):
            with tempfile.TemporaryDirectory() as temp_dir:
                _, project_dir = scaffold_project_workspace(temp_dir)
                seed_generation_fixtures(project_dir)
                rewrite(
                    project_dir / "generation" / "asset-manifest.json",
                    lambda manifest: mutate(manifest["rows"][0]),
                )
                with self.assertRaisesRegex(ValidationError, message):
                    validate_project(project_dir)

    def test_role_kind_lineage_enforced_on_packaged_refs(self):
        from tests.test_analytics import scaffold_published_project
        from tests.test_cli import rewrite_json as rewrite

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            rewrite(
                project_dir / "output-package" / "output-package.json",
                lambda package: package["upload_ready"][0].update(
                    generation_manifest_ref="gen_asset_luna_tiny_reset_thumb_001"
                ),
            )
            with self.assertRaisesRegex(ValueError, "cannot trace to a"):
                validate_project(project_dir)

    def test_generation_status_must_match_referenced_origins(self):
        from tests.test_analytics import scaffold_published_project
        from tests.test_cli import rewrite_json as rewrite

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            rewrite(
                project_dir / "output-package" / "output-package.json",
                lambda package: package["provider_boundary"].update(
                    generation_status="imported"
                ),
            )
            with self.assertRaisesRegex(ValueError, "contradicts referenced generated"):
                validate_project(project_dir)

    def test_reference_import_refuses_symlinked_destination(self):
        from influencer_os.generation import import_reference_asset

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_generation_ready_project(temp_dir)
            library = json.loads(
                (workspace_dir / "references" / "reference-library.json").read_text()
            )
            asset = next(
                a for a in library["assets"] if a["asset_id"] == "asset_luna_identity_plate"
            )
            destination = workspace_dir / asset["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            outside = Path(temp_dir) / "outside-target.png"
            outside.write_bytes(b"outside\n")
            destination.symlink_to(outside)

            source = Path(temp_dir) / "identity.png"
            source.write_bytes(b"identity bytes\n")
            with self.assertRaisesRegex(ValidationError, "symlink"):
                import_reference_asset(
                    workspace_dir, source, "asset_luna_identity_plate"
                )


class QualityReviewTests(unittest.TestCase):
    def test_example_validates(self):
        validate_record("quality-review", load_example("quality-review"))

    def test_checklist_must_cover_every_check_exactly_once(self):
        review = load_example("quality-review")
        review["checklist"][1]["check"] = "identity_consistency"
        with self.assertRaisesRegex(ValidationError, "exactly once"):
            validate_record("quality-review", review)

    def test_verdict_must_agree_with_items(self):
        review = load_example("quality-review")
        review["checklist"][0]["result"] = "fail"
        with self.assertRaisesRegex(ValidationError, "failing checklist item"):
            validate_record("quality-review", review)
        review["overall_verdict"] = "fail"
        validate_record("quality-review", review)
        review["checklist"][0]["result"] = "pass"
        with self.assertRaisesRegex(ValidationError, "requires at[\\s\\S]*least one"):
            validate_record("quality-review", review)

    def test_review_scoping_unknown_assets_fails_at_rest(self):
        from tests.test_cli import rewrite_json as rewrite, seed_generation_fixtures

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            seed_generation_fixtures(project_dir)
            rewrite(
                project_dir
                / "generation"
                / "quality-reviews"
                / "quality_review_luna_tiny_reset_001.json",
                lambda review: review.update(
                    scope_asset_ids=["gen_asset_never_manifested"]
                ),
            )
            with self.assertRaisesRegex(ValidationError, "no[\\s\\S]*manifest row"):
                validate_project(project_dir)

    def test_generated_without_review_warns(self):
        from tests.test_cli import seed_generation_fixtures

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            seed_generation_fixtures(project_dir)
            review_path = (
                project_dir
                / "generation"
                / "quality-reviews"
                / "quality_review_luna_tiny_reset_001.json"
            )
            review_path.unlink()
            result = validate_project(project_dir)
            self.assertTrue(
                any("quality review" in warning for warning in result["warnings"])
            )


class PackagingQualityGateTests(unittest.TestCase):
    def stage_package(self, temp_dir, project_dir):
        from tests.test_cli import copy_example_record, write_upload_ready_assets

        package_path = Path(temp_dir) / "output-package.json"
        copy_example_record("output-package.example.json", package_path)
        package = json.loads(package_path.read_text())
        asset_root = Path(temp_dir) / "source-assets"
        write_upload_ready_assets(asset_root, package)
        return package_path, asset_root

    def test_packaging_refuses_without_passing_review(self):
        # Exit criterion 4: register-output-package fails when generation
        # media lacks a passing QualityReview.
        from influencer_os.projects import register_output_package
        from tests.test_cli import seed_generation_fixtures

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            seed_generation_fixtures(project_dir)
            (
                project_dir
                / "generation"
                / "quality-reviews"
                / "quality_review_luna_tiny_reset_001.json"
            ).unlink()
            package_path, asset_root = self.stage_package(temp_dir, project_dir)
            with self.assertRaisesRegex(ValueError, "no passing QualityReview"):
                register_output_package(project_dir, package_path, asset_root=asset_root)
            # Rollback: the refusal leaves the project unpackaged.
            project = json.loads((project_dir / "project.json").read_text())
            self.assertEqual(project["status"], "generated")

    def test_hand_flipped_failing_review_fails_at_rest(self):
        # Exit criterion 4 at-rest parity: flipping a passing review to
        # failing after packaging makes validate project fail.
        from tests.test_analytics import scaffold_published_project
        from tests.test_cli import rewrite_json as rewrite

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)

            def flip(review):
                review["checklist"][0]["result"] = "fail"
                review["overall_verdict"] = "fail"
            rewrite(
                project_dir
                / "generation"
                / "quality-reviews"
                / "quality_review_luna_tiny_reset_001.json",
                flip,
            )
            with self.assertRaisesRegex(ValueError, "no passing QualityReview"):
                validate_project(project_dir)


class MockEndToEndChainTests(unittest.TestCase):
    def test_mock_generation_to_packaging_chain(self):
        # Exit criterion 5: approval -> mock dispatch -> quality review ->
        # packaging; every upload-ready media asset resolves through the
        # manifest to its approval record and plan.
        from influencer_os.generation import import_generated_asset, load_asset_manifest
        from influencer_os.projects import register_output_package
        from tests.test_cli import copy_example_record, write_upload_ready_assets

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_generation_ready_project(temp_dir)

            # Approve and dispatch the mock video generation.
            record_path, record = stage_approval_record(
                temp_dir,
                mutate=lambda r: r["requested_assets"][0].update(
                    filename="tiny-reset-video-001.mp4"
                ),
            )
            record_generation_approval(project_dir, record_path)
            dispatch_generation(
                project_dir, record["generation_approval_record_id"], config=BASE_CONFIG
            )

            # Import the externally made thumbnail.
            thumb_source = Path(temp_dir) / "thumb-export.png"
            thumb_source.write_bytes(b"external thumbnail bytes\n")
            import_generated_asset(
                project_dir,
                thumb_source,
                "gen_asset_luna_tiny_reset_thumb_001",
                "image",
                filename="tiny-reset-thumb-001.png",
                source="Provider web UI export",
                license_text="operator-generated, full rights",
            )

            # Quality-review the batch, then package.
            review = load_example("quality-review")
            reviews_dir = project_dir / "generation" / "quality-reviews"
            reviews_dir.mkdir(parents=True, exist_ok=True)
            write_json(
                reviews_dir / f"{review['quality_review_id']}.json", review
            )

            package_path = Path(temp_dir) / "output-package.json"
            copy_example_record("output-package.example.json", package_path)
            package = json.loads(package_path.read_text())
            package["provider_boundary"]["generation_status"] = "generated"
            package["provider_boundary"]["provider_calls_made"] = True
            write_json(package_path, package)
            asset_root = Path(temp_dir) / "source-assets"
            write_upload_ready_assets(asset_root, package)
            register_output_package(project_dir, package_path, asset_root=asset_root)

            result = validate_project(project_dir)
            self.assertEqual(
                json.loads((project_dir / "project.json").read_text())["status"],
                "packaged",
            )
            # Chain resolution: each packaged media ref -> manifest row ->
            # (generated) executed approval naming the plan.
            manifest = load_asset_manifest(project_dir)
            rows = {row["asset_id"]: row for row in manifest["rows"]}
            packaged = json.loads(
                (project_dir / "output-package" / "output-package.json").read_text()
            )
            media_refs = [
                asset["generation_manifest_ref"]
                for asset in packaged["upload_ready"]
                if "generation_manifest_ref" in asset
            ]
            self.assertEqual(len(media_refs), 2)
            for ref in media_refs:
                self.assertIn(ref, rows)
            video_row = rows["gen_asset_luna_tiny_reset_video_001"]
            self.assertEqual(
                video_row["approval_record_id"],
                record["generation_approval_record_id"],
            )
            self.assertTrue(video_row["plan_prompt_ref"].startswith("plan/generation-plan.json"))


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
