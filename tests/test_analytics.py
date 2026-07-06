"""Phase 2 slice 2: Analytics Snapshot ingestion.

Covers the shared ingestion seam (write_analytics_snapshot), manual entry,
the neutral CSV import, and the at-rest parity checks in validate_project.
Every ingestion path — manual, CSV, and the mocked API shape — goes through
one writer, and every writer invariant has a hand-edit probe.
"""
import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from influencer_os.analytics import csv_columns, import_analytics_csv
from influencer_os.projects import (
    add_analytics_snapshot,
    register_published_post,
    validate_project,
    write_analytics_snapshot,
)
from influencer_os.validation import validate_record
from tests.test_cli import copy_example_record, rewrite_json
from tests.test_published_posts import scaffold_packaged_project, stage_published_record


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_SNAPSHOT_ID = "analytics_snapshot_luna_tiny_reset_youtube_24h"


def scaffold_published_project(temp_dir):
    """A published project: packaged, with the example live PPR registered."""
    workspace_dir, project_dir = scaffold_packaged_project(temp_dir)
    register_published_post(project_dir, stage_published_record(temp_dir))
    stage_raw_files(project_dir)
    return workspace_dir, project_dir


def stage_raw_files(project_dir):
    """The raw files the example snapshot references under analytics/raw/."""
    raw_dir = project_dir / "analytics" / "raw"
    (raw_dir / "youtube-24h-manual-entry.json").write_text("{}\n")
    (raw_dir / "youtube-retention-24h.csv").write_text("second,retention\n")


def stage_snapshot_record(temp_dir, mutate=None, filename="analytics-snapshot.json"):
    record_path = Path(temp_dir) / filename
    copy_example_record("analytics-snapshot.example.json", record_path)
    if mutate is not None:
        rewrite_json(record_path, mutate)
    return record_path


def snapshot_destination(project_dir, snapshot_id=EXAMPLE_SNAPSHOT_ID):
    return project_dir / "analytics" / "snapshots" / f"{snapshot_id}.json"


def csv_row_from_record(record, overrides=None):
    """Flatten a schema-shaped record into a template CSV row."""
    row = {
        "analytics_snapshot_id": record["analytics_snapshot_id"],
        "published_post_record_id": record["published_post_record_id"],
        "snapshot_at": record["snapshot_at"],
        "source_type": record["source"]["source_type"],
        "collected_by": record["source"]["collected_by"],
        "confidence": record["source"]["confidence"],
        "platform": record["platform"],
        "hours_since_publish": _cell(record["hours_since_publish"]),
        "raw_source_ref": _cell(record["raw_source_ref"]),
        "notes": record["notes"],
    }
    for field, value in record["metrics"].items():
        row[field] = _cell(value)
    for stage, stage_record in record["attribution_metrics"].items():
        for field, value in stage_record.items():
            row[f"{stage}_{field}"] = _cell(value)
    if overrides:
        row.update(overrides)
    return row


def _cell(value):
    return "" if value is None else str(value)


