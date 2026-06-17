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
    return _transition_request_records_from_owner_callable_adapters(owner_callable_adapters(payload))


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


def _transition_request_records_from_owner_callable_adapters(
    adapters: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for adapter in adapters:
        request = _mapping(adapter.get("opl_domain_progress_transition_request")) or _mapping(
            _mapping(adapter.get("prompt_contract")).get("opl_domain_progress_transition_request")
        )
        record = {
            **_transition_request_identity_fields(adapter),
            "surface": "mas_domain_progress_transition_request_projection",
            "projection_source": "legacy_owner_callable_adapter_readback",
            "legacy_owner_callable_adapter_readback": True,
            "legacy_owner_callable_adapter_missing_opl_request": not bool(request),
            "opl_domain_progress_transition_request": request or None,
            "domain_intent": _mapping(adapter.get("domain_intent")) or None,
            "authority_boundary": _mapping(adapter.get("authority_boundary")) or None,
            "stage_transition_authority_boundary": _mapping(adapter.get("stage_transition_authority_boundary"))
            or None,
            "refs": _mapping(adapter.get("refs")) or None,
            "source_action": _mapping(adapter.get("source_action")) or None,
            "owner_route": _mapping(adapter.get("owner_route")) or None,
            "prompt_contract_ref": _mapping(adapter.get("prompt_contract")) or None,
            "progress_first_closeout_admission": _mapping(adapter.get("progress_first_closeout_admission"))
            or None,
            "provider_admission_pending": False,
            "provider_admission_requires_opl_runtime_result": True,
            "provider_completion_is_domain_completion": False,
            "mas_dispatch_authority": False,
            "mas_creates_owner_callable_carrier": False,
            "mas_creates_opl_outbox": False,
            "mas_creates_opl_event": False,
            "mas_creates_opl_stage_run": False,
            "target_runtime_owner": _text(adapter.get("target_runtime_owner")) or "one-person-lab",
            "dispatch_status": _text(adapter.get("dispatch_status")) or "transition_request_pending",
            "blocked_reason": _text(adapter.get("blocked_reason")),
        }
        if any(
            record.get(key)
            for key in (
                "study_id",
                "action_type",
                "work_unit_id",
                "work_unit_fingerprint",
                "dispatch_path",
            )
        ):
            records.append(_normalized_transition_request_record(record))
    return records


def _transition_request_identity_fields(payload: Mapping[str, Any]) -> dict[str, Any]:
    refs = _mapping(payload.get("refs"))
    source_action = _mapping(payload.get("source_action"))
    request = _mapping(payload.get("opl_domain_progress_transition_request"))
    return {
        key: value
        for key, value in {
            "study_id": _text(payload.get("study_id")) or _text(request.get("study_id")),
            "quest_id": _text(payload.get("quest_id")) or _text(request.get("quest_id")),
            "action_type": _text(payload.get("action_type")) or _text(request.get("action_type")),
            "work_unit_id": (
                _text(payload.get("work_unit_id"))
                or _text(payload.get("next_work_unit"))
                or _text(source_action.get("work_unit_id"))
                or _text(request.get("work_unit_id"))
            ),
            "work_unit_fingerprint": (
                _text(payload.get("work_unit_fingerprint"))
                or _text(payload.get("action_fingerprint"))
                or _text(source_action.get("work_unit_fingerprint"))
                or _text(request.get("work_unit_fingerprint"))
            ),
            "action_fingerprint": _text(payload.get("action_fingerprint"))
            or _text(payload.get("work_unit_fingerprint")),
            "next_executable_owner": _text(payload.get("next_executable_owner"))
            or _text(request.get("next_owner")),
            "required_output_surface": _text(payload.get("required_output_surface"))
            or _text(request.get("required_output_surface")),
            "dispatch_authority": _text(payload.get("dispatch_authority"))
            or _text(request.get("dispatch_authority")),
            "dispatch_path": _text(payload.get("dispatch_path")) or _text(refs.get("dispatch_path")),
            "stage_packet_ref": _text(payload.get("stage_packet_ref")) or _text(refs.get("stage_packet_ref")),
            "stage_packet_refs": payload.get("stage_packet_refs") or refs.get("stage_packet_refs"),
        }.items()
        if value is not None
    }


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
