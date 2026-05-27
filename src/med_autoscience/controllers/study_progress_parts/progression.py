from __future__ import annotations

from .activity_timeout_lane import activity_timeout_lane, activity_timeout_state
from .completion_evidence import (
    append_completion_blocker,
    completion_intervention_lane,
    completion_next_action_or_reason,
    completion_progress_freshness_required,
    completion_stage_summary_or_reason,
)
from .milestone_parking import finalize_milestone_parking_active, finalize_milestone_parking_summary
from .parked_progression import parked_intervention_lane, publication_supervisor_blocks_handoff, task_intake_quality_lane
from .runtime_liveness_projection import live_managed_runtime_present, runtime_recovery_pending_from_status
from .specificity_lane import specificity_intervention_lane, specificity_next_system_action, specificity_stage_summary
from .stage_state import current_stage_from_runtime_attempt_state, progress_freshness_required
from .base_progress_freshness import _progress_freshness
from . import shared as _shared
from . import publication_runtime as _publication_runtime
from .quality_review_loop import quality_review_loop_action_required

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_publication_runtime)
_live_managed_runtime_present = live_managed_runtime_present
_runtime_recovery_pending_from_status = runtime_recovery_pending_from_status


def _domain_transition_route_repair(status: dict[str, Any]) -> dict[str, Any] | None:
    domain_transition = _mapping_copy(status.get("domain_transition"))
    if not domain_transition:
        return None
    route_target = _non_empty_text(domain_transition.get("route_target"))
    if route_target is None:
        return None
    next_work_unit = _mapping_copy(domain_transition.get("next_work_unit"))
    unit_id = _non_empty_text(next_work_unit.get("unit_id"))
    summary = _non_empty_text(next_work_unit.get("summary"))
    route_key_question = (
        _non_empty_text(domain_transition.get("route_key_question"))
        or unit_id
        or summary
        or route_target
    )
    action_type = _non_empty_text(domain_transition.get("decision_type")) or "route_back_same_line"
    route_label = _paper_stage_label(route_target) or route_target
    repair_mode = "bounded_analysis" if route_target == "analysis-campaign" else _route_repair_mode(action_type)
    candidate = {
        "action_id": _non_empty_text(domain_transition.get("action_id")),
        "action_type": action_type,
        "priority": _non_empty_text(domain_transition.get("priority")) or "now",
        "repair_mode": repair_mode,
        "repair_mode_label": _ROUTE_REPAIR_MODE_LABELS.get(repair_mode),
        "route_target": route_target,
        "route_target_label": route_label,
        "route_key_question": route_key_question,
        "route_rationale": (
            _non_empty_text(domain_transition.get("route_rationale"))
            or summary
            or _non_empty_text(status.get("reason"))
        ),
    }
    route_summary = _route_repair_summary(candidate)
    if route_summary is not None:
        candidate["route_summary"] = route_summary
    if unit_id is not None:
        candidate["work_unit_id"] = unit_id
    return candidate


def _event(
    *,
    timestamp: str | None,
    category: str,
    title: str,
    summary: str,
    source: str,
    artifact_path: Path | None,
) -> dict[str, Any] | None:
    normalized = _normalize_timestamp(timestamp)
    if normalized is None:
        return None
    return {
        "timestamp": normalized,
        "time_label": _time_label(normalized),
        "category": category,
        "title": title,
        "summary": summary,
        "source": source,
        "artifact_path": str(artifact_path) if artifact_path is not None else None,
    }


def _latest_event_display_tier(category: object) -> int:
    text = _non_empty_text(category)
    if text is None:
        return 0
    return _LATEST_EVENT_DISPLAY_TIERS.get(text, 0)


def _progress_freshness_status_label(status: object) -> str | None:
    text = _non_empty_text(status)
    if text is None:
        return None
    return _PROGRESS_FRESHNESS_STATUS_LABELS.get(text, _humanize_token(text))


