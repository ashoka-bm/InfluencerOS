import argparse
import sys
from pathlib import Path

from influencer_os.creator_workspaces import (
    DEFAULT_CREATOR_WORKSPACE_ROOT,
    init_creator,
    sync_creator_runtime,
    validate_creator_workspace,
)
from influencer_os.projects import init_project, validate_project
from influencer_os.runs import DEFAULT_WORKSPACE, init_run
from influencer_os.validation import ValidationError, validate_examples


def main(argv=None):
    parser = argparse.ArgumentParser(prog="influencer-os")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate repository records.")
    validate_parser.add_argument("target", choices=["examples", "workspace", "project"], help="Validation target.")
    validate_parser.add_argument("path", nargs="?", help="Path for workspace or project validation.")

    init_parser = subparsers.add_parser("init-run", help="Initialize a dry-run workspace from a creator profile.")
    init_parser.add_argument("creator_profile", help="Path to a Creator Profile JSON file.")
    init_parser.add_argument("--workspace", default=str(DEFAULT_WORKSPACE), help="Run workspace directory.")
    init_parser.add_argument("--run-id", help="Optional explicit run id.")

    creator_parser = subparsers.add_parser("init-creator", help="Initialize a Creator Workspace from a workspace manifest.")
    creator_parser.add_argument("creator_workspace", help="Path to a Creator Workspace JSON manifest.")
    creator_parser.add_argument("--workspace-root", default=str(DEFAULT_CREATOR_WORKSPACE_ROOT), help="Creator workspace root directory.")

    sync_creator_parser = subparsers.add_parser("sync-creator-runtime", help="Refresh copied runtime skills inside a Creator Workspace.")
    sync_creator_parser.add_argument("creator_workspace", help="Path to the Creator Workspace.")

    project_parser = subparsers.add_parser("init-project", help="Initialize a project folder inside a Creator Workspace.")
    project_parser.add_argument("project", help="Path to a Project JSON manifest.")
    project_parser.add_argument("--creator-workspace", required=True, help="Path to the Creator Workspace.")

    args = parser.parse_args(argv)

    try:
        if args.command == "validate":
            if args.target == "examples":
                results = validate_examples()
                print(f"Validated {len(results)} example records.")
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

        if args.command == "init-project":
            project_dir = init_project(
                args.project,
                creator_workspace=Path(args.creator_workspace),
            )
            print(f"Initialized project: {project_dir}")
            print("Next phase: add selected idea and production plan")
            return 0
    except (ValidationError, FileExistsError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    parser.error(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