def write_csv(temp_dir, rows, columns=None, filename="snapshots.csv"):
    columns = columns or csv_columns()
    csv_path = Path(temp_dir) / filename
    with open(csv_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return csv_path


class AddAnalyticsSnapshotTests(unittest.TestCase):
    def test_cli_ingests_manual_snapshot(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            record_path = stage_snapshot_record(temp_dir)

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "add-analytics-snapshot",
                    str(record_path),
                    "--project",
                    str(project_dir),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Ingested analytics snapshot", result.stdout)
            self.assertTrue(snapshot_destination(project_dir).exists())
            validate_project(project_dir)

    def test_derives_hours_since_publish_when_null(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            record_path = stage_snapshot_record(
                temp_dir, lambda record: record.update(hours_since_publish=None)
            )

            result = add_analytics_snapshot(project_dir, record_path)

            self.assertEqual(result["hours_since_publish"], 24.0)
            written = json.loads(snapshot_destination(project_dir).read_text())
            self.assertEqual(written["hours_since_publish"], 24.0)

    def test_rejects_snapshot_earlier_than_publish(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            record_path = stage_snapshot_record(
                temp_dir,
                lambda record: record.update(
                    hours_since_publish=None, snapshot_at="2026-06-28T18:30:00Z"
                ),
            )

            with self.assertRaises(ValueError) as ctx:
                add_analytics_snapshot(project_dir, record_path)

            self.assertIn("earlier than", str(ctx.exception))

    def test_rejects_pre_publication_snapshot_with_supplied_hours(self):
        # Review finding: the ordering check must not depend on derivation.
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            record_path = stage_snapshot_record(
                temp_dir,
                lambda record: record.update(
                    snapshot_at="2026-06-28T18:30:00Z", hours_since_publish=24
                ),
            )

            with self.assertRaises(ValueError) as ctx:
                add_analytics_snapshot(project_dir, record_path)

            self.assertIn("earlier than", str(ctx.exception))

    def test_rejects_symlinked_raw_ref_inside_project(self):
        # Review finding: a symlink under analytics/raw/ pointing at another
        # project file must not pass containment.
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            link = project_dir / "analytics" / "raw" / "project-link.json"
            link.symlink_to(Path("..") / ".." / "project.json")
            record_path = stage_snapshot_record(
                temp_dir,
                lambda record: record.update(
                    raw_source_ref="analytics/raw/project-link.json"
                ),
            )

            with self.assertRaises(ValueError) as ctx:
                add_analytics_snapshot(project_dir, record_path)

            self.assertIn("escapes root", str(ctx.exception))

    def test_rejects_below_published_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_packaged_project(temp_dir)
            record_path = stage_snapshot_record(temp_dir)

            with self.assertRaises(ValueError) as ctx:
                add_analytics_snapshot(project_dir, record_path)

            self.assertIn("requires a published project", str(ctx.exception))

    def test_rejects_dangling_published_post_record(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            record_path = stage_snapshot_record(
                temp_dir,
                lambda record: record.update(published_post_record_id="ppr_missing_001"),
            )

            with self.assertRaises(ValueError) as ctx:
                add_analytics_snapshot(project_dir, record_path)

            self.assertIn("does not resolve to a registered published post record", str(ctx.exception))

    def test_rejects_platform_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            record_path = stage_snapshot_record(
                temp_dir, lambda record: record.update(platform="instagram_reels")
            )

            with self.assertRaises(ValueError) as ctx:
                add_analytics_snapshot(project_dir, record_path)

            self.assertIn("platform does not match", str(ctx.exception))

    def test_rejects_snapshot_for_non_live_publication(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            failed_record = stage_published_record(
                temp_dir,
                lambda record: record.update(
                    published_post_record_id="ppr_luna_tiny_reset_youtube_failed",
                    publication_status="failed",
                    public_url=None,
                    platform_post_id=None,
                ),
                filename="failed-record.json",
            )
            register_published_post(project_dir, failed_record)
            record_path = stage_snapshot_record(
                temp_dir,
                lambda record: record.update(
                    published_post_record_id="ppr_luna_tiny_reset_youtube_failed"
                ),
            )

            with self.assertRaises(ValueError) as ctx:
                add_analytics_snapshot(project_dir, record_path)

            self.assertIn("only measure posts that went live", str(ctx.exception))

    def test_rejects_raw_ref_outside_analytics_raw(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            record_path = stage_snapshot_record(
                temp_dir,
                lambda record: record.update(raw_source_ref="output-package/output-package.json"),
            )

            with self.assertRaises(ValueError) as ctx:
                add_analytics_snapshot(project_dir, record_path)

            self.assertIn("must live under analytics/raw/", str(ctx.exception))

    def test_rejects_raw_ref_escape(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            record_path = stage_snapshot_record(
                temp_dir,
                lambda record: record.update(raw_source_ref="analytics/raw/../../project.json"),
            )

            with self.assertRaises(ValueError) as ctx:
                add_analytics_snapshot(project_dir, record_path)

            self.assertIn("relative path inside the project", str(ctx.exception))

    def test_rejects_missing_raw_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            (project_dir / "analytics" / "raw" / "youtube-24h-manual-entry.json").unlink()
            record_path = stage_snapshot_record(temp_dir)

            with self.assertRaises(FileNotFoundError) as ctx:
                add_analytics_snapshot(project_dir, record_path)

            self.assertIn("does not resolve to a file", str(ctx.exception))

    def test_rejects_duplicate_snapshot_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            record_path = stage_snapshot_record(temp_dir)
            add_analytics_snapshot(project_dir, record_path)

            with self.assertRaises(FileExistsError):
                add_analytics_snapshot(project_dir, record_path)

    def test_api_sourced_record_flows_through_shared_writer(self):
        # ADR 0004: a future API connector produces the same record shape and
        # writes through the same seam; this mock pins that contract.
        def fake_connector_fetch(example_path):
            record = json.loads(example_path.read_text())
            record["analytics_snapshot_id"] = "analytics_snapshot_luna_tiny_reset_api_48h"
            record["snapshot_at"] = "2026-07-01T18:30:00Z"
            record["hours_since_publish"] = None
            record["source"] = {
                "source_type": "api",
                "collected_by": "mock-platform-connector",
                "confidence": "high",
            }
            record["raw_source_ref"] = None
            record["attribution_metrics"]["body_retention"]["retention_curve_ref"] = None
            return record

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            record = fake_connector_fetch(ROOT / "examples" / "analytics-snapshot.example.json")

            result = write_analytics_snapshot(project_dir, record)

            self.assertEqual(result["hours_since_publish"], 48.0)
            written = json.loads(
                snapshot_destination(
                    project_dir, "analytics_snapshot_luna_tiny_reset_api_48h"
                ).read_text()
            )
            self.assertEqual(written["source"]["source_type"], "api")
            validate_project(project_dir)


class ImportAnalyticsCsvTests(unittest.TestCase):
    def example_record(self):
        return json.loads((ROOT / "examples" / "analytics-snapshot.example.json").read_text())

    def test_imports_rows_with_blank_metrics_as_null(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            base = self.example_record()
            row_one = csv_row_from_record(base)
            row_two = csv_row_from_record(
                base,
                overrides={
                    "analytics_snapshot_id": "analytics_snapshot_luna_tiny_reset_youtube_72h",
                    "snapshot_at": "2026-07-02T18:30:00Z",
                    "hours_since_publish": "",
                    "views": "2400",
                    "impressions": "",
                    "raw_source_ref": "",
                    "body_retention_retention_curve_ref": "",
                    "source_type": "csv",
                },
            )
            csv_path = write_csv(temp_dir, [row_one, row_two])

            results = import_analytics_csv(project_dir, csv_path)

            self.assertEqual(len(results), 2)
            second = json.loads(
                snapshot_destination(
                    project_dir, "analytics_snapshot_luna_tiny_reset_youtube_72h"
                ).read_text()
            )
            self.assertEqual(second["metrics"]["views"], 2400)
            self.assertIsNone(second["metrics"]["impressions"])
            self.assertEqual(second["hours_since_publish"], 72.0)
            self.assertEqual(second["source"]["source_type"], "csv")
            validate_project(project_dir)

    def test_rejects_header_not_matching_template(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            columns = [c for c in csv_columns() if c != "platform"]
            row = {k: v for k, v in csv_row_from_record(self.example_record()).items() if k != "platform"}
            csv_path = write_csv(temp_dir, [row], columns=columns)

            with self.assertRaises(ValueError) as ctx:
                import_analytics_csv(project_dir, csv_path)

            self.assertIn("does not match the InfluencerOS template", str(ctx.exception))

    def test_rejects_non_numeric_metric_cell_with_row_number(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            row = csv_row_from_record(self.example_record(), overrides={"views": "lots"})
            csv_path = write_csv(temp_dir, [row])

            with self.assertRaises(ValueError) as ctx:
                import_analytics_csv(project_dir, csv_path)

            self.assertIn("row 2", str(ctx.exception))
            self.assertIn("'views'", str(ctx.exception))

    def test_failed_row_rolls_back_written_rows(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            base = self.example_record()
            good_row = csv_row_from_record(base)
            bad_row = csv_row_from_record(
                base,
                overrides={
                    "analytics_snapshot_id": "analytics_snapshot_luna_tiny_reset_bad",
                    "published_post_record_id": "ppr_missing_001",
                },
            )
            csv_path = write_csv(temp_dir, [good_row, bad_row])

            with self.assertRaises(ValueError):
                import_analytics_csv(project_dir, csv_path)

            snapshots_dir = project_dir / "analytics" / "snapshots"
            self.assertEqual(list(snapshots_dir.glob("*.json")), [])
            validate_project(project_dir)

    def test_rejects_nan_and_infinite_metric_cells(self):
        # Review finding: float() accepts "nan"/"inf"; neither is valid JSON
        # and NaN silently defeats the validator's min/max comparisons.
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            for bad_value in ("nan", "inf", "-inf"):
                row = csv_row_from_record(self.example_record(), overrides={"views": bad_value})
                csv_path = write_csv(temp_dir, [row], filename=f"bad-{bad_value.strip('-')}.csv")

                with self.assertRaises(ValueError) as ctx:
                    import_analytics_csv(project_dir, csv_path)

                self.assertIn("finite", str(ctx.exception))

    def test_validator_rejects_nan_in_record(self):
        from influencer_os.validation import ValidationError

        record = self.example_record()
        record["metrics"]["views"] = float("nan")

        with self.assertRaises(ValidationError) as ctx:
            validate_record("analytics-snapshot", record)

        self.assertIn("not a finite number", str(ctx.exception))

    def test_template_file_matches_column_contract(self):
        template = (ROOT / "docs" / "templates" / "analytics" / "analytics-snapshot-template.csv")
        header = next(csv.reader(io.StringIO(template.read_text())))
        self.assertEqual(header, csv_columns())

    def test_full_csv_row_constructs_schema_valid_record(self):
        # Drift pin: the CSV column constants must construct a record the
        # analytics-snapshot schema accepts.
        from influencer_os.analytics import _row_to_record

        record = self.example_record()
        row = csv_row_from_record(record)
        constructed = _row_to_record(
            row,
            {"project_id": record["project_id"], "creator_profile_id": record["creator_profile_id"]},
            {"output_package_id": record["output_package_id"]},
        )
        validate_record("analytics-snapshot", constructed)


class AnalyticsAtRestTests(unittest.TestCase):
    def ingested_project(self, temp_dir):
        _, project_dir = scaffold_published_project(temp_dir)
        add_analytics_snapshot(project_dir, stage_snapshot_record(temp_dir))
        return project_dir

    def test_hand_edited_package_mismatch_fails_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = self.ingested_project(temp_dir)
            rewrite_json(
                snapshot_destination(project_dir),
                lambda record: record.update(output_package_id="output_package_other_001"),
            )

            with self.assertRaises(ValueError) as ctx:
                validate_project(project_dir)

            self.assertIn("does not match the registered package", str(ctx.exception))

    def test_misnamed_snapshot_file_fails_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = self.ingested_project(temp_dir)
            destination = snapshot_destination(project_dir)
            destination.rename(destination.with_name("analytics_snapshot_renamed.json"))

            with self.assertRaises(ValueError) as ctx:
                validate_project(project_dir)

            self.assertIn("filename must match its id", str(ctx.exception))

    def test_hand_edited_pre_publication_snapshot_at_fails_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = self.ingested_project(temp_dir)
            rewrite_json(
                snapshot_destination(project_dir),
                lambda record: record.update(snapshot_at="2026-06-28T18:30:00Z"),
            )

            with self.assertRaises(ValueError) as ctx:
                validate_project(project_dir)

            self.assertIn("earlier than", str(ctx.exception))

    def test_symlinked_raw_file_fails_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = self.ingested_project(temp_dir)
            raw_file = project_dir / "analytics" / "raw" / "youtube-24h-manual-entry.json"
            raw_file.unlink()
            raw_file.symlink_to(Path("..") / ".." / "project.json")

            with self.assertRaises(ValueError) as ctx:
                validate_project(project_dir)

            self.assertIn("escapes root", str(ctx.exception))

    def test_deleted_raw_file_fails_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = self.ingested_project(temp_dir)
            (project_dir / "analytics" / "raw" / "youtube-retention-24h.csv").unlink()

            with self.assertRaises(FileNotFoundError) as ctx:
                validate_project(project_dir)

            self.assertIn("retention_curve_ref", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
