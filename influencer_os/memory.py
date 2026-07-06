"""Bounded memory and learnings writes (ADR 0016, ADR 0008).

`write_memory_fact` performs the deduplicated, capped `MEMORY.md` writes the
`memory-write` skill relies on; the 2,500-byte cap is checked before every
write. `append_skill_learning` appends dated per-skill entries to a learnings
file for the `wrap-up` skill. `append_creator_lesson` appends evidence-linked
creator lessons to a Creator Workspace `memory/learnings.md` for the
`distill-creator-learning` skill: every lesson must resolve to real workspace
records at write time, and `validate_creator_lessons` re-checks the same rule
at rest (Phase 2 exit criterion 4).
"""

import datetime
import re
from pathlib import Path

from influencer_os.validation import ValidationError, load_json


MEMORY_BYTE_CAP = 2500
DEFAULT_MEMORY_SECTION = "Active Threads"

LEARNINGS_SKILLS_HEADING = "## Individual Skills"
LEARNINGS_SCAFFOLD = """# Learnings

## General

## Individual Skills
"""

CREATOR_LESSONS_HEADING = "## Creator Lessons"

# Pinned to performance-summary.schema.json distilled_lessons
# evidence_strength (enum drift check in tests/test_creator_lessons.py).
EVIDENCE_STRENGTHS = ("single_post_signal", "multi_post_pattern", "weak_signal")

# A creator lesson is one parseable line so the at-rest validator can re-check
# every write-time rule: dated, strength-marked, evidence-linked (ADR 0008).
CREATOR_LESSON_ENTRY_PATTERN = re.compile(
    r"^- (?P<date>\d{4}-\d{2}-\d{2}) \[(?P<strength>[a-z_]+)\]: "
    r"(?P<lesson>.+) \(evidence: (?P<evidence>[^()]+)\)$"
)

# Evidence ids resolve against the performance chain records on disk; any
# other prefix fails closed. Filename==id is validator-enforced for the
# per-record directories, and the singleton records carry their id field.
EVIDENCE_ID_PREFIXES = (
    "performance_summary_",
    "analytics_snapshot_",
    "ppr_",
    "project_",
    "output_package_",
)


def write_memory_fact(memory_path, fact, section=DEFAULT_MEMORY_SECTION):
    memory_path = Path(memory_path)
    if not memory_path.exists():
        raise FileNotFoundError(
            f"Missing memory file: {memory_path} (scaffold it before writing facts)"
        )

    fact_text = " ".join(fact.split())
    if not fact_text:
        raise ValidationError("memory fact must not be empty")

    content = memory_path.read_text()
    if fact_text in content:
        return {
            "status": "duplicate",
            "bytes_used": len(content.encode("utf-8")),
            "byte_cap": MEMORY_BYTE_CAP,
        }

    sections = re.findall(r"^## (.+)$", content, flags=re.MULTILINE)
    if section not in sections:
        raise ValidationError(
            f"memory section {section!r} not found in {memory_path}; available sections: {sections}"
        )

    updated = _insert_line_in_section(content, f"## {section}", f"- {fact_text}", ("## ", "# "))
    bytes_used = len(updated.encode("utf-8"))
    if bytes_used > MEMORY_BYTE_CAP:
        raise ValidationError(
            f"write would put {memory_path} at {bytes_used} bytes, over the "
            f"{MEMORY_BYTE_CAP}-byte cap; consolidate existing entries first"
        )

    memory_path.write_text(updated)
    return {"status": "written", "bytes_used": bytes_used, "byte_cap": MEMORY_BYTE_CAP}


