import json
import tempfile
import unittest
from pathlib import Path

from influencer_os.brand_boards import validate_brand_board
from influencer_os.creator_workspaces import validate_creator_workspace


ROOT = Path(__file__).resolve().parents[1]


class VisualFoundationMigrationTests(unittest.TestCase):
    def test_migrates_legacy_avatar_and_visual_plan_idempotently(self):
        from influencer_os.migrations import migrate_visual_foundation
        from tests.test_readiness_validation import make_ready_workspace

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_ready_workspace(temp_dir, "foundation_ready")
            board_path = workspace_dir / "references" / "brand" / "personal-brand-board.json"
            board = json.loads(board_path.read_text())
            avatar_id = board.pop("avatar_asset_id")
            library = json.loads(
                (workspace_dir / "references" / "reference-library.json").read_text()
            )
            avatar = next(asset for asset in library["assets"] if asset["asset_id"] == avatar_id)
            board["avatar_image"] = avatar["path"]
            board_path.write_text(json.dumps(board, indent=2) + "\n")

            plan_path = workspace_dir / "references" / "visual-continuity-plan.json"
            plan = json.loads(plan_path.read_text())
            plan.pop("setup_reference_generation")
            plan_path.write_text(json.dumps(plan, indent=2) + "\n")

            first = migrate_visual_foundation(workspace_dir)
            second = migrate_visual_foundation(workspace_dir)

            self.assertIn(Path("references/brand/personal-brand-board.json"), first["changed_paths"])
            self.assertIn(Path("references/visual-continuity-plan.json"), first["changed_paths"])
            self.assertEqual(second["changed_paths"], [])
            migrated_plan = json.loads(plan_path.read_text())
            authorized_ids = migrated_plan["setup_reference_generation"]["asset_ids"]
            self.assertNotIn(avatar_id, authorized_ids)
            self.assertTrue(
                all(
                    next(
                        asset for asset in library["assets"]
                        if asset["asset_id"] == asset_id
                    )["asset_status"] in {"planned", "prompted"}
                    for asset_id in authorized_ids
                )
            )
            validate_brand_board(workspace_dir)
            validate_creator_workspace(workspace_dir)


if __name__ == "__main__":
    unittest.main()
