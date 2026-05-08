from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

from med_autoscience import study_runtime_analysis_bundle as analysis_bundle_controller
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol

from .study_runtime_execution_parts import action_family_dispatch as _action_family_dispatch
from .study_runtime_execution_parts import receipt_materialization as _receipt_materialization
from .study_runtime_execution_parts import runtime_events as _runtime_events
from .study_runtime_execution_parts.controller_authorization import (
    _relay_controller_decision_authorization_if_required,
    adopt_controller_work_unit_evidence_for_current_authorization,
)
from .study_runtime_execution_parts.decision_relay import (
    _LIVE_CONTROLLER_REROUTE_FORCE_RESTART_AUTO_TURN_THRESHOLD,
    _append_route_context_to_message,
    _controller_owned_interaction_reply_message,
    _live_controller_reroute_fingerprint,
    _mark_live_controller_reroute_restart,
    _relay_controller_owned_runtime_reply_if_required,
    _should_force_restart_for_live_controller_reroute,
    _should_skip_redundant_resume_for_live_controller_reroute,
)
from .study_runtime_execution_parts.execution_types import (
    StudyRuntimeExecutionContext,
    StudyRuntimeExecutionOutcome,
)
from .study_runtime_status import (
    StudyCompletionSyncResult,
    StudyRuntimeAnalysisBundleResult,
    StudyRuntimeBindingAction,
    StudyRuntimeDaemonStep,
    StudyRuntimeDecision,
    StudyRuntimeOverlayResult,
    StudyRuntimePartialQuestRecoveryResult,
    StudyRuntimeQuestStatus,
    StudyRuntimeReason,
    StudyRuntimeStatus,
    _LIVE_QUEST_STATUSES,
)
from .study_runtime_transport import _get_quest_session

__all__ = [
    "StudyRuntimeExecutionContext",
    "StudyRuntimeExecutionOutcome",
    "_build_context_create_payload",
    "_build_execution_context",
    "_enable_explicit_user_wakeup_if_requested",
    "_enable_explicit_stopped_relaunch_if_requested",
    "_execute_blocked_refresh_runtime_decision",
    "_execute_completion_runtime_decision",
    "_execute_create_runtime_decision",
    "_execute_pause_runtime_decision",
    "_execute_resume_runtime_decision",
    "_execute_runtime_decision",
    "_persist_runtime_artifacts",
    "_record_autonomous_runtime_notice_if_required",
    "_run_runtime_preflight",
]


def _router_module():
    return import_module("med_autoscience.controllers.study_runtime_router")


def _should_run_startup_hydration_for_resume(*, status: StudyRuntimeStatus) -> bool:
    return _action_family_dispatch._should_run_startup_hydration_for_resume(status=status)


def _build_execution_context(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    study_payload: dict[str, Any],
    source: str,
) -> StudyRuntimeExecutionContext:
    router = _router_module()
    execution = router._execution_payload(study_payload, profile=profile)
    quest_id = str(execution.get("quest_id") or study_id).strip() or study_id
    runtime_context = study_runtime_protocol.resolve_study_runtime_context(
        profile=profile,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
    )
    runtime_backend = router._managed_runtime_backend_for_execution(
        execution,
        profile=profile,
        runtime_root=runtime_context.runtime_root,
    ) or router._default_managed_runtime_backend()
    completion_state = router._study_completion_state(study_root=study_root)
    return StudyRuntimeExecutionContext(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        study_payload=study_payload,
        execution=execution,
        quest_id=quest_id,
        runtime_context=runtime_context,
        runtime_backend=runtime_backend,
        completion_state=completion_state,
        source=source,
    )


def _enable_explicit_stopped_relaunch_if_requested(
    *,
    status: StudyRuntimeStatus,
) -> None:
    if (
        status.decision is not StudyRuntimeDecision.BLOCKED
        or status.reason
        not in {
            StudyRuntimeReason.QUEST_STOPPED_REQUIRES_EXPLICIT_RERUN,
            StudyRuntimeReason.QUEST_EXISTS_WITH_NON_RESUMABLE_STATE,
        }
        or status.quest_status
        not in {
            StudyRuntimeQuestStatus.STOPPED,
            StudyRuntimeQuestStatus.FAILED,
        }
    ):
        return
    if not status.startup_boundary_allows_compute_stage:
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
        )
        return
    if not status.runtime_reentry_allows_runtime_entry:
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME,
        )
        return
    status.set_decision(
        StudyRuntimeDecision.RELAUNCH_STOPPED,
        StudyRuntimeReason.QUEST_STOPPED_EXPLICIT_RELAUNCH_REQUESTED,
    )


