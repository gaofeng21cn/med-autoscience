from __future__ import annotations

from typing import Any, Mapping

from .shared import *  # noqa: F403
from .publication_runtime import *  # noqa: F403
from .progression import *  # noqa: F403
from .runtime_efficiency import *  # noqa: F403

def render_study_progress_markdown(payload: dict[str, Any]) -> str:
    latest_events = [dict(item) for item in (payload.get("latest_events") or []) if isinstance(item, dict)]
    blockers: list[str] = []
    for item in payload.get("current_blockers") or []:
        if not str(item).strip():
            continue
        label = _blocker_label(item) or str(item)
        if label not in blockers:
            blockers.append(label)
    continuation_state = dict(payload.get("continuation_state") or {})
    manual_finish_contract = (
        dict(payload.get("manual_finish_contract") or {})
        if isinstance(payload.get("manual_finish_contract"), dict)
        else None
    )
    if _manual_finish_active(manual_finish_contract):
        runtime_decision = _manual_finish_runtime_decision_summary(manual_finish_contract)
        runtime_reason = _manual_finish_runtime_reason_summary(manual_finish_contract)
        continuation_reason = ""
    else:
        runtime_decision = _runtime_decision_label(payload.get("runtime_decision")) or "未知"
        runtime_reason = _reason_label(payload.get("runtime_reason")) or _display_text(payload.get("runtime_reason")) or ""
        continuation_reason = (
            _continuation_reason_label(continuation_state.get("continuation_reason"))
            or str(continuation_state.get("continuation_reason") or "").strip()
        )
    runtime_health = _runtime_health_label(((payload.get("supervision") or {}).get("health_status"))) or "未知"
    supervisor_tick_status = _supervisor_tick_status_label(((payload.get("supervision") or {}).get("supervisor_tick_status"))) or ""
    progress_freshness = dict(payload.get("progress_freshness") or {})
    task_intake = dict(payload.get("task_intake") or {})
    status_human_view = _status_narration_human_view(payload)
    has_status_contract = isinstance(payload.get("status_narration_contract"), Mapping)
    current_stage = _non_empty_text(status_human_view.get("current_stage_label")) or _current_stage_label(
        payload.get("current_stage")
    ) or "未知"
    if has_status_contract:
        current_judgment = _non_empty_text(status_human_view.get("status_summary")) or _non_empty_text(
            status_human_view.get("latest_update")
        )
    else:
        current_judgment = _non_empty_text(status_human_view.get("latest_update")) or _non_empty_text(
            status_human_view.get("status_summary")
        )
    if not current_judgment:
        current_judgment = _display_text(payload.get("current_stage_summary")) or str(
            payload.get("current_stage_summary") or ""
        ).strip()
    next_step_summary = _non_empty_text(status_human_view.get("next_step")) or str(
        payload.get("next_system_action") or ""
    ).strip()
    normalized_payload = _normalize_study_progress_payload(payload)
    paper_stage = _paper_stage_label(normalized_payload.get("paper_stage")) or "未知"
    intervention_lane = _mapping_copy(normalized_payload.get("intervention_lane"))
    intervention_title = _non_empty_text(intervention_lane.get("title"))
    intervention_summary = _display_text(intervention_lane.get("summary")) or _non_empty_text(
        intervention_lane.get("summary")
    )
    intervention_severity = _INTERVENTION_SEVERITY_LABELS.get(
        _non_empty_text(intervention_lane.get("severity")) or "",
        "",
    )
    operator_status_card = _mapping_copy(normalized_payload.get("operator_status_card"))
    autonomy_contract = _mapping_copy(normalized_payload.get("autonomy_contract"))
    quality_closure_truth = _mapping_copy(normalized_payload.get("quality_closure_truth"))
    quality_execution_lane = _mapping_copy(normalized_payload.get("quality_execution_lane"))
    same_line_route_truth = _mapping_copy(normalized_payload.get("same_line_route_truth"))
    same_line_route_surface = _mapping_copy(normalized_payload.get("same_line_route_surface"))
    quality_closure_basis = _mapping_copy(normalized_payload.get("quality_closure_basis"))
    quality_review_agenda = _mapping_copy(normalized_payload.get("quality_review_agenda"))
    quality_revision_plan = _mapping_copy(normalized_payload.get("quality_revision_plan"))
    quality_review_loop = _mapping_copy(normalized_payload.get("quality_review_loop"))
    quality_repair_batch_followthrough = _mapping_copy(normalized_payload.get("quality_repair_batch_followthrough"))
    gate_clearing_batch_followthrough = _mapping_copy(normalized_payload.get("gate_clearing_batch_followthrough"))
    quality_review_followthrough = _mapping_copy(normalized_payload.get("quality_review_followthrough"))
    recovery_contract = _mapping_copy(normalized_payload.get("recovery_contract"))
    module_surfaces = _mapping_copy(normalized_payload.get("module_surfaces"))
    runtime_efficiency = _mapping_copy(normalized_payload.get("runtime_efficiency"))
    if bool(quality_review_followthrough.get("waiting_auto_re_review")):
        current_judgment = _non_empty_text(quality_review_followthrough.get("summary")) or current_judgment
        next_step_summary = (
            _non_empty_text(quality_review_followthrough.get("blocking_reason"))
            or _non_empty_text(quality_review_followthrough.get("next_confirmation_signal"))
            or next_step_summary
        )
    recovery_action_mode = _RECOVERY_ACTION_MODE_LABELS.get(
        _non_empty_text(recovery_contract.get("action_mode")) or "",
        "",
    )
    recovery_steps = [
        dict(item)
        for item in (normalized_payload.get("recommended_commands") or [])
        if isinstance(item, dict)
    ]
    lines = [
        "# 研究进度",
        "",
        f"- study_id: `{str(normalized_payload.get('study_id') or '')}`",
        f"- quest_id: `{str(normalized_payload.get('quest_id') or 'none')}`",
        f"- 当前阶段: {current_stage}",
    ]
    if current_judgment:
        lines.append(f"- 当前判断: {current_judgment}")
    if intervention_title or intervention_summary:
        label = intervention_title or "继续监督当前 study"
        if intervention_severity:
            label = f"{label}（{intervention_severity}）"
        lines.extend(
            [
                f"- 干预类型: {label}",
            ]
        )
        if intervention_summary:
            lines.append(f"- 干预摘要: {intervention_summary}")
    if task_intake:
        lines.extend(
            [
                "",
                "## 当前任务",
                "",
                f"- 任务意图: {task_intake.get('task_intent') or '未提供'}",
            ]
        )
        if task_intake.get("journal_target"):
            lines.append(f"- 目标期刊: {task_intake.get('journal_target')}")
        if task_intake.get("entry_mode"):
            lines.append(f"- 入口模式: {task_intake.get('entry_mode')}")
        if task_intake.get("emitted_at"):
            lines.append(f"- 任务写入时间: {task_intake.get('emitted_at')}")
        first_cycle_outputs = [str(item).strip() for item in task_intake.get("first_cycle_outputs") or [] if str(item).strip()]
        if first_cycle_outputs:
            lines.append(f"- 首轮输出要求: {', '.join(first_cycle_outputs)}")
    lines.extend(
        [
            "",
            "## 论文推进",
            "",
            f"- 论文阶段: {paper_stage}",
            f"- 论文摘要: {_display_text(normalized_payload.get('paper_stage_summary')) or str(normalized_payload.get('paper_stage_summary') or '').strip()}",
            "",
            "## 运行监管",
            "",
            f"- 运行健康: {runtime_health}",
            f"- MAS 决策: {runtime_decision}",
        ]
    )
    if supervisor_tick_status:
        lines.append(f"- MAS 监管心跳: {supervisor_tick_status}")
    progress_freshness_summary = _display_text(progress_freshness.get("summary")) or _non_empty_text(progress_freshness.get("summary"))
    if progress_freshness_summary:
        progress_status_label = _progress_freshness_status_label(progress_freshness.get("status"))
        if progress_status_label:
            lines.append(f"- 研究进度信号: {progress_status_label}；{progress_freshness_summary}")
        else:
            lines.append(f"- 研究进度信号: {progress_freshness_summary}")
    if progress_freshness.get("latest_progress_time_label") and progress_freshness.get("latest_progress_summary"):
        lines.append(
            f"- 最近明确推进: {progress_freshness.get('latest_progress_time_label')}，"
            f"{progress_freshness.get('latest_progress_summary')}"
        )
    if runtime_reason:
        lines.append(f"- 决策原因: {runtime_reason}")
    if continuation_reason:
        lines.append(f"- continuation_reason: {continuation_reason}")
    lines.extend(_runtime_efficiency_markdown_lines(runtime_efficiency))
    if operator_status_card:
        lines.extend(
            [
                "",
                "## 操作员状态卡",
                "",
                f"- 当前处理态: {operator_status_card.get('handling_state_label') or operator_status_card.get('handling_state') or '未知'}",
                f"- 用户可见结论: {operator_status_card.get('user_visible_verdict') or 'none'}",
                f"- 当前聚焦: {operator_status_card.get('current_focus') or 'none'}",
            ]
        )
        if operator_status_card.get("owner_summary"):
            lines.append(f"- 责任说明: {operator_status_card.get('owner_summary')}")
        if operator_status_card.get("latest_truth_source_label") or operator_status_card.get("latest_truth_time"):
            truth_source = operator_status_card.get("latest_truth_source_label") or operator_status_card.get("latest_truth_source") or "unknown"
            truth_time = operator_status_card.get("latest_truth_time") or "unknown"
            lines.append(f"- 当前真相源: {truth_source} @ {truth_time}")
        if operator_status_card.get("human_surface_summary"):
            lines.append(
                f"- 人类查看面: `{operator_status_card.get('human_surface_freshness') or 'unknown'}`；"
                f"{operator_status_card.get('human_surface_summary')}"
            )
        if operator_status_card.get("next_confirmation_signal"):
            lines.append(f"- 下一确认信号: {operator_status_card.get('next_confirmation_signal')}")
    if bool(quality_review_followthrough.get("waiting_auto_re_review")):
        lines.extend(
            [
                "",
                "## 自动复评后续",
                "",
                f"- 当前状态: {quality_review_followthrough.get('state_label') or quality_review_followthrough.get('state') or '未知'}",
                (
                    "- 系统自动继续: 会"
                    if bool(quality_review_followthrough.get("auto_continue_expected"))
                    else "- 系统自动继续: 不会"
                ),
            ]
        )
        if quality_review_followthrough.get("summary"):
            lines.append(f"- 后续摘要: {quality_review_followthrough.get('summary')}")
        if quality_review_followthrough.get("blocking_reason"):
            lines.append(f"- 未自动继续原因: {quality_review_followthrough.get('blocking_reason')}")
        if quality_review_followthrough.get("next_confirmation_signal"):
            lines.append(f"- 下一确认信号: {quality_review_followthrough.get('next_confirmation_signal')}")
    if quality_repair_batch_followthrough:
        lines.extend(
            [
                "",
                "## Quality-Repair Batch",
                "",
                f"- 当前状态: {quality_repair_batch_followthrough.get('status') or 'unknown'}",
            ]
        )
        if quality_repair_batch_followthrough.get("summary"):
            lines.append(f"- 当前判断: {quality_repair_batch_followthrough.get('summary')}")
        if quality_repair_batch_followthrough.get("failed_unit_count") is not None:
            lines.append(f"- 失败单元数: {quality_repair_batch_followthrough.get('failed_unit_count')}")
        if quality_repair_batch_followthrough.get("blocking_issue_count") is not None:
            lines.append(f"- 剩余 gate blocker: {quality_repair_batch_followthrough.get('blocking_issue_count')}")
        if quality_repair_batch_followthrough.get("next_confirmation_signal"):
            lines.append(f"- 下一确认信号: {quality_repair_batch_followthrough.get('next_confirmation_signal')}")
    if gate_clearing_batch_followthrough:
        lines.extend(
            [
                "",
                "## Gate-Clearing Batch",
                "",
                f"- 当前状态: {gate_clearing_batch_followthrough.get('status') or 'unknown'}",
            ]
        )
        if gate_clearing_batch_followthrough.get("summary"):
            lines.append(f"- 当前判断: {gate_clearing_batch_followthrough.get('summary')}")
        if gate_clearing_batch_followthrough.get("failed_unit_count") is not None:
            lines.append(f"- 失败单元数: {gate_clearing_batch_followthrough.get('failed_unit_count')}")
        if gate_clearing_batch_followthrough.get("blocking_issue_count") is not None:
            lines.append(f"- 剩余 gate blocker: {gate_clearing_batch_followthrough.get('blocking_issue_count')}")
        if gate_clearing_batch_followthrough.get("next_confirmation_signal"):
            lines.append(f"- 下一确认信号: {gate_clearing_batch_followthrough.get('next_confirmation_signal')}")
    if same_line_route_truth:
        lines.extend(
            [
                "",
                "## 同线路由真相",
                "",
                f"- 路由状态: {same_line_route_truth.get('same_line_state_label') or '未知'}",
                f"- 当前判断: {same_line_route_truth.get('summary') or 'none'}",
                f"- 当前关键问题: {same_line_route_truth.get('current_focus') or 'none'}",
            ]
        )
        if same_line_route_truth.get("route_target_label") or same_line_route_truth.get("route_target"):
            lines.append(
                f"- 收口目标: {same_line_route_truth.get('route_target_label') or same_line_route_truth.get('route_target')}"
            )
    elif same_line_route_surface:
        lines.extend(
            [
                "",
                "## 同线收口动作",
                "",
                f"- 收口目标: {same_line_route_surface.get('route_target_label') or same_line_route_surface.get('route_target') or '未知'}",
                f"- 当前判断: {same_line_route_surface.get('summary') or 'none'}",
                f"- 当前关键问题: {same_line_route_surface.get('route_key_question') or 'none'}",
            ]
        )
        if same_line_route_surface.get("why_now"):
            lines.append(f"- 为什么现在做: {same_line_route_surface.get('why_now')}")
    if module_surfaces:
        lines.extend(
            [
                "",
                "## 主线模块",
                "",
            ]
        )
        for module_name in ("controller_charter", "runtime", "eval_hygiene"):
            module_surface = dict(module_surfaces.get(module_name) or {})
            if not module_surface:
                continue
            lines.append(
                "- "
                + module_name
                + ": "
                + (module_surface.get("status_summary") or "none")
                + " 下一动作："
                + (module_surface.get("next_action_summary") or "none")
                + " ref: `"
                + (module_surface.get("summary_ref") or "none")
                + "`"
            )
    lines.extend(
        [
            "",
        "## 当前阻塞",
        "",
        ]
    )
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- 当前没有额外阻塞记录。")
    lines.extend(
        [
            "",
            "## 下一步",
            "",
            f"- 下一步建议: {next_step_summary}",
        ]
    )
    if autonomy_contract:
        lines.extend(["", "## 自治合同", ""])
        if autonomy_contract.get("summary"):
            lines.append(
                f"- 当前自治判断: {_display_text(autonomy_contract.get('summary')) or autonomy_contract.get('summary')}"
            )
        if autonomy_contract.get("next_signal"):
            lines.append(
                f"- 下一确认信号: {_display_text(autonomy_contract.get('next_signal')) or autonomy_contract.get('next_signal')}"
            )
        if autonomy_contract.get("recommended_command"):
            lines.append(f"- 恢复/续跑命令: `{autonomy_contract.get('recommended_command')}`")
        restore_point = dict(autonomy_contract.get("restore_point") or {})
        if restore_point.get("summary"):
            lines.append(
                f"- 恢复点: {_display_text(restore_point.get('summary')) or restore_point.get('summary')}"
            )
        latest_outer_loop_dispatch = dict(autonomy_contract.get("latest_outer_loop_dispatch") or {})
        if latest_outer_loop_dispatch.get("summary"):
            lines.append(
                "- 最近一次自治续跑: "
                + (
                    _display_text(latest_outer_loop_dispatch.get("summary"))
                    or latest_outer_loop_dispatch.get("summary")
                )
            )
    autonomy_soak_status = _mapping_copy(normalized_payload.get("autonomy_soak_status"))
    if autonomy_soak_status:
        lines.extend(["", "## 自治 Proof / Soak", ""])
        if autonomy_soak_status.get("summary"):
            lines.append(
                f"- 当前自治证据: {_display_text(autonomy_soak_status.get('summary')) or autonomy_soak_status.get('summary')}"
            )
        if autonomy_soak_status.get("progress_freshness_status"):
            lines.append(f"- 进度新鲜度: `{autonomy_soak_status.get('progress_freshness_status')}`")
        if autonomy_soak_status.get("next_confirmation_signal"):
            lines.append(
                "- 下一确认信号: "
                + (
                    _display_text(autonomy_soak_status.get("next_confirmation_signal"))
                    or autonomy_soak_status.get("next_confirmation_signal")
                )
            )
    if quality_closure_truth:
        lines.extend(["", "## 质量闭环", ""])
        if quality_closure_truth.get("summary"):
            lines.append(
                f"- 当前质量判断: {_display_text(quality_closure_truth.get('summary')) or quality_closure_truth.get('summary')}"
            )
        if quality_execution_lane.get("summary"):
            lines.append(
                f"- 当前质量执行线: {_display_text(quality_execution_lane.get('summary')) or quality_execution_lane.get('summary')}"
            )
        for key in (
            "clinical_significance",
            "evidence_strength",
            "novelty_positioning",
            "human_review_readiness",
            "publication_gate",
        ):
            basis_item = dict(quality_closure_basis.get(key) or {})
            summary = _display_text(basis_item.get("summary")) or basis_item.get("summary")
            if summary:
                lines.append(f"- {_QUALITY_CLOSURE_BASIS_LABELS.get(key, key)}: {summary}")
    if quality_review_agenda:
        lines.extend(["", "## 质量评审议程", ""])
        top_priority_issue = _display_text(quality_review_agenda.get("top_priority_issue")) or _non_empty_text(
            quality_review_agenda.get("top_priority_issue")
        )
        suggested_revision = _display_text(quality_review_agenda.get("suggested_revision")) or _non_empty_text(
            quality_review_agenda.get("suggested_revision")
        )
        next_review_focus = _display_text(quality_review_agenda.get("next_review_focus")) or _non_empty_text(
            quality_review_agenda.get("next_review_focus")
        )
        if top_priority_issue:
            lines.append(f"- 当前优先问题: {top_priority_issue}")
        if suggested_revision:
            lines.append(f"- 建议修订动作: {suggested_revision}")
        if next_review_focus:
            lines.append(f"- 下一轮复评重点: {next_review_focus}")
    if quality_review_loop:
        lines.extend(["", "## 质量评审闭环", ""])
        current_phase_label = _display_text(quality_review_loop.get("current_phase_label")) or _non_empty_text(
            quality_review_loop.get("current_phase_label")
        )
        recommended_next_phase_label = _display_text(
            quality_review_loop.get("recommended_next_phase_label")
        ) or _non_empty_text(quality_review_loop.get("recommended_next_phase_label"))
        summary = _display_text(quality_review_loop.get("summary")) or _non_empty_text(quality_review_loop.get("summary"))
        recommended_next_action = _display_text(quality_review_loop.get("recommended_next_action")) or _non_empty_text(
            quality_review_loop.get("recommended_next_action")
        )
        if current_phase_label:
            lines.append(f"- 当前闭环阶段: {current_phase_label}")
        if recommended_next_phase_label:
            lines.append(f"- 下一跳: {recommended_next_phase_label}")
        if isinstance(quality_review_loop.get("blocking_issue_count"), int):
            lines.append(f"- 当前阻塞数: {quality_review_loop.get('blocking_issue_count')}")
        if summary:
            lines.append(f"- 闭环摘要: {summary}")
        if recommended_next_action:
            lines.append(f"- 下一动作: {recommended_next_action}")
        for item in [
            _display_text(issue) or _non_empty_text(issue)
            for issue in (quality_review_loop.get("blocking_issues") or [])
        ]:
            if item:
                lines.append(f"- 当前阻塞项: {item}")
        for focus in [
            _display_text(item) or _non_empty_text(item)
            for item in (quality_review_loop.get("next_review_focus") or [])
        ]:
            if focus:
                lines.append(f"- 复评关注点: {focus}")
    if quality_revision_plan:
        lines.extend(["", "## 质量修订计划", ""])
        overall_diagnosis = _display_text(quality_revision_plan.get("overall_diagnosis")) or _non_empty_text(
            quality_revision_plan.get("overall_diagnosis")
        )
        if overall_diagnosis:
            lines.append(f"- 总体诊断: {overall_diagnosis}")
        for item in [dict(entry) for entry in (quality_revision_plan.get("items") or []) if isinstance(entry, dict)]:
            priority = (_non_empty_text(item.get("priority")) or "p1").upper()
            dimension = _QUALITY_REVISION_DIMENSION_LABELS.get(
                _non_empty_text(item.get("dimension")) or "",
                _humanize_token(item.get("dimension")) or "未命名维度",
            )
            route_target = _display_text(item.get("route_target")) or _non_empty_text(item.get("route_target"))
            item_title = f"{priority} [{dimension}]"
            if route_target:
                item_title = f"{item_title} -> {route_target}"
            action = _display_text(item.get("action")) or _non_empty_text(item.get("action"))
            rationale = _display_text(item.get("rationale")) or _non_empty_text(item.get("rationale"))
            done_criteria = _display_text(item.get("done_criteria")) or _non_empty_text(item.get("done_criteria"))
            if action:
                lines.append(f"- {item_title}: {action}")
            else:
                lines.append(f"- {item_title}")
            if rationale:
                lines.append(f"- 修订理由: {rationale}")
            if done_criteria:
                lines.append(f"- 完成标准: {done_criteria}")
        for focus in [
            _display_text(item) or _non_empty_text(item)
            for item in (quality_revision_plan.get("next_review_focus") or [])
        ]:
            if focus:
                lines.append(f"- 下一轮复评关注: {focus}")
    if recovery_contract:
        lines.extend(["", "## 恢复合同", ""])
        if recovery_action_mode:
            lines.append(f"- 恢复模式: {recovery_action_mode}")
        if recovery_contract.get("summary"):
            lines.append(
                f"- 合同摘要: {_display_text(recovery_contract.get('summary')) or recovery_contract.get('summary')}"
            )
        for item in recovery_steps:
            title = _non_empty_text(item.get("title")) or _humanize_token(item.get("step_id")) or "未命名步骤"
            surface_label = (_non_empty_text(item.get("surface_kind")) or "unknown").replace("_", "-")
            command = _non_empty_text(item.get("command")) or "none"
            lines.append(f"- {title} [{surface_label}]: `{command}`")
    if payload.get("user_decision_summary") or payload.get("physician_decision_summary"):
        summary = payload.get("user_decision_summary") or payload.get("physician_decision_summary")
        lines.extend(["", "## 用户判断", "", f"- {str(summary or '').strip()}"])
    lines.extend(["", "## 最近进展", ""])
    if latest_events:
        for item in latest_events:
            time_label = str(item.get("time_label") or item.get("timestamp") or "").strip()
            summary = _display_text(item.get("summary")) or str(item.get("summary") or "").strip()
            lines.append(f"- {time_label}: {summary}")
    else:
        lines.append("- 目前没有可用的阶段事件。")
    supervision = dict(payload.get("supervision") or {})
    lines.extend(["", "## 监督入口", ""])
    supervision_labels = {
        "browser_url": "监控入口",
        "quest_session_api_url": "会话接口",
        "active_run_id": "active_run_id",
        "launch_report_path": "launch_report_path",
    }
    for key in ("browser_url", "quest_session_api_url", "active_run_id", "launch_report_path"):
        value = str(supervision.get(key) or "").strip()
        if value:
            lines.append(f"- {supervision_labels[key]}: `{value}`")
    return "\n".join(lines) + "\n"
__all__ = ["render_study_progress_markdown"]
