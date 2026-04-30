from __future__ import annotations

from typing import Any


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _status_worker_running(status: dict[str, Any]) -> bool | None:
    worker_running = status.get("worker_running")
    if isinstance(worker_running, bool):
        return worker_running
    runtime_liveness_audit = status.get("runtime_liveness_audit")
    if isinstance(runtime_liveness_audit, dict):
        runtime_audit = runtime_liveness_audit.get("runtime_audit")
        if isinstance(runtime_audit, dict) and isinstance(runtime_audit.get("worker_running"), bool):
            return bool(runtime_audit.get("worker_running"))
    return None


def live_managed_runtime_present(
    *,
    status: dict[str, Any],
    autonomous_runtime_notice: dict[str, Any],
    execution_owner_guard: dict[str, Any],
    continuation_state: dict[str, Any],
) -> bool:
    runtime_liveness_status = _non_empty_text(status.get("runtime_liveness_status"))
    active_run_id = (
        _non_empty_text(status.get("active_run_id"))
        or _non_empty_text((execution_owner_guard or {}).get("active_run_id"))
        or _non_empty_text((autonomous_runtime_notice or {}).get("active_run_id"))
        or _non_empty_text((continuation_state or {}).get("active_run_id"))
    )
    if runtime_liveness_status == "live":
        worker_running = _status_worker_running(status)
        return active_run_id is not None and worker_running is not False
    if not bool((execution_owner_guard or {}).get("supervisor_only")):
        return False
    if active_run_id is None:
        return False
    guard_reason = _non_empty_text((execution_owner_guard or {}).get("guard_reason"))
    notice_reason = _non_empty_text((autonomous_runtime_notice or {}).get("notification_reason"))
    continuation_quest_status = _non_empty_text((continuation_state or {}).get("quest_status"))
    if continuation_quest_status != "running":
        return False
    return (
        guard_reason in {"live_managed_runtime", "runtime_live"}
        or notice_reason in {"managed_runtime_live", "detected_existing_live_managed_runtime"}
    )


def runtime_recovery_pending_from_status(
    *,
    status: dict[str, Any],
    supervisor_tick_audit: dict[str, Any],
    live_managed_runtime: bool,
) -> bool:
    if live_managed_runtime:
        return False
    quest_status = _non_empty_text(status.get("quest_status"))
    if quest_status not in {"running", "active"}:
        return False
    active_run_id = (
        _non_empty_text(status.get("active_run_id"))
        or _non_empty_text(((status.get("execution_owner_guard") or {}) if isinstance(status.get("execution_owner_guard"), dict) else {}).get("active_run_id"))
        or _non_empty_text(((status.get("autonomous_runtime_notice") or {}) if isinstance(status.get("autonomous_runtime_notice"), dict) else {}).get("active_run_id"))
        or _non_empty_text(((status.get("continuation_state") or {}) if isinstance(status.get("continuation_state"), dict) else {}).get("active_run_id"))
    )
    if active_run_id is None:
        runtime_liveness_audit = status.get("runtime_liveness_audit")
        if isinstance(runtime_liveness_audit, dict):
            runtime_audit = runtime_liveness_audit.get("runtime_audit")
            active_run_id = _non_empty_text(runtime_liveness_audit.get("active_run_id")) or (
                _non_empty_text(runtime_audit.get("active_run_id")) if isinstance(runtime_audit, dict) else None
            )
    if active_run_id is not None:
        return False
    reason = _non_empty_text(status.get("reason"))
    supervisor_tick_status = _non_empty_text((supervisor_tick_audit or {}).get("status"))
    return (
        reason == "quest_marked_running_but_no_live_session"
        or supervisor_tick_status in {"missing", "stale", "invalid"}
    )
