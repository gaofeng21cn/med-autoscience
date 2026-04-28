from __future__ import annotations

from .milestone_parking import finalize_milestone_parking_active, finalize_milestone_parking_summary
from . import shared as _shared
from . import publication_runtime as _publication_runtime
from .quality_review_loop import quality_review_loop_action_required

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_publication_runtime)

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


def _progress_freshness_required(current_stage: str) -> bool:
    return current_stage not in {
        "study_completed",
        "manual_finishing",
        "waiting_physician_decision",
    }


def _append_progress_signal(
    *,
    signals: list[dict[str, Any]],
    timestamp: object,
    source: str,
    summary: object,
) -> None:
    normalized_timestamp = _normalize_timestamp(timestamp)
    rendered_summary = _display_text(summary)
    if normalized_timestamp is None or rendered_summary is None:
        return
    signals.append(
        {
            "timestamp": normalized_timestamp,
            "time_label": _time_label(normalized_timestamp),
            "source": source,
            "summary": rendered_summary,
        }
    )


def _latest_progress_signal(
    *,
    bash_summary_payload: dict[str, Any] | None,
    details_projection_payload: dict[str, Any] | None,
    controller_decision_payload: dict[str, Any] | None,
    publication_eval_payload: dict[str, Any] | None,
) -> dict[str, Any] | None:
    signals: list[dict[str, Any]] = []
    latest_session = (bash_summary_payload or {}).get("latest_session")
    if isinstance(latest_session, dict):
        last_progress = latest_session.get("last_progress")
        if isinstance(last_progress, dict):
            _append_progress_signal(
                signals=signals,
                timestamp=_non_empty_text(last_progress.get("ts")) or _non_empty_text(latest_session.get("updated_at")),
                source="bash_summary",
                summary=_non_empty_text(last_progress.get("message")) or _non_empty_text(last_progress.get("step")),
            )
    if details_projection_payload is not None:
        _append_progress_signal(
            signals=signals,
            timestamp=_non_empty_text(((details_projection_payload.get("summary") or {}).get("updated_at")))
            or _non_empty_text((details_projection_payload or {}).get("generated_at")),
            source="details_projection",
            summary=_non_empty_text(((details_projection_payload.get("summary") or {}).get("status_line"))),
        )
    if controller_decision_payload is not None:
        decision_type = _decision_type_label(controller_decision_payload.get("decision_type")) or "形成控制面决定"
        reason = _display_text(controller_decision_payload.get("reason"))
        summary = f"控制面正式决定：{decision_type}。"
        if reason:
            summary += f" 原因：{reason}"
        _append_progress_signal(
            signals=signals,
            timestamp=controller_decision_payload.get("emitted_at"),
            source="controller_decision",
            summary=summary,
        )
    if publication_eval_payload is not None:
        verdict = (publication_eval_payload.get("verdict") or {}) if isinstance(publication_eval_payload, dict) else {}
        _append_progress_signal(
            signals=signals,
            timestamp=publication_eval_payload.get("emitted_at"),
            source="publication_eval",
            summary=_non_empty_text(verdict.get("summary")) or "发表评估已更新。",
        )
    if not signals:
        return None
    return max(signals, key=lambda item: item["timestamp"])


