import json
import shutil
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from influencer_os.validation import (
    SchemaDefinitionError,
    ValidationError,
    discover_example_schema_pairs,
    load_json,
    load_schema,
    validate_examples,
    validate_record,
    validate_schema_subset,
)

ROOT = Path(__file__).resolve().parents[1]


class SchemaValidationTests(unittest.TestCase):
    def test_examples_validate_against_schemas(self):
        results = validate_examples()
        schemas_on_disk = list((ROOT / "schemas").glob("*.schema.json"))
        self.assertEqual(len(results), len(schemas_on_disk))
        for schema_name, example_path in results:
            with self.subTest(schema=schema_name):
                self.assertTrue(example_path.exists())

    def test_analytics_rejects_negative_counts(self):
        schema = load_schema("analytics-snapshot")
        example = load_json("examples/analytics-snapshot.example.json")
        invalid = deepcopy(example)
        invalid["metrics"]["views"] = -1

        with self.assertRaises(ValidationError):
            validate_schema_subset(schema, invalid)

    def test_analytics_rejects_rate_above_one(self):
        schema = load_schema("analytics-snapshot")
        example = load_json("examples/analytics-snapshot.example.json")
        invalid = deepcopy(example)
        invalid["attribution_metrics"]["hook"]["retention_3s_pct"] = 1.5

        with self.assertRaises(ValidationError):
            validate_schema_subset(schema, invalid)

    def test_project_requires_acceptance_criteria(self):
        example = load_json("examples/project.example.json")
        invalid = deepcopy(example)
        invalid.pop("acceptance_criteria")

        with self.assertRaises(ValidationError):
            validate_record("project", invalid)

    def test_output_package_requires_template_and_video_pack_refs(self):
        example = load_json("examples/output-package.example.json")
        for field in ("applied_social_template_id", "video_understanding_pack_ids"):
            invalid = deepcopy(example)
            invalid["source_refs"].pop(field)
            with self.subTest(field=field):
                with self.assertRaises(ValidationError):
                    validate_record("output-package", invalid)

    def test_workspace_intake_paths_are_pinned_under_sources(self):
        example = load_json("examples/creator-workspace.example.json")
        for bad_path in (
            "../../outside-intake.md",
            "/tmp/outside-intake.md",
            "research/misfiled-intake.md",
            "sources/other/misfiled-intake.md",
            "sources/intakes/nested/too-deep.md",
        ):
            invalid = deepcopy(example)
            invalid["source_intakes"][0]["path"] = bad_path
            with self.subTest(path=bad_path):
                with self.assertRaises(ValidationError):
                    validate_record("creator-workspace", invalid)

        valid = deepcopy(example)
        valid["source_intakes"][0]["path"] = "sources/imports/exported-brand-doc.md"
        validate_record("creator-workspace", valid)

    def test_content_ideas_require_evidence_refs(self):
        example = load_json("examples/content-idea-set.example.json")
        invalid = deepcopy(example)
        invalid["ideas"][0].pop("evidence_ref_ids", None)

        with self.assertRaises(ValidationError):
            validate_record("content-idea-set", invalid)

    def test_output_package_requires_all_creative_performance_stages(self):
        example = load_json("examples/output-package.example.json")
        invalid = deepcopy(example)
        invalid["creative_performance_map"] = [
            deepcopy(example["creative_performance_map"][0])
            for _ in range(5)
        ]

        with self.assertRaises(ValidationError):
            validate_record("output-package", invalid)

    def test_performance_summary_requires_all_stage_findings(self):
        example = load_json("examples/performance-summary.example.json")
        invalid = deepcopy(example)
        invalid["stage_findings"] = [
            deepcopy(example["stage_findings"][0])
            for _ in range(5)
        ]

        with self.assertRaises(ValidationError):
            validate_record("performance-summary", invalid)

    def test_output_package_example_refs_existing_plan_examples(self):
        output_package = load_json("examples/output-package.example.json")
        micro_journey = load_json("examples/micro-journey-video-plan.example.json")
        generation_plan = load_json("examples/base-video-generation-plan.example.json")
        known_plan_ids = {
            micro_journey["micro_journey_video_plan_id"],
            generation_plan["base_video_generation_plan_id"],
        }

        self.assertTrue(
            set(output_package["source_refs"]["production_plan_ids"]).issubset(known_plan_ids)
        )

    def test_validate_examples_runs_semantic_checks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            shutil.copytree("schemas", temp_root / "schemas")
            shutil.copytree("examples", temp_root / "examples")
            output_package_path = temp_root / "examples" / "output-package.example.json"
            output_package = load_json(output_package_path)
            output_package["creative_performance_map"] = [
                deepcopy(output_package["creative_performance_map"][0])
                for _ in range(5)
            ]
            output_package_path.write_text(json.dumps(output_package, indent=2) + "\n")

            with self.assertRaises(ValidationError):
                validate_examples(root=temp_root)


