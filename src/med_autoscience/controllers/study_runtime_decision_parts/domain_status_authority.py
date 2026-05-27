from __future__ import annotations

if __name__ != "med_autoscience.controllers.study_runtime_decision":
    from .domain_transition_arbitration import *  # noqa: F403
    from .manual_finish_dominance import *  # noqa: F403
    from .publication_and_submission import *  # noqa: F403
    from .runtime_events import *  # noqa: F403
    from .domain_transition_status import *  # noqa: F403
    from .quest_status_decisions import *  # noqa: F403
    from .runtime_health_dominance import *  # noqa: F403
    from .status_projection_shell import *  # noqa: F403
    from .supervisor_state_overrides import *  # noqa: F403

from med_autoscience.controllers.owner_route_reconcile_parts import opl_provider_attempts


def _status_state(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    study_payload: dict[str, object],
    entry_mode: str | None,
    sync_runtime_summary: bool = True,
    include_progress_projection: bool = True,
) -> ProgressProjectionStatus:
    router = _router_module()
    execution = router._execution_payload(study_payload, profile=profile)
    explicit_opl_runtime_ref = opl_runtime_contract.explicit_opl_runtime_ref(execution)
    selected_entry_mode = str(entry_mode or execution.get("default_entry_mode") or "full_research").strip() or "full_research"
    quest_id = str(execution.get("quest_id") or study_id).strip() or study_id
    runtime_context = study_runtime_protocol.resolve_study_runtime_context(
        profile=profile,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
    )
    runtime_root = runtime_context.runtime_root
    quest_root = runtime_context.quest_root
    runtime_binding_path = runtime_context.runtime_binding_path
    launch_report_path = runtime_context.launch_report_path
    quest_runtime = quest_state.inspect_quest_runtime(quest_root)
    quest_exists = quest_runtime.quest_exists
    quest_status = ProgressProjectionStatus._normalize_quest_status_field(quest_runtime.quest_status)
    if quest_status in _LIVE_QUEST_STATUSES and opl_runtime_contract.is_opl_hosted_research_execution(execution):
        runtime_liveness_projection = _opl_current_control_state_runtime_liveness_projection(
            profile=profile,
            study_root=study_root,
            study_id=study_id,
            quest_status=quest_status,
        )
        quest_runtime = quest_runtime.with_runtime_liveness_audit(
            runtime_liveness_projection
            or _unknown_opl_current_control_state_runtime_liveness(quest_status=quest_status)
        )
    contracts = router.inspect_workspace_contracts(profile)
    readiness = startup_data_readiness_controller.startup_data_readiness(workspace_root=profile.workspace_root)
    startup_boundary_gate = startup_boundary_gate_controller.evaluate_startup_boundary(
        profile=profile,
        study_root=study_root,
        study_payload=study_payload,
        execution=execution,
    )
    runtime_reentry_gate = runtime_reentry_gate_controller.evaluate_runtime_reentry(
        study_root=study_root,
        study_payload=study_payload,
        execution=execution,
        quest_root=quest_root if quest_exists else None,
        enforce_startup_hydration=quest_status in _LIVE_QUEST_STATUSES,
    )
    completion_state = router._study_completion_state(study_root=study_root)
    result = ProgressProjectionStatus(
        schema_version=1,
        study_id=study_id,
        study_root=str(study_root),
        entry_mode=selected_entry_mode,
        execution=execution,
        quest_id=quest_id,
        quest_root=str(quest_root),
        quest_exists=quest_exists,
        quest_status=quest_status,
        runtime_binding_path=str(runtime_binding_path),
        runtime_binding_exists=runtime_binding_path.exists(),
        workspace_contracts=contracts,
        startup_data_readiness=readiness,
        startup_boundary_gate=startup_boundary_gate,
        runtime_reentry_gate=runtime_reentry_gate,
        study_completion_state=completion_state,
        controller_first_policy_summary=router.render_controller_first_summary(),
        automation_ready_summary=router.render_automation_ready_summary(),
    )

    if quest_exists:
        from med_autoscience.study_task_intake import build_task_intake_progress_override

        publication_gate_report = publication_gate_controller.build_gate_report(
            publication_gate_controller.build_gate_state(quest_root)
        )
        task_intake_progress_override = build_task_intake_progress_override(
            read_latest_task_intake(study_root=study_root),
            study_root=study_root,
            publishability_gate_report=publication_gate_report,
        )
        result.record_publication_supervisor_state(
            _task_intake_publication_supervisor_state(task_intake_progress_override)
            or publication_gate_controller.extract_publication_supervisor_state(publication_gate_report)
        )
        manual_finish_state = _derive_manual_finish_dominance_state(
            quest_exists=quest_exists,
            quest_status=quest_status,
            study_root=study_root,
            quest_root=quest_root,
            publication_gate_report=publication_gate_report,
        )
        if sync_runtime_summary:
            _materialize_publication_eval_from_gate_report(
                study_root=study_root,
                study_id=study_id,
                quest_root=quest_root,
                quest_id=quest_id,
                publication_gate_report=publication_gate_report,
            )
    else:
        publication_gate_report = None
        manual_finish_state = _derive_manual_finish_dominance_state(
            quest_exists=quest_exists,
            quest_status=quest_status,
            study_root=study_root,
            quest_root=quest_root,
            publication_gate_report=publication_gate_report,
        )
    task_intake_releases_manual_finish_parking = manual_finish_state["task_intake_releases_manual_finish_parking"]
    reviewer_revision_open_blockers_release_manual_finish_parking = manual_finish_state[
        "reviewer_revision_open_blockers_release_manual_finish_parking"
    ]
    submission_metadata_only_manual_finish = manual_finish_state["submission_metadata_only_manual_finish"]
    task_intake_yields_to_submission_closeout = manual_finish_state["task_intake_yields_to_submission_closeout"]
    manual_hold_task_intake = manual_finish_state["manual_hold_task_intake"]
    bundle_only_manual_finish = manual_finish_state["bundle_only_manual_finish"]
    manual_finish_compatibility_guard = manual_finish_state["manual_finish_compatibility_guard"]
    submission_metadata_only_wait = manual_finish_state["submission_metadata_only_wait"]
    task_intake_releases_bare_paused_parking = (
        task_intake_releases_manual_finish_parking
        and not task_intake_yields_to_submission_closeout
    )
    _record_continuation_state_if_present(
        status=result,
        quest_root=quest_root,
        active_run_id=_runtime_liveness_active_run_id(quest_runtime.runtime_liveness_audit),
        live_opl_provider_attempt=(
            _runtime_liveness_active_run_id(quest_runtime.runtime_liveness_audit) is not None
        ),
    )
    _record_controller_authorization_if_present(status=result, quest_root=quest_root, study_root=study_root)
    _record_blocked_closeout_if_present(status=result, quest_root=quest_root)
    _record_blocked_closeout_supersession_if_present(
        status=result,
        study_root=study_root,
        quest_root=quest_root,
    )
    record_domain_transition_if_required(status=result, study_root=study_root)
    _record_pending_user_interaction_if_required(
        status=result,
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id=quest_id,
        publication_gate_report=publication_gate_report,
    )
    _record_interaction_arbitration_if_required(
        status=result,
        quest_root=quest_root,
        execution=execution,
        submission_metadata_only=submission_metadata_only_wait,
        publication_gate_report=publication_gate_report,
    )

    def _finalize_result() -> ProgressProjectionStatus:
        return finalize_status_projection_shell(
            status=result,
            study_id=study_id,
            profile=profile,
            study_root=study_root,
            quest_id=quest_id,
            quest_root=quest_root,
            quest_runtime=quest_runtime,
            runtime_context=runtime_context,
            router=router,
            entry_mode=entry_mode,
            sync_runtime_summary=sync_runtime_summary,
            include_progress_projection=include_progress_projection,
        )

    if explicit_opl_runtime_ref is not None and not opl_runtime_contract.is_opl_hosted_research_execution(execution):
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STUDY_EXECUTION_RUNTIME_BACKEND_UNBOUND,
        )
        return _finalize_result()

    if not opl_runtime_contract.is_opl_hosted_research_execution(execution):
        result.set_decision(
            StudyRuntimeDecision.LIGHTWEIGHT,
            StudyRuntimeReason.STUDY_EXECUTION_NOT_MANAGED_RUNTIME_BACKEND,
        )
        return _finalize_result()

    auto_entry = str(execution.get("auto_entry") or "").strip()
    default_entry_mode = str(execution.get("default_entry_mode") or "full_research").strip() or "full_research"
    if auto_entry != "on_managed_research_intent":
        result.set_decision(
            StudyRuntimeDecision.LIGHTWEIGHT,
            StudyRuntimeReason.STUDY_EXECUTION_NOT_MANAGED,
        )
        return _finalize_result()
    if selected_entry_mode != default_entry_mode:
        result.set_decision(
            StudyRuntimeDecision.LIGHTWEIGHT,
            StudyRuntimeReason.ENTRY_MODE_NOT_MANAGED,
        )
        return _finalize_result()
    if _publication_supervisor_requests_stop_loss(result):
        result.set_decision(
            StudyRuntimeDecision.PAUSE if quest_status in _LIVE_QUEST_STATUSES else StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.PUBLISHABILITY_STOP_LOSS_RECOMMENDED,
        )
        return _finalize_result()
    if manual_hold_task_intake or _publication_supervisor_requests_manual_hold(result):
        result.set_decision(
            StudyRuntimeDecision.PAUSE if quest_status in _LIVE_QUEST_STATUSES else StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_WAITING_FOR_EXPLICIT_WAKEUP_AFTER_MANUAL_HOLD,
        )
        return _finalize_result()
    study_charter_gate_reason = _study_charter_gate_reason(publication_gate_report)
    if study_charter_gate_reason is not None:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            study_charter_gate_reason,
        )
        return _finalize_result()

    completion_contract_status = completion_state.status
    if completion_contract_status in {
        StudyCompletionStateStatus.INVALID,
        StudyCompletionStateStatus.INCOMPLETE,
    }:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STUDY_COMPLETION_CONTRACT_NOT_READY,
        )
        return _finalize_result()
    if completion_state.ready:
        contract = completion_state.contract
        if contract is not None and contract.requires_program_human_confirmation:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.STUDY_COMPLETION_REQUIRES_PROGRAM_HUMAN_CONFIRMATION,
            )
            return _finalize_result()
        if quest_exists and quest_status == StudyRuntimeQuestStatus.COMPLETED:
            result.set_decision(
                StudyRuntimeDecision.COMPLETED,
                StudyRuntimeReason.QUEST_ALREADY_COMPLETED,
            )
            return _finalize_result()
        if _apply_completion_publication_gate_decision(
            result,
            study_root=study_root,
            publication_gate_report=publication_gate_report,
        ):
            return _finalize_result()
        if not quest_exists:
            result.set_decision(
                StudyRuntimeDecision.COMPLETED,
                StudyRuntimeReason.STUDY_COMPLETION_DECLARED_WITHOUT_MANAGED_QUEST,
            )
            return _finalize_result()
        if quest_status in _LIVE_QUEST_STATUSES:
            audit_status = router._record_quest_runtime_audits(status=result, quest_runtime=quest_runtime)
            if audit_status is quest_state.QuestRuntimeLivenessStatus.UNKNOWN:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.STUDY_COMPLETION_LIVE_RUNTIME_AUDIT_FAILED,
                )
            elif audit_status is quest_state.QuestRuntimeLivenessStatus.LIVE:
                result.set_decision(
                    StudyRuntimeDecision.PAUSE_AND_COMPLETE,
                    StudyRuntimeReason.STUDY_COMPLETION_READY,
                )
            else:
                result.set_decision(
                    StudyRuntimeDecision.SYNC_COMPLETION,
                    StudyRuntimeReason.STUDY_COMPLETION_READY,
                )
            return _finalize_result()
        result.set_decision(
            StudyRuntimeDecision.SYNC_COMPLETION,
            StudyRuntimeReason.STUDY_COMPLETION_READY,
        )
        return _finalize_result()
    if _is_delivered_human_review_milestone_without_live_worker(result, study_root=study_root):
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_PARKED_ON_UNCHANGED_FINALIZE_STATE,
        )
        return _finalize_result()

    if not result.workspace_overall_ready:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.WORKSPACE_CONTRACT_NOT_READY,
        )
        return _finalize_result()

    if result.has_unresolved_contract_for(study_id):
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STUDY_DATA_READINESS_BLOCKED,
        )
        return _finalize_result()

    if sync_runtime_summary:
        startup_contract_validation = study_runtime_protocol.validate_startup_contract_resolution(
            startup_contract=router._build_startup_contract(
                profile=profile,
                study_id=study_id,
                study_root=study_root,
                study_payload=study_payload,
                execution=execution,
            )
        )
    else:
        startup_contract_validation = _read_only_startup_contract_validation(
            profile=profile,
            study_root=study_root,
            study_payload=study_payload,
        )
    result.record_startup_contract_validation(startup_contract_validation.to_dict())
    if startup_contract_validation.status is not study_runtime_protocol.StartupContractValidationStatus.CLEAR:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STARTUP_CONTRACT_RESOLUTION_FAILED,
        )
        return _finalize_result()

    if quest_status in _RESUMABLE_QUEST_STATUSES:
        domain_redrive_reason = _current_ai_reviewer_domain_redrive_reason(
            result,
            study_root=study_root,
        )
        if _apply_ai_reviewer_domain_redrive_decision(
            result,
            reason=domain_redrive_reason,
            execution=execution,
            running_quest=False,
        ):
            return _finalize_result()

    if (
        manual_finish_compatibility_guard
        and (not task_intake_releases_manual_finish_parking or task_intake_yields_to_submission_closeout)
        and quest_status not in _LIVE_QUEST_STATUSES
        and not _has_domain_transition_runtime_redrive(result)
        and not _has_controller_work_unit_pending_redrive(result)
    ):
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
        )
        return _finalize_result()

    if not quest_exists:
        if result.startup_boundary_allows_compute_stage:
            if result.runtime_reentry_allows_runtime_entry:
                result.set_decision(
                    StudyRuntimeDecision.CREATE_AND_START,
                    StudyRuntimeReason.QUEST_MISSING,
                )
            else:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_AUTO_START,
                )
        else:
            result.set_decision(
                StudyRuntimeDecision.CREATE_ONLY,
                StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_AUTO_START,
            )
        return _finalize_result()

    if quest_status in _LIVE_QUEST_STATUSES:
        return _apply_live_quest_status_decision(
            result=result,
            router=router,
            quest_runtime=quest_runtime,
            execution=execution,
            study_root=study_root,
            study_id=study_id,
            quest_id=quest_id,
            publication_gate_report=publication_gate_report,
            manual_finish_compatibility_guard=manual_finish_compatibility_guard,
            submission_metadata_only_manual_finish=submission_metadata_only_manual_finish,
            task_intake_releases_manual_finish_parking=task_intake_releases_manual_finish_parking,
            task_intake_yields_to_submission_closeout=task_intake_yields_to_submission_closeout,
            reviewer_revision_open_blockers_release_manual_finish_parking=(
                reviewer_revision_open_blockers_release_manual_finish_parking
            ),
            finalize_result=_finalize_result,
        )

    if quest_status in _RESUMABLE_QUEST_STATUSES:
        return _apply_resumable_quest_status_decision(
            result=result,
            rebuild_status=lambda: _status_state(
                    profile=profile,
                    study_id=study_id,
                    study_root=study_root,
                    study_payload=study_payload,
                    entry_mode=entry_mode,
                    sync_runtime_summary=sync_runtime_summary,
                    include_progress_projection=include_progress_projection,
            ),
            execution=execution,
            study_root=study_root,
            quest_root=quest_root,
            quest_status=quest_status,
            task_intake_releases_bare_paused_parking=task_intake_releases_bare_paused_parking,
            task_intake_releases_manual_finish_parking=task_intake_releases_manual_finish_parking,
            submission_metadata_only_manual_finish=submission_metadata_only_manual_finish,
            bundle_only_manual_finish=bundle_only_manual_finish,
            finalize_result=_finalize_result,
        )

    if quest_status in {StudyRuntimeQuestStatus.STOPPED, StudyRuntimeQuestStatus.FAILED}:
        return _apply_stopped_or_failed_quest_status_decision(
            result=result,
            execution=execution,
            quest_root=quest_root,
            quest_status=quest_status,
            publication_gate_report=publication_gate_report,
            task_intake_releases_manual_finish_parking=task_intake_releases_manual_finish_parking,
            task_intake_yields_to_submission_closeout=task_intake_yields_to_submission_closeout,
            submission_metadata_only_manual_finish=submission_metadata_only_manual_finish,
            bundle_only_manual_finish=bundle_only_manual_finish,
            finalize_result=_finalize_result,
        )

    if quest_status == StudyRuntimeQuestStatus.WAITING_FOR_USER:
        return _apply_waiting_for_user_status_decision(
            result=result,
            submission_metadata_only_wait=submission_metadata_only_wait,
            submission_metadata_only_manual_finish=submission_metadata_only_manual_finish,
            finalize_result=_finalize_result,
        )

    result.set_decision(
        StudyRuntimeDecision.BLOCKED,
        StudyRuntimeReason.QUEST_EXISTS_WITH_NON_RESUMABLE_STATE,
    )
    return _finalize_result()


