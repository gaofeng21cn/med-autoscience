from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.paper_mission_opl_carrier import paper_mission_opl_runtime_carrier
from med_autoscience.paper_mission_transaction import PaperMissionTransaction


PAPER_MISSION_CONSUMPTION_LEDGER_RELPATH = (
    Path("ops") / "medautoscience" / "paper_mission_consumption_ledger"
)


def latest_paper_mission_consumption_transaction_readback(
    *,
    workspace_root: Path,
    study_id: str,
) -> dict[str, Any] | None:
    ledger_root = (
        workspace_root.expanduser().resolve()
        / PAPER_MISSION_CONSUMPTION_LEDGER_RELPATH
    )
    if not ledger_root.exists():
        return None
    candidates: list[tuple[str, float, str, dict[str, Any]]] = []
    for consume_record_ref in ledger_root.glob(f"**/{study_id}/consume_record.json"):
        readback = _valid_consumption_transaction_readback(
            consume_record_ref=consume_record_ref,
            study_id=study_id,
        )
        if readback is None:
            continue
        try:
            mtime = consume_record_ref.stat().st_mtime
        except OSError:
            mtime = 0.0
        candidates.append(
            (
                _ledger_timestamp_key(consume_record_ref),
                mtime,
                str(consume_record_ref),
                readback,
            )
        )
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item[0], item[1], item[2]))[3]


def _valid_consumption_transaction_readback(
    *,
    consume_record_ref: Path,
    study_id: str,
) -> dict[str, Any] | None:
    consume_record = _read_json_object(consume_record_ref)
    if not _valid_consume_record(consume_record, study_id=study_id):
        return None
    ledger_dir = consume_record_ref.parent
    consume_readback = _read_json_object(ledger_dir / "consume_readback.json")
    transaction = _mapping(consume_readback.get("paper_mission_transaction"))
    if not transaction:
        return None
    try:
        transaction = PaperMissionTransaction.from_payload(transaction).to_dict()
    except ValueError:
        return None
    if _text(transaction.get("study_id")) != study_id:
        return None
    expected_ref = _text(consume_record.get("paper_mission_transaction_ref"))
    if expected_ref and _text(transaction.get("transaction_id")) != expected_ref:
        return None
    stage_packet = _read_json_object(ledger_dir / "stage_terminal_decision.json")
    route_packet = _read_json_object(ledger_dir / "opl_route_command.json")
    handoff = _read_json_object(ledger_dir / "opl_route_handoff.json")
    if not _valid_route_handoff(handoff, study_id=study_id, transaction=transaction):
        return None
    stage_terminal_decision = _mapping(transaction.get("stage_terminal_decision"))
    opl_route_command = _mapping(transaction.get("opl_route_command"))
    carrier = _mapping(handoff.get("opl_runtime_carrier")) or paper_mission_opl_runtime_carrier(
        transaction
    )
    return {
        "surface_kind": "paper_mission_consumption_ledger_transaction_readback",
        "schema_version": 1,
        "source": "paper_mission_consumption_ledger",
        "source_ref": str(consume_record_ref),
        "ledger_root": str(ledger_dir),
        "study_id": study_id,
        "mission_id": _text(transaction.get("mission_id")),
        "candidate_ref": _text(consume_record.get("candidate_ref")),
        "candidate_id": _text(consume_record.get("candidate_id")),
        "consume_candidate_status": _consume_candidate_status(
            consume_record=consume_record,
            stage_terminal_decision=stage_terminal_decision,
        ),
        "selected_outcome": _text(consume_record.get("selected_outcome")),
        "route_handoff_status": _text(consume_record.get("route_handoff_status")),
        "paper_mission_transaction": transaction,
        "stage_terminal_decision": stage_terminal_decision,
        "opl_route_command": opl_route_command,
        "opl_runtime_carrier": carrier,
        "transaction_state": _text(
            stage_packet.get("transaction_state")
        )
        or _text(consume_record.get("status"))
        or _text(stage_terminal_decision.get("status"))
        or "not_materialized",
        "consume_record": consume_record,
        "consume_readback": consume_readback,
        "stage_terminal_decision_packet": stage_packet,
        "opl_route_command_packet": route_packet,
        "opl_route_handoff": {
            **handoff,
            "source_ref": str(ledger_dir / "opl_route_handoff.json"),
            "source_surface_kind": "mas_paper_mission_opl_route_handoff_record",
            "paper_mission_default_handoff_source": "paper_mission_consumption_ledger",
        },
        "authority_materialized": False,
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
    }


