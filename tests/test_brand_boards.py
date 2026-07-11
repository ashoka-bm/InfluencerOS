import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from influencer_os.brand_boards import rebuild_brand_board, validate_brand_board
from influencer_os.creator_workspaces import init_creator
from influencer_os.validation import ValidationError


ROOT = Path(__file__).resolve().parents[1]


def write_json(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + "\n")


def make_brand_board_workspace(temp_dir):
    workspace_dir = init_creator(
        ROOT / "examples" / "creator-workspace.example.json",
        workspace_root=Path(temp_dir),
    )
    reference_library = json.loads(
        (ROOT / "examples" / "reference-library.example.json").read_text()
    )
    write_json(workspace_dir / "references" / "reference-library.json", reference_library)
    spec = {
        "board_type": "mini_style_guide",
        "approval_status": "approved",
        "name": "Luna <Fit>",
        "handle": "@lunafit",
        "tagline": "Movement small enough to start.",
        "descriptor": "Desk-worker movement guide",
        "summary": "Tiny resets for real workdays.",
        "audience": "Busy desk workers.",
        "promise": "Make movement feel available now.",
        "differentiator": "Constraint-first demonstrations.",
        "brand_adjectives": ["calm", "practical", "kind"],
        "anti_adjectives": ["punishing", "clinical", "luxury"],
        "hero_image": "references/character/luna-fit-identity-plate.png",
        "avatar_asset_id": "asset_luna_identity_plate",
        "palette": [
            {"name": "Warm Paper", "hex": "#F6F0E6", "role": "Base", "usage": "46%"},
            {"name": "Soft Sand", "hex": "#D8CDBD", "role": "Surface", "usage": "14%"},
            {"name": "Quiet Line", "hex": "#A7A094", "role": "Line", "usage": "8%"},
            {"name": "Reset Blue", "hex": "#587C8D", "role": "Primary", "usage": "12%"},
            {"name": "Pale Glass", "hex": "#DDE8E7", "role": "Support", "usage": "6%"},
            {"name": "Warm Amber", "hex": "#B8844C", "role": "Emphasis", "usage": "4%"},
            {"name": "Steady Moss", "hex": "#5D6B59", "role": "Secondary", "usage": "4%"},
            {"name": "Workday Ink", "hex": "#242424", "role": "Text", "usage": "6%"},
        ],
        "typography": {
            "display": {"name": "Georgia", "stack": "Georgia, serif", "sample": "Start smaller.", "spec": "64-88px / 0.95"},
            "subhead": {"name": "Avenir Next", "stack": "\"Avenir Next\", Arial, sans-serif", "sample": "BEFORE THE NEXT CALL", "spec": "14-18px / 700"},
            "body": {"name": "Avenir Next", "stack": "\"Avenir Next\", Arial, sans-serif", "sample": "A useful reset should fit the day you actually have.", "spec": "16-18px / 1.5"},
            "caption_data": {"name": "IBM Plex Mono", "stack": "\"IBM Plex Mono\", Menlo, monospace", "sample": "RESET 01 / 02:00", "spec": "11-13px / 700"},
        },
        "wordmark": {"primary": "Luna Fit", "handle_treatment": "@lunafit / tiny resets", "submark": "LF", "avatar_guidance": "Close face crop; no overlay text."},
        "production_spaces": [
            {"title": "Desk Corner", "purpose": "A recurring place for workday resets.", "best_for": ["desk reset videos", "chair demonstrations"], "continuity_notes": "Keep the desk, chair, and window direction stable.", "reference_asset_id": "asset_luna_living_room"},
            {"title": "Living Room Wall", "purpose": "A clear full-body demonstration space.", "best_for": ["standing mobility", "wall-supported modifications"], "continuity_notes": "Keep the wall clear and camera at waist height.", "reference_asset_id": "asset_luna_living_room_wall"},
        ],
        "signature_props": [
            {"title": "Reset Timer", "role": "A recurring object that makes the two-minute promise visible.", "best_for": ["timer close-ups", "routine openings"], "continuity_notes": "Use the same matte timer with no distracting brand marks.", "reference_asset_id": "asset_luna_reset_timer"},
        ],
        "imagery_rules": {"framing": ["Eye-level portrait"], "lighting": ["Soft daylight"], "use": ["One visual lead"], "avoid": ["Luxury wellness stock"]},
        "content_templates": [
            {"title": "Carousel Cover", "headline": "Two minutes counts.", "caption": "SAVE THIS RESET", "image": ""},
            {"title": "Reel Title", "headline": "Before the next call.", "caption": "DESK RESET", "image": ""},
            {"title": "Story Frame", "headline": "Choose one.", "caption": "LOW-PRESSURE MENU", "image": ""},
        ],
        "voice": {"headlines": ["Start smaller."], "caption_starters": ["Use the chair you already have."], "use_words": ["reset", "available"], "avoid_words": ["burn", "punish"], "sliders": [{"left": "intense", "right": "calm", "position": 82}]},
        "pillars": [
            {"name": "Desk Resets", "description": "One visible action."},
            {"name": "Habit Cues", "description": "Use an existing moment."},
            {"name": "Modifications", "description": "Make the action fit."},
            {"name": "Body Neutrality", "description": "Capability without shame."},
        ],
        "qa_notes": [
            {"title": "Accessibility", "body": "Use Workday Ink on Warm Paper for body copy."},
            {"title": "Production", "body": "One action and one hierarchy per frame."},
        ],
        "footer": ["Small enough to start", "Clear enough to repeat"],
    }
    image_path = workspace_dir / "references" / "character" / "luna-fit-identity-plate.png"
    image_path.write_bytes(b"fixture-image")
    avatar_asset_path = workspace_dir / "references" / "character" / "luna-identity-plate.png"
    avatar_asset_path.write_bytes(b"fixture-image")
    (workspace_dir / "references" / "locations" / "luna-living-room-master-location-sheet.png").write_bytes(b"fixture-location")
    (workspace_dir / "references" / "locations" / "luna-fit-living-room-wall.png").write_bytes(b"fixture-location")
    (workspace_dir / "references" / "objects" / "luna-fit-reset-timer.png").write_bytes(b"fixture-prop")
    write_json(workspace_dir / "references" / "brand" / "personal-brand-board.json", spec)
    return workspace_dir


