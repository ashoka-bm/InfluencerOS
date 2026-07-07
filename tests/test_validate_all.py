import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from influencer_os.boards import rebuild_board
from influencer_os.creator_workspaces import init_creator
from influencer_os.full_validation import validate_all
from influencer_os.projects import validate_project
from influencer_os.validation import ValidationError
from tests.test_cli import (
    populate_promotion_records,
    populate_research_packs,
    populate_workspace_records,
    scaffold_project_workspace,
)
from tests.test_research_validation import (
    ENTRY_ID,
    RUN_ID,
    frontmatter_block,
    load_example,
    write_json,
    write_jsonl,
)


ROOT = Path(__file__).resolve().parents[1]


def scaffold_full_workspace(temp_dir):
    """One workspace that passes every layer: the full project scaffold from
    the CLI tests plus the research-run state from the research tests, with
    the board rebuilt from canonical records."""
    workspace_dir, project_dir = scaffold_project_workspace(temp_dir)
    research = workspace_dir / "research"

    run_dir = research / "runs" / RUN_ID
    write_json(run_dir / "research-run.json", load_example("research-run"))
    write_json(run_dir / "search-plan.json", load_example("research-search-plan"))
    write_jsonl(run_dir / "source-yield.jsonl", [load_example("research-source-yield")])
    write_jsonl(run_dir / "evidence.jsonl", [load_example("research-evidence")])
    write_jsonl(run_dir / "metric-snapshots.jsonl", [load_example("metric-snapshot")])

    findings_path = research / "findings.md"
    findings_path.write_text(
        frontmatter_block(load_example("research-findings"))
        + "\n## Desk resets\n\nLunch-break resets are outperforming baselines this week.\n"
    )

    stable_path = research / "stable-findings" / "stable_finding_luna_fit_001.md"
    stable_path.parent.mkdir(parents=True, exist_ok=True)
    stable_path.write_text(
        frontmatter_block(load_example("stable-finding"))
        + "\nDesk resets are a durable topic cluster for Luna.\n"
    )

    intelligence = research / "intelligence"
    write_json(intelligence / "sources.json", load_example("research-sources"))
    write_json(intelligence / "hashtags.json", load_example("research-hashtags"))
    write_json(intelligence / "search-terms.json", load_example("research-search-terms"))
    write_json(intelligence / "reference-creators.json", load_example("reference-creators"))
    write_json(intelligence / "watchlist.json", load_example("research-watchlist"))

    write_json(research / "idea-queue" / "queue.json", load_example("idea-queue"))
    write_jsonl(workspace_dir / "system" / "project-warnings.jsonl", [load_example("project-warning")])
    write_jsonl(workspace_dir / "system" / "creator-events.jsonl", [load_example("system-event")])

    rebuild_board(workspace_dir)
    return workspace_dir, project_dir


def rewrite_json(path, mutate):
    record = json.loads(path.read_text())
    mutate(record)
    path.write_text(json.dumps(record, indent=2) + "\n")


