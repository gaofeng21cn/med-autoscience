from __future__ import annotations

from collections.abc import Mapping

from .workspace_attention import (
    _attention_queue,
    _autonomy_soak_focus,
    _gate_clearing_followthrough_focus,
    _quality_execution_focus,
    _quality_repair_followthrough_focus,
    _quality_review_followthrough_focus,
    _operator_status_summary,
    _same_line_route_focus,
    _same_line_route_truth_payload,
    _workspace_operator_brief,
)
from .paper_orchestra_operator import (
    build_workspace_paper_orchestra_operator_projection,
    render_paper_orchestra_operator_projection_lines,
)
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
        "needs_user_decision": 0,
        "auto_runtime_parked": 0,
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
        elif lane_id == "auto_runtime_parked":
            counts["auto_runtime_parked"] += 1

        progress_freshness = dict(item.get("progress_freshness") or {})
        freshness_status = _non_empty_text(progress_freshness.get("status"))
        if freshness_status == "fresh":
            counts["progress_fresh"] += 1
        elif freshness_status == "stale":
            counts["progress_stale"] += 1
        elif freshness_status == "missing":
            counts["progress_missing"] += 1

        if bool(item.get("needs_user_decision")) or bool(item.get("needs_physician_decision")):
            counts["needs_user_decision"] += 1
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


