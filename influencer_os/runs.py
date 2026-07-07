import json
import re
import shutil
from datetime import date, datetime, timezone
from pathlib import Path

from influencer_os.json_io import write_json_atomic
from influencer_os.validation import ROOT, load_json, validate_record


DEFAULT_WORKSPACE = ROOT / "workspace-library" / "runs"


def init_run(creator_profile_path, workspace=DEFAULT_WORKSPACE, run_id=None):
    creator_profile_path = Path(creator_profile_path)
    workspace = Path(workspace)
    creator_profile = load_json(creator_profile_path)
    validate_record("creator-profile", creator_profile)

    resolved_run_id = validate_run_id(run_id or build_run_id(creator_profile))
    run_dir = workspace / resolved_run_id
    if run_dir.exists():
        raise FileExistsError(f"Run already exists: {run_dir}")

    records_dir = run_dir / "records"
    records_dir.mkdir(parents=True)
    shutil.copyfile(creator_profile_path, records_dir / "creator-profile.json")

    manifest = {
        "run_id": resolved_run_id,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": "creator_profile_loaded",
        "creator_profile_id": creator_profile["creator_profile_id"],
        "creator_display_name": creator_profile["display_name"],
        "next_phase": "social_research_pack",
        "records": {
            "creator_profile": "records/creator-profile.json"
        }
    }
    write_json(run_dir / "run.json", manifest)
    (run_dir / "events.jsonl").write_text(json.dumps({
        "event": "run_initialized",
        "at": manifest["created_at"],
        "creator_profile_id": creator_profile["creator_profile_id"]
    }) + "\n")
    return run_dir


def build_run_id(creator_profile):
    return f"{slugify(creator_profile['display_name'])}-{date.today().isoformat()}"


def validate_run_id(run_id):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", run_id):
        raise ValueError(f"Invalid run id: {run_id!r}")
    return run_id


def slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "creator"


def write_json(path, data):
    write_json_atomic(path, data)
