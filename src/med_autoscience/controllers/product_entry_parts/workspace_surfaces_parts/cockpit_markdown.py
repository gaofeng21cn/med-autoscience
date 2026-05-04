from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.medical_paper_research_loop import research_loop_markdown_lines


def render_workspace_cockpit_markdown(payload: dict[str, Any]) -> str:
    mainline_snapshot = dict(payload.get("mainline_snapshot") or {})
    workspace_supervision = dict(payload.get("workspace_supervision") or {})
    service = dict(workspace_supervision.get("service") or {})
    study_counts = dict(workspace_supervision.get("study_counts") or {})
    operator_brief = dict(payload.get("operator_brief") or {})
    phase2_user_product_loop = dict(payload.get("phase2_user_product_loop") or {})
    lines = [
        "# Workspace Cockpit",
        "",
        f"- profile: `{payload.get('profile_name')}`",
        f"- workspace_root: `{payload.get('workspace_root')}`",
        f"- 当前 workspace 状态: {_workspace_status_label(payload.get('workspace_status'))}",
        "",
        "## Now",
        "",
    ]
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
    lines.extend([
        "",
        "## Mainline Snapshot",
        "",
    ])
    if mainline_snapshot:
        lines.append(f"- 当前 program: `{mainline_snapshot.get('program_id') or 'unknown'}`")
        lines.append(f"- 当前主线阶段: `{mainline_snapshot.get('current_stage_id') or 'unknown'}`")
        if mainline_snapshot.get("current_stage_summary"):
            lines.append(f"- 当前判断: {mainline_snapshot.get('current_stage_summary')}")
        if mainline_snapshot.get("current_program_phase_id"):
            lines.append(
                f"- 当前 program phase: `{mainline_snapshot.get('current_program_phase_id')}`"
            )
        if mainline_snapshot.get("current_program_phase_summary"):
            lines.append(f"- program phase 摘要: {mainline_snapshot.get('current_program_phase_summary')}")
        next_focus = list(mainline_snapshot.get("next_focus") or [])
        if next_focus:
            lines.append(f"- 下一步焦点: {next_focus[0]}")
    else:
        lines.append("- 当前还没有 repo 主线快照。")
    lines.extend([
        "",
        "## Workspace Supervision",
        "",
    ])
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
    lines.extend(["", "## 自动医学论文能力闭环 / Medical Paper Readiness", ""])
    readiness_state = dict(payload.get("medical_paper_readiness_state") or {})
    if readiness_state:
        counts = dict(readiness_state.get("counts") or {})
        lines.append(f"- 当前 readiness 摘要: {readiness_state.get('summary') or 'none'}")
        lines.append(
            "- 当前计数: "
            f"已接入 {counts.get('projected_count', 0)}；"
            f"ready {counts.get('ready', 0)}；"
            f"需要关注 {counts.get('attention_required', 0)}；"
            f"missing {counts.get('missing', 0)}"
        )
        for study in readiness_state.get("studies") or []:
            if not isinstance(study, Mapping):
                continue
            next_action = dict(study.get("next_action") or {})
            lines.append(
                f"- `{study.get('study_id') or 'unknown-study'}` overall_status: "
                f"`{study.get('overall_status') or 'unknown'}` "
                f"({study.get('ready_count', 0)}/{study.get('required_count', 0)})"
            )
            if next_action.get("summary"):
                lines.append(f"  下一步: {next_action.get('summary')}")
            action_cards = [card for card in study.get("action_cards") or [] if isinstance(card, Mapping)]
            if action_cards:
                labels = "；".join(
                    _readiness_action_card_label(card) for card in action_cards if card.get("label")
                )
                if labels:
                    lines.append(f"  动作卡: {labels}")
            lines.append("  quality authorization: projection-only")
    else:
        lines.append("- 当前还没有 Medical Paper Readiness projection。")
    lines.extend(["", "## v4 生产运行面 / Medical Paper Operations", ""])
    v4_operations_state = dict(payload.get("medical_paper_v4_operations_state") or {})
    if v4_operations_state:
        counts = dict(v4_operations_state.get("counts") or {})
        lines.append(f"- 当前 v4 operations 摘要: {v4_operations_state.get('summary') or 'none'}")
        lines.append(
            "- 当前计数: "
            f"study {counts.get('study_count', 0)}；"
            f"ready {counts.get('ready', 0)}；"
            f"partial {counts.get('partial', 0)}；"
            f"blocked {counts.get('blocked', 0)}"
        )
        for study in v4_operations_state.get("studies") or []:
            if not isinstance(study, Mapping):
                continue
            next_action = dict(study.get("next_action") or {})
            lines.append(
                f"- `{study.get('study_id') or 'unknown-study'}` v4 operations: "
                f"`{study.get('overall_status') or 'unknown'}`；"
                f"下一步 `{next_action.get('summary') or 'none'}`"
            )
    else:
        lines.append("- 当前还没有 v4 operations projection。")
    lines.extend(["", "## v5 运营健康闭环 / Medical Paper Ops Health", ""])
    ops_health_state = dict(payload.get("medical_paper_ops_health_state") or {})
    if ops_health_state:
        counts = dict(ops_health_state.get("counts") or {})
        lines.append(f"- 当前 ops health 摘要: {ops_health_state.get('summary') or 'none'}")
        lines.append(f"- last-green: `{ops_health_state.get('last_green_at') or 'none'}`")
        lines.append(
            "- 当前计数: "
            f"study {counts.get('study_count', 0)}；"
            f"ready {counts.get('ready', 0)}；"
            f"partial {counts.get('partial', 0)}；"
            f"blocked {counts.get('blocked', 0)}"
        )
        for study in ops_health_state.get("studies") or []:
            if not isinstance(study, Mapping):
                continue
            next_action = dict(study.get("next_operator_action") or {})
            lines.append(
                f"- `{study.get('study_id') or 'unknown-study'}` ops health: "
                f"`{study.get('overall_status') or 'unknown'}`；"
                f"下一步 `{next_action.get('summary') or 'none'}`"
            )
    else:
        lines.append("- 当前还没有 v5 ops health projection。")
    research_loop_state = dict(payload.get("medical_paper_research_loop_state") or {})
    if research_loop_state:
        lines.extend(research_loop_markdown_lines(research_loop_state))
        for study in research_loop_state.get("studies") or []:
            if not isinstance(study, Mapping):
                continue
            lines.append(
                f"- `{study.get('study_id') or 'unknown-study'}` research loop: "
                f"`{study.get('overall_status') or 'unknown'}`"
            )
            lines.extend(research_loop_markdown_lines(study, heading=False))
    else:
        lines.extend(["", "## 自动论文科研闭环 / Medical Paper Research Loop", ""])
        lines.append("- 当前还没有 Medical Paper Research Loop projection。")
    lines.extend(["", "## AI-first Operations", ""])
    ai_first_operations_state = dict(payload.get("ai_first_operations_state") or {})
    if ai_first_operations_state:
        counts = dict(ai_first_operations_state.get("counts") or {})
        lines.append(f"- 当前 operations 摘要: {ai_first_operations_state.get('summary') or 'none'}")
        lines.append(
            "- 当前计数: "
            f"已接入 {counts.get('dashboard_count', 0)}；"
            f"AI reviewer trace 不完整 {counts.get('ai_reviewer_trace_incomplete', 0)}；"
            f"route-back 未闭环 {counts.get('route_back_active', 0)}；"
            f"产物待刷新 {counts.get('artifact_refresh_pending', 0)}；"
            f"等待人工判断 {counts.get('human_review_required', 0)}；"
            f"运行反馈 {counts.get('open_feedback_count', 0)}；"
            f"重复返工 {counts.get('repeat_toil_count', 0)}；"
            f"动作未闭合 {counts.get('action_active', 0)}；"
            f"动作阻塞 {counts.get('action_blocked', 0)}；"
            f"quality learning open priorities {counts.get('quality_learning_open_priority_count', 0)}；"
            f"system improvements {counts.get('quality_learning_system_improvement_count', 0)}"
        )
        for dashboard in ai_first_operations_state.get("study_dashboards") or []:
            if not isinstance(dashboard, Mapping):
                continue
            study_id = dashboard.get("study_id") or "unknown-study"
            lines.append(f"- `{study_id}` operations: {dashboard.get('current_stage') or 'unknown'}")
            if dashboard.get("pre_draft_status"):
                lines.append(f"  pre-draft: {dashboard.get('pre_draft_status')}")
            if dashboard.get("ai_reviewer_workflow_status"):
                lines.append(
                    f"  AI reviewer workflow: {dashboard.get('ai_reviewer_workflow_status')}"
                )
            if dashboard.get("artifact_proof_status"):
                lines.append(f"  artifact proof: {dashboard.get('artifact_proof_status')}")
            if dashboard.get("route_back_status"):
                lines.append(f"  route-back: {dashboard.get('route_back_status')}")
            if dashboard.get("next_step"):
                lines.append(f"  下一步: {dashboard.get('next_step')}")
            if dashboard.get("human_judgment"):
                lines.append(f"  人工判断: {dashboard.get('human_judgment')}")
            if dashboard.get("feedback_summary"):
                lines.append(f"  运行反馈: {dashboard.get('feedback_summary')}")
            if dashboard.get("feedback_primary_reason"):
                lines.append(f"  反馈原因: {dashboard.get('feedback_primary_reason')}")
            if dashboard.get("feedback_action_summary"):
                lines.append(f"  建议动作: {dashboard.get('feedback_action_summary')}")
            if dashboard.get("action_primary_summary"):
                lines.append(
                    "  动作生命周期: "
                    f"{dashboard.get('action_primary_status') or 'unknown'}；"
                    f"{dashboard.get('action_primary_summary')}"
                )
            if dashboard.get("quality_learning_operations_report_summary"):
                lines.append(
                    f"  Quality learning operations: {dashboard.get('quality_learning_operations_report_summary')}"
                )
            top_open_priority = dict(dashboard.get("quality_learning_top_open_priority") or {})
            if top_open_priority:
                lines.append(
                    "  Maintainer priority: "
                    f"{top_open_priority.get('reason')} | "
                    f"frequency={top_open_priority.get('frequency')} | "
                    f"impact={top_open_priority.get('impact_entry')} | "
                    f"fix_layer={top_open_priority.get('suggested_fix_layer')}"
                )
            top_system_improvement = dict(dashboard.get("quality_learning_top_system_improvement") or {})
            if top_system_improvement:
                lines.append(
                    "  System improvement priority: "
                    f"{top_system_improvement.get('reason')} | "
                    f"frequency={top_system_improvement.get('frequency')} | "
                    f"impact={top_system_improvement.get('impact_entry')} | "
                    f"fix_layer={top_system_improvement.get('suggested_fix_layer')}"
                )
            if dashboard.get("ai_reviewer_trace_complete") is not None:
                lines.append(
                    "  AI reviewer trace: "
                    + ("完整" if dashboard.get("ai_reviewer_trace_complete") else "不完整")
                )
            if dashboard.get("route_back_count"):
                lines.append(
                    f"  route-back: {dashboard.get('route_back_count')} -> {dashboard.get('route_back_target') or 'unknown'}"
                )
            if dashboard.get("stale_artifact_count"):
                lines.append(f"  产物刷新: {dashboard.get('stale_artifact_count')} 个待刷新")
    else:
        lines.append("- 当前还没有 AI-first operations runtime state。")
    lines.extend(["", "## AI-first Cross-Study Completion", ""])
    completion_projection = dict(payload.get("ai_first_cross_study_completion_projection") or {})
    if completion_projection:
        user_view = dict(completion_projection.get("user_view") or {})
        maintainer_view = dict(completion_projection.get("maintainer_view") or {})
        lines.append(f"- 当前 completion 状态: {user_view.get('status') or completion_projection.get('status') or 'unknown'}")
        lines.append(
            "- 当前计数: "
            f"study {user_view.get('study_count', 0)}；"
            f"需要关注 {user_view.get('attention_required_count', 0)}；"
            f"等待人工判断 {user_view.get('human_review_required_count', 0)}；"
            f"观测不足 {maintainer_view.get('insufficient_observability_count', 0)}"
        )
        if user_view.get("primary_next_action"):
            lines.append(f"- 主下一步: {user_view.get('primary_next_action')}")
        for study in completion_projection.get("studies") or []:
            if not isinstance(study, Mapping):
                continue
            study_id = study.get("study_id") or "unknown-study"
            study_user = dict(study.get("user_view") or {})
            maintainer = dict(study.get("maintainer_view") or {})
            feedback = dict(maintainer.get("feedback") or {})
            dispatch = dict(maintainer.get("dispatch") or {})
            ai_reviewer = dict(maintainer.get("ai_reviewer_authority") or {})
            artifact = dict(maintainer.get("artifact_proof") or {})
            human_review = dict(maintainer.get("human_review") or {})
            external_owner = dict(maintainer.get("external_owner") or {})
            lines.append(f"- `{study_id}` completion: {study_user.get('status') or study.get('status') or 'unknown'}")
            lines.append(
                "  feedback: "
                f"{feedback.get('open_feedback_count', 0)} open；"
                f"dispatch: {dispatch.get('open_action_count', 0)} open / {dispatch.get('total_action_count', 0)} total / {dispatch.get('latest_status') or 'unknown'}；"
                f"AI reviewer: {ai_reviewer.get('owner') or 'unknown'} "
                f"({'backed' if ai_reviewer.get('reviewer_backed') else 'not backed'})"
            )
            lines.append(
                "  artifact proof: "
                f"{artifact.get('rebuild_status') or 'unknown'}；"
                f"human gate: {'open' if human_review.get('required') else 'closed'}；"
                f"external owner: {external_owner.get('owner') or 'unknown'}"
            )
            if study_user.get("next_action"):
                lines.append(f"  下一步: {study_user.get('next_action')}")
    else:
        lines.append("- 当前还没有 cross-study completion projection。")
    lines.extend(render_paper_orchestra_operator_projection_lines(payload.get("paper_orchestra_operator_projection") or {}))
    lines.extend(_render_portable_supervisor_queue_dashboard_lines(payload.get("portable_supervisor_queue_dashboard") or {}))
    lines.extend(
        [
            "",
        "## Workspace Alerts",
        "",
        ]
    )
    workspace_alerts = list(payload.get("workspace_alerts") or [])
    if workspace_alerts:
        lines.extend(f"- {item}" for item in workspace_alerts)
    else:
        lines.append("- 当前没有新的 workspace 级硬告警。")
    lines.extend(["", "## Attention Queue", ""])
    attention_queue = list(payload.get("attention_queue") or [])
    if attention_queue:
        for item in attention_queue:
            title = _non_empty_text(item.get("title")) or "未命名关注项"
            lines.append(f"- 当前关注项: {title}")
            if item.get("summary"):
                lines.append(f"  当前判断: {item.get('summary')}")
            autonomy_contract = dict(item.get("autonomy_contract") or {})
            if autonomy_contract.get("summary"):
                lines.append(f"  自治合同: {autonomy_contract.get('summary')}")
            autonomy_soak_status = dict(item.get("autonomy_soak_status") or {})
            if autonomy_soak_status.get("summary"):
                lines.append(f"  自治 Proof / Soak: {autonomy_soak_status.get('summary')}")
            quality_closure_truth = dict(item.get("quality_closure_truth") or {})
            if quality_closure_truth.get("summary"):
                lines.append(f"  质量闭环: {quality_closure_truth.get('summary')}")
            quality_execution_lane = dict(item.get("quality_execution_lane") or {})
            if quality_execution_lane.get("summary"):
                lines.append(f"  质量执行线: {quality_execution_lane.get('summary')}")
            same_line_route_truth_preview = _same_line_route_truth_preview(item.get("same_line_route_truth"))
            if same_line_route_truth_preview:
                lines.append(f"  同线路由: {same_line_route_truth_preview}")
            quality_review_loop_preview = _quality_review_loop_preview(item.get("quality_review_loop"))
            if quality_review_loop_preview:
                lines.append(f"  质量评审闭环: {quality_review_loop_preview}")
            quality_review_followthrough_preview = _quality_review_followthrough_preview(
                item.get("quality_review_followthrough")
            )
            if quality_review_followthrough_preview:
                lines.append(f"  质量复评跟进: {quality_review_followthrough_preview}")
            quality_repair_followthrough_preview = _quality_repair_followthrough_preview(
                item.get("quality_repair_followthrough")
            )
            if quality_repair_followthrough_preview:
                lines.append(f"  quality-repair 跟进: {quality_repair_followthrough_preview}")
            gate_clearing_followthrough_preview = _gate_clearing_followthrough_preview(
                item.get("gate_clearing_followthrough")
            )
            if gate_clearing_followthrough_preview:
                lines.append(f"  gate-clearing 跟进: {gate_clearing_followthrough_preview}")
            readiness = dict(item.get("medical_paper_readiness") or {})
            if readiness:
                next_action = dict(readiness.get("next_action") or {})
                lines.append(
                    "  Medical Paper Readiness: "
                    f"{readiness.get('overall_status') or 'unknown'}；"
                    f"{next_action.get('summary') or 'no next action'}；"
                    "projection-only"
                )
            restore_point = dict(autonomy_contract.get("restore_point") or {})
            if restore_point.get("summary"):
                lines.append(f"  恢复点: {restore_point.get('summary')}")
            if item.get("recommended_command"):
                lines.append(f"  处理命令: `{item.get('recommended_command')}`")
            operator_status_card = dict(item.get("operator_status_card") or {})
            handling_state_label = _operator_handling_state_label(operator_status_card)
            if handling_state_label:
                lines.append(f"  当前处理状态: {handling_state_label}")
            if operator_status_card.get("next_confirmation_signal"):
                lines.append(f"  下一确认信号: {operator_status_card.get('next_confirmation_signal')}")
    else:
        lines.append("- 当前没有新的 attention item。")
    lines.extend(["", "## User Loop", ""])
    for name, command in (payload.get("user_loop") or {}).items():
        lines.append(f"- `{name}`: `{command}`")
    lines.extend(["", "## Phase 2 User Loop", ""])
    lines.append(f"- 当前路径摘要: {phase2_user_product_loop.get('summary') or 'none'}")
    lines.append(f"- 推荐动作: `{phase2_user_product_loop.get('recommended_step_id') or 'none'}`")
    lines.append(f"- 推荐命令: `{phase2_user_product_loop.get('recommended_command') or 'none'}`")
    for item in phase2_user_product_loop.get("operator_questions") or []:
        if not isinstance(item, Mapping):
            continue
        lines.append(f"- {item.get('question') or 'question'}: `{item.get('command') or 'none'}`")
    lines.extend(["", "## Commands", ""])
    for name, command in (payload.get("commands") or {}).items():
        lines.append(f"- `{name}`: `{command}`")
    lines.extend(["", "## Studies", ""])
    for item in payload.get("studies") or []:
        lines.extend(
            [
                f"### {item.get('study_id')}",
                "",
                f"- 浏览器入口: `{((item.get('monitoring') or {}).get('browser_url') or 'none')}`",
                f"- 当前运行批次: `{((item.get('monitoring') or {}).get('active_run_id') or 'none')}`",
            ]
        )
        _append_human_status_lines(lines, item)
        task_intake = dict(item.get("task_intake") or {})
        if task_intake:
            lines.append(f"- 当前任务意图: {task_intake.get('task_intent') or '未提供'}")
            lines.append(f"- 当前投稿目标: {task_intake.get('journal_target') or 'none'}")
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
        operator_status_card = dict(item.get("operator_status_card") or {})
        handling_state_label = _operator_handling_state_label(operator_status_card)
        if handling_state_label:
            lines.append(f"- 当前处理状态: {handling_state_label}")
        if operator_status_card.get("user_visible_verdict"):
            lines.append(f"- 当前处理结论: {operator_status_card.get('user_visible_verdict')}")
        if operator_status_card.get("next_confirmation_signal"):
            lines.append(f"- 下一确认信号: {operator_status_card.get('next_confirmation_signal')}")
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
        readiness = dict(item.get("medical_paper_readiness") or {})
        if readiness:
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
                    + "；".join(
                        _readiness_action_card_label(card)
                        for card in action_cards
                        if card.get("label")
                    )
                )
        research_loop = dict(item.get("medical_paper_research_loop") or {})
        if research_loop:
            lines.append(
                "- Medical Paper Research Loop: "
                f"overall_status `{research_loop.get('overall_status') or 'unknown'}`；"
                f"下一步: {dict(research_loop.get('next_action') or {}).get('summary') or 'none'}；"
                "authority contract: projection-only"
            )
        restore_point = dict(autonomy_contract.get("restore_point") or {})
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
    return "\n".join(lines)


