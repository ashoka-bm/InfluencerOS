import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from influencer_os.recall_index import (
    collect_index_rows,
    rebuild_index,
    resolve_record_id,
)
from influencer_os.validation import ValidationError

from test_research_validation import (
    ENTRY_ID,
    RUN_ID,
    load_example,
    scaffold_research_workspace,
    write_json,
)


ROOT = Path(__file__).resolve().parents[1]

PROJECT_ID = "project_luna_tiny_reset_001"


def scaffold_indexable_workspace(temp_dir):
    """Research scaffold plus one project, so every draft record kind exists."""
    workspace_dir = scaffold_research_workspace(temp_dir)
    write_json(
        workspace_dir / "projects" / PROJECT_ID / "project.json",
        load_example("project"),
    )
    return workspace_dir


def db_path_for(temp_dir):
    return Path(temp_dir) / "index" / "influencer-os.sqlite"


class RecallIndexResolutionTests(unittest.TestCase):
    def test_rebuild_resolves_every_draft_record_kind(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            db_path = db_path_for(temp_dir)
            result = rebuild_index(workspace_dir, db_path=db_path)
            self.assertEqual(result["creator_slug"], "luna-fit")

            def only(record_id):
                rows = resolve_record_id(db_path, record_id)
                self.assertEqual(len(rows), 1, f"{record_id}: {rows}")
                return rows[0]

            evidence = only("evidence_luna_fit_001")
            self.assertEqual(evidence["record_type"], "research-evidence")
            self.assertEqual(
                evidence["source_path"], f"research/runs/{RUN_ID}/evidence.jsonl"
            )
            self.assertEqual(evidence["line_number"], 1)
            self.assertEqual(evidence["creator_profile_id"], "creator_luna_fit")
            self.assertTrue(evidence["content_hash"])
            self.assertTrue(evidence["indexed_on"])

            metric = only("metric_snapshot_luna_fit_001")
            self.assertEqual(metric["line_number"], 1)
            self.assertEqual(
                metric["source_path"],
                f"research/runs/{RUN_ID}/metric-snapshots.jsonl",
            )

            entry = only(ENTRY_ID)
            self.assertEqual(
                entry["source_path"],
                f"research/idea-queue/entries/{ENTRY_ID}.json",
            )
            self.assertIsNone(entry["line_number"])

            only("idea_promotion_luna_fit_001")
            only("video_research_luna_fit_001")
            only("stable_finding_luna_fit_001")

            project = only(PROJECT_ID)
            self.assertEqual(project["project_id"], PROJECT_ID)
            self.assertEqual(
                project["source_path"], f"projects/{PROJECT_ID}/project.json"
            )

            idea_card = only(f"card_{ENTRY_ID}")
            self.assertEqual(idea_card["source_path"], "boards/content-board.json")
            self.assertIsNone(idea_card["project_id"])
            project_card = only(f"card_{PROJECT_ID}")
            self.assertEqual(project_card["project_id"], PROJECT_ID)

    def test_finding_id_dual_resolves_to_findings_and_stable_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            db_path = db_path_for(temp_dir)
            rebuild_index(workspace_dir, db_path=db_path)

            rows = resolve_record_id(db_path, "finding_luna_fit_desk_reset_lunch")
            self.assertEqual(len(rows), 2)
            self.assertEqual({row["record_type"] for row in rows}, {"research-finding"})
            self.assertEqual(
                {row["source_path"] for row in rows},
                {
                    "research/findings.md",
                    "research/stable-findings/stable_finding_luna_fit_001.md",
                },
            )

    def test_rebuild_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            db_path = db_path_for(temp_dir)
            first = rebuild_index(workspace_dir, db_path=db_path)
            second = rebuild_index(workspace_dir, db_path=db_path)
            self.assertEqual(first["row_count"], second["row_count"])

            connection = sqlite3.connect(db_path)
            try:
                total = connection.execute("SELECT COUNT(*) FROM records").fetchone()[0]
            finally:
                connection.close()
            self.assertEqual(total, second["row_count"])

    def test_rebuild_replaces_only_the_named_creators_rows(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            db_path = db_path_for(temp_dir)
            rebuild_index(workspace_dir, db_path=db_path)

            connection = sqlite3.connect(db_path)
            try:
                connection.execute(
                    "INSERT INTO records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        "evidence_other_001",
                        "research-evidence",
                        "creator_other",
                        "other-creator",
                        None,
                        "research/runs/research_run_other/evidence.jsonl",
                        1,
                        "hash",
                        "2026-07-03T00:00:00+00:00",
                    ),
                )
                connection.commit()
            finally:
                connection.close()

            rebuild_index(workspace_dir, db_path=db_path)
            rows = resolve_record_id(db_path, "evidence_other_001")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["creator_slug"], "other-creator")


class RecallIndexFailClosedTests(unittest.TestCase):
    def test_duplicate_unique_id_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            # The same pack id in the workspace-level and run-level pack
            # directories is ambiguous for bare-id resolution.
            pack = load_example("video-understanding-pack")
            write_json(
                workspace_dir / "research" / "runs" / RUN_ID
                / "video-understanding-packs" / "video_research_luna_fit_001.json",
                pack,
            )

            with self.assertRaises(ValidationError) as ctx:
                collect_index_rows(workspace_dir)
            self.assertIn("more than one source", str(ctx.exception))

    def test_malformed_jsonl_fails_closed_with_line(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            evidence_path = workspace_dir / "research" / "runs" / RUN_ID / "evidence.jsonl"
            with evidence_path.open("a") as handle:
                handle.write("{not json\n")

            with self.assertRaises(ValidationError) as ctx:
                collect_index_rows(workspace_dir)
            self.assertIn("evidence.jsonl:2:", str(ctx.exception))

    def test_default_db_path_requires_creators_layout(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)

            with self.assertRaises(ValidationError) as ctx:
                rebuild_index(workspace_dir)
            self.assertIn("creators/", str(ctx.exception))

    def test_default_db_path_used_under_creators_layout(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            creators_dir = Path(temp_dir) / "workspace-library" / "creators"
            creators_dir.mkdir(parents=True)
            workspace_dir = scaffold_indexable_workspace(creators_dir)

            result = rebuild_index(workspace_dir)
            self.assertEqual(
                result["db_path"],
                Path(temp_dir).resolve() / "workspace-library" / "index"
                / "influencer-os.sqlite",
            )
            self.assertTrue(result["db_path"].exists())


class RecallIndexCliTests(unittest.TestCase):
    def test_rebuild_index_command(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            db_path = db_path_for(temp_dir)

            result = subprocess.run(
                [
                    sys.executable, "-m", "influencer_os", "rebuild-index",
                    str(workspace_dir), "--db", str(db_path),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Rebuilt recall index rows for luna-fit", result.stdout)
            self.assertTrue(db_path.exists())


if __name__ == "__main__":
    unittest.main()
