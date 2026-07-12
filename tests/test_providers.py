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
from unittest import mock

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
from tests.support import scaffold_project_workspace


ROOT = Path(__file__).resolve().parents[1]

BASE_CONFIG = {"DISABLE_PAID_CONNECTORS": False}
KILLED_CONFIG = {"DISABLE_PAID_CONNECTORS": True}


def copy_example_record(example_name, destination):
    destination.write_text((ROOT / "examples" / example_name).read_text())


def rewrite_json(path, mutate):
    record = json.loads(path.read_text())
    mutate(record)
    path.write_text(json.dumps(record, indent=2) + "\n")


rewrite = rewrite_json


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

    def test_provider_registry_keys_are_loaded_by_normal_configuration(self):
        from influencer_os.connectors import env

        keyed_provider = {
            "provider_id": "future-test-provider",
            "capabilities": ["image"],
            "key": "FUTURE_PROVIDER_API_KEY",
            "cost_notes": "test only",
            "approval_model": EXACT_APPROVAL,
            "summary": "Test provider with its own key.",
        }
        PROVIDERS.append(keyed_provider)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                env_path = Path(tmp) / ".env"
                env_path.write_text("FUTURE_PROVIDER_API_KEY=available\n")
                with mock.patch.dict("os.environ", {}, clear=True):
                    config = env.get_config(env_path=env_path)

            rows = {row["provider_id"]: row for row in provider_status(config)}
            self.assertEqual(config["FUTURE_PROVIDER_API_KEY"], "available")
            self.assertTrue(rows["future-test-provider"]["available"])
        finally:
            PROVIDERS.remove(keyed_provider)

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


