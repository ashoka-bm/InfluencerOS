"""Phase 2 slice 3: Performance Summary contract.

Covers the at-rest performance-summary.json checks in validate_project —
evidence-ref resolution against registered records, stage uniqueness, chain
id pinning, containment — and the published-but-never-summarized advisory
WARN. There is no summary write gate: the interpretive skill authors the
record and validate_project is the enforcement seam, so every check here is
an at-rest probe.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from influencer_os.projects import (
    PERFORMANCE_SUMMARY_DUE_HOURS,
    add_analytics_snapshot,
    validate_project,
)
from influencer_os.validation import ValidationError
from tests.test_analytics import (
    scaffold_published_project,
    stage_snapshot_record,
)
from tests.test_cli import copy_example_record, rewrite_json
from tests.test_published_posts import scaffold_project_workspace


ROOT = Path(__file__).resolve().parents[1]

# A snapshot_at past the WARN maturity threshold relative to the example
# published_at (2026-06-29T18:30:00Z).
MATURE_SNAPSHOT_AT = "2026-07-03T18:30:00Z"
MATURE_HOURS = 96


def ingest_example_snapshot(temp_dir, project_dir, mutate=None):
    record_path = stage_snapshot_record(temp_dir, mutate=mutate)
    return add_analytics_snapshot(project_dir, record_path)


def make_snapshot_mature(record):
    record["snapshot_at"] = MATURE_SNAPSHOT_AT
    record["hours_since_publish"] = MATURE_HOURS


def write_summary(project_dir, mutate=None):
    summary_path = project_dir / "performance-summary.json"
    copy_example_record("performance-summary.example.json", summary_path)
    if mutate is not None:
        rewrite_json(summary_path, mutate)
    return summary_path


def summary_warnings(result):
    """The slice 3 WARN only; the fixture promotion emits its own advisories."""
    return [w for w in result["warnings"] if "performance-summary.json" in w]


def scaffold_summarized_project(temp_dir, snapshot_mutate=None):
    """A published project with one ingested snapshot and the example summary."""
    workspace_dir, project_dir = scaffold_published_project(temp_dir)
    ingest_example_snapshot(temp_dir, project_dir, mutate=snapshot_mutate)
    write_summary(project_dir)
    return workspace_dir, project_dir


class PerformanceSummaryAtRestTests(unittest.TestCase):
    def test_valid_summary_passes_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_summarized_project(temp_dir)
            result = validate_project(project_dir)
            self.assertEqual(summary_warnings(result), [])

    def test_dangling_published_post_record_id_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_summarized_project(temp_dir)

            def mutate(record):
                record["evidence_refs"]["published_post_record_ids"].append("ppr_never_registered")

            write_summary(project_dir, mutate=mutate)
            with self.assertRaisesRegex(ValueError, "published_post_record_ids do not resolve"):
                validate_project(project_dir)

    def test_dangling_analytics_snapshot_id_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_summarized_project(temp_dir)

            def mutate(record):
                record["evidence_refs"]["analytics_snapshot_ids"] = ["analytics_snapshot_never_ingested"]

            write_summary(project_dir, mutate=mutate)
            with self.assertRaisesRegex(ValueError, "analytics_snapshot_ids do not resolve"):
                validate_project(project_dir)

    def test_output_package_id_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_summarized_project(temp_dir)

            def mutate(record):
                record["evidence_refs"]["output_package_id"] = "output_package_other_project"

            write_summary(project_dir, mutate=mutate)
            with self.assertRaisesRegex(ValueError, "output_package_id does not match"):
                validate_project(project_dir)

    def test_project_id_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_summarized_project(temp_dir)

            def mutate(record):
                record["project_id"] = "project_other_creator_post"

            write_summary(project_dir, mutate=mutate)
            with self.assertRaisesRegex(ValueError, "project_id does not match"):
                validate_project(project_dir)

    def test_creator_profile_id_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_summarized_project(temp_dir)

            def mutate(record):
                record["creator_profile_id"] = "creator_someone_else"

            write_summary(project_dir, mutate=mutate)
            with self.assertRaisesRegex(ValueError, "creator_profile_id does not match"):
                validate_project(project_dir)

    def test_duplicated_stage_fails(self):
        # The schema's minItems: 5 + enum admits five findings with a
        # repeated stage; record semantics close that gap, and it is
        # reported as the duplicate, not the stage the repeat displaced.
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_summarized_project(temp_dir)

            def mutate(record):
                record["stage_findings"][4]["stage"] = "hook"

            write_summary(project_dir, mutate=mutate)
            with self.assertRaisesRegex(ValidationError, "duplicate stages.*hook"):
                validate_project(project_dir)

    def test_six_findings_with_duplicate_stage_fail(self):
        # All five stages present plus a repeat: required-stages passes,
        # so only the uniqueness rule can reject this shape.
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_summarized_project(temp_dir)

            def mutate(record):
                extra = dict(record["stage_findings"][0])
                record["stage_findings"].append(extra)

            write_summary(project_dir, mutate=mutate)
            with self.assertRaisesRegex(ValidationError, "duplicate stages.*packaging"):
                validate_project(project_dir)

    def test_schema_invalid_summary_fails_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_summarized_project(temp_dir)

            def mutate(record):
                del record["semantic_lookup"]

            write_summary(project_dir, mutate=mutate)
            with self.assertRaises(ValidationError):
                validate_project(project_dir)

    def test_summary_on_unpackaged_project_fails(self):
        # A freshly initialized project has no registered Output Package;
        # a summary cannot attach to a project with nothing to measure.
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            write_summary(project_dir)
            with self.assertRaisesRegex(ValueError, "requires a packaged project"):
                validate_project(project_dir)

    def test_symlinked_summary_escaping_project_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            ingest_example_snapshot(temp_dir, project_dir)
            outside_path = Path(temp_dir) / "outside-summary.json"
            copy_example_record("performance-summary.example.json", outside_path)
            (project_dir / "performance-summary.json").symlink_to(outside_path)
            with self.assertRaisesRegex(ValueError, "escapes root"):
                validate_project(project_dir)


class PerformanceSummaryWarnTests(unittest.TestCase):
    def test_warn_fires_for_mature_unsummarized_published_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            ingest_example_snapshot(temp_dir, project_dir, mutate=make_snapshot_mature)
            warnings = summary_warnings(validate_project(project_dir))
            self.assertEqual(len(warnings), 1)
            self.assertIn(str(PERFORMANCE_SUMMARY_DUE_HOURS), warnings[0])

    def test_no_warn_below_maturity_threshold(self):
        # The example snapshot sits at 24h — inside the platform reporting
        # lag, so nagging for a summary would over-read early data.
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            ingest_example_snapshot(temp_dir, project_dir)
            result = validate_project(project_dir)
            self.assertEqual(summary_warnings(result), [])

    def test_no_warn_once_summary_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_summarized_project(
                temp_dir, snapshot_mutate=make_snapshot_mature
            )
            result = validate_project(project_dir)
            self.assertEqual(summary_warnings(result), [])

    def test_warn_derives_maturity_when_hours_hand_edited_to_null(self):
        # hours_since_publish is authoritative when recorded; when a
        # hand-edit nulls it, maturity still derives from the timestamps.
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            result = ingest_example_snapshot(
                temp_dir, project_dir, mutate=make_snapshot_mature
            )
            rewrite_json(
                result["snapshot_path"],
                lambda record: record.update(hours_since_publish=None),
            )
            warnings = summary_warnings(validate_project(project_dir))
            self.assertEqual(len(warnings), 1)

    def test_cli_validate_project_prints_warn_to_stderr(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_published_project(temp_dir)
            ingest_example_snapshot(temp_dir, project_dir, mutate=make_snapshot_mature)
            result = subprocess.run(
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
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Validated project", result.stdout)
            self.assertIn("performance-summary.json", result.stderr)


if __name__ == "__main__":
    unittest.main()
