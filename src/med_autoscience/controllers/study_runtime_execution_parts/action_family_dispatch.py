from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
import json
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


def _materialize_fresh_domain_transition_controller_decision_if_required(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
) -> dict[str, Any] | None:
    if status.reason is not StudyRuntimeReason.DOMAIN_TRANSITION_AI_REVIEWER_RE_EVAL:
        return None
    domain_transition = status.extras.get("domain_transition")
    if not isinstance(domain_transition, dict):
        return None
    transition_unit = domain_transition.get("next_work_unit")
    transition_unit_id = str(transition_unit.get("unit_id") or "").strip() if isinstance(transition_unit, dict) else ""
    transition_action = str(domain_transition.get("controller_action") or "").strip()
    transition_type = str(domain_transition.get("decision_type") or "").strip()
    if (
        transition_type != "ai_reviewer_re_eval"
        or transition_action != "return_to_ai_reviewer_workflow"
        or not transition_unit_id
    ):
        return None
    outer_loop = import_module("med_autoscience.controllers.study_outer_loop")
    status_payload = status.to_dict()
    tick_request = outer_loop.build_runtime_watch_outer_loop_tick_request(
        study_root=context.study_root,
        status_payload=status_payload,
    )
    if not isinstance(tick_request, dict):
        status.extras["controller_decision_currentness"] = {
            "status": "skipped",
            "reason": "outer_loop_tick_request_unavailable",
        }
        return None
    if not _tick_request_matches_domain_transition(
        tick_request=tick_request,
        transition_action=transition_action,
        transition_type=transition_type,
        transition_unit_id=transition_unit_id,
    ):
        status.extras["controller_decision_currentness"] = {
            "status": "skipped",
            "reason": "outer_loop_tick_request_did_not_match_domain_transition",
            "transition_unit_id": transition_unit_id,
            "tick_work_unit_id": _work_unit_id_from_tick_request(tick_request),
            "tick_controller_actions": _controller_action_types_from_tick_request(tick_request),
        }
        return None
    if _latest_controller_decision_matches_tick_request(
        study_root=context.study_root,
        tick_request=tick_request,
    ):
        status.extras["controller_decision_currentness"] = {
            "status": "already_current",
            "work_unit_id": transition_unit_id,
            "work_unit_fingerprint": str(tick_request.get("work_unit_fingerprint") or "").strip() or None,
        }
        return None
    materialized = outer_loop.materialize_non_dispatching_outer_loop_decision(
        profile=context.profile,
        study_id=context.study_id,
        study_root=context.study_root,
        status_payload=status_payload,
        charter_ref=tick_request["charter_ref"],
        publication_eval_ref=tick_request["publication_eval_ref"],
        decision_type=str(tick_request["decision_type"]),
        route_target=str(tick_request.get("route_target") or "").strip() or None,
        route_key_question=str(tick_request.get("route_key_question") or "").strip() or None,
        route_rationale=str(tick_request.get("route_rationale") or "").strip() or None,
        source_route_key_question=str(tick_request.get("source_route_key_question") or "").strip() or None,
        work_unit_fingerprint=str(tick_request.get("work_unit_fingerprint") or "").strip() or None,
        next_work_unit=(
            dict(tick_request.get("next_work_unit"))
            if isinstance(tick_request.get("next_work_unit"), dict)
            else None
        ),
        blocking_work_units=[
            dict(item) for item in tick_request.get("blocking_work_units") or [] if isinstance(item, dict)
        ],
        requires_human_confirmation=bool(tick_request.get("requires_human_confirmation")),
        controller_actions=[
            dict(item) for item in tick_request.get("controller_actions") or [] if isinstance(item, dict)
        ],
        reason=str(tick_request.get("reason") or "").strip()
        or "fresh domain transition requires current controller authorization before runtime resume",
        source=context.source,
    )
    status.extras["controller_decision_currentness"] = {
        "status": "materialized",
        "work_unit_id": transition_unit_id,
        "work_unit_fingerprint": str(tick_request.get("work_unit_fingerprint") or "").strip() or None,
        "materialization": dict(materialized) if isinstance(materialized, dict) else {},
    }
    return dict(materialized) if isinstance(materialized, dict) else {}


def _tick_request_matches_domain_transition(
    *,
    tick_request: dict[str, Any],
    transition_action: str,
    transition_type: str,
    transition_unit_id: str,
) -> bool:
    tick_unit_id = _work_unit_id_from_tick_request(tick_request)
    if tick_unit_id != transition_unit_id:
        return False
    if transition_action not in _controller_action_types_from_tick_request(tick_request):
        return False
    fingerprint = str(tick_request.get("work_unit_fingerprint") or "").strip()
    return fingerprint == f"domain-transition::{transition_type}::{transition_unit_id}"


