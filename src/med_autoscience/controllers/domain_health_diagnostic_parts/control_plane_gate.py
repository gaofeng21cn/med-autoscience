from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import authority_route_gate, domain_health_diagnostic_work_units
from med_autoscience.controllers.gate_clearing_batch_work_units import UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS


CONTROL_PLANE_DISPATCH_BLOCKED_SUMMARY = (
    "authority_snapshot 已阻断外环 dispatch；domain_health_diagnostic 只记录审计和 ledger。"
)
FAIL_CLOSED_BLOCKING_REASONS = frozenset(
    {
        "study_truth_epoch_missing",
        "runtime_health_epoch_missing",
        "runtime_recovery_retry_budget_exhausted",
    }
)
RUNTIME_RECOVERY_ACTIONS = frozenset(
    {
        "request_opl_stage_attempt",
        "request_opl_stage_attempt_relaunch",
    }
)
AI_REVIEWER_WORKFLOW_ACTION = "return_to_ai_reviewer_workflow"


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _string_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return list(
        dict.fromkeys(
            text
            for item in value
            if isinstance(item, str)
            for text in (item.strip(),)
            if text
        )
    )


def _controller_action_types(tick_request: Mapping[str, Any]) -> set[str]:
    action_types: set[str] = set()
    for action in tick_request.get("controller_actions") or []:
        if not isinstance(action, Mapping):
            continue
        action_type = _non_empty_text(action.get("action_type"))
        if action_type is not None:
            action_types.add(action_type)
    return action_types


def _first_controller_action(tick_request: Mapping[str, Any]) -> Mapping[str, Any]:
    controller_actions = tick_request.get("controller_actions")
    if not isinstance(controller_actions, list | tuple) or not controller_actions:
        return {}
    first_action = controller_actions[0]
    return first_action if isinstance(first_action, Mapping) else {}


def _next_work_unit_id(tick_request: Mapping[str, Any]) -> str | None:
    next_work_unit = tick_request.get("next_work_unit")
    if not isinstance(next_work_unit, Mapping):
        return None
    return _non_empty_text(next_work_unit.get("unit_id"))


def _route_action_for_tick_request(tick_request: Mapping[str, Any]) -> str | None:
    action_type = _non_empty_text(_first_controller_action(tick_request).get("action_type"))
    if action_type in RUNTIME_RECOVERY_ACTIONS:
        return "runtime_recovery"
    if action_type in {"run_quality_repair_batch", AI_REVIEWER_WORKFLOW_ACTION}:
        return "paper_write"
    if action_type != "run_gate_clearing_batch":
        return None
    work_unit_id = _next_work_unit_id(tick_request)
    if work_unit_id in UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS:
        return "paper_write"
    return "bundle_build"


def _controller_route_context(tick_request: Mapping[str, Any]) -> dict[str, Any] | None:
    action_type = _non_empty_text(_first_controller_action(tick_request).get("action_type"))
    work_unit_id = _next_work_unit_id(tick_request)
    if action_type is None or work_unit_id is None:
        return None
    control_surface = {
        "run_gate_clearing_batch": "gate_clearing_batch",
        "run_quality_repair_batch": "quality_repair_batch",
        AI_REVIEWER_WORKFLOW_ACTION: "ai_reviewer_workflow",
    }.get(action_type)
    if control_surface is None:
        return None
    publication_eval_ref = tick_request.get("publication_eval_ref")
    source_eval_id = (
        _non_empty_text(publication_eval_ref.get("eval_id"))
        if isinstance(publication_eval_ref, Mapping)
        else None
    )
    return {
        "control_surface": control_surface,
        "controller_action_type": action_type,
        "work_unit_id": work_unit_id,
        "requires_human_confirmation": bool(tick_request.get("requires_human_confirmation")),
        "source_eval_id": source_eval_id,
        "work_unit_fingerprint": _non_empty_text(tick_request.get("work_unit_fingerprint")),
    }


def _authorized_dispatch_route(
    *,
    snapshot: Mapping[str, Any],
    tick_request: Mapping[str, Any],
    route_payload: Mapping[str, Any],
    blocking_reasons: list[str],
) -> dict[str, Any] | None:
    route_action = _route_action_for_tick_request(tick_request)
    if route_action not in {"paper_write", "bundle_build"}:
        return None
    controller_route_context = _controller_route_context(tick_request)
    if controller_route_context is None:
        return None
    gate = authority_route_gate.authorize_authority_route(
        route_action,
        {
            "authority_snapshot": snapshot,
            "controller_route_context": controller_route_context,
        },
    )
    return gate if gate.get("authorized") is True else None


