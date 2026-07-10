"""Interactive content-calendar projection over canonical creator records."""

import calendar
import hashlib
import html
import os
import re
import tempfile
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from influencer_os.creator_scope import check_creator_scope, load_workspace_scope
from influencer_os.validation import ValidationError, load_json, validate_file


TEMPLATE_PATH = Path(__file__).with_name("templates") / "content-calendar.html"
SOURCE_DIGEST_PATTERN = re.compile(
    r'<meta name="influencer-os-source-digest" content="([0-9a-f]{64})">'
)

PLATFORM_PRESENTATION = {
    "x": ("X", "#272725"),
    "instagram": ("Instagram", "#8e5b3f"),
    "tiktok": ("TikTok", "#343b43"),
    "substack": ("Substack", "#65733d"),
    "medium": ("Medium", "#49665b"),
    "reddit": ("Reddit", "#b54035"),
    "facebook": ("Facebook", "#46678c"),
    "linkedin": ("LinkedIn", "#2f6171"),
    "youtube": ("YouTube", "#b54035"),
    "multi-platform": ("Multiple platforms", "#7d6c9b"),
}

FORMAT_LABELS = {
    "format_short_form_video": "Short-form video",
    "format_carousel": "Carousel",
    "format_single_image_post": "Single image post",
    "format_story_sequence": "Story sequence",
    "format_article": "Article",
    "format_thread": "Thread",
}

RESEARCH_STATE_LABELS = {
    "unresearched": "Research pending",
    "candidates_ready": "Candidates ready",
    "selected": "Idea selected",
    "inherits_anchor": "Inherits anchor research",
}


def calendar_path_for(workspace_dir):
    return Path(workspace_dir) / "boards" / "content-calendar.html"


def schedule_research_state_errors(schedule):
    """Return cross-slot research-state errors that JSON Schema cannot express."""
    errors = []
    slots = schedule.get("calendar_slots", [])
    slot_ids = [slot["slot_id"] for slot in slots]
    duplicates = sorted(
        slot_id for slot_id, count in Counter(slot_ids).items() if count > 1
    )
    if duplicates:
        errors.append(f"content-schedule.json has duplicate slot_ids: {duplicates}")

    by_id = {slot["slot_id"]: slot for slot in slots}
    for slot in slots:
        slot_id = slot["slot_id"]
        state = slot["research_state"]
        state_status = state["status"]
        run_ids = state["research_run_ids"]
        selected_opportunity_id = state.get("selected_content_opportunity_id")
        selected_concept_id = state.get("selected_campaign_concept_id")
        selection = selected_opportunity_id or selected_concept_id
        anchor_id = state.get("anchor_slot_id")
        if selected_opportunity_id and selected_concept_id:
            errors.append(
                f"calendar slot {slot_id} selects both a content opportunity "
                "and a campaign concept; slot research resolves to exactly one"
            )
        if len(run_ids) != len(set(run_ids)):
            errors.append(
                f"calendar slot {slot_id} research_state contains duplicate research_run_ids"
            )
        if state_status == "unresearched":
            if run_ids or selection or anchor_id:
                errors.append(
                    f"calendar slot {slot_id} is unresearched but carries research, "
                    "selection, or anchor provenance"
                )
        elif state_status == "candidates_ready":
            if not run_ids or selection or anchor_id:
                errors.append(
                    f"calendar slot {slot_id} candidates_ready requires research_run_ids "
                    "and forbids a selection or anchor"
                )
        elif state_status == "selected":
            if not run_ids or not selection or anchor_id:
                errors.append(
                    f"calendar slot {slot_id} selected research requires research_run_ids "
                    "and exactly one of selected_content_opportunity_id or "
                    "selected_campaign_concept_id, with no anchor"
                )
        elif state_status == "inherits_anchor":
            if run_ids or selection or not anchor_id:
                errors.append(
                    f"calendar slot {slot_id} inherits_anchor requires anchor_slot_id "
                    "and forbids direct research or selection provenance"
                )
        if slot["status"] == "filled" and state_status not in {
            "selected",
            "inherits_anchor",
        }:
            errors.append(
                f"calendar slot {slot_id} is filled but research_state is "
                f"{state_status!r}; filled slots require selected research or an anchor"
            )
        if state_status != "inherits_anchor":
            continue
        if not anchor_id:
            continue
        if anchor_id == slot_id:
            errors.append(f"calendar slot {slot_id} cannot inherit research from itself")
            continue
        anchor = by_id.get(anchor_id)
        if anchor is None:
            errors.append(
                f"calendar slot {slot_id} inherits research from missing anchor {anchor_id}"
            )
            continue
        if slot["status"] == "filled" and anchor["research_state"]["status"] != "selected":
            errors.append(
                f"filled calendar slot {slot_id} inherits from {anchor_id}, but the "
                "anchor research_state is not selected"
            )
    return errors


