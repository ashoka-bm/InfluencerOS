import argparse
import datetime
import sys
from pathlib import Path

from influencer_os.memory import DEFAULT_MEMORY_SECTION, append_skill_learning, write_memory_fact
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
from influencer_os.projects import init_project, validate_project
from influencer_os.research import validate_queue, validate_research
from influencer_os.runs import DEFAULT_WORKSPACE, init_run
from influencer_os.validation import ValidationError, validate_examples, validate_file


def main(argv=None):
    parser = argparse.ArgumentParser(prog="influencer-os")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate repository records.")
    validate_parser.add_argument("target", choices=["examples", "workspace", "project", "record", "research", "queue"], help="Validation target.")
    validate_parser.add_argument("path", nargs="?", help="Path for workspace/project/research/queue validation, or schema name for record validation.")
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

    memory_parser = subparsers.add_parser("memory-write", help="Add one durable fact to a MEMORY.md file, deduplicated and capped.")
    memory_parser.add_argument("memory_file", help="Path to the MEMORY.md file.")
    memory_parser.add_argument("fact", help="One-line durable fact.")
    memory_parser.add_argument("--section", default=DEFAULT_MEMORY_SECTION, help="Target section heading, without the leading '## '.")

    learning_parser = subparsers.add_parser("log-learning", help="Append a dated per-skill learning entry to a learnings file.")
    learning_parser.add_argument("learnings_file", help="Path to the learnings file.")
    learning_parser.add_argument("skill_name", help="Skill folder name the learning applies to.")
    learning_parser.add_argument("entry", help="One-line learning entry.")
    learning_parser.add_argument("--date", dest="entry_date", help="Entry date as YYYY-MM-DD; defaults to today.")

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
                return 0
            if args.target == "project":
                if not args.path:
                    raise ValueError("validate project requires a project path")
                result = validate_project(args.path)
                print(f"Validated project: {result['project_path']}")
                print(f"Checked {len(result['checked_paths'])} project paths.")
                return 0
            if args.target == "research":
                if not args.path:
                    raise ValueError("validate research requires a creator workspace path")
                result = validate_research(args.path)
                print(f"Validated research state: {result['workspace_path']}")
                print(f"Checked {len(result['checked_paths'])} research records.")
                return 0
            if args.target == "queue":
                if not args.path:
                    raise ValueError("validate queue requires a creator workspace path")
                result = validate_queue(args.path)
                print(f"Validated idea queue: {result['manifest_path']}")
                print(f"Checked {result['entry_count']} queue entries.")
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

        if args.command == "memory-write":
            result = write_memory_fact(args.memory_file, args.fact, section=args.section)
            if result["status"] == "duplicate":
                print("Already saved; no change.")
            else:
                print(f"Saved memory fact ({result['bytes_used']}/{result['byte_cap']} bytes).")
            return 0

        if args.command == "log-learning":
            entry_date = args.entry_date or datetime.date.today().isoformat()
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


if __name__ == "__main__":
    raise SystemExit(main())
