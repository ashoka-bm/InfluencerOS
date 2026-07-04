"""Research-module validation: JSONL records, findings frontmatter, and
creator research state (ADR 0020 slice, batch B).

Frontmatter is a scoped YAML subset matching the hand-rolled validator
philosophy — fail-closed, no third-party dependency. Supported: top-level
``key: value`` scalars and ``key:`` followed by ``- item`` string lists.
Nested mappings or any other construct are errors, never silent skips.
"""
import json
from collections import Counter
from pathlib import Path

from influencer_os.validation import (
    GATED_RESEARCH_ACCESS_METHODS,
    ValidationError,
    load_json,
    validate_file,
    validate_record,
)


RESEARCH_INTELLIGENCE_FILES = {
    "sources.json": "research-sources",
    "hashtags.json": "research-hashtags",
    "search-terms.json": "research-search-terms",
    "reference-creators.json": "reference-creators",
    "watchlist.json": "research-watchlist",
}

# (filename, schema, record id field, research-run outputs field). A run's
# outputs id lists must reconcile exactly with its JSONL contents.
RESEARCH_JSONL_FILES = (
    ("evidence.jsonl", "research-evidence", "evidence_id", "evidence_ids"),
    ("metric-snapshots.jsonl", "metric-snapshot", "metric_snapshot_id", "metric_snapshot_ids"),
)

SYSTEM_JSONL_FILES = (
    ("project-warnings.jsonl", "project-warning"),
    ("creator-events.jsonl", "system-event"),
)

# Formats with a production plan schema (projects.PRODUCTION_PLAN_SCHEMAS).
# A promotion must approve at least one of these; approving only unsupported
# formats records approval intent on the queue entry instead (ADR 0020).
PRODUCTION_SUPPORTED_FORMATS = frozenset({
    "format_short_form_video",
    "format_carousel",
    "format_single_image_post",
    "format_story_sequence",
    "format_article",
    "format_thread",
})

# A completed run that changed the rolling findings but grounded them in few
# promoted-to-evidence sources is a thin-evidence run. This is an advisory WARN,
# never a failure: thin research is allowed (local-first posture), it just must
# not read as well-corroborated. Runs that checked fewer than the minimum are
# too small for the promotion rate to mean anything, so they are not evaluated.
THIN_EVIDENCE_MIN_CHECKED = 3
THIN_EVIDENCE_PROMOTION_RATE = 0.34


def _iter_jsonl_lines(path):
    # Split on newlines only: splitlines() would also break on U+2028/U+2029,
    # which are legal inside JSON strings, corrupting records and line numbers.
    for line_number, line in enumerate(path.read_text().split("\n"), start=1):
        if line.strip():
            yield line_number, line


def validate_jsonl_file(schema_name, path, record_check=None):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Missing JSONL file: {path}")
    records = []
    for line_number, line in _iter_jsonl_lines(path):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"{path}:{line_number}: invalid JSON: {exc}") from None
        try:
            validate_record(schema_name, record)
            if record_check is not None:
                record_check(record)
        except ValidationError as exc:
            raise ValidationError(f"{path}:{line_number}: {exc}") from None
        records.append(record)
    return records


def check_project_warning_pairing(record):
    """A warning targeting promoted work carries both project_id and
    idea_promotion_id; a queue-level warning carries neither (ADR 0020)."""
    if ("project_id" in record) != ("idea_promotion_id" in record):
        raise ValidationError(
            "project warning must carry both project_id and idea_promotion_id "
            "when it targets promoted work, and neither for queue-level warnings"
        )


def collect_project_manifests(workspace_dir):
    """Map project_id -> (manifest path, manifest) from projects/*/project.json.

    Project folders are named by project_slug (`init-project` layout), so
    resolution goes through each manifest's project_id; id-named folders in
    older fixtures resolve the same way. A duplicate project_id fails closed
    because it makes link resolution ambiguous."""
    workspace_dir = Path(workspace_dir)
    projects_dir = workspace_dir / "projects"
    manifests = {}
    if projects_dir.exists():
        for manifest_path in sorted(projects_dir.glob("*/project.json")):
            try:
                record = load_json(manifest_path)
            except json.JSONDecodeError as exc:
                raise ValidationError(f"{manifest_path}: invalid JSON: {exc}") from None
            project_id = record.get("project_id")
            if not isinstance(project_id, str) or not project_id:
                raise ValidationError(
                    f"{manifest_path}: project manifest has no project_id"
                )
            if project_id in manifests:
                raise ValidationError(
                    f"project_id {project_id!r} appears more than once under "
                    f"projects/: {manifests[project_id][0]} and {manifest_path}"
                )
            manifests[project_id] = (manifest_path, record)
    return manifests


def check_promotion_entry_links(promotion, entry):
    """An active promotion pins its queue entry: the entry must be promoted
    and must back-link the promotion. Superseded and cancelled promotions
    impose no entry requirement — the entry may have reverted or been
    re-promoted (slice 5 lifecycle rules)."""
    if promotion["promotion_status"] != "active":
        return
    promotion_id = promotion["idea_promotion_id"]
    entry_id = entry["idea_queue_entry_id"]
    if entry["status"] != "promoted":
        raise ValidationError(
            f"Idea promotion {promotion_id} is active but its queue entry "
            f"{entry_id} has status {entry['status']!r}; an active promotion "
            "requires the entry to be 'promoted'"
        )
    if promotion_id not in entry.get("linked_idea_promotion_ids", []):
        raise ValidationError(
            f"Idea promotion {promotion_id} is active but queue entry "
            f"{entry_id} does not list it in linked_idea_promotion_ids"
        )