def _current_stage(
    *,
    status: dict[str, Any],
    needs_physician_decision: bool,
    publication_supervisor_state: dict[str, Any],
    autonomous_runtime_notice: dict[str, Any],
    execution_owner_guard: dict[str, Any],
    continuation_state: dict[str, Any],
    supervisor_tick_audit: dict[str, Any],
    manual_finish_contract: dict[str, Any] | None,
    task_intake_progress_override: dict[str, Any] | None,
) -> str:
    quest_status = _non_empty_text(status.get("quest_status"))
    decision = _non_empty_text(status.get("decision"))
    runtime_health_snapshot = _mapping_copy(status.get("runtime_health_snapshot"))
    runtime_health_action = _non_empty_text(runtime_health_snapshot.get("canonical_runtime_action"))
    runtime_health_attempt_state = _non_empty_text(runtime_health_snapshot.get("attempt_state"))
    live_managed_runtime = live_managed_runtime_present(
        status=status,
        autonomous_runtime_notice=autonomous_runtime_notice,
        execution_owner_guard=execution_owner_guard,
        continuation_state=continuation_state,
    )
    handoff_blocked_by_supervisor = publication_supervisor_blocks_handoff(_mapping_copy(status.get("publication_supervisor_state")))
    if decision == "completed" or (quest_status == "completed" and decision != "blocked"):
        return "study_completed"
    if task_intake_progress_override:
        return "publication_supervision"
    if manual_finish_guard_only(manual_finish_contract) and not publication_supervisor_blocks_handoff(publication_supervisor_state):
        return "manual_finishing"
    if needs_physician_decision:
        return "waiting_user_decision"
    if finalize_milestone_parking_active(status) and not publication_supervisor_blocks_handoff(publication_supervisor_state):
        return "manual_finishing"
    domain_transition_repair = _domain_transition_route_repair(status)
    if domain_transition_repair is not None and not live_managed_runtime:
        return "publication_supervision"
    if runtime_health_action == "recover_runtime" or runtime_health_attempt_state == "recovering":
        return "managed_runtime_recovering"
    attempt_stage = current_stage_from_runtime_attempt_state(runtime_health_attempt_state)
    if attempt_stage is not None:
        return attempt_stage
    if runtime_recovery_pending_from_status(
        status=status,
        supervisor_tick_audit=supervisor_tick_audit,
        live_managed_runtime=live_managed_runtime,
    ):
        return "managed_runtime_recovering"
    if _supervisor_tick_gap_present(supervisor_tick_audit):
        return "managed_opl_runtime_owner_handoff_gap"
    if decision == "blocked":
        return "runtime_blocked"
    if isinstance(publication_supervisor_state, dict) and _non_empty_text(
        publication_supervisor_state.get("supervisor_phase")
    ):
        return "publication_supervision"
    if bool((execution_owner_guard or {}).get("supervisor_only")) or bool(
        (autonomous_runtime_notice or {}).get("required")
    ):
        return "managed_runtime_active"
    if decision == "blocked":
        return "runtime_blocked"
    return "runtime_preflight"


def _paper_stage_summary(
    *,
    paper_stage: str | None,
    publication_supervisor_state: dict[str, Any],
    publication_eval_payload: dict[str, Any] | None,
) -> str:
    parts: list[str] = []
    stage_label = _paper_stage_label(paper_stage)
    if stage_label is not None:
        parts.append(f"论文当前建议推进到“{stage_label}”阶段。")
    controller_stage_note = _non_empty_text((publication_supervisor_state or {}).get("controller_stage_note"))
    if controller_stage_note is not None:
        parts.append(controller_stage_note)
    if bool((publication_supervisor_state or {}).get("bundle_tasks_downstream_only")):
        parts.append("submission bundle 仍属于后续步骤，当前不会抢跑打包。")
    verdict_summary = _non_empty_text(((publication_eval_payload or {}).get("verdict") or {}).get("summary"))
    if verdict_summary is not None:
        parts.append(f"当前发表判断：{verdict_summary}")
    if not parts:
        parts.append("论文主线仍在收敛中，当前尚未形成明确的下一篇章。")
    return " ".join(parts)


def _task_intake_override_is_manuscript_fast_lane(
    task_intake_progress_override: dict[str, Any] | None,
) -> bool:
    if not isinstance(task_intake_progress_override, dict):
        return False
    fast_lane = _mapping_copy(task_intake_progress_override.get("manuscript_fast_lane"))
    return bool(fast_lane.get("enabled")) or _non_empty_text(fast_lane.get("status")) == "requested"


