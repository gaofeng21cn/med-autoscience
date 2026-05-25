from __future__ import annotations

from typing import Any


MANUAL_HOLD_KINDS = frozenset({"manual_hold", "hold_until_explicit_wakeup"})
MANUAL_HOLD_ACTIONS = frozenset({"hold_until_explicit_wakeup", "pause_runtime_until_explicit_wakeup"})


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def task_intake_requests_manual_hold(payload: dict[str, Any] | None) -> bool:
    if not isinstance(payload, dict):
        return False
    if (_non_empty_text(payload.get("task_intake_kind")) or _non_empty_text(payload.get("intake_kind"))) in MANUAL_HOLD_KINDS:
        return True
    manual_hold = _mapping(payload.get("manual_hold_intake"))
    if manual_hold:
        return (
            _non_empty_text(manual_hold.get("kind")) in MANUAL_HOLD_KINDS
            or _non_empty_text(manual_hold.get("route")) == "await_explicit_wakeup"
            or _non_empty_text(_mapping(manual_hold.get("decision_policy")).get("controller_action")) in MANUAL_HOLD_ACTIONS
        )
    quality_closure_truth = _mapping(payload.get("quality_closure_truth"))
    if _non_empty_text(quality_closure_truth.get("state")) == "manual_hold":
        return True
    current_required_action = _non_empty_text(payload.get("current_required_action"))
    return current_required_action in MANUAL_HOLD_ACTIONS


def build_manual_hold_intake(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not task_intake_requests_manual_hold(payload):
        return None
    return {
        "kind": "manual_hold",
        "status": "active",
        "route": "await_explicit_wakeup",
        "handoff_required": True,
        "decision_policy": {
            "canonical_action": "pause_runtime",
            "controller_action": "hold_until_explicit_wakeup",
            "reason": "The latest intake explicitly parks this paper line until a new plan and explicit wakeup.",
        },
        "auto_recovery_allowed": False,
        "opl_owner_route_auto_recovery_allowed": False,
        "relaunch_requires": ["new study plan or revised study charter", "explicit user wakeup"],
    }


def build_manual_hold_progress_override(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not task_intake_requests_manual_hold(payload):
        return None
    blocker_summary = "最新 task intake 明确要求手动停驻，等待新方案和显式唤醒；MAS 不得自动恢复写入。"
    route_summary = "保持当前论文线停驻；形成新方案并显式唤醒后，再由 controller 重新判断是否重启。"
    return {
        "blocker_summary": blocker_summary,
        "current_stage_summary": blocker_summary,
        "next_system_action": route_summary,
        "current_required_action": "hold_until_explicit_wakeup",
        "paper_stage": "manual_hold",
        "paper_stage_summary": route_summary,
        "quality_closure_truth": {
            "state": "manual_hold",
            "summary": blocker_summary,
            "current_required_action": "hold_until_explicit_wakeup",
            "route_target": "manual_hold",
        },
        "quality_execution_lane": {
            "lane_id": "manual_hold",
            "lane_label": "手动停驻",
            "repair_mode": "manual_hold",
            "route_target": "manual_hold",
            "route_key_question": "是否已有新方案和显式唤醒许可？",
            "summary": route_summary,
            "why_now": blocker_summary,
        },
        "same_line_route_truth": {
            "surface_kind": "same_line_route_truth",
            "same_line_state": "manual_hold",
            "same_line_state_label": "手动停驻待新方案",
            "route_mode": "hold",
            "route_target": "manual_hold",
            "route_target_label": "手动停驻",
            "summary": route_summary,
            "current_focus": "等待新方案和显式唤醒",
        },
        "same_line_route_surface": {
            "surface_kind": "same_line_route_surface",
            "lane_id": "manual_hold",
            "repair_mode": "manual_hold",
            "route_target": "manual_hold",
            "route_target_label": "手动停驻",
            "route_key_question": "是否已有新方案和显式唤醒许可？",
            "summary": route_summary,
            "why_now": blocker_summary,
            "current_required_action": "hold_until_explicit_wakeup",
            "closure_state": "manual_hold",
        },
    }


def render_manual_hold_markdown_lines(payload: dict[str, Any]) -> list[str]:
    if not task_intake_requests_manual_hold(payload):
        return []
    return [
        "",
        "## Manual Hold Intake",
        "",
        "- 当前任务要求保持论文线停驻，等待新方案和显式唤醒。",
        "- OPL owner-route 自动恢复、supervisor redrive 或 active/no-live recovery 不能自动恢复写入。",
        "- 未来重启必须先形成新的 study plan 或修订 study charter，再由用户显式 wakeup。",
    ]


def render_manual_hold_runtime_context_lines(payload: dict[str, Any]) -> list[str]:
    if not task_intake_requests_manual_hold(payload):
        return []
    return [
        "Manual hold intake: active",
        "Route: await_explicit_wakeup",
        "Controller action: hold_until_explicit_wakeup",
        "Do not auto-recover through OPL owner-route auto recovery or supervisor redrive.",
        "Future relaunch requires a new plan and explicit user wakeup.",
    ]


__all__ = [
    "build_manual_hold_intake",
    "build_manual_hold_progress_override",
    "render_manual_hold_markdown_lines",
    "render_manual_hold_runtime_context_lines",
    "task_intake_requests_manual_hold",
]
