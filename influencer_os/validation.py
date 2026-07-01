import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_SCHEMA_PAIRS = [
    ("creator-workspace", "creator-workspace"),
    ("creator-profile", "creator-profile"),
    ("reference-library", "reference-library"),
    ("project", "project"),
    ("output-package", "output-package"),
    ("published-post-record", "published-post-record"),
    ("analytics-snapshot", "analytics-snapshot"),
    ("performance-summary", "performance-summary"),
    ("social-research-pack", "social-research-pack"),
    ("video-understanding-pack", "video-understanding-pack"),
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

REQUIRED_CREATIVE_STAGES = {
    "packaging",
    "hook",
    "body_retention",
    "payoff",
    "cta",
}


class ValidationError(AssertionError):
    pass


def load_json(path):
    return json.loads(Path(path).read_text())


def load_schema(schema_name, root=ROOT):
    return load_json(Path(root) / "schemas" / f"{schema_name}.schema.json")


def validate_record(schema_name, record, root=ROOT):
    schema = load_schema(schema_name, root=root)
    validate_schema_subset(schema, record)
    validate_record_semantics(schema_name, record)


def validate_file(schema_name, record_path, root=ROOT):
    validate_record(schema_name, load_json(record_path), root=root)


def validate_examples(root=ROOT):
    results = []
    for schema_name, example_name in EXAMPLE_SCHEMA_PAIRS:
        example_path = Path(root) / "examples" / f"{example_name}.example.json"
        validate_record(schema_name, load_json(example_path), root=root)
        results.append((schema_name, example_path))
    return results


def validate_schema_subset(schema, value, path="$"):
    expected_type = schema.get("type")
    if expected_type:
        allowed = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(_matches_type(value, type_name) for type_name in allowed):
            raise ValidationError(f"{path}: expected {allowed}, got {type(value).__name__}")

    if "const" in schema and value != schema["const"]:
        raise ValidationError(f"{path}: expected const {schema['const']!r}")

    if "enum" in schema and value not in schema["enum"]:
        raise ValidationError(f"{path}: {value!r} not in enum")

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            raise ValidationError(f"{path}: string shorter than minLength")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            raise ValidationError(f"{path}: {value!r} does not match {schema['pattern']!r}")
        if schema.get("format") == "date" and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValidationError(f"{path}: {value!r} is not YYYY-MM-DD")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise ValidationError(f"{path}: number below minimum {schema['minimum']!r}")
        if "maximum" in schema and value > schema["maximum"]:
            raise ValidationError(f"{path}: number above maximum {schema['maximum']!r}")

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise ValidationError(f"{path}: array shorter than minItems")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ValidationError(f"{path}: array longer than maxItems")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                validate_schema_subset(item_schema, item, f"{path}[{index}]")

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                raise ValidationError(f"{path}: missing required key {key!r}")

        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = set(value) - set(properties)
            if extra:
                raise ValidationError(f"{path}: unexpected keys {sorted(extra)!r}")

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
    if type_name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "null":
        return value is None
    return False


def validate_record_semantics(schema_name, record):
    if schema_name == "output-package":
        validate_required_stages(record, "creative_performance_map", "OutputPackage")
    if schema_name == "performance-summary":
        validate_required_stages(record, "stage_findings", "PerformanceSummary")


def validate_required_stages(record, field_name, record_name):
    observed = {
        entry.get("stage")
        for entry in record.get(field_name, [])
        if isinstance(entry, dict)
    }
    missing = REQUIRED_CREATIVE_STAGES - observed
    if missing:
        raise ValidationError(
            f"{record_name}.{field_name}: missing required stages {sorted(missing)!r}"
        )
