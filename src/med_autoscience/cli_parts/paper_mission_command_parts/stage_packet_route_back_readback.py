from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.cli_parts.paper_mission_command_parts.common import (
    _mapping,
    _optional_text,
)


def _preferred_terminal_stage_attempt_ids(
    readback: Mapping[str, Any],
) -> set[str]:
    stage_attempt_ids = set()
    for carrier_key in (
        "opl_runtime_carrier_readback",
        "current_opl_runtime_carrier_readback",
    ):
        terminal_closeout = _mapping(
            _mapping(readback.get(carrier_key)).get("terminal_closeout")
        )
        stage_attempt_id = _optional_text(terminal_closeout.get("stage_attempt_id"))
        if stage_attempt_id is not None and (
            carrier_key == "current_opl_runtime_carrier_readback"
            or _terminal_closeout_is_live_runtime_observed(terminal_closeout)
        ):
            stage_attempt_ids.add(stage_attempt_id)
    return stage_attempt_ids


def _terminal_closeout_is_live_runtime_observed(
    closeout: Mapping[str, Any],
) -> bool:
    closeout_ref = _optional_text(closeout.get("closeout_ref"))
    return (
        closeout_ref is not None
        and closeout_ref.startswith("opl://family-runtime/tasks/")
    ) or _optional_text(closeout.get("runtime_readback_source")) in {
        "opl_family_runtime_queue_inspect",
        "opl_family_runtime_queue_list",
    }


def _expected_stage_attempt_identity(readback: Mapping[str, Any]) -> dict[str, set[str]]:
    next_action = _mapping(readback.get("next_action"))
    domain_transition = _mapping(readback.get("domain_transition"))
    transition_work_unit = _mapping(domain_transition.get("next_work_unit"))
    stage_decision = _mapping(readback.get("stage_terminal_decision"))
    transaction = _mapping(readback.get("paper_mission_transaction"))
    return {
        "stage_ids": {
            value
            for value in (
                _optional_text(next_action.get("stage_id")),
                _optional_text(domain_transition.get("route_target")),
                _optional_text(transaction.get("stage_id")),
                _optional_text(stage_decision.get("target_stage_id")),
            )
            if value is not None
        },
        "work_unit_ids": {
            value
            for value in (
                _optional_text(next_action.get("work_unit_id")),
                _optional_text(transition_work_unit.get("unit_id")),
                _optional_text(transaction.get("work_unit_id")),
                _optional_text(stage_decision.get("next_work_unit")),
                _optional_text(stage_decision.get("target_work_unit_id")),
            )
            if value is not None
        },
    }


def _load_stage_packet_route_back_evidence(
    *,
    workspace_root: Path,
    packet: Mapping[str, Any],
) -> dict[str, Any]:
    ref = _optional_text(packet.get("route_back_evidence_ref"))
    if ref is None:
        return {}
    path = Path(ref).expanduser()
    if not path.is_absolute():
        path = workspace_root / path
    if not path.exists():
        return {}
    return _load_json_object(path)


def _stage_packet_route_stage_id(
    *,
    study_id: str,
    packet: Mapping[str, Any],
    route_back: Mapping[str, Any],
    stage_packet_ref: str | None,
) -> str | None:
    derived = _paper_mission_transaction_stage_id(
        stage_packet_ref,
        study_id=study_id,
    )
    packet_stage_id = _optional_text(packet.get("stage_id"))
    route_stage_id = _optional_text(route_back.get("stage_id"))
    route_work_unit_id = _optional_text(route_back.get("work_unit_id"))
    return (
        derived
        or (
            route_stage_id
            if packet_stage_id is not None
            and route_work_unit_id is not None
            and packet_stage_id == route_work_unit_id
            else None
        )
        or packet_stage_id
        or route_stage_id
    )


def _paper_mission_transaction_stage_id(
    transaction_ref: str | None,
    *,
    study_id: str,
) -> str | None:
    if transaction_ref is None:
        return None
    prefix = f"paper-mission-transaction::{study_id}::"
    suffix = "::paper-mission::"
    if not transaction_ref.startswith(prefix) or suffix not in transaction_ref:
        return None
    stage_segment = transaction_ref[len(prefix) : transaction_ref.index(suffix)]
    return stage_segment.split("::followthrough::", 1)[0] if stage_segment else None


def _stage_packet_transaction_priority(
    *,
    stage_packet_ref: str | None,
    current_transaction_ref: str | None,
    study_id: str,
) -> int:
    if stage_packet_ref is None or current_transaction_ref is None:
        return 0
    if stage_packet_ref == current_transaction_ref:
        return 1
    if stage_packet_ref.startswith(f"{current_transaction_ref}::followthrough::"):
        return 2
    if current_transaction_ref.startswith(f"{stage_packet_ref}::followthrough::"):
        return 1
    current_stage = _paper_mission_transaction_stage_id(
        current_transaction_ref, study_id=study_id
    )
    stage_packet_stage = _paper_mission_transaction_stage_id(
        stage_packet_ref, study_id=study_id
    )
    if current_stage is None or stage_packet_stage is None:
        return 0
    if stage_packet_stage.startswith(f"{current_stage}::followthrough::"):
        return 2
    if current_stage.startswith(f"{stage_packet_stage}::followthrough::"):
        return 1
    return 0


