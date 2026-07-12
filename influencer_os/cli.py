import argparse
import datetime
import json
import sys
from pathlib import Path

from influencer_os.json_io import write_json_atomic
from influencer_os.memory import (
    DEFAULT_MEMORY_SECTION,
    EVIDENCE_STRENGTHS,
    append_creator_lesson,
    append_skill_learning,
    creator_lessons_workspace,
    write_memory_fact,
)
from influencer_os.migrations import (
    migrate_campaign_model,
    migrate_content_series,
    migrate_visual_foundation,
)
from influencer_os.creator_workspaces import (
    DEFAULT_CREATOR_WORKSPACE_ROOT,
    INTAKE_DESTINATIONS,
    import_intake,
    init_creator,
    set_intake_status,
    sync_creator_runtime,
    update_creators,
    validate_creator_workspace,
)
from influencer_os.boards import rebuild_board, validate_board
from influencer_os.brand_boards import rebuild_brand_board, validate_brand_board
from influencer_os.calendars import rebuild_calendar, validate_calendar
from influencer_os.connectors.fetch import FETCH_MODES
from influencer_os.constructors import SCAFFOLD_TYPES
from influencer_os.full_validation import validate_all
from influencer_os.analytics import import_analytics_csv
from influencer_os.projects import init_project, validate_project
from influencer_os.projects import add_analytics_snapshot, register_output_package, register_published_post
from influencer_os.prune import DEFAULT_RETENTION_DAYS, prune_research
from influencer_os.recall_index import rebuild_index
from influencer_os.readiness import require_production_ready
from influencer_os.research import validate_queue, validate_research
from influencer_os.semantic_lookup import query_lookup, rebuild_lookup
from influencer_os.skill_runtime import sync_codex_skills, validate_codex_skill_drift
from influencer_os.validation import ValidationError, validate_examples, validate_file


