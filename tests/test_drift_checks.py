import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Canonical ADR 0020 research enums. The validator resolves only intra-file
# $ref, so every research-module schema repeats these; this check pins each
# copy to the one canonical list. Legacy compatibility records (social
# research packs) are deliberately out of scope.
RESEARCH_PLATFORMS = ["x", "instagram", "tiktok", "substack", "medium", "reddit", "facebook", "linkedin", "youtube"]
RESEARCH_SOURCE_PLATFORMS = RESEARCH_PLATFORMS + ["public_web"]
RESEARCH_CONTENT_TYPES = [
    "x_post", "x_thread",
    "instagram_reel", "instagram_post", "instagram_story", "instagram_carousel",
    "tiktok_video",
    "substack_article", "substack_note",
    "medium_article",
    "reddit_thread", "reddit_comment",
    "facebook_post", "facebook_reel",
    "linkedin_post", "linkedin_article",
    "youtube_video", "youtube_short", "youtube_comment",
]
RESEARCH_SOURCE_CONTENT_TYPES = RESEARCH_CONTENT_TYPES + [
    "public_web_page", "institutional_article", "research_article",
]
RESEARCH_MODULE_SCHEMAS = (
    "creator-content-schedule", "research-run", "research-evidence", "metric-snapshot",
    "research-findings", "stable-finding", "research-sources", "research-hashtags",
    "research-search-terms", "reference-creators", "research-watchlist",
    "idea-queue-entry", "idea-queue", "idea-promotion", "project-warning",
    "content-board", "automation-run", "system-event",
)
# The closed v1 format vocabulary (approval-surface decisions, 2026-07-03).
# Text formats joined in Phase 1 slice 6; multi-platform packaging is still
# deferred until it has a production plan contract.
RESEARCH_FORMATS = [
    "format_short_form_video", "format_carousel",
    "format_single_image_post", "format_story_sequence",
    "format_article", "format_thread",
]
# project.schema.json caches both enums in source_refs (source_platforms /
# source_platform_content_types), output-package embeds format_id twice, and
# applied-social-template carries the plan-layer target_format_id; those
# copies must stay pinned too.
ENUM_PINNED_SCHEMAS = RESEARCH_MODULE_SCHEMAS + (
    "project", "output-package", "applied-social-template", "creator-profile",
)
PLATFORM_PROPERTY_NAMES = {
    "platform", "platforms", "active_platforms", "approved_platforms",
    "platform_recommendations", "preferred_platforms", "source_platforms",
    "primary_surfaces",
}
CONTENT_TYPE_PROPERTY_NAMES = {"platform_content_type", "source_platform_content_types"}
FORMAT_PROPERTY_NAMES = {
    "approved_formats", "format_recommendations", "target_formats",
    "preferred_formats", "format_id", "target_format_id",
}
# Pinned-name properties that legitimately carry no enum: the output-package
# platform adaptation targets the open distribution-surface vocabulary
# (youtube_shorts et al.), which closes in the production build-out.
ENUM_EXEMPT_PROPERTIES = {("output-package", "platform")}
SOURCE_PROVENANCE_PLATFORM_LOCATIONS = {
    "project.properties.source_refs.source_platforms",
    "research-evidence.platform",
    "research-run.platforms",
    "research-search-plan.platforms",
    "research-search-plan.properties.planned_queries.items.platform",
    "research-search-plan.properties.planned_sources.items.platform",
    "research-search-plan.properties.skipped_sources.items.platform",
    "research-sources.properties.items.items.platform",
    "research-search-terms.properties.items.items.platform",
    "research-source-yield.platform",
    "metric-snapshot.platform",
}
SOURCE_PROVENANCE_CONTENT_TYPE_LOCATIONS = {
    "project.properties.source_refs.source_platform_content_types",
    "research-evidence.platform_content_type",
}

# The Content Beat Spine (ADR 0024): every beat_role / hook_category enum
# copy across schemas must match the canonical constants in validation.py.
BEAT_ROLES = ["hook", "retain", "payoff", "cta", "packaging"]
HOOK_CATEGORIES = [
    "identity_call_out", "pattern_interrupt", "contrarian", "result_first",
    "curiosity_gap", "direct_challenge", "confession", "timeliness",
    "problem_solution", "reveal_teaser", "bold_promise",
]
BEAT_SPINE_SCHEMAS = ("social-template", "applied-social-template")
BEAT_ROLE_PROPERTY_NAMES = {"beat_role"}
HOOK_CATEGORY_PROPERTY_NAMES = {"hook_category"}

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