def check_promotion_created_projects(promotion, projects_by_id):
    """Every project a promotion claims to have created must exist and must
    lock this promotion as its upstream ref (source_refs.idea_promotion_id).
    Projects are never deleted in v1, so a dangling id is invalid state."""
    promotion_id = promotion["idea_promotion_id"]
    for project_id in promotion["project_ids_created"]:
        if project_id not in projects_by_id:
            raise ValidationError(
                f"Idea promotion {promotion_id} lists created project "
                f"{project_id!r} with no project record"
            )
        _, project = projects_by_id[project_id]
        locked = project.get("source_refs", {}).get("idea_promotion_id")
        if locked != promotion_id:
            raise ValidationError(
                f"Idea promotion {promotion_id} lists created project "
                f"{project_id!r}, but that project's locked promotion is "
                f"{locked!r}; source_refs.idea_promotion_id does not point back"
            )


def check_promotion_slot_claims(workspace_dir, promotion):
    """An active promotion's claimed schedule slots must resolve and be
    filled. Superseded/cancelled promotions impose nothing: the schedule is
    mutable planning state, so freed slots legitimately reopen or disappear
    while the locked promotion keeps its historical claim."""
    if promotion["promotion_status"] != "active":
        return
    claimed = promotion.get("schedule_slot_ids", [])
    if not claimed:
        return
    promotion_id = promotion["idea_promotion_id"]
    schedule_path = Path(workspace_dir) / "content-schedule.json"
    if not schedule_path.exists():
        raise ValidationError(
            f"Idea promotion {promotion_id} claims schedule slots but the "
            "workspace has no content-schedule.json"
        )
    # Schema-validate before reading: this check is reachable from validate
    # project, which does not otherwise validate the schedule, and a
    # malformed slot must fail cleanly, not crash on a missing key.
    validate_file("creator-content-schedule", schedule_path)
    slots = {
        slot["slot_id"]: slot
        for slot in load_json(schedule_path).get("calendar_slots", [])
    }
    for slot_id in claimed:
        if slot_id not in slots:
            raise ValidationError(
                f"Idea promotion {promotion_id} claims {slot_id!r}, which "
                "resolves to no schedule slot in content-schedule.json"
            )
        status = slots[slot_id]["status"]
        if status != "filled":
            raise ValidationError(
                f"Idea promotion {promotion_id} is active but claimed slot "
                f"{slot_id} has status {status!r}; a claimed slot must be "
                "'filled'"
            )


def check_project_warning_target_refs(record, workspace_dir, projects_by_id=None):
    """A warning must target records that exist and form one consistent
    promotion chain — queue entries, projects, and promotions are never
    deleted in v1, so a dangling target is invalid state, not history, and
    a mismatched tuple would badge the wrong card on the board."""
    workspace_dir = Path(workspace_dir)
    warning_id = record.get("project_warning_id", "<unknown>")
    entry_id = record["idea_queue_entry_id"]
    entry_path = (
        workspace_dir / "research" / "idea-queue" / "entries" / f"{entry_id}.json"
    )
    if not entry_path.exists():
        raise ValidationError(
            f"project warning {warning_id} targets queue entry {entry_id!r} "
            "with no entry file"
        )
    if "project_id" in record:
        project_id = record["project_id"]
        if projects_by_id is None:
            projects_by_id = collect_project_manifests(workspace_dir)
        if project_id not in projects_by_id:
            raise ValidationError(
                f"project warning {warning_id} targets project {project_id!r} "
                "with no project record"
            )
        promotion_id = record["idea_promotion_id"]
        promotion_path = (
            workspace_dir / "research" / "idea-promotions" / f"{promotion_id}.json"
        )
        if not promotion_path.exists():
            raise ValidationError(
                f"project warning {warning_id} targets idea promotion "
                f"{promotion_id!r} with no promotion record"
            )
        _, project = projects_by_id[project_id]
        locked_promotion = project.get("source_refs", {}).get("idea_promotion_id")
        if locked_promotion != promotion_id:
            raise ValidationError(
                f"project warning {warning_id} pairs project {project_id!r} "
                f"with idea promotion {promotion_id!r}, but the project's "
                f"locked promotion is {locked_promotion!r}"
            )
        promotion = load_json(promotion_path)
        promoted_entry = promotion.get("idea_queue_entry_id")
        if promoted_entry != entry_id:
            raise ValidationError(
                f"project warning {warning_id} targets queue entry "
                f"{entry_id!r}, but idea promotion {promotion_id!r} was "
                f"promoted from {promoted_entry!r}"
            )


def load_workspace_scope(workspace_dir):
    """The research module is creator-scoped: every record in a Creator
    Workspace must belong to the workspace's creator."""
    manifest_path = Path(workspace_dir) / "creator-workspace.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing creator workspace manifest: {manifest_path}")
    manifest = load_json(manifest_path)
    try:
        validate_record("creator-workspace", manifest)
    except ValidationError as exc:
        raise ValidationError(f"{manifest_path}: {exc}") from None
    return {
        "creator_profile_id": manifest["creator_profile_id"],
        "creator_slug": manifest["creator_slug"],
    }


def check_creator_scope(record, scope, context=None):
    """Pin a record's creator fields to the owning workspace. Fields a
    record's schema does not carry (project warnings) are skipped."""
    for field, expected in scope.items():
        value = record.get(field)
        if value is not None and value != expected:
            prefix = f"{context}: " if context else ""
            raise ValidationError(
                f"{prefix}{field} {value!r} does not match the owning "
                f"creator workspace ({expected!r})"
            )


def parse_frontmatter(path):
    path = Path(path)
    text = path.read_text()
    if not text.startswith("---\n"):
        raise ValidationError(f"{path}: missing frontmatter block")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValidationError(f"{path}: unterminated frontmatter block")
    data = _parse_yaml_subset(text[4:end], path)
    body = text[end + len("\n---\n"):]
    return data, body


