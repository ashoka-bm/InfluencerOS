import json
import tempfile
import unittest
from pathlib import Path

from influencer_os.creator_workspaces import init_creator, validate_creator_workspace
from influencer_os.validation import ValidationError


ROOT = Path(__file__).resolve().parents[1]

FOUNDATION_SAMPLE = {
    "context/SOUL.md": "Luna is a calm, encouraging home-fitness guide for desk workers.\n",
    "context/USER.md": "Luna serves office workers who want tiny daily movement resets.\n",
    "context/MEMORY.md": "- Setup accepted; research not started yet.\n",
    "brand_context/identity.md": "Luna lives in a warm apartment and teaches two-minute resets.\n",
    "brand_context/soul.md": "Luna believes rest is productive and never shames missed days.\n",
    "brand_context/personal-brand.md": "Short-form vertical video first; no crash-diet content ever.\n",
    "brand_context/voice-samples.md": "\"Two minutes. That is the whole workout. Ready?\"\n",
}


def rewrite_json(path, mutate):
    record = json.loads(path.read_text())
    mutate(record)
    path.write_text(json.dumps(record, indent=2) + "\n")


def init_workspace_with_status(temp_dir, status):
    manifest = json.loads((ROOT / "examples" / "creator-workspace.example.json").read_text())
    manifest["status"] = status
    manifest_path = Path(temp_dir) / "creator-workspace.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    workspace_dir = init_creator(manifest_path, workspace_root=Path(temp_dir) / "creators")
    (workspace_dir / "creator-profile.json").write_text(
        (ROOT / "examples" / "creator-profile.example.json").read_text()
    )
    (workspace_dir / "references" / "reference-library.json").write_text(
        (ROOT / "examples" / "reference-library.example.json").read_text()
    )
    (workspace_dir / "sources" / "intakes" / "luna-fit-breakdown.md").write_text(
        (ROOT / "examples" / "sources" / "luna-fit-breakdown.example.md").read_text()
    )
    return workspace_dir


def populate_foundation(workspace_dir):
    for relative_path, sample in FOUNDATION_SAMPLE.items():
        target = workspace_dir / relative_path
        target.write_text(target.read_text() + sample)


