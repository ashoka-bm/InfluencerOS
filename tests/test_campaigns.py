"""Campaign hierarchy records and constructors (ADRs 0029-0032, Slice 1).

The canonical-seed tests follow the fixture contract from
docs/record-constructors.md: a seed of authored fields must scaffold to a
record field-equal to the repository example, proving the constructor owns
every derived and copied field.
"""

import datetime
import json
import tempfile
import unittest
from pathlib import Path

from influencer_os.campaigns import (
    activate_campaign,
    check_project_expression_against_approval,
    scaffold_campaign,
    scaffold_campaign_concept,
    scaffold_content_opportunity,
    validate_campaign_records,
)
from influencer_os.creator_workspaces import init_creator
from influencer_os.json_io import write_json_atomic
from influencer_os.validation import (
    ValidationError,
    load_json,
    validate_record,
)
from tests.support import ROOT, populate_workspace_records


def _example(name):
    return json.loads((ROOT / "examples" / name).read_text())


def _campaign_seed_from_example():
    example = _example("campaign.example.json")
    return {
        "name": example["name"],
        "objective": example["objective"],
        "primary_content_pillar_id": example["primary_content_pillar_id"],
        "supporting_content_pillar_ids": example["supporting_content_pillar_ids"],
        "primary_audience_segment": example["primary_audience_segment"],
        "supporting_audience_segments": example["supporting_audience_segments"],
        "primary_offer_conversion_asset_id": example[
            "primary_offer_conversion_asset_id"
        ],
        "supporting_conversion_asset_ids": example[
            "supporting_conversion_asset_ids"
        ],
        "measurable_outcome": example["measurable_outcome"],
        "notes": example["notes"],
    }


def _concept_seed_from_example():
    example = _example("campaign-concept.example.json")
    return {
        "campaign_id": example["campaign_id"],
        "title": example["title"],
        "hypothesis": example["hypothesis"],
        "audience_tension": example["audience_tension"],
        "promise": example["promise"],
        "audience_segment": example["audience_segment"],
        "content_pillar_id": example["content_pillar_id"],
        "primary_commercial_function": example["primary_commercial_function"],
        "supporting_commercial_functions": example[
            "supporting_commercial_functions"
        ],
        "source_content_opportunity_id": example[
            "source_content_opportunity_id"
        ],
        "related_concepts": example["related_concepts"],
        "notes": example["notes"],
    }


def _opportunity_seed_from_example():
    example = _example("content-opportunity.example.json")
    seed = {
        field: example[field]
        for field in (
            "title",
            "hook",
            "premise_summary",
            "intended_payoff",
            "intended_emotion",
            "core_message",
            "topic_cluster",
            "platform_recommendations",
            "format_recommendations",
            "schedule_fit_type",
            "evidence_refs",
            "scores",
        )
        if field in example
    }
    for optional in (
        "content_pillar_ids",
        "source_finding_ids",
        "urgency_window",
        "creator_fit_notes",
        "production_notes",
        "avoid_notes",
        "stale_on",
        "assignment_intent_note",
    ):
        if optional in example:
            seed[optional] = example[optional]
    return seed


def _campaign_workspace(temp_dir):
    """Creator workspace with profile records and the conversion asset the
    campaign example names, rooted under creators/ (index-path invariant)."""
    workspace_dir = init_creator(
        ROOT / "examples" / "creator-workspace.example.json",
        workspace_root=Path(temp_dir) / "creators",
    )
    populate_workspace_records(workspace_dir)
    asset = _example("conversion-asset.example.json")
    assets_dir = workspace_dir / "conversion-assets"
    assets_dir.mkdir(exist_ok=True)
    write_json_atomic(
        assets_dir / f"{asset['conversion_asset_id']}.json", asset
    )
    return workspace_dir


def _write_opportunity_fixture(workspace_dir):
    """Materialize the example opportunity + queue as canonical records."""
    entry = _example("content-opportunity.example.json")
    queue = _example("content-opportunity-queue.example.json")
    queue_dir = workspace_dir / "research" / "content-opportunity-queue"
    entries_dir = queue_dir / "entries"
    entries_dir.mkdir(parents=True, exist_ok=True)
    write_json_atomic(
        entries_dir / f"{entry['content_opportunity_id']}.json", entry
    )
    write_json_atomic(queue_dir / "queue.json", queue)


class ScaffoldCampaignTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace_dir = _campaign_workspace(self.temp.name)

    def test_canonical_seed_reproduces_example_after_activation(self):
        result = scaffold_campaign(
            _campaign_seed_from_example(),
            self.workspace_dir,
            now=datetime.datetime(2026, 7, 1, 9, 0, 0),
        )
        self.assertEqual(result["campaign_id"], "campaign_luna_fit_001")
        activate_campaign(
            self.workspace_dir,
            "campaign_luna_fit_001",
            activation_note="Approved after the July slot-research review.",
            now=datetime.datetime(2026, 7, 3, 9, 0, 0),
        )
        written = load_json(result["campaign_path"])
        self.assertEqual(written, _example("campaign.example.json"))

    def test_scaffold_starts_draft_without_activation(self):
        result = scaffold_campaign(
            _campaign_seed_from_example(), self.workspace_dir
        )
        written = load_json(result["campaign_path"])
        self.assertEqual(written["status"], "draft")
        self.assertNotIn("activation", written)

    def test_seed_rejects_constructor_owned_fields(self):
        seed = _campaign_seed_from_example()
        seed["status"] = "active"
        with self.assertRaisesRegex(ValidationError, "non-seed fields"):
            scaffold_campaign(seed, self.workspace_dir)

    def test_seed_missing_authored_field_fails(self):
        seed = _campaign_seed_from_example()
        del seed["measurable_outcome"]
        with self.assertRaisesRegex(ValidationError, "missing authored"):
            scaffold_campaign(seed, self.workspace_dir)

    def test_unknown_pillar_fails(self):
        seed = _campaign_seed_from_example()
        seed["primary_content_pillar_id"] = "pillar_never_declared"
        with self.assertRaisesRegex(ValidationError, "pillar_never_declared"):
            scaffold_campaign(seed, self.workspace_dir)

    def test_unknown_conversion_asset_fails(self):
        seed = _campaign_seed_from_example()
        seed["primary_offer_conversion_asset_id"] = "conversion_asset_ghost"
        with self.assertRaisesRegex(ValidationError, "conversion_asset_ghost"):
            scaffold_campaign(seed, self.workspace_dir)

    def test_campaign_ids_sequence(self):
        first = scaffold_campaign(
            _campaign_seed_from_example(), self.workspace_dir
        )
        seed = _campaign_seed_from_example()
        seed["name"] = "Second campaign"
        second = scaffold_campaign(seed, self.workspace_dir)
        self.assertEqual(first["campaign_id"], "campaign_luna_fit_001")
        self.assertEqual(second["campaign_id"], "campaign_luna_fit_002")

    def test_activation_requires_draft(self):
        scaffold_campaign(_campaign_seed_from_example(), self.workspace_dir)
        activate_campaign(self.workspace_dir, "campaign_luna_fit_001")
        with self.assertRaisesRegex(ValidationError, "only a draft"):
            activate_campaign(self.workspace_dir, "campaign_luna_fit_001")


class ScaffoldCampaignConceptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace_dir = _campaign_workspace(self.temp.name)
        scaffold_campaign(
            _campaign_seed_from_example(),
            self.workspace_dir,
            now=datetime.datetime(2026, 7, 1, 9, 0, 0),
        )
        activate_campaign(
            self.workspace_dir,
            "campaign_luna_fit_001",
            activation_note="Approved after the July slot-research review.",
            now=datetime.datetime(2026, 7, 3, 9, 0, 0),
        )
        _write_opportunity_fixture(self.workspace_dir)

    def test_canonical_seed_reproduces_example(self):
        result = scaffold_campaign_concept(
            _concept_seed_from_example(),
            self.workspace_dir,
            now=datetime.datetime(2026, 7, 3, 10, 0, 0),
        )
        self.assertEqual(
            result["campaign_concept_id"], "campaign_concept_luna_fit_001"
        )
        written = load_json(result["concept_path"])
        self.assertEqual(written, _example("campaign-concept.example.json"))

    def test_evidence_is_copied_from_assigned_opportunity(self):
        result = scaffold_campaign_concept(
            _concept_seed_from_example(), self.workspace_dir
        )
        written = load_json(result["concept_path"])
        opportunity = _example("content-opportunity.example.json")
        self.assertEqual(written["evidence_refs"], opportunity["evidence_refs"])

    def test_seed_with_evidence_and_source_opportunity_fails_closed(self):
        seed = _concept_seed_from_example()
        seed["evidence_refs"] = _example("content-opportunity.example.json")[
            "evidence_refs"
        ]
        with self.assertRaisesRegex(ValidationError, "copied from"):
            scaffold_campaign_concept(seed, self.workspace_dir)

    def test_seed_rejects_constructor_owned_fields(self):
        seed = _concept_seed_from_example()
        seed["status"] = "active"
        with self.assertRaisesRegex(ValidationError, "non-seed fields"):
            scaffold_campaign_concept(seed, self.workspace_dir)

    def test_unknown_campaign_fails(self):
        seed = _concept_seed_from_example()
        seed["campaign_id"] = "campaign_luna_fit_999"
        with self.assertRaisesRegex(ValidationError, "resolves to no campaign"):
            scaffold_campaign_concept(seed, self.workspace_dir)

    def test_unapproved_audience_segment_fails(self):
        seed = _concept_seed_from_example()
        seed["audience_segment"] = "An audience the campaign never approved."
        with self.assertRaisesRegex(ValidationError, "does not approve"):
            scaffold_campaign_concept(seed, self.workspace_dir)

    def test_unapproved_pillar_fails(self):
        seed = _concept_seed_from_example()
        seed["content_pillar_id"] = "pillar_never_declared"
        with self.assertRaisesRegex(ValidationError, "does not approve"):
            scaffold_campaign_concept(seed, self.workspace_dir)

    def test_missing_source_opportunity_fails(self):
        seed = _concept_seed_from_example()
        seed["source_content_opportunity_id"] = "content_opportunity_ghost"
        with self.assertRaisesRegex(ValidationError, "content_opportunity_ghost"):
            scaffold_campaign_concept(seed, self.workspace_dir)

    def test_campaign_scoped_concept_authors_its_own_evidence(self):
        seed = _concept_seed_from_example()
        del seed["source_content_opportunity_id"]
        evidence = _example("content-opportunity.example.json")["evidence_refs"]
        seed["evidence_refs"] = evidence
        result = scaffold_campaign_concept(seed, self.workspace_dir)
        written = load_json(result["concept_path"])
        self.assertEqual(written["evidence_refs"], evidence)
        self.assertNotIn("source_content_opportunity_id", written)


class ScaffoldContentOpportunityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace_dir = _campaign_workspace(self.temp.name)

    def test_canonical_seed_reproduces_example_and_queue(self):
        result = scaffold_content_opportunity(
            _opportunity_seed_from_example(),
            self.workspace_dir,
            now=datetime.datetime(2026, 7, 3, 9, 0, 0),
        )
        self.assertEqual(
            result["content_opportunity_id"], "content_opportunity_luna_fit_001"
        )
        written = load_json(result["entry_path"])
        self.assertEqual(written, _example("content-opportunity.example.json"))
        queue = load_json(result["queue_path"])
        self.assertEqual(
            queue, _example("content-opportunity-queue.example.json")
        )

    def test_seed_rejects_constructor_owned_fields(self):
        seed = _opportunity_seed_from_example()
        seed["status"] = "assigned"
        with self.assertRaisesRegex(ValidationError, "non-seed fields"):
            scaffold_content_opportunity(seed, self.workspace_dir)

    def test_queue_upsert_tracks_second_entry(self):
        scaffold_content_opportunity(
            _opportunity_seed_from_example(), self.workspace_dir
        )
        seed = _opportunity_seed_from_example()
        seed["title"] = "A second desk-reset angle"
        result = scaffold_content_opportunity(seed, self.workspace_dir)
        self.assertEqual(
            result["content_opportunity_id"], "content_opportunity_luna_fit_002"
        )
        queue = load_json(result["queue_path"])
        self.assertEqual(len(queue["entry_refs"]), 2)
        self.assertEqual(queue["status_counts"], {"new": 2})


