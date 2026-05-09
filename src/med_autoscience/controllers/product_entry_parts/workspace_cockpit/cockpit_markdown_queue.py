from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.product_entry_parts.shared_base import (
    _gate_clearing_followthrough_preview,
    _operator_handling_state_label,
    _quality_repair_followthrough_preview,
    _quality_review_followthrough_preview,
    _quality_review_loop_preview,
    _same_line_route_truth_preview,
)
from med_autoscience.controllers.product_entry_parts.shared_labels import _non_empty_text


def append_portable_supervisor_queue_dashboard(lines: list[str], projection: object) -> None:
    if not isinstance(projection, Mapping) or not projection:
        return
    counts = dict(projection.get("counts") or {})
    lines.extend(
        [
            "",
            "## Portable Supervisor Queue",
            "",
            "- surface: read-only hourly supervisor projection",
            f"- authority: `{projection.get('authority') or 'observability_only'}`",
            "- runtime boundary: Codex App heartbeat is an outer developer supervisor signal, not a MAS architecture dependency.",
            f"- 当前摘要: {projection.get('summary') or 'none'}",
            (
                "- 当前计数: "
                f"study {counts.get('projection_count', 0)}；"
                f"queue action {counts.get('queued_action_count', 0)}；"
                f"blocked {counts.get('blocked', 0)}；"
                f"external supervisor {counts.get('external_supervisor_required', 0)}"
            ),
        ]
    )
    _append_portable_supervisor_mode(lines, projection)
    for study in projection.get("studies") or []:
        if isinstance(study, Mapping):
            _append_portable_supervisor_study(lines, study)


def _append_portable_supervisor_study(lines: list[str], study: Mapping[str, Any]) -> None:
    gate_specificity = dict(study.get("gate_specificity") or {})
    lines.append(_portable_supervisor_study_summary(study))
    _append_portable_blocked_reason(lines, study, gate_specificity)
    _append_portable_action_queue(lines, study)
    _append_portable_why_not_applied(lines, study)
    _append_portable_next_owner(lines, study)


def _portable_supervisor_study_summary(study: Mapping[str, Any]) -> str:
    runtime_health = dict(study.get("runtime_health") or {})
    artifact_delta = dict(study.get("artifact_delta") or {})
    gate_specificity = dict(study.get("gate_specificity") or {})
    ai_reviewer = dict(study.get("ai_reviewer_status") or {})
    return (
        f"- `{study.get('study_id') or 'unknown-study'}` queue: "
        f"quest `{study.get('quest_status') or 'unknown'}`；"
        f"run `{study.get('active_run_id') or 'none'}`；"
        f"health `{runtime_health.get('health_status') or 'unknown'}`；"
        f"artifact `{artifact_delta.get('status') or 'unknown'}`；"
        f"gate `{gate_specificity.get('status') or 'unknown'}`；"
        f"AI reviewer `{ai_reviewer.get('status') or 'unknown'}`"
    )


def _append_portable_blocked_reason(
    lines: list[str],
    study: Mapping[str, Any],
    gate_specificity: Mapping[str, Any],
) -> None:
    blocked_reason = _non_empty_text(study.get("blocked_reason")) or _non_empty_text(gate_specificity.get("blocked_reason"))
    if blocked_reason:
        lines.append(f"  blocked_reason: `{blocked_reason}`")


def _append_portable_action_queue(lines: list[str], study: Mapping[str, Any]) -> None:
    for action in study.get("action_queue") or []:
        if not isinstance(action, Mapping):
            continue
        lines.append(
            f"  queue action: `{action.get('action_type') or action.get('action_id') or 'unknown_action'}` "
            f"{action.get('summary') or ''}".rstrip()
        )
        owner_pickup = action.get("owner_pickup") if isinstance(action.get("owner_pickup"), Mapping) else {}
        if owner_pickup:
            lines.append(f"  owner_pickup `{owner_pickup.get('state') or 'unknown'}`")
        consumption = action.get("consumption") if isinstance(action.get("consumption"), Mapping) else {}
        if consumption:
            lines.append(
                "  developer_supervisor_attention_required "
                f"`{consumption.get('developer_supervisor_attention_required')}`"
            )


def _append_portable_supervisor_mode(lines: list[str], projection: Mapping[str, Any]) -> None:
    supervisor_mode = dict(projection.get("supervisor_mode") or {})
    if not supervisor_mode:
        return
    lines.append(
        "- developer supervisor mode: "
        f"`{supervisor_mode.get('mode') or 'unknown'}`"
        f" ({supervisor_mode.get('mode_label') or 'unlabeled'})；"
        f"scheduler_owner `{supervisor_mode.get('scheduler_owner') or 'unknown'}`；"
        f"Codex App heartbeat required `{supervisor_mode.get('codex_app_heartbeat_required')}`；"
        f"safe actions `{supervisor_mode.get('safe_actions_enabled')}`；"
        f"repo repair authority `{supervisor_mode.get('repo_level_repair_authority') or 'unknown'}`；"
        f"authority gate `{supervisor_mode.get('authority_gate') or supervisor_mode.get('github_user_gate') or 'unknown'}`"
    )