def _progress_freshness(
    *,
    current_stage: str,
    bash_summary_payload: dict[str, Any] | None,
    details_projection_payload: dict[str, Any] | None,
    controller_decision_payload: dict[str, Any] | None,
    publication_eval_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    required = _progress_freshness_required(current_stage)
    latest_signal = _latest_progress_signal(
        bash_summary_payload=bash_summary_payload,
        details_projection_payload=details_projection_payload,
        controller_decision_payload=controller_decision_payload,
        publication_eval_payload=publication_eval_payload,
    )
    if not required:
        summary = "当前阶段以人工判断或收尾为主，不要求系统继续产出新的自动推进信号。"
        return {
            "status": "not_required",
            "required": False,
            "summary": summary,
            "stale_after_seconds": _PROGRESS_STALE_AFTER_SECONDS,
            "latest_progress_at": latest_signal.get("timestamp") if latest_signal else None,
            "latest_progress_time_label": latest_signal.get("time_label") if latest_signal else None,
            "latest_progress_source": latest_signal.get("source") if latest_signal else None,
            "latest_progress_summary": latest_signal.get("summary") if latest_signal else None,
            "seconds_since_latest_progress": None,
        }
    if latest_signal is None:
        return {
            "status": "missing",
            "required": True,
            "summary": "当前还没有看到明确的研究推进记录，用户现在只能看到监管或状态面。",
            "stale_after_seconds": _PROGRESS_STALE_AFTER_SECONDS,
            "latest_progress_at": None,
            "latest_progress_time_label": None,
            "latest_progress_source": None,
            "latest_progress_summary": None,
            "seconds_since_latest_progress": None,
        }

    progress_freshness_now = _controller_override("_progress_freshness_now", _progress_freshness_now)
    age_seconds = max(
        0,
        int((progress_freshness_now() - datetime.fromisoformat(str(latest_signal["timestamp"]))).total_seconds()),
    )
    if age_seconds > _PROGRESS_STALE_AFTER_SECONDS:
        summary = (
            f"距离上一次明确研究推进已经超过 {_duration_hours_label(_PROGRESS_STALE_AFTER_SECONDS)}，"
            "当前要重点排查是否卡住或空转。"
        )
        status = "stale"
    else:
        summary = f"最近 {_duration_hours_label(_PROGRESS_STALE_AFTER_SECONDS)}内仍有明确研究推进记录。"
        status = "fresh"
    return {
        "status": status,
        "required": True,
        "summary": summary,
        "stale_after_seconds": _PROGRESS_STALE_AFTER_SECONDS,
        "latest_progress_at": latest_signal["timestamp"],
        "latest_progress_time_label": latest_signal["time_label"],
        "latest_progress_source": latest_signal["source"],
        "latest_progress_summary": latest_signal["summary"],
        "seconds_since_latest_progress": age_seconds,
    }


def _current_stage(
    *,
    status: dict[str, Any],
    needs_physician_decision: bool,
    publication_supervisor_state: dict[str, Any],
    autonomous_runtime_notice: dict[str, Any],
    execution_owner_guard: dict[str, Any],
    continuation_state: dict[str, Any],
    runtime_supervision_payload: dict[str, Any] | None,
    supervisor_tick_audit: dict[str, Any],
    manual_finish_contract: dict[str, Any] | None,
    task_intake_progress_override: dict[str, Any] | None,
) -> str:
    quest_status = _non_empty_text(status.get("quest_status"))
    decision = _non_empty_text(status.get("decision"))
    runtime_health_status = _non_empty_text((runtime_supervision_payload or {}).get("health_status"))
    live_managed_runtime = _live_managed_runtime_present(
        status=status,
        autonomous_runtime_notice=autonomous_runtime_notice,
        execution_owner_guard=execution_owner_guard,
        continuation_state=continuation_state,
    )
    if decision == "completed" or (quest_status == "completed" and decision != "blocked"):
        return "study_completed"
    if bool((manual_finish_contract or {}).get("compatibility_guard_only")):
        return "manual_finishing"
    if task_intake_progress_override:
        return "publication_supervision"
    if needs_physician_decision:
        return "waiting_physician_decision"
    if finalize_milestone_parking_active(status):
        return "manual_finishing"
    if runtime_health_status == "recovering" and not live_managed_runtime:
        return "managed_runtime_recovering"
    if runtime_health_status == "degraded" and not live_managed_runtime:
        return "managed_runtime_degraded"
    if runtime_health_status == "escalated" and not live_managed_runtime:
        return "managed_runtime_escalated"
    if _supervisor_tick_gap_present(supervisor_tick_audit):
        return "managed_runtime_supervision_gap"
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


def _live_managed_runtime_present(
    *,
    status: dict[str, Any],
    autonomous_runtime_notice: dict[str, Any],
    execution_owner_guard: dict[str, Any],
    continuation_state: dict[str, Any],
) -> bool:
    runtime_liveness_status = _non_empty_text(status.get("runtime_liveness_status"))
    if runtime_liveness_status == "live":
        return True
    if not bool((execution_owner_guard or {}).get("supervisor_only")):
        return False
    active_run_id = (
        _non_empty_text((execution_owner_guard or {}).get("active_run_id"))
        or _non_empty_text((autonomous_runtime_notice or {}).get("active_run_id"))
        or _non_empty_text((continuation_state or {}).get("active_run_id"))
    )
    if active_run_id is None:
        return False
    guard_reason = _non_empty_text((execution_owner_guard or {}).get("guard_reason"))
    notice_reason = _non_empty_text((autonomous_runtime_notice or {}).get("notification_reason"))
    continuation_quest_status = _non_empty_text((continuation_state or {}).get("quest_status"))
    if continuation_quest_status != "running":
        return False
    return (
        guard_reason in {"live_managed_runtime", "runtime_live"}
        or notice_reason in {"managed_runtime_live", "detected_existing_live_managed_runtime"}
    )


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
    runtime_supervision_payload: dict[str, Any] | None,
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
        summary = (
            _non_empty_text((runtime_supervision_payload or {}).get("clinician_update"))
            or _non_empty_text((runtime_supervision_payload or {}).get("summary"))
            or "托管运行时当前处在健康监管状态。"
        )
        next_action_summary = _non_empty_text((runtime_supervision_payload or {}).get("next_action_summary"))
        if current_stage == "managed_runtime_escalated" and next_action_summary is not None:
            if "人工介入" not in summary:
                summary = f"{summary} 当前需要人工介入。"
            return f"{summary} {next_action_summary}"
        return summary
    if current_stage == "managed_runtime_supervision_gap":
        summary = (
            _non_empty_text((supervisor_tick_audit or {}).get("summary"))
            or "MedAutoScience 外环监管心跳异常，当前不能把托管运行视为被持续监管。"
        )
        next_action_summary = _non_empty_text((supervisor_tick_audit or {}).get("next_action_summary"))
        if next_action_summary is not None:
            return f"{summary} {next_action_summary}"
        return summary
    if current_stage == "waiting_physician_decision":
        summary = "系统已经把研究推进到需要医生/PI 明确确认的节点，目前不会越权自动继续。"
        if latest_progress_message:
            summary += f" 最近一次可见推进是：{latest_progress_message}"
        return summary
    if current_stage == "publication_supervision":
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
        reason = _reason_label(status.get("reason"))
        if reason is not None:
            return reason
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
            or "控制面已经形成正式下一步建议，但该动作需要医生/PI 先确认，系统会停在监管态等待。"
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
    runtime_watch_payload: dict[str, Any] | None,
    current_blockers: list[str],
    execution_owner_guard: dict[str, Any],
    status: dict[str, Any],
    autonomous_runtime_notice: dict[str, Any],
    continuation_state: dict[str, Any],
    runtime_supervision_payload: dict[str, Any] | None,
    supervisor_tick_audit: dict[str, Any],
    manual_finish_contract: dict[str, Any] | None,
    task_intake_progress_override: dict[str, Any] | None,
    evaluation_summary_payload: dict[str, Any] | None,
) -> str:
    if bool((manual_finish_contract or {}).get("compatibility_guard_only")):
        if _task_intake_override_is_manuscript_fast_lane(task_intake_progress_override):
            return (
                _non_empty_text(task_intake_progress_override.get("next_system_action"))
                or "按 controller-visible manuscript fast lane 修订 canonical paper source，并运行 export/sync 与 QC。"
            )
        return (
            _non_empty_text((manual_finish_contract or {}).get("next_action_summary"))
            or "继续保持兼容性与监督入口；如需重新自动续跑，再显式 rerun 或 relaunch。"
        )
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
            return f"等待医生/PI 确认后，再{action_type}。"
        return "等待医生/PI 明确确认后，再继续下一步托管推进。"
    supervisor_tick_next_action = _non_empty_text((supervisor_tick_audit or {}).get("next_action_summary"))
    if _supervisor_tick_gap_present(supervisor_tick_audit) and supervisor_tick_next_action is not None:
        return supervisor_tick_next_action
    decision = _non_empty_text(status.get("decision"))
    if finalize_milestone_parking_active(status):
        return finalize_milestone_parking_summary(status)
    runtime_next_action = _non_empty_text((runtime_supervision_payload or {}).get("next_action_summary"))
    runtime_health_status = _non_empty_text((runtime_supervision_payload or {}).get("health_status"))
    live_managed_runtime = _live_managed_runtime_present(
        status=status,
        autonomous_runtime_notice=autonomous_runtime_notice,
        execution_owner_guard=execution_owner_guard,
        continuation_state=continuation_state,
    )
    if (
        runtime_health_status in {"recovering", "degraded", "escalated"}
        and runtime_next_action is not None
        and not live_managed_runtime
    ):
        return runtime_next_action
    if decision == "blocked":
        reason = _reason_label(status.get("reason"))
        if reason is not None:
            return reason
    publication_action_key = _non_empty_text((publication_supervisor_state or {}).get("current_required_action"))
    route_repair = _publication_eval_route_repair(publication_eval_payload)
    route_repair_action = _route_repair_summary(route_repair)
    if (
        current_blockers
        and route_repair_action is not None
        and _quality_blocker_present(
            publication_eval_payload=publication_eval_payload,
            runtime_watch_payload=runtime_watch_payload,
        )
    ):
        return route_repair_action
    if (
        current_blockers
        and publication_action_key in {"continue_bundle_stage", "complete_bundle_stage"}
        and _quality_blocker_present(
            publication_eval_payload=publication_eval_payload,
            runtime_watch_payload=runtime_watch_payload,
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
    runtime_watch_payload: dict[str, Any] | None,
    runtime_escalation_payload: dict[str, Any] | None,
    controller_confirmation_summary: dict[str, Any] | None,
    controller_decision_payload: dict[str, Any] | None,
    pending_user_interaction: dict[str, Any],
    interaction_arbitration: dict[str, Any] | None,
    runtime_supervision_payload: dict[str, Any] | None,
    supervisor_tick_audit: dict[str, Any],
    progress_freshness: dict[str, Any],
    manual_finish_contract: dict[str, Any] | None,
    task_intake_progress_override: dict[str, Any] | None,
    evaluation_summary_payload: dict[str, Any] | None,
) -> list[str]:
    blockers: list[str] = []
    manual_finish_active = _manual_finish_active(manual_finish_contract)
    if manual_finish_active:
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
        _append_unique(
            blockers,
            _non_empty_text((progress_freshness or {}).get("summary")),
        )
    runtime_health_status = _non_empty_text((runtime_supervision_payload or {}).get("health_status"))
    if runtime_health_status in {"degraded", "escalated"}:
        _append_unique(
            blockers,
            _non_empty_text((runtime_supervision_payload or {}).get("summary"))
            or _non_empty_text((runtime_supervision_payload or {}).get("clinician_update")),
        )
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
    if _controller_confirmation_pending(
        controller_confirmation_summary=controller_confirmation_summary,
        controller_decision_payload=controller_decision_payload,
    ):
        _append_unique(
            blockers,
            _controller_confirmation_summary_text(controller_confirmation_summary)
            or "当前控制面决策需要医生/PI 确认，系统不会自动越权继续。",
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
    controllers_payload = (runtime_watch_payload or {}).get("controllers") or {}
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
    runtime_watch_payload: dict[str, Any] | None,
) -> bool:
    for gap in (publication_eval_payload or {}).get("gaps") or []:
        if isinstance(gap, dict) and _publication_eval_gap_is_blocking(gap):
            return True
    controllers_payload = (runtime_watch_payload or {}).get("controllers") or {}
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
    runtime_watch_payload: dict[str, Any] | None,
    status: dict[str, Any],
    autonomous_runtime_notice: dict[str, Any],
    execution_owner_guard: dict[str, Any],
    continuation_state: dict[str, Any],
    runtime_supervision_payload: dict[str, Any] | None,
    supervisor_tick_audit: dict[str, Any],
    manual_finish_contract: dict[str, Any] | None,
    task_intake_progress_override: dict[str, Any] | None,
    evaluation_summary_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    blocker_summary = _non_empty_text(current_blockers[0] if current_blockers else None)
    progress_status = _non_empty_text((progress_freshness or {}).get("status"))
    runtime_health_status = _non_empty_text((runtime_supervision_payload or {}).get("health_status"))
    live_managed_runtime = _live_managed_runtime_present(
        status=status,
        autonomous_runtime_notice=autonomous_runtime_notice,
        execution_owner_guard=execution_owner_guard,
        continuation_state=continuation_state,
    )

    if _manual_finish_active(manual_finish_contract):
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
            "title": "保持人工收尾兼容保护",
            "severity": "observe",
            "summary": (
                _non_empty_text((manual_finish_contract or {}).get("summary"))
                or current_stage_summary
                or next_system_action
            ),
            "recommended_action_id": "maintain_compatibility_guard",
        }
    if task_intake_progress_override:
        same_line_route_truth = _mapping_copy(task_intake_progress_override.get("same_line_route_truth"))
        payload = {
            "lane_id": "quality_floor_blocker",
            "title": (
                "优先完成有限补充分析"
                if _non_empty_text(same_line_route_truth.get("same_line_state")) == "bounded_analysis"
                else "优先收口同线质量硬阻塞"
            ),
            "severity": "critical",
            "summary": (
                _non_empty_text(task_intake_progress_override.get("next_system_action"))
                or _non_empty_text(task_intake_progress_override.get("blocker_summary"))
                or current_stage_summary
                or next_system_action
            ),
            "recommended_action_id": _non_empty_text(task_intake_progress_override.get("current_required_action"))
            or "inspect_progress",
        }
        if same_line_route_truth:
            payload.update(
                {
                    "repair_mode": _non_empty_text(same_line_route_truth.get("same_line_state")),
                    "route_target": _non_empty_text(same_line_route_truth.get("route_target")),
                    "route_target_label": _non_empty_text(same_line_route_truth.get("route_target_label")),
                    "route_key_question": _non_empty_text(same_line_route_truth.get("current_focus")),
                    "route_summary": _non_empty_text(same_line_route_truth.get("summary")),
                }
            )
        return payload
    if _supervisor_tick_gap_present(supervisor_tick_audit):
        return {
            "lane_id": "workspace_supervision_gap",
            "title": "优先恢复 Hermes-hosted 托管监管",
            "severity": "critical",
            "summary": (
                _non_empty_text((supervisor_tick_audit or {}).get("summary"))
                or current_stage_summary
                or blocker_summary
                or next_system_action
            ),
            "recommended_action_id": "refresh_supervision",
        }
    if finalize_milestone_parking_active(status):
        return {
            "lane_id": "manual_finishing",
            "title": "保持投稿包里程碑停驻",
            "severity": "observe",
            "summary": blocker_summary or current_stage_summary or next_system_action,
            "recommended_action_id": "inspect_progress",
        }
    if runtime_health_status in {"recovering", "degraded", "escalated"} and not live_managed_runtime:
        return {
            "lane_id": "runtime_recovery_required",
            "title": "优先处理 runtime recovery",
            "severity": "critical" if runtime_health_status in {"degraded", "escalated"} else "warning",
            "summary": (
                _non_empty_text((runtime_supervision_payload or {}).get("summary"))
                or _non_empty_text((runtime_supervision_payload or {}).get("clinician_update"))
                or current_stage_summary
                or blocker_summary
                or next_system_action
            ),
            "recommended_action_id": "continue_or_relaunch",
        }
    if _quality_blocker_present(
        publication_eval_payload=publication_eval_payload,
        runtime_watch_payload=runtime_watch_payload,
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
            "lane_id": "human_decision_gate",
            "title": "等待医生或 PI 判断",
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
