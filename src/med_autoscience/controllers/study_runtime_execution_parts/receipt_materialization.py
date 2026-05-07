from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..study_runtime_status import StudyRuntimeBindingAction, StudyRuntimeStatus
from . import runtime_events as _runtime_events
from .execution_types import StudyRuntimeExecutionContext, StudyRuntimeExecutionOutcome


def _record_autonomous_runtime_notice_if_required(
    *,
    status: StudyRuntimeStatus,
    runtime_root: Path,
    launch_report_path: Path,
    router_module: Callable[[], Any],
    binding_last_action: StudyRuntimeBindingAction | None = None,
    active_run_id: str | None = None,
) -> None:
    _runtime_events.record_autonomous_runtime_notice_if_required(
        status=status,
        runtime_root=runtime_root,
        launch_report_path=launch_report_path,
        router_module=router_module,
        binding_last_action=binding_last_action,
        active_run_id=active_run_id,
    )


def _runtime_event_status_snapshot(status: StudyRuntimeStatus) -> dict[str, object]:
    return _runtime_events.runtime_event_status_snapshot(status)


def _record_transition_runtime_event(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
    outcome: StudyRuntimeExecutionOutcome,
    router_module: Callable[[], Any],
    get_quest_session: Callable[..., Any],
) -> None:
    _runtime_events.record_transition_runtime_event(
        status=status,
        context=context,
        outcome=outcome,
        router_module=router_module,
        get_quest_session=get_quest_session,
    )


def _maybe_emit_runtime_escalation_record(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
    router_module: Callable[[], Any],
) -> None:
    _runtime_events.maybe_emit_runtime_escalation_record(
        status=status,
        context=context,
        emitted_at=router_module()._utc_now(),
    )


def _persist_runtime_artifacts(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
    outcome: StudyRuntimeExecutionOutcome,
    force: bool,
    source: str,
    router_module: Callable[[], Any],
    get_quest_session: Callable[..., Any],
) -> None:
    router = router_module()
    recorded_at = router._utc_now()
    _record_transition_runtime_event(
        status=status,
        context=context,
        outcome=outcome,
        router_module=router_module,
        get_quest_session=get_quest_session,
    )
    _record_autonomous_runtime_notice_if_required(
        status=status,
        runtime_root=context.runtime_root,
        launch_report_path=context.launch_report_path,
        router_module=router_module,
        binding_last_action=outcome.binding_last_action,
        active_run_id=outcome.active_run_id(),
    )
    artifact_paths = router.study_runtime_protocol.persist_runtime_artifacts(
        runtime_binding_path=context.runtime_binding_path,
        launch_report_path=context.launch_report_path,
        runtime_root=context.runtime_root,
        study_id=context.study_id,
        study_root=context.study_root,
        quest_id=status.quest_id.strip() or None,
        last_action=outcome.binding_last_action.value if outcome.binding_last_action is not None else None,
        status=status.to_dict(),
        source=source,
        force=force,
        startup_payload_path=outcome.startup_payload_path,
        daemon_result=outcome.serialized_daemon_result(),
        recorded_at=recorded_at,
    )
    status.record_runtime_artifacts(
        runtime_binding_path=artifact_paths.runtime_binding_path,
        launch_report_path=artifact_paths.launch_report_path,
        startup_payload_path=artifact_paths.startup_payload_path,
    )
    _maybe_emit_runtime_escalation_record(status=status, context=context, router_module=router_module)
    if "runtime_escalation_ref" in status.extras:
        router.study_runtime_protocol.write_launch_report(
            launch_report_path=context.launch_report_path,
            status=status.to_dict(),
            source=source,
            force=force,
            startup_payload_path=outcome.startup_payload_path,
            daemon_result=outcome.serialized_daemon_result(),
            recorded_at=recorded_at,
        )
    _runtime_events.materialize_runtime_supervision(
        study_root=context.study_root,
        status_payload=status.to_dict(),
        recorded_at=recorded_at,
    )