def _stage_summary(
    *,
    status: dict[str, Any],
    current_stage: str,
    publication_supervisor_state: dict[str, Any],
    publication_eval_payload: dict[str, Any] | None,
    latest_progress_message: str | None,
    supervisor_tick_audit: dict[str, Any],
    manual_finish_contract: dict[str, Any] | None,
    task_intake_progress_override: dict[str, Any] | None,
) -> str:
    if current_stage == "study_completed":
        return "研究主线已经进入结题/交付阶段，系统不会继续自动实验。"
    if current_stage == "manual_finishing":
        if _task_intake_override_is_manuscript_fast_lane(task_intake_progress_override):
            return (
                _non_empty_text(task_intake_progress_override.get("current_stage_summary"))
                or _non_empty_text(task_intake_progress_override.get("blocker_summary"))
                or "当前 study 已转入人工收尾；最新 task intake 要求走 controller-visible manuscript fast lane。"
            )
        return (
            _non_empty_text((manual_finish_contract or {}).get("summary"))
            or "当前 study 已转入人工收尾；MAS 只保持兼容性与监督入口，不再把它视为默认自动续跑对象。"
        )
    if task_intake_progress_override:
        return (
            _non_empty_text(task_intake_progress_override.get("current_stage_summary"))
            or _non_empty_text(task_intake_progress_override.get("blocker_summary"))
            or "最新 task intake 已经接管当前论文线优先级，系统将先回到待修订状态。"
        )
    if current_stage in {
        "managed_runtime_recovering",
        "managed_runtime_degraded",
        "managed_runtime_escalated",
    }:
        if current_stage == "managed_runtime_recovering":
            return "OPL runtime refs 显示当前运行需要恢复；MAS 只保留 domain authority refs，不再物化运行健康 read model。"
        if current_stage == "managed_runtime_escalated":
            return "OPL runtime refs 显示运行恢复已升级；需要等待 OPL current_control_state 或 MAS typed blocker/owner receipt 闭环。"
        return "OPL runtime refs 显示运行健康异常；MAS 不再从 handoff payload 推断运行状态。"
    if current_stage == "managed_opl_runtime_owner_handoff_gap":
        summary = (
            _non_empty_text((supervisor_tick_audit or {}).get("summary"))
            or "MedAutoScience 外环监管心跳异常，当前不能把托管运行视为被持续监管。"
        )
        next_action_summary = _non_empty_text((supervisor_tick_audit or {}).get("next_action_summary"))
        if next_action_summary is not None:
            return f"{summary} {next_action_summary}"
        return summary
    if current_stage in {"waiting_physician_decision", "waiting_user_decision"}:
        summary = "系统已经把研究推进到需要用户明确确认的节点，目前不会越权自动继续。"
        if latest_progress_message:
            summary += f" 最近一次可见推进是：{latest_progress_message}"
        return summary
    if current_stage == "publication_supervision":
        domain_transition_repair = _domain_transition_route_repair(status)
        if domain_transition_repair is not None:
            route_summary = _route_repair_summary(domain_transition_repair, include_rationale=True)
            if route_summary is not None:
                return f"论文质量监管已转入结构化修复：{route_summary}"
        specificity_request = _publication_eval_specificity_request(publication_eval_payload)
        if specificity_request is not None:
            return specificity_stage_summary()
        route_repair = _publication_eval_route_repair(publication_eval_payload)
        route_summary = _route_repair_summary(route_repair, include_rationale=True)
        if route_summary is not None:
            return f"论文质量监管已转入结构化修复：{route_summary}"
        note = _non_empty_text((publication_supervisor_state or {}).get("controller_stage_note"))
        return note or "论文主线当前停在发表监管阶段，系统会先守住可发表性与交付门控。"
    if current_stage == "managed_runtime_active":
        summary = "托管运行时正在自动推进研究，前台当前应以监督为主。"
        if latest_progress_message:
            summary += f" 最近一次可见推进是：{latest_progress_message}"
        return summary
    if current_stage == "runtime_blocked":
        if summary := completion_stage_summary_or_reason(
            status,
            current_stage=current_stage,
            reason_label=_reason_label,
        ):
            return summary
        return "自动推进已被硬阻断，需要先补齐前置条件后才能继续。"
    return "研究运行仍处在准备或轻量评估阶段。"


def _interaction_arbitration_action(interaction_arbitration: dict[str, Any] | None) -> str | None:
    return _non_empty_text((interaction_arbitration or {}).get("action"))


def _resume_arbitration_external_metadata_wait(
    *,
    status: dict[str, Any],
    pending_user_interaction: dict[str, Any],
    interaction_arbitration: dict[str, Any] | None,
) -> bool:
    if _interaction_arbitration_action(interaction_arbitration) != "resume":
        return False
    if _non_empty_text((interaction_arbitration or {}).get("classification")) != "submission_metadata_only":
        return False
    if _non_empty_text(status.get("reason")) != "quest_parked_on_unchanged_finalize_state":
        return False
    if _non_empty_text((pending_user_interaction or {}).get("kind")) != "progress":
        return False
    if _non_empty_text((pending_user_interaction or {}).get("decision_type")) is not None:
        return False
    if not bool((pending_user_interaction or {}).get("relay_required")):
        return False
    if not bool((pending_user_interaction or {}).get("guidance_requires_user_decision")):
        return False
    if not bool((pending_user_interaction or {}).get("expects_reply")):
        return False
    return True


def _supervisor_tick_gap_present(supervisor_tick_audit: dict[str, Any]) -> bool:
    if not bool((supervisor_tick_audit or {}).get("required")):
        return False
    return _non_empty_text((supervisor_tick_audit or {}).get("status")) in _SUPERVISOR_TICK_GAP_STATUSES


def _controller_confirmation_pending(
    *,
    controller_confirmation_summary: dict[str, Any] | None,
    controller_decision_payload: dict[str, Any] | None,
) -> bool:
    summary_status = _non_empty_text((controller_confirmation_summary or {}).get("status"))
    if summary_status is not None:
        return summary_status == "pending" and _controller_human_gate_allowed_from_payload(
            controller_confirmation_summary or {}
        )
    if not bool((controller_decision_payload or {}).get("requires_human_confirmation")):
        return False
    return _controller_human_gate_allowed_from_payload(controller_decision_payload or {})


