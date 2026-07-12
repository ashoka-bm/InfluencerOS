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


def set_output_package_format(record, format_id):
    record["universal_core"].update(format_id=format_id)
    for adaptation in record["platform_adaptations"]:
        adaptation.update(format_id=format_id)
        if format_id in {"format_article", "format_thread"}:
            adaptation["thumbnail_or_first_frame_asset_id"] = None


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

    def test_approved_conversion_asset_requires_user_approval_at_record_boundary(self):
        record = load_json("examples/conversion-asset.example.json")
        invalid = deepcopy(record)
        invalid["approval"] = {
            "status": "pending",
            "approved_by": None,
            "approved_on": None,
            "notes": "Rendered but not reviewed.",
        }

        with self.assertRaises(ValidationError):
            validate_record("conversion-asset", invalid)

    def test_format_fields_reject_unknown_format_ids(self):
        # The format vocabulary is a closed enum (approval-surface decisions);
        # a typo like format_shortform_video must fail, not silently never match.
        cases = (
            ("concept-approval", lambda r: r["approved_formats"].append("format_interpretive_dance")),
            ("content-opportunity", lambda r: r["format_recommendations"].append("format_interpretive_dance")),
            ("project", lambda r: r["target_formats"].append("format_interpretive_dance")),
            (
                "creator-content-schedule",
                lambda r: r["content_goals"][0]["preferred_formats"].append("format_interpretive_dance"),
            ),
            ("output-package", lambda r: r["universal_core"].update(format_id="format_interpretive_dance")),
        )
        for schema_name, mutate in cases:
            invalid = deepcopy(load_json(f"examples/{schema_name}.example.json"))
            mutate(invalid)
            with self.subTest(schema=schema_name):
                with self.assertRaises(ValidationError):
                    validate_record(schema_name, invalid)

    def test_text_formats_are_supported_vocabulary(self):
        cases = (
            ("concept-approval", lambda r: r["approved_formats"].extend(["format_article", "format_thread"])),
            ("content-opportunity", lambda r: r["format_recommendations"].extend(["format_article", "format_thread"])),
            ("project", lambda r: r.update(target_formats=["format_article"])),
            (
                "creator-content-schedule",
                lambda r: r["content_goals"][0]["preferred_formats"].extend(["format_article", "format_thread"]),
            ),
            ("output-package", lambda r: set_output_package_format(r, "format_article")),
            ("applied-social-template", lambda r: r.update(target_format_id="format_thread")),
        )
        for schema_name, mutate in cases:
            valid = deepcopy(load_json(f"examples/{schema_name}.example.json"))
            mutate(valid)
            with self.subTest(schema=schema_name):
                validate_record(schema_name, valid)

    def test_text_output_package_allows_null_thumbnail_or_first_frame(self):
        package = deepcopy(load_json("examples/output-package.example.json"))
        package["universal_core"].update(format_id="format_article")
        for adaptation in package["platform_adaptations"]:
            adaptation.update(
                format_id="format_article",
                thumbnail_or_first_frame_asset_id=None,
            )

        validate_record("output-package", package)

    def test_visual_output_package_requires_thumbnail_or_first_frame(self):
        package = deepcopy(load_json("examples/output-package.example.json"))
        package["platform_adaptations"][0]["thumbnail_or_first_frame_asset_id"] = None

        with self.assertRaises(ValidationError):
            validate_record("output-package", package)

    def test_output_package_asset_refs_must_resolve_to_upload_ready_assets(self):
        package = deepcopy(load_json("examples/output-package.example.json"))
        package["universal_core"]["primary_asset_refs"] = ["upload_asset_missing"]

        with self.assertRaises(ValidationError):
            validate_record("output-package", package)

    def test_output_package_platform_adaptations_match_universal_format(self):
        package = deepcopy(load_json("examples/output-package.example.json"))
        package["platform_adaptations"][0]["format_id"] = "format_article"

        with self.assertRaises(ValidationError):
            validate_record("output-package", package)

    def test_project_rejects_production_unsupported_unit_type(self):
        # multi_platform_package has no production plan schema yet.
        example = load_json("examples/project.example.json")
        invalid = deepcopy(example)
        invalid["content_unit_type"] = "multi_platform_package"

        with self.assertRaises(ValidationError):
            validate_record("project", invalid)

    def test_project_accepts_text_unit_types(self):
        example = load_json("examples/project.example.json")
        for unit_type, format_id in (
            ("article", "format_article"),
            ("thread", "format_thread"),
        ):
            project = deepcopy(example)
            project["content_unit_type"] = unit_type
            project["target_formats"] = [format_id]
            with self.subTest(unit_type=unit_type):
                validate_record("project", project)

    def test_project_rejects_multiple_target_formats_at_record_level(self):
        example = load_json("examples/project.example.json")
        invalid = deepcopy(example)
        invalid["target_formats"].append("format_article")

        with self.assertRaises(ValidationError):
            validate_record("project", invalid)

    def test_project_requires_acceptance_criteria(self):
        example = load_json("examples/project.example.json")
        invalid = deepcopy(example)
        invalid.pop("acceptance_criteria")

        with self.assertRaises(ValidationError):
            validate_record("project", invalid)

    def test_public_web_evidence_validates_with_honest_source_type(self):
        evidence = deepcopy(load_json("examples/research-evidence.example.json"))
        evidence.update(
            evidence_id="evidence_luna_fit_public_web_001",
            platform="public_web",
            platform_content_type="institutional_article",
            source_url="https://www.mayoclinic.org/healthy-lifestyle/fitness/in-depth/stretching/art-20047931",
            source_summary="Institutional background article about stretching basics.",
            signal_summary="Background context only; not native social performance evidence.",
            confidence="medium",
            limitations="No native social engagement metrics were available.",
        )
        evidence.pop("source_account", None)
        evidence.pop("visible_metrics", None)

        validate_record("research-evidence", evidence)

    def test_public_web_metric_snapshot_validates_without_youtube_claim(self):
        snapshot = deepcopy(load_json("examples/metric-snapshot.example.json"))
        snapshot.update(
            metric_snapshot_id="metric_snapshot_luna_fit_public_web_001",
            evidence_id="evidence_luna_fit_public_web_001",
            platform="public_web",
            visible_metrics={
                "other": "No social engagement metrics captured; public web source only."
            },
            observed_age="Public page available as of capture date.",
            velocity_estimate="unknown",
            reference_creator_baseline="not applicable",
            outperformance_note="No platform performance claim.",
        )

        validate_record("metric-snapshot", snapshot)
        self.assertNotEqual(snapshot["platform"], "youtube")

    def test_public_web_search_term_validates_without_youtube_claim(self):
        terms = deepcopy(load_json("examples/research-search-terms.example.json"))
        terms["items"][0]["platform"] = "public_web"
        terms["items"][0]["rationale"] = (
            "Grounds public-web source discovery without claiming native "
            "YouTube evidence."
        )

        validate_record("research-search-terms", terms)
        self.assertNotEqual(terms["items"][0]["platform"], "youtube")

    def test_public_web_research_source_validates_without_youtube_claim(self):
        sources = deepcopy(load_json("examples/research-sources.example.json"))
        sources["items"][0]["platform"] = "public_web"
        sources["items"][0]["url"] = "https://www.mayoclinic.org/healthy-lifestyle/adult-health/in-depth/office-stretches/art-20046041"
        sources["items"][0]["rationale"] = (
            "Tracks a public-web source for safety grounding without claiming "
            "native YouTube evidence."
        )

        validate_record("research-sources", sources)
        self.assertNotEqual(sources["items"][0]["platform"], "youtube")

    def test_project_source_refs_allow_public_web_without_youtube_claim(self):
        project = deepcopy(load_json("examples/project.example.json"))
        source_refs = project["source_refs"]
        source_refs["source_platforms"] = ["public_web"]
        source_refs["source_platform_content_types"] = ["research_article"]

        validate_record("project", project)
        self.assertNotIn("youtube", source_refs["source_platforms"])
        self.assertNotIn("youtube_video", source_refs["source_platform_content_types"])

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
            "sources/intakes/..",
            "sources/intakes/.",
            "sources/intakes/trailing-newline.md\n",
        ):
            invalid = deepcopy(example)
            invalid["source_intakes"][0]["path"] = bad_path
            with self.subTest(path=bad_path):
                with self.assertRaises(ValidationError):
                    validate_record("creator-workspace", invalid)

        valid = deepcopy(example)
        valid["source_intakes"][0]["path"] = "sources/imports/exported-brand-doc.md"
        validate_record("creator-workspace", valid)

    def test_creator_workspace_accepts_onboarding_stage_statuses(self):
        example = load_json("examples/creator-workspace.example.json")
        for status in (
            "draft",
            "profile_ready",
            "foundation_ready",
            "strategy_ready",
            "production_ready",
            "active",
            "archived",
        ):
            valid = deepcopy(example)
            valid["status"] = status
            with self.subTest(status=status):
                validate_record("creator-workspace", valid)

    def test_creator_workspace_only_accepts_deprecated_statuses_that_can_be_warned(self):
        example = load_json("examples/creator-workspace.example.json")
        for status in ("content_ready", "generation_ready"):
            legacy = deepcopy(example)
            legacy["status"] = status
            with self.subTest(status=status):
                validate_record("creator-workspace", legacy)

        for status in ("foundation_review", "unknown_ready"):
            invalid = deepcopy(example)
            invalid["status"] = status
            with self.subTest(status=status):
                with self.assertRaises(ValidationError):
                    validate_record("creator-workspace", invalid)

    def test_creator_workspace_requires_onboarding_canonical_files(self):
        example = load_json("examples/creator-workspace.example.json")
        for field in ("readiness_gates", "channels", "content_strategy"):
            invalid = deepcopy(example)
            invalid["canonical_files"].pop(field, None)
            with self.subTest(field=field):
                with self.assertRaises(ValidationError):
                    validate_record("creator-workspace", invalid)

        invalid = deepcopy(example)
        invalid["directories"].pop("conversion_assets", None)
        with self.assertRaises(ValidationError):
            validate_record("creator-workspace", invalid)

    def test_applied_template_format_is_closed_vocabulary(self):
        # The plan-layer format field was the only format-typed property
        # outside the closed enum; a made-up format must fail at the schema.
        example = load_json("examples/applied-social-template.example.json")
        invalid = deepcopy(example)
        invalid["target_format_id"] = "format_interpretive_dance"

        with self.assertRaises(ValidationError):
            validate_record("applied-social-template", invalid)

    def test_concept_approval_requires_evidence_refs(self):
        # Projects resolve evidence provenance transitively through the
        # locked approval, so an approval with no evidence refs would sever
        # the Product Invariant's research-evidence trace silently.
        example = load_json("examples/concept-approval.example.json")
        invalid = deepcopy(example)
        invalid["evidence_refs"] = []

        with self.assertRaises(ValidationError):
            validate_record("concept-approval", invalid)

    def test_video_style_primary_is_optional_for_text_first_creators(self):
        example = load_json("examples/creator-profile.example.json")
        text_first = deepcopy(example)
        text_first["reference_refs"].pop("primary_video_style_asset_id")

        validate_record("creator-profile", text_first)

    def test_reference_asset_paths_are_pinned_under_references(self):
        example = load_json("examples/reference-library.example.json")
        for field, bad_value in (
            ("path", "../../outside-asset.png"),
            ("path", "/tmp/outside-asset.png"),
            ("path", "sources/notes/misfiled-asset.png"),
            ("path", "references/character/nested/too-deep.png"),
            ("path", "references/character/.."),
            ("path", "references/character/plate.png\n"),
            ("prompt_path", "../escape.prompt.md"),
        ):
            invalid = deepcopy(example)
            invalid["assets"][0][field] = bad_value
            with self.subTest(field=field, value=bad_value):
                with self.assertRaises(ValidationError):
                    validate_record("reference-library", invalid)

    def test_visual_continuity_approval_requires_user_metadata(self):
        example = load_json("examples/visual-continuity-plan.example.json")
        validate_record("visual-continuity-plan", example)

        invalid = deepcopy(example)
        invalid["selection_review"]["decided_by"] = None

        with self.assertRaises(ValidationError):
            validate_record("visual-continuity-plan", invalid)

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

    def test_search_plan_rejects_non_active_adapter_used_now(self):
        # The deferred logged-in adapter flipped to use_now must fail: only
        # active adapters may be used now.
        example = load_json("examples/research-search-plan.example.json")
        invalid = deepcopy(example)
        adapter = next(
            a for a in invalid["adapters_considered"]
            if a["adapter_id"] == "instagram_logged_in_browser"
        )
        adapter["decision"] = "use_now"

        with self.assertRaises(ValidationError):
            validate_record("research-search-plan", invalid)

    def test_search_plan_allows_active_key_gated_connector_use_now(self):
        # ADR 0022: an active api_backed/scraping_api connector is standing-
        # approved by key presence, so use_now with approval_required false is valid.
        example = load_json("examples/research-search-plan.example.json")
        valid = deepcopy(example)
        valid["adapters_considered"].append({
            "adapter_id": "reddit_api_or_search",
            "access_method": "api_backed",
            "adapter_status": "active",
            "auth_required": True,
            "approval_required": False,
            "decision": "use_now",
            "reason": "OPENAI_API_KEY present; standing-approved research connector.",
        })
        validate_record("research-search-plan", valid)  # must not raise

    def test_search_plan_allows_active_youtube_data_api_use_now(self):
        # ADR 0027: youtube_data_api is standing-approved by key presence.
        example = load_json("examples/research-search-plan.example.json")
        valid = deepcopy(example)
        valid["platforms"].append("youtube")
        valid["adapters_considered"].append({
            "adapter_id": "youtube_data_api",
            "access_method": "api_backed",
            "adapter_status": "active",
            "auth_required": True,
            "approval_required": False,
            "decision": "use_now",
            "reason": "YOUTUBE_API_KEY present; standing-approved public YouTube research connector.",
        })
        valid["planned_queries"].append({
            "query_id": "query_luna_fit_youtube_001",
            "platform": "youtube",
            "query_intent": "trend_scan",
            "query": "desk stretch routine",
            "source_type": "search_term",
            "purpose": "Check current YouTube video patterns around desk reset routines.",
            "expected_signal": "Recent public videos with visible engagement and reusable hooks.",
            "routing_basis": "Term from creator_profile.json desk wellness pillar.",
            "term_basis": ["creator_profile"],
        })

        validate_record("research-search-plan", valid)

    def test_search_plan_rejects_non_approved_api_backed_use_now(self):
        # instagram_logged_in_api is api_backed but NOT a standing-approved
        # connector, so active + use_now + approval false must still fail.
        example = load_json("examples/research-search-plan.example.json")
        invalid = deepcopy(example)
        invalid["adapters_considered"].append({
            "adapter_id": "instagram_logged_in_api",
            "access_method": "api_backed",
            "adapter_status": "active",
            "auth_required": True,
            "approval_required": False,
            "decision": "use_now",
            "reason": "attempting to use an unapproved api_backed adapter now",
        })
        with self.assertRaises(ValidationError):
            validate_record("research-search-plan", invalid)

    def test_search_plan_still_rejects_loggedin_use_now(self):
        example = load_json("examples/research-search-plan.example.json")
        invalid = deepcopy(example)
        invalid["adapters_considered"].append({
            "adapter_id": "instagram_logged_in_browser",
            "access_method": "logged_in_browser",
            "adapter_status": "active",
            "auth_required": True,
            "approval_required": True,
            "decision": "use_now",
            "reason": "attempting to use a logged-in session directly",
        })
        with self.assertRaises(ValidationError):
            validate_record("research-search-plan", invalid)

    def test_search_plan_rejects_query_outside_planned_platforms(self):
        example = load_json("examples/research-search-plan.example.json")
        invalid = deepcopy(example)
        invalid["platforms"] = ["instagram", "tiktok"]

        with self.assertRaises(ValidationError):
            validate_record("research-search-plan", invalid)

    def test_search_plan_requires_planned_source_url_or_ref(self):
        example = load_json("examples/research-search-plan.example.json")
        invalid = deepcopy(example)
        invalid["planned_sources"][0].pop("url")
        invalid["planned_sources"][0].pop("source_ref")

        with self.assertRaises(ValidationError):
            validate_record("research-search-plan", invalid)

    def test_search_plan_query_requires_term_basis(self):
        example = load_json("examples/research-search-plan.example.json")
        invalid = deepcopy(example)
        invalid["planned_queries"][0].pop("term_basis")

        with self.assertRaises(ValidationError):
            validate_record("research-search-plan", invalid)

    def test_search_plan_rejects_unknown_term_basis(self):
        example = load_json("examples/research-search-plan.example.json")
        invalid = deepcopy(example)
        invalid["planned_queries"][0]["term_basis"] = ["outside_trend_list"]

        with self.assertRaises(ValidationError):
            validate_record("research-search-plan", invalid)

    def test_source_yield_promoted_outcome_requires_evidence(self):
        example = load_json("examples/research-source-yield.example.json")
        invalid = deepcopy(example)
        invalid["evidence_ids"] = []

        with self.assertRaises(ValidationError):
            validate_record("research-source-yield", invalid)

    def test_source_yield_low_yield_outcome_rejects_evidence(self):
        example = load_json("examples/research-source-yield.example.json")
        invalid = deepcopy(example)
        invalid["outcome"] = "not_creator_fit"

        with self.assertRaises(ValidationError):
            validate_record("research-source-yield", invalid)