def _parse_yaml_subset(block, path):
    data = {}
    current_list_key = None
    for line_number, raw_line in enumerate(block.splitlines(), start=2):
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            if current_list_key is None:
                raise ValidationError(f"{path}:{line_number}: list item without a list key")
            data[current_list_key].append(_parse_scalar(stripped[2:].strip()))
            continue
        if raw_line[0] in (" ", "\t"):
            raise ValidationError(
                f"{path}:{line_number}: nested frontmatter is not supported (scoped YAML subset)"
            )
        key, separator, value = raw_line.partition(":")
        if not separator or not key.strip():
            raise ValidationError(f"{path}:{line_number}: expected 'key: value'")
        key = key.strip()
        value = value.strip()
        if value:
            data[key] = _parse_scalar(value)
            current_list_key = None
        else:
            data[key] = []
            current_list_key = key
    return data


def _parse_scalar(value):
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1]
    if value == "true":
        return True
    if value == "false":
        return False
    try:
        return int(value)
    except ValueError:
        return value


def validate_findings_file(path):
    data, body = parse_frontmatter(path)
    try:
        validate_record("research-findings", data)
    except ValidationError as exc:
        raise ValidationError(f"{path}: {exc}") from None
    limit = data["summary_char_limit"]
    if len(body) > limit:
        raise ValidationError(
            f"{path}: body is {len(body)} characters, over summary_char_limit {limit}"
        )
    return data


def validate_stable_finding_file(path):
    data, _ = parse_frontmatter(path)
    try:
        validate_record("stable-finding", data)
    except ValidationError as exc:
        raise ValidationError(f"{path}: {exc}") from None
    return data


