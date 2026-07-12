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
    "contains",
    "enum",
    "format",
    "items",
    "maxItems",
    "maxLength",
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

# The canonical research platform set (ADR 0020's 8 platforms plus youtube
# per ADR 0027; Creative Direction Decision A: per-file schema enums stay,
# but every copy — and every code copy — pins to this one constant via the
# drift check).
RESEARCH_PLATFORMS = (
    "x", "instagram", "tiktok", "substack", "medium", "reddit", "facebook", "linkedin",
    "youtube",
)

def research_platform_for_surface(surface):
    """Map a distribution surface (e.g. ``youtube_shorts``) to its canonical
    research platform, or None for surfaces off the research set."""
    for platform in RESEARCH_PLATFORMS:
        if surface == platform or surface.startswith(f"{platform}_"):
            return platform
    return None


# Source provenance may include background public-web records. Keep this
# separate from RESEARCH_PLATFORMS because the latter also drives production
# platform-fit checks and approval surfaces.
RESEARCH_SOURCE_PLATFORMS = RESEARCH_PLATFORMS + ("public_web",)
RESEARCH_SOURCE_CONTENT_TYPES = (
    "x_post", "x_thread",
    "instagram_reel", "instagram_post", "instagram_story", "instagram_carousel",
    "tiktok_video",
    "substack_article", "substack_note",
    "medium_article",
    "reddit_thread", "reddit_comment",
    "facebook_post", "facebook_reel",
    "linkedin_post", "linkedin_article",
    "youtube_video", "youtube_short", "youtube_comment",
    "public_web_page", "institutional_article", "research_article",
)

# The pure modality enum (ADR 0024): carousel/story_sequence are formats,
# not modalities. Audio is selectable but has no production-plan schema in
# v1 — standalone-audio production warns.
CONTENT_MODALITIES = ("text", "image", "video", "audio")

# Advisory platform-fit vocabulary for the platform_fit ProjectWarning.
PLATFORM_FIT_LEVELS = ("native", "subtype", "analog", "none")

# Improvement OS (ADR 0025) closed vocabularies. Criterion ids double as
# recurrence keys; the maturity ladder is minted -> proven -> blocking, with
# retired for criteria that no longer apply. Friction (rejection/incident)
# events are the only events that carry rubric fields.
RUBRIC_SCOPES = ("os", "creator")
CRITERION_STATUSES = ("minted", "proven", "blocking", "retired")
CRITERION_ORIGINS = ("seed", "rejection", "distillation")
FRICTION_EVENT_TYPES = ("rejection", "incident")

# Loop A falsifiable predictions (ADR 0025, D4): a Creative Performance Map
# stage may quantify its intended effect; the performance summary scores it
# confirmed/refuted/unmeasurable with the comparator recomputed mechanically.
PREDICTION_COMPARATORS = (">=", "<=", ">", "<")
PREDICTION_RESULTS = ("confirmed", "refuted", "unmeasurable")


def prediction_holds(measured_value, comparator, threshold):
    if comparator == ">=":
        return measured_value >= threshold
    if comparator == "<=":
        return measured_value <= threshold
    if comparator == ">":
        return measured_value > threshold
    if comparator == "<":
        return measured_value < threshold
    raise ValidationError(f"unknown prediction comparator {comparator!r}")

# Review roles with a built reviewer skill. The schema enum carries the full
# decided vocabulary, but a record claiming an unbuilt review ran fails closed.
PROJECT_SCOPED_REVIEW_ROLES = {"hook_payoff", "creator_fit", "fact_check"}
WORKSPACE_SCOPED_REVIEW_ROLES = {"setup", "strategy", "quarterly", "concept"}
BUILT_REVIEW_ROLES = {"hook_payoff", "setup", "strategy", "quarterly"}
REVIEW_ROLE_SOURCE_SKILLS = {
    "hook_payoff": "review-hook-payoff",
    "setup": "review-creator-setup",
    "strategy": "review-strategy",
    "quarterly": "review-quarter-plan",
}