class ResearchFetchResultSchemaTests(unittest.TestCase):
    def valid_result(self):
        return {
            "connector": "reddit_openai",
            "adapter_id": "reddit_api_or_search",
            "platform": "reddit",
            "topic": "pothos",
            "from_date": "2026-06-05",
            "to_date": "2026-07-05",
            "model": "gpt-4o",
            "candidates": [
                {
                    "id": "R1",
                    "url": "https://www.reddit.com/r/s/comments/a/t/",
                    "title": "Pothos help",
                }
            ],
            "enriched_count": 1,
            "calls_used": 1,
            "truncated": False,
            "capped": False,
            "status": "ok",
            "notes": [],
        }

    def test_fetch_candidate_rejects_unknown_payload_fields(self):
        record = self.valid_result()
        record["candidates"][0]["raw_provider_payload"] = {"secret": "not for this boundary"}

        with self.assertRaises(ValidationError):
            validate_record("research-fetch-result", record)

    def test_fetch_candidate_rejects_overlong_text(self):
        record = self.valid_result()
        record["candidates"][0]["title"] = "x" * 301

        with self.assertRaises(ValidationError):
            validate_record("research-fetch-result", record)


class AtomicJsonWriteTests(unittest.TestCase):
    def test_atomic_json_write_preserves_existing_file_when_replace_fails(self):
        from influencer_os.json_io import write_json_atomic

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "record.json"
            path.write_text('{"status": "approved"}\n')

            def fail_replace(_source, _destination):
                raise OSError("replace failed")

            with self.assertRaises(OSError):
                write_json_atomic(path, {"status": "executing"}, replace=fail_replace)

            self.assertEqual(json.loads(path.read_text()), {"status": "approved"})
            self.assertEqual(list(Path(temp_dir).glob(".*.tmp")), [])


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

    def test_contains_requires_a_matching_item(self):
        schema = {"type": "array", "contains": {"type": "string"}}

        with self.assertRaises(ValidationError):
            validate_schema_subset(schema, [])

    def test_contains_is_supported_inside_a_matching_combinator(self):
        schema = {"anyOf": [{"type": "string"}, {"contains": {"type": "string"}}]}

        validate_schema_subset(schema, "matches-first-branch")

    def test_date_format_rejects_impossible_calendar_dates(self):
        # Shape-only checking would accept 2026-99-99 as durable evidence dates.
        schema = {"type": "string", "format": "date"}

        validate_schema_subset(schema, "2026-07-03")
        with self.assertRaises(ValidationError):
            validate_schema_subset(schema, "2026-99-99")
        with self.assertRaises(ValidationError):
            validate_schema_subset(schema, "2026-02-30")

    def test_date_time_format_requires_real_timestamps(self):
        schema = {"type": "string", "format": "date-time"}

        validate_schema_subset(schema, "2026-07-03T14:30:00")
        for bad_value in (
            "2026-07-03",  # date without time
            "2026-07-03 14:30:00",  # missing T separator
            "2026-99-99T14:30:00",  # impossible date
            "2026-07-03T25:00:00",  # impossible time
        ):
            with self.subTest(value=bad_value):
                with self.assertRaises(ValidationError):
                    validate_schema_subset(schema, bad_value)

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

    def test_anchored_patterns_match_the_whole_string(self):
        # Python's `$` tolerates a trailing newline under re.search; anchored
        # ^...$ patterns must behave as whole-string matches instead.
        schema = {"type": "string", "pattern": "^slot_[a-zA-Z0-9_-]+$"}

        validate_schema_subset(schema, "slot_weekly_reset")
        with self.assertRaises(ValidationError):
            validate_schema_subset(schema, "slot_weekly_reset\n")

    def test_unanchored_patterns_keep_search_semantics(self):
        # Prefix patterns like the URL pin stay unanchored on the right.
        schema = {"type": "string", "pattern": "^https?://"}

        validate_schema_subset(schema, "https://example.com/post")
        with self.assertRaises(ValidationError):
            validate_schema_subset(schema, "ftp://example.com/post")

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


class MaxLengthKeywordTests(unittest.TestCase):
    """maxLength joined the supported subset for the ADR 0025 one-line
    message cap; like every keyword it validates fail-closed."""

    def test_string_longer_than_max_length_fails(self):
        schema = {"type": "string", "maxLength": 5}
        validate_schema_subset(schema, "12345")
        with self.assertRaisesRegex(ValidationError, "longer than maxLength"):
            validate_schema_subset(schema, "123456")

    def test_max_length_must_be_an_integer(self):
        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset({"type": "string", "maxLength": "5"}, "x")
        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset({"type": "string", "maxLength": True}, "x")
