from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .shared import _non_empty_text

_QUALITY_REPAIR_LABEL = "质量修复/复审中"


def _normalized_texts(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = _non_empty_text(item)
        if text is not None and text not in items:
            items.append(text)
    return items


def _state_label(
    *,
    writer_state: str,
    user_next: str,
    reason: str,
    package_delivered: bool,
    terminal_delivery: bool,
    quality_owner_pending: bool = False,
) -> str:
    if writer_state == "conflict" or reason == "truth_conflict":
        return "状态需要检查"
    if writer_state == "live":
        return "自动运行中"
    if user_next == "submit_info" and reason == "external_info" and package_delivered:
        return "投稿包已交付，等待外部投稿信息"
    if user_next == "runtime_handoff":
        return "等待 OPL runtime handoff"
    if quality_owner_pending:
        return _QUALITY_REPAIR_LABEL
    if terminal_delivery and writer_state == "parked":
        return "投稿包已交付，自动停驻"
    if reason == "user_stop":
        return "用户暂停/手动停驻"
    if reason == "stop_loss":
        return "止损/终止"
    if reason == "quality" or user_next in {"repair", "revise"}:
        return _QUALITY_REPAIR_LABEL
    if writer_state == "queued":
        return "系统排队处理中"
    return "用户暂停/手动停驻" if writer_state == "parked" else "状态需要检查"


def _state_summary(
    *,
    state_label: str,
    writer_state: str,
    user_next: str,
    reason: str,
    package_delivered: bool,
    actual_write_active: bool,
    user_action_required: bool,
    current_blockers: list[str],
) -> str:
    if state_label == "自动运行中":
        if actual_write_active:
            return "自动运行中；系统有实际 writer/run 正在推进。"
        return "自动运行中；worker 已接管，但尚未观察到论文产物级有效增量。"
    if state_label == "系统排队处理中":
        return "系统排队处理中；当前没有实际写入，但 MAS 已有明确 owner/action。"
    if state_label == "投稿包已交付，等待外部投稿信息":
        return "投稿包已交付，系统已自动停驻并释放运行资源；等待补齐外部投稿信息。"
    if state_label == "投稿包已交付，自动停驻":
        return "投稿包已交付，系统已自动停驻并释放运行资源。"
    if state_label == "用户暂停/手动停驻":
        return "用户暂停/手动停驻；当前没有实际写入，需显式恢复或给出新方案。"
    if state_label == _QUALITY_REPAIR_LABEL:
        return "质量修复/复审中；质量、artifact 或 runtime 有明确修复 owner。"
    if state_label == "等待 OPL runtime handoff":
        return "等待 OPL runtime handoff；MAS 已输出 domain blocker/handoff refs，generic runtime 生命周期归 OPL。"
    if state_label == "止损/终止":
        return "止损/终止；当前论文线不再自动推进，需新计划或明确重开。"
    if current_blockers:
        return f"{state_label}；{current_blockers[0]}"
    write_text = "有实际写入" if actual_write_active else "没有实际写入"
    delivered_text = "投稿包已交付" if package_delivered else "投稿包未交付"
    user_text = "需要用户动作" if user_action_required else "当前不需要用户补东西"
    return f"{state_label}；{write_text}，{delivered_text}，{user_text}（{writer_state}/{user_next}/{reason}）。"


def _next_step(
    *,
    writer_state: str,
    user_next: str,
    reason: str,
    terminal_delivery: bool,
    details: Mapping[str, Any],
    quality_owner_pending: bool = False,
) -> str:
    if writer_state == "live":
        return "观察自动运行推进。"
    if user_next == "submit_info" and reason == "external_info":
        missing = _normalized_texts(details.get("missing_external_info"))
        suffix = f": {', '.join(missing)}" if missing else ""
        return f"补齐外部投稿信息{suffix}。"
    if quality_owner_pending:
        return "等待质量修复/复审 owner 完成处理。"
    if user_next == "runtime_handoff":
        return "等待 OPL generic runtime handoff 完成；MAS 只保留 domain blocker/handoff refs。"
    if writer_state == "queued":
        return "等待 MAS 已登记的 owner/action 处理。"
    if terminal_delivery:
        return "投稿包已交付；系统保持自动停驻。"
    if reason == "user_stop":
        return "等待用户显式恢复或给出新方案。"
    if reason == "stop_loss":
        return "等待新计划或明确重开。"
    if reason == "quality" or user_next in {"repair", "revise"}:
        return "等待质量修复/复审 owner 完成处理。"
    return "检查并重新生成 canonical progress projection。"


def _projection_conditions(
    *,
    writer_state: str,
    user_next: str,
    reason: str,
    package_delivered: bool,
    actual_write_active: bool,
    meaningful_artifact_delta: bool,
    next_owner: str | None,
    why_not_progressing: str | None,
    user_action_required: bool,
    current_blockers: list[str],
    next_step: str,
    supervision: dict[str, Any],
    evidence: dict[str, Any],
) -> list[dict[str, str]]:
    return [
        _condition(
            "macro_state_known",
            True,
            f"{writer_state}/{user_next}/{reason}",
            "用户可见状态来自 study_macro_state。",
        ),
        _condition(
            "package_delivered",
            package_delivered,
            "package_delivered" if package_delivered else "package_not_delivered",
            "投稿包已交付。" if package_delivered else "投稿包未交付。",
        ),
        _condition(
            "actual_write_active",
            actual_write_active,
            "writer_active" if actual_write_active else "writer_inactive",
            "系统有实际 writer/run 正在写入。" if actual_write_active else "当前没有实际写入。",
        ),
        _condition(
            "meaningful_artifact_delta",
            meaningful_artifact_delta,
            "artifact_delta_present" if meaningful_artifact_delta else "artifact_delta_absent",
            "已观察到论文产物级有效增量。" if meaningful_artifact_delta else "尚未观察到论文产物级有效增量。",
        ),
        _condition(
            "next_owner",
            bool(next_owner),
            "next_owner_present" if next_owner else "next_owner_missing",
            next_owner,
        ),
        _condition(
            "why_not_progressing",
            bool(why_not_progressing),
            "why_not_progressing_present" if why_not_progressing else "progressing_or_unknown",
            why_not_progressing,
        ),
        _condition(
            "blocked",
            bool(current_blockers),
            "blockers_present" if current_blockers else "no_current_blockers",
            current_blockers[0] if current_blockers else "当前没有新的卡点。",
        ),
        _condition(
            "next_action_known",
            bool(next_step),
            "next_action_present" if next_step else "next_action_missing",
            next_step,
        ),
        _condition(
            "evidence_available",
            bool(evidence.get("latest_events") or evidence.get("refs")),
            "evidence_refs_present" if evidence.get("latest_events") or evidence.get("refs") else "evidence_missing",
            "关键证据引用可用。" if evidence.get("latest_events") or evidence.get("refs") else "缺少关键证据引用。",
        ),
        _condition(
            "user_action_required",
            user_action_required,
            "user_action_present" if user_action_required else "user_action_absent",
            "当前需要用户补充或决策。" if user_action_required else "当前不需要用户补东西。",
        ),
        _condition(
            "runtime_supervised",
            bool(
                _non_empty_text(supervision.get("active_run_id"))
                or _non_empty_text(supervision.get("health_status"))
                or _non_empty_text(supervision.get("supervisor_tick_status"))
            ),
            "supervision_signal_present",
            _non_empty_text(supervision.get("health_status")) or _non_empty_text(supervision.get("active_run_id")),
        ),
    ]


def _condition(condition_type: str, status: bool, reason: str, message: str | None) -> dict[str, str]:
    return {
        "type": condition_type,
        "status": "true" if status else "false",
        "reason": reason,
        "message": message or "",
    }
