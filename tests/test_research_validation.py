import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from influencer_os.research import (
    parse_frontmatter,
    validate_findings_file,
    validate_promotion_gate,
    validate_queue,
    validate_research,
)
from influencer_os.validation import ValidationError, validate_jsonl_file


ROOT = Path(__file__).resolve().parents[1]

RUN_ID = "research_run_luna_fit_2026_07_03_001"
RUN_ID_2 = "research_run_luna_fit_2026_07_03_002"
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


def background_yield(idx):
    # A schema-valid low-yield source-yield record on an ad-hoc key, so it does
    # not feed the source_intel_* yield_stats reconciliation.
    record = load_example("research-source-yield")
    record["research_source_yield_id"] = f"research_source_yield_luna_fit_bg_{idx}"
    record["source_key"] = f"ad_hoc_thin_source_{idx}"
    record["source_kind"] = "search_result"
    record["outcome"] = "background_only"
    record["evidence_ids"] = []
    record["metric_snapshot_ids"] = []
    record["finding_ids"] = []
    record["idea_queue_entry_ids"] = []
    record["engagement_basis"] = {
        "visible_metric_signal": "weak",
        "cross_platform_validation": False,
        "creator_fit": "low",
        "notes": "Background context only; no promotable signal.",
    }
    record["recommended_intelligence_action"] = "none"
    record.pop("source_plan_id", None)
    return record


def scaffold_research_workspace(temp_dir):
    workspace_dir = Path(temp_dir) / "luna-fit"
    research = workspace_dir / "research"

    # Research validation pins every record to the owning workspace creator.
    write_json(workspace_dir / "creator-workspace.json", load_example("creator-workspace"))

    write_json(workspace_dir / "content-schedule.json", load_example("creator-content-schedule"))

    run_dir = research / "runs" / RUN_ID
    write_json(run_dir / "research-run.json", load_example("research-run"))
    write_json(run_dir / "search-plan.json", load_example("research-search-plan"))
    write_jsonl(run_dir / "source-yield.jsonl", [load_example("research-source-yield")])
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

    # The example warning targets promoted work, and warning targets must
    # exist, so the scaffold carries the example project.
    project = load_example("project")
    write_json(
        workspace_dir / "projects" / project["project_id"] / "project.json", project
    )

    return workspace_dir


def make_research_phase_only(workspace_dir):
    """Keep the run, findings, and queue candidate without production state."""
    shutil.rmtree(workspace_dir / "research" / "idea-promotions")
    shutil.rmtree(workspace_dir / "projects")
    shutil.rmtree(workspace_dir / "boards")
    write_jsonl(workspace_dir / "system" / "project-warnings.jsonl", [])

    entry_path = (
        workspace_dir / "research" / "idea-queue" / "entries" / f"{ENTRY_ID}.json"
    )
    entry = json.loads(entry_path.read_text())
    entry["status"] = "shortlisted"
    entry.pop("linked_idea_promotion_ids", None)
    entry.pop("linked_project_ids", None)
    write_json(entry_path, entry)

    queue_path = workspace_dir / "research" / "idea-queue" / "queue.json"
    queue = json.loads(queue_path.read_text())
    queue["entry_refs"] = [
        {"idea_queue_entry_id": ENTRY_ID, "status": "shortlisted"}
    ]
    queue["status_counts"] = {"shortlisted": 1}
    write_json(queue_path, queue)

    return workspace_dir


