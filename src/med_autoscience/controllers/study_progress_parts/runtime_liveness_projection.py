from __future__ import annotations

from typing import Any

from med_autoscience.controllers.control_plane_facts import resolve_control_plane_facts


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
    payload = {
        **dict(status or {}),
        "autonomous_runtime_notice": dict(autonomous_runtime_notice or {}),
        "execution_owner_guard": dict(execution_owner_guard or {}),
        "continuation_state": dict(continuation_state or {}),
    }
    facts = resolve_control_plane_facts(payload)
    if facts.strict_live:
        return True
    if not bool((execution_owner_guard or {}).get("supervisor_only")):
        return False
    if facts.active_run_id is None:
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
    facts = resolve_control_plane_facts(status, supervisor_tick_audit=supervisor_tick_audit)
    if facts.quest_status not in {"running", "active"}:
        return False
    return facts.recovery_pending
