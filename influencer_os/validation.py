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

import datetime
import json
import math
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

SUPPORTED_FORMATS = {"date", "date-time"}

MAX_REF_CHAIN_LENGTH = 25

REQUIRED_CREATIVE_STAGES = {
    "packaging",
    "hook",
    "body_retention",
    "payoff",
    "cta",
}

# The Content Beat Spine (ADR 0024): the one closed template vocabulary.
# HOOK → RETAIN → PAYOFF → CTA are the content stages; packaging is the
# pre-hook stage (thumbnail/caption). Emotion is a per-beat attribute, not
# a stage.
BEAT_ROLES = ["hook", "retain", "payoff", "cta", "packaging"]

# Every template must at least land a hook and a payoff; retain/cta/packaging
# beats are template-specific.
REQUIRED_BEAT_ROLES = {"hook", "payoff"}

# Typed hook taxonomy (ADR 0024 Decision B): the 8 AOS categories plus the
# three web-validated additions from the cross-OS comparison.
HOOK_CATEGORIES = [
    "identity_call_out",
    "pattern_interrupt",
    "contrarian",
    "result_first",
    "curiosity_gap",
    "direct_challenge",
    "confession",
    "timeliness",
    "problem_solution",
    "reveal_teaser",
    "bold_promise",
]

# The intent fields captured at the idea origin and carried verbatim through
# promotion (ADR 0024: schema-optional, skill-required).
INTENT_FIELDS = ("intended_emotion", "core_message")

# The canonical ADR 0020 8-platform set (Creative Direction Decision A:
# per-file schema enums stay, but every copy — and every code copy — pins to
# this one constant via the drift check).
RESEARCH_PLATFORMS = (
    "x", "instagram", "tiktok", "substack", "medium", "reddit", "facebook", "linkedin",
)

# The pure modality enum (ADR 0024): carousel/story_sequence are formats,
# not modalities. Audio is selectable but has no production-plan schema in
# v1 — standalone-audio production warns.
CONTENT_MODALITIES = ("text", "image", "video", "audio")

# Advisory platform-fit vocabulary for the platform_fit ProjectWarning.
PLATFORM_FIT_LEVELS = ("native", "subtype", "analog", "none")

# Review roles with a built reviewer skill. The schema enum carries the full
# decided vocabulary (creator_fit and fact_check are approved for the reviews
# second slice), but a record claiming an unbuilt review ran fails closed.
BUILT_REVIEW_ROLES = {"hook_payoff"}

# Access methods for the ADR 0022 key-gated research-acquisition connectors.
# Standing-approved by API-key presence: they MAY be `use_now` (when the adapter
# is active) and need not set `approval_required`.
STANDING_APPROVED_ACCESS_METHODS = {
    "api_backed",
    "scraping_api",
}

# Access methods still fully gated: they may never be `use_now` and must set
# `approval_required` (logged-in sessions and unattended scheduled jobs).
FULLY_GATED_ACCESS_METHODS = {
    "logged_in_browser",
    "scheduled_job",
}

# Union retained for callers that mean "any provider/heavy access method".
GATED_RESEARCH_ACCESS_METHODS = STANDING_APPROVED_ACCESS_METHODS | FULLY_GATED_ACCESS_METHODS

# The exact ADR 0022 connectors that key presence standing-approves, each pinned
# to its expected access method (source of truth: connectors/registry.py).
# Standing approval is per (adapter_id, method), not to the access method at
# large: other api_backed/scraping_api adapters (e.g. youtube_data_api) stay
# gated, and a standing-approved adapter paired with the wrong method is not.
STANDING_APPROVED_ADAPTER_METHODS = {
    "reddit_api_or_search": "api_backed",
    "x_api": "api_backed",
    "firecrawl_public_web": "scraping_api",
    "linkedin_apify": "api_backed",
}

STANDING_APPROVED_ADAPTER_IDS = frozenset(STANDING_APPROVED_ADAPTER_METHODS)


def is_standing_approved_adapter(adapter_id, access_method):
    """True only for an exact ADR 0022 connector using its expected access method."""
    return STANDING_APPROVED_ADAPTER_METHODS.get(adapter_id) == access_method