class RepositoryHygieneTests(unittest.TestCase):
    def test_python_project_metadata_exists(self):
        pyproject = ROOT / "pyproject.toml"
        self.assertTrue(pyproject.exists(), "pyproject.toml is required for Python version and test metadata")
        text = pyproject.read_text()
        self.assertIn("requires-python", text)
        self.assertIn("unittest", text)

    def test_ci_runs_unit_and_example_validation_floor(self):
        workflow_dir = ROOT / ".github" / "workflows"
        workflows = list(workflow_dir.glob("*.yml")) + list(workflow_dir.glob("*.yaml"))
        self.assertTrue(workflows, "a GitHub Actions workflow is required for the verification floor")
        combined = "\n".join(path.read_text() for path in workflows)
        self.assertIn("python3 -m unittest discover -s tests", combined)
        self.assertIn("python3 -m influencer_os validate examples", combined)

    def test_no_stale_youtube_approval_boundary_wording(self):
        stale_phrases = (
            "non-approved api_backed adapters such as\n        # youtube_data_api",
            "non-approved api_backed adapters such as youtube_data_api",
            "`youtube_data_api`) stays fully gated",
            "YouTube as a research platform — remains `planned`",
        )
        files = (
            ROOT / "influencer_os" / "validation.py",
            ROOT / "docs" / "adr" / "0022-research-acquisition-connector-layer.md",
        )
        for path in files:
            text = path.read_text()
            for phrase in stale_phrases:
                self.assertNotIn(phrase, text, f"{path} contains stale YouTube approval wording")


class RealCreatorRunbookDriftTests(unittest.TestCase):
    """The day-1 runbook is the operator's entry point for real onboarding;
    it must exist and keep naming the release gate and the wipe warning."""

    def test_runbook_exists_and_names_the_release_gate(self):
        text = read_repo_text("docs/onboard-real-creator-runbook.md")
        self.assertIn("validate all", text)
        self.assertIn("irreversible", text)
        self.assertIn(".env.example", text)

    # Pinned to the argparse choices in influencer_os/cli.py; a drift here
    # means either the CLI or the runbook changed without the other.
    VALIDATE_TARGETS = {
        "examples", "workspace", "project", "record", "research",
        "queue", "board", "calendar", "all",
    }
    FETCH_CONNECTORS = {
        "reddit", "x", "firecrawl", "linkedin", "youtube-search",
        "youtube-channel",
    }
    RUNBOOK_PRODUCER_SKILLS = {
        "create-influencer",
        "create-research-findings",
        "manage-idea-queue",
        "promote-idea",
        "apply-social-template",
        "create-production-plan",
        "create-output-package",
    }

    def test_runbook_cli_invocations_are_real_command_forms(self):
        text = read_repo_text("docs/onboard-real-creator-runbook.md")
        invocations = re.findall(r"python3 -m influencer_os ([a-z-]+)(?:\s+(\S+))?", text)
        self.assertTrue(invocations, "runbook names no CLI invocations")
        parser_source = (ROOT / "influencer_os" / "cli.py").read_text()
        for command, first_arg in invocations:
            self.assertIn(
                f'"{command}"',
                parser_source,
                f"runbook names a CLI command that does not exist: {command}",
            )
            if command == "validate":
                self.assertIn(
                    first_arg,
                    self.VALIDATE_TARGETS,
                    f"runbook names an unknown validate target: {first_arg}",
                )
            if command == "research-fetch":
                self.assertIn(
                    first_arg,
                    self.FETCH_CONNECTORS,
                    f"runbook names an unknown connector: {first_arg}",
                )

    def test_runbook_names_real_producer_skills(self):
        text = read_repo_text("docs/onboard-real-creator-runbook.md")
        on_disk = skills_on_disk()
        for skill in sorted(self.RUNBOOK_PRODUCER_SKILLS):
            self.assertIn(f"`{skill}`", text, f"runbook no longer names skill {skill}")
            self.assertIn(skill, on_disk, f"runbook names a skill not on disk: {skill}")


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


class GuidedE2EDriftTests(unittest.TestCase):
    def test_create_influencer_normal_user_guidance_contract_is_pinned(self):
        skill = read_repo_text("skills/create-influencer/SKILL.md").lower()
        required = (
            "normal-user e2e",
            "normal/new user",
            "do not preload missing answers",
            "exactly three onboarding paths",
            "ask one concrete question at a time",
            "recommended answer",
            "short reason",
            "accept, revise, skip, or system-fill",
            "progress/setup-interview.md",
            "progress/setup-checklist.md",
            "question",
            "recommendation",
            "rationale",
            "answer source",
            "user_provided",
            "imported",
            "generated_from_intake",
            "system_filled",
            "acceptance status",
            "whole-foundation review package",
            "profile_ready",
            "foundation_ready",
            "strategy_ready",
            "production_ready",
            "distinguish generated/system-filled answers from user-provided answers",
        )
        for phrase in required:
            self.assertIn(phrase, skill, f"create-influencer missing guided E2E phrase: {phrase}")

    def test_create_influencer_forbids_validation_based_preapproval(self):
        skill = read_repo_text("skills/create-influencer/SKILL.md").lower()
        self.assertIn("validation alone is not approval", skill)
        self.assertIn("generic `approved if files validate`", skill)
        self.assertIn("explicit user approval", skill)