class CreatorSetupStandingApprovalTests(unittest.TestCase):
    def _prompt_ready_workspace(self, temp_dir):
        from tests.test_readiness_validation import make_ready_workspace

        workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
        plan = json.loads(
            (workspace_dir / "references" / "visual-continuity-plan.json").read_text()
        )
        authorized = set(plan["setup_reference_generation"]["asset_ids"])
        library_path = workspace_dir / "references" / "reference-library.json"
        library = json.loads(library_path.read_text())
        for asset in library["assets"]:
            if asset["asset_id"] not in authorized:
                continue
            asset["asset_status"] = "prompted"
            asset["prompt_path"] = (
                f"references/{asset['asset_type']}/{asset['asset_id']}.prompt.md"
            )
            target = workspace_dir / asset["path"]
            target.unlink(missing_ok=True)
            prompt = workspace_dir / asset["prompt_path"]
            prompt.parent.mkdir(parents=True, exist_ok=True)
            prompt.write_text(f"Prompt for {asset['asset_id']}.\n")
        write_json(library_path, library)
        return workspace_dir, sorted(authorized)

    def test_derives_single_use_records_from_approved_visual_plan(self):
        from influencer_os.generation import derive_setup_reference_approvals

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, authorized = self._prompt_ready_workspace(temp_dir)
            paths = derive_setup_reference_approvals(
                workspace_dir,
                provider_id="mock",
                model="mock-1",
                cost_note="Mock; zero cost.",
            )

            self.assertEqual(len(paths), len(authorized))
            records = [json.loads(path.read_text()) for path in paths]
            self.assertEqual(
                {record["reference_asset_id"] for record in records}, set(authorized)
            )
            self.assertTrue(all(record["scope"] == "single_call" for record in records))
            self.assertTrue(
                all("approved Visual Continuity Plan" in record["user_approval_statement"] for record in records)
            )
            self.assertEqual(
                derive_setup_reference_approvals(
                    workspace_dir,
                    provider_id="mock",
                    model="mock-1",
                    cost_note="Mock; zero cost.",
                ),
                paths,
            )

            with self.assertRaisesRegex(FileExistsError, "already recorded"):
                derive_setup_reference_approvals(
                    workspace_dir,
                    provider_id="mock",
                    model="different-model",
                    cost_note="Changed route.",
                )

    def test_visual_plan_derivation_excludes_the_designated_avatar(self):
        from influencer_os.generation import derive_setup_reference_approvals

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = self._prompt_ready_workspace(temp_dir)
            board = json.loads(
                (workspace_dir / "references" / "brand" / "personal-brand-board.json").read_text()
            )
            plan_path = workspace_dir / "references" / "visual-continuity-plan.json"
            plan = json.loads(plan_path.read_text())
            plan["setup_reference_generation"]["asset_ids"].append(
                board["avatar_asset_id"]
            )
            plan["setup_reference_generation"]["max_calls"] = len(
                plan["setup_reference_generation"]["asset_ids"]
            )
            write_json(plan_path, plan)

            with self.assertRaisesRegex(ValidationError, "exclude the designated Avatar Image"):
                derive_setup_reference_approvals(
                    workspace_dir,
                    provider_id="mock",
                    model="mock-1",
                    cost_note="Mock; zero cost.",
                )

    def test_setup_approval_derivation_refuses_shared_lock(self):
        from influencer_os.generation import derive_setup_reference_approvals

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = self._prompt_ready_workspace(temp_dir)
            lock_path = workspace_dir / "references" / "setup-approval-derivation.lock"
            lock_path.write_text("busy\n")

            with self.assertRaisesRegex(FileExistsError, "already running"):
                derive_setup_reference_approvals(
                    workspace_dir,
                    provider_id="mock",
                    model="mock-1",
                    cost_note="Mock; zero cost.",
                )
            self.assertFalse(
                (workspace_dir / "references" / "approval-records").exists()
            )

    def test_reference_dispatch_is_single_use_and_updates_library(self):
        from influencer_os.generation import derive_setup_reference_approvals
        from influencer_os.providers.dispatch import dispatch_reference_generation

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = self._prompt_ready_workspace(temp_dir)
            approval_paths = derive_setup_reference_approvals(
                workspace_dir,
                provider_id="mock",
                model="mock-1",
                cost_note="Mock; zero cost.",
            )
            record = json.loads(approval_paths[0].read_text())
            notices = []
            calls = dispatch_reference_generation(
                workspace_dir,
                record["generation_approval_record_id"],
                config=BASE_CONFIG,
                notice_callback=notices.append,
            )

            self.assertEqual(len(calls), 1)
            self.assertIn("provider=mock", notices[0])
            self.assertIn("model=mock-1", notices[0])
            self.assertIn("calls=1", notices[0])
            self.assertIn("cost=Mock; zero cost.", notices[0])
            library = json.loads(
                (workspace_dir / "references" / "reference-library.json").read_text()
            )
            asset = next(
                item for item in library["assets"]
                if item["asset_id"] == record["reference_asset_id"]
            )
            self.assertEqual(asset["asset_status"], "generated")
            self.assertEqual(asset["source"]["source_ref"], record["generation_approval_record_id"])
            self.assertTrue((workspace_dir / asset["path"]).is_file())
            from influencer_os.brand_boards import validate_brand_board

            validate_brand_board(workspace_dir)

            with self.assertRaisesRegex(GenerationDispatchError, "already consumed"):
                dispatch_reference_generation(
                    workspace_dir,
                    record["generation_approval_record_id"],
                    config=BASE_CONFIG,
                )

    def test_reference_dispatch_rejects_changed_frozen_scope(self):
        from influencer_os.generation import derive_setup_reference_approvals
        from influencer_os.providers.dispatch import dispatch_reference_generation

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = self._prompt_ready_workspace(temp_dir)
            approval_path = derive_setup_reference_approvals(
                workspace_dir,
                provider_id="mock",
                model="mock-1",
                cost_note="Mock; zero cost.",
            )[0]
            record = json.loads(approval_path.read_text())
            plan_path = workspace_dir / "references" / "visual-continuity-plan.json"
            plan = json.loads(plan_path.read_text())
            plan["setup_reference_generation"]["notice"] += " Changed."
            plan_path.write_text(json.dumps(plan, indent=2) + "\n")

            with self.assertRaisesRegex(GenerationDispatchError, "changed after"):
                dispatch_reference_generation(
                    workspace_dir,
                    record["generation_approval_record_id"],
                    config=BASE_CONFIG,
                )

    def test_reference_dispatch_rejects_changed_prompt_content(self):
        from influencer_os.generation import derive_setup_reference_approvals
        from influencer_os.providers.dispatch import dispatch_reference_generation

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = self._prompt_ready_workspace(temp_dir)
            approval_path = derive_setup_reference_approvals(
                workspace_dir,
                provider_id="mock",
                model="mock-1",
                cost_note="Mock; zero cost.",
            )[0]
            record = json.loads(approval_path.read_text())
            prompt_path = workspace_dir / record["requested_assets"][0]["prompt_ref"]
            prompt_path.write_text(prompt_path.read_text() + "Changed prompt.\n")

            with self.assertRaisesRegex(GenerationDispatchError, "prompt.*changed"):
                dispatch_reference_generation(
                    workspace_dir,
                    record["generation_approval_record_id"],
                    config=BASE_CONFIG,
                )

    def test_reference_dispatch_refuses_shared_library_lock_without_consuming(self):
        from influencer_os.generation import derive_setup_reference_approvals
        from influencer_os.providers.dispatch import dispatch_reference_generation

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = self._prompt_ready_workspace(temp_dir)
            approval_path = derive_setup_reference_approvals(
                workspace_dir,
                provider_id="mock",
                model="mock-1",
                cost_note="Mock; zero cost.",
            )[0]
            record = json.loads(approval_path.read_text())
            lock_path = workspace_dir / "references" / "reference-library.lock"
            lock_path.write_text("busy\n")

            with self.assertRaisesRegex(GenerationDispatchError, "Reference Library is locked"):
                dispatch_reference_generation(
                    workspace_dir,
                    record["generation_approval_record_id"],
                    config=BASE_CONFIG,
                )

            self.assertEqual(json.loads(approval_path.read_text())["status"], "approved")

    def test_reference_dispatch_rejects_tampered_request_fields(self):
        from influencer_os.generation import derive_setup_reference_approvals
        from influencer_os.providers.dispatch import dispatch_reference_generation

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = self._prompt_ready_workspace(temp_dir)
            approval_path = derive_setup_reference_approvals(
                workspace_dir,
                provider_id="mock",
                model="mock-1",
                cost_note="Mock; zero cost.",
            )[0]
            record = json.loads(approval_path.read_text())
            record["requested_assets"][0]["asset_id"] = "gen_asset_tampered"
            approval_path.write_text(json.dumps(record, indent=2) + "\n")

            with self.assertRaisesRegex(GenerationDispatchError, "scope changed"):
                dispatch_reference_generation(
                    workspace_dir,
                    record["generation_approval_record_id"],
                    config=BASE_CONFIG,
                )

    def test_reference_dispatch_rejects_symlinked_prompt(self):
        from influencer_os.generation import derive_setup_reference_approvals
        from influencer_os.providers.dispatch import dispatch_reference_generation

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = self._prompt_ready_workspace(temp_dir)
            approval_path = derive_setup_reference_approvals(
                workspace_dir,
                provider_id="mock",
                model="mock-1",
                cost_note="Mock; zero cost.",
            )[0]
            record = json.loads(approval_path.read_text())
            prompt_path = workspace_dir / record["requested_assets"][0]["prompt_ref"]
            external_prompt = Path(temp_dir) / "external.prompt.md"
            external_prompt.write_text(prompt_path.read_text())
            prompt_path.unlink()
            prompt_path.symlink_to(external_prompt)

            with self.assertRaisesRegex(GenerationDispatchError, "symlink"):
                dispatch_reference_generation(
                    workspace_dir,
                    record["generation_approval_record_id"],
                    config=BASE_CONFIG,
                )


