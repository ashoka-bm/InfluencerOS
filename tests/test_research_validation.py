import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from influencer_os.research import (
    parse_frontmatter,
    validate_findings_file,
    validate_jsonl_file,
    validate_queue,
    validate_research,
)
from influencer_os.validation import ValidationError


ROOT = Path(__file__).resolve().parents[1]

RUN_ID = "research_run_luna_fit_2026_07_03_001"
ENTRY_ID = "idea_queue_entry_luna_fit_001"


def load_example(name):
    return json.loads((ROOT / "examples" / f"{name}.example.json").read_text())


def frontmatter_block(data):
    lines = ["---"]
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            lines.extend(f"  - {item}" for item in value)
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


def scaffold_research_workspace(temp_dir):
    workspace_dir = Path(temp_dir) / "luna-fit"
    research = workspace_dir / "research"

    write_json(workspace_dir / "content-schedule.json", load_example("creator-content-schedule"))

    run_dir = research / "runs" / RUN_ID
    write_json(run_dir / "research-run.json", load_example("research-run"))
    write_jsonl(run_dir / "evidence.jsonl", [load_example("research-evidence")])
    write_jsonl(run_dir / "metric-snapshots.jsonl", [load_example("metric-snapshot")])

    findings_path = research / "findings.md"
    findings_path.parent.mkdir(parents=True, exist_ok=True)
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
    write_json(
        research / "idea-queue" / "entries" / f"{ENTRY_ID}.json",
        load_example("idea-queue-entry"),
    )
    write_json(
        research / "idea-promotions" / "idea_promotion_luna_fit_001.json",
        load_example("idea-promotion"),
    )

    write_json(workspace_dir / "boards" / "content-board.json", load_example("content-board"))
    write_jsonl(workspace_dir / "system" / "project-warnings.jsonl", [load_example("project-warning")])
    write_jsonl(workspace_dir / "system" / "creator-events.jsonl", [load_example("system-event")])

    return workspace_dir


class ResearchStateValidationTests(unittest.TestCase):
    def test_full_research_workspace_validates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)

            result = validate_research(workspace_dir)
            checked = set(result["checked_paths"])
            self.assertIn("content-schedule.json", checked)
            self.assertIn("research/findings.md", checked)
            self.assertIn(f"research/runs/{RUN_ID}/evidence.jsonl", checked)
            self.assertIn("boards/content-board.json", checked)

    def test_invalid_jsonl_line_reports_line_number(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            evidence_path = workspace_dir / "research" / "runs" / RUN_ID / "evidence.jsonl"
            bad_record = load_example("research-evidence")
            bad_record["platform"] = "myspace"
            with evidence_path.open("a") as handle:
                handle.write(json.dumps(bad_record) + "\n")

            with self.assertRaises(ValidationError) as ctx:
                validate_jsonl_file("research-evidence", evidence_path)
            self.assertIn(":2:", str(ctx.exception))

    def test_findings_body_over_char_limit_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            findings_path = workspace_dir / "research" / "findings.md"
            frontmatter = load_example("research-findings")
            frontmatter["summary_char_limit"] = 10
            findings_path.write_text(
                frontmatter_block(frontmatter) + "This body is longer than ten characters.\n"
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_findings_file(findings_path)
            self.assertIn("summary_char_limit", str(ctx.exception))

    def test_run_folder_without_manifest_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            (workspace_dir / "research" / "runs" / RUN_ID / "research-run.json").unlink()

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("research-run.json", str(ctx.exception))

    def test_nested_frontmatter_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            nested = Path(temp_dir) / "nested.md"
            nested.write_text("---\nouter:\n  inner: value\n---\nbody\n")

            with self.assertRaises(ValidationError) as ctx:
                parse_frontmatter(nested)
            self.assertIn("nested", str(ctx.exception))


class IdeaQueueValidationTests(unittest.TestCase):
    def test_consistent_queue_validates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)

            result = validate_queue(workspace_dir)
            self.assertEqual(result["entry_count"], 1)

    def test_manifest_naming_a_missing_entry_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            (workspace_dir / "research" / "idea-queue" / "entries" / f"{ENTRY_ID}.json").unlink()

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            self.assertIn(ENTRY_ID, str(ctx.exception))

    def test_manifest_status_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            queue_path = workspace_dir / "research" / "idea-queue" / "queue.json"
            manifest = json.loads(queue_path.read_text())
            manifest["entry_refs"][0]["status"] = "new"
            write_json(queue_path, manifest)

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            self.assertIn("does not match entry file status", str(ctx.exception))

    def test_dangling_evidence_ref_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            entry_path = workspace_dir / "research" / "idea-queue" / "entries" / f"{ENTRY_ID}.json"
            entry = json.loads(entry_path.read_text())
            entry["evidence_refs"][0]["evidence_id"] = "evidence_luna_fit_missing"
            write_json(entry_path, entry)

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            self.assertIn("evidence_luna_fit_missing", str(ctx.exception))

    def test_entry_filename_must_match_entry_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            entries_dir = workspace_dir / "research" / "idea-queue" / "entries"
            (entries_dir / f"{ENTRY_ID}.json").rename(entries_dir / "wrong-name.json")

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            self.assertIn("filename does not match", str(ctx.exception))


class ResearchCliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "influencer_os", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_validate_research_and_queue_commands(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)

            research_result = self.run_cli("validate", "research", str(workspace_dir))
            self.assertEqual(research_result.returncode, 0, research_result.stderr)
            self.assertIn("Validated research state", research_result.stdout)

            queue_result = self.run_cli("validate", "queue", str(workspace_dir))
            self.assertEqual(queue_result.returncode, 0, queue_result.stderr)
            self.assertIn("Checked 1 queue entries", queue_result.stdout)


if __name__ == "__main__":
    unittest.main()