def validate_research(workspace_path):
    workspace_dir = Path(workspace_path)
    research_dir = workspace_dir / "research"
    if not research_dir.exists():
        raise FileNotFoundError(f"Missing research directory: {research_dir}")

    scope = load_workspace_scope(workspace_dir)

    def scoped(record):
        check_creator_scope(record, scope)

    checked = []
    source_yield_stats = {}
    run_warnings = []

    schedule_path = workspace_dir / "content-schedule.json"
    if schedule_path.exists():
        validate_file("creator-content-schedule", schedule_path)
        check_creator_scope(load_json(schedule_path), scope, schedule_path)
        checked.append("content-schedule.json")

    findings_path = research_dir / "findings.md"
    if findings_path.exists():
        findings_data = validate_findings_file(findings_path)
        check_creator_scope(findings_data, scope, findings_path)
        checked.append("research/findings.md")

    stable_dir = research_dir / "stable-findings"
    if stable_dir.exists():
        for stable_path in sorted(stable_dir.glob("*.md")):
            stable_data = validate_stable_finding_file(stable_path)
            # The entries/promotions filename==id pattern: it also makes a
            # duplicated stable_finding_id impossible at rest.
            if stable_data["stable_finding_id"] != stable_path.stem:
                raise ValidationError(
                    f"{stable_path}: filename does not match stable_finding_id "
                    f"{stable_data['stable_finding_id']!r}"
                )
            check_creator_scope(stable_data, scope, stable_path)
            checked.append(str(stable_path.relative_to(workspace_dir)))

    runs_dir = research_dir / "runs"
    if runs_dir.exists():
        for run_dir in sorted(path for path in runs_dir.iterdir() if path.is_dir()):
            run_manifest = run_dir / "research-run.json"
            if not run_manifest.exists():
                raise ValidationError(f"Research run folder has no research-run.json: {run_dir}")
            validate_file("research-run", run_manifest)
            run_record = load_json(run_manifest)
            if run_record["research_run_id"] != run_dir.name:
                raise ValidationError(
                    f"{run_manifest}: folder name {run_dir.name!r} does not match "
                    f"research_run_id {run_record['research_run_id']!r} "
                    "(layout is research/runs/<research-run-id>/)"
                )
            check_creator_scope(run_record, scope, run_manifest)
            checked.append(str(run_manifest.relative_to(workspace_dir)))
            run_id = run_record["research_run_id"]

            search_plan = None
            search_plan_path = run_dir / "search-plan.json"
            completed_run = run_record["run_status"] != "failed"
            if completed_run and not search_plan_path.exists():
                raise ValidationError(f"Research run folder has no search-plan.json: {run_dir}")
            if search_plan_path.exists():
                try:
                    validate_file("research-search-plan", search_plan_path)
                except ValidationError as exc:
                    raise ValidationError(f"{search_plan_path}: {exc}") from None
                search_plan = load_json(search_plan_path)
                if search_plan["research_run_id"] != run_id:
                    raise ValidationError(
                        f"{search_plan_path}: research_run_id "
                        f"{search_plan['research_run_id']!r} does not match "
                        f"the containing run {run_id!r}"
                    )
                if search_plan["mode"] != run_record["mode"]:
                    raise ValidationError(
                        f"{search_plan_path}: mode {search_plan['mode']!r} "
                        f"does not match research-run.json mode {run_record['mode']!r}"
                    )
                missing_run_platforms = sorted(
                    set(run_record["platforms"]) - set(search_plan["platforms"])
                )
                if missing_run_platforms:
                    raise ValidationError(
                        f"{search_plan_path}: research-run.json platforms "
                        f"{missing_run_platforms!r} are not present in "
                        "search-plan.json platforms"
                    )
                check_creator_scope(search_plan, scope, search_plan_path)
                checked.append(str(search_plan_path.relative_to(workspace_dir)))

            def run_scoped(record, _run_id=run_id):
                check_creator_scope(record, scope)
                record_run = record.get("research_run_id")
                if record_run != _run_id:
                    raise ValidationError(
                        f"research_run_id {record_run!r} does not match "
                        f"the containing run {_run_id!r}"
                    )

            run_records = {filename: [] for filename, *_ in RESEARCH_JSONL_FILES}
            for filename, schema_name, id_field, outputs_field in RESEARCH_JSONL_FILES:
                jsonl_path = run_dir / filename
                jsonl_ids = set()
                if jsonl_path.exists():
                    records = validate_jsonl_file(
                        schema_name, jsonl_path, record_check=run_scoped
                    )
                    id_counts = Counter(record[id_field] for record in records)
                    duplicate_ids = sorted(
                        record_id for record_id, count in id_counts.items() if count > 1
                    )
                    if duplicate_ids:
                        # A duplicated id validates against the declared
                        # outputs (set comparison) but makes every ref to it
                        # ambiguous and bricks the recall index rebuild.
                        raise ValidationError(
                            f"{jsonl_path}: duplicate {id_field} values within "
                            f"the run: {duplicate_ids}"
                        )
                    run_records[filename] = records
                    jsonl_ids = set(id_counts)
                    checked.append(str(jsonl_path.relative_to(workspace_dir)))
                declared_ids = set(run_record["outputs"][outputs_field])
                # Prune records removals instead of rewriting outputs, so the
                # manifest keeps its original account of what the run produced:
                # JSONL contents must equal outputs minus pruned ids.
                pruned_field = f"pruned_{outputs_field}"
                pruned_ids = set(run_record.get(pruned_field, []))
                undeclared_pruned = sorted(pruned_ids - declared_ids)
                if undeclared_pruned:
                    raise ValidationError(
                        f"{run_manifest}: {pruned_field} list ids never "
                        f"declared in outputs.{outputs_field}: {undeclared_pruned}"
                    )
                still_present = sorted(pruned_ids & jsonl_ids)
                if still_present:
                    raise ValidationError(
                        f"{run_manifest}: {pruned_field} list ids still "
                        f"present in {filename}: {still_present}"
                    )
                expected_ids = declared_ids - pruned_ids
                undeclared = sorted(jsonl_ids - expected_ids)
                if undeclared:
                    raise ValidationError(
                        f"{run_manifest}: outputs.{outputs_field} omit ids "
                        f"present in {filename}: {undeclared}"
                    )
                ghost = sorted(expected_ids - jsonl_ids)
                if ghost:
                    raise ValidationError(
                        f"{run_manifest}: outputs.{outputs_field} list ids "
                        f"not present in {filename} and not pruned: {ghost}"
                    )

            # Metric snapshots are run-scoped observations of run evidence:
            # a snapshot whose evidence_id is absent from the run severs the
            # trajectory link and can never be pruned (snapshots prune with
            # their evidence).
            run_evidence_ids = {
                record["evidence_id"] for record in run_records["evidence.jsonl"]
            }
            for snapshot in run_records["metric-snapshots.jsonl"]:
                if snapshot["evidence_id"] not in run_evidence_ids:
                    raise ValidationError(
                        f"{run_dir / 'metric-snapshots.jsonl'}: metric snapshot "
                        f"{snapshot['metric_snapshot_id']} snapshots evidence "
                        f"{snapshot['evidence_id']!r}, which is not in this "
                        "run's evidence.jsonl"
                    )

            source_yield_path = run_dir / "source-yield.jsonl"
            if completed_run and not source_yield_path.exists():
                raise ValidationError(f"Research run folder has no source-yield.jsonl: {run_dir}")
            if source_yield_path.exists():
                source_yield_records = validate_jsonl_file(
                    "research-source-yield", source_yield_path, record_check=run_scoped
                )
                yield_id_counts = Counter(
                    record["research_source_yield_id"]
                    for record in source_yield_records
                )
                duplicate_yield_ids = sorted(
                    yield_id for yield_id, count in yield_id_counts.items() if count > 1
                )
                if duplicate_yield_ids:
                    # A duplicated id makes every ref to it ambiguous and
                    # double-counts into yield_stats — the same guard the
                    # evidence and metric ledgers already carry.
                    raise ValidationError(
                        f"{source_yield_path}: duplicate research_source_yield_id "
                        f"values within the run: {duplicate_yield_ids}"
                    )
                plan_platforms = set(search_plan["platforms"]) if search_plan else set()
                run_metric_ids = {
                    record["metric_snapshot_id"]
                    for record in run_records["metric-snapshots.jsonl"]
                }
                for record in source_yield_records:
                    if record["access_method"] in GATED_RESEARCH_ACCESS_METHODS:
                        # The yield ledger records what the run actually did;
                        # a gated method here attests the run executed something
                        # the slice forbids, so the plan-side gate is not enough.
                        raise ValidationError(
                            f"{source_yield_path}: source yield "
                            f"{record['research_source_yield_id']} used gated "
                            f"access method {record['access_method']!r}, which is "
                            "not permitted in this slice"
                        )
                    if plan_platforms and record["platform"] not in plan_platforms:
                        raise ValidationError(
                            f"{source_yield_path}: source yield "
                            f"{record['research_source_yield_id']} platform "
                            f"{record['platform']!r} is not in search-plan.json platforms"
                        )
                    missing_evidence = sorted(set(record["evidence_ids"]) - run_evidence_ids)
                    if missing_evidence:
                        raise ValidationError(
                            f"{source_yield_path}: source yield "
                            f"{record['research_source_yield_id']} references evidence "
                            f"not present in this run: {missing_evidence}"
                        )
                    missing_metrics = sorted(set(record["metric_snapshot_ids"]) - run_metric_ids)
                    if missing_metrics:
                        raise ValidationError(
                            f"{source_yield_path}: source yield "
                            f"{record['research_source_yield_id']} references metric "
                            f"snapshots not present in this run: {missing_metrics}"
                        )
                    if record["source_key"].startswith("source_intel_"):
                        stats = source_yield_stats.setdefault(
                            record["source_key"],
                            {
                                "checked_count": 0,
                                "promoted_to_evidence_count": 0,
                                "background_use_count": 0,
                                "low_yield_count": 0,
                            },
                        )
                        stats["checked_count"] += 1
                        if record["outcome"] == "promoted_to_evidence":
                            stats["promoted_to_evidence_count"] += 1
                        elif record["outcome"] == "used_as_background":
                            stats["background_use_count"] += 1
                        else:
                            stats["low_yield_count"] += 1
                checked_sources = len(source_yield_records)
                promoted_sources = sum(
                    1 for record in source_yield_records
                    if record["outcome"] == "promoted_to_evidence"
                )
                if (
                    run_record["material_update"]
                    and checked_sources >= THIN_EVIDENCE_MIN_CHECKED
                    and promoted_sources
                    < THIN_EVIDENCE_PROMOTION_RATE * checked_sources
                ):
                    run_warnings.append(
                        f"{run_manifest}: run declares a material update but only "
                        f"{promoted_sources} of {checked_sources} checked sources "
                        "produced evidence; treat its findings as thin-evidence, "
                        "not well-corroborated"
                    )
                checked.append(str(source_yield_path.relative_to(workspace_dir)))

    for filename, schema_name in RESEARCH_INTELLIGENCE_FILES.items():
        intel_path = research_dir / "intelligence" / filename
        if intel_path.exists():
            validate_file(schema_name, intel_path)
            check_creator_scope(load_json(intel_path), scope, intel_path)
            checked.append(str(intel_path.relative_to(workspace_dir)))

    sources_path = research_dir / "intelligence" / "sources.json"
    if source_yield_stats and not sources_path.exists():
        raise ValidationError(
            f"source-yield references saved source ids, but {sources_path} is missing"
        )
    if sources_path.exists():
        sources = load_json(sources_path)
        sources_by_id = {item["source_intel_id"]: item for item in sources["items"]}
        zero_stats = {
            "checked_count": 0,
            "promoted_to_evidence_count": 0,
            "background_use_count": 0,
            "low_yield_count": 0,
        }
        # records -> sources: every source a yield record credited must be saved.
        for source_id in sorted(source_yield_stats):
            if source_id not in sources_by_id:
                raise ValidationError(
                    f"{sources_path}: source-yield references {source_id!r}, "
                    "but sources.json has no matching item"
                )
        # sources -> records: every saved source's counts must equal the
        # aggregate of its yield records — all zeros when it has none — so a
        # hand-edited source cannot advertise an invented usefulness history.
        for source_id, item in sorted(sources_by_id.items()):
            expected_stats = source_yield_stats.get(source_id, zero_stats)
            actual_stats = item.get("yield_stats", {})
            for field, expected_value in expected_stats.items():
                actual_value = actual_stats.get(field)
                if actual_value != expected_value:
                    raise ValidationError(
                        f"{sources_path}: {source_id}.yield_stats.{field} "
                        f"is {actual_value!r}, expected {expected_value!r} "
                        "from source-yield.jsonl records"
                    )

    board_path = workspace_dir / "boards" / "content-board.json"
    if board_path.exists():
        validate_file("content-board", board_path)
        check_creator_scope(load_json(board_path), scope, board_path)
        checked.append("boards/content-board.json")

    for filename, schema_name in SYSTEM_JSONL_FILES:
        system_path = workspace_dir / "system" / filename
        if system_path.exists():
            if schema_name == "project-warning":
                def record_check(record):
                    check_project_warning_pairing(record)
                    check_project_warning_target_refs(record, workspace_dir)
                    check_creator_scope(record, scope)
            else:
                record_check = scoped
            validate_jsonl_file(schema_name, system_path, record_check=record_check)
            checked.append(str(system_path.relative_to(workspace_dir)))

    warnings, promotion_paths, _promotions_by_id = validate_promotions(
        workspace_dir, scope=scope
    )
    checked.extend(promotion_paths)
    warnings = run_warnings + warnings

    # Promotion checks run identically on the research and queue paths: when
    # the queue exists, the research path also verifies the entry-side
    # consistency (manifest agreement, ref resolution, and the
    # entry <-> promotion <-> project closure).
    queue_manifest_path = workspace_dir / "research" / "idea-queue" / "queue.json"
    if queue_manifest_path.exists():
        _check_queue_consistency(workspace_dir, scope)
        checked.append("research/idea-queue/queue.json")

    return {"workspace_path": workspace_dir, "checked_paths": checked, "warnings": warnings}


