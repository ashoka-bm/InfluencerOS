"""Bounded memory and learnings writes (ADR 0016).

`write_memory_fact` performs the deduplicated, capped `MEMORY.md` writes the
`memory-write` skill relies on; the 2,500-byte cap is checked before every
write. `append_skill_learning` appends dated per-skill entries to a learnings
file for the `wrap-up` skill.
"""

import re
from pathlib import Path

from influencer_os.validation import ValidationError


MEMORY_BYTE_CAP = 2500
DEFAULT_MEMORY_SECTION = "Active Threads"

LEARNINGS_SKILLS_HEADING = "## Individual Skills"
LEARNINGS_SCAFFOLD = """# Learnings

## General

## Individual Skills
"""


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
