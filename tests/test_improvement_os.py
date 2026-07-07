"""Improvement OS tests (ADR 0025): the Production Rubric substrate and the
friction-event seam. Writer (log-incident / mint-criterion) and at-rest
validation (validate workspace / validate research) share one seam, so every
negative case is probed on both sides where it applies."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from influencer_os.creator_workspaces import init_creator, validate_creator_workspace
from influencer_os.research import load_workspace_scope, validate_events_ledger
from influencer_os.rubric import (
    DEFAULT_REFLECTION_THRESHOLDS,
    REFLECTION_RUNS_DIR_RELATIVE,
    collect_criteria,
    log_incident,
    mint_criterion,
    reflection_report,
)
from influencer_os.validation import ValidationError, validate_record

ROOT = Path(__file__).resolve().parents[1]


def make_event(**overrides):
    record = {
        "event_id": "event_luna_fit_900",
        "occurred_on": "2026-07-06T12:00:00",
        "event_type": "rejection",
        "severity": "important",
        "message": "Rejected draft for testing.",
        "source_type": "skill",
        "source_id": "create-production-plan",
        "creator_profile_id": "creator_luna_fit",
        "creator_slug": "luna-fit",
        "recurrence_key": "gen.identity.consistent",
        "criterion_id": "gen.identity.consistent",
    }
    record.update(overrides)
    return {key: value for key, value in record.items() if value is not None}


class WorkspaceScaffoldMixin:
    """One template workspace per class; per-test copies keep tests isolated
    without re-running init_creator (which syncs every runtime skill)."""

    @classmethod
    def setUpClass(cls):
        cls._template_tmp = tempfile.TemporaryDirectory()
        template_root = Path(cls._template_tmp.name)
        workspace = init_creator(
            ROOT / "examples" / "creator-workspace.example.json",
            workspace_root=template_root,
        )
        shutil.copyfile(
            ROOT / "examples" / "creator-profile.example.json",
            workspace / "creator-profile.json",
        )
        shutil.copyfile(
            ROOT / "examples" / "reference-library.example.json",
            workspace / "references" / "reference-library.json",
        )
        shutil.copyfile(
            ROOT / "examples" / "sources" / "luna-fit-breakdown.example.md",
            workspace / "sources" / "intakes" / "luna-fit-breakdown.md",
        )
        cls._template_workspace = workspace

    @classmethod
    def tearDownClass(cls):
        cls._template_tmp.cleanup()

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.workspace = Path(tmp.name) / "luna-fit"
        shutil.copytree(self._template_workspace, self.workspace)

    def append_ledger_line(self, record):
        ledger = self.workspace / "system" / "creator-events.jsonl"
        ledger.parent.mkdir(parents=True, exist_ok=True)
        with ledger.open("a") as handle:
            handle.write(json.dumps(record) + "\n")

    def scope(self):
        return load_workspace_scope(self.workspace)


class EventSemanticsTests(unittest.TestCase):
    """Structural friction semantics run wherever validate_record runs."""

    def test_rejection_with_both_criterion_and_unclassified_fails(self):
        with self.assertRaisesRegex(ValidationError, "exactly one of"):
            validate_record("system-event", make_event(unclassified=True))

    def test_rejection_with_neither_criterion_nor_unclassified_fails(self):
        record = make_event()
        del record["criterion_id"]
        with self.assertRaisesRegex(ValidationError, "exactly one of"):
            validate_record("system-event", record)

    def test_recurrence_key_must_equal_cited_criterion(self):
        record = make_event(recurrence_key="gen.plan.continuity")
        with self.assertRaisesRegex(ValidationError, "recurrence_key must equal"):
            validate_record("system-event", record)

    def test_friction_fields_forbidden_on_non_friction_events(self):
        record = make_event(event_type="research_run_completed")
        del record["criterion_id"]
        with self.assertRaisesRegex(ValidationError, "only valid on friction"):
            validate_record("system-event", record)

    def test_incident_requires_recurrence_key(self):
        record = make_event(event_type="incident")
        del record["criterion_id"]
        del record["recurrence_key"]
        with self.assertRaisesRegex(ValidationError, "require recurrence_key"):
            validate_record("system-event", record)

    def test_incident_may_not_be_unclassified(self):
        record = make_event(event_type="incident", unclassified=True)
        del record["criterion_id"]
        with self.assertRaisesRegex(ValidationError, "rejections only"):
            validate_record("system-event", record)


class RubricSemanticsTests(unittest.TestCase):
    def make_rubric(self, **overrides):
        rubric = {
            "rubric_id": "rubric_luna_fit",
            "scope": "creator",
            "creator_profile_id": "creator_luna_fit",
            "creator_slug": "luna-fit",
            "criteria": [],
        }
        rubric.update(overrides)
        return {key: value for key, value in rubric.items() if value is not None}

    def make_criterion(self, **overrides):
        criterion = {
            "criterion_id": "creator.test.rule",
            "statement": "The draft follows the test rule.",
            "status": "minted",
            "origin": "rejection",
            "minted_on": "2026-07-06",
        }
        criterion.update(overrides)
        return criterion

    def test_creator_scope_requires_creator_fields(self):
        rubric = self.make_rubric(creator_profile_id=None)
        with self.assertRaisesRegex(ValidationError, "requires creator_profile_id"):
            validate_record("production-rubric", rubric)

    def test_os_scope_forbids_creator_fields(self):
        rubric = self.make_rubric(scope="os")
        with self.assertRaisesRegex(ValidationError, "must not carry"):
            validate_record("production-rubric", rubric)

    def test_duplicate_criterion_ids_within_file_fail(self):
        rubric = self.make_rubric(
            criteria=[self.make_criterion(), self.make_criterion()]
        )
        with self.assertRaisesRegex(ValidationError, "duplicate criterion id"):
            validate_record("production-rubric", rubric)

    def test_blocking_requires_adr(self):
        rubric = self.make_rubric(criteria=[self.make_criterion(status="blocking")])
        with self.assertRaisesRegex(ValidationError, "requires blocking_adr"):
            validate_record("production-rubric", rubric)

    def test_non_blocking_forbids_adr(self):
        rubric = self.make_rubric(
            criteria=[
                self.make_criterion(
                    blocking_adr="docs/adr/0025-improvement-os-feedback-loops.md"
                )
            ]
        )
        with self.assertRaisesRegex(ValidationError, "but is not blocking"):
            validate_record("production-rubric", rubric)


class RubricSubstrateTests(WorkspaceScaffoldMixin, unittest.TestCase):
    def test_init_creator_scaffolds_valid_empty_rubric(self):
        rubric_path = self.workspace / "production-rubric.json"
        self.assertTrue(rubric_path.exists())
        rubric = json.loads(rubric_path.read_text())
        validate_record("production-rubric", rubric)
        self.assertEqual(rubric["scope"], "creator")
        self.assertEqual(rubric["criteria"], [])
        validate_creator_workspace(self.workspace)

    def test_log_incident_writes_a_resolvable_rejection(self):
        result = log_incident(
            self.workspace,
            event_type="rejection",
            recurrence_key="gen.identity.consistent",
            criterion_id="gen.identity.consistent",
            message="Face drifts from the identity plate.",
            source_id="review-generated-assets",
            iteration_count=2,
        )
        self.assertEqual(result["event_id"], "event_luna_fit_001")
        validate_creator_workspace(self.workspace)
        validate_events_ledger(self.workspace, self.scope())

    def test_unclassified_rejection_validates_end_to_end(self):
        log_incident(
            self.workspace,
            event_type="rejection",
            recurrence_key="vibe.cluster.tone",
            unclassified=True,
            message="Tone felt off; rule not articulable yet.",
            source_id="create-production-plan",
        )
        validate_creator_workspace(self.workspace)

    def test_citing_unknown_criterion_fails_writer_and_at_rest(self):
        with self.assertRaisesRegex(ValidationError, "unknown rubric criterion"):
            log_incident(
                self.workspace,
                event_type="rejection",
                recurrence_key="ghost.rule",
                criterion_id="ghost.rule",
                message="should fail",
                source_id="create-production-plan",
            )
        self.append_ledger_line(
            make_event(recurrence_key="ghost.rule", criterion_id="ghost.rule")
        )
        with self.assertRaisesRegex(ValidationError, "unknown rubric criterion"):
            validate_creator_workspace(self.workspace)

    def test_citing_retired_criterion_fails_writer_and_at_rest(self):
        mint_criterion(
            self.workspace,
            criterion_id="creator.test.retired_rule",
            statement="A rule that gets retired.",
        )
        rubric_path = self.workspace / "production-rubric.json"
        rubric = json.loads(rubric_path.read_text())
        rubric["criteria"][0]["status"] = "retired"
        rubric_path.write_text(json.dumps(rubric, indent=2) + "\n")
        with self.assertRaisesRegex(ValidationError, "retired rubric criterion"):
            log_incident(
                self.workspace,
                event_type="rejection",
                recurrence_key="creator.test.retired_rule",
                criterion_id="creator.test.retired_rule",
                message="should fail",
                source_id="create-production-plan",
            )
        self.append_ledger_line(
            make_event(
                recurrence_key="creator.test.retired_rule",
                criterion_id="creator.test.retired_rule",
            )
        )
        with self.assertRaisesRegex(ValidationError, "retired rubric criterion"):
            validate_creator_workspace(self.workspace)

    def test_duplicate_event_ids_fail_at_rest(self):
        record = make_event()
        self.append_ledger_line(record)
        self.append_ledger_line(record)
        with self.assertRaisesRegex(ValidationError, "duplicate event id"):
            validate_creator_workspace(self.workspace)

    def test_mint_criterion_rejects_duplicates_across_scopes(self):
        mint_criterion(
            self.workspace,
            criterion_id="creator.test.rule",
            statement="The draft follows the test rule.",
        )
        with self.assertRaisesRegex(ValidationError, "already exists"):
            mint_criterion(
                self.workspace,
                criterion_id="creator.test.rule",
                statement="Duplicate within the creator rubric.",
            )
        with self.assertRaisesRegex(ValidationError, "already exists"):
            mint_criterion(
                self.workspace,
                criterion_id="gen.identity.consistent",
                statement="Collides with an OS seed criterion.",
            )

    def test_workspace_rubric_duplicating_an_os_criterion_fails_at_rest(self):
        rubric_path = self.workspace / "production-rubric.json"
        rubric = json.loads(rubric_path.read_text())
        rubric["criteria"].append(
            {
                "criterion_id": "gen.identity.consistent",
                "statement": "Shadows the OS seed criterion.",
                "status": "minted",
                "origin": "rejection",
                "minted_on": "2026-07-06",
            }
        )
        rubric_path.write_text(json.dumps(rubric, indent=2) + "\n")
        with self.assertRaisesRegex(ValidationError, "duplicate criterion id"):
            validate_creator_workspace(self.workspace)

    def test_workspace_rubric_with_foreign_creator_fails(self):
        rubric_path = self.workspace / "production-rubric.json"
        rubric = json.loads(rubric_path.read_text())
        rubric["creator_profile_id"] = "creator_other"
        rubric_path.write_text(json.dumps(rubric, indent=2) + "\n")
        with self.assertRaisesRegex(ValidationError, "does not match the owning"):
            validate_creator_workspace(self.workspace)

    def test_minted_from_event_id_must_resolve(self):
        rubric_path = self.workspace / "production-rubric.json"
        rubric = json.loads(rubric_path.read_text())
        rubric["criteria"].append(
            {
                "criterion_id": "creator.test.from_event",
                "statement": "Minted from a ledger event.",
                "status": "minted",
                "origin": "distillation",
                "minted_on": "2026-07-06",
                "minted_from_event_id": "event_luna_fit_777",
            }
        )
        rubric_path.write_text(json.dumps(rubric, indent=2) + "\n")
        with self.assertRaisesRegex(ValidationError, "does not resolve to a ledger event"):
            validate_creator_workspace(self.workspace)
        self.append_ledger_line(
            make_event(
                event_id="event_luna_fit_777",
                event_type="rejection",
                recurrence_key="vibe.cluster.framing",
                criterion_id=None,
                unclassified=True,
            )
        )
        validate_creator_workspace(self.workspace)

    def test_blocking_adr_must_resolve_to_a_file(self):
        # Batch-1 review (Medium): the pairing rule alone let a hand-edited
        # rubric block on a nonexistent ADR.
        rubric_path = self.workspace / "production-rubric.json"
        rubric = json.loads(rubric_path.read_text())
        rubric["criteria"].append(
            {
                "criterion_id": "creator.test.ghost_blocking",
                "statement": "Blocks on a decision that was never recorded.",
                "status": "blocking",
                "origin": "distillation",
                "minted_on": "2026-07-06",
                "blocking_adr": "docs/adr/9999-not-a-real-decision.md",
            }
        )
        rubric_path.write_text(json.dumps(rubric, indent=2) + "\n")
        with self.assertRaisesRegex(ValidationError, "does not resolve to a file"):
            validate_creator_workspace(self.workspace)

    def test_multiline_message_fails_writer_and_at_rest(self):
        # Batch-1 review (Low): a multiline message is how a rejected draft
        # sneaks onto the durable ledger.
        with self.assertRaisesRegex(ValidationError, "must be one line"):
            log_incident(
                self.workspace,
                event_type="rejection",
                recurrence_key="gen.identity.consistent",
                criterion_id="gen.identity.consistent",
                message="Rejected draft:\nHere is the entire draft text...",
                source_id="create-production-plan",
            )
        self.append_ledger_line(make_event(message="line one\nline two"))
        with self.assertRaisesRegex(ValidationError, "must be one line"):
            validate_creator_workspace(self.workspace)

    def test_manifest_without_production_rubric_fails(self):
        # Batch-1 review (Medium): optional canonical_files.production_rubric
        # made the Rubric Ratchet skippable by omission.
        manifest_path = self.workspace / "creator-workspace.json"
        manifest = json.loads(manifest_path.read_text())
        del manifest["canonical_files"]["production_rubric"]
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        with self.assertRaisesRegex(ValidationError, "production_rubric"):
            validate_creator_workspace(self.workspace)

    def test_collect_criteria_unions_both_scopes(self):
        mint_criterion(
            self.workspace,
            criterion_id="creator.test.rule",
            statement="The draft follows the test rule.",
        )
        criteria = collect_criteria(self.workspace, scope=self.scope())
        self.assertIn("creator.test.rule", criteria)
        self.assertIn("gen.identity.consistent", criteria)


class ReflectionTriggerTests(WorkspaceScaffoldMixin, unittest.TestCase):
    def log_incidents(self, count, key="gen.prompt.churn", unclassified=False):
        for index in range(count):
            log_incident(
                self.workspace,
                event_type="rejection" if unclassified else "incident",
                recurrence_key=key if key else f"cluster.key_{index}",
                unclassified=unclassified,
                message=f"Friction sample {index}.",
                source_id="create-production-plan",
            )

    def write_reflection_run(self, run_id, event_ids, run_status="completed", **overrides):
        run = {
            "automation_run_id": run_id,
            "job_id": "job_reflection_luna_fit",
            "job_type": "reflection",
            "started_on": "2026-07-06T18:00:00",
            "completed_on": "2026-07-06T18:10:00",
            "run_status": run_status,
            "creator_profile_id": "creator_luna_fit",
            "material_update": True,
            "linked_research_run_ids": [],
            "event_ids": event_ids,
        }
        run.update(overrides)
        runs_dir = self.workspace / REFLECTION_RUNS_DIR_RELATIVE
        runs_dir.mkdir(parents=True, exist_ok=True)
        (runs_dir / f"{run_id}.json").write_text(json.dumps(run, indent=2) + "\n")
        return run

    def test_recurrence_threshold_fires_and_stays_advisory(self):
        self.log_incidents(3)
        result = validate_creator_workspace(self.workspace)
        fired = [w for w in result["warnings"] if "reflection due" in w]
        self.assertTrue(fired, result["warnings"])
        self.assertIn("gen.prompt.churn", fired[0])
        report = reflection_report(self.workspace)
        self.assertEqual(report["recurrence_counts"]["gen.prompt.churn"], 3)

    def test_under_threshold_stays_silent(self):
        self.log_incidents(2)
        result = validate_creator_workspace(self.workspace)
        self.assertFalse([w for w in result["warnings"] if "reflection due" in w])

    def test_claimed_events_do_not_count(self):
        self.log_incidents(3)
        self.write_reflection_run(
            "automation_run_luna_fit_r001",
            ["event_luna_fit_001", "event_luna_fit_002", "event_luna_fit_003"],
        )
        result = validate_creator_workspace(self.workspace)
        self.assertFalse([w for w in result["warnings"] if "reflection due" in w])
        report = reflection_report(self.workspace)
        self.assertEqual(report["unprocessed_count"], 0)
        self.assertEqual(report["claimed_count"], 3)

    def test_failed_runs_claim_nothing(self):
        self.log_incidents(3)
        self.write_reflection_run(
            "automation_run_luna_fit_r001",
            [],
            run_status="failed",
            last_error="reflection crashed mid-way",
        )
        result = validate_creator_workspace(self.workspace)
        self.assertTrue([w for w in result["warnings"] if "reflection due" in w])

    def test_failed_run_attesting_claims_fails_at_rest(self):
        # Batch-1 review (High): a failed run's event_ids used to skip both
        # the dangling and double-claim checks entirely.
        self.log_incidents(1)
        self.write_reflection_run(
            "automation_run_luna_fit_r001",
            ["event_luna_fit_001"],
            run_status="failed",
            last_error="crashed after partial work",
        )
        with self.assertRaisesRegex(ValidationError, "must attest event_ids"):
            validate_creator_workspace(self.workspace)

    def test_unprocessed_total_threshold_fires(self):
        self.log_incidents(10, key=None)
        report = reflection_report(self.workspace)
        self.assertEqual(report["unprocessed_count"], 10)
        self.assertTrue(
            [w for w in report["warnings"] if "10 unprocessed friction" in w]
        )

    def test_unclassified_gap_signal_fires(self):
        self.log_incidents(3, key=None, unclassified=True)
        report = reflection_report(self.workspace)
        self.assertEqual(report["unclassified_count"], 3)
        self.assertTrue([w for w in report["warnings"] if "rubric gap" in w])

    def test_workspace_thresholds_override_defaults(self):
        manifest_path = self.workspace / "creator-workspace.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["reflection_thresholds"] = {"recurrence_k": 2}
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        self.log_incidents(2)
        report = reflection_report(self.workspace)
        self.assertEqual(report["thresholds"]["recurrence_k"], 2)
        self.assertEqual(
            report["thresholds"]["unprocessed_n"],
            DEFAULT_REFLECTION_THRESHOLDS["unprocessed_n"],
        )
        self.assertTrue([w for w in report["warnings"] if "reflection due" in w])

    def test_dangling_claimed_event_fails_at_rest(self):
        self.log_incidents(1)
        self.write_reflection_run(
            "automation_run_luna_fit_r001", ["event_luna_fit_999"]
        )
        with self.assertRaisesRegex(ValidationError, "does not exist on the ledger"):
            validate_creator_workspace(self.workspace)

    def test_double_claimed_event_fails_at_rest(self):
        self.log_incidents(1)
        self.write_reflection_run("automation_run_luna_fit_r001", ["event_luna_fit_001"])
        self.write_reflection_run("automation_run_luna_fit_r002", ["event_luna_fit_001"])
        with self.assertRaisesRegex(ValidationError, "claimed by both"):
            validate_creator_workspace(self.workspace)

    def test_reflection_run_filename_must_match_id(self):
        self.log_incidents(1)
        run = self.write_reflection_run(
            "automation_run_luna_fit_r001", ["event_luna_fit_001"]
        )
        runs_dir = self.workspace / REFLECTION_RUNS_DIR_RELATIVE
        (runs_dir / "automation_run_luna_fit_r001.json").rename(
            runs_dir / "automation_run_luna_fit_wrong.json"
        )
        with self.assertRaisesRegex(ValidationError, "filename must match"):
            validate_creator_workspace(self.workspace)

    def test_reflection_run_wrong_job_type_fails(self):
        self.log_incidents(1)
        self.write_reflection_run(
            "automation_run_luna_fit_r001",
            ["event_luna_fit_001"],
            job_type="scheduled_research",
        )
        with self.assertRaisesRegex(ValidationError, "must have job_type"):
            validate_creator_workspace(self.workspace)

    def test_reflection_run_foreign_creator_fails(self):
        self.log_incidents(1)
        self.write_reflection_run(
            "automation_run_luna_fit_r001",
            ["event_luna_fit_001"],
            creator_profile_id="creator_other",
        )
        with self.assertRaisesRegex(ValidationError, "does not match the owning"):
            validate_creator_workspace(self.workspace)


class ImprovementClaimTests(WorkspaceScaffoldMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        claims_tmp = tempfile.TemporaryDirectory()
        self.addCleanup(claims_tmp.cleanup)
        self.claims_dir = Path(claims_tmp.name) / "improvement-claims"
        self.workspace_root = self.workspace.parent

    def make_claim(self, **overrides):
        claim = {
            "claim_id": "claim_test_001",
            "created_on": "2026-07-06",
            "target_skill": "create-production-plan",
            "criterion_id": "gen.identity.consistent",
            "creator_slug": "luna-fit",
            "baseline": {
                "window_description": "Last 3 attempts",
                "violation_count": 3,
            },
            "expectation": {
                "window_description": "Next 3 attempts",
                "max_violations": 0,
            },
            "evidence_event_ids": ["event_luna_fit_001"],
            "status": "open",
        }
        claim.update(overrides)
        return {key: value for key, value in claim.items() if value is not None}

    def write_claim_file(self, claim):
        path = self.workspace_root / f"{claim['claim_id']}-draft.json"
        path.write_text(json.dumps(claim, indent=2) + "\n")
        return path

    def record(self, claim):
        from influencer_os.claims import record_claim

        return record_claim(
            self.write_claim_file(claim),
            workspace_root=self.workspace_root,
            claims_dir=self.claims_dir,
        )

    def check(self):
        from influencer_os.claims import check_claims

        return check_claims(
            workspace_root=self.workspace_root, claims_dir=self.claims_dir
        )

    def log_violation(self, event_id=None):
        log_incident(
            self.workspace,
            event_type="rejection",
            recurrence_key="gen.identity.consistent",
            criterion_id="gen.identity.consistent",
            message="Identity drift again.",
            source_id="create-production-plan",
            event_id=event_id,
        )

    def test_record_and_confirm_lifecycle(self):
        self.log_violation("event_luna_fit_001")
        self.record(self.make_claim())
        report = self.check()[0]
        self.assertEqual(report["resolution"], "resolved")
        self.assertEqual(report["violations_since"], 0)
        self.assertEqual(report["suggestion"], "confirmed")

    def test_refuted_when_violations_exceed_ceiling(self):
        self.log_violation("event_luna_fit_001")
        self.record(self.make_claim())
        self.log_violation()
        report = self.check()[0]
        self.assertEqual(report["violations_since"], 1)
        self.assertEqual(report["suggestion"], "refuted")

    def test_writer_fails_on_dangling_evidence(self):
        with self.assertRaisesRegex(ValidationError, "do not resolve to"):
            self.record(self.make_claim(evidence_event_ids=["event_luna_fit_777"]))

    def test_writer_fails_on_unknown_criterion(self):
        self.log_violation("event_luna_fit_001")
        with self.assertRaisesRegex(ValidationError, "does not resolve against"):
            self.record(self.make_claim(criterion_id="ghost.rule"))

    def test_writer_fails_on_missing_workspace(self):
        self.log_violation("event_luna_fit_001")
        with self.assertRaises(FileNotFoundError):
            self.record(self.make_claim(creator_slug="nobody-here"))

    def test_writer_refuses_overwrite_and_dangling_supersedes(self):
        self.log_violation("event_luna_fit_001")
        self.record(self.make_claim())
        with self.assertRaises(FileExistsError):
            self.record(self.make_claim())
        with self.assertRaisesRegex(ValidationError, "supersedes_claim_id"):
            self.record(
                self.make_claim(
                    claim_id="claim_test_002",
                    supersedes_claim_id="claim_test_777",
                )
            )

    def test_target_skill_must_exist_on_disk(self):
        self.log_violation("event_luna_fit_001")
        with self.assertRaisesRegex(ValidationError, "does not resolve to a skill"):
            self.record(self.make_claim(target_skill="not-a-real-skill"))

    def test_missing_workspace_degrades_to_report(self):
        from influencer_os.claims import load_claims

        self.log_violation("event_luna_fit_001")
        self.record(self.make_claim())
        shutil.rmtree(self.workspace)
        report = self.check()[0]
        self.assertEqual(report["resolution"], "workspace_missing")
        self.assertIsNone(report["suggestion"])
        self.assertIn("claim_test_001", load_claims(self.claims_dir))

    def test_closed_claim_semantics(self):
        with self.assertRaisesRegex(ValidationError, "require"):
            validate_record("improvement-claim", self.make_claim(status="refuted"))
        with self.assertRaisesRegex(ValidationError, "must not carry"):
            validate_record(
                "improvement-claim",
                self.make_claim(closed_on="2026-07-07", closed_by="user"),
            )
        validate_record(
            "improvement-claim",
            self.make_claim(
                status="confirmed", closed_on="2026-07-07", closed_by="user"
            ),
        )

    def test_filename_must_match_claim_id(self):
        from influencer_os.claims import load_claims

        self.claims_dir.mkdir(parents=True)
        claim = self.make_claim()
        (self.claims_dir / "claim_wrong_name.json").write_text(
            json.dumps(claim, indent=2) + "\n"
        )
        with self.assertRaisesRegex(ValidationError, "filename must match"):
            load_claims(self.claims_dir)


if __name__ == "__main__":
    unittest.main()
