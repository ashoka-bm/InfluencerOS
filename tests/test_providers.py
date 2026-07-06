"""Phase 3 (Generation OS): provider boundary, approval workflow, dispatch.

Guard rules 8-9 (ADR 0023): no code path may dispatch a generation call
without an approved GenerationApprovalRecord id, and the suite never
instantiates a real provider adapter — the deterministic mock is the only
adapter, so these tests are CI-safe and free by construction.
"""

import inspect
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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


ROOT = Path(__file__).resolve().parents[1]

BASE_CONFIG = {"DISABLE_PAID_CONNECTORS": False}
KILLED_CONFIG = {"DISABLE_PAID_CONNECTORS": True}


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
