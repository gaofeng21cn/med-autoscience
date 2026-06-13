from __future__ import annotations

from med_autoscience.controllers import (
    ai_first_observability,
    paper_authority_migration,
    domain_action_request_lifecycle,
    artifact_runtime_proof,
    opl_runtime_refs,
    medical_paper_ops_health,
    medical_paper_readiness,
    open_auto_research_projection,
    paper_progress_stall,
    outer_supervision_slo,
)
from med_autoscience.controllers.stage_artifact_index import build_stage_artifact_index
from .delivery_inspection import (
    attach_delivery_inspection_projection as _attach_delivery_inspection_projection,
    read_delivery_inspection_projection as _read_delivery_inspection_projection,
)
from . import existing_projection_refresh as _existing_projection_refresh
from .medical_writing_surfaces import medical_writing_quality_surface_status
from .parked_projection import (
    build_progress_parked_projection,
    parked_text_override,
    projected_current_stage,
)
from .opl_current_control_state_handoff import (
    build_readonly_ai_repair_lifecycle_projection as _build_readonly_ai_repair_lifecycle_projection,
    current_status_publication_gate_stationary as _current_status_publication_gate_stationary,
    current_status_suppresses_ai_repair_lifecycle as _current_status_suppresses_ai_repair_lifecycle,
    merge_live_attempt_observability_into_handoff as _merge_live_attempt_observability_into_handoff,
    opl_current_control_state_live_attempt_handoff_projection as _opl_current_control_state_live_attempt_handoff_projection,
    opl_current_control_state_study_handoff_projection as _opl_current_control_state_study_handoff_projection,
    read_ai_repair_lifecycle as _read_ai_repair_lifecycle,
)
from .current_domain_truth_projection import (
    _current_blockers_respecting_controller_closure,
    domain_truth_supersedes_ai_repair_lifecycle as _domain_truth_supersedes_ai_repair_lifecycle,
    progress_projection_respecting_current_domain_truth as _progress_projection_respecting_current_domain_truth,
)
from .projection_sources import (
    _attach_existing_autonomy_slo_projection,
    _read_gate_specificity_request,
    _read_or_materialize_autonomy_slo_status,
    _supervision_active_run_id,
)
from .projection_eval_surface import read_projection_surface_payloads
from .projection_inputs import resolve_projection_input_paths
from .projection_payload_assembly import (
    assemble_study_progress_payload,
    build_projection_refs,
)
from .projection_quality_surfaces import build_quality_projection_surfaces as _quality_projection_surfaces
from .projection_runtime_surfaces import (
    supervision_health_status as _supervision_health_status,
)
from .runtime_medical_publication_surface import build_runtime_medical_publication_surface_projection
from .runtime_closeout_invalidation import status_with_invalidated_closed_runtime_attempt
from .projection_status_context import build_projection_status_context
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


def _refresh_existing_projection_user_visible_status(payload: dict[str, Any]) -> dict[str, Any]:
    return _existing_projection_refresh.refresh_existing_projection_user_visible_status(payload)


