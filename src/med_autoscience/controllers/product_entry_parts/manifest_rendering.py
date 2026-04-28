from __future__ import annotations

from typing import Any, Mapping

from .program_surfaces import _render_phase5_platform_target_markdown_lines
from .shared import *  # noqa: F403
from .workspace_attention import (
    _autonomy_soak_focus,
    _gate_clearing_followthrough_focus,
    _operator_status_summary,
    _quality_execution_focus,
    _quality_repair_followthrough_focus,
    _quality_review_followthrough_focus,
    _same_line_route_focus,
)


def render_product_entry_manifest_markdown(payload: dict[str, Any]) -> str:
    workspace_locator = dict(payload.get("workspace_locator") or {})
    repo_mainline = dict(payload.get("repo_mainline") or {})
    product_entry_shell = dict(payload.get("product_entry_shell") or {})
    shared_handoff = dict(payload.get("shared_handoff") or {})
    gateway_interaction_contract = dict(payload.get("gateway_interaction_contract") or {})
    phase2_user_product_loop = dict(payload.get("phase2_user_product_loop") or {})
    product_entry_guardrails = dict(payload.get("product_entry_guardrails") or {})
    phase3_clearance_lane = dict(payload.get("phase3_clearance_lane") or {})
    phase4_backend_deconstruction = dict(payload.get("phase4_backend_deconstruction") or {})
    phase5_platform_target = dict(payload.get("phase5_platform_target") or {})
    single_project_boundary = dict(payload.get("single_project_boundary") or {})
    capability_owner_boundary = dict(payload.get("capability_owner_boundary") or {})
    lines = [
        "# Product Entry Manifest",
        "",
        f"- manifest 类型: `{payload.get('manifest_kind')}`",
        f"- schema 引用: `{payload.get('schema_ref')}`",
        f"- 目标域: `{payload.get('target_domain_id')}`",
        f"- profile 名称: `{workspace_locator.get('profile_name')}`",
        f"- workspace 根目录: `{workspace_locator.get('workspace_root')}`",
        f"- 当前 program phase: `{repo_mainline.get('current_program_phase_id')}`",
        f"- 当前主线阶段: `{repo_mainline.get('current_stage_id')}`",
        f"- 程序摘要: {repo_mainline.get('summary') or 'none'}",
        f"- 前台入口归属: `{gateway_interaction_contract.get('frontdoor_owner') or 'none'}`",
        f"- 交互模式: {_user_interaction_mode_label(gateway_interaction_contract.get('user_interaction_mode'))}",
        "",
        "## Product Entry Shell",
        "",
    ]
    for name, item in product_entry_shell.items():
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{name}`: `{item.get('command')}`")
    lines.extend([""] + _render_single_project_boundary_markdown_lines(single_project_boundary) + [""])
    lines.extend(_render_capability_owner_boundary_markdown_lines(capability_owner_boundary) + [""])
    lines.extend(["", "## Operator Loop Actions", ""])
    for name, item in (payload.get("operator_loop_actions") or {}).items():
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{name}`: `{item.get('command')}`")
    lines.extend(["", "## Shared Handoff", ""])
    for name, item in shared_handoff.items():
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{name}`: `{item.get('command')}`")
    lines.extend(["", "## Phase 2 User Loop", ""])
    lines.append(f"- program phase 摘要: {phase2_user_product_loop.get('summary') or 'none'}")
    lines.append(f"- 推荐动作: `{phase2_user_product_loop.get('recommended_step_id') or 'none'}`")
    lines.append(f"- 推荐命令: `{phase2_user_product_loop.get('recommended_command') or 'none'}`")
    for item in phase2_user_product_loop.get("single_path") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- 单一路径 `{item.get('step_id')}`: `{item.get('command') or 'none'}`")
    lines.extend(["", "## Guardrails", ""])
    lines.append(f"- 当前摘要: {product_entry_guardrails.get('summary') or 'none'}")
    for item in product_entry_guardrails.get("guardrail_classes") or []:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- `{item.get('guardrail_id')}`: `{item.get('recommended_command') or 'none'}`"
        )
    lines.extend(["", "## Phase 3 Clearance", ""])
    lines.append(f"- 清障重点: {phase3_clearance_lane.get('summary') or 'none'}")
    lines.append(f"- 推荐动作: `{phase3_clearance_lane.get('recommended_step_id') or 'none'}`")
    lines.append(f"- 推荐命令: `{phase3_clearance_lane.get('recommended_command') or 'none'}`")
    for item in phase3_clearance_lane.get("clearance_targets") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('target_id')}`: `{((item.get('commands') or ['none'])[0])}`")
    for item in phase3_clearance_lane.get("clearance_loop") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- 清障步骤 `{item.get('step_id')}`: `{item.get('command') or 'none'}`")
    lines.extend(["", "## Phase 4 Deconstruction", ""])
    for item in phase4_backend_deconstruction.get("substrate_targets") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('capability_id')}`: {item.get('summary') or 'none'}")
    lines.extend([""])
    lines.extend(_render_phase5_platform_target_markdown_lines(phase5_platform_target))
    lines.extend(["", "## Remaining Gaps", ""])
    remaining_gaps = list(payload.get("remaining_gaps") or [])
    if remaining_gaps:
        lines.extend(f"- {item}" for item in remaining_gaps)
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def render_skill_catalog_markdown(payload: dict[str, Any]) -> str:
    skills = [dict(item) for item in (payload.get("skills") or []) if isinstance(item, Mapping)]
    lines = [
        "# Skill Catalog",
        "",
        f"- surface kind: `{payload.get('surface_kind') or 'none'}`",
        f"- summary: {payload.get('summary') or 'none'}",
        "",
        "## Skills",
        "",
    ]
    if not skills:
        lines.append("- 当前没有 skill descriptor。")
    for skill in skills:
        lines.append(f"- `{skill.get('skill_id') or 'unknown'}`: {skill.get('description') or 'none'}")
        lines.append(f"  - target surface: `{skill.get('target_surface_kind') or 'none'}`")
        lines.append(f"  - command: `{skill.get('command') or 'none'}`")
    command_contracts = [dict(item) for item in (payload.get("command_contracts") or []) if isinstance(item, Mapping)]
    lines.extend(["", "## Command Contracts", ""])
    if not command_contracts:
        lines.append("- 当前没有 command contract。")
    for contract in command_contracts:
        required_fields = ", ".join(contract.get("required_fields") or []) or "none"
        optional_fields = ", ".join(contract.get("optional_fields") or []) or "none"
        lines.append(f"- `{contract.get('command') or 'unknown'}`")
        lines.append(f"  - required: {required_fields}")
        lines.append(f"  - optional: {optional_fields}")
    return "\n".join(lines)


def render_product_frontdesk_markdown(payload: dict[str, Any]) -> str:
    entry_surfaces = dict(payload.get("entry_surfaces") or {})
    gateway_interaction_contract = dict(payload.get("gateway_interaction_contract") or {})
    phase2_user_product_loop = dict(payload.get("phase2_user_product_loop") or {})
    product_entry_guardrails = dict(payload.get("product_entry_guardrails") or {})
    phase3_clearance_lane = dict(payload.get("phase3_clearance_lane") or {})
    phase4_backend_deconstruction = dict(payload.get("phase4_backend_deconstruction") or {})
    phase5_platform_target = dict(payload.get("phase5_platform_target") or {})
    single_project_boundary = dict(payload.get("single_project_boundary") or {})
    capability_owner_boundary = dict(payload.get("capability_owner_boundary") or {})
    operator_brief = dict(payload.get("operator_brief") or {})
    quickstart = dict(payload.get("product_entry_quickstart") or {})
    workspace_operator_brief = dict(payload.get("workspace_operator_brief") or {})
    lines = [
        "# Product Frontdesk",
        "",
        f"- 目标域: `{payload.get('target_domain_id')}`",
        f"- 契约引用: `{payload.get('schema_ref') or 'none'}`",
        f"- 前台归属: `{gateway_interaction_contract.get('frontdoor_owner') or 'none'}`",
        f"- 交互模式: `{gateway_interaction_contract.get('user_interaction_mode') or 'none'}`",
        f"- 前台入口命令: `{(payload.get('summary') or {}).get('frontdesk_command') or 'none'}`",
        f"- 推荐继续命令: `{(payload.get('summary') or {}).get('recommended_command') or 'none'}`",
        f"- 当前 loop 命令: `{(payload.get('summary') or {}).get('operator_loop_command') or 'none'}`",
        "",
        "## Now",
        "",
    ]
    if operator_brief:
        lines.append(f"- 当前状态: {_operator_verdict_label(operator_brief.get('verdict'))}")
        lines.append(f"- 当前判断: {operator_brief.get('summary') or 'none'}")
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
        lines.append("- 当前还没有 frontdesk operator brief。")
    lines.extend([""] + _render_single_project_boundary_markdown_lines(single_project_boundary) + [""])
    lines.extend(_render_capability_owner_boundary_markdown_lines(capability_owner_boundary) + [""])
    lines.extend([
        "",
        "## Single Path",
        "",
    ])
    for step in quickstart.get("steps") or []:
        if not isinstance(step, dict):
            continue
        lines.append(
            f"- `{step.get('step_id')}`: `{step.get('command') or 'none'}` {step.get('summary') or ''}"
        )
    lines.extend([
        "",
        "## Product Entry Overview",
        "",
        f"- 总览判断: `{(payload.get('product_entry_overview') or {}).get('summary') or 'none'}`",
        f"- 启动提示: `{(payload.get('product_entry_start') or {}).get('summary') or 'none'}`",
        f"- 启动后恢复命令: `{((payload.get('product_entry_start') or {}).get('resume_surface') or {}).get('command') or 'none'}`",
        f"- 前置检查已通过: `{'是' if (payload.get('product_entry_preflight') or {}).get('ready_to_try_now') else '否'}`",
        f"- 前置检查命令: `{(payload.get('product_entry_preflight') or {}).get('recommended_check_command') or 'none'}`",
        f"- 查看进度命令: `{((payload.get('product_entry_overview') or {}).get('progress_surface') or {}).get('command') or 'none'}`",
        f"- 恢复当前 loop 命令: `{((payload.get('product_entry_overview') or {}).get('resume_surface') or {}).get('command') or 'none'}`",
        "",
        "## Workspace Preview",
        "",
    ])
    if workspace_operator_brief:
        lines.append(
            f"- 当前 workspace 状态: {_operator_verdict_label(workspace_operator_brief.get('verdict'))}"
        )
        lines.append(f"- 当前 workspace 判断: {workspace_operator_brief.get('summary') or 'none'}")
        lines.append(
            f"- 当前 workspace 推荐命令: `{workspace_operator_brief.get('recommended_command') or 'none'}`"
        )
    else:
        lines.append("- 当前没有 workspace preview。")
    for item in payload.get("workspace_attention_queue_preview") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- 当前关注项: {item.get('title') or '未命名关注项'}")
        lines.append(f"- 处理命令: `{item.get('recommended_command') or 'none'}`")
        autonomy_contract = dict(item.get("autonomy_contract") or {})
        if autonomy_contract.get("summary"):
            lines.append(f"- 自治合同: {autonomy_contract.get('summary')}")
        autonomy_soak_status = dict(item.get("autonomy_soak_status") or {})
        if autonomy_soak_status.get("summary"):
            lines.append(f"- 自治 Proof / Soak: {autonomy_soak_status.get('summary')}")
        quality_closure_truth = dict(item.get("quality_closure_truth") or {})
        if quality_closure_truth.get("summary"):
            lines.append(f"- 质量闭环: {quality_closure_truth.get('summary')}")
        quality_execution_lane = dict(item.get("quality_execution_lane") or {})
        if quality_execution_lane.get("summary"):
            lines.append(f"- 质量执行线: {quality_execution_lane.get('summary')}")
        same_line_route_truth_preview = _same_line_route_truth_preview(item.get("same_line_route_truth"))
        if same_line_route_truth_preview:
            lines.append(f"- 同线路由: {same_line_route_truth_preview}")
        quality_review_loop_preview = _quality_review_loop_preview(item.get("quality_review_loop"))
        if quality_review_loop_preview:
            lines.append(f"- 质量评审闭环: {quality_review_loop_preview}")
        quality_review_followthrough_preview = _quality_review_followthrough_preview(
            item.get("quality_review_followthrough")
        )
        if quality_review_followthrough_preview:
            lines.append(f"- 质量复评跟进: {quality_review_followthrough_preview}")
        quality_repair_followthrough_preview = _quality_repair_followthrough_preview(
            item.get("quality_repair_followthrough")
        )
        if quality_repair_followthrough_preview:
            lines.append(f"- quality-repair 跟进: {quality_repair_followthrough_preview}")
        gate_clearing_followthrough_preview = _gate_clearing_followthrough_preview(
            item.get("gate_clearing_followthrough")
        )
        if gate_clearing_followthrough_preview:
            lines.append(f"- gate-clearing 跟进: {gate_clearing_followthrough_preview}")
        restore_point = dict(autonomy_contract.get("restore_point") or {})
        if restore_point.get("summary"):
            lines.append(f"- 恢复点: {restore_point.get('summary')}")
        operator_status_card = dict(item.get("operator_status_card") or {})
        if operator_status_card.get("handling_state"):
            lines.append(f"- 处理状态: `{operator_status_card.get('handling_state')}`")
        if operator_status_card.get("user_visible_verdict"):
            lines.append(f"- 当前处理结论: {operator_status_card.get('user_visible_verdict')}")
        if operator_status_card.get("next_confirmation_signal"):
            lines.append(f"- 下一确认信号: {operator_status_card.get('next_confirmation_signal')}")
    lines.extend([
        "",
        "## Phase 2 User Loop",
        "",
    ])
    lines.append(f"- program phase 摘要: {phase2_user_product_loop.get('summary') or 'none'}")
    lines.append(f"- 推荐动作: `{phase2_user_product_loop.get('recommended_step_id') or 'none'}`")
    lines.append(f"- 推荐命令: `{phase2_user_product_loop.get('recommended_command') or 'none'}`")
    for item in phase2_user_product_loop.get("single_path") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- 单一路径 `{item.get('step_id')}`: `{item.get('command') or 'none'}`")
    lines.extend([
        "",
        "## Guardrails",
        "",
    ])
    guardrail_classes = list(product_entry_guardrails.get("guardrail_classes") or [])
    if not guardrail_classes:
        lines.append("- `workspace_supervision_gap`: `none`")
    for item in guardrail_classes:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- `{item.get('guardrail_id')}`: `{item.get('recommended_command') or 'none'}`"
        )
    lines.extend(
        [
            "",
            "## Phase 3 Clearance",
            "",
        ]
    )
    lines.append(f"- 清障重点: {phase3_clearance_lane.get('summary') or 'none'}")
    lines.append(f"- 推荐动作: `{phase3_clearance_lane.get('recommended_step_id') or 'none'}`")
    lines.append(f"- 推荐命令: `{phase3_clearance_lane.get('recommended_command') or 'none'}`")
    clearance_targets = list(phase3_clearance_lane.get("clearance_targets") or [])
    if not clearance_targets:
        lines.append("- `external_runtime_contract`: `none`")
    for item in clearance_targets:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('target_id')}`: `{((item.get('commands') or ['none'])[0])}`")
    clearance_loop = list(phase3_clearance_lane.get("clearance_loop") or [])
    if not clearance_loop:
        lines.append("- 清障步骤 `refresh_supervision`: `none`")
    for item in clearance_loop:
        if not isinstance(item, dict):
            continue
        lines.append(f"- 清障步骤 `{item.get('step_id')}`: `{item.get('command') or 'none'}`")
    lines.extend(
        [
            "",
            "## Phase 4 Deconstruction",
            "",
        ]
    )
    substrate_targets = list(phase4_backend_deconstruction.get("substrate_targets") or [])
    if not substrate_targets:
        lines.append("- `session_run_watch_recovery`: none")
    for item in substrate_targets:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('capability_id')}`: {item.get('summary') or 'none'}")
    lines.extend([""])
    lines.extend(_render_phase5_platform_target_markdown_lines(phase5_platform_target))
    lines.extend(["", "## Entry Surfaces", ""])
    for name, item in entry_surfaces.items():
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{name}`: `{item.get('command') or 'none'}`")
    lines.append("")
    return "\n".join(lines)


