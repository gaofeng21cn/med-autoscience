from __future__ import annotations

from typing import Any


STARTUP_FRESHNESS_CONTINUATION_REASONS = frozenset({"current_package_freshness_required"})
BUNDLE_STAGE_CURRENT_REQUIRED_ACTIONS = frozenset({"continue_bundle_stage", "complete_bundle_stage"})
FINALIZE_ROUTE_TARGETS = frozenset({"finalize"})
FINALIZE_WORK_UNIT_IDS = frozenset(
    {
        "submission_authority_sync_closure",
        "submission_minimal_refresh",
        "submission_delivery_sync_closure",
        "publication_gate_replay",
    }
)


def continuation_reason(payload: dict[str, Any]) -> str | None:
    continuation_state = payload.get("continuation_state")
    if isinstance(continuation_state, dict):
        reason = str(continuation_state.get("continuation_reason") or "").strip()
        if reason:
            return reason
    reason = str(payload.get("continuation_reason") or "").strip()
    return reason or None


def gate_clearing_preempts_task_intake(
    *,
    status_payload: dict[str, Any],
    batch_action: dict[str, Any] | None,
) -> bool:
    if not isinstance(batch_action, dict):
        return False
    if str(batch_action.get("controller_action_type") or "").strip() != "run_gate_clearing_batch":
        return False
    return continuation_reason(status_payload) in STARTUP_FRESHNESS_CONTINUATION_REASONS


def startup_freshness_requires_gate_clearing(status_payload: dict[str, Any]) -> bool:
    return continuation_reason(status_payload) in STARTUP_FRESHNESS_CONTINUATION_REASONS


def _payload_text(payload: dict[str, Any], *keys: str) -> str | None:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    text = str(current or "").strip()
    return text or None


def _gate_report_is_clear_bundle_stage(gate_report: dict[str, Any]) -> bool:
    if str(gate_report.get("status") or "").strip() != "clear":
        return False
    if gate_report.get("allow_write") is False:
        return False
    blockers = [str(item or "").strip() for item in (gate_report.get("blockers") or []) if str(item or "").strip()]
    if blockers:
        return False
    current_required_action = str(gate_report.get("current_required_action") or "").strip()
    return current_required_action in BUNDLE_STAGE_CURRENT_REQUIRED_ACTIONS


def _runtime_status_reports_bundle_stage_ready(status_payload: dict[str, Any]) -> bool:
    supervisor_phase = _payload_text(status_payload, "publication_supervisor_state", "supervisor_phase")
    current_required_action = _payload_text(status_payload, "publication_supervisor_state", "current_required_action")
    if supervisor_phase not in {"bundle_stage_ready", "bundle_stage_blocked"}:
        return False
    return current_required_action in BUNDLE_STAGE_CURRENT_REQUIRED_ACTIONS


def _publication_eval_action_is_finalize_route(action: dict[str, Any]) -> bool:
    if action.get("requires_controller_decision") is not True:
        return False
    action_type = str(action.get("action_type") or "").strip()
    if action_type not in {"continue_same_line", "route_back_same_line"}:
        return False
    route_target = str(action.get("route_target") or "").strip()
    next_work_unit = action.get("next_work_unit")
    next_work_unit_lane = (
        str(next_work_unit.get("lane") or "").strip()
        if isinstance(next_work_unit, dict)
        else ""
    )
    next_work_unit_id = (
        str(next_work_unit.get("unit_id") or "").strip()
        if isinstance(next_work_unit, dict)
        else ""
    )
    return (
        route_target in FINALIZE_ROUTE_TARGETS
        or next_work_unit_lane in FINALIZE_ROUTE_TARGETS
        or next_work_unit_id in FINALIZE_WORK_UNIT_IDS
    )


def publication_eval_has_finalize_route(publication_eval_payload: dict[str, Any]) -> bool:
    actions = publication_eval_payload.get("recommended_actions")
    if not isinstance(actions, list):
        return False
    return any(
        _publication_eval_action_is_finalize_route(action)
        for action in actions
        if isinstance(action, dict)
    )


def _publication_eval_has_finalize_work_unit(publication_eval_payload: dict[str, Any]) -> bool:
    actions = publication_eval_payload.get("recommended_actions")
    if not isinstance(actions, list):
        return False
    for action in actions:
        if not isinstance(action, dict):
            continue
        if action.get("requires_controller_decision") is not True:
            continue
        next_work_unit = action.get("next_work_unit")
        if not isinstance(next_work_unit, dict):
            continue
        next_work_unit_lane = str(next_work_unit.get("lane") or "").strip()
        next_work_unit_id = str(next_work_unit.get("unit_id") or "").strip()
        if next_work_unit_lane in FINALIZE_ROUTE_TARGETS or next_work_unit_id in FINALIZE_WORK_UNIT_IDS:
            return True
    return False


def bundle_stage_publication_eval_preempts_task_intake(
    *,
    status_payload: dict[str, Any],
    gate_report: dict[str, Any],
    publication_eval_payload: dict[str, Any],
    task_intake_action: dict[str, Any] | None = None,
) -> bool:
    if not publication_eval_has_finalize_route(publication_eval_payload):
        return False
    if task_intake_action is not None and not _publication_eval_has_finalize_work_unit(publication_eval_payload):
        return False
    if _runtime_status_reports_bundle_stage_ready(status_payload):
        return True
    return task_intake_action is None and _gate_report_is_clear_bundle_stage(gate_report)