CONTENT_BEAT_SPINE_AREAS = {"hook", "retain", "payoff", "cta", "general"}
WORKSPACE_REVIEW_AREAS = {
    "foundation",
    "positioning",
    "audience",
    "strategy",
    "evidence",
    "schedule",
    "visual_identity",
    "general",
}


def review_has_new_research_demand(review):
    return any(
        finding.get("research_demand") == "new"
        for finding in review.get("findings", [])
        if isinstance(finding, dict)
    )


def validate_research_demand_loops(reviews_by_id):
    """Validate computable Strategy/Quarterly Review lineage (ADR 0046)."""
    for review in reviews_by_id.values():
        role = review.get("review_role")
        if role not in {"strategy", "quarterly"}:
            continue
        label = "Strategy" if role == "strategy" else "Quarterly"
        review_id = review["review_record_id"]
        loop = review["research_demand_loop"]
        extra_round = loop["extra_research_round"]
        prior_review_id = loop["prior_review_record_id"]
        if extra_round == 0:
            if prior_review_id is not None:
                raise ValidationError(
                    f"{label} Review {review_id} round 0 must not name a prior review"
                )
            carried = any(
                finding.get("research_demand") == "carried_forward"
                for finding in review["findings"]
            )
            if carried:
                raise ValidationError(
                    f"{label} Review {review_id} round 0 cannot carry forward a "
                    "Demand without a prior review"
                )
            continue

        prior_review = reviews_by_id.get(prior_review_id)
        if prior_review is None:
            raise ValidationError(
                f"{label} Review {review_id} prior_review_record_id "
                f"{prior_review_id!r} does not resolve under workspace reviews/"
            )
        if prior_review.get("review_role") != role:
            raise ValidationError(
                f"{label} Review {review_id} prior_review_record_id "
                f"{prior_review_id!r} must reference a {role} review"
            )
        prior_loop = prior_review["research_demand_loop"]
        if prior_loop["extra_research_round"] != extra_round - 1:
            raise ValidationError(
                f"{label} Review {review_id} round {extra_round} must follow "
                f"round {extra_round - 1}"
            )
        if f"reviews/{prior_review_id}.json" not in review["artifact_refs"]:
            raise ValidationError(
                f"{label} Review {review_id} must include its prior {label} "
                "Review Record in artifact_refs"
            )
        if not review_has_new_research_demand(prior_review):
            raise ValidationError(
                f"{label} Review {review_id} may run only after prior review "
                f"{prior_review_id} issues new Research Demands"
            )
        prior_demands = {
            finding["note"]
            for finding in prior_review["findings"]
            if finding.get("research_demand") in {"new", "carried_forward"}
        }
        for finding in review["findings"]:
            if (
                finding.get("research_demand") == "carried_forward"
                and finding["note"] not in prior_demands
            ):
                raise ValidationError(
                    f"{label} Review {review_id} marks a Demand carried_forward "
                    f"that is not unresolved in its prior {label} Review"
                )

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

