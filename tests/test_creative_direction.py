"""Creative Direction workstream checks (ADR 0024).

Slice 1: the Content Beat Spine is the one template vocabulary, and the
intent pair (intended_emotion / core_message) is captured at the idea origin
and survives promotion verbatim.

Slice 2: the micro-journey plan is spine-shaped, plans resolve intent by
reference (never override the locked promotion), and the learning loop
speaks spine (an unplanned CTA reads `not_used`, never a judged result).
"""

import json
import tempfile
import unittest
from pathlib import Path

from influencer_os.creator_workspaces import validate_creator_workspace
from influencer_os.projects import validate_project
from influencer_os.research import validate_approval_gate, validate_research
from influencer_os.validation import (
    ValidationError,
    validate_file,
    validate_record,
)
from tests.support import scaffold_project_workspace
from tests.test_performance_summary import (
    ingest_example_snapshot,
    scaffold_summarized_project,
    write_summary,
)
from tests.test_analytics import scaffold_published_project
from tests.test_research_validation import (
    ENTRY_ID,
    scaffold_research_workspace,
    write_json,
)


ROOT = Path(__file__).resolve().parents[1]

SETUP_REVIEW_PACKET = [
    "creator-profile.json",
    "brand_context/identity.md",
    "brand_context/soul.md",
    "brand_context/personal-brand.md",
    "references/reference-library.json",
    "references/character/luna-identity-plate.png",
    "references/visual-continuity-plan.json",
]

STRATEGY_REVIEW_PACKET = [
    "creator-profile.json",
    "content-strategy.json",
    "content-schedule.json",
    "research/findings.md",
    "research/runs/research_run_luna_fit_2026_07_03_001/evidence.jsonl",
]

QUARTERLY_REVIEW_PACKET = [
    "creator-profile.json",
    "quarter-plans/packets/quarter_plan_luna_fit_001/draft-quarter-plan.json",
    "quarter-plans/packets/quarter_plan_luna_fit_001/campaign-concept-set.json",
    "research/findings.md",
    "research/runs/research_run_luna_fit_2026_07_03_001/evidence.jsonl",
]

CONCEPT_REVIEW_PACKET = [
    "creator-profile.json",
    "content-schedule.json",
    "research/findings.md",
    "research/runs/research_run_luna_fit_2026_07_03_001/evidence.jsonl",
    "research/content-opportunity-queue/entries/content_opportunity_luna_fit_001.json",
    "research/content-opportunity-queue/entries/content_opportunity_luna_fit_002.json",
]


def copy_example_record(example_name, destination):
    destination.write_text((ROOT / "examples" / example_name).read_text())


def rewrite_json(path, mutate):
    record = json.loads(path.read_text())
    mutate(record)
    path.write_text(json.dumps(record, indent=2) + "\n")

SEEDED_TEMPLATE_DIR = ROOT / "docs" / "templates" / "social-templates"

# Decision C (approved 2026-07-06): the five named-framework presets.
SEEDED_TEMPLATE_IDS = {
    "template_pas",
    "template_before_after_bridge",
    "template_listicle",
    "template_myth_truth",
    "template_i_tried_x",
}


def load_example(name):
    return json.loads((ROOT / "examples" / f"{name}.example.json").read_text())


class BeatSpineTests(unittest.TestCase):
    def test_template_beats_require_beat_role(self):
        template = load_example("social-template")
        del template["beat_sequence"][0]["beat_role"]
        with self.assertRaisesRegex(ValidationError, "beat_role"):
            validate_record("social-template", template)

    def test_template_beat_role_outside_spine_enum_fails(self):
        template = load_example("social-template")
        template["beat_sequence"][0]["beat_role"] = "emotion"
        with self.assertRaisesRegex(ValidationError, "not in enum"):
            validate_record("social-template", template)

    def test_template_skipping_hook_fails(self):
        template = load_example("social-template")
        for beat in template["beat_sequence"]:
            if beat["beat_role"] == "hook":
                beat.pop("hook_category", None)
                beat["beat_role"] = "retain"
        with self.assertRaisesRegex(ValidationError, r"skip required spine role.*hook"):
            validate_record("social-template", template)

    def test_template_skipping_payoff_fails(self):
        template = load_example("social-template")
        for beat in template["beat_sequence"]:
            if beat["beat_role"] == "payoff":
                beat["beat_role"] = "retain"
        with self.assertRaisesRegex(ValidationError, r"skip required spine role.*payoff"):
            validate_record("social-template", template)

    def test_hook_category_on_non_hook_beat_fails(self):
        template = load_example("social-template")
        for beat in template["beat_sequence"]:
            if beat["beat_role"] == "payoff":
                beat["hook_category"] = "curiosity_gap"
        with self.assertRaisesRegex(ValidationError, "hook_category is only"):
            validate_record("social-template", template)

    def test_unknown_hook_category_fails(self):
        template = load_example("social-template")
        for beat in template["beat_sequence"]:
            if beat["beat_role"] == "hook":
                beat["hook_category"] = "clickbait"
        with self.assertRaisesRegex(ValidationError, "not in enum"):
            validate_record("social-template", template)

    def test_applied_beats_require_beat_role(self):
        applied = load_example("applied-social-template")
        del applied["applied_beats"][0]["beat_role"]
        with self.assertRaisesRegex(ValidationError, "beat_role"):
            validate_record("applied-social-template", applied)

    def test_applied_hook_category_on_non_hook_beat_fails(self):
        applied = load_example("applied-social-template")
        applied["applied_beats"][-1]["hook_category"] = "confession"
        with self.assertRaisesRegex(ValidationError, "hook_category is only"):
            validate_record("applied-social-template", applied)

    def test_applied_template_may_drop_cta_and_packaging(self):
        # Dropping cta/packaging stays legitimate: the learning loop records
        # an absent CTA as a `not_used` stage finding instead.
        applied = load_example("applied-social-template")
        applied["applied_beats"] = [
            beat
            for beat in applied["applied_beats"]
            if beat["beat_role"] in {"hook", "retain", "payoff"}
        ]
        validate_record("applied-social-template", applied)

    def test_applied_template_dropping_hook_or_payoff_fails(self):
        # Slice 2 review finding: hook/payoff stage findings must always
        # have an applied beat to attribute to, so applications may never
        # drop them.
        for dropped in ("hook", "payoff"):
            applied = load_example("applied-social-template")
            applied["applied_beats"] = [
                beat
                for beat in applied["applied_beats"]
                if beat["beat_role"] != dropped
            ]
            with self.assertRaisesRegex(ValidationError, "skip required spine role"):
                validate_record("applied-social-template", applied)


