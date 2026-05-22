from __future__ import annotations

from importlib import import_module
import sys
from typing import Any, Mapping

from .shared import *  # noqa: F403


def build_same_line_route_truth(*, quality_closure_truth: Mapping[str, Any], quality_execution_lane: Mapping[str, Any]):
    product_entry_module = sys.modules.get("med_autoscience.controllers.product_entry")  # noqa: F405
    default = import_module("med_autoscience.evaluation_summary").build_same_line_route_truth
    build_truth = getattr(product_entry_module, "build_same_line_route_truth", default) if product_entry_module else default
    return build_truth(
        quality_closure_truth=quality_closure_truth,
        quality_execution_lane=quality_execution_lane,
    )

def _attention_item(
    *,
    code: str,
    title: str,
    summary: str,
    recommended_step_id: str | None,
    recommended_command: str | None,
    scope: str,
    study_id: str | None = None,
    operator_status_card: dict[str, Any] | None = None,
    autonomy_contract: dict[str, Any] | None = None,
    quality_closure_truth: dict[str, Any] | None = None,
    quality_execution_lane: dict[str, Any] | None = None,
    same_line_route_truth: dict[str, Any] | None = None,
    same_line_route_surface: dict[str, Any] | None = None,
    quality_repair_followthrough: dict[str, Any] | None = None,
    quality_review_followthrough: dict[str, Any] | None = None,
    gate_clearing_followthrough: dict[str, Any] | None = None,
    autonomy_soak_status: dict[str, Any] | None = None,
    research_runtime_control_projection: dict[str, Any] | None = None,
    study_truth_snapshot: dict[str, Any] | None = None,
    medical_paper_readiness: dict[str, Any] | None = None,
    runtime_reconcile_trigger: dict[str, Any] | None = None,
    outer_supervision_slo: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "priority": _ATTENTION_PRIORITIES.get(code, 999),
        "scope": scope,
        "study_id": study_id,
        "code": code,
        "title": title,
        "summary": summary,
        "recommended_step_id": recommended_step_id,
        "recommended_command": recommended_command,
        "operator_status_card": dict(operator_status_card or {}) or None,
        "autonomy_contract": dict(autonomy_contract or {}) or None,
        "quality_closure_truth": dict(quality_closure_truth or {}) or None,
        "quality_execution_lane": dict(quality_execution_lane or {}) or None,
        "same_line_route_truth": dict(same_line_route_truth or {}) or None,
        "same_line_route_surface": dict(same_line_route_surface or {}) or None,
        "quality_repair_followthrough": dict(quality_repair_followthrough or {}) or None,
        "quality_review_followthrough": dict(quality_review_followthrough or {}) or None,
        "gate_clearing_followthrough": dict(gate_clearing_followthrough or {}) or None,
        "autonomy_soak_status": dict(autonomy_soak_status or {}) or None,
        "research_runtime_control_projection": dict(research_runtime_control_projection or {}) or None,
        "study_truth_snapshot": dict(study_truth_snapshot or {}) or None,
        "medical_paper_readiness": dict(medical_paper_readiness or {}) or None,
        "runtime_reconcile_trigger": dict(runtime_reconcile_trigger or {}) or None,
        "outer_supervision_slo": dict(outer_supervision_slo or {}) or None,
    }


def _operator_status_summary(card: Mapping[str, Any] | None) -> str | None:
    if not isinstance(card, Mapping):
        return None
    return _non_empty_text(card.get("user_visible_verdict")) or _non_empty_text(card.get("owner_summary"))


def _quality_route_focus(intervention_lane: Mapping[str, Any] | None) -> str | None:
    if not isinstance(intervention_lane, Mapping):
        return None
    return _non_empty_text(intervention_lane.get("route_summary"))


