import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from influencer_os.memory import (
    MEMORY_BYTE_CAP,
    append_skill_learning,
    write_memory_fact,
)
from influencer_os.validation import ValidationError


ROOT = Path(__file__).resolve().parents[1]

MEMORY_FIXTURE = """# Working Memory

## Active Threads

- Existing thread.

## Decisions

## Blockers
"""

LEARNINGS_FIXTURE = """# InfluencerOS Process Learnings

## General

- Existing general lesson.

## Individual Skills

### influencer-os

- Pending repeated feedback.
"""


class MemoryWriteTests(unittest.TestCase):
    def make_memory_file(self, content=MEMORY_FIXTURE):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", temp_dir], check=False))
        memory_path = Path(temp_dir) / "MEMORY.md"
        memory_path.write_text(content)
        return memory_path

    def test_write_appends_fact_under_section(self):
        memory_path = self.make_memory_file()

        result = write_memory_fact(memory_path, "New durable fact.", section="Active Threads")

        self.assertEqual(result["status"], "written")
        content = memory_path.read_text()
        active_threads = content.split("## Active Threads")[1].split("## Decisions")[0]
        self.assertIn("- New durable fact.", active_threads)

    def test_write_dedupes_existing_fact(self):
        memory_path = self.make_memory_file()
        write_memory_fact(memory_path, "New durable fact.")
        before = memory_path.read_text()

        result = write_memory_fact(memory_path, "New durable fact.")

        self.assertEqual(result["status"], "duplicate")
        self.assertEqual(memory_path.read_text(), before)

    def test_write_rejects_unknown_section(self):
        memory_path = self.make_memory_file()

        with self.assertRaises(ValidationError):
            write_memory_fact(memory_path, "A fact.", section="Nonexistent Section")

    def test_write_refuses_fact_past_byte_cap(self):
        padding = "- " + "x" * (MEMORY_BYTE_CAP - len(MEMORY_FIXTURE) - 10) + "\n"
        memory_path = self.make_memory_file(MEMORY_FIXTURE + padding)
        before = memory_path.read_text()

        with self.assertRaises(ValidationError):
            write_memory_fact(memory_path, "This fact would push the file over the cap.")

        self.assertEqual(memory_path.read_text(), before)

    def test_write_requires_existing_file(self):
        with self.assertRaises(FileNotFoundError):
            write_memory_fact(Path(tempfile.mkdtemp()) / "MEMORY.md", "A fact.")


class SkillLearningTests(unittest.TestCase):
    def make_learnings_file(self, content=LEARNINGS_FIXTURE):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", temp_dir], check=False))
        learnings_path = Path(temp_dir) / "learnings.md"
        if content is not None:
            learnings_path.write_text(content)
        return learnings_path

    def test_append_adds_dated_entry_under_skill_section(self):
        learnings_path = self.make_learnings_file()

        result = append_skill_learning(
            learnings_path, "influencer-os", "Cite evidence in every idea.", "2026-07-03"
        )

        self.assertEqual(result["status"], "written")
        content = learnings_path.read_text()
        skill_section = content.split("### influencer-os")[1]
        self.assertIn("- 2026-07-03: Cite evidence in every idea.", skill_section)

    def test_append_creates_missing_skill_section(self):
        learnings_path = self.make_learnings_file()

        append_skill_learning(learnings_path, "wrap-up", "First wrap-up lesson.", "2026-07-03")

        content = learnings_path.read_text()
        self.assertIn("### wrap-up", content)
        skill_section = content.split("### wrap-up")[1]
        self.assertIn("- 2026-07-03: First wrap-up lesson.", skill_section)

    def test_append_creates_missing_file_with_scaffold(self):
        learnings_path = self.make_learnings_file(content=None)

        append_skill_learning(learnings_path, "wrap-up", "First lesson.", "2026-07-03")

        content = learnings_path.read_text()
        self.assertIn("## Individual Skills", content)
        self.assertIn("- 2026-07-03: First lesson.", content)

    def test_append_dedupes_same_lesson(self):
        learnings_path = self.make_learnings_file()
        append_skill_learning(learnings_path, "influencer-os", "Same lesson.", "2026-07-03")
        before = learnings_path.read_text()

        result = append_skill_learning(learnings_path, "influencer-os", "Same lesson.", "2026-07-04")

        self.assertEqual(result["status"], "duplicate")
        self.assertEqual(learnings_path.read_text(), before)

    def test_append_rejects_bad_date(self):
        learnings_path = self.make_learnings_file()

        with self.assertRaises(ValidationError):
            append_skill_learning(learnings_path, "wrap-up", "Lesson.", "July 3rd")


class MemoryCliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "influencer_os", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_memory_write_command_saves_fact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "MEMORY.md"
            memory_path.write_text(MEMORY_FIXTURE)

            result = self.run_cli("memory-write", str(memory_path), "A CLI fact.")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Saved memory fact", result.stdout)
            self.assertIn("- A CLI fact.", memory_path.read_text())

    def test_memory_write_command_refuses_over_cap(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "MEMORY.md"
            padding = "- " + "x" * MEMORY_BYTE_CAP + "\n"
            memory_path.write_text(MEMORY_FIXTURE + padding)

            result = self.run_cli("memory-write", str(memory_path), "Over-cap fact.")

            self.assertEqual(result.returncode, 1)
            self.assertIn("cap", result.stderr)

    def test_log_learning_command_appends_entry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            learnings_path = Path(temp_dir) / "learnings.md"
            learnings_path.write_text(LEARNINGS_FIXTURE)

            result = self.run_cli(
                "log-learning",
                str(learnings_path),
                "influencer-os",
                "CLI-logged lesson.",
                "--date",
                "2026-07-03",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Logged learning", result.stdout)
            self.assertIn("- 2026-07-03: CLI-logged lesson.", learnings_path.read_text())


if __name__ == "__main__":
    unittest.main()
