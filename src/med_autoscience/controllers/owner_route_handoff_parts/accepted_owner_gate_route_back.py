from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.default_executor_action_policy import (
    SUPPORTED_ACTION_TYPES,
    request_owner_for_action_type,
)


def accepted_owner_gate_route_back_action(
    *,
    current_progress: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
) -> Mapping[str, Any]:
    recovery = _mapping(current_progress.get("paper_recovery_state"))
    if _text(recovery.get("phase")) != "owner_action_ready":
        return {}
    next_safe_action = _mapping(recovery.get("next_safe_action"))
    if _text(next_safe_action.get("kind")) != "route_back_to_owner_or_repair_materialization":
        return {}
    accepted = _mapping(next_safe_action.get("accepted_owner_gate_decision"))
    if _text(accepted.get("decision")) != "route_back_to_mas_packet_materialization_bug":
        return {}
    action_type = _text(accepted.get("action_type"))
    work_unit_id = _text(accepted.get("work_unit_id"))
    work_unit_fingerprint = _text(accepted.get("work_unit_fingerprint"))
    if action_type not in SUPPORTED_ACTION_TYPES or work_unit_id is None or work_unit_fingerprint is None:
        return {}
    if _text(current_work_unit.get("status")) != "typed_blocker":
        return {}
    typed_blocker = _current_typed_blocker(
        current_work_unit=current_work_unit,
        current_execution_envelope=_mapping(current_progress.get("current_execution_envelope")),
    )
    if _typed_blocker_identity(typed_blocker) != "stage_packet_not_current_selected_dispatch":
        return {}
    if _text(current_work_unit.get("action_type")) not in {None, action_type}:
        return {}
    if _text(current_work_unit.get("work_unit_id")) not in {None, work_unit_id}:
        return {}
    current_fingerprint = _text(current_work_unit.get("work_unit_fingerprint")) or _text(
        current_work_unit.get("action_fingerprint")
    )
    if current_fingerprint not in {None, work_unit_fingerprint}:
        return {}
    owner = request_owner_for_action_type(action_type)
    currentness_basis = {
        "truth_epoch": work_unit_fingerprint,
        "runtime_health_epoch": work_unit_fingerprint,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
    }
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": _text(current_progress.get("study_id")),
        "quest_id": _text(current_progress.get("quest_id")) or _text(current_progress.get("study_id")),
        "truth_epoch": work_unit_fingerprint,
        "runtime_health_epoch": work_unit_fingerprint,
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_fingerprint": work_unit_fingerprint,
        "current_owner": "mas_controller",
        "next_owner": owner,
        "owner_reason": work_unit_id,
        "active_run_id": _text(current_progress.get("active_run_id")),
        "allowed_actions": [action_type],
        "source_refs": {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "source_surface": "paper_recovery_state.accepted_owner_gate_decision",
            "source_ref": _text(accepted.get("route_back_evidence_ref")),
            "owner_route_currentness_basis": dict(currentness_basis),
        },
        "idempotency_key": (
            f"paper-recovery-owner-gate::{_text(current_progress.get('study_id'))}::"
            f"{action_type}::{work_unit_fingerprint}"
        ),
    }
    return {
        "surface_kind": "current_executable_owner_action",
        "status": "ready",
        "source": "paper_recovery_state.accepted_owner_gate_decision",
        "authority": "paper_recovery_state.accepted_owner_gate_decision",
        "next_owner": owner,
        "action_type": action_type,
        "allowed_actions": [action_type],
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": work_unit_fingerprint,
        "source_fingerprint": work_unit_fingerprint,
        "source_ref": _text(accepted.get("route_back_evidence_ref")),
        "provider_admission_allowed": False,
        "provider_admission_requires_opl_runtime_result": True,
        "owner_route": owner_route,
        "owner_route_currentness_basis": currentness_basis,
    }


def _current_typed_blocker(
    *,
    current_work_unit: Mapping[str, Any],
    current_execution_envelope: Mapping[str, Any],
) -> Mapping[str, Any]:
    work_unit_state = _mapping(current_work_unit.get("state"))
    return (
        _mapping(work_unit_state.get("typed_blocker"))
        or _mapping(current_work_unit.get("typed_blocker"))
        or _mapping(current_execution_envelope.get("typed_blocker"))
    )


def _typed_blocker_identity(typed_blocker: Mapping[str, Any]) -> str | None:
    return (
        _text(typed_blocker.get("blocker_id"))
        or _text(typed_blocker.get("blocker_type"))
        or _text(typed_blocker.get("reason"))
        or _text(typed_blocker.get("blocked_reason"))
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    value_text = str(value or "").strip()
    return value_text or None


__all__ = ["accepted_owner_gate_route_back_action"]