def _workspace_ai_first_operations_state(*, studies: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {
        "study_count": len(studies),
        "dashboard_count": 0,
        "default_entry_state_count": 0,
        "feedback_state_count": 0,
        "attention_required": 0,
        "human_review_required": 0,
        "ai_reviewer_trace_incomplete": 0,
        "route_back_active": 0,
        "artifact_refresh_pending": 0,
        "open_feedback_count": 0,
        "repeat_toil_count": 0,
        "manual_judgment_pending": 0,
    }
    study_dashboards: list[dict[str, Any]] = []
    for item in studies:
        projection = _ai_first_operations_study_projection(item)
        if not projection:
            continue
        counts["dashboard_count"] += 1
        if projection.get("read_model") == "ai_first_default_entry_state_read_model":
            counts["default_entry_state_count"] += 1
        blockers = [str(value) for value in (projection.get("blockers") or []) if str(value).strip()]
        if blockers:
            counts["attention_required"] += 1
        if bool(projection.get("human_review_required")):
            counts["human_review_required"] += 1

        if projection.get("ai_reviewer_trace_complete") is False:
            counts["ai_reviewer_trace_incomplete"] += 1

        if _coerce_int(projection.get("route_back_count")) > 0:
            counts["route_back_active"] += 1

        if _coerce_int(projection.get("stale_artifact_count")) > 0:
            counts["artifact_refresh_pending"] += 1
        feedback_counts = dict(projection.get("feedback_counts") or {})
        if feedback_counts:
            counts["feedback_state_count"] += 1
            counts["open_feedback_count"] += _coerce_int(feedback_counts.get("open_feedback_count"))
            counts["repeat_toil_count"] += _coerce_int(feedback_counts.get("repeat_toil_count"))
            counts["manual_judgment_pending"] += _coerce_int(
                feedback_counts.get("manual_judgment_pending_count")
            )

        study_dashboards.append(projection)

    if counts["dashboard_count"] == 0:
        status = "not_available"
        summary = "当前还没有可汇总的 AI-first operations runtime state。"
    elif (
        counts["ai_reviewer_trace_incomplete"]
        or counts["route_back_active"]
        or counts["artifact_refresh_pending"]
        or counts["attention_required"]
        or counts["human_review_required"]
    ):
        status = "attention_required"
        summary = (
            f"{counts['dashboard_count']} 个 study 已接入 AI-first operations state；"
            f"{counts['ai_reviewer_trace_incomplete']} 个 AI reviewer trace 不完整；"
            f"{counts['route_back_active']} 个 route-back 未闭环；"
            f"{counts['artifact_refresh_pending']} 个产物需要从 canonical source 刷新；"
            f"{counts['human_review_required']} 个等待人工判断；"
            f"{counts['open_feedback_count']} 个运行反馈信号打开。"
        )
    else:
        status = "on_track"
        summary = (
            f"{counts['dashboard_count']} 个 study 已接入 AI-first operations state；"
            "当前 pre-draft、AI reviewer workflow、artifact proof 与 route-back 没有新的可见阻塞。"
        )
    return {
        "surface_kind": "workspace_ai_first_operations_state",
        "read_model": "ai_first_default_entry_state_read_model"
        if counts["default_entry_state_count"]
        else "ai_first_operations_dashboard_read_model",
        "authority": "observability_only",
        "status": status,
        "summary": summary,
        "counts": counts,
        "study_dashboards": study_dashboards,
    }


def _ai_first_operations_study_projection(item: Mapping[str, Any]) -> dict[str, Any] | None:
    feedback_state = dict(item.get("ai_first_feedback_state") or {})
    default_state = dict(item.get("ai_first_default_entry_state") or {})
    if default_state:
        return _attach_feedback_projection(
            _ai_first_default_entry_state_projection(item=item, default_state=default_state),
            feedback_state=feedback_state,
        )
    dashboard = dict(item.get("ai_first_operations_dashboard") or {})
    if dashboard:
        return _attach_feedback_projection(
            _legacy_ai_first_dashboard_projection(item=item, dashboard=dashboard),
            feedback_state=feedback_state,
        )
    if feedback_state:
        return _attach_feedback_projection(
            {
                "study_id": item.get("study_id"),
                "read_model": "ai_first_feedback_read_model",
                "source_surface": "ai_first_feedback_state",
                "current_stage": feedback_state.get("current_stage") or item.get("current_stage"),
                "blockers": [],
                "next_step": (feedback_state.get("user_view") or {}).get("next_step"),
                "human_review_required": bool(
                    (feedback_state.get("user_view") or {}).get("human_review_required")
                ),
                "authority": "observability_only",
            },
            feedback_state=feedback_state,
        )
    return None


def _attach_feedback_projection(
    projection: dict[str, Any],
    *,
    feedback_state: Mapping[str, Any],
) -> dict[str, Any]:
    if not feedback_state:
        return projection
    user_view = dict(feedback_state.get("user_view") or {})
    counts = dict(feedback_state.get("counts") or {})
    primary = dict(feedback_state.get("primary_feedback") or {})
    primary_action = dict(feedback_state.get("primary_action") or {})
    updated = dict(projection)
    updated["feedback_status"] = feedback_state.get("status")
    updated["feedback_summary"] = feedback_state.get("summary")
    updated["feedback_primary_category"] = primary.get("category")
    updated["feedback_primary_reason"] = user_view.get("primary_feedback_reason")
    updated["feedback_action_id"] = primary_action.get("action_id")
    updated["feedback_action_target_surface"] = primary_action.get("target_surface")
    updated["feedback_action_summary"] = primary_action.get("summary") or user_view.get("next_action")
    updated["feedback_counts"] = counts
    updated["human_review_required"] = bool(
        updated.get("human_review_required") or user_view.get("human_review_required")
    )
    updated["next_step"] = updated.get("next_step") or user_view.get("next_step")
    return updated


def _ai_first_default_entry_state_projection(
    *,
    item: Mapping[str, Any],
    default_state: Mapping[str, Any],
) -> dict[str, Any]:
    pre_draft = _state_section(default_state, "pre_draft", "pre_draft_state")
    ai_reviewer_workflow = _state_section(
        default_state,
        "ai_reviewer_workflow",
        "ai_reviewer_workflow_state",
        "ai_reviewer",
    )
    artifact_proof = _state_section(
        default_state,
        "artifact_proof",
        "artifact_proof_state",
        "proof",
    )
    route_back = _state_section(default_state, "route_back", "route_back_state")
    human_judgment = _state_section(
        default_state,
        "human_judgment",
        "manual_judgment",
        "human_review",
    )
    blockers = _normalized_strings(default_state.get("blockers") or default_state.get("attention"))
    human_review_required = (
        _state_bool(human_judgment, "required", "human_review_required", "manual_judgment_required")
        or bool(default_state.get("human_review_required"))
        or bool(default_state.get("manual_judgment_required"))
    )
    return {
        "study_id": item.get("study_id"),
        "read_model": "ai_first_default_entry_state_read_model",
        "source_surface": _non_empty_text(default_state.get("surface"))
        or "ai_first_default_entry_state",
        "current_stage": _first_text(
            default_state.get("current_stage"),
            default_state.get("stage"),
            item.get("current_stage"),
        ),
        "blockers": blockers,
        "pre_draft_status": _state_label(pre_draft),
        "ai_reviewer_workflow_status": _state_label(ai_reviewer_workflow),
        "artifact_proof_status": _state_label(artifact_proof),
        "route_back_status": _state_label(route_back),
        "next_step": _first_text(
            default_state.get("next_step"),
            default_state.get("next_action"),
            (default_state.get("next") or {}).get("summary")
            if isinstance(default_state.get("next"), Mapping)
            else None,
        ),
        "human_judgment": _state_label(human_judgment),
        "human_review_required": human_review_required,
        "ai_reviewer_trace_complete": _state_bool(
            ai_reviewer_workflow,
            "trace_complete",
            "complete",
            "ai_reviewer_trace_complete",
        ),
        "route_back_count": _route_back_count(route_back),
        "route_back_target": _first_text(route_back.get("target"), route_back.get("return_to")),
        "stale_artifact_count": _artifact_refresh_count(artifact_proof),
        "current_package_from_canonical_source": _state_bool(
            artifact_proof,
            "current_package_from_canonical_source",
            "from_canonical_source",
        ),
        "quality_toil_count": _coerce_int(default_state.get("quality_toil_count")),
        "recommended_command": item.get("recommended_command")
        or ((item.get("commands") or {}).get("progress")),
        "authority": "observability_only",
    }


def _legacy_ai_first_dashboard_projection(
    *,
    item: Mapping[str, Any],
    dashboard: Mapping[str, Any],
) -> dict[str, Any]:
    user_view = dict(dashboard.get("user_view") or {})
    maintainer_view = dict(dashboard.get("maintainer_view") or {})
    blockers = [str(value) for value in (user_view.get("blockers") or []) if str(value).strip()]
    ai_reviewer_trace = dict(maintainer_view.get("ai_reviewer_trace") or {})
    route_back = dict(maintainer_view.get("route_back") or {})
    route_back_count = _coerce_int(route_back.get("count"))
    artifact_stale = dict(maintainer_view.get("artifact_stale") or {})
    stale_artifact_count = _coerce_int(artifact_stale.get("stale_artifact_count"))
    return {
        "study_id": item.get("study_id"),
        "read_model": "ai_first_operations_dashboard_read_model",
        "source_surface": _non_empty_text(dashboard.get("surface"))
        or "ai_first_operations_dashboard",
        "current_stage": user_view.get("current_stage"),
        "blockers": blockers,
        "pre_draft_status": _first_text(user_view.get("pre_draft_status"), user_view.get("current_stage")),
        "ai_reviewer_workflow_status": "完整" if ai_reviewer_trace.get("complete") else "不完整",
        "artifact_proof_status": "有待刷新产物" if stale_artifact_count > 0 else "无待刷新产物",
        "route_back_status": _first_text(route_back.get("summary"), route_back.get("target")),
        "next_step": user_view.get("next_step"),
        "human_judgment": "等待人工判断" if bool(user_view.get("human_review_required")) else "暂不需要人工判断",
        "human_review_required": bool(user_view.get("human_review_required")),
        "ai_reviewer_trace_complete": ai_reviewer_trace.get("complete"),
        "route_back_count": route_back_count,
        "route_back_target": route_back.get("target"),
        "stale_artifact_count": stale_artifact_count,
        "current_package_from_canonical_source": artifact_stale.get(
            "current_package_from_canonical_source"
        ),
        "quality_toil_count": _coerce_int(
            dict(maintainer_view.get("quality_toil") or {}).get("toil_count")
        ),
        "recommended_command": item.get("recommended_command")
        or ((item.get("commands") or {}).get("progress")),
        "authority": "observability_only",
    }


def _state_section(payload: Mapping[str, Any], *keys: str) -> dict[str, Any]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, Mapping):
            return dict(value)
        text = _non_empty_text(value)
        if text is not None:
            return {"summary": text}
    return {}


