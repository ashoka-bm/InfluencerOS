"""Phase 2 slice 4: Learning distillation writer and at-rest parity.

Covers the evidence-linked creator-lesson writer (`append_creator_lesson`,
reached via `log-learning --evidence --strength`), the write-time evidence
resolution against workspace records, and the `validate workspace` at-rest
re-check of the same rules (exit criterion 4). The MEMORY.md promotion path
is the existing capped `memory-write` writer, whose refusal tests live in
tests/test_memory.py.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from influencer_os.creator_workspaces import validate_creator_workspace
from influencer_os.memory import (
    EVIDENCE_STRENGTHS,
    append_creator_lesson,
    creator_lessons_workspace,
    validate_creator_lessons,
)
from influencer_os.validation import ValidationError
from tests.test_performance_summary import scaffold_summarized_project


ROOT = Path(__file__).resolve().parents[1]

SUMMARY_ID = "performance_summary_luna_tiny_reset_001"
POST_ID = "ppr_luna_tiny_reset_youtube_001"
SNAPSHOT_ID = "analytics_snapshot_luna_tiny_reset_youtube_24h"
PROJECT_ID = "project_luna_tiny_reset_001"
PACKAGE_ID = "output_package_luna_tiny_reset_001"

LESSON = "Shorter spoken hooks hold viewers past the 3s mark."


def append_lesson(workspace_dir, **overrides):
    arguments = {
        "topic": "hooks",
        "lesson": LESSON,
        "evidence_ids": [SUMMARY_ID, SNAPSHOT_ID],
        "strength": "single_post_signal",
        "entry_date": "2026-07-06",
    }
    arguments.update(overrides)
    return append_creator_lesson(workspace_dir, **arguments)


def learnings_path(workspace_dir):
    return workspace_dir / "memory" / "learnings.md"


class CreatorLessonWriteTests(unittest.TestCase):
    def test_append_writes_dated_evidence_linked_entry_under_topic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_summarized_project(temp_dir)

            result = append_lesson(workspace_dir)

            self.assertEqual(result["status"], "written")
            content = learnings_path(workspace_dir).read_text()
            self.assertIn("## Creator Lessons", content)
            topic_section = content.split("### hooks")[1]
            self.assertIn(
                f"- 2026-07-06 [single_post_signal]: {LESSON} "
                f"(evidence: {SUMMARY_ID}, {SNAPSHOT_ID})",
                topic_section,
            )

    def test_append_accepts_every_performance_chain_id_type(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_summarized_project(temp_dir)

            result = append_lesson(
                workspace_dir,
                evidence_ids=[SUMMARY_ID, POST_ID, SNAPSHOT_ID, PROJECT_ID, PACKAGE_ID],
            )

            self.assertEqual(result["status"], "written")

    def test_append_rejects_unresolvable_evidence_and_leaves_file_unchanged(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_summarized_project(temp_dir)
            before = learnings_path(workspace_dir).read_text()

            with self.assertRaisesRegex(ValidationError, "ppr_ghost"):
                append_lesson(workspace_dir, evidence_ids=[SUMMARY_ID, "ppr_ghost"])

            self.assertEqual(learnings_path(workspace_dir).read_text(), before)

    def test_append_rejects_unsupported_evidence_prefix(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_summarized_project(temp_dir)

            with self.assertRaisesRegex(ValidationError, "prefix"):
                append_lesson(workspace_dir, evidence_ids=["finding_luna_fit_001"])

    def test_append_requires_evidence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_summarized_project(temp_dir)

            for empty in (None, []):
                with self.assertRaisesRegex(ValidationError, "evidence"):
                    append_lesson(workspace_dir, evidence_ids=empty)

    def test_append_rejects_unknown_strength(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_summarized_project(temp_dir)

            for strength in (None, "gut_feeling"):
                with self.assertRaisesRegex(ValidationError, "strength"):
                    append_lesson(workspace_dir, strength=strength)

    def test_append_rejects_impossible_calendar_date(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_summarized_project(temp_dir)

            with self.assertRaises(ValidationError):
                append_lesson(workspace_dir, entry_date="2026-99-99")

    def test_append_dedupes_same_lesson_within_topic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_summarized_project(temp_dir)
            append_lesson(workspace_dir)
            before = learnings_path(workspace_dir).read_text()

            result = append_lesson(workspace_dir, entry_date="2026-07-07")

            self.assertEqual(result["status"], "duplicate")
            self.assertEqual(learnings_path(workspace_dir).read_text(), before)

    def test_topic_headings_stay_scoped_to_creator_lessons_section(self):
        # A skill section with the same name as a lesson topic must not
        # receive the creator-lesson entry.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_summarized_project(temp_dir)
            path = learnings_path(workspace_dir)
            path.write_text(
                "# Learnings\n\n## Individual Skills\n\n### hooks\n\n"
                "- 2026-07-01: A per-skill note.\n"
            )

            append_lesson(workspace_dir)

            content = path.read_text()
            skills_section = content.split("## Individual Skills")[1].split("## Creator Lessons")[0]
            lessons_section = content.split("## Creator Lessons")[1]
            self.assertNotIn("[single_post_signal]", skills_section)
            self.assertIn("[single_post_signal]", lessons_section)

    def test_creator_lessons_workspace_detection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_summarized_project(temp_dir)

            self.assertEqual(
                creator_lessons_workspace(learnings_path(workspace_dir)), workspace_dir
            )
            self.assertIsNone(creator_lessons_workspace(ROOT / "context" / "learnings.md"))
            self.assertIsNone(
                creator_lessons_workspace(Path(temp_dir) / "memory" / "learnings.md")
            )


class CreatorLessonAtRestTests(unittest.TestCase):
    def test_workspace_with_valid_lesson_validates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_summarized_project(temp_dir)
            append_lesson(workspace_dir)

            result = validate_creator_workspace(workspace_dir)

            self.assertEqual(result["creator_slug"], "luna-fit")
            self.assertEqual(validate_creator_lessons(workspace_dir)["lesson_count"], 1)

    def test_hand_edited_dangling_evidence_fails_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_summarized_project(temp_dir)
            append_lesson(workspace_dir)
            path = learnings_path(workspace_dir)
            path.write_text(path.read_text().replace(SNAPSHOT_ID, "analytics_snapshot_ghost"))

            with self.assertRaisesRegex(ValidationError, "analytics_snapshot_ghost"):
                validate_creator_workspace(workspace_dir)

    def test_lesson_bullet_without_evidence_fails_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_summarized_project(temp_dir)
            path = learnings_path(workspace_dir)
            path.write_text(
                "# Learnings\n\n## Creator Lessons\n\n### hooks\n\n"
                "- 2026-07-06: A lesson missing its evidence suffix.\n"
            )

            with self.assertRaisesRegex(ValidationError, "evidence"):
                validate_creator_workspace(workspace_dir)

    def test_unknown_strength_marker_fails_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_summarized_project(temp_dir)
            append_lesson(workspace_dir)
            path = learnings_path(workspace_dir)
            path.write_text(
                path.read_text().replace("[single_post_signal]", "[gut_feeling]")
            )

            with self.assertRaisesRegex(ValidationError, "gut_feeling"):
                validate_creator_workspace(workspace_dir)

    def test_stray_prose_inside_creator_lessons_section_fails_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_summarized_project(temp_dir)
            path = learnings_path(workspace_dir)
            path.write_text(
                "# Learnings\n\n## Creator Lessons\n\n"
                "An unparseable free-text lesson.\n"
            )

            with self.assertRaises(ValidationError):
                validate_creator_workspace(workspace_dir)

    def test_content_outside_creator_lessons_section_is_not_policed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_summarized_project(temp_dir)
            path = learnings_path(workspace_dir)
            path.write_text(
                "# Learnings\n\n## General\n\nFree-form notes stay legal here.\n\n"
                "## Individual Skills\n\n### create-performance-summary\n\n"
                "- 2026-07-05: A per-skill entry without evidence.\n"
            )

            result = validate_creator_workspace(workspace_dir)

            self.assertEqual(result["creator_slug"], "luna-fit")

    def test_workspace_without_lessons_section_validates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_summarized_project(temp_dir)

            self.assertEqual(validate_creator_lessons(workspace_dir)["lesson_count"], 0)
            validate_creator_workspace(workspace_dir)


class CreatorLessonCliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "influencer_os", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_cli_writes_creator_lesson_with_evidence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_summarized_project(temp_dir)

            result = self.run_cli(
                "log-learning",
                str(learnings_path(workspace_dir)),
                "hooks",
                LESSON,
                "--date", "2026-07-06",
                "--evidence", SUMMARY_ID, SNAPSHOT_ID,
                "--strength", "single_post_signal",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Logged creator lesson", result.stdout)
            self.assertIn(
                f"(evidence: {SUMMARY_ID}, {SNAPSHOT_ID})",
                learnings_path(workspace_dir).read_text(),
            )

    def test_cli_requires_evidence_for_creator_workspace_learnings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_summarized_project(temp_dir)

            result = self.run_cli(
                "log-learning",
                str(learnings_path(workspace_dir)),
                "hooks",
                LESSON,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("evidence", result.stderr)

    def test_cli_rejects_evidence_flags_outside_creator_workspaces(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            plain_learnings = Path(temp_dir) / "learnings.md"

            result = self.run_cli(
                "log-learning",
                str(plain_learnings),
                "wrap-up",
                "An OS lesson.",
                "--evidence", "ppr_anything",
                "--strength", "weak_signal",
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("creator", result.stderr.lower())
            self.assertFalse(plain_learnings.exists())

    def test_cli_rejects_dangling_evidence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_summarized_project(temp_dir)

            result = self.run_cli(
                "log-learning",
                str(learnings_path(workspace_dir)),
                "hooks",
                LESSON,
                "--evidence", "ppr_ghost",
                "--strength", "weak_signal",
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("ppr_ghost", result.stderr)


class EvidenceStrengthEnumDriftTests(unittest.TestCase):
    def test_strengths_match_performance_summary_schema_enum(self):
        # The learnings strength markers are a code copy of the schema's
        # distilled_lessons vocabulary; pin them together (enum-pin rule).
        schema = json.loads(
            (ROOT / "schemas" / "performance-summary.schema.json").read_text()
        )
        schema_enum = schema["properties"]["distilled_lessons"]["items"][
            "properties"
        ]["evidence_strength"]["enum"]
        self.assertEqual(list(EVIDENCE_STRENGTHS), schema_enum)


if __name__ == "__main__":
    unittest.main()
