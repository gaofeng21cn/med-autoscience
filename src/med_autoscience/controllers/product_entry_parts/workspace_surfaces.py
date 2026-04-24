from __future__ import annotations

from . import shared as _shared
from . import program_surfaces as _program_surfaces

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_program_surfaces)

def _workspace_supervision_summary(
    *,
    studies: list[dict[str, Any]],
    service: dict[str, Any],
) -> dict[str, Any]:
    counts = {
        "total": len(studies),
        "supervisor_fresh": 0,
        "supervisor_gap": 0,
        "recovery_required": 0,
        "quality_blocked": 0,
        "progress_fresh": 0,
        "progress_stale": 0,
        "progress_missing": 0,
        "needs_physician_decision": 0,
    }
    for item in studies:
        monitoring = dict(item.get("monitoring") or {})
        supervisor_tick_status = _non_empty_text(monitoring.get("supervisor_tick_status"))
        if supervisor_tick_status == "fresh":
            counts["supervisor_fresh"] += 1
        elif supervisor_tick_status in {"stale", "missing", "invalid"}:
            counts["supervisor_gap"] += 1

        intervention_lane = dict(item.get("intervention_lane") or {})
        lane_id = _non_empty_text(intervention_lane.get("lane_id"))
        if lane_id == "runtime_recovery_required":
            counts["recovery_required"] += 1
        elif lane_id == "quality_floor_blocker":
            counts["quality_blocked"] += 1

        progress_freshness = dict(item.get("progress_freshness") or {})
        freshness_status = _non_empty_text(progress_freshness.get("status"))
        if freshness_status == "fresh":
            counts["progress_fresh"] += 1
        elif freshness_status == "stale":
            counts["progress_stale"] += 1
        elif freshness_status == "missing":
            counts["progress_missing"] += 1

        if bool(item.get("needs_physician_decision")):
            counts["needs_physician_decision"] += 1

    summary = (
        f"{counts['total']} 个 study；"
        f"{counts['supervisor_gap']} 个监管心跳缺口；"
        f"{counts['recovery_required']} 个恢复异常；"
        f"{counts['quality_blocked']} 个质量阻塞；"
        f"{counts['progress_stale']} 个进度陈旧；"
        f"{counts['progress_missing']} 个缺少明确进度信号。"
    )
    return {
        "service": service,
        "study_counts": counts,
        "summary": summary,
    }


