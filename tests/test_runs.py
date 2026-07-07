import json
import tempfile
import unittest
from pathlib import Path

from influencer_os.runs import build_run_id, init_run, slugify, validate_run_id
from influencer_os.validation import ValidationError


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_PROFILE = ROOT / "examples" / "creator-profile.example.json"


class InitRunTests(unittest.TestCase):
    def test_init_run_scaffolds_manifest_and_events(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = init_run(EXAMPLE_PROFILE, workspace=Path(temp_dir), run_id="luna-test-run")

            manifest = json.loads((run_dir / "run.json").read_text())
            self.assertEqual(manifest["run_id"], "luna-test-run")
            self.assertEqual(manifest["status"], "creator_profile_loaded")
            self.assertEqual(manifest["next_phase"], "social_research_pack")
            self.assertTrue((run_dir / "records" / "creator-profile.json").exists())

            events = (run_dir / "events.jsonl").read_text().splitlines()
            self.assertEqual(len(events), 1)
            self.assertEqual(json.loads(events[0])["event"], "run_initialized")

    def test_init_run_refuses_existing_run_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            init_run(EXAMPLE_PROFILE, workspace=Path(temp_dir), run_id="luna-test-run")
            with self.assertRaises(FileExistsError):
                init_run(EXAMPLE_PROFILE, workspace=Path(temp_dir), run_id="luna-test-run")

    def test_init_run_rejects_invalid_profile(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_profile = Path(temp_dir) / "profile.json"
            bad_profile.write_text(json.dumps({"creator_profile_id": "creator_x"}))
            with self.assertRaises(ValidationError):
                init_run(bad_profile, workspace=Path(temp_dir) / "runs")

    def test_run_id_validation(self):
        self.assertEqual(validate_run_id("luna-2026-07-07"), "luna-2026-07-07")
        for bad in ("", "Luna", "-leading", "has space", "path/../escape"):
            with self.assertRaises(ValueError):
                validate_run_id(bad)

    def test_build_run_id_slugifies_display_name(self):
        profile = json.loads(EXAMPLE_PROFILE.read_text())
        run_id = build_run_id(profile)
        self.assertTrue(run_id.startswith(slugify(profile["display_name"])))
        validate_run_id(run_id)

    def test_slugify_never_returns_empty(self):
        self.assertEqual(slugify("!!!"), "creator")


if __name__ == "__main__":
    unittest.main()