def _status_payload(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    study_payload: dict[str, object],
    entry_mode: str | None,
    sync_runtime_summary: bool = True,
    include_progress_projection: bool = True,
) -> dict[str, object]:
    router = _router_module()
    return router._status_state(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        study_payload=study_payload,
        entry_mode=entry_mode,
        sync_runtime_summary=sync_runtime_summary,
        include_progress_projection=include_progress_projection,
    ).to_dict()


def _read_only_startup_contract_validation(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    study_payload: dict[str, object],
) -> study_runtime_protocol.StartupContractValidation:
    from med_autoscience.controllers import (
        medical_analysis_contract as medical_analysis_contract_controller,
        medical_reporting_contract as medical_reporting_contract_controller,
    )

    medical_analysis_contract_summary = medical_analysis_contract_controller.resolve_medical_analysis_contract_for_study(
        study_root=study_root,
        study_payload=study_payload,
        profile=profile,
    )
    medical_reporting_contract_summary = medical_reporting_contract_controller.resolve_medical_reporting_contract_for_study(
        study_root=study_root,
        study_payload=study_payload,
        profile=profile,
    )
    return study_runtime_protocol.validate_startup_contract_resolution(
        startup_contract={
            "medical_analysis_contract_summary": medical_analysis_contract_summary,
            "medical_reporting_contract_summary": medical_reporting_contract_summary,
        }
    )


