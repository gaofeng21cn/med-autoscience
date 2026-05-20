from __future__ import annotations

if __name__ != "med_autoscience.controllers.study_runtime_decision":
    from .domain_transition_arbitration import *  # noqa: F403
    from .manual_finish_dominance import *  # noqa: F403
    from .publication_and_submission import *  # noqa: F403
    from .runtime_events import *  # noqa: F403
    from .domain_transition_status import *  # noqa: F403
    from .quest_status_decisions import *  # noqa: F403
    from .runtime_health_dominance import *  # noqa: F403
    from .status_finalization import *  # noqa: F403
    from .supervisor_state_overrides import *  # noqa: F403


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
    _record_continuation_state_if_present(status=result, quest_root=quest_root)
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
        _record_runtime_worker_activity(result)
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


__all__ = [name for name in globals() if not name.startswith("__")]
