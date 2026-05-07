from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def append_ai_first_operations_state(lines: list[str], payload: Mapping[str, Any]) -> None:
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
            if isinstance(dashboard, Mapping):
                _append_ai_first_dashboard(lines, dashboard)
    else:
        lines.append("- 当前还没有 AI-first operations runtime state。")


def _append_ai_first_dashboard(lines: list[str], dashboard: Mapping[str, Any]) -> None:
    study_id = dashboard.get("study_id") or "unknown-study"
    lines.append(f"- `{study_id}` operations: {dashboard.get('current_stage') or 'unknown'}")
    for field, label in (
        ("pre_draft_status", "pre-draft"),
        ("ai_reviewer_workflow_status", "AI reviewer workflow"),
        ("artifact_proof_status", "artifact proof"),
        ("route_back_status", "route-back"),
        ("next_step", "下一步"),
        ("human_judgment", "人工判断"),
        ("feedback_summary", "运行反馈"),
        ("feedback_primary_reason", "反馈原因"),
        ("feedback_action_summary", "建议动作"),
    ):
        if dashboard.get(field):
            lines.append(f"  {label}: {dashboard.get(field)}")
    if dashboard.get("action_primary_summary"):
        lines.append(
            "  动作生命周期: "
            f"{dashboard.get('action_primary_status') or 'unknown'}；"
            f"{dashboard.get('action_primary_summary')}"
        )
    if dashboard.get("quality_learning_operations_report_summary"):
        lines.append(f"  Quality learning operations: {dashboard.get('quality_learning_operations_report_summary')}")
    _append_learning_priority(lines, dashboard, "quality_learning_top_open_priority", "Maintainer priority")
    _append_learning_priority(lines, dashboard, "quality_learning_top_system_improvement", "System improvement priority")
    if dashboard.get("ai_reviewer_trace_complete") is not None:
        lines.append("  AI reviewer trace: " + ("完整" if dashboard.get("ai_reviewer_trace_complete") else "不完整"))
    if dashboard.get("route_back_count"):
        lines.append(f"  route-back: {dashboard.get('route_back_count')} -> {dashboard.get('route_back_target') or 'unknown'}")
    if dashboard.get("stale_artifact_count"):
        lines.append(f"  产物刷新: {dashboard.get('stale_artifact_count')} 个待刷新")


def _append_learning_priority(
    lines: list[str],
    dashboard: Mapping[str, Any],
    field: str,
    label: str,
) -> None:
    priority = dict(dashboard.get(field) or {})
    if priority:
        lines.append(
            f"  {label}: "
            f"{priority.get('reason')} | "
            f"frequency={priority.get('frequency')} | "
            f"impact={priority.get('impact_entry')} | "
            f"fix_layer={priority.get('suggested_fix_layer')}"
        )


def append_ai_first_cross_study_completion(lines: list[str], payload: Mapping[str, Any]) -> None:
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
            if isinstance(study, Mapping):
                _append_completion_study(lines, study)
    else:
        lines.append("- 当前还没有 cross-study completion projection。")


def _append_completion_study(lines: list[str], study: Mapping[str, Any]) -> None:
    study_id = study.get("study_id") or "unknown-study"
    study_user = dict(study.get("user_view") or {})
    maintainer = dict(study.get("maintainer_view") or {})
    lines.append(f"- `{study_id}` completion: {study_user.get('status') or study.get('status') or 'unknown'}")
    _append_completion_feedback_line(lines, maintainer)
    _append_completion_artifact_line(lines, maintainer)
    if study_user.get("next_action"):
        lines.append(f"  下一步: {study_user.get('next_action')}")


def _append_completion_feedback_line(lines: list[str], maintainer: Mapping[str, Any]) -> None:
    feedback = dict(maintainer.get("feedback") or {})
    dispatch = dict(maintainer.get("dispatch") or {})
    ai_reviewer = dict(maintainer.get("ai_reviewer_authority") or {})
    lines.append(
        "  feedback: "
        f"{feedback.get('open_feedback_count', 0)} open；"
        f"dispatch: {dispatch.get('open_action_count', 0)} open / {dispatch.get('total_action_count', 0)} total / {dispatch.get('latest_status') or 'unknown'}；"
        f"AI reviewer: {ai_reviewer.get('owner') or 'unknown'} "
        f"({'backed' if ai_reviewer.get('reviewer_backed') else 'not backed'})"
    )


def _append_completion_artifact_line(lines: list[str], maintainer: Mapping[str, Any]) -> None:
    artifact = dict(maintainer.get("artifact_proof") or {})
    human_review = dict(maintainer.get("human_review") or {})
    external_owner = dict(maintainer.get("external_owner") or {})
    lines.append(
        "  artifact proof: "
        f"{artifact.get('rebuild_status') or 'unknown'}；"
        f"human gate: {'open' if human_review.get('required') else 'closed'}；"
        f"external owner: {external_owner.get('owner') or 'unknown'}"
    )