def append_skill_learning(learnings_path, skill_name, entry, entry_date):
    learnings_path = Path(learnings_path)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", entry_date):
        raise ValidationError(f"entry date must be YYYY-MM-DD, got {entry_date!r}")

    entry_text = " ".join(entry.split())
    if not entry_text:
        raise ValidationError("learning entry must not be empty")

    if learnings_path.exists():
        content = learnings_path.read_text()
    else:
        content = LEARNINGS_SCAFFOLD

    if not _has_heading(content, LEARNINGS_SKILLS_HEADING):
        content = content.rstrip("\n") + f"\n\n{LEARNINGS_SKILLS_HEADING}\n"

    skill_heading = f"### {skill_name}"
    if not _has_heading(content, skill_heading):
        content = _insert_line_in_section(
            content, LEARNINGS_SKILLS_HEADING, f"\n{skill_heading}\n", ("## ", "# ")
        )

    skill_section = _section_body(content, skill_heading, ("### ", "## ", "# "))
    if f": {entry_text}" in skill_section:
        return {"status": "duplicate", "path": learnings_path}

    updated = _insert_line_in_section(
        content, skill_heading, f"- {entry_date}: {entry_text}", ("### ", "## ", "# ")
    )
    learnings_path.write_text(updated)
    return {"status": "written", "path": learnings_path}


def creator_lessons_workspace(learnings_path):
    """The owning Creator Workspace when the path is a creator memory ledger.

    Detection is deterministic: `<workspace>/memory/learnings.md` beside a
    `creator-workspace.json` manifest. Everything else (root
    `context/learnings.md`, ad-hoc files) is a per-skill learnings file.
    """
    learnings_path = Path(learnings_path)
    if learnings_path.name != "learnings.md" or learnings_path.parent.name != "memory":
        return None
    workspace_dir = learnings_path.parent.parent
    if not (workspace_dir / "creator-workspace.json").exists():
        return None
    return workspace_dir


def resolve_workspace_evidence(workspace_dir, evidence_ids):
    """Every evidence id must resolve to a performance-chain record on disk."""
    workspace_dir = Path(workspace_dir)
    unsupported = sorted(
        evidence_id
        for evidence_id in evidence_ids
        if not evidence_id.startswith(EVIDENCE_ID_PREFIXES)
    )
    if unsupported:
        raise ValidationError(
            "creator lesson evidence ids must use a performance-chain prefix "
            f"{sorted(EVIDENCE_ID_PREFIXES)}: {unsupported}"
        )
    known_ids = _workspace_evidence_ids(workspace_dir)
    dangling = sorted(set(evidence_ids) - known_ids)
    if dangling:
        raise ValidationError(
            "creator lesson evidence ids do not resolve to records in "
            f"{workspace_dir}: {dangling}"
        )


def append_creator_lesson(workspace_dir, topic, lesson, evidence_ids, strength, entry_date):
    """Append one evidence-linked creator lesson to memory/learnings.md.

    Creator lessons are distilled judgments (ADR 0008): dated, marked with an
    honest evidence-strength scope, grouped under a `### <topic>` heading that
    mirrors the PerformanceSummary `applies_to` vocabulary, and linked to the
    workspace records that back them.
    """
    workspace_dir = Path(workspace_dir)
    learnings_path = workspace_dir / "memory" / "learnings.md"

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", entry_date or ""):
        raise ValidationError(f"entry date must be YYYY-MM-DD, got {entry_date!r}")
    _require_real_date(entry_date)

    topic_text = " ".join((topic or "").split())
    if not topic_text:
        raise ValidationError("creator lesson topic must not be empty")
    lesson_text = " ".join((lesson or "").split())
    if not lesson_text:
        raise ValidationError("creator lesson must not be empty")
    if not evidence_ids:
        raise ValidationError(
            "creator lessons require at least one evidence id "
            "(--evidence; ADR 0008: lessons stay traceable to evidence)"
        )
    if strength not in EVIDENCE_STRENGTHS:
        raise ValidationError(
            f"creator lesson evidence strength must be one of {list(EVIDENCE_STRENGTHS)}, "
            f"got {strength!r}"
        )
    resolve_workspace_evidence(workspace_dir, evidence_ids)

    entry_line = (
        f"- {entry_date} [{strength}]: {lesson_text} "
        f"(evidence: {', '.join(evidence_ids)})"
    )
    if CREATOR_LESSON_ENTRY_PATTERN.match(entry_line) is None:
        raise ValidationError(
            "creator lesson text breaks the parseable entry format; remove "
            "any '(evidence: ...)'-shaped fragment from the lesson"
        )

    if learnings_path.exists():
        content = learnings_path.read_text()
    else:
        content = "# Learnings\n"

    if not _has_heading(content, CREATOR_LESSONS_HEADING):
        content = content.rstrip("\n") + f"\n\n{CREATOR_LESSONS_HEADING}\n"

    section_start, section_end = _section_bounds(
        content, CREATOR_LESSONS_HEADING, ("## ", "# ")
    )
    topic_heading = f"### {topic_text}"
    lines = content.splitlines()
    section_lines = lines[section_start + 1 : section_end]

    if f"]: {lesson_text} (evidence:" in "\n".join(section_lines):
        return {"status": "duplicate", "path": learnings_path}

    if not any(line.strip() == topic_heading for line in section_lines):
        content = _insert_line_in_section(
            content, CREATOR_LESSONS_HEADING, f"\n{topic_heading}\n", ("## ", "# ")
        )

    updated = _insert_line_in_subsection(
        content, CREATOR_LESSONS_HEADING, topic_heading, entry_line
    )
    learnings_path.parent.mkdir(parents=True, exist_ok=True)
    learnings_path.write_text(updated)
    return {"status": "written", "path": learnings_path}


