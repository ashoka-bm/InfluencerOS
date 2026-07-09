"""Generation dispatch seam (ADR 0023, Phase 3 slices 1-2).

``dispatch_generation`` is the ONLY public entry point that can reach a
generation adapter, and it requires an approved GenerationApprovalRecord id
as a positional argument — the no-approval-no-call rule enforced by shape.
Adapters live in a private table and must never be called directly.
"""

import datetime
import hashlib
import json
import os
from pathlib import Path

from influencer_os import generation as generation_records
from influencer_os.connectors import env
from influencer_os.json_io import write_json_atomic
from influencer_os.providers.registry import get_provider, provider_status
from influencer_os.validation import ValidationError, load_json, validate_record


class GenerationDispatchError(Exception):
    """Dispatch refused: missing/unusable approval, kill switch, or provider."""


def _mock_generate(request, assets_dir, approval_record):
    """Deterministic test double (ADR 0023 Decision 3): writes fixture bytes
    derived from the request, returns echo metadata. Never networks, never
    costs."""
    asset_id = request["asset_id"]
    filename = request.get("filename") or f"{asset_id}.bin"
    artifact_path = generation_records.contained_generation_artifact_path(
        assets_dir, filename, asset_id, error_class=GenerationDispatchError
    )
    seed = json.dumps(
        {
            "asset_id": asset_id,
            "asset_kind": request["asset_kind"],
            "prompt_ref": request.get("prompt_ref"),
            "approval": approval_record["generation_approval_record_id"],
        },
        sort_keys=True,
    )
    artifact_path.write_bytes(
        b"mock-generated-artifact\n" + hashlib.sha256(seed.encode()).hexdigest().encode() + b"\n"
    )
    return {
        "provider_id": "mock",
        "model": "mock-1",
        "params_hash": hashlib.sha256(seed.encode()).hexdigest(),
        "artifact_path": artifact_path,
    }


# Private adapter table: provider_id -> callable. The dispatch seam is the
# only caller; tests probe that no other public surface reaches an adapter.
_ADAPTERS = {
    "mock": _mock_generate,
}


def _approval_records_dir(project_dir):
    return Path(project_dir) / "generation" / "approval-records"


def _load_approval_record(project_dir, approval_record_id):
    record_path = _approval_records_dir(project_dir) / f"{approval_record_id}.json"
    if not record_path.exists():
        raise GenerationDispatchError(
            f"no approval record {approval_record_id!r} under "
            "generation/approval-records/; a generation call requires an "
            "approved GenerationApprovalRecord (ADR 0023) — record one with "
            "record-generation-approval"
        )
    record = load_json(record_path)
    try:
        validate_record("generation-approval-record", record)
    except ValidationError as exc:
        raise GenerationDispatchError(
            f"approval record {approval_record_id!r} does not validate: {exc}"
        ) from exc
    if record["generation_approval_record_id"] != approval_record_id:
        raise GenerationDispatchError(
            f"approval record file {record_path.name} carries id "
            f"{record['generation_approval_record_id']!r}"
        )
    return record_path, record