def place_asset_files(workspace_dir):
    library = json.loads((workspace_dir / "references" / "reference-library.json").read_text())
    for asset in library["assets"]:
        if asset["asset_status"] in {"user_provided", "generated", "approved"}:
            target = workspace_dir / asset["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"placeholder for {asset['asset_id']}\n")
        if asset.get("prompt_path"):
            prompt = workspace_dir / asset["prompt_path"]
            prompt.parent.mkdir(parents=True, exist_ok=True)
            prompt.write_text(f"prompt for {asset['asset_id']}\n")


def make_ready_workspace(temp_dir, status):
    workspace_dir = init_workspace_with_status(temp_dir, status)
    populate_foundation(workspace_dir)
    place_asset_files(workspace_dir)
    return workspace_dir


class DraftLenienceTests(unittest.TestCase):
    def test_draft_workspace_with_scaffold_foundation_validates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_workspace_with_status(temp_dir, "draft")

            result = validate_creator_workspace(workspace_dir)
            self.assertEqual(result["creator_slug"], "luna-fit")


class ContentReadyBlockerTests(unittest.TestCase):
    def test_populated_content_ready_workspace_validates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")

            result = validate_creator_workspace(workspace_dir)
            self.assertEqual(result["creator_slug"], "luna-fit")

    def test_scaffold_only_foundation_file_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")
            identity = workspace_dir / "brand_context" / "identity.md"
            identity.write_text("# Identity\n\n")

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("brand_context/identity.md", str(ctx.exception))

    def test_tbd_placeholder_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")
            soul = workspace_dir / "brand_context" / "soul.md"
            soul.write_text(soul.read_text() + "\nHumor rules: TBD\n")

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("TBD", str(ctx.exception))

    def test_oversized_context_file_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")
            soul = workspace_dir / "context" / "SOUL.md"
            soul.write_text(soul.read_text() + ("Luna keeps sessions tiny. " * 200))

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("context/SOUL.md", str(ctx.exception))
            self.assertIn("byte cap", str(ctx.exception))

    def test_missing_source_intake_provenance_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")
            rewrite_json(
                workspace_dir / "creator-workspace.json",
                lambda manifest: manifest.update(source_intakes=[]),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("source intake", str(ctx.exception))

    def test_missing_required_asset_kind_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")

            def drop_outfit_and_brand(library):
                library["assets"] = [
                    asset
                    for asset in library["assets"]
                    if asset["asset_type"] not in {"outfit", "brand"}
                ]

            rewrite_json(
                workspace_dir / "references" / "reference-library.json", drop_outfit_and_brand
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("outfit", str(ctx.exception))
            self.assertIn("brand", str(ctx.exception))

    def test_one_error_reports_every_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")
            (workspace_dir / "brand_context" / "identity.md").write_text("# Identity\n\n")
            soul = workspace_dir / "brand_context" / "soul.md"
            soul.write_text(soul.read_text() + "\nTriggers: TBD\n")

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("brand_context/identity.md", message)
            self.assertIn("brand_context/soul.md", message)


class AssetLifecycleExistenceTests(unittest.TestCase):
    def test_approved_asset_with_missing_path_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")
            (workspace_dir / "references" / "video-style" / "default-video-photo-style.md").unlink()

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("default-video-photo-style.md", str(ctx.exception))

    def test_prompted_asset_without_prompt_path_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")

            def strip_outfit_prompt(library):
                for asset in library["assets"]:
                    if asset["asset_type"] == "outfit":
                        asset.pop("prompt_path", None)

            rewrite_json(
                workspace_dir / "references" / "reference-library.json", strip_outfit_prompt
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("prompt_path", str(ctx.exception))

    def test_planned_asset_without_prompt_path_passes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")

            def plan_outfit(library):
                for asset in library["assets"]:
                    if asset["asset_type"] == "outfit":
                        asset["asset_status"] = "planned"
                        asset.pop("prompt_path", None)

            rewrite_json(workspace_dir / "references" / "reference-library.json", plan_outfit)

            result = validate_creator_workspace(workspace_dir)
            self.assertEqual(result["creator_slug"], "luna-fit")

    def test_retired_asset_with_dead_path_passes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")

            def add_retired(library):
                library["assets"].append(
                    {
                        "asset_id": "asset_luna_retired_poster",
                        "asset_type": "brand",
                        "asset_status": "retired",
                        "role": "Retired launch poster",
                        "path": "references/brand/retired-launch-poster.png",
                        "source": {"source_type": "generated", "source_ref": "old run"},
                        "created_on": "2026-06-01",
                        "usage_notes": "Do not use for new work.",
                        "semantic_index_allowed": False,
                    }
                )

            rewrite_json(workspace_dir / "references" / "reference-library.json", add_retired)

            result = validate_creator_workspace(workspace_dir)
            self.assertEqual(result["creator_slug"], "luna-fit")

    def test_symlinked_asset_path_escaping_the_workspace_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "content_ready")
            outside = Path(temp_dir) / "outside-style.md"
            outside.write_text("# Outside\n")
            style_path = workspace_dir / "references" / "video-style" / "default-video-photo-style.md"
            style_path.unlink()
            style_path.symlink_to(outside)

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("default-video-photo-style.md", str(ctx.exception))


class GenerationReadyTests(unittest.TestCase):
    def test_planned_required_kind_blocks_generation_ready(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "generation_ready")

            def plan_outfit(library):
                for asset in library["assets"]:
                    if asset["asset_type"] == "outfit":
                        asset["asset_status"] = "planned"
                        asset.pop("prompt_path", None)

            rewrite_json(workspace_dir / "references" / "reference-library.json", plan_outfit)

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("outfit", str(ctx.exception))

    def test_fully_prompted_generation_ready_workspace_validates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "generation_ready")

            result = validate_creator_workspace(workspace_dir)
            self.assertEqual(result["creator_slug"], "luna-fit")


class TextFirstCreatorTests(unittest.TestCase):
    def test_active_text_first_creator_validates_without_visual_assets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "active")
            rewrite_json(
                workspace_dir / "creator-profile.json",
                lambda profile: profile["content_strategy"].update(content_mediums=["text"]),
            )

            result = validate_creator_workspace(workspace_dir)
            self.assertEqual(result["creator_slug"], "luna-fit")


class ReferenceRefResolutionTests(unittest.TestCase):
    def test_dangling_primary_asset_id_fails_even_at_draft(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = init_workspace_with_status(temp_dir, "draft")
            rewrite_json(
                workspace_dir / "creator-profile.json",
                lambda profile: profile["reference_refs"]["primary_character_asset_ids"].append(
                    "asset_luna_missing_prop"
                ),
            )

            with self.assertRaises(ValidationError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("asset_luna_missing_prop", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