def _unknown_opl_current_control_state_runtime_liveness(
    *,
    quest_status: StudyRuntimeQuestStatus | None,
) -> dict[str, object]:
    return {
        "status": "unknown",
        "source": "opl_current_control_state_required",
        "runtime_owner": "one-person-lab",
        "domain_owner": "med-autoscience",
        "mas_provider_live_query_retired": True,
        "provider_completion_is_domain_completion": False,
        "snapshot": {"status": quest_status.value if quest_status is not None else None},
    }


def _runtime_health_liveness_status(study_entry: dict[str, object]) -> str | None:
    runtime_health = study_entry.get("runtime_health")
    if isinstance(runtime_health, dict):
        value = str(runtime_health.get("runtime_liveness_status") or "").strip()
        if value:
            return value
    return str(study_entry.get("runtime_liveness_status") or "").strip() or None


def _runtime_liveness_active_run_id(runtime_liveness_audit: dict[str, object] | None) -> str | None:
    if not isinstance(runtime_liveness_audit, dict):
        return None
    if str(runtime_liveness_audit.get("source") or "").strip() != "opl_current_control_state_provider_attempt":
        return None
    return str(runtime_liveness_audit.get("active_run_id") or "").strip() or None


def _opl_current_control_state_runtime_liveness_projection(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    study_id: str,
    quest_status: StudyRuntimeQuestStatus | None,
) -> dict[str, object] | None:
    latest_report_path = _opl_current_control_state_handoff_path(study_root=study_root)
    latest_report = _read_json_mapping(latest_report_path) or {}
    study_entry = _opl_current_control_state_study_entry(latest_report, study_id=study_id)
    if study_entry is not None:
        handoff_projection = _opl_current_control_state_handoff_liveness_projection(
            latest_report=latest_report,
            latest_report_path=latest_report_path,
            study_entry=study_entry,
            quest_status=quest_status,
        )
        if handoff_projection is not None:
            return handoff_projection
    live_attempt = opl_provider_attempts.live_provider_attempt_for_study(
        profile=profile,
        study_id=study_id,
    )
    if live_attempt is not None:
        return _opl_live_provider_attempt_liveness_projection(
            latest_report=latest_report,
            latest_report_path=latest_report_path,
            live_attempt=live_attempt,
            quest_status=quest_status,
        )
    return None