def _refresh_existing_projection_batch_followthroughs(
    *,
    payload: dict[str, Any],
    status: dict[str, Any],
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
    study_id: str,
    study_root: Path,
    publication_eval_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    return _existing_projection_refresh.refresh_existing_projection_batch_followthroughs(
        payload=payload,
        status=status,
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )


def _refresh_existing_projection_current_owner_surfaces(
    *,
    payload: dict[str, Any],
    status: dict[str, Any],
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
    study_root: Path,
    publication_eval_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    return _existing_projection_refresh.refresh_existing_projection_current_owner_surfaces(
        payload=payload,
        status=status,
        profile=profile,
        profile_ref=profile_ref,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
        attach_delivery_inspection_projection_fn=_attach_delivery_inspection_projection,
    )


_sync_progress_first_owner_action_admission = (
    _existing_projection_refresh.sync_progress_first_owner_action_admission
)


_current_redrive_top_level_next_action = _existing_projection_refresh.current_redrive_top_level_next_action


_current_gate_clearing_eval_ids = _existing_projection_refresh.current_gate_clearing_eval_ids


def _stage_artifact_index_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
) -> dict[str, Any] | None:
    return _existing_projection_refresh.stage_artifact_index_projection(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        build_stage_artifact_index_fn=build_stage_artifact_index,
    )


def build_study_progress_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    status_payload: dict[str, Any] | Any,
    profile_ref: str | Path | None = None,
    entry_mode: str | None = None,
    materialize_read_model_artifacts: bool = True,
) -> dict[str, Any]:
    del entry_mode
    status = _status_payload(status_payload)
    status = status_with_invalidated_closed_runtime_attempt(status=status, study_root=study_root)
    existing_projection = status.get("progress_projection")
    if isinstance(existing_projection, dict) and _non_empty_text(existing_projection.get("study_id")) == study_id:
        publication_eval_payload = _read_json_object(
            study_root / "artifacts" / "publication_eval" / "latest.json"
        )
        normalized_existing = _normalize_study_progress_payload(
            {
                **existing_projection,
                "publication_supervisor_state": _mapping_copy(status.get("publication_supervisor_state")),
            }
        )
        normalized_existing.pop("publication_supervisor_state", None)
        normalized_existing = _progress_projection_respecting_current_domain_truth(
            study_root=study_root,
            publication_eval_payload=publication_eval_payload,
            payload=normalized_existing,
        )
        normalized_existing = _refresh_existing_projection_batch_followthroughs(
            payload=normalized_existing,
            status=status,
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            study_root=study_root,
            publication_eval_payload=publication_eval_payload,
        )
        return _attach_existing_autonomy_slo_projection(
            _refresh_existing_projection_user_visible_status(
                _refresh_existing_projection_current_owner_surfaces(
                    payload=normalized_existing,
                    status=status,
                    profile=profile,
                    profile_ref=profile_ref,
                    study_root=study_root,
                    publication_eval_payload=publication_eval_payload,
                )
            ),
            study_root=study_root,
        )

    resolved_study_id = study_id
    resolved_study_root = study_root
    input_paths = resolve_projection_input_paths(status=status, study_root=resolved_study_root)
    quest_id = input_paths.quest_id
    quest_root = input_paths.quest_root
    launch_report_path = input_paths.launch_report_path
    publication_eval_path = input_paths.publication_eval_path
    controller_decision_path = input_paths.controller_decision_path
    runtime_escalation_path = input_paths.runtime_escalation_path
    domain_health_diagnostic_path = input_paths.domain_health_diagnostic_path
    opl_runtime_owner_handoff_path = input_paths.opl_runtime_owner_handoff_path
    gate_clearing_batch_path = input_paths.gate_clearing_batch_path
    bash_summary_path = input_paths.bash_summary_path
    details_projection_path = input_paths.details_projection_path

    runtime_health_snapshot = _mapping_copy(status.get("runtime_health_snapshot"))
    runtime_health_status = (
        _non_empty_text(runtime_health_snapshot.get("attempt_state"))
        or _non_empty_text(status.get("runtime_liveness_status"))
    )
    surface_payloads = read_projection_surface_payloads(
        study_root=resolved_study_root,
        study_id=resolved_study_id,
        status=status,
        paths=input_paths,
        runtime_health_status=runtime_health_status,
        materialize_read_model_artifacts=materialize_read_model_artifacts,
    )
    launch_report_payload = surface_payloads.launch_report_payload
    controller_decision_payload = surface_payloads.controller_decision_payload
    gate_clearing_batch_payload = surface_payloads.gate_clearing_batch_payload
    controller_confirmation_summary_path = surface_payloads.controller_confirmation_summary_path
    controller_confirmation_summary = surface_payloads.controller_confirmation_summary
    opl_runtime_owner_handoff_payload = surface_payloads.opl_runtime_owner_handoff_payload
    runtime_escalation_payload = surface_payloads.runtime_escalation_payload
    domain_health_diagnostic_payload = surface_payloads.domain_health_diagnostic_payload
    publication_eval_payload = surface_payloads.publication_eval_payload
    cutover_publication_eval = paper_authority_migration.cutover_publication_eval_payload(
        study_root=resolved_study_root,
    )
    if cutover_publication_eval is not None:
        publication_eval_payload = {
            **cutover_publication_eval,
            "source_publication_eval": publication_eval_payload,
        }
    gate_specificity_request_path, gate_specificity_request = _read_gate_specificity_request(
        study_root=resolved_study_root,
        publication_eval_payload=publication_eval_payload,
    )
    _publishability_gate_payload = surface_payloads.publishability_gate_payload
    bash_summary_payload = surface_payloads.bash_summary_payload
    details_projection_wrapper = surface_payloads.details_projection_wrapper
    details_projection_payload = surface_payloads.details_projection_payload
    evaluation_summary_payload = surface_payloads.evaluation_summary_payload
    status_context = build_projection_status_context(status=status, study_root=resolved_study_root)
    publication_supervisor_state = status_context.publication_supervisor_state
    autonomous_runtime_notice = status_context.autonomous_runtime_notice
    execution_owner_guard = status_context.execution_owner_guard
    pending_user_interaction = status_context.pending_user_interaction
    interaction_arbitration = status_context.interaction_arbitration
    supervisor_tick_audit = status_context.supervisor_tick_audit
    continuation_state = status_context.continuation_state
    family_checkpoint_lineage = status_context.family_checkpoint_lineage
    runtime_health_snapshot = status_context.runtime_health_snapshot
    study_truth_snapshot = status_context.study_truth_snapshot
    authority_snapshot = status_context.authority_snapshot
    manual_finish_contract = status_context.manual_finish_contract
    medical_writing_quality_surfaces = medical_writing_quality_surface_status(study_root=resolved_study_root)
    runtime_medical_publication_surface = build_runtime_medical_publication_surface_projection(
        study_root=resolved_study_root,
        quest_root=quest_root,
        domain_health_diagnostic_payload=domain_health_diagnostic_payload,
    )
    readiness_builder = (
        medical_paper_readiness.build_medical_paper_readiness_surface
        if materialize_read_model_artifacts
        else medical_paper_readiness.build_medical_paper_readiness_payload
    )
    medical_paper_readiness_surface = readiness_builder(study_root=resolved_study_root)
    medical_paper_ops_health_surface = medical_paper_ops_health.build_medical_paper_ops_health(
        medical_paper_readiness_surface,
    )
    artifact_runtime_proof_surface = artifact_runtime_proof.build_artifact_runtime_proof(
        resolved_study_root,
    )
    submission_hygiene_truth = artifact_runtime_proof.build_submission_hygiene_truth(
        resolved_study_root,
        artifact_runtime_proof=artifact_runtime_proof_surface,
        publication_eval_payload=publication_eval_payload,
        evaluation_summary_payload=evaluation_summary_payload,
    )
    delivery_inspection = _read_delivery_inspection_projection(
        profile=profile,
        profile_ref=profile_ref,
        study_root=resolved_study_root,
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
    runtime_facts = opl_runtime_refs.resolve_opl_runtime_refs(
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
        publication_eval_payload=publication_eval_payload,
    )
    current_stage = _current_stage(
        status=status,
        needs_physician_decision=needs_physician_decision,
        publication_supervisor_state=publication_supervisor_state,
        autonomous_runtime_notice=autonomous_runtime_notice,
        execution_owner_guard=execution_owner_guard,
        continuation_state=continuation_state,
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
        gate_clearing_batch_payload=gate_clearing_batch_payload,
        publication_eval_payload=publication_eval_payload,
        runtime_facts=runtime_facts,
        quest_root=quest_root,
    )
    current_stage_summary = _display_text(_stage_summary(
        status=status,
        current_stage=current_stage,
        publication_supervisor_state=publication_supervisor_state,
        publication_eval_payload=publication_eval_payload,
        latest_progress_message=latest_progress_message,
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
        _current_blockers_respecting_controller_closure(
            study_root=resolved_study_root,
            publication_eval_payload=publication_eval_payload,
            blockers=_current_blockers(
                status=status,
                publication_eval_payload=publication_eval_payload,
                domain_health_diagnostic_payload=domain_health_diagnostic_payload,
                runtime_medical_publication_surface=runtime_medical_publication_surface,
                runtime_escalation_payload=runtime_escalation_payload,
                controller_confirmation_summary=controller_confirmation_summary,
                controller_decision_payload=controller_decision_payload,
                pending_user_interaction=pending_user_interaction,
                interaction_arbitration=interaction_arbitration,
                supervisor_tick_audit=supervisor_tick_audit,
                progress_freshness=progress_freshness,
                manual_finish_contract=manual_finish_contract,
                task_intake_progress_override=task_intake_progress_override,
                evaluation_summary_payload=evaluation_summary_payload,
            ),
        )
    )
    next_system_action = _display_text(_next_system_action(
        needs_physician_decision=needs_physician_decision,
        controller_decision_payload=controller_decision_payload,
        publication_supervisor_state=publication_supervisor_state,
        publication_eval_payload=publication_eval_payload,
        domain_health_diagnostic_payload=domain_health_diagnostic_payload,
        current_blockers=current_blockers,
        execution_owner_guard=execution_owner_guard,
        status=status,
        autonomous_runtime_notice=autonomous_runtime_notice,
        continuation_state=continuation_state,
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
        domain_health_diagnostic_payload=domain_health_diagnostic_payload,
        status=status,
        autonomous_runtime_notice=autonomous_runtime_notice,
        execution_owner_guard=execution_owner_guard,
        continuation_state=continuation_state,
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
        domain_health_diagnostic_payload=domain_health_diagnostic_payload,
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
        opl_runtime_owner_handoff_payload=opl_runtime_owner_handoff_payload,
        opl_runtime_owner_handoff_path=(
            opl_runtime_owner_handoff_path if opl_runtime_owner_handoff_payload is not None else None
        ),
        runtime_escalation_payload=runtime_escalation_payload,
        runtime_escalation_path=runtime_escalation_path,
        publication_eval_payload=publication_eval_payload,
        publication_eval_path=publication_eval_path,
        controller_decision_payload=controller_decision_payload,
        controller_decision_path=controller_decision_path,
        domain_health_diagnostic_payload=domain_health_diagnostic_payload,
        domain_health_diagnostic_path=domain_health_diagnostic_path,
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
    outer_supervision_slo_projection = outer_supervision_slo.build_outer_supervision_slo_projection(
        profile=profile,
        profile_ref=profile_ref,
        study_id=resolved_study_id,
        supervision_status=_mapping_copy(status.get("workspace_opl_runtime_owner_handoff")),
        generated_at=_non_empty_text(status.get("generated_at")),
    )
    status_with_outer_slo = {
        **status,
        "outer_supervision_slo": outer_supervision_slo_projection,
        "progress_freshness": progress_freshness,
        "autonomy_slo": autonomy_slo_status,
    }
    paper_progress_stall_projection = paper_progress_stall.build_paper_progress_stall_read_model(
        status_payload=status_with_outer_slo,
        progress_payload={
            "study_id": resolved_study_id,
            "quest_id": quest_id,
            "progress_freshness": progress_freshness,
            "autonomy_slo": autonomy_slo_status,
        },
    )
    existing_paper_progress_stall = _mapping_copy(status.get("paper_progress_stall"))
    if existing_paper_progress_stall:
        paper_progress_stall_projection = {
            **paper_progress_stall_projection,
            **existing_paper_progress_stall,
        }
    ai_doctor_state = (
        _mapping_copy((autonomy_slo_status or {}).get("ai_doctor_request"))
        or {
            "state": (autonomy_slo_status or {}).get("ai_doctor_state") or "not_observed",
            "request_required": bool((autonomy_slo_status or {}).get("ai_doctor_request_required")),
        }
    )
    repair_recommendation = _mapping_copy((autonomy_slo_status or {}).get("repair_recommendation"))
    ai_repair_lifecycle = None
    if not _current_status_suppresses_ai_repair_lifecycle(status):
        persisted_ai_repair_lifecycle = _read_ai_repair_lifecycle(study_root=resolved_study_root)
        stale_opl_route_superseded = False
        if _domain_truth_supersedes_ai_repair_lifecycle(
            persisted_ai_repair_lifecycle,
            latest_events=latest_events,
        ):
            persisted_ai_repair_lifecycle = None
            stale_opl_route_superseded = True
        if stale_opl_route_superseded:
            ai_repair_lifecycle = None
        else:
            ai_repair_lifecycle = (
                persisted_ai_repair_lifecycle
                or _build_readonly_ai_repair_lifecycle_projection(
                    study_root=resolved_study_root,
                    status_payload=status,
                )
            )
    opl_current_control_state_handoff = _opl_current_control_state_study_handoff_projection(
        profile=profile,
        study_id=resolved_study_id,
    )
    opl_current_control_state_handoff = _merge_live_attempt_observability_into_handoff(
        handoff=opl_current_control_state_handoff,
        live_attempt_handoff=_opl_current_control_state_live_attempt_handoff_projection(
            profile=profile,
            study_id=resolved_study_id,
            runtime_liveness_audit=_mapping_copy(status.get("runtime_liveness_audit")),
        ),
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
        domain_health_diagnostic_payload=domain_health_diagnostic_payload,
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
        domain_health_diagnostic_payload=domain_health_diagnostic_payload,
        quest_root=quest_root,
        materialize_read_model_artifacts=materialize_read_model_artifacts,
    )
    publication_gate_stationary = _current_status_publication_gate_stationary(status)
    runtime_module_surface = _runtime_module_surface(
        generated_at=generated_at,
        study_id=resolved_study_id,
        quest_id=quest_id,
        study_root=resolved_study_root,
        launch_report_path=launch_report_path,
        opl_runtime_owner_handoff_path=opl_runtime_owner_handoff_path,
        opl_runtime_owner_handoff_payload=opl_runtime_owner_handoff_payload,
        runtime_escalation_path=runtime_escalation_path,
        domain_health_diagnostic_path=domain_health_diagnostic_path,
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
        publication_gate_stationary=publication_gate_stationary,
        materialize_read_model_artifacts=materialize_read_model_artifacts,
    )
    quality_projection = _quality_projection_surfaces(
        controller_module_surface=controller_module_surface,
        runtime_module_surface=runtime_module_surface,
        evaluation_module_surface=evaluation_module_surface,
        task_intake_progress_override=task_intake_progress_override,
        publication_supervisor_state=publication_supervisor_state,
    )
    module_surfaces = quality_projection["module_surfaces"]
    quality_closure_truth = quality_projection["quality_closure_truth"]
    quality_execution_lane = quality_projection["quality_execution_lane"]
    same_line_route_truth = quality_projection["same_line_route_truth"]
    same_line_route_surface = quality_projection["same_line_route_surface"]
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
        current_eval_ids=_current_gate_clearing_eval_ids(status=status),
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
        domain_health_diagnostic_path=domain_health_diagnostic_path,
        controller_decision_path=controller_decision_path,
    )
    supervision_health_status = _supervision_health_status(
        publication_gate_stationary=publication_gate_stationary,
        auto_runtime_parked=auto_runtime_parked,
        runtime_facts=runtime_facts,
        runtime_health_status=runtime_health_status,
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
        opl_runtime_owner_handoff_ref=(
            str(opl_runtime_owner_handoff_path) if opl_runtime_owner_handoff_payload is not None else None
        ),
        domain_health_diagnostic_ref=str(domain_health_diagnostic_path) if domain_health_diagnostic_path is not None else None,
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
    current_active_run_id = _supervision_active_run_id(
        status=status,
        execution_owner_guard=execution_owner_guard,
        autonomous_runtime_notice=autonomous_runtime_notice,
        continuation_state=continuation_state,
    )
    open_auto_research_state = open_auto_research_projection.build_open_auto_research_projection(
        study_root=resolved_study_root,
        active_run_id=current_active_run_id,
    )
    ai_reviewer_request_lifecycle = domain_action_request_lifecycle.project_ai_reviewer_request_lifecycle(
        study_root=resolved_study_root,
        publication_eval_payload=publication_eval_payload,
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
    refs = build_projection_refs(
        launch_report_path=launch_report_path,
        publication_eval_path=publication_eval_path,
        controller_decision_path=controller_decision_path,
        controller_confirmation_summary_path=controller_confirmation_summary_path,
        controller_confirmation_summary=controller_confirmation_summary,
        controller_module_surface=controller_module_surface,
        opl_runtime_owner_handoff_path=opl_runtime_owner_handoff_path,
        opl_runtime_owner_handoff_payload=opl_runtime_owner_handoff_payload,
        runtime_escalation_path=runtime_escalation_path,
        domain_health_diagnostic_path=domain_health_diagnostic_path,
        runtime_module_surface=runtime_module_surface,
        runtime_efficiency_refs=_runtime_efficiency_refs(runtime_efficiency),
        study_root=resolved_study_root,
        autonomy_slo_status=autonomy_slo_status,
        ai_repair_lifecycle=ai_repair_lifecycle,
        evaluation_module_surface=evaluation_module_surface,
        medical_writing_quality_surfaces=medical_writing_quality_surfaces,
        gate_specificity_request_path=gate_specificity_request_path,
        gate_specificity_request=gate_specificity_request,
        artifact_runtime_proof_surface=artifact_runtime_proof_surface,
        submission_hygiene_truth=submission_hygiene_truth,
        bash_summary_path=bash_summary_path,
        details_projection_path=details_projection_path,
        ai_first_observability_snapshots=ai_first_observability_snapshots,
        opl_current_control_state_handoff=opl_current_control_state_handoff,
        runtime_medical_publication_surface=runtime_medical_publication_surface,
    )
    refs["ai_reviewer_request_lifecycle_path"] = (
        str(
            domain_action_request_lifecycle.stable_ai_reviewer_request_path(
                study_root=resolved_study_root,
            )
        )
        if ai_reviewer_request_lifecycle is not None
        else None
    )
    stage_artifact_index_projection = _stage_artifact_index_projection(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
    )
    payload = assemble_study_progress_payload(
        generated_at=generated_at,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        quest_id=quest_id,
        quest_root=quest_root,
        current_stage=current_stage,
        current_stage_summary=current_stage_summary,
        paper_stage=paper_stage,
        paper_stage_summary=paper_stage_summary,
        status_narration_contract=status_narration_contract,
        latest_events=latest_events,
        current_blockers=current_blockers,
        next_system_action=next_system_action,
        current_active_run_id=current_active_run_id,
        auto_runtime_parked=auto_runtime_parked,
        intervention_lane=intervention_lane,
        operator_verdict=operator_verdict,
        operator_status_card=operator_status_card,
        recommended_command=recommended_command,
        recommended_commands=recommended_commands,
        autonomy_contract=autonomy_contract,
        autonomy_soak_status=autonomy_soak_status,
        recovery_contract=recovery_contract,
        needs_physician_decision=needs_physician_decision,
        physician_decision_summary=physician_decision_summary,
        status=status,
        continuation_state=continuation_state,
        family_checkpoint_lineage=family_checkpoint_lineage,
        interaction_arbitration=interaction_arbitration,
        manual_finish_contract=manual_finish_contract,
        task_intake=task_intake,
        progress_freshness=progress_freshness,
        quality_closure_truth=quality_closure_truth,
        quality_execution_lane=quality_execution_lane,
        same_line_route_truth=same_line_route_truth,
        same_line_route_surface=same_line_route_surface,
        quality_closure_basis=quality_closure_basis,
        quality_review_agenda=quality_review_agenda,
        quality_revision_plan=quality_revision_plan,
        quality_review_loop=quality_review_loop,
        quality_repair_batch_followthrough=quality_repair_batch_followthrough,
        gate_clearing_batch_followthrough=gate_clearing_batch_followthrough,
        quality_review_followthrough=quality_review_followthrough,
        medical_writing_quality_surfaces=medical_writing_quality_surfaces,
        medical_paper_readiness_surface=medical_paper_readiness_surface,
        medical_paper_ops_health_surface=medical_paper_ops_health_surface,
        artifact_runtime_proof_surface=artifact_runtime_proof_surface,
        submission_hygiene_truth=submission_hygiene_truth,
        delivery_inspection=delivery_inspection,
        research_runtime_control_projection=research_runtime_control_projection,
        open_auto_research_state=open_auto_research_state,
        ai_reviewer_request_lifecycle=ai_reviewer_request_lifecycle,
        opl_current_control_state_handoff=opl_current_control_state_handoff,
        runtime_medical_publication_surface=runtime_medical_publication_surface,
        gate_specificity_request=gate_specificity_request,
        ai_first_default_entry_state=ai_first_default_entry_state,
        paper_orchestra_operator_projection=paper_orchestra_operator_projection,
        ai_first_observability_snapshots=ai_first_observability_snapshots,
        ai_first_operations_dashboard=ai_first_operations_dashboard,
        study_truth_snapshot=study_truth_snapshot,
        runtime_health_snapshot=runtime_health_snapshot,
        authority_snapshot=authority_snapshot,
        module_surfaces=module_surfaces,
        runtime_efficiency=runtime_efficiency,
        paper_progress_stall=paper_progress_stall_projection,
        outer_supervision_slo=outer_supervision_slo_projection,
        autonomy_slo_status=autonomy_slo_status,
        ai_doctor_state=ai_doctor_state,
        repair_recommendation=repair_recommendation,
        ai_repair_lifecycle=ai_repair_lifecycle,
        publication_eval_payload=publication_eval_payload,
        stage_artifact_index=stage_artifact_index_projection,
        autonomous_runtime_notice=autonomous_runtime_notice,
        execution_owner_guard=execution_owner_guard,
        supervisor_tick_audit=supervisor_tick_audit,
        runtime_facts=runtime_facts,
        supervision_health_status=supervision_health_status,
        refs=refs,
        materialize_sidecar_observation=materialize_read_model_artifacts,
    )
    return _progress_projection_respecting_current_domain_truth(
        study_root=resolved_study_root,
        publication_eval_payload=publication_eval_payload,
        payload=payload,
    )


def read_study_progress(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: Path | None = None,
    entry_mode: str | None = None,
    sync_runtime_summary: bool = True,
    materialize_read_model_artifacts: bool | None = None,
) -> dict[str, Any]:
    resolved_study_id, resolved_study_root, _study_payload = _resolve_study(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    status = domain_status_projection.progress_projection(
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
        materialize_read_model_artifacts=sync_runtime_summary
        if materialize_read_model_artifacts is None
        else materialize_read_model_artifacts,
    )
__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
