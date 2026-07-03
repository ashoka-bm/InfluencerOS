import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# The canonical read order lives once in AGENTS.md (ADR 0019). This list is the
# drift check's fixed expectation: removing a doc from AGENTS.md fails here.
REQUIRED_READ_ORDER_DOCS = (
    "CONTEXT.md",
    "docs/os-construction/prd.md",
    "docs/os-construction/roadmap.md",
    "docs/os-construction/short-term-plan.md",
    "docs/os-construction/repository-map.md",
    "docs/os-construction/architecture-map.md",
    "docs/os-construction/agentic-os-alignment.md",
    "docs/os-construction/agentic-os-copy-plan.md",
    "docs/os-construction/agentic-os-parity-plan.md",
    "docs/os-construction/divergence-test.md",
    "docs/os-construction/visual-architecture-maps.md",
    "docs/os-construction/context-matrix.md",
    "docs/os-construction/skill-registry.md",
    "ARCHITECTURE.md",
    "docs/pipeline-contract.md",
)

THIN_ADAPTERS = ("CLAUDE.md", "SOUL.md")

REGISTRY_PATH = "docs/os-construction/skill-registry.md"
MATRIX_PATH = "docs/os-construction/context-matrix.md"
INSTALLED_REGISTRY_SECTIONS = ("Core Workflow Skills", "Creator Setup Subskills", "System Skills")
FUTURE_REGISTRY_SECTION = "Missing Future Skills"
PERSONAL_BRAND_AUDIENCE_TERMS = (
    "audience language",
    "jobs-to-be-done",
    "tried alternatives",
    "objections",
    "trigger moments",
    "trusted sources",
    "negative audience",
    "proof and trust cues",
)

# A numbered list entry pointing at a durable doc, e.g. "3. `docs/...`":
# thin adapters must not restate the read order in any form (ADR 0019).
NUMBERED_DOC_LINE = re.compile(r"^\s*\d+\.\s+`(?:docs/|CONTEXT\.md|ARCHITECTURE\.md)")


def read_repo_text(relative_path):
    return (ROOT / relative_path).read_text()


