from __future__ import annotations

from collections.abc import Callable
from typing import Any

from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol

from ..study_runtime_status import (
    StudyCompletionSyncResult,
    StudyRuntimeBindingAction,
    StudyRuntimeDaemonStep,
    StudyRuntimeDecision,
    StudyRuntimeOverlayResult,
    StudyRuntimePartialQuestRecoveryResult,
    StudyRuntimeQuestStatus,
    StudyRuntimeReason,
    StudyRuntimeStatus,
)
from . import runtime_events as _runtime_events
from .controller_authorization import (
    _relay_controller_decision_authorization_if_required,
    adopt_controller_work_unit_evidence_for_current_authorization,
)
from .decision_relay import (
    _LIVE_CONTROLLER_REROUTE_FORCE_RESTART_AUTO_TURN_THRESHOLD,
    _live_controller_reroute_fingerprint,
    _mark_live_controller_reroute_restart,
    _relay_controller_owned_runtime_reply_if_required,
    _should_skip_redundant_resume_for_live_domain_redrive,
    _should_force_restart_for_live_controller_reroute,
    _should_skip_redundant_resume_for_live_controller_reroute,
)
from .execution_types import StudyRuntimeExecutionContext, StudyRuntimeExecutionOutcome


def _should_run_startup_hydration_for_resume(*, status: StudyRuntimeStatus) -> bool:
    return status.runtime_reentry_gate_result.require_startup_hydration


def _resume_postcondition_payload(
    *,
    status: StudyRuntimeStatus,
    resume_result: dict[str, Any],
) -> dict[str, Any]:
    snapshot = dict(resume_result.get("snapshot") or {}) if isinstance(resume_result.get("snapshot"), dict) else {}
    interaction_arbitration = status.extras.get("interaction_arbitration")
    snapshot_status = str(snapshot.get("status") or resume_result.get("status") or "").strip() or None
    active_run_id = str(snapshot.get("active_run_id") or resume_result.get("active_run_id") or "").strip() or None
    scheduled = bool(resume_result.get("scheduled"))
    started = bool(resume_result.get("started"))
    queued = bool(resume_result.get("queued"))
    has_runtime_launch_signals = any(key in resume_result for key in ("scheduled", "started", "queued"))
    effective = (
        active_run_id is not None
        or started
        or queued
        or snapshot_status in {"running", "retrying"}
        or (snapshot_status == "active" and not has_runtime_launch_signals)
    )
    failure_mode = None
    if not effective:
        failure_mode = "no_effect"
        if has_runtime_launch_signals and snapshot_status == "active":
            failure_mode = "no_live_run_started"
        if isinstance(interaction_arbitration, dict):
            action = str(interaction_arbitration.get("action") or "").strip()
            if snapshot_status == "waiting_for_user" and action == StudyRuntimeDecision.RESUME.value:
                failure_mode = "waiting_state_preserved"
    payload = {
        "effective": effective,
        "failure_mode": failure_mode,
        "snapshot_status": snapshot_status,
        "active_run_id": active_run_id,
        "scheduled": scheduled,
        "started": started,
        "queued": queued,
    }
    for key in ("blocked_reason", "terminal_reason", "terminal_source"):
        value = str(resume_result.get(key) or "").strip()
        if value:
            payload[key] = value
    return payload


def _apply_resume_postcondition(
    *,
    status: StudyRuntimeStatus,
    outcome: StudyRuntimeExecutionOutcome,
) -> bool:
    resume_result = outcome.daemon_step(StudyRuntimeDaemonStep.RESUME)
    payload = _resume_postcondition_payload(status=status, resume_result=resume_result)
    status._record_dict_extra("resume_postcondition", payload)
    if payload["effective"]:
        return True
    status.set_decision(
        StudyRuntimeDecision.BLOCKED,
        StudyRuntimeReason.RESUME_REQUEST_FAILED,
    )
    outcome.binding_last_action = StudyRuntimeBindingAction.BLOCKED
    return False


def _restore_explicit_user_wakeup_surface(status: StudyRuntimeStatus, pre_resume_wakeup: Any) -> None:
    if "explicit_user_wakeup" in status.extras or not isinstance(pre_resume_wakeup, dict):
        return
    status._record_dict_extra("explicit_user_wakeup", pre_resume_wakeup)


