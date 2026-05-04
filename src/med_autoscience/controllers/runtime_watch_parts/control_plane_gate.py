from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import runtime_watch_work_units
from med_autoscience.controllers.runtime_watch_parts.managed_wakeup import (
    _controller_decision_latest_matches_outer_loop_request,
)


CONTROL_PLANE_DISPATCH_BLOCKED_SUMMARY = (
    "control_plane_snapshot 已阻断外环 dispatch；runtime_watch 只记录审计和 ledger。"
)


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


def control_plane_dispatch_block(
    *,
    status_payload: Mapping[str, Any],
    tick_request: Mapping[str, Any],
) -> dict[str, Any] | None:
    snapshot = status_payload.get("control_plane_snapshot")
    if not isinstance(snapshot, Mapping):
        return {
            "outcome": "control_plane_dispatch_blocked",
            "reason": "control_plane_snapshot is missing; runtime_watch dispatch fails closed",
            "no_op_acknowledged": True,
            "dedupe_scope": "control_plane_snapshot_dispatch_gate",
            "operator_summary": CONTROL_PLANE_DISPATCH_BLOCKED_SUMMARY,
            "control_plane_snapshot": None,
            "control_plane_blocking_reasons": ["control_plane_snapshot_missing"],
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
    if route_payload.get("authorized") is False and "route_not_authorized" not in blocking_reasons:
        dispatch_blocked = True
        blocking_reasons.append("route_not_authorized")
    runtime_recovery_actions = {
        "ensure_study_runtime",
        "relaunch_runtime",
        "recover_runtime",
        "resume_runtime",
        "resume_same_study_line",
    }
    if (
        route_payload.get("runtime_recovery_allowed") is False
        and _controller_action_types(tick_request) & runtime_recovery_actions
    ):
        dispatch_blocked = True
        blocking_reasons.append("runtime_recovery_not_authorized")

    blocking_reasons = list(dict.fromkeys(blocking_reasons))
    if not dispatch_blocked:
        return None
    return {
        "outcome": "control_plane_dispatch_blocked",
        "reason": "control_plane_snapshot dispatch gate blocked runtime_watch outer-loop dispatch",
        "no_op_acknowledged": True,
        "dedupe_scope": "control_plane_snapshot_dispatch_gate",
        "operator_summary": CONTROL_PLANE_DISPATCH_BLOCKED_SUMMARY,
        "control_plane_snapshot": dict(snapshot),
        "control_plane_blocking_reasons": blocking_reasons,
    }


def runtime_recovery_blocked_by_control_plane(status_payload: Mapping[str, Any]) -> dict[str, Any] | None:
    snapshot = status_payload.get("control_plane_snapshot")
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
        "reason": "control_plane_snapshot route_authorization blocked runtime recovery",
        "control_plane_snapshot": dict(snapshot),
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
        **runtime_watch_work_units.context_payload(
            tick_request,
            work_unit_dispatch_key=runtime_watch_work_units.dispatch_key(tick_request),
        ),
    }
    if profile is not None and not _controller_decision_latest_matches_outer_loop_request(
        study_root=study_root,
        status_payload=status_payload,
        tick_request=tick_request,
    ):
        from med_autoscience.controllers import study_outer_loop

        decision_result = study_outer_loop.materialize_non_dispatching_outer_loop_decision(
            profile=profile,
            status_payload=dict(status_payload),
            source="runtime_watch_outer_loop_wakeup",
            recorded_at=_non_empty_text(blocked_audit.get("recorded_at")),
            **runtime_watch_work_units.strip_context(tick_request),
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
    runtime_watch_work_units.append_ledger_event(
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
    "apply_control_plane_dispatch_block",
    "control_plane_dispatch_block",
    "runtime_recovery_blocked_by_control_plane",
]
