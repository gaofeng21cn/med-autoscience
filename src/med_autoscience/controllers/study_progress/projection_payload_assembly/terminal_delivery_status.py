from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.study_progress.current_owner_handoff_projection import (
    current_owner_redrive_domain_transition,
)
from med_autoscience.controllers.study_progress.shared import _mapping_copy, _non_empty_text


def apply_terminal_delivery_user_visible_status(payload: dict[str, Any]) -> dict[str, Any]:
    if not terminal_delivery_closed(payload):
        return payload
    user_visible = _mapping_copy(payload.get("user_visible_projection"))
    updated = dict(payload)
    updated["current_stage"] = _non_empty_text(user_visible.get("current_stage")) or "parked"
    updated["current_stage_summary"] = _non_empty_text(user_visible.get("current_stage_summary")) or (
        _non_empty_text(user_visible.get("state_summary")) or "投稿包已交付，系统已自动停驻。"
    )
    if _non_empty_text(user_visible.get("paper_stage_summary")) is not None:
        updated["paper_stage_summary"] = _non_empty_text(user_visible.get("paper_stage_summary"))
    updated["current_blockers"] = [
        str(item)
        for item in (user_visible.get("current_blockers") or [])
        if str(item or "").strip()
    ]
    updated["next_system_action"] = _non_empty_text(user_visible.get("next_system_action")) or (
        _non_empty_text(user_visible.get("next_step")) or "投稿包已交付；系统保持自动停驻。"
    )
    user_action_required = bool(user_visible.get("user_action_required"))
    updated["needs_user_decision"] = user_action_required
    updated["needs_physician_decision"] = user_action_required
    if not user_action_required:
        updated["physician_decision_summary"] = None
        updated["user_decision_summary"] = None
    updated["operator_status_card"] = terminal_delivery_operator_status_card(
        payload=updated,
        user_visible=user_visible,
    )
    status_contract = _mapping_copy(updated.get("status_narration_contract"))
    if status_contract:
        stage = _mapping_copy(status_contract.get("stage"))
        stage["current_stage"] = updated["current_stage"]
        status_contract["stage"] = stage
        readiness = _mapping_copy(status_contract.get("readiness"))
        readiness["needs_physician_decision"] = user_action_required
        status_contract["readiness"] = readiness
        status_contract["current_blockers"] = list(updated["current_blockers"])
        status_contract["latest_update"] = updated["current_stage_summary"]
        status_contract["next_step"] = updated["next_system_action"]
        updated["status_narration_contract"] = status_contract
    return updated


def terminal_delivery_closed(payload: Mapping[str, Any]) -> bool:
    if current_owner_redrive_domain_transition(payload):
        return False
    user_visible = _mapping_copy(payload.get("user_visible_projection"))
    paper_progress = _mapping_copy(user_visible.get("paper_progress_state"))
    if user_visible.get("package_delivered") is not True:
        return False
    if _non_empty_text(paper_progress.get("state")) != "terminal_delivered":
        return False
    delivery = _mapping_copy(payload.get("delivery_inspection"))
    delivery_freshness = _mapping_copy(delivery.get("freshness"))
    if _non_empty_text(delivery.get("status")) != "current" and _non_empty_text(
        delivery_freshness.get("delivery_status")
    ) != "current":
        return False
    followthrough = _mapping_copy(payload.get("gate_clearing_batch_followthrough"))
    return (
        _non_empty_text(followthrough.get("gate_replay_status")) == "clear"
        and int(followthrough.get("failed_unit_count") or 0) == 0
    )


def terminal_delivery_operator_status_card(
    *,
    payload: Mapping[str, Any],
    user_visible: Mapping[str, Any],
) -> dict[str, Any]:
    existing = _mapping_copy(payload.get("operator_status_card"))
    user_action_required = bool(user_visible.get("user_action_required"))
    handling_state = "external_metadata_pending" if user_action_required else "package_ready_handoff"
    label = "外部投稿元数据待补" if user_action_required else "投稿包/人审包交付停驻"
    focus = _non_empty_text(user_visible.get("next_step")) or _non_empty_text(user_visible.get("state_summary"))
    if focus is None:
        focus = "投稿包已与 controller-authorized source 对齐；系统保持自动停驻。"
    next_signal = (
        "看外部作者、单位、伦理、基金和声明等投稿元数据是否补齐。"
        if user_action_required
        else "看是否出现新的审阅反馈、外部条件解除或显式 resume/rerun/relaunch。"
    )
    return {
        **existing,
        "surface_kind": "study_operator_status_card",
        "study_id": _non_empty_text(payload.get("study_id")),
        "handling_state": handling_state,
        "handling_state_label": label,
        "owner_summary": "MAS 已完成 controller-authorized 投稿包交付闭环；自动运行资源已释放。",
        "current_focus": focus,
        "human_surface_freshness": "current",
        "human_surface_summary": "给人看的投稿包镜像已与 controller-authorized source 对齐；当前没有 stale/QC 刷新告警。",
        "next_confirmation_signal": next_signal,
        "user_visible_verdict": _non_empty_text(user_visible.get("state_label")) or "投稿包已交付，自动停驻",
    }


__all__ = [
    "apply_terminal_delivery_user_visible_status",
    "terminal_delivery_closed",
    "terminal_delivery_operator_status_card",
]
