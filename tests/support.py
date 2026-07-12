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
    for relative_path in (
        "brand_context/identity.md",
        "brand_context/soul.md",
        "brand_context/personal-brand.md",
        "references/character/luna-identity-plate.png",
    ):
        path = workspace_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("review packet fixture\n")
    board_path = workspace_dir / "references" / "brand" / "personal-brand-board.json"
    board_path.parent.mkdir(parents=True, exist_ok=True)
    board_path.write_text(
        json.dumps({"avatar_asset_id": "asset_luna_identity_plate"}) + "\n"
    )
    review = json.loads((ROOT / "examples" / "review-record.example.json").read_text())
    review.pop("project_id")
    review.pop("concept_approval_id")
    review.update(
        review_record_id="review_luna_setup_001",
        review_role="setup",
        artifact_refs=[
            "creator-profile.json",
            "brand_context/identity.md",
            "brand_context/soul.md",
            "brand_context/personal-brand.md",
            "references/reference-library.json",
            "references/character/luna-identity-plate.png",
            "references/visual-continuity-plan.json",
        ],
    )
    review["findings"] = [
        {
            "area": "foundation",
            "severity": "none",
            "note": "The fixture foundation is internally consistent.",
        }
    ]
    review["reviewer_execution"]["source_skill"] = "review-creator-setup"
    reviews_dir = workspace_dir / "reviews"
    reviews_dir.mkdir(exist_ok=True)
    (reviews_dir / f"{review['review_record_id']}.json").write_text(
        json.dumps(review, indent=2) + "\n"
    )


def write_setup_review_fixture(workspace_dir):
    """Add the terminal Setup Review required by an approved plan fixture."""
    for relative_path in (
        "brand_context/identity.md",
        "brand_context/soul.md",
        "brand_context/personal-brand.md",
        "references/character/luna-identity-plate.png",
    ):
        path = workspace_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("review packet fixture\n")
    board_path = workspace_dir / "references" / "brand" / "personal-brand-board.json"
    board_path.parent.mkdir(parents=True, exist_ok=True)
    if not board_path.exists():
        board_path.write_text(
            json.dumps({"avatar_asset_id": "asset_luna_identity_plate"}) + "\n"
        )
    review = json.loads((ROOT / "examples" / "review-record.example.json").read_text())
    review.pop("project_id")
    review.pop("concept_approval_id")
    review.update(
        review_record_id="review_luna_setup_001",
        review_role="setup",
        artifact_refs=[
            "creator-profile.json",
            "brand_context/identity.md",
            "brand_context/soul.md",
            "brand_context/personal-brand.md",
            "references/reference-library.json",
            "references/character/luna-identity-plate.png",
            "references/visual-continuity-plan.json",
        ],
        findings=[
            {
                "area": "foundation",
                "severity": "none",
                "note": "The fixture foundation is internally consistent.",
            }
        ],
    )
    review["reviewer_execution"]["source_skill"] = "review-creator-setup"
    reviews_dir = workspace_dir / "reviews"
    reviews_dir.mkdir(exist_ok=True)
    (reviews_dir / "review_luna_setup_001.json").write_text(
        json.dumps(review, indent=2) + "\n"
    )