def _controller_human_gate_allowed_from_payload(payload: dict[str, Any]) -> bool:
    decision_type = _non_empty_text(payload.get("decision_type"))
    if decision_type is None:
        return False
    action_types = payload.get("controller_action_types")
    if not isinstance(action_types, list):
        raw_actions = payload.get("controller_actions")
        action_types = [
            _non_empty_text(action.get("action_type"))
            for action in raw_actions
            if isinstance(action, dict)
        ] if isinstance(raw_actions, list) else []
    try:
        return controller_human_gate_allowed(
            decision_type=decision_type,
            controller_action_types=[action_type for action_type in action_types if action_type],
        )
    except (TypeError, ValueError):
        return False


def _controller_confirmation_summary_text(
    controller_confirmation_summary: dict[str, Any] | None,
) -> str | None:
    if controller_confirmation_summary is None:
        return None
    question = _non_empty_text(controller_confirmation_summary.get("question_for_user"))
    next_action = _non_empty_text(controller_confirmation_summary.get("next_action_if_approved"))
    reason = _non_empty_text(controller_confirmation_summary.get("request_reason"))
    details: list[str] = []
    if question is not None:
        details.append(question)
    if next_action is not None:
        details.append(f"确认后系统将{next_action}。")
    if reason is not None:
        details.append(f"控制面理由：{reason}。")
    return " ".join(details) if details else None


def _needs_physician_decision(
    *,
    status: dict[str, Any],
    controller_confirmation_summary: dict[str, Any] | None,
    controller_decision_payload: dict[str, Any] | None,
    pending_user_interaction: dict[str, Any],
    interaction_arbitration: dict[str, Any] | None,
) -> bool:
    controller_requires = _controller_confirmation_pending(
        controller_confirmation_summary=controller_confirmation_summary,
        controller_decision_payload=controller_decision_payload,
    )
    if controller_requires:
        return True
    if _resume_arbitration_external_metadata_wait(
        status=status,
        pending_user_interaction=pending_user_interaction,
        interaction_arbitration=interaction_arbitration,
    ):
        return True
    arbitration_action = _interaction_arbitration_action(interaction_arbitration)
    if arbitration_action == "resume":
        return False
    pending_requires = bool(
        (pending_user_interaction or {}).get("guidance_requires_user_decision")
        or (
            bool((pending_user_interaction or {}).get("blocking"))
            and bool((pending_user_interaction or {}).get("expects_reply"))
        )
    )
    if arbitration_action == "block":
        return bool((interaction_arbitration or {}).get("requires_user_input")) or pending_requires
    return pending_requires


def _physician_decision_summary(
    *,
    status: dict[str, Any],
    controller_confirmation_summary: dict[str, Any] | None,
    controller_decision_payload: dict[str, Any] | None,
    pending_user_interaction: dict[str, Any],
    interaction_arbitration: dict[str, Any] | None,
) -> str | None:
    if _controller_confirmation_pending(
        controller_confirmation_summary=controller_confirmation_summary,
        controller_decision_payload=controller_decision_payload,
    ):
        return (
            _controller_confirmation_summary_text(controller_confirmation_summary)
            or "控制面已经形成正式下一步建议，但该动作需要用户先确认，系统会停在监管态等待。"
        )
    if _resume_arbitration_external_metadata_wait(
        status=status,
        pending_user_interaction=pending_user_interaction,
        interaction_arbitration=interaction_arbitration,
    ):
        return _non_empty_text((pending_user_interaction or {}).get("summary")) or _non_empty_text(
            (pending_user_interaction or {}).get("message")
        )
    if _interaction_arbitration_action(interaction_arbitration) == "resume":
        return None
    interaction_summary = _non_empty_text((pending_user_interaction or {}).get("summary"))
    if interaction_summary is not None:
        return interaction_summary
    interaction_message = _non_empty_text((pending_user_interaction or {}).get("message"))
    if interaction_message is not None:
        return interaction_message
    return None