def dispatch_generation(project_dir, approval_record_id, config=None):
    """Execute the approved generation described by an approval record.

    Refuses (GenerationDispatchError) when the kill switch is on, the record
    is missing, invalid, not `approved`, already consumed, or cancelled, or
    the provider is unknown/unavailable. On success runs the provider adapter
    once per requested asset, marks the record `executed` with
    `resulting_asset_ids`, and returns the per-asset call metadata.
    """
    project_dir = Path(project_dir)
    config = config if config is not None else env.get_config()
    # The kill switch is a hard stop read from the real environment on every
    # dispatch — an injected config can restrict further but never re-enable
    # (batch-1 review finding).
    if env.paid_connectors_disabled(config) or env.paid_connectors_disabled(env.get_config()):
        raise GenerationDispatchError(
            "generation dispatch is disabled by "
            "INFLUENCER_OS_DISABLE_PAID_CONNECTORS (kill switch); an approved "
            "record does not override a hard stop"
        )

    record_path, record = _load_approval_record(project_dir, approval_record_id)

    # Bind the record to the project it sits in before trusting it (batch-1
    # review finding): a hand-written approved record targeting a different
    # project, creator, premature status, or dangling plan refs must refuse
    # exactly like the writer would have.
    project = generation_records.validate_approval_record_binding(
        project_dir, record, error_class=GenerationDispatchError
    )

    status = record["status"]
    if status == "draft":
        raise GenerationDispatchError(
            f"approval record {approval_record_id!r} is a draft; the human "
            "approval statement has not been recorded"
        )
    if status == "cancelled":
        raise GenerationDispatchError(
            f"approval record {approval_record_id!r} is cancelled"
        )
    if status == "executing":
        raise GenerationDispatchError(
            f"approval record {approval_record_id!r} is mid-execution or a "
            "dispatch crashed; investigate the assets on disk and record a "
            "new approval — an in-flight record is never re-run"
        )
    if status == "executed":
        raise GenerationDispatchError(
            f"approval record {approval_record_id!r} is already consumed; "
            "re-generation requires a new approval record (ADR 0023 "
            "Decision 2)"
        )
    if status != "approved":
        raise GenerationDispatchError(
            f"approval record {approval_record_id!r} has status {status!r}"
        )

    provider_id = record["provider_id"]
    try:
        get_provider(provider_id)
    except KeyError as exc:
        raise GenerationDispatchError(str(exc)) from exc
    availability = {
        row["provider_id"]: row for row in provider_status(config)
    }[provider_id]
    if not availability["available"]:
        raise GenerationDispatchError(
            f"provider {provider_id!r} is unavailable: {availability['reason']}"
        )
    adapter = _ADAPTERS.get(provider_id)
    if adapter is None:
        raise GenerationDispatchError(
            f"provider {provider_id!r} has no installed adapter; the first "
            "real adapter is an operator-approved batch (ADR 0023 Decision 3)"
        )

    requested = record["requested_assets"]
    if record["scope"] == "batch" and len(requested) > record["max_calls"]:
        raise GenerationDispatchError(
            f"approval record {approval_record_id!r} requests "
            f"{len(requested)} assets but its batch cap is "
            f"{record['max_calls']}"
        )

    assets_dir = generation_records.ensure_generation_assets_dir(
        project_dir, error_class=GenerationDispatchError
    )

    # Two-phase consumption (batch-1 review finding): flip the record to
    # `executing` BEFORE any adapter call so a crash or concurrent dispatch
    # can never replay calls against the same approval — a leftover
    # `executing` record refuses dispatch and demands a fresh approval.
    # The approved -> executing transition is an exclusive compare-and-swap
    # (batch-2 review finding): an O_EXCL lock file serializes the
    # read-verify-write window so two concurrent dispatches cannot both
    # observe `approved`.
    lock_path = record_path.with_suffix(".lock")
    try:
        lock_descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise GenerationDispatchError(
            f"approval record {approval_record_id!r} is locked by another "
            "dispatch (or a crashed one left the lock); investigate before "
            "recording a new approval"
        ) from None
    try:
        os.close(lock_descriptor)
        # Re-read under the lock: the record must still be approved.
        _, record = _load_approval_record(project_dir, approval_record_id)
        if record["status"] != "approved":
            raise GenerationDispatchError(
                f"approval record {approval_record_id!r} changed status to "
                f"{record['status']!r} before dispatch could consume it"
            )
        record["status"] = "executing"
        write_json_atomic(record_path, record)
    finally:
        lock_path.unlink(missing_ok=True)

    calls = []
    for request in requested:
        requested_at = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        metadata = adapter(request, assets_dir, record)
        completed_at = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        calls.append(
            {
                **metadata,
                "asset_id": request["asset_id"],
                "request": request,
                "requested_at": requested_at,
                "completed_at": completed_at,
            }
        )

    # Provenance ledger rows before consumption (ADR 0023 Decision 4): if
    # the append fails, the record stays `executing` — an honest crash state
    # that refuses re-dispatch — instead of executed-without-provenance.
    generation_records.record_generated_calls(
        project_dir, project, approval_record_id, calls
    )

    # Phase two: consume the record (single-use by construction, Decision 2).
    record["status"] = "executed"
    record["executed_at"] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    record["resulting_asset_ids"] = [call["asset_id"] for call in calls]
    write_json_atomic(record_path, record)
    return calls
