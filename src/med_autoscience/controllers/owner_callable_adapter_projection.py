from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def owner_callable_adapters(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    adapters = payload.get("owner_callable_adapters")
    if isinstance(adapters, list):
        return [dict(item) for item in adapters if isinstance(item, Mapping)]
    legacy = payload.get("default_executor_dispatches")
    if isinstance(legacy, list):
        return [dict(item) for item in legacy if isinstance(item, Mapping)]
    return []


def adapter_count(payload: Mapping[str, Any]) -> int:
    if "owner_callable_adapter_count" in payload:
        return _int_value(payload.get("owner_callable_adapter_count"))
    return len(owner_callable_adapters(payload))


def adapter_status_count(payload: Mapping[str, Any], status: str) -> int:
    key = f"{status}_owner_callable_adapter_count"
    if key in payload:
        return _int_value(payload.get(key))
    return sum(_text(item.get("dispatch_status")) == status for item in owner_callable_adapters(payload))


def with_owner_callable_adapter_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    projected = dict(payload)
    adapters = owner_callable_adapters(projected)
    projected.setdefault("owner_callable_adapter_count", len(adapters))
    projected.setdefault("ready_owner_callable_adapter_count", _status_count(adapters, "ready"))
    projected.setdefault("blocked_owner_callable_adapter_count", _status_count(adapters, "blocked"))
    projected.setdefault(
        "transition_request_pending_owner_callable_adapter_count",
        _status_count(adapters, "transition_request_pending"),
    )
    projected.setdefault("owner_callable_adapters", adapters)
    return projected


def _status_count(adapters: list[dict[str, Any]], status: str) -> int:
    return sum(_text(item.get("dispatch_status")) == status for item in adapters)


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _int_value(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


__all__ = [
    "adapter_count",
    "adapter_status_count",
    "owner_callable_adapters",
    "with_owner_callable_adapter_projection",
]
