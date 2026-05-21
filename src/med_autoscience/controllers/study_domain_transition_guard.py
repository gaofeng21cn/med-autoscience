from __future__ import annotations

from collections.abc import Mapping
from typing import Any


AUTO_REDRIVE_BLOCKED_REASON = "domain_transition_auto_redrive_blocked"
CURRENT_ROUTE_MISSING_REASON = "domain_transition_current_controller_route_missing"
TERMINAL_OR_HANDOFF_DECISION_TYPES = frozenset(
    {
        "completion_receipt_consumed",
        "delivered_package_handoff",
        "fail_closed",
        "human_gate",
        "memory_writeback_receipt_consumed",
        "stop_loss",
        "owner_apply_receipt_consumed",
        "artifact_delta_live_apply",
    }
)
RUNTIME_REDRIVE_DECISION_TYPES = frozenset(
    {
        "ai_reviewer_re_eval",
        "bundle_stage_finalize",
        "publication_gate_blocker",
        "route_back_same_line",
    }
)
ACTION_TYPE_BY_DECISION_TYPE = {
    "ai_reviewer_re_eval": "return_to_ai_reviewer_workflow",
    "bundle_stage_finalize": "runtime_platform_repair",
    "publication_gate_blocker": "publication_gate_specificity_required",
    "route_back_same_line": "run_quality_repair_batch",
}
REASON_BY_DECISION_TYPE = {
    "ai_reviewer_re_eval": "domain_transition_ai_reviewer_re_eval",
    "bundle_stage_finalize": "domain_transition_bundle_stage_finalize",
    "publication_gate_blocker": "domain_transition_publication_gate_blocker",
    "route_back_same_line": "quest_waiting_opl_runtime_owner_route",
}


def transition_from_status(status: Mapping[str, Any]) -> dict[str, Any]:
    return _mapping(status.get("domain_transition"))


def decision_type(status: Mapping[str, Any]) -> str | None:
    return transition_decision_type(transition_from_status(status))


def transition_decision_type(transition: Mapping[str, Any]) -> str | None:
    return _text(transition.get("decision_type"))


def blocks_auto_redrive(status: Mapping[str, Any]) -> bool:
    decision = decision_type(status)
    return decision in TERMINAL_OR_HANDOFF_DECISION_TYPES


def redrive_block_payload(status: Mapping[str, Any]) -> dict[str, Any] | None:
    transition = transition_from_status(status)
    decision = transition_decision_type(transition)
    if decision not in TERMINAL_OR_HANDOFF_DECISION_TYPES:
        return None
    next_work_unit = _mapping(transition.get("next_work_unit"))
    typed_blocker = _mapping(transition.get("typed_blocker"))
    return {
        "dispatch_status": "blocked",
        "reason": AUTO_REDRIVE_BLOCKED_REASON,
        "domain_transition_decision_type": decision,
        "domain_transition_route_target": _text(transition.get("route_target")),
        "domain_transition_controller_action": _text(transition.get("controller_action")),
        "domain_transition_next_work_unit_id": _text(next_work_unit.get("unit_id")),
        "domain_transition_typed_blocker_id": _text(typed_blocker.get("blocker_id")),
    }


def runtime_redrive_decision_type(status: Mapping[str, Any]) -> str | None:
    decision = decision_type(status)
    return decision if decision in RUNTIME_REDRIVE_DECISION_TYPES else None


def supported_action_type(status: Mapping[str, Any]) -> str | None:
    decision = decision_type(status)
    if decision is None:
        return None
    return ACTION_TYPE_BY_DECISION_TYPE.get(decision)


def reason(status: Mapping[str, Any]) -> str | None:
    decision = decision_type(status)
    if decision is None:
        return None
    return REASON_BY_DECISION_TYPE.get(decision)


def next_work_unit_id(status: Mapping[str, Any]) -> str | None:
    next_work_unit = _mapping(transition_from_status(status).get("next_work_unit"))
    return _text(next_work_unit.get("unit_id"))


def owner(status: Mapping[str, Any]) -> str | None:
    return _text(transition_from_status(status).get("owner"))


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "AUTO_REDRIVE_BLOCKED_REASON",
    "CURRENT_ROUTE_MISSING_REASON",
    "ACTION_TYPE_BY_DECISION_TYPE",
    "REASON_BY_DECISION_TYPE",
    "RUNTIME_REDRIVE_DECISION_TYPES",
    "TERMINAL_OR_HANDOFF_DECISION_TYPES",
    "blocks_auto_redrive",
    "decision_type",
    "next_work_unit_id",
    "owner",
    "reason",
    "redrive_block_payload",
    "runtime_redrive_decision_type",
    "supported_action_type",
    "transition_decision_type",
    "transition_from_status",
]
