import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from influencer_os.creator_workspaces import (
    init_creator,
    sync_creator_runtime,
    update_creators,
    validate_creator_workspace,
)
from influencer_os.projects import init_project, validate_project
from influencer_os.validation import ValidationError
from tests.test_readiness_validation import place_asset_files, populate_foundation


ROOT = Path(__file__).resolve().parents[1]


def copy_example_record(example_name, destination):
    destination.write_text((ROOT / "examples" / example_name).read_text())


def populate_workspace_records(workspace_dir):
    copy_example_record("creator-profile.example.json", workspace_dir / "creator-profile.json")
    copy_example_record("reference-library.example.json", workspace_dir / "references" / "reference-library.json")
    # The example manifest declares this source intake; place it so intake
    # provenance resolves during workspace validation.
    (workspace_dir / "sources" / "intakes" / "luna-fit-breakdown.md").write_text(
        (ROOT / "examples" / "sources" / "luna-fit-breakdown.example.md").read_text()
    )


def populate_research_packs(workspace_dir):
    copy_example_record(
        "social-research-pack.example.json",
        workspace_dir / "research" / "social-research-packs" / "research_luna_fit_2026_06_28.json",
    )
    copy_example_record(
        "video-understanding-pack.example.json",
        workspace_dir / "research" / "video-understanding-packs" / "video_research_luna_fit_001.json",
    )


def scaffold_project_workspace(temp_dir):
    workspace_dir = init_creator(
        ROOT / "examples" / "creator-workspace.example.json",
        workspace_root=Path(temp_dir),
    )
    populate_workspace_records(workspace_dir)
    populate_research_packs(workspace_dir)
    project_dir = init_project(
        ROOT / "examples" / "project.example.json",
        creator_workspace=workspace_dir,
    )
    populate_project_records(project_dir)
    return workspace_dir, project_dir


def rewrite_json(path, mutate):
    record = json.loads(path.read_text())
    mutate(record)
    path.write_text(json.dumps(record, indent=2) + "\n")


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

            populate_workspace_records(workspace_dir)
            populate_research_packs(workspace_dir)
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


