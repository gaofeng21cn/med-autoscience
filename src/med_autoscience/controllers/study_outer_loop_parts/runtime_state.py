from __future__ import annotations

from typing import Any


_NON_LIVE_RUNTIME_STATUSES = frozenset({"none", "not_live", "missing", "missing_live_session"})
_UNKNOWN_RUNTIME_STATUSES = frozenset({"unknown"})


def _runtime_status_text(payload: dict[str, Any], *keys: str) -> str | None:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    text = str(current or "").strip()
    return text or None


def _runtime_status_bool(payload: dict[str, Any], *keys: str) -> bool | None:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current if isinstance(current, bool) else None


def _runtime_status_has_active_run_id(status_payload: dict[str, Any]) -> bool:
    candidate_paths = (
        ("active_run_id",),
        ("continuation_state", "active_run_id"),
        ("runtime_liveness_audit", "active_run_id"),
        ("runtime_liveness_audit", "runtime_audit", "active_run_id"),
    )
    return any(
        _runtime_status_text(status_payload, *path) is not None
        for path in candidate_paths
    )


def _runtime_status_has_explicit_no_live_worker(status_payload: dict[str, Any]) -> bool:
    if _runtime_status_has_active_run_id(status_payload):
        return False
    liveness_statuses = {
        status
        for path in (
            ("runtime_liveness_status",),
            ("runtime_liveness_audit", "status"),
            ("runtime_liveness_audit", "runtime_audit", "status"),
        )
        if (status := _runtime_status_text(status_payload, *path)) is not None
    }
    if "live" in liveness_statuses:
        return False
    worker_running_values = [
        value
        for path in (
            ("worker_running",),
            ("runtime_liveness_audit", "worker_running"),
            ("runtime_liveness_audit", "runtime_audit", "worker_running"),
        )
        if (value := _runtime_status_bool(status_payload, *path)) is not None
    ]
    if True in worker_running_values:
        return False
    worker_explicitly_not_running = False in worker_running_values
    if liveness_statuses & _NON_LIVE_RUNTIME_STATUSES:
        return True
    return bool(worker_explicitly_not_running and liveness_statuses & _UNKNOWN_RUNTIME_STATUSES)


def _runtime_status_is_live(status_payload: dict[str, Any]) -> bool:
    runtime_liveness_status = str(status_payload.get("runtime_liveness_status") or "").strip()
    if runtime_liveness_status == "live":
        return True
    runtime_liveness_audit = status_payload.get("runtime_liveness_audit")
    if isinstance(runtime_liveness_audit, dict) and str(runtime_liveness_audit.get("status") or "").strip() == "live":
        return True
    if str(status_payload.get("quest_status") or "").strip() in {"active", "running"}:
        return not _runtime_status_has_explicit_no_live_worker(status_payload)
    return False


def _parked_submission_milestone_manual_finish(status_payload: dict[str, Any]) -> bool:
    reason = str(status_payload.get("reason") or "").strip()
    if reason not in {
        "quest_waiting_for_submission_metadata",
        "quest_waiting_for_submission_metadata_but_auto_resume_disabled",
    }:
        return False
    continuation_state = status_payload.get("continuation_state")
    if not isinstance(continuation_state, dict):
        return True
    if str(continuation_state.get("active_run_id") or "").strip():
        return False
    continuation_policy = str(continuation_state.get("continuation_policy") or "").strip()
    return not continuation_policy or continuation_policy == "wait_for_user_or_resume"