def _next_system_action(
    *,
    needs_physician_decision: bool,
    controller_decision_payload: dict[str, Any] | None,
    publication_supervisor_state: dict[str, Any],
    publication_eval_payload: dict[str, Any] | None,
    domain_health_diagnostic_payload: dict[str, Any] | None,
    current_blockers: list[str],
    execution_owner_guard: dict[str, Any],
    status: dict[str, Any],
    autonomous_runtime_notice: dict[str, Any],
    continuation_state: dict[str, Any],
    supervisor_tick_audit: dict[str, Any],
    manual_finish_contract: dict[str, Any] | None,
    task_intake_progress_override: dict[str, Any] | None,
    evaluation_summary_payload: dict[str, Any] | None,
) -> str:
    if manual_finish_guard_only(manual_finish_contract):
        if _task_intake_override_is_manuscript_fast_lane(task_intake_progress_override):
            return (
                _non_empty_text(task_intake_progress_override.get("next_system_action"))
                or "按 controller-visible manuscript fast lane 修订 canonical paper source，并运行 export/sync 与 QC。"
            )
        return (
            _non_empty_text((manual_finish_contract or {}).get("next_action_summary"))
            or "继续保持兼容性与监督入口；如需重新自动续跑，再显式 rerun 或 relaunch。"
        )
    if _non_empty_text(status.get("decision")) == "completed" or (
        _non_empty_text(status.get("quest_status")) == "completed"
        and _non_empty_text(status.get("reason")) == "quest_already_completed"
    ):
        return "保持 completed truth；不派发 runtime repair、publication gate 或 AI reviewer owner。"
    if task_intake_progress_override:
        return (
            _non_empty_text(task_intake_progress_override.get("next_system_action"))
            or _non_empty_text(task_intake_progress_override.get("current_stage_summary"))
            or "先回到最新 task intake 指定的修订范围。"
        )
    if needs_physician_decision:
        controller_actions = list((controller_decision_payload or {}).get("controller_actions") or [])
        first_action = controller_actions[0] if controller_actions else {}
        action_type = _controller_action_label(first_action.get("action_type"))
        if action_type is not None:
            return f"等待用户确认后，再{action_type}。"
        return "等待用户明确确认后，再继续下一步托管推进。"
    supervisor_tick_next_action = _non_empty_text((supervisor_tick_audit or {}).get("next_action_summary"))
    if _supervisor_tick_gap_present(supervisor_tick_audit) and supervisor_tick_next_action is not None:
        return supervisor_tick_next_action
    decision = _non_empty_text(status.get("decision"))
    if finalize_milestone_parking_active(status):
        return finalize_milestone_parking_summary(status)
    runtime_health_snapshot = _mapping_copy(status.get("runtime_health_snapshot"))
    runtime_health_action = _non_empty_text(runtime_health_snapshot.get("canonical_runtime_action"))
    runtime_health_attempt_state = _non_empty_text(runtime_health_snapshot.get("attempt_state"))
    live_managed_runtime = _live_managed_runtime_present(
        status=status,
        autonomous_runtime_notice=autonomous_runtime_notice,
        execution_owner_guard=execution_owner_guard,
        continuation_state=continuation_state,
    )
    domain_transition_repair = _domain_transition_route_repair(status)
    if domain_transition_repair is not None and not live_managed_runtime:
        route_summary = _route_repair_summary(domain_transition_repair)
        if route_summary is not None:
            return route_summary
    if (
        runtime_health_action in {"recover_runtime", "escalate_runtime"}
        or runtime_health_attempt_state in {"recovering", "degraded", "escalated"}
        or runtime_recovery_pending_from_status(
            status=status,
            supervisor_tick_audit=supervisor_tick_audit,
            live_managed_runtime=live_managed_runtime,
        )
    ):
        return "等待 OPL current_control_state 或 stage attempt refs 恢复，并确认 meaningful artifact delta 刷新。"
    if decision == "blocked":
        if action := completion_next_action_or_reason(
            status,
            decision=decision,
            reason_label=_reason_label,
        ):
            return action
    publication_action_key = _non_empty_text((publication_supervisor_state or {}).get("current_required_action"))
    specificity_request = _publication_eval_specificity_request(publication_eval_payload)
    if specificity_request is not None:
        return specificity_next_system_action()
    route_repair = _publication_eval_route_repair(publication_eval_payload)
    route_repair_action = _route_repair_summary(route_repair)
    if (
        current_blockers
        and route_repair_action is not None
        and _quality_blocker_present(
            publication_eval_payload=publication_eval_payload,
            domain_health_diagnostic_payload=domain_health_diagnostic_payload,
        )
    ):
        return route_repair_action
    if (
        current_blockers
        and publication_action_key in {"continue_bundle_stage", "complete_bundle_stage"}
        and _quality_blocker_present(
            publication_eval_payload=publication_eval_payload,
            domain_health_diagnostic_payload=domain_health_diagnostic_payload,
        )
    ):
        return "先修正当前质量阻塞，再决定是否继续投稿打包。"
    quality_review_action = quality_review_loop_action_required(evaluation_summary_payload)
    if quality_review_action is not None:
        return (
            _non_empty_text(quality_review_action.get("recommended_next_action"))
            or _non_empty_text(quality_review_action.get("summary"))
            or "先完成当前质量评审闭环，再继续后续投稿包动作。"
        )
    publication_action = _action_label(publication_action_key)
    if publication_action is not None:
        return publication_action
    guard_action = _action_label((execution_owner_guard or {}).get("current_required_action"))
    if guard_action is not None:
        return guard_action
    if decision in {"create_and_start", "resume", "relaunch_stopped"}:
        return "系统会继续托管推进当前研究运行。"
    return "继续轮询研究状态，并把新的阶段变化投影到前台。"