def validate_creator_lessons(workspace_dir):
    """At-rest re-check of every write-time creator-lesson rule.

    A hand-edited `memory/learnings.md` must fail the same way the writer
    would have: every bullet under `## Creator Lessons` must parse, carry a
    known evidence strength and a real date, and cite evidence ids that
    resolve to workspace records (Phase 2 exit criterion 4). Content outside
    the Creator Lessons section is not policed here.
    """
    workspace_dir = Path(workspace_dir)
    learnings_path = workspace_dir / "memory" / "learnings.md"
    if not learnings_path.exists():
        return {"lesson_count": 0}

    content = learnings_path.read_text()
    if not _has_heading(content, CREATOR_LESSONS_HEADING):
        return {"lesson_count": 0}

    section_start, section_end = _section_bounds(
        content, CREATOR_LESSONS_HEADING, ("## ", "# ")
    )
    lines = content.splitlines()
    lesson_count = 0
    for offset, line in enumerate(lines[section_start + 1 : section_end]):
        line_number = section_start + 2 + offset
        stripped = line.strip()
        if not stripped or stripped.startswith("### "):
            continue
        match = CREATOR_LESSON_ENTRY_PATTERN.match(line)
        if match is None:
            raise ValidationError(
                f"{learnings_path}:{line_number}: creator lessons must be "
                "'- YYYY-MM-DD [strength]: lesson (evidence: id, ...)' "
                f"entries or '### <topic>' headings, got: {stripped!r}"
            )
        _require_real_date(match["date"], context=f"{learnings_path}:{line_number}")
        if match["strength"] not in EVIDENCE_STRENGTHS:
            raise ValidationError(
                f"{learnings_path}:{line_number}: unknown evidence strength "
                f"{match['strength']!r}; expected one of {list(EVIDENCE_STRENGTHS)}"
            )
        evidence_ids = [part.strip() for part in match["evidence"].split(",")]
        if not all(evidence_ids):
            raise ValidationError(
                f"{learnings_path}:{line_number}: empty evidence id in "
                f"{match['evidence']!r}"
            )
        resolve_workspace_evidence(workspace_dir, evidence_ids)
        lesson_count += 1
    return {"lesson_count": lesson_count}


def _require_real_date(value, context=None):
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        prefix = f"{context}: " if context else ""
        raise ValidationError(f"{prefix}not a real calendar date: {value!r}") from None