class PropagationTests(unittest.TestCase):
    def make_second_manifest(self, temp_dir):
        manifest = json.loads((ROOT / "examples" / "creator-workspace.example.json").read_text())
        manifest["creator_workspace_id"] = "creator_workspace_nova_tech"
        manifest["creator_slug"] = "nova-tech"
        manifest["creator_profile_id"] = "creator_nova_tech"
        manifest["root_path"] = "workspace-library/creators/nova-tech/"
        manifest_path = Path(temp_dir) / "nova-workspace.json"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        return manifest_path

    def test_init_creator_writes_thin_claude_wrapper(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_creator(
                ROOT / "examples" / "creator-workspace.example.json",
                workspace_root=Path(temp_dir),
            )

            claude_text = (workspace_dir / "CLAUDE.md").read_text()
            self.assertIn("@AGENTS.md", claude_text)

    def test_init_creator_carries_no_gated_zone_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_creator(
                ROOT / "examples" / "creator-workspace.example.json",
                workspace_root=Path(temp_dir),
            )

            for gated in (".claude/hooks", ".claude/settings.json", "cron", "scripts"):
                self.assertFalse((workspace_dir / gated).exists(), f"gated zone not inert: {gated}")

    def test_update_creators_refreshes_all_and_preserves_creator_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "creators"
            ws1 = init_creator(
                ROOT / "examples" / "creator-workspace.example.json", workspace_root=root
            )
            init_creator(self.make_second_manifest(temp_dir), workspace_root=root)
            (root / "not-a-workspace").mkdir()

            skill_dir = ws1 / ".claude" / "skills" / "influencer-os"
            (skill_dir / "SKILL.md").write_text("# Stale copy\n")
            (skill_dir / "SKILL.local.md").write_text("# Local override\n")
            creator_only = ws1 / ".claude" / "skills" / "creator-only" / "SKILL.md"
            creator_only.parent.mkdir(parents=True)
            creator_only.write_text("# Creator-only\n")
            populate_workspace_records(ws1)
            profile_before = (ws1 / "creator-profile.json").read_text()

            results = update_creators(workspace_root=root)

            self.assertEqual(len(results), 2)
            self.assertEqual(
                (skill_dir / "SKILL.md").read_text(),
                (ROOT / "skills" / "influencer-os" / "SKILL.md").read_text(),
            )
            self.assertEqual((skill_dir / "SKILL.local.md").read_text(), "# Local override\n")
            self.assertEqual(creator_only.read_text(), "# Creator-only\n")
            self.assertEqual((ws1 / "creator-profile.json").read_text(), profile_before)
            backup = ws1 / ".claude" / "skills-backup" / "influencer-os" / "SKILL.md"
            self.assertEqual(backup.read_text(), "# Stale copy\n")

    def test_update_creators_requires_existing_root(self):
        with self.assertRaises(FileNotFoundError):
            update_creators(workspace_root=Path("/nonexistent/creators-root"))

    def test_update_creators_cli_command(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            init_creator(
                ROOT / "examples" / "creator-workspace.example.json",
                workspace_root=Path(temp_dir),
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "update-creators",
                    "--workspace-root",
                    temp_dir,
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Updated 1 creator workspace", result.stdout)


class ProvenanceResolutionTests(unittest.TestCase):
    def test_validate_project_rejects_dangling_reference_asset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            rewrite_json(
                project_dir / "project.json",
                lambda project: project["source_refs"]["reference_asset_ids"].append("asset_missing_prop"),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_project(project_dir)
            self.assertIn("asset_missing_prop", str(ctx.exception))

    def test_validate_project_rejects_missing_research_pack_record(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, project_dir = scaffold_project_workspace(temp_dir)
            pack_path = (
                workspace_dir / "research" / "video-understanding-packs" / "video_research_luna_fit_001.json"
            )
            pack_path.unlink()

            with self.assertRaises(ValidationError) as ctx:
                validate_project(project_dir)
            self.assertIn("video_research_luna_fit_001", str(ctx.exception))

    def test_validate_project_accepts_packaged_project_with_matching_output_package(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            copy_example_record(
                "output-package.example.json",
                project_dir / "output-package" / "output-package.json",
            )
            rewrite_json(
                project_dir / "project.json",
                lambda project: project.update(status="packaged"),
            )

            result = validate_project(project_dir)
            self.assertEqual(result["project_id"], "project_luna_tiny_reset_001")

    def test_validate_project_rejects_output_package_creator_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            package_path = project_dir / "output-package" / "output-package.json"
            copy_example_record("output-package.example.json", package_path)
            rewrite_json(
                package_path,
                lambda package: package.update(creator_profile_id="creator_other"),
            )
            rewrite_json(
                project_dir / "project.json",
                lambda project: project.update(status="packaged"),
            )

            with self.assertRaises(ValueError):
                validate_project(project_dir)

    def test_validate_project_requires_every_project_plan_in_output_package(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            package_path = project_dir / "output-package" / "output-package.json"
            copy_example_record("output-package.example.json", package_path)
            rewrite_json(
                package_path,
                lambda package: package["source_refs"].update(
                    production_plan_ids=["mjvp_luna_001"]
                ),
            )
            rewrite_json(
                project_dir / "project.json",
                lambda project: project.update(status="packaged"),
            )

            with self.assertRaises(ValueError) as ctx:
                validate_project(project_dir)
            self.assertIn("bvgp_luna_001", str(ctx.exception))

    def test_validate_project_rejects_unknown_production_plan_ids(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            package_path = project_dir / "output-package" / "output-package.json"
            copy_example_record("output-package.example.json", package_path)
            rewrite_json(
                package_path,
                lambda package: package["source_refs"].update(
                    production_plan_ids=["wrong_plan_id"]
                ),
            )
            rewrite_json(
                project_dir / "project.json",
                lambda project: project.update(status="packaged"),
            )

            with self.assertRaises(ValueError) as ctx:
                validate_project(project_dir)
            self.assertIn("wrong_plan_id", str(ctx.exception))

    def test_validate_project_rejects_output_package_template_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            package_path = project_dir / "output-package" / "output-package.json"
            copy_example_record("output-package.example.json", package_path)
            rewrite_json(
                package_path,
                lambda package: package["source_refs"].update(
                    applied_social_template_id="applied_template_other_001"
                ),
            )
            rewrite_json(
                project_dir / "project.json",
                lambda project: project.update(status="packaged"),
            )

            with self.assertRaises(ValueError):
                validate_project(project_dir)


class ReadinessGateTests(unittest.TestCase):
    def init_workspace_with_status(self, temp_dir, status):
        manifest = json.loads((ROOT / "examples" / "creator-workspace.example.json").read_text())
        manifest["status"] = status
        manifest_path = Path(temp_dir) / "creator-workspace.json"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        workspace_dir = init_creator(manifest_path, workspace_root=Path(temp_dir) / "creators")
        populate_workspace_records(workspace_dir)
        populate_foundation(workspace_dir)
        place_asset_files(workspace_dir)
        return workspace_dir

    def test_generation_ready_requires_an_approved_visual_asset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = self.init_workspace_with_status(temp_dir, "generation_ready")

            def demote_all_assets(library):
                for asset in library["assets"]:
                    asset["asset_status"] = "generated"

            rewrite_json(workspace_dir / "references" / "reference-library.json", demote_all_assets)

            with self.assertRaises(ValidationError):
                validate_creator_workspace(workspace_dir)

    def test_generation_ready_passes_with_approved_visual_asset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = self.init_workspace_with_status(temp_dir, "generation_ready")

            result = validate_creator_workspace(workspace_dir)
            self.assertEqual(result["creator_slug"], "luna-fit")


class ValidateRecordCliTests(unittest.TestCase):
    def run_validate_record(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "influencer_os", "validate", "record", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_validate_record_accepts_matching_record(self):
        result = self.run_validate_record("project", "examples/project.example.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Validated record", result.stdout)

    def test_validate_record_rejects_mismatched_record(self):
        result = self.run_validate_record("project", "examples/creator-profile.example.json")

        self.assertEqual(result.returncode, 1)
        self.assertIn("error:", result.stderr)

    def test_validate_record_requires_schema_and_path(self):
        result = self.run_validate_record()

        self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
