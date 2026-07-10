import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from influencer_os.boards import (
    DEFAULT_BOARD_COLUMNS,
    rebuild_board,
    validate_board,
)
from influencer_os.validation import ValidationError

from test_recall_index import (
    PROJECT_ID,
    PROJECT_SLUG,
    scaffold_indexable_workspace,
)
from test_research_validation import ENTRY_ID, load_example, write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[1]

IDEA_CARD = f"card_{ENTRY_ID}"
PROJECT_CARD = f"card_{PROJECT_ID}"
PILLAR_CARD = "card_pillar_tiny_home_workouts"
CAMPAIGN_CARD = "card_campaign_luna_fit_001"
CONCEPT_CARD = "card_campaign_concept_luna_fit_001"
HIERARCHY_ORDER = [
    PILLAR_CARD, CAMPAIGN_CARD, CONCEPT_CARD, PROJECT_CARD, IDEA_CARD,
]


def load_board(workspace_dir):
    return json.loads((workspace_dir / "boards" / "content-board.json").read_text())


def board_cards_by_id(workspace_dir):
    return {card["content_card_id"]: card for card in load_board(workspace_dir)["cards"]}


class RebuildBoardTests(unittest.TestCase):
    def test_rebuild_derives_cards_from_canonical_records(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            (workspace_dir / "boards" / "content-board.json").unlink()

            result = rebuild_board(workspace_dir)
            self.assertEqual(result["opportunity_cards"], 1)
            self.assertEqual(result["project_cards"], 1)

            board = load_board(workspace_dir)
            self.assertEqual(board["content_board_id"], "content_board_luna_fit")
            self.assertEqual(board["columns"], list(DEFAULT_BOARD_COLUMNS))
            self.assertEqual(board["manual_order"], HIERARCHY_ORDER)

            cards = {card["content_card_id"]: card for card in board["cards"]}
            pillar = cards[PILLAR_CARD]
            self.assertEqual(pillar["card_type"], "pillar")
            self.assertEqual(pillar["child_card_ids"], [CAMPAIGN_CARD])
            campaign = cards[CAMPAIGN_CARD]
            self.assertEqual(campaign["card_type"], "campaign")
            self.assertEqual(campaign["status"], "active")
            self.assertEqual(campaign["parent_card_id"], PILLAR_CARD)
            self.assertEqual(campaign["child_card_ids"], [CONCEPT_CARD])
            concept = cards[CONCEPT_CARD]
            self.assertEqual(concept["card_type"], "concept")
            self.assertEqual(concept["parent_card_id"], CAMPAIGN_CARD)
            self.assertEqual(concept["child_card_ids"], [PROJECT_CARD])
            idea = cards[IDEA_CARD]
            self.assertEqual(idea["card_type"], "opportunity")
            self.assertEqual(idea["status"], "assigned")
            self.assertEqual(idea["child_card_ids"], [])
            # The example warning targets approved work, so the badge belongs
            # to the project card, not the opportunity card.
            self.assertEqual(idea["warning_badges"], [])
            project = cards[PROJECT_CARD]
            self.assertEqual(project["card_type"], "project")
            self.assertEqual(project["status"], "planning")
            self.assertEqual(project["parent_card_id"], CONCEPT_CARD)
            self.assertEqual(project["warning_badges"], ["important"])

            validate_board(workspace_dir)

    def test_rebuild_matches_the_example_board_fixture(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            # The scaffold writes the example board; the derivation must agree
            # with it (columns/manual_order/updated_on are projection-free).
            validate_board(workspace_dir)

    def test_rebuild_preserves_columns_and_manual_order(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            board_path = workspace_dir / "boards" / "content-board.json"
            board = json.loads(board_path.read_text())
            board["manual_order"] = [PROJECT_CARD, IDEA_CARD]
            write_json(board_path, board)

            rebuild_board(workspace_dir)
            rebuilt = load_board(workspace_dir)
            self.assertEqual(
                rebuilt["manual_order"],
                [PROJECT_CARD, IDEA_CARD, PILLAR_CARD, CAMPAIGN_CARD,
                 CONCEPT_CARD],
            )
            self.assertEqual(
                [column["column_id"] for column in rebuilt["columns"]],
                ["column_queue", "column_in_production"],
            )

    def test_rebuild_appends_new_cards_after_existing_order(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            rebuild_board(workspace_dir)

            entry = load_example("content-opportunity")
            entry["content_opportunity_id"] = "content_opportunity_luna_fit_002"
            entry["status"] = "new"
            entry.pop("linked_campaign_concept_ids", None)
            entry.pop("linked_project_ids", None)
            write_json(
                workspace_dir / "research" / "content-opportunity-queue" / "entries"
                / "content_opportunity_luna_fit_002.json",
                entry,
            )

            rebuild_board(workspace_dir)
            board = load_board(workspace_dir)
            self.assertEqual(
                board["manual_order"],
                HIERARCHY_ORDER + ["card_content_opportunity_luna_fit_002"],
            )

    def test_rebuild_drops_stale_cards(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            rebuild_board(workspace_dir)
            # Warning targets must exist, so removing the project requires
            # clearing the warning that targets it first.
            (workspace_dir / "system" / "project-warnings.jsonl").write_text("")
            manifest_path = workspace_dir / "projects" / PROJECT_SLUG / "project.json"
            manifest_path.unlink()

            rebuild_board(workspace_dir)
            board = load_board(workspace_dir)
            self.assertEqual(
                board["manual_order"],
                [PILLAR_CARD, CAMPAIGN_CARD, CONCEPT_CARD, IDEA_CARD],
            )
            cards = board_cards_by_id(workspace_dir)
            self.assertNotIn(PROJECT_CARD, cards)
            self.assertEqual(cards[CONCEPT_CARD]["child_card_ids"], [])

    def test_resolved_warning_does_not_badge(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            warning = load_example("project-warning")
            warning["resolved_status"] = "resolved"
            write_jsonl(
                workspace_dir / "system" / "project-warnings.jsonl", [warning]
            )

            rebuild_board(workspace_dir)
            cards = board_cards_by_id(workspace_dir)
            self.assertEqual(cards[PROJECT_CARD]["warning_badges"], [])

    def test_queue_level_warning_badges_the_idea_card(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            warning = load_example("project-warning")
            warning.pop("project_id")
            warning.pop("concept_approval_id")
            warning["severity"] = "urgent"
            write_jsonl(
                workspace_dir / "system" / "project-warnings.jsonl", [warning]
            )

            rebuild_board(workspace_dir)
            cards = board_cards_by_id(workspace_dir)
            self.assertEqual(cards[IDEA_CARD]["warning_badges"], ["urgent"])
            self.assertEqual(cards[PROJECT_CARD]["warning_badges"], [])

    def test_badges_are_unique_and_severity_ranked(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            first = load_example("project-warning")
            second = load_example("project-warning")
            second["project_warning_id"] = "project_warning_luna_fit_002"
            second["severity"] = "urgent"
            third = load_example("project-warning")
            third["project_warning_id"] = "project_warning_luna_fit_003"
            third["severity"] = "urgent"
            write_jsonl(
                workspace_dir / "system" / "project-warnings.jsonl",
                [first, second, third],
            )

            rebuild_board(workspace_dir)
            cards = board_cards_by_id(workspace_dir)
            self.assertEqual(
                cards[PROJECT_CARD]["warning_badges"], ["urgent", "important"]
            )

    def test_rebuild_fails_when_project_promotion_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            # Clear the warning that also targets the promotion, so the
            # parent-resolution failure is what fires.
            (workspace_dir / "system" / "project-warnings.jsonl").write_text("")
            (
                workspace_dir / "campaigns" / "campaign_luna_fit_001" / "approvals"
                / "concept_approval_luna_fit_001.json"
            ).unlink()

            with self.assertRaises(ValidationError) as ctx:
                rebuild_board(workspace_dir)
            self.assertIn("cannot resolve its parent card", str(ctx.exception))


class ValidateBoardTests(unittest.TestCase):
    def test_status_drift_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            rebuild_board(workspace_dir)
            entry_path = (
                workspace_dir / "research" / "content-opportunity-queue" / "entries"
                / f"{ENTRY_ID}.json"
            )
            entry = json.loads(entry_path.read_text())
            entry["status"] = "shortlisted"
            write_json(entry_path, entry)

            with self.assertRaises(ValidationError) as ctx:
                validate_board(workspace_dir)
            message = str(ctx.exception)
            self.assertIn("status", message)
            self.assertIn("rebuild-board", message)

    def test_missing_card_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            rebuild_board(workspace_dir)
            board_path = workspace_dir / "boards" / "content-board.json"
            board = json.loads(board_path.read_text())
            board["cards"] = [
                card for card in board["cards"]
                if card["content_card_id"] != PROJECT_CARD
            ]
            board["manual_order"].remove(PROJECT_CARD)
            write_json(board_path, board)

            with self.assertRaises(ValidationError) as ctx:
                validate_board(workspace_dir)
            self.assertIn("missing cards", str(ctx.exception))

    def test_manual_order_must_list_every_card_once(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            rebuild_board(workspace_dir)
            board_path = workspace_dir / "boards" / "content-board.json"
            board = json.loads(board_path.read_text())
            board["manual_order"] = [IDEA_CARD]
            write_json(board_path, board)

            with self.assertRaises(ValidationError) as ctx:
                validate_board(workspace_dir)
            self.assertIn("manual_order", str(ctx.exception))

    def test_missing_board_names_rebuild_command(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)
            (workspace_dir / "boards" / "content-board.json").unlink()

            with self.assertRaises(FileNotFoundError) as ctx:
                validate_board(workspace_dir)
            self.assertIn("rebuild-board", str(ctx.exception))


class BoardCliTests(unittest.TestCase):
    def test_rebuild_board_and_validate_board_commands(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_indexable_workspace(temp_dir)

            rebuild = subprocess.run(
                [sys.executable, "-m", "influencer_os", "rebuild-board", str(workspace_dir)],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(rebuild.returncode, 0, rebuild.stderr)
            self.assertIn("Rebuilt content board: 5 cards", rebuild.stdout)

            validate = subprocess.run(
                [sys.executable, "-m", "influencer_os", "validate", "board", str(workspace_dir)],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(validate.returncode, 0, validate.stderr)
            self.assertIn("Checked 5 board cards.", validate.stdout)


if __name__ == "__main__":
    unittest.main()