def validate_queue(workspace_path):
    workspace_dir = Path(workspace_path)
    manifest_path = workspace_dir / "research" / "idea-queue" / "queue.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing idea queue manifest: {manifest_path}")

    scope = load_workspace_scope(workspace_dir)

    # Entry-side consistency first (queue-focused errors surface first),
    # then the same promotion check set as validate research (gate, creator
    # scope, filename==id, slot claims, gate warnings) so no promotion state
    # can validate on one command and fail the other.
    entries = _check_queue_consistency(workspace_dir, scope)
    warnings, _promotion_paths, _promotions_by_id = validate_promotions(
        workspace_dir, scope=scope
    )

    return {
        "workspace_path": workspace_dir,
        "entry_count": len(entries),
        "manifest_path": manifest_path,
        "warnings": warnings,
    }


def _check_queue_consistency(workspace_dir, scope):
    """Entry-side queue consistency, shared by validate_queue and
    validate_research: manifest/entry agreement, evidence and finding ref
    resolution, and the entry <-> promotion <-> project closure."""
    workspace_dir = Path(workspace_dir)
    queue_dir = workspace_dir / "research" / "idea-queue"
    manifest_path = queue_dir / "queue.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing idea queue manifest: {manifest_path}")

    manifest = load_json(manifest_path)
    validate_record("idea-queue", manifest)
    check_creator_scope(manifest, scope, manifest_path)

    entries_dir = queue_dir / "entries"
    entries = {}
    if entries_dir.exists():
        for entry_path in sorted(entries_dir.glob("*.json")):
            record = load_json(entry_path)
            try:
                validate_record("idea-queue-entry", record)
            except ValidationError as exc:
                raise ValidationError(f"{entry_path}: {exc}") from None
            if record["idea_queue_entry_id"] != entry_path.stem:
                raise ValidationError(
                    f"{entry_path}: filename does not match idea_queue_entry_id "
                    f"{record['idea_queue_entry_id']!r}"
                )
            check_creator_scope(record, scope, entry_path)
            entries[record["idea_queue_entry_id"]] = record

    ref_ids = [ref["idea_queue_entry_id"] for ref in manifest["entry_refs"]]
    duplicate_refs = sorted(
        ref_id for ref_id in set(ref_ids) if ref_ids.count(ref_id) > 1
    )
    if duplicate_refs:
        raise ValidationError(
            f"Queue manifest lists entries more than once: {duplicate_refs}"
        )
    manifest_refs = {ref["idea_queue_entry_id"]: ref["status"] for ref in manifest["entry_refs"]}
    missing = sorted(set(manifest_refs) - set(entries))
    if missing:
        raise ValidationError(f"Queue manifest names entries with no entry file: {missing}")
    unlisted = sorted(set(entries) - set(manifest_refs))
    if unlisted:
        raise ValidationError(f"Queue entry files missing from the manifest: {unlisted}")
    for entry_id, status in manifest_refs.items():
        if entries[entry_id]["status"] != status:
            raise ValidationError(
                f"Queue manifest status {status!r} does not match entry file status "
                f"{entries[entry_id]['status']!r} for {entry_id}"
            )

    status_counts = manifest.get("status_counts")
    if status_counts is not None:
        actual_counts = {}
        for status in manifest_refs.values():
            actual_counts[status] = actual_counts.get(status, 0) + 1
        for status, count in status_counts.items():
            if actual_counts.get(status, 0) != count:
                raise ValidationError(
                    f"Queue manifest status_counts[{status!r}] is {count}, but "
                    f"{actual_counts.get(status, 0)} entries have that status"
                )
        uncounted = sorted(set(actual_counts) - set(status_counts))
        if uncounted:
            raise ValidationError(
                f"Queue manifest status_counts omit statuses present in the queue: {uncounted}"
            )

    evidence_runs, metric_runs, metric_evidence = collect_research_record_ids(workspace_dir)
    video_pack_ids = collect_video_pack_ids(workspace_dir)
    known_finding_ids = collect_finding_ids(workspace_dir)
    for entry in entries.values():
        for ref in entry["evidence_refs"]:
            problems = resolve_evidence_ref(
                ref, evidence_runs, metric_runs, video_pack_ids, metric_evidence
            )
            if problems:
                raise ValidationError(
                    f"{entry['idea_queue_entry_id']}: {problems[0]}"
                )
        for finding_id in entry.get("source_finding_ids", []):
            if finding_id not in known_finding_ids:
                raise ValidationError(
                    f"{entry['idea_queue_entry_id']}: source finding ref "
                    f"{finding_id!r} does not resolve to any findings "
                    "frontmatter, stable finding, or run output"
                )

    # Slice 5 link consistency: entry <-> promotion <-> project links hold at
    # rest. The promotion act writes both sides in one workflow, so a
    # one-sided link is always invalid state, never an in-progress step.
    # Promotions load schema-valid here for the entry-side closure; the
    # per-promotion gate, creator scope, filename==id, and slot-claim checks
    # run in validate_promotions on both validator paths.
    promotions_by_id = {}
    promotions_dir = workspace_dir / "research" / "idea-promotions"
    if promotions_dir.exists():
        for promotion_path in sorted(promotions_dir.glob("*.json")):
            promotion = load_json(promotion_path)
            try:
                validate_record("idea-promotion", promotion)
            except ValidationError as exc:
                raise ValidationError(f"{promotion_path}: {exc}") from None
            promotions_by_id[promotion["idea_promotion_id"]] = promotion
    projects_by_id = collect_project_manifests(workspace_dir)

    for entry_id, entry in entries.items():
        linked_promotions = entry.get("linked_idea_promotion_ids", [])
        for promotion_id in linked_promotions:
            promotion = promotions_by_id.get(promotion_id)
            if promotion is None:
                raise ValidationError(
                    f"{entry_id}: linked idea promotion {promotion_id!r} has "
                    "no promotion record"
                )
            if promotion["idea_queue_entry_id"] != entry_id:
                raise ValidationError(
                    f"{entry_id}: linked idea promotion {promotion_id!r} was "
                    f"promoted from {promotion['idea_queue_entry_id']!r}"
                )
        active = [
            promotion_id
            for promotion_id in linked_promotions
            if promotions_by_id[promotion_id]["promotion_status"] == "active"
        ]
        if entry["status"] == "promoted":
            if not linked_promotions:
                raise ValidationError(
                    f"{entry_id}: status is 'promoted' but "
                    "linked_idea_promotion_ids is empty"
                )
            if not active:
                raise ValidationError(
                    f"{entry_id}: status is 'promoted' but no linked promotion "
                    "is active; the entry should have reverted with the last "
                    "active promotion"
                )
            if len(active) > 1:
                raise ValidationError(
                    f"{entry_id}: more than one linked promotion is active "
                    f"({sorted(active)}); scope expansion must supersede the "
                    "earlier promotion, not add a second active one"
                )
        elif active:
            raise ValidationError(
                f"{entry_id}: status is {entry['status']!r} but the entry "
                f"links active promotion(s) {sorted(active)}"
            )
        linked_projects = entry.get("linked_project_ids", [])
        for project_id in linked_projects:
            if project_id not in projects_by_id:
                raise ValidationError(
                    f"{entry_id}: linked project {project_id!r} has no "
                    "project record"
                )
        # Slice 5 review P1: promotion must leave production work behind.
        # The rule is entry-level, not a promotion-level minimum, because an
        # active supersede-expansion promotion legitimately creates no new
        # project — the entry still links the superseded promotion's work.
        if entry["status"] == "promoted" and not linked_projects:
            raise ValidationError(
                f"{entry_id}: status is 'promoted' but the entry has no "
                "linked project; a promotion must leave production work "
                "behind in linked_project_ids"
            )
        for project_id in linked_projects:
            _, project = projects_by_id[project_id]
            locked = project.get("source_refs", {}).get("idea_promotion_id")
            if locked not in linked_promotions:
                raise ValidationError(
                    f"{entry_id}: linked project {project_id!r} locks "
                    f"promotion {locked!r}, which is not among the entry's "
                    "linked promotions"
                )
        for promotion_id in linked_promotions:
            missing = sorted(
                set(promotions_by_id[promotion_id]["project_ids_created"])
                - set(linked_projects)
            )
            if missing:
                raise ValidationError(
                    f"{entry_id}: linked promotion {promotion_id} created "
                    f"projects missing from linked_project_ids: {missing}"
                )

    return entries


