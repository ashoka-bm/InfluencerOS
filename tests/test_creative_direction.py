"""Creative Direction workstream checks (ADR 0024).

Slice 1: the Content Beat Spine is the one template vocabulary, and the
intent pair (intended_emotion / core_message) is captured at the idea origin
and survives promotion verbatim.
"""

import json
import tempfile
import unittest
from pathlib import Path

from influencer_os.research import validate_promotion_gate
from influencer_os.validation import (
    ValidationError,
    validate_record,
)
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
        # Coverage binds templates, not applications: the learning loop
        # records an absent CTA as a `not_used` stage finding instead.
        applied = load_example("applied-social-template")
        applied["applied_beats"] = [
            beat
            for beat in applied["applied_beats"]
            if beat["beat_role"] in {"hook", "retain", "payoff"}
        ]
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


if __name__ == "__main__":
    unittest.main()
