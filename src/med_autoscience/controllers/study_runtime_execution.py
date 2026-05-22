from __future__ import annotations

from importlib import import_module
import json
from pathlib import Path
from typing import Any

from med_autoscience import study_runtime_analysis_bundle as analysis_bundle_controller
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol
from med_autoscience.controllers import runtime_health_kernel, study_control_plane_kernel

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
from .progress_projection import (
    StudyCompletionSyncResult,
    StudyRuntimeAnalysisBundleResult,
    StudyRuntimeAuditStatus,
    StudyRuntimeBindingAction,
    StudyRuntimeDaemonStep,
    StudyRuntimeDecision,
    StudyRuntimeInteractionArbitration,
    StudyRuntimeOverlayResult,
    StudyRuntimePartialQuestRecoveryResult,
    StudyRuntimeQuestStatus,
    StudyRuntimeReason,
    ProgressProjectionStatus,
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
    "_execute_relaunch_stopped_runtime_decision",
    "_execute_resume_runtime_decision",
    "_execute_runtime_decision",
    "_persist_runtime_artifacts",
    "_refresh_runtime_read_models_after_runtime_decision_override",
    "_record_autonomous_runtime_notice_if_required",
    "_run_runtime_preflight",
]


def _router_module():
    return import_module("med_autoscience.controllers.study_runtime_router")


def _should_run_startup_hydration_for_resume(*, status: ProgressProjectionStatus) -> bool:
    return _action_family_dispatch._should_run_startup_hydration_for_resume(status=status)


