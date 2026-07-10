"""Shared integration-test workspace and project builders."""

import json
from pathlib import Path

from influencer_os.creator_workspaces import init_creator
from influencer_os.projects import init_project


ROOT = Path(__file__).resolve().parents[1]

GENERATION_FIXTURE_ARTIFACTS = {
    "tiny-reset-video-001.mp4": b"tiny-reset-video-001\n",
    "tiny-reset-thumb-001.png": b"tiny-reset-thumb-001\n",
}


def _copy_example_record(example_name, destination):
    destination.write_text((ROOT / "examples" / example_name).read_text())


def _copy_example_jsonl(example_name, destination):
    record = json.loads((ROOT / "examples" / example_name).read_text())
    destination.write_text(json.dumps(record) + "\n")


def _rewrite_json(path, mutate):
    record = json.loads(path.read_text())
    mutate(record)
    path.write_text(json.dumps(record, indent=2) + "\n")


def populate_workspace_records(workspace_dir):
    _copy_example_record("creator-profile.example.json", workspace_dir / "creator-profile.json")
    _copy_example_record(
        "visual-continuity-plan.example.json",
        workspace_dir / "references" / "visual-continuity-plan.json",
    )
    _copy_example_record(
        "reference-library.example.json",
        workspace_dir / "references" / "reference-library.json",
    )
    (workspace_dir / "sources" / "intakes" / "luna-fit-breakdown.md").write_text(
        (ROOT / "examples" / "sources" / "luna-fit-breakdown.example.md").read_text()
    )


def populate_video_understanding_packs(workspace_dir):
    _copy_example_record(
        "video-understanding-pack.example.json",
        workspace_dir
        / "research"
        / "video-understanding-packs"
        / "video_research_luna_fit_001.json",
    )


def populate_promotion_records(workspace_dir):
    run_dir = (
        workspace_dir
        / "research"
        / "runs"
        / "research_run_luna_fit_2026_07_03_001"
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    _copy_example_record("research-run.example.json", run_dir / "research-run.json")
    _copy_example_record(
        "research-search-plan.example.json", run_dir / "search-plan.json"
    )
    source_yield = json.loads(
        (ROOT / "examples" / "research-source-yield.example.json").read_text()
    )
    source_yield["source_key"] = "ad_hoc_project_fixture"
    source_yield.pop("source_plan_id", None)
    (run_dir / "source-yield.jsonl").write_text(json.dumps(source_yield) + "\n")
    _copy_example_jsonl(
        "research-evidence.example.json", run_dir / "evidence.jsonl"
    )
    _copy_example_jsonl(
        "metric-snapshot.example.json", run_dir / "metric-snapshots.jsonl"
    )
    promotion_path = (
        workspace_dir
        / "research"
        / "idea-promotions"
        / "idea_promotion_luna_fit_001.json"
    )
    promotion_path.parent.mkdir(parents=True, exist_ok=True)
    _copy_example_record("idea-promotion.example.json", promotion_path)
    entry_path = (
        workspace_dir
        / "research"
        / "idea-queue"
        / "entries"
        / "idea_queue_entry_luna_fit_001.json"
    )
    entry_path.parent.mkdir(parents=True, exist_ok=True)
    _copy_example_record("idea-queue-entry.example.json", entry_path)
    _copy_example_record(
        "creator-content-schedule.example.json",
        workspace_dir / "content-schedule.json",
    )
    _rewrite_json(
        workspace_dir / "content-schedule.json",
        lambda schedule: schedule["calendar_slots"][0].update(
            status="filled",
            working_title="A two-minute desk reset between meetings",
            research_state={
                "status": "selected",
                "research_run_ids": ["research_run_luna_fit_2026_07_03_001"],
                "selected_idea_queue_entry_id": "idea_queue_entry_luna_fit_001",
            },
        ),
    )


def populate_project_records(project_dir):
    _copy_example_record(
        "applied-social-template.example.json",
        project_dir / "plan" / "applied-template.json",
    )
    _copy_example_record(
        "micro-journey-video-plan.example.json",
        project_dir / "plan" / "production-plan.json",
    )
    _copy_example_record(
        "base-video-generation-plan.example.json",
        project_dir / "plan" / "generation-plan.json",
    )


def scaffold_project_workspace(temp_dir):
    workspace_dir = init_creator(
        ROOT / "examples" / "creator-workspace.example.json",
        workspace_root=Path(temp_dir),
    )
    populate_workspace_records(workspace_dir)
    populate_video_understanding_packs(workspace_dir)
    populate_promotion_records(workspace_dir)
    project_dir = init_project(
        ROOT / "examples" / "project.example.json",
        creator_workspace=workspace_dir,
    )
    populate_project_records(project_dir)
    return workspace_dir, project_dir


def write_upload_ready_assets(asset_root, package):
    for asset in package["upload_ready"]:
        asset_path = asset_root / asset["path"]
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        asset_path.write_text(f"{asset['upload_asset_id']}\n")


def seed_generation_fixtures(project_dir):
    project_dir = Path(project_dir)
    assets_dir = project_dir / "generation" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    for name, content in GENERATION_FIXTURE_ARTIFACTS.items():
        (assets_dir / name).write_bytes(content)

    approval = json.loads(
        (ROOT / "examples" / "generation-approval-record.example.json").read_text()
    )
    approval.update(
        status="executed",
        executed_at="2026-07-06T16:06:01",
        resulting_asset_ids=["gen_asset_luna_tiny_reset_video_001"],
    )
    approvals_dir = project_dir / "generation" / "approval-records"
    approvals_dir.mkdir(parents=True, exist_ok=True)
    (approvals_dir / f"{approval['generation_approval_record_id']}.json").write_text(
        json.dumps(approval, indent=2) + "\n"
    )
    _copy_example_record(
        "generation-asset-manifest.example.json",
        project_dir / "generation" / "asset-manifest.json",
    )
    reviews_dir = project_dir / "generation" / "quality-reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    _copy_example_record(
        "quality-review.example.json",
        reviews_dir / "quality_review_luna_tiny_reset_001.json",
    )
    _rewrite_json(
        project_dir / "project.json",
        lambda project: project.update(status="generated"),
    )


def switch_project_to_text_format(workspace_dir, project_dir, unit_type):
    format_id = f"format_{unit_type}"
    platform = "substack" if unit_type == "article" else "x"
    _rewrite_json(
        project_dir / "project.json",
        lambda project: project.update(
            content_unit_type=unit_type,
            target_formats=[format_id],
            platform_targets=[platform],
        ),
    )
    _rewrite_json(
        workspace_dir / "research" / "idea-promotions" / "idea_promotion_luna_fit_001.json",
        lambda promotion: promotion.update(
            approved_formats=[format_id], approved_platforms=[platform]
        ),
    )
    _rewrite_json(
        project_dir / "plan" / "applied-template.json",
        lambda template: template.update(target_format_id=format_id),
    )
    _copy_example_record(
        f"{unit_type}-plan.example.json",
        project_dir / "plan" / "production-plan.json",
    )
    (project_dir / "plan" / "generation-plan.json").unlink()
