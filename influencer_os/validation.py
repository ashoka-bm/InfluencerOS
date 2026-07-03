"""Schema and record validation.

The schema validator implements a scoped, fail-closed subset of JSON Schema
(short-term plan, Execution Decisions 2026-07-02):

- supported constructs: the keywords in ``VALIDATION_KEYWORDS``, including
  intra-file ``$ref`` to ``#/definitions`` targets, ``oneOf``, ``anyOf``, and
  ``allOf``;
- fail-closed: an unrecognized keyword, type name, format, or construct form
  raises ``SchemaDefinitionError`` instead of being silently ignored, so a
  schema can never appear to validate through an unimplemented constraint.

Example coverage is derived from disk: every ``schemas/*.schema.json`` must
have a matching ``examples/*.example.json`` and vice versa.
"""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ANNOTATION_KEYWORDS = {
    "$comment",
    "$id",
    "$schema",
    "default",
    "definitions",
    "description",
    "examples",
    "title",
}

VALIDATION_KEYWORDS = {
    "$ref",
    "additionalProperties",
    "allOf",
    "anyOf",
    "const",
    "enum",
    "format",
    "items",
    "maxItems",
    "maximum",
    "minItems",
    "minLength",
    "minimum",
    "oneOf",
    "pattern",
    "properties",
    "required",
    "type",
}

KNOWN_KEYWORDS = ANNOTATION_KEYWORDS | VALIDATION_KEYWORDS

KNOWN_TYPE_NAMES = {"array", "boolean", "integer", "null", "number", "object", "string"}

SUPPORTED_FORMATS = {"date"}

MAX_REF_CHAIN_LENGTH = 25

REQUIRED_CREATIVE_STAGES = {
    "packaging",
    "hook",
    "body_retention",
    "payoff",
    "cta",
}


class ValidationError(AssertionError):
    pass


class SchemaDefinitionError(ValidationError):
    """The schema itself is invalid or uses an unsupported construct."""


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


def discover_example_schema_pairs(root=ROOT):
    schema_names = {
        path.name[: -len(".schema.json")]
        for path in (Path(root) / "schemas").glob("*.schema.json")
    }
    example_names = {
        path.name[: -len(".example.json")]
        for path in (Path(root) / "examples").glob("*.example.json")
    }

    missing_examples = sorted(schema_names - example_names)
    if missing_examples:
        raise ValidationError(f"schemas without a matching example: {missing_examples!r}")

    orphan_examples = sorted(example_names - schema_names)
    if orphan_examples:
        raise ValidationError(f"examples without a matching schema: {orphan_examples!r}")

    return [(name, name) for name in sorted(schema_names)]


def validate_examples(root=ROOT):
    results = []
    for schema_name, example_name in discover_example_schema_pairs(root=root):
        example_path = Path(root) / "examples" / f"{example_name}.example.json"
        validate_record(schema_name, load_json(example_path), root=root)
        results.append((schema_name, example_path))
    return results


def validate_schema_subset(schema, value, path="$", root_schema=None):
    if root_schema is None:
        root_schema = schema

    schema = _resolve_ref_chain(schema, root_schema, path)

    unknown = set(schema) - KNOWN_KEYWORDS
    if unknown:
        raise SchemaDefinitionError(
            f"{path}: unsupported schema keyword(s) {sorted(unknown)!r}; "
            "the validator is fail-closed, extend it before using new keywords"
        )

    _require_keyword_shapes(schema, path)

    expected_type = schema.get("type")
    if expected_type:
        allowed = expected_type if isinstance(expected_type, list) else [expected_type]
        unknown_types = [name for name in allowed if name not in KNOWN_TYPE_NAMES]
        if unknown_types:
            raise SchemaDefinitionError(f"{path}: unknown type name(s) {unknown_types!r}")
        if not any(_matches_type(value, type_name) for type_name in allowed):
            raise ValidationError(f"{path}: expected {allowed}, got {type(value).__name__}")

    if "const" in schema and value != schema["const"]:
        raise ValidationError(f"{path}: expected const {schema['const']!r}")

    if "enum" in schema and value not in schema["enum"]:
        raise ValidationError(f"{path}: {value!r} not in enum")

    if "format" in schema:
        format_name = schema["format"]
        if format_name not in SUPPORTED_FORMATS:
            raise SchemaDefinitionError(f"{path}: unsupported format {format_name!r}")
        if format_name == "date" and isinstance(value, str):
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                raise ValidationError(f"{path}: {value!r} is not YYYY-MM-DD")

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            raise ValidationError(f"{path}: string shorter than minLength")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            raise ValidationError(f"{path}: {value!r} does not match {schema['pattern']!r}")

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
                validate_schema_subset(item_schema, item, f"{path}[{index}]", root_schema)

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                raise ValidationError(f"{path}: missing required key {key!r}")

        properties = schema.get("properties", {})
        if schema.get("additionalProperties", True) is False:
            extra = set(value) - set(properties)
            if extra:
                raise ValidationError(f"{path}: unexpected keys {sorted(extra)!r}")

        for key, child_schema in properties.items():
            if key in value:
                validate_schema_subset(child_schema, value[key], f"{path}.{key}", root_schema)

    if "allOf" in schema:
        for index, subschema in enumerate(schema["allOf"]):
            validate_schema_subset(subschema, value, f"{path}(allOf[{index}])", root_schema)

    if "anyOf" in schema:
        match_count, failures = _run_combinator_branches(
            schema["anyOf"], value, path, root_schema, "anyOf"
        )
        if match_count == 0:
            raise ValidationError(f"{path}: value matches no anyOf branch: {failures!r}")

    if "oneOf" in schema:
        match_count, failures = _run_combinator_branches(
            schema["oneOf"], value, path, root_schema, "oneOf"
        )
        if match_count != 1:
            raise ValidationError(
                f"{path}: value matches {match_count} oneOf branches, expected exactly 1"
                + (f": {failures!r}" if match_count == 0 else "")
            )