def _state_label(payload: Mapping[str, Any]) -> str | None:
    return _first_text(payload.get("summary"), payload.get("label"), payload.get("status"))


def _state_bool(payload: Mapping[str, Any], *keys: str) -> bool | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, bool):
            return value
    return None


def _route_back_count(route_back: Mapping[str, Any]) -> int:
    count = _coerce_int(route_back.get("count"))
    if count > 0:
        return count
    active = _state_bool(route_back, "active", "required")
    return 1 if active else 0


def _artifact_refresh_count(artifact_proof: Mapping[str, Any]) -> int:
    count = _coerce_int(
        artifact_proof.get("stale_artifact_count")
        or artifact_proof.get("refresh_pending_count")
        or artifact_proof.get("pending_count")
    )
    if count > 0:
        return count
    refresh_pending = _state_bool(artifact_proof, "refresh_pending", "stale", "pending")
    return 1 if refresh_pending else 0


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _non_empty_text(value)
        if text is not None:
            return text
    return None


def _coerce_int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


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
    auto_runtime_parked = dict(progress_payload.get("auto_runtime_parked") or {})
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
    ai_first_default_entry_state = dict(progress_payload.get("ai_first_default_entry_state") or {})
    ai_first_operations_dashboard = dict(progress_payload.get("ai_first_operations_dashboard") or {})
    ai_first_feedback_state = dict(progress_payload.get("ai_first_feedback_state") or {})
    paper_orchestra_operator_projection = dict(progress_payload.get("paper_orchestra_operator_projection") or {})
    recovery_contract = dict(progress_payload.get("recovery_contract") or {})
    study_truth_snapshot = _truth_snapshot_summary(progress_payload.get("study_truth_snapshot"))
    runtime_health_snapshot = _runtime_health_snapshot_summary(progress_payload.get("runtime_health_snapshot"))
    research_runtime_control_projection = dict(progress_payload.get("research_runtime_control_projection") or {})
    gate_surface = dict(research_runtime_control_projection.get("research_gate_surface") or {})
    if gate_surface.get("approval_gate_field") == "needs_user_decision":
        gate_surface.setdefault("legacy_approval_gate_field", "needs_physician_decision")
        research_runtime_control_projection["research_gate_surface"] = gate_surface
    return {
        "study_id": study_id,
        "truth_epoch": _non_empty_text(progress_payload.get("truth_epoch"))
        or _non_empty_text((study_truth_snapshot or {}).get("truth_epoch")),
        "study_truth_snapshot": study_truth_snapshot,
        "runtime_health_epoch": _non_empty_text(progress_payload.get("runtime_health_epoch"))
        or _non_empty_text((runtime_health_snapshot or {}).get("runtime_health_epoch")),
        "runtime_health_snapshot": runtime_health_snapshot,
        "current_stage": progress_payload.get("current_stage"),
        "current_stage_summary": progress_payload.get("current_stage_summary"),
        "current_blockers": list(progress_payload.get("current_blockers") or []),
        "next_system_action": progress_payload.get("next_system_action"),
        "intervention_lane": intervention_lane or None,
        "operator_verdict": operator_verdict or None,
        "operator_status_card": operator_status_card or None,
        "auto_runtime_parked": auto_runtime_parked or None,
        "parked_state": progress_payload.get("parked_state"),
        "parked_owner": progress_payload.get("parked_owner"),
        "resource_release_expected": progress_payload.get("resource_release_expected"),
        "awaiting_explicit_wakeup": progress_payload.get("awaiting_explicit_wakeup"),
        "auto_execution_complete": progress_payload.get("auto_execution_complete"),
        "reopen_policy": progress_payload.get("reopen_policy"),
        "legacy_current_stage": progress_payload.get("legacy_current_stage"),
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
        "ai_first_default_entry_state": ai_first_default_entry_state or None,
        "ai_first_operations_dashboard": ai_first_operations_dashboard or None,
        "ai_first_feedback_state": ai_first_feedback_state or None,
        "paper_orchestra_operator_projection": paper_orchestra_operator_projection or None,
        "research_runtime_control_projection": research_runtime_control_projection or None,
        "recovery_contract": recovery_contract or None,
        "needs_physician_decision": bool(progress_payload.get("needs_physician_decision")),
        "needs_user_decision": bool(progress_payload.get("needs_user_decision")),
        "monitoring": monitoring,
        "task_intake": task_intake or None,
        "progress_freshness": progress_freshness or None,
        "commands": commands,
    }


