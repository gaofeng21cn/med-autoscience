from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from . import event_log


VOLATILE_SUPERVISOR_KEYS = frozenset(
    {
        "age_seconds",
        "checked_at",
        "generated_at",
        "seconds_since_latest_recorded_at",
        "seconds_since_latest_progress",
    }
)
STABLE_RUNTIME_AUDIT_KEYS = (
    "ok",
    "status",
    "source",
    "active_run_id",
    "worker_running",
    "worker_pending",
    "stop_requested",
    "runtime_event_contract_error",
    "runtime_event_ref_contract_error",
    "liveness_guard_reason",
)
STABLE_RUNTIME_LIVENESS_AUDIT_KEYS = (
    "ok",
    "status",
    "source",
    "active_run_id",
    "runner_live",
    "bash_live",
    "stale_progress",
    "liveness_guard_reason",
    "error",
)


def text(value: object) -> str | None:
    result = str(value or "").strip()
    return result or None


def bool_value(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def read_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def stable_runtime_audit(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: payload[key] for key in STABLE_RUNTIME_AUDIT_KEYS if key in payload}


def stable_runtime_liveness_audit(payload: Mapping[str, Any]) -> dict[str, Any]:
    stable = {key: payload[key] for key in STABLE_RUNTIME_LIVENESS_AUDIT_KEYS if key in payload}
    runtime_audit = mapping(payload.get("runtime_audit"))
    if runtime_audit:
        stable["runtime_audit"] = stable_runtime_audit(runtime_audit)
    bash_session_audit = mapping(payload.get("bash_session_audit"))
    if bash_session_audit:
        stable["bash_session_audit"] = {
            key: bash_session_audit[key]
            for key in ("ok", "status", "session_count", "live_session_count", "live_session_ids")
            if key in bash_session_audit
        }
    return stable


def stable_event_payload(event_type: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    if event_type != "runtime_state_observed":
        return dict(payload)
    stable = dict(payload)
    stable.pop("observed_at", None)
    runtime_audit = mapping(stable.get("runtime_audit"))
    if runtime_audit:
        stable["runtime_audit"] = stable_runtime_audit(runtime_audit)
    liveness_audit = mapping(stable.get("runtime_liveness_audit"))
    if liveness_audit:
        stable["runtime_liveness_audit"] = stable_runtime_liveness_audit(liveness_audit)
    return stable


def event_source_signature(event_type: str, payload: Mapping[str, Any]) -> str:
    return event_log.event_source_signature(
        event_type=event_type,
        payload=payload,
        stable_event_payload=stable_event_payload,
    )


def source_signature_for_event(event: Mapping[str, Any]) -> str:
    return event_log.source_signature_for_event(
        event,
        text=text,
        mapping=mapping,
        stable_event_payload=stable_event_payload,
    )


def snapshot_source_signature(events: list[dict[str, Any]]) -> str | None:
    return event_log.snapshot_source_signature(
        events,
        source_signature_for_event=source_signature_for_event,
    )


def authority_ref(event: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "event_id": text(event.get("event_id")),
        "event_type": text(event.get("event_type")),
        "recorded_at": text(event.get("recorded_at")),
    }


def latest_event(events: Iterable[dict[str, Any]], event_type: str) -> dict[str, Any] | None:
    for event in reversed(list(events)):
        if event.get("event_type") == event_type:
            return event
    return None


def events_for(events: Iterable[dict[str, Any]], event_types: frozenset[str]) -> list[dict[str, Any]]:
    return [event for event in events if str(event.get("event_type") or "") in event_types]


def event_payload(event: Mapping[str, Any] | None) -> dict[str, Any]:
    return mapping(event.get("payload")) if event is not None else {}


def first_text(*values: object) -> str | None:
    for value in values:
        result = text(value)
        if result is not None:
            return result
    return None


def active_run_from_payload(payload: Mapping[str, Any]) -> str | None:
    return first_text(
        payload.get("active_run_id"),
        mapping(payload.get("runtime_audit")).get("active_run_id"),
        mapping(payload.get("runtime_liveness_audit")).get("active_run_id"),
        mapping(payload.get("autonomous_runtime_notice")).get("active_run_id"),
    )


def last_known_run_id(events: list[dict[str, Any]], *, strict_live: bool, active_run_id: str | None) -> str | None:
    if strict_live:
        return active_run_id
    for event in reversed(events):
        payload = event_payload(event)
        candidate = active_run_from_payload(payload)
        if candidate is not None:
            return candidate
    return None


def latest_runtime_observation(events: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    event = latest_event(events, "runtime_state_observed")
    return event, event_payload(event)


def latest_supervisor_state(events: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    event = latest_event(events, "supervisor_tick")
    payload = event_payload(event)
    status = first_text(payload.get("supervisor_tick_status"), payload.get("status"))
    stable_payload = {
        key: item
        for key, item in payload.items()
        if key not in VOLATILE_SUPERVISOR_KEYS
    }
    return event, {
        "status": status or "unknown",
        "required": bool_value(payload.get("required")),
        "latest_recorded_at": first_text(payload.get("latest_recorded_at"), payload.get("recorded_at")),
        "source_signature": event_source_signature("supervisor_tick", stable_payload),
    }