def validate_promotion_gate(workspace_dir, promotion, projects_by_id=None):
    """Enforce the promotion gate (Phase 0C workstream 12 residue).

    A promotion must point to a real idea queue entry. Unresolved evidence
    refs warn for human-approved promotions (the human saw the evidence) and
    fail for any future automated promotion path. Returns warning strings.
    """
    workspace_dir = Path(workspace_dir)
    promotion_id = promotion["idea_promotion_id"]
    entry_id = promotion["idea_queue_entry_id"]
    entry_path = workspace_dir / "research" / "idea-queue" / "entries" / f"{entry_id}.json"
    if not entry_path.exists():
        raise ValidationError(
            f"Idea promotion {promotion_id} does not point to a real idea queue entry: "
            f"research/idea-queue/entries/{entry_id}.json is missing"
        )
    entry = load_json(entry_path)
    try:
        validate_record("idea-queue-entry", entry)
    except ValidationError as exc:
        raise ValidationError(f"{entry_path}: {exc}") from None
    if entry["creator_profile_id"] != promotion["creator_profile_id"]:
        raise ValidationError(
            f"Idea promotion {promotion_id} points to a queue entry owned by a "
            f"different creator: {entry['creator_profile_id']!r} != "
            f"{promotion['creator_profile_id']!r}"
        )
    if not set(promotion["approved_formats"]) & PRODUCTION_SUPPORTED_FORMATS:
        raise ValidationError(
            f"Idea promotion {promotion_id} approves no production-supported "
            f"format ({sorted(promotion['approved_formats'])}); record the "
            "approval intent on the queue entry instead until the format lands"
        )
    check_promotion_entry_links(promotion, entry)
    if projects_by_id is None:
        projects_by_id = collect_project_manifests(workspace_dir)
    check_promotion_created_projects(promotion, projects_by_id)
    check_promotion_slot_claims(workspace_dir, promotion)

    evidence_runs, metric_runs, metric_evidence = collect_research_record_ids(workspace_dir)
    video_pack_ids = collect_video_pack_ids(workspace_dir)
    warnings = []

    unresolved = []
    for ref in promotion["evidence_refs"]:
        unresolved.extend(
            resolve_evidence_ref(
                ref, evidence_runs, metric_runs, video_pack_ids, metric_evidence
            )
        )
    if unresolved:
        message = (
            f"idea promotion {promotion_id} has unresolved evidence refs: "
            + "; ".join(sorted(set(unresolved)))
        )
        if promotion["approved_by"] != "user":
            raise ValidationError(message)
        warnings.append(
            f"warning: {message} (human-approved promotion: warning only)"
        )

    known_finding_ids = collect_finding_ids(workspace_dir)
    unresolved_findings = sorted(
        finding_id
        for finding_id in set(promotion.get("research_finding_ids", []))
        if finding_id not in known_finding_ids
    )
    if unresolved_findings:
        message = (
            f"idea promotion {promotion_id} has research finding refs that "
            "resolve to no findings frontmatter, stable finding, or run "
            f"output: {unresolved_findings}"
        )
        if promotion["approved_by"] != "user":
            raise ValidationError(message)
        warnings.append(
            f"warning: {message} (human-approved promotion: warning only)"
        )
    return warnings


