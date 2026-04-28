from __future__ import annotations

from typing import Any, Mapping

from .shared import *  # noqa: F403

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
                title="先恢复 Hermes-hosted 常驻监管",
                summary=_non_empty_text(service.get("summary"))
                or "当前 workspace 还没有稳定的 Hermes-hosted 常驻监管入口。",
                recommended_step_id=_attention_step_id("workspace_supervisor_service_not_loaded"),
                recommended_command=commands.get("service_status") or commands.get("service_install"),
                scope="workspace",
            )
        )

    for item in studies:
        study_id = _non_empty_text(item.get("study_id")) or "unknown-study"
        monitoring = dict(item.get("monitoring") or {})
        progress_freshness = dict(item.get("progress_freshness") or {})
        blocker_list = list(item.get("current_blockers") or [])
        operator_verdict = dict(item.get("operator_verdict") or {})
        operator_status_card = dict(item.get("operator_status_card") or {})
        auto_runtime_parked = dict(item.get("auto_runtime_parked") or {})
        autonomy_contract = dict(item.get("autonomy_contract") or {})
        quality_closure_truth = dict(item.get("quality_closure_truth") or {})
        quality_execution_lane = dict(item.get("quality_execution_lane") or {})
        same_line_route_truth = _same_line_route_truth_payload(item)
        same_line_route_surface = dict(item.get("same_line_route_surface") or {})
        quality_repair_followthrough = dict(item.get("quality_repair_followthrough") or {})
        quality_review_followthrough = dict(item.get("quality_review_followthrough") or {})
        gate_clearing_followthrough = dict(item.get("gate_clearing_followthrough") or {})
        autonomy_soak_status = dict(item.get("autonomy_soak_status") or {})
        research_runtime_control_projection = dict(item.get("research_runtime_control_projection") or {})
        gate_clearing_summary = _gate_clearing_followthrough_summary(gate_clearing_followthrough)
        quality_repair_step_id = _non_empty_text(quality_repair_followthrough.get("recommended_step_id"))
        quality_repair_command = _non_empty_text(quality_repair_followthrough.get("recommended_command"))
        gate_clearing_step_id = _non_empty_text(gate_clearing_followthrough.get("recommended_step_id"))
        gate_clearing_command = _non_empty_text(gate_clearing_followthrough.get("recommended_command"))
        progress_command = _non_empty_text(((item.get("commands") or {}).get("progress")))
        launch_command = _non_empty_text(((item.get("commands") or {}).get("launch")))
        preferred_command = quality_repair_command or gate_clearing_command or _non_empty_text(item.get("recommended_command")) or _non_empty_text(
            operator_verdict.get("primary_command")
        )
        supervisor_tick_status = _non_empty_text(monitoring.get("supervisor_tick_status"))
        progress_status = _non_empty_text(progress_freshness.get("status"))
        current_stage_summary = _non_empty_text(item.get("current_stage_summary"))
        next_system_action = _non_empty_text(item.get("next_system_action"))
        intervention_lane = dict(item.get("intervention_lane") or {})
        lane_id = _non_empty_text(intervention_lane.get("lane_id"))
        autonomy_summary = _non_empty_text(autonomy_contract.get("summary"))
        lane_summary = (
            _operator_status_summary(operator_status_card)
            or gate_clearing_summary
            or _non_empty_text(operator_verdict.get("summary"))
            or _non_empty_text(intervention_lane.get("summary"))
            or current_stage_summary
            or next_system_action
        )

        if lane_id in {"user_decision_gate", "human_decision_gate"} or bool(item.get("needs_user_decision")) or bool(
            item.get("needs_physician_decision")
        ):
            queue.append(
                _attention_item(
                    code="study_waiting_user_decision",
                    title=f"{study_id} 需要用户判断",
                    summary=lane_summary or "当前 study 已到需要用户明确决策的节点。",
                    recommended_step_id=quality_repair_step_id or gate_clearing_step_id or _attention_step_id("study_waiting_user_decision"),
                    recommended_command=preferred_command or progress_command,
                    scope="study",
                    study_id=study_id,
                    operator_status_card=operator_status_card,
                    autonomy_contract=autonomy_contract,
                    quality_closure_truth=quality_closure_truth,
                    quality_execution_lane=quality_execution_lane,
                    same_line_route_truth=same_line_route_truth,
                    same_line_route_surface=same_line_route_surface,
                    quality_repair_followthrough=quality_repair_followthrough,
                    quality_review_followthrough=quality_review_followthrough,
                    gate_clearing_followthrough=gate_clearing_followthrough,
                    autonomy_soak_status=autonomy_soak_status,
                    research_runtime_control_projection=research_runtime_control_projection,
                )
            )
            continue
        if lane_id == "auto_runtime_parked" or bool(auto_runtime_parked.get("parked")):
            parked_label = _non_empty_text(auto_runtime_parked.get("parked_state_label"))
            queue.append(
                _attention_item(
                    code="study_auto_runtime_parked",
                    title=f"{study_id} 当前{parked_label or '自动运行已停驻'}",
                    summary=autonomy_summary
                    or lane_summary
                    or _non_empty_text(auto_runtime_parked.get("summary"))
                    or current_stage_summary
                    or next_system_action
                    or "当前 study 已停驻并释放自动运行资源。",
                    recommended_step_id=quality_repair_step_id or gate_clearing_step_id or _attention_step_id("study_auto_runtime_parked"),
                    recommended_command=preferred_command or progress_command,
                    scope="study",
                    study_id=study_id,
                    operator_status_card=operator_status_card,
                    autonomy_contract=autonomy_contract,
                    quality_closure_truth=quality_closure_truth,
                    quality_execution_lane=quality_execution_lane,
                    same_line_route_truth=same_line_route_truth,
                    same_line_route_surface=same_line_route_surface,
                    quality_repair_followthrough=quality_repair_followthrough,
                    quality_review_followthrough=quality_review_followthrough,
                    gate_clearing_followthrough=gate_clearing_followthrough,
                    autonomy_soak_status=autonomy_soak_status,
                    research_runtime_control_projection=research_runtime_control_projection,
                )
            )
            continue
        if lane_id == "workspace_supervision_gap" or supervisor_tick_status in {"stale", "missing", "invalid"}:
            queue.append(
                _attention_item(
                    code="study_supervision_gap",
                    title=f"{study_id} 当前失去新鲜监管心跳",
                    summary=lane_summary or "Hermes-hosted 托管监管存在缺口。",
                    recommended_step_id=quality_repair_step_id or gate_clearing_step_id or _attention_step_id("study_supervision_gap"),
                    recommended_command=preferred_command or commands.get("supervisor_tick") or progress_command,
                    scope="study",
                    study_id=study_id,
                    operator_status_card=operator_status_card,
                    autonomy_contract=autonomy_contract,
                    quality_closure_truth=quality_closure_truth,
                    quality_execution_lane=quality_execution_lane,
                    same_line_route_truth=same_line_route_truth,
                    same_line_route_surface=same_line_route_surface,
                    quality_repair_followthrough=quality_repair_followthrough,
                    quality_review_followthrough=quality_review_followthrough,
                    gate_clearing_followthrough=gate_clearing_followthrough,
                    autonomy_soak_status=autonomy_soak_status,
                    research_runtime_control_projection=research_runtime_control_projection,
                )
            )
            continue
        if lane_id == "runtime_recovery_required":
            queue.append(
                _attention_item(
                    code="study_runtime_recovery_required",
                    title=f"{study_id} 当前需要优先处理 runtime recovery",
                    summary=autonomy_summary or lane_summary or "托管运行恢复失败或健康降级，需要尽快介入。",
                    recommended_step_id=quality_repair_step_id or gate_clearing_step_id or _attention_step_id("study_runtime_recovery_required"),
                    recommended_command=preferred_command or launch_command or progress_command,
                    scope="study",
                    study_id=study_id,
                    operator_status_card=operator_status_card,
                    autonomy_contract=autonomy_contract,
                    quality_closure_truth=quality_closure_truth,
                    quality_execution_lane=quality_execution_lane,
                    same_line_route_truth=same_line_route_truth,
                    same_line_route_surface=same_line_route_surface,
                    quality_repair_followthrough=quality_repair_followthrough,
                    quality_review_followthrough=quality_review_followthrough,
                    gate_clearing_followthrough=gate_clearing_followthrough,
                    autonomy_soak_status=autonomy_soak_status,
                    research_runtime_control_projection=research_runtime_control_projection,
                )
            )
            continue
        if lane_id == "manual_finishing" and (blocker_list or workspace_status in {"attention_required", "blocked"}):
            queue.append(
                _attention_item(
                    code="study_manual_finishing",
                    title=f"{study_id} 当前保持人工收尾兼容保护",
                    summary=autonomy_summary
                    or lane_summary
                    or current_stage_summary
                    or next_system_action
                    or "当前 study 已进入人工收尾兼容保护。",
                    recommended_step_id=quality_repair_step_id or gate_clearing_step_id or _attention_step_id("study_manual_finishing"),
                    recommended_command=preferred_command or progress_command,
                    scope="study",
                    study_id=study_id,
                    operator_status_card=operator_status_card,
                    autonomy_contract=autonomy_contract,
                    quality_closure_truth=quality_closure_truth,
                    quality_execution_lane=quality_execution_lane,
                    same_line_route_truth=same_line_route_truth,
                    same_line_route_surface=same_line_route_surface,
                    quality_repair_followthrough=quality_repair_followthrough,
                    quality_review_followthrough=quality_review_followthrough,
                    gate_clearing_followthrough=gate_clearing_followthrough,
                    autonomy_soak_status=autonomy_soak_status,
                    research_runtime_control_projection=research_runtime_control_projection,
                )
            )
            continue
        if lane_id == "quality_floor_blocker":
            route_focus = _quality_route_focus(intervention_lane)
            queue.append(
                _attention_item(
                    code="study_quality_floor_blocker",
                    title=_quality_blocker_title(study_id, intervention_lane),
                    summary=(
                        _non_empty_text(quality_repair_followthrough.get("summary"))
                        or gate_clearing_summary
                        or _non_empty_text(same_line_route_truth.get("summary"))
                        or _non_empty_text(same_line_route_surface.get("summary"))
                        or
                        _non_empty_text(quality_execution_lane.get("summary"))
                        or
                        route_focus
                        or
                        lane_summary
                        or _non_empty_text(blocker_list[0] if blocker_list else None)
                        or "当前 study 存在质量或发表门控硬阻塞。"
                    ),
                    recommended_step_id=quality_repair_step_id or gate_clearing_step_id or _attention_step_id("study_quality_floor_blocker"),
                    recommended_command=preferred_command or progress_command,
                    scope="study",
                    study_id=study_id,
                    operator_status_card=operator_status_card,
                    autonomy_contract=autonomy_contract,
                    quality_closure_truth=quality_closure_truth,
                    quality_execution_lane=quality_execution_lane,
                    same_line_route_truth=same_line_route_truth,
                    same_line_route_surface=same_line_route_surface,
                    quality_repair_followthrough=quality_repair_followthrough,
                    quality_review_followthrough=quality_review_followthrough,
                    gate_clearing_followthrough=gate_clearing_followthrough,
                    autonomy_soak_status=autonomy_soak_status,
                    research_runtime_control_projection=research_runtime_control_projection,
                )
            )
            continue
        if progress_status == "stale":
            queue.append(
                _attention_item(
                    code="study_progress_stale",
                    title=f"{study_id} 进度信号已陈旧",
                    summary=_non_empty_text(quality_repair_followthrough.get("summary"))
                    or gate_clearing_summary
                    or _non_empty_text(progress_freshness.get("summary"))
                    or "最近缺少新的明确研究推进记录，需要排查是否卡住或空转。",
                    recommended_step_id=quality_repair_step_id or gate_clearing_step_id or _attention_step_id("study_progress_stale"),
                    recommended_command=preferred_command or progress_command,
                    scope="study",
                    study_id=study_id,
                    operator_status_card=operator_status_card,
                    autonomy_contract=autonomy_contract,
                    quality_closure_truth=quality_closure_truth,
                    quality_execution_lane=quality_execution_lane,
                    same_line_route_truth=same_line_route_truth,
                    same_line_route_surface=same_line_route_surface,
                    quality_repair_followthrough=quality_repair_followthrough,
                    quality_review_followthrough=quality_review_followthrough,
                    gate_clearing_followthrough=gate_clearing_followthrough,
                    autonomy_soak_status=autonomy_soak_status,
                    research_runtime_control_projection=research_runtime_control_projection,
                )
            )
            continue
        if progress_status == "missing":
            queue.append(
                _attention_item(
                    code="study_progress_missing",
                    title=f"{study_id} 缺少明确进度信号",
                    summary=_non_empty_text(quality_repair_followthrough.get("summary"))
                    or gate_clearing_summary
                    or _non_empty_text(progress_freshness.get("summary"))
                    or "当前还没有看到明确的研究推进记录。",
                    recommended_step_id=quality_repair_step_id or gate_clearing_step_id or _attention_step_id("study_progress_missing"),
                    recommended_command=preferred_command or progress_command,
                    scope="study",
                    study_id=study_id,
                    operator_status_card=operator_status_card,
                    autonomy_contract=autonomy_contract,
                    quality_closure_truth=quality_closure_truth,
                    quality_execution_lane=quality_execution_lane,
                    same_line_route_truth=same_line_route_truth,
                    same_line_route_surface=same_line_route_surface,
                    quality_repair_followthrough=quality_repair_followthrough,
                    quality_review_followthrough=quality_review_followthrough,
                    gate_clearing_followthrough=gate_clearing_followthrough,
                    autonomy_soak_status=autonomy_soak_status,
                    research_runtime_control_projection=research_runtime_control_projection,
                )
            )
            continue
        if blocker_list or workspace_status in {"attention_required", "blocked"}:
            same_line_title = _same_line_route_truth_title(study_id, same_line_route_truth)
            quality_lane_title = _quality_execution_lane_title(study_id, quality_execution_lane)
            queue.append(
                _attention_item(
                    code="study_blocked",
                    title=same_line_title or quality_lane_title or f"{study_id} 仍有主线阻塞",
                    summary=_non_empty_text(quality_repair_followthrough.get("summary"))
                    or gate_clearing_summary
                    or _non_empty_text(same_line_route_truth.get("summary"))
                    or _non_empty_text(same_line_route_surface.get("summary"))
                    or _non_empty_text(quality_execution_lane.get("summary"))
                    or _non_empty_text(blocker_list[0] if blocker_list else None)
                    or current_stage_summary
                    or next_system_action
                    or "当前 study 仍有待收口问题。",
                    recommended_step_id=quality_repair_step_id or gate_clearing_step_id or _attention_step_id("study_blocked"),
                    recommended_command=preferred_command or progress_command,
                    scope="study",
                    study_id=study_id,
                    operator_status_card=operator_status_card,
                    autonomy_contract=autonomy_contract,
                    quality_closure_truth=quality_closure_truth,
                    quality_execution_lane=quality_execution_lane,
                    same_line_route_truth=same_line_route_truth,
                    quality_repair_followthrough=quality_repair_followthrough,
                    quality_review_followthrough=quality_review_followthrough,
                    gate_clearing_followthrough=gate_clearing_followthrough,
                    autonomy_soak_status=autonomy_soak_status,
                    research_runtime_control_projection=research_runtime_control_projection,
                )
            )

    return sorted(
        queue,
        key=lambda item: (
            int(item.get("priority", 999)),
            str(item.get("study_id") or ""),
            str(item.get("code") or ""),
        ),
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
