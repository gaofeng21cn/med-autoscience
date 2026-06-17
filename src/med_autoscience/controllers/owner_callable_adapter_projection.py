from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def owner_callable_adapters(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    adapters = payload.get("owner_callable_adapters")
    if isinstance(adapters, list):
        return [dict(item) for item in adapters if isinstance(item, Mapping)]
    return []


def domain_progress_transition_requests(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    requests = payload.get("domain_progress_transition_requests")
    if isinstance(requests, list):
        return [_normalized_transition_request_record(item) for item in requests if isinstance(item, Mapping)]
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
    transition_requests = domain_progress_transition_requests(projected)
    projected.setdefault("owner_callable_adapter_count", len(adapters))
    projected.setdefault("ready_owner_callable_adapter_count", _status_count(adapters, "ready"))
    projected.setdefault("blocked_owner_callable_adapter_count", _status_count(adapters, "blocked"))
    projected.setdefault(
        "transition_request_pending_owner_callable_adapter_count",
        _status_count(adapters, "transition_request_pending"),
    )
    projected.setdefault("owner_callable_adapters", adapters)
    projected.setdefault("domain_progress_transition_request_count", len(transition_requests))
    projected.setdefault("domain_progress_transition_requests", transition_requests)
    return projected


def _normalized_transition_request_record(value: Mapping[str, Any]) -> dict[str, Any]:
    record = {key: item for key, item in dict(value).items() if item is not None}
    request = _mapping(record.get("opl_domain_progress_transition_request"))
    if request:
        record["opl_domain_progress_transition_request"] = request
    record.setdefault("surface", "mas_domain_progress_transition_request_projection")
    record.setdefault("provider_admission_pending", False)
    record.setdefault("provider_admission_requires_opl_runtime_result", True)
    record.setdefault("provider_completion_is_domain_completion", False)
    record.setdefault("mas_dispatch_authority", False)
    record.setdefault("mas_creates_owner_callable_carrier", False)
    record.setdefault("mas_creates_opl_outbox", False)
    record.setdefault("mas_creates_opl_event", False)
    record.setdefault("mas_creates_opl_stage_run", False)
    record.setdefault("target_runtime_owner", "one-person-lab")
    record.setdefault("dispatch_status", "transition_request_pending")
    return record


def _status_count(adapters: list[dict[str, Any]], status: str) -> int:
    return sum(_text(item.get("dispatch_status")) == status for item in adapters)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


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
    "domain_progress_transition_requests",
    "owner_callable_adapters",
    "with_owner_callable_adapter_projection",
]
