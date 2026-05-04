from __future__ import annotations

from collections.abc import Mapping

from med_autoscience.controllers import medical_paper_readiness, open_auto_research_projection

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
        "action_lifecycle_count": 0,
        "action_open": 0,
        "action_accepted": 0,
        "action_in_progress": 0,
        "action_blocked": 0,
        "action_closed": 0,
        "action_active": 0,
        "quality_learning_open_priority_count": 0,
        "quality_learning_system_improvement_count": 0,
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
        lifecycle_counts = dict(projection.get("action_lifecycle_counts") or {})
        if lifecycle_counts:
            counts["action_lifecycle_count"] += 1
            counts["action_open"] += _coerce_int(lifecycle_counts.get("open"))
            counts["action_accepted"] += _coerce_int(lifecycle_counts.get("accepted"))
            counts["action_in_progress"] += _coerce_int(lifecycle_counts.get("in_progress"))
            counts["action_blocked"] += _coerce_int(lifecycle_counts.get("blocked"))
            counts["action_closed"] += _coerce_int(lifecycle_counts.get("closed"))
            counts["action_active"] += _coerce_int(lifecycle_counts.get("active"))
        report_counts = dict(projection.get("quality_learning_operations_report_counts") or {})
        counts["quality_learning_open_priority_count"] += _coerce_int(
            report_counts.get("open_feedback_priority_count")
        )
        counts["quality_learning_system_improvement_count"] += _coerce_int(
            report_counts.get("system_improvement_priority_count")
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
            f"{counts['open_feedback_count']} 个运行反馈信号打开；"
            f"{counts['action_active']} 个 operator action 未闭合。"
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


def _workspace_ai_first_cross_study_completion_projection(
    *,
    study_roots: list[Path],
    studies: list[dict[str, Any]],
) -> dict[str, Any]:
    progress_snapshots = {
        str(item.get("study_id") or "").strip(): dict(item)
        for item in studies
        if str(item.get("study_id") or "").strip()
    }
    return ai_first_cross_study_completion.build_ai_first_cross_study_completion_projection(
        study_roots=study_roots,
        progress_snapshots=progress_snapshots,
        use_study_root_artifact_fallbacks=False,
    )


def _ai_first_operations_study_projection(item: Mapping[str, Any]) -> dict[str, Any] | None:
    feedback_state = dict(item.get("ai_first_feedback_state") or {})
    action_lifecycle = dict(item.get("ai_first_action_dispatch_lifecycle") or {})
    default_state = dict(item.get("ai_first_default_entry_state") or {})
    if default_state:
        return _attach_action_lifecycle_projection(
            _attach_feedback_projection(
                _ai_first_default_entry_state_projection(item=item, default_state=default_state),
                feedback_state=feedback_state,
            ),
            action_lifecycle=action_lifecycle,
        )
    dashboard = dict(item.get("ai_first_operations_dashboard") or {})
    if dashboard:
        return _attach_action_lifecycle_projection(
            _attach_feedback_projection(
                _legacy_ai_first_dashboard_projection(item=item, dashboard=dashboard),
                feedback_state=feedback_state,
            ),
            action_lifecycle=action_lifecycle,
        )
    if feedback_state:
        return _attach_action_lifecycle_projection(
            _attach_feedback_projection(
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
            ),
            action_lifecycle=action_lifecycle,
        )
    if action_lifecycle:
        return _attach_action_lifecycle_projection(
            {
                "study_id": item.get("study_id"),
                "read_model": "ai_first_action_dispatch_lifecycle_read_model",
                "source_surface": "ai_first_action_dispatch_lifecycle",
                "current_stage": item.get("current_stage"),
                "blockers": [],
                "authority": "operations_governance_only",
            },
            action_lifecycle=action_lifecycle,
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
    maintainer_view = dict(feedback_state.get("maintainer_view") or {})
    quality_learning_report = dict(
        feedback_state.get("quality_learning_operations_report")
        or maintainer_view.get("quality_learning_operations_report")
        or {}
    )
    open_priorities = [
        dict(item)
        for item in quality_learning_report.get("open_feedback_priorities") or []
        if isinstance(item, Mapping)
    ]
    system_improvements = [
        dict(item)
        for item in quality_learning_report.get("system_improvement_priorities") or []
        if isinstance(item, Mapping)
    ]
    updated = dict(projection)
    updated["feedback_status"] = feedback_state.get("status")
    updated["feedback_summary"] = feedback_state.get("summary")
    updated["feedback_primary_category"] = primary.get("category")
    updated["feedback_primary_reason"] = user_view.get("primary_feedback_reason")
    updated["feedback_action_id"] = primary_action.get("action_id")
    updated["feedback_action_target_surface"] = primary_action.get("target_surface")
    updated["feedback_action_summary"] = primary_action.get("summary") or user_view.get("next_action")
    updated["feedback_counts"] = counts
    if quality_learning_report:
        updated["quality_learning_operations_report_summary"] = quality_learning_report.get("summary")
        updated["quality_learning_operations_report_counts"] = quality_learning_report.get("counts")
        updated["quality_learning_top_open_priority"] = open_priorities[0] if open_priorities else None
        updated["quality_learning_top_system_improvement"] = system_improvements[0] if system_improvements else None
    updated["human_review_required"] = bool(
        updated.get("human_review_required") or user_view.get("human_review_required")
    )
    updated["next_step"] = updated.get("next_step") or user_view.get("next_step")
    return updated


def _attach_action_lifecycle_projection(
    projection: dict[str, Any],
    *,
    action_lifecycle: Mapping[str, Any],
) -> dict[str, Any]:
    if not action_lifecycle:
        return projection
    counts = dict(action_lifecycle.get("counts") or {})
    primary = dict(action_lifecycle.get("primary_action") or {})
    user_view = dict(action_lifecycle.get("user_view") or {})
    updated = dict(projection)
    updated["action_lifecycle_status"] = action_lifecycle.get("status")
    updated["action_lifecycle_counts"] = counts
    updated["action_primary_status"] = primary.get("status") or user_view.get("primary_action_status")
    updated["action_primary_summary"] = primary.get("summary") or user_view.get("next_step")
    updated["action_primary_id"] = primary.get("action_id")
    updated["action_target_surface"] = primary.get("target_surface")
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
    blockers = _normalized_strings(default_state.get("blockers") or default_state.get("attention") or [])
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