def _execute_create_runtime_decision(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
    router_module: Callable[[], Any],
) -> StudyRuntimeExecutionOutcome:
    router = router_module()
    planned_decision = status.decision
    outcome = StudyRuntimeExecutionOutcome()
    create_payload = router._build_context_create_payload(context)
    startup_contract_validation = study_runtime_protocol.validate_startup_contract_resolution(
        startup_contract=dict(create_payload.get("startup_contract") or {})
    )
    status.record_startup_contract_validation(startup_contract_validation.to_dict())
    if startup_contract_validation.status is not study_runtime_protocol.StartupContractValidationStatus.CLEAR:
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STARTUP_CONTRACT_RESOLUTION_FAILED,
        )
    partial_quest_recovery = study_runtime_protocol.archive_invalid_partial_quest_root(
        quest_root=context.quest_root,
        runtime_root=context.runtime_root,
        slug=router._timestamp_slug(),
    )
    if partial_quest_recovery is not None:
        status.record_partial_quest_recovery(StudyRuntimePartialQuestRecoveryResult.from_payload(partial_quest_recovery))
    create_payload["auto_start"] = False
    if status.decision not in {StudyRuntimeDecision.CREATE_AND_START, StudyRuntimeDecision.CREATE_ONLY}:
        return outcome
    outcome.startup_payload_path = study_runtime_protocol.write_startup_payload(
        startup_payload_root=context.startup_payload_root,
        create_payload=create_payload,
        slug=router._timestamp_slug(),
    )
    try:
        create_result = router._create_quest(
            runtime_root=context.runtime_root,
            payload=create_payload,
            runtime_backend=context.runtime_backend,
        )
    except RuntimeError as exc:
        outcome.record_daemon_step(
            StudyRuntimeDaemonStep.CREATE,
            {
                "ok": False,
                "status": "unavailable",
                "error": str(exc),
            },
        )
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.CREATE_REQUEST_FAILED,
        )
        outcome.binding_last_action = StudyRuntimeBindingAction.BLOCKED
        return outcome
    outcome.record_daemon_step(StudyRuntimeDaemonStep.CREATE, create_result)
    status.update_quest_runtime(
        quest_id=create_payload["quest_id"],
        quest_root=context.quest_root,
        quest_exists=True,
        quest_status=outcome.quest_status_for_step(StudyRuntimeDaemonStep.CREATE, fallback="created"),
    )
    if context.profile.enable_medical_overlay:
        runtime_overlay_result = StudyRuntimeOverlayResult.from_payload(
            router._prepare_runtime_overlay(
                profile=context.profile,
                quest_root=context.quest_root,
            )
        )
        status.record_runtime_overlay(runtime_overlay_result)
        if not runtime_overlay_result.audit.all_roots_ready:
            status.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.RUNTIME_OVERLAY_NOT_READY,
            )
    if status.decision == StudyRuntimeDecision.BLOCKED:
        outcome.binding_last_action = StudyRuntimeBindingAction.BLOCKED
        return outcome
    hydration_result, validation_result = router._run_startup_hydration(
        quest_root=context.quest_root,
        create_payload=create_payload,
        study_root=context.study_root,
        workspace_root=context.profile.workspace_root,
    )
    status.record_startup_hydration(hydration_result, validation_result)
    if validation_result.status is not study_runtime_protocol.StartupHydrationValidationStatus.CLEAR:
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.HYDRATION_VALIDATION_FAILED,
        )
        outcome.binding_last_action = StudyRuntimeBindingAction.BLOCKED
        return outcome
    if planned_decision == StudyRuntimeDecision.CREATE_AND_START:
        try:
            resume_result = router._resume_quest(
                runtime_root=context.runtime_root,
                quest_id=status.quest_id,
                source=context.source,
                runtime_backend=context.runtime_backend,
            )
        except RuntimeError as exc:
            outcome.record_daemon_step(
                StudyRuntimeDaemonStep.RESUME,
                {
                    "ok": False,
                    "status": "unavailable",
                    "error": str(exc),
                },
            )
            status.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.RESUME_REQUEST_FAILED,
            )
            outcome.binding_last_action = StudyRuntimeBindingAction.BLOCKED
            return outcome
        outcome.record_daemon_step(StudyRuntimeDaemonStep.RESUME, resume_result)
        status.update_quest_runtime(
            quest_status=outcome.quest_status_for_step(StudyRuntimeDaemonStep.RESUME, fallback="running"),
        )
        if not _apply_resume_postcondition(status=status, outcome=outcome):
            return outcome
        outcome.binding_last_action = StudyRuntimeBindingAction.CREATE_AND_START
    else:
        outcome.binding_last_action = StudyRuntimeBindingAction.CREATE_ONLY
    return outcome