def _require_keyword_shapes(schema, path):
    """Fail closed on malformed keyword VALUES, not just unknown keyword names.

    Without this, a malformed value degrades silently: `"enum": "abc"` becomes
    substring matching, and `"additionalProperties": "false"` is truthy and
    behaves like permissive true.
    """
    if "type" in schema:
        type_value = schema["type"]
        if isinstance(type_value, str):
            well_formed = bool(type_value)
        elif isinstance(type_value, list):
            well_formed = bool(type_value) and all(
                isinstance(name, str) and name for name in type_value
            )
        else:
            well_formed = False
        if not well_formed:
            raise SchemaDefinitionError(
                f"{path}: 'type' must be a non-empty string or a non-empty list of strings"
            )

    typed_keywords = (
        ("enum", list),
        ("required", list),
        ("properties", dict),
        ("items", dict),
        ("definitions", dict),
        ("allOf", list),
        ("anyOf", list),
        ("oneOf", list),
        ("pattern", str),
        ("format", str),
        ("additionalProperties", bool),
    )
    for keyword, expected in typed_keywords:
        if keyword in schema and not isinstance(schema[keyword], expected):
            raise SchemaDefinitionError(
                f"{path}: {keyword!r} must be a {expected.__name__}, "
                f"got {type(schema[keyword]).__name__}"
            )

    for keyword in ("allOf", "anyOf", "oneOf"):
        if keyword in schema:
            for index, member in enumerate(schema[keyword]):
                if not isinstance(member, dict):
                    raise SchemaDefinitionError(
                        f"{path}: {keyword}[{index}] must be a schema object, "
                        f"got {type(member).__name__}"
                    )

    for keyword in ("minLength", "minItems", "maxItems"):
        if keyword in schema:
            if isinstance(schema[keyword], bool) or not isinstance(schema[keyword], int):
                raise SchemaDefinitionError(f"{path}: {keyword!r} must be an integer")

    for keyword in ("minimum", "maximum"):
        if keyword in schema:
            bound = schema[keyword]
            if isinstance(bound, bool) or not isinstance(bound, (int, float)):
                raise SchemaDefinitionError(f"{path}: {keyword!r} must be a number")


def _run_combinator_branches(subschemas, value, path, root_schema, keyword):
    match_count = 0
    failures = []
    for index, subschema in enumerate(subschemas):
        try:
            validate_schema_subset(subschema, value, f"{path}({keyword}[{index}])", root_schema)
            match_count += 1
        except SchemaDefinitionError:
            # A broken branch schema must never read as "did not match".
            raise
        except ValidationError as error:
            failures.append(str(error))
    return match_count, failures


def _resolve_ref_chain(schema, root_schema, path):
    seen_refs = []
    while isinstance(schema, dict) and "$ref" in schema:
        ref = schema["$ref"]
        siblings = set(schema) - {"$ref"} - ANNOTATION_KEYWORDS
        if siblings:
            raise SchemaDefinitionError(
                f"{path}: $ref must not carry sibling validation keywords {sorted(siblings)!r}"
            )
        if not isinstance(ref, str) or not ref.startswith("#/"):
            raise SchemaDefinitionError(
                f"{path}: only intra-file '#/...' $ref targets are supported, got {ref!r}"
            )
        if ref in seen_refs or len(seen_refs) >= MAX_REF_CHAIN_LENGTH:
            raise SchemaDefinitionError(f"{path}: circular or too-deep $ref chain at {ref!r}")
        seen_refs.append(ref)
        schema = _resolve_json_pointer(root_schema, ref, path)
    return schema


def _resolve_json_pointer(root_schema, ref, path):
    target = root_schema
    for raw_token in ref[2:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if not (isinstance(target, dict) and token in target):
            raise SchemaDefinitionError(f"{path}: unresolvable $ref {ref!r}")
        target = target[token]
    if not isinstance(target, dict):
        raise SchemaDefinitionError(f"{path}: $ref {ref!r} does not resolve to a schema object")
    return target


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