def _opl_current_control_state_handoff_liveness_projection(
    *,
    latest_report: dict[str, object],
    latest_report_path: Path,
    study_entry: dict[str, object],
    quest_status: StudyRuntimeQuestStatus | None,
) -> dict[str, object] | None:
    active_run_id = str(study_entry.get("active_run_id") or "").strip() or None
    if active_run_id is None or study_entry.get("running_provider_attempt") is not True:
        return None
    if _runtime_health_liveness_status(study_entry) != "live":
        return None
    active_stage_attempt_id = str(study_entry.get("active_stage_attempt_id") or "").strip() or None
    active_workflow_id = str(study_entry.get("active_workflow_id") or "").strip() or None
    runtime_health = study_entry.get("runtime_health")
    return {
        "status": "live",
        "source": "opl_current_control_state_provider_attempt",
        "runtime_owner": "one-person-lab",
        "domain_owner": "med-autoscience",
        "mas_provider_live_query_retired": True,
        "provider_completion_is_domain_completion": False,
        "authority": str(latest_report.get("authority") or "observability_only").strip() or "observability_only",
        "active_run_id": active_run_id,
        "active_stage_attempt_id": active_stage_attempt_id,
        "active_workflow_id": active_workflow_id,
        "running_provider_attempt": True,
        "handoff_path": str(latest_report_path),
        "handoff_generated_at": str(latest_report.get("generated_at") or latest_report.get("recorded_at") or "").strip()
        or None,
        "runtime_health": dict(runtime_health) if isinstance(runtime_health, dict) else {},
        "stage_progress_log": _stage_progress_log(study_entry.get("stage_progress_log")),
        "snapshot": {"status": quest_status.value if quest_status is not None else None},
    }