class AvatarAutoGenerationTests(unittest.TestCase):
    """ADR 0045's single, system-derived creator-setup call."""

    def _avatar_prompt_ready_workspace(self, temp_dir):
        from influencer_os.brand_boards import rebuild_brand_board
        from tests.test_readiness_validation import make_ready_workspace

        workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
        profile_path = workspace_dir / "creator-profile.json"
        profile = json.loads(profile_path.read_text())
        profile["content_strategy"]["content_mediums"] = ["text"]
        profile["reference_refs"]["primary_character_asset_ids"] = []
        profile["reference_refs"]["primary_location_asset_ids"] = []
        profile["reference_refs"].pop("primary_video_style_asset_id", None)
        write_json(profile_path, profile)

        board_path = workspace_dir / "references" / "brand" / "personal-brand-board.json"
        board = json.loads(board_path.read_text())
        board["production_spaces"] = []
        board["signature_props"] = []

        library_path = workspace_dir / "references" / "reference-library.json"
        library = json.loads(library_path.read_text())
        avatar_id = board["avatar_asset_id"]
        avatar = next(asset for asset in library["assets"] if asset["asset_id"] == avatar_id)
        avatar["asset_status"] = "prompted"
        avatar["prompt_path"] = "references/character/avatar.prompt.md"
        (workspace_dir / avatar["path"]).unlink(missing_ok=True)
        prompt_path = workspace_dir / avatar["prompt_path"]
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text("Prompt for the platform-facing avatar.\n")
        library["assets"] = [
            avatar,
            next(asset for asset in library["assets"] if asset["asset_id"] == "asset_luna_brand_system"),
            next(asset for asset in library["assets"] if asset["asset_id"] == "asset_luna_elevenlabs_voice_design"),
        ]
        write_json(library_path, library)
        declared_prompts = {
            asset["prompt_path"] for asset in library["assets"] if asset.get("prompt_path")
        }
        for path in (workspace_dir / "references").rglob("*.prompt.md"):
            if path.relative_to(workspace_dir).as_posix() not in declared_prompts:
                path.unlink()
        write_json(board_path, board)

        plan_path = workspace_dir / "references" / "visual-continuity-plan.json"
        plan = json.loads(plan_path.read_text())
        plan["candidates"] = []
        plan["selection_review"] = {
            "status": "draft",
            "presented_on": None,
            "decided_on": None,
            "decided_by": None,
            "notes": "Avatar generation precedes Visual Continuity Plan approval.",
        }
        plan["setup_reference_generation"] = {
            "status": "not_authorized",
            "asset_ids": [],
            "max_calls": 0,
            "authorized_on": None,
            "authorized_by": None,
            "notice": "Visual Continuity Plan has not been approved; setup reference generation is not authorized.",
        }
        write_json(plan_path, plan)
        rebuild_brand_board(workspace_dir)
        return workspace_dir, avatar_id

    def test_avatar_approval_derives_without_visual_continuity_plan(self):
        from influencer_os.generation import derive_avatar_approval

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, avatar_id = self._avatar_prompt_ready_workspace(temp_dir)
            paths = derive_avatar_approval(
                workspace_dir,
                provider_id="mock",
                model="mock-1",
                cost_note="Mock; zero cost.",
            )

            self.assertEqual(len(paths), 1)
            record = json.loads(paths[0].read_text())
            self.assertEqual(record["approval_basis"], "system_avatar_setup")
            self.assertEqual(record["scope"], "batch")
            self.assertEqual(record["max_calls"], 1)
            self.assertEqual(record["reference_asset_id"], avatar_id)
            self.assertEqual(record["status"], "approved")
            self.assertNotIn("user_approval_statement", record)
            self.assertEqual(len(record["requested_assets"]), 1)
            self.assertEqual(record["requested_assets"][0]["asset_kind"], "image")
            self.assertNotIn(
                "user_approval_statement",
                inspect.signature(derive_avatar_approval).parameters,
            )

    def test_avatar_dispatch_generates_with_no_prompt_and_reconciles(self):
        from influencer_os.generation import derive_avatar_approval
        from influencer_os.providers.dispatch import dispatch_avatar_generation

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, avatar_id = self._avatar_prompt_ready_workspace(temp_dir)
            approval_path = derive_avatar_approval(
                workspace_dir,
                provider_id="mock",
                model="mock-1",
                cost_note="Mock; zero cost.",
            )[0]
            record = json.loads(approval_path.read_text())
            calls = dispatch_avatar_generation(
                workspace_dir,
                record["generation_approval_record_id"],
                config=BASE_CONFIG,
            )

            self.assertEqual(len(calls), 1)
            library = json.loads(
                (workspace_dir / "references" / "reference-library.json").read_text()
            )
            avatar = next(asset for asset in library["assets"] if asset["asset_id"] == avatar_id)
            self.assertEqual(avatar["asset_status"], "generated")
            self.assertEqual(
                avatar["source"],
                {"source_type": "generated", "source_ref": record["generation_approval_record_id"]},
            )
            self.assertTrue((workspace_dir / avatar["path"]).is_file())
            executed = json.loads(approval_path.read_text())
            self.assertEqual(executed["status"], "executed")
            self.assertEqual(executed["resulting_asset_ids"], [record["requested_assets"][0]["asset_id"]])
            result = subprocess.run(
                [sys.executable, "-m", "influencer_os", "validate", "workspace", str(workspace_dir)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_avatar_carve_out_cannot_widen(self):
        from influencer_os.generation import (
            derive_avatar_approval,
            validate_avatar_approval_binding,
        )
        from influencer_os.providers.dispatch import dispatch_avatar_generation

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = self._avatar_prompt_ready_workspace(temp_dir)
            approval_path = derive_avatar_approval(
                workspace_dir,
                provider_id="mock",
                model="mock-1",
                cost_note="Mock; zero cost.",
            )[0]
            with self.assertRaisesRegex(FileExistsError, "already recorded"):
                derive_avatar_approval(
                    workspace_dir,
                    provider_id="mock",
                    model="mock-1",
                    cost_note="Mock; zero cost.",
                )

            forged = json.loads(approval_path.read_text())
            forged["generation_approval_record_id"] = "gen_approval_luna_fit_avatar_forged"
            forged["reference_asset_id"] = "asset_luna_brand_system"
            forged_path = approval_path.with_name(
                f"{forged['generation_approval_record_id']}.json"
            )
            write_json(forged_path, forged)
            with self.assertRaisesRegex(ValidationError, "designated single-use id"):
                validate_avatar_approval_binding(workspace_dir, forged)
            with self.assertRaisesRegex(GenerationDispatchError, "designated single-use id"):
                dispatch_avatar_generation(
                    workspace_dir,
                    forged["generation_approval_record_id"],
                    config=BASE_CONFIG,
                )

    def test_avatar_semantics_are_bounded_and_other_bases_stay_fail_closed(self):
        from influencer_os.validation import validate_generation_approval_semantics

        record = load_example("generation-approval-record")
        record.update(
            approval_basis="system_avatar_setup",
            scope="batch",
            max_calls=1,
            reference_asset_id="asset_luna_identity_plate",
        )
        record.pop("project_id")
        record["requested_assets"][0]["asset_kind"] = "image"
        record.pop("user_approval_statement")
        record.pop("approved_at")
        validate_generation_approval_semantics(record)

        for mutate in (
            lambda value: value.update(scope="single_call") or value.pop("max_calls"),
            lambda value: value.update(max_calls=2),
            lambda value: value["requested_assets"][0].update(asset_kind="video"),
            lambda value: value.update(user_approval_statement="I approve this."),
        ):
            invalid = json.loads(json.dumps(record))
            mutate(invalid)
            with self.assertRaises(ValidationError):
                validate_generation_approval_semantics(invalid)

        for basis in (None, "exact_user_statement", "approved_visual_continuity_plan"):
            invalid = json.loads(json.dumps(record))
            invalid["approval_basis"] = basis
            if basis is None:
                invalid.pop("approval_basis")
            with self.assertRaisesRegex(ValidationError, "verbatim user_approval_statement"):
                validate_generation_approval_semantics(invalid)

        project_scoped = json.loads(json.dumps(record))
        project_scoped["project_id"] = "project_luna_tiny_reset_001"
        project_scoped.pop("reference_asset_id")
        with self.assertRaisesRegex(ValidationError, "reference-library scoped"):
            validate_generation_approval_semantics(project_scoped)

    def test_rejected_avatar_can_regenerate_only_from_fresh_exact_reference_approval(self):
        from influencer_os.brand_boards import rebuild_brand_board
        from influencer_os.generation import derive_avatar_approval
        from influencer_os.providers.dispatch import (
            dispatch_avatar_generation,
            dispatch_reference_generation,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, avatar_id = self._avatar_prompt_ready_workspace(temp_dir)
            initial_path = derive_avatar_approval(
                workspace_dir,
                provider_id="mock",
                model="mock-1",
                cost_note="Mock; zero cost.",
            )[0]
            initial = json.loads(initial_path.read_text())
            dispatch_avatar_generation(
                workspace_dir,
                initial["generation_approval_record_id"],
                config=BASE_CONFIG,
            )

            library_path = workspace_dir / "references" / "reference-library.json"
            library = json.loads(library_path.read_text())
            avatar = next(asset for asset in library["assets"] if asset["asset_id"] == avatar_id)
            (workspace_dir / avatar["path"]).unlink()
            avatar["asset_status"] = "prompted"
            write_json(library_path, library)
            rebuild_brand_board(workspace_dir)

            regeneration = {
                **initial,
                "generation_approval_record_id": "gen_approval_luna_fit_avatar_regeneration_001",
                "scope": "single_call",
                "requested_assets": [
                    {
                        **initial["requested_assets"][0],
                        "asset_id": "gen_asset_luna_fit_avatar_regeneration_001",
                    }
                ],
                "user_approval_statement": (
                    "Approved: regenerate the rejected Avatar Image with mock/mock-1, "
                    "one exact reference call."
                ),
                "approved_at": "2026-07-12T12:00:00",
                "approval_basis": "exact_user_statement",
                "created_at": "2026-07-12T12:00:00",
            }
            regeneration.pop("max_calls")
            regeneration.pop("authorization_source_digest")
            input_path = Path(temp_dir) / "avatar-regeneration-approval.json"
            write_json(input_path, regeneration)
            record_generation_approval(workspace_dir, input_path)

            calls = dispatch_reference_generation(
                workspace_dir,
                regeneration["generation_approval_record_id"],
                config=BASE_CONFIG,
            )
            self.assertEqual(len(calls), 1)
            self.assertTrue((workspace_dir / avatar["path"]).is_file())


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

    def test_project_dispatch_rejects_forged_system_avatar_carve_out(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_generation_ready_project(temp_dir)
            record = load_example("generation-approval-record")
            record.update(
                approval_basis="system_avatar_setup",
                scope="batch",
                max_calls=1,
            )
            record["requested_assets"][0]["asset_kind"] = "image"
            record.pop("user_approval_statement")
            record.pop("approved_at")
            record_path = (
                project_dir
                / "generation"
                / "approval-records"
                / f"{record['generation_approval_record_id']}.json"
            )
            write_json(record_path, record)

            with self.assertRaisesRegex(GenerationDispatchError, "reference-library scoped"):
                dispatch_generation(
                    project_dir,
                    record["generation_approval_record_id"],
                    config=BASE_CONFIG,
                )

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

    def test_reference_route_refuses_to_overwrite_prompt_asset_with_media(self):
        from influencer_os.generation import import_reference_asset

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_generation_ready_project(temp_dir)
            library_path = workspace_dir / "references" / "reference-library.json"
            library = json.loads(library_path.read_text())
            prompt_asset = next(
                asset
                for asset in library["assets"]
                if asset["asset_id"] == "asset_luna_elevenlabs_voice_design"
            )
            prompt_path = workspace_dir / prompt_asset["path"]
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            prompt_body = b"# Voice Design Prompt\n"
            prompt_path.write_bytes(prompt_body)
            source = self.stage_source(temp_dir, name="voice-preview.mp3")

            with self.assertRaisesRegex(
                ValidationError, "separate Reference Library asset"
            ):
                import_reference_asset(
                    workspace_dir,
                    source,
                    prompt_asset["asset_id"],
                    origin="user_provided",
                )

            self.assertEqual(prompt_path.read_bytes(), prompt_body)
            self.assertEqual(
                json.loads(library_path.read_text()),
                library,
            )

    def test_reference_route_imports_voice_sample_as_separate_asset(self):
        from influencer_os.generation import import_reference_asset

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_generation_ready_project(temp_dir)
            library_path = workspace_dir / "references" / "reference-library.json"
            library = json.loads(library_path.read_text())
            prompt_path = (
                "references/voice/luna-fit-elevenlabs-voice-design.prompt.md"
            )
            library["assets"].append(
                {
                    "asset_id": "asset_luna_approved_voice_preview",
                    "asset_type": "voice",
                    "asset_status": "planned",
                    "role": "Approved voice preview for spoken continuity",
                    "path": "references/voice/luna-approved-voice-preview.mp3",
                    "prompt_path": prompt_path,
                    "source": {
                        "source_type": "derived",
                        "source_ref": prompt_path,
                    },
                    "created_on": "2026-07-09",
                    "usage_notes": "Import the selected preview here after approval.",
                    "semantic_index_allowed": False,
                }
            )
            write_json(library_path, library)
            source = self.stage_source(temp_dir, name="voice-preview.mp3")

            destination = import_reference_asset(
                workspace_dir,
                source,
                "asset_luna_approved_voice_preview",
                origin="user_provided",
            )

            self.assertEqual(
                destination,
                workspace_dir / "references/voice/luna-approved-voice-preview.mp3",
            )
            imported_library = json.loads(library_path.read_text())
            imported_asset = next(
                asset
                for asset in imported_library["assets"]
                if asset["asset_id"] == "asset_luna_approved_voice_preview"
            )
            self.assertEqual(imported_asset["asset_status"], "user_provided")
            self.assertEqual(imported_asset["prompt_path"], prompt_path)

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
        from tests.support import seed_generation_fixtures

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            seed_generation_fixtures(project_dir)
            (project_dir / "generation" / "assets" / "tiny-reset-thumb-001.png").unlink()
            with self.assertRaisesRegex(ValidationError, "does not resolve"):
                validate_project(project_dir)

    def test_tampered_artifact_fails_hash_check(self):
        from tests.support import seed_generation_fixtures

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            seed_generation_fixtures(project_dir)
            (project_dir / "generation" / "assets" / "tiny-reset-thumb-001.png").write_bytes(
                b"tampered\n"
            )
            with self.assertRaisesRegex(ValidationError, "does not match the recorded hash"):
                validate_project(project_dir)

    def test_generated_row_requires_executed_resolving_approval(self):
        from tests.support import seed_generation_fixtures

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
        from tests.support import seed_generation_fixtures

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
        from tests.support import seed_generation_fixtures

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

    def test_stale_review_does_not_cover_reimported_asset(self):
        # Batch-3 review finding: coverage is content-bound — a review of the
        # old bytes stops covering a hand-replaced artifact.
        from tests.support import seed_generation_fixtures

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            seed_generation_fixtures(project_dir)
            import hashlib
            new_bytes = b"replaced thumbnail bytes\n"
            (project_dir / "generation" / "assets" / "tiny-reset-thumb-001.png").write_bytes(new_bytes)
            rewrite(
                project_dir / "generation" / "asset-manifest.json",
                lambda manifest: manifest["rows"][1].update(
                    content_hash=hashlib.sha256(new_bytes).hexdigest()
                ),
            )
            from influencer_os.generation import (
                load_asset_manifest,
                validate_project_generation_assets,
                validate_project_generation_records,
            )
            project = json.loads((project_dir / "project.json").read_text())
            approvals, _ = validate_project_generation_records(project_dir, project)
            rows = validate_project_generation_assets(project_dir, project, approvals)
            from influencer_os.generation import validate_project_quality_reviews

            passing, _ = validate_project_quality_reviews(project_dir, project, rows)
            self.assertIn("gen_asset_luna_tiny_reset_video_001", passing)
            self.assertNotIn("gen_asset_luna_tiny_reset_thumb_001", passing)

    def test_latest_review_verdict_wins(self):
        # Batch-3 review finding: a newer failing review on the same content
        # beats an older pass.
        from tests.support import seed_generation_fixtures

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            seed_generation_fixtures(project_dir)
            follow_up = load_example("quality-review")
            follow_up["quality_review_id"] = "quality_review_luna_tiny_reset_002"
            follow_up["checklist"][0]["result"] = "fail"
            follow_up["checklist"][0]["notes"] = "Identity drift found on a second look."
            follow_up["overall_verdict"] = "fail"
            follow_up["reviewed_at"] = "2026-07-06T18:00:00"
            write_json(
                project_dir
                / "generation"
                / "quality-reviews"
                / "quality_review_luna_tiny_reset_002.json",
                follow_up,
            )
            from influencer_os.generation import (
                validate_project_generation_assets,
                validate_project_generation_records,
                validate_project_quality_reviews,
            )
            project = json.loads((project_dir / "project.json").read_text())
            approvals, _ = validate_project_generation_records(project_dir, project)
            rows = validate_project_generation_assets(project_dir, project, approvals)
            passing, _ = validate_project_quality_reviews(project_dir, project, rows)
            self.assertEqual(passing, set())

    def test_all_not_applicable_pass_is_rejected(self):
        review = load_example("quality-review")
        for item in review["checklist"]:
            item["result"] = "not_applicable"
        with self.assertRaisesRegex(ValidationError, "judge nothing"):
            validate_record("quality-review", review)

    def test_generated_refs_require_provider_calls_made(self):
        from tests.test_analytics import scaffold_published_project

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            rewrite(
                project_dir / "output-package" / "output-package.json",
                lambda package: package["provider_boundary"].update(
                    provider_calls_made=False
                ),
            )
            with self.assertRaisesRegex(ValueError, "provider_calls_made must be"):
                validate_project(project_dir)

    def test_planned_status_cannot_detach_ledgered_project(self):
        # Own adversarial sweep: declaring planned_not_generated on a
        # project with ledger rows would skip every media binding.
        from tests.test_analytics import scaffold_published_project

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)

            def detach(package):
                package["provider_boundary"]["generation_status"] = "planned_not_generated"
                package["provider_boundary"]["provider_calls_made"] = False
                for asset in package["upload_ready"]:
                    asset.pop("generation_manifest_ref", None)
            rewrite(project_dir / "output-package" / "output-package.json", detach)
            with self.assertRaisesRegex(ValueError, "must bind to its provenance"):
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
        from tests.support import seed_generation_fixtures

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            seed_generation_fixtures(project_dir)
            rewrite(
                project_dir
                / "generation"
                / "quality-reviews"
                / "quality_review_luna_tiny_reset_001.json",
                lambda review: review.update(
                    scope_assets=[
                        {
                            "asset_id": "gen_asset_never_manifested",
                            "content_hash": "0" * 63 + "a",
                        }
                    ]
                ),
            )
            with self.assertRaisesRegex(ValidationError, "no[\\s\\S]*manifest row"):
                validate_project(project_dir)

    def test_generated_without_review_warns(self):
        from tests.support import seed_generation_fixtures

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
        from tests.support import write_upload_ready_assets

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
        from tests.support import seed_generation_fixtures

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
        from tests.support import write_upload_ready_assets

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

            # Quality-review the batch (content-bound to the live manifest),
            # then package.
            manifest = load_asset_manifest(project_dir)
            review = load_example("quality-review")
            review["scope_assets"] = [
                {"asset_id": row["asset_id"], "content_hash": row["content_hash"]}
                for row in manifest["rows"]
            ]
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