def _work_unit_id_from_tick_request(tick_request: dict[str, Any]) -> str | None:
    next_work_unit = tick_request.get("next_work_unit")
    if not isinstance(next_work_unit, dict):
        return None
    text = str(next_work_unit.get("unit_id") or "").strip()
    return text or None


def _controller_action_types_from_tick_request(tick_request: dict[str, Any]) -> list[str]:
    action_types: list[str] = []
    for item in tick_request.get("controller_actions") or []:
        if not isinstance(item, dict):
            continue
        action_type = str(item.get("action_type") or "").strip()
        if action_type:
            action_types.append(action_type)
    return sorted(set(action_types))


def _latest_controller_decision_matches_tick_request(
    *,
    study_root: Any,
    tick_request: dict[str, Any],
) -> bool:
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    try:
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return False
    if not isinstance(decision, dict):
        return False
    decision_actions = _controller_action_types_from_tick_request(
        {"controller_actions": decision.get("controller_actions")}
    )
    tick_actions = _controller_action_types_from_tick_request(tick_request)
    decision_unit = decision.get("next_work_unit")
    decision_unit_id = str(decision_unit.get("unit_id") or "").strip() if isinstance(decision_unit, dict) else ""
    return (
        str(decision.get("work_unit_fingerprint") or "").strip()
        == str(tick_request.get("work_unit_fingerprint") or "").strip()
        and decision_unit_id == (_work_unit_id_from_tick_request(tick_request) or "")
        and decision_actions == tick_actions
    )


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
        quest_status=outcome.quest_status_for_step(StudyRuntimeDaemonStep.CREATE, default_status="created"),
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
            quest_status=outcome.quest_status_for_step(StudyRuntimeDaemonStep.RESUME, default_status="running"),
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
    _materialize_fresh_domain_transition_controller_decision_if_required(status=status, context=context)
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
            quest_status=outcome.quest_status_for_step(StudyRuntimeDaemonStep.PAUSE, default_status="paused"),
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
        quest_status=outcome.quest_status_for_step(StudyRuntimeDaemonStep.RESUME, default_status="running"),
    )
    if not _apply_resume_postcondition(status=status, outcome=outcome):
        _restore_explicit_user_wakeup_surface(status, pre_resume_wakeup)
        return outcome
    outcome.binding_last_action = StudyRuntimeBindingAction.RESUME
    _restore_explicit_user_wakeup_surface(status, pre_resume_wakeup)
    return outcome


def _execute_relaunch_stopped_runtime_decision(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
    router_module: Callable[[], Any],
) -> StudyRuntimeExecutionOutcome:
    router = router_module()
    outcome = StudyRuntimeExecutionOutcome()
    pre_relaunch_wakeup = status.extras.get("explicit_user_wakeup")
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
            _restore_explicit_user_wakeup_surface(status, pre_relaunch_wakeup)
            return outcome
    _materialize_fresh_domain_transition_controller_decision_if_required(status=status, context=context)
    _relay_controller_decision_authorization_if_required(status=status, context=context)
    try:
        relaunch_result = router._relaunch_stopped_quest(
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
        _restore_explicit_user_wakeup_surface(status, pre_relaunch_wakeup)
        return outcome
    outcome.record_daemon_step(StudyRuntimeDaemonStep.RESUME, relaunch_result)
    status.update_quest_runtime(
        quest_status=outcome.quest_status_for_step(StudyRuntimeDaemonStep.RESUME, default_status="running"),
    )
    if not _apply_resume_postcondition(status=status, outcome=outcome):
        _restore_explicit_user_wakeup_surface(status, pre_relaunch_wakeup)
        return outcome
    outcome.binding_last_action = StudyRuntimeBindingAction.RELAUNCH_STOPPED
    _restore_explicit_user_wakeup_surface(status, pre_relaunch_wakeup)
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
                    default_status=status.quest_status.value if status.quest_status is not None else "paused",
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
        quest_status=outcome.quest_status_for_step(StudyRuntimeDaemonStep.PAUSE, default_status="paused"),
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
            quest_status=outcome.quest_status_for_step(StudyRuntimeDaemonStep.PAUSE, default_status="paused"),
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
        return router._execute_relaunch_stopped_runtime_decision(status=status, context=context)
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
        _relay_controller_decision_authorization_if_required(status=status, context=context)
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