def validate_promotions(workspace_path, scope=None):
    """Validate every promotion record and its gate. Returns warning strings,
    checked paths, and the promotion map keyed by idea_promotion_id."""
    workspace_dir = Path(workspace_path)
    if scope is None:
        scope = load_workspace_scope(workspace_dir)
    promotions_dir = workspace_dir / "research" / "idea-promotions"
    warnings = []
    checked = []
    promotions_by_id = {}
    if promotions_dir.exists():
        projects_by_id = collect_project_manifests(workspace_dir)
        claimed_slots = {}
        for promotion_path in sorted(promotions_dir.glob("*.json")):
            promotion = load_json(promotion_path)
            try:
                validate_record("idea-promotion", promotion)
            except ValidationError as exc:
                raise ValidationError(f"{promotion_path}: {exc}") from None
            if promotion["idea_promotion_id"] != promotion_path.stem:
                raise ValidationError(
                    f"{promotion_path}: filename does not match idea_promotion_id "
                    f"{promotion['idea_promotion_id']!r}"
                )
            check_creator_scope(promotion, scope, promotion_path)
            warnings.extend(
                validate_promotion_gate(
                    workspace_dir, promotion, projects_by_id=projects_by_id
                )
            )
            if promotion["promotion_status"] == "active":
                for slot_id in promotion.get("schedule_slot_ids", []):
                    earlier = claimed_slots.setdefault(
                        slot_id, promotion["idea_promotion_id"]
                    )
                    if earlier != promotion["idea_promotion_id"]:
                        raise ValidationError(
                            f"Schedule slot {slot_id} is claimed by more than "
                            f"one active promotion: {earlier} and "
                            f"{promotion['idea_promotion_id']}"
                        )
            promotions_by_id[promotion["idea_promotion_id"]] = promotion
            checked.append(str(promotion_path.relative_to(workspace_dir)))
    return warnings, checked, promotions_by_id


