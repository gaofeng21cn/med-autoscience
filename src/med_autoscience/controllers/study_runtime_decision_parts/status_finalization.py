from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers import runtime_supervision as runtime_supervision_controller
from med_autoscience.controllers.study_runtime_decision_parts.publication_and_submission import (
    _record_supervisor_tick_audit,
)
from med_autoscience.controllers.study_runtime_decision_parts.runtime_events.runtime_summary import (
    _should_refresh_runtime_supervision_from_status,
)
from med_autoscience.controllers.study_runtime_types import StudyRuntimeStatus
from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol


def _refresh_runtime_supervision_from_status_if_needed(
    *,
    status: StudyRuntimeStatus,
    study_root: Path,
    runtime_context: study_runtime_protocol.StudyRuntimeContext,
    router: object,
    sync_runtime_summary: bool,
) -> None:
    supervisor_tick_status = str(
        (status.extras.get("supervisor_tick_audit") or {}).get("status")
        if isinstance(status.extras.get("supervisor_tick_audit"), dict)
        else ""
    ).strip()
    status_payload = status.to_dict()
    runtime_facts = runtime_supervision_controller._runtime_facts(status_payload)
    quest_status = str(status_payload.get("quest_status") or "").strip()
    runtime_reason = str(status_payload.get("reason") or "").strip()
    auto_continuation_recovery_pending = runtime_supervision_controller.is_auto_continuation_recovery_pending(
        status_payload,
        strict_live=bool(runtime_facts["strict_live"]),
    )
    refreshable_runtime_supervision = bool(
        runtime_facts["strict_live"]
        or runtime_reason == "quest_stopped_requires_explicit_rerun"
        or (
            quest_status in {"running", "active"}
            and runtime_supervision_controller.needs_recovery_projection(
                status_payload,
                strict_live=bool(runtime_facts["strict_live"]),
            )
        )
    )
    if not (
        (supervisor_tick_status == "fresh" or auto_continuation_recovery_pending)
        and refreshable_runtime_supervision
        and _should_refresh_runtime_supervision_from_status(status=status, study_root=study_root)
    ):
        return

    runtime_supervision_controller.materialize_runtime_supervision(
        study_root=study_root,
        status_payload=status_payload,
        recorded_at=router._utc_now(),
        apply=False,
    )
    _record_supervisor_tick_audit(status=status, study_root=study_root)
    if not sync_runtime_summary:
        return
    study_runtime_protocol.persist_runtime_artifacts(
        runtime_binding_path=runtime_context.runtime_binding_path,
        launch_report_path=runtime_context.launch_report_path,
        runtime_root=runtime_context.runtime_root,
        study_id=status.study_id,
        study_root=Path(status.study_root),
        quest_id=status.quest_id if status.quest_exists else None,
        last_action=None,
        status=status.to_dict(),
        source="study_runtime_status",
        force=False,
        startup_payload_path=None,
        daemon_result=None,
        recorded_at=router._utc_now(),
    )


__all__ = [name for name in globals() if not name.startswith("__")]