def _execute_relaunch_stopped_runtime_decision(
    *,
    status: ProgressProjectionStatus,
    context: StudyRuntimeExecutionContext,
) -> StudyRuntimeExecutionOutcome:
    return _action_family_dispatch._execute_relaunch_stopped_runtime_decision(
        status=status,
        context=context,
        router_module=_router_module,
    )


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
    status: ProgressProjectionStatus,
) -> None:
    explicit_rerun_request = (
        status.decision is StudyRuntimeDecision.BLOCKED
        and status.reason
        in {
            StudyRuntimeReason.QUEST_STOPPED_REQUIRES_EXPLICIT_RERUN,
            StudyRuntimeReason.QUEST_EXISTS_WITH_NON_RESUMABLE_STATE,
        }
    )
    explicit_terminal_resume_request = (
        status.decision is StudyRuntimeDecision.RESUME
        and status.reason is StudyRuntimeReason.QUEST_WAITING_ON_INVALID_BLOCKING
    )
    controller_authorized_redrive = _is_controller_authorized_stopped_redrive(status)
    if (
        not (explicit_rerun_request or explicit_terminal_resume_request or controller_authorized_redrive)
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


def _refresh_runtime_read_models_after_runtime_decision_override(
    *,
    status: ProgressProjectionStatus,
    context: StudyRuntimeExecutionContext,
) -> None:
    status.extras["runtime_health_snapshot"] = runtime_health_kernel.derive_runtime_health_snapshot_from_status_payload(
        study_root=context.study_root,
        study_id=context.study_id,
        quest_id=context.quest_id,
        status_payload=status.to_dict(),
        recorded_at=_router_module()._utc_now(),
    )
    status.extras["runtime_health_epoch"] = status.extras["runtime_health_snapshot"].get("runtime_health_epoch")
    status.extras["control_plane_snapshot"] = study_control_plane_kernel.build_control_plane_snapshot(status.to_dict())


def _is_controller_authorized_stopped_redrive(status: ProgressProjectionStatus) -> bool:
    if (
        status.decision is not StudyRuntimeDecision.RESUME
        or status.reason is not StudyRuntimeReason.QUEST_WAITING_PLATFORM_REPAIR_REDRIVE
    ):
        return False
    interaction_arbitration = status.extras.get("interaction_arbitration")
    if not isinstance(interaction_arbitration, dict):
        return False
    return (
        str(interaction_arbitration.get("classification") or "").strip()
        in {
            "controller_work_unit_pending_redrive",
            "domain_transition_runtime_redrive",
        }
        and str(interaction_arbitration.get("action") or "").strip() == StudyRuntimeDecision.RESUME.value
    )


def _enable_explicit_user_wakeup_if_requested(
    *,
    status: ProgressProjectionStatus,
    context: StudyRuntimeExecutionContext,
) -> None:
    if _active_explicit_resume_barrier_can_handoff_to_opl(status):
        wakeup_record = _runtime_events.record_explicit_user_wakeup(
            quest_root=context.quest_root,
            source=context.source,
        )
        if wakeup_record is None:
            return
        status._record_dict_extra("explicit_user_wakeup", wakeup_record)
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_WAITING_OPL_RUNTIME_OWNER_ROUTE,
        )
        _record_opl_runtime_owner_route_handoff_projection(
            status=status,
            wakeup_record=wakeup_record,
        )
        return
    if (
        status.decision is StudyRuntimeDecision.BLOCKED
        and status.reason is StudyRuntimeReason.QUEST_WAITING_OPL_RUNTIME_OWNER_ROUTE
        and status.quest_status is StudyRuntimeQuestStatus.WAITING_FOR_USER
    ):
        wakeup_record = _record_explicit_user_wakeup_projection(status=status, context=context)
        if wakeup_record is None:
            _record_opl_runtime_owner_route_handoff_projection(
                status=status,
                wakeup_record={
                    "runtime_state_path": str(context.quest_root / ".ds" / "runtime_state.json"),
                    "source": context.source,
                },
            )
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_WAITING_OPL_RUNTIME_OWNER_ROUTE,
        )
        return
    if (
        status.decision is StudyRuntimeDecision.BLOCKED
        and status.reason is StudyRuntimeReason.QUEST_WAITING_FOR_USER
        and status.quest_status is StudyRuntimeQuestStatus.WAITING_FOR_USER
    ):
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
        wakeup_record = _record_explicit_user_wakeup_projection(status=status, context=context)
        if wakeup_record is None:
            return
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_WAITING_OPL_RUNTIME_OWNER_ROUTE,
        )
        return
    if (
        status.decision is StudyRuntimeDecision.BLOCKED
        and status.reason is StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA
        and status.quest_status is StudyRuntimeQuestStatus.WAITING_FOR_USER
        and _explicit_wakeup_can_release_submission_metadata_projection(status)
    ):
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
        wakeup_record = _record_explicit_user_wakeup_projection(status=status, context=context)
        if wakeup_record is None:
            return
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_WAITING_OPL_RUNTIME_OWNER_ROUTE,
        )
        return
    if (
        status.decision is StudyRuntimeDecision.RESUME
        and status.reason is StudyRuntimeReason.QUEST_WAITING_PLATFORM_REPAIR_REDRIVE
        and status.quest_status is StudyRuntimeQuestStatus.WAITING_FOR_USER
    ):
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
        wakeup_record = _record_explicit_user_wakeup_projection(status=status, context=context)
        if wakeup_record is None:
            return
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_WAITING_OPL_RUNTIME_OWNER_ROUTE,
        )
        return
    if (
        status.decision is StudyRuntimeDecision.BLOCKED
        and status.reason is StudyRuntimeReason.QUEST_STOPPED_REQUIRES_EXPLICIT_RERUN
        and status.quest_status is StudyRuntimeQuestStatus.STOPPED
    ):
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
        if wakeup_record is None:
            return
        status._record_dict_extra("explicit_user_wakeup", wakeup_record)
        if wakeup_record.get("handoff_kind") == "opl_runtime_owner_route":
            status.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_WAITING_OPL_RUNTIME_OWNER_ROUTE,
            )
            _record_opl_runtime_owner_route_handoff_projection(
                status=status,
                wakeup_record=wakeup_record,
            )
            return
        status.set_decision(
            StudyRuntimeDecision.RELAUNCH_STOPPED,
            StudyRuntimeReason.QUEST_STOPPED_EXPLICIT_RELAUNCH_REQUESTED,
        )
        return
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
    if wakeup_record is None:
        return
    status._record_dict_extra("explicit_user_wakeup", wakeup_record)
    if wakeup_record.get("handoff_kind") == "opl_runtime_owner_route":
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_WAITING_OPL_RUNTIME_OWNER_ROUTE,
        )
        _record_opl_runtime_owner_route_handoff_projection(
            status=status,
            wakeup_record=wakeup_record,
        )
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


