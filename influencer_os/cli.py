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
from influencer_os.full_validation import validate_all
from influencer_os.analytics import import_analytics_csv
from influencer_os.projects import init_project, validate_project
from influencer_os.projects import add_analytics_snapshot, register_output_package, register_published_post
from influencer_os.prune import DEFAULT_RETENTION_DAYS, prune_research
from influencer_os.recall_index import rebuild_index
from influencer_os.research import validate_queue, validate_research
from influencer_os.semantic_lookup import query_lookup, rebuild_lookup
from influencer_os.runs import DEFAULT_WORKSPACE, init_run
from influencer_os.validation import ValidationError, validate_examples, validate_file


def main(argv=None):
    parser = argparse.ArgumentParser(prog="influencer-os")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate repository records.")
    validate_parser.add_argument("target", choices=["examples", "workspace", "project", "record", "research", "queue", "board", "all"], help="Validation target ('all' composes workspace, research, queue, board, and every project — the alpha release gate).")
    validate_parser.add_argument("path", nargs="?", help="Path for workspace/project/research/queue/board validation, or schema name for record validation.")
    validate_parser.add_argument("record_path", nargs="?", help="Record path for record validation.")

    init_parser = subparsers.add_parser("init-run", help="Initialize a dry-run workspace from a creator profile.")
    init_parser.add_argument("creator_profile", help="Path to a Creator Profile JSON file.")
    init_parser.add_argument("--workspace", default=str(DEFAULT_WORKSPACE), help="Run workspace directory.")
    init_parser.add_argument("--run-id", help="Optional explicit run id.")

    creator_parser = subparsers.add_parser("init-creator", help="Initialize a Creator Workspace from a workspace manifest.")
    creator_parser.add_argument("creator_workspace", help="Path to a Creator Workspace JSON manifest.")
    creator_parser.add_argument("--workspace-root", default=str(DEFAULT_CREATOR_WORKSPACE_ROOT), help="Creator workspace root directory.")

    sync_creator_parser = subparsers.add_parser("sync-creator-runtime", help="Refresh copied runtime skills inside a Creator Workspace.")
    sync_creator_parser.add_argument("creator_workspace", help="Path to the Creator Workspace.")

    update_creators_parser = subparsers.add_parser("update-creators", help="Refresh copied runtime skills across every Creator Workspace under a root.")
    update_creators_parser.add_argument("--workspace-root", default=str(DEFAULT_CREATOR_WORKSPACE_ROOT), help="Creator workspace root directory.")

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

    board_parser = subparsers.add_parser("rebuild-board", help="Rebuild the Content Board projection from canonical records.")
    board_parser.add_argument("creator_workspace", help="Path to the Creator Workspace.")

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
    import_asset_parser.add_argument("--reference-asset", help="Route the import to this Reference Library asset id instead of a project.")
    import_asset_parser.add_argument("--approval-record", help="Reference route only: the gen_approval_ record that authorized the generation, when one exists.")

    fetch_parser = subparsers.add_parser("research-fetch", help="Run one research-acquisition connector fetch (ADR 0022; standing-approved by key presence) and emit a validated fetch-result JSON.")
    fetch_parser.add_argument("connector", choices=["reddit", "x", "firecrawl", "linkedin", "youtube-search", "youtube-channel"], help="Connector to run.")
    fetch_parser.add_argument("target", help="Topic (reddit/x/youtube-search), page URL (firecrawl), profile URL (linkedin), or channel id/@handle (youtube-channel).")
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
                print(f"Validated idea queue: {result['manifest_path']}")
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

        if args.command == "init-run":
            run_dir = init_run(
                args.creator_profile,
                workspace=Path(args.workspace),
                run_id=args.run_id,
            )
            print(f"Initialized run: {run_dir}")
            print("Next phase: social_research_pack")
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
            project_dir = init_project(
                args.project,
                creator_workspace=Path(args.creator_workspace),
            )
            print(f"Initialized project: {project_dir}")
            print("Next phase: add selected idea and production plan")
            return 0

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

        if args.command == "rebuild-board":
            result = rebuild_board(args.creator_workspace)
            print(
                f"Rebuilt content board: {result['card_count']} cards "
                f"({result['idea_cards']} ideas, {result['project_cards']} projects)"
            )
            print(f"Board: {result['board_path']}")
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
            budget = _load_connector_budget(run_dir, config["MAX_CALLS"])
            try:
                if args.connector == "reddit":
                    result = connector_fetch.fetch_reddit(
                        args.target, config, budget, depth=args.depth,
                        from_date=args.from_date, to_date=args.to_date, days=args.days,
                    )
                elif args.connector == "x":
                    result = connector_fetch.fetch_x(
                        args.target, config, budget, depth=args.depth,
                        from_date=args.from_date, to_date=args.to_date, days=args.days,
                    )
                elif args.connector == "firecrawl":
                    result = connector_fetch.fetch_firecrawl(args.target, config, budget)
                elif args.connector == "youtube-search":
                    result = connector_fetch.fetch_youtube_search(
                        args.target, config, budget,
                        from_date=args.from_date, to_date=args.to_date,
                        days=args.days, max_results=args.max_results,
                        order=args.order,
                    )
                elif args.connector == "youtube-channel":
                    result = connector_fetch.fetch_youtube_channel(
                        args.target, config, budget,
                        from_date=args.from_date, to_date=args.to_date,
                        days=args.days, max_results=args.max_results,
                    )
                else:
                    result = connector_fetch.fetch_linkedin(
                        args.target, config, budget,
                        max_posts=args.max_posts, days=args.days,
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