def _mainline_snapshot() -> dict[str, Any]:
    payload = mainline_status.read_mainline_status()
    current_stage = dict(payload.get("current_stage") or {})
    current_program_phase = dict(payload.get("current_program_phase") or {})
    next_focus = _normalized_strings(payload.get("next_focus") or [])
    explicitly_not_now = _normalized_strings(payload.get("explicitly_not_now") or [])
    single_project_boundary = _validate_single_project_boundary(
        _single_project_boundary_payload(payload.get("single_project_boundary")),
        context="mainline_snapshot.single_project_boundary",
    )
    capability_owner_boundary = _validate_capability_owner_boundary(
        _capability_owner_boundary_payload(payload.get("capability_owner_boundary")),
        context="mainline_snapshot.capability_owner_boundary",
    )
    return {
        "program_id": _non_empty_text(payload.get("program_id")),
        "current_stage_id": _non_empty_text(current_stage.get("id")),
        "current_stage_status": _non_empty_text(current_stage.get("status")),
        "current_stage_summary": _non_empty_text(current_stage.get("summary")),
        "current_program_phase_id": _non_empty_text(current_program_phase.get("id")),
        "current_program_phase_status": _non_empty_text(current_program_phase.get("status")),
        "current_program_phase_summary": _non_empty_text(current_program_phase.get("summary")),
        "next_focus": list(next_focus),
        "explicitly_not_now": list(explicitly_not_now),
        "single_project_boundary": single_project_boundary,
        "capability_owner_boundary": capability_owner_boundary,
    }


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
        autonomy_contract = dict(item.get("autonomy_contract") or {})
        quality_closure_truth = dict(item.get("quality_closure_truth") or {})
        quality_execution_lane = dict(item.get("quality_execution_lane") or {})
        same_line_route_truth = _same_line_route_truth_payload(item)
        same_line_route_surface = dict(item.get("same_line_route_surface") or {})
        quality_repair_followthrough = dict(item.get("quality_repair_followthrough") or {})
        quality_review_followthrough = dict(item.get("quality_review_followthrough") or {})
        gate_clearing_followthrough = dict(item.get("gate_clearing_followthrough") or {})
        autonomy_soak_status = dict(item.get("autonomy_soak_status") or {})
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

        if lane_id == "human_decision_gate" or bool(item.get("needs_physician_decision")):
            queue.append(
                _attention_item(
                    code="study_needs_physician_decision",
                    title=f"{study_id} 需要医生或 PI 判断",
                    summary=lane_summary or "当前 study 已到需要人工明确决策的节点。",
                    recommended_step_id=quality_repair_step_id or gate_clearing_step_id or _attention_step_id("study_needs_physician_decision"),
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


def _user_loop(*, profile: WorkspaceProfile, profile_ref: str | Path | None) -> dict[str, str]:
    profile_arg = _profile_arg(profile_ref)
    prefix = _command_prefix(profile_ref)
    return {
        "mainline_status": f"{prefix} mainline-status",
        "phase_status_current": f"{prefix} mainline-phase --phase current",
        "phase_status_next": f"{prefix} mainline-phase --phase next",
        "open_workspace_cockpit": f"{prefix} workspace-cockpit --profile {profile_arg}",
        "submit_task_template": (
            f"{prefix} submit-study-task --profile {profile_arg} --study-id <study_id> "
            "--task-intent '<task_intent>'"
        ),
        "launch_study_template": f"{prefix} launch-study --profile {profile_arg} --study-id <study_id>",
        "watch_progress_template": f"{prefix} study-progress --profile {profile_arg} --study-id <study_id>",
        "refresh_supervision": (
            f"{prefix} watch --runtime-root {_quote_cli_arg(profile.runtime_root)} "
            f"--profile {profile_arg} --ensure-study-runtimes --apply"
        ),
    }


def _study_item(
    *,
    progress_payload: dict[str, Any],
    profile_ref: str | Path | None,
) -> dict[str, Any]:
    study_id = str(progress_payload.get("study_id") or "").strip()
    commands = {
        "launch": (
            f"{_command_prefix(profile_ref)} launch-study --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=study_id)}"
        ),
        "progress": (
            f"{_command_prefix(profile_ref)} study-progress --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=study_id)}"
        ),
        "status": (
            f"{_command_prefix(profile_ref)} study-runtime-status --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=study_id)}"
        ),
    }
    supervision = dict(progress_payload.get("supervision") or {})
    monitoring = {
        "browser_url": _non_empty_text(supervision.get("browser_url")),
        "quest_session_api_url": _non_empty_text(supervision.get("quest_session_api_url")),
        "active_run_id": _non_empty_text(supervision.get("active_run_id")),
        "health_status": _non_empty_text(supervision.get("health_status")),
        "supervisor_tick_status": _non_empty_text(supervision.get("supervisor_tick_status")),
    }
    task_intake = dict(progress_payload.get("task_intake") or {})
    progress_freshness = dict(progress_payload.get("progress_freshness") or {})
    intervention_lane = dict(progress_payload.get("intervention_lane") or {})
    operator_verdict = dict(progress_payload.get("operator_verdict") or {})
    operator_status_card = dict(progress_payload.get("operator_status_card") or {})
    recommended_command = _non_empty_text(progress_payload.get("recommended_command"))
    recommended_commands = [
        dict(item)
        for item in (progress_payload.get("recommended_commands") or [])
        if isinstance(item, dict)
    ]
    autonomy_contract = dict(progress_payload.get("autonomy_contract") or {})
    autonomy_soak_status = dict(progress_payload.get("autonomy_soak_status") or {})
    quality_closure_truth = dict(progress_payload.get("quality_closure_truth") or {})
    quality_execution_lane = dict(progress_payload.get("quality_execution_lane") or {})
    same_line_route_truth = _same_line_route_truth_payload(progress_payload)
    same_line_route_surface = dict(progress_payload.get("same_line_route_surface") or {})
    quality_review_loop = dict(progress_payload.get("quality_review_loop") or {})
    quality_repair_followthrough = dict(progress_payload.get("quality_repair_batch_followthrough") or {})
    quality_review_followthrough = dict(progress_payload.get("quality_review_followthrough") or {})
    gate_clearing_followthrough = _normalized_gate_clearing_followthrough(
        progress_payload,
        fallback_command=commands["progress"],
    )
    recovery_contract = dict(progress_payload.get("recovery_contract") or {})
    research_runtime_control_projection = dict(progress_payload.get("research_runtime_control_projection") or {})
    return {
        "study_id": study_id,
        "current_stage": progress_payload.get("current_stage"),
        "current_stage_summary": progress_payload.get("current_stage_summary"),
        "current_blockers": list(progress_payload.get("current_blockers") or []),
        "next_system_action": progress_payload.get("next_system_action"),
        "intervention_lane": intervention_lane or None,
        "operator_verdict": operator_verdict or None,
        "operator_status_card": operator_status_card or None,
        "recommended_command": recommended_command,
        "recommended_commands": recommended_commands,
        "autonomy_contract": autonomy_contract or None,
        "autonomy_soak_status": autonomy_soak_status or None,
        "quality_closure_truth": quality_closure_truth or None,
        "quality_execution_lane": quality_execution_lane or None,
        "same_line_route_truth": same_line_route_truth or None,
        "same_line_route_surface": same_line_route_surface or None,
        "quality_review_loop": quality_review_loop or None,
        "quality_repair_followthrough": quality_repair_followthrough or None,
        "quality_review_followthrough": quality_review_followthrough or None,
        "gate_clearing_followthrough": gate_clearing_followthrough or None,
        "research_runtime_control_projection": research_runtime_control_projection or None,
        "recovery_contract": recovery_contract or None,
        "needs_physician_decision": bool(progress_payload.get("needs_physician_decision")),
        "monitoring": monitoring,
        "task_intake": task_intake or None,
        "progress_freshness": progress_freshness or None,
        "commands": commands,
    }


def _study_roots(profile: WorkspaceProfile) -> list[Path]:
    if not profile.studies_root.exists():
        return []
    return [
        study_root
        for study_root in sorted(path for path in profile.studies_root.iterdir() if path.is_dir())
        if (study_root / "study.yaml").exists()
    ]


def _workspace_cockpit_study_snapshot(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
    study_root: Path,
) -> tuple[dict[str, Any], list[str]]:
    progress_payload = study_progress.read_study_progress(
        profile=profile,
        profile_ref=profile_ref,
        study_root=study_root,
    )
    item = _study_item(progress_payload=progress_payload, profile_ref=profile_ref)
    alerts = list(item["current_blockers"])
    progress_freshness = dict(item.get("progress_freshness") or {})
    progress_summary = _non_empty_text(progress_freshness.get("summary"))
    if _non_empty_text(progress_freshness.get("status")) in {"stale", "missing"} and progress_summary is not None:
        alerts.append(progress_summary)
    return item, alerts


def read_workspace_cockpit(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
) -> dict[str, Any]:
    build_doctor_report_fn = _controller_override("build_doctor_report", build_doctor_report)
    inspect_workspace_supervision = _controller_override("_inspect_workspace_supervision", _inspect_workspace_supervision)
    doctor_report = build_doctor_report_fn(profile)
    workspace_alerts = _workspace_ready_alerts(doctor_report)
    studies: list[dict[str, Any]] = []
    study_roots = _study_roots(profile)
    if study_roots:
        with ThreadPoolExecutor(max_workers=len(study_roots)) as executor:
            futures = [
                executor.submit(
                    _workspace_cockpit_study_snapshot,
                    profile=profile,
                    profile_ref=profile_ref,
                    study_root=study_root,
                )
                for study_root in study_roots
            ]
            for future in futures:
                item, item_alerts = future.result()
                studies.append(item)
                for alert in item_alerts:
                    if alert not in workspace_alerts:
                        workspace_alerts.append(alert)
    service = inspect_workspace_supervision(profile)
    workspace_supervision = _workspace_supervision_summary(studies=studies, service=service)
    if (
        (not bool(service.get("loaded")) or bool(service.get("drift_reasons")))
        and service.get("summary") not in workspace_alerts
    ):
        workspace_alerts.append(str(service.get("summary")))
    baseline_alerts = _workspace_ready_alerts(doctor_report)
    if workspace_alerts and not baseline_alerts:
        workspace_status = "attention_required"
    elif baseline_alerts:
        workspace_status = "blocked"
    else:
        workspace_status = "ready"
    mainline_snapshot = _mainline_snapshot()
    commands = {
        "mainline_status": f"{_command_prefix(profile_ref)} mainline-status",
        "doctor": f"{_command_prefix(profile_ref)} doctor --profile {_profile_arg(profile_ref)}",
        "bootstrap": f"{_command_prefix(profile_ref)} bootstrap --profile {_profile_arg(profile_ref)}",
        "supervisor_tick": (
            f"{_command_prefix(profile_ref)} watch --runtime-root {_quote_cli_arg(profile.runtime_root)} "
            f"--profile {_profile_arg(profile_ref)} --ensure-study-runtimes --apply"
        ),
        "service_install": f"{_command_prefix(profile_ref)} runtime-ensure-supervision --profile {_profile_arg(profile_ref)}",
        "service_status": f"{_command_prefix(profile_ref)} runtime-supervision-status --profile {_profile_arg(profile_ref)}",
    }
    attention_queue = _attention_queue(
        workspace_status=workspace_status,
        workspace_supervision=workspace_supervision,
        studies=studies,
        commands=commands,
    )
    user_loop = _user_loop(profile=profile, profile_ref=profile_ref)
    operator_brief = _workspace_operator_brief(
        workspace_status=workspace_status,
        workspace_alerts=workspace_alerts,
        attention_queue=attention_queue,
        studies=studies,
        user_loop=user_loop,
        commands=commands,
    )
    phase2_user_product_loop = _build_phase2_user_product_loop(
        profile=profile,
        profile_ref=profile_ref,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "profile_name": profile.name,
        "workspace_root": str(profile.workspace_root),
        "workspace_status": workspace_status,
        "mainline_snapshot": mainline_snapshot,
        "workspace_alerts": workspace_alerts,
        "workspace_supervision": workspace_supervision,
        "attention_queue": attention_queue,
        "operator_brief": operator_brief,
        "user_loop": user_loop,
        "phase2_user_product_loop": phase2_user_product_loop,
        "studies": studies,
        "commands": commands,
    }


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
                f"进度陈旧 {study_counts.get('progress_stale', 0)}；"
                f"进度缺失 {study_counts.get('progress_missing', 0)}；"
                f"等待医生判断 {study_counts.get('needs_physician_decision', 0)}"
            )
    else:
        lines.append("- 当前还没有 workspace 级监管汇总。")
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


def launch_study(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: Path | None = None,
    entry_mode: str | None = None,
    allow_stopped_relaunch: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    resolved_study_id, resolved_study_root, _study_payload = _resolve_study(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    runtime_status = _serialize_runtime_status(
        study_runtime_router.ensure_study_runtime(
            profile=profile,
            study_id=resolved_study_id,
            study_root=resolved_study_root,
            entry_mode=entry_mode,
            allow_stopped_relaunch=allow_stopped_relaunch,
            force=force,
            source="product_entry",
        )
    )
    progress_payload = study_progress.build_study_progress_projection(
        profile=profile,
        profile_ref=profile_ref,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        status_payload=runtime_status,
        entry_mode=entry_mode,
    )
    resolved_study_id = (
        _non_empty_text(progress_payload.get("study_id"))
        or _non_empty_text(runtime_status.get("study_id"))
        or resolved_study_id
    )
    commands = {
        "progress": (
            f"{_command_prefix(profile_ref)} study-progress --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=resolved_study_id)}"
        ),
        "status": (
            f"{_command_prefix(profile_ref)} study-runtime-status --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=resolved_study_id)}"
        ),
        "cockpit": f"{_command_prefix(profile_ref)} workspace-cockpit --profile {_profile_arg(profile_ref)}",
        "supervisor_tick": (
            f"{_command_prefix(profile_ref)} watch --runtime-root {_quote_cli_arg(profile.runtime_root)} "
            f"--profile {_profile_arg(profile_ref)} --ensure-study-runtimes --apply"
        ),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "study_id": resolved_study_id,
        "runtime_status": runtime_status,
        "progress": progress_payload,
        "commands": commands,
    }


def render_launch_study_markdown(payload: dict[str, Any]) -> str:
    progress_payload = dict(payload.get("progress") or {})
    supervision = dict(progress_payload.get("supervision") or {})
    blockers = list(progress_payload.get("current_blockers") or [])
    task_intake = dict(progress_payload.get("task_intake") or {})
    progress_freshness = dict(progress_payload.get("progress_freshness") or {})
    recovery_contract = dict(progress_payload.get("recovery_contract") or {})
    recommended_commands = [
        dict(item)
        for item in (progress_payload.get("recommended_commands") or [])
        if isinstance(item, dict)
    ]
    lines = [
        "# Launch Study",
        "",
        f"- 当前 study: `{payload.get('study_id')}`",
        f"- 当前运行判断: {_runtime_decision_label((payload.get('runtime_status') or {}).get('decision'))}",
        f"- 浏览器入口: `{supervision.get('browser_url') or 'none'}`",
        f"- 当前运行批次: `{supervision.get('active_run_id') or 'none'}`",
    ]
    _append_human_status_lines(lines, progress_payload)
    if task_intake:
        lines.extend(
            [
                f"- 当前任务意图: {task_intake.get('task_intent') or '未提供'}",
                f"- 当前投稿目标: {task_intake.get('journal_target') or 'none'}",
            ]
        )
    if progress_freshness.get("summary"):
        lines.append(f"- 进度信号: {progress_freshness.get('summary')}")
    lines.extend(["", "## Blockers", ""])
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- 当前没有新的硬阻塞。")
    if recovery_contract:
        lines.extend(["", "## 恢复建议", ""])
        if recovery_contract.get("contract_kind"):
            lines.append(f"- 恢复合同类型: `{recovery_contract.get('contract_kind')}`")
        recovery_action_mode_label = _recovery_action_mode_label(recovery_contract)
        if recovery_action_mode_label:
            lines.append(f"- 当前恢复模式: {recovery_action_mode_label}")
        if recovery_contract.get("summary"):
            lines.append(f"- 当前恢复判断: {recovery_contract.get('summary')}")
        for item in recommended_commands:
            title = _non_empty_text(item.get("title")) or _non_empty_text(item.get("step_id")) or "unnamed"
            lines.append(f"- {title}: `{item.get('command') or 'none'}`")
    lines.extend(["", "## Commands", ""])
    for name, command in (payload.get("commands") or {}).items():
        lines.append(f"- `{name}`: `{command}`")
    lines.append("")
    return "\n".join(lines)
__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