def write_strategy_review_fixture(workspace_dir):
    """Add the terminal Strategy Review required by production readiness."""
    findings_path = workspace_dir / "research" / "findings.md"
    findings_path.parent.mkdir(parents=True, exist_ok=True)
    if not findings_path.exists():
        findings_path.write_text(
            "---\n"
            "research_findings_id: research_findings_luna_fit\n"
            "creator_profile_id: creator_luna_fit\n"
            "last_updated: 2026-07-03\n"
            "last_ran: 2026-07-03T09:40:00\n"
            "summary_char_limit: 6000\n"
            "active_platforms:\n"
            "- instagram\n"
            "- tiktok\n"
            "active_topic_clusters:\n"
            "- desk resets\n"
            "- evening wind-down\n"
            "source_run_ids:\n"
            "- research_run_luna_fit_2026_07_03_001\n"
            "finding_ids:\n"
            "- finding_luna_fit_desk_reset_lunch\n"
            "---\n"
        )
    review = json.loads((ROOT / "examples" / "review-record.example.json").read_text())
    review.pop("project_id")
    review.pop("concept_approval_id")
    review.update(
        review_record_id="review_luna_strategy_001",
        review_role="strategy",
        research_demand_loop={
            "extra_research_round": 0,
            "prior_review_record_id": None,
        },
        artifact_refs=[
            "creator-profile.json",
            "content-strategy.json",
            "content-schedule.json",
            "research/findings.md",
            "research/runs/research_run_luna_fit_2026_07_03_001/evidence.jsonl",
        ],
        findings=[
            {
                "area": "strategy",
                "severity": "none",
                "note": "The fixture strategy is internally consistent.",
            }
        ],
    )
    review["reviewer_execution"]["source_skill"] = "review-strategy"
    reviews_dir = workspace_dir / "reviews"
    reviews_dir.mkdir(exist_ok=True)
    (reviews_dir / "review_luna_strategy_001.json").write_text(
        json.dumps(review, indent=2) + "\n"
    )


def populate_video_understanding_packs(workspace_dir):
    _copy_example_record(
        "video-understanding-pack.example.json",
        workspace_dir
        / "research"
        / "video-understanding-packs"
        / "video_research_luna_fit_001.json",
    )


def populate_approval_records(workspace_dir):
    """The full approval-chain fixture: research run, assigned content
    opportunity + queue, active campaign, active concept, active concept
    approval, and the claimed schedule slot (selected via the opportunity)."""
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

    entry_path = (
        workspace_dir
        / "research"
        / "content-opportunity-queue"
        / "entries"
        / "content_opportunity_luna_fit_001.json"
    )
    entry_path.parent.mkdir(parents=True, exist_ok=True)
    _copy_example_record("content-opportunity.example.json", entry_path)
    _copy_example_record(
        "content-opportunity-queue.example.json",
        workspace_dir / "research" / "content-opportunity-queue" / "queue.json",
    )
    assets_dir = workspace_dir / "conversion-assets"
    assets_dir.mkdir(exist_ok=True)
    _copy_example_record(
        "conversion-asset.example.json",
        assets_dir / "conversion_asset_luna_reset_checklist.json",
    )
    asset_record = json.loads(
        (ROOT / "examples" / "conversion-asset.example.json").read_text()
    )
    for file_ref in asset_record.get("file_refs", []):
        ref_path = workspace_dir / file_ref
        ref_path.parent.mkdir(parents=True, exist_ok=True)
        if not ref_path.exists():
            ref_path.write_text("Fixture conversion asset body.\n")
    campaign_root = workspace_dir / "campaigns" / "campaign_luna_fit_001"
    (campaign_root / "concepts").mkdir(parents=True, exist_ok=True)
    (campaign_root / "approvals").mkdir(parents=True, exist_ok=True)
    _copy_example_record(
        "campaign.example.json", campaign_root / "campaign.json"
    )
    _copy_example_record(
        "campaign-concept.example.json",
        campaign_root / "concepts" / "campaign_concept_luna_fit_001.json",
    )
    _rewrite_json(
        campaign_root / "concepts" / "campaign_concept_luna_fit_001.json",
        lambda concept: concept.update(status="active"),
    )
    _copy_example_record(
        "concept-approval.example.json",
        campaign_root / "approvals" / "concept_approval_luna_fit_001.json",
    )

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
                "selected_content_opportunity_id": "content_opportunity_luna_fit_001",
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
    populate_approval_records(workspace_dir)
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
        workspace_dir / "campaigns" / "campaign_luna_fit_001" / "approvals"
        / "concept_approval_luna_fit_001.json",
        lambda approval: approval.update(
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