class ResearchStateValidationTests(unittest.TestCase):
    def test_full_research_workspace_validates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)

            result = validate_research(workspace_dir)
            checked = set(result["checked_paths"])
            self.assertIn("content-schedule.json", checked)
            self.assertIn("research/findings.md", checked)
            self.assertIn(f"research/runs/{RUN_ID}/search-plan.json", checked)
            self.assertIn(f"research/runs/{RUN_ID}/source-yield.jsonl", checked)
            self.assertIn(f"research/runs/{RUN_ID}/evidence.jsonl", checked)
            self.assertIn("boards/content-board.json", checked)

    def test_completed_run_without_search_plan_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            (workspace_dir / "research" / "runs" / RUN_ID / "search-plan.json").unlink()

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("search-plan.json", str(ctx.exception))

    def test_completed_run_without_source_yield_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            (workspace_dir / "research" / "runs" / RUN_ID / "source-yield.jsonl").unlink()

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("source-yield.jsonl", str(ctx.exception))

    def test_search_plan_may_include_attempted_platform_not_on_run(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)

            validate_research(workspace_dir)

    def test_research_run_platform_must_be_planned(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            run_path = workspace_dir / "research" / "runs" / RUN_ID / "research-run.json"
            run = json.loads(run_path.read_text())
            run["platforms"] = ["linkedin"]
            write_json(run_path, run)

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("not present in search-plan.json platforms", str(ctx.exception))

    def test_search_plan_run_id_must_match_containing_run(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            plan_path = workspace_dir / "research" / "runs" / RUN_ID / "search-plan.json"
            plan = json.loads(plan_path.read_text())
            plan["research_run_id"] = RUN_ID_2
            write_json(plan_path, plan)

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("search-plan.json", str(ctx.exception))
            self.assertIn("research_run_id", str(ctx.exception))

    def test_search_plan_creator_must_match_workspace_creator(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            plan_path = workspace_dir / "research" / "runs" / RUN_ID / "search-plan.json"
            plan = json.loads(plan_path.read_text())
            plan["creator_profile_id"] = "creator_other"
            write_json(plan_path, plan)

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("search-plan.json", str(ctx.exception))
            self.assertIn("creator_profile_id", str(ctx.exception))

    def test_source_yield_platform_must_be_planned(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            yield_path = workspace_dir / "research" / "runs" / RUN_ID / "source-yield.jsonl"
            record = load_example("research-source-yield")
            record["platform"] = "linkedin"
            write_jsonl(yield_path, [record])

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("source-yield.jsonl", str(ctx.exception))
            self.assertIn("search-plan.json platforms", str(ctx.exception))

    def test_source_yield_evidence_refs_must_resolve_to_same_run(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            yield_path = workspace_dir / "research" / "runs" / RUN_ID / "source-yield.jsonl"
            record = load_example("research-source-yield")
            record["evidence_ids"] = ["evidence_luna_fit_missing"]
            write_jsonl(yield_path, [record])

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("evidence_luna_fit_missing", str(ctx.exception))

    def test_source_yield_stats_must_match_sources_intelligence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            sources_path = workspace_dir / "research" / "intelligence" / "sources.json"
            sources = json.loads(sources_path.read_text())
            sources["items"][0]["yield_stats"]["checked_count"] = 0
            write_json(sources_path, sources)

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("yield_stats.checked_count", str(ctx.exception))

    def test_source_yield_stats_cannot_be_fabricated_without_records(self):
        # A saved source that no source-yield record ever produced must not be
        # able to advertise a non-zero usefulness history. The reconciliation
        # runs sources->records, not only records->sources, so an item with
        # zero backing records must carry all-zero counts.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            sources_path = workspace_dir / "research" / "intelligence" / "sources.json"
            sources = json.loads(sources_path.read_text())
            fabricated = json.loads(json.dumps(sources["items"][0]))
            fabricated["source_intel_id"] = "source_intel_luna_fit_999"
            fabricated["yield_stats"] = {
                "checked_count": 999,
                "promoted_to_evidence_count": 999,
                "background_use_count": 0,
                "low_yield_count": 0,
                "usefulness_basis": "Invented history with no backing records.",
            }
            sources["items"].append(fabricated)
            write_json(sources_path, sources)

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("source_intel_luna_fit_999", str(ctx.exception))
            self.assertIn("yield_stats", str(ctx.exception))

    def test_duplicate_source_yield_id_within_run_fails(self):
        # source-yield ids are first-class refs; a duplicate makes every
        # reference ambiguous and double-counts into yield_stats, exactly like
        # the guard already enforced for evidence and metric snapshots.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            yield_path = workspace_dir / "research" / "runs" / RUN_ID / "source-yield.jsonl"
            record = load_example("research-source-yield")
            write_jsonl(yield_path, [record, json.loads(json.dumps(record))])

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("duplicate research_source_yield_id", str(ctx.exception))

    def test_source_yield_cannot_use_gated_access_method(self):
        # The yield ledger records what the run actually did; a gated method
        # here attests the run executed something the slice forbids, so the
        # prohibition must be enforced on the yield, not only on the plan.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            yield_path = workspace_dir / "research" / "runs" / RUN_ID / "source-yield.jsonl"
            record = load_example("research-source-yield")
            record["access_method"] = "logged_in_browser"
            write_jsonl(yield_path, [record])

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("gated access method", str(ctx.exception))

    def test_source_yield_allows_standing_approved_connector(self):
        # An exact ADR 0022 connector using its api_backed method is permitted.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            yield_path = workspace_dir / "research" / "runs" / RUN_ID / "source-yield.jsonl"
            record = load_example("research-source-yield")
            record["access_method"] = "api_backed"
            record["adapter_id"] = "reddit_api_or_search"
            write_jsonl(yield_path, [record])

            validate_research(workspace_dir)  # must not raise

    def test_source_yield_rejects_unapproved_api_backed_adapter(self):
        # instagram_logged_in_api is api_backed but not standing-approved, so a
        # yield record attesting the run used it must fail.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            yield_path = workspace_dir / "research" / "runs" / RUN_ID / "source-yield.jsonl"
            record = load_example("research-source-yield")
            record["access_method"] = "api_backed"
            record["adapter_id"] = "instagram_logged_in_api"
            write_jsonl(yield_path, [record])

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("gated access method", str(ctx.exception))

    def test_source_yield_allows_youtube_data_api_connector(self):
        # ADR 0027: youtube_data_api is a standing-approved research connector.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            run_dir = workspace_dir / "research" / "runs" / RUN_ID
            plan = json.loads((run_dir / "search-plan.json").read_text())
            plan["platforms"].append("youtube")
            write_json(run_dir / "search-plan.json", plan)
            yield_path = run_dir / "source-yield.jsonl"
            record = load_example("research-source-yield")
            record["platform"] = "youtube"
            record["access_method"] = "api_backed"
            record["adapter_id"] = "youtube_data_api"
            write_jsonl(yield_path, [record])

            validate_research(workspace_dir)

    def test_source_yield_rejects_standing_approved_adapter_with_wrong_method(self):
        # Standing approval is pinned per (adapter_id, method): reddit_api_or_search
        # is approved only with api_backed, so pairing it with scraping_api fails.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            yield_path = workspace_dir / "research" / "runs" / RUN_ID / "source-yield.jsonl"
            record = load_example("research-source-yield")
            record["access_method"] = "scraping_api"
            record["adapter_id"] = "reddit_api_or_search"
            write_jsonl(yield_path, [record])

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("gated access method", str(ctx.exception))

    def test_is_standing_approved_adapter_enforces_expected_method(self):
        from influencer_os.validation import is_standing_approved_adapter
        self.assertTrue(is_standing_approved_adapter("reddit_api_or_search", "api_backed"))
        self.assertTrue(is_standing_approved_adapter("firecrawl_public_web", "scraping_api"))
        # Right adapter id, wrong method -> not standing approved.
        self.assertFalse(is_standing_approved_adapter("reddit_api_or_search", "scraping_api"))
        self.assertFalse(is_standing_approved_adapter("firecrawl_public_web", "api_backed"))
        # ADR 0027 approved youtube_data_api, pinned to api_backed only.
        self.assertTrue(is_standing_approved_adapter("youtube_data_api", "api_backed"))
        self.assertFalse(is_standing_approved_adapter("youtube_data_api", "scraping_api"))
        # Unapproved adapter id.
        self.assertFalse(is_standing_approved_adapter("instagram_logged_in_api", "api_backed"))

    def test_thin_evidence_material_run_warns(self):
        # A run that declares a material update but grounds it in a low share of
        # promoted-to-evidence sources gets an advisory (non-failing) WARN.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            run_dir = workspace_dir / "research" / "runs" / RUN_ID
            manifest_path = run_dir / "research-run.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["material_update"] = True
            write_json(manifest_path, manifest)
            promoted = load_example("research-source-yield")
            write_jsonl(
                run_dir / "source-yield.jsonl",
                [promoted, background_yield(1), background_yield(2), background_yield(3)],
            )

            result = validate_research(workspace_dir)
            self.assertTrue(
                any("thin-evidence" in warning for warning in result["warnings"]),
                result["warnings"],
            )

    def test_thin_evidence_warns_on_material_outputs_despite_flag(self):
        # A stale material_update=false must not suppress the warning when the
        # run's declared outputs (findings/ideas) show it was a material run.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            run_dir = workspace_dir / "research" / "runs" / RUN_ID
            manifest_path = run_dir / "research-run.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["material_update"] = False
            # outputs.finding_ids and idea_queue_entry_ids stay populated.
            write_json(manifest_path, manifest)
            promoted = load_example("research-source-yield")
            write_jsonl(
                run_dir / "source-yield.jsonl",
                [promoted, background_yield(1), background_yield(2), background_yield(3)],
            )

            result = validate_research(workspace_dir)
            self.assertTrue(
                any("thin-evidence" in warning for warning in result["warnings"]),
                result["warnings"],
            )

    def test_material_run_with_enough_evidence_does_not_warn(self):
        # Same size run, but a healthy promotion rate must not trip the gate.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            run_dir = workspace_dir / "research" / "runs" / RUN_ID
            manifest_path = run_dir / "research-run.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["material_update"] = True
            write_json(manifest_path, manifest)
            promoted = load_example("research-source-yield")
            promoted_2 = load_example("research-source-yield")
            promoted_2["research_source_yield_id"] = "research_source_yield_luna_fit_p2"
            promoted_2["source_key"] = "ad_hoc_second_promoted"
            promoted_2["source_kind"] = "search_result"
            write_jsonl(
                run_dir / "source-yield.jsonl",
                [promoted, promoted_2, background_yield(1)],
            )

            result = validate_research(workspace_dir)
            self.assertFalse(
                any("thin-evidence" in warning for warning in result["warnings"]),
                result["warnings"],
            )

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

    def test_warning_targeting_missing_queue_entry_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            warning = load_example("project-warning")
            warning.pop("project_id")
            warning.pop("idea_promotion_id")
            warning["idea_queue_entry_id"] = "idea_queue_entry_luna_fit_ghost"
            write_jsonl(
                workspace_dir / "system" / "project-warnings.jsonl", [warning]
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("idea_queue_entry_luna_fit_ghost", message)
            self.assertIn("no entry file", message)

    def test_warning_targeting_missing_project_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            warning = load_example("project-warning")
            warning["project_id"] = "project_luna_ghost"
            write_jsonl(
                workspace_dir / "system" / "project-warnings.jsonl", [warning]
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("project_luna_ghost", message)
            self.assertIn("no project record", message)

    def test_warning_entry_mismatching_promotion_chain_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            # A second real entry: the warning tuple names it while the
            # promotion was locked from the first entry.
            entry = load_example("idea-queue-entry")
            entry["idea_queue_entry_id"] = "idea_queue_entry_luna_fit_002"
            write_json(
                workspace_dir / "research" / "idea-queue" / "entries"
                / "idea_queue_entry_luna_fit_002.json",
                entry,
            )
            warning = load_example("project-warning")
            warning["idea_queue_entry_id"] = "idea_queue_entry_luna_fit_002"
            write_jsonl(
                workspace_dir / "system" / "project-warnings.jsonl", [warning]
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("was promoted from", str(ctx.exception))

    def test_warning_promotion_mismatching_project_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            # A second real promotion of the same entry: the warning pairs it
            # with a project locked to the first promotion.
            promotion = load_example("idea-promotion")
            promotion["idea_promotion_id"] = "idea_promotion_luna_fit_002"
            write_json(
                workspace_dir / "research" / "idea-promotions"
                / "idea_promotion_luna_fit_002.json",
                promotion,
            )
            warning = load_example("project-warning")
            warning["idea_promotion_id"] = "idea_promotion_luna_fit_002"
            write_jsonl(
                workspace_dir / "system" / "project-warnings.jsonl", [warning]
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("locked promotion", str(ctx.exception))

    def test_duplicate_manifest_entry_ref_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            queue_path = workspace_dir / "research" / "idea-queue" / "queue.json"
            manifest = json.loads(queue_path.read_text())
            manifest["entry_refs"].append(dict(manifest["entry_refs"][0]))
            write_json(queue_path, manifest)

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            self.assertIn("more than once", str(ctx.exception))

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


class ResearchPhaseContractTests(unittest.TestCase):
    def test_offline_research_phase_contract_validates_without_promotion(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_research_phase_only(
                scaffold_research_workspace(temp_dir)
            )
            run_dir = workspace_dir / "research" / "runs" / RUN_ID
            promoted = load_example("research-source-yield")
            write_jsonl(
                run_dir / "source-yield.jsonl",
                [promoted, background_yield(1)],
            )

            result = validate_research(workspace_dir)
            checked = set(result["checked_paths"])
            run = json.loads((run_dir / "research-run.json").read_text())
            plan = json.loads((run_dir / "search-plan.json").read_text())
            evidence = validate_jsonl_file("research-evidence", run_dir / "evidence.jsonl")
            metrics = validate_jsonl_file(
                "metric-snapshot", run_dir / "metric-snapshots.jsonl"
            )
            yields = validate_jsonl_file(
                "research-source-yield", run_dir / "source-yield.jsonl"
            )

            self.assertEqual(result["warnings"], [])
            self.assertNotIn(
                "research/idea-promotions/idea_promotion_luna_fit_001.json",
                checked,
            )
            self.assertFalse((workspace_dir / "projects").exists())
            self.assertEqual(run["outputs"]["evidence_ids"], [evidence[0]["evidence_id"]])
            self.assertEqual(
                run["outputs"]["metric_snapshot_ids"],
                [metrics[0]["metric_snapshot_id"]],
            )
            self.assertTrue(
                set(run["platforms"]).issubset(set(plan["platforms"]))
            )
            self.assertTrue(any(y["outcome"] == "promoted_to_evidence" for y in yields))
            self.assertTrue(any(y["outcome"] == "background_only" for y in yields))
            for record in yields:
                if record["outcome"] == "background_only":
                    self.assertEqual(record["evidence_ids"], [])
                    self.assertEqual(record["metric_snapshot_ids"], [])

    def test_manual_research_eval_harness_runs_without_live_connectors(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_research_phase_only(
                scaffold_research_workspace(temp_dir)
            )
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("INFLUENCER_OS_DISABLE_PAID_CONNECTORS=1\n")
            db_path = Path(temp_dir) / "research-eval.sqlite"

            connector_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "list-connectors",
                    "--env-file",
                    str(env_path),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(connector_result.returncode, 0, connector_result.stderr)
            self.assertIn("0/5 available", connector_result.stdout)

            commands = [
                ("validate", "research", str(workspace_dir)),
                ("rebuild-index", str(workspace_dir), "--db", str(db_path)),
                ("prune", str(workspace_dir), "--retention-days", "30"),
            ]
            for command in commands:
                with self.subTest(command=command):
                    result = subprocess.run(
                        [sys.executable, "-m", "influencer_os", *command],
                        cwd=ROOT,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)

            self.assertTrue(db_path.exists())


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


def add_second_run(workspace_dir, evidence_id="evidence_luna_fit_002", metric_id=None):
    """Add a second, self-consistent run so tests can cross run boundaries."""
    run = load_example("research-run")
    run["research_run_id"] = RUN_ID_2
    run["outputs"] = {
        "finding_ids": [],
        "idea_queue_entry_ids": [],
        "evidence_ids": [evidence_id],
        "metric_snapshot_ids": [metric_id] if metric_id else [],
        "research_intelligence_updates": [],
    }
    evidence = load_example("research-evidence")
    evidence["evidence_id"] = evidence_id
    evidence["research_run_id"] = RUN_ID_2
    run_dir = Path(workspace_dir) / "research" / "runs" / RUN_ID_2
    write_json(run_dir / "research-run.json", run)
    plan = load_example("research-search-plan")
    plan["research_search_plan_id"] = "research_search_plan_luna_fit_2026_07_03_002"
    plan["research_run_id"] = RUN_ID_2
    write_json(run_dir / "search-plan.json", plan)
    write_jsonl(run_dir / "evidence.jsonl", [evidence])
    if metric_id:
        metric = load_example("metric-snapshot")
        metric["metric_snapshot_id"] = metric_id
        metric["evidence_id"] = evidence_id
        metric["research_run_id"] = RUN_ID_2
        write_jsonl(run_dir / "metric-snapshots.jsonl", [metric])
    source_yield = load_example("research-source-yield")
    source_yield["research_source_yield_id"] = "research_source_yield_luna_fit_002"
    source_yield["research_run_id"] = RUN_ID_2
    source_yield["source_key"] = "ad_hoc_second_run_source"
    source_yield["source_kind"] = "direct_url"
    source_yield["evidence_ids"] = [evidence_id]
    source_yield["metric_snapshot_ids"] = [metric_id] if metric_id else []
    write_jsonl(run_dir / "source-yield.jsonl", [source_yield])
    return run_dir


def add_public_web_background_run(workspace_dir):
    """Add a public-web evidence run with no metric snapshots."""
    run_id = "research_run_luna_fit_public_web_001"
    evidence_id = "evidence_luna_fit_public_web_001"
    run = load_example("research-run")
    run["research_run_id"] = run_id
    run["platforms"] = ["public_web"]
    run["material_update"] = False
    run["outputs"] = {
        "finding_ids": [],
        "idea_queue_entry_ids": [],
        "evidence_ids": [evidence_id],
        "metric_snapshot_ids": [],
        "research_intelligence_updates": [],
    }
    run_dir = Path(workspace_dir) / "research" / "runs" / run_id
    write_json(run_dir / "research-run.json", run)

    plan = load_example("research-search-plan")
    plan["research_search_plan_id"] = "research_search_plan_luna_fit_public_web_001"
    plan["research_run_id"] = run_id
    plan["platforms"] = ["public_web"]
    for query in plan["planned_queries"]:
        query["platform"] = "public_web"
        query["query"] = "desk stretching institutional guidance"
        query["source_type"] = "ad_hoc"
        query["purpose"] = "Collect background institutional context without social-platform metrics."
        query["expected_signal"] = "Credible public-web background evidence."
        query["term_basis"] = ["hypothesis"]
    for planned_source in plan["planned_sources"]:
        planned_source["platform"] = "public_web"
        planned_source["source_type"] = "direct_url"
        planned_source["url"] = "https://www.mayoclinic.org/healthy-lifestyle/fitness/in-depth/stretching/art-20047931"
        planned_source["reason"] = "Institutional background source for safe stretching context."
        planned_source.pop("source_ref", None)
    for skipped_source in plan["skipped_sources"]:
        skipped_source["platform"] = "public_web"
    write_json(run_dir / "search-plan.json", plan)

    evidence = load_example("research-evidence")
    evidence.update(
        evidence_id=evidence_id,
        research_run_id=run_id,
        platform="public_web",
        platform_content_type="institutional_article",
        source_url="https://www.mayoclinic.org/healthy-lifestyle/fitness/in-depth/stretching/art-20047931",
        source_relationship="farther_field",
        source_summary="Institutional article used as background context.",
        signal_summary="Background stretching guidance, not native social performance evidence.",
        confidence="medium",
        limitations="No native platform metrics are available for this background source.",
    )
    evidence.pop("source_account", None)
    evidence.pop("visible_metrics", None)
    write_jsonl(run_dir / "evidence.jsonl", [evidence])

    source_yield = load_example("research-source-yield")
    source_yield.update(
        research_source_yield_id="research_source_yield_luna_fit_public_web_001",
        research_run_id=run_id,
        source_key="public_web_mayo_stretching",
        source_kind="direct_url",
        platform="public_web",
        adapter_id="manual_public_web",
        access_method="public_web",
        url=evidence["source_url"],
        outcome="promoted_to_evidence",
        yield_reason="Useful background source; no social metric snapshot created.",
        evidence_ids=[evidence_id],
        metric_snapshot_ids=[],
        finding_ids=[],
        idea_queue_entry_ids=[],
        engagement_basis={
            "visible_metric_signal": "none",
            "cross_platform_validation": False,
            "creator_fit": "medium",
            "notes": "No visible social metrics; background context only.",
        },
        recommended_intelligence_action="none",
    )
    source_yield.pop("query_id", None)
    source_yield.pop("source_plan_id", None)
    write_jsonl(run_dir / "source-yield.jsonl", [source_yield])
    return run_dir


class RunScopeConsistencyTests(unittest.TestCase):
    def test_evidence_run_id_must_match_containing_run(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            evidence_path = workspace_dir / "research" / "runs" / RUN_ID / "evidence.jsonl"
            record = load_example("research-evidence")
            record["research_run_id"] = RUN_ID_2
            write_jsonl(evidence_path, [record])

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("does not match the containing run", message)
            self.assertIn("evidence.jsonl:1:", message)

    def test_metric_snapshot_run_id_must_match_containing_run(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            metric_path = (
                workspace_dir / "research" / "runs" / RUN_ID / "metric-snapshots.jsonl"
            )
            record = load_example("metric-snapshot")
            record["research_run_id"] = RUN_ID_2
            write_jsonl(metric_path, [record])

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("does not match the containing run", str(ctx.exception))

    def test_public_web_background_evidence_validates_without_metric_snapshots(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            run_dir = add_public_web_background_run(workspace_dir)

            result = validate_research(workspace_dir)
            checked = set(result["checked_paths"])
            self.assertIn(
                str((run_dir / "evidence.jsonl").relative_to(workspace_dir)),
                checked,
            )
            self.assertIn(
                str((run_dir / "source-yield.jsonl").relative_to(workspace_dir)),
                checked,
            )
            self.assertFalse((run_dir / "metric-snapshots.jsonl").exists())
            source_yield = validate_jsonl_file(
                "research-source-yield", run_dir / "source-yield.jsonl"
            )[0]
            self.assertEqual(source_yield["platform"], "public_web")
            self.assertEqual(source_yield["metric_snapshot_ids"], [])

    def test_run_outputs_omitting_a_jsonl_id_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            run_manifest = workspace_dir / "research" / "runs" / RUN_ID / "research-run.json"
            run = json.loads(run_manifest.read_text())
            run["outputs"]["evidence_ids"] = []
            write_json(run_manifest, run)

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("outputs.evidence_ids", message)
            self.assertIn("evidence_luna_fit_001", message)

    def test_run_outputs_naming_an_absent_id_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            run_manifest = workspace_dir / "research" / "runs" / RUN_ID / "research-run.json"
            run = json.loads(run_manifest.read_text())
            run["outputs"]["evidence_ids"].append("evidence_luna_fit_ghost")
            write_json(run_manifest, run)

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("outputs.evidence_ids", message)
            self.assertIn("evidence_luna_fit_ghost", message)

    def test_run_outputs_reconcile_metric_snapshots(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            run_manifest = workspace_dir / "research" / "runs" / RUN_ID / "research-run.json"
            run = json.loads(run_manifest.read_text())
            run["outputs"]["metric_snapshot_ids"] = []
            write_json(run_manifest, run)

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("outputs.metric_snapshot_ids", message)
            self.assertIn("metric_snapshot_luna_fit_001", message)

    def test_queue_ref_run_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            add_second_run(workspace_dir)
            entry_path = workspace_dir / "research" / "idea-queue" / "entries" / f"{ENTRY_ID}.json"
            entry = json.loads(entry_path.read_text())
            # The evidence lives in RUN_ID; the ref claims RUN_ID_2.
            entry["evidence_refs"][0]["research_run_id"] = RUN_ID_2
            write_json(entry_path, entry)

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("resolves to run", message)
            self.assertIn(RUN_ID_2, message)

    def test_queue_metric_ref_run_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            add_second_run(workspace_dir, metric_id="metric_snapshot_luna_fit_002")
            entry_path = workspace_dir / "research" / "idea-queue" / "entries" / f"{ENTRY_ID}.json"
            entry = json.loads(entry_path.read_text())
            # The ref names RUN_ID, but this metric snapshot lives in RUN_ID_2.
            entry["evidence_refs"][0]["metric_snapshot_ids"].append(
                "metric_snapshot_luna_fit_002"
            )
            write_json(entry_path, entry)

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("metric_snapshot_luna_fit_002", message)
            self.assertIn("resolves to run", message)

    def test_dangling_source_finding_ref_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            entry_path = workspace_dir / "research" / "idea-queue" / "entries" / f"{ENTRY_ID}.json"
            entry = json.loads(entry_path.read_text())
            entry["source_finding_ids"] = ["finding_luna_fit_ghost"]
            write_json(entry_path, entry)

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            self.assertIn("finding_luna_fit_ghost", str(ctx.exception))

    def test_finding_rotated_out_of_rolling_summary_still_resolves(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            # Simulate the char-limit demotion: the finding leaves the rolling
            # summary but stays declared by the run that produced it (and by
            # its stable finding), so queue refs must keep resolving.
            findings_path = workspace_dir / "research" / "findings.md"
            findings = load_example("research-findings")
            findings["finding_ids"] = []
            findings_path.write_text(
                frontmatter_block(findings) + "\nNothing rolling right now.\n"
            )

            validate_queue(workspace_dir)

    def test_promotion_with_dangling_finding_ref_warns_for_human_approved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            promotion_path = (
                workspace_dir / "research" / "idea-promotions"
                / "idea_promotion_luna_fit_001.json"
            )
            promotion = json.loads(promotion_path.read_text())
            promotion["research_finding_ids"] = ["finding_luna_fit_ghost"]
            write_json(promotion_path, promotion)

            result = validate_research(workspace_dir)
            self.assertEqual(len(result["warnings"]), 1)
            self.assertIn("finding_luna_fit_ghost", result["warnings"][0])
            self.assertIn("human-approved", result["warnings"][0])

    def test_promotion_with_dangling_finding_ref_fails_for_automated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            promotion = load_example("idea-promotion")
            promotion["approved_by"] = "automation"
            promotion["research_finding_ids"] = ["finding_luna_fit_ghost"]

            with self.assertRaises(ValidationError) as ctx:
                validate_promotion_gate(workspace_dir, promotion)
            self.assertIn("finding_luna_fit_ghost", str(ctx.exception))

    def test_duplicate_evidence_id_across_runs_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            add_second_run(workspace_dir, evidence_id="evidence_luna_fit_001")

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            self.assertIn("more than one run", str(ctx.exception))

    def test_promotion_ref_run_mismatch_warns_for_human_approved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            add_second_run(workspace_dir)
            promotion_path = (
                workspace_dir / "research" / "idea-promotions"
                / "idea_promotion_luna_fit_001.json"
            )
            promotion = json.loads(promotion_path.read_text())
            promotion["evidence_refs"][0]["research_run_id"] = RUN_ID_2
            write_json(promotion_path, promotion)

            result = validate_research(workspace_dir)
            self.assertEqual(len(result["warnings"]), 1)
            self.assertIn("resolves to run", result["warnings"][0])
            self.assertIn("human-approved", result["warnings"][0])

    def test_promotion_ref_run_mismatch_fails_for_automated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            promotion = load_example("idea-promotion")
            promotion["approved_by"] = "automation"
            promotion["evidence_refs"][0]["research_run_id"] = RUN_ID_2

            with self.assertRaises(ValidationError) as ctx:
                validate_promotion_gate(workspace_dir, promotion)
            self.assertIn("unresolved evidence refs", str(ctx.exception))


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
            # Clear the warning that also targets the entry, so the promotion
            # gate failure is what fires.
            (workspace_dir / "system" / "project-warnings.jsonl").write_text("")
            (workspace_dir / "research" / "idea-queue" / "entries" / f"{ENTRY_ID}.json").unlink()

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("does not point to a real idea queue entry", str(ctx.exception))

    def test_unresolved_evidence_warns_for_human_approved_promotion(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            # Deleting evidence.jsonl outright would now hard-fail outputs
            # reconciliation before the gate runs; the human-approved warning
            # path is for refs that do not resolve in an otherwise valid
            # workspace.
            promotion_path = (
                workspace_dir / "research" / "idea-promotions"
                / "idea_promotion_luna_fit_001.json"
            )
            promotion = json.loads(promotion_path.read_text())
            promotion["evidence_refs"][0]["evidence_id"] = "evidence_luna_fit_missing"
            write_json(promotion_path, promotion)

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

    def test_promotion_approving_no_supported_format_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            promotion = load_example("idea-promotion")
            # Simulate a future format past the schema, like the automation case.
            promotion["approved_formats"] = ["format_podcast"]

            with self.assertRaises(ValidationError) as ctx:
                validate_promotion_gate(workspace_dir, promotion)
            self.assertIn("no production-supported format", str(ctx.exception))

    def test_text_formats_are_production_supported(self):
        for format_id, platform in (
            ("format_article", "substack"),
            ("format_thread", "x"),
        ):
            with self.subTest(format_id=format_id):
                with tempfile.TemporaryDirectory() as temp_dir:
                    workspace_dir = scaffold_research_workspace(temp_dir)
                    promotion = load_example("idea-promotion")
                    promotion["approved_formats"] = [format_id]
                    promotion["approved_platforms"] = [platform]

                    result = validate_promotion_gate(workspace_dir, promotion)

                    self.assertEqual(result, [])

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


class CreatorScopeTests(unittest.TestCase):
    def test_missing_workspace_manifest_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            (workspace_dir / "creator-workspace.json").unlink()

            with self.assertRaises(FileNotFoundError):
                validate_research(workspace_dir)
            with self.assertRaises(FileNotFoundError):
                validate_queue(workspace_dir)

    def test_foreign_creator_schedule_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            schedule = load_example("creator-content-schedule")
            schedule["creator_profile_id"] = "creator_other"
            write_json(workspace_dir / "content-schedule.json", schedule)

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("creator_other", str(ctx.exception))
            self.assertIn("does not match the owning creator workspace", str(ctx.exception))

    def test_foreign_creator_evidence_line_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            evidence = load_example("research-evidence")
            evidence["creator_profile_id"] = "creator_other"
            write_jsonl(
                workspace_dir / "research" / "runs" / RUN_ID / "evidence.jsonl", [evidence]
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("evidence.jsonl:1:", message)
            self.assertIn("creator_other", message)

    def test_foreign_creator_promotion_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            promotion = load_example("idea-promotion")
            promotion["creator_profile_id"] = "creator_other"
            write_json(
                workspace_dir / "research" / "idea-promotions" / "idea_promotion_luna_fit_001.json",
                promotion,
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("creator_other", str(ctx.exception))

    def test_foreign_creator_queue_entry_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            entry = load_example("idea-queue-entry")
            entry["creator_profile_id"] = "creator_other"
            write_json(
                workspace_dir / "research" / "idea-queue" / "entries" / f"{ENTRY_ID}.json",
                entry,
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            self.assertIn("creator_other", str(ctx.exception))

    def test_promotion_pointing_to_foreign_creator_entry_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            promotion = load_example("idea-promotion")
            # The gate compares entry ownership to the promotion directly, so
            # the check also protects validate_project's call path.
            promotion["creator_profile_id"] = "creator_other"

            with self.assertRaises(ValidationError) as ctx:
                validate_promotion_gate(workspace_dir, promotion)
            self.assertIn("owned by a different creator", str(ctx.exception))


PROMOTION_ID = "idea_promotion_luna_fit_001"
PROJECT_ID = "project_luna_tiny_reset_001"


def set_entry_status(workspace_dir, status):
    """Flip the scaffold entry's status with the manifest kept consistent."""
    entry_path = (
        workspace_dir / "research" / "idea-queue" / "entries" / f"{ENTRY_ID}.json"
    )
    entry = json.loads(entry_path.read_text())
    entry["status"] = status
    write_json(entry_path, entry)
    queue_path = workspace_dir / "research" / "idea-queue" / "queue.json"
    queue = json.loads(queue_path.read_text())
    for ref in queue["entry_refs"]:
        if ref["idea_queue_entry_id"] == ENTRY_ID:
            ref["status"] = status
    queue["status_counts"] = {status: 1}
    write_json(queue_path, queue)
    return entry


def edit_json(path, mutate):
    record = json.loads(path.read_text())
    mutate(record)
    write_json(path, record)
    return record


class PromotionLinkConsistencyTests(unittest.TestCase):
    """Slice 5 batch A: promotion <-> entry <-> project links hold at rest."""

    def promotion_path(self, workspace_dir, promotion_id=PROMOTION_ID):
        return (
            workspace_dir / "research" / "idea-promotions" / f"{promotion_id}.json"
        )

    def entry_path(self, workspace_dir):
        return (
            workspace_dir / "research" / "idea-queue" / "entries" / f"{ENTRY_ID}.json"
        )

    def test_active_promotion_requires_promoted_entry_status(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            set_entry_status(workspace_dir, "shortlisted")

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("active", message)
            self.assertIn("'shortlisted'", message)

    def test_active_promotion_requires_entry_backlink(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            edit_json(
                self.entry_path(workspace_dir),
                lambda entry: entry.__setitem__("linked_idea_promotion_ids", []),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("linked_idea_promotion_ids", str(ctx.exception))

    def test_promotion_created_projects_must_resolve(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            edit_json(
                self.promotion_path(workspace_dir),
                lambda promo: promo["project_ids_created"].append("project_luna_ghost"),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("project_luna_ghost", message)
            self.assertIn("no project record", message)

    def test_promotion_created_project_must_point_back(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            # The example warning pairs this project with the promotion and
            # would fail first; clear the warnings stream so the closure
            # check under test is what fires.
            write_jsonl(workspace_dir / "system" / "project-warnings.jsonl", [])
            edit_json(
                workspace_dir / "projects" / PROJECT_ID / "project.json",
                lambda project: project["source_refs"].__setitem__(
                    "idea_promotion_id", "idea_promotion_luna_fit_other"
                ),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("does not point back", str(ctx.exception))

    def test_promoted_entry_requires_linked_promotion(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            edit_json(
                self.entry_path(workspace_dir),
                lambda entry: entry.__setitem__("linked_idea_promotion_ids", []),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            self.assertIn("linked_idea_promotion_ids is empty", str(ctx.exception))

    def test_promoted_entry_requires_an_active_promotion(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            edit_json(
                self.promotion_path(workspace_dir),
                lambda promo: promo.__setitem__("promotion_status", "cancelled"),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            self.assertIn("no linked promotion is active", str(ctx.exception))

    def test_promoted_entry_rejects_second_active_promotion(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            second = load_example("idea-promotion")
            second["idea_promotion_id"] = "idea_promotion_luna_fit_002"
            second["project_ids_created"] = []
            write_json(
                self.promotion_path(workspace_dir, "idea_promotion_luna_fit_002"),
                second,
            )
            edit_json(
                self.entry_path(workspace_dir),
                lambda entry: entry["linked_idea_promotion_ids"].append(
                    "idea_promotion_luna_fit_002"
                ),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            self.assertIn("supersede", str(ctx.exception))

    def test_entry_linked_promotion_must_name_entry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            second = load_example("idea-promotion")
            second["idea_promotion_id"] = "idea_promotion_luna_fit_002"
            second["idea_queue_entry_id"] = "idea_queue_entry_luna_fit_002"
            second["promotion_status"] = "cancelled"
            second["project_ids_created"] = []
            write_json(
                self.promotion_path(workspace_dir, "idea_promotion_luna_fit_002"),
                second,
            )
            edit_json(
                self.entry_path(workspace_dir),
                lambda entry: entry["linked_idea_promotion_ids"].append(
                    "idea_promotion_luna_fit_002"
                ),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            self.assertIn("was promoted from", str(ctx.exception))

    def test_entry_linked_projects_must_resolve(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            edit_json(
                self.entry_path(workspace_dir),
                lambda entry: entry["linked_project_ids"].append("project_luna_ghost"),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("project_luna_ghost", message)
            self.assertIn("no project record", message)

    def test_non_promoted_entry_rejects_active_linked_promotion(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            set_entry_status(workspace_dir, "shortlisted")

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("'shortlisted'", message)
            self.assertIn("active", message)

    def test_cancelled_promotion_allows_reverted_entry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            edit_json(
                self.promotion_path(workspace_dir),
                lambda promo: promo.__setitem__("promotion_status", "cancelled"),
            )
            set_entry_status(workspace_dir, "shortlisted")

            validate_research(workspace_dir)
            validate_queue(workspace_dir)

    def test_warning_resolves_slug_foldered_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            # init-project names project folders by project_slug, not
            # project_id; resolution must go through the manifest.
            (workspace_dir / "projects" / PROJECT_ID).rename(
                workspace_dir / "projects" / "tiny-reset-after-laptop-day"
            )

            validate_research(workspace_dir)
            validate_queue(workspace_dir)

    def test_duplicate_project_id_across_folders_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            project = load_example("project")
            write_json(
                workspace_dir / "projects" / "duplicate-slug" / "project.json",
                project,
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("more than once", str(ctx.exception))

    def test_promoted_entry_requires_a_linked_project(self):
        # Slice 5 review P1: an active supported-format promotion with
        # project_ids_created [] and no entry project links validated,
        # leaving the promotion-to-project path unenforced.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            edit_json(
                self.promotion_path(workspace_dir),
                lambda promo: promo.__setitem__("project_ids_created", []),
            )
            edit_json(
                self.entry_path(workspace_dir),
                lambda entry: entry.pop("linked_project_ids"),
            )
            shutil.rmtree(workspace_dir / "projects")
            write_jsonl(workspace_dir / "system" / "project-warnings.jsonl", [])

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            self.assertIn("no linked project", str(ctx.exception))

    def test_linked_project_promotion_must_be_linked_to_entry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            stray = load_example("project")
            stray["project_id"] = "project_luna_other"
            stray["project_slug"] = "other-slug"
            stray["project_paths"] = dict(
                stray["project_paths"], root="projects/other-slug/"
            )
            stray["source_refs"] = dict(
                stray["source_refs"], idea_promotion_id="idea_promotion_luna_fit_other"
            )
            write_json(
                workspace_dir / "projects" / "other-slug" / "project.json", stray
            )
            edit_json(
                self.entry_path(workspace_dir),
                lambda entry: entry["linked_project_ids"].append("project_luna_other"),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("project_luna_other", message)
            self.assertIn("not among the entry's linked promotions", message)

    def test_promotion_created_projects_must_be_linked_on_entry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            second = load_example("project")
            second["project_id"] = "project_luna_tiny_reset_002"
            second["project_slug"] = "tiny-reset-second"
            second["project_paths"] = dict(
                second["project_paths"], root="projects/tiny-reset-second/"
            )
            write_json(
                workspace_dir / "projects" / "tiny-reset-second" / "project.json",
                second,
            )
            edit_json(
                self.promotion_path(workspace_dir),
                lambda promo: promo["project_ids_created"].append(
                    "project_luna_tiny_reset_002"
                ),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("project_luna_tiny_reset_002", message)
            self.assertIn("linked_project_ids", message)

    def test_active_promotion_slot_claim_must_resolve(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            edit_json(
                self.promotion_path(workspace_dir),
                lambda promo: promo.__setitem__(
                    "schedule_slot_ids", ["slot_luna_ghost"]
                ),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("slot_luna_ghost", message)
            self.assertIn("no schedule slot", message)

    def test_active_promotion_claimed_slot_must_be_filled(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            schedule_path = workspace_dir / "content-schedule.json"
            schedule = json.loads(schedule_path.read_text())
            schedule["calendar_slots"][0]["status"] = "open"
            write_json(schedule_path, schedule)

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("filled", message)
            self.assertIn("'open'", message)

    def test_slot_claimed_by_two_active_promotions_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            second_entry = load_example("idea-queue-entry")
            second_entry["idea_queue_entry_id"] = "idea_queue_entry_luna_fit_002"
            second_entry["linked_idea_promotion_ids"] = [
                "idea_promotion_luna_fit_002"
            ]
            second_entry["linked_project_ids"] = []
            write_json(
                workspace_dir / "research" / "idea-queue" / "entries"
                / "idea_queue_entry_luna_fit_002.json",
                second_entry,
            )
            second_promo = load_example("idea-promotion")
            second_promo["idea_promotion_id"] = "idea_promotion_luna_fit_002"
            second_promo["idea_queue_entry_id"] = "idea_queue_entry_luna_fit_002"
            second_promo["project_ids_created"] = []
            write_json(
                self.promotion_path(workspace_dir, "idea_promotion_luna_fit_002"),
                second_promo,
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("claimed by more than one active promotion", message)

    def test_cancelled_promotion_keeps_historical_slot_claim(self):
        # The schedule is mutable planning state: a freed slot may reopen or
        # disappear while the locked promotion keeps its historical claim.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            edit_json(
                self.promotion_path(workspace_dir),
                lambda promo: promo.update(
                    promotion_status="cancelled",
                    schedule_slot_ids=["slot_luna_ghost"],
                ),
            )
            set_entry_status(workspace_dir, "shortlisted")

            validate_research(workspace_dir)


class ValidatorPathParityTests(unittest.TestCase):
    """Five-slice review: the queue and research paths run the same
    promotion check set, so no promotion state validates on one command
    and fails the other."""

    def promotion_path(self, workspace_dir, promotion_id=PROMOTION_ID):
        return (
            workspace_dir / "research" / "idea-promotions" / f"{promotion_id}.json"
        )

    def test_queue_rejects_superseded_promotion_with_dangling_entry(self):
        # Previously only active promotions were entry-checked on the queue
        # path; a superseded promotion with a ghost entry passed validate
        # queue while validate research rejected it.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            promo2 = load_example("idea-promotion")
            promo2["idea_promotion_id"] = "idea_promotion_luna_fit_002"
            promo2["promotion_status"] = "superseded"
            promo2["idea_queue_entry_id"] = "idea_queue_entry_luna_fit_ghost"
            promo2["project_ids_created"] = []
            promo2["schedule_slot_ids"] = []
            write_json(
                self.promotion_path(workspace_dir, "idea_promotion_luna_fit_002"),
                promo2,
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            self.assertIn(
                "does not point to a real idea queue entry", str(ctx.exception)
            )

    def test_queue_rejects_foreign_creator_promotion(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            edit_json(
                self.promotion_path(workspace_dir),
                lambda promo: promo.__setitem__(
                    "creator_profile_id", "creator_other"
                ),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            self.assertIn("creator_other", str(ctx.exception))

    def test_queue_rejects_promotion_filename_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            promotion_path = self.promotion_path(workspace_dir)
            promotion_path.rename(
                promotion_path.with_name("idea_promotion_luna_fit_wrong.json")
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            self.assertIn("filename does not match idea_promotion_id", str(ctx.exception))

    def test_queue_rejects_dangling_slot_claim(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            edit_json(
                self.promotion_path(workspace_dir),
                lambda promo: promo.__setitem__(
                    "schedule_slot_ids", ["slot_luna_ghost"]
                ),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            self.assertIn("resolves to no schedule slot", str(ctx.exception))

    def test_queue_reports_gate_warnings(self):
        # The gate's human-approved unresolved-evidence warnings surface on
        # the queue path too; previously validate_queue had no warnings
        # channel at all.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            edit_json(
                self.promotion_path(workspace_dir),
                lambda promo: promo["evidence_refs"][0].__setitem__(
                    "evidence_id", "evidence_luna_fit_never_existed"
                ),
            )

            result = validate_queue(workspace_dir)
            self.assertTrue(result["warnings"])
            self.assertIn("unresolved evidence refs", result["warnings"][0])

    def test_research_path_enforces_entry_closure(self):
        # The slice 5 P1 closure (a promoted entry must leave production
        # work behind) previously lived only in validate_queue; an active
        # promotion with zero projects passed validate research.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            write_jsonl(workspace_dir / "system" / "project-warnings.jsonl", [])
            shutil.rmtree(workspace_dir / "projects" / PROJECT_ID)
            edit_json(
                self.promotion_path(workspace_dir),
                lambda promo: promo.__setitem__("project_ids_created", []),
            )
            entry_path = (
                workspace_dir / "research" / "idea-queue" / "entries" / f"{ENTRY_ID}.json"
            )
            edit_json(
                entry_path,
                lambda entry: entry.__setitem__("linked_project_ids", []),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("no linked project", str(ctx.exception))


class ResearchRecordLinkageTests(unittest.TestCase):
    """Five-slice review: run records stay unambiguous and linked."""

    def run_path(self, workspace_dir, filename):
        return workspace_dir / "research" / "runs" / RUN_ID / filename

    def test_duplicate_evidence_id_within_a_run_fails(self):
        # A duplicated id passes set-based outputs reconciliation but makes
        # every ref ambiguous and bricks the recall index rebuild.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            evidence_path = self.run_path(workspace_dir, "evidence.jsonl")
            duplicate = load_example("research-evidence")
            duplicate["source_summary"] = "Conflicting duplicate record."
            with evidence_path.open("a") as handle:
                handle.write(json.dumps(duplicate) + "\n")

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn("duplicate evidence_id values", str(ctx.exception))

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            self.assertIn("duplicated within the run", str(ctx.exception))

    def test_metric_snapshot_must_reference_run_evidence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            snapshot = load_example("metric-snapshot")
            snapshot["evidence_id"] = "evidence_luna_fit_ghost"
            write_jsonl(
                self.run_path(workspace_dir, "metric-snapshots.jsonl"), [snapshot]
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("snapshots evidence", message)
            self.assertIn("evidence_luna_fit_ghost", message)

    def test_evidence_ref_pairing_must_match(self):
        # A ref pairing evidence A with a snapshot of evidence B severs the
        # metric trajectory; refs must cite snapshots of their own evidence.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            evidence_b = load_example("research-evidence")
            evidence_b["evidence_id"] = "evidence_luna_fit_002"
            with self.run_path(workspace_dir, "evidence.jsonl").open("a") as handle:
                handle.write(json.dumps(evidence_b) + "\n")
            snapshot_b = load_example("metric-snapshot")
            snapshot_b["metric_snapshot_id"] = "metric_snapshot_luna_fit_002"
            snapshot_b["evidence_id"] = "evidence_luna_fit_002"
            with self.run_path(workspace_dir, "metric-snapshots.jsonl").open(
                "a"
            ) as handle:
                handle.write(json.dumps(snapshot_b) + "\n")
            edit_json(
                self.run_path(workspace_dir, "research-run.json"),
                lambda run: (
                    run["outputs"]["evidence_ids"].append("evidence_luna_fit_002"),
                    run["outputs"]["metric_snapshot_ids"].append(
                        "metric_snapshot_luna_fit_002"
                    ),
                ),
            )
            entry_path = (
                workspace_dir / "research" / "idea-queue" / "entries" / f"{ENTRY_ID}.json"
            )
            edit_json(
                entry_path,
                lambda entry: entry["evidence_refs"][0].__setitem__(
                    "metric_snapshot_ids", ["metric_snapshot_luna_fit_002"]
                ),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            self.assertIn("not the ref's evidence", str(ctx.exception))

    def test_slot_claims_fail_cleanly_on_malformed_schedule(self):
        # Reachable from validate project, which does not otherwise validate
        # the schedule: a slot missing its status must fail with a validation
        # error, not crash with a KeyError.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            edit_json(
                workspace_dir / "content-schedule.json",
                lambda schedule: schedule["calendar_slots"][0].pop("status"),
            )

            with self.assertRaises(ValidationError):
                validate_queue(workspace_dir)

    def test_video_pack_id_must_match_filename(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            pack_path = (
                workspace_dir
                / "research"
                / "video-understanding-packs"
                / "video_research_luna_fit_001.json"
            )
            edit_json(
                pack_path,
                lambda pack: pack.__setitem__(
                    "video_understanding_pack_id", "video_research_luna_fit_999"
                ),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_queue(workspace_dir)
            self.assertIn(
                "filename does not match video_understanding_pack_id",
                str(ctx.exception),
            )

    def test_stable_finding_filename_must_match_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            stable_dir = workspace_dir / "research" / "stable-findings"
            (stable_dir / "stable_finding_luna_fit_001.md").rename(
                stable_dir / "wrong-name.md"
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_research(workspace_dir)
            self.assertIn(
                "filename does not match stable_finding_id", str(ctx.exception)
            )


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