def render_product_entry_preflight_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Product Entry Preflight",
        "",
        f"- 当前可直接尝试: {_bool_label(payload.get('ready_to_try_now'))}",
        f"- 当前摘要: {payload.get('summary') or 'none'}",
        f"- 前置检查命令: `{payload.get('recommended_check_command') or 'none'}`",
        f"- 推荐启动命令: `{payload.get('recommended_start_command') or 'none'}`",
        "",
        "## Checks",
        "",
    ]
    checks = list(payload.get("checks") or [])
    if checks:
        for check in checks:
            if not isinstance(check, dict):
                continue
            lines.append(
                "- "
                + f"`{check.get('check_id')}` "
                + f"[{_check_status_label(check.get('status'))}] "
                + f"({'阻塞项' if check.get('blocking') else '非阻塞项'}) "
                + f"{check.get('summary') or ''} "
                + f"`{check.get('command') or 'none'}`"
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def render_product_entry_start_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Product Entry Start",
        "",
        f"- 当前摘要: {payload.get('summary') or 'none'}",
        f"- 建议入口: {_start_mode_label(payload.get('recommended_mode_id'))}",
        f"- 恢复入口: {_surface_kind_label(((payload.get('resume_surface') or {}).get('surface_kind')))}",
        "",
        "## 可用入口",
        "",
    ]
    modes = list(payload.get("modes") or [])
    if modes:
        for mode in modes:
            if not isinstance(mode, dict):
                continue
            lines.append(
                "- "
                + f"{_start_mode_label(mode.get('mode_id'))}: "
                + f"`{mode.get('command') or 'none'}` "
                + f"{mode.get('summary') or ''}"
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)
