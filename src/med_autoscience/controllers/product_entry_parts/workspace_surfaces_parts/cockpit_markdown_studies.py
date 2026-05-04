from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.product_entry_parts.shared_base import (
    _append_human_status_lines,
    _gate_clearing_followthrough_preview,
    _operator_handling_state_label,
    _quality_repair_followthrough_preview,
    _quality_review_followthrough_preview,
    _quality_review_loop_preview,
    _recovery_action_mode_label,
    _same_line_route_truth_preview,
)
from med_autoscience.controllers.product_entry_parts.shared_labels import _operator_verdict_label
from med_autoscience.controllers.product_entry_parts.workspace_surfaces_parts.cockpit_markdown_common import (
    readiness_action_card_label,
)
from med_autoscience.controllers.product_entry_parts.workspace_surfaces_parts.cockpit_markdown_medical import (
    active_item_delivery_inspection_lines,
    active_item_research_loop_lines,
)


def append_studies(lines: list[str], payload: Mapping[str, Any]) -> None:
    lines.extend(["", "## Studies", ""])
    for item in payload.get("studies") or []:
        if isinstance(item, Mapping):
            _append_study(lines, item)


def _append_study(lines: list[str], item: Mapping[str, Any]) -> None:
    lines.extend(
        [
            f"### {item.get('study_id')}",
            "",
            f"- 浏览器入口: `{((item.get('monitoring') or {}).get('browser_url') or 'none')}`",
            f"- 当前运行批次: `{((item.get('monitoring') or {}).get('active_run_id') or 'none')}`",
        ]
    )
    _append_human_status_lines(lines, item)
    _append_study_task_intake(lines, item)
    _append_study_status_lines(lines, item)
    readiness = dict(item.get("medical_paper_readiness") or {})
    if readiness:
        _append_study_readiness(lines, readiness)
    lines.extend(active_item_delivery_inspection_lines(item.get("delivery_inspection")))
    lines.extend(active_item_research_loop_lines(item.get("medical_paper_research_loop")))
    _append_study_recovery_and_launch(lines, item)


def _append_study_task_intake(lines: list[str], item: Mapping[str, Any]) -> None:
    task_intake = dict(item.get("task_intake") or {})
    if task_intake:
        lines.append(f"- 当前任务意图: {task_intake.get('task_intent') or '未提供'}")
        lines.append(f"- 当前投稿目标: {task_intake.get('journal_target') or 'none'}")


def _append_study_recovery_and_launch(lines: list[str], item: Mapping[str, Any]) -> None:
    restore_point = dict((item.get("autonomy_contract") or {}).get("restore_point") or {})
    if restore_point.get("summary"):
        lines.append(f"- 恢复点: {restore_point.get('summary')}")
    recovery_contract = dict(item.get("recovery_contract") or {})
    recovery_action_mode_label = _recovery_action_mode_label(recovery_contract)
    if recovery_action_mode_label:
        lines.append(f"- 恢复建议: {recovery_action_mode_label}")
    if item.get("recommended_command"):
        lines.append(f"- 推荐动作命令: `{item.get('recommended_command')}`")
    blockers = list(item.get("current_blockers") or [])
    lines.append(f"- 当前卡点: {', '.join(blockers) if blockers else '当前没有新的卡点。'}")
    lines.append(f"- 启动命令: `{((item.get('commands') or {}).get('launch') or '')}`")
    lines.append("")


def _append_study_status_lines(lines: list[str], item: Mapping[str, Any]) -> None:
    progress_freshness = dict(item.get("progress_freshness") or {})
    if progress_freshness.get("summary"):
        lines.append(f"- 进度信号: {progress_freshness.get('summary')}")
    intervention_lane = dict(item.get("intervention_lane") or {})
    if intervention_lane.get("title"):
        lines.append(f"- 当前介入通道: {intervention_lane.get('title')}")
    if intervention_lane.get("summary"):
        lines.append(f"- 当前介入摘要: {intervention_lane.get('summary')}")
    operator_verdict = dict(item.get("operator_verdict") or {})
    if operator_verdict.get("decision_mode"):
        lines.append(f"- 当前决策模式: {_operator_verdict_label(operator_verdict.get('decision_mode'))}")
    if operator_verdict.get("summary"):
        lines.append(f"- 当前处理摘要: {operator_verdict.get('summary')}")
    _append_study_operator_status(lines, item)
    _append_study_lifecycle_summaries(lines, item)
    _append_study_quality_previews(lines, item)


def _append_study_operator_status(lines: list[str], item: Mapping[str, Any]) -> None:
    operator_status_card = dict(item.get("operator_status_card") or {})
    handling_state_label = _operator_handling_state_label(operator_status_card)
    if handling_state_label:
        lines.append(f"- 当前处理状态: {handling_state_label}")
    if operator_status_card.get("user_visible_verdict"):
        lines.append(f"- 当前处理结论: {operator_status_card.get('user_visible_verdict')}")
    if operator_status_card.get("next_confirmation_signal"):
        lines.append(f"- 下一确认信号: {operator_status_card.get('next_confirmation_signal')}")


def _append_study_lifecycle_summaries(lines: list[str], item: Mapping[str, Any]) -> None:
    for field, label in (
        ("autonomy_contract", "自治合同"),
        ("autonomy_soak_status", "自治 Proof / Soak"),
        ("quality_closure_truth", "质量闭环"),
        ("quality_execution_lane", "质量执行线"),
    ):
        value = dict(item.get(field) or {})
        if value.get("summary"):
            lines.append(f"- {label}: {value.get('summary')}")


def _append_study_quality_previews(lines: list[str], item: Mapping[str, Any]) -> None:
    preview_specs = (
        (_same_line_route_truth_preview, item.get("same_line_route_truth"), "同线路由"),
        (_quality_review_loop_preview, item.get("quality_review_loop"), "质量评审闭环"),
        (_quality_review_followthrough_preview, item.get("quality_review_followthrough"), "质量复评跟进"),
        (_quality_repair_followthrough_preview, item.get("quality_repair_followthrough"), "quality-repair 跟进"),
        (_gate_clearing_followthrough_preview, item.get("gate_clearing_followthrough"), "gate-clearing 跟进"),
    )
    for preview_fn, value, label in preview_specs:
        preview = preview_fn(value)
        if preview:
            lines.append(f"- {label}: {preview}")


def _append_study_readiness(lines: list[str], readiness: Mapping[str, Any]) -> None:
    next_action = dict(readiness.get("next_action") or {})
    lines.append(
        "- Medical Paper Readiness: "
        f"overall_status `{readiness.get('overall_status') or 'unknown'}`；"
        f"下一步: {next_action.get('summary') or 'none'}；"
        "quality authorization: projection-only"
    )
    action_cards = [card for card in readiness.get("action_cards") or [] if isinstance(card, Mapping)]
    if action_cards:
        lines.append(
            "- Medical Paper Readiness 动作卡: "
            + "；".join(readiness_action_card_label(card) for card in action_cards if card.get("label"))
        )
