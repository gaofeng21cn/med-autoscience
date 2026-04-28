from __future__ import annotations

from typing import Any, Mapping

from .publication_runtime import *  # noqa: F403
from .progression import *  # noqa: F403
from .runtime_efficiency import *  # noqa: F403
from .shared import *  # noqa: F403


def _progress_blocker_labels(payload: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    for item in payload.get("current_blockers") or []:
        if not str(item).strip():
            continue
        label = _blocker_label(item) or str(item)
        if label not in blockers:
            blockers.append(label)
    return blockers


def _runtime_decision_context(
    payload: Mapping[str, Any],
    *,
    manual_finish_contract: dict[str, Any] | None,
    continuation_state: dict[str, Any],
) -> tuple[str, str, str]:
    if _manual_finish_active(manual_finish_contract):
        return (
            _manual_finish_runtime_decision_summary(manual_finish_contract),
            _manual_finish_runtime_reason_summary(manual_finish_contract),
            "",
        )
    runtime_decision = _runtime_decision_label(payload.get("runtime_decision")) or "未知"
    runtime_reason = _reason_label(payload.get("runtime_reason")) or _display_text(payload.get("runtime_reason")) or ""
    continuation_reason = (
        _continuation_reason_label(continuation_state.get("continuation_reason"))
        or str(continuation_state.get("continuation_reason") or "").strip()
    )
    return runtime_decision, runtime_reason, continuation_reason


def _current_stage_context(payload: Mapping[str, Any], status_human_view: Mapping[str, Any]) -> tuple[str, str]:
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
    return current_stage, current_judgment


def _followthrough_adjusted_summary(
    *,
    current_judgment: str,
    next_step_summary: str,
    quality_review_followthrough: Mapping[str, Any],
) -> tuple[str, str]:
    if not bool(quality_review_followthrough.get("waiting_auto_re_review")):
        return current_judgment, next_step_summary
    return (
        _non_empty_text(quality_review_followthrough.get("summary")) or current_judgment,
        _non_empty_text(quality_review_followthrough.get("blocking_reason"))
        or _non_empty_text(quality_review_followthrough.get("next_confirmation_signal"))
        or next_step_summary,
    )


def _build_markdown_context(payload: dict[str, Any]) -> dict[str, Any]:
    continuation_state = dict(payload.get("continuation_state") or {})
    manual_finish_contract = (
        dict(payload.get("manual_finish_contract") or {})
        if isinstance(payload.get("manual_finish_contract"), dict)
        else None
    )
    runtime_decision, runtime_reason, continuation_reason = _runtime_decision_context(
        payload,
        manual_finish_contract=manual_finish_contract,
        continuation_state=continuation_state,
    )
    status_human_view = _status_narration_human_view(payload)
    current_stage, current_judgment = _current_stage_context(payload, status_human_view)
    next_step_summary = _non_empty_text(status_human_view.get("next_step")) or str(
        payload.get("next_system_action") or ""
    ).strip()
    normalized_payload = _normalize_study_progress_payload(payload)
    quality_review_followthrough = _mapping_copy(normalized_payload.get("quality_review_followthrough"))
    current_judgment, next_step_summary = _followthrough_adjusted_summary(
        current_judgment=current_judgment,
        next_step_summary=next_step_summary,
        quality_review_followthrough=quality_review_followthrough,
    )
    intervention_lane = _mapping_copy(normalized_payload.get("intervention_lane"))
    recovery_contract = _mapping_copy(normalized_payload.get("recovery_contract"))
    return {
        "latest_events": [dict(item) for item in (payload.get("latest_events") or []) if isinstance(item, dict)],
        "blockers": _progress_blocker_labels(payload),
        "runtime_decision": runtime_decision,
        "runtime_reason": runtime_reason,
        "continuation_reason": continuation_reason,
        "runtime_health": _runtime_health_label(((payload.get("supervision") or {}).get("health_status"))) or "未知",
        "supervisor_tick_status": _supervisor_tick_status_label(
            ((payload.get("supervision") or {}).get("supervisor_tick_status"))
        )
        or "",
        "progress_freshness": dict(payload.get("progress_freshness") or {}),
        "task_intake": dict(payload.get("task_intake") or {}),
        "current_stage": current_stage,
        "current_judgment": current_judgment,
        "next_step_summary": next_step_summary,
        "normalized_payload": normalized_payload,
        "paper_stage": _paper_stage_label(normalized_payload.get("paper_stage")) or "未知",
        "intervention_title": _non_empty_text(intervention_lane.get("title")),
        "intervention_summary": _display_text(intervention_lane.get("summary"))
        or _non_empty_text(intervention_lane.get("summary")),
        "intervention_severity": _INTERVENTION_SEVERITY_LABELS.get(
            _non_empty_text(intervention_lane.get("severity")) or "",
            "",
        ),
        "operator_status_card": _mapping_copy(normalized_payload.get("operator_status_card")),
        "autonomy_contract": _mapping_copy(normalized_payload.get("autonomy_contract")),
        "quality_closure_truth": _mapping_copy(normalized_payload.get("quality_closure_truth")),
        "quality_execution_lane": _mapping_copy(normalized_payload.get("quality_execution_lane")),
        "same_line_route_truth": _mapping_copy(normalized_payload.get("same_line_route_truth")),
        "same_line_route_surface": _mapping_copy(normalized_payload.get("same_line_route_surface")),
        "quality_closure_basis": _mapping_copy(normalized_payload.get("quality_closure_basis")),
        "quality_review_agenda": _mapping_copy(normalized_payload.get("quality_review_agenda")),
        "quality_revision_plan": _mapping_copy(normalized_payload.get("quality_revision_plan")),
        "quality_review_loop": _mapping_copy(normalized_payload.get("quality_review_loop")),
        "quality_repair_batch_followthrough": _mapping_copy(
            normalized_payload.get("quality_repair_batch_followthrough")
        ),
        "gate_clearing_batch_followthrough": _mapping_copy(
            normalized_payload.get("gate_clearing_batch_followthrough")
        ),
        "quality_review_followthrough": quality_review_followthrough,
        "recovery_contract": recovery_contract,
        "recovery_action_mode": _RECOVERY_ACTION_MODE_LABELS.get(
            _non_empty_text(recovery_contract.get("action_mode")) or "",
            "",
        ),
        "recovery_steps": [
            dict(item)
            for item in (normalized_payload.get("recommended_commands") or [])
            if isinstance(item, dict)
        ],
        "module_surfaces": _mapping_copy(normalized_payload.get("module_surfaces")),
        "runtime_efficiency": _mapping_copy(normalized_payload.get("runtime_efficiency")),
    }


def _append_intervention_summary(lines: list[str], ctx: Mapping[str, Any]) -> None:
    if not (ctx["intervention_title"] or ctx["intervention_summary"]):
        return
    label = ctx["intervention_title"] or "继续监督当前 study"
    if ctx["intervention_severity"]:
        label = f"{label}（{ctx['intervention_severity']}）"
    lines.append(f"- 干预类型: {label}")
    if ctx["intervention_summary"]:
        lines.append(f"- 干预摘要: {ctx['intervention_summary']}")


def _append_task_intake_section(lines: list[str], task_intake: Mapping[str, Any]) -> None:
    if not task_intake:
        return
    lines.extend(["", "## 当前任务", "", f"- 任务意图: {task_intake.get('task_intent') or '未提供'}"])
    for key, label in (
        ("journal_target", "目标期刊"),
        ("entry_mode", "入口模式"),
        ("emitted_at", "任务写入时间"),
    ):
        if task_intake.get(key):
            lines.append(f"- {label}: {task_intake.get(key)}")
    first_cycle_outputs = [
        str(item).strip()
        for item in task_intake.get("first_cycle_outputs") or []
        if str(item).strip()
    ]
    if first_cycle_outputs:
        lines.append(f"- 首轮输出要求: {', '.join(first_cycle_outputs)}")


def _append_paper_runtime_section(lines: list[str], payload: Mapping[str, Any], ctx: Mapping[str, Any]) -> None:
    normalized_payload = ctx["normalized_payload"]
    lines.extend(
        [
            "",
            "## 论文推进",
            "",
            f"- 论文阶段: {ctx['paper_stage']}",
            f"- 论文摘要: {_display_text(normalized_payload.get('paper_stage_summary')) or str(normalized_payload.get('paper_stage_summary') or '').strip()}",
            "",
            "## 运行监管",
            "",
            f"- 运行健康: {ctx['runtime_health']}",
            f"- MAS 决策: {ctx['runtime_decision']}",
        ]
    )
    if ctx["supervisor_tick_status"]:
        lines.append(f"- MAS 监管心跳: {ctx['supervisor_tick_status']}")
    _append_progress_freshness(lines, ctx["progress_freshness"])
    if ctx["runtime_reason"]:
        lines.append(f"- 决策原因: {ctx['runtime_reason']}")
    if ctx["continuation_reason"]:
        lines.append(f"- continuation_reason: {ctx['continuation_reason']}")
    lines.extend(_runtime_efficiency_markdown_lines(ctx["runtime_efficiency"]))


def _append_progress_freshness(lines: list[str], progress_freshness: Mapping[str, Any]) -> None:
    progress_freshness_summary = _display_text(progress_freshness.get("summary")) or _non_empty_text(
        progress_freshness.get("summary")
    )
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


def _append_operator_status_card(lines: list[str], operator_status_card: Mapping[str, Any]) -> None:
    if not operator_status_card:
        return
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
    _append_operator_optional_lines(lines, operator_status_card)


def _append_operator_optional_lines(lines: list[str], operator_status_card: Mapping[str, Any]) -> None:
    if operator_status_card.get("owner_summary"):
        lines.append(f"- 责任说明: {operator_status_card.get('owner_summary')}")
    if operator_status_card.get("latest_truth_source_label") or operator_status_card.get("latest_truth_time"):
        truth_source = operator_status_card.get("latest_truth_source_label") or operator_status_card.get(
            "latest_truth_source"
        ) or "unknown"
        truth_time = operator_status_card.get("latest_truth_time") or "unknown"
        lines.append(f"- 当前真相源: {truth_source} @ {truth_time}")
    if operator_status_card.get("human_surface_summary"):
        lines.append(
            f"- 人类查看面: `{operator_status_card.get('human_surface_freshness') or 'unknown'}`；"
            f"{operator_status_card.get('human_surface_summary')}"
        )
    if operator_status_card.get("next_confirmation_signal"):
        lines.append(f"- 下一确认信号: {operator_status_card.get('next_confirmation_signal')}")


def _append_auto_re_review_section(lines: list[str], quality_review_followthrough: Mapping[str, Any]) -> None:
    if not bool(quality_review_followthrough.get("waiting_auto_re_review")):
        return
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
    for key, label in (
        ("summary", "后续摘要"),
        ("blocking_reason", "未自动继续原因"),
        ("next_confirmation_signal", "下一确认信号"),
    ):
        if quality_review_followthrough.get(key):
            lines.append(f"- {label}: {quality_review_followthrough.get(key)}")


def _append_batch_followthrough_section(lines: list[str], title: str, followthrough: Mapping[str, Any]) -> None:
    if not followthrough:
        return
    lines.extend(["", f"## {title}", "", f"- 当前状态: {followthrough.get('status') or 'unknown'}"])
    for key, label in (
        ("summary", "当前判断"),
        ("failed_unit_count", "失败单元数"),
        ("blocking_issue_count", "剩余 gate blocker"),
        ("next_confirmation_signal", "下一确认信号"),
    ):
        if followthrough.get(key) is not None:
            lines.append(f"- {label}: {followthrough.get(key)}")


def _append_same_line_route_section(lines: list[str], ctx: Mapping[str, Any]) -> None:
    same_line_route_truth = ctx["same_line_route_truth"]
    same_line_route_surface = ctx["same_line_route_surface"]
    if same_line_route_truth:
        _append_same_line_truth_section(lines, same_line_route_truth)
    elif same_line_route_surface:
        _append_same_line_surface_section(lines, same_line_route_surface)


def _append_same_line_truth_section(lines: list[str], same_line_route_truth: Mapping[str, Any]) -> None:
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


def _append_same_line_surface_section(lines: list[str], same_line_route_surface: Mapping[str, Any]) -> None:
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


def _append_module_surfaces(lines: list[str], module_surfaces: Mapping[str, Any]) -> None:
    if not module_surfaces:
        return
    lines.extend(["", "## 主线模块", ""])
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


def _append_blockers_and_next_step(lines: list[str], ctx: Mapping[str, Any]) -> None:
    lines.extend(["", "## 当前阻塞", ""])
    if ctx["blockers"]:
        lines.extend(f"- {item}" for item in ctx["blockers"])
    else:
        lines.append("- 当前没有额外阻塞记录。")
    lines.extend(["", "## 下一步", "", f"- 下一步建议: {ctx['next_step_summary']}"])


def _append_autonomy_contract(lines: list[str], autonomy_contract: Mapping[str, Any]) -> None:
    if not autonomy_contract:
        return
    lines.extend(["", "## 自治合同", ""])
    for key, label in (
        ("summary", "当前自治判断"),
        ("next_signal", "下一确认信号"),
    ):
        if autonomy_contract.get(key):
            lines.append(f"- {label}: {_display_text(autonomy_contract.get(key)) or autonomy_contract.get(key)}")
    if autonomy_contract.get("recommended_command"):
        lines.append(f"- 恢复/续跑命令: `{autonomy_contract.get('recommended_command')}`")
    _append_autonomy_restore_point(lines, autonomy_contract)
    _append_latest_outer_loop_dispatch(lines, autonomy_contract)


def _append_autonomy_restore_point(lines: list[str], autonomy_contract: Mapping[str, Any]) -> None:
    restore_point = dict(autonomy_contract.get("restore_point") or {})
    if restore_point.get("summary"):
        lines.append(f"- 恢复点: {_display_text(restore_point.get('summary')) or restore_point.get('summary')}")


def _append_latest_outer_loop_dispatch(lines: list[str], autonomy_contract: Mapping[str, Any]) -> None:
    latest_outer_loop_dispatch = dict(autonomy_contract.get("latest_outer_loop_dispatch") or {})
    if latest_outer_loop_dispatch.get("summary"):
        lines.append(
            "- 最近一次自治续跑: "
            + (
                _display_text(latest_outer_loop_dispatch.get("summary"))
                or latest_outer_loop_dispatch.get("summary")
            )
        )


def _append_autonomy_soak_status(lines: list[str], normalized_payload: Mapping[str, Any]) -> None:
    autonomy_soak_status = _mapping_copy(normalized_payload.get("autonomy_soak_status"))
    if not autonomy_soak_status:
        return
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


def _append_quality_closure(lines: list[str], ctx: Mapping[str, Any]) -> None:
    if not ctx["quality_closure_truth"]:
        return
    lines.extend(["", "## 质量闭环", ""])
    if ctx["quality_closure_truth"].get("summary"):
        lines.append(
            f"- 当前质量判断: {_display_text(ctx['quality_closure_truth'].get('summary')) or ctx['quality_closure_truth'].get('summary')}"
        )
    if ctx["quality_execution_lane"].get("summary"):
        lines.append(
            f"- 当前质量执行线: {_display_text(ctx['quality_execution_lane'].get('summary')) or ctx['quality_execution_lane'].get('summary')}"
        )
    _append_quality_closure_basis(lines, ctx["quality_closure_basis"])


def _append_quality_closure_basis(lines: list[str], quality_closure_basis: Mapping[str, Any]) -> None:
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


def _append_quality_review_agenda(lines: list[str], quality_review_agenda: Mapping[str, Any]) -> None:
    if not quality_review_agenda:
        return
    lines.extend(["", "## 质量评审议程", ""])
    for key, label in (
        ("top_priority_issue", "当前优先问题"),
        ("suggested_revision", "建议修订动作"),
        ("next_review_focus", "下一轮复评重点"),
    ):
        text = _display_text(quality_review_agenda.get(key)) or _non_empty_text(quality_review_agenda.get(key))
        if text:
            lines.append(f"- {label}: {text}")


def _append_quality_review_loop(lines: list[str], quality_review_loop: Mapping[str, Any]) -> None:
    if not quality_review_loop:
        return
    lines.extend(["", "## 质量评审闭环", ""])
    _append_quality_review_loop_header(lines, quality_review_loop)
    _append_quality_review_loop_lists(lines, quality_review_loop)


def _append_quality_review_loop_header(lines: list[str], quality_review_loop: Mapping[str, Any]) -> None:
    for key, label in (
        ("current_phase_label", "当前闭环阶段"),
        ("recommended_next_phase_label", "下一跳"),
        ("summary", "闭环摘要"),
        ("recommended_next_action", "下一动作"),
    ):
        text = _display_text(quality_review_loop.get(key)) or _non_empty_text(quality_review_loop.get(key))
        if text:
            lines.append(f"- {label}: {text}")
    if isinstance(quality_review_loop.get("blocking_issue_count"), int):
        lines.append(f"- 当前阻塞数: {quality_review_loop.get('blocking_issue_count')}")


def _append_quality_review_loop_lists(lines: list[str], quality_review_loop: Mapping[str, Any]) -> None:
    for item in [_display_text(issue) or _non_empty_text(issue) for issue in (quality_review_loop.get("blocking_issues") or [])]:
        if item:
            lines.append(f"- 当前阻塞项: {item}")
    for focus in [
        _display_text(item) or _non_empty_text(item)
        for item in (quality_review_loop.get("next_review_focus") or [])
    ]:
        if focus:
            lines.append(f"- 复评关注点: {focus}")


def _append_quality_revision_plan(lines: list[str], quality_revision_plan: Mapping[str, Any]) -> None:
    if not quality_revision_plan:
        return
    lines.extend(["", "## 质量修订计划", ""])
    overall_diagnosis = _display_text(quality_revision_plan.get("overall_diagnosis")) or _non_empty_text(
        quality_revision_plan.get("overall_diagnosis")
    )
    if overall_diagnosis:
        lines.append(f"- 总体诊断: {overall_diagnosis}")
    for item in [dict(entry) for entry in (quality_revision_plan.get("items") or []) if isinstance(entry, dict)]:
        _append_quality_revision_item(lines, item)
    for focus in [
        _display_text(item) or _non_empty_text(item)
        for item in (quality_revision_plan.get("next_review_focus") or [])
    ]:
        if focus:
            lines.append(f"- 下一轮复评关注: {focus}")


def _append_quality_revision_item(lines: list[str], item: Mapping[str, Any]) -> None:
    item_title = _quality_revision_item_title(item)
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


def _quality_revision_item_title(item: Mapping[str, Any]) -> str:
    priority = (_non_empty_text(item.get("priority")) or "p1").upper()
    dimension = _QUALITY_REVISION_DIMENSION_LABELS.get(
        _non_empty_text(item.get("dimension")) or "",
        _humanize_token(item.get("dimension")) or "未命名维度",
    )
    route_target = _display_text(item.get("route_target")) or _non_empty_text(item.get("route_target"))
    item_title = f"{priority} [{dimension}]"
    if route_target:
        item_title = f"{item_title} -> {route_target}"
    return item_title


def _append_recovery_contract(lines: list[str], ctx: Mapping[str, Any]) -> None:
    recovery_contract = ctx["recovery_contract"]
    if not recovery_contract:
        return
    lines.extend(["", "## 恢复合同", ""])
    if ctx["recovery_action_mode"]:
        lines.append(f"- 恢复模式: {ctx['recovery_action_mode']}")
    if recovery_contract.get("summary"):
        lines.append(f"- 合同摘要: {_display_text(recovery_contract.get('summary')) or recovery_contract.get('summary')}")
    for item in ctx["recovery_steps"]:
        title = _non_empty_text(item.get("title")) or _humanize_token(item.get("step_id")) or "未命名步骤"
        surface_label = (_non_empty_text(item.get("surface_kind")) or "unknown").replace("_", "-")
        command = _non_empty_text(item.get("command")) or "none"
        lines.append(f"- {title} [{surface_label}]: `{command}`")


def _append_user_judgment(lines: list[str], payload: Mapping[str, Any]) -> None:
    if payload.get("user_decision_summary") or payload.get("physician_decision_summary"):
        summary = payload.get("user_decision_summary") or payload.get("physician_decision_summary")
        lines.extend(["", "## 用户判断", "", f"- {str(summary or '').strip()}"])


def _append_recent_events(lines: list[str], latest_events: list[dict[str, Any]]) -> None:
    lines.extend(["", "## 最近进展", ""])
    if not latest_events:
        lines.append("- 目前没有可用的阶段事件。")
        return
    for item in latest_events:
        time_label = str(item.get("time_label") or item.get("timestamp") or "").strip()
        summary = _display_text(item.get("summary")) or str(item.get("summary") or "").strip()
        lines.append(f"- {time_label}: {summary}")


def _append_supervision_links(lines: list[str], payload: Mapping[str, Any]) -> None:
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


def render_study_progress_markdown(payload: dict[str, Any]) -> str:
    ctx = _build_markdown_context(payload)
    normalized_payload = ctx["normalized_payload"]
    lines = [
        "# 研究进度",
        "",
        f"- study_id: `{str(normalized_payload.get('study_id') or '')}`",
        f"- quest_id: `{str(normalized_payload.get('quest_id') or 'none')}`",
        f"- 当前阶段: {ctx['current_stage']}",
    ]
    if ctx["current_judgment"]:
        lines.append(f"- 当前判断: {ctx['current_judgment']}")
    _append_intervention_summary(lines, ctx)
    _append_task_intake_section(lines, ctx["task_intake"])
    _append_paper_runtime_section(lines, payload, ctx)
    _append_operator_status_card(lines, ctx["operator_status_card"])
    _append_auto_re_review_section(lines, ctx["quality_review_followthrough"])
    _append_batch_followthrough_section(lines, "Quality-Repair Batch", ctx["quality_repair_batch_followthrough"])
    _append_batch_followthrough_section(lines, "Gate-Clearing Batch", ctx["gate_clearing_batch_followthrough"])
    _append_same_line_route_section(lines, ctx)
    _append_module_surfaces(lines, ctx["module_surfaces"])
    _append_blockers_and_next_step(lines, ctx)
    _append_autonomy_contract(lines, ctx["autonomy_contract"])
    _append_autonomy_soak_status(lines, normalized_payload)
    _append_quality_closure(lines, ctx)
    _append_quality_review_agenda(lines, ctx["quality_review_agenda"])
    _append_quality_review_loop(lines, ctx["quality_review_loop"])
    _append_quality_revision_plan(lines, ctx["quality_revision_plan"])
    _append_recovery_contract(lines, ctx)
    _append_user_judgment(lines, payload)
    _append_recent_events(lines, ctx["latest_events"])
    _append_supervision_links(lines, payload)
    return "\n".join(lines) + "\n"


__all__ = ["render_study_progress_markdown"]
