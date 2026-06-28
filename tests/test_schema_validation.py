import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def validate_schema_subset(schema, value, path="$"):
    expected_type = schema.get("type")
    if expected_type:
        allowed = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(_matches_type(value, type_name) for type_name in allowed):
            raise AssertionError(f"{path}: expected {allowed}, got {type(value).__name__}")

    if "const" in schema and value != schema["const"]:
        raise AssertionError(f"{path}: expected const {schema['const']!r}")

    if "enum" in schema and value not in schema["enum"]:
        raise AssertionError(f"{path}: {value!r} not in enum")

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            raise AssertionError(f"{path}: string shorter than minLength")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            raise AssertionError(f"{path}: {value!r} does not match {schema['pattern']!r}")
        if schema.get("format") == "date" and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise AssertionError(f"{path}: {value!r} is not YYYY-MM-DD")

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise AssertionError(f"{path}: array shorter than minItems")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise AssertionError(f"{path}: array longer than maxItems")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                validate_schema_subset(item_schema, item, f"{path}[{index}]")

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                raise AssertionError(f"{path}: missing required key {key!r}")

        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = set(value) - set(properties)
            if extra:
                raise AssertionError(f"{path}: unexpected keys {sorted(extra)!r}")

        for key, child_schema in properties.items():
            if key in value:
                validate_schema_subset(child_schema, value[key], f"{path}.{key}")


def _matches_type(value, type_name):
    if type_name == "object":
        return isinstance(value, dict)
    if type_name == "array":
        return isinstance(value, list)
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "null":
        return value is None
    return False


class SchemaValidationTests(unittest.TestCase):
    def test_examples_validate_against_schemas(self):
        pairs = [
            ("creator-profile", "creator-profile"),
            ("social-research-pack", "social-research-pack"),
            ("social-post-format", "social-post-format"),
            ("content-idea-set", "content-idea-set"),
            ("selected-content-idea", "selected-content-idea"),
            ("social-template", "social-template"),
            ("applied-social-template", "applied-social-template"),
            ("micro-journey-video-plan", "micro-journey-video-plan"),
            ("carousel-plan", "carousel-plan"),
            ("single-image-post-plan", "single-image-post-plan"),
            ("story-sequence-plan", "story-sequence-plan"),
            ("base-video-generation-plan", "base-video-generation-plan"),
        ]

        for schema_name, example_name in pairs:
            with self.subTest(schema=schema_name):
                schema = json.loads((ROOT / "schemas" / f"{schema_name}.schema.json").read_text())
                example = json.loads((ROOT / "examples" / f"{example_name}.example.json").read_text())
                validate_schema_subset(schema, example)


if __name__ == "__main__":
    unittest.main()
