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
    arbitration = interaction_arbitration_controller.arbitrate_waiting_for_user(
        pending_interaction=payload if isinstance(payload, dict) else None,
        decision_policy=str(execution.get("decision_policy") or "").strip() or None,
        submission_metadata_only=submission_metadata_only,
        publication_gate_report=publication_gate_report if isinstance(publication_gate_report, dict) else None,
    )
    status.record_interaction_arbitration(arbitration)


def _record_runtime_recovery_lifecycle_if_required(status: StudyRuntimeStatus) -> None:
    reason = status.reason.value if status.reason is not None else ""
    decision = status.decision.value if status.decision is not None else ""
    if reason not in {
        StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_NO_LIVE_SESSION.value,
        StudyRuntimeReason.RUNNING_QUEST_LIVE_SESSION_AUDIT_FAILED.value,
        StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED.value,
    }:
        return
    runtime_liveness_audit = (
        dict(status.extras.get("runtime_liveness_audit") or {})
        if isinstance(status.extras.get("runtime_liveness_audit"), dict)
        else {}
    )
    active_run_id = str(runtime_liveness_audit.get("active_run_id") or "").strip() or None
    if decision == StudyRuntimeDecision.RESUME.value:
        state = "recovering"
        recent_recovery_action = "resume"
        recovery_attempt_count = 1
        next_check_reason = "confirm_recovered_live_session"
    else:
        state = "parked_requires_resume"
        recent_recovery_action = (
            "enable_auto_resume"
            if reason == StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED.value
            else "inspect_runtime_liveness"
        )
        recovery_attempt_count = 0
        next_check_reason = "recover_runtime_audit_then_resume"
    next_check_after_seconds = 300
    status.extras["runtime_recovery_lifecycle"] = {
        "state": state,
        "reason": reason,
        "decision": decision,
        "runtime_liveness_status": str(runtime_liveness_audit.get("status") or "").strip() or None,
        "active_run_id": active_run_id,
        "recovery_attempt_count": recovery_attempt_count,
        "recent_recovery_action": recent_recovery_action,
        "next_check_reason": next_check_reason,
        "next_check_after_seconds": next_check_after_seconds,
        "next_check_at": (datetime.now(timezone.utc) + timedelta(seconds=next_check_after_seconds))
        .replace(microsecond=0)
        .isoformat(),
    }


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
    task_intake_overrides_auto_manual_finish = _task_intake_overrides_auto_manual_finish_active(
        study_root=study_root,
    )
    submission_metadata_only_manual_finish = (
        quest_exists
        and not task_intake_overrides_auto_manual_finish
        and _submission_metadata_only_manual_finish_active(
            study_root=study_root,
            quest_root=quest_root,
        )
    )
    task_intake_yields_to_submission_closeout = False
    bundle_only_manual_finish = (
        quest_exists
        and _bundle_only_submission_ready_manual_finish_active(
            study_root=study_root,
            quest_root=quest_root,
        )
    )
    delivered_package_manual_finish = quest_exists and _delivered_submission_package_manual_finish_active(
        study_root=study_root,
    )
    if task_intake_overrides_auto_manual_finish and bundle_only_manual_finish:
        summary_payload = _load_json_dict(
            study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
        )
        task_intake_yields_to_submission_closeout = task_intake_yields_to_deterministic_submission_closeout(
            read_latest_task_intake(study_root=study_root),
            publishability_gate_report=None,
            evaluation_summary=summary_payload,
        )
        if not task_intake_yields_to_submission_closeout:
            bundle_only_manual_finish = False
    explicit_manual_finish_compatibility_guard = _explicit_manual_finish_compatibility_guard_active(
        study_root=study_root,
    )
    manual_finish_compatibility_guard = (
        explicit_manual_finish_compatibility_guard
        or submission_metadata_only_manual_finish
        or bundle_only_manual_finish
        or delivered_package_manual_finish
    )
    submission_metadata_only_wait = (
        quest_exists
        and quest_status == StudyRuntimeQuestStatus.WAITING_FOR_USER
        and not task_intake_overrides_auto_manual_finish
        and _waiting_submission_metadata_only(quest_root)
    )

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
        publication_gate_report = publication_gate_controller.build_gate_report(
            publication_gate_controller.build_gate_state(quest_root)
        )
        result.record_publication_supervisor_state(
            publication_gate_controller.extract_publication_supervisor_state(publication_gate_report)
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
    task_intake_yields_to_submission_closeout = task_intake_yields_to_submission_closeout or _task_intake_yields_to_submission_closeout_active(
        study_root=study_root,
        publication_gate_report=publication_gate_report,
    )
    _record_continuation_state_if_present(status=result, quest_root=quest_root)
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
        _record_runtime_recovery_lifecycle_if_required(result)
        router._record_autonomous_runtime_notice_if_required(
            status=result,
            runtime_root=runtime_root,
            launch_report_path=launch_report_path,
        )
        _record_execution_owner_guard(status=result, quest_root=quest_root)
        _record_supervisor_tick_audit(status=result, study_root=study_root)
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
        supervisor_tick_is_fresh = str(
            (result.extras.get("supervisor_tick_audit") or {}).get("status")
            if isinstance(result.extras.get("supervisor_tick_audit"), dict)
            else ""
        ).strip() == "fresh"
        status_payload_for_supervision = result.to_dict()
        runtime_facts_for_supervision = runtime_supervision_controller._runtime_facts(status_payload_for_supervision)
        quest_status_for_supervision = str(status_payload_for_supervision.get("quest_status") or "").strip()
        refreshable_runtime_supervision = bool(
            runtime_facts_for_supervision["strict_live"]
            or (
                quest_status_for_supervision in {"running", "active"}
                and runtime_supervision_controller.needs_recovery_projection(
                    status_payload_for_supervision,
                    strict_live=bool(runtime_facts_for_supervision["strict_live"]),
                )
            )
        )
        if (
            supervisor_tick_is_fresh
            and refreshable_runtime_supervision
            and _should_refresh_runtime_supervision_from_status(status=result, study_root=study_root)
        ):
            runtime_supervision_controller.materialize_runtime_supervision(
                study_root=study_root,
                status_payload=status_payload_for_supervision,
                recorded_at=router._utc_now(),
                apply=False,
            )
            _record_supervisor_tick_audit(status=result, study_root=study_root)
            if sync_runtime_summary:
                study_runtime_protocol.persist_runtime_artifacts(
                    runtime_binding_path=runtime_context.runtime_binding_path,
                    launch_report_path=runtime_context.launch_report_path,
                    runtime_root=runtime_context.runtime_root,
                    study_id=result.study_id,
                    study_root=Path(result.study_root),
                    quest_id=result.quest_id if result.quest_exists else None,
                    last_action=None,
                    status=result.to_dict(),
                    source="study_runtime_status",
                    force=False,
                    startup_payload_path=None,
                    daemon_result=None,
                    recorded_at=router._utc_now(),
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
        if quest_status == StudyRuntimeQuestStatus.COMPLETED:
            result.set_decision(
                StudyRuntimeDecision.COMPLETED,
                StudyRuntimeReason.QUEST_ALREADY_COMPLETED,
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
        and (not task_intake_overrides_auto_manual_finish or task_intake_yields_to_submission_closeout)
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
        if human_review_milestone_parking and audit_status is not quest_state.QuestRuntimeLivenessStatus.LIVE:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_PARKED_ON_UNCHANGED_FINALIZE_STATE,
            )
            return _finalize_result()
        if audit_status is quest_state.QuestRuntimeLivenessStatus.UNKNOWN:
            if manual_finish_compatibility_guard and (
                not task_intake_overrides_auto_manual_finish or task_intake_yields_to_submission_closeout
            ):
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
                )
            elif _stale_progress_without_live_bash_sessions(result):
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
                        StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_NO_LIVE_SESSION,
                    )
                else:
                    result.set_decision(
                        StudyRuntimeDecision.BLOCKED,
                        StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED,
                    )
            else:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.RUNNING_QUEST_LIVE_SESSION_AUDIT_FAILED,
                )
        elif audit_status is quest_state.QuestRuntimeLivenessStatus.LIVE:
            if manual_finish_compatibility_guard and (
                not task_intake_overrides_auto_manual_finish or task_intake_yields_to_submission_closeout
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
        if (
            (submission_metadata_only_manual_finish or bundle_only_manual_finish)
            and not task_intake_overrides_auto_manual_finish
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
            task_intake_overrides_auto_manual_finish
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