def _source_digest(profile_path, schedule_path):
    digest = hashlib.sha256()
    for path in (profile_path, schedule_path, TEMPLATE_PATH, Path(__file__)):
        digest.update(path.name.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _load_sources(workspace_dir):
    workspace_dir = Path(workspace_dir)
    scope = load_workspace_scope(workspace_dir)
    profile_path = workspace_dir / "creator-profile.json"
    schedule_path = workspace_dir / "content-schedule.json"
    if not profile_path.exists():
        raise FileNotFoundError(f"Missing creator profile: {profile_path}")
    if not schedule_path.exists():
        raise FileNotFoundError(f"Missing creator content schedule: {schedule_path}")

    validate_file("creator-profile", profile_path)
    validate_file("creator-content-schedule", schedule_path)
    profile = load_json(profile_path)
    schedule = load_json(schedule_path)
    state_errors = schedule_research_state_errors(schedule)
    if state_errors:
        raise ValidationError("; ".join(state_errors))
    check_creator_scope(profile, scope, profile_path)
    check_creator_scope(schedule, scope, schedule_path)
    return profile_path, schedule_path, profile, schedule


def _choose_platform(slot, goal):
    if slot.get("platform"):
        return slot["platform"]
    preferred = goal["preferred_platforms"]
    return preferred[0] if len(preferred) == 1 else "multi-platform"


def _format_label(slot, goal):
    if slot.get("format_label"):
        return slot["format_label"]
    if slot.get("format_id"):
        return FORMAT_LABELS[slot["format_id"]]
    preferred = goal["preferred_formats"]
    if len(preferred) == 1:
        return FORMAT_LABELS[preferred[0]]
    return "Content slot"


def _project_events(schedule):
    goals = {goal["goal_id"]: goal for goal in schedule["content_goals"]}
    events = []
    for slot in schedule["calendar_slots"]:
        goal = goals.get(slot["content_goal_id"])
        if goal is None:
            raise ValidationError(
                f"calendar slot {slot['slot_id']} references unknown content goal "
                f"{slot['content_goal_id']!r}"
            )
        platform_id = _choose_platform(slot, goal)
        platform_label, color = PLATFORM_PRESENTATION[platform_id]
        events.append({
            "id": slot["slot_id"],
            "date": date.fromisoformat(slot["target_date"]),
            "platform_label": platform_label,
            "color": color,
            "format": _format_label(slot, goal),
            "title": slot.get("working_title") or slot["topic_cluster"],
            "week": slot.get("week_label", ""),
            "theme": slot.get("theme") or goal["description"],
            "pillar": goal["name"],
            "funnel": slot.get("funnel_role", ""),
            "cta": slot.get("cta", ""),
            "note": slot.get("production_note") or slot["date_flexibility"],
            "status": slot["status"],
            "research_state": RESEARCH_STATE_LABELS[
                slot["research_state"]["status"]
            ],
        })
    return sorted(events, key=lambda event: (event["date"], event["id"]))


def _month_sequence(events):
    first = events[0]["date"].replace(day=1)
    last = events[-1]["date"].replace(day=1)
    year, month = first.year, first.month
    while (year, month) <= (last.year, last.month):
        yield year, month
        month += 1
        if month == 13:
            year += 1
            month = 1


def _display_date(value):
    return f"{value.strftime('%B')} {value.day}, {value.year}"


def _detail_row(label, value):
    if not value:
        return ""
    return (
        '<span class="row"><span class="label">'
        f"{html.escape(label)}</span><span>{html.escape(str(value))}</span></span>"
    )


def _render_post(event):
    title = html.escape(event["title"], quote=True)
    details = "".join([
        _detail_row("Platform", event["platform_label"]),
        _detail_row("Format", event["format"]),
        _detail_row("Pillar", event["pillar"]),
        _detail_row("Funnel", event["funnel"]),
        _detail_row("CTA", event["cta"]),
        _detail_row("Status", event["status"]),
        _detail_row("Research", event["research_state"]),
        _detail_row("Note", event["note"]),
    ])
    return (
        f'<button class="post" style="--platform-color: {event["color"]}" '
        f'type="button" aria-label="{html.escape(event["platform_label"], quote=True)}: {title}">'
        f'<span class="platform">{html.escape(event["format"])}</span>'
        f'<span class="title">{title}</span>'
        '<span class="tooltip" role="tooltip">'
        f'<span><strong>{title}</strong>{html.escape(event["theme"])}</span>'
        f"{details}</span></button>"
    )


def _render_months(events):
    by_date = defaultdict(list)
    for event in events:
        by_date[event["date"]].append(event)

    rendered = []
    month_calendar = calendar.Calendar(firstweekday=6)
    for year, month in _month_sequence(events):
        month_events = [
            event for event in events
            if event["date"].year == year and event["date"].month == month
        ]
        cells = []
        for cell_date in month_calendar.itermonthdates(year, month):
            is_outside = cell_date.month != month
            day_events = [] if is_outside else by_date[cell_date]
            outside = " outside" if is_outside else ""
            week = f"W{html.escape(str(day_events[0]['week']))}" if day_events and day_events[0]["week"] else ""
            posts = "".join(_render_post(event) for event in day_events)
            cells.append(
                f'<div class="day{outside}"><div class="date"><span>{cell_date.day}</span>'
                f'<span class="week-tag">{week}</span></div><div class="posts">{posts}</div></div>'
            )
        weekdays = "".join(
            f'<div class="weekday">{day}</div>'
            for day in ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")
        )
        count = len(month_events)
        rendered.append(
            '<section class="month"><div class="month-title">'
            f"<h2>{calendar.month_name[month]} {year}</h2>"
            f'<span>{count} scheduled {"post" if count == 1 else "posts"}</span></div>'
            f'<div class="calendar">{weekdays}{"".join(cells)}</div></section>'
        )
    return "".join(rendered)


def _render_legend(events):
    seen = set()
    chips = []
    for event in events:
        key = (event["platform_label"], event["color"])
        if key in seen:
            continue
        seen.add(key)
        chips.append(
            '<span class="chip"><span class="dot" '
            f'style="--platform-color: {event["color"]}"></span>'
            f'{html.escape(event["platform_label"])}</span>'
        )
    return "".join(chips)


def _replace_once(template, placeholder, value):
    if template.count(placeholder) != 1:
        raise ValidationError(f"calendar template must contain exactly one {placeholder}")
    return template.replace(placeholder, value)


def _write_text_atomic(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", text=True
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "w") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise


def rebuild_calendar(workspace_path):
    workspace_dir = Path(workspace_path)
    profile_path, schedule_path, profile, schedule = _load_sources(workspace_dir)
    events = _project_events(schedule)
    if not events:
        raise ValidationError("content-schedule.json has no calendar slots to render")

    source_digest = _source_digest(profile_path, schedule_path)
    output = _render_calendar_document(
        profile_path, schedule_path, profile, schedule, events
    )
    output_path = calendar_path_for(workspace_dir)
    _write_text_atomic(output_path, output)
    return {
        "calendar_path": output_path,
        "post_count": len(events),
        "source_digest": source_digest,
    }


def _render_calendar_document(profile_path, schedule_path, profile, schedule, events):
    source_digest = _source_digest(profile_path, schedule_path)
    research_status = schedule["research_basis"]["status"]
    state_counts = Counter(
        slot["research_state"]["status"] for slot in schedule["calendar_slots"]
    )
    status_label = (
        "Rolling content calendar - "
        f"{state_counts['selected']} selected, "
        f"{state_counts['candidates_ready']} candidates ready, "
        f"{state_counts['unresearched']} research pending, "
        f"{state_counts['inherits_anchor']} inherit anchor"
    )
    description = {
        "strategy_scaffold": (
            "A planning scaffold derived from the accepted content strategy. "
            "Each slot remains provisional until its own research status advances."
        ),
        "research_informed": (
            "The baseline strategy has been informed by current research. Each slot remains "
            "gated by its own research status; hover or focus a post for details."
        ),
    }[research_status]
    replacements = {
        "__SOURCE_DIGEST__": source_digest,
        "__DOCUMENT_TITLE__": html.escape(f"{profile['display_name']} Content Calendar"),
        "__HEADING__": html.escape(f"{profile['display_name']} Content Calendar"),
        "__DESCRIPTION__": html.escape(description),
        "__SCHEDULE_WINDOW__": html.escape(
            f"{_display_date(events[0]['date'])} - {_display_date(events[-1]['date'])}"
        ),
        "__STATUS__": html.escape(status_label),
        "__SCHEDULING_NOTE__": html.escape(schedule["cadence_expectations"]),
        "__LEGEND__": _render_legend(events),
        "__MONTHS__": _render_months(events),
        "__GUARDRAIL_NOTE__": html.escape(
            "This is a rebuildable planning view. content-schedule.json remains the source of truth."
        ),
    }
    output = TEMPLATE_PATH.read_text()
    for placeholder, value in replacements.items():
        output = _replace_once(output, placeholder, value)
    return output


def validate_calendar(workspace_path):
    workspace_dir = Path(workspace_path)
    profile_path, schedule_path, _profile, schedule = _load_sources(workspace_dir)
    output_path = calendar_path_for(workspace_dir)
    if not output_path.exists():
        raise FileNotFoundError(
            f"Missing content calendar: {output_path} (run rebuild-calendar)"
        )
    match = SOURCE_DIGEST_PATTERN.search(output_path.read_text())
    if match is None:
        raise ValidationError(
            f"{output_path}: missing InfluencerOS source digest (run rebuild-calendar)"
        )
    expected = _source_digest(profile_path, schedule_path)
    if match.group(1) != expected:
        raise ValidationError(
            f"{output_path}: stale content calendar projection (run rebuild-calendar)"
        )
    events = _project_events(schedule)
    expected_output = _render_calendar_document(
        profile_path, schedule_path, _profile, schedule, events
    )
    if output_path.read_text() != expected_output:
        raise ValidationError(
            f"{output_path}: content calendar does not match canonical sources "
            "(run rebuild-calendar)"
        )
    return {
        "calendar_path": output_path,
        "post_count": len(events),
        "source_digest": expected,
    }
