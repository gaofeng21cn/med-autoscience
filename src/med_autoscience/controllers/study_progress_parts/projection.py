from __future__ import annotations

from med_autoscience.controllers import (
    ai_first_feedback,
    ai_first_observability,
    autonomy_ai_doctor,
    control_plane_facts,
    runtime_health_kernel,
    study_truth_kernel,
)

from .medical_writing_surfaces import medical_writing_quality_surface_status
from .parked_projection import (
    build_progress_parked_projection,
    parked_progress_fields,
    parked_text_override,
    projected_current_stage,
)
from .markdown_projection import render_study_progress_markdown
from .task_intake_override import task_intake_override_superseded_by_gate_specificity
from . import ai_first_default_entry as _ai_first_default_entry, operator_view as _operator_view, progress_freshness as _progress_freshness_parts, publication_runtime as _publication_runtime
from . import progression as _progression, runtime_efficiency as _runtime_efficiency, shared as _shared

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

for _module in (
    _shared,
    _publication_runtime,
    _progression,
    _progress_freshness_parts,
    _operator_view,
    _runtime_efficiency,
    _ai_first_default_entry,
):
    _module_reexport(_module)


def _supervision_active_run_id(
    *,
    status: dict[str, Any],
    execution_owner_guard: dict[str, Any],
    autonomous_runtime_notice: dict[str, Any],
    continuation_state: dict[str, Any],
) -> str | None:
    return control_plane_facts.active_run_id(
        {
            **dict(status or {}),
            "execution_owner_guard": dict(execution_owner_guard or {}),
            "autonomous_runtime_notice": dict(autonomous_runtime_notice or {}),
            "continuation_state": dict(continuation_state or {}),
        }
    )


def _attach_existing_autonomy_slo_projection(
    payload: dict[str, Any],
    *,
    study_root: Path,
) -> dict[str, Any]:
    autonomy_slo_status = autonomy_ai_doctor.read_latest_slo_status(study_root=study_root)
    if autonomy_slo_status is None:
        return payload
    updated = dict(payload)
    updated["autonomy_slo"] = autonomy_slo_status
    updated["ai_doctor_state"] = (
        _mapping_copy(autonomy_slo_status.get("ai_doctor_request"))
        or {
            "state": autonomy_slo_status.get("ai_doctor_state") or "not_observed",
            "request_required": bool(autonomy_slo_status.get("ai_doctor_request_required")),
        }
    )
    repair_recommendation = _mapping_copy(autonomy_slo_status.get("repair_recommendation"))
    updated["repair_recommendation"] = repair_recommendation or None
    updated["last_meaningful_progress_at"] = _non_empty_text(
        autonomy_slo_status.get("last_meaningful_progress_at")
    )
    refs = _mapping_copy(updated.get("refs"))
    refs["autonomy_slo_status_path"] = str(
        autonomy_ai_doctor.stable_slo_status_path(study_root=study_root)
    )
    updated["refs"] = refs
    return updated


def _autonomy_slo_observer_status(
    *,
    study_root: Path,
    state: str,
    observer_status: str,
    error: object | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "surface": "autonomy_progress_slo_status",
        "schema_version": 1,
        "study_id": study_root.name,
        "state": state,
        "observer_status": observer_status,
        "breach_types": [],
        "ai_doctor_request_required": False,
        "ai_doctor_state": "not_required",
        "quality_gate_relaxation_allowed": False,
        "status_path": str(autonomy_ai_doctor.stable_slo_status_path(study_root=study_root)),
    }
    if error is not None:
        payload["observer_error"] = str(error)
    return payload


def _read_or_materialize_autonomy_slo_status(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
) -> dict[str, Any] | None:
    autonomy_slo_status = autonomy_ai_doctor.read_latest_slo_status(study_root=study_root)
    if autonomy_slo_status is not None:
        return autonomy_slo_status
    try:
        from med_autoscience.controllers import study_cycle_profiler

        profile_payload = study_cycle_profiler.profile_study_cycle(
            profile=profile,
            study_id=None,
            study_root=study_root,
        )
    except (OSError, json.JSONDecodeError, TypeError, ValueError, RuntimeError) as exc:
        return _autonomy_slo_observer_status(
            study_root=study_root,
            state="observer_failed",
            observer_status="failed",
            error=exc,
        )
    profile_slo_status = _mapping_copy(profile_payload.get("autonomy_progress_slo_status"))
    if profile_slo_status:
        return profile_slo_status
    autonomy_slo_status = autonomy_ai_doctor.read_latest_slo_status(study_root=study_root)
    if autonomy_slo_status is not None:
        return autonomy_slo_status
    return _autonomy_slo_observer_status(
        study_root=study_root,
        state="observer_not_materialized",
        observer_status="not_materialized",
    )