def _workspace_evidence_ids(workspace_dir):
    """All performance-chain record ids present in a workspace's projects."""
    projects_dir = Path(workspace_dir) / "projects"
    known = set()
    if not projects_dir.is_dir():
        return known
    for project_dir in sorted(projects_dir.iterdir()):
        if not project_dir.is_dir():
            continue
        for relative_path, id_field in (
            ("project.json", "project_id"),
            ("output-package/output-package.json", "output_package_id"),
            ("performance-summary.json", "performance_summary_id"),
        ):
            known.update(_record_id(project_dir / relative_path, id_field))
        for directory, id_field in (
            ("published/published-post-records", "published_post_record_id"),
            ("analytics/snapshots", "analytics_snapshot_id"),
        ):
            records_dir = project_dir / directory
            if not records_dir.is_dir():
                continue
            for record_path in sorted(records_dir.glob("*.json")):
                known.update(_record_id(record_path, id_field))
    return known


def _record_id(record_path, id_field):
    if not record_path.is_file():
        return []
    try:
        record = load_json(record_path)
    except (ValueError, OSError):
        # An unreadable or malformed record resolves nothing here; it fails
        # its own schema validation elsewhere.
        return []
    value = record.get(id_field) if isinstance(record, dict) else None
    return [value] if isinstance(value, str) else []


def _has_heading(content, heading):
    return any(line.strip() == heading for line in content.splitlines())


def _insert_line_in_section(content, heading, new_line, stop_prefixes):
    lines = content.splitlines()
    start = next(
        (index for index, line in enumerate(lines) if line.strip() == heading), None
    )
    if start is None:
        raise ValidationError(f"missing heading {heading!r}")

    end = len(lines)
    for index in range(start + 1, len(lines)):
        if any(lines[index].startswith(prefix) for prefix in stop_prefixes):
            end = index
            break

    insert_at = end
    while insert_at > start + 1 and lines[insert_at - 1].strip() == "":
        insert_at -= 1
    if insert_at == start + 1 and end > start + 1 and lines[start + 1].strip() == "":
        insert_at = start + 2

    lines[insert_at:insert_at] = new_line.splitlines() if "\n" in new_line else [new_line]
    return "\n".join(lines) + "\n"


def _section_bounds(content, heading, stop_prefixes):
    """(heading line index, section end index) for a `## `-level heading."""
    lines = content.splitlines()
    start = next(
        (index for index, line in enumerate(lines) if line.strip() == heading), None
    )
    if start is None:
        raise ValidationError(f"missing heading {heading!r}")
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if any(lines[index].startswith(prefix) for prefix in stop_prefixes):
            end = index
            break
    return start, end


def _insert_line_in_subsection(content, parent_heading, sub_heading, new_line):
    """Insert under a `### ` heading scoped to its parent `## ` section.

    _insert_line_in_section matches the first heading anywhere in the file; a
    creator-lesson topic could collide with an Individual Skills skill name,
    so the topic heading is located inside the parent section bounds.
    """
    section_start, section_end = _section_bounds(content, parent_heading, ("## ", "# "))
    lines = content.splitlines()
    sub_start = next(
        (
            index
            for index in range(section_start + 1, section_end)
            if lines[index].strip() == sub_heading
        ),
        None,
    )
    if sub_start is None:
        raise ValidationError(f"missing heading {sub_heading!r} under {parent_heading!r}")

    sub_end = section_end
    for index in range(sub_start + 1, section_end):
        if lines[index].startswith("### "):
            sub_end = index
            break

    insert_at = sub_end
    while insert_at > sub_start + 1 and lines[insert_at - 1].strip() == "":
        insert_at -= 1
    if insert_at == sub_start + 1 and sub_end > sub_start + 1 and lines[sub_start + 1].strip() == "":
        insert_at = sub_start + 2

    lines[insert_at:insert_at] = [new_line]
    return "\n".join(lines) + "\n"


def _section_body(content, heading, stop_prefixes):
    lines = content.splitlines()
    start = next(
        (index for index, line in enumerate(lines) if line.strip() == heading), None
    )
    if start is None:
        return ""
    body = []
    for line in lines[start + 1 :]:
        if any(line.startswith(prefix) for prefix in stop_prefixes):
            break
        body.append(line)
    return "\n".join(body)
