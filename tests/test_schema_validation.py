import json
import shutil
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from influencer_os.validation import (
    EXAMPLE_SCHEMA_PAIRS,
    ValidationError,
    load_json,
    load_schema,
    validate_examples,
    validate_record,
    validate_schema_subset,
)


class SchemaValidationTests(unittest.TestCase):
    def test_examples_validate_against_schemas(self):
        results = validate_examples()
        self.assertEqual(len(results), len(EXAMPLE_SCHEMA_PAIRS))
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


if __name__ == "__main__":
    unittest.main()
