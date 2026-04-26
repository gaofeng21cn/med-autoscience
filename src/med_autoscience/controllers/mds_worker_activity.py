from __future__ import annotations

from typing import Any, Mapping


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def normalize_activity(status_payload: Mapping[str, Any]) -> dict[str, Any]:
    quest_status = _text(status_payload.get("quest_status"))
    reason = _text(status_payload.get("reason")) or _text(status_payload.get("runtime_reason"))
    runtime_liveness_audit = _mapping(status_payload.get("runtime_liveness_audit"))
    liveness = _text(status_payload.get("runtime_liveness_status")) or _text(runtime_liveness_audit.get("status"))
    notice = _mapping(status_payload.get("autonomous_runtime_notice"))
    monitoring_url = _text(notice.get("browser_url"))
    active_run_id = (
        _text(status_payload.get("active_run_id"))
        or _text(notice.get("active_run_id"))
        or _text(runtime_liveness_audit.get("active_run_id"))
    )
    if quest_status == "running" and liveness == "live":
        activity_state = "running"
        heartbeat_state = "live"
    elif quest_status == "running" and reason == "quest_marked_running_but_no_live_session":
        activity_state = "recovering"
        heartbeat_state = "missing_live_session"
    elif quest_status in {"stopped", "completed"}:
        activity_state = "stopped"
        heartbeat_state = "inactive"
    else:
        activity_state = "unknown"
        heartbeat_state = liveness or "unknown"
    return {
        "worker": "MDS",
        "activity_state": activity_state,
        "heartbeat_state": heartbeat_state,
        "quest_status": quest_status,
        "active_run_id": active_run_id,
        "monitoring_url": monitoring_url,
        "reason": reason,
    }
