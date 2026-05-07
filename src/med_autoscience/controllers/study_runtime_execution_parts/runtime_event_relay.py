from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from med_autoscience.controllers import runtime_supervision as runtime_supervision_controller
from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol

from ..study_runtime_status import (
    StudyRuntimeBindingAction,
    StudyRuntimeDaemonStep,
    StudyRuntimeQuestStatus,
    StudyRuntimeReason,
    StudyRuntimeStatus,
)


def runtime_event_status_snapshot(status: StudyRuntimeStatus) -> dict[str, object]:
    runtime_liveness_audit = (
        dict(status.extras.get("runtime_liveness_audit"))
        if isinstance(status.extras.get("runtime_liveness_audit"), dict)
        else {}
    )
    runtime_audit = (
        dict(runtime_liveness_audit.get("runtime_audit"))
        if isinstance(runtime_liveness_audit.get("runtime_audit"), dict)
        else {}
    )
    continuation_state = status.extras.get("continuation_state")
    supervisor_tick_audit = status.extras.get("supervisor_tick_audit")
    return {
        "quest_status": status.quest_status.value if status.quest_status is not None else None,
        "decision": status.decision.value if status.decision is not None else None,
        "reason": status.reason.value if status.reason is not None else None,
        "active_run_id": (
            str(runtime_liveness_audit.get("active_run_id") or runtime_audit.get("active_run_id") or "").strip() or None
        ),
        "runtime_liveness_status": str(runtime_liveness_audit.get("status") or "").strip() or None,
        "worker_running": runtime_audit.get("worker_running") if isinstance(runtime_audit.get("worker_running"), bool) else None,
        "continuation_policy": (
            str(continuation_state.get("continuation_policy") or "").strip() or None
            if isinstance(continuation_state, dict)
            else None
        ),
        "continuation_anchor": (
            str(continuation_state.get("continuation_anchor") or "").strip() or None
            if isinstance(continuation_state, dict)
            else None
        ),
        "continuation_reason": (
            str(continuation_state.get("continuation_reason") or "").strip() or None
            if isinstance(continuation_state, dict)
            else None
        ),
        "supervisor_tick_status": (
            str(supervisor_tick_audit.get("status") or "").strip() or None
            if isinstance(supervisor_tick_audit, dict)
            else None
        ),
        "controller_owned_finalize_parking": False,
        "runtime_escalation_ref": (
            dict(status.extras.get("runtime_escalation_ref"))
            if isinstance(status.extras.get("runtime_escalation_ref"), dict)
            else None
        ),
    }


def runtime_event_outer_loop_input(status: StudyRuntimeStatus) -> dict[str, object]:
    snapshot = runtime_event_status_snapshot(status)
    interaction_arbitration = status.extras.get("interaction_arbitration")
    return {
        "quest_status": snapshot["quest_status"],
        "decision": snapshot["decision"],
        "reason": snapshot["reason"],
        "active_run_id": snapshot["active_run_id"],
        "runtime_liveness_status": snapshot["runtime_liveness_status"],
        "worker_running": snapshot["worker_running"],
        "supervisor_tick_status": snapshot["supervisor_tick_status"],
        "controller_owned_finalize_parking": snapshot["controller_owned_finalize_parking"],
        "interaction_action": (
            str(interaction_arbitration.get("action") or "").strip() or None
            if isinstance(interaction_arbitration, dict)
            else None
        ),
        "interaction_requires_user_input": (
            bool(interaction_arbitration.get("requires_user_input"))
            if isinstance(interaction_arbitration, dict)
            else False
        ),
        "runtime_escalation_ref": snapshot["runtime_escalation_ref"],
    }


def post_transition_quest_status(
    *,
    status: StudyRuntimeStatus,
    outcome: Any,
) -> StudyRuntimeQuestStatus | None:
    if outcome.binding_last_action is StudyRuntimeBindingAction.CREATE_AND_START:
        return StudyRuntimeQuestStatus(
            outcome.quest_status_for_step(StudyRuntimeDaemonStep.CREATE, fallback="created")
        )
    if outcome.binding_last_action in {
        StudyRuntimeBindingAction.RESUME,
        StudyRuntimeBindingAction.RELAUNCH_STOPPED,
    }:
        return StudyRuntimeQuestStatus(
            outcome.quest_status_for_step(StudyRuntimeDaemonStep.RESUME, fallback="running")
        )
    if outcome.binding_last_action is StudyRuntimeBindingAction.PAUSE:
        return StudyRuntimeQuestStatus(
            outcome.quest_status_for_step(StudyRuntimeDaemonStep.PAUSE, fallback="paused")
        )
    if outcome.binding_last_action is StudyRuntimeBindingAction.COMPLETED:
        return StudyRuntimeQuestStatus(outcome.completion_snapshot_status(fallback="completed"))
    return status.quest_status