def _current_blockers(
    *,
    status: dict[str, Any],
    publication_eval_payload: dict[str, Any] | None,
    domain_health_diagnostic_payload: dict[str, Any] | None,
    runtime_escalation_payload: dict[str, Any] | None,
    controller_confirmation_summary: dict[str, Any] | None,
    controller_decision_payload: dict[str, Any] | None,
    pending_user_interaction: dict[str, Any],
    interaction_arbitration: dict[str, Any] | None,
    supervisor_tick_audit: dict[str, Any],
    progress_freshness: dict[str, Any],
    manual_finish_contract: dict[str, Any] | None,
    task_intake_progress_override: dict[str, Any] | None,
    evaluation_summary_payload: dict[str, Any] | None,
) -> list[str]:
    blockers: list[str] = []
    if _non_empty_text(status.get("decision")) == "completed":
        return blockers
    if (
        _non_empty_text(status.get("quest_status")) == "completed"
        and _non_empty_text(status.get("reason")) == "quest_already_completed"
    ):
        return blockers
    manual_finish_active = _manual_finish_active(manual_finish_contract)
    if manual_finish_active or finalize_milestone_parking_active(status):
        return blockers
    metadata_wait = _resume_arbitration_external_metadata_wait(
        status=status,
        pending_user_interaction=pending_user_interaction,
        interaction_arbitration=interaction_arbitration,
    )
    if _supervisor_tick_gap_present(supervisor_tick_audit):
        _append_unique(
            blockers,
            _non_empty_text((supervisor_tick_audit or {}).get("summary")),
        )
    if _non_empty_text((progress_freshness or {}).get("status")) in {"stale", "missing"}:
        if completion_progress_freshness_required(status):
            _append_unique(
                blockers,
                _non_empty_text((progress_freshness or {}).get("summary")),
            )
    runtime_health_snapshot = _mapping_copy(status.get("runtime_health_snapshot"))
    for reason in runtime_health_snapshot.get("blocking_reasons") or []:
        _append_unique(blockers, _reason_label(reason) or _non_empty_text(reason))
    if task_intake_progress_override:
        _append_unique(blockers, _non_empty_text(task_intake_progress_override.get("blocker_summary")))
    else:
        quality_review_action = quality_review_loop_action_required(evaluation_summary_payload)
        if quality_review_action is not None:
            for issue in quality_review_action.get("blocking_issues") or []:
                _append_unique(blockers, _non_empty_text(issue))
            if not quality_review_action.get("blocking_issues"):
                _append_unique(
                    blockers,
                    _non_empty_text(quality_review_action.get("summary"))
                    or _non_empty_text(quality_review_action.get("recommended_next_action")),
                )
    if (
        _non_empty_text(status.get("decision")) == "blocked"
        and not manual_finish_active
        and not task_intake_progress_override
    ):
        _append_unique(
            blockers,
            _reason_label(status.get("reason")) or _non_empty_text(status.get("reason")),
        )
    append_completion_blocker(blockers, status, _append_unique)
    if _controller_confirmation_pending(
        controller_confirmation_summary=controller_confirmation_summary,
        controller_decision_payload=controller_decision_payload,
    ):
        _append_unique(
            blockers,
            _controller_confirmation_summary_text(controller_confirmation_summary)
            or "当前控制面决策需要用户确认，系统不会自动越权继续。",
        )
    if metadata_wait and not task_intake_progress_override:
        _append_unique(
            blockers,
            _non_empty_text((pending_user_interaction or {}).get("summary"))
            or _non_empty_text((pending_user_interaction or {}).get("message")),
        )
    if _interaction_arbitration_action(interaction_arbitration) != "resume" and bool(
        (pending_user_interaction or {}).get("blocking")
    ):
        _append_unique(
            blockers,
            _non_empty_text((pending_user_interaction or {}).get("summary"))
            or _non_empty_text((pending_user_interaction or {}).get("message")),
        )
    for gap in (publication_eval_payload or {}).get("gaps") or []:
        if isinstance(gap, dict) and _publication_eval_gap_is_blocking(gap):
            _append_unique(blockers, _non_empty_text(gap.get("summary")))
    controllers_payload = (domain_health_diagnostic_payload or {}).get("controllers") or {}
    if isinstance(controllers_payload, dict):
        for controller_payload in controllers_payload.values():
            if not isinstance(controller_payload, dict):
                continue
            for blocker in controller_payload.get("blockers") or []:
                _append_unique(blockers, _watch_blocker_label(blocker))
            if _non_empty_text(controller_payload.get("status")) == "blocked":
                _append_unique(
                    blockers,
                    _non_empty_text(controller_payload.get("controller_stage_note"))
                    or _non_empty_text(controller_payload.get("controller_note")),
                )
    _append_unique(blockers, _reason_label((runtime_escalation_payload or {}).get("reason")))
    return blockers


