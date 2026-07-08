from __future__ import annotations

from typing import Any, Mapping

from ..shared import _mapping_copy, _non_empty_text
from .current_execution_surfaces import typed_blocker_reason as _typed_blocker_reason


def apply_current_work_unit_typed_blocker_user_visible_status(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if _paper_recovery_suppresses_current_work_unit_typed_blocker(payload):
        return payload
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("status")) not in {
        "typed_blocker",
        "blocked_current_work_unit",
    }:
        return payload
    intervention_lane = _mapping_copy(payload.get("intervention_lane"))
    operator_status = _mapping_copy(payload.get("operator_status_card"))
    if _mapping_copy(operator_status.get("no_op_suppression")):
        return payload
    if _non_empty_text(intervention_lane.get("lane_id")) in {
        "runtime_recovery_required",
        "workspace_supervision_gap",
        "quality_floor_blocker",
        "completion_evidence_required",
        "progress_continuation_required",
        "current_owner_action_ready",
        "manual_finishing_fast_lane",
    }:
        return payload
    typed_blocker = _current_work_unit_typed_blocker(current_work_unit)
    if not typed_blocker:
        return payload
    updated = dict(payload)
    reason = (
        _typed_blocker_reason(typed_blocker)
        or _non_empty_text(current_work_unit.get("status"))
        or "typed_blocker"
    )
    owner = (
        _non_empty_text(typed_blocker.get("required_next_owner"))
        or _non_empty_text(typed_blocker.get("owner"))
        or _non_empty_text(current_work_unit.get("owner"))
    )
    work_unit_id = _non_empty_text(typed_blocker.get("work_unit_id")) or _non_empty_text(
        current_work_unit.get("work_unit_id")
    )
    action_type = _non_empty_text(typed_blocker.get("action_type")) or _non_empty_text(
        current_work_unit.get("action_type")
    )
    next_step = _typed_blocker_next_step(
        reason=reason,
        owner=owner,
        work_unit_id=work_unit_id,
        action_type=action_type,
    )
    blockers = _typed_blocker_blockers(typed_blocker, reason=reason)
    updated["current_blockers"] = blockers
    updated["next_system_action"] = next_step
    if owner is not None:
        updated["next_owner"] = owner
    user_visible = _mapping_copy(updated.get("user_visible_projection"))
    if user_visible:
        if owner is not None:
            user_visible["owner_resolution_state"] = "ready_for_owner_action"
        else:
            user_visible["owner_resolution_state"] = "blocked_with_typed_owner"
        user_visible["current_blockers"] = blockers
        user_visible["next_system_action"] = next_step
        user_visible["next_step"] = next_step
        user_visible["why_not_progressing"] = reason
        if owner is not None:
            user_visible["next_owner"] = owner
        updated["user_visible_projection"] = user_visible
    status_contract = _mapping_copy(updated.get("status_narration_contract"))
    if status_contract:
        status_contract["current_blockers"] = blockers
        status_contract["next_step"] = next_step
        status_contract["latest_update"] = next_step
        stage = _mapping_copy(status_contract.get("stage"))
        if stage:
            stage["intervention_lane"] = "typed_owner_blocker"
            status_contract["stage"] = stage
        updated["status_narration_contract"] = status_contract
    intervention_lane = _mapping_copy(updated.get("intervention_lane"))
    if intervention_lane:
        intervention_lane.update(
            {
                "lane_id": "typed_owner_blocker",
                "title": "等待当前 typed blocker owner",
                "severity": "critical",
                "summary": next_step,
                "recommended_action_id": "inspect_current_typed_blocker",
                "route_target": owner,
                "route_target_label": owner,
                "route_key_question": reason,
                "route_summary": next_step,
                "work_unit_id": work_unit_id,
                "action_type": action_type,
            }
        )
        updated["intervention_lane"] = {
            key: value for key, value in intervention_lane.items() if value not in (None, "", [], {})
        }
    for key in ("operator_verdict", "recovery_contract"):
        surface = _mapping_copy(updated.get(key))
        if not surface:
            continue
        surface["summary"] = next_step
        if "reason_summary" in surface:
            surface["reason_summary"] = reason
        updated[key] = surface
    operator_status = _mapping_copy(updated.get("operator_status_card"))
    if operator_status:
        operator_status["current_focus"] = next_step
        operator_status["user_visible_verdict"] = next_step
        updated["operator_status_card"] = operator_status
    return updated


def _paper_recovery_suppresses_current_work_unit_typed_blocker(
    payload: Mapping[str, Any],
) -> bool:
    recovery = _mapping_copy(payload.get("paper_recovery_state"))
    suppressed = {
        text
        for item in recovery.get("suppressed_surfaces") or []
        if (text := _non_empty_text(item)) is not None
    }
    return "current_work_unit_typed_blocker" in suppressed


def _current_work_unit_typed_blocker(
    current_work_unit: Mapping[str, Any],
) -> dict[str, Any]:
    state = _mapping_copy(current_work_unit.get("state"))
    typed_blocker = _mapping_copy(state.get("typed_blocker")) or _mapping_copy(
        current_work_unit.get("typed_blocker")
    )
    if _non_empty_text(current_work_unit.get("status")) != "typed_blocker" and not typed_blocker:
        return {}
    if not typed_blocker:
        typed_blocker = {
            "blocker_type": _non_empty_text(state.get("blocker_type")),
            "blocker_id": _non_empty_text(state.get("blocker_id")),
            "blocked_reason": _non_empty_text(state.get("blocked_reason")),
        }
    for key in ("owner", "action_type", "work_unit_id", "work_unit_fingerprint"):
        typed_blocker.setdefault(key, _non_empty_text(current_work_unit.get(key)))
    if _non_empty_text(
        current_work_unit.get("status")
    ) == "blocked_current_work_unit" and _generic_unresolved_typed_blocker(
        typed_blocker=typed_blocker,
        source=_non_empty_text(state.get("source")),
    ):
        return {}
    return {key: value for key, value in typed_blocker.items() if value not in (None, "", [], {})}


def _generic_unresolved_typed_blocker(
    *,
    typed_blocker: Mapping[str, Any],
    source: str | None,
) -> bool:
    if source != "blocked_current_work_unit":
        return False
    if _typed_blocker_reason(typed_blocker) != "current_work_unit_unresolved":
        return False
    identity_fields = (
        "action_type",
        "work_unit_id",
        "work_unit_fingerprint",
        "action_fingerprint",
        "blocker_id",
        "latest_owner_answer_ref",
        "typed_blocker_ref",
        "owner_receipt_ref",
    )
    return not any(_non_empty_text(typed_blocker.get(key)) is not None for key in identity_fields)


def _typed_blocker_blockers(typed_blocker: Mapping[str, Any], *, reason: str) -> list[str]:
    values: list[str] = [reason]
    for item in typed_blocker.get("remaining_blockers") or []:
        if text := _non_empty_text(item):
            values.append(text)
    for key in ("summary", "required_input", "source_ref"):
        if text := _non_empty_text(typed_blocker.get(key)):
            values.append(text)
    return list(dict.fromkeys(values))[:8]


def _typed_blocker_next_step(
    *,
    reason: str,
    owner: str | None,
    work_unit_id: str | None,
    action_type: str | None,
) -> str:
    owner_text = owner or "当前 owner"
    subject = f" work unit {work_unit_id}" if work_unit_id is not None else ""
    action = f" / {action_type}" if action_type is not None else ""
    return f"等待 {owner_text} 处理当前 typed blocker：{reason}{subject}{action}。"
