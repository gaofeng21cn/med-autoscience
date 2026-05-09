from __future__ import annotations

if __name__ != "med_autoscience.controllers.study_runtime_decision":
    from .manual_finish_dominance import *  # noqa: F403
    from .publication_and_submission import *  # noqa: F403
    from .runtime_events import *  # noqa: F403
    from .runtime_health_dominance import *  # noqa: F403
    from .status_finalization import *  # noqa: F403
    from .supervisor_state_overrides import *  # noqa: F403


def _record_interaction_arbitration_if_required(
    *,
    status: StudyRuntimeStatus,
    quest_root: Path,
    execution: dict[str, object],
    submission_metadata_only: bool,
    publication_gate_report: dict[str, object] | None,
) -> None:
    stopped_recovery_context = _stopped_controller_owned_auto_recovery_context(
        status=status,
        quest_root=quest_root,
        publication_gate_report=publication_gate_report,
    )
    if (
        status.quest_status is not StudyRuntimeQuestStatus.WAITING_FOR_USER
        and not _is_controller_owned_finalize_parking(status)
        and stopped_recovery_context is None
    ):
        return
    payload = status.extras.get("pending_user_interaction")
    blocked_closeout = status.extras.get("blocked_turn_closeout")
    continuation_state = status.extras.get("continuation_state")
    arbitration = interaction_arbitration_controller.arbitrate_waiting_for_user(
        pending_interaction=payload if isinstance(payload, dict) else None,
        decision_policy=str(execution.get("decision_policy") or "").strip() or None,
        submission_metadata_only=submission_metadata_only,
        publication_gate_report=publication_gate_report if isinstance(publication_gate_report, dict) else None,
        blocked_closeout=blocked_closeout if isinstance(blocked_closeout, dict) else None,
        continuation_state=continuation_state if isinstance(continuation_state, dict) else None,
    )
    status.record_interaction_arbitration(arbitration)