def _quality_blocker_present(
    *,
    publication_eval_payload: dict[str, Any] | None,
    domain_health_diagnostic_payload: dict[str, Any] | None,
) -> bool:
    for gap in (publication_eval_payload or {}).get("gaps") or []:
        if isinstance(gap, dict) and _publication_eval_gap_is_blocking(gap):
            return True
    controllers_payload = (domain_health_diagnostic_payload or {}).get("controllers") or {}
    if not isinstance(controllers_payload, dict):
        return False
    for controller_payload in controllers_payload.values():
        if not isinstance(controller_payload, dict):
            continue
        blockers = list(controller_payload.get("blockers") or [])
        if blockers:
            return True
        if _non_empty_text(controller_payload.get("status")) == "blocked" and (
            _non_empty_text(controller_payload.get("controller_stage_note"))
            or _non_empty_text(controller_payload.get("controller_note"))
        ):
            return True
    return False


def _intervention_lane(
    *,
    current_stage: str,
    current_stage_summary: str,
    current_blockers: list[str],
    next_system_action: str,
    needs_physician_decision: bool,
    progress_freshness: dict[str, Any],
    publication_eval_payload: dict[str, Any] | None,
    domain_health_diagnostic_payload: dict[str, Any] | None,
    status: dict[str, Any],
    autonomous_runtime_notice: dict[str, Any],
    execution_owner_guard: dict[str, Any],
    continuation_state: dict[str, Any],
    supervisor_tick_audit: dict[str, Any],
    manual_finish_contract: dict[str, Any] | None,
    task_intake_progress_override: dict[str, Any] | None,
    evaluation_summary_payload: dict[str, Any] | None,
    auto_runtime_parked: dict[str, Any] | None,
) -> dict[str, Any]:
    blocker_summary = _non_empty_text(current_blockers[0] if current_blockers else None)
    progress_status = _non_empty_text((progress_freshness or {}).get("status"))
    live_managed_runtime = _live_managed_runtime_present(
        status=status,
        autonomous_runtime_notice=autonomous_runtime_notice,
        execution_owner_guard=execution_owner_guard,
        continuation_state=continuation_state,
    )
    handoff_blocked_by_supervisor = publication_supervisor_blocks_handoff(_mapping_copy(status.get("publication_supervisor_state")))

    if current_stage == "study_completed":
        return {
            "lane_id": "completed",
            "title": "研究已结题",
            "severity": "observe",
            "summary": current_stage_summary or "研究主线已经进入结题/交付阶段，系统不会继续自动实验。",
            "recommended_action_id": "inspect_progress",
        }
    specificity_request = _publication_eval_specificity_request(publication_eval_payload)
    if specificity_request is not None:
        return specificity_intervention_lane(specificity_request)
    domain_transition_repair = _domain_transition_route_repair(status)
    if domain_transition_repair is not None and not live_managed_runtime:
        route_summary = _route_repair_summary(domain_transition_repair)
        payload = {
            "lane_id": "quality_floor_blocker",
            "title": (
                "优先完成有限补充分析"
                if _non_empty_text(domain_transition_repair.get("repair_mode")) == "bounded_analysis"
                else "优先收口同线质量硬阻塞"
            ),
            "severity": "critical",
            "summary": route_summary or blocker_summary or current_stage_summary or next_system_action,
            "recommended_action_id": _non_empty_text(domain_transition_repair.get("action_type")) or "inspect_progress",
        }
        payload.update(domain_transition_repair)
        return payload
    if activity_timeout_state(progress_freshness) == "timed_out":
        return activity_timeout_lane(
            progress_freshness=progress_freshness,
            current_stage_summary=current_stage_summary,
            blocker_summary=blocker_summary,
            next_system_action=next_system_action,
        )
    lane = parked_intervention_lane(
        auto_runtime_parked,
        current_stage_summary=current_stage_summary,
        next_system_action=next_system_action,
    )
    if lane is not None:
        return lane
    if task_intake_progress_override and not _task_intake_override_is_manuscript_fast_lane(task_intake_progress_override):
        lane = task_intake_quality_lane(
            task_intake_progress_override,
            current_stage_summary=current_stage_summary,
            next_system_action=next_system_action,
        )
        if lane is not None:
            return lane
    if _manual_finish_active(manual_finish_contract) and not handoff_blocked_by_supervisor:
        if _task_intake_override_is_manuscript_fast_lane(task_intake_progress_override):
            same_line_route_truth = _mapping_copy(task_intake_progress_override.get("same_line_route_truth"))
            return {
                "lane_id": "manual_finishing_fast_lane",
                "title": "执行论文快修通道",
                "severity": "observe",
                "summary": (
                    _non_empty_text(task_intake_progress_override.get("next_system_action"))
                    or _non_empty_text(task_intake_progress_override.get("blocker_summary"))
                    or current_stage_summary
                    or next_system_action
                ),
                "recommended_action_id": _non_empty_text(
                    task_intake_progress_override.get("current_required_action")
                )
                or "run_manuscript_fast_lane",
                "repair_mode": _non_empty_text(same_line_route_truth.get("same_line_state")),
                "route_target": _non_empty_text(same_line_route_truth.get("route_target")),
                "route_target_label": _non_empty_text(same_line_route_truth.get("route_target_label")),
                "route_key_question": _non_empty_text(same_line_route_truth.get("current_focus")),
                "route_summary": _non_empty_text(same_line_route_truth.get("summary")),
            }
        return {
            "lane_id": "manual_finishing",
            "title": "保持人工收尾显式保护",
            "severity": "observe",
            "summary": (
                _non_empty_text((manual_finish_contract or {}).get("summary"))
                or current_stage_summary
                or next_system_action
            ),
            "recommended_action_id": "maintain_manual_finish_guard",
        }
    lane = task_intake_quality_lane(
        task_intake_progress_override,
        current_stage_summary=current_stage_summary,
        next_system_action=next_system_action,
    )
    if lane is not None:
        return lane
    completion_lane = completion_intervention_lane(status)
    if completion_lane is not None:
        return completion_lane
    if _supervisor_tick_gap_present(supervisor_tick_audit):
        return {
            "lane_id": "workspace_supervision_gap",
            "title": "优先刷新 OPL runtime manager 托管监管",
            "severity": "critical",
            "summary": (
                _non_empty_text((supervisor_tick_audit or {}).get("summary"))
                or current_stage_summary
                or blocker_summary
                or next_system_action
            ),
            "recommended_action_id": "refresh_supervision",
        }
    if finalize_milestone_parking_active(status) and not handoff_blocked_by_supervisor:
        return {
            "lane_id": "manual_finishing",
            "title": "保持投稿包里程碑停驻",
            "severity": "observe",
            "summary": finalize_milestone_parking_summary(status),
            "recommended_action_id": "inspect_progress",
        }
    if current_stage in {"managed_runtime_recovering", "managed_runtime_degraded", "managed_runtime_escalated"}:
        return {
            "lane_id": "runtime_recovery_required",
            "title": "优先处理 OPL runtime recovery",
            "severity": "critical" if current_stage in {"managed_runtime_degraded", "managed_runtime_escalated"} else "warning",
            "summary": current_stage_summary or blocker_summary or next_system_action,
            "recommended_action_id": "continue_or_relaunch",
        }
    if _quality_blocker_present(
        publication_eval_payload=publication_eval_payload,
        domain_health_diagnostic_payload=domain_health_diagnostic_payload,
    ):
        route_repair = _publication_eval_route_repair(publication_eval_payload)
        route_summary = _route_repair_summary(route_repair)
        payload = {
            "lane_id": "quality_floor_blocker",
            "title": (
                "优先完成有限补充分析"
                if _non_empty_text((route_repair or {}).get("repair_mode")) == "bounded_analysis"
                else "优先收口同线质量硬阻塞"
                if route_repair is not None
                else "优先收口质量硬阻塞"
            ),
            "severity": "critical",
            "summary": route_summary or blocker_summary or current_stage_summary or next_system_action,
            "recommended_action_id": _non_empty_text((route_repair or {}).get("action_type")) or "inspect_progress",
        }
        if route_repair is not None:
            payload.update(route_repair)
        return payload
    quality_review_action = quality_review_loop_action_required(evaluation_summary_payload)
    if quality_review_action is not None:
        return {
            "lane_id": "quality_floor_blocker",
            "title": (
                "优先完成 AI reviewer 质量闭环"
                if bool(quality_review_action.get("mentions_ai_reviewer"))
                else "优先完成质量评审闭环"
            ),
            "severity": "critical",
            "summary": (
                _non_empty_text(quality_review_action.get("recommended_next_action"))
                or _non_empty_text(quality_review_action.get("summary"))
                or blocker_summary
                or current_stage_summary
                or next_system_action
            ),
            "recommended_action_id": "complete_quality_review_loop",
        }
    if needs_physician_decision:
        return {
            "lane_id": "user_decision_gate",
            "title": "等待用户判断",
            "severity": "handoff",
            "summary": current_stage_summary or blocker_summary or next_system_action,
            "recommended_action_id": "inspect_progress",
        }
    if progress_status in {"stale", "missing"}:
        return {
            "lane_id": "study_progress_gap",
            "title": "优先检查研究是否卡住",
            "severity": "warning",
            "summary": (
                _non_empty_text((progress_freshness or {}).get("summary"))
                or current_stage_summary
                or blocker_summary
                or next_system_action
            ),
            "recommended_action_id": "inspect_progress",
        }
    if current_stage == "runtime_blocked":
        return {
            "lane_id": "runtime_blocker",
            "title": "优先恢复或重启当前 study",
            "severity": "warning",
            "summary": current_stage_summary or blocker_summary or next_system_action,
            "recommended_action_id": "continue_or_relaunch",
        }
    return {
        "lane_id": "monitor_only",
        "title": "继续监督当前 study",
        "severity": "observe",
        "summary": current_stage_summary or next_system_action or "当前 study 没有新的接管动作。",
        "recommended_action_id": "inspect_progress",
    }
__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