def build_study_progress_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    status_payload: dict[str, Any] | Any,
    profile_ref: str | Path | None = None,
    entry_mode: str | None = None,
) -> dict[str, Any]:
    del entry_mode
    status = _status_payload(status_payload)
    existing_projection = status.get("progress_projection")
    if isinstance(existing_projection, dict) and _non_empty_text(existing_projection.get("study_id")) == study_id:
        normalized_existing = _normalize_study_progress_payload(
            {
                **existing_projection,
                "publication_supervisor_state": _mapping_copy(status.get("publication_supervisor_state")),
            }
        )
        normalized_existing.pop("publication_supervisor_state", None)
        return _attach_existing_autonomy_slo_projection(
            normalized_existing,
            study_root=study_root,
        )

    resolved_study_id = study_id
    resolved_study_root = study_root
    quest_id = _non_empty_text(status.get("quest_id"))
    quest_root = _candidate_path(status.get("quest_root"))
    launch_report_path = (
        _candidate_path(status.get("launch_report_path"))
        or resolved_study_root / "artifacts" / "runtime" / "last_launch_report.json"
    )
    publication_eval_path = resolved_study_root / "artifacts" / "publication_eval" / "latest.json"
    controller_decision_path = resolved_study_root / "artifacts" / "controller_decisions" / "latest.json"
    runtime_escalation_path = _candidate_path(((status.get("runtime_escalation_ref") or {}).get("artifact_path")))
    if runtime_escalation_path is None and quest_root is not None:
        runtime_escalation_path = (
            quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
        )
    runtime_watch_path = _latest_runtime_watch_report(quest_root)
    runtime_supervision_path = resolved_study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"
    gate_clearing_batch_path = resolved_study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
    bash_summary_path = quest_root / ".ds" / "bash_exec" / "summary.json" if quest_root is not None else None
    details_projection_path = quest_root / ".ds" / "projections" / "details.v1.json" if quest_root is not None else None

    launch_report_payload = _read_json_object(launch_report_path)
    controller_decision_payload = _read_json_object(controller_decision_path)
    gate_clearing_batch_payload = _read_json_object(gate_clearing_batch_path)
    if controller_decision_payload is not None:
        try:
            materialize_controller_confirmation_summary(
                study_root=resolved_study_root,
                decision_ref=controller_decision_path,
            )
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    controller_confirmation_summary_path = stable_controller_confirmation_summary_path(study_root=resolved_study_root)
    try:
        controller_confirmation_summary = (
            read_controller_confirmation_summary(
                study_root=resolved_study_root,
                ref=controller_confirmation_summary_path,
            )
            if controller_confirmation_summary_path.exists()
            else None
        )
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        controller_confirmation_summary = None
    runtime_supervision_payload = _read_json_object(runtime_supervision_path)
    runtime_health_snapshot = _mapping_copy(status.get("runtime_health_snapshot"))
    runtime_health_status = (
        _non_empty_text(runtime_health_snapshot.get("attempt_state"))
        or _non_empty_text((runtime_supervision_payload or {}).get("health_status"))
    )
    if runtime_escalation_path is not None and (
        status.get("runtime_escalation_ref") is not None or runtime_health_status in {"degraded", "escalated"}
    ):
        runtime_escalation_payload = _read_json_object(runtime_escalation_path)
    else:
        runtime_escalation_payload = None
    runtime_watch_payload = _read_json_object(runtime_watch_path) if runtime_watch_path is not None else None
    publication_eval_payload, _publishability_gate_path, _publishability_gate_payload = (
        _refresh_publication_surfaces_from_gate_report(
            study_root=resolved_study_root,
            study_id=resolved_study_id,
            quest_root=quest_root,
            quest_id=quest_id,
            publication_eval_path=publication_eval_path,
            runtime_escalation_path=runtime_escalation_path,
            runtime_watch_payload=runtime_watch_payload,
        )
    )
    bash_summary_payload = _read_json_object(bash_summary_path) if bash_summary_path is not None else None
    details_projection_wrapper = _read_json_object(details_projection_path) if details_projection_path is not None else None
    details_projection_payload = _details_projection_payload(details_projection_path)
    evaluation_summary_payload = _read_json_object(stable_evaluation_summary_path(study_root=resolved_study_root))
    study_truth_snapshot = _mapping_copy(status.get("study_truth_snapshot"))
    medical_writing_quality_surfaces = medical_writing_quality_surface_status(study_root=resolved_study_root)

    publication_supervisor_state = (
        dict(status.get("publication_supervisor_state") or {})
        if isinstance(status.get("publication_supervisor_state"), dict)
        else {}
    )
    autonomous_runtime_notice = (
        dict(status.get("autonomous_runtime_notice") or {})
        if isinstance(status.get("autonomous_runtime_notice"), dict)
        else {}
    )
    execution_owner_guard = (
        dict(status.get("execution_owner_guard") or {})
        if isinstance(status.get("execution_owner_guard"), dict)
        else {}
    )
    pending_user_interaction = (
        dict(status.get("pending_user_interaction") or {})
        if isinstance(status.get("pending_user_interaction"), dict)
        else {}
    )
    interaction_arbitration = (
        dict(status.get("interaction_arbitration") or {})
        if isinstance(status.get("interaction_arbitration"), dict)
        else {}
    )
    supervisor_tick_audit = (
        dict(status.get("supervisor_tick_audit") or {})
        if isinstance(status.get("supervisor_tick_audit"), dict)
        else {}
    )
    continuation_state = (
        dict(status.get("continuation_state") or {})
        if isinstance(status.get("continuation_state"), dict)
        else {}
    )
    family_checkpoint_lineage = (
        dict(status.get("family_checkpoint_lineage") or {})
        if isinstance(status.get("family_checkpoint_lineage"), dict)
        else {}
    )
    quest_root_for_manual_finish = _candidate_path(status.get("quest_root"))
    try:
        manual_finish = resolve_effective_study_manual_finish_contract(
            study_root=resolved_study_root,
            quest_root=quest_root_for_manual_finish,
        )
    except ValueError:
        manual_finish = None
    manual_finish_contract = (
        {
            "status": manual_finish.status.value,
            "summary": manual_finish.summary,
            "next_action_summary": manual_finish.next_action_summary,
            "compatibility_guard_only": manual_finish.compatibility_guard_only,
        }
        if manual_finish is not None
        else None
    )
    paper_contract_health = (
        dict((details_projection_payload or {}).get("paper_contract_health") or {})
        if isinstance((details_projection_payload or {}).get("paper_contract_health"), dict)
        else {}
    )
    paper_stage = (
        _non_empty_text(paper_contract_health.get("recommended_next_stage"))
        or _non_empty_text(publication_supervisor_state.get("supervisor_phase"))
    )
    latest_task_intake_payload = read_latest_task_intake(study_root=resolved_study_root)
    task_intake = summarize_task_intake(latest_task_intake_payload)
    manuscript_fast_lane_requested = task_intake_requests_manuscript_fast_lane(latest_task_intake_payload)
    task_intake_progress_override = (
        build_task_intake_progress_override(
            latest_task_intake_payload,
            study_root=resolved_study_root,
            publishability_gate_report=_publishability_gate_payload,
            evaluation_summary=evaluation_summary_payload,
        )
        if manual_finish_contract is None
        or manuscript_fast_lane_requested
        or latest_task_intake_payload is not None
        else None
    )
    if task_intake_override_superseded_by_gate_specificity(
        task_intake_progress_override=task_intake_progress_override,
        latest_task_intake_payload=latest_task_intake_payload,
        publication_eval_payload=publication_eval_payload,
    ):
        task_intake_progress_override = None
    latest_progress_message = None
    latest_session = ((bash_summary_payload or {}).get("latest_session"))
    if isinstance(latest_session, dict) and isinstance(latest_session.get("last_progress"), dict):
        latest_progress_message = _non_empty_text((latest_session.get("last_progress") or {}).get("message"))
    if latest_progress_message is None and isinstance(details_projection_wrapper, dict):
        latest_progress_message = _non_empty_text(
            (((details_projection_payload or {}).get("summary") or {}).get("status_line"))
        )

    needs_physician_decision = _needs_physician_decision(
        status=status,
        controller_confirmation_summary=controller_confirmation_summary,
        controller_decision_payload=controller_decision_payload,
        pending_user_interaction=pending_user_interaction,
        interaction_arbitration=interaction_arbitration,
    )
    if _manual_finish_active(manual_finish_contract):
        needs_physician_decision = False
    runtime_facts = control_plane_facts.resolve_control_plane_facts(
        status,
        supervisor_tick_audit=supervisor_tick_audit,
    )
    parked_status = dict(status)
    parked_status["runtime_liveness_status"] = runtime_facts.runtime_liveness_status
    parked_status["active_run_id"] = runtime_facts.active_run_id
    if runtime_facts.runtime_liveness_status == "parked" and runtime_facts.active_run_id is None:
        parked_status["reason"] = runtime_facts.reason or "completed_parked_auto_continue_no_new_message"
        parked_status.setdefault("decision", "blocked")
        parked_status.setdefault("quest_status", runtime_facts.quest_status or "active")
    auto_runtime_parked = build_progress_parked_projection(
        parked_status,
        needs_user_decision=needs_physician_decision,
        manual_finish_contract=manual_finish_contract,
        task_intake_progress_override=task_intake_progress_override,
    )
    current_stage = _current_stage(
        status=status,
        needs_physician_decision=needs_physician_decision,
        publication_supervisor_state=publication_supervisor_state,
        autonomous_runtime_notice=autonomous_runtime_notice,
        execution_owner_guard=execution_owner_guard,
        continuation_state=continuation_state,
        runtime_supervision_payload=runtime_supervision_payload,
        supervisor_tick_audit=supervisor_tick_audit,
        manual_finish_contract=manual_finish_contract,
        task_intake_progress_override=task_intake_progress_override,
    )
    current_stage = projected_current_stage(current_stage, auto_runtime_parked)
    base_progress_freshness = _progress_freshness(
        current_stage=current_stage,
        bash_summary_payload=bash_summary_payload,
        details_projection_payload=details_projection_payload,
        controller_decision_payload=controller_decision_payload,
        publication_eval_payload=publication_eval_payload,
        gate_clearing_batch_payload=gate_clearing_batch_payload,
        gate_clearing_batch_path=gate_clearing_batch_path,
    )
    autonomy_slo_status = _read_or_materialize_autonomy_slo_status(
        profile=profile,
        study_root=resolved_study_root,
    )
    progress_freshness = _split_progress_freshness(
        progress_freshness=base_progress_freshness,
        status=status,
        supervisor_tick_audit=supervisor_tick_audit,
        autonomy_slo_status=autonomy_slo_status,
        runtime_facts=runtime_facts,
        runtime_supervision_payload=runtime_supervision_payload,
    )
    current_stage_summary = _display_text(_stage_summary(
        status=status,
        current_stage=current_stage,
        publication_supervisor_state=publication_supervisor_state,
        publication_eval_payload=publication_eval_payload,
        latest_progress_message=latest_progress_message,
        runtime_supervision_payload=runtime_supervision_payload,
        supervisor_tick_audit=supervisor_tick_audit,
        manual_finish_contract=manual_finish_contract,
        task_intake_progress_override=task_intake_progress_override,
    )) or ""
    current_stage_summary = parked_text_override(
        current_stage_summary,
        auto_runtime_parked,
        "summary",
        display_text=_display_text,
    )
    if task_intake_progress_override:
        paper_stage = _non_empty_text(task_intake_progress_override.get("paper_stage")) or paper_stage
    paper_stage_summary = _display_text(_paper_stage_summary(
        paper_stage=paper_stage,
        publication_supervisor_state=publication_supervisor_state,
        publication_eval_payload=publication_eval_payload,
    )) or ""
    if task_intake_progress_override:
        paper_stage_summary = (
            _display_text(task_intake_progress_override.get("paper_stage_summary"))
            or _non_empty_text(task_intake_progress_override.get("paper_stage_summary"))
            or paper_stage_summary
        )
    current_blockers = _humanized_blockers(
        _current_blockers(
            status=status,
            publication_eval_payload=publication_eval_payload,
            runtime_watch_payload=runtime_watch_payload,
            runtime_escalation_payload=runtime_escalation_payload,
            controller_confirmation_summary=controller_confirmation_summary,
            controller_decision_payload=controller_decision_payload,
            pending_user_interaction=pending_user_interaction,
            interaction_arbitration=interaction_arbitration,
            runtime_supervision_payload=runtime_supervision_payload,
            supervisor_tick_audit=supervisor_tick_audit,
            progress_freshness=progress_freshness,
            manual_finish_contract=manual_finish_contract,
            task_intake_progress_override=task_intake_progress_override,
            evaluation_summary_payload=evaluation_summary_payload,
        )
    )
    next_system_action = _display_text(_next_system_action(
        needs_physician_decision=needs_physician_decision,
        controller_decision_payload=controller_decision_payload,
        publication_supervisor_state=publication_supervisor_state,
        publication_eval_payload=publication_eval_payload,
        runtime_watch_payload=runtime_watch_payload,
        current_blockers=current_blockers,
        execution_owner_guard=execution_owner_guard,
        status=status,
        autonomous_runtime_notice=autonomous_runtime_notice,
        continuation_state=continuation_state,
        runtime_supervision_payload=runtime_supervision_payload,
        supervisor_tick_audit=supervisor_tick_audit,
        manual_finish_contract=manual_finish_contract,
        task_intake_progress_override=task_intake_progress_override,
        evaluation_summary_payload=evaluation_summary_payload,
    )) or ""
    next_system_action = parked_text_override(
        next_system_action,
        auto_runtime_parked,
        "next_action_summary",
        display_text=_display_text,
    )
    physician_decision_summary = _display_text(_physician_decision_summary(
        status=status,
        controller_confirmation_summary=controller_confirmation_summary,
        controller_decision_payload=controller_decision_payload,
        pending_user_interaction=pending_user_interaction,
        interaction_arbitration=interaction_arbitration,
    )) if needs_physician_decision else None
    intervention_lane = _intervention_lane(
        current_stage=current_stage,
        current_stage_summary=current_stage_summary,
        current_blockers=current_blockers,
        next_system_action=next_system_action,
        needs_physician_decision=needs_physician_decision,
        progress_freshness=progress_freshness,
        publication_eval_payload=publication_eval_payload,
        runtime_watch_payload=runtime_watch_payload,
        status=status,
        autonomous_runtime_notice=autonomous_runtime_notice,
        execution_owner_guard=execution_owner_guard,
        continuation_state=continuation_state,
        runtime_supervision_payload=runtime_supervision_payload,
        supervisor_tick_audit=supervisor_tick_audit,
        manual_finish_contract=manual_finish_contract,
        task_intake_progress_override=task_intake_progress_override,
        evaluation_summary_payload=evaluation_summary_payload,
        auto_runtime_parked=auto_runtime_parked,
    )
    recommended_command, recommended_commands, recovery_contract = _recovery_contract(
        profile=profile,
        study_id=resolved_study_id,
        profile_ref=profile_ref,
        intervention_lane=intervention_lane,
        current_stage_summary=current_stage_summary,
        next_system_action=next_system_action,
        current_blockers=current_blockers,
    )
    autonomy_contract = _autonomy_contract(
        study_id=resolved_study_id,
        intervention_lane=intervention_lane,
        recovery_contract=recovery_contract,
        recommended_command=recommended_command,
        current_stage_summary=current_stage_summary,
        next_system_action=next_system_action,
        continuation_state=continuation_state,
        family_checkpoint_lineage=family_checkpoint_lineage,
        runtime_watch_payload=runtime_watch_payload,
        needs_physician_decision=needs_physician_decision,
        manual_finish_contract=manual_finish_contract,
        auto_runtime_parked=auto_runtime_parked,
    )
    operator_verdict = _operator_verdict(
        study_id=resolved_study_id,
        intervention_lane=intervention_lane,
        recovery_contract=recovery_contract,
        recommended_command=recommended_command,
        current_stage_summary=current_stage_summary,
        next_system_action=next_system_action,
        current_blockers=current_blockers,
    )
    latest_events = _latest_events(
        launch_report_payload=launch_report_payload,
        launch_report_path=launch_report_path,
        runtime_supervision_payload=runtime_supervision_payload,
        runtime_supervision_path=runtime_supervision_path if runtime_supervision_payload is not None else None,
        runtime_escalation_payload=runtime_escalation_payload,
        runtime_escalation_path=runtime_escalation_path,
        publication_eval_payload=publication_eval_payload,
        publication_eval_path=publication_eval_path,
        controller_decision_payload=controller_decision_payload,
        controller_decision_path=controller_decision_path,
        runtime_watch_payload=runtime_watch_payload,
        runtime_watch_path=runtime_watch_path,
        details_projection_payload=details_projection_payload,
        details_projection_path=details_projection_path,
        bash_summary_payload=bash_summary_payload,
        bash_summary_path=bash_summary_path,
        publication_supervisor_state=publication_supervisor_state,
        task_intake_progress_override=task_intake_progress_override,
    )
    runtime_efficiency = _latest_run_telemetry_surface(
        quest_root=quest_root,
        status=status,
        study_root=resolved_study_root,
    )
    ai_doctor_state = (
        _mapping_copy((autonomy_slo_status or {}).get("ai_doctor_request"))
        or {
            "state": (autonomy_slo_status or {}).get("ai_doctor_state") or "not_observed",
            "request_required": bool((autonomy_slo_status or {}).get("ai_doctor_request_required")),
        }
    )
    repair_recommendation = _mapping_copy((autonomy_slo_status or {}).get("repair_recommendation"))
    operator_status_card = _operator_status_card(
        study_id=resolved_study_id,
        current_stage=current_stage,
        current_stage_summary=current_stage_summary,
        intervention_lane=intervention_lane,
        needs_physician_decision=needs_physician_decision,
        current_blockers=current_blockers,
        next_system_action=next_system_action,
        latest_events=latest_events,
        publication_eval_payload=publication_eval_payload,
        controller_confirmation_summary=controller_confirmation_summary,
        controller_decision_payload=controller_decision_payload,
        runtime_watch_payload=runtime_watch_payload,
        runtime_supervision_payload=runtime_supervision_payload,
        supervisor_tick_audit=supervisor_tick_audit,
        manual_finish_contract=manual_finish_contract,
        auto_runtime_parked=auto_runtime_parked,
        runtime_efficiency=runtime_efficiency,
    )
    status_narration_contract = build_status_narration_contract(
        contract_id=f"study-progress::{resolved_study_id}",
        surface_kind="study_progress",
        stage={
            "current_stage": current_stage,
            "paper_stage": paper_stage,
            "intervention_lane": str(intervention_lane.get("lane_id") or "").strip() or None,
        },
        readiness={
            "needs_physician_decision": needs_physician_decision,
            "progress_freshness": str(progress_freshness.get("status") or "").strip() or None,
        },
        current_blockers=current_blockers[:8],
        latest_update=latest_progress_message or current_stage_summary,
        next_step=next_system_action,
        facts={
            "study_id": resolved_study_id,
            "quest_id": quest_id,
            "paper_stage_summary": paper_stage_summary,
        },
        answer_checklist=PROGRESS_ANSWER_CHECKLIST,
    )
    generated_at = _utc_now()
    controller_module_surface = _controller_module_surface(study_root=resolved_study_root)
    evaluation_module_surface = _evaluation_module_surface(
        study_root=resolved_study_root,
        publication_eval_payload=publication_eval_payload,
        runtime_escalation_path=runtime_escalation_path,
        runtime_watch_payload=runtime_watch_payload,
        quest_root=quest_root,
    )
    runtime_module_surface = _runtime_module_surface(
        generated_at=generated_at,
        study_id=resolved_study_id,
        quest_id=quest_id,
        study_root=resolved_study_root,
        launch_report_path=launch_report_path,
        runtime_supervision_path=runtime_supervision_path,
        runtime_supervision_payload=runtime_supervision_payload,
        runtime_escalation_path=runtime_escalation_path,
        runtime_watch_path=runtime_watch_path,
        recovery_contract=recovery_contract,
        execution_owner_guard=execution_owner_guard,
        publication_supervisor_state=publication_supervisor_state,
        current_stage=current_stage,
        current_stage_summary=current_stage_summary,
        next_system_action=next_system_action,
        needs_physician_decision=needs_physician_decision,
        status=status,
        supervisor_tick_audit=supervisor_tick_audit,
        manual_finish_contract=manual_finish_contract,
        auto_runtime_parked=auto_runtime_parked,
    )
    module_surfaces: dict[str, Any] = {}
    if controller_module_surface is not None:
        module_surfaces["controller_charter"] = controller_module_surface
    module_surfaces["runtime"] = runtime_module_surface
    if evaluation_module_surface is not None:
        module_surfaces["eval_hygiene"] = evaluation_module_surface
    quality_closure_truth = (
        _mapping_copy(evaluation_module_surface.get("quality_closure_truth"))
        if evaluation_module_surface is not None
        else {}
    )
    quality_execution_lane = (
        _mapping_copy(evaluation_module_surface.get("quality_execution_lane"))
        if evaluation_module_surface is not None
        else {}
    )
    same_line_route_truth = (
        _mapping_copy(evaluation_module_surface.get("same_line_route_truth"))
        if evaluation_module_surface is not None
        else {}
    )
    same_line_route_surface = (
        _mapping_copy(evaluation_module_surface.get("same_line_route_surface"))
        if evaluation_module_surface is not None
        else {}
    )
    if task_intake_progress_override:
        quality_closure_truth = _mapping_copy(task_intake_progress_override.get("quality_closure_truth"))
        quality_execution_lane = _mapping_copy(task_intake_progress_override.get("quality_execution_lane"))
        same_line_route_truth = _mapping_copy(task_intake_progress_override.get("same_line_route_truth"))
        same_line_route_surface = _mapping_copy(task_intake_progress_override.get("same_line_route_surface"))
        eval_surface = _mapping_copy(module_surfaces.get("eval_hygiene"))
        if eval_surface:
            eval_surface["quality_closure_truth"] = quality_closure_truth or None
            eval_surface["quality_execution_lane"] = quality_execution_lane or None
            eval_surface["same_line_route_truth"] = same_line_route_truth or None
            eval_surface["same_line_route_surface"] = same_line_route_surface or None
            module_surfaces["eval_hygiene"] = eval_surface
    if _publication_supervisor_blocks_same_line_route(publication_supervisor_state):
        same_line_route_truth = {}
        same_line_route_surface = {}
        eval_surface = _mapping_copy(module_surfaces.get("eval_hygiene"))
        if eval_surface:
            eval_surface["same_line_route_truth"] = None
            eval_surface["same_line_route_surface"] = None
            module_surfaces["eval_hygiene"] = eval_surface
    quality_closure_basis = (
        _mapping_copy(evaluation_module_surface.get("quality_closure_basis"))
        if evaluation_module_surface is not None
        else {}
    )
    quality_review_agenda = (
        _mapping_copy(evaluation_module_surface.get("quality_review_agenda"))
        if evaluation_module_surface is not None
        else {}
    )
    quality_revision_plan = (
        _mapping_copy(evaluation_module_surface.get("quality_revision_plan"))
        if evaluation_module_surface is not None
        else {}
    )
    quality_review_loop = (
        _mapping_copy(evaluation_module_surface.get("quality_review_loop"))
        if evaluation_module_surface is not None
        else {}
    )
    study_commands = _study_command_surfaces(
        profile=profile,
        study_id=resolved_study_id,
        profile_ref=profile_ref,
    )
    gate_clearing_batch_followthrough = _gate_clearing_batch_followthrough(
        study_root=resolved_study_root,
        publication_eval_payload=publication_eval_payload,
    )
    quality_repair_batch_followthrough = _quality_repair_batch_followthrough(
        study_root=resolved_study_root,
        publication_eval_payload=publication_eval_payload,
        recommended_command=study_commands.get("quality_repair_batch"),
    )
    quality_review_followthrough = _quality_review_followthrough_projection(
        quality_review_loop=quality_review_loop,
        needs_physician_decision=needs_physician_decision,
        interaction_arbitration=interaction_arbitration,
        runtime_decision=_non_empty_text(status.get("decision")),
        quest_status=_non_empty_text(status.get("quest_status")),
        current_blockers=current_blockers,
        next_system_action=next_system_action,
    )
    operator_status_card = _apply_quality_review_followthrough_to_operator_status(
        operator_status_card=operator_status_card,
        followthrough=quality_review_followthrough,
    )
    autonomy_soak_status = _autonomy_soak_status(
        autonomy_contract=autonomy_contract,
        progress_freshness=progress_freshness,
        runtime_watch_path=runtime_watch_path,
        controller_decision_path=controller_decision_path,
    )
    if bool(auto_runtime_parked.get("parked")):
        supervision_health_status = "parked"
    elif runtime_facts.recovery_pending or runtime_facts.missing_live_session:
        supervision_health_status = "recovering"
    elif runtime_facts.strict_live:
        supervision_health_status = runtime_health_status or "live"
    else:
        supervision_health_status = runtime_health_status
    research_runtime_control_projection = _research_runtime_control_projection(
        study_commands=study_commands,
        autonomy_contract=autonomy_contract,
        operator_status_card=operator_status_card,
        continuation_state=continuation_state,
        family_checkpoint_lineage=family_checkpoint_lineage,
        intervention_lane=intervention_lane,
        needs_physician_decision=needs_physician_decision,
        evaluation_summary_ref=(
            evaluation_module_surface["summary_ref"] if evaluation_module_surface is not None else None
        ),
        publication_eval_ref=str(publication_eval_path),
        controller_decision_ref=str(controller_decision_path),
        runtime_supervision_ref=str(runtime_supervision_path) if runtime_supervision_payload is not None else None,
        runtime_watch_ref=str(runtime_watch_path) if runtime_watch_path is not None else None,
    )
    ai_first_observability_snapshots = ai_first_observability.build_ai_first_observability_snapshots_from_study_root(
        study_root=resolved_study_root,
    )
    ai_first_default_entry_state = _ai_first_default_entry.build_ai_first_default_entry_state(
        study_root=resolved_study_root,
    )
    paper_orchestra_operator_projection = _mapping_copy(
        ai_first_default_entry_state.get("paper_orchestra_operator_projection")
    )
    ai_first_operations_dashboard = ai_first_observability.build_ai_first_operations_dashboard_summary(
        drift_audit={"status": "not_run", "summary": {"fail_count": 0}},
        progress_snapshot={
            "current_stage": current_stage,
            "current_blockers": current_blockers,
            "next_system_action": next_system_action,
            "human_review_required": needs_physician_decision
            or bool(ai_first_default_entry_state.get("human_review_required")),
            "autonomy_contract": autonomy_contract,
            "ai_first_default_entry_state": ai_first_default_entry_state,
        },
        runtime_snapshot=ai_first_observability_snapshots["runtime_snapshot"],
        quality_snapshot=ai_first_observability_snapshots["quality_snapshot"],
        artifact_snapshot=ai_first_observability_snapshots["artifact_snapshot"],
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "truth_epoch": _non_empty_text(study_truth_snapshot.get("truth_epoch")),
        "runtime_health_epoch": _non_empty_text(runtime_health_snapshot.get("runtime_health_epoch")),
        "study_id": resolved_study_id,
        "study_root": str(resolved_study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root) if quest_root is not None else None,
        "current_stage": current_stage,
        "current_stage_summary": current_stage_summary,
        "paper_stage": paper_stage,
        "paper_stage_summary": paper_stage_summary,
        "status_narration_contract": status_narration_contract,
        "latest_events": latest_events,
        "current_blockers": current_blockers,
        "next_system_action": next_system_action,
        **parked_progress_fields(auto_runtime_parked),
        "intervention_lane": intervention_lane,
        "operator_verdict": operator_verdict,
        "operator_status_card": operator_status_card,
        "recommended_command": recommended_command,
        "recommended_commands": recommended_commands,
        "autonomy_contract": autonomy_contract,
        "autonomy_soak_status": autonomy_soak_status,
        "recovery_contract": recovery_contract,
        "needs_physician_decision": needs_physician_decision,
        "needs_user_decision": needs_physician_decision,
        "physician_decision_summary": physician_decision_summary,
        "user_decision_summary": physician_decision_summary,
        "runtime_decision": _non_empty_text(status.get("decision")),
        "runtime_reason": _non_empty_text(status.get("reason")),
        "continuation_state": continuation_state or None,
        "family_checkpoint_lineage": family_checkpoint_lineage or None,
        "interaction_arbitration": interaction_arbitration or None,
        "manual_finish_contract": manual_finish_contract,
        "task_intake": task_intake,
        "progress_freshness": progress_freshness,
        "quality_closure_truth": quality_closure_truth or None,
        "quality_execution_lane": quality_execution_lane or None,
        "same_line_route_truth": same_line_route_truth or None,
        "same_line_route_surface": same_line_route_surface or None,
        "quality_closure_basis": quality_closure_basis or None,
        "quality_review_agenda": quality_review_agenda or None,
        "quality_revision_plan": quality_revision_plan or None,
        "quality_review_loop": quality_review_loop or None,
        "quality_repair_batch_followthrough": quality_repair_batch_followthrough or None,
        "gate_clearing_batch_followthrough": gate_clearing_batch_followthrough or None,
        "quality_review_followthrough": quality_review_followthrough or None,
        "medical_writing_quality_surfaces": medical_writing_quality_surfaces,
        "research_runtime_control_projection": research_runtime_control_projection,
        "ai_first_default_entry_state": ai_first_default_entry_state,
        "paper_orchestra_operator_projection": paper_orchestra_operator_projection or None,
        "ai_first_observability_snapshots": ai_first_observability_snapshots,
        "ai_first_operations_dashboard": ai_first_operations_dashboard,
        "study_truth_snapshot": study_truth_snapshot or None,
        "runtime_health_snapshot": runtime_health_snapshot or None,
        "module_surfaces": module_surfaces,
        "runtime_efficiency": runtime_efficiency,
        "autonomy_slo": autonomy_slo_status,
        "ai_doctor_state": ai_doctor_state,
        "repair_recommendation": repair_recommendation or None,
        "last_meaningful_progress_at": (
            _non_empty_text((autonomy_slo_status or {}).get("last_meaningful_progress_at"))
            if autonomy_slo_status is not None
            else None
        ),
        "supervision": {
            "browser_url": _non_empty_text(autonomous_runtime_notice.get("browser_url")),
            "quest_session_api_url": _non_empty_text(autonomous_runtime_notice.get("quest_session_api_url")),
            "active_run_id": _supervision_active_run_id(
                status=status,
                execution_owner_guard=execution_owner_guard,
                autonomous_runtime_notice=autonomous_runtime_notice,
                continuation_state=continuation_state,
            ),
            "health_status": supervision_health_status,
            "supervisor_tick_status": _non_empty_text(supervisor_tick_audit.get("status")),
            "supervisor_tick_required": bool(supervisor_tick_audit.get("required")),
            "supervisor_tick_summary": _non_empty_text(supervisor_tick_audit.get("summary")),
            "supervisor_tick_latest_recorded_at": _non_empty_text(supervisor_tick_audit.get("latest_recorded_at")),
            "launch_report_path": str(launch_report_path),
        },
        "refs": {
            "launch_report_path": str(launch_report_path),
            "publication_eval_path": str(publication_eval_path),
            "controller_decision_path": str(controller_decision_path),
            "controller_confirmation_summary_path": (
                str(controller_confirmation_summary_path) if controller_confirmation_summary is not None else None
            ),
            "controller_summary_path": (
                controller_module_surface["summary_ref"] if controller_module_surface is not None else None
            ),
            "runtime_supervision_path": str(runtime_supervision_path) if runtime_supervision_payload is not None else None,
            "runtime_escalation_path": str(runtime_escalation_path) if runtime_escalation_path is not None else None,
            "runtime_watch_report_path": str(runtime_watch_path) if runtime_watch_path is not None else None,
            "runtime_status_summary_path": runtime_module_surface["summary_ref"],
            **_runtime_efficiency_refs(runtime_efficiency),
            "autonomy_slo_status_path": (
                str(autonomy_ai_doctor.stable_slo_status_path(study_root=resolved_study_root))
                if autonomy_slo_status is not None
                else None
            ),
            "evaluation_summary_path": (
                evaluation_module_surface["summary_ref"] if evaluation_module_surface is not None else None
            ),
            "medical_manuscript_blueprint_path": medical_writing_quality_surfaces["blueprint"]["path"],
            "medical_journal_style_corpus_path": medical_writing_quality_surfaces["style_corpus"]["path"],
            "medical_prose_review_request_path": medical_writing_quality_surfaces["prose_review_request"]["path"],
            "medical_prose_review_path": medical_writing_quality_surfaces["prose_review"]["path"],
            "retrospective_medical_prose_audit_request_path": (
                medical_writing_quality_surfaces["retrospective_audit_request"]["path"]
            ),
            "retrospective_medical_prose_audit_path": medical_writing_quality_surfaces["retrospective_audit"]["path"],
            "study_truth_snapshot_path": str(study_truth_kernel.truth_snapshot_path(study_root=resolved_study_root)),
            "runtime_health_snapshot_path": str(
                runtime_health_kernel.runtime_health_snapshot_path(study_root=resolved_study_root)
            ),
            "promotion_gate_path": (
                evaluation_module_surface["promotion_gate_ref"] if evaluation_module_surface is not None else None
            ),
            "bash_summary_path": str(bash_summary_path) if bash_summary_path is not None else None,
            "details_projection_path": str(details_projection_path) if details_projection_path is not None else None,
            "ai_first_observability_publication_eval_path": ai_first_observability_snapshots["refs"][
                "publication_eval_path"
            ],
            "ai_first_observability_runtime_health_path": ai_first_observability_snapshots["refs"][
                "runtime_health_path"
            ],
            "ai_first_observability_delivery_manifest_path": ai_first_observability_snapshots["refs"][
                "delivery_manifest_path"
            ],
        },
    }
    ai_first_feedback_state = ai_first_feedback.materialize_ai_first_feedback_state(
        study_root=resolved_study_root,
        progress_snapshot=payload,
        observed_at=generated_at,
    )
    payload["ai_first_feedback_state"] = ai_first_feedback_state
    payload["refs"]["ai_first_feedback_ledger_path"] = ai_first_feedback_state["ledger"]["path"]
    return payload


def read_study_progress(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: Path | None = None,
    entry_mode: str | None = None,
    sync_runtime_summary: bool = True,
) -> dict[str, Any]:
    resolved_study_id, resolved_study_root, _study_payload = _resolve_study(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    status = study_runtime_router.study_runtime_status(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        entry_mode=entry_mode,
        sync_runtime_summary=sync_runtime_summary,
        include_progress_projection=False,
    )
    return build_study_progress_projection(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        status_payload=status,
        profile_ref=profile_ref,
        entry_mode=entry_mode,
    )


__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