def _status_state(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    study_payload: dict[str, object],
    entry_mode: str | None,
    sync_runtime_summary: bool = True,
    include_progress_projection: bool = True,
) -> StudyRuntimeStatus:
    router = _router_module()
    execution = router._execution_payload(study_payload, profile=profile)
    explicit_runtime_backend_id = runtime_backend_contract.explicit_runtime_backend_id(execution)
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
    managed_runtime_backend = router._managed_runtime_backend_for_execution(
        execution,
        profile=profile,
        runtime_root=runtime_root,
    )
    if managed_runtime_backend is not None:
        execution = dict(execution)
        execution.setdefault("runtime_backend_id", getattr(managed_runtime_backend, "BACKEND_ID", ""))
        execution.setdefault("runtime_backend", getattr(managed_runtime_backend, "BACKEND_ID", ""))
        execution.setdefault("runtime_engine_id", getattr(managed_runtime_backend, "ENGINE_ID", ""))
    quest_runtime = quest_state.inspect_quest_runtime(quest_root)
    quest_exists = quest_runtime.quest_exists
    quest_status = StudyRuntimeStatus._normalize_quest_status_field(quest_runtime.quest_status)
    if quest_status in _LIVE_QUEST_STATUSES and managed_runtime_backend is not None:
        runtime_liveness_audit = router._inspect_quest_live_execution(
            runtime_root=runtime_root,
            quest_id=quest_id,
            runtime_backend=managed_runtime_backend,
        )
        quest_runtime = quest_runtime.with_runtime_liveness_audit(runtime_liveness_audit).with_bash_session_audit(
            dict(runtime_liveness_audit.get("bash_session_audit") or {})
        )
        quest_status = StudyRuntimeStatus._normalize_quest_status_field(quest_runtime.quest_status)
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
    result = StudyRuntimeStatus(
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
    submission_metadata_only_manual_finish = manual_finish_state["submission_metadata_only_manual_finish"]
    task_intake_yields_to_submission_closeout = manual_finish_state["task_intake_yields_to_submission_closeout"]
    manual_hold_task_intake = manual_finish_state["manual_hold_task_intake"]
    bundle_only_manual_finish = manual_finish_state["bundle_only_manual_finish"]
    manual_finish_compatibility_guard = manual_finish_state["manual_finish_compatibility_guard"]
    submission_metadata_only_wait = manual_finish_state["submission_metadata_only_wait"]
    _record_continuation_state_if_present(status=result, quest_root=quest_root)
    _record_blocked_closeout_if_present(status=result, quest_root=quest_root)
    _record_pending_user_interaction_if_required(
        status=result,
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id=quest_id,
        publication_gate_report=publication_gate_report,
        runtime_backend=managed_runtime_backend,
    )
    _record_interaction_arbitration_if_required(
        status=result,
        quest_root=quest_root,
        execution=execution,
        submission_metadata_only=submission_metadata_only_wait,
        publication_gate_report=publication_gate_report,
    )

    def _finalize_result() -> StudyRuntimeStatus:
        if quest_runtime.runtime_liveness_audit is not None or quest_runtime.bash_session_audit is not None:
            router._record_quest_runtime_audits(status=result, quest_runtime=quest_runtime)
        _record_runtime_recovery_lifecycle_if_required(result)
        router._record_autonomous_runtime_notice_if_required(
            status=result,
            runtime_root=runtime_root,
            launch_report_path=launch_report_path,
        )
        _record_execution_owner_guard(status=result, quest_root=quest_root)
        _record_supervisor_tick_audit(status=result, study_root=study_root)
        _record_runtime_health_dominance(
            status=result,
            study_root=study_root,
            study_id=study_id,
            quest_id=quest_id,
            recorded_at=router._utc_now(),
        )
        if not result.should_refresh_startup_hydration_while_blocked():
            result.extras.pop("runtime_escalation_ref", None)
        else:
            runtime_escalation_ref = study_runtime_protocol.read_runtime_escalation_record_ref(quest_root=quest_root)
            if runtime_escalation_ref is not None:
                result.record_runtime_escalation_ref(runtime_escalation_ref)
        if sync_runtime_summary:
            _sync_runtime_summary_if_needed(
                status=result,
                runtime_context=runtime_context,
            )
        _refresh_runtime_supervision_from_status_if_needed(
            status=result,
            study_root=study_root,
            runtime_context=runtime_context,
            router=router,
            sync_runtime_summary=sync_runtime_summary,
        )
        _record_runtime_event(
            status=result,
            runtime_context=runtime_context,
            runtime_backend=managed_runtime_backend,
        )
        _record_family_orchestration_companion(
            status=result,
            study_root=study_root,
            runtime_context=runtime_context,
        )
        _record_mds_worker_activity(result)
        _record_auto_runtime_parked_projection(result)
        result.extras["study_truth_snapshot"] = study_truth_kernel.derive_truth_snapshot_from_status_payload(
            study_root=study_root,
            study_id=study_id,
            status_payload=result.to_dict(),
            recorded_at=router._utc_now(),
        )
        from med_autoscience.controllers import study_control_plane_kernel

        result.extras["control_plane_snapshot"] = study_control_plane_kernel.build_control_plane_snapshot(
            result.to_dict()
        )
        if include_progress_projection:
            from med_autoscience.controllers import study_progress as study_progress_controller

            result.record_progress_projection(
                study_progress_controller.build_study_progress_projection(
                    profile=profile,
                    study_id=study_id,
                    study_root=study_root,
                    status_payload=result,
                    entry_mode=entry_mode,
                )
            )
        return result

    if explicit_runtime_backend_id is not None and managed_runtime_backend is None:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STUDY_EXECUTION_RUNTIME_BACKEND_UNBOUND,
        )
        return _finalize_result()

    if managed_runtime_backend is None:
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
        if publication_gate_report is not None and str(publication_gate_report.get("status") or "").strip() != "clear":
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.STUDY_COMPLETION_PUBLISHABILITY_GATE_BLOCKED,
            )
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

    startup_contract_validation = study_runtime_protocol.validate_startup_contract_resolution(
        startup_contract=router._build_startup_contract(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            study_payload=study_payload,
            execution=execution,
        )
    )
    result.record_startup_contract_validation(startup_contract_validation.to_dict())
    if startup_contract_validation.status is not study_runtime_protocol.StartupContractValidationStatus.CLEAR:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STARTUP_CONTRACT_RESOLUTION_FAILED,
        )
        return _finalize_result()

    if (
        manual_finish_compatibility_guard
        and (not task_intake_releases_manual_finish_parking or task_intake_yields_to_submission_closeout)
        and quest_status not in _LIVE_QUEST_STATUSES
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
        audit_status = router._record_quest_runtime_audits(status=result, quest_runtime=quest_runtime)
        controller_owned_finalize_parking = _is_controller_owned_finalize_parking(result)
        human_review_milestone_parking = _is_human_review_milestone_parking(
            result,
            study_root=study_root,
        )
        if _user_pause_contract_without_live_worker(result, audit_status=audit_status):
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_USER_PAUSED_REQUIRES_EXPLICIT_WAKEUP,
            )
            return _finalize_result()
        if _runtime_health_requires_explicit_resume(status=result, study_root=study_root, study_id=study_id, quest_id=quest_id):
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_STOPPED_REQUIRES_EXPLICIT_RERUN,
            )
            return _finalize_result()
        if _record_existing_controller_work_unit_evidence_adoption(status=result, study_root=study_root) is not None:
            result.set_decision(
                StudyRuntimeDecision.NOOP,
                StudyRuntimeReason.CONTROLLER_WORK_UNIT_EVIDENCE_ADOPTED,
            )
            return _finalize_result()
        if _should_park_delivered_or_redriven_package_without_live_worker(
            result, study_root=study_root, audit_status=audit_status, manual_finish_compatibility_guard=manual_finish_compatibility_guard
        ):
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
            )
            return _finalize_result()
        if human_review_milestone_parking and audit_status is not quest_state.QuestRuntimeLivenessStatus.LIVE:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_PARKED_ON_UNCHANGED_FINALIZE_STATE,
            )
            return _finalize_result()
        if audit_status is quest_state.QuestRuntimeLivenessStatus.UNKNOWN:
            if manual_finish_compatibility_guard and (
                not task_intake_releases_manual_finish_parking or task_intake_yields_to_submission_closeout
            ):
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
                )
            elif _stale_progress_without_live_bash_sessions(result) or _live_worker_missing_active_run_id(result):
                _set_running_quest_recovery_decision(
                    status=result,
                    execution=execution,
                )
            else:
                _set_running_quest_recovery_decision(
                    status=result,
                    execution=execution,
                )
        elif audit_status is quest_state.QuestRuntimeLivenessStatus.LIVE:
            if manual_finish_compatibility_guard and (
                not task_intake_releases_manual_finish_parking or task_intake_yields_to_submission_closeout
            ):
                result.set_decision(
                    StudyRuntimeDecision.PAUSE,
                    StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
                )
            elif _publication_gate_requires_live_runtime_reroute(
                publication_gate_report,
                status=result,
            ):
                if execution.get("auto_resume") is True:
                    result.set_decision(
                        StudyRuntimeDecision.RESUME,
                        StudyRuntimeReason.QUEST_DRIFTING_INTO_WRITE_WITHOUT_GATE_APPROVAL,
                    )
                else:
                    result.set_decision(
                        StudyRuntimeDecision.BLOCKED,
                        StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED,
                    )
            elif _publication_gate_allows_live_runtime_write_stage_resume(
                status=result,
                publication_gate_report=publication_gate_report,
            ):
                if execution.get("auto_resume") is True:
                    result.set_decision(
                        StudyRuntimeDecision.RESUME,
                        StudyRuntimeReason.QUEST_STALE_DECISION_AFTER_WRITE_STAGE_READY,
                    )
                else:
                    result.set_decision(
                        StudyRuntimeDecision.BLOCKED,
                        StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED,
                    )
            elif not result.startup_boundary_allows_compute_stage:
                result.set_decision(
                    StudyRuntimeDecision.PAUSE,
                    StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RUNNING_QUEST,
                )
            elif not result.runtime_reentry_allows_runtime_entry:
                result.set_decision(
                    StudyRuntimeDecision.PAUSE,
                    StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RUNNING_QUEST,
                )
            else:
                result.set_decision(
                    StudyRuntimeDecision.NOOP,
                    StudyRuntimeReason.QUEST_ALREADY_RUNNING,
                )
        elif controller_owned_finalize_parking:
            if submission_metadata_only_manual_finish:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
                )
                return _finalize_result()
            interaction_arbitration = result.extras.get("interaction_arbitration")
            if isinstance(interaction_arbitration, dict):
                classification = str(interaction_arbitration.get("classification") or "").strip()
                action = str(interaction_arbitration.get("action") or "").strip()
                if classification == "external_input_required" and action == "block":
                    result.set_decision(
                        StudyRuntimeDecision.BLOCKED,
                        StudyRuntimeReason.QUEST_WAITING_FOR_EXTERNAL_INPUT,
                    )
                    return _finalize_result()
            if _controller_decision_requires_human_confirmation(study_root=study_root) or _publication_supervisor_requires_human_confirmation(result):
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_PARKED_ON_UNCHANGED_FINALIZE_STATE,
                )
            elif not result.startup_boundary_allows_compute_stage:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
                )
            elif not result.runtime_reentry_allows_runtime_entry:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME,
                )
            elif execution.get("auto_resume") is True:
                result.set_decision(
                    StudyRuntimeDecision.RESUME,
                    StudyRuntimeReason.QUEST_PARKED_ON_UNCHANGED_FINALIZE_STATE,
                )
            else:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED,
                )
        elif not result.startup_boundary_allows_compute_stage:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
            )
        elif not result.runtime_reentry_allows_runtime_entry:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME,
            )
        elif execution.get("auto_resume") is True:
            result.set_decision(
                StudyRuntimeDecision.RESUME,
                StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_NO_LIVE_SESSION,
            )
        else:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED,
            )
        return _finalize_result()

    if quest_status in _RESUMABLE_QUEST_STATUSES:
        if _user_pause_contract_without_live_worker(result):
            from med_autoscience.controllers.study_runtime_execution_parts import (
                runtime_events as runtime_execution_events,
            )

            repaired_human_takeover = runtime_execution_events.repair_legacy_human_takeover_user_pause_contract(
                quest_root=quest_root,
                source="legacy_human_takeover_escalation_repair",
            )
            if repaired_human_takeover is not None:
                result._record_dict_extra("human_takeover_contract", repaired_human_takeover)
                result = _status_state(
                    profile=profile,
                    study_id=study_id,
                    study_root=study_root,
                    study_payload=study_payload,
                    entry_mode=entry_mode,
                    sync_runtime_summary=sync_runtime_summary,
                    include_progress_projection=include_progress_projection,
                )
                result._record_dict_extra("human_takeover_contract", repaired_human_takeover)
                quest_status = result.quest_status
            else:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_USER_PAUSED_REQUIRES_EXPLICIT_WAKEUP,
                )
                return _finalize_result()
        if quest_status not in _RESUMABLE_QUEST_STATUSES:
            return _finalize_result()
        if _user_pause_contract_without_live_worker(result):
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_USER_PAUSED_REQUIRES_EXPLICIT_WAKEUP,
            )
            return _finalize_result()
        if _should_park_delivered_package_without_live_worker(result, study_root=study_root) and not task_intake_releases_manual_finish_parking:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
            )
            return _finalize_result()
        if (
            (submission_metadata_only_manual_finish or bundle_only_manual_finish)
            and not task_intake_releases_manual_finish_parking
        ):
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
            )
            return _finalize_result()
        if not result.startup_boundary_allows_compute_stage:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
            )
            return _finalize_result()
        if not result.runtime_reentry_allows_runtime_entry:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME,
            )
            return _finalize_result()
        if execution.get("auto_resume") is True:
            resumable_reason = {
                StudyRuntimeQuestStatus.PAUSED: StudyRuntimeReason.QUEST_PAUSED,
            }.get(quest_status, StudyRuntimeReason.QUEST_INITIALIZED_WAITING_TO_START)
            result.set_decision(
                StudyRuntimeDecision.RESUME,
                resumable_reason,
            )
        else:
            blocked_reason = {
                StudyRuntimeQuestStatus.PAUSED: StudyRuntimeReason.QUEST_PAUSED_BUT_AUTO_RESUME_DISABLED,
            }.get(quest_status, StudyRuntimeReason.QUEST_INITIALIZED_BUT_AUTO_RESUME_DISABLED)
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                blocked_reason,
            )
        return _finalize_result()

    if quest_status == StudyRuntimeQuestStatus.STOPPED:
        if _user_pause_contract_without_live_worker(result):
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_USER_PAUSED_REQUIRES_EXPLICIT_WAKEUP,
            )
            return _finalize_result()
        if submission_metadata_only_manual_finish or bundle_only_manual_finish:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
            )
            return _finalize_result()
        stopped_recovery_context = _stopped_controller_owned_auto_recovery_context(
            status=result,
            quest_root=quest_root,
            publication_gate_report=publication_gate_report,
        )
        interaction_arbitration = result.extras.get("interaction_arbitration")
        if (
            isinstance(stopped_recovery_context, dict)
            and str(stopped_recovery_context.get("recovery_mode") or "").strip() == "controller_guard"
        ):
            post_clear_continuation = _publication_gate_allows_post_clear_runtime_continuation(publication_gate_report)
            if not result.startup_boundary_allows_compute_stage:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
                )
            elif not result.runtime_reentry_allows_runtime_entry:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME,
                )
            elif execution.get("auto_resume") is True:
                result.set_decision(
                    StudyRuntimeDecision.RESUME,
                    (
                        StudyRuntimeReason.QUEST_STALE_DECISION_AFTER_WRITE_STAGE_READY
                        if post_clear_continuation
                        else StudyRuntimeReason.QUEST_STOPPED_BY_CONTROLLER_GUARD
                    ),
                )
            else:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_STOPPED_BUT_AUTO_RESUME_DISABLED,
                )
            return _finalize_result()
        if stopped_recovery_context is not None and isinstance(interaction_arbitration, dict):
            classification = str(interaction_arbitration.get("classification") or "").strip()
            action = str(interaction_arbitration.get("action") or "").strip()
            if action == "resume" and (
                classification != "invalid_blocking"
                or _stopped_invalid_blocking_auto_resume_allowed(stopped_recovery_context=stopped_recovery_context)
            ):
                if not result.startup_boundary_allows_compute_stage:
                    result.set_decision(
                        StudyRuntimeDecision.BLOCKED,
                        StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
                    )
                elif not result.runtime_reentry_allows_runtime_entry:
                    result.set_decision(
                        StudyRuntimeDecision.BLOCKED,
                        StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME,
                    )
                elif execution.get("auto_resume") is True:
                    resume_reason = {
                        "submission_metadata_only": StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
                        "premature_completion_request": (
                            StudyRuntimeReason.QUEST_COMPLETION_REQUESTED_BEFORE_PUBLICATION_GATE_CLEAR
                        ),
                        "invalid_blocking": StudyRuntimeReason.QUEST_WAITING_ON_INVALID_BLOCKING,
                    }.get(classification, StudyRuntimeReason.QUEST_WAITING_ON_INVALID_BLOCKING)
                    result.set_decision(
                        StudyRuntimeDecision.RESUME,
                        resume_reason,
                    )
                else:
                    blocked_reason = (
                        StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA_BUT_AUTO_RESUME_DISABLED
                        if classification == "submission_metadata_only"
                        else StudyRuntimeReason.QUEST_STOPPED_BUT_AUTO_RESUME_DISABLED
                    )
                    result.set_decision(
                        StudyRuntimeDecision.BLOCKED,
                        blocked_reason,
                    )
                return _finalize_result()
            if classification == "external_input_required":
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_WAITING_FOR_EXTERNAL_INPUT,
                )
                return _finalize_result()
        if (
            isinstance(stopped_recovery_context, dict)
            and str(stopped_recovery_context.get("recovery_mode") or "").strip() == "managed_auto_continuation"
        ):
            if not result.startup_boundary_allows_compute_stage:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
                )
            elif not result.runtime_reentry_allows_runtime_entry:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME,
                )
            elif execution.get("auto_resume") is True:
                result.set_decision(
                    StudyRuntimeDecision.RESUME,
                    StudyRuntimeReason.QUEST_WAITING_ON_INVALID_BLOCKING,
                )
            else:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_STOPPED_BUT_AUTO_RESUME_DISABLED,
                )
            return _finalize_result()
        if (
            task_intake_releases_manual_finish_parking
            and not task_intake_yields_to_submission_closeout
            and _task_intake_override_allows_stopped_auto_resume(
            quest_root=quest_root
        )
        ):
            if not result.startup_boundary_allows_compute_stage:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
                )
            elif not result.runtime_reentry_allows_runtime_entry:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME,
                )
            elif execution.get("auto_resume") is True:
                result.set_decision(
                    StudyRuntimeDecision.RESUME,
                    StudyRuntimeReason.QUEST_WAITING_ON_INVALID_BLOCKING,
                )
            else:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_STOPPED_BUT_AUTO_RESUME_DISABLED,
                )
            return _finalize_result()
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_STOPPED_REQUIRES_EXPLICIT_RERUN,
        )
        return _finalize_result()

    if quest_status == StudyRuntimeQuestStatus.WAITING_FOR_USER:
        if submission_metadata_only_wait and submission_metadata_only_manual_finish:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
            )
            return _finalize_result()
        interaction_arbitration = result.extras.get("interaction_arbitration")
        if isinstance(interaction_arbitration, dict):
            classification = str(interaction_arbitration.get("classification") or "").strip()
            action = str(interaction_arbitration.get("action") or "").strip()
            if action == "resume":
                resume_reason = {
                    "submission_metadata_only": StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
                    "premature_completion_request": (
                        StudyRuntimeReason.QUEST_COMPLETION_REQUESTED_BEFORE_PUBLICATION_GATE_CLEAR
                    ),
                    "invalid_blocking": StudyRuntimeReason.QUEST_WAITING_ON_INVALID_BLOCKING,
                    "pending_user_message_redrive": StudyRuntimeReason.QUEST_WAITING_USER_MESSAGE_REDRIVE,
                    "platform_repair_decision_redrive": (
                        StudyRuntimeReason.QUEST_WAITING_PLATFORM_REPAIR_REDRIVE
                    ),
                }.get(classification, StudyRuntimeReason.QUEST_WAITING_ON_INVALID_BLOCKING)
                result.set_decision(
                    StudyRuntimeDecision.RESUME,
                    resume_reason,
                )
                return _finalize_result()
            if classification == "external_input_required":
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_WAITING_FOR_EXTERNAL_INPUT,
                )
                return _finalize_result()
        if submission_metadata_only_wait:
            result.set_decision(
                StudyRuntimeDecision.RESUME,
                StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
            )
            return _finalize_result()
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_WAITING_FOR_USER,
        )
        return _finalize_result()

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


__all__ = [name for name in globals() if not name.startswith("__")]