def _enable_explicit_user_wakeup_if_requested(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
) -> None:
    if (
        status.decision is not StudyRuntimeDecision.BLOCKED
        or status.reason is not StudyRuntimeReason.QUEST_USER_PAUSED_REQUIRES_EXPLICIT_WAKEUP
        or status.quest_status
        not in {
            StudyRuntimeQuestStatus.PAUSED,
            StudyRuntimeQuestStatus.STOPPED,
        }
    ):
        return
    if not status.startup_boundary_allows_compute_stage:
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
        )
        return
    if not status.runtime_reentry_allows_runtime_entry:
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME,
        )
        return
    wakeup_record = _runtime_events.record_explicit_user_wakeup(
        quest_root=context.quest_root,
        source=context.source,
    )
    status._record_dict_extra("explicit_user_wakeup", wakeup_record)
    if wakeup_record is None:
        return
    if status.quest_status is StudyRuntimeQuestStatus.STOPPED:
        status.set_decision(
            StudyRuntimeDecision.RELAUNCH_STOPPED,
            StudyRuntimeReason.QUEST_STOPPED_EXPLICIT_RELAUNCH_REQUESTED,
        )
    else:
        status.set_decision(
            StudyRuntimeDecision.RESUME,
            StudyRuntimeReason.QUEST_PAUSED,
        )


def _build_context_create_payload(context: StudyRuntimeExecutionContext) -> dict[str, Any]:
    router = _router_module()
    return router._build_create_payload(
        profile=context.profile,
        study_id=context.study_id,
        study_root=context.study_root,
        study_payload=context.study_payload,
        execution=context.execution,
    )


def _run_runtime_preflight(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
) -> None:
    router = _router_module()
    if (
        status.decision == StudyRuntimeDecision.RESUME
        and context.source == "runtime_platform_repair"
        and status.quest_status is StudyRuntimeQuestStatus.PAUSED
        and _runtime_events.has_delivered_human_package_surface(context.study_root)
    ):
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
        )
        _runtime_events.record_auto_runtime_parked_projection(status)
        return
    if status.decision in {
        StudyRuntimeDecision.CREATE_AND_START,
        StudyRuntimeDecision.CREATE_ONLY,
        StudyRuntimeDecision.RESUME,
    }:
        analysis_bundle_result = StudyRuntimeAnalysisBundleResult.from_payload(
            analysis_bundle_controller.ensure_study_runtime_analysis_bundle()
        )
        status.record_analysis_bundle(analysis_bundle_result)
        if not analysis_bundle_result.ready:
            status.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.STUDY_RUNTIME_ANALYSIS_BUNDLE_NOT_READY,
            )
        elif status.runtime_reentry_requires_managed_skill_audit and not context.profile.enable_medical_overlay:
            status.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.MANAGED_SKILL_AUDIT_NOT_AVAILABLE,
            )
        elif context.profile.enable_medical_overlay and status.decision == StudyRuntimeDecision.RESUME:
            runtime_overlay_result = StudyRuntimeOverlayResult.from_payload(
                router._prepare_runtime_overlay(
                    profile=context.profile,
                    quest_root=context.quest_root,
                )
            )
            status.record_runtime_overlay(runtime_overlay_result)
            if not runtime_overlay_result.audit.all_roots_ready:
                if status.reason is StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_NO_LIVE_SESSION:
                    status.set_decision(
                        StudyRuntimeDecision.BLOCKED,
                        StudyRuntimeReason.RUNNING_QUEST_LIVE_SESSION_AUDIT_FAILED,
                    )
                    return
                status.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.RUNTIME_OVERLAY_NOT_READY,
                )
    elif context.profile.enable_medical_overlay and status.quest_exists:
        should_prepare_existing_overlay = status.quest_status not in _LIVE_QUEST_STATUSES
        runtime_overlay_payload = (
            router._prepare_runtime_overlay(
                profile=context.profile,
                quest_root=context.quest_root,
            )
            if should_prepare_existing_overlay
            else {"audit": router._audit_runtime_overlay(profile=context.profile, quest_root=context.quest_root)}
        )
        runtime_overlay_result = StudyRuntimeOverlayResult.from_payload(runtime_overlay_payload)
        status.record_runtime_overlay(runtime_overlay_result)
        if should_prepare_existing_overlay and not runtime_overlay_result.audit.all_roots_ready:
            status.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.RUNTIME_OVERLAY_NOT_READY,
            )
        if (
            status.quest_status in _LIVE_QUEST_STATUSES
            and status.decision
            in {
                StudyRuntimeDecision.NOOP,
                StudyRuntimeDecision.PAUSE,
                StudyRuntimeDecision.PAUSE_AND_COMPLETE,
            }
        ):
            if not runtime_overlay_result.audit.all_roots_ready:
                runtime_overlay_result = StudyRuntimeOverlayResult.from_payload(
                    router._prepare_runtime_overlay(
                        profile=context.profile,
                        quest_root=context.quest_root,
                    )
                )
                status.record_runtime_overlay(runtime_overlay_result)
            if not runtime_overlay_result.audit.all_roots_ready:
                status.set_decision(
                    StudyRuntimeDecision.PAUSE,
                    StudyRuntimeReason.RUNTIME_OVERLAY_AUDIT_FAILED_FOR_RUNNING_QUEST,
                )


