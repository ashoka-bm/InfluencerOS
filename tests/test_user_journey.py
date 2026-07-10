import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_readiness_validation import (
    place_asset_files,
    place_brand_board_space_files,
    populate_foundation,
    write_channels,
    write_readiness_milestones,
)


ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "research_run_luna_fit_2026_07_03_001"
ENTRY_ID = "content_opportunity_luna_fit_001"
PROJECT_SLUG = "tiny-reset-after-laptop-day"


def run_cli(*args, cwd=ROOT):
    result = subprocess.run(
        [sys.executable, "-m", "influencer_os", *map(str, args)],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"Command failed: {' '.join(map(str, args))}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result


def copy_example(example_name, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text((ROOT / "examples" / example_name).read_text())


def write_json(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + "\n")


def write_jsonl_from_example(example_name, destination):
    record = json.loads((ROOT / "examples" / example_name).read_text())
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(record) + "\n")


def frontmatter(data):
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


def set_workspace_status(workspace_dir, status):
    manifest_path = workspace_dir / "creator-workspace.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["status"] = status
    write_json(manifest_path, manifest)


def write_research_markdown(workspace_dir):
    findings = json.loads((ROOT / "examples" / "research-findings.example.json").read_text())
    stable = json.loads((ROOT / "examples" / "stable-finding.example.json").read_text())

    findings_path = workspace_dir / "research" / "findings.md"
    findings_path.parent.mkdir(parents=True, exist_ok=True)
    findings_path.write_text(
        frontmatter(findings)
        + "\n## Desk resets\n\nLunch-break resets are outperforming baselines this week.\n"
    )

    stable_path = (
        workspace_dir
        / "research"
        / "stable-findings"
        / "stable_finding_luna_fit_001.md"
    )
    stable_path.parent.mkdir(parents=True, exist_ok=True)
    stable_path.write_text(
        frontmatter(stable) + "\nDesk resets are a durable topic cluster for Luna.\n"
    )


def seed_creator_setup_outputs(workspace_dir):
    copy_example("creator-profile.example.json", workspace_dir / "creator-profile.json")
    copy_example(
        "visual-continuity-plan.example.json",
        workspace_dir / "references" / "visual-continuity-plan.json",
    )
    copy_example(
        "reference-library.example.json",
        workspace_dir / "references" / "reference-library.json",
    )
    copy_example(
        "sources/luna-fit-breakdown.example.md",
        workspace_dir / "sources" / "intakes" / "luna-fit-breakdown.md",
    )
    populate_foundation(workspace_dir)
    place_asset_files(workspace_dir)
    write_channels(workspace_dir)
    write_readiness_milestones(workspace_dir)
    copy_example(
        "personal-brand-board.example.json",
        workspace_dir / "references" / "brand" / "personal-brand-board.json",
    )
    place_brand_board_space_files(workspace_dir)
    run_cli("rebuild-brand-board", workspace_dir)


def seed_research_outputs(workspace_dir):
    run_dir = workspace_dir / "research" / "runs" / RUN_ID
    copy_example("research-run.example.json", run_dir / "research-run.json")
    copy_example("research-search-plan.example.json", run_dir / "search-plan.json")
    write_jsonl_from_example("research-evidence.example.json", run_dir / "evidence.jsonl")
    write_jsonl_from_example(
        "metric-snapshot.example.json", run_dir / "metric-snapshots.jsonl"
    )
    write_jsonl_from_example(
        "research-source-yield.example.json", run_dir / "source-yield.jsonl"
    )

    copy_example(
        "video-understanding-pack.example.json",
        workspace_dir
        / "research"
        / "video-understanding-packs"
        / "video_research_luna_fit_001.json",
    )

    intelligence = workspace_dir / "research" / "intelligence"
    copy_example("research-sources.example.json", intelligence / "sources.json")
    copy_example("research-hashtags.example.json", intelligence / "hashtags.json")
    copy_example("research-search-terms.example.json", intelligence / "search-terms.json")
    copy_example("reference-creators.example.json", intelligence / "reference-creators.json")
    copy_example("research-watchlist.example.json", intelligence / "watchlist.json")

    write_research_markdown(workspace_dir)

    copy_example(
        "creator-content-schedule.example.json", workspace_dir / "content-schedule.json"
    )
    schedule_path = workspace_dir / "content-schedule.json"
    schedule = json.loads(schedule_path.read_text())
    schedule["calendar_slots"][0].update(
        status="filled",
        working_title="A two-minute desk reset between meetings",
        research_state={
            "status": "selected",
            "research_run_ids": [RUN_ID],
            "selected_content_opportunity_id": ENTRY_ID,
        },
    )
    schedule_path.write_text(json.dumps(schedule, indent=2) + "\n")
    copy_example(
        "content-opportunity-queue.example.json",
        workspace_dir / "research" / "content-opportunity-queue" / "queue.json",
    )
    copy_example(
        "content-opportunity.example.json",
        workspace_dir
        / "research"
        / "content-opportunity-queue"
        / "entries"
        / "content_opportunity_luna_fit_001.json",
    )
    campaign_root = workspace_dir / "campaigns" / "campaign_luna_fit_001"
    copy_example("campaign.example.json", campaign_root / "campaign.json")
    concept_path = (
        campaign_root / "concepts" / "campaign_concept_luna_fit_001.json"
    )
    copy_example("campaign-concept.example.json", concept_path)
    concept = json.loads(concept_path.read_text())
    concept["status"] = "active"
    concept_path.write_text(json.dumps(concept, indent=2) + "\n")
    copy_example(
        "concept-approval.example.json",
        campaign_root / "approvals" / "concept_approval_luna_fit_001.json",
    )
    asset_path = (
        workspace_dir / "conversion-assets"
        / "conversion_asset_luna_reset_checklist.json"
    )
    copy_example("conversion-asset.example.json", asset_path)
    asset = json.loads(asset_path.read_text())
    for file_ref in asset.get("file_refs", []):
        ref_path = workspace_dir / file_ref
        ref_path.parent.mkdir(parents=True, exist_ok=True)
        if not ref_path.exists():
            ref_path.write_text("Journey conversion asset body.\n")
    write_jsonl_from_example(
        "project-warning.example.json", workspace_dir / "system" / "project-warnings.jsonl"
    )
    write_jsonl_from_example(
        "system-event.example.json", workspace_dir / "system" / "creator-events.jsonl"
    )


def seed_project_outputs(project_dir):
    copy_example(
        "applied-social-template.example.json",
        project_dir / "plan" / "applied-template.json",
    )
    copy_example(
        "micro-journey-video-plan.example.json",
        project_dir / "plan" / "production-plan.json",
    )
    copy_example(
        "base-video-generation-plan.example.json",
        project_dir / "plan" / "generation-plan.json",
    )


def seed_upload_ready_assets(asset_root):
    package = json.loads((ROOT / "examples" / "output-package.example.json").read_text())
    for asset in package["upload_ready"]:
        destination = asset_root / asset["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(asset["upload_asset_id"] + "\n")


class PhaseOneUserJourneyTests(unittest.TestCase):
    def test_user_can_run_planning_os_from_creator_setup_to_packaged_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            run_root = Path(temp_dir)
            creators_root = run_root / "creators"
            workspace_dir = creators_root / "luna-fit"
            project_dir = workspace_dir / "projects" / PROJECT_SLUG

            run_cli(
                "init-creator",
                ROOT / "examples" / "creator-workspace.example.json",
                "--workspace-root",
                creators_root,
            )

            seed_creator_setup_outputs(workspace_dir)
            intake_source = run_root / "operator-interview.md"
            intake_source.write_text(
                "# Operator Interview\n\nLuna should prioritize short desk-reset videos.\n"
            )
            run_cli(
                "import-intake",
                intake_source,
                "--creator-workspace",
                workspace_dir,
                "--source-type",
                "interview",
                "--source-id",
                "source_luna_fit_interview_001",
                "--imported-on",
                "2026-07-04",
                "--notes",
                "Operator interview for end-to-end planning journey test.",
            )
            run_cli(
                "set-intake-status",
                workspace_dir,
                "source_luna_fit_interview_001",
                "reviewed",
            )
            set_workspace_status(workspace_dir, "foundation_ready")
            run_cli("validate", "workspace", workspace_dir)

            seed_research_outputs(workspace_dir)
            run_cli(
                "init-project",
                ROOT / "examples" / "project.example.json",
                "--creator-workspace",
                workspace_dir,
            )
            seed_project_outputs(project_dir)

            run_cli("validate", "research", workspace_dir)
            run_cli("validate", "queue", workspace_dir)
            run_cli("validate", "project", project_dir)

            # Generation provenance (ADR 0023): the example package's media
            # refs resolve through the seeded approval record + manifest.
            from tests.support import seed_generation_fixtures

            seed_generation_fixtures(project_dir)

            asset_root = run_root / "package-assets"
            seed_upload_ready_assets(asset_root)
            run_cli(
                "register-output-package",
                ROOT / "examples" / "output-package.example.json",
                "--project",
                project_dir,
                "--asset-root",
                asset_root,
            )
            run_cli("validate", "project", project_dir)
            run_cli("rebuild-board", workspace_dir)
            run_cli("validate", "board", workspace_dir)
            run_cli("rebuild-index", workspace_dir, "--db", run_root / "index.sqlite")
            run_cli("prune", workspace_dir)
            run_cli("update-creators", "--workspace-root", creators_root)

            project = json.loads((project_dir / "project.json").read_text())
            board = json.loads((workspace_dir / "boards" / "content-board.json").read_text())

            self.assertEqual(project["status"], "packaged")
            self.assertTrue((project_dir / "output-package" / "output-package.json").exists())
            self.assertEqual(len(board["cards"]), 5)
            self.assertTrue((run_root / "index.sqlite").exists())
