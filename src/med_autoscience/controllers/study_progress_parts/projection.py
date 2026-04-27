from __future__ import annotations

from . import shared as _shared
from . import publication_runtime as _publication_runtime
from . import progression as _progression
from . import operator_view as _operator_view

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_publication_runtime)
_module_reexport(_progression)
_module_reexport(_operator_view)

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
        return normalized_existing

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
    bash_summary_path = quest_root / ".ds" / "bash_exec" / "summary.json" if quest_root is not None else None
    details_projection_path = quest_root / ".ds" / "projections" / "details.v1.json" if quest_root is not None else None

    launch_report_payload = _read_json_object(launch_report_path)
    controller_decision_payload = _read_json_object(controller_decision_path)
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
    runtime_health_status = _non_empty_text((runtime_supervision_payload or {}).get("health_status"))
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
    task_intake_progress_override = (
        build_task_intake_progress_override(
            latest_task_intake_payload,
            study_root=resolved_study_root,
            publishability_gate_report=_publishability_gate_payload,
            evaluation_summary=evaluation_summary_payload,
        )
        if manual_finish_contract is None
        else None
    )
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
    progress_freshness = _progress_freshness(
        current_stage=current_stage,
        bash_summary_payload=bash_summary_payload,
        details_projection_payload=details_projection_payload,
        controller_decision_payload=controller_decision_payload,
        publication_eval_payload=publication_eval_payload,
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
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
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
        "intervention_lane": intervention_lane,
        "operator_verdict": operator_verdict,
        "operator_status_card": operator_status_card,
        "recommended_command": recommended_command,
        "recommended_commands": recommended_commands,
        "autonomy_contract": autonomy_contract,
        "autonomy_soak_status": autonomy_soak_status,
        "recovery_contract": recovery_contract,
        "needs_physician_decision": needs_physician_decision,
        "physician_decision_summary": physician_decision_summary,
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
        "research_runtime_control_projection": research_runtime_control_projection,
        "module_surfaces": module_surfaces,
        "supervision": {
            "browser_url": _non_empty_text(autonomous_runtime_notice.get("browser_url")),
            "quest_session_api_url": _non_empty_text(autonomous_runtime_notice.get("quest_session_api_url")),
            "active_run_id": _non_empty_text(execution_owner_guard.get("active_run_id"))
            or _non_empty_text(autonomous_runtime_notice.get("active_run_id")),
            "health_status": runtime_health_status,
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
            "evaluation_summary_path": (
                evaluation_module_surface["summary_ref"] if evaluation_module_surface is not None else None
            ),
            "promotion_gate_path": (
                evaluation_module_surface["promotion_gate_ref"] if evaluation_module_surface is not None else None
            ),
            "bash_summary_path": str(bash_summary_path) if bash_summary_path is not None else None,
            "details_projection_path": str(details_projection_path) if details_projection_path is not None else None,
        },
    }
    return payload


