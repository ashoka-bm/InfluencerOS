"""Improvement claims (ADR 0025, D5): falsifiable statements attached to
distilled skill/routine updates. Violation counts are computed mechanically
from the friction ledger; a human closes each claim. Claims are OS-scope
records under context/improvement-claims/ that cite creator-workspace
evidence, so full resolution runs only where the named workspace exists —
writers fail closed, the at-rest check degrades to a warning when the
workspace is absent (wiped fixtures, CI)."""

import json
from pathlib import Path

from influencer_os.creator_workspaces import DEFAULT_CREATOR_WORKSPACE_ROOT
from influencer_os.rubric import EVENTS_LEDGER_RELATIVE, collect_criteria
from influencer_os.validation import (
    ROOT,
    ValidationError,
    load_json,
    validate_record,
)

CLAIMS_DIR = ROOT / "context" / "improvement-claims"


def load_claims(claims_dir=CLAIMS_DIR):
    """Load and validate every claim: schema + semantics, filename == id,
    target_skill on disk, and supersedes chains resolving within the set."""
    claims_dir = Path(claims_dir)
    claims = {}
    if not claims_dir.exists():
        return claims
    for path in sorted(claims_dir.glob("*.json")):
        claim = load_json(path)
        try:
            validate_record("improvement-claim", claim)
        except ValidationError as exc:
            raise ValidationError(f"{path}: {exc}") from None
        if claim["claim_id"] != path.stem:
            raise ValidationError(
                f"{path}: filename must match claim_id ({claim['claim_id']!r})"
            )
        _check_target_skill(claim, path)
        claims[claim["claim_id"]] = claim
    for claim in claims.values():
        superseded = claim.get("supersedes_claim_id")
        if superseded is not None and superseded not in claims:
            raise ValidationError(
                f"claim {claim['claim_id']}: supersedes_claim_id "
                f"{superseded!r} does not resolve to a recorded claim"
            )
    return claims


def _check_target_skill(claim, context):
    """Shared by the writer and the at-rest load: a claim must target a
    skill that exists on disk."""
    skill_path = ROOT / "skills" / claim["target_skill"] / "SKILL.md"
    if not skill_path.is_file():
        raise ValidationError(
            f"{context}: target_skill {claim['target_skill']!r} does not "
            "resolve to a skill on disk"
        )


def _read_ledger_records(workspace_dir):
    ledger_path = Path(workspace_dir) / EVENTS_LEDGER_RELATIVE
    records = []
    if not ledger_path.exists():
        return records
    for line in ledger_path.read_text().split("\n"):
        if line.strip():
            records.append(json.loads(line))
    return records


def count_violations(claim, workspace_dir):
    """Violations since the claim: friction events citing the claim's
    criterion, dated on or after created_on, excluding the baseline evidence
    events the claim was distilled from. ISO strings compare lexically."""
    return sum(
        1
        for record in _read_ledger_records(workspace_dir)
        if record.get("criterion_id") == claim["criterion_id"]
        and record["event_id"] not in claim["evidence_event_ids"]
        and record["occurred_on"][:10] >= claim["created_on"]
    )


def _resolve_claim_against_workspace(claim, workspace_dir, context):
    ledger_ids = {record["event_id"] for record in _read_ledger_records(workspace_dir)}
    dangling = sorted(set(claim["evidence_event_ids"]) - ledger_ids)
    if dangling:
        raise ValidationError(
            f"{context}: evidence_event_ids {dangling} do not resolve to "
            f"ledger events in {workspace_dir}"
        )
    criteria = collect_criteria(workspace_dir)
    if claim["criterion_id"] not in criteria:
        raise ValidationError(
            f"{context}: criterion {claim['criterion_id']!r} does not resolve "
            "against the OS or creator rubric"
        )


def record_claim(claim_file, workspace_root=DEFAULT_CREATOR_WORKSPACE_ROOT, claims_dir=CLAIMS_DIR):
    """Writer: validate, fully resolve (writers always fail closed), and
    place the claim at context/improvement-claims/<claim_id>.json."""
    claim = load_json(claim_file)
    validate_record("improvement-claim", claim)
    _check_target_skill(claim, f"claim {claim['claim_id']}")
    workspace_dir = Path(workspace_root) / claim["creator_slug"]
    if not workspace_dir.exists():
        raise FileNotFoundError(
            f"Creator workspace for claim evidence does not exist: {workspace_dir}"
        )
    _resolve_claim_against_workspace(claim, workspace_dir, f"claim {claim['claim_id']}")

    existing = load_claims(claims_dir)
    superseded = claim.get("supersedes_claim_id")
    if superseded is not None and superseded not in existing:
        raise ValidationError(
            f"claim {claim['claim_id']}: supersedes_claim_id {superseded!r} "
            "does not resolve to a recorded claim"
        )

    claims_dir = Path(claims_dir)
    claims_dir.mkdir(parents=True, exist_ok=True)
    destination = claims_dir / f"{claim['claim_id']}.json"
    if destination.exists():
        raise FileExistsError(f"Claim already recorded: {destination}")
    destination.write_text(json.dumps(claim, indent=2, allow_nan=False) + "\n")
    return {"claim_id": claim["claim_id"], "claim_path": str(destination)}


def check_claims(workspace_root=DEFAULT_CREATOR_WORKSPACE_ROOT, claims_dir=CLAIMS_DIR):
    """Report each claim's mechanically computed status suggestion. The
    human closes the claim (D5) — this check never mutates. A claim whose
    workspace is absent reports resolution 'workspace_missing' instead of
    failing: claims are durable, fixture evidence is disposable."""
    reports = []
    for claim in load_claims(claims_dir).values():
        workspace_dir = Path(workspace_root) / claim["creator_slug"]
        report = {
            "claim_id": claim["claim_id"],
            "status": claim["status"],
            "target_skill": claim["target_skill"],
            "criterion_id": claim["criterion_id"],
            "max_violations": claim["expectation"]["max_violations"],
        }
        if not workspace_dir.exists():
            report["resolution"] = "workspace_missing"
            report["violations_since"] = None
            report["suggestion"] = None
        else:
            _resolve_claim_against_workspace(
                claim, workspace_dir, f"claim {claim['claim_id']}"
            )
            violations = count_violations(claim, workspace_dir)
            report["resolution"] = "resolved"
            report["violations_since"] = violations
            report["suggestion"] = (
                "confirmed"
                if violations <= claim["expectation"]["max_violations"]
                else "refuted"
            )
        reports.append(report)
    return reports