class ExampleCoverageDiscoveryTests(unittest.TestCase):
    PROBE_SCHEMA = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["probe_id"],
        "properties": {"probe_id": {"type": "string"}},
        "additionalProperties": False,
    }

    def make_temp_root(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir)
        temp_root = Path(temp_dir)
        shutil.copytree("schemas", temp_root / "schemas")
        shutil.copytree("examples", temp_root / "examples")
        return temp_root

    def test_pairs_are_derived_from_schemas_on_disk(self):
        pairs = discover_example_schema_pairs()
        schema_stems = sorted(
            path.name[: -len(".schema.json")]
            for path in (ROOT / "schemas").glob("*.schema.json")
        )
        self.assertEqual([schema for schema, _ in pairs], schema_stems)

    def test_new_schema_example_pair_is_covered_automatically(self):
        temp_root = self.make_temp_root()
        baseline = len(validate_examples(root=temp_root))
        (temp_root / "schemas" / "zz-probe.schema.json").write_text(
            json.dumps(self.PROBE_SCHEMA, indent=2) + "\n"
        )
        (temp_root / "examples" / "zz-probe.example.json").write_text(
            json.dumps({"probe_id": "probe_1"}, indent=2) + "\n"
        )

        results = validate_examples(root=temp_root)
        self.assertEqual(len(results), baseline + 1)

    def test_schema_without_example_fails_discovery(self):
        temp_root = self.make_temp_root()
        (temp_root / "schemas" / "zz-probe.schema.json").write_text(
            json.dumps(self.PROBE_SCHEMA, indent=2) + "\n"
        )

        with self.assertRaises(ValidationError):
            validate_examples(root=temp_root)

    def test_example_without_schema_fails_discovery(self):
        temp_root = self.make_temp_root()
        (temp_root / "examples" / "zz-orphan.example.json").write_text("{}\n")

        with self.assertRaises(ValidationError):
            validate_examples(root=temp_root)