def _render_portable_supervisor_queue_dashboard_lines(projection: object) -> list[str]:
    if not isinstance(projection, Mapping) or not projection:
        return []
    counts = dict(projection.get("counts") or {})
    lines = [
        "",
        "## Portable Supervisor Queue",
        "",
        "- surface: read-only hourly supervisor projection",
        f"- authority: `{projection.get('authority') or 'observability_only'}`",
        f"- 当前摘要: {projection.get('summary') or 'none'}",
        (
            "- 当前计数: "
            f"study {counts.get('projection_count', 0)}；"
            f"queue action {counts.get('queued_action_count', 0)}；"
            f"blocked {counts.get('blocked', 0)}；"
            f"external supervisor {counts.get('external_supervisor_required', 0)}"
        ),
    ]
    for study in projection.get("studies") or []:
        if not isinstance(study, Mapping):
            continue
        runtime_health = dict(study.get("runtime_health") or {})
        artifact_delta = dict(study.get("artifact_delta") or {})
        gate_specificity = dict(study.get("gate_specificity") or {})
        ai_reviewer = dict(study.get("ai_reviewer_status") or {})
        lines.append(
            f"- `{study.get('study_id') or 'unknown-study'}` queue: "
            f"quest `{study.get('quest_status') or 'unknown'}`；"
            f"run `{study.get('active_run_id') or 'none'}`；"
            f"health `{runtime_health.get('health_status') or 'unknown'}`；"
            f"artifact `{artifact_delta.get('status') or 'unknown'}`；"
            f"gate `{gate_specificity.get('status') or 'unknown'}`；"
            f"AI reviewer `{ai_reviewer.get('status') or 'unknown'}`"
        )
        blocked_reason = (
            _non_empty_text(study.get("blocked_reason"))
            or _non_empty_text(gate_specificity.get("blocked_reason"))
        )
        if blocked_reason:
            lines.append(f"  blocked_reason: `{blocked_reason}`")
        for action in study.get("action_queue") or []:
            if not isinstance(action, Mapping):
                continue
            lines.append(
                f"  queue action: `{action.get('action_type') or action.get('action_id') or 'unknown_action'}` "
                f"{action.get('summary') or ''}".rstrip()
            )
        why_not_applied = [
            text for item in study.get("why_not_applied") or [] if (text := _non_empty_text(item)) is not None
        ]
        if why_not_applied:
            lines.append("  why_not_applied: " + "；".join(f"`{item}`" for item in why_not_applied))
        if study.get("next_owner") or study.get("external_supervisor_required") is not None:
            lines.append(
                f"  next_owner: `{study.get('next_owner') or 'unknown'}`；"
                f"external_supervisor_required: `{study.get('external_supervisor_required')}`"
            )
    return lines


def _readiness_action_card_label(card: Mapping[str, Any]) -> str:
    status = _non_empty_text(card.get("status"))
    missing_reason = _non_empty_text(card.get("missing_reason"))
    suffix = ""
    if status and missing_reason:
        suffix = f" [{status} / {missing_reason}]"
    elif status:
        suffix = f" [{status}]"
    return f"{card.get('label')}{suffix}: {card.get('summary')}"