class SeededTemplateLibraryTests(unittest.TestCase):
    def test_seeded_preset_set_is_exactly_the_approved_five(self):
        on_disk = {path.stem for path in SEEDED_TEMPLATE_DIR.glob("*.json")}
        self.assertEqual(on_disk, SEEDED_TEMPLATE_IDS)

    def test_every_seeded_template_validates(self):
        for path in sorted(SEEDED_TEMPLATE_DIR.glob("*.json")):
            template = json.loads(path.read_text())
            self.assertEqual(
                template["social_template_id"],
                path.stem,
                f"{path.name}: filename must equal social_template_id",
            )
            validate_record("social-template", template)

    def test_every_seeded_template_hook_carries_a_category(self):
        for path in sorted(SEEDED_TEMPLATE_DIR.glob("*.json")):
            template = json.loads(path.read_text())
            hook_beats = [
                beat
                for beat in template["beat_sequence"]
                if beat["beat_role"] == "hook"
            ]
            for beat in hook_beats:
                self.assertIn(
                    "hook_category",
                    beat,
                    f"{path.name}: seeded preset hook beats carry a typed hook_category",
                )


class IntentCarryForwardTests(unittest.TestCase):
    def load_entry_and_promotion(self, workspace_dir):
        """Return the concept and approval pair (intent now carries
        forward concept -> approval)."""
        entry_path = (
            workspace_dir / "campaigns" / "campaign_luna_fit_001"
            / "concepts" / "campaign_concept_luna_fit_001.json"
        )
        promotion_path = (
            workspace_dir / "campaigns" / "campaign_luna_fit_001"
            / "approvals" / "concept_approval_luna_fit_001.json"
        )
        return (
            entry_path,
            json.loads(entry_path.read_text()),
            promotion_path,
            json.loads(promotion_path.read_text()),
        )

    def test_matching_intent_passes_the_gate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            _, _, _, promotion = self.load_entry_and_promotion(workspace_dir)
            validate_approval_gate(workspace_dir, promotion)

    def test_promotion_rewriting_intent_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            _, _, promotion_path, promotion = self.load_entry_and_promotion(workspace_dir)
            promotion["intended_emotion"] = "smug and superior"
            write_json(promotion_path, promotion)
            with self.assertRaisesRegex(ValidationError, "rewrites intended_emotion"):
                validate_approval_gate(workspace_dir, promotion)

    def test_promotion_dropping_intent_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            _, _, promotion_path, promotion = self.load_entry_and_promotion(workspace_dir)
            del promotion["core_message"]
            write_json(promotion_path, promotion)
            with self.assertRaisesRegex(ValidationError, "drops core_message"):
                validate_approval_gate(workspace_dir, promotion)

    def test_promotion_inventing_intent_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            entry_path, entry, _, promotion = self.load_entry_and_promotion(workspace_dir)
            del entry["intended_emotion"]
            write_json(entry_path, entry)
            with self.assertRaisesRegex(
                ValidationError, "never invented downstream"
            ):
                validate_approval_gate(workspace_dir, promotion)

    def test_legacy_records_without_intent_still_pass(self):
        # Schema-optional: pre-ADR-0024 fixtures carry no intent pair and the
        # gate imposes none.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            entry_path, entry, promotion_path, promotion = self.load_entry_and_promotion(
                workspace_dir
            )
            for field in ("intended_emotion", "core_message"):
                entry.pop(field, None)
                promotion.pop(field, None)
            write_json(entry_path, entry)
            write_json(promotion_path, promotion)
            validate_approval_gate(workspace_dir, promotion)


class SpineShapedMicroJourneyTests(unittest.TestCase):
    def test_example_is_spine_shaped(self):
        plan = load_example("micro-journey-video-plan")
        for field in ("hook", "retain", "payoff", "cta_or_loop", "intended_emotion"):
            self.assertIn(field, plan)
        self.assertEqual(sorted(plan["retain"]), ["escalation", "setup"])
        validate_record("micro-journey-video-plan", plan)

    def test_legacy_shape_fails(self):
        plan = load_example("micro-journey-video-plan")
        plan["opening_hook"] = plan.pop("hook")
        retain = plan.pop("retain")
        plan["setup"] = retain["setup"]
        plan["escalation"] = retain["escalation"]
        plan["loop_or_ending"] = plan.pop("cta_or_loop")
        plan["intended_viewer_feeling"] = plan.pop("intended_emotion")
        # Clean break (Decision D): the legacy field names fail both ways —
        # the spine fields are missing and the old keys are unexpected.
        with self.assertRaises(ValidationError):
            validate_record("micro-journey-video-plan", plan)