def collect_research_record_ids(workspace_dir):
    """Scan run JSONL files and map evidence and metric snapshot ids to their
    containing run folder, plus each metric snapshot's evidence link.
    File-first by design: the recall index is a rebuildable projection, never
    a validation dependency. Duplicate ids fail closed — cross-run because
    they make run-scoped ref resolution ambiguous, within-run because every
    ref to the id becomes ambiguous and the recall index rebuild fails."""
    evidence_runs = {}
    metric_runs = {}
    metric_evidence = {}
    runs_dir = Path(workspace_dir) / "research" / "runs"
    if runs_dir.exists():
        scans = (
            ("evidence.jsonl", "evidence_id", evidence_runs),
            ("metric-snapshots.jsonl", "metric_snapshot_id", metric_runs),
        )
        for filename, id_field, id_runs in scans:
            for jsonl_path in sorted(runs_dir.glob(f"*/{filename}")):
                run_id = jsonl_path.parent.name
                for line_number, line in _iter_jsonl_lines(jsonl_path):
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValidationError(
                            f"{jsonl_path}:{line_number}: invalid JSON: {exc}"
                        ) from None
                    if id_field not in record:
                        raise ValidationError(
                            f"{jsonl_path}:{line_number}: record has no {id_field}"
                        )
                    record_id = record[id_field]
                    existing_run = id_runs.get(record_id)
                    if existing_run == run_id:
                        raise ValidationError(
                            f"{jsonl_path}:{line_number}: {id_field} {record_id!r} "
                            "is duplicated within the run; ids must be unique"
                        )
                    if existing_run is not None:
                        raise ValidationError(
                            f"{jsonl_path}:{line_number}: {id_field} {record_id!r} "
                            f"appears in more than one run ({existing_run!r} and "
                            f"{run_id!r}); ids must resolve to exactly one run"
                        )
                    id_runs[record_id] = run_id
                    if id_field == "metric_snapshot_id":
                        metric_evidence[record_id] = record.get("evidence_id")
    return evidence_runs, metric_runs, metric_evidence


def resolve_evidence_ref(ref, evidence_runs, metric_runs, video_pack_ids, metric_evidence=None):
    """Return problem strings for one structured evidence ref (empty when the
    ref resolves). Evidence and metric snapshots must live in the run the ref
    names — the ADR 0020 ref shape carries research_run_id precisely so
    provenance cannot float across runs — and each referenced snapshot must
    snapshot the ref's own evidence, not another record's. Video packs may be
    workspace-level, so they resolve by id alone."""
    problems = []
    ref_run = ref["research_run_id"]
    evidence_id = ref["evidence_id"]
    evidence_run = evidence_runs.get(evidence_id)
    if evidence_run is None:
        problems.append(
            f"evidence ref {evidence_id!r} does not resolve to any "
            "research run evidence record"
        )
    elif evidence_run != ref_run:
        problems.append(
            f"evidence ref {evidence_id!r} resolves to run {evidence_run!r}, "
            f"but the ref names run {ref_run!r}"
        )
    for metric_id in ref.get("metric_snapshot_ids", []):
        metric_run = metric_runs.get(metric_id)
        if metric_run is None:
            problems.append(
                f"metric snapshot ref {metric_id!r} does not resolve to any "
                "research run metric snapshot"
            )
        elif metric_run != ref_run:
            problems.append(
                f"metric snapshot ref {metric_id!r} resolves to run "
                f"{metric_run!r}, but the ref names run {ref_run!r}"
            )
        elif (
            metric_evidence is not None
            and metric_evidence.get(metric_id) != evidence_id
        ):
            problems.append(
                f"metric snapshot ref {metric_id!r} snapshots evidence "
                f"{metric_evidence.get(metric_id)!r}, not the ref's evidence "
                f"{evidence_id!r}"
            )
    for pack_id in ref.get("video_understanding_pack_ids", []):
        if pack_id not in video_pack_ids:
            problems.append(
                f"video understanding pack ref {pack_id!r} does not resolve "
                "to a video-understanding-pack record"
            )
    return problems


def collect_finding_ids(workspace_dir):
    """Every finding id the workspace has declared: the rolling findings
    frontmatter, stable findings, and each run's immutable outputs. Findings
    legitimately rotate out of the rolling summary (the char limit demotes
    them), so refs resolve against the union — a ghost id fails while a
    rotated finding still resolves through the run that produced it."""
    research_dir = Path(workspace_dir) / "research"
    finding_ids = set()
    findings_path = research_dir / "findings.md"
    if findings_path.exists():
        data, _body = parse_frontmatter(findings_path)
        finding_ids.update(data.get("finding_ids", []))
    stable_dir = research_dir / "stable-findings"
    if stable_dir.exists():
        for stable_path in sorted(stable_dir.glob("*.md")):
            data, _body = parse_frontmatter(stable_path)
            if data.get("finding_id"):
                finding_ids.add(data["finding_id"])
    runs_dir = research_dir / "runs"
    if runs_dir.exists():
        for manifest_path in sorted(runs_dir.glob("*/research-run.json")):
            outputs = load_json(manifest_path).get("outputs", {})
            finding_ids.update(outputs.get("finding_ids", []))
    return finding_ids


def collect_video_pack_ids(workspace_dir):
    """Video Understanding Pack ids resolve to <pack-id>.json files, either in
    the workspace-level pack directory or inside a run folder. The file is
    read and its video_understanding_pack_id must match the filename stem, so
    a ref cannot resolve through a mislabeled or malformed pack file."""
    research_dir = Path(workspace_dir) / "research"
    pack_ids = set()
    for pattern in (
        "video-understanding-packs/*.json",
        "runs/*/video-understanding-packs/*.json",
    ):
        for path in sorted(research_dir.glob(pattern)):
            try:
                record = load_json(path)
            except json.JSONDecodeError as exc:
                raise ValidationError(f"{path}: invalid JSON: {exc}") from None
            pack_id = record.get("video_understanding_pack_id")
            if pack_id != path.stem:
                raise ValidationError(
                    f"{path}: filename does not match "
                    f"video_understanding_pack_id {pack_id!r}"
                )
            pack_ids.add(pack_id)
    return pack_ids