LOW_YIELD_OUTCOMES = {
    "background_only",
    "no_platform_signal",
    "no_visible_metrics",
    "not_creator_fit",
    "not_current",
    "not_accessible",
    "skipped_approval_required",
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
            # Keep the shape check: 3.11+ fromisoformat also accepts other
            # ISO 8601 forms (e.g. 20260703) that must stay rejected.
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                raise ValidationError(f"{path}: {value!r} is not YYYY-MM-DD")
            try:
                datetime.date.fromisoformat(value)
            except ValueError:
                raise ValidationError(f"{path}: {value!r} is not a real calendar date") from None
        if format_name == "date-time" and isinstance(value, str):
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", value):
                raise ValidationError(f"{path}: {value!r} is not YYYY-MM-DDTHH:MM:SS")
            try:
                datetime.datetime.fromisoformat(value)
            except ValueError:
                raise ValidationError(f"{path}: {value!r} is not a real timestamp") from None

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            raise ValidationError(f"{path}: string shorter than minLength")
        if "pattern" in schema:
            pattern = schema["pattern"]
            # Python's `$` matches before a trailing newline under search;
            # treat fully anchored patterns as whole-string matches so a
            # value like "slot_x\n" cannot slip past the pin. Unanchored
            # patterns (e.g. the ^https?:// prefix pin) keep search
            # semantics per JSON Schema.
            anchored = (
                pattern.startswith("^")
                and pattern.endswith("$")
                and not pattern.endswith("\\$")
            )
            matched = re.fullmatch(pattern, value) if anchored else re.search(pattern, value)
            if not matched:
                raise ValidationError(f"{path}: {value!r} does not match {pattern!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        # NaN/Infinity are not valid JSON, and NaN silently defeats the
        # min/max comparisons below (all comparisons are false). Python's
        # json.loads accepts them by default, so reject them here fail-closed.
        if isinstance(value, float) and not math.isfinite(value):
            raise ValidationError(f"{path}: {value!r} is not a finite number")
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
    if schema_name == "social-template":
        validate_beat_spine(record, "beat_sequence", "SocialTemplate", require_coverage=True)
    if schema_name == "applied-social-template":
        validate_beat_spine(
            record, "applied_beats", "AppliedSocialTemplate", require_coverage=True
        )
    if schema_name == "output-package":
        validate_required_stages(record, "creative_performance_map", "OutputPackage")
        validate_output_package_assets(record)
    if schema_name == "performance-summary":
        # Uniqueness first: five findings with a repeated stage are better
        # reported as the duplicate than as the stage the repeat displaced.
        validate_unique_stages(record, "stage_findings", "PerformanceSummary")
        validate_required_stages(record, "stage_findings", "PerformanceSummary")
    if schema_name == "project-warning":
        validate_platform_fit_warning_semantics(record)
    if schema_name == "review-record":
        validate_review_record_semantics(record)
    if schema_name == "generation-approval-record":
        validate_generation_approval_semantics(record)
    if schema_name == "research-search-plan":
        validate_research_search_plan_semantics(record)
    if schema_name == "research-source-yield":
        validate_research_source_yield_semantics(record)


def validate_beat_spine(record, field_name, record_name, require_coverage):
    """Content Beat Spine semantics (ADR 0024, Creative Direction slice 1).

    The schema pins beat_role to the closed enum; this closes the gaps the
    schema cannot express: templates and applied templates must land at
    least a hook and a payoff (slice 2 review finding: hook/payoff stage
    findings must always have an applied beat to attribute to), and
    hook_category may only annotate a hook-role beat. Dropping a template's
    cta/packaging beat stays legitimate — the learning loop records an
    absent CTA as a `not_used` stage finding instead.
    """
    beats = [
        beat for beat in record.get(field_name, []) if isinstance(beat, dict)
    ]
    for index, beat in enumerate(beats):
        if "hook_category" in beat and beat.get("beat_role") != "hook":
            raise ValidationError(
                f"{record_name}.{field_name}[{index}]: hook_category is only "
                f"allowed on hook-role beats, got beat_role "
                f"{beat.get('beat_role')!r}"
            )
    if require_coverage:
        observed_roles = {beat.get("beat_role") for beat in beats}
        missing = REQUIRED_BEAT_ROLES - observed_roles
        if missing:
            raise ValidationError(
                f"{record_name}.{field_name}: template beats skip required "
                f"spine role(s) {sorted(missing)!r}"
            )


def validate_generation_approval_semantics(record):
    """GenerationApprovalRecord semantics (ADR 0023 Decision 2).

    The status ladder is draft -> approved -> executed | cancelled, and
    every field required by a status must be present exactly there: a draft
    carries no approval statement, an approved record carries the verbatim
    statement and timestamp, and only an executed record carries execution
    fields. Scope semantics: single_call approves exactly one asset and no
    batch cap; batch requires a cap the request stays within.
    """
    record_id = record.get("generation_approval_record_id", "<unknown>")
    has_project = "project_id" in record
    has_reference = "reference_asset_id" in record
    if has_project == has_reference:
        raise ValidationError(
            f"generation approval {record_id}: exactly one of project_id or "
            "reference_asset_id must be set (project or reference-library "
            "scope)"
        )
    if has_project and "plan_ref" not in record:
        raise ValidationError(
            f"generation approval {record_id}: project-scoped approvals must "
            "carry plan_ref (the exact plan the human approved)"
        )

    requested = record.get("requested_assets", [])
    asset_ids = [asset.get("asset_id") for asset in requested]
    duplicated = sorted({a for a in asset_ids if asset_ids.count(a) > 1})
    if duplicated:
        raise ValidationError(
            f"generation approval {record_id}: duplicate requested asset ids "
            f"{duplicated!r}"
        )

    scope = record.get("scope")
    if scope == "single_call":
        if "max_calls" in record:
            raise ValidationError(
                f"generation approval {record_id}: single_call scope carries "
                "no max_calls"
            )
        if len(requested) != 1:
            raise ValidationError(
                f"generation approval {record_id}: single_call scope approves "
                f"exactly one asset, got {len(requested)}"
            )
    if scope == "batch":
        if "max_calls" not in record:
            raise ValidationError(
                f"generation approval {record_id}: batch scope requires a "
                "bounded max_calls"
            )
        if len(requested) > record["max_calls"]:
            raise ValidationError(
                f"generation approval {record_id}: {len(requested)} requested "
                f"assets exceed the approved batch cap {record['max_calls']}"
            )

    status = record.get("status")
    has_statement = "user_approval_statement" in record
    has_approved_at = "approved_at" in record
    has_executed_at = "executed_at" in record
    has_results = bool(record.get("resulting_asset_ids"))
    if status == "draft":
        if has_statement or has_approved_at or has_executed_at or has_results:
            raise ValidationError(
                f"generation approval {record_id}: a draft carries no "
                "approval statement, approval timestamp, or execution fields"
            )
    if status in ("approved", "executed"):
        if not (has_statement and has_approved_at):
            raise ValidationError(
                f"generation approval {record_id}: status {status!r} requires "
                "the verbatim user_approval_statement and approved_at"
            )
    if status == "approved" and (has_executed_at or has_results):
        raise ValidationError(
            f"generation approval {record_id}: execution fields belong only "
            "on executed records"
        )
    if status == "executed":
        if not (has_executed_at and has_results):
            raise ValidationError(
                f"generation approval {record_id}: executed records require "
                "executed_at and non-empty resulting_asset_ids"
            )
        unknown_results = sorted(
            set(record["resulting_asset_ids"]) - set(asset_ids)
        )
        if unknown_results:
            raise ValidationError(
                f"generation approval {record_id}: resulting_asset_ids not in "
                f"the approved request: {unknown_results}"
            )
    if status == "cancelled" and (has_executed_at or has_results):
        raise ValidationError(
            f"generation approval {record_id}: cancelled records carry no "
            "execution fields"
        )


def validate_review_record_semantics(record):
    """ReviewRecord semantics (ADR 0024, Creative Direction slice 4).

    Creative reviews are advisory — none of these rules make a review
    blocking; they keep the record honest. A fallback execution names why
    the bounded sub-agent path was unavailable (and a bounded run carries
    no fallback excuse); a human waiver only means something when there is
    a blocking-severity finding to waive.
    """
    review_id = record.get("review_record_id", "<unknown>")
    review_role = record.get("review_role")
    if review_role is not None and review_role not in BUILT_REVIEW_ROLES:
        raise ValidationError(
            f"review record {review_id}: review_role {review_role!r} is "
            "approved but unbuilt (reviews second slice); a record may not "
            "claim an unbuilt review ran"
        )
    execution = record.get("reviewer_execution", {})
    mode = execution.get("execution_mode")
    if mode == "fallback_separated_pass" and "fallback_reason" not in execution:
        raise ValidationError(
            f"review record {review_id}: fallback_separated_pass requires "
            "fallback_reason"
        )
    if mode == "bounded_sub_agent" and "fallback_reason" in execution:
        raise ValidationError(
            f"review record {review_id}: fallback_reason is only allowed on "
            "fallback_separated_pass executions"
        )
    if "human_waiver" in record:
        has_blocking_finding = any(
            finding.get("severity") == "blocking"
            for finding in record.get("findings", [])
            if isinstance(finding, dict)
        )
        if not has_blocking_finding:
            raise ValidationError(
                f"review record {review_id}: human_waiver requires a "
                "blocking-severity finding to waive"
            )


def validate_platform_fit_warning_semantics(record):
    """A platform_fit warning always names its fit level, and fit_level is
    meaningless on any other warning type (Creative Direction slice 3)."""
    warning_id = record.get("project_warning_id", "<unknown>")
    if record.get("warning_type") == "platform_fit":
        if "fit_level" not in record:
            raise ValidationError(
                f"project warning {warning_id}: platform_fit warnings must "
                "carry fit_level"
            )
    elif "fit_level" in record:
        raise ValidationError(
            f"project warning {warning_id}: fit_level is only allowed on "
            "platform_fit warnings"
        )


def validate_intent_carry_forward(promotion, entry):
    """Intent captured at the idea origin survives promotion verbatim
    (ADR 0024). A promotion may neither drop, invent, nor rewrite
    intended_emotion / core_message relative to its source entry."""
    promotion_id = promotion.get("idea_promotion_id")
    entry_id = entry.get("idea_queue_entry_id")
    for field in INTENT_FIELDS:
        entry_value = entry.get(field)
        promotion_value = promotion.get(field)
        if entry_value == promotion_value:
            continue
        if entry_value is None:
            raise ValidationError(
                f"Idea promotion {promotion_id} carries {field} "
                f"{promotion_value!r} but its source entry {entry_id} has "
                "none; intent is captured at the idea origin, never invented "
                "at promotion"
            )
        if promotion_value is None:
            raise ValidationError(
                f"Idea promotion {promotion_id} drops {field} "
                f"{entry_value!r} from its source entry {entry_id}; "
                "promotion must carry the entry's intent verbatim"
            )
        raise ValidationError(
            f"Idea promotion {promotion_id} rewrites {field} from "
            f"{entry_value!r} to {promotion_value!r}; promotion must carry "
            f"the source entry {entry_id} intent verbatim"
        )


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


def validate_unique_stages(record, field_name, record_name):
    """Each attribution stage appears exactly once (Phase 2 slice 3).

    The schema's enum + minItems admits a stage list with repeats; this
    closes that gap. Combined with validate_required_stages, the five
    stages must appear exactly once each.
    """
    stages = [
        entry.get("stage")
        for entry in record.get(field_name, [])
        if isinstance(entry, dict)
    ]
    duplicated = sorted({stage for stage in stages if stages.count(stage) > 1})
    if duplicated:
        raise ValidationError(
            f"{record_name}.{field_name}: duplicate stages {duplicated!r}"
        )


def validate_research_search_plan_semantics(record):
    planned_platforms = set(record.get("platforms", []))
    for adapter in record.get("adapters_considered", []):
        if adapter.get("decision") == "use_now" and adapter.get("adapter_status") != "active":
            raise ValidationError(
                "ResearchSearchPlan.adapters_considered: only active adapters "
                "may have decision 'use_now'"
            )
        # ADR 0022: only the exact standing-approved connectors are exempt from
        # the gate. Every other gated access method (logged-in, scheduled, and
        # any non-approved api_backed/scraping_api adapter such as
        # youtube_data_api) may not be `use_now` and must require approval.
        access_method = adapter.get("access_method")
        if access_method in GATED_RESEARCH_ACCESS_METHODS and not is_standing_approved_adapter(
            adapter.get("adapter_id"), access_method
        ):
            if adapter.get("decision") == "use_now":
                raise ValidationError(
                    "ResearchSearchPlan.adapters_considered: gated access methods "
                    "cannot be used now unless the adapter is a standing-approved "
                    "ADR 0022 connector"
                )
            if adapter.get("approval_required") is not True:
                raise ValidationError(
                    "ResearchSearchPlan.adapters_considered: gated access methods "
                    "must require approval unless standing-approved"
                )

    for query in record.get("planned_queries", []):
        if query.get("platform") not in planned_platforms:
            raise ValidationError(
                "ResearchSearchPlan.planned_queries: query platform must be "
                "listed in top-level platforms"
            )

    for source in record.get("planned_sources", []):
        if source.get("platform") not in planned_platforms:
            raise ValidationError(
                "ResearchSearchPlan.planned_sources: source platform must be "
                "listed in top-level platforms"
            )
        if not (source.get("url") or source.get("source_ref")):
            raise ValidationError(
                "ResearchSearchPlan.planned_sources: each source needs url "
                "or source_ref"
            )


def validate_research_source_yield_semantics(record):
    outcome = record.get("outcome")
    evidence_ids = record.get("evidence_ids", [])
    if outcome == "promoted_to_evidence" and not evidence_ids:
        raise ValidationError(
            "ResearchSourceYield: promoted_to_evidence requires evidence_ids"
        )
    if outcome in LOW_YIELD_OUTCOMES and evidence_ids:
        raise ValidationError(
            "ResearchSourceYield: low-yield outcomes must not reference evidence_ids"
        )


TEXT_FORMAT_IDS = {"format_article", "format_thread"}


def validate_output_package_assets(record):
    upload_asset_ids = [asset["upload_asset_id"] for asset in record.get("upload_ready", [])]
    duplicate_asset_ids = sorted(
        asset_id for asset_id in set(upload_asset_ids) if upload_asset_ids.count(asset_id) > 1
    )
    if duplicate_asset_ids:
        raise ValidationError(
            f"OutputPackage.upload_ready: duplicate upload_asset_id values {duplicate_asset_ids!r}"
        )

    known_asset_ids = set(upload_asset_ids)
    upload_paths = [asset["path"] for asset in record.get("upload_ready", [])]
    known_upload_paths = set(upload_paths)
    duplicate_upload_paths = sorted(
        path for path in known_upload_paths if upload_paths.count(path) > 1
    )
    if duplicate_upload_paths:
        raise ValidationError(
            f"OutputPackage.upload_ready: duplicate path values {duplicate_upload_paths!r}"
        )

    primary_refs = set(record.get("universal_core", {}).get("primary_asset_refs", []))
    missing_primary_refs = sorted(primary_refs - known_asset_ids)
    if missing_primary_refs:
        raise ValidationError(
            "OutputPackage.universal_core.primary_asset_refs do not resolve to "
            f"upload_ready assets: {missing_primary_refs!r}"
        )

    for index, adaptation in enumerate(record.get("platform_adaptations", [])):
        universal_format_id = record.get("universal_core", {}).get("format_id")
        format_id = adaptation.get("format_id")
        if format_id != universal_format_id:
            raise ValidationError(
                "OutputPackage.platform_adaptations"
                f"[{index}].format_id does not match universal_core.format_id: "
                f"{format_id!r} != {universal_format_id!r}"
            )
        caption_path = adaptation.get("caption_or_description_path")
        if caption_path not in known_upload_paths:
            raise ValidationError(
                "OutputPackage.platform_adaptations"
                f"[{index}].caption_or_description_path does not resolve to "
                f"an upload_ready path: {caption_path!r}"
            )
        asset_id = adaptation.get("thumbnail_or_first_frame_asset_id")
        if asset_id is None:
            if format_id not in TEXT_FORMAT_IDS:
                raise ValidationError(
                    "OutputPackage.platform_adaptations"
                    f"[{index}].thumbnail_or_first_frame_asset_id is required for {format_id!r}"
                )
            continue
        if asset_id not in known_asset_ids:
            raise ValidationError(
                "OutputPackage.platform_adaptations"
                f"[{index}].thumbnail_or_first_frame_asset_id does not resolve to "
                f"an upload_ready asset: {asset_id!r}"
            )