class IntentResolveByReferenceTests(unittest.TestCase):
    def test_plan_matching_promotion_intent_passes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            validate_project(project_dir)

    def test_plan_overriding_promotion_intent_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            rewrite_json(
                project_dir / "plan" / "production-plan.json",
                lambda plan: plan.update(intended_emotion="triumphant awe"),
            )
            with self.assertRaisesRegex(ValueError, "overrides the locked approval"):
                validate_project(project_dir)

    def test_premature_plan_on_created_project_still_checked(self):
        # Slice 2 review finding: plan records validate whenever they exist,
        # not only once the project reaches planning status.
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            rewrite_json(
                project_dir / "project.json",
                lambda project: project.update(status="created"),
            )
            rewrite_json(
                project_dir / "plan" / "production-plan.json",
                lambda plan: plan.update(intended_emotion="triumphant awe"),
            )
            with self.assertRaisesRegex(ValueError, "overrides the locked approval"):
                validate_project(project_dir)

    def test_plan_alone_carrying_intent_is_legacy_compatible(self):
        # A promotion that predates intent capture imposes nothing on the
        # plan's own intended_emotion.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, project_dir = scaffold_project_workspace(temp_dir)
            for record_path in (
                workspace_dir / "campaigns" / "campaign_luna_fit_001"
                / "approvals" / "concept_approval_luna_fit_001.json",
                workspace_dir / "campaigns" / "campaign_luna_fit_001"
                / "concepts" / "campaign_concept_luna_fit_001.json",
                workspace_dir / "research" / "content-opportunity-queue"
                / "entries" / "content_opportunity_luna_fit_001.json",
            ):
                rewrite_json(
                    record_path,
                    lambda record: [
                        record.pop(field, None)
                        for field in ("intended_emotion", "core_message")
                    ],
                )
            validate_project(project_dir)

    def test_workspace_path_enforces_intent_carry_forward(self):
        # Slice 1 review finding: the carry-forward probe must be reachable
        # from `validate workspace`, not only `validate research`.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_project_workspace(temp_dir)
            validate_creator_workspace(workspace_dir)
            rewrite_json(
                workspace_dir
                / "campaigns" / "campaign_luna_fit_001" / "approvals"
                / "concept_approval_luna_fit_001.json",
                lambda promotion: promotion.update(intended_emotion="smug"),
            )
            with self.assertRaisesRegex(ValidationError, "rewrites intended_emotion"):
                validate_creator_workspace(workspace_dir)


