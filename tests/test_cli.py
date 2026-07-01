import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from influencer_os.creator_workspaces import sync_creator_runtime


ROOT = Path(__file__).resolve().parents[1]


def copy_example_record(example_name, destination):
    destination.write_text((ROOT / "examples" / example_name).read_text())


def populate_workspace_records(workspace_dir):
    copy_example_record("creator-profile.example.json", workspace_dir / "creator-profile.json")
    copy_example_record("reference-library.example.json", workspace_dir / "references" / "reference-library.json")


def populate_project_records(project_dir):
    copy_example_record("selected-content-idea.example.json", project_dir / "idea" / "selected-content-idea.json")
    copy_example_record("applied-social-template.example.json", project_dir / "plan" / "applied-template.json")
    copy_example_record("micro-journey-video-plan.example.json", project_dir / "plan" / "production-plan.json")
    copy_example_record("base-video-generation-plan.example.json", project_dir / "plan" / "generation-plan.json")


class CliTests(unittest.TestCase):
    def test_validate_examples_command(self):
        result = subprocess.run(
            [sys.executable, "-m", "influencer_os", "validate", "examples"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Validated", result.stdout)

    def test_init_run_creates_workspace_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "init-run",
                    "examples/creator-profile.example.json",
                    "--workspace",
                    temp_dir,
                    "--run-id",
                    "luna-test-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            run_dir = Path(temp_dir) / "luna-test-run"
            self.assertTrue((run_dir / "records" / "creator-profile.json").exists())
            self.assertTrue((run_dir / "events.jsonl").exists())

            manifest = json.loads((run_dir / "run.json").read_text())
            self.assertEqual(manifest["status"], "creator_profile_loaded")
            self.assertEqual(manifest["next_phase"], "social_research_pack")

    def test_init_run_rejects_path_like_run_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "init-run",
                    "examples/creator-profile.example.json",
                    "--workspace",
                    temp_dir,
                    "--run-id",
                    "../escaped-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("Invalid run id", result.stderr)
            self.assertFalse((Path(temp_dir).parent / "escaped-run").exists())

    def test_init_creator_creates_workspace_tree(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "init-creator",
                    "examples/creator-workspace.example.json",
                    "--workspace-root",
                    temp_dir,
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            workspace_dir = Path(temp_dir) / "luna-fit"
            self.assertTrue((workspace_dir / "creator-workspace.json").exists())
            self.assertTrue((workspace_dir / "creator-profile.json").exists())
            self.assertTrue((workspace_dir / "context" / "SOUL.md").exists())
            self.assertTrue((workspace_dir / "context" / "USER.md").exists())
            self.assertTrue((workspace_dir / "context" / "MEMORY.md").exists())
            self.assertTrue((workspace_dir / "brand_context" / "identity.md").exists())
            self.assertTrue((workspace_dir / "brand_context" / "soul.md").exists())
            self.assertTrue((workspace_dir / "brand_context" / "personal-brand.md").exists())
            self.assertTrue((workspace_dir / "brand_context" / "voice-samples.md").exists())
            self.assertTrue((workspace_dir / "references" / "reference-library.json").exists())
            self.assertTrue((workspace_dir / "research" / "social-research-packs").is_dir())
            self.assertTrue((workspace_dir / "projects").is_dir())
            self.assertTrue((workspace_dir / "sources" / "intakes").is_dir())
            self.assertTrue((workspace_dir / "progress").is_dir())
            self.assertTrue((workspace_dir / "progress" / "setup-checklist.md").exists())
            self.assertTrue((workspace_dir / "memory" / "MEMORY.md").exists())
            self.assertTrue((workspace_dir / "memory" / "learnings.md").exists())
            self.assertTrue((workspace_dir / ".claude" / "skills" / "influencer-os" / "SKILL.md").exists())
            self.assertTrue((workspace_dir / ".claude" / "skills" / "create-influencer" / "SKILL.md").exists())

    def test_validate_workspace_command_accepts_initialized_creator(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            init_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "init-creator",
                    "examples/creator-workspace.example.json",
                    "--workspace-root",
                    temp_dir,
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(init_result.returncode, 0, init_result.stderr)

            workspace_dir = Path(temp_dir) / "luna-fit"
            populate_workspace_records(workspace_dir)
            validate_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "validate",
                    "workspace",
                    str(workspace_dir),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(validate_result.returncode, 0, validate_result.stderr)
            self.assertIn("Validated creator workspace", validate_result.stdout)

    def test_validate_workspace_command_rejects_unfilled_creator_records(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            init_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "init-creator",
                    "examples/creator-workspace.example.json",
                    "--workspace-root",
                    temp_dir,
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(init_result.returncode, 0, init_result.stderr)

            validate_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "validate",
                    "workspace",
                    str(Path(temp_dir) / "luna-fit"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(validate_result.returncode, 1)
            self.assertIn("Invalid workspace record", validate_result.stderr)

    def test_validate_workspace_command_rejects_missing_manifest_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            init_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "init-creator",
                    "examples/creator-workspace.example.json",
                    "--workspace-root",
                    temp_dir,
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(init_result.returncode, 0, init_result.stderr)

            workspace_dir = Path(temp_dir) / "luna-fit"
            populate_workspace_records(workspace_dir)
            (workspace_dir / "memory" / "learnings.md").unlink()
            validate_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "validate",
                    "workspace",
                    str(workspace_dir),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(validate_result.returncode, 1)
            self.assertIn("Missing workspace paths", validate_result.stderr)

    def test_sync_creator_runtime_refreshes_base_skills_and_preserves_local_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            init_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "init-creator",
                    "examples/creator-workspace.example.json",
                    "--workspace-root",
                    temp_dir,
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(init_result.returncode, 0, init_result.stderr)

            workspace_dir = Path(temp_dir) / "luna-fit"
            copied_skill_dir = workspace_dir / ".claude" / "skills" / "influencer-os"
            copied_skill_path = copied_skill_dir / "SKILL.md"
            local_override_path = copied_skill_dir / "SKILL.local.md"
            copied_skill_path.write_text("# Stale local copy\n")
            local_override_path.write_text("# Local override\n\nKeep Luna concise.\n")

            creator_only_skill = workspace_dir / ".claude" / "skills" / "creator-only" / "SKILL.md"
            creator_only_skill.parent.mkdir(parents=True)
            creator_only_skill.write_text("# Creator-only Skill\n")

            sync_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "sync-creator-runtime",
                    str(workspace_dir),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(sync_result.returncode, 0, sync_result.stderr)
            self.assertEqual(copied_skill_path.read_text(), (ROOT / "skills" / "influencer-os" / "SKILL.md").read_text())
            self.assertEqual(local_override_path.read_text(), "# Local override\n\nKeep Luna concise.\n")
            self.assertEqual(creator_only_skill.read_text(), "# Creator-only Skill\n")
            self.assertIn("Synced creator runtime", sync_result.stdout)

    def test_sync_creator_runtime_does_not_copy_source_local_override(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = Path(temp_dir) / "creator"
            source_skills_dir = Path(temp_dir) / "source-skills"
            source_skill_dir = source_skills_dir / "baseline"
            target_skill_dir = workspace_dir / ".claude" / "skills" / "baseline"

            workspace_dir.mkdir()
            (workspace_dir / "creator-workspace.json").write_text("{}\n")
            source_skill_dir.mkdir(parents=True)
            (source_skill_dir / "SKILL.md").write_text("# Baseline\n")
            (source_skill_dir / "SKILL.local.md").write_text("# OS-only override\n")
            (source_skill_dir / "references.md").write_text("# Reference\n")

            result = sync_creator_runtime(workspace_dir, source_skills_dir=source_skills_dir)

            self.assertEqual(result["synced_skills"], ["baseline"])
            self.assertEqual((target_skill_dir / "SKILL.md").read_text(), "# Baseline\n")
            self.assertEqual((target_skill_dir / "references.md").read_text(), "# Reference\n")
            self.assertFalse((target_skill_dir / "SKILL.local.md").exists())

    def test_init_project_creates_project_tree(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            init_creator_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "init-creator",
                    "examples/creator-workspace.example.json",
                    "--workspace-root",
                    temp_dir,
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(init_creator_result.returncode, 0, init_creator_result.stderr)

            workspace_dir = Path(temp_dir) / "luna-fit"
            init_project_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "init-project",
                    "examples/project.example.json",
                    "--creator-workspace",
                    str(workspace_dir),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(init_project_result.returncode, 0, init_project_result.stderr)
            project_dir = workspace_dir / "projects" / "tiny-reset-after-laptop-day"
            self.assertTrue((project_dir / "project.json").exists())
            self.assertTrue((project_dir / "idea").is_dir())
            self.assertTrue((project_dir / "plan").is_dir())
            self.assertTrue((project_dir / "output-package" / "assets").is_dir())
            self.assertTrue((project_dir / "output-package" / "upload-ready").is_dir())
            self.assertTrue((project_dir / "output-package" / "source-refs").is_dir())
            self.assertTrue((project_dir / "output-package" / "platform-adaptations").is_dir())
            self.assertTrue((project_dir / "published" / "published-post-records").is_dir())
            self.assertTrue((project_dir / "analytics" / "snapshots").is_dir())
            self.assertTrue((project_dir / "analytics" / "raw").is_dir())
            self.assertTrue((project_dir / "performance-summary.md").exists())

    def test_validate_project_command_accepts_initialized_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            init_creator_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "init-creator",
                    "examples/creator-workspace.example.json",
                    "--workspace-root",
                    temp_dir,
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(init_creator_result.returncode, 0, init_creator_result.stderr)

            workspace_dir = Path(temp_dir) / "luna-fit"
            init_project_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "init-project",
                    "examples/project.example.json",
                    "--creator-workspace",
                    str(workspace_dir),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(init_project_result.returncode, 0, init_project_result.stderr)

            project_dir = workspace_dir / "projects" / "tiny-reset-after-laptop-day"
            populate_project_records(project_dir)
            validate_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "validate",
                    "project",
                    str(project_dir),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(validate_result.returncode, 0, validate_result.stderr)
            self.assertIn("Validated project", validate_result.stdout)

    def test_validate_project_command_rejects_incomplete_planned_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            init_creator_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "init-creator",
                    "examples/creator-workspace.example.json",
                    "--workspace-root",
                    temp_dir,
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(init_creator_result.returncode, 0, init_creator_result.stderr)

            workspace_dir = Path(temp_dir) / "luna-fit"
            init_project_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "init-project",
                    "examples/project.example.json",
                    "--creator-workspace",
                    str(workspace_dir),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(init_project_result.returncode, 0, init_project_result.stderr)

            validate_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "validate",
                    "project",
                    str(workspace_dir / "projects" / "tiny-reset-after-laptop-day"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(validate_result.returncode, 1)
            self.assertIn("Missing project paths", validate_result.stderr)

    def test_init_project_rejects_creator_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            init_creator_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "init-creator",
                    "examples/creator-workspace.example.json",
                    "--workspace-root",
                    temp_dir,
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(init_creator_result.returncode, 0, init_creator_result.stderr)

            project_path = Path(temp_dir) / "wrong-project.json"
            project = json.loads((ROOT / "examples" / "project.example.json").read_text())
            project["creator_profile_id"] = "creator_other"
            project_path.write_text(json.dumps(project, indent=2) + "\n")

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "init-project",
                    str(project_path),
                    "--creator-workspace",
                    str(Path(temp_dir) / "luna-fit"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("does not match creator workspace", result.stderr)


if __name__ == "__main__":
    unittest.main()