def _valid_consume_record(payload: Mapping[str, Any], *, study_id: str) -> bool:
    if payload.get("surface_kind") != "mas_paper_mission_candidate_consumption_record":
        return False
    if _text(payload.get("study_id")) != study_id:
        return False
    if payload.get("counts_as_stage_terminalizer_evidence") is not True:
        return False
    if payload.get("counts_as_opl_route_handoff_evidence") is not True:
        return False
    if _text(payload.get("route_handoff_status")) != "ready_for_opl_route_command":
        return False
    if not _text(payload.get("paper_mission_transaction_ref")):
        return False
    if not _text(payload.get("stage_terminal_decision_ref")):
        return False
    if not _text(payload.get("opl_route_command_ref")):
        return False
    if payload.get("authority_materialized") is True:
        return False
    if any(
        payload.get(flag) is True
        for flag in (
            "counts_as_paper_progress",
            "counts_as_runtime_truth",
            "can_claim_paper_progress",
            "can_claim_runtime_ready",
        )
    ):
        return False
    boundary = _mapping(payload.get("authority_boundary"))
    return not _has_forbidden_write_claim(payload, boundary)


def _valid_route_handoff(
    payload: Mapping[str, Any],
    *,
    study_id: str,
    transaction: Mapping[str, Any],
) -> bool:
    if payload.get("surface_kind") != "mas_paper_mission_opl_route_handoff_record":
        return False
    if _text(payload.get("study_id")) != study_id:
        return False
    if _text(payload.get("handoff_status")) != "ready_for_opl_route_command":
        return False
    if payload.get("can_submit_to_opl_runtime") is not True:
        return False
    if payload.get("transaction_materialized") is not True:
        return False
    if _text(payload.get("paper_mission_transaction_ref")) != _text(
        transaction.get("transaction_id")
    ):
        return False
    command_kind = _text(payload.get("route_command_kind")) or _text(
        _mapping(payload.get("opl_route_command")).get("command_kind")
    )
    if command_kind not in {"start_next_stage", "resume_stage", "route_back"}:
        return False
    if any(
        payload.get(flag) is True
        for flag in (
            "can_claim_opl_runtime_enqueued",
            "can_claim_opl_stage_run_created",
            "can_claim_provider_running",
            "can_claim_paper_progress",
            "can_claim_runtime_ready",
        )
    ):
        return False
    if _has_forbidden_write_claim(payload, _mapping(payload.get("authority_boundary"))):
        return False
    return True


def _has_forbidden_write_claim(
    payload: Mapping[str, Any],
    authority: Mapping[str, Any],
) -> bool:
    forbidden_flags = (
        "writes_authority_surface",
        "writes_publication_eval",
        "writes_controller_decision",
        "can_write_owner_receipt",
        "can_write_typed_blocker",
        "can_write_human_gate",
        "can_write_current_package",
        "can_write_paper_body",
        "can_write_runtime_queue",
        "can_write_opl_outbox",
        "can_write_opl_event",
        "can_write_opl_stage_run",
        "can_write_provider_attempt",
        "can_write_publication_eval",
        "can_write_controller_decisions",
        "can_write_runtime_queue_or_provider_attempt",
        "can_authorize_publication_ready",
        "can_authorize_quality_verdict",
        "can_authorize_provider_admission",
        "writes_owner_receipt",
        "writes_typed_blocker",
        "writes_human_gate",
        "writes_current_package",
        "writes_paper_body",
        "writes_runtime_queue",
        "writes_opl_outbox",
        "writes_opl_event",
        "writes_opl_stage_run",
        "writes_provider_attempt",
        "writes_yang_authority",
    )
    return any(
        payload.get(flag) is True or authority.get(flag) is True
        for flag in forbidden_flags
    )


def _consume_candidate_status(
    *,
    consume_record: Mapping[str, Any],
    stage_terminal_decision: Mapping[str, Any],
) -> str:
    status = _text(stage_terminal_decision.get("status"))
    if status:
        return status
    selected = _text(consume_record.get("selected_outcome"))
    if selected == "accepted_candidate":
        return "accepted"
    if selected == "typed_blocker_required":
        return "typed_blocker"
    if selected == "human_gate_required":
        return "human_gate"
    return _text(consume_record.get("status")) or "not_consumed"


def _ledger_timestamp_key(path: Path) -> str:
    for part in reversed(path.parts):
        match = re.search(r"20\d{6}T[0-9A-Za-z_-]+", part)
        if match:
            return match.group(0)
    return ""


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = ["latest_paper_mission_consumption_transaction_readback"]
