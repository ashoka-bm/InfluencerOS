"""Neutral InfluencerOS analytics CSV import (Phase 2 slice 2, Decision 3).

The CSV template is InfluencerOS's own column contract, not a platform
export format: the operator maps a platform export onto these columns once,
so no per-platform parser exists. Each row becomes one AnalyticsSnapshot
written through the shared ingestion seam
(`projects.write_analytics_snapshot`), the same function manual entry and
any future API connector use (ADR 0004).

Blank cells become null for nullable fields — absent platform metrics are
recorded as absent, never guessed. Chain ids (project, creator, output
package) are filled from the project being imported into, so a CSV cannot
mistype them.
"""
import csv
from pathlib import Path

from influencer_os.projects import write_analytics_snapshot
from influencer_os.validation import load_json


# The flat top-level metric fields, in schema order. All nullable numbers.
METRIC_FIELDS = (
    "views",
    "impressions",
    "likes",
    "comments",
    "shares",
    "saves",
    "clicks",
    "follows_or_subscribers",
)

# Attribution stages and their nullable fields, in schema order. CSV columns
# are "<stage>_<field>"; every stage also carries a required "<stage>_notes"
# column. `retention_curve_ref` is the one string field; the rest are
# nullable numbers.
ATTRIBUTION_STAGE_FIELDS = {
    "packaging": ("click_through_rate", "first_frame_hold"),
    "hook": ("retention_3s_pct", "early_drop_off_pct"),
    "body_retention": ("avg_view_duration_sec", "midpoint_retention_pct", "retention_curve_ref"),
    "payoff": ("completion_rate_pct", "rewatch_rate_pct"),
    "cta": ("profile_visits", "link_clicks", "conversion_events"),
}

ATTRIBUTION_STRING_FIELDS = frozenset({"retention_curve_ref"})

# Identity/context columns. hours_since_publish and raw_source_ref may be
# blank; a blank hours_since_publish is derived from the published post's
# publish time when both timestamps parse.
CONTEXT_COLUMNS = (
    "analytics_snapshot_id",
    "published_post_record_id",
    "snapshot_at",
    "source_type",
    "collected_by",
    "confidence",
    "platform",
    "hours_since_publish",
    "raw_source_ref",
    "notes",
)


def csv_columns():
    """The full ordered CSV column contract."""
    columns = list(CONTEXT_COLUMNS)
    columns.extend(METRIC_FIELDS)
    for stage, fields in ATTRIBUTION_STAGE_FIELDS.items():
        columns.extend(f"{stage}_{field}" for field in fields)
        columns.append(f"{stage}_notes")
    return columns


def import_analytics_csv(project_path, csv_path):
    """Import every CSV row as an AnalyticsSnapshot, all-or-nothing.

    Rows are parsed and constructed first; writes happen only after every
    row parsed cleanly, and any write failure rolls back the rows already
    written in this import.
    """
    project_dir = Path(project_path)
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing analytics CSV: {csv_path}")

    project = load_json(project_dir / "project.json")
    package = load_json(project_dir / "output-package" / "output-package.json")

    records = _parse_rows(csv_path, project, package)
    if not records:
        raise ValueError(f"Analytics CSV contains no data rows: {csv_path}")

    results = []
    written_paths = []
    try:
        for record in records:
            result = write_analytics_snapshot(project_dir, record)
            written_paths.append(result["snapshot_path"])
            results.append(result)
    except Exception:
        for path in written_paths:
            if path.exists():
                path.unlink()
        raise
    return results


def _parse_rows(csv_path, project, package):
    expected_columns = csv_columns()
    records = []
    with open(csv_path, newline="") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        missing = sorted(set(expected_columns) - set(header))
        unknown = sorted(set(header) - set(expected_columns))
        if missing or unknown:
            raise ValueError(
                "Analytics CSV header does not match the InfluencerOS template: "
                f"missing columns {missing}, unknown columns {unknown}"
            )
        for line_number, row in enumerate(reader, start=2):
            if None in row.values() or None in row:
                raise ValueError(
                    f"Analytics CSV row {line_number} has a different column "
                    "count than the header"
                )
            try:
                records.append(_row_to_record(row, project, package))
            except ValueError as exc:
                raise ValueError(f"Analytics CSV row {line_number}: {exc}") from exc
    return records


def _row_to_record(row, project, package):
    attribution = {}
    for stage, fields in ATTRIBUTION_STAGE_FIELDS.items():
        stage_record = {}
        for field in fields:
            cell = row[f"{stage}_{field}"]
            if field in ATTRIBUTION_STRING_FIELDS:
                stage_record[field] = _optional_text(cell)
            else:
                stage_record[field] = _optional_number(cell, f"{stage}_{field}")
        stage_record["notes"] = _required_text(row[f"{stage}_notes"], f"{stage}_notes")
        attribution[stage] = stage_record

    return {
        "analytics_snapshot_id": _required_text(row["analytics_snapshot_id"], "analytics_snapshot_id"),
        "published_post_record_id": _required_text(row["published_post_record_id"], "published_post_record_id"),
        "output_package_id": package["output_package_id"],
        "project_id": project["project_id"],
        "creator_profile_id": project["creator_profile_id"],
        "snapshot_at": _required_text(row["snapshot_at"], "snapshot_at"),
        "source": {
            "source_type": _required_text(row["source_type"], "source_type"),
            "collected_by": _required_text(row["collected_by"], "collected_by"),
            "confidence": _required_text(row["confidence"], "confidence"),
        },
        "platform": _required_text(row["platform"], "platform"),
        "hours_since_publish": _optional_number(row["hours_since_publish"], "hours_since_publish"),
        "metrics": {
            field: _optional_number(row[field], field) for field in METRIC_FIELDS
        },
        "attribution_metrics": attribution,
        "raw_source_ref": _optional_text(row["raw_source_ref"]),
        "notes": _required_text(row["notes"], "notes"),
    }


def _required_text(cell, column):
    value = cell.strip()
    if not value:
        raise ValueError(f"column {column!r} must not be blank")
    return value


def _optional_text(cell):
    value = cell.strip()
    return value if value else None


def _optional_number(cell, column):
    value = cell.strip()
    if not value:
        return None
    try:
        if value.lstrip("-").isdigit():
            return int(value)
        return float(value)
    except ValueError:
        raise ValueError(f"column {column!r} is not a number: {value!r}") from None