class PersonalBrandBoardTests(unittest.TestCase):
    def test_rebuild_brand_board_populates_shared_template_with_exact_tokens(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_brand_board_workspace(temp_dir)

            result = rebuild_brand_board(workspace_dir)

            board_path = workspace_dir / "references" / "brand" / "personal-brand-board.html"
            rendered = board_path.read_text()
            self.assertEqual(result["board_path"], board_path)
            self.assertIn("Luna &lt;Fit&gt;", rendered)
            self.assertIn("#587C8D", rendered)
            self.assertIn("IBM Plex Mono", rendered)
            self.assertIn("Carousel Cover", rendered)
            self.assertIn("Production Spaces", rendered)
            self.assertIn("Desk Corner", rendered)
            self.assertIn("Signature Props", rendered)
            self.assertIn("Reset Timer", rendered)
            self.assertNotIn("Visual Territories", rendered)
            self.assertNotIn("Luna <Fit>", rendered)
            self.assertIn('name="influencer-os-brand-board-source-digest"', rendered)
            self.assertNotIn("__BRAND_BOARD_", rendered)

    def test_validate_brand_board_rejects_a_stale_projection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_brand_board_workspace(temp_dir)
            rebuild_brand_board(workspace_dir)
            validate_brand_board(workspace_dir)

            spec_path = workspace_dir / "references" / "brand" / "personal-brand-board.json"
            spec = json.loads(spec_path.read_text())
            spec["tagline"] = "A changed promise."
            write_json(spec_path, spec)

            with self.assertRaisesRegex(ValidationError, "stale.*rebuild-brand-board"):
                validate_brand_board(workspace_dir)

    def test_reference_library_change_makes_projection_stale(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_brand_board_workspace(temp_dir)
            rebuild_brand_board(workspace_dir)
            library_path = workspace_dir / "references" / "reference-library.json"
            library = json.loads(library_path.read_text())
            library["assets"][0]["usage_notes"] = "Changed continuity guidance."
            write_json(library_path, library)

            with self.assertRaisesRegex(ValidationError, "stale.*rebuild-brand-board"):
                validate_brand_board(workspace_dir)

    def test_prompt_ready_reference_renders_an_intentional_placeholder(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_brand_board_workspace(temp_dir)
            library_path = workspace_dir / "references" / "reference-library.json"
            library = json.loads(library_path.read_text())
            for asset in library["assets"]:
                if asset["asset_id"] == "asset_luna_living_room":
                    asset["asset_status"] = "planned"
            write_json(library_path, library)

            rebuild_brand_board(workspace_dir)
            rendered = (
                workspace_dir / "references" / "brand" / "personal-brand-board.html"
            ).read_text()
            self.assertIn('class="image-placeholder "', rendered)
            self.assertNotIn("luna-living-room-master-location-sheet.png", rendered)

    def test_prompt_ready_avatar_renders_an_intentional_placeholder(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_brand_board_workspace(temp_dir)
            library_path = workspace_dir / "references" / "reference-library.json"
            library = json.loads(library_path.read_text())
            for asset in library["assets"]:
                if asset["asset_id"] == "asset_luna_identity_plate":
                    asset["asset_status"] = "prompted"
                    asset["prompt_path"] = "references/character/luna-identity-plate.prompt.md"
            write_json(library_path, library)
            prompt = workspace_dir / "references" / "character" / "luna-identity-plate.prompt.md"
            prompt.write_text("Prompt-staged avatar.\n")

            rebuild_brand_board(workspace_dir)
            rendered = (
                workspace_dir / "references" / "brand" / "personal-brand-board.html"
            ).read_text()
            self.assertIn('class="image-placeholder avatar"', rendered)
            self.assertNotIn('alt="Avatar crop"', rendered)

    def test_brand_board_rejects_an_unprompted_avatar_asset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_brand_board_workspace(temp_dir)
            library_path = workspace_dir / "references" / "reference-library.json"
            library = json.loads(library_path.read_text())
            for asset in library["assets"]:
                if asset["asset_id"] == "asset_luna_identity_plate":
                    asset["asset_status"] = "planned"
            write_json(library_path, library)

            with self.assertRaisesRegex(ValidationError, "avatar asset.*prompted"):
                rebuild_brand_board(workspace_dir)

    def test_production_space_rejects_a_non_location_reference(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_brand_board_workspace(temp_dir)
            spec_path = workspace_dir / "references" / "brand" / "personal-brand-board.json"
            spec = json.loads(spec_path.read_text())
            spec["production_spaces"][0]["reference_asset_id"] = "asset_luna_identity_plate"
            write_json(spec_path, spec)

            with self.assertRaisesRegex(ValidationError, "expected location"):
                rebuild_brand_board(workspace_dir)

    def test_cli_rebuilds_and_validates_brand_board(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_brand_board_workspace(temp_dir)

            rebuild = subprocess.run(
                [sys.executable, "-m", "influencer_os", "rebuild-brand-board", str(workspace_dir)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            validate = subprocess.run(
                [sys.executable, "-m", "influencer_os", "validate", "brand-board", str(workspace_dir)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(rebuild.returncode, 0, rebuild.stderr)
            self.assertIn("Rebuilt personal brand board", rebuild.stdout)
            self.assertEqual(validate.returncode, 0, validate.stderr)
            self.assertIn("Validated personal brand board", validate.stdout)


if __name__ == "__main__":
    unittest.main()