# The exact connectors that key presence standing-approves (ADR 0022, extended
# by ADR 0027), each pinned to its expected access method (source of truth:
# connectors/registry.py). Standing approval is per (adapter_id, method), not
# to the access method at large: other api_backed/scraping_api adapters stay
# gated, and a standing-approved adapter paired with the wrong method is not.
STANDING_APPROVED_ADAPTER_METHODS = {
    "reddit_api_or_search": "api_backed",
    "x_api": "api_backed",
    "firecrawl_public_web": "scraping_api",
    "linkedin_apify": "api_backed",
    "youtube_data_api": "api_backed",
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


def iter_jsonl_lines(path):
    """Yield non-empty JSONL lines without splitting legal JSON separators."""
    path = Path(path)
    # splitlines() would also break on U+2028/U+2029, which are legal inside
    # JSON strings and would corrupt both records and line numbers.
    for line_number, line in enumerate(path.read_text().split("\n"), start=1):
        if line.strip():
            yield line_number, line


def validate_jsonl_file(schema_name, path, record_check=None):
    """Validate every JSONL record and return the parsed records."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Missing JSONL file: {path}")
    records = []
    for line_number, line in iter_jsonl_lines(path):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"{path}:{line_number}: invalid JSON: {exc}") from None
        try:
            validate_record(schema_name, record)
            if record_check is not None:
                record_check(record)
        except ValidationError as exc:
            raise ValidationError(f"{path}:{line_number}: {exc}") from None
        records.append(record)
    return records


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
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            raise ValidationError(f"{path}: string longer than maxLength")
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
        if "contains" in schema:
            matches = 0
            failures = []
            for index, item in enumerate(value):
                try:
                    validate_schema_subset(
                        schema["contains"], item, f"{path}[{index}]", root_schema
                    )
                except ValidationError as exc:
                    failures.append(str(exc))
                else:
                    matches += 1
            if matches == 0:
                raise ValidationError(
                    f"{path}: array contains no matching item: {failures!r}"
                )

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
        ("contains", dict),
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

    for keyword in ("minLength", "maxLength", "minItems", "maxItems"):
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
        validate_stage_prediction_semantics(record)
    if schema_name == "project-warning":
        validate_platform_fit_warning_semantics(record)
    if schema_name == "review-record":
        validate_review_record_semantics(record)
    if schema_name == "generation-approval-record":
        validate_generation_approval_semantics(record)
    if schema_name == "generation-asset-manifest":
        validate_generation_manifest_semantics(record)
    if schema_name == "quality-review":
        validate_quality_review_semantics(record)
    if schema_name == "research-search-plan":
        validate_research_search_plan_semantics(record)
    if schema_name == "research-source-yield":
        validate_research_source_yield_semantics(record)
    if schema_name == "production-rubric":
        validate_rubric_semantics(record)
    if schema_name == "system-event":
        validate_system_event_semantics(record)
    if schema_name == "improvement-claim":
        validate_improvement_claim_semantics(record)
    if schema_name == "campaign":
        validate_campaign_semantics(record)
    if schema_name == "campaign-concept":
        validate_campaign_concept_semantics(record)
    if schema_name == "concept-approval":
        validate_concept_approval_semantics(record)
    if schema_name == "project" and "commercial_expression" in record:
        validate_project_commercial_expression(record)


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
    approval_basis = record.get("approval_basis")
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
    if approval_basis == "system_avatar_setup":
        if not has_reference:
            raise ValidationError(
                f"generation approval {record_id}: system_avatar_setup must be "
                "reference-library scoped"
            )
        if scope != "batch" or record.get("max_calls") != 1:
            raise ValidationError(
                f"generation approval {record_id}: system_avatar_setup must be a "
                "batch with max_calls 1"
            )
        if len(requested) != 1 or requested[0].get("asset_kind") != "image":
            raise ValidationError(
                f"generation approval {record_id}: system_avatar_setup must request "
                "exactly one image asset"
            )
        if has_statement or has_approved_at:
            raise ValidationError(
                f"generation approval {record_id}: system_avatar_setup carries no "
                "user approval metadata"
            )
    elif status in ("approved", "executing", "executed"):
        if not (has_statement and has_approved_at):
            raise ValidationError(
                f"generation approval {record_id}: status {status!r} requires "
                "the verbatim user_approval_statement and approved_at"
            )
    if status in ("approved", "executing") and (has_executed_at or has_results):
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
        results = record["resulting_asset_ids"]
        duplicated_results = sorted({r for r in results if results.count(r) > 1})
        if duplicated_results:
            raise ValidationError(
                f"generation approval {record_id}: duplicate "
                f"resulting_asset_ids {duplicated_results!r}"
            )
        # All-or-nothing honesty (batch-1 review finding): an executed record
        # accounts for every approved asset exactly once. Partial execution
        # is a crashed `executing` record, never a partially-filled
        # `executed` one.
        if set(results) != set(asset_ids):
            raise ValidationError(
                f"generation approval {record_id}: resulting_asset_ids must "
                "equal the approved requested_assets exactly; partial "
                "execution stays in status 'executing'"
            )
    if status == "cancelled" and (has_executed_at or has_results):
        raise ValidationError(
            f"generation approval {record_id}: cancelled records carry no "
            "execution fields"
        )


QUALITY_REVIEW_CHECKS = {
    "identity_consistency",
    "continuity_with_plan",
    "technical_conformance",
    "creator_boundary_compliance",
}


def validate_quality_review_semantics(record):
    """QualityReview semantics (ADR 0023 Decision 5): the closed checklist
    appears exactly once per check, and the overall verdict must agree with
    the items — a pass with a failing item (or a fail without one) is a
    dishonest record, not a judgment call. A pass also requires at least one
    genuinely passing item: all-not_applicable is no review at all (batch-3
    review finding)."""
    review_id = record.get("quality_review_id", "<unknown>")
    checks = [item.get("check") for item in record.get("checklist", [])]
    if sorted(checks) != sorted(QUALITY_REVIEW_CHECKS):
        raise ValidationError(
            f"quality review {review_id}: checklist must cover each of "
            f"{sorted(QUALITY_REVIEW_CHECKS)} exactly once, got {checks!r}"
        )
    scope_ids = [
        entry.get("asset_id")
        for entry in record.get("scope_assets", [])
        if isinstance(entry, dict)
    ]
    duplicated = sorted({a for a in scope_ids if scope_ids.count(a) > 1})
    if duplicated:
        raise ValidationError(
            f"quality review {review_id}: duplicate scope asset ids {duplicated!r}"
        )
    rubric_results = record.get("rubric_criteria_results", [])
    rubric_ids = [item.get("criterion_id") for item in rubric_results]
    duplicated_criteria = sorted({c for c in rubric_ids if rubric_ids.count(c) > 1})
    if duplicated_criteria:
        raise ValidationError(
            f"quality review {review_id}: duplicate rubric criteria results "
            f"{duplicated_criteria!r}"
        )
    results = [item.get("result") for item in record.get("checklist", [])]
    rubric_result_values = [item.get("result") for item in rubric_results]
    # Verdict agreement is status-aware (batch-3 review, High): only the
    # closed checklist FORCES a failing verdict at the record level. A
    # failing advisory (minted/proven) rubric result may coexist with a
    # passing verdict — advisory criteria gate nothing — while a failing
    # BLOCKING rubric result with a passing verdict is rejected at the
    # project seam, which knows criterion statuses. A rubric fail may still
    # JUSTIFY a failing verdict: the reviewer owns the judgment.
    has_failing_checklist = "fail" in results
    verdict = record.get("overall_verdict")
    if verdict == "pass" and has_failing_checklist:
        raise ValidationError(
            f"quality review {review_id}: overall_verdict 'pass' with a "
            "failing checklist item"
        )
    if verdict == "pass" and "pass" not in results:
        raise ValidationError(
            f"quality review {review_id}: overall_verdict 'pass' requires at "
            "least one passing checklist item; all-not_applicable reviews "
            "judge nothing"
        )
    if verdict == "fail" and not (has_failing_checklist or "fail" in rubric_result_values):
        raise ValidationError(
            f"quality review {review_id}: overall_verdict 'fail' requires at "
            "least one failing checklist or rubric item"
        )


def validate_rubric_semantics(record):
    """ProductionRubric semantics (ADR 0025): scope-conditional creator
    fields, unique criterion ids (they double as recurrence keys), and the
    blocking ADR pairing — a criterion may only block through a recorded
    gates-and-reviews ADR decision, and a non-blocking criterion carrying an
    ADR ref would misstate its authority."""
    rubric_id = record.get("rubric_id", "<unknown>")
    scope = record.get("scope")
    if scope == "creator":
        for field in ("creator_profile_id", "creator_slug"):
            if not record.get(field):
                raise ValidationError(
                    f"rubric {rubric_id}: scope 'creator' requires {field}"
                )
    if scope == "os":
        for field in ("creator_profile_id", "creator_slug"):
            if field in record:
                raise ValidationError(
                    f"rubric {rubric_id}: scope 'os' must not carry {field}"
                )
    seen_ids = set()
    for criterion in record.get("criteria", []):
        criterion_id = criterion.get("criterion_id", "<unknown>")
        if criterion_id in seen_ids:
            raise ValidationError(
                f"rubric {rubric_id}: duplicate criterion id {criterion_id!r}"
            )
        seen_ids.add(criterion_id)
        blocking = criterion.get("status") == "blocking"
        has_adr = "blocking_adr" in criterion
        if blocking and not has_adr:
            raise ValidationError(
                f"rubric {rubric_id}: blocking criterion {criterion_id!r} "
                "requires blocking_adr (gates-and-reviews ADR checklist)"
            )
        if not blocking and has_adr:
            raise ValidationError(
                f"rubric {rubric_id}: criterion {criterion_id!r} carries "
                "blocking_adr but is not blocking"
            )


def validate_system_event_semantics(record):
    """SystemEvent friction semantics (ADR 0025), the structural half of the
    Rubric Ratchet: rejection/incident events carry recurrence keys; a
    rejection cites exactly one of a criterion or unclassified: true; and a
    cited criterion id IS the recurrence key. Resolution against the
    collected rubric lives in rubric.check_event_resolution, which needs the
    filesystem."""
    event_id = record.get("event_id", "<unknown>")
    event_type = record.get("event_type")
    message = record.get("message", "")
    if "\n" in message or "\r" in message:
        raise ValidationError(
            f"event {event_id}: message must be one line — verdicts are "
            "durable, rejected material stays ephemeral (ADR 0025)"
        )
    friction = event_type in FRICTION_EVENT_TYPES
    for field in ("recurrence_key", "criterion_id", "iteration_count", "unclassified"):
        if field in record and not friction:
            raise ValidationError(
                f"event {event_id}: {field} is only valid on friction events "
                f"({', '.join(FRICTION_EVENT_TYPES)}), not {event_type!r}"
            )
    if friction and not record.get("recurrence_key"):
        raise ValidationError(
            f"event {event_id}: {event_type} events require recurrence_key"
        )
    if event_type == "rejection":
        has_criterion = "criterion_id" in record
        unclassified = record.get("unclassified") is True
        if has_criterion == unclassified:
            raise ValidationError(
                f"event {event_id}: a rejection must carry exactly one of "
                "criterion_id or unclassified: true (cite-or-mint, ADR 0025)"
            )
    if event_type == "incident" and record.get("unclassified"):
        raise ValidationError(
            f"event {event_id}: unclassified applies to rejections only"
        )
    if "criterion_id" in record and record.get("recurrence_key") != record["criterion_id"]:
        raise ValidationError(
            f"event {event_id}: recurrence_key must equal criterion_id when a "
            "criterion is cited (criterion ids are recurrence keys)"
        )


def validate_stage_prediction_semantics(record):
    """Record-shape half of the Loop A prediction contract (ADR 0025, D4):
    confirmed/refuted require a numeric measured_value, unmeasurable requires
    a reason and no measurement, and neither field appears without a
    prediction_result. The cross-record half — pairing against the Output
    Package's predictions and recomputing the comparator — lives in the
    summary↔package match seam (projects), which has both records."""
    for finding in record.get("stage_findings", []):
        stage = finding.get("stage", "<unknown>")
        result = finding.get("prediction_result")
        has_measured = "measured_value" in finding
        has_reason = "prediction_result_reason" in finding
        if result is None:
            if has_measured or has_reason:
                raise ValidationError(
                    f"PerformanceSummary stage {stage}: measured_value/"
                    "prediction_result_reason require a prediction_result"
                )
            continue
        if result in ("confirmed", "refuted"):
            if not isinstance(finding.get("measured_value"), (int, float)) or isinstance(
                finding.get("measured_value"), bool
            ):
                raise ValidationError(
                    f"PerformanceSummary stage {stage}: {result} requires a "
                    "numeric measured_value"
                )
            if has_reason:
                raise ValidationError(
                    f"PerformanceSummary stage {stage}: prediction_result_reason "
                    "applies to unmeasurable results only"
                )
        if result == "unmeasurable":
            if finding.get("measured_value") is not None:
                raise ValidationError(
                    f"PerformanceSummary stage {stage}: unmeasurable results "
                    "carry no measured_value"
                )
            if not finding.get("prediction_result_reason"):
                raise ValidationError(
                    f"PerformanceSummary stage {stage}: unmeasurable requires "
                    "prediction_result_reason"
                )


def validate_improvement_claim_semantics(record):
    """ImprovementClaim semantics (ADR 0025, D5): a closed claim records who
    closed it and when; an open claim carries neither. Status is the human's
    verdict — the mechanical count is reporting, never a writer."""
    claim_id = record.get("claim_id", "<unknown>")
    status = record.get("status")
    closed_fields = [field for field in ("closed_on", "closed_by") if field in record]
    if status == "open" and closed_fields:
        raise ValidationError(
            f"claim {claim_id}: open claims must not carry {closed_fields}"
        )
    if status in ("confirmed", "refuted", "withdrawn"):
        missing = [f for f in ("closed_on", "closed_by") if f not in record]
        if missing:
            raise ValidationError(
                f"claim {claim_id}: {status} claims require {missing}"
            )


def _duplicate_values(values):
    return sorted({value for value in values if values.count(value) > 1})


def validate_campaign_semantics(record):
    """Campaign semantics (ADR 0029): a paid-conversion campaign names its
    one primary paid offer; active/paused/completed carry the human
    activation metadata (archived may come straight from an unactivated
    draft, so it carries no requirement); supporting lists never repeat
    the primary."""
    campaign_id = record.get("campaign_id", "<unknown>")
    primary_offer = record.get("primary_offer_conversion_asset_id")
    if record.get("objective") == "paid_conversion" and not primary_offer:
        raise ValidationError(
            f"campaign {campaign_id}: a paid_conversion campaign requires "
            "primary_offer_conversion_asset_id (ADR 0029)"
        )
    if record.get("status") in ("active", "paused", "completed") and (
        "activation" not in record
    ):
        raise ValidationError(
            f"campaign {campaign_id}: status {record.get('status')!r} requires "
            "the human activation record"
        )
    if record.get("primary_content_pillar_id") in record.get(
        "supporting_content_pillar_ids", []
    ):
        raise ValidationError(
            f"campaign {campaign_id}: supporting pillars repeat the primary "
            f"pillar {record.get('primary_content_pillar_id')!r}"
        )
    if record.get("primary_audience_segment") in record.get(
        "supporting_audience_segments", []
    ):
        raise ValidationError(
            f"campaign {campaign_id}: supporting audience segments repeat "
            "the primary segment"
        )
    if primary_offer and primary_offer in record.get(
        "supporting_conversion_asset_ids", []
    ):
        raise ValidationError(
            f"campaign {campaign_id}: supporting conversion assets repeat "
            "the primary offer"
        )


def validate_campaign_concept_semantics(record):
    """CampaignConcept semantics (ADR 0030): one primary Commercial Function,
    supporting functions never repeat it; related concepts are unique and
    never self-referential."""
    concept_id = record.get("campaign_concept_id", "<unknown>")
    supporting = record.get("supporting_commercial_functions", [])
    if record.get("primary_commercial_function") in supporting:
        raise ValidationError(
            f"concept {concept_id}: supporting commercial functions repeat "
            f"the primary {record.get('primary_commercial_function')!r}"
        )
    if _duplicate_values(supporting):
        raise ValidationError(
            f"concept {concept_id}: supporting commercial functions repeat"
        )
    related_ids = [
        related.get("campaign_concept_id")
        for related in record.get("related_concepts", [])
    ]
    if concept_id in related_ids:
        raise ValidationError(
            f"concept {concept_id}: a concept cannot relate to itself"
        )
    duplicates = _duplicate_values(related_ids)
    if duplicates:
        raise ValidationError(
            f"concept {concept_id}: duplicate related concepts {duplicates!r}"
        )


def validate_concept_approval_semantics(record):
    """ConceptApproval semantics (ADR 0029): the approval authorizes an
    exact project set — ids are unique, and so are claimed slots."""
    approval_id = record.get("concept_approval_id", "<unknown>")
    duplicate_projects = _duplicate_values(record.get("project_ids_created", []))
    if duplicate_projects:
        raise ValidationError(
            f"concept approval {approval_id}: duplicate project ids "
            f"{duplicate_projects!r}"
        )
    duplicate_slots = _duplicate_values(record.get("schedule_slot_ids", []))
    if duplicate_slots:
        raise ValidationError(
            f"concept approval {approval_id}: duplicate schedule slots "
            f"{duplicate_slots!r}"
        )


def validate_project_commercial_expression(record):
    """Project commercial expression (ADR 0030): the planned offer
    integration and CTA intensity must form a valid pressure-matrix cell —
    pressure itself is derived, never stored."""
    from influencer_os.pressure import derive_commercial_pressure

    expression = record["commercial_expression"]
    try:
        derive_commercial_pressure(
            expression["offer_integration"], expression["cta_intensity"]
        )
    except ValidationError as exc:
        raise ValidationError(
            f"project {record.get('project_id', '<unknown>')}: {exc}"
        ) from None


def validate_generation_manifest_semantics(record):
    """GenerationAssetManifest semantics (ADR 0023 Decision 4).

    The ledger is the single provenance surface: rows are unique per asset
    and artifact, a generated row must bind to its approval record and plan
    prompt (viz-image-gen lineage), and an imported/user-provided row must
    carry its import origin (tool-image-search lineage) — never both shapes
    on one row.
    """
    rows = record.get("rows", [])
    asset_ids = [row.get("asset_id") for row in rows]
    duplicate_assets = sorted({a for a in asset_ids if asset_ids.count(a) > 1})
    if duplicate_assets:
        raise ValidationError(
            f"GenerationAssetManifest: duplicate asset ids {duplicate_assets!r}"
        )
    paths = [row.get("artifact_path") for row in rows]
    duplicate_paths = sorted({p for p in paths if paths.count(p) > 1})
    if duplicate_paths:
        raise ValidationError(
            f"GenerationAssetManifest: duplicate artifact paths {duplicate_paths!r}"
        )
    for row in rows:
        asset_id = row.get("asset_id", "<unknown>")
        if row.get("origin") == "generated":
            missing = [
                field
                for field in ("approval_record_id", "plan_prompt_ref", "provider_call")
                if field not in row
            ]
            if missing:
                raise ValidationError(
                    f"GenerationAssetManifest: generated row {asset_id} is "
                    f"missing {missing!r}; generated assets bind to their "
                    "approval record and plan prompt"
                )
            if "import_source" in row:
                raise ValidationError(
                    f"GenerationAssetManifest: generated row {asset_id} must "
                    "not carry import_source"
                )
        else:
            if "import_source" not in row:
                raise ValidationError(
                    f"GenerationAssetManifest: {row.get('origin')} row "
                    f"{asset_id} requires import_source"
                )
            forbidden = [
                field
                for field in ("approval_record_id", "plan_prompt_ref", "provider_call")
                if field in row
            ]
            if forbidden:
                raise ValidationError(
                    f"GenerationAssetManifest: {row.get('origin')} row "
                    f"{asset_id} must not carry generated-row fields "
                    f"{forbidden!r}"
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
    if review_role in PROJECT_SCOPED_REVIEW_ROLES and "project_id" not in record:
        raise ValidationError(
            f"review record {review_id}: project-scoped review {review_role!r} "
            "requires project_id"
        )
    if review_role in WORKSPACE_SCOPED_REVIEW_ROLES:
        if "project_id" in record:
            raise ValidationError(
                f"review record {review_id}: workspace-scoped review {review_role!r} "
                "must not carry project_id; it anchors by creator_profile_id"
            )
        if "concept_approval_id" in record:
            raise ValidationError(
                f"review record {review_id}: workspace-scoped review {review_role!r} "
                "must not carry concept_approval_id"
            )
    loop_roles = {"strategy", "quarterly"}
    if review_role in loop_roles and "research_demand_loop" not in record:
        raise ValidationError(
            f"review record {review_id}: {review_role} reviews require "
            "research_demand_loop"
        )
    if review_role not in loop_roles and "research_demand_loop" in record:
        raise ValidationError(
            f"review record {review_id}: research_demand_loop is only allowed "
            "on strategy and quarterly reviews"
        )
    allowed_areas = (
        CONTENT_BEAT_SPINE_AREAS
        if review_role in PROJECT_SCOPED_REVIEW_ROLES
        else WORKSPACE_REVIEW_AREAS
    )
    scope_label = "project-scoped" if review_role in PROJECT_SCOPED_REVIEW_ROLES else "workspace-scoped"
    for finding in record.get("findings", []):
        if not isinstance(finding, dict):
            continue
        area = finding.get("area")
        if area not in allowed_areas:
            raise ValidationError(
                f"review record {review_id}: {scope_label} review area {area!r} "
                "is outside its allowed vocabulary"
            )
        if (
            "research_demand" in finding
            and review_role not in WORKSPACE_SCOPED_REVIEW_ROLES
        ):
            raise ValidationError(
                f"review record {review_id}: research_demand marker is only "
                "allowed on ladder review roles"
            )
    execution = record.get("reviewer_execution", {})
    expected_skill = REVIEW_ROLE_SOURCE_SKILLS.get(review_role)
    if expected_skill is not None and execution.get("source_skill") != expected_skill:
        raise ValidationError(
            f"review record {review_id}: review_role {review_role!r} requires "
            f"reviewer_execution.source_skill {expected_skill!r}"
        )
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


def validate_intent_carry_forward(downstream, upstream, downstream_label,
                                  upstream_label):
    """Intent captured at the origin survives each hand-off verbatim
    (ADR 0024): an opportunity's intent pair survives concept assignment,
    and a concept's survives its approval — never dropped, invented, or
    rewritten downstream."""
    for field in INTENT_FIELDS:
        upstream_value = upstream.get(field)
        downstream_value = downstream.get(field)
        if upstream_value == downstream_value:
            continue
        if upstream_value is None:
            raise ValidationError(
                f"{downstream_label} carries {field} {downstream_value!r} "
                f"but its source {upstream_label} has none; intent is "
                "captured at the origin, never invented downstream"
            )
        if downstream_value is None:
            raise ValidationError(
                f"{downstream_label} drops {field} {upstream_value!r} from "
                f"its source {upstream_label}; intent carries forward verbatim"
            )
        raise ValidationError(
            f"{downstream_label} rewrites {field} from {upstream_value!r} "
            f"to {downstream_value!r}; intent from {upstream_label} carries "
            "forward verbatim"
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
        # ADR 0022/0027: only exact standing-approved connector+method pairs are
        # exempt from the gate. Every other gated access method (logged-in,
        # scheduled, and unapproved api_backed/scraping_api adapters) may not be
        # `use_now` and must require approval.
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

# Upload-ready roles that carry media (ADR 0023 slice 4): once a package's
# generation_status leaves planned_not_generated, these must bind to a
# generation-asset-manifest row. Text roles are exempt.
MEDIA_UPLOAD_ROLES = {"video", "image", "thumbnail"}


def validate_output_package_assets(record):
    generation_status = record.get("provider_boundary", {}).get("generation_status")
    if generation_status and generation_status != "planned_not_generated":
        for index, asset in enumerate(record.get("upload_ready", [])):
            if (
                asset.get("asset_role") in MEDIA_UPLOAD_ROLES
                and "generation_manifest_ref" not in asset
            ):
                raise ValidationError(
                    f"OutputPackage.upload_ready[{index}]: media assets must "
                    "carry generation_manifest_ref once generation_status is "
                    f"{generation_status!r} (ADR 0023 slice 4)"
                )

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
