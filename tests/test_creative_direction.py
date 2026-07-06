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
from influencer_os.research import validate_promotion_gate, validate_research
from influencer_os.validation import (
    ValidationError,
    validate_record,
)
from tests.test_cli import rewrite_json, scaffold_project_workspace
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
        entry_path = (
            workspace_dir / "research" / "idea-queue" / "entries" / f"{ENTRY_ID}.json"
        )
        promotion_path = (
            workspace_dir
            / "research"
            / "idea-promotions"
            / "idea_promotion_luna_fit_001.json"
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
            validate_promotion_gate(workspace_dir, promotion)

    def test_promotion_rewriting_intent_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            _, _, promotion_path, promotion = self.load_entry_and_promotion(workspace_dir)
            promotion["intended_emotion"] = "smug and superior"
            write_json(promotion_path, promotion)
            with self.assertRaisesRegex(ValidationError, "rewrites intended_emotion"):
                validate_promotion_gate(workspace_dir, promotion)

    def test_promotion_dropping_intent_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            _, _, promotion_path, promotion = self.load_entry_and_promotion(workspace_dir)
            del promotion["core_message"]
            write_json(promotion_path, promotion)
            with self.assertRaisesRegex(ValidationError, "drops core_message"):
                validate_promotion_gate(workspace_dir, promotion)

    def test_promotion_inventing_intent_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            entry_path, entry, _, promotion = self.load_entry_and_promotion(workspace_dir)
            del entry["intended_emotion"]
            write_json(entry_path, entry)
            with self.assertRaisesRegex(
                ValidationError, "never invented at promotion"
            ):
                validate_promotion_gate(workspace_dir, promotion)

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
            validate_promotion_gate(workspace_dir, promotion)


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
            with self.assertRaisesRegex(ValueError, "overrides the locked promotion"):
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
            with self.assertRaisesRegex(ValueError, "overrides the locked promotion"):
                validate_project(project_dir)

    def test_plan_alone_carrying_intent_is_legacy_compatible(self):
        # A promotion that predates intent capture imposes nothing on the
        # plan's own intended_emotion.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir, project_dir = scaffold_project_workspace(temp_dir)
            for record_name in ("idea-promotions/idea_promotion_luna_fit_001",
                                "idea-queue/entries/idea_queue_entry_luna_fit_001"):
                rewrite_json(
                    workspace_dir / "research" / f"{record_name}.json",
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
                / "research"
                / "idea-promotions"
                / "idea_promotion_luna_fit_001.json",
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
                / "research"
                / "idea-promotions"
                / "idea_promotion_luna_fit_001.json",
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
                    / "research"
                    / "idea-promotions"
                    / "idea_promotion_luna_fit_001.json"
                ).read_text()
            )
            # Force a non-native fit so the writer has something to append.
            rewrite_json(
                workspace_dir / "creator-profile.json",
                lambda profile: profile["content_strategy"].update(
                    primary_surfaces=["medium"]
                ),
            )
            _emit_platform_fit_warning(workspace_dir, project, promotion)
            _emit_platform_fit_warning(workspace_dir, project, promotion)
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


if __name__ == "__main__":
    unittest.main()