class ResearchProvenanceSkillDriftTests(unittest.TestCase):
    def test_research_skill_forbids_public_web_as_youtube(self):
        skill = read_repo_text("skills/create-research-findings/SKILL.md").lower()
        required = (
            "never label public-web",
            "manual citation evidence as youtube",
            "source evidence",
            "target distribution platforms",
            "only background/public-web evidence exists",
            "ask the user whether to proceed",
            "do not create metric snapshots",
            "no real visible metrics",
        )
        for phrase in required:
            self.assertIn(phrase, skill, f"create-research-findings missing provenance phrase: {phrase}")

    def test_conductor_phase_checklist_and_creative_review_are_pinned(self):
        skill = read_repo_text("skills/influencer-os/SKILL.md").lower()
        required = (
            "phase checklist",
            "current phase",
            "required next artifact",
            "validation command",
            "human gate",
            "dry-run drafting step",
            "provider boundary",
            "after production planning",
            "offer or run",
            "advisory creative review",
        )
        for phrase in required:
            self.assertIn(phrase, skill, f"influencer-os missing conductor phrase: {phrase}")


class SkillCliInvocationDriftTests(unittest.TestCase):
    def test_promote_idea_names_real_init_project_invocation(self):
        # Slice 5 review: the skill taught a positional creator-workspace
        # argument, but the CLI requires the --creator-workspace flag; an
        # agent following the skill failed mid-construction.
        skill = read_repo_text("skills/promote-idea/SKILL.md")
        invocations = [
            line for line in skill.splitlines() if "init-project" in line
        ]
        self.assertTrue(invocations, "promote-idea no longer documents init-project")
        for line in invocations:
            if "influencer_os init-project" in line:
                self.assertIn(
                    "--creator-workspace",
                    line,
                    f"init-project invocation missing --creator-workspace: {line!r}",
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


class ResearchEnumDriftTests(unittest.TestCase):
    def iter_enums_by_names(self, node, kinds, path=""):
        """Yield (location, kind, enum-or-None) for every pinned-name
        property. None means the property carries no enum — that fails the
        drift check unless the (schema, property) pair is exempt, so deleting
        an enum cannot silently drop the pin."""
        if isinstance(node, dict):
            for prop_name, prop_schema in node.get("properties", {}).items():
                target = prop_schema
                if isinstance(target, dict) and isinstance(target.get("items"), dict):
                    target = target["items"]
                if not isinstance(target, dict):
                    continue
                for names, kind in kinds:
                    if prop_name in names:
                        yield f"{path}.{prop_name}", kind, target.get("enum")
            for key, child in node.items():
                yield from self.iter_enums_by_names(child, kinds, f"{path}.{key}")
        elif isinstance(node, list):
            for index, child in enumerate(node):
                yield from self.iter_enums_by_names(child, kinds, f"{path}[{index}]")

    def iter_platform_enums(self, node, path=""):
        kinds = (
            (PLATFORM_PROPERTY_NAMES, "platform"),
            (CONTENT_TYPE_PROPERTY_NAMES, "content_type"),
            (FORMAT_PROPERTY_NAMES, "format"),
        )
        yield from self.iter_enums_by_names(node, kinds, path)

    def test_every_research_schema_matches_the_canonical_enums(self):
        expected = {
            "platform": RESEARCH_PLATFORMS,
            "content_type": RESEARCH_CONTENT_TYPES,
            "format": RESEARCH_FORMATS,
        }
        found_any = {"platform": False, "content_type": False, "format": False}
        for schema_name in ENUM_PINNED_SCHEMAS:
            schema = json.loads((ROOT / "schemas" / f"{schema_name}.schema.json").read_text())
            for location, kind, values in self.iter_platform_enums(schema, schema_name):
                prop_name = location.rsplit(".", 1)[-1]
                if values is None:
                    self.assertIn(
                        (schema_name, prop_name),
                        ENUM_EXEMPT_PROPERTIES,
                        f"{location} names a pinned {kind} property but carries no enum",
                    )
                    continue
                found_any[kind] = True
                if location in SOURCE_PROVENANCE_PLATFORM_LOCATIONS:
                    self.assertEqual(
                        values,
                        RESEARCH_SOURCE_PLATFORMS,
                        f"{location} must allow public_web source provenance",
                    )
                    continue
                if location in SOURCE_PROVENANCE_CONTENT_TYPE_LOCATIONS:
                    self.assertEqual(
                        values,
                        RESEARCH_SOURCE_CONTENT_TYPES,
                        f"{location} must allow public-web source content types",
                    )
                    continue
                self.assertEqual(
                    values,
                    expected[kind],
                    f"{location} diverges from the canonical ADR 0020 {kind} enum",
                )
        self.assertTrue(all(found_any.values()), "drift check found no research enums to pin")

    def test_every_beat_spine_schema_matches_the_canonical_enums(self):
        expected = {"beat_role": BEAT_ROLES, "hook_category": HOOK_CATEGORIES}
        found_any = {"beat_role": False, "hook_category": False}
        for schema_name in BEAT_SPINE_SCHEMAS:
            schema = json.loads((ROOT / "schemas" / f"{schema_name}.schema.json").read_text())
            for location, kind, values in self.iter_enums_by_names(
                schema,
                (
                    (BEAT_ROLE_PROPERTY_NAMES, "beat_role"),
                    (HOOK_CATEGORY_PROPERTY_NAMES, "hook_category"),
                ),
                schema_name,
            ):
                self.assertIsNotNone(
                    values, f"{location} names a spine property but carries no enum"
                )
                found_any[kind] = True
                self.assertEqual(
                    values,
                    expected[kind],
                    f"{location} diverges from the canonical ADR 0024 {kind} enum",
                )
        self.assertTrue(all(found_any.values()), "drift check found no spine enums to pin")

    def test_beat_spine_code_constants_match_the_canonical_enums(self):
        from influencer_os.validation import BEAT_ROLES as CODE_BEAT_ROLES
        from influencer_os.validation import HOOK_CATEGORIES as CODE_HOOK_CATEGORIES
        from influencer_os.validation import REQUIRED_BEAT_ROLES

        self.assertEqual(CODE_BEAT_ROLES, BEAT_ROLES)
        self.assertEqual(CODE_HOOK_CATEGORIES, HOOK_CATEGORIES)
        self.assertTrue(REQUIRED_BEAT_ROLES <= set(BEAT_ROLES))

    def test_modality_enum_is_pinned(self):
        # ADR 0024: content_mediums is the pure modality enum, identical in
        # the creator-profile schema, the canonical code constant, and the
        # medium-based readiness blocker keys.
        from influencer_os.creator_workspaces import MEDIUM_REQUIRED_ASSET_KINDS
        from influencer_os.validation import CONTENT_MODALITIES

        expected = ["text", "image", "video", "audio"]
        self.assertEqual(list(CONTENT_MODALITIES), expected)
        self.assertEqual(list(MEDIUM_REQUIRED_ASSET_KINDS), expected)
        schema = json.loads((ROOT / "schemas" / "creator-profile.schema.json").read_text())
        mediums_enum = schema["properties"]["content_strategy"]["properties"][
            "content_mediums"
        ]["items"]["enum"]
        self.assertEqual(mediums_enum, expected)

    def test_platform_fit_map_covers_every_format_and_platform(self):
        # The advisory capability map must classify all 6 formats across all
        # distribution platforms with fit levels from the closed vocabulary.
        # public_web is source provenance only and must not become a production
        # platform target.
        from influencer_os.projects import PLATFORM_FORMAT_FIT
        from influencer_os.validation import PLATFORM_FIT_LEVELS

        self.assertEqual(sorted(PLATFORM_FORMAT_FIT), sorted(RESEARCH_FORMATS))
        for format_id, fits in PLATFORM_FORMAT_FIT.items():
            self.assertEqual(
                sorted(fits), sorted(RESEARCH_PLATFORMS),
                f"{format_id} capability row does not cover the 9 platforms",
            )
            for platform, fit in fits.items():
                self.assertIn(
                    fit, PLATFORM_FIT_LEVELS,
                    f"{format_id}/{platform} has unknown fit {fit!r}",
                )

    def test_code_constants_match_the_canonical_enums(self):
        # The canonical platform constant lives in validation.py (Creative
        # Direction Decision A); every code copy pins to it like the schema
        # copies do.
        from influencer_os.projects import PRODUCTION_PLAN_SCHEMAS
        from influencer_os.projects import RESEARCH_PLATFORMS as CODE_PLATFORMS
        from influencer_os.research import PRODUCTION_SUPPORTED_FORMATS
        from influencer_os.validation import RESEARCH_PLATFORMS as CANONICAL_PLATFORMS

        self.assertEqual(list(CANONICAL_PLATFORMS), RESEARCH_PLATFORMS)
        self.assertEqual(list(CODE_PLATFORMS), RESEARCH_PLATFORMS)
        self.assertTrue(PRODUCTION_SUPPORTED_FORMATS <= set(RESEARCH_FORMATS))
        self.assertEqual(
            {f"format_{unit_type}" for unit_type in PRODUCTION_PLAN_SCHEMAS},
            set(PRODUCTION_SUPPORTED_FORMATS),
            "PRODUCTION_SUPPORTED_FORMATS must mirror the production plan schemas",
        )


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


class ImprovementOsDriftTests(unittest.TestCase):
    """ADR 0025 drift pins: rubric vocabularies stay identical across the
    schema, the code constants, and the quality-review checklist; the OS
    rubric seed validates and covers every quality-review category; and the
    friction-logging obligation stays present in the producing skills."""

    RUBRIC_SCHEMA = json.loads((ROOT / "schemas" / "production-rubric.schema.json").read_text())
    EVENT_SCHEMA = json.loads((ROOT / "schemas" / "system-event.schema.json").read_text())

    def criterion_properties(self):
        return self.RUBRIC_SCHEMA["properties"]["criteria"]["items"]["properties"]

    def test_rubric_enums_match_code_constants(self):
        from influencer_os.validation import (
            CRITERION_ORIGINS,
            CRITERION_STATUSES,
            RUBRIC_SCOPES,
        )

        self.assertEqual(
            self.RUBRIC_SCHEMA["properties"]["scope"]["enum"], list(RUBRIC_SCOPES)
        )
        criterion = self.criterion_properties()
        self.assertEqual(criterion["status"]["enum"], list(CRITERION_STATUSES))
        self.assertEqual(criterion["origin"]["enum"], list(CRITERION_ORIGINS))

    def test_rubric_category_enum_matches_quality_review_checklist(self):
        from influencer_os.validation import QUALITY_REVIEW_CHECKS

        category_enum = self.criterion_properties()["quality_review_category"]["enum"]
        self.assertEqual(sorted(category_enum), sorted(QUALITY_REVIEW_CHECKS))
        quality_schema = json.loads(
            (ROOT / "schemas" / "quality-review.schema.json").read_text()
        )
        checklist_enum = quality_schema["properties"]["checklist"]["items"][
            "properties"
        ]["check"]["enum"]
        self.assertEqual(sorted(category_enum), sorted(checklist_enum))

    def test_event_friction_fields_share_the_criterion_id_pattern(self):
        criterion_pattern = self.criterion_properties()["criterion_id"]["pattern"]
        event_props = self.EVENT_SCHEMA["properties"]
        self.assertEqual(event_props["criterion_id"]["pattern"], criterion_pattern)
        self.assertEqual(event_props["recurrence_key"]["pattern"], criterion_pattern)

    def test_os_rubric_seed_validates_and_covers_every_category(self):
        from influencer_os.validation import QUALITY_REVIEW_CHECKS, validate_record

        rubric = json.loads((ROOT / "context" / "production-rubric.json").read_text())
        validate_record("production-rubric", rubric)
        self.assertEqual(rubric["scope"], "os")
        covered = {
            criterion.get("quality_review_category")
            for criterion in rubric["criteria"]
        }
        self.assertTrue(
            set(QUALITY_REVIEW_CHECKS) <= covered,
            f"OS rubric seed must cover every quality-review category; got {covered}",
        )

    def test_producing_skills_carry_the_friction_logging_rule(self):
        for skill in (
            "review-generated-assets",
            "request-generation-approval",
            "create-production-plan",
            "create-output-package",
        ):
            text = (ROOT / "skills" / skill / "SKILL.md").read_text()
            self.assertIn("## Friction Logging", text, skill)
            self.assertIn("log-incident", text, skill)
            self.assertIn("cite-or-mint", text, skill)

    def test_reflection_threshold_keys_match_the_schema(self):
        from influencer_os.rubric import DEFAULT_REFLECTION_THRESHOLDS

        workspace_schema = json.loads(
            (ROOT / "schemas" / "creator-workspace.schema.json").read_text()
        )
        schema_keys = set(
            workspace_schema["properties"]["reflection_thresholds"]["properties"]
        )
        self.assertEqual(schema_keys, set(DEFAULT_REFLECTION_THRESHOLDS))

    def test_prediction_enums_match_code_constants(self):
        from influencer_os.validation import PREDICTION_COMPARATORS, PREDICTION_RESULTS

        package_schema = json.loads(
            (ROOT / "schemas" / "output-package.schema.json").read_text()
        )
        comparator_enum = package_schema["properties"]["creative_performance_map"][
            "items"
        ]["properties"]["prediction"]["properties"]["comparator"]["enum"]
        self.assertEqual(comparator_enum, list(PREDICTION_COMPARATORS))
        summary_schema = json.loads(
            (ROOT / "schemas" / "performance-summary.schema.json").read_text()
        )
        result_enum = summary_schema["properties"]["stage_findings"]["items"][
            "properties"
        ]["prediction_result"]["enum"]
        self.assertEqual(result_enum, list(PREDICTION_RESULTS))


class SkillProseDriftTests(unittest.TestCase):
    """Fleet-wide skill-prose pins from the 2026-07-07 skill review
    (docs/workflows/skill-quality-remediation-implementation-plan.md).
    Every confirmed defect in that review lived inside prose that had
    drifted from code, schema, or canon; each test here pins one class."""

    def test_skill_descriptions_are_safe_yaml_scalars(self):
        # F1: an unquoted `: ` inside a plain YAML scalar is invalid strict
        # YAML ("bad indentation of a mapping entry"); a strict frontmatter
        # loader drops or rejects the description — the skill's entire
        # invocation surface. Stdlib has no YAML parser, so this is a
        # conservative scalar lint: quoted scalars must be balanced with no
        # unescaped inner quote; plain scalars must avoid the breakers
        # (`: `, ` #`, unsafe leading indicator characters).
        for skill in sorted(skills_on_disk()):
            text = read_repo_text(f"skills/{skill}/SKILL.md")
            match = re.search(r"^description:[ \t]*(.+)$", text, flags=re.MULTILINE)
            self.assertIsNotNone(match, f"skills/{skill} has no description line")
            value = match.group(1).strip()
            if value[0] in "\"'":
                quote = value[0]
                self.assertTrue(
                    len(value) >= 2 and value.endswith(quote),
                    f"skills/{skill} description quote is unbalanced",
                )
                inner = value[1:-1]
                if quote == '"':
                    self.assertNotRegex(
                        inner,
                        r'(?<!\\)"',
                        f"skills/{skill} description holds an unescaped double "
                        "quote inside a double-quoted scalar",
                    )
                else:
                    self.assertNotIn(
                        "'",
                        inner.replace("''", ""),
                        f"skills/{skill} description holds an unescaped single "
                        "quote inside a single-quoted scalar",
                    )
                continue
            self.assertNotIn(
                value[0],
                "-?:,[]{}#&*!|>%@`",
                f"skills/{skill} plain description starts with a YAML "
                "indicator character — quote the scalar",
            )
            for breaker, why in ((": ", "starts a nested mapping"), (" #", "starts a comment")):
                self.assertNotIn(
                    breaker,
                    value,
                    f"skills/{skill} description holds an unquoted {breaker!r} "
                    f"({why}) — quote the scalar so strict-YAML frontmatter "
                    "loaders keep the description",
                )

    def test_batch1_contract_fixes_stay_pinned(self):
        # Batch 1 gpt-5.5 review follow-up: pin the specific contracts the
        # mechanical fixes corrected so they cannot silently regress.
        review_schema = json.loads(
            (ROOT / "schemas" / "review-record.schema.json").read_text()
        )
        hook = read_repo_text("skills/review-hook-payoff/SKILL.md")
        for field in review_schema["properties"]["reviewer_execution"]["required"]:
            self.assertIn(
                field,
                hook,
                f"review-hook-payoff no longer names schema-required "
                f"reviewer_execution field {field!r}",
            )
        approval = read_repo_text("skills/request-generation-approval/SKILL.md")
        for phrase in ("write-once", "`cancelled`", "record a fresh approval"):
            self.assertIn(
                phrase, approval,
                f"request-generation-approval cancellation contract lost {phrase!r}",
            )
        package = read_repo_text("skills/create-output-package/SKILL.md")
        for phrase in ("one entry for each of the five stages", "QualityReview"):
            self.assertIn(
                phrase, package,
                f"create-output-package contract lost {phrase!r}",
            )
        for skill, schema in (
            ("create-output-package", "output-package"),
            ("register-published-post", "published-post-record"),
            ("ingest-analytics", "analytics-snapshot"),
            ("distill-production-learning", "improvement-claim"),
        ):
            self.assertIn(
                f"schemas/{schema}.schema.json",
                read_repo_text(f"skills/{skill}/SKILL.md"),
                f"skills/{skill} no longer names its authoring schema",
            )
        self.assertIsNone(
            frontmatter_dependencies("distill-production-learning"),
            "distill-production-learning re-grew a dependencies list its "
            "body does not route to",
        )

    def test_skill_prose_repo_paths_exist(self):
        # Dead-pointer class: every docs/, schemas/, or examples/ path a
        # skill names must exist. `../../` prefixes resolve to repo root
        # from a skill folder and are normalized here.
        pattern = re.compile(
            r"(?:\.\./\.\./)?((?:docs|schemas|examples)/[A-Za-z0-9_./-]+)"
        )
        for skill in sorted(skills_on_disk()):
            text = read_repo_text(f"skills/{skill}/SKILL.md")
            for path in sorted(set(pattern.findall(text))):
                cleaned = path.rstrip(".")
                self.assertTrue(
                    (ROOT / cleaned).exists(),
                    f"skills/{skill} points at missing repo path {cleaned}",
                )

    def test_skill_workspace_file_paths_are_canonical(self):
        # F4: a skill pointed at context/voice-samples.md — a file no
        # scaffold creates, in the OS-persona scope instead of the creator
        # scope. Workspace-file mentions must name a scaffolded foundation
        # file, a known workspace/OS ledger, or a real repo-root file.
        from influencer_os.creator_workspaces import FOUNDATION_FILES

        known = set(FOUNDATION_FILES) | {
            "memory/learnings.md",
            "context/learnings.md",
            "context/production-rubric.json",
        }
        pattern = re.compile(
            r"\b((?:context|brand_context|memory)/[A-Za-z0-9_-]+\.(?:md|json))\b"
        )
        for skill in sorted(skills_on_disk()):
            text = read_repo_text(f"skills/{skill}/SKILL.md")
            for path in sorted(set(pattern.findall(text))):
                self.assertTrue(
                    path in known or (ROOT / path).exists(),
                    f"skills/{skill} names non-canonical workspace file {path}",
                )

    def test_reference_library_status_vocabulary_matches_schema(self):
        # F3: the skill once recommended `generated-from-intake` /
        # `system-filled` — interview vocabulary, not asset_status values.
        # The skill's Asset Status list must equal the schema enum exactly.
        schema = json.loads(
            (ROOT / "schemas" / "reference-library.schema.json").read_text()
        )
        enum = set(
            schema["properties"]["assets"]["items"]["properties"]["asset_status"][
                "enum"
            ]
        )
        text = read_repo_text("skills/create-reference-library/SKILL.md")
        section = text.split("## Asset Status")[1].split("\n## ")[0]
        listed = set(re.findall(r"^- `([a-z_]+)`", section, flags=re.MULTILINE))
        self.assertEqual(
            listed,
            enum,
            "create-reference-library Asset Status list disagrees with the "
            "reference-library schema enum",
        )
        for bad in ("generated-from-intake", "system-filled"):
            self.assertNotIn(
                bad,
                text,
                f"create-reference-library recommends {bad!r}, which no schema "
                "field accepts (interview vocabulary leaked into the record contract)",
            )

    def test_object_reference_prompt_contract_stays_atomic(self):
        skill = read_repo_text("skills/create-reference-library/SKILL.md")
        template = read_repo_text(
            "docs/templates/creator-setup/reference-prompts/"
            "standard-object-reference-prompts.md"
        )
        workflow = read_repo_text("docs/workflows/creator-setup.md")
        skill_flat = re.sub(r"\s+", " ", skill)
        template_flat = re.sub(r"\s+", " ", template)

        for phrase in (
            "Every distinct prop, product, or signature object gets its own Reference Asset",
            "one distinct prop per Reference Asset and per planned reference image",
            "If a prompt names more than one distinct object, split it",
        ):
            self.assertIn(
                phrase,
                skill_flat,
                f"create-reference-library lost atomic object rule {phrase!r}",
            )

        for phrase in (
            "Use one prompt and one output image for exactly one distinct target object",
            "Multiple panels are allowed only as different views of the same single target",
            "no grouped flat-lay",
        ):
            self.assertIn(
                phrase,
                template_flat,
                f"standard object prompt lost atomic output guard {phrase!r}",
            )

        self.assertIn(
            "Object references are atomic",
            workflow,
            "creator setup workflow lost the object fan-out rule",
        )

    def test_template_ids_resolve_and_library_is_pointed_at(self):
        # F2: the conductor carried an inline starter-template list whose IDs
        # had drifted from docs/social-template-library.md (6 of 9 resolved
        # to nothing). The library owns template IDs; skills may only name
        # IDs it defines, and the two template-handling skills must point at
        # the library rather than restate it.
        library = read_repo_text("docs/social-template-library.md")
        library_ids = set(re.findall(r"`(template_[a-z0-9_]+)`", library))
        self.assertTrue(library_ids, "social-template-library defines no template IDs")
        for skill in sorted(skills_on_disk()):
            text = read_repo_text(f"skills/{skill}/SKILL.md")
            for template_id in sorted(set(re.findall(r"\btemplate_[a-z0-9_]+\b", text))):
                self.assertIn(
                    template_id,
                    library_ids,
                    f"skills/{skill} names template id {template_id!r} that "
                    "docs/social-template-library.md does not define",
                )
        for skill in ("influencer-os", "apply-social-template"):
            self.assertIn(
                "docs/social-template-library.md",
                read_repo_text(f"skills/{skill}/SKILL.md"),
                f"skills/{skill} does not point at the canonical template library",
            )

    def test_v1_scope_covers_every_research_platform(self):
        # F8: the conductor's V1 Scope sentence and the AGENTS.md research
        # rule both lagged ADR 0027 (YouTube). Display names key off the
        # canonical platform list so a new platform fails loudly here until
        # both sentences and this map are updated together.
        display = {
            "x": "X", "instagram": "Instagram", "tiktok": "TikTok",
            "substack": "Substack", "medium": "Medium", "reddit": "Reddit",
            "facebook": "Facebook", "linkedin": "LinkedIn", "youtube": "YouTube",
        }
        self.assertEqual(set(display), set(RESEARCH_PLATFORMS))
        scope = skill_body("influencer-os").split("## V1 Scope")[1].split("\n## ")[0]
        for platform in RESEARCH_PLATFORMS:
            self.assertRegex(
                scope,
                rf"\b{display[platform]}\b",
                f"influencer-os V1 Scope omits research platform {platform!r}",
            )
        agents = read_repo_text("AGENTS.md")
        self.assertIn(
            "ADR 0027",
            agents,
            "AGENTS.md research-scope rule does not acknowledge the ADR 0027 "
            "platform extension",
        )

    def test_every_skill_cli_invocation_is_a_real_command_form(self):
        # Fleet-wide version of the runbook CLI pin: every
        # `python3 -m influencer_os <command>` snippet in any skill must name
        # a real subcommand, and validate/research-fetch targets must exist.
        parser_source = (ROOT / "influencer_os" / "cli.py").read_text()
        found_any = False
        for skill in sorted(skills_on_disk()):
            text = read_repo_text(f"skills/{skill}/SKILL.md")
            for command, first_arg in re.findall(
                r"python3 -m influencer_os ([a-z][a-z-]*)(?:\s+(\S+))?", text
            ):
                found_any = True
                self.assertIn(
                    f'"{command}"',
                    parser_source,
                    f"skills/{skill} names a CLI command that does not exist: {command}",
                )
                first_arg = first_arg.strip("`.,;:)")
                if first_arg.startswith("<"):
                    continue  # documentation placeholder, not a literal target
                if command == "validate":
                    self.assertIn(
                        first_arg,
                        RealCreatorRunbookDriftTests.VALIDATE_TARGETS,
                        f"skills/{skill} names an unknown validate target: {first_arg}",
                    )
                if command == "research-fetch":
                    self.assertIn(
                        first_arg,
                        RealCreatorRunbookDriftTests.FETCH_CONNECTORS,
                        f"skills/{skill} names an unknown connector: {first_arg}",
                    )
        self.assertTrue(found_any, "no skill documents any CLI invocation")

    def test_shared_skill_blocks_stay_identical(self):
        # D4 (remediation plan): Self-Update and Friction Logging live
        # inline in every carrier because runtime copies travel into
        # creator workspaces without docs/. Inline-by-design duplication is
        # only safe if a protocol change is a mechanically verified sweep:
        # normalizing each skill's own name away, every carrier of a
        # dialect must hold byte-identical block text.
        # Normalize only the sanctioned skill-name slots; a block that
        # mentions its own name anywhere else stays different on purpose,
        # so an unexpected mention surfaces as divergence.
        NAME_SLOTS = (
            "log-learning context/learnings.md {skill} ",
            "--source-id {skill} ",
            "skills/{skill}/SKILL.local.md",
        )

        def block(skill, heading):
            body = skill_body(skill)
            marker = f"\n## {heading}\n"
            if marker not in body:
                return None
            text = body.split(marker, 1)[1]
            cut = text.find("\n## ")
            if cut != -1:
                text = text[:cut]
            for slot in NAME_SLOTS:
                text = text.replace(
                    slot.format(skill=skill), slot.format(skill="<skill>")
                )
            return text.strip()

        # Bespoke Self-Update dialects; every other carrier must match one
        # of the two shared forms exactly.
        BESPOKE_SELF_UPDATE = {"memory-write", "wrap-up"}

        groups = {}
        unclassified = set()
        for skill in sorted(skills_on_disk()):
            self_update = block(skill, "Self-Update")
            if self_update is not None:
                first_line = self_update.splitlines()[0]
                if first_line.startswith("When corrected twice the same way"):
                    groups.setdefault("self-update:producer", {})[skill] = self_update
                elif first_line.startswith("When the user flags an issue with this skill"):
                    groups.setdefault("self-update:conductor", {})[skill] = self_update
                else:
                    unclassified.add(skill)
            friction = block(skill, "Friction Logging (ADR 0025)")
            if friction is not None:
                groups.setdefault("friction-logging", {})[skill] = friction

        self.assertEqual(
            unclassified,
            BESPOKE_SELF_UPDATE,
            "a Self-Update block left the shared dialects; either restore "
            "the shared first line or add the skill to the bespoke set here",
        )
        self.assertGreaterEqual(
            len(groups.get("self-update:producer", {})), 10,
            "producer Self-Update carriers vanished; the dialect grouping is stale",
        )
        self.assertEqual(
            sorted(groups.get("self-update:conductor", {})),
            ["create-influencer", "influencer-os"],
        )
        self.assertGreaterEqual(len(groups.get("friction-logging", {})), 4)
        for group_name, members in groups.items():
            variants = {}
            for skill, text in members.items():
                variants.setdefault(text, []).append(skill)
            self.assertEqual(
                len(variants), 1,
                f"{group_name} blocks diverge across carriers: "
                + "; ".join(str(sorted(v)) for v in variants.values()),
            )
