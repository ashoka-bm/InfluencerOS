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
# init-project creates slug-named project folders (process-learning
# 2026-07-03: scaffolds copy the CLI's layout, not an approximation).
PROJECT_SLUG = "tiny-reset-after-laptop-day"
PPR_ID = "ppr_luna_tiny_reset_youtube_001"
SNAPSHOT_ID = "analytics_snapshot_luna_tiny_reset_youtube_24h"
SUMMARY_ID = "performance_summary_luna_tiny_reset_001"
SECOND_PROJECT_ID = "project_luna_second_001"


def second_project_manifest():
    """A schema-valid manifest for a second project, so duplicate-id probes
    can anchor their planted records properly."""
    manifest = load_example("project")
    manifest["project_id"] = SECOND_PROJECT_ID
    return manifest


def scaffold_indexable_workspace(temp_dir):
    """Research scaffold plus one project carrying the three Phase 2 learning
    records, so every indexed record kind exists. Per-record files carry
    their id as the filename, mirroring the writers."""
    workspace_dir = scaffold_research_workspace(temp_dir)
    # The research scaffold carries the example project in an id-named
    # folder; init-project builds slug-named folders, so mirror that here.
    project_dir = workspace_dir / "projects" / PROJECT_SLUG
    (workspace_dir / "projects" / PROJECT_ID).rename(project_dir)
    write_json(
        project_dir / "published" / "published-post-records" / f"{PPR_ID}.json",
        load_example("published-post-record"),
    )
    write_json(
        project_dir / "analytics" / "snapshots" / f"{SNAPSHOT_ID}.json",
        load_example("analytics-snapshot"),
    )
    write_json(
        project_dir / "performance-summary.json",
        load_example("performance-summary"),
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
                f"research/content-opportunity-queue/entries/{ENTRY_ID}.json",
            )
            self.assertIsNone(entry["line_number"])

            only("concept_approval_luna_fit_001")
            only("video_research_luna_fit_001")
            only("stable_finding_luna_fit_001")

            project = only(PROJECT_ID)
            self.assertEqual(project["project_id"], PROJECT_ID)
            self.assertEqual(
                project["source_path"], f"projects/{PROJECT_SLUG}/project.json"
            )

            post = only(PPR_ID)
            self.assertEqual(post["record_type"], "published-post-record")
            self.assertEqual(
                post["source_path"],
                f"projects/{PROJECT_SLUG}/published/published-post-records/"
                f"{PPR_ID}.json",
            )
            self.assertEqual(post["project_id"], PROJECT_ID)

            snapshot = only(SNAPSHOT_ID)
            self.assertEqual(snapshot["record_type"], "analytics-snapshot")
            self.assertEqual(
                snapshot["source_path"],
                f"projects/{PROJECT_SLUG}/analytics/snapshots/{SNAPSHOT_ID}.json",
            )
            self.assertEqual(snapshot["project_id"], PROJECT_ID)

            summary = only(SUMMARY_ID)
            self.assertEqual(summary["record_type"], "performance-summary")
            self.assertEqual(
                summary["source_path"],
                f"projects/{PROJECT_SLUG}/performance-summary.json",
            )
            self.assertEqual(summary["project_id"], PROJECT_ID)

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

            foreign_rows = (
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
                (
                    "analytics_snapshot_other_001",
                    "analytics-snapshot",
                    "creator_other",
                    "other-creator",
                    "project_other_001",
                    "projects/other-post/analytics/snapshots/"
                    "analytics_snapshot_other_001.json",
                    None,
                    "hash",
                    "2026-07-03T00:00:00+00:00",
                ),
            )
            connection = sqlite3.connect(db_path)
            try:
                connection.executemany(
                    "INSERT INTO records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    foreign_rows,
                )
                connection.commit()
            finally:
                connection.close()

            rebuild_index(workspace_dir, db_path=db_path)
            for record_id in ("evidence_other_001", "analytics_snapshot_other_001"):
                rows = resolve_record_id(db_path, record_id)
                self.assertEqual(len(rows), 1, record_id)
                self.assertEqual(rows[0]["creator_slug"], "other-creator")

    def test_delete_and_rebuild_reproduces_identical_rows(self):
        # ADR 0010 reconciliation: the database is never the only copy of
        # anything, so deleting it and rebuilding must reproduce the same
        # rows modulo the indexed_on timestamp.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            db_path = db_path_for(temp_dir)

            def dump_rows():
                connection = sqlite3.connect(db_path)
                try:
                    return connection.execute(
                        "SELECT record_id, record_type, creator_profile_id, "
                        "creator_slug, project_id, source_path, line_number, "
                        "content_hash FROM records "
                        "ORDER BY record_type, record_id, source_path"
                    ).fetchall()
                finally:
                    connection.close()

            rebuild_index(workspace_dir, db_path=db_path)
            first = dump_rows()
            db_path.unlink()
            rebuild_index(workspace_dir, db_path=db_path)
            self.assertEqual(first, dump_rows())
            self.assertTrue(first)


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

    def test_duplicate_stable_finding_id_fails_closed(self):
        # Two stable-finding files carrying the same stable_finding_id make
        # bare-id resolution ambiguous; rest validation also rejects this via
        # the filename==id rule, and the projection defends itself too.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            stable_dir = workspace_dir / "research" / "stable-findings"
            original = stable_dir / "stable_finding_luna_fit_001.md"
            (stable_dir / "stable_finding_luna_fit_copy.md").write_text(
                original.read_text()
            )

            with self.assertRaises(ValidationError) as ctx:
                collect_index_rows(workspace_dir)
            self.assertIn("more than one source", str(ctx.exception))

    def test_duplicate_published_post_record_id_across_projects_fails_closed(self):
        # Two fully anchored projects (valid manifests, matching chain ids,
        # filename==id) sharing one published-post id is still ambiguous for
        # bare-id resolution.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            second_dir = workspace_dir / "projects" / "second-project"
            write_json(second_dir / "project.json", second_project_manifest())
            post = load_example("published-post-record")
            post["project_id"] = SECOND_PROJECT_ID
            write_json(
                second_dir / "published" / "published-post-records"
                / f"{PPR_ID}.json",
                post,
            )

            with self.assertRaises(ValidationError) as ctx:
                collect_index_rows(workspace_dir)
            self.assertIn("more than one source", str(ctx.exception))

    def test_duplicate_analytics_snapshot_id_across_projects_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            second_dir = workspace_dir / "projects" / "second-project"
            write_json(second_dir / "project.json", second_project_manifest())
            snapshot = load_example("analytics-snapshot")
            snapshot["project_id"] = SECOND_PROJECT_ID
            write_json(
                second_dir / "analytics" / "snapshots" / f"{SNAPSHOT_ID}.json",
                snapshot,
            )

            with self.assertRaises(ValidationError) as ctx:
                collect_index_rows(workspace_dir)
            self.assertIn("more than one source", str(ctx.exception))

    def test_id_field_only_record_fails_closed(self):
        # Existence of an id is not existence of a record (process-learning
        # 2026-07-06): a planted JSON carrying only the id fields must not
        # index as an analytics snapshot, even inside an anchored project.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            write_json(
                workspace_dir / "projects" / PROJECT_SLUG / "analytics"
                / "snapshots" / "analytics_snapshot_fake.json",
                {
                    "analytics_snapshot_id": "analytics_snapshot_fake",
                    "project_id": PROJECT_ID,
                },
            )

            with self.assertRaises(ValidationError) as ctx:
                collect_index_rows(workspace_dir)
            self.assertIn("analytics_snapshot_fake.json", str(ctx.exception))
            self.assertIn("not a valid analytics-snapshot", str(ctx.exception))

    def test_id_field_only_record_in_unanchored_folder_fails_closed(self):
        # The slice 5 review reproduction: junk in a fake project folder with
        # no manifest fails on the missing anchor.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            write_json(
                workspace_dir / "projects" / "fake-project" / "analytics"
                / "snapshots" / "analytics_snapshot_fake.json",
                {
                    "analytics_snapshot_id": "analytics_snapshot_fake",
                    "project_id": "project_nonexistent_001",
                },
            )

            with self.assertRaises(ValidationError) as ctx:
                collect_index_rows(workspace_dir)
            self.assertIn("fake-project", str(ctx.exception))
            self.assertIn("manifest", str(ctx.exception))

    def test_record_filename_must_equal_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            snapshots_dir = (
                workspace_dir / "projects" / PROJECT_SLUG / "analytics" / "snapshots"
            )
            (snapshots_dir / f"{SNAPSHOT_ID}.json").rename(
                snapshots_dir / "analytics_snapshot_renamed.json"
            )

            with self.assertRaises(ValidationError) as ctx:
                collect_index_rows(workspace_dir)
            self.assertIn("filename", str(ctx.exception))

    def test_record_project_id_must_match_owning_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            summary_path = (
                workspace_dir / "projects" / PROJECT_SLUG / "performance-summary.json"
            )
            summary = load_example("performance-summary")
            summary["project_id"] = "project_someone_elses_001"
            write_json(summary_path, summary)

            with self.assertRaises(ValidationError) as ctx:
                collect_index_rows(workspace_dir)
            self.assertIn("manifest", str(ctx.exception))

    def test_valid_record_without_project_manifest_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            post = load_example("published-post-record")
            write_json(
                workspace_dir / "projects" / "unanchored" / "published"
                / "published-post-records" / f"{PPR_ID}.json",
                post,
            )

            with self.assertRaises(ValidationError) as ctx:
                collect_index_rows(workspace_dir)
            self.assertIn("manifest", str(ctx.exception))

    def test_raw_analytics_payloads_are_never_scanned(self):
        # analytics/raw/ holds safe exports outside the record contract; the
        # scan names only snapshots/, so a raw copy of a snapshot must
        # neither index nor trip duplicate-id detection.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            write_json(
                workspace_dir / "projects" / PROJECT_SLUG / "analytics"
                / "raw" / "platform-export.json",
                load_example("analytics-snapshot"),
            )

            rows = collect_index_rows(workspace_dir)
            raw_paths = [
                row["source_path"] for row in rows
                if "analytics/raw" in row["source_path"]
            ]
            self.assertEqual(raw_paths, [])
            snapshot_rows = [
                row for row in rows if row["record_id"] == SNAPSHOT_ID
            ]
            self.assertEqual(len(snapshot_rows), 1)

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