def main(argv=None):
    parser = argparse.ArgumentParser(prog="influencer-os")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate repository records.")
    validate_parser.add_argument("target", choices=["examples", "workspace", "project", "record", "research", "queue", "board", "calendar", "brand-board", "all"], help="Validation target ('all' composes workspace, research, queue, projections, and every project — the alpha release gate).")
    validate_parser.add_argument("path", nargs="?", help="Path for workspace/project/research/queue/board validation, or schema name for record validation.")
    validate_parser.add_argument("record_path", nargs="?", help="Record path for record validation.")

    creator_parser = subparsers.add_parser("init-creator", help="Initialize a Creator Workspace from a workspace manifest.")
    creator_parser.add_argument("creator_workspace", help="Path to a Creator Workspace JSON manifest.")
    creator_parser.add_argument("--workspace-root", default=str(DEFAULT_CREATOR_WORKSPACE_ROOT), help="Creator workspace root directory.")

    sync_creator_parser = subparsers.add_parser("sync-creator-runtime", help="Refresh copied runtime skills inside a Creator Workspace.")
    sync_creator_parser.add_argument("creator_workspace", help="Path to the Creator Workspace.")

    update_creators_parser = subparsers.add_parser("update-creators", help="Refresh copied runtime skills across every Creator Workspace under a root.")
    update_creators_parser.add_argument("--workspace-root", default=str(DEFAULT_CREATOR_WORKSPACE_ROOT), help="Creator workspace root directory.")

    migrate_campaign_parser = subparsers.add_parser(
        "migrate-campaign-model",
        help="Convert a legacy idea-queue Creator Workspace to the campaign model (ADR 0031); fails closed on promoted work, which needs an explicit mapping or a fixture rebuild.",
    )
    migrate_campaign_parser.add_argument(
        "creator_workspace", help="Path to the Creator Workspace."
    )

    migrate_series_parser = subparsers.add_parser(
        "migrate-content-series",
        help="Rename legacy content_strategy.content_campaigns to content_series (ADR 0031) in one Creator Workspace, including calendar-slot refs.",
    )
    migrate_series_parser.add_argument(
        "creator_workspace", help="Path to the Creator Workspace."
    )

    migrate_visual_parser = subparsers.add_parser(
        "migrate-visual-foundation",
        help="Upgrade a legacy creator workspace to required avatar and setup-generation authorization records.",
    )
    migrate_visual_parser.add_argument(
        "creator_workspace", help="Path to the Creator Workspace."
    )

    sync_codex_parser = subparsers.add_parser(
        "sync-codex-skills",
        help="Refresh repository-owned skills in the global Codex runtime.",
    )
    sync_codex_parser.add_argument(
        "--target-root", help="Codex skills directory; defaults to ~/.codex/skills."
    )

    check_codex_parser = subparsers.add_parser(
        "check-codex-skills",
        help="Fail when global Codex skill copies differ from repository sources.",
    )
    check_codex_parser.add_argument(
        "--target-root", help="Codex skills directory; defaults to ~/.codex/skills."
    )

    intake_parser = subparsers.add_parser("import-intake", help="Import a setup source file into a Creator Workspace and record source intake provenance.")
    intake_parser.add_argument("source_file", help="Path to the source file to import.")
    intake_parser.add_argument("--creator-workspace", required=True, help="Path to the Creator Workspace.")
    intake_parser.add_argument("--source-type", required=True, choices=sorted(INTAKE_DESTINATIONS), help="Source intake type; routes the file under sources/.")
    intake_parser.add_argument("--notes", required=True, help="Provenance note for the source intake record.")
    intake_parser.add_argument("--source-id", help="Optional explicit source id; auto-generated when omitted.")
    intake_parser.add_argument("--imported-on", help="Import date as YYYY-MM-DD; defaults to today.")

    intake_status_parser = subparsers.add_parser("set-intake-status", help="Move a source intake's extraction status forward (pending -> drafted -> reviewed).")
    intake_status_parser.add_argument("creator_workspace", help="Path to the Creator Workspace.")
    intake_status_parser.add_argument("source_id", help="Source intake id from creator-workspace.json.")
    intake_status_parser.add_argument("status", choices=["drafted", "reviewed"], help="New extraction status.")

    project_parser = subparsers.add_parser("init-project", help="Initialize a project folder inside a Creator Workspace.")
    project_parser.add_argument("project", help="Path to a Project JSON manifest.")
    project_parser.add_argument("--creator-workspace", required=True, help="Path to the Creator Workspace.")

    scaffold_parser = subparsers.add_parser("scaffold", help="Build a canonical record from a seed of authored fields (ADR 0042); the constructor derives, copies, validates, and writes the rest in one invocation.")
    scaffold_parser.add_argument("record_type", nargs="?", choices=sorted(SCAFFOLD_TYPES), help="Record type to scaffold.")
    scaffold_parser.add_argument("--seed", help="Path to the seed JSON (authored fields only; see docs/record-constructors.md).")
    scaffold_parser.add_argument("--creator-workspace", help="Path to the Creator Workspace.")
    scaffold_parser.add_argument("--list", action="store_true", dest="list_types", help="List the record types that have constructors.")

    stage_parser = subparsers.add_parser("stage", help="Stage a pre-approval draft bundle under system/staging/ (ADR 0042). Writes nothing canonical; present the approval package from the staged records.")
    stage_parser.add_argument("bundle", choices=["approval"], help="Bundle kind to stage.")
    stage_parser.add_argument("--concept", required=True, help="Campaign concept id being approved.")
    stage_parser.add_argument("--seed", required=True, help="Path to the approval bundle seed JSON.")
    stage_parser.add_argument("--creator-workspace", required=True, help="Path to the Creator Workspace.")

    commit_stage_parser = subparsers.add_parser("commit-stage", help="Commit a staged bundle at the human approval gate: verify freshness, stamp approval, write in construction order, flip the entry/queue/slots, validate, and rebuild projections.")
    commit_stage_parser.add_argument("stage", help="Stage id or stage directory path.")
    commit_stage_parser.add_argument("--creator-workspace", required=True, help="Path to the Creator Workspace.")

    complete_run_parser = subparsers.add_parser("complete-run", help="Derive the research-run record from its staged search plan and accumulated ledgers, then move the run folder into canonical research/runs/ (ADR 0042).")
    complete_run_parser.add_argument("run", help="Staged run directory or research run id.")
    complete_run_parser.add_argument("--creator-workspace", required=True, help="Path to the Creator Workspace.")
    material_group = complete_run_parser.add_mutually_exclusive_group(required=True)
    material_group.add_argument("--material-update", dest="material_update", action="store_true", help="The run produced a material research update.")
    material_group.add_argument("--no-material-update", dest="material_update", action="store_false", help="The run completed without a material update.")
    complete_run_parser.add_argument("--error", help="Mark the run failed with this error message.")
    complete_run_parser.add_argument("--finding", dest="finding_ids", nargs="+", metavar="FINDING_ID", help="Explicit finding ids the run produced (default: scan stable findings citing the run).")
    complete_run_parser.add_argument("--intelligence", dest="intelligence_updates", nargs="+", metavar="NOTE", help="Research intelligence update notes.")

    refresh_concept_research_parser = subparsers.add_parser(
        "refresh-concept-research",
        help=(
            "Append one canonical focused scheduled-needs run's evidence to "
            "a pre-existing scheduled Campaign Concept."
        ),
    )
    refresh_concept_research_parser.add_argument(
        "--concept", required=True, help="Scheduled Campaign Concept id."
    )
    refresh_concept_research_parser.add_argument(
        "--run", required=True, help="Completed focused research run id."
    )
    refresh_concept_research_parser.add_argument(
        "--creator-workspace", required=True, help="Path to the Creator Workspace."
    )

    refresh_parser = subparsers.add_parser("refresh-workspace", help="Session-open refresh (ADR 0042): validate all, then rebuild the recall index, semantic lookup, and content board in one invocation. Suitable as a background task when a creator session opens.")
    refresh_parser.add_argument("creator_workspace", help="Path to the Creator Workspace.")

    package_parser = subparsers.add_parser("register-output-package", help="Register an Output Package inside a project and mark it packaged.")
    package_parser.add_argument("output_package", help="Path to an Output Package JSON record.")
    package_parser.add_argument("--project", required=True, help="Path to the project directory.")
    package_parser.add_argument("--asset-root", help="Directory containing upload-ready files at the paths named in the package record.")

    published_parser = subparsers.add_parser("register-published-post", help="Register a Published Post Record inside a packaged project (records a human publication; never publishes).")
    published_parser.add_argument("record", help="Path to a PublishedPostRecord JSON file.")
    published_parser.add_argument("--project", required=True, help="Path to the project directory.")

    snapshot_parser = subparsers.add_parser("add-analytics-snapshot", help="Ingest one AnalyticsSnapshot JSON record for a published project (manual/derived entry).")
    snapshot_parser.add_argument("record", help="Path to an AnalyticsSnapshot JSON file.")
    snapshot_parser.add_argument("--project", required=True, help="Path to the project directory.")

    csv_parser = subparsers.add_parser("import-analytics-csv", help="Import AnalyticsSnapshots from the neutral InfluencerOS CSV template (all-or-nothing).")
    csv_parser.add_argument("csv_file", help="Path to a CSV file matching docs/templates/analytics/analytics-snapshot-template.csv.")
    csv_parser.add_argument("--project", required=True, help="Path to the project directory.")

    index_parser = subparsers.add_parser("rebuild-index", help="Rebuild one creator's rows in the local recall index (ADR 0010 projection).")
    index_parser.add_argument("creator_workspace", help="Path to the Creator Workspace.")
    index_parser.add_argument("--db", dest="db_path", help="Index database path; defaults to workspace-library/index/influencer-os.sqlite.")

    lookup_parser = subparsers.add_parser("rebuild-lookup", help="Rebuild one creator's semantic lookup projection (ADR 0011 FTS5 keyword leg).")
    lookup_parser.add_argument("creator_workspace", help="Path to the Creator Workspace.")
    lookup_parser.add_argument("--db", dest="db_path", help="Index database path; defaults to workspace-library/index/influencer-os.sqlite.")

    query_parser = subparsers.add_parser("query-lookup", help="Search one creator's semantic lookup projection; results cite source path and lines. Queries are never persisted.")
    query_parser.add_argument("creator_workspace", help="Path to the Creator Workspace (sets the creator scope).")
    query_parser.add_argument("terms", nargs="+", help="Search terms (matched as AND).")
    query_parser.add_argument("--db", dest="db_path", help="Index database path; defaults to workspace-library/index/influencer-os.sqlite.")
    query_parser.add_argument("--limit", type=int, default=8, help="Maximum matches to return (default 8).")

    pressure_parser = subparsers.add_parser("pressure-projection", help="Report the advisory per-platform Commercial Pressure projection over the current schedule horizon (ADR 0030/0032). Reporting only; never blocks approvals or creation.")
    pressure_parser.add_argument("creator_workspace", help="Path to the Creator Workspace.")

    campaign_status_parser = subparsers.add_parser("campaign-status", help="Report rebuildable Campaign and Concept evaluation summaries aggregated from canonical records; missing analytics stay unknown (ADR 0032).")
    campaign_status_parser.add_argument("creator_workspace", help="Path to the Creator Workspace.")

    board_parser = subparsers.add_parser("rebuild-board", help="Rebuild the Content Board projection from canonical records.")
    board_parser.add_argument("creator_workspace", help="Path to the Creator Workspace.")

    calendar_parser = subparsers.add_parser("rebuild-calendar", help="Rebuild the interactive content calendar projection from canonical records.")
    calendar_parser.add_argument("creator_workspace", help="Path to the Creator Workspace.")

    brand_board_parser = subparsers.add_parser("rebuild-brand-board", help="Populate the reusable personal brand board template from a creator's canonical brand spec.")
    brand_board_parser.add_argument("creator_workspace", help="Path to the Creator Workspace.")

    prune_parser = subparsers.add_parser("prune", help="Apply research retention rules (dry-run unless --apply).")
    prune_parser.add_argument("creator_workspace", help="Path to the Creator Workspace.")
    prune_parser.add_argument("--apply", action="store_true", help="Delete prunable records; without this flag prune only reports.")
    prune_parser.add_argument("--retention-days", type=int, default=DEFAULT_RETENTION_DAYS, help="Retention window for unreferenced evidence (default 30).")

    memory_parser = subparsers.add_parser("memory-write", help="Add one durable fact to a MEMORY.md file, deduplicated and capped.")
    memory_parser.add_argument("memory_file", help="Path to the MEMORY.md file.")
    memory_parser.add_argument("fact", help="One-line durable fact.")
    memory_parser.add_argument("--section", default=DEFAULT_MEMORY_SECTION, help="Target section heading, without the leading '## '.")

    connectors_parser = subparsers.add_parser("list-connectors", help="Show research-acquisition connectors and whether each is available given current API keys (ADR 0022).")
    connectors_parser.add_argument("--env-file", help="Path to a .env file; defaults to the repo .env.")

    providers_parser = subparsers.add_parser("list-providers", help="Show generation providers with capability, key presence, and approval model (ADR 0023; always exact_approval — key presence is never approval).")
    providers_parser.add_argument("--env-file", help="Path to a .env file; defaults to the repo .env.")

    gen_approval_parser = subparsers.add_parser("record-generation-approval", help="Record a human generation approval as a GenerationApprovalRecord (ADR 0023). Target is the project directory (project scope) or the creator workspace (reference-library scope).")
    gen_approval_parser.add_argument("target", help="Project directory (project scope) or creator workspace (reference scope).")
    gen_approval_parser.add_argument("record_file", help="Path to the GenerationApprovalRecord JSON to validate and record.")

    setup_approval_parser = subparsers.add_parser(
        "derive-setup-reference-approvals",
        help="Derive single-use reference approval records from an approved Visual Continuity Plan.",
    )
    setup_approval_parser.add_argument("creator_workspace")
    setup_approval_parser.add_argument("--provider", required=True)
    setup_approval_parser.add_argument("--model", required=True)
    setup_approval_parser.add_argument("--cost-note", required=True)

    avatar_approval_parser = subparsers.add_parser(
        "derive-avatar-approval",
        help="Derive the one system-authorized creator Avatar Image approval (ADR 0045).",
    )
    avatar_approval_parser.add_argument("creator_workspace")
    avatar_approval_parser.add_argument("--provider", required=True)
    avatar_approval_parser.add_argument("--model", required=True)
    avatar_approval_parser.add_argument("--cost-note", required=True)

    reference_dispatch_parser = subparsers.add_parser(
        "dispatch-reference-generation",
        help="Consume one approved creator-setup reference generation record.",
    )
    reference_dispatch_parser.add_argument("creator_workspace")
    reference_dispatch_parser.add_argument("approval_record_id")

    avatar_dispatch_parser = subparsers.add_parser(
        "dispatch-avatar-generation",
        help="Consume the one system-authorized creator Avatar Image approval.",
    )
    avatar_dispatch_parser.add_argument("creator_workspace")
    avatar_dispatch_parser.add_argument("approval_record_id")

    import_asset_parser = subparsers.add_parser("import-generated-asset", help="Import an externally generated or user-provided media file with full provenance (ADR 0023 slice 3): copies into generation/assets/ and writes the asset-manifest row, or routes into the Reference Library with --reference-asset.")
    import_asset_parser.add_argument("target", help="Project directory, or the creator workspace when using --reference-asset.")
    import_asset_parser.add_argument("source_file", help="Local media file to import.")
    import_asset_parser.add_argument("--asset-id", help="Manifest asset id (gen_asset_...); required for project imports.")
    import_asset_parser.add_argument("--asset-kind", choices=["image", "video", "audio", "render"], help="Asset kind; required for project imports.")
    import_asset_parser.add_argument("--origin", choices=["imported", "user_provided"], default="imported", help="Provenance origin (default imported).")
    import_asset_parser.add_argument("--filename", help="Destination filename (defaults to the source file name).")
    import_asset_parser.add_argument("--source", help="Where the asset came from (URL, tool export, operator note).")
    import_asset_parser.add_argument("--tool", dest="tool_or_provider", help="Tool or provider that produced the asset, when known.")
    import_asset_parser.add_argument("--license", dest="license_text", help="License or usage-rights statement; omitted = a license-unknown warning is recorded, never guessed.")
    import_asset_parser.add_argument("--creator", help="Original creator, when applicable.")
    import_asset_parser.add_argument("--attribution", help="Required attribution, when applicable.")
    import_asset_parser.add_argument("--warning", action="append", default=[], help="Provenance warning to record (repeatable).")
    import_asset_parser.add_argument("--notes", help="Free-form provenance notes.")
    import_asset_parser.add_argument("--reference-asset", help="Route the import to this Reference Library media asset id instead of a project. Prompt-package assets reject media imports; register resulting media as a separate asset.")
    import_asset_parser.add_argument("--approval-record", help="Reference route only: the gen_approval_ record that authorized the generation, when one exists.")

    fetch_parser = subparsers.add_parser("research-fetch", help="Run one research-acquisition connector fetch (ADR 0022; standing-approved by key presence) and emit a validated fetch-result JSON.")
    fetch_parser.add_argument("connector", nargs="?", choices=FETCH_MODES, help="Connector mode to run (omit with --plan).")
    fetch_parser.add_argument("target", nargs="?", help="Topic (reddit/x/youtube-search), page URL (firecrawl), profile URL (linkedin), or channel id/@handle (youtube-channel).")
    fetch_parser.add_argument("--plan", help="Path to a search-plan.json: fan out every connector-routable planned fetch concurrently (ADR 0042) instead of one connector/target.")
    fetch_parser.add_argument("--depth", choices=["quick", "default", "deep"], default="default", help="Discovery depth for reddit/x.")
    fetch_parser.add_argument("--days", type=int, default=30, help="Recency window in days (default 30).")
    fetch_parser.add_argument("--from-date", dest="from_date", help="Window start YYYY-MM-DD; overrides --days with --to-date.")
    fetch_parser.add_argument("--to-date", dest="to_date", help="Window end YYYY-MM-DD.")
    fetch_parser.add_argument("--max-posts", dest="max_posts", type=int, default=5, help="Max posts per LinkedIn profile (default 5).")
    fetch_parser.add_argument("--max-results", dest="max_results", type=int, default=10, help="Max YouTube search results or channel uploads (default 10).")
    fetch_parser.add_argument("--order", choices=["date", "relevance", "viewCount", "rating"], default="date", help="YouTube search order (default date).")
    fetch_parser.add_argument("--run-dir", required=True, help="Existing research run directory used to persist the per-run paid-call budget.")
    fetch_parser.add_argument("--out", help="Write the fetch-result JSON here instead of stdout.")
    fetch_parser.add_argument("--env-file", help="Path to a .env file; defaults to the repo .env.")

    incident_parser = subparsers.add_parser("log-incident", help="Append one friction event (rejection or incident) to the creator-events ledger (ADR 0025). Rejections must cite a Production Rubric criterion or pass --unclassified (cite-or-mint); verdicts are durable, rejected drafts stay ephemeral.")
    incident_parser.add_argument("creator_workspace", help="Path to the Creator Workspace.")
    incident_parser.add_argument("--type", dest="event_type", required=True, choices=["rejection", "incident"], help="Friction event type.")
    incident_parser.add_argument("--recurrence-key", required=True, help="Recurrence key for bracketing; must equal --criterion when one is cited.")
    incident_parser.add_argument("--message", required=True, help="One-line description of the friction; never the rejected material itself.")
    incident_parser.add_argument("--criterion", dest="criterion_id", help="Cited Production Rubric criterion id.")
    incident_parser.add_argument("--unclassified", action="store_true", help="Rejection whose reason cannot be articulated yet; counts toward the rubric-gap signal.")
    incident_parser.add_argument("--iteration-count", type=int, help="How many attempts this friction consumed.")
    incident_parser.add_argument("--project", dest="project_id", help="Project id the friction occurred in.")
    incident_parser.add_argument("--severity", default="important", choices=["info", "important", "urgent"], help="Event severity (default important).")
    incident_parser.add_argument("--source-type", default="skill", help="Event source type (default skill).")
    incident_parser.add_argument("--source-id", required=True, help="Event source id, e.g. the logging skill's name.")

    mint_parser = subparsers.add_parser("mint-criterion", help="Add one minted Production Rubric criterion (ADR 0025). Criterion ids double as recurrence keys and must be unique across the OS and creator rubrics.")
    mint_parser.add_argument("creator_workspace", help="Path to the Creator Workspace (also the duplicate-check scope).")
    mint_parser.add_argument("--id", dest="criterion_id", required=True, help="Criterion id (lowercase dotted, e.g. gen.image.hands_correct).")
    mint_parser.add_argument("--statement", required=True, help="The binary yes/no criterion statement.")
    mint_parser.add_argument("--os", dest="os_scope", action="store_true", help="Mint into the OS-scope rubric (context/production-rubric.json) instead of the creator rubric.")
    mint_parser.add_argument("--origin", default="rejection", choices=["seed", "rejection", "distillation"], help="Criterion origin (default rejection).")
    mint_parser.add_argument("--category", choices=["identity_consistency", "continuity_with_plan", "technical_conformance", "creator_boundary_compliance"], help="Optional quality-review category.")
    mint_parser.add_argument("--from-event", dest="minted_from_event_id", help="Ledger event id this criterion was distilled from.")
    mint_parser.add_argument("--notes", help="Optional criterion notes.")

    reflection_parser = subparsers.add_parser("check-reflection", help="Report unprocessed friction events, per-recurrence-key counts, and reflection-trigger crossings (ADR 0025). Reporting only; mutates nothing and never blocks.")
    reflection_parser.add_argument("creator_workspace", help="Path to the Creator Workspace.")

    claim_parser = subparsers.add_parser("record-improvement-claim", help="Record a validated ImprovementClaim under context/improvement-claims/ (ADR 0025). The claim's criterion and evidence events must resolve against the named creator workspace.")
    claim_parser.add_argument("claim_file", help="Path to an ImprovementClaim JSON file.")
    claim_parser.add_argument("--workspace-root", default=str(DEFAULT_CREATOR_WORKSPACE_ROOT), help="Creator workspace root directory.")

    check_claims_parser = subparsers.add_parser("check-claims", help="Report each improvement claim's mechanically computed violations-since count and confirm/refute suggestion (ADR 0025, D5). The human closes claims; this never mutates.")
    check_claims_parser.add_argument("--workspace-root", default=str(DEFAULT_CREATOR_WORKSPACE_ROOT), help="Creator workspace root directory.")

    learning_parser = subparsers.add_parser("log-learning", help="Append a dated learning entry: per-skill for OS learnings files, evidence-linked creator lessons for a Creator Workspace memory/learnings.md.")
    learning_parser.add_argument("learnings_file", help="Path to the learnings file.")
    learning_parser.add_argument("skill_name", help="Skill folder name for OS learnings, or the lesson topic (applies-to) for creator lessons.")
    learning_parser.add_argument("entry", help="One-line learning entry.")
    learning_parser.add_argument("--date", dest="entry_date", help="Entry date as YYYY-MM-DD; defaults to today.")
    learning_parser.add_argument("--evidence", nargs="+", metavar="RECORD_ID", help="Evidence record ids backing a creator lesson; required when the learnings file is a Creator Workspace memory/learnings.md (ADR 0008).")
    learning_parser.add_argument("--strength", choices=EVIDENCE_STRENGTHS, help="Evidence strength for a creator lesson; required with --evidence.")

    args = parser.parse_args(argv)

    try:
        if args.command == "validate":
            if args.target == "examples":
                results = validate_examples()
                print(f"Validated {len(results)} example records.")
                return 0
            if args.target == "record":
                if not args.path or not args.record_path:
                    raise ValueError("validate record requires a schema name and a record path")
                validate_file(args.path, args.record_path)
                print(f"Validated record against {args.path}: {args.record_path}")
                return 0
            if args.target == "workspace":
                if not args.path:
                    raise ValueError("validate workspace requires a workspace path")
                result = validate_creator_workspace(args.path)
                print(f"Validated creator workspace: {result['workspace_path']}")
                print(f"Checked {len(result['checked_paths'])} workspace paths.")
                for warning in result.get("warnings", []):
                    print(warning, file=sys.stderr)
                return 0
            if args.target == "project":
                if not args.path:
                    raise ValueError("validate project requires a project path")
                result = validate_project(args.path)
                print(f"Validated project: {result['project_path']}")
                print(f"Checked {len(result['checked_paths'])} project paths.")
                for warning in result.get("warnings", []):
                    print(warning, file=sys.stderr)
                return 0
            if args.target == "research":
                if not args.path:
                    raise ValueError("validate research requires a creator workspace path")
                result = validate_research(args.path)
                print(f"Validated research state: {result['workspace_path']}")
                print(f"Checked {len(result['checked_paths'])} research records.")
                for warning in result.get("warnings", []):
                    print(warning, file=sys.stderr)
                return 0
            if args.target == "queue":
                if not args.path:
                    raise ValueError("validate queue requires a creator workspace path")
                result = validate_queue(args.path)
                print(f"Validated content opportunity queue: {result['manifest_path']}")
                print(f"Checked {result['entry_count']} queue entries.")
                for warning in result.get("warnings", []):
                    print(warning, file=sys.stderr)
                return 0
            if args.target == "board":
                if not args.path:
                    raise ValueError("validate board requires a creator workspace path")
                result = validate_board(args.path)
                print(f"Validated content board: {result['board_path']}")
                print(f"Checked {result['card_count']} board cards.")
                return 0
            if args.target == "calendar":
                if not args.path:
                    raise ValueError("validate calendar requires a creator workspace path")
                result = validate_calendar(args.path)
                print(f"Validated content calendar: {result['calendar_path']}")
                print(f"Checked {result['post_count']} scheduled posts.")
                return 0
            if args.target == "brand-board":
                if not args.path:
                    raise ValueError("validate brand-board requires a creator workspace path")
                result = validate_brand_board(args.path)
                print(f"Validated personal brand board: {result['board_path']}")
                return 0
            if args.target == "all":
                if not args.path:
                    raise ValueError("validate all requires a creator workspace path")
                result = validate_all(args.path)
                print(f"Validated full chain: {result['workspace_path']}")
                for layer, summary in result["layers"]:
                    print(f"  {layer}: {summary}")
                for layer, reason in result["skipped"]:
                    print(f"  {layer}: skipped ({reason})")
                print(
                    f"Layers passed: {len(result['layers'])}; "
                    f"skipped: {len(result['skipped'])}; "
                    f"warnings: {len(result['warnings'])}."
                )
                for warning in result["warnings"]:
                    print(warning, file=sys.stderr)
                return 0
            return 0

        if args.command == "init-creator":
            workspace_dir = init_creator(
                args.creator_workspace,
                workspace_root=Path(args.workspace_root),
            )
            print(f"Initialized creator workspace: {workspace_dir}")
            print("Next phase: author creator profile and reference library")
            return 0

        if args.command == "sync-creator-runtime":
            result = sync_creator_runtime(args.creator_workspace)
            print(f"Synced creator runtime: {result['workspace_path']}")
            print(f"Synced {len(result['synced_skills'])} skills into {result['skills_path']}")
            print(f"Preserved {result['preserved_overrides']} local overrides")
            return 0

        if args.command == "migrate-campaign-model":
            result = migrate_campaign_model(args.creator_workspace)
            print(f"Migrated to the campaign model: {result['workspace_path']}")
            print(f"Changed {len(result['changed_paths'])} records.")
            for path in result["changed_paths"]:
                print(f"- {path}")
            return 0

        if args.command == "migrate-content-series":
            result = migrate_content_series(args.creator_workspace)
            print(f"Migrated content series naming: {result['workspace_path']}")
            print(f"Changed {len(result['changed_paths'])} records.")
            for path in result["changed_paths"]:
                print(f"- {path}")
            return 0

        if args.command == "migrate-visual-foundation":
            result = migrate_visual_foundation(args.creator_workspace)
            print(f"Migrated visual foundation: {result['workspace_path']}")
            print(f"Changed {len(result['changed_paths'])} records or projections.")
            for path in result["changed_paths"]:
                print(f"- {path}")
            return 0

        if args.command == "sync-codex-skills":
            kwargs = {"target_root": args.target_root} if args.target_root else {}
            result = sync_codex_skills(**kwargs)
            print(
                f"Synced Codex skills: {len(result['synced_skills'])} into "
                f"{result['target_root']}"
            )
            print(
                f"Backed up {result['backed_up_skills']} skills; preserved "
                f"{result['preserved_overrides']} local overrides."
            )
            return 0

        if args.command == "check-codex-skills":
            kwargs = {"target_root": args.target_root} if args.target_root else {}
            result = validate_codex_skill_drift(**kwargs)
            print(
                f"Codex skill copies match {result['skill_count']} repository "
                f"sources in {result['target_root']}"
            )
            return 0

        if args.command == "import-intake":
            result = import_intake(
                args.creator_workspace,
                args.source_file,
                source_type=args.source_type,
                notes=args.notes,
                source_id=args.source_id,
                imported_on=args.imported_on,
            )
            print(f"Imported intake {result['source_id']} -> {result['destination']}")
            print("Next phase: derive foundation drafts (create-influencer)")
            return 0

        if args.command == "set-intake-status":
            result = set_intake_status(args.creator_workspace, args.source_id, args.status)
            print(
                f"Set intake {result['source_id']} extraction status: "
                f"{result['previous_status']} -> {result['extraction_status']}"
            )
            return 0

        if args.command == "init-project":
            require_production_ready(args.creator_workspace)
            project_dir = init_project(
                args.project,
                creator_workspace=Path(args.creator_workspace),
            )
            print(f"Initialized project: {project_dir}")
            print("Next phase: add selected idea and production plan")
            return 0

        if args.command == "scaffold":
            from influencer_os.campaigns import (
                scaffold_campaign,
                scaffold_campaign_concept,
                scaffold_content_opportunity,
            )
            from influencer_os.cadence import (
                scaffold_foundation_revision,
                scaffold_quarter_plan,
                scaffold_strategy_revision,
            )
            from influencer_os.constructors import (
                scaffold_project,
                scaffold_review_record,
                scaffold_search_plan,
            )

            if args.list_types:
                for name, description in sorted(SCAFFOLD_TYPES.items()):
                    print(f"- {name}: {description}")
                return 0
            if not args.record_type or not args.seed or not args.creator_workspace:
                raise ValueError(
                    "scaffold requires a record type, --seed, and "
                    "--creator-workspace (or --list)"
                )
            if args.record_type == "project":
                result = scaffold_project(args.seed, args.creator_workspace)
                print(
                    f"Scaffolded project {result['project_id']}: "
                    f"{result['project_dir']}"
                )
            elif args.record_type == "campaign":
                result = scaffold_campaign(args.seed, args.creator_workspace)
                print(
                    f"Scaffolded draft campaign {result['campaign_id']}: "
                    f"{result['campaign_path']}"
                )
            elif args.record_type == "campaign-concept":
                result = scaffold_campaign_concept(
                    args.seed, args.creator_workspace
                )
                print(
                    f"Scaffolded draft concept {result['campaign_concept_id']}: "
                    f"{result['concept_path']}"
                )
            elif args.record_type == "content-opportunity":
                result = scaffold_content_opportunity(
                    args.seed, args.creator_workspace
                )
                print(
                    f"Scaffolded content opportunity "
                    f"{result['content_opportunity_id']}: {result['entry_path']}"
                )
            elif args.record_type == "review-record":
                result = scaffold_review_record(args.seed, args.creator_workspace)
                print(
                    f"Scaffolded Concept Review {result['review_record_id']}: "
                    f"{result['review_path']}"
                )
            elif args.record_type == "quarter-plan":
                result = scaffold_quarter_plan(args.seed, args.creator_workspace)
                print(
                    f"Scaffolded Quarter Plan {result['id']}: "
                    f"{result['path']}"
                )
            elif args.record_type == "foundation-revision":
                result = scaffold_foundation_revision(
                    args.seed, args.creator_workspace
                )
                print(
                    f"Scaffolded Foundation Revision {result['id']}: "
                    f"{result['path']}"
                )
            elif args.record_type == "strategy-revision":
                result = scaffold_strategy_revision(
                    args.seed, args.creator_workspace
                )
                print(
                    f"Scaffolded Strategy Revision {result['id']}: "
                    f"{result['path']}"
                )
            else:
                result = scaffold_search_plan(args.seed, args.creator_workspace)
                print(
                    f"Scaffolded search plan for {result['research_run_id']}: "
                    f"{result['search_plan_path']}"
                )
                print(f"Staged in-flight run directory: {result['run_dir']}")
                print(
                    "Next: research-fetch --plan "
                    f"{result['search_plan_path']} --run-dir "
                    f"{result['run_dir']}; complete-run when the run finishes."
                )
            return 0

        if args.command == "stage":
            from influencer_os.staging import stage_concept_approval

            result = stage_concept_approval(
                args.seed, args.creator_workspace, args.concept
            )
            print(f"Staged approval bundle {result['stage_id']}: {result['stage_dir']}")
            print(f"- approval: {result['approval']['concept_approval_id']}")
            for project in result["projects"]:
                print(f"- project: {project['project_id']} ({project['project_slug']})")
            for warning in result["warnings"]:
                print(warning, file=sys.stderr)
            print("Present the approval package from the staged records; on approval run commit-stage.")
            return 0

        if args.command == "commit-stage":
            from influencer_os.staging import commit_stage

            result = commit_stage(args.stage, args.creator_workspace)
            print(f"Committed concept approval {result['concept_approval_id']}: {result['approval_path']}")
            for project_dir in result["project_dirs"]:
                print(f"- project: {project_dir}")
            for warning in result["warnings"]:
                print(warning, file=sys.stderr)
            return 0

        if args.command == "complete-run":
            from influencer_os.constructors import complete_run

            result = complete_run(
                args.run,
                args.creator_workspace,
                material_update=args.material_update,
                error=args.error,
                finding_ids=args.finding_ids,
                intelligence_updates=args.intelligence_updates,
            )
            outputs = result["outputs"]
            print(
                f"Completed research run {result['research_run_id']} "
                f"({result['run_status']}): {result['run_dir']}"
            )
            print(
                f"- outputs: {len(outputs['evidence_ids'])} evidence, "
                f"{len(outputs['metric_snapshot_ids'])} metric snapshots, "
                f"{len(outputs['finding_ids'])} findings, "
                f"{len(outputs['content_opportunity_ids'])} opportunities"
            )
            return 0

        if args.command == "refresh-concept-research":
            from influencer_os.research import refresh_campaign_concept_research

            result = refresh_campaign_concept_research(
                args.creator_workspace, args.concept, args.run
            )
            print(
                f"Refreshed Campaign Concept {result['campaign_concept_id']} "
                f"from {result['research_run_id']}: {result['concept_path']}"
            )
            print(
                f"- added {len(result['evidence_refs_added'])} evidence refs "
                f"for slots {', '.join(result['focused_slot_ids'])}"
            )
            return 0

        if args.command == "refresh-workspace":
            failures = 0
            try:
                result = validate_all(args.creator_workspace)
                print(f"[ok] validate all ({result['project_count']} projects)")
                for warning in result.get("warnings", []):
                    print(warning, file=sys.stderr)
            except (ValidationError, FileNotFoundError, ValueError) as exc:
                failures += 1
                print(f"[failed] validate all: {exc}", file=sys.stderr)
            rebuilds = (
                ("rebuild-index", lambda: rebuild_index(args.creator_workspace)),
                ("rebuild-lookup", lambda: rebuild_lookup(args.creator_workspace)),
                ("rebuild-board", lambda: rebuild_board(args.creator_workspace)),
            )
            for name, rebuild in rebuilds:
                try:
                    rebuild()
                    print(f"[ok] {name}")
                except FileNotFoundError as exc:
                    # A projection whose source records do not exist yet is a
                    # lifecycle skip, not a failure (full_validation.py rules).
                    print(f"[skipped] {name}: {exc}")
                except (ValidationError, ValueError) as exc:
                    failures += 1
                    print(f"[failed] {name}: {exc}", file=sys.stderr)
            return 1 if failures else 0

        if args.command == "register-output-package":
            result = register_output_package(
                args.project,
                args.output_package,
                asset_root=args.asset_root,
            )
            print(f"Registered output package: {result['output_package_path']}")
            print(f"Copied {len(result['copied_assets'])} upload-ready assets.")
            print("Next phase: manual publication record when published.")
            return 0

        if args.command == "register-published-post":
            result = register_published_post(args.project, args.record)
            print(f"Registered published post record: {result['record_path']}")
            print(f"Project status: {result['project_status']}")
            print("Next phase: analytics snapshots for this published post.")
            return 0

        if args.command == "add-analytics-snapshot":
            result = add_analytics_snapshot(args.project, args.record)
            print(f"Ingested analytics snapshot: {result['snapshot_path']}")
            print(f"Hours since publish: {result['hours_since_publish']}")
            print("Next phase: performance summary once enough snapshots exist.")
            return 0

        if args.command == "import-analytics-csv":
            results = import_analytics_csv(args.project, args.csv_file)
            print(f"Imported {len(results)} analytics snapshots:")
            for result in results:
                print(f"- {result['snapshot_path']}")
            print("Next phase: performance summary once enough snapshots exist.")
            return 0

        if args.command == "update-creators":
            results = update_creators(workspace_root=Path(args.workspace_root))
            print(f"Updated {len(results)} creator workspaces.")
            for result in results:
                print(
                    f"- {result['workspace_path']}: {len(result['synced_skills'])} skills synced, "
                    f"{result['preserved_overrides']} overrides preserved, "
                    f"{result['backed_up_skills']} skill folders backed up"
                )
            return 0

        if args.command == "rebuild-index":
            result = rebuild_index(args.creator_workspace, db_path=args.db_path)
            print(
                f"Rebuilt recall index rows for {result['creator_slug']}: "
                f"{result['row_count']} records"
            )
            print(f"Index database: {result['db_path']}")
            return 0

        if args.command == "rebuild-lookup":
            result = rebuild_lookup(args.creator_workspace, db_path=args.db_path)
            print(
                f"Rebuilt lookup projection for {result['creator_slug']}: "
                f"{result['chunk_count']} chunks from {result['source_count']} "
                f"sources ({result['unchanged_sources']} unchanged)"
            )
            print(f"Index database: {result['db_path']}")
            return 0

        if args.command == "query-lookup":
            hits = query_lookup(
                args.creator_workspace, args.terms,
                db_path=args.db_path, limit=args.limit,
            )
            if not hits:
                print("No matches.")
                return 0
            for hit in hits:
                if hit["start_line"] is not None:
                    locator = f"{hit['source_path']}:{hit['start_line']}-{hit['end_line']}"
                else:
                    locator = hit["source_path"]
                heading = f" [{hit['heading']}]" if hit["heading"] else ""
                snippet = " ".join(hit["content"].split())
                if len(snippet) > 160:
                    snippet = snippet[:157] + "..."
                print(f"{hit['final_score']:.4f} {locator}{heading}: {snippet}")
            return 0

        if args.command == "pressure-projection":
            from influencer_os.campaigns import derive_pressure_projection

            result = derive_pressure_projection(args.creator_workspace)
            coverage = result["known_coverage"]
            print(
                f"Pressure projection: {result['known_slot_count']} known "
                f"slot(s), {result['unresolved_slot_count']} unresolved "
                f"(coverage {coverage:.0%})" if coverage is not None else
                "Pressure projection: no calendar slots in the horizon"
            )
            for platform, indicator in result["platforms"].items():
                counts = indicator["tier_counts"]
                tier_text = ", ".join(
                    f"{tier}={counts[tier]}" for tier in result["tiers"]
                )
                share = indicator["high_share"]
                print(
                    f"- {platform}: {indicator['known_touches']} touch(es), "
                    f"score {indicator['score']}, high share {share:.0%} "
                    f"({tier_text})"
                )
                if indicator["advisory_warning"]:
                    print(
                        f"  advisory: {platform} known high-pressure share "
                        "exceeds 25% (guides, never gates)",
                        file=sys.stderr,
                    )
            if result["unresolved_slot_ids"]:
                print(
                    "Unresolved pre-Project slots (never counted as low): "
                    + ", ".join(result["unresolved_slot_ids"])
                )
            return 0

        if args.command == "campaign-status":
            from influencer_os.campaigns import derive_campaign_evaluation

            result = derive_campaign_evaluation(args.creator_workspace)
            if not result["campaigns"]:
                print("No campaigns yet.")
                return 0
            for campaign_id, summary in result["campaigns"].items():
                print(
                    f"{campaign_id} [{summary['status']}] "
                    f"{summary['objective']}: {summary['name']}"
                )
                print(f"  outcome: {summary['measurable_outcome']}")
                print(f"  measured progress: {summary['measured_progress']}")
                if summary["past_target"]:
                    print(
                        "  advisory: past target end date "
                        f"{summary['target_end_date']} (retarget in the next "
                        "Quarterly Planning Cycle)"
                    )
                for concept_id, concept in summary["concepts"].items():
                    pressure_text = ", ".join(
                        f"{tier}={count}"
                        for tier, count in sorted(
                            concept["pressure_tier_counts"].items()
                        )
                    ) or "none derived"
                    print(
                        f"  - {concept_id} [{concept['status']}] "
                        f"{concept['primary_commercial_function']}: "
                        f"{concept['project_count']} project(s), "
                        f"{concept['published_project_count']} published; "
                        f"pressure {pressure_text}"
                    )
            return 0

        if args.command == "rebuild-board":
            result = rebuild_board(args.creator_workspace)
            print(
                f"Rebuilt content board: {result['card_count']} cards "
                f"({result['opportunity_cards']} opportunities, {result['project_cards']} projects)"
            )
            print(f"Board: {result['board_path']}")
            return 0

        if args.command == "rebuild-calendar":
            result = rebuild_calendar(args.creator_workspace)
            count = result["post_count"]
            print(f"Rebuilt content calendar: {count} scheduled {'post' if count == 1 else 'posts'}")
            print(f"Calendar: {result['calendar_path']}")
            return 0

        if args.command == "rebuild-brand-board":
            result = rebuild_brand_board(args.creator_workspace)
            print(f"Rebuilt personal brand board: {result['board_path']}")
            return 0

        if args.command == "prune":
            result = prune_research(
                args.creator_workspace,
                retention_days=args.retention_days,
                apply=args.apply,
            )
            mode = "Pruned" if result["applied"] else "Prunable (dry run)"
            print(
                f"{mode}: {result['evidence_pruned']} evidence records, "
                f"{result['metric_snapshots_pruned']} metric snapshots "
                f"(cutoff {result['cutoff']}, retention {result['retention_days']} days)"
            )
            for run in result["runs"]:
                print(f"- {run['research_run_id']}: {', '.join(run['pruned_evidence_ids'])}")
            if not result["runs"]:
                print("Nothing to prune.")
            elif not result["applied"]:
                print("Dry run: pass --apply to delete.")
            return 0

        if args.command == "memory-write":
            result = write_memory_fact(args.memory_file, args.fact, section=args.section)
            if result["status"] == "duplicate":
                print("Already saved; no change.")
            else:
                print(f"Saved memory fact ({result['bytes_used']}/{result['byte_cap']} bytes).")
            return 0

        if args.command == "record-generation-approval":
            from influencer_os.generation import record_generation_approval

            destination = record_generation_approval(args.target, args.record_file)
            print(f"Recorded generation approval: {destination}")
            return 0

        if args.command == "derive-setup-reference-approvals":
            from influencer_os.generation import derive_setup_reference_approvals

            destinations = derive_setup_reference_approvals(
                args.creator_workspace,
                provider_id=args.provider,
                model=args.model,
                cost_note=args.cost_note,
            )
            print(f"Derived {len(destinations)} setup reference approvals.")
            for destination in destinations:
                print(f"- {destination}")
            return 0

        if args.command == "derive-avatar-approval":
            from influencer_os.generation import derive_avatar_approval

            destinations = derive_avatar_approval(
                args.creator_workspace,
                provider_id=args.provider,
                model=args.model,
                cost_note=args.cost_note,
            )
            print(f"Derived Avatar Image approval: {destinations[0]}")
            return 0

        if args.command == "dispatch-reference-generation":
            from influencer_os.providers.dispatch import dispatch_reference_generation

            calls = dispatch_reference_generation(
                args.creator_workspace, args.approval_record_id
            )
            print(f"Generated {len(calls)} reference asset.")
            return 0

        if args.command == "dispatch-avatar-generation":
            from influencer_os.providers.dispatch import dispatch_avatar_generation

            calls = dispatch_avatar_generation(
                args.creator_workspace, args.approval_record_id
            )
            print(f"Generated {len(calls)} Avatar Image.")
            return 0

        if args.command == "import-generated-asset":
            from influencer_os.generation import (
                import_generated_asset,
                import_reference_asset,
            )

            if args.reference_asset:
                destination = import_reference_asset(
                    args.target,
                    args.source_file,
                    args.reference_asset,
                    origin=args.origin,
                    approval_record_id=args.approval_record,
                )
            else:
                if not args.asset_id or not args.asset_kind:
                    raise ValueError(
                        "import-generated-asset requires --asset-id and --asset-kind for project imports"
                    )
                destination = import_generated_asset(
                    args.target,
                    args.source_file,
                    args.asset_id,
                    args.asset_kind,
                    origin=args.origin,
                    filename=args.filename,
                    source=args.source,
                    tool_or_provider=args.tool_or_provider,
                    license_text=args.license_text,
                    creator=args.creator,
                    attribution=args.attribution,
                    warnings=args.warning,
                    notes=args.notes,
                )
            print(f"Imported generated asset: {destination}")
            return 0

        if args.command == "list-providers":
            from influencer_os.connectors import env as connector_env
            from influencer_os.providers import registry as provider_registry
            config = connector_env.get_config(
                env_path=Path(args.env_file) if args.env_file else None
            )
            rows = provider_registry.provider_status(config)
            available = sum(1 for r in rows if r["available"])
            print(f"Generation providers: {available}/{len(rows)} available")
            print("Approval model: exact_approval for every provider — key presence is never generation approval (ADR 0023).")
            if connector_env.paid_connectors_disabled(config):
                print("(generation dispatch is OFF via INFLUENCER_OS_DISABLE_PAID_CONNECTORS)")
            for r in rows:
                mark = "available" if r["available"] else "unavailable"
                capabilities = ",".join(r["capabilities"])
                print(f"- {r['provider_id']} [{capabilities}] ({mark}: {r['reason']}) approval_model={r['approval_model']} — {r['summary']}")
            return 0

        if args.command == "list-connectors":
            from influencer_os.connectors import env as connector_env, registry
            config = connector_env.get_config(
                env_path=Path(args.env_file) if args.env_file else None
            )
            rows = registry.connector_status(config)
            available = sum(1 for r in rows if r["available"])
            print(f"Research-acquisition connectors: {available}/{len(rows)} available")
            if connector_env.paid_connectors_disabled(config):
                print("(paid connector tier is OFF via INFLUENCER_OS_DISABLE_PAID_CONNECTORS)")
            for r in rows:
                mark = "available" if r["available"] else "unavailable"
                platform = r["platform"] or "web"
                print(f"- [{mark}] {r['connector']} ({r['adapter_id']}, {platform}) - {r['reason']}")
            return 0

        if args.command == "research-fetch":
            import json as json_module

            from influencer_os.connectors import env as connector_env, fetch as connector_fetch, http as connector_http
            from influencer_os.validation import validate_record as validate_record_fn

            config = connector_env.get_config(
                env_path=Path(args.env_file) if args.env_file else None
            )
            run_dir = Path(args.run_dir)

            if args.plan:
                from influencer_os.connectors import plan_fetch
                from influencer_os.validation import load_json as load_json_fn

                plan = load_json_fn(args.plan)
                budget = plan_fetch.locked_budget_from(
                    _load_connector_budget(run_dir, config["MAX_CALLS"])
                )
                try:
                    summary = plan_fetch.fetch_for_plan(
                        plan,
                        run_dir,
                        config,
                        budget,
                        depth=args.depth,
                        from_date=args.from_date,
                        to_date=args.to_date,
                        days=args.days,
                        max_posts=args.max_posts,
                        max_results=args.max_results,
                        order=args.order,
                    )
                finally:
                    _save_connector_budget(run_dir, budget)
                for outcome in summary["jobs"]:
                    job = outcome["job"]
                    if outcome["status"] == "fetched":
                        print(
                            f"[fetched] {job['id']} via {job['mode']}: "
                            f"{len(outcome['result']['candidates'])} candidate(s) "
                            f"-> {outcome['result_path']}",
                            file=sys.stderr,
                        )
                    else:
                        print(
                            f"[{outcome['status']}] {job['id']} via "
                            f"{job['mode']}: {outcome['error']}",
                            file=sys.stderr,
                        )
                for skip in summary["skipped"]:
                    print(f"[skipped] {skip['id']}: {skip['reason']}", file=sys.stderr)
                print(
                    f"Plan fan-out: {summary['fetched']}/{len(summary['jobs'])} "
                    f"fetches completed, {budget.used}/{budget.max_calls} paid "
                    "call(s) used."
                )
                return 1 if summary["jobs"] and not summary["fetched"] else 0

            if not args.connector or not args.target:
                raise ValueError(
                    "research-fetch needs a connector and target, or --plan"
                )
            budget = _load_connector_budget(run_dir, config["MAX_CALLS"])
            try:
                result = connector_fetch.fetch_for_mode(
                    args.connector,
                    args.target,
                    config,
                    budget,
                    depth=args.depth,
                    from_date=args.from_date,
                    to_date=args.to_date,
                    days=args.days,
                    max_posts=args.max_posts,
                    max_results=args.max_results,
                    order=args.order,
                )
            except connector_fetch.ConnectorUnavailable as exc:
                _save_connector_budget(run_dir, budget)
                print(f"error: {exc}", file=sys.stderr)
                print("Run `python3 -m influencer_os list-connectors` to see availability.", file=sys.stderr)
                return 1
            except connector_http.HTTPError as exc:
                _save_connector_budget(run_dir, budget)
                # A provider fault (bad/expired key -> 401/403, 5xx after retries,
                # or a malformed body) must degrade to a clean error, not a
                # traceback: HTTPError is not in the outer handler's tuple.
                print(f"error: provider request failed: {exc}", file=sys.stderr)
                return 1

            _save_connector_budget(run_dir, budget)
            validate_record_fn("research-fetch-result", result)
            payload = json_module.dumps(result, indent=2)
            if args.out:
                Path(args.out).write_text(payload + "\n")
                print(f"Wrote fetch result: {args.out}", file=sys.stderr)
            else:
                print(payload)
            print(
                f"{result['connector']}: {len(result['candidates'])} candidate(s), "
                f"{result['calls_used']} paid call(s) used, status {result['status']}",
                file=sys.stderr,
            )
            return 0

        if args.command == "log-incident":
            from influencer_os.rubric import log_incident

            result = log_incident(
                args.creator_workspace,
                event_type=args.event_type,
                recurrence_key=args.recurrence_key,
                message=args.message,
                source_id=args.source_id,
                criterion_id=args.criterion_id,
                unclassified=args.unclassified,
                iteration_count=args.iteration_count,
                project_id=args.project_id,
                severity=args.severity,
                source_type=args.source_type,
            )
            print(f"Logged {args.event_type} {result['event_id']} -> {result['ledger_path']}")
            return 0

        if args.command == "mint-criterion":
            from influencer_os.rubric import mint_criterion

            result = mint_criterion(
                args.creator_workspace,
                criterion_id=args.criterion_id,
                statement=args.statement,
                os_scope=args.os_scope,
                origin=args.origin,
                category=args.category,
                minted_from_event_id=args.minted_from_event_id,
                notes=args.notes,
            )
            print(f"Minted criterion {result['criterion_id']} -> {result['rubric_path']}")
            return 0

        if args.command == "check-reflection":
            from influencer_os.rubric import reflection_report

            report = reflection_report(args.creator_workspace)
            thresholds = report["thresholds"]
            print(
                f"Unprocessed friction events: {report['unprocessed_count']} "
                f"(threshold {thresholds['unprocessed_n']}); "
                f"unclassified: {report['unclassified_count']} "
                f"(threshold {thresholds['unclassified_n']}); "
                f"processed: {report['claimed_count']} across "
                f"{report['run_count']} reflection run(s)"
            )
            for key, count in sorted(report["recurrence_counts"].items()):
                print(f"- {key}: {count} (threshold {thresholds['recurrence_k']})")
            for warning in report["warnings"]:
                print(warning)
            if not report["warnings"]:
                print("No reflection thresholds crossed.")
            return 0

        if args.command == "record-improvement-claim":
            from influencer_os.claims import record_claim

            result = record_claim(args.claim_file, workspace_root=Path(args.workspace_root))
            print(f"Recorded improvement claim: {result['claim_path']}")
            print("Verify with check-claims after subsequent runs; a human closes the claim.")
            return 0

        if args.command == "check-claims":
            from influencer_os.claims import check_claims

            reports = check_claims(workspace_root=Path(args.workspace_root))
            if not reports:
                print("No improvement claims recorded.")
                return 0
            for report in reports:
                if report["resolution"] == "workspace_missing":
                    print(
                        f"- {report['claim_id']} [{report['status']}] "
                        f"{report['criterion_id']} -> workspace missing; resolution skipped"
                    )
                else:
                    print(
                        f"- {report['claim_id']} [{report['status']}] "
                        f"{report['criterion_id']}: {report['violations_since']} violation(s) "
                        f"since created (max {report['max_violations']}) "
                        f"-> suggest {report['suggestion']}"
                    )
            return 0

        if args.command == "log-learning":
            entry_date = args.entry_date or datetime.date.today().isoformat()
            workspace_dir = creator_lessons_workspace(args.learnings_file)
            if workspace_dir is not None:
                result = append_creator_lesson(
                    workspace_dir,
                    topic=args.skill_name,
                    lesson=args.entry,
                    evidence_ids=args.evidence,
                    strength=args.strength,
                    entry_date=entry_date,
                )
                if result["status"] == "duplicate":
                    print("Creator lesson already recorded; no change.")
                else:
                    print(f"Logged creator lesson under {args.skill_name}.")
                return 0
            if args.evidence or args.strength:
                raise ValueError(
                    "--evidence/--strength mark creator lessons and apply only to a "
                    "Creator Workspace memory/learnings.md (beside creator-workspace.json)"
                )
            result = append_skill_learning(args.learnings_file, args.skill_name, args.entry, entry_date)
            if result["status"] == "duplicate":
                print("Learning already recorded; no change.")
            else:
                print(f"Logged learning for {args.skill_name}.")
            return 0
    except (ValidationError, FileExistsError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    parser.error(f"Unhandled command: {args.command}")


def _connector_budget_path(run_dir):
    return Path(run_dir) / "connector-budget.json"


def _load_connector_budget(run_dir, max_calls):
    from influencer_os.connectors import env as connector_env

    run_dir = Path(run_dir)
    if not run_dir.exists() or not run_dir.is_dir():
        raise FileNotFoundError(f"Missing research run directory: {run_dir}")
    if run_dir.is_symlink():
        raise ValueError(f"Research run directory must not be a symlink: {run_dir}")
    budget_path = _connector_budget_path(run_dir)
    if budget_path.is_symlink():
        raise ValueError(f"Connector budget file must not be a symlink: {budget_path}")

    calls_used = 0
    if budget_path.exists():
        try:
            record = json.loads(budget_path.read_text())
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid connector budget file {budget_path}: {exc}") from None
        calls_used = record.get("calls_used", 0)
        stored_max = record.get("max_calls", max_calls)
        if not isinstance(calls_used, int) or calls_used < 0:
            raise ValueError(f"Invalid calls_used in connector budget: {calls_used!r}")
        if not isinstance(stored_max, int) or stored_max < 0:
            raise ValueError(f"Invalid max_calls in connector budget: {stored_max!r}")
        max_calls = min(max_calls, stored_max)

    budget = connector_env.CallBudget(max_calls)
    budget.used = calls_used
    return budget


def _save_connector_budget(run_dir, budget):
    write_json_atomic(
        _connector_budget_path(run_dir),
        {
            "max_calls": budget.max_calls,
            "calls_used": budget.used,
            "remaining_calls": budget.remaining(),
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        },
    )


if __name__ == "__main__":
    raise SystemExit(main())
