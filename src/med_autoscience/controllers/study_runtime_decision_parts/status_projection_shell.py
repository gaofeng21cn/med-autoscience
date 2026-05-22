from __future__ import annotations

from pathlib import Path

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
from med_autoscience.controllers.study_runtime_decision_parts.status_projection_shell_parts.read_model_projection_assembly import (
    attach_status_read_model_projections,
)
from med_autoscience.controllers.study_runtime_types import ProgressProjectionStatus
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol


def finalize_status_projection_shell(
    *,
    status: ProgressProjectionStatus,
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
) -> ProgressProjectionStatus:
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
    attach_status_read_model_projections(
        status=status,
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        recorded_at=router._utc_now(),
        entry_mode=entry_mode,
        include_progress_projection=include_progress_projection,
    )
    return status


__all__ = [name for name in globals() if not name.startswith("__")]