class ValidateAllTests(unittest.TestCase):
    def test_full_workspace_passes_every_layer(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _project_dir = scaffold_full_workspace(temp_dir)

            result = validate_all(workspace_dir)
            layer_names = [name for name, _summary in result["layers"]]
            self.assertEqual(
                layer_names, ["workspace", "research", "queue", "board", "projects"]
            )
            self.assertEqual(result["skipped"], [])
            self.assertEqual(result["project_count"], 1)

    def test_dangling_entry_evidence_passes_project_but_fails_all(self):
        # The pre-alpha review false green: validate project alone trusts the
        # promotion gate, which never re-resolves the queue entry's own
        # evidence refs — only the composed command catches the broken chain.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, project_dir = scaffold_full_workspace(temp_dir)
            entry_path = (
                workspace_dir / "research" / "idea-queue" / "entries" / f"{ENTRY_ID}.json"
            )

            def break_evidence(entry):
                entry["evidence_refs"][0]["evidence_id"] = "evidence_luna_fit_ghost"

            rewrite_json(entry_path, break_evidence)

            validate_project(project_dir)  # the false green, still green

            with self.assertRaises(ValidationError) as ctx:
                validate_all(workspace_dir)
            message = str(ctx.exception)
            self.assertRegex(message, r"^\[(research|queue)\]")
            self.assertIn("evidence_luna_fit_ghost", message)

    def test_human_approved_promotion_warning_surfaces_once(self):
        # D2: warn-only promotion refs stay warnings, but the composed command
        # must report them (deduplicated across layers), never swallow them.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _project_dir = scaffold_full_workspace(temp_dir)
            promotion_path = (
                workspace_dir / "research" / "idea-promotions" / "idea_promotion_luna_fit_001.json"
            )

            def break_promotion_ref(promotion):
                # Append (never replace) so the project's cached refs stay a
                # subset of the locked promotion and only the gate warns.
                ghost = json.loads(json.dumps(promotion["evidence_refs"][0]))
                ghost["evidence_id"] = "evidence_luna_fit_ghost"
                promotion["evidence_refs"].append(ghost)

            rewrite_json(promotion_path, break_promotion_ref)

            result = validate_all(workspace_dir)
            matching = [
                warning
                for warning in result["warnings"]
                if "evidence_luna_fit_ghost" in warning
            ]
            self.assertEqual(len(matching), 1, result["warnings"])

    def test_entries_without_queue_manifest_fail(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _project_dir = scaffold_full_workspace(temp_dir)
            (workspace_dir / "research" / "idea-queue" / "queue.json").unlink()

            with self.assertRaises(ValidationError) as ctx:
                validate_all(workspace_dir)
            self.assertIn("[queue]", str(ctx.exception))
            self.assertIn("without a queue manifest", str(ctx.exception))

    def test_fresh_workspace_skips_queue_and_board(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_creator(
                ROOT / "examples" / "creator-workspace.example.json",
                workspace_root=Path(temp_dir),
            )
            populate_workspace_records(workspace_dir)

            result = validate_all(workspace_dir)
            skipped_layers = [name for name, _reason in result["skipped"]]
            self.assertEqual(skipped_layers, ["queue", "board"])
            self.assertEqual(result["project_count"], 0)

    def test_project_layer_error_names_the_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, project_dir = scaffold_full_workspace(temp_dir)
            (project_dir / "plan" / "applied-template.json").unlink()

            with self.assertRaises(ValidationError) as ctx:
                validate_all(workspace_dir)
            self.assertIn("[project project_luna_tiny_reset_001]", str(ctx.exception))

    def test_malformed_json_fails_with_layer_name(self):
        # json.JSONDecodeError is a ValueError, so the layer wrapper names
        # the layer instead of letting a traceback escape (Codex review).
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _project_dir = scaffold_full_workspace(temp_dir)
            (workspace_dir / "creator-profile.json").write_text("{not json")

            with self.assertRaises(ValidationError) as ctx:
                validate_all(workspace_dir)
            self.assertIn("[workspace]", str(ctx.exception))

    def test_non_object_project_manifest_fails_closed(self):
        # A JSON-valid but non-object project.json must be a ValidationError,
        # never an AttributeError escaping the layer wrapper (Codex review).
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, project_dir = scaffold_full_workspace(temp_dir)
            (project_dir / "project.json").write_text("[]\n")

            with self.assertRaises(ValidationError) as ctx:
                validate_all(workspace_dir)
            self.assertIn("must be a JSON object", str(ctx.exception))

    def test_orphan_project_folder_fails(self):
        # A projects/ subfolder without a manifest is invisible to the glob;
        # the composed gate must reject it rather than skip it (Codex review).
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _project_dir = scaffold_full_workspace(temp_dir)
            (workspace_dir / "projects" / "half-created").mkdir()

            with self.assertRaises(ValidationError) as ctx:
                validate_all(workspace_dir)
            self.assertIn("without a project.json manifest", str(ctx.exception))
            self.assertIn("projects/half-created", str(ctx.exception))

    def test_cli_validate_all(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _project_dir = scaffold_full_workspace(temp_dir)

            completed = subprocess.run(
                [sys.executable, "-m", "influencer_os", "validate", "all", str(workspace_dir)],
                capture_output=True,
                text=True,
                cwd=ROOT,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Validated full chain", completed.stdout)
            self.assertIn("warnings: 0.", completed.stdout)

    def test_cli_validate_all_fails_on_broken_chain(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _project_dir = scaffold_full_workspace(temp_dir)
            shutil.rmtree(workspace_dir / "research" / "runs" / RUN_ID)

            completed = subprocess.run(
                [sys.executable, "-m", "influencer_os", "validate", "all", str(workspace_dir)],
                capture_output=True,
                text=True,
                cwd=ROOT,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn("error:", completed.stderr)


if __name__ == "__main__":
    unittest.main()