def control_plane_dispatch_block(
    *,
    status_payload: Mapping[str, Any],
    tick_request: Mapping[str, Any],
) -> dict[str, Any] | None:
    snapshot = status_payload.get("authority_snapshot")
    if not isinstance(snapshot, Mapping):
        return {
            "outcome": "control_plane_dispatch_blocked",
            "reason": "authority_snapshot is missing; domain_health_diagnostic dispatch fails closed",
            "no_op_acknowledged": True,
            "dedupe_scope": "authority_snapshot_dispatch_gate",
            "operator_summary": CONTROL_PLANE_DISPATCH_BLOCKED_SUMMARY,
            "authority_snapshot": None,
            "control_plane_blocking_reasons": ["authority_snapshot_missing"],
        }

    gate = snapshot.get("dispatch_gate")
    route_authorization = snapshot.get("route_authorization")
    gate_payload = gate if isinstance(gate, Mapping) else {}
    route_payload = route_authorization if isinstance(route_authorization, Mapping) else {}
    blocking_reasons = [
        *_string_items(gate_payload.get("blocking_reasons")),
        *_string_items(snapshot.get("blocking_reasons")),
    ]
    gate_state = _non_empty_text(gate_payload.get("state"))
    dispatch_allowed = gate_payload.get("dispatch_allowed")
    dispatch_blocked = False
    if gate_state != "open" or dispatch_allowed is not True:
        dispatch_blocked = True
        if not blocking_reasons:
            blocking_reasons.append("dispatch_gate_blocked")
    authorized_dispatch_route = _authorized_dispatch_route(
        snapshot=snapshot,
        tick_request=tick_request,
        route_payload=route_payload,
        blocking_reasons=blocking_reasons,
    )
    if authorized_dispatch_route is not None:
        dispatch_blocked = False
    if FAIL_CLOSED_BLOCKING_REASONS.intersection(blocking_reasons) and authorized_dispatch_route is None:
        dispatch_blocked = True
    if (
        route_payload.get("authorized") is False
        and authorized_dispatch_route is None
        and "route_not_authorized" not in blocking_reasons
    ):
        dispatch_blocked = True
        blocking_reasons.append("route_not_authorized")
    if (
        route_payload.get("runtime_recovery_allowed") is False
        and _controller_action_types(tick_request) & RUNTIME_RECOVERY_ACTIONS
    ):
        dispatch_blocked = True
        blocking_reasons.append("runtime_recovery_not_authorized")

    blocking_reasons = list(dict.fromkeys(blocking_reasons))
    if not dispatch_blocked:
        return None
    return {
        "outcome": "control_plane_dispatch_blocked",
        "reason": "authority_snapshot dispatch gate blocked domain_health_diagnostic outer-loop dispatch",
        "no_op_acknowledged": True,
        "dedupe_scope": "authority_snapshot_dispatch_gate",
        "operator_summary": CONTROL_PLANE_DISPATCH_BLOCKED_SUMMARY,
        "authority_snapshot": dict(snapshot),
        "control_plane_blocking_reasons": blocking_reasons,
    }


def runtime_recovery_blocked_by_control_plane(status_payload: Mapping[str, Any]) -> dict[str, Any] | None:
    snapshot = status_payload.get("authority_snapshot")
    if not isinstance(snapshot, Mapping):
        return None
    route_authorization = snapshot.get("route_authorization")
    route_payload = route_authorization if isinstance(route_authorization, Mapping) else {}
    if route_payload.get("runtime_recovery_allowed") is not False:
        return None
    blocking_reasons = [
        *_string_items(snapshot.get("blocking_reasons")),
        *_string_items(route_payload.get("blocking_reasons")),
    ]
    if "runtime_recovery_not_authorized" not in blocking_reasons:
        blocking_reasons.append("runtime_recovery_not_authorized")
    return {
        "outcome": "control_plane_runtime_recovery_blocked",
        "reason": "authority_snapshot route_authorization blocked runtime recovery",
        "authority_snapshot": dict(snapshot),
        "control_plane_blocking_reasons": list(dict.fromkeys(blocking_reasons)),
    }


def apply_control_plane_dispatch_block(
    *,
    profile: Any | None = None,
    study_root: Path,
    status_payload: Mapping[str, Any],
    tick_request: Mapping[str, Any],
    wakeup_audit: Mapping[str, Any],
    quest_report: dict[str, Any] | None,
    managed_study_no_op_suppressions: list[dict[str, Any]],
    serialize_no_op_suppression: Callable[..., dict[str, Any] | None],
    attach_no_op_suppression_to_quest_report: Callable[..., None],
    default_recorded_at: str,
    controller_decision_matches: Callable[..., bool] | None = None,
    materialize_non_dispatching_decision: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    control_plane_block = control_plane_dispatch_block(
        status_payload=status_payload,
        tick_request=tick_request,
    )
    if control_plane_block is None:
        return None
    blocked_audit = {
        **wakeup_audit,
        **control_plane_block,
        **domain_health_diagnostic_work_units.context_payload(
            tick_request,
            work_unit_dispatch_key=domain_health_diagnostic_work_units.dispatch_key(tick_request),
        ),
    }
    if (
        profile is not None
        and controller_decision_matches is not None
        and materialize_non_dispatching_decision is not None
        and not controller_decision_matches(
        study_root=study_root,
        status_payload=status_payload,
        tick_request=tick_request,
        )
    ):
        decision_result = materialize_non_dispatching_decision(
            profile=profile,
            study_root=study_root,
            status_payload=dict(status_payload),
            tick_request=tick_request,
            wakeup_audit=blocked_audit,
        )
        blocked_audit = {
            **blocked_audit,
            "controller_decision": {
                "dispatch_status": decision_result.get("dispatch_status"),
                "study_decision_ref": decision_result.get("study_decision_ref"),
            },
        }
    suppression = serialize_no_op_suppression(
        study_root=study_root,
        status_payload=status_payload,
        wakeup_audit=blocked_audit,
    )
    if suppression is not None:
        managed_study_no_op_suppressions.append(suppression)
        attach_no_op_suppression_to_quest_report(quest_report=quest_report, suppression=suppression)
    domain_health_diagnostic_work_units.append_ledger_event(
        study_root=study_root,
        status_payload=status_payload,
        tick_request=tick_request,
        event_type="control_plane_dispatch_blocked",
        wakeup_audit=blocked_audit,
        default_recorded_at=default_recorded_at,
    )
    return blocked_audit


__all__ = [
    "CONTROL_PLANE_DISPATCH_BLOCKED_SUMMARY",
    "FAIL_CLOSED_BLOCKING_REASONS",
    "apply_control_plane_dispatch_block",
    "control_plane_dispatch_block",
    "runtime_recovery_blocked_by_control_plane",
]