def _resume_postcondition_payload(
    *,
    status: StudyRuntimeStatus,
    resume_result: dict[str, Any],
) -> dict[str, Any]:
    return _action_family_dispatch._resume_postcondition_payload(status=status, resume_result=resume_result)


def _apply_resume_postcondition(
    *,
    status: StudyRuntimeStatus,
    outcome: StudyRuntimeExecutionOutcome,
) -> bool:
    return _action_family_dispatch._apply_resume_postcondition(status=status, outcome=outcome)


def _execute_create_runtime_decision(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
) -> StudyRuntimeExecutionOutcome:
    return _action_family_dispatch._execute_create_runtime_decision(
        status=status,
        context=context,
        router_module=_router_module,
    )


def _execute_resume_runtime_decision(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
) -> StudyRuntimeExecutionOutcome:
    return _action_family_dispatch._execute_resume_runtime_decision(
        status=status,
        context=context,
        router_module=_router_module,
    )


def _execute_blocked_refresh_runtime_decision(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
) -> StudyRuntimeExecutionOutcome:
    return _action_family_dispatch._execute_blocked_refresh_runtime_decision(
        status=status,
        context=context,
        router_module=_router_module,
    )


def _execute_pause_runtime_decision(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
) -> StudyRuntimeExecutionOutcome:
    return _action_family_dispatch._execute_pause_runtime_decision(
        status=status,
        context=context,
        router_module=_router_module,
    )


def _execute_completion_runtime_decision(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
) -> StudyRuntimeExecutionOutcome:
    return _action_family_dispatch._execute_completion_runtime_decision(
        status=status,
        context=context,
        router_module=_router_module,
    )


def _execute_runtime_decision(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
) -> StudyRuntimeExecutionOutcome:
    return _action_family_dispatch._execute_runtime_decision(
        status=status,
        context=context,
        router_module=_router_module,
    )


def _record_autonomous_runtime_notice_if_required(
    *,
    status: StudyRuntimeStatus,
    runtime_root: Path,
    launch_report_path: Path,
    binding_last_action: StudyRuntimeBindingAction | None = None,
    active_run_id: str | None = None,
) -> None:
    _receipt_materialization._record_autonomous_runtime_notice_if_required(
        status=status,
        runtime_root=runtime_root,
        launch_report_path=launch_report_path,
        router_module=_router_module,
        binding_last_action=binding_last_action,
        active_run_id=active_run_id,
    )


def _runtime_event_status_snapshot(status: StudyRuntimeStatus) -> dict[str, object]:
    return _receipt_materialization._runtime_event_status_snapshot(status)


def _record_transition_runtime_event(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
    outcome: StudyRuntimeExecutionOutcome,
) -> None:
    _receipt_materialization._record_transition_runtime_event(
        status=status,
        context=context,
        outcome=outcome,
        router_module=_router_module,
        get_quest_session=_get_quest_session,
    )


def _maybe_emit_runtime_escalation_record(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
) -> None:
    _receipt_materialization._maybe_emit_runtime_escalation_record(
        status=status,
        context=context,
        router_module=_router_module,
    )


def _persist_runtime_artifacts(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
    outcome: StudyRuntimeExecutionOutcome,
    force: bool,
    source: str,
) -> None:
    _receipt_materialization._persist_runtime_artifacts(
        status=status,
        context=context,
        outcome=outcome,
        force=force,
        source=source,
        router_module=_router_module,
        get_quest_session=_get_quest_session,
    )