def _same_line_route_truth_payload(item: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(item, Mapping):
        return {}
    direct_truth = dict(item.get("same_line_route_truth") or {})
    if direct_truth:
        return direct_truth
    return build_same_line_route_truth(
        quality_closure_truth=dict(item.get("quality_closure_truth") or {}),
        quality_execution_lane=dict(item.get("quality_execution_lane") or {}),
    )


def _quality_execution_focus(item: Mapping[str, Any] | None) -> str | None:
    if not isinstance(item, Mapping):
        return None
    quality_execution_lane = dict(item.get("quality_execution_lane") or {})
    route_key_question = _non_empty_text(quality_execution_lane.get("route_key_question"))
    if route_key_question is not None:
        return route_key_question
    return _non_empty_text(quality_execution_lane.get("summary"))


def _same_line_route_focus(item: Mapping[str, Any] | None) -> str | None:
    same_line_route_truth = _same_line_route_truth_payload(item)
    if same_line_route_truth:
        return _non_empty_text(same_line_route_truth.get("current_focus")) or _non_empty_text(
            same_line_route_truth.get("summary")
        )
    if not isinstance(item, Mapping):
        return None
    same_line_route_surface = dict(item.get("same_line_route_surface") or {})
    route_key_question = _non_empty_text(same_line_route_surface.get("route_key_question"))
    if route_key_question is not None:
        return route_key_question
    return _non_empty_text(same_line_route_surface.get("summary"))


def _autonomy_soak_focus(item: Mapping[str, Any] | None) -> str | None:
    if not isinstance(item, Mapping):
        return None
    autonomy_soak_status = dict(item.get("autonomy_soak_status") or {})
    route_key_question = _non_empty_text(autonomy_soak_status.get("route_key_question"))
    if route_key_question is not None:
        return route_key_question
    return _non_empty_text(autonomy_soak_status.get("summary"))


def _quality_review_followthrough_focus(item: Mapping[str, Any] | None) -> str | None:
    if not isinstance(item, Mapping):
        return None
    followthrough = dict(item.get("quality_review_followthrough") or {})
    return _non_empty_text(followthrough.get("next_confirmation_signal")) or _non_empty_text(
        followthrough.get("summary")
    )


def _quality_repair_followthrough_focus(item: Mapping[str, Any] | None) -> str | None:
    if not isinstance(item, Mapping):
        return None
    followthrough = dict(item.get("quality_repair_followthrough") or {})
    return _non_empty_text(followthrough.get("next_confirmation_signal")) or _non_empty_text(
        followthrough.get("summary")
    )


def _gate_clearing_followthrough_focus(item: Mapping[str, Any] | None) -> str | None:
    if not isinstance(item, Mapping):
        return None
    followthrough = dict(item.get("gate_clearing_followthrough") or {})
    return (
        _non_empty_text(followthrough.get("next_confirmation_signal"))
        or _non_empty_text(followthrough.get("current_focus"))
        or _gate_clearing_followthrough_summary(followthrough)
    )


def _quality_execution_lane_title(study_id: str, lane: Mapping[str, Any] | None) -> str | None:
    if not isinstance(lane, Mapping):
        return None
    lane_id = _non_empty_text(lane.get("lane_id"))
    if lane_id == "reviewer_first":
        return f"{study_id} 当前先做 reviewer-first 收口"
    if lane_id == "claim_evidence":
        return f"{study_id} 当前先做 claim-evidence 修复"
    if lane_id == "submission_hardening":
        return f"{study_id} 当前先做投稿包硬化收口"
    if lane_id == "write_ready":
        return f"{study_id} 当前进入同线写作推进"
    if lane_id == "general_quality_repair":
        return f"{study_id} 当前先做质量修复收口"
    return None


def _same_line_route_truth_title(study_id: str, truth: Mapping[str, Any] | None) -> str | None:
    if not isinstance(truth, Mapping):
        return None
    same_line_state = _non_empty_text(truth.get("same_line_state"))
    route_target_label = _non_empty_text(truth.get("route_target_label")) or _non_empty_text(truth.get("route_target"))
    if same_line_state == "finalize_only_remaining":
        return f"{study_id} 当前已进入同线定稿与投稿包收尾"
    if same_line_state == "write_continuation":
        return f"{study_id} 当前进入同线写作推进"
    if same_line_state == "bounded_analysis" and route_target_label is not None:
        return f"{study_id} 当前需要进入{route_target_label}完成有限补充分析"
    if same_line_state == "same_line_route_back" and route_target_label is not None:
        return f"{study_id} 当前需要回到{route_target_label}修复质量阻塞"
    if same_line_state == "quality_repair_pending":
        return f"{study_id} 当前先做质量修复收口"
    return None


def _attention_step_id(code: str) -> str:
    if code == "workspace_supervisor_service_not_loaded":
        return "inspect_supervision_service"
    if code == "study_supervision_gap":
        return "refresh_supervision"
    if code == "study_runtime_recovery_required":
        return "continue_or_relaunch"
    return "inspect_study_progress"


def _quality_blocker_title(study_id: str, intervention_lane: Mapping[str, Any] | None) -> str:
    if not isinstance(intervention_lane, Mapping):
        return f"{study_id} 当前存在质量硬阻塞"
    repair_mode = _non_empty_text(intervention_lane.get("repair_mode"))
    route_target_label = _non_empty_text(intervention_lane.get("route_target_label"))
    if route_target_label is None:
        return f"{study_id} 当前存在质量硬阻塞"
    if repair_mode == "bounded_analysis":
        return f"{study_id} 当前需要进入{route_target_label}完成有限补充分析"
    return f"{study_id} 当前需要回到{route_target_label}修复质量阻塞"


def _workspace_operator_brief(
    *,
    workspace_status: str,
    workspace_alerts: list[str],
    attention_queue: list[dict[str, Any]],
    studies: list[dict[str, Any]],
    user_loop: dict[str, str],
    commands: dict[str, str],
) -> dict[str, Any]:
    if workspace_status == "blocked":
        summary = _non_empty_text(workspace_alerts[0] if workspace_alerts else None) or (
            "当前 workspace 还没有通过正式前置检查，先不要盲目启动研究。"
        )
        return {
            "surface_kind": "workspace_operator_brief",
            "verdict": "preflight_blocked",
            "summary": summary,
            "should_intervene_now": True,
            "focus_scope": "workspace",
            "focus_study_id": None,
            "recommended_step_id": "run_doctor",
            "recommended_command": commands.get("doctor"),
        }
    if attention_queue:
        top = dict(attention_queue[0] or {})
        operator_status_card = dict(top.get("operator_status_card") or {})
        brief = {
            "surface_kind": "workspace_operator_brief",
            "verdict": "attention_required",
            "summary": _operator_status_summary(operator_status_card)
            or _non_empty_text(top.get("summary"))
            or _non_empty_text(top.get("title"))
            or "当前 workspace 有需要优先处理的 attention item。",
            "should_intervene_now": True,
            "focus_scope": _non_empty_text(top.get("scope")) or "workspace",
            "focus_study_id": _non_empty_text(top.get("study_id")),
            "recommended_step_id": _non_empty_text(top.get("recommended_step_id")) or "handle_attention_item",
            "recommended_command": _non_empty_text(top.get("recommended_command")) or commands.get("doctor"),
        }
        current_focus = (
            _non_empty_text(operator_status_card.get("current_focus"))
            or _same_line_route_focus(top)
            or _gate_clearing_followthrough_focus(top)
            or _quality_repair_followthrough_focus(top)
            or _quality_execution_focus(top)
            or _quality_review_followthrough_focus(top)
            or _autonomy_soak_focus(top)
        )
        if current_focus is not None:
            brief["current_focus"] = current_focus
        next_confirmation_signal = _non_empty_text(operator_status_card.get("next_confirmation_signal"))
        if next_confirmation_signal is not None:
            brief["next_confirmation_signal"] = next_confirmation_signal
        research_runtime_control_projection = dict(top.get("research_runtime_control_projection") or {})
        if research_runtime_control_projection:
            brief["research_runtime_control_projection"] = research_runtime_control_projection
        return brief
    if not studies:
        return {
            "surface_kind": "workspace_operator_brief",
            "verdict": "ready_for_task",
            "summary": "当前 workspace 已 ready，下一步先给目标 study 写 durable task intake。",
            "should_intervene_now": False,
            "focus_scope": "workspace",
            "focus_study_id": None,
            "recommended_step_id": "submit_task",
            "recommended_command": user_loop.get("submit_task_template"),
        }

    lead_study = dict(studies[0] or {})
    lead_study_id = _non_empty_text(lead_study.get("study_id"))
    lead_status_card = dict(lead_study.get("operator_status_card") or {})
    recommended_command = _non_empty_text(lead_study.get("recommended_command")) or _non_empty_text(
        ((lead_study.get("commands") or {}).get("progress"))
    )
    summary = (
        _operator_status_summary(lead_status_card)
        or
        _quality_repair_followthrough_preview(lead_study.get("quality_repair_followthrough"))
        or
        _gate_clearing_followthrough_preview(lead_study.get("gate_clearing_followthrough"))
        or
        _quality_review_followthrough_preview(lead_study.get("quality_review_followthrough"))
        or _non_empty_text((lead_study.get("autonomy_soak_status") or {}).get("summary"))
        or (
            f"当前没有新的 workspace 级硬告警，继续盯住 {lead_study_id} 的进度与监管即可。"
        if lead_study_id is not None
        else "当前没有新的 workspace 级硬告警，继续保持对活跃 study 的监管即可。"
        )
    )
    brief = {
        "surface_kind": "workspace_operator_brief",
        "verdict": "monitor_only",
        "summary": summary,
        "should_intervene_now": False,
        "focus_scope": "study",
        "focus_study_id": lead_study_id,
        "recommended_step_id": "inspect_progress",
        "recommended_command": recommended_command or user_loop.get("open_workspace_cockpit"),
    }
    current_focus = (
        _non_empty_text(lead_status_card.get("current_focus"))
        or _same_line_route_focus(lead_study)
        or _gate_clearing_followthrough_focus(lead_study)
        or _quality_repair_followthrough_focus(lead_study)
        or _quality_review_followthrough_focus(lead_study)
        or _autonomy_soak_focus(lead_study)
    )
    if current_focus is not None:
        brief["current_focus"] = current_focus
    next_confirmation_signal = _non_empty_text(lead_status_card.get("next_confirmation_signal"))
    if next_confirmation_signal is not None:
        brief["next_confirmation_signal"] = next_confirmation_signal
    research_runtime_control_projection = dict(lead_study.get("research_runtime_control_projection") or {})
    if research_runtime_control_projection:
        brief["research_runtime_control_projection"] = research_runtime_control_projection
    return brief


def _attention_queue(
    *,
    workspace_status: str,
    workspace_supervision: dict[str, Any],
    studies: list[dict[str, Any]],
    commands: dict[str, str],
) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    service = dict(workspace_supervision.get("service") or {})
    study_counts = dict(workspace_supervision.get("study_counts") or {})
    service_loaded = bool(service.get("loaded"))
    if not service_loaded or bool(service.get("drift_reasons")):
        queue.append(
            _attention_item(
                code="workspace_supervisor_service_not_loaded",
                title="先检查 OPL scheduler replacement",
                summary=_non_empty_text(service.get("summary"))
                or "当前 workspace 还没有稳定的 OPL scheduler replacement projection。",
                recommended_step_id=_attention_step_id("workspace_supervisor_service_not_loaded"),
                recommended_command=commands.get("service_install") or commands.get("service_status"),
                scope="workspace",
            )
        )

    for item in studies:
        queue.extend(_study_attention_items(item=item, workspace_status=workspace_status, commands=commands))

    return sorted(
        queue,
        key=lambda item: (
            int(item.get("priority", 999)),
            str(item.get("study_id") or ""),
            str(item.get("code") or ""),
        ),
    )


def _study_attention_items(
    *,
    item: Mapping[str, Any],
    workspace_status: str,
    commands: Mapping[str, str],
) -> list[dict[str, Any]]:
    context = _study_attention_context(item)
    entries: list[dict[str, Any]] = []
    readiness_gap = _medical_paper_readiness_attention_item(context, item)
    if readiness_gap is not None:
        entries.append(readiness_gap)
    primary = _primary_study_attention_item(context, item, workspace_status=workspace_status, commands=commands)
    if primary is not None:
        entries.append(primary)
    return entries


def _study_attention_context(item: Mapping[str, Any]) -> dict[str, Any]:
    context = _study_attention_surface_context(item)
    context.update(_study_attention_command_context(item, context))
    context.update(_study_attention_state_context(item, context))
    return context


def _study_attention_surface_context(item: Mapping[str, Any]) -> dict[str, Any]:
    context = _study_attention_identity_context(item)
    context.update(_study_attention_operator_context(item))
    context.update(_study_attention_quality_context(item))
    context.update(_study_attention_runtime_context(item))
    return context


def _study_attention_identity_context(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "study_id": _non_empty_text(item.get("study_id")) or "unknown-study",
        "monitoring": dict(item.get("monitoring") or {}),
        "progress_freshness": dict(item.get("progress_freshness") or {}),
        "blocker_list": list(item.get("current_blockers") or []),
    }


def _study_attention_operator_context(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "operator_verdict": dict(item.get("operator_verdict") or {}),
        "operator_status_card": dict(item.get("operator_status_card") or {}),
    }


def _study_attention_quality_context(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "quality_closure_truth": dict(item.get("quality_closure_truth") or {}),
        "quality_execution_lane": dict(item.get("quality_execution_lane") or {}),
        "same_line_route_truth": _same_line_route_truth_payload(item),
        "same_line_route_surface": dict(item.get("same_line_route_surface") or {}),
        "quality_repair_followthrough": dict(item.get("quality_repair_followthrough") or {}),
        "quality_review_followthrough": dict(item.get("quality_review_followthrough") or {}),
        "gate_clearing_followthrough": dict(item.get("gate_clearing_followthrough") or {}),
        "medical_paper_readiness": dict(item.get("medical_paper_readiness") or {}),
        "intervention_lane": dict(item.get("intervention_lane") or {}),
    }


def _study_attention_runtime_context(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "auto_runtime_parked": dict(item.get("auto_runtime_parked") or {}),
        "autonomy_contract": dict(item.get("autonomy_contract") or {}),
        "autonomy_soak_status": dict(item.get("autonomy_soak_status") or {}),
        "research_runtime_control_projection": dict(item.get("research_runtime_control_projection") or {}),
        "runtime_reconcile_trigger": dict(item.get("runtime_reconcile_trigger") or {}),
        "outer_supervision_slo": dict(item.get("outer_supervision_slo") or {}),
        "study_truth_snapshot": dict(item.get("study_truth_snapshot") or {}),
    }


def _study_attention_command_context(item: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    quality_repair_followthrough = dict(context.get("quality_repair_followthrough") or {})
    gate_clearing_followthrough = dict(context.get("gate_clearing_followthrough") or {})
    operator_verdict = dict(context.get("operator_verdict") or {})
    progress_command = _non_empty_text(((item.get("commands") or {}).get("progress")))
    return {
        "quality_repair_step_id": _non_empty_text(quality_repair_followthrough.get("recommended_step_id")),
        "gate_clearing_step_id": _non_empty_text(gate_clearing_followthrough.get("recommended_step_id")),
        "progress_command": progress_command,
        "launch_command": _non_empty_text(((item.get("commands") or {}).get("launch"))),
        "preferred_command": _non_empty_text(quality_repair_followthrough.get("recommended_command"))
        or _non_empty_text(gate_clearing_followthrough.get("recommended_command"))
        or _non_empty_text(item.get("recommended_command"))
        or _non_empty_text(operator_verdict.get("primary_command")),
    }


def _study_attention_state_context(item: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    monitoring = dict(context.get("monitoring") or {})
    progress_freshness = dict(context.get("progress_freshness") or {})
    gate_clearing_summary = _gate_clearing_followthrough_summary(dict(context.get("gate_clearing_followthrough") or {}))
    current_stage_summary = _non_empty_text(item.get("current_stage_summary"))
    next_system_action = _non_empty_text(item.get("next_system_action"))
    intervention_lane = dict(context.get("intervention_lane") or {})
    operator_verdict = dict(context.get("operator_verdict") or {})
    operator_status_card = dict(context.get("operator_status_card") or {})
    return {
        "gate_clearing_summary": gate_clearing_summary,
        "supervisor_tick_status": _non_empty_text(monitoring.get("supervisor_tick_status")),
        "progress_status": _non_empty_text(progress_freshness.get("status")),
        "current_stage_summary": current_stage_summary,
        "next_system_action": next_system_action,
        "lane_id": _non_empty_text(intervention_lane.get("lane_id")),
        "autonomy_summary": _non_empty_text(dict(item.get("autonomy_contract") or {}).get("summary")),
        "lane_summary": (
            _operator_status_summary(operator_status_card)
            or gate_clearing_summary
            or _non_empty_text(operator_verdict.get("summary"))
            or _non_empty_text(intervention_lane.get("summary"))
            or current_stage_summary
            or next_system_action
        ),
    }


def _attention_common_payload(context: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "operator_status_card": dict(context.get("operator_status_card") or {}),
        "autonomy_contract": dict(context.get("autonomy_contract") or {}),
        "quality_closure_truth": dict(context.get("quality_closure_truth") or {}),
        "quality_execution_lane": dict(context.get("quality_execution_lane") or {}),
        "same_line_route_truth": dict(context.get("same_line_route_truth") or {}),
        "same_line_route_surface": dict(context.get("same_line_route_surface") or {}),
        "quality_repair_followthrough": dict(context.get("quality_repair_followthrough") or {}),
        "quality_review_followthrough": dict(context.get("quality_review_followthrough") or {}),
        "gate_clearing_followthrough": dict(context.get("gate_clearing_followthrough") or {}),
        "autonomy_soak_status": dict(context.get("autonomy_soak_status") or {}),
        "research_runtime_control_projection": dict(context.get("research_runtime_control_projection") or {}),
        "study_truth_snapshot": dict(context.get("study_truth_snapshot") or {}),
    }


def _medical_paper_readiness_attention_item(
    context: Mapping[str, Any],
    item: Mapping[str, Any],
) -> dict[str, Any] | None:
    readiness = dict(context.get("medical_paper_readiness") or {})
    if _non_empty_text(readiness.get("overall_status")) not in {"missing", "blocked", "partial"}:
        return None
    action_cards = [card for card in readiness.get("action_cards") or [] if isinstance(card, Mapping)]
    primary_card = dict(action_cards[0]) if action_cards else {}
    next_action = dict(readiness.get("next_action") or {})
    return _attention_item(
        code="medical_paper_readiness_gap",
        title=f"{context.get('study_id')} Medical Paper Readiness 仍有缺口",
        summary=_non_empty_text(primary_card.get("summary"))
        or _non_empty_text(next_action.get("summary"))
        or "Medical Paper Readiness projection 显示自动医学论文能力闭环仍有缺口。",
        recommended_step_id=_non_empty_text(primary_card.get("action_id"))
        or _non_empty_text(next_action.get("action_id"))
        or "inspect_medical_paper_readiness",
        recommended_command=_non_empty_text(((item.get("commands") or {}).get("progress"))),
        scope="study",
        study_id=str(context.get("study_id") or "unknown-study"),
        medical_paper_readiness=readiness,
    )


def _primary_study_attention_item(
    context: Mapping[str, Any],
    item: Mapping[str, Any],
    *,
    workspace_status: str,
    commands: Mapping[str, str],
) -> dict[str, Any] | None:
    resolvers = (
        lambda: _user_decision_attention_item(context, item),
        lambda: _runtime_state_attention_item(context, commands),
        lambda: _lane_state_attention_item(context, workspace_status),
        lambda: _progress_or_blocked_attention_item(context, workspace_status),
    )
    for resolve in resolvers:
        result = resolve()
        if result is not None:
            return result
    return None


def _user_decision_attention_item(context: Mapping[str, Any], item: Mapping[str, Any]) -> dict[str, Any] | None:
    lane_id = _non_empty_text(context.get("lane_id"))
    if lane_id not in {"user_decision_gate", "human_decision_gate"} and not item.get(
        "needs_user_decision"
    ):
        return None
    return _standard_study_attention_item(context, code="study_waiting_user_decision", title_suffix="需要用户判断")


def _runtime_state_attention_item(
    context: Mapping[str, Any],
    commands: Mapping[str, str],
) -> dict[str, Any] | None:
    lane_id = _non_empty_text(context.get("lane_id"))
    if _runtime_reconcile_requestable(context):
        return _runtime_reconcile_attention_item(context)
    if lane_id == "auto_runtime_parked" or bool(dict(context.get("auto_runtime_parked") or {}).get("parked")):
        return _auto_runtime_parked_attention_item(context)
    if lane_id != "workspace_supervision_gap" and context.get("supervisor_tick_status") not in {"stale", "missing", "invalid"}:
        return None
    return _standard_study_attention_item(
        context,
        code="study_supervision_gap",
        title_suffix="当前失去新鲜监管心跳",
        summary=str(context.get("lane_summary") or "OPL scheduler replacement projection 或 MAS domain runtime freshness 存在缺口。"),
        command=str(context.get("preferred_command") or commands.get("supervisor_tick") or context.get("progress_command") or ""),
    )


def _lane_state_attention_item(context: Mapping[str, Any], workspace_status: str) -> dict[str, Any] | None:
    lane_id = _non_empty_text(context.get("lane_id"))
    if lane_id == "runtime_recovery_required":
        return _runtime_recovery_attention_item(context)
    if lane_id == "manual_finishing" and (context.get("blocker_list") or workspace_status in {"attention_required", "blocked"}):
        return _manual_finishing_attention_item(context)
    if lane_id == "quality_floor_blocker":
        return _quality_floor_attention_item(context)
    return None


def _progress_or_blocked_attention_item(context: Mapping[str, Any], workspace_status: str) -> dict[str, Any] | None:
    if context.get("progress_status") == "stale":
        return _progress_attention_item(context, code="study_progress_stale", title_suffix="进度信号已陈旧")
    if context.get("progress_status") == "missing":
        return _progress_attention_item(context, code="study_progress_missing", title_suffix="缺少明确进度信号")
    if context.get("blocker_list") or workspace_status in {"attention_required", "blocked"}:
        return _blocked_study_attention_item(context)
    return None


def _standard_study_attention_item(
    context: Mapping[str, Any],
    *,
    code: str,
    title_suffix: str,
    summary: str | None = None,
    command: str | None = None,
) -> dict[str, Any]:
    study_id = str(context.get("study_id") or "unknown-study")
    return _attention_item(
        code=code,
        title=f"{study_id} {title_suffix}",
        summary=summary or str(context.get("lane_summary") or "当前 study 已到需要用户明确决策的节点。"),
        recommended_step_id=context.get("quality_repair_step_id")
        or context.get("gate_clearing_step_id")
        or _attention_step_id(code),
        recommended_command=command or context.get("preferred_command") or context.get("progress_command"),
        scope="study",
        study_id=study_id,
        **_attention_common_payload(context),
    )


def _runtime_reconcile_requestable(context: Mapping[str, Any]) -> bool:
    trigger = dict(context.get("runtime_reconcile_trigger") or {})
    slo = dict(context.get("outer_supervision_slo") or {})
    return trigger.get("safe_to_request") is True or _non_empty_text(slo.get("state")) in {"due", "stale", "missing"}


def _runtime_reconcile_attention_item(context: Mapping[str, Any]) -> dict[str, Any]:
    trigger = dict(context.get("runtime_reconcile_trigger") or {})
    slo = dict(context.get("outer_supervision_slo") or {})
    payload = _attention_common_payload(context)
    payload["runtime_reconcile_trigger"] = trigger
    payload["outer_supervision_slo"] = slo
    return _attention_item(
        code="study_runtime_reconcile_requestable",
        title=f"{context.get('study_id')} 可以请求一次 safe runtime reconcile",
        summary=_non_empty_text(trigger.get("summary"))
        or _non_empty_text(slo.get("summary"))
        or "runtime/session 信号已陈旧，当前可先请求 controller-owned one-shot reconcile dry-run。",
        recommended_step_id="request_runtime_reconcile",
        recommended_command=_non_empty_text(trigger.get("recommended_command"))
        or _non_empty_text(slo.get("recommended_command"))
        or context.get("preferred_command")
        or context.get("progress_command"),
        scope="study",
        study_id=str(context.get("study_id") or "unknown-study"),
        **payload,
    )


def _auto_runtime_parked_attention_item(context: Mapping[str, Any]) -> dict[str, Any]:
    parked = dict(context.get("auto_runtime_parked") or {})
    parked_label = _non_empty_text(parked.get("parked_state_label"))
    return _standard_study_attention_item(
        context,
        code="study_auto_runtime_parked",
        title_suffix=f"当前{parked_label or '自动运行已停驻'}",
        summary=_non_empty_text(context.get("autonomy_summary"))
        or _non_empty_text(context.get("lane_summary"))
        or _non_empty_text(parked.get("summary"))
        or _non_empty_text(context.get("current_stage_summary"))
        or _non_empty_text(context.get("next_system_action"))
        or "当前 study 已停驻并释放自动运行资源。",
    )


def _runtime_recovery_attention_item(context: Mapping[str, Any]) -> dict[str, Any]:
    return _standard_study_attention_item(
        context,
        code="study_runtime_recovery_required",
        title_suffix="当前需要优先处理 runtime recovery",
        summary=_non_empty_text(context.get("autonomy_summary"))
        or _non_empty_text(context.get("lane_summary"))
        or "托管运行恢复失败或健康降级，需要尽快介入。",
        command=str(context.get("preferred_command") or context.get("launch_command") or context.get("progress_command") or ""),
    )


def _manual_finishing_attention_item(context: Mapping[str, Any]) -> dict[str, Any]:
    return _standard_study_attention_item(
        context,
        code="study_auto_runtime_parked",
        title_suffix="当前投稿包/人审包交付停驻",
        summary=_non_empty_text(context.get("autonomy_summary"))
        or _non_empty_text(context.get("lane_summary"))
        or _non_empty_text(context.get("current_stage_summary"))
        or _non_empty_text(context.get("next_system_action"))
        or "当前 study 已到投稿包/人审包交付节点，自动运行应停驻并释放资源。",
    )


def _quality_floor_attention_item(context: Mapping[str, Any]) -> dict[str, Any]:
    intervention_lane = dict(context.get("intervention_lane") or {})
    item = _standard_study_attention_item(
        context,
        code="study_quality_floor_blocker",
        title_suffix="当前存在质量硬阻塞",
        summary=_quality_floor_summary(context, intervention_lane),
    )
    item["title"] = _quality_blocker_title(str(context.get("study_id") or "unknown-study"), intervention_lane)
    return item


def _quality_floor_summary(context: Mapping[str, Any], intervention_lane: Mapping[str, Any]) -> str:
    blocker_list = list(context.get("blocker_list") or [])
    return (
        _non_empty_text(dict(context.get("quality_repair_followthrough") or {}).get("summary"))
        or _non_empty_text(context.get("gate_clearing_summary"))
        or _non_empty_text(dict(context.get("same_line_route_truth") or {}).get("summary"))
        or _non_empty_text(dict(context.get("same_line_route_surface") or {}).get("summary"))
        or _non_empty_text(dict(context.get("quality_execution_lane") or {}).get("summary"))
        or _quality_route_focus(intervention_lane)
        or _non_empty_text(context.get("lane_summary"))
        or _non_empty_text(blocker_list[0] if blocker_list else None)
        or "当前 study 存在质量或发表门控硬阻塞。"
    )


def _progress_attention_item(context: Mapping[str, Any], *, code: str, title_suffix: str) -> dict[str, Any]:
    progress_freshness = dict(context.get("progress_freshness") or {})
    default_summary = (
        "最近缺少新的明确研究推进记录，需要排查是否卡住或空转。"
        if code == "study_progress_stale"
        else "当前还没有看到明确的研究推进记录。"
    )
    return _standard_study_attention_item(
        context,
        code=code,
        title_suffix=title_suffix,
        summary=_non_empty_text(dict(context.get("quality_repair_followthrough") or {}).get("summary"))
        or _non_empty_text(context.get("gate_clearing_summary"))
        or _non_empty_text(progress_freshness.get("summary"))
        or default_summary,
    )


def _blocked_study_attention_item(context: Mapping[str, Any]) -> dict[str, Any]:
    same_line_truth = dict(context.get("same_line_route_truth") or {})
    quality_execution = dict(context.get("quality_execution_lane") or {})
    study_id = str(context.get("study_id") or "unknown-study")
    title = _blocked_study_title(study_id, same_line_truth, quality_execution)
    item = _standard_study_attention_item(
        context,
        code="study_blocked",
        title_suffix="仍有主线阻塞",
        summary=_blocked_study_summary(context, same_line_truth, quality_execution),
    )
    item["title"] = title
    return item


def _blocked_study_title(
    study_id: str,
    same_line_truth: Mapping[str, Any],
    quality_execution: Mapping[str, Any],
) -> str:
    return (
        _same_line_route_truth_title(study_id, same_line_truth)
        or _quality_execution_lane_title(study_id, quality_execution)
        or f"{study_id} 仍有主线阻塞"
    )


def _blocked_study_summary(
    context: Mapping[str, Any],
    same_line_truth: Mapping[str, Any],
    quality_execution: Mapping[str, Any],
) -> str:
    blocker_list = list(context.get("blocker_list") or [])
    return (
        _non_empty_text(dict(context.get("quality_repair_followthrough") or {}).get("summary"))
        or _non_empty_text(context.get("gate_clearing_summary"))
        or _non_empty_text(same_line_truth.get("summary"))
        or _non_empty_text(dict(context.get("same_line_route_surface") or {}).get("summary"))
        or _non_empty_text(quality_execution.get("summary"))
        or _non_empty_text(blocker_list[0] if blocker_list else None)
        or _non_empty_text(context.get("current_stage_summary"))
        or _non_empty_text(context.get("next_system_action"))
        or "当前 study 仍有待收口问题。"
    )


__all__ = [
    "_attention_queue",
    "_autonomy_soak_focus",
    "_gate_clearing_followthrough_focus",
    "_quality_execution_focus",
    "_quality_repair_followthrough_focus",
    "_quality_review_followthrough_focus",
    "_operator_status_summary",
    "_same_line_route_focus",
    "_same_line_route_truth_payload",
    "_workspace_operator_brief",
]