def _append_portable_why_not_applied(lines: list[str], study: Mapping[str, Any]) -> None:
    why_not_applied = [
        text for item in study.get("why_not_applied") or [] if (text := _non_empty_text(item)) is not None
    ]
    if why_not_applied:
        lines.append("  why_not_applied: " + "；".join(f"`{item}`" for item in why_not_applied))


def _append_portable_next_owner(lines: list[str], study: Mapping[str, Any]) -> None:
    if study.get("next_owner") or study.get("external_supervisor_required") is not None:
        lines.append(
            f"  next_owner: `{study.get('next_owner') or 'unknown'}`；"
            f"external_supervisor_required: `{study.get('external_supervisor_required')}`"
        )


def append_workspace_alerts(lines: list[str], payload: Mapping[str, Any]) -> None:
    lines.extend(["", "## Workspace Alerts", ""])
    workspace_alerts = list(payload.get("workspace_alerts") or [])
    if workspace_alerts:
        lines.extend(f"- {item}" for item in workspace_alerts)
    else:
        lines.append("- 当前没有新的 workspace 级硬告警。")


def append_attention_queue(lines: list[str], payload: Mapping[str, Any]) -> None:
    lines.extend(["", "## Attention Queue", ""])
    attention_queue = list(payload.get("attention_queue") or [])
    if attention_queue:
        for item in attention_queue:
            if isinstance(item, Mapping):
                _append_attention_item(lines, item)
    else:
        lines.append("- 当前没有新的 attention item。")


def _append_attention_item(lines: list[str], item: Mapping[str, Any]) -> None:
    title = _non_empty_text(item.get("title")) or "未命名关注项"
    lines.append(f"- 当前关注项: {title}")
    if item.get("summary"):
        lines.append(f"  当前判断: {item.get('summary')}")
    autonomy_contract = dict(item.get("autonomy_contract") or {})
    if autonomy_contract.get("summary"):
        lines.append(f"  自治合同: {autonomy_contract.get('summary')}")
    _append_attention_status_lines(lines, item)
    _append_attention_readiness(lines, item)
    _append_attention_restore_and_command(lines, item, autonomy_contract)
    _append_attention_operator_status(lines, item)


def _append_attention_readiness(lines: list[str], item: Mapping[str, Any]) -> None:
    readiness = dict(item.get("medical_paper_readiness") or {})
    if not readiness:
        return
    next_action = dict(readiness.get("next_action") or {})
    lines.append(
        "  Medical Paper Readiness: "
        f"{readiness.get('overall_status') or 'unknown'}；"
        f"{next_action.get('summary') or 'no next action'}；"
        "projection-only"
    )


def _append_attention_restore_and_command(
    lines: list[str],
    item: Mapping[str, Any],
    autonomy_contract: Mapping[str, Any],
) -> None:
    restore_point = dict(autonomy_contract.get("restore_point") or {})
    if restore_point.get("summary"):
        lines.append(f"  恢复点: {restore_point.get('summary')}")
    if item.get("recommended_command"):
        lines.append(f"  处理命令: `{item.get('recommended_command')}`")


def _append_attention_operator_status(lines: list[str], item: Mapping[str, Any]) -> None:
    operator_status_card = dict(item.get("operator_status_card") or {})
    handling_state_label = _operator_handling_state_label(operator_status_card)
    if handling_state_label:
        lines.append(f"  当前处理状态: {handling_state_label}")
    if operator_status_card.get("next_confirmation_signal"):
        lines.append(f"  下一确认信号: {operator_status_card.get('next_confirmation_signal')}")


def _append_attention_status_lines(lines: list[str], item: Mapping[str, Any]) -> None:
    for field, label in (
        ("autonomy_soak_status", "自治 Proof / Soak"),
        ("quality_closure_truth", "质量闭环"),
        ("quality_execution_lane", "质量执行线"),
    ):
        value = dict(item.get(field) or {})
        if value.get("summary"):
            lines.append(f"  {label}: {value.get('summary')}")
    _append_attention_quality_previews(lines, item)


def _append_attention_quality_previews(lines: list[str], item: Mapping[str, Any]) -> None:
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
            lines.append(f"  {label}: {preview}")


def append_user_loop(lines: list[str], payload: Mapping[str, Any]) -> None:
    lines.extend(["", "## User Loop", ""])
    for name, command in (payload.get("user_loop") or {}).items():
        lines.append(f"- `{name}`: `{command}`")


def append_phase2_user_loop(lines: list[str], payload: Mapping[str, Any]) -> None:
    phase2_user_product_loop = dict(payload.get("phase2_user_product_loop") or {})
    lines.extend(["", "## Phase 2 User Loop", ""])
    lines.append(f"- 当前路径摘要: {phase2_user_product_loop.get('summary') or 'none'}")
    lines.append(f"- 推荐动作: `{phase2_user_product_loop.get('recommended_step_id') or 'none'}`")
    lines.append(f"- 推荐命令: `{phase2_user_product_loop.get('recommended_command') or 'none'}`")
    for item in phase2_user_product_loop.get("operator_questions") or []:
        if isinstance(item, Mapping):
            lines.append(f"- {item.get('question') or 'question'}: `{item.get('command') or 'none'}`")


def append_commands(lines: list[str], payload: Mapping[str, Any]) -> None:
    lines.extend(["", "## Commands", ""])
    for name, command in (payload.get("commands") or {}).items():
        lines.append(f"- `{name}`: `{command}`")