class ValidatorSubsetTests(unittest.TestCase):
    REF_SCHEMA = {
        "type": "object",
        "required": ["status"],
        "properties": {"status": {"$ref": "#/definitions/status"}},
        "additionalProperties": False,
        "definitions": {"status": {"type": "string", "enum": ["new", "promoted"]}},
    }

    def test_ref_enforces_the_referenced_definition(self):
        validate_schema_subset(self.REF_SCHEMA, {"status": "new"})

        with self.assertRaises(ValidationError):
            validate_schema_subset(self.REF_SCHEMA, {"status": "bogus"})

    def test_unresolvable_ref_is_a_schema_error(self):
        schema = {"type": "object", "properties": {"x": {"$ref": "#/definitions/missing"}}}

        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset(schema, {"x": 1})

    def test_external_ref_is_a_schema_error(self):
        schema = {"type": "object", "properties": {"x": {"$ref": "other.json#/definitions/x"}}}

        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset(schema, {"x": 1})

    def test_circular_ref_chain_is_a_schema_error(self):
        schema = {
            "type": "object",
            "properties": {"x": {"$ref": "#/definitions/a"}},
            "definitions": {
                "a": {"$ref": "#/definitions/b"},
                "b": {"$ref": "#/definitions/a"},
            },
        }

        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset(schema, {"x": 1})

    def test_ref_with_sibling_validation_keywords_is_a_schema_error(self):
        schema = {
            "type": "object",
            "properties": {"x": {"$ref": "#/definitions/status", "minLength": 2}},
            "definitions": {"status": {"type": "string"}},
        }

        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset(schema, {"x": "ok"})

    def test_one_of_requires_exactly_one_match(self):
        exclusive = {"oneOf": [{"type": "string"}, {"type": "number"}]}
        validate_schema_subset(exclusive, "text")

        overlapping = {"oneOf": [{"type": "string"}, {"type": "string", "minLength": 1}]}
        with self.assertRaises(ValidationError):
            validate_schema_subset(overlapping, "ab")
        with self.assertRaises(ValidationError):
            validate_schema_subset(exclusive, True)

    def test_any_of_requires_at_least_one_match(self):
        schema = {"anyOf": [{"type": "number"}, {"type": "integer"}]}
        validate_schema_subset(schema, 3)

        with self.assertRaises(ValidationError):
            validate_schema_subset(schema, "text")

    def test_all_of_requires_every_branch_to_match(self):
        schema = {"allOf": [{"type": "string"}, {"type": "string", "minLength": 3}]}
        validate_schema_subset(schema, "abc")

        with self.assertRaises(ValidationError):
            validate_schema_subset(schema, "ab")

    def test_unknown_keyword_fails_closed(self):
        schema = {"type": "array", "contains": {"type": "string"}}

        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset(schema, [])

    def test_unknown_keyword_inside_a_matching_combinator_still_fails_closed(self):
        schema = {"anyOf": [{"type": "string"}, {"contains": {"type": "string"}}]}

        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset(schema, "matches-first-branch")

    def test_date_format_rejects_impossible_calendar_dates(self):
        # Shape-only checking would accept 2026-99-99 as durable evidence dates.
        schema = {"type": "string", "format": "date"}

        validate_schema_subset(schema, "2026-07-03")
        with self.assertRaises(ValidationError):
            validate_schema_subset(schema, "2026-99-99")
        with self.assertRaises(ValidationError):
            validate_schema_subset(schema, "2026-02-30")

    def test_enum_must_be_a_list(self):
        # A string enum would silently degrade to substring matching.
        schema = {"type": "string", "enum": "abc"}

        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset(schema, "a")

    def test_additional_properties_must_be_boolean(self):
        # The string "false" is truthy and would behave like permissive true.
        schema = {"type": "object", "additionalProperties": "false"}

        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset(schema, {"unexpected": 1})

    def test_pattern_must_be_a_string(self):
        schema = {"type": "string", "pattern": 123}

        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset(schema, "value")

    def test_combinators_must_be_lists_of_schemas(self):
        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset({"oneOf": "nope"}, "value")

        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset({"anyOf": [{"type": "string"}, "bad"]}, "value")

    def test_type_must_be_a_nonempty_string_or_string_list(self):
        # An empty list is falsy and would skip type validation entirely.
        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset({"type": []}, "anything")

        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset({"type": ["string", 3]}, "anything")

        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset({"type": ""}, "anything")

    def test_numeric_bounds_must_be_numbers(self):
        schema = {"type": "number", "minimum": "0"}

        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset(schema, 5)

    def test_items_must_be_a_schema_object(self):
        schema = {"type": "array", "items": "nope"}

        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset(schema, ["x"])

    def test_unknown_format_fails_closed(self):
        schema = {"type": "string", "format": "uri"}

        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset(schema, "https://example.com")

    def test_unknown_type_name_fails_closed(self):
        schema = {"type": "float"}

        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset(schema, 1.5)

    def test_schema_form_additional_properties_fails_closed(self):
        schema = {"type": "object", "additionalProperties": {"type": "string"}}

        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset(schema, {"x": "y"})

    def test_tuple_form_items_fails_closed(self):
        schema = {"type": "array", "items": [{"type": "string"}]}

        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset(schema, ["x"])


if __name__ == "__main__":
    unittest.main()
