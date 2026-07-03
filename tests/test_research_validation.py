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
    validate_promotion_gate,
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

    # The promotion and queue entry cite this pack; the gate resolves it.
    write_json(
        research / "video-understanding-packs" / "video_research_luna_fit_001.json",
        load_example("video-understanding-pack"),
    )

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

    def test_run_folder_name_must_match_run_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            runs_dir = workspace_dir / "research" / "runs"
            (runs_dir / RUN_ID).rename(runs_dir / "wrong-run-folder-name")

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("does not match research_run_id", str(ctx.exception))

    def test_malformed_jsonl_line_reports_file_and_line(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            evidence_path = workspace_dir / "research" / "runs" / RUN_ID / "evidence.jsonl"
            with evidence_path.open("a") as handle:
                handle.write("{not json\n")

            with self.assertRaises(ValidationError) as ctx:
                validate_jsonl_file("research-evidence", evidence_path)
            message = str(ctx.exception)
            self.assertIn("evidence.jsonl:2:", message)
            self.assertIn("invalid JSON", message)

    def test_jsonl_line_separator_inside_string_validates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            evidence_path = workspace_dir / "research" / "runs" / RUN_ID / "evidence.jsonl"
            record = load_example("research-evidence")
            # Raw U+2028 is legal inside a JSON string; splitlines() would
            # break the line there and corrupt the record.
            record["source_summary"] = "Reset montage with lunch-break framing."
            evidence_path.write_text(json.dumps(record, ensure_ascii=False) + "\n")

            records = validate_jsonl_file("research-evidence", evidence_path)
            self.assertEqual(len(records), 1)

    def test_invalid_stable_finding_frontmatter_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            stable_path = (
                workspace_dir / "research" / "stable-findings" / "stable_finding_luna_fit_001.md"
            )
            frontmatter = load_example("stable-finding")
            del frontmatter["creator_profile_id"]
            stable_path.write_text(frontmatter_block(frontmatter) + "\nBody.\n")

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("stable_finding_luna_fit_001.md", str(ctx.exception))

    def test_project_warning_with_unpaired_promotion_ids_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            warning = load_example("project-warning")
            del warning["idea_promotion_id"]
            write_jsonl(workspace_dir / "system" / "project-warnings.jsonl", [warning])

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("project-warnings.jsonl:1:", message)
            self.assertIn("both project_id and idea_promotion_id", message)

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

    def test_status_counts_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            queue_path = workspace_dir / "research" / "idea-queue" / "queue.json"
            manifest = json.loads(queue_path.read_text())
            manifest["status_counts"] = {"new": 99}
            write_json(queue_path, manifest)

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            self.assertIn("status_counts", str(ctx.exception))

    def test_status_counts_omitting_a_present_status_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            queue_path = workspace_dir / "research" / "idea-queue" / "queue.json"
            manifest = json.loads(queue_path.read_text())
            manifest["status_counts"] = {}
            write_json(queue_path, manifest)

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            self.assertIn("omit statuses present in the queue", str(ctx.exception))

    def test_dangling_video_pack_ref_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            pack_path = (
                workspace_dir / "research" / "video-understanding-packs"
                / "video_research_luna_fit_001.json"
            )
            pack_path.unlink()

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            self.assertIn("video_research_luna_fit_001", str(ctx.exception))

    def test_malformed_run_jsonl_reports_file_and_line(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            evidence_path = workspace_dir / "research" / "runs" / RUN_ID / "evidence.jsonl"
            with evidence_path.open("a") as handle:
                handle.write("{not json\n")

            # validate_queue reaches the malformed line through the raw id
            # scan, which must still name the file and file line.
            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("evidence.jsonl:2:", message)
            self.assertIn("invalid JSON", message)


class PromotionGateTests(unittest.TestCase):
    def test_resolvable_promotion_produces_no_warnings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)

            result = validate_research(workspace_dir)
            self.assertEqual(result["warnings"], [])
            self.assertIn(
                "research/idea-promotions/idea_promotion_luna_fit_001.json",
                result["checked_paths"],
            )

    def test_promotion_without_real_queue_entry_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            (workspace_dir / "research" / "idea-queue" / "entries" / f"{ENTRY_ID}.json").unlink()

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("does not point to a real idea queue entry", str(ctx.exception))

    def test_unresolved_evidence_warns_for_human_approved_promotion(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            (workspace_dir / "research" / "runs" / RUN_ID / "evidence.jsonl").unlink()

            result = validate_research(workspace_dir)
            self.assertEqual(len(result["warnings"]), 1)
            self.assertIn("unresolved evidence refs", result["warnings"][0])
            self.assertIn("human-approved", result["warnings"][0])

    def test_unresolved_video_pack_warns_for_human_approved_promotion(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            (
                workspace_dir / "research" / "video-understanding-packs"
                / "video_research_luna_fit_001.json"
            ).unlink()
            # Keep the queue entry resolvable so only the promotion gate trips:
            # the entry's own pack ref would fail validate_queue, not this path.
            entry_path = (
                workspace_dir / "research" / "idea-queue" / "entries" / f"{ENTRY_ID}.json"
            )
            entry = json.loads(entry_path.read_text())
            entry["evidence_refs"][0].pop("video_understanding_pack_ids", None)
            write_json(entry_path, entry)

            result = validate_research(workspace_dir)
            self.assertEqual(len(result["warnings"]), 1)
            self.assertIn("video_research_luna_fit_001", result["warnings"][0])
            self.assertIn("human-approved", result["warnings"][0])

    def test_unresolved_evidence_fails_for_automated_promotion(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            (workspace_dir / "research" / "runs" / RUN_ID / "evidence.jsonl").unlink()
            promotion = load_example("idea-promotion")
            # Future automated promotion paths never get the human benefit of
            # the doubt; simulate one past the schema's v1 enum.
            promotion["approved_by"] = "automation"

            with self.assertRaises(ValidationError) as ctx:
                validate_promotion_gate(workspace_dir, promotion)
            self.assertIn("unresolved evidence refs", str(ctx.exception))


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