def read_study_progress(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: Path | None = None,
    entry_mode: str | None = None,
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


def render_study_progress_markdown(payload: dict[str, Any]) -> str:
    latest_events = [dict(item) for item in (payload.get("latest_events") or []) if isinstance(item, dict)]
    blockers: list[str] = []
    for item in payload.get("current_blockers") or []:
        if not str(item).strip():
            continue
        label = _blocker_label(item) or str(item)
        if label not in blockers:
            blockers.append(label)
    continuation_state = dict(payload.get("continuation_state") or {})
    manual_finish_contract = (
        dict(payload.get("manual_finish_contract") or {})
        if isinstance(payload.get("manual_finish_contract"), dict)
        else None
    )
    if _manual_finish_active(manual_finish_contract):
        runtime_decision = _manual_finish_runtime_decision_summary(manual_finish_contract)
        runtime_reason = _manual_finish_runtime_reason_summary(manual_finish_contract)
        continuation_reason = ""
    else:
        runtime_decision = _runtime_decision_label(payload.get("runtime_decision")) or "未知"
        runtime_reason = _reason_label(payload.get("runtime_reason")) or _display_text(payload.get("runtime_reason")) or ""
        continuation_reason = (
            _continuation_reason_label(continuation_state.get("continuation_reason"))
            or str(continuation_state.get("continuation_reason") or "").strip()
        )
    runtime_health = _runtime_health_label(((payload.get("supervision") or {}).get("health_status"))) or "未知"
    supervisor_tick_status = _supervisor_tick_status_label(((payload.get("supervision") or {}).get("supervisor_tick_status"))) or ""
    progress_freshness = dict(payload.get("progress_freshness") or {})
    task_intake = dict(payload.get("task_intake") or {})
    status_human_view = _status_narration_human_view(payload)
    has_status_contract = isinstance(payload.get("status_narration_contract"), Mapping)
    current_stage = _non_empty_text(status_human_view.get("current_stage_label")) or _current_stage_label(
        payload.get("current_stage")
    ) or "未知"
    if has_status_contract:
        current_judgment = _non_empty_text(status_human_view.get("status_summary")) or _non_empty_text(
            status_human_view.get("latest_update")
        )
    else:
        current_judgment = _non_empty_text(status_human_view.get("latest_update")) or _non_empty_text(
            status_human_view.get("status_summary")
        )
    if not current_judgment:
        current_judgment = _display_text(payload.get("current_stage_summary")) or str(
            payload.get("current_stage_summary") or ""
        ).strip()
    next_step_summary = _non_empty_text(status_human_view.get("next_step")) or str(
        payload.get("next_system_action") or ""
    ).strip()
    normalized_payload = _normalize_study_progress_payload(payload)
    paper_stage = _paper_stage_label(normalized_payload.get("paper_stage")) or "未知"
    intervention_lane = _mapping_copy(normalized_payload.get("intervention_lane"))
    intervention_title = _non_empty_text(intervention_lane.get("title"))
    intervention_summary = _display_text(intervention_lane.get("summary")) or _non_empty_text(
        intervention_lane.get("summary")
    )
    intervention_severity = _INTERVENTION_SEVERITY_LABELS.get(
        _non_empty_text(intervention_lane.get("severity")) or "",
        "",
    )
    operator_status_card = _mapping_copy(normalized_payload.get("operator_status_card"))
    autonomy_contract = _mapping_copy(normalized_payload.get("autonomy_contract"))
    quality_closure_truth = _mapping_copy(normalized_payload.get("quality_closure_truth"))
    quality_execution_lane = _mapping_copy(normalized_payload.get("quality_execution_lane"))
    same_line_route_truth = _mapping_copy(normalized_payload.get("same_line_route_truth"))
    same_line_route_surface = _mapping_copy(normalized_payload.get("same_line_route_surface"))
    quality_closure_basis = _mapping_copy(normalized_payload.get("quality_closure_basis"))
    quality_review_agenda = _mapping_copy(normalized_payload.get("quality_review_agenda"))
    quality_revision_plan = _mapping_copy(normalized_payload.get("quality_revision_plan"))
    quality_review_loop = _mapping_copy(normalized_payload.get("quality_review_loop"))
    quality_repair_batch_followthrough = _mapping_copy(normalized_payload.get("quality_repair_batch_followthrough"))
    gate_clearing_batch_followthrough = _mapping_copy(normalized_payload.get("gate_clearing_batch_followthrough"))
    quality_review_followthrough = _mapping_copy(normalized_payload.get("quality_review_followthrough"))
    recovery_contract = _mapping_copy(normalized_payload.get("recovery_contract"))
    module_surfaces = _mapping_copy(normalized_payload.get("module_surfaces"))
    if bool(quality_review_followthrough.get("waiting_auto_re_review")):
        current_judgment = _non_empty_text(quality_review_followthrough.get("summary")) or current_judgment
        next_step_summary = (
            _non_empty_text(quality_review_followthrough.get("blocking_reason"))
            or _non_empty_text(quality_review_followthrough.get("next_confirmation_signal"))
            or next_step_summary
        )
    recovery_action_mode = _RECOVERY_ACTION_MODE_LABELS.get(
        _non_empty_text(recovery_contract.get("action_mode")) or "",
        "",
    )
    recovery_steps = [
        dict(item)
        for item in (normalized_payload.get("recommended_commands") or [])
        if isinstance(item, dict)
    ]
    lines = [
        "# 研究进度",
        "",
        f"- study_id: `{str(normalized_payload.get('study_id') or '')}`",
        f"- quest_id: `{str(normalized_payload.get('quest_id') or 'none')}`",
        f"- 当前阶段: {current_stage}",
    ]
    if current_judgment:
        lines.append(f"- 当前判断: {current_judgment}")
    if intervention_title or intervention_summary:
        label = intervention_title or "继续监督当前 study"
        if intervention_severity:
            label = f"{label}（{intervention_severity}）"
        lines.extend(
            [
                f"- 干预类型: {label}",
            ]
        )
        if intervention_summary:
            lines.append(f"- 干预摘要: {intervention_summary}")
    if task_intake:
        lines.extend(
            [
                "",
                "## 当前任务",
                "",
                f"- 任务意图: {task_intake.get('task_intent') or '未提供'}",
            ]
        )
        if task_intake.get("journal_target"):
            lines.append(f"- 目标期刊: {task_intake.get('journal_target')}")
        if task_intake.get("entry_mode"):
            lines.append(f"- 入口模式: {task_intake.get('entry_mode')}")
        if task_intake.get("emitted_at"):
            lines.append(f"- 任务写入时间: {task_intake.get('emitted_at')}")
        first_cycle_outputs = [str(item).strip() for item in task_intake.get("first_cycle_outputs") or [] if str(item).strip()]
        if first_cycle_outputs:
            lines.append(f"- 首轮输出要求: {', '.join(first_cycle_outputs)}")
    lines.extend(
        [
            "",
            "## 论文推进",
            "",
            f"- 论文阶段: {paper_stage}",
            f"- 论文摘要: {_display_text(normalized_payload.get('paper_stage_summary')) or str(normalized_payload.get('paper_stage_summary') or '').strip()}",
            "",
            "## 运行监管",
            "",
            f"- 运行健康: {runtime_health}",
            f"- MAS 决策: {runtime_decision}",
        ]
    )
    if supervisor_tick_status:
        lines.append(f"- MAS 监管心跳: {supervisor_tick_status}")
    progress_freshness_summary = _display_text(progress_freshness.get("summary")) or _non_empty_text(progress_freshness.get("summary"))
    if progress_freshness_summary:
        progress_status_label = _progress_freshness_status_label(progress_freshness.get("status"))
        if progress_status_label:
            lines.append(f"- 研究进度信号: {progress_status_label}；{progress_freshness_summary}")
        else:
            lines.append(f"- 研究进度信号: {progress_freshness_summary}")
    if progress_freshness.get("latest_progress_time_label") and progress_freshness.get("latest_progress_summary"):
        lines.append(
            f"- 最近明确推进: {progress_freshness.get('latest_progress_time_label')}，"
            f"{progress_freshness.get('latest_progress_summary')}"
        )
    if runtime_reason:
        lines.append(f"- 决策原因: {runtime_reason}")
    if continuation_reason:
        lines.append(f"- continuation_reason: {continuation_reason}")
    if operator_status_card:
        lines.extend(
            [
                "",
                "## 操作员状态卡",
                "",
                f"- 当前处理态: {operator_status_card.get('handling_state_label') or operator_status_card.get('handling_state') or '未知'}",
                f"- 用户可见结论: {operator_status_card.get('user_visible_verdict') or 'none'}",
                f"- 当前聚焦: {operator_status_card.get('current_focus') or 'none'}",
            ]
        )
        if operator_status_card.get("owner_summary"):
            lines.append(f"- 责任说明: {operator_status_card.get('owner_summary')}")
        if operator_status_card.get("latest_truth_source_label") or operator_status_card.get("latest_truth_time"):
            truth_source = operator_status_card.get("latest_truth_source_label") or operator_status_card.get("latest_truth_source") or "unknown"
            truth_time = operator_status_card.get("latest_truth_time") or "unknown"
            lines.append(f"- 当前真相源: {truth_source} @ {truth_time}")
        if operator_status_card.get("human_surface_summary"):
            lines.append(
                f"- 人类查看面: `{operator_status_card.get('human_surface_freshness') or 'unknown'}`；"
                f"{operator_status_card.get('human_surface_summary')}"
            )
        if operator_status_card.get("next_confirmation_signal"):
            lines.append(f"- 下一确认信号: {operator_status_card.get('next_confirmation_signal')}")
    if bool(quality_review_followthrough.get("waiting_auto_re_review")):
        lines.extend(
            [
                "",
                "## 自动复评后续",
                "",
                f"- 当前状态: {quality_review_followthrough.get('state_label') or quality_review_followthrough.get('state') or '未知'}",
                (
                    "- 系统自动继续: 会"
                    if bool(quality_review_followthrough.get("auto_continue_expected"))
                    else "- 系统自动继续: 不会"
                ),
            ]
        )
        if quality_review_followthrough.get("summary"):
            lines.append(f"- 后续摘要: {quality_review_followthrough.get('summary')}")
        if quality_review_followthrough.get("blocking_reason"):
            lines.append(f"- 未自动继续原因: {quality_review_followthrough.get('blocking_reason')}")
        if quality_review_followthrough.get("next_confirmation_signal"):
            lines.append(f"- 下一确认信号: {quality_review_followthrough.get('next_confirmation_signal')}")
    if quality_repair_batch_followthrough:
        lines.extend(
            [
                "",
                "## Quality-Repair Batch",
                "",
                f"- 当前状态: {quality_repair_batch_followthrough.get('status') or 'unknown'}",
            ]
        )
        if quality_repair_batch_followthrough.get("summary"):
            lines.append(f"- 当前判断: {quality_repair_batch_followthrough.get('summary')}")
        if quality_repair_batch_followthrough.get("failed_unit_count") is not None:
            lines.append(f"- 失败单元数: {quality_repair_batch_followthrough.get('failed_unit_count')}")
        if quality_repair_batch_followthrough.get("blocking_issue_count") is not None:
            lines.append(f"- 剩余 gate blocker: {quality_repair_batch_followthrough.get('blocking_issue_count')}")
        if quality_repair_batch_followthrough.get("next_confirmation_signal"):
            lines.append(f"- 下一确认信号: {quality_repair_batch_followthrough.get('next_confirmation_signal')}")
    if gate_clearing_batch_followthrough:
        lines.extend(
            [
                "",
                "## Gate-Clearing Batch",
                "",
                f"- 当前状态: {gate_clearing_batch_followthrough.get('status') or 'unknown'}",
            ]
        )
        if gate_clearing_batch_followthrough.get("summary"):
            lines.append(f"- 当前判断: {gate_clearing_batch_followthrough.get('summary')}")
        if gate_clearing_batch_followthrough.get("failed_unit_count") is not None:
            lines.append(f"- 失败单元数: {gate_clearing_batch_followthrough.get('failed_unit_count')}")
        if gate_clearing_batch_followthrough.get("blocking_issue_count") is not None:
            lines.append(f"- 剩余 gate blocker: {gate_clearing_batch_followthrough.get('blocking_issue_count')}")
        if gate_clearing_batch_followthrough.get("next_confirmation_signal"):
            lines.append(f"- 下一确认信号: {gate_clearing_batch_followthrough.get('next_confirmation_signal')}")
    if same_line_route_truth:
        lines.extend(
            [
                "",
                "## 同线路由真相",
                "",
                f"- 路由状态: {same_line_route_truth.get('same_line_state_label') or '未知'}",
                f"- 当前判断: {same_line_route_truth.get('summary') or 'none'}",
                f"- 当前关键问题: {same_line_route_truth.get('current_focus') or 'none'}",
            ]
        )
        if same_line_route_truth.get("route_target_label") or same_line_route_truth.get("route_target"):
            lines.append(
                f"- 收口目标: {same_line_route_truth.get('route_target_label') or same_line_route_truth.get('route_target')}"
            )
    elif same_line_route_surface:
        lines.extend(
            [
                "",
                "## 同线收口动作",
                "",
                f"- 收口目标: {same_line_route_surface.get('route_target_label') or same_line_route_surface.get('route_target') or '未知'}",
                f"- 当前判断: {same_line_route_surface.get('summary') or 'none'}",
                f"- 当前关键问题: {same_line_route_surface.get('route_key_question') or 'none'}",
            ]
        )
        if same_line_route_surface.get("why_now"):
            lines.append(f"- 为什么现在做: {same_line_route_surface.get('why_now')}")
    if module_surfaces:
        lines.extend(
            [
                "",
                "## 主线模块",
                "",
            ]
        )
        for module_name in ("controller_charter", "runtime", "eval_hygiene"):
            module_surface = dict(module_surfaces.get(module_name) or {})
            if not module_surface:
                continue
            lines.append(
                "- "
                + module_name
                + ": "
                + (module_surface.get("status_summary") or "none")
                + " 下一动作："
                + (module_surface.get("next_action_summary") or "none")
                + " ref: `"
                + (module_surface.get("summary_ref") or "none")
                + "`"
            )
    lines.extend(
        [
            "",
        "## 当前阻塞",
        "",
        ]
    )
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- 当前没有额外阻塞记录。")
    lines.extend(
        [
            "",
            "## 下一步",
            "",
            f"- 下一步建议: {next_step_summary}",
        ]
    )
    if autonomy_contract:
        lines.extend(["", "## 自治合同", ""])
        if autonomy_contract.get("summary"):
            lines.append(
                f"- 当前自治判断: {_display_text(autonomy_contract.get('summary')) or autonomy_contract.get('summary')}"
            )
        if autonomy_contract.get("next_signal"):
            lines.append(
                f"- 下一确认信号: {_display_text(autonomy_contract.get('next_signal')) or autonomy_contract.get('next_signal')}"
            )
        if autonomy_contract.get("recommended_command"):
            lines.append(f"- 恢复/续跑命令: `{autonomy_contract.get('recommended_command')}`")
        restore_point = dict(autonomy_contract.get("restore_point") or {})
        if restore_point.get("summary"):
            lines.append(
                f"- 恢复点: {_display_text(restore_point.get('summary')) or restore_point.get('summary')}"
            )
        latest_outer_loop_dispatch = dict(autonomy_contract.get("latest_outer_loop_dispatch") or {})
        if latest_outer_loop_dispatch.get("summary"):
            lines.append(
                "- 最近一次自治续跑: "
                + (
                    _display_text(latest_outer_loop_dispatch.get("summary"))
                    or latest_outer_loop_dispatch.get("summary")
                )
            )
    autonomy_soak_status = _mapping_copy(normalized_payload.get("autonomy_soak_status"))
    if autonomy_soak_status:
        lines.extend(["", "## 自治 Proof / Soak", ""])
        if autonomy_soak_status.get("summary"):
            lines.append(
                f"- 当前自治证据: {_display_text(autonomy_soak_status.get('summary')) or autonomy_soak_status.get('summary')}"
            )
        if autonomy_soak_status.get("progress_freshness_status"):
            lines.append(f"- 进度新鲜度: `{autonomy_soak_status.get('progress_freshness_status')}`")
        if autonomy_soak_status.get("next_confirmation_signal"):
            lines.append(
                "- 下一确认信号: "
                + (
                    _display_text(autonomy_soak_status.get("next_confirmation_signal"))
                    or autonomy_soak_status.get("next_confirmation_signal")
                )
            )
    if quality_closure_truth:
        lines.extend(["", "## 质量闭环", ""])
        if quality_closure_truth.get("summary"):
            lines.append(
                f"- 当前质量判断: {_display_text(quality_closure_truth.get('summary')) or quality_closure_truth.get('summary')}"
            )
        if quality_execution_lane.get("summary"):
            lines.append(
                f"- 当前质量执行线: {_display_text(quality_execution_lane.get('summary')) or quality_execution_lane.get('summary')}"
            )
        for key in (
            "clinical_significance",
            "evidence_strength",
            "novelty_positioning",
            "human_review_readiness",
            "publication_gate",
        ):
            basis_item = dict(quality_closure_basis.get(key) or {})
            summary = _display_text(basis_item.get("summary")) or basis_item.get("summary")
            if summary:
                lines.append(f"- {_QUALITY_CLOSURE_BASIS_LABELS.get(key, key)}: {summary}")
    if quality_review_agenda:
        lines.extend(["", "## 质量评审议程", ""])
        top_priority_issue = _display_text(quality_review_agenda.get("top_priority_issue")) or _non_empty_text(
            quality_review_agenda.get("top_priority_issue")
        )
        suggested_revision = _display_text(quality_review_agenda.get("suggested_revision")) or _non_empty_text(
            quality_review_agenda.get("suggested_revision")
        )
        next_review_focus = _display_text(quality_review_agenda.get("next_review_focus")) or _non_empty_text(
            quality_review_agenda.get("next_review_focus")
        )
        if top_priority_issue:
            lines.append(f"- 当前优先问题: {top_priority_issue}")
        if suggested_revision:
            lines.append(f"- 建议修订动作: {suggested_revision}")
        if next_review_focus:
            lines.append(f"- 下一轮复评重点: {next_review_focus}")
    if quality_review_loop:
        lines.extend(["", "## 质量评审闭环", ""])
        current_phase_label = _display_text(quality_review_loop.get("current_phase_label")) or _non_empty_text(
            quality_review_loop.get("current_phase_label")
        )
        recommended_next_phase_label = _display_text(
            quality_review_loop.get("recommended_next_phase_label")
        ) or _non_empty_text(quality_review_loop.get("recommended_next_phase_label"))
        summary = _display_text(quality_review_loop.get("summary")) or _non_empty_text(quality_review_loop.get("summary"))
        recommended_next_action = _display_text(quality_review_loop.get("recommended_next_action")) or _non_empty_text(
            quality_review_loop.get("recommended_next_action")
        )
        if current_phase_label:
            lines.append(f"- 当前闭环阶段: {current_phase_label}")
        if recommended_next_phase_label:
            lines.append(f"- 下一跳: {recommended_next_phase_label}")
        if isinstance(quality_review_loop.get("blocking_issue_count"), int):
            lines.append(f"- 当前阻塞数: {quality_review_loop.get('blocking_issue_count')}")
        if summary:
            lines.append(f"- 闭环摘要: {summary}")
        if recommended_next_action:
            lines.append(f"- 下一动作: {recommended_next_action}")
        for item in [
            _display_text(issue) or _non_empty_text(issue)
            for issue in (quality_review_loop.get("blocking_issues") or [])
        ]:
            if item:
                lines.append(f"- 当前阻塞项: {item}")
        for focus in [
            _display_text(item) or _non_empty_text(item)
            for item in (quality_review_loop.get("next_review_focus") or [])
        ]:
            if focus:
                lines.append(f"- 复评关注点: {focus}")
    if quality_revision_plan:
        lines.extend(["", "## 质量修订计划", ""])
        overall_diagnosis = _display_text(quality_revision_plan.get("overall_diagnosis")) or _non_empty_text(
            quality_revision_plan.get("overall_diagnosis")
        )
        if overall_diagnosis:
            lines.append(f"- 总体诊断: {overall_diagnosis}")
        for item in [dict(entry) for entry in (quality_revision_plan.get("items") or []) if isinstance(entry, dict)]:
            priority = (_non_empty_text(item.get("priority")) or "p1").upper()
            dimension = _QUALITY_REVISION_DIMENSION_LABELS.get(
                _non_empty_text(item.get("dimension")) or "",
                _humanize_token(item.get("dimension")) or "未命名维度",
            )
            route_target = _display_text(item.get("route_target")) or _non_empty_text(item.get("route_target"))
            item_title = f"{priority} [{dimension}]"
            if route_target:
                item_title = f"{item_title} -> {route_target}"
            action = _display_text(item.get("action")) or _non_empty_text(item.get("action"))
            rationale = _display_text(item.get("rationale")) or _non_empty_text(item.get("rationale"))
            done_criteria = _display_text(item.get("done_criteria")) or _non_empty_text(item.get("done_criteria"))
            if action:
                lines.append(f"- {item_title}: {action}")
            else:
                lines.append(f"- {item_title}")
            if rationale:
                lines.append(f"- 修订理由: {rationale}")
            if done_criteria:
                lines.append(f"- 完成标准: {done_criteria}")
        for focus in [
            _display_text(item) or _non_empty_text(item)
            for item in (quality_revision_plan.get("next_review_focus") or [])
        ]:
            if focus:
                lines.append(f"- 下一轮复评关注: {focus}")
    if recovery_contract:
        lines.extend(["", "## 恢复合同", ""])
        if recovery_action_mode:
            lines.append(f"- 恢复模式: {recovery_action_mode}")
        if recovery_contract.get("summary"):
            lines.append(
                f"- 合同摘要: {_display_text(recovery_contract.get('summary')) or recovery_contract.get('summary')}"
            )
        for item in recovery_steps:
            title = _non_empty_text(item.get("title")) or _humanize_token(item.get("step_id")) or "未命名步骤"
            surface_label = (_non_empty_text(item.get("surface_kind")) or "unknown").replace("_", "-")
            command = _non_empty_text(item.get("command")) or "none"
            lines.append(f"- {title} [{surface_label}]: `{command}`")
    if payload.get("physician_decision_summary"):
        lines.extend(["", "## 医生判断", "", f"- {str(payload.get('physician_decision_summary') or '').strip()}"])
    lines.extend(["", "## 最近进展", ""])
    if latest_events:
        for item in latest_events:
            time_label = str(item.get("time_label") or item.get("timestamp") or "").strip()
            summary = _display_text(item.get("summary")) or str(item.get("summary") or "").strip()
            lines.append(f"- {time_label}: {summary}")
    else:
        lines.append("- 目前没有可用的阶段事件。")
    supervision = dict(payload.get("supervision") or {})
    lines.extend(["", "## 监督入口", ""])
    supervision_labels = {
        "browser_url": "监控入口",
        "quest_session_api_url": "会话接口",
        "active_run_id": "active_run_id",
        "launch_report_path": "launch_report_path",
    }
    for key in ("browser_url", "quest_session_api_url", "active_run_id", "launch_report_path"):
        value = str(supervision.get(key) or "").strip()
        if value:
            lines.append(f"- {supervision_labels[key]}: `{value}`")
    return "\n".join(lines) + "\n"
__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
