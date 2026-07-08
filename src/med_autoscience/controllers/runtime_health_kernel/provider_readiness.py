from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable


MappingReader = Callable[[object], dict[str, Any]]
TextReader = Callable[[object], str | None]
BoolReader = Callable[[object], bool | None]

HANDOFF_KEYS = (
    "opl_current_control_state_handoff",
    "opl_current_control_state",
    "current_control_state",
)


def provider_readiness_payload(
    payload: Mapping[str, Any],
    *,
    mapping: MappingReader,
) -> dict[str, Any]:
    readiness = mapping(payload.get("provider_readiness"))
    if readiness:
        return readiness
    for key in HANDOFF_KEYS:
        candidate = mapping(mapping(payload.get(key)).get("provider_readiness"))
        if candidate:
            return candidate
    return dict(payload)


def provider_readiness_from_status_payload(
    status_payload: Mapping[str, Any],
    *,
    mapping: MappingReader,
) -> dict[str, Any]:
    for key in HANDOFF_KEYS:
        candidate = mapping(mapping(status_payload.get(key)).get("provider_readiness"))
        if candidate:
            return candidate
    return {}


def recovered_supervisor_tick(
    payload: Mapping[str, Any],
    *,
    mapping: MappingReader,
    text: TextReader,
    bool_value: BoolReader,
) -> bool:
    status = text(payload.get("supervisor_tick_status")) or text(payload.get("status"))
    if status not in {"fresh", "ok"}:
        return False
    readiness = provider_readiness_payload(payload, mapping=mapping)
    provider_ready = bool_value(readiness.get("provider_ready"))
    worker_ready = bool_value(readiness.get("worker_ready"))
    source_current = bool_value(readiness.get("managed_worker_source_current"))
    if source_current is None:
        source_current = bool_value(readiness.get("worker_source_current"))
    return provider_ready is True and worker_ready is True and source_current is True