def _opl_live_provider_attempt_liveness_projection(
    *,
    latest_report: dict[str, object],
    latest_report_path: Path,
    live_attempt: dict[str, object],
    quest_status: StudyRuntimeQuestStatus | None,
) -> dict[str, object] | None:
    active_run_id = str(live_attempt.get("active_run_id") or "").strip() or None
    if active_run_id is None or live_attempt.get("running_provider_attempt") is not True:
        return None
    runtime_health = live_attempt.get("runtime_health")
    return {
        "status": "live",
        "source": "opl_current_control_state_provider_attempt",
        "provider_attempt_source": str(live_attempt.get("source") or "opl_family_runtime_queue_inspect").strip()
        or "opl_family_runtime_queue_inspect",
        "runtime_owner": "one-person-lab",
        "domain_owner": "med-autoscience",
        "mas_provider_live_query_retired": True,
        "provider_completion_is_domain_completion": False,
        "authority": str(latest_report.get("authority") or "observability_only").strip() or "observability_only",
        "active_run_id": active_run_id,
        "active_stage_attempt_id": str(live_attempt.get("active_stage_attempt_id") or "").strip() or None,
        "active_workflow_id": str(live_attempt.get("active_workflow_id") or "").strip() or None,
        "running_provider_attempt": True,
        "handoff_path": str(latest_report_path),
        "handoff_generated_at": str(latest_report.get("generated_at") or latest_report.get("recorded_at") or "").strip()
        or None,
        "runtime_health": dict(runtime_health) if isinstance(runtime_health, dict) else {},
        "stage_progress_log": _stage_progress_log(live_attempt.get("stage_progress_log")),
        "snapshot": {"status": quest_status.value if quest_status is not None else None},
    }


def _stage_progress_log(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    keys = (
        "surface_kind",
        "projection_scope",
        "attempt_count",
        "completed_attempt_count",
        "blocked_attempt_count",
        "activity_event_count",
        "runner_progress_event_count",
        "duration_observed_attempt_count",
        "missing_usage_telemetry_attempt_count",
        "temporal_attempt_count",
        "temporal_webui_ref_count",
        "temporal_visibility_readiness_statuses",
        "activity_event_ref_count",
        "attempt_refs",
        "temporal_webui_refs",
        "authority_boundary",
    )
    projection = {key: value[key] for key in keys if key in value}
    return projection or None


__all__ = [name for name in globals() if not name.startswith("__")]
