from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.product_entry_parts.shared_labels import (
    _operator_verdict_label,
    _workspace_status_label,
)


def append_workspace_cockpit_header(lines: list[str], payload: Mapping[str, Any]) -> None:
    operator_brief = dict(payload.get("operator_brief") or {})
    lines.extend(
        [
            "# Workspace Cockpit",
            "",
            f"- profile: `{payload.get('profile_name')}`",
            f"- workspace_root: `{payload.get('workspace_root')}`",
            f"- 当前 workspace 状态: {_workspace_status_label(payload.get('workspace_status'))}",
            "",
            "## Now",
            "",
        ]
    )
    if operator_brief:
        lines.append(f"- 当前状态: {_operator_verdict_label(operator_brief.get('verdict'))}")
        lines.append(f"- 当前处理摘要: {operator_brief.get('summary') or 'none'}")
        lines.append(f"- 是否需要立刻介入: {'是' if operator_brief.get('should_intervene_now') else '否'}")
        lines.append(f"- 推荐动作: `{operator_brief.get('recommended_step_id') or 'none'}`")
        lines.append(f"- 推荐命令: `{operator_brief.get('recommended_command') or 'none'}`")
        if operator_brief.get("focus_study_id"):
            lines.append(f"- 聚焦 study: `{operator_brief.get('focus_study_id')}`")
        if operator_brief.get("current_focus"):
            lines.append(f"- 当前清障重点: {operator_brief.get('current_focus')}")
        if operator_brief.get("next_confirmation_signal"):
            lines.append(f"- 下一确认信号: {operator_brief.get('next_confirmation_signal')}")
    else:
        lines.append("- 当前还没有 operator brief。")


def append_workspace_supervision_sections(lines: list[str], payload: Mapping[str, Any]) -> None:
    _append_mainline_snapshot(lines, payload)
    _append_workspace_supervision(lines, payload)


def _append_mainline_snapshot(lines: list[str], payload: Mapping[str, Any]) -> None:
    mainline_snapshot = dict(payload.get("mainline_snapshot") or {})
    lines.extend(["", "## Mainline Snapshot", ""])
    if mainline_snapshot:
        lines.append(f"- 当前 program: `{mainline_snapshot.get('program_id') or 'unknown'}`")
        lines.append(f"- 当前主线阶段: `{mainline_snapshot.get('current_stage_id') or 'unknown'}`")
        if mainline_snapshot.get("current_stage_summary"):
            lines.append(f"- 当前判断: {mainline_snapshot.get('current_stage_summary')}")
        if mainline_snapshot.get("current_program_phase_id"):
            lines.append(f"- 当前 program phase: `{mainline_snapshot.get('current_program_phase_id')}`")
        if mainline_snapshot.get("current_program_phase_summary"):
            lines.append(f"- program phase 摘要: {mainline_snapshot.get('current_program_phase_summary')}")
        next_focus = list(mainline_snapshot.get("next_focus") or [])
        if next_focus:
            lines.append(f"- 下一步焦点: {next_focus[0]}")
    else:
        lines.append("- 当前还没有 repo 主线快照。")


def _append_workspace_supervision(lines: list[str], payload: Mapping[str, Any]) -> None:
    workspace_supervision = dict(payload.get("workspace_supervision") or {})
    service = dict(workspace_supervision.get("service") or {})
    study_counts = dict(workspace_supervision.get("study_counts") or {})
    lines.extend(["", "## Workspace Supervision", ""])
    if workspace_supervision:
        lines.append(f"- 当前监管摘要: {workspace_supervision.get('summary')}")
        if service.get("summary"):
            lines.append(f"- 监管服务: {service.get('summary')}")
        if study_counts:
            lines.append(
                "- 当前计数: "
                f"监管缺口 {study_counts.get('supervisor_gap', 0)}；"
                f"需要恢复 {study_counts.get('recovery_required', 0)}；"
                f"质量阻塞 {study_counts.get('quality_blocked', 0)}；"
                f"自动停驻 {study_counts.get('auto_runtime_parked', 0)}；"
                f"进度陈旧 {study_counts.get('progress_stale', 0)}；"
                f"进度缺失 {study_counts.get('progress_missing', 0)}；"
                f"等待用户判断 {study_counts.get('needs_user_decision', 0)}"
            )
    else:
        lines.append("- 当前还没有 workspace 级监管汇总。")