def _stage_packet_route_back_semantic_priority(
    *,
    packet: Mapping[str, Any],
    route_back: Mapping[str, Any],
) -> int:
    route_impact = _mapping(packet.get("route_impact"))
    priority = 0
    if _first_non_empty_text(
        packet.get("paper_facing_delta_ref"),
        route_impact.get("paper_facing_delta_ref"),
        route_back.get("paper_facing_delta_ref"),
    ) is not None:
        priority += 2
    if _first_non_empty_text(
        packet.get("progress_events_ref"),
        route_back.get("progress_events_ref"),
    ) is not None:
        priority += 1
    if _first_non_empty_text(
        route_impact.get("stage_log_summary"),
        route_impact.get("user_stage_log"),
        route_impact.get("human_stage_log"),
    ) is not None:
        priority += 1
    if _first_non_empty_text(
        route_back.get("owner_gate_verdict"),
        route_back.get("next_forced_paper_action"),
        route_back.get("source_readiness_checklist_ref"),
        route_back.get("remaining_blocker"),
    ) is not None:
        priority += 1
    if _mapping(route_back.get("source_evidence")):
        priority += 1
    return priority


def _first_non_empty_text(*values: object) -> str | None:
    for value in values:
        text = _optional_text(value)
        if text is not None:
            return text
    return None


def _stage_packet_opl_runtime_carrier_readback(
    *,
    packet: Mapping[str, Any],
    route_back: Mapping[str, Any],
    stage_attempt_id: str | None,
    stage_id: str | None,
    work_unit_id: str | None,
    provider_attempt_ref: str | None,
    closeout_ref: str,
) -> dict[str, Any]:
    closeout_receipt_status = (
        _optional_text(packet.get("closeout_receipt_status"))
        or "accepted_stage_attempt_closeout"
    )
    blocked_reason = (
        _optional_text(packet.get("blocked_reason"))
        or "paper_mission_stage_route_domain_gate_pending"
    )
    receipt_ref = provider_attempt_ref or closeout_ref
    receipt_evidence = {
        "receipt_kind": "opl_transition_receipt",
        "receipt_ref": receipt_ref,
        "runtime_closeout_ref": closeout_ref,
        "stage_attempt_ref": receipt_ref,
        "can_claim_paper_progress": False,
    }
    return {
        "surface_kind": "paper_mission_opl_runtime_carrier_readback",
        "schema_version": 1,
        "carrier_status": "opl_runtime_terminal_readback_observed",
        "runtime_readback_status": "terminal_closeout_observed",
        "dispatch_status": "terminal_closeout_observed",
        "domain_ready_verdict": "domain_gate_pending",
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
        "can_claim_provider_running": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_materialized": False,
        "request_carrier_preserved": True,
        "terminal_closeout": {
            "surface_kind": "stage_attempt_closeout_packet",
            "status": _optional_text(packet.get("status")) or "completed",
            "study_id": _optional_text(packet.get("study_id"))
            or _optional_text(route_back.get("study_id")),
            "stage_id": stage_id,
            "stage_attempt_id": stage_attempt_id,
            "work_unit_id": work_unit_id,
            "provider_attempt_ref": provider_attempt_ref,
            "blocked_reason": blocked_reason,
            "closeout_refs": [closeout_ref],
            "closeout_receipt_status": closeout_receipt_status,
            "provider_completion_is_domain_completion": False,
            "provider_completion_is_domain_ready": False,
            "domain_completion_claimed": False,
            "domain_ready_claimed": False,
        },
        "opl_transition_receipt": {
            "surface_kind": "opl_transition_receipt",
            "receipt_status": "terminal_closeout_observed",
            "role": "transport_receipt_only",
            "stage_attempt_id": stage_attempt_id,
            "stage_attempt_ref": receipt_ref,
            "closeout_receipt_status": closeout_receipt_status,
            "blocked_reason": blocked_reason,
            "can_claim_paper_progress": False,
        },
        "receipt_evidence": receipt_evidence,
        "mas_receipt_consumption": {
            "surface_kind": "mas_receipt_consumption_projection",
            "status": "requires_mas_owner_consumption",
            "next_legal_action": (
                "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
            ),
            "forbidden_next_action": "synonymous_route_back_redrive",
            "receipt_ref": receipt_ref,
            "runtime_closeout_ref": closeout_ref,
            "durable_stop_allowed": False,
        },
    }


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"Expected JSON object at {path}")
    return dict(payload)
