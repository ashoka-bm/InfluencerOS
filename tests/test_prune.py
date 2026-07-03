import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from influencer_os.prune import prune_research
from influencer_os.research import validate_queue, validate_research
from influencer_os.validation import ValidationError

from test_recall_index import scaffold_indexable_workspace
from test_research_validation import (
    RUN_ID,
    load_example,
    scaffold_research_workspace,
    write_json,
)


ROOT = Path(__file__).resolve().parents[1]

OLD_EVIDENCE_ID = "evidence_luna_fit_old"
OLD_METRIC_ID = "metric_snapshot_luna_fit_old"
AS_OF = "2026-07-03"  # example records are captured on this date


def run_paths(workspace_dir):
    run_dir = workspace_dir / "research" / "runs" / RUN_ID
    return run_dir / "research-run.json", run_dir / "evidence.jsonl", run_dir / "metric-snapshots.jsonl"


def add_old_unreferenced_records(workspace_dir, captured_on="2026-01-01T09:00:00",
                                 with_metric=True):
    """Append an old evidence record (and optionally a metric snapshot) that
    nothing references, keeping the run manifest outputs reconciled."""
    manifest_path, evidence_path, metrics_path = run_paths(workspace_dir)

    evidence = load_example("research-evidence")
    evidence["evidence_id"] = OLD_EVIDENCE_ID
    evidence["captured_on"] = captured_on
    with evidence_path.open("a") as handle:
        handle.write(json.dumps(evidence) + "\n")

    manifest = json.loads(manifest_path.read_text())
    manifest["outputs"]["evidence_ids"].append(OLD_EVIDENCE_ID)

    if with_metric:
        metric = load_example("metric-snapshot")
        metric["metric_snapshot_id"] = OLD_METRIC_ID
        metric["evidence_id"] = OLD_EVIDENCE_ID
        metric["captured_on"] = captured_on
        with metrics_path.open("a") as handle:
            handle.write(json.dumps(metric) + "\n")
        manifest["outputs"]["metric_snapshot_ids"].append(OLD_METRIC_ID)

    write_json(manifest_path, manifest)


class PruneTests(unittest.TestCase):
    def test_dry_run_reports_without_modifying_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            add_old_unreferenced_records(workspace_dir)
            manifest_path, evidence_path, _ = run_paths(workspace_dir)
            before = evidence_path.read_text()

            result = prune_research(workspace_dir, as_of=AS_OF)
            self.assertFalse(result["applied"])
            self.assertEqual(result["evidence_pruned"], 1)
            self.assertEqual(result["metric_snapshots_pruned"], 1)
            self.assertEqual(
                result["runs"][0]["pruned_evidence_ids"], [OLD_EVIDENCE_ID]
            )
            self.assertEqual(evidence_path.read_text(), before)
            self.assertNotIn(
                "pruned_evidence_ids", json.loads(manifest_path.read_text())
            )

    def test_apply_removes_records_and_records_pruned_ids(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            add_old_unreferenced_records(workspace_dir)
            manifest_path, evidence_path, metrics_path = run_paths(workspace_dir)

            result = prune_research(workspace_dir, apply=True, as_of=AS_OF)
            self.assertTrue(result["applied"])
            self.assertEqual(result["evidence_pruned"], 1)

            self.assertNotIn(OLD_EVIDENCE_ID, evidence_path.read_text())
            self.assertIn("evidence_luna_fit_001", evidence_path.read_text())
            self.assertNotIn(OLD_METRIC_ID, metrics_path.read_text())
            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(manifest["pruned_evidence_ids"], [OLD_EVIDENCE_ID])
            self.assertEqual(manifest["pruned_metric_snapshot_ids"], [OLD_METRIC_ID])
            # The original outputs declaration is untouched.
            self.assertIn(OLD_EVIDENCE_ID, manifest["outputs"]["evidence_ids"])

            validate_research(workspace_dir)
            validate_queue(workspace_dir)

    def test_referenced_evidence_is_never_pruned(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            # Make the referenced example evidence ancient: still protected.
            _, evidence_path, _ = run_paths(workspace_dir)
            evidence = load_example("research-evidence")
            evidence["captured_on"] = "2020-01-01T09:00:00"
            evidence_path.write_text(json.dumps(evidence) + "\n")

            result = prune_research(workspace_dir, apply=True, as_of=AS_OF)
            self.assertEqual(result["evidence_pruned"], 0)
            self.assertIn("evidence_luna_fit_001", evidence_path.read_text())

    def test_evidence_with_protected_metric_snapshot_is_kept(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Research-only scaffold: no project caches, so protection comes
            # from the queue entry and promotion refs alone.
            workspace_dir = scaffold_research_workspace(temp_dir)
            add_old_unreferenced_records(workspace_dir)
            # Reference only the old metric snapshot from the queue entry; the
            # ref shape carries the evidence id alongside, so use a crafted
            # project cache instead to isolate metric-only protection.
            project = load_example("project")
            project["source_refs"]["research_evidence_ids"] = []
            project["source_refs"]["metric_snapshot_ids"] = [OLD_METRIC_ID]
            write_json(
                workspace_dir / "projects" / project["project_id"] / "project.json",
                project,
            )

            result = prune_research(workspace_dir, as_of=AS_OF)
            self.assertEqual(result["evidence_pruned"], 0)

    def test_fresh_unreferenced_evidence_is_kept(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            add_old_unreferenced_records(
                workspace_dir, captured_on="2026-06-20T09:00:00", with_metric=False
            )

            result = prune_research(workspace_dir, as_of=AS_OF)
            self.assertEqual(result["evidence_pruned"], 0)

    def test_apply_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            add_old_unreferenced_records(workspace_dir)

            first = prune_research(workspace_dir, apply=True, as_of=AS_OF)
            second = prune_research(workspace_dir, apply=True, as_of=AS_OF)
            self.assertEqual(first["evidence_pruned"], 1)
            self.assertEqual(second["evidence_pruned"], 0)
            manifest_path, _, _ = run_paths(workspace_dir)
            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(manifest["pruned_evidence_ids"], [OLD_EVIDENCE_ID])


class PrunedReconciliationTests(unittest.TestCase):
    def test_pruned_run_manifest_validates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            add_old_unreferenced_records(workspace_dir)
            prune_research(workspace_dir, apply=True, as_of=AS_OF)

            validate_research(workspace_dir)

    def test_pruned_id_still_present_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            manifest_path, _, _ = run_paths(workspace_dir)
            manifest = json.loads(manifest_path.read_text())
            manifest["pruned_evidence_ids"] = ["evidence_luna_fit_001"]
            write_json(manifest_path, manifest)

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("still present", str(ctx.exception))

    def test_pruned_id_never_declared_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            manifest_path, _, _ = run_paths(workspace_dir)
            manifest = json.loads(manifest_path.read_text())
            manifest["pruned_evidence_ids"] = ["evidence_luna_fit_ghost"]
            write_json(manifest_path, manifest)

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("never declared", str(ctx.exception))


class PruneCliTests(unittest.TestCase):
    def test_prune_command_dry_runs_by_default(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)

            result = subprocess.run(
                [sys.executable, "-m", "influencer_os", "prune", str(workspace_dir)],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("dry run", result.stdout)
            self.assertIn("Nothing to prune.", result.stdout)


if __name__ == "__main__":
    unittest.main()