def markdown_section(text, heading):
    match = re.search(
        rf"^## {re.escape(heading)}$(.*?)(?=^## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"missing markdown section: ## {heading}")
    return match.group(1)


def table_skill_names(section_text):
    return set(re.findall(r"^\|\s*`([a-z0-9-]+)`\s*\|", section_text, flags=re.MULTILINE))


def table_workflow_names(section_text):
    names = set()
    for line in section_text.splitlines():
        match = re.match(r"^\|\s*([^|`]+?)\s*\|", line)
        if match is None:
            continue
        cell = match.group(1)
        if cell == "Workflow" or set(cell) <= {"-", " "}:
            continue
        names.add(cell)
    return names


def skills_on_disk():
    return {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")}


class AdapterDriftTests(unittest.TestCase):
    def test_agents_read_order_lists_every_required_doc(self):
        read_order = markdown_section(read_repo_text("AGENTS.md"), "Read Order")
        for doc in REQUIRED_READ_ORDER_DOCS:
            self.assertIn(f"`{doc}`", read_order, f"AGENTS.md read order is missing `{doc}`")

    def test_read_order_docs_exist_on_disk(self):
        for doc in REQUIRED_READ_ORDER_DOCS:
            self.assertTrue((ROOT / doc).exists(), f"read-order doc missing on disk: {doc}")

    def test_source_of_truth_paths_exist_on_disk(self):
        source_section = markdown_section(read_repo_text("AGENTS.md"), "Source Of Truth")
        paths = re.findall(r"`([^`]+)`", source_section)
        self.assertTrue(paths, "AGENTS.md Source Of Truth names no paths")
        for path in paths:
            self.assertTrue((ROOT / path).exists(), f"source-of-truth path missing on disk: {path}")

    def test_thin_adapters_import_agents(self):
        for adapter in THIN_ADAPTERS:
            self.assertIn("@AGENTS.md", read_repo_text(adapter), f"{adapter} must import AGENTS.md")

    def test_thin_adapters_restate_no_read_order(self):
        for adapter in THIN_ADAPTERS:
            text = read_repo_text(adapter)
            self.assertNotIn(
                "## Read Order", text, f"{adapter} restates a read order; AGENTS.md owns it"
            )
            for line in text.splitlines():
                self.assertIsNone(
                    NUMBERED_DOC_LINE.match(line),
                    f"{adapter} restates an ordered doc list: {line.strip()}",
                )


class SkillRegistryDriftTests(unittest.TestCase):
    def setUp(self):
        registry = read_repo_text(REGISTRY_PATH)
        self.disk_skills = skills_on_disk()
        self.installed = set()
        for heading in INSTALLED_REGISTRY_SECTIONS:
            self.installed |= table_skill_names(markdown_section(registry, heading))
        self.future = table_skill_names(markdown_section(registry, FUTURE_REGISTRY_SECTION))

    def test_every_skill_on_disk_has_an_installed_registry_row(self):
        missing = sorted(self.disk_skills - self.installed)
        self.assertEqual(missing, [], f"skills on disk without a registry row: {missing}")

    def test_every_installed_registry_row_has_a_skill_on_disk(self):
        stale = sorted(self.installed - self.disk_skills)
        self.assertEqual(stale, [], f"registry rows without a skill on disk: {stale}")

    def test_future_registry_rows_are_not_yet_on_disk(self):
        built = sorted(self.future & self.disk_skills)
        self.assertEqual(
            built,
            [],
            "skills listed as future but present on disk; "
            f"move their rows to an installed table: {built}",
        )


class ContextMatrixDriftTests(unittest.TestCase):
    def setUp(self):
        matrix = read_repo_text(MATRIX_PATH)
        workflow_rows = set()
        for heading in ("OS Scope", "Creator Scope"):
            workflow_rows |= table_workflow_names(markdown_section(matrix, heading))
        self.workflows = {name.casefold() for name in workflow_rows}
        self.coverage = dict(
            re.findall(
                r"^\|\s*`([a-z0-9-]+)`\s*\|\s*([^|]+?)\s*\|",
                markdown_section(matrix, "Skill Coverage"),
                flags=re.MULTILINE,
            )
        )

    def test_every_skill_on_disk_has_matrix_coverage(self):
        missing = sorted(skills_on_disk() - set(self.coverage))
        self.assertEqual(missing, [], f"skills on disk without context-matrix coverage: {missing}")

    def test_coverage_rows_name_known_workflows(self):
        self.assertTrue(self.workflows, "context matrix defines no workflow rows")
        for skill, coverage in self.coverage.items():
            for item in coverage.split(","):
                workflow = item.strip()
                self.assertIn(
                    workflow.casefold(),
                    self.workflows,
                    f"`{skill}` coverage names an unknown workflow: {workflow}",
                )


class CreatorSetupTemplateDriftTests(unittest.TestCase):
    def test_personal_brand_template_and_skill_keep_icp_grade_audience_fields(self):
        template = read_repo_text("docs/templates/creator-setup/personal-brand.md").lower()
        skill = read_repo_text("skills/create-personal-brand/SKILL.md").lower()
        for term in PERSONAL_BRAND_AUDIENCE_TERMS:
            self.assertIn(
                term,
                template,
                f"personal-brand template no longer asks for `{term}`",
            )
            self.assertIn(
                term,
                skill,
                f"create-personal-brand skill no longer extracts `{term}`",
            )


def frontmatter_dependencies(skill_name):
    text = read_repo_text(f"skills/{skill_name}/SKILL.md")
    match = re.match(r"^---\n(.*?)\n---", text, flags=re.DOTALL)
    if match is None:
        return None
    frontmatter = match.group(1)
    if re.search(r"^dependencies:\s*\[\s*\]\s*$", frontmatter, flags=re.MULTILINE):
        return []
    block = re.search(
        r"^dependencies:\n((?:\s+-\s+.+\n?)+)", frontmatter, flags=re.MULTILINE
    )
    if block is None:
        return None
    return re.findall(r"-\s+([a-z0-9-]+)", block.group(1))


def skill_body(skill_name):
    text = read_repo_text(f"skills/{skill_name}/SKILL.md")
    return text.split("---", 2)[2] if text.startswith("---") else text


class ConductorCallGraphDriftTests(unittest.TestCase):
    CONDUCTORS = ("influencer-os", "create-influencer")
    MAP_SECTION = "Creation-Flow Call Graph (skill → skill)"

    def test_conductors_declare_dependencies_frontmatter(self):
        for skill in self.CONDUCTORS:
            deps = frontmatter_dependencies(skill)
            self.assertTrue(
                deps,
                f"skills/{skill}/SKILL.md declares no `dependencies` frontmatter (ADR 0017)",
            )

    def test_dependencies_exist_on_disk_or_are_planned_with_halt(self):
        for skill in sorted(skills_on_disk()):
            deps = frontmatter_dependencies(skill)
            if not deps:
                continue
            body = skill_body(skill)
            for dep in deps:
                if (ROOT / "skills" / dep / "SKILL.md").exists():
                    continue
                planned_lines = [
                    line for line in body.splitlines() if dep in line and "[PLANNED" in line
                ]
                self.assertTrue(
                    planned_lines,
                    f"skills/{skill} depends on missing skill {dep!r} "
                    "without a [PLANNED] marker in its body",
                )
                self.assertIn(
                    "halt",
                    body.lower(),
                    f"skills/{skill} names [PLANNED] dependencies but declares no halt instruction",
                )

    def test_dependencies_are_registered(self):
        registry = read_repo_text(REGISTRY_PATH)
        known = set()
        for heading in INSTALLED_REGISTRY_SECTIONS + (FUTURE_REGISTRY_SECTION,):
            known |= table_skill_names(markdown_section(registry, heading))
        for skill in sorted(skills_on_disk()):
            deps = frontmatter_dependencies(skill)
            for dep in deps or []:
                self.assertIn(
                    dep, known, f"skills/{skill} depends on unregistered skill {dep!r}"
                )

    def test_content_conductor_declares_phase_owners(self):
        body = skill_body("influencer-os")
        self.assertIn("## Phase Owners", body, "influencer-os declares no phase-to-owner table")
        owners_section = body.split("## Phase Owners")[1]
        for dep in frontmatter_dependencies("influencer-os"):
            self.assertIn(
                dep, owners_section, f"phase-owner table names no phase for dependency {dep!r}"
            )

    def test_conductor_frontmatter_matches_architecture_map(self):
        map_text = read_repo_text("docs/os-construction/architecture-map.md")
        section = markdown_section(map_text, self.MAP_SECTION)
        fences = re.findall(r"```text\n(.*?)```", section, flags=re.DOTALL)
        for skill in self.CONDUCTORS:
            fence = next((f for f in fences if f"skills/{skill}/SKILL.md" in f), None)
            self.assertIsNotNone(
                fence, f"architecture-map call graph has no fence for skills/{skill}"
            )
            map_skills = set(re.findall(r"Skill\((?:skill: \")?([a-z0-9-]+)\"?\)", fence))
            self.assertEqual(
                map_skills,
                set(frontmatter_dependencies(skill) or []),
                f"architecture-map call graph and skills/{skill} `dependencies` frontmatter disagree",
            )


class MemoryPolicyDriftTests(unittest.TestCase):
    def test_root_memory_stays_within_byte_cap(self):
        from influencer_os.memory import MEMORY_BYTE_CAP

        size = len((ROOT / "context" / "MEMORY.md").read_bytes())
        self.assertLessEqual(
            size,
            MEMORY_BYTE_CAP,
            f"context/MEMORY.md is {size} bytes, over the {MEMORY_BYTE_CAP}-byte cap; consolidate it",
        )

    def test_conductor_skills_carry_rules_and_self_update(self):
        for skill in ("influencer-os", "create-influencer"):
            text = read_repo_text(f"skills/{skill}/SKILL.md")
            for heading in ("## Rules", "## Self-Update"):
                self.assertIn(heading, text, f"skills/{skill}/SKILL.md is missing {heading} (ADR 0016)")

    def test_worked_local_override_exists(self):
        overrides = list((ROOT / "skills").glob("*/SKILL.local.md"))
        self.assertTrue(
            overrides,
            "no skills/*/SKILL.local.md worked example exists (ADR 0016 requires at least one)",
        )


if __name__ == "__main__":
    unittest.main()