def _active_explicit_resume_barrier_can_handoff_to_opl(status: ProgressProjectionStatus) -> bool:
    if (
        status.decision is not StudyRuntimeDecision.BLOCKED
        or status.reason is not StudyRuntimeReason.QUEST_USER_PAUSED_REQUIRES_EXPLICIT_WAKEUP
        or status.quest_status is not StudyRuntimeQuestStatus.ACTIVE
    ):
        return False
    try:
        runtime_liveness = status.runtime_liveness_audit_record
    except KeyError:
        runtime_liveness = None
    if runtime_liveness is not None and runtime_liveness.status is StudyRuntimeAuditStatus.LIVE:
        return False
    try:
        continuation_state = status.continuation_state
    except KeyError:
        continuation_state = None
    if continuation_state is not None and continuation_state.active_run_id is not None:
        return False
    if status._resolved_active_run_id() is not None:
        return False
    snapshot = status.extras.get("runtime_health_snapshot")
    if not isinstance(snapshot, dict):
        return False
    canonical_action = str(snapshot.get("canonical_runtime_action") or "").strip()
    if canonical_action != "await_explicit_resume":
        return False
    observed_state = snapshot.get("observed_quest_state")
    observed_reason = (
        str(observed_state.get("reason") or "").strip()
        if isinstance(observed_state, dict)
        else ""
    )
    if observed_reason and observed_reason != StudyRuntimeReason.QUEST_USER_PAUSED_REQUIRES_EXPLICIT_WAKEUP.value:
        return False
    return True


def _record_explicit_user_wakeup_projection(
    *,
    status: ProgressProjectionStatus,
    context: StudyRuntimeExecutionContext,
) -> dict[str, Any] | None:
    wakeup_record = _runtime_events.record_explicit_user_wakeup(
        quest_root=context.quest_root,
        source=context.source,
    )
    if wakeup_record is None:
        return None
    status._record_dict_extra("explicit_user_wakeup", wakeup_record)
    _record_opl_runtime_owner_route_handoff_projection(
        status=status,
        wakeup_record=wakeup_record,
    )
    return wakeup_record


def _explicit_wakeup_can_release_submission_metadata_projection(
    status: ProgressProjectionStatus,
) -> bool:
    interaction_arbitration = status.extras.get("interaction_arbitration")
    if isinstance(interaction_arbitration, dict):
        classification = str(interaction_arbitration.get("classification") or "").strip()
        action = str(interaction_arbitration.get("action") or "").strip()
        if action == "resume" and classification in {
            "blocked_closeout_owner_redrive",
            "controller_work_unit_pending_redrive",
            "platform_repair_decision_redrive",
            "pending_user_message_redrive",
            "invalid_blocking",
        }:
            return True
    truth = status.extras.get("study_truth_snapshot")
    if isinstance(truth, dict):
        return str(truth.get("canonical_next_action") or "").strip() == "resume_same_study_line"
    return False