def record_transition_runtime_event(
    *,
    status: StudyRuntimeStatus,
    context: Any,
    outcome: Any,
    router_module: Callable[[], Any],
    get_quest_session: Callable[..., dict[str, Any]],
) -> None:
    if outcome.binding_last_action not in {
        StudyRuntimeBindingAction.CREATE_AND_START,
        StudyRuntimeBindingAction.RESUME,
        StudyRuntimeBindingAction.RELAUNCH_STOPPED,
        StudyRuntimeBindingAction.PAUSE,
        StudyRuntimeBindingAction.COMPLETED,
    }:
        return
    execution = status.execution
    if (
        router_module()._managed_runtime_backend_for_execution(execution) is None
        or str(execution.get("auto_entry") or "").strip() != "on_managed_research_intent"
        or not status.quest_exists
    ):
        status.extras.pop("runtime_event_ref", None)
        status.extras.pop("runtime_event", None)
        return
    post_transition_status = post_transition_quest_status(status=status, outcome=outcome)
    status.update_quest_runtime(quest_status=post_transition_status)
    try:
        session_payload = get_quest_session(
            runtime_root=context.runtime_root,
            quest_id=status.quest_id,
            runtime_backend=context.runtime_backend,
        )
    except (RuntimeError, OSError, ValueError):
        status.extras.pop("runtime_event_ref", None)
        status.extras.pop("runtime_event", None)
        return
    runtime_event_ref = session_payload.get("runtime_event_ref")
    if isinstance(runtime_event_ref, dict):
        status.record_runtime_event_ref(runtime_event_ref)
    else:
        status.extras.pop("runtime_event_ref", None)
    runtime_event = session_payload.get("runtime_event")
    if isinstance(runtime_event, dict):
        status["runtime_event"] = dict(runtime_event)
    else:
        status.extras.pop("runtime_event", None)


def runtime_escalation_trigger_source(reason: StudyRuntimeReason | None) -> str:
    if reason in {
        StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
        StudyRuntimeReason.QUEST_PAUSED_BUT_AUTO_RESUME_DISABLED,
        StudyRuntimeReason.QUEST_INITIALIZED_BUT_AUTO_RESUME_DISABLED,
    }:
        return "startup_boundary_gate"
    if reason is StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME:
        return "runtime_reentry_gate"
    return "study_runtime_status"


def runtime_escalation_recommended_actions(reason: StudyRuntimeReason | None) -> tuple[str, ...]:
    if reason is StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME:
        return ("refresh_startup_hydration", "controller_review_required")
    if reason in {
        StudyRuntimeReason.QUEST_PAUSED_BUT_AUTO_RESUME_DISABLED,
        StudyRuntimeReason.QUEST_INITIALIZED_BUT_AUTO_RESUME_DISABLED,
    }:
        return ("refresh_startup_hydration", "controller_review_required")
    return ("refresh_startup_hydration", "controller_review_required")


def runtime_escalation_evidence_refs(status: StudyRuntimeStatus) -> tuple[str, ...]:
    evidence_refs: list[str] = []
    for key in ("startup_hydration", "startup_hydration_validation"):
        payload = status.extras.get(key)
        if not isinstance(payload, dict):
            continue
        report_path = str(payload.get("report_path") or "").strip()
        if report_path:
            evidence_refs.append(report_path)
    return tuple(evidence_refs)


def maybe_emit_runtime_escalation_record(
    *,
    status: StudyRuntimeStatus,
    context: Any,
    emitted_at: str,
) -> None:
    if not status.should_refresh_startup_hydration_while_blocked():
        return
    reason = status.reason
    if reason is None:
        return
    launch_report_path = str(context.launch_report_path)
    record = study_runtime_protocol.RuntimeEscalationRecord(
        schema_version=1,
        record_id=f"runtime-escalation::{context.study_id}::{status.quest_id}::{reason.value}::{emitted_at}",
        study_id=context.study_id,
        quest_id=status.quest_id,
        emitted_at=emitted_at,
        trigger=study_runtime_protocol.RuntimeEscalationTrigger(
            trigger_id=reason.value,
            source=runtime_escalation_trigger_source(reason),
        ),
        scope="quest",
        severity="quest",
        reason=reason.value,
        recommended_actions=runtime_escalation_recommended_actions(reason),
        evidence_refs=runtime_escalation_evidence_refs(status),
        runtime_context_refs={
            "launch_report_path": launch_report_path,
        },
        summary_ref=launch_report_path,
        artifact_path=None,
    )
    written_record = study_runtime_protocol.write_runtime_escalation_record(
        quest_root=context.quest_root,
        record=record,
    )
    status.record_runtime_escalation_ref(written_record.ref())


def materialize_runtime_supervision(
    *,
    study_root: Path,
    status_payload: dict[str, Any],
    recorded_at: str,
) -> None:
    runtime_supervision_controller.materialize_runtime_supervision(
        study_root=study_root,
        status_payload=status_payload,
        recorded_at=recorded_at,
        apply=True,
    )


def runtime_event_recorded_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