class SummarySpineAlignmentTests(unittest.TestCase):
    def test_unplanned_cta_summary_defaults_pass(self):
        # The example applied template plans no cta beat and the example
        # summary records the stage as not_used.
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_summarized_project(temp_dir)
            validate_project(project_dir)

    def test_unplanned_cta_with_judged_result_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_summarized_project(temp_dir)

            def mutate(summary):
                for finding in summary["stage_findings"]:
                    if finding["stage"] == "cta":
                        finding["result"] = "Weak conversion."
            write_summary(project_dir, mutate=mutate)
            with self.assertRaisesRegex(ValidationError, "not_used"):
                validate_project(project_dir)

    def test_planned_cta_beat_allows_judged_result(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, project_dir = scaffold_published_project(temp_dir)
            rewrite_json(
                project_dir / "plan" / "applied-template.json",
                lambda applied: applied["applied_beats"].append(
                    {
                        "beat_label": "cta",
                        "idea_application": "Luna asks viewers to save the reset for their next meeting.",
                        "viewer_question_answered": "What should I do with this?",
                        "beat_role": "cta",
                    }
                ),
            )
            ingest_example_snapshot(temp_dir, project_dir)

            def mutate(summary):
                for finding in summary["stage_findings"]:
                    if finding["stage"] == "cta":
                        finding["result"] = "Saves were strong after the explicit ask."
                        finding["interpretation"] = "The planned save CTA converted."
            write_summary(project_dir, mutate=mutate)
            validate_project(project_dir)


class PlatformModalityTests(unittest.TestCase):
    def test_primary_surfaces_outside_platform_enum_fail(self):
        profile = load_example("creator-profile")
        profile["content_strategy"]["primary_surfaces"] = ["YouTube Shorts"]
        with self.assertRaisesRegex(ValidationError, "not in enum"):
            validate_record("creator-profile", profile)

    def test_content_mediums_outside_modality_enum_fail(self):
        profile = load_example("creator-profile")
        profile["content_strategy"]["content_mediums"] = ["video", "carousel"]
        with self.assertRaisesRegex(ValidationError, "not in enum"):
            validate_record("creator-profile", profile)

    def test_audio_medium_yields_workspace_warning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_project_workspace(temp_dir)
            rewrite_json(
                workspace_dir / "creator-profile.json",
                lambda profile: profile["content_strategy"].update(
                    content_mediums=["video", "audio"]
                ),
            )
            rewrite_json(
                workspace_dir / "references" / "reference-library.json",
                lambda library: library["assets"].append(
                    {
                        "asset_id": "asset_luna_voice_sample",
                        "asset_type": "voice",
                        "asset_status": "planned",
                        "role": "Narration voice reference for audio work.",
                        "path": "references/voice/luna-voice-sample.md",
                        "source": {
                            "source_type": "user_provided",
                            "source_ref": "sources/intakes/luna-fit-breakdown.md",
                        },
                        "created_on": "2026-07-06",
                        "usage_notes": "Planned voice sample; not yet recorded.",
                        "semantic_index_allowed": False,
                    }
                ),
            )
            result = validate_creator_workspace(workspace_dir)
            self.assertTrue(
                any("audio" in warning for warning in result["warnings"]),
                f"expected a standalone-audio warning, got {result['warnings']}",
            )


class FormatSubtypeTests(unittest.TestCase):
    SEEDS = {
        "article-plan": ("essay", ["reported_feature", "newsletter_dispatch"]),
        "carousel-plan": ("designed_slides", ["photo_set"]),
        "thread-plan": ("chain", ["single_post"]),
    }

    def test_valid_subtypes_accepted_and_optional(self):
        for schema_name, (subtype, _) in self.SEEDS.items():
            plan = load_example(schema_name)
            validate_record(schema_name, plan)  # optional: absent is fine
            plan["format_subtype"] = subtype
            validate_record(schema_name, plan)

    def test_unknown_subtype_fails(self):
        for schema_name in self.SEEDS:
            plan = load_example(schema_name)
            plan["format_subtype"] = "long_form_video"
            with self.assertRaisesRegex(ValidationError, "not in enum"):
                validate_record(schema_name, plan)


class PlatformFitWarningTests(unittest.TestCase):
    def read_warnings(self, workspace_dir):
        path = workspace_dir / "system" / "project-warnings.jsonl"
        if not path.exists():
            return []
        return [
            json.loads(line)
            for line in path.read_text().splitlines()
            if line.strip()
        ]

    def test_native_fit_emits_no_warning(self):
        # Luna: instagram + tiktok surfaces, short_form_video project.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_project_workspace(temp_dir)
            fits = [
                record
                for record in self.read_warnings(workspace_dir)
                if record["warning_type"] == "platform_fit"
            ]
            self.assertEqual(fits, [])

    def test_off_surface_format_warns_and_never_blocks(self):
        # An article project for an instagram/tiktok creator: best fit is
        # `none`; the project is still created and the workspace still
        # validates.
        from influencer_os.projects import init_project

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_project_workspace(temp_dir)
            rewrite_json(
                workspace_dir
                / "campaigns" / "campaign_luna_fit_001" / "approvals"
                / "concept_approval_luna_fit_001.json",
                lambda promotion: promotion.update(
                    approved_formats=["format_short_form_video", "format_article"],
                    project_ids_created=promotion["project_ids_created"]
                    + ["project_luna_article_001"],
                ),
            )
            manifest_path = Path(temp_dir) / "article-project.json"
            project = load_example("project")
            project.update(
                project_id="project_luna_article_001",
                project_slug="tiny-reset-article",
                content_unit_type="article",
                target_formats=["format_article"],
                platform_targets=["instagram"],
            )
            project["project_paths"]["root"] = "projects/tiny-reset-article/"
            write_json(manifest_path, project)
            project_dir = init_project(manifest_path, creator_workspace=workspace_dir)
            self.assertTrue((project_dir / "project.json").exists())

            fits = [
                record
                for record in self.read_warnings(workspace_dir)
                if record["warning_type"] == "platform_fit"
            ]
            self.assertEqual(len(fits), 1)
            self.assertEqual(fits[0]["fit_level"], "none")
            self.assertEqual(fits[0]["project_id"], "project_luna_article_001")
            validate_record("project-warning", fits[0])
            # Exit criterion 5's strongest at-rest surface: the appended
            # warning passes pairing, target-ref, and creator-scope checks
            # inside the research validators (slice 3 review finding).
            validate_research(workspace_dir)

    def test_platform_fit_warning_is_idempotent_per_project(self):
        from influencer_os.projects import _emit_platform_fit_warning

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, project_dir = scaffold_project_workspace(temp_dir)
            project = json.loads((project_dir / "project.json").read_text())
            promotion = json.loads(
                (
                    workspace_dir
                    / "campaigns" / "campaign_luna_fit_001" / "approvals"
                    / "concept_approval_luna_fit_001.json"
                ).read_text()
            )
            concept = json.loads(
                (
                    workspace_dir
                    / "campaigns" / "campaign_luna_fit_001" / "concepts"
                    / "campaign_concept_luna_fit_001.json"
                ).read_text()
            )
            # Force a non-native fit so the writer has something to append.
            rewrite_json(
                workspace_dir / "creator-profile.json",
                lambda profile: profile["content_strategy"].update(
                    primary_surfaces=["medium"]
                ),
            )
            _emit_platform_fit_warning(workspace_dir, project, promotion, concept)
            _emit_platform_fit_warning(workspace_dir, project, promotion, concept)
            fits = [
                record
                for record in self.read_warnings(workspace_dir)
                if record["warning_type"] == "platform_fit"
            ]
            self.assertEqual(len(fits), 1)

    def test_fit_level_requires_platform_fit_type(self):
        warning = load_example("project-warning")
        warning["fit_level"] = "analog"
        with self.assertRaisesRegex(ValidationError, "only allowed on"):
            validate_record("project-warning", warning)

    def test_platform_fit_warning_requires_fit_level(self):
        warning = load_example("project-warning")
        warning["warning_type"] = "platform_fit"
        warning.pop("fit_level", None)
        with self.assertRaisesRegex(ValidationError, "must[\\s\\S]*carry fit_level"):
            validate_record("project-warning", warning)


class ReviewRecordTests(unittest.TestCase):
    def write_review(self, project_dir, mutate=None):
        review = load_example("review-record")
        if mutate is not None:
            mutate(review)
        reviews_dir = project_dir / "reviews"
        reviews_dir.mkdir(exist_ok=True)
        path = reviews_dir / f"{review['review_record_id']}.json"
        write_json(path, review)
        return path, review

    def test_example_validates(self):
        validate_record("review-record", load_example("review-record"))

    def test_fallback_requires_reason_and_bounded_forbids_it(self):
        review = load_example("review-record")
        del review["reviewer_execution"]["fallback_reason"]
        with self.assertRaisesRegex(ValidationError, "requires[\\s\\S]*fallback_reason"):
            validate_record("review-record", review)
        review["reviewer_execution"]["execution_mode"] = "bounded_sub_agent"
        review["reviewer_execution"]["fallback_reason"] = "unneeded"
        with self.assertRaisesRegex(ValidationError, "only allowed on"):
            validate_record("review-record", review)

    def test_waiver_requires_blocking_finding(self):
        review = load_example("review-record")
        review["human_waiver"] = {
            "waived_by": "user",
            "waived_on": "2026-07-06",
            "reason": "Verified the claim against the brand's published spec sheet.",
        }
        with self.assertRaisesRegex(ValidationError, "blocking-severity finding"):
            validate_record("review-record", review)
        review["findings"][0]["severity"] = "blocking"
        validate_record("review-record", review)

    def test_valid_review_record_passes_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            self.write_review(project_dir)
            validate_project(project_dir)

    def test_block_status_is_advisory_and_halts_nothing(self):
        # The exit-criterion 6 probe: a block-status creative ReviewRecord
        # does not stop validate project (nor, therefore, packaging — the
        # packaging preflight is validate_project).
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)

            def mutate(review):
                review["approval_status"] = "block"
                review["findings"][0]["severity"] = "blocking"
            self.write_review(project_dir, mutate=mutate)
            result = validate_project(project_dir)
            advisory = [w for w in result["warnings"] if "advisory only" in w]
            self.assertEqual(len(advisory), 1)

    def test_unbuilt_review_role_fails_closed(self):
        # Slice 4 review finding: the schema enum carries the decided
        # vocabulary, but a record may not claim an unbuilt review ran.
        for role in ("creator_fit", "fact_check"):
            review = load_example("review-record")
            review["review_role"] = role
            with self.assertRaisesRegex(ValidationError, "approved but unbuilt"):
                validate_record("review-record", review)

    def test_setup_and_strategy_roles_validate(self):
        for role, packet, area in (
            ("setup", SETUP_REVIEW_PACKET, "foundation"),
            ("strategy", STRATEGY_REVIEW_PACKET, "strategy"),
        ):
            review = load_example("review-record")
            review.pop("project_id")
            review.pop("concept_approval_id", None)
            review["review_role"] = role
            review["artifact_refs"] = packet
            review["findings"] = [review["findings"][0]]
            review["findings"][0]["area"] = area
            review["reviewer_execution"]["source_skill"] = {
                "setup": "review-creator-setup",
                "strategy": "review-strategy",
            }[role]
            if role == "strategy":
                review["research_demand_loop"] = {
                    "extra_research_round": 0,
                    "prior_review_record_id": None,
                }
            validate_record("review-record", review)

    def test_ladder_reviews_require_complete_role_specific_packets(self):
        for role, packet, area in (
            ("setup", SETUP_REVIEW_PACKET, "foundation"),
            ("strategy", STRATEGY_REVIEW_PACKET, "strategy"),
        ):
            for missing_ref in packet:
                with self.subTest(role=role, missing_ref=missing_ref):
                    review = load_example("review-record")
                    review.pop("project_id")
                    review.pop("concept_approval_id", None)
                    review["review_role"] = role
                    review["artifact_refs"] = [ref for ref in packet if ref != missing_ref]
                    review["findings"] = [review["findings"][0]]
                    review["findings"][0]["area"] = area
                    review["reviewer_execution"]["source_skill"] = {
                        "setup": "review-creator-setup",
                        "strategy": "review-strategy",
                    }[role]
                    if role == "strategy":
                        review["research_demand_loop"] = {
                            "extra_research_round": 0,
                            "prior_review_record_id": None,
                        }
                    with self.assertRaises(ValidationError):
                        validate_record("review-record", review)

    def test_review_role_requires_its_exact_reviewer_skill(self):
        for role, packet, area, forged_skill in (
            ("setup", SETUP_REVIEW_PACKET, "foundation", "review-hook-payoff"),
            ("strategy", STRATEGY_REVIEW_PACKET, "strategy", "review-creator-setup"),
        ):
            with self.subTest(role=role):
                review = load_example("review-record")
                review.pop("project_id")
                review.pop("concept_approval_id", None)
                review["review_role"] = role
                review["artifact_refs"] = packet
                review["findings"] = [review["findings"][0]]
                review["findings"][0]["area"] = area
                review["reviewer_execution"]["source_skill"] = forged_skill
                if role == "strategy":
                    review["research_demand_loop"] = {
                        "extra_research_round": 0,
                        "prior_review_record_id": None,
                    }
                with self.assertRaisesRegex(ValidationError, "source_skill"):
                    validate_record("review-record", review)

    def test_concept_review_file_rejects_arbitrary_fixture_packet(self):
        # Path-shaped strings are not provenance. At-rest validation must
        # resolve the schedule, queue candidates, Findings, and Evidence in
        # the owning workspace.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "creator"
            review_path = workspace / "reviews" / "review_luna_concept_001.json"
            review = load_example("review-record")
            review.pop("project_id")
            review.pop("concept_approval_id", None)
            review["review_record_id"] = review_path.stem
            review["review_role"] = "concept"
            review["artifact_refs"] = CONCEPT_REVIEW_PACKET
            review["findings"] = [review["findings"][0]]
            review["findings"][0]["area"] = "strategy"
            review["reviewer_execution"]["source_skill"] = (
                "review-concept-promotion"
            )
            write_json(review_path, review)

            with self.assertRaisesRegex(
                ValidationError, "artifact ref does not resolve|Workspace"
            ):
                validate_file("review-record", review_path)

    def test_concept_review_rejects_profile_only_packet(self):
        review = load_example("review-record")
        review.pop("project_id")
        review.pop("concept_approval_id", None)
        review["review_role"] = "concept"
        review["artifact_refs"] = ["creator-profile.json"]
        review["findings"] = [review["findings"][0]]
        review["findings"][0]["area"] = "strategy"
        review["reviewer_execution"]["source_skill"] = (
            "review-concept-promotion"
        )

        with self.assertRaises(ValidationError):
            validate_record("review-record", review)

    def test_concept_review_requires_each_packet_component(self):
        for missing_ref in (
            "content-schedule.json",
            "research/findings.md",
            "research/runs/research_run_luna_fit_2026_07_03_001/evidence.jsonl",
            "research/content-opportunity-queue/entries/content_opportunity_luna_fit_002.json",
        ):
            with self.subTest(missing_ref=missing_ref):
                review = load_example("review-record")
                review.pop("project_id")
                review.pop("concept_approval_id", None)
                review["review_role"] = "concept"
                review["artifact_refs"] = [
                    ref for ref in CONCEPT_REVIEW_PACKET if ref != missing_ref
                ]
                review["findings"] = [review["findings"][0]]
                review["findings"][0]["area"] = "evidence"
                review["reviewer_execution"]["source_skill"] = (
                    "review-concept-promotion"
                )

                with self.assertRaises(ValidationError):
                    validate_record("review-record", review)

    def test_concept_review_uses_only_bounded_area_vocabulary(self):
        for area in ("evidence", "strategy", "audience", "general"):
            with self.subTest(area=area):
                review = load_example("review-record")
                review.pop("project_id")
                review.pop("concept_approval_id", None)
                review["review_role"] = "concept"
                review["artifact_refs"] = CONCEPT_REVIEW_PACKET
                review["findings"] = [review["findings"][0]]
                review["findings"][0]["area"] = area
                review["reviewer_execution"]["source_skill"] = (
                    "review-concept-promotion"
                )
                validate_record("review-record", review)

        for area in (
            "foundation",
            "positioning",
            "schedule",
            "visual_identity",
            "hook",
        ):
            with self.subTest(area=area):
                review = load_example("review-record")
                review.pop("project_id")
                review.pop("concept_approval_id", None)
                review["review_role"] = "concept"
                review["artifact_refs"] = CONCEPT_REVIEW_PACKET
                review["findings"] = [review["findings"][0]]
                review["findings"][0]["area"] = area
                review["reviewer_execution"]["source_skill"] = (
                    "review-concept-promotion"
                )

                with self.assertRaisesRegex(
                    ValidationError, "outside its allowed vocabulary"
                ):
                    validate_record("review-record", review)

    def test_quarterly_role_validates(self):
        review = load_example("review-record")
        review.pop("project_id")
        review.pop("concept_approval_id", None)
        review["review_role"] = "quarterly"
        review["artifact_refs"] = QUARTERLY_REVIEW_PACKET
        review["findings"] = [review["findings"][0]]
        review["findings"][0]["area"] = "strategy"
        review["reviewer_execution"]["source_skill"] = "review-quarter-plan"
        review["research_demand_loop"] = {
            "extra_research_round": 0,
            "prior_review_record_id": None,
        }
        validate_record("review-record", review)

    def test_quarterly_review_requires_loop_lineage_and_complete_plan_packet(self):
        review = load_example("review-record")
        review.pop("project_id")
        review.pop("concept_approval_id", None)
        review["review_role"] = "quarterly"
        review["artifact_refs"] = QUARTERLY_REVIEW_PACKET
        review["findings"] = [review["findings"][0]]
        review["findings"][0]["area"] = "strategy"
        review["reviewer_execution"]["source_skill"] = "review-quarter-plan"

        with self.assertRaisesRegex(ValidationError, "research_demand_loop"):
            validate_record("review-record", review)

        review["research_demand_loop"] = {
            "extra_research_round": 0,
            "prior_review_record_id": None,
        }
        for missing_ref in QUARTERLY_REVIEW_PACKET:
            with self.subTest(missing_ref=missing_ref):
                review["artifact_refs"] = [
                    ref for ref in QUARTERLY_REVIEW_PACKET if ref != missing_ref
                ]
                with self.assertRaises(ValidationError):
                    validate_record("review-record", review)

    def test_project_scoped_role_requires_project_id(self):
        review = load_example("review-record")
        review.pop("project_id")
        with self.assertRaisesRegex(ValidationError, "project-scoped review.*requires project_id"):
            validate_record("review-record", review)

    def test_workspace_scoped_role_forbids_project_id(self):
        review = load_example("review-record")
        review["review_role"] = "setup"
        review.pop("concept_approval_id", None)
        review["artifact_refs"] = SETUP_REVIEW_PACKET
        review["findings"][0]["area"] = "foundation"
        review["reviewer_execution"]["source_skill"] = "review-creator-setup"
        with self.assertRaisesRegex(ValidationError, "workspace-scoped review.*must not carry project_id"):
            validate_record("review-record", review)

    def test_workspace_scoped_role_forbids_concept_approval_id(self):
        review = load_example("review-record")
        review.pop("project_id")
        review["review_role"] = "setup"
        review["artifact_refs"] = SETUP_REVIEW_PACKET
        review["findings"][0]["area"] = "foundation"
        review["reviewer_execution"]["source_skill"] = "review-creator-setup"
        with self.assertRaisesRegex(
            ValidationError, "workspace-scoped review.*must not carry concept_approval_id"
        ):
            validate_record("review-record", review)

    def test_workspace_area_vocab_enforced_by_scope(self):
        workspace_review = load_example("review-record")
        workspace_review.pop("project_id")
        workspace_review.pop("concept_approval_id", None)
        workspace_review["review_role"] = "setup"
        workspace_review["artifact_refs"] = SETUP_REVIEW_PACKET
        workspace_review["reviewer_execution"]["source_skill"] = "review-creator-setup"
        with self.assertRaisesRegex(ValidationError, "workspace.*area.*hook"):
            validate_record("review-record", workspace_review)

        project_review = load_example("review-record")
        project_review["findings"][0]["area"] = "strategy"
        with self.assertRaisesRegex(ValidationError, "project.*area.*strategy"):
            validate_record("review-record", project_review)

    def test_research_demand_marker_only_on_ladder_roles(self):
        project_review = load_example("review-record")
        project_review["findings"][0]["research_demand"] = True
        with self.assertRaisesRegex(ValidationError, "research_demand"):
            validate_record("review-record", project_review)

        workspace_review = load_example("review-record")
        workspace_review.pop("project_id")
        workspace_review.pop("concept_approval_id", None)
        workspace_review["review_role"] = "strategy"
        workspace_review["artifact_refs"] = STRATEGY_REVIEW_PACKET
        workspace_review["findings"] = [workspace_review["findings"][0]]
        workspace_review["findings"][0].update(area="evidence", research_demand="new")
        workspace_review["reviewer_execution"]["source_skill"] = "review-strategy"
        workspace_review["research_demand_loop"] = {
            "extra_research_round": 0,
            "prior_review_record_id": None,
        }
        validate_record("review-record", workspace_review)

        workspace_review["findings"][0]["research_demand"] = "carried_forward"
        validate_record("review-record", workspace_review)

        workspace_review["findings"][0]["research_demand"] = True
        with self.assertRaises(ValidationError):
            validate_record("review-record", workspace_review)

    def test_project_review_rejects_research_demand_by_field_presence(self):
        review = load_example("review-record")
        for value in (False, "new", "carried_forward"):
            with self.subTest(value=value):
                review["findings"][0]["research_demand"] = value
                with self.assertRaisesRegex(ValidationError, "research_demand"):
                    validate_record("review-record", review)

    def test_human_ladder_approvals_require_terminal_review_references(self):
        plan = load_example("visual-continuity-plan")
        plan["selection_review"].pop("terminal_review_record_id")
        with self.assertRaises(ValidationError):
            validate_record("visual-continuity-plan", plan)

        readiness = load_example("readiness-gates")
        readiness["milestones"]["production"].update(
            status="ready",
            approved_on="2026-07-12",
            approved_by="user",
            blockers=[],
        )
        with self.assertRaises(ValidationError):
            validate_record("readiness-gates", readiness)

    def test_unwaived_blocking_finding_warns_regardless_of_status(self):
        # Slice 4 review finding: the must-acknowledge advisory keys on the
        # finding severity, not only on a block approval_status.
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)

            def mutate(review):
                review["approval_status"] = "revise"
                review["findings"][0]["severity"] = "blocking"
            self.write_review(project_dir, mutate=mutate)
            result = validate_project(project_dir)
            advisory = [
                w for w in result["warnings"] if "blocking-severity finding" in w
            ]
            self.assertEqual(len(advisory), 1)

    def test_block_review_does_not_stop_packaging(self):
        # End-to-end exit-criterion 6 probe (slice 4 review finding): a
        # well-formed block-status review present at packaging time does not
        # stop register_output_package.
        from influencer_os.projects import register_output_package
        from tests.support import (
            seed_generation_fixtures,
            write_upload_ready_assets,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            seed_generation_fixtures(project_dir)

            def mutate(review):
                review["approval_status"] = "block"
                review["findings"][0]["severity"] = "blocking"
            self.write_review(project_dir, mutate=mutate)

            package_path = Path(temp_dir) / "output-package.json"
            copy_example_record("output-package.example.json", package_path)
            package = json.loads(package_path.read_text())
            asset_root = Path(temp_dir) / "source-assets"
            write_upload_ready_assets(asset_root, package)
            register_output_package(project_dir, package_path, asset_root=asset_root)
            self.assertTrue(
                (project_dir / "output-package" / "output-package.json").exists()
            )

    def test_dangling_artifact_ref_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            self.write_review(
                project_dir,
                mutate=lambda review: review.update(
                    artifact_refs=["plan/missing-plan.json"]
                ),
            )
            with self.assertRaisesRegex(FileNotFoundError, "does not resolve"):
                validate_project(project_dir)

    def test_escaping_artifact_ref_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            self.write_review(
                project_dir,
                mutate=lambda review: review.update(
                    artifact_refs=["../../creator-profile.json"]
                ),
            )
            with self.assertRaisesRegex(ValueError, "relative paths inside"):
                validate_project(project_dir)

    def test_filename_must_match_review_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            path, review = self.write_review(project_dir)
            path.rename(path.with_name("review_wrong_name.json"))
            with self.assertRaisesRegex(ValidationError, "filename does not match"):
                validate_project(project_dir)

    def test_wrong_promotion_ref_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            self.write_review(
                project_dir,
                mutate=lambda review: review.update(
                    concept_approval_id="concept_approval_luna_fit_999"
                ),
            )
            with self.assertRaisesRegex(ValueError, "locked approval"):
                validate_project(project_dir)


class WorkspaceReviewRecordTests(unittest.TestCase):
    def _materialize_setup_packet(self, workspace_dir):
        for relative_path in SETUP_REVIEW_PACKET:
            path = workspace_dir / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text("review packet fixture\n")

        board_path = workspace_dir / "references" / "brand" / "personal-brand-board.json"
        board_path.parent.mkdir(parents=True, exist_ok=True)
        board_path.write_text(
            json.dumps({"avatar_asset_id": "asset_luna_identity_plate"}) + "\n"
        )

    def write_workspace_review(self, workspace_dir, mutate=None):
        self._materialize_setup_packet(workspace_dir)
        review = load_example("review-record")
        review.pop("project_id")
        review.pop("concept_approval_id", None)
        review["review_role"] = "setup"
        review["artifact_refs"] = SETUP_REVIEW_PACKET
        review["findings"] = [review["findings"][0]]
        review["findings"][0]["area"] = "foundation"
        review["reviewer_execution"]["source_skill"] = "review-creator-setup"
        if mutate is not None:
            mutate(review)
        reviews_dir = workspace_dir / "reviews"
        reviews_dir.mkdir(exist_ok=True)
        path = reviews_dir / f"{review['review_record_id']}.json"
        write_json(path, review)
        return path, review

    def test_workspace_review_validates_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_project_workspace(temp_dir)
            self.write_workspace_review(workspace_dir)
            result = validate_creator_workspace(workspace_dir)
            self.assertEqual(result["warnings"], [])

    def test_workspace_block_review_halts_nothing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_project_workspace(temp_dir)
            self.write_workspace_review(
                workspace_dir,
                mutate=lambda review: (
                    review.update(approval_status="block"),
                    review["findings"][0].update(severity="blocking"),
                ),
            )
            result = validate_creator_workspace(workspace_dir)
            advisory = [warning for warning in result["warnings"] if "advisory only" in warning]
            self.assertEqual(len(advisory), 1)

    def test_workspace_scoped_role_rejected_under_project_reviews(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, project_dir = scaffold_project_workspace(temp_dir)
            review = load_example("review-record")
            review.pop("project_id")
            review.pop("concept_approval_id", None)
            review["review_role"] = "setup"
            review["artifact_refs"] = SETUP_REVIEW_PACKET
            review["findings"] = [review["findings"][0]]
            review["findings"][0]["area"] = "foundation"
            review["reviewer_execution"]["source_skill"] = "review-creator-setup"
            write_json(project_dir / "reviews" / f"{review['review_record_id']}.json", review)
            with self.assertRaisesRegex(ValidationError, "workspace-scoped review.*does not belong"):
                validate_project(project_dir)

    def test_project_scoped_role_rejected_under_workspace_reviews(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_project_workspace(temp_dir)
            review = load_example("review-record")
            review["artifact_refs"] = ["creator-profile.json"]
            reviews_dir = workspace_dir / "reviews"
            reviews_dir.mkdir(exist_ok=True)
            write_json(reviews_dir / f"{review['review_record_id']}.json", review)
            with self.assertRaisesRegex(ValidationError, "project-scoped review"):
                validate_creator_workspace(workspace_dir)

    def test_dangling_workspace_artifact_ref_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_project_workspace(temp_dir)
            self.write_workspace_review(
                workspace_dir,
                mutate=lambda review: review.update(
                    artifact_refs=[
                        *SETUP_REVIEW_PACKET,
                        "missing-artifact.md",
                    ]
                ),
            )
            with self.assertRaisesRegex(FileNotFoundError, "does not resolve"):
                validate_creator_workspace(workspace_dir)

    def test_reviews_directory_must_be_a_real_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_project_workspace(temp_dir)
            reviews_dir = workspace_dir / "reviews"
            for path in reviews_dir.iterdir():
                path.unlink()
            reviews_dir.rmdir()
            reviews_dir.write_text("not a directory\n")
            with self.assertRaisesRegex(ValidationError, "reviews.*directory"):
                validate_creator_workspace(workspace_dir)

    def test_reviews_directory_symlink_is_rejected_before_scanning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_project_workspace(temp_dir)
            external_reviews = Path(temp_dir) / "external-reviews"
            external_reviews.mkdir()
            reviews_dir = workspace_dir / "reviews"
            for path in reviews_dir.iterdir():
                path.unlink()
            reviews_dir.rmdir()
            reviews_dir.symlink_to(external_reviews, target_is_directory=True)
            with self.assertRaisesRegex(ValidationError, "reviews.*symlink"):
                validate_creator_workspace(workspace_dir)

    def test_workspace_review_file_symlink_is_rejected_before_reading(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_project_workspace(temp_dir)
            external_review = Path(temp_dir) / "external-review.json"
            review = load_example("review-record")
            external_review.write_text(json.dumps(review) + "\n")
            reviews_dir = workspace_dir / "reviews"
            reviews_dir.mkdir(exist_ok=True)
            (reviews_dir / "review_luna_hook_payoff_001.json").symlink_to(external_review)
            with self.assertRaisesRegex(ValidationError, "review file.*symlink"):
                validate_creator_workspace(workspace_dir)

    def test_terminal_review_reference_requires_the_matching_ladder_role(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_project_workspace(temp_dir)
            rewrite_json(
                workspace_dir / "references" / "visual-continuity-plan.json",
                lambda plan: plan["selection_review"].update(
                    terminal_review_record_id="review_luna_hook_payoff_001"
                ),
            )
            with self.assertRaisesRegex(ValidationError, "does not resolve"):
                validate_creator_workspace(workspace_dir)


class StrategyReviewLoopContractTests(unittest.TestCase):
    """ADR 0044's capped Strategy Review loop is validated at rest."""

    def write_strategy_review(
        self,
        workspace_dir,
        review_id,
        *,
        extra_research_round,
        prior_review_record_id=None,
        research_demand=None,
    ):
        findings_path = workspace_dir / "research" / "findings.md"
        findings_path.parent.mkdir(parents=True, exist_ok=True)
        findings_path.write_text(
            "---\n"
            "finding_ids:\n"
            "- finding_luna_fit_desk_reset_lunch\n"
            "---\n"
            "# Strategy Findings\n\nFixture evidence.\n"
        )
        review = load_example("review-record")
        review.pop("project_id")
        review.pop("concept_approval_id", None)
        review.update(
            review_record_id=review_id,
            review_role="strategy",
            artifact_refs=[
                *STRATEGY_REVIEW_PACKET,
                *(
                    [f"reviews/{prior_review_record_id}.json"]
                    if prior_review_record_id
                    else []
                ),
            ],
            findings=[
                {
                    "area": "evidence",
                    "severity": "low",
                    "note": "Confirm current platform guidance before approval.",
                    **(
                        {"research_demand": research_demand}
                        if research_demand
                        else {}
                    ),
                }
            ],
            research_demand_loop={
                "extra_research_round": extra_research_round,
                "prior_review_record_id": prior_review_record_id,
            },
        )
        review["reviewer_execution"]["source_skill"] = "review-strategy"
        path = workspace_dir / "reviews" / f"{review_id}.json"
        path.parent.mkdir(exist_ok=True)
        write_json(path, review)
        return review

    def mark_terminal(self, workspace_dir, review_id):
        rewrite_json(
            workspace_dir / "readiness-gates.json",
            lambda gates: gates["milestones"]["production"].update(
                status="ready",
                approved_on="2026-07-12",
                approved_by="user",
                blockers=[],
                terminal_review_record_id=review_id,
            ),
        )

    def test_strategy_review_requires_loop_lineage(self):
        review = load_example("review-record")
        review.pop("project_id")
        review.pop("concept_approval_id", None)
        review.update(
            review_role="strategy",
            artifact_refs=STRATEGY_REVIEW_PACKET,
            findings=[
                {
                    "area": "evidence",
                    "severity": "low",
                    "note": "Confirm current platform guidance before approval.",
                }
            ],
        )
        review["reviewer_execution"]["source_skill"] = "review-strategy"
        with self.assertRaisesRegex(ValidationError, "research_demand_loop"):
            validate_record("review-record", review)

    def test_production_terminal_must_close_the_loop_or_reach_the_cap(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_project_workspace(temp_dir)
            self.write_strategy_review(
                workspace_dir,
                "review_luna_strategy_001",
                extra_research_round=0,
                research_demand="new",
            )
            self.mark_terminal(workspace_dir, "review_luna_strategy_001")
            with self.assertRaisesRegex(ValidationError, "issues new Research Demands"):
                validate_creator_workspace(workspace_dir)

    def test_two_extra_round_cap_and_lineage_allow_production_terminal(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, _ = scaffold_project_workspace(temp_dir)
            self.write_strategy_review(
                workspace_dir,
                "review_luna_strategy_001",
                extra_research_round=0,
                research_demand="new",
            )
            self.write_strategy_review(
                workspace_dir,
                "review_luna_strategy_002",
                extra_research_round=1,
                prior_review_record_id="review_luna_strategy_001",
                research_demand="new",
            )
            self.write_strategy_review(
                workspace_dir,
                "review_luna_strategy_003",
                extra_research_round=2,
                prior_review_record_id="review_luna_strategy_002",
                research_demand="carried_forward",
            )
            rewrite_json(
                workspace_dir / "reviews" / "review_luna_strategy_003.json",
                lambda review: (
                    review.update(approval_status="block"),
                    review["findings"][0].update(severity="blocking"),
                ),
            )
            self.mark_terminal(workspace_dir, "review_luna_strategy_003")
            result = validate_creator_workspace(workspace_dir)
            self.assertTrue(
                any("advisory only" in warning for warning in result["warnings"]),
                result["warnings"],
            )

    def test_third_extra_round_is_rejected(self):
        review = load_example("review-record")
        review.pop("project_id")
        review.pop("concept_approval_id", None)
        review.update(
            review_role="strategy",
            artifact_refs=[*STRATEGY_REVIEW_PACKET, "reviews/review_luna_strategy_003.json"],
            findings=[
                {
                    "area": "evidence",
                    "severity": "low",
                    "note": "Still missing current evidence.",
                    "research_demand": "new",
                }
            ],
            research_demand_loop={
                "extra_research_round": 3,
                "prior_review_record_id": "review_luna_strategy_003",
            },
        )
        review["reviewer_execution"]["source_skill"] = "review-strategy"
        with self.assertRaisesRegex(ValidationError, "extra_research_round"):
            validate_record("review-record", review)


if __name__ == "__main__":
    unittest.main()
