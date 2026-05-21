from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers import study_truth_kernel
from med_autoscience.controllers.study_runtime_decision_parts.publication_and_submission import (
    _record_auto_runtime_parked_projection,
    _record_runtime_worker_activity,
    _record_supervisor_tick_audit,
)
from med_autoscience.controllers.study_runtime_decision_parts.runtime_events.ownership_and_continuation import (
    _record_execution_owner_guard,
)
from med_autoscience.controllers.study_runtime_decision_parts.runtime_events.runtime_summary import (
    _record_family_orchestration_companion,
    _record_runtime_event,
    _sync_runtime_summary_if_needed,
)
from med_autoscience.controllers.study_runtime_decision_parts.runtime_health_dominance import (
    _record_runtime_health_dominance,
    _record_runtime_recovery_lifecycle_if_required,
)
from med_autoscience.controllers.study_runtime_decision_parts.status_finalization import (
    _refresh_runtime_supervision_from_status_if_needed,
)
from med_autoscience.controllers.study_runtime_types import StudyRuntimeStatus
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol


def finalize_status_projection_shell(
    *,
    status: StudyRuntimeStatus,
    profile,
    study_id: str,
    study_root: Path,
    quest_id: str,
    quest_root: Path,
    quest_runtime: quest_state.QuestRuntimeSnapshot,
    runtime_context: study_runtime_protocol.StudyRuntimeContext,
    runtime_backend,
    router,
    entry_mode: str | None,
    sync_runtime_summary: bool,
    include_progress_projection: bool,
) -> StudyRuntimeStatus:
    """Attach refs-only runtime/read-model projections after MAS has chosen the decision."""
    if quest_runtime.runtime_liveness_audit is not None or quest_runtime.bash_session_audit is not None:
        router._record_quest_runtime_audits(status=status, quest_runtime=quest_runtime)
    _record_runtime_recovery_lifecycle_if_required(status)
    router._record_autonomous_runtime_notice_if_required(
        status=status,
        runtime_root=runtime_context.runtime_root,
        launch_report_path=runtime_context.launch_report_path,
    )
    _record_execution_owner_guard(status=status, quest_root=quest_root)
    _record_supervisor_tick_audit(status=status, study_root=study_root)
    _record_runtime_health_dominance(
        status=status,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        recorded_at=router._utc_now(),
    )
    if not status.should_refresh_startup_hydration_while_blocked():
        status.extras.pop("runtime_escalation_ref", None)
    else:
        runtime_escalation_ref = study_runtime_protocol.read_runtime_escalation_record_ref(quest_root=quest_root)
        if runtime_escalation_ref is not None:
            status.record_runtime_escalation_ref(runtime_escalation_ref)
    if sync_runtime_summary:
        _sync_runtime_summary_if_needed(
            status=status,
            runtime_context=runtime_context,
        )
    _refresh_runtime_supervision_from_status_if_needed(
        status=status,
        study_root=study_root,
        runtime_context=runtime_context,
        router=router,
        sync_runtime_summary=sync_runtime_summary,
    )
    _record_runtime_event(
        status=status,
        runtime_context=runtime_context,
        runtime_backend=runtime_backend,
    )
    _record_family_orchestration_companion(
        status=status,
        study_root=study_root,
        runtime_context=runtime_context,
    )
    _record_runtime_worker_activity(status)
    _record_auto_runtime_parked_projection(status)
    status.extras["study_truth_snapshot"] = study_truth_kernel.derive_truth_snapshot_from_status_payload(
        study_root=study_root,
        study_id=study_id,
        status_payload=status.to_dict(),
        recorded_at=router._utc_now(),
    )
    from med_autoscience.controllers import study_control_plane_kernel

    status.extras["control_plane_snapshot"] = study_control_plane_kernel.build_control_plane_snapshot(
        status.to_dict()
    )
    if include_progress_projection:
        from med_autoscience.controllers import study_progress as study_progress_controller

        status.record_progress_projection(
            study_progress_controller.build_study_progress_projection(
                profile=profile,
                study_id=study_id,
                study_root=study_root,
                status_payload=status,
                entry_mode=entry_mode,
            )
        )
    return status


__all__ = [name for name in globals() if not name.startswith("__")]