def _record_opl_runtime_owner_route_handoff_projection(
    *,
    status: ProgressProjectionStatus,
    wakeup_record: dict[str, Any],
) -> None:
    previous_continuation = status.extras.get("continuation_state")
    pending_user_message_count = (
        int(previous_continuation.get("pending_user_message_count") or 0)
        if isinstance(previous_continuation, dict)
        else 0
    )
    runtime_state_path = str(wakeup_record.get("runtime_state_path") or "").strip()
    if not runtime_state_path:
        return
    owner_route_record = wakeup_record.get("owner_route_handoff")
    handoff = (
        dict(owner_route_record.get("handoff"))
        if isinstance(owner_route_record, dict) and isinstance(owner_route_record.get("handoff"), dict)
        else {}
    )
    if not handoff:
        handoff = {
            "surface_kind": "mas_runtime_owner_route_handoff",
            "domain_truth_owner": "med-autoscience",
            "queue_owner": "one-person-lab",
            "dispatch_surface": "medautosci sidecar export -> medautosci sidecar dispatch",
            "recommended_task_kind": "domain_route/reconcile-apply",
            "runtime_state_path": runtime_state_path,
            "source": wakeup_record.get("source"),
            "reason": StudyRuntimeReason.QUEST_WAITING_OPL_RUNTIME_OWNER_ROUTE.value,
            "authority_boundary": {
                "mas_writes_generic_runtime_queue": False,
                "mas_submits_runtime_chat": False,
                "mas_resumes_provider_worker": False,
                "opl_writes_mas_truth": False,
                "mas_owner_receipt_required": True,
            },
        }
    handoff.setdefault("study_id", status.study_id)
    handoff.setdefault("quest_id", status.quest_id)
    handoff.setdefault("reason", StudyRuntimeReason.QUEST_WAITING_OPL_RUNTIME_OWNER_ROUTE.value)
    status.record_interaction_arbitration(
        StudyRuntimeInteractionArbitration.from_payload(
            {
                "classification": "opl_runtime_owner_route_handoff",
                "action": "block",
                "reason_code": StudyRuntimeReason.QUEST_WAITING_OPL_RUNTIME_OWNER_ROUTE.value,
                "requires_user_input": False,
                "valid_blocking": False,
                "kind": "opl_runtime_owner_route",
                "decision_type": None,
                "source_artifact_path": None,
                "pending_user_message_count": pending_user_message_count,
                "controller_stage_note": (
                    "Explicit user wakeup surfaced a stale controller-owned wait state for the OPL runtime "
                    "owner; MAS does not enqueue runtime chat or perform provider redrive."
                ),
            }
        )
    )
    status.extras["opl_runtime_owner_route_handoff"] = {
        **handoff,
        "surface_kind": str(handoff.get("surface_kind") or "mas_runtime_owner_route_handoff"),
        "domain_truth_owner": "med-autoscience",
        "queue_owner": "one-person-lab",
        "dispatch_surface": "medautosci sidecar export -> medautosci sidecar dispatch",
        "recommended_task_kind": "domain_route/reconcile-apply",
        "reason": str(handoff.get("reason") or StudyRuntimeReason.QUEST_WAITING_OPL_RUNTIME_OWNER_ROUTE.value),
        "runtime_state_path": runtime_state_path,
        "authority_boundary": {
            "mas_writes_generic_runtime_queue": False,
            "mas_submits_runtime_chat": False,
            "mas_resumes_provider_worker": False,
            "opl_writes_mas_truth": False,
            "mas_owner_receipt_required": True,
        },
    }
    handoff_path = Path(status.study_root) / "artifacts" / "supervision" / "owner_route_handoff" / "latest.json"
    handoff_path.parent.mkdir(parents=True, exist_ok=True)
    handoff_path.write_text(
        json.dumps(
            {
                "surface_kind": "mas_runtime_owner_route_handoff_record",
                "schema_version": 1,
                "study_id": status.study_id,
                "quest_id": status.quest_id,
                "recorded_at": str(handoff.get("recorded_at") or wakeup_record.get("recorded_at") or ""),
                "source": str(wakeup_record.get("source") or handoff.get("source") or "study_runtime_execution"),
                "handoff": status.extras["opl_runtime_owner_route_handoff"],
                "queue_owner": "one-person-lab",
                "domain_truth_owner": "med-autoscience",
                "recommended_task_kind": "domain_route/reconcile-apply",
                "runtime_state_mutated": False,
                "authority_boundary": status.extras["opl_runtime_owner_route_handoff"]["authority_boundary"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
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
    status: ProgressProjectionStatus,
    context: StudyRuntimeExecutionContext,
) -> None:
    router = _router_module()
    if (
        status.decision == StudyRuntimeDecision.RESUME
        and context.source == "runtime_platform_repair"
        and status.quest_status
        in {
            StudyRuntimeQuestStatus.PAUSED,
            StudyRuntimeQuestStatus.RUNNING,
            StudyRuntimeQuestStatus.ACTIVE,
        }
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
    status: ProgressProjectionStatus,
    resume_result: dict[str, Any],
) -> dict[str, Any]:
    return _action_family_dispatch._resume_postcondition_payload(status=status, resume_result=resume_result)


def _apply_resume_postcondition(
    *,
    status: ProgressProjectionStatus,
    outcome: StudyRuntimeExecutionOutcome,
) -> bool:
    return _action_family_dispatch._apply_resume_postcondition(status=status, outcome=outcome)


def _execute_create_runtime_decision(
    *,
    status: ProgressProjectionStatus,
    context: StudyRuntimeExecutionContext,
) -> StudyRuntimeExecutionOutcome:
    return _action_family_dispatch._execute_create_runtime_decision(
        status=status,
        context=context,
        router_module=_router_module,
    )


def _execute_resume_runtime_decision(
    *,
    status: ProgressProjectionStatus,
    context: StudyRuntimeExecutionContext,
) -> StudyRuntimeExecutionOutcome:
    return _action_family_dispatch._execute_resume_runtime_decision(
        status=status,
        context=context,
        router_module=_router_module,
    )


def _execute_blocked_refresh_runtime_decision(
    *,
    status: ProgressProjectionStatus,
    context: StudyRuntimeExecutionContext,
) -> StudyRuntimeExecutionOutcome:
    return _action_family_dispatch._execute_blocked_refresh_runtime_decision(
        status=status,
        context=context,
        router_module=_router_module,
    )


def _execute_pause_runtime_decision(
    *,
    status: ProgressProjectionStatus,
    context: StudyRuntimeExecutionContext,
) -> StudyRuntimeExecutionOutcome:
    return _action_family_dispatch._execute_pause_runtime_decision(
        status=status,
        context=context,
        router_module=_router_module,
    )


def _execute_completion_runtime_decision(
    *,
    status: ProgressProjectionStatus,
    context: StudyRuntimeExecutionContext,
) -> StudyRuntimeExecutionOutcome:
    return _action_family_dispatch._execute_completion_runtime_decision(
        status=status,
        context=context,
        router_module=_router_module,
    )


def _execute_runtime_decision(
    *,
    status: ProgressProjectionStatus,
    context: StudyRuntimeExecutionContext,
) -> StudyRuntimeExecutionOutcome:
    return _action_family_dispatch._execute_runtime_decision(
        status=status,
        context=context,
        router_module=_router_module,
    )


def _record_autonomous_runtime_notice_if_required(
    *,
    status: ProgressProjectionStatus,
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


def _runtime_event_status_snapshot(status: ProgressProjectionStatus) -> dict[str, object]:
    return _receipt_materialization._runtime_event_status_snapshot(status)


def _record_transition_runtime_event(
    *,
    status: ProgressProjectionStatus,
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
    status: ProgressProjectionStatus,
    context: StudyRuntimeExecutionContext,
) -> None:
    _receipt_materialization._maybe_emit_runtime_escalation_record(
        status=status,
        context=context,
        router_module=_router_module,
    )


def _persist_runtime_artifacts(
    *,
    status: ProgressProjectionStatus,
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