def _execute_resume_runtime_decision(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
    router_module: Callable[[], Any],
) -> StudyRuntimeExecutionOutcome:
    router = router_module()
    outcome = StudyRuntimeExecutionOutcome()
    pre_resume_wakeup = status.extras.get("explicit_user_wakeup")
    if adopt_controller_work_unit_evidence_for_current_authorization(status=status, context=context) is not None:
        status.set_decision(
            StudyRuntimeDecision.NOOP,
            StudyRuntimeReason.CONTROLLER_WORK_UNIT_EVIDENCE_ADOPTED,
        )
        outcome.binding_last_action = StudyRuntimeBindingAction.NOOP
        _restore_explicit_user_wakeup_surface(status, pre_resume_wakeup)
        return outcome
    create_payload = router._build_context_create_payload(context)
    startup_context_sync = router._sync_existing_quest_startup_context(
        runtime_root=context.runtime_root,
        quest_id=status.quest_id,
        create_payload=create_payload,
        execution=context.execution,
    )
    status.record_startup_context_sync(startup_context_sync)
    if _should_run_startup_hydration_for_resume(status=status):
        hydration_result, validation_result = router._run_startup_hydration(
            quest_root=context.quest_root,
            create_payload=create_payload,
            study_root=context.study_root,
            workspace_root=context.profile.workspace_root,
        )
        status.record_startup_hydration(hydration_result, validation_result)
        if validation_result.status is not study_runtime_protocol.StartupHydrationValidationStatus.CLEAR:
            status.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.HYDRATION_VALIDATION_FAILED,
            )
            outcome.binding_last_action = StudyRuntimeBindingAction.BLOCKED
            _restore_explicit_user_wakeup_surface(status, pre_resume_wakeup)
            return outcome
    _relay_controller_decision_authorization_if_required(status=status, context=context)
    if "controller_work_unit_evidence_adoption" in status.extras:
        status.set_decision(
            StudyRuntimeDecision.NOOP,
            StudyRuntimeReason.CONTROLLER_WORK_UNIT_EVIDENCE_ADOPTED,
        )
        outcome.binding_last_action = StudyRuntimeBindingAction.NOOP
        _restore_explicit_user_wakeup_surface(status, pre_resume_wakeup)
        return outcome
    force_live_controller_reroute_restart = _should_force_restart_for_live_controller_reroute(
        status=status,
        context=context,
    )
    if force_live_controller_reroute_restart:
        same_fingerprint_auto_turn_count = int(
            quest_state.load_runtime_state(context.quest_root).get("same_fingerprint_auto_turn_count") or 0
        )
        pause_result = router._pause_quest(
            runtime_root=context.runtime_root,
            quest_id=status.quest_id,
            source=context.source,
            runtime_backend=context.runtime_backend,
        )
        outcome.record_daemon_step(StudyRuntimeDaemonStep.PAUSE, pause_result)
        status.update_quest_runtime(
            quest_status=outcome.quest_status_for_step(StudyRuntimeDaemonStep.PAUSE, fallback="paused"),
        )
        status.extras["controller_reroute_restart"] = {
            "forced": True,
            "threshold": _LIVE_CONTROLLER_REROUTE_FORCE_RESTART_AUTO_TURN_THRESHOLD,
            "fingerprint": _live_controller_reroute_fingerprint(status=status),
            "same_fingerprint_auto_turn_count": same_fingerprint_auto_turn_count,
        }
        _mark_live_controller_reroute_restart(
            status=status,
            context=context,
            same_fingerprint_auto_turn_count=same_fingerprint_auto_turn_count,
        )
    _relay_controller_owned_runtime_reply_if_required(status=status, context=context)
    if _should_skip_redundant_resume_for_live_domain_redrive(status=status):
        outcome.binding_last_action = StudyRuntimeBindingAction.NOOP
        _restore_explicit_user_wakeup_surface(status, pre_resume_wakeup)
        return outcome
    if _should_skip_redundant_resume_for_live_controller_reroute(status=status) and not force_live_controller_reroute_restart:
        outcome.binding_last_action = StudyRuntimeBindingAction.NOOP
        return outcome
    try:
        resume_result = router._resume_quest(
            runtime_root=context.runtime_root,
            quest_id=status.quest_id,
            source=context.source,
            runtime_backend=context.runtime_backend,
        )
    except RuntimeError as exc:
        outcome.record_daemon_step(
            StudyRuntimeDaemonStep.RESUME,
            {
                "ok": False,
                "status": "unavailable",
                "error": str(exc),
            },
        )
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.RESUME_REQUEST_FAILED,
        )
        outcome.binding_last_action = StudyRuntimeBindingAction.BLOCKED
        _restore_explicit_user_wakeup_surface(status, pre_resume_wakeup)
        return outcome
    outcome.record_daemon_step(StudyRuntimeDaemonStep.RESUME, resume_result)
    status.update_quest_runtime(
        quest_status=outcome.quest_status_for_step(StudyRuntimeDaemonStep.RESUME, fallback="running"),
    )
    if not _apply_resume_postcondition(status=status, outcome=outcome):
        _restore_explicit_user_wakeup_surface(status, pre_resume_wakeup)
        return outcome
    outcome.binding_last_action = StudyRuntimeBindingAction.RESUME
    _restore_explicit_user_wakeup_surface(status, pre_resume_wakeup)
    return outcome