def _truth_snapshot_summary(value: object) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    keys = (
        "truth_epoch",
        "authority_epoch",
        "canonical_next_action",
        "blocking_reasons",
        "dominant_authority_refs",
        "allowed_controller_actions",
        "package_state",
        "writer_epoch",
        "source_signature",
    )
    summary = {key: value[key] for key in keys if key in value}
    return summary or None


def _runtime_health_snapshot_summary(value: object) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    keys = (
        "runtime_health_epoch",
        "canonical_runtime_action",
        "attempt_state",
        "retry_budget_remaining",
        "worker_liveness_state",
        "supervisor_state",
        "dominant_runtime_refs",
        "blocking_reasons",
        "allowed_controller_actions",
        "source_signature",
    )
    summary = {key: value[key] for key in keys if key in value}
    return summary or None


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
    ai_first_operations_state = _workspace_ai_first_operations_state(studies=studies)
    paper_orchestra_operator_projection = build_workspace_paper_orchestra_operator_projection(studies=studies)
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
        "ai_first_operations_state": ai_first_operations_state,
        "paper_orchestra_operator_projection": paper_orchestra_operator_projection,
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
                f"自动停驻 {study_counts.get('auto_runtime_parked', 0)}；"
                f"进度陈旧 {study_counts.get('progress_stale', 0)}；"
                f"进度缺失 {study_counts.get('progress_missing', 0)}；"
                f"等待用户判断 {study_counts.get('needs_user_decision', 0)}"
            )
    else:
        lines.append("- 当前还没有 workspace 级监管汇总。")
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
            f"重复返工 {counts.get('repeat_toil_count', 0)}"
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
    lines.extend(render_paper_orchestra_operator_projection_lines(payload.get("paper_orchestra_operator_projection") or {}))
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
