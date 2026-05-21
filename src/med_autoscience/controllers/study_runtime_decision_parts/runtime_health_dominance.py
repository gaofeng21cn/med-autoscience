from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from med_autoscience.controllers import runtime_health_kernel
from med_autoscience.controllers.study_runtime_types import (
    StudyRuntimeDecision,
    StudyRuntimeReason,
    StudyRuntimeAuditStatus,
    StudyRuntimeStatus,
    _LIVE_QUEST_STATUSES,
)


def _latest_runtime_health_snapshot(study_root: Path) -> dict[str, object]:
    path = runtime_health_kernel.runtime_health_snapshot_path(study_root=study_root)
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _runtime_health_requires_explicit_resume(
    *,
    status: StudyRuntimeStatus,
    study_root: Path,
    study_id: str,
    quest_id: str,
) -> bool:
    if status.quest_status not in _LIVE_QUEST_STATUSES:
        return False
    try:
        if status.runtime_liveness_audit_record.status is StudyRuntimeAuditStatus.LIVE:
            return False
    except KeyError:
        pass
    try:
        continuation_state = status.continuation_state
    except KeyError:
        return False
    if continuation_state.active_run_id is not None:
        return False
    if continuation_state.continuation_policy != "wait_for_user_or_resume":
        return False
    snapshot = _latest_runtime_health_snapshot(study_root)
    if snapshot.get("study_id") != study_id or snapshot.get("quest_id") != quest_id:
        return False
    return (
        snapshot.get("canonical_runtime_action") == "await_explicit_resume"
        and snapshot.get("failure_reason") == "quest_stopped_requires_explicit_rerun"
    )


def _runtime_health_requires_live_recovery(
    *,
    status: StudyRuntimeStatus,
    runtime_health_snapshot: dict[str, object],
) -> bool:
    if status.quest_status not in _LIVE_QUEST_STATUSES:
        return False
    if runtime_health_snapshot.get("canonical_runtime_action") != "recover_runtime":
        return False
    worker_liveness_state = runtime_health_snapshot.get("worker_liveness_state")
    worker_state = (
        str(worker_liveness_state.get("state") or "").strip()
        if isinstance(worker_liveness_state, dict)
        else ""
    )
    return worker_state == "activity_timeout"


def _record_autonomy_slo_status_if_present(*, status: StudyRuntimeStatus, study_root: Path) -> None:
    from med_autoscience.controllers import autonomy_ai_doctor

    payload = autonomy_ai_doctor.read_latest_slo_status(study_root=study_root)
    if isinstance(payload, dict):
        status.extras["autonomy_slo"] = dict(payload)


def _derive_runtime_health_snapshot_for_status(
    *,
    status: StudyRuntimeStatus,
    study_root: Path,
    study_id: str,
    quest_id: str,
    recorded_at: str,
) -> dict[str, object]:
    return runtime_health_kernel.derive_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        status_payload=status.to_dict(),
        recorded_at=recorded_at,
    )


def _record_runtime_recovery_lifecycle_if_required(status: StudyRuntimeStatus) -> None:
    reason = status.reason.value if status.reason is not None else ""
    decision = status.decision.value if status.decision is not None else ""
    if reason not in {
        StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_NO_LIVE_SESSION.value,
        StudyRuntimeReason.QUEST_WAITING_OPL_RUNTIME_OWNER_ROUTE.value,
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


def _record_runtime_health_dominance(
    *,
    status: StudyRuntimeStatus,
    study_root: Path,
    study_id: str,
    quest_id: str,
    recorded_at: str,
) -> None:
    _record_autonomy_slo_status_if_present(status=status, study_root=study_root)
    runtime_health_snapshot = _derive_runtime_health_snapshot_for_status(
        status=status,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        recorded_at=recorded_at,
    )
    if _runtime_health_requires_live_recovery(status=status, runtime_health_snapshot=runtime_health_snapshot):
        try:
            runtime_liveness = status.runtime_liveness_audit_record
        except KeyError:
            runtime_liveness = None
        if runtime_liveness is None or runtime_liveness.status is not StudyRuntimeAuditStatus.LIVE:
            status.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_WAITING_OPL_RUNTIME_OWNER_ROUTE,
            )
            _record_runtime_recovery_lifecycle_if_required(status)
        runtime_health_snapshot = _derive_runtime_health_snapshot_for_status(
            status=status,
            study_root=study_root,
            study_id=study_id,
            quest_id=quest_id,
            recorded_at=recorded_at,
    )
    status.extras["runtime_health_snapshot"] = runtime_health_snapshot
    status.extras["runtime_health_epoch"] = runtime_health_snapshot.get("runtime_health_epoch")


__all__ = [name for name in globals() if not name.startswith("__")]