def _execute_blocked_refresh_runtime_decision(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
    router_module: Callable[[], Any],
) -> StudyRuntimeExecutionOutcome:
    router = router_module()
    outcome = StudyRuntimeExecutionOutcome(binding_last_action=StudyRuntimeBindingAction.BLOCKED)
    create_payload = router._build_context_create_payload(context)
    startup_contract_validation = study_runtime_protocol.validate_startup_contract_resolution(
        startup_contract=dict(create_payload.get("startup_contract") or {})
    )
    status.record_startup_contract_validation(startup_contract_validation.to_dict())
    if startup_contract_validation.status is not study_runtime_protocol.StartupContractValidationStatus.CLEAR:
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STARTUP_CONTRACT_RESOLUTION_FAILED,
        )
        return outcome
    startup_context_sync = router._sync_existing_quest_startup_context(
        runtime_root=context.runtime_root,
        quest_id=status.quest_id,
        create_payload=create_payload,
        execution=context.execution,
    )
    status.record_startup_context_sync(startup_context_sync)
    hydration_result, validation_result = router._run_startup_hydration(
        quest_root=context.quest_root,
        create_payload=create_payload,
        study_root=context.study_root,
        workspace_root=context.profile.workspace_root,
    )
    status.record_startup_hydration(hydration_result, validation_result)
    if validation_result.status is not study_runtime_protocol.StartupHydrationValidationStatus.CLEAR:
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.HYDRATION_VALIDATION_FAILED,
        )
    return outcome


def _execute_pause_runtime_decision(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
    router_module: Callable[[], Any],
) -> StudyRuntimeExecutionOutcome:
    router = router_module()
    outcome = StudyRuntimeExecutionOutcome(binding_last_action=StudyRuntimeBindingAction.PAUSE)
    try:
        pause_result = router._pause_quest(
            runtime_root=context.runtime_root,
            quest_id=status.quest_id,
            source=context.source,
            runtime_backend=context.runtime_backend,
        )
    except RuntimeError as exc:
        postcondition = _runtime_events.pause_runtime_state_postcondition(
            quest_root=context.quest_root,
            error=str(exc),
        )
        status._record_dict_extra("pause_postcondition", postcondition)
        pause_result = _runtime_events.pause_failure_result_from_postcondition(postcondition)
        outcome.record_daemon_step(StudyRuntimeDaemonStep.PAUSE, pause_result)
        if postcondition["effective"]:
            status.update_quest_runtime(
                quest_status=outcome.quest_status_for_step(
                    StudyRuntimeDaemonStep.PAUSE,
                    fallback=status.quest_status.value if status.quest_status is not None else "paused",
                )
            )
            if status.reason is StudyRuntimeReason.HUMAN_TAKEOVER_REQUESTED:
                human_takeover_contract = _runtime_events.record_human_takeover_contract_after_pause(
                    quest_root=context.quest_root,
                    source=context.source,
                )
                if human_takeover_contract is not None:
                    status._record_dict_extra("human_takeover_contract", human_takeover_contract)
            return outcome
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.PAUSE_REQUEST_FAILED,
        )
        outcome.binding_last_action = StudyRuntimeBindingAction.BLOCKED
        return outcome
    outcome.record_daemon_step(StudyRuntimeDaemonStep.PAUSE, pause_result)
    status.update_quest_runtime(
        quest_status=outcome.quest_status_for_step(StudyRuntimeDaemonStep.PAUSE, fallback="paused"),
    )
    clearance = _runtime_events.clear_stale_platform_repair_redrive_after_pause(
        quest_root=context.quest_root,
        source=context.source,
    )
    if clearance is not None:
        status._record_dict_extra("platform_repair_redrive_clearance", clearance)
    if status.reason is StudyRuntimeReason.HUMAN_TAKEOVER_REQUESTED:
        human_takeover_contract = _runtime_events.record_human_takeover_contract_after_pause(
            quest_root=context.quest_root,
            source=context.source,
        )
        if human_takeover_contract is not None:
            status._record_dict_extra("human_takeover_contract", human_takeover_contract)
    return outcome