class CampaignSemanticsTests(unittest.TestCase):
    def test_paid_conversion_requires_primary_offer(self):
        campaign = _example("campaign.example.json")
        campaign["objective"] = "paid_conversion"
        del campaign["primary_offer_conversion_asset_id"]
        with self.assertRaisesRegex(ValidationError, "paid_conversion"):
            validate_record("campaign", campaign)

    def test_active_status_requires_activation(self):
        campaign = _example("campaign.example.json")
        del campaign["activation"]
        with self.assertRaisesRegex(ValidationError, "activation"):
            validate_record("campaign", campaign)

    def test_supporting_pillars_must_not_repeat_primary(self):
        campaign = _example("campaign.example.json")
        campaign["supporting_content_pillar_ids"] = [
            campaign["primary_content_pillar_id"]
        ]
        with self.assertRaisesRegex(ValidationError, "repeat the primary"):
            validate_record("campaign", campaign)

    def test_supporting_functions_must_not_repeat_primary(self):
        concept = _example("campaign-concept.example.json")
        concept["supporting_commercial_functions"] = [
            concept["primary_commercial_function"]
        ]
        with self.assertRaisesRegex(ValidationError, "repeat"):
            validate_record("campaign-concept", concept)

    def test_concept_cannot_relate_to_itself(self):
        concept = _example("campaign-concept.example.json")
        concept["related_concepts"] = [
            {
                "relation": "refines",
                "campaign_concept_id": concept["campaign_concept_id"],
            }
        ]
        with self.assertRaisesRegex(ValidationError, "relate to itself"):
            validate_record("campaign-concept", concept)

    def test_approval_rejects_duplicate_project_ids(self):
        approval = _example("concept-approval.example.json")
        approval["project_ids_created"] = approval["project_ids_created"] * 2
        with self.assertRaisesRegex(ValidationError, "duplicate project ids"):
            validate_record("concept-approval", approval)

    def test_project_expression_rejects_invalid_matrix_cell(self):
        project = _example("project.example.json")
        project["commercial_expression"] = {
            "commercial_function": "direct_conversion",
            "offer_integration": "absent",
            "cta_intensity": "direct",
        }
        with self.assertRaises(ValidationError):
            validate_record("project", project)

    def test_project_expression_accepts_valid_matrix_cell(self):
        project = _example("project.example.json")
        project["commercial_expression"] = {
            "commercial_function": "lead_capture",
            "offer_integration": "embedded",
            "cta_intensity": "soft",
        }
        validate_record("project", project)


class ProjectExpressionAgainstApprovalTests(unittest.TestCase):
    def setUp(self):
        self.approval = _example("concept-approval.example.json")
        self.concept = _example("campaign-concept.example.json")
        self.project = _example("project.example.json")

    def _expression(self, function="lead_capture", offer="embedded", cta="soft"):
        self.project["commercial_expression"] = {
            "commercial_function": function,
            "offer_integration": offer,
            "cta_intensity": cta,
        }

    def test_at_ceiling_expression_passes(self):
        self._expression()
        check_project_expression_against_approval(
            self.project, self.approval, self.concept
        )

    def test_missing_expression_fails(self):
        with self.assertRaisesRegex(ValidationError, "commercial_expression"):
            check_project_expression_against_approval(
                self.project, self.approval, self.concept
            )

    def test_unapproved_function_fails(self):
        self._expression(function="direct_conversion")
        with self.assertRaisesRegex(ValidationError, "does not approve"):
            check_project_expression_against_approval(
                self.project, self.approval, self.concept
            )

    def test_expression_above_ceilings_fails(self):
        self._expression(offer="central", cta="soft")
        with self.assertRaisesRegex(ValidationError, "ceilings"):
            check_project_expression_against_approval(
                self.project, self.approval, self.concept
            )

    def test_invalid_matrix_cell_fails_even_below_ceilings(self):
        approval = dict(self.approval)
        approval["max_offer_integration"] = "central"
        approval["max_cta_intensity"] = "direct"
        self._expression(offer="embedded", cta="direct")
        with self.assertRaises(ValidationError):
            check_project_expression_against_approval(
                self.project, approval, self.concept
            )


class ValidateCampaignRecordsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace_dir = _campaign_workspace(self.temp.name)
        scaffold_campaign(
            _campaign_seed_from_example(),
            self.workspace_dir,
            now=datetime.datetime(2026, 7, 1, 9, 0, 0),
        )
        activate_campaign(
            self.workspace_dir,
            "campaign_luna_fit_001",
            activation_note="Approved after the July slot-research review.",
            now=datetime.datetime(2026, 7, 3, 9, 0, 0),
        )
        _write_opportunity_fixture(self.workspace_dir)
        scaffold_campaign_concept(
            _concept_seed_from_example(),
            self.workspace_dir,
            now=datetime.datetime(2026, 7, 3, 10, 0, 0),
        )

    def _write_approval(self):
        approval = _example("concept-approval.example.json")
        approvals_dir = (
            self.workspace_dir / "campaigns" / "campaign_luna_fit_001"
            / "approvals"
        )
        approvals_dir.mkdir(parents=True, exist_ok=True)
        write_json_atomic(
            approvals_dir / f"{approval['concept_approval_id']}.json", approval
        )

    def test_consistent_hierarchy_validates(self):
        self._write_approval()
        result = validate_campaign_records(self.workspace_dir)
        checked = result["checked_paths"]
        self.assertIn("campaigns/campaign_luna_fit_001/campaign.json", checked)
        self.assertIn(
            "campaigns/campaign_luna_fit_001/concepts/"
            "campaign_concept_luna_fit_001.json",
            checked,
        )
        self.assertIn(
            "campaigns/campaign_luna_fit_001/approvals/"
            "concept_approval_luna_fit_001.json",
            checked,
        )
        self.assertIn(
            "research/content-opportunity-queue/queue.json", checked
        )

    def test_workspace_without_campaigns_validates(self):
        import shutil

        shutil.rmtree(self.workspace_dir / "campaigns")
        shutil.rmtree(
            self.workspace_dir / "research" / "content-opportunity-queue"
        )
        result = validate_campaign_records(self.workspace_dir)
        self.assertEqual(result["checked_paths"], [])

    def test_folder_name_must_match_campaign_id(self):
        (self.workspace_dir / "campaigns" / "campaign_luna_fit_001").rename(
            self.workspace_dir / "campaigns" / "campaign_luna_fit_wrong"
        )
        with self.assertRaisesRegex(ValidationError, "folder name"):
            validate_campaign_records(self.workspace_dir)

    def test_cross_campaign_concept_rejected(self):
        seed = _campaign_seed_from_example()
        seed["name"] = "Second campaign"
        scaffold_campaign(seed, self.workspace_dir)
        concept_path = (
            self.workspace_dir / "campaigns" / "campaign_luna_fit_001"
            / "concepts" / "campaign_concept_luna_fit_001.json"
        )
        foreign_dir = (
            self.workspace_dir / "campaigns" / "campaign_luna_fit_002"
            / "concepts"
        )
        foreign_dir.mkdir(parents=True)
        concept_path.rename(
            foreign_dir / "campaign_concept_luna_fit_001.json"
        )
        with self.assertRaisesRegex(ValidationError, "belongs to"):
            validate_campaign_records(self.workspace_dir)

    def test_approval_must_name_existing_concept(self):
        approval = _example("concept-approval.example.json")
        approval["campaign_concept_id"] = "campaign_concept_luna_fit_999"
        approvals_dir = (
            self.workspace_dir / "campaigns" / "campaign_luna_fit_001"
            / "approvals"
        )
        approvals_dir.mkdir(parents=True, exist_ok=True)
        write_json_atomic(
            approvals_dir / f"{approval['concept_approval_id']}.json", approval
        )
        with self.assertRaisesRegex(ValidationError, "does not exist"):
            validate_campaign_records(self.workspace_dir)

    def test_queue_count_drift_rejected(self):
        queue_path = (
            self.workspace_dir / "research" / "content-opportunity-queue"
            / "queue.json"
        )
        queue = load_json(queue_path)
        queue["status_counts"] = {"new": 5}
        write_json_atomic(queue_path, queue)
        with self.assertRaisesRegex(ValidationError, "status_counts"):
            validate_campaign_records(self.workspace_dir)

    def test_entries_without_manifest_rejected(self):
        queue_path = (
            self.workspace_dir / "research" / "content-opportunity-queue"
            / "queue.json"
        )
        queue_path.unlink()
        with self.assertRaisesRegex(ValidationError, "queue manifest"):
            validate_campaign_records(self.workspace_dir)

    def test_dangling_concept_link_rejected(self):
        entry_path = (
            self.workspace_dir / "research" / "content-opportunity-queue"
            / "entries" / "content_opportunity_luna_fit_001.json"
        )
        entry = load_json(entry_path)
        entry["linked_campaign_concept_ids"] = ["campaign_concept_luna_fit_404"]
        write_json_atomic(entry_path, entry)
        with self.assertRaisesRegex(ValidationError, "does not exist"):
            validate_campaign_records(self.workspace_dir)


if __name__ == "__main__":
    unittest.main()