def _execute_completion_runtime_decision(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
    router_module: Callable[[], Any],
) -> StudyRuntimeExecutionOutcome:
    router = router_module()
    outcome = StudyRuntimeExecutionOutcome()
    if status.decision == StudyRuntimeDecision.PAUSE_AND_COMPLETE:
        pause_result = router._pause_quest(
            runtime_root=context.runtime_root,
            quest_id=status.quest_id,
            source=context.source,
            runtime_backend=context.runtime_backend,
        )
        outcome.record_daemon_step(StudyRuntimeDaemonStep.PAUSE, pause_result)
        status.update_quest_runtime(
            quest_status=outcome.quest_status_for_step(StudyRuntimeDaemonStep.PAUSE, fallback="paused"),
        )
    completion_sync = StudyCompletionSyncResult.from_payload(
        router._sync_study_completion(
            runtime_root=context.runtime_root,
            quest_id=status.quest_id,
            completion_state=context.completion_state,
            source=context.source,
            runtime_backend=context.runtime_backend,
        )
    )
    outcome.record_daemon_step(StudyRuntimeDaemonStep.COMPLETION_SYNC, completion_sync.to_dict())
    status.record_completion_sync(completion_sync)
    status.update_quest_runtime(
        quest_status=completion_sync.snapshot_status_or("completed"),
    )
    status.set_decision(
        StudyRuntimeDecision.COMPLETED,
        StudyRuntimeReason.STUDY_COMPLETION_SYNCED,
    )
    outcome.binding_last_action = StudyRuntimeBindingAction.COMPLETED
    return outcome


def _execute_runtime_decision(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
    router_module: Callable[[], Any],
) -> StudyRuntimeExecutionOutcome:
    router = router_module()
    if status.decision in {StudyRuntimeDecision.CREATE_AND_START, StudyRuntimeDecision.CREATE_ONLY}:
        return router._execute_create_runtime_decision(status=status, context=context)
    if status.decision == StudyRuntimeDecision.RESUME:
        return router._execute_resume_runtime_decision(status=status, context=context)
    if status.decision == StudyRuntimeDecision.RELAUNCH_STOPPED:
        outcome = router._execute_resume_runtime_decision(status=status, context=context)
        if outcome.binding_last_action is StudyRuntimeBindingAction.RESUME:
            outcome.binding_last_action = StudyRuntimeBindingAction.RELAUNCH_STOPPED
        return outcome
    if status.should_refresh_startup_hydration_while_blocked():
        return router._execute_blocked_refresh_runtime_decision(status=status, context=context)
    if status.decision == StudyRuntimeDecision.PAUSE:
        return router._execute_pause_runtime_decision(status=status, context=context)
    if status.decision in {StudyRuntimeDecision.SYNC_COMPLETION, StudyRuntimeDecision.PAUSE_AND_COMPLETE}:
        return router._execute_completion_runtime_decision(status=status, context=context)
    if status.decision == StudyRuntimeDecision.COMPLETED:
        return StudyRuntimeExecutionOutcome(binding_last_action=StudyRuntimeBindingAction.COMPLETED)
    if status.decision == StudyRuntimeDecision.NOOP:
        _relay_controller_decision_authorization_if_required(status=status, context=context)
        return StudyRuntimeExecutionOutcome(binding_last_action=StudyRuntimeBindingAction.NOOP)
    if status.decision == StudyRuntimeDecision.BLOCKED:
        if adopt_controller_work_unit_evidence_for_current_authorization(status=status, context=context) is not None:
            status.set_decision(
                StudyRuntimeDecision.NOOP,
                StudyRuntimeReason.CONTROLLER_WORK_UNIT_EVIDENCE_ADOPTED,
            )
            return StudyRuntimeExecutionOutcome(binding_last_action=StudyRuntimeBindingAction.NOOP)
        return StudyRuntimeExecutionOutcome(
            binding_last_action=StudyRuntimeBindingAction.BLOCKED if status.quest_exists else None
        )
    if status.decision == StudyRuntimeDecision.LIGHTWEIGHT:
        return StudyRuntimeExecutionOutcome()
    raise ValueError(f"unsupported study runtime decision: {status.decision}")
