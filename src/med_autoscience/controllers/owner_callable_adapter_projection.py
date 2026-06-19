from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def owner_callable_adapters(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Retired active body reader.

    Top-level owner_callable_adapters is no longer a controller/readiness/action
    carrier. Use domain_progress_transition_requests for active reads and
    legacy_owner_callable_adapter_refs for migration diagnostics.
    """
    return []


def domain_progress_transition_requests(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    requests = payload.get("domain_progress_transition_requests")
    if isinstance(requests, list):
        return [_normalized_transition_request_record(item) for item in requests if isinstance(item, Mapping)]
    return []


def transition_request_count(payload: Mapping[str, Any]) -> int:
    if "domain_progress_transition_request_count" in payload:
        return _int_value(payload.get("domain_progress_transition_request_count"))
    return len(domain_progress_transition_requests(payload))


def transition_request_status_count(payload: Mapping[str, Any], status: str) -> int:
    key = f"{status}_domain_progress_transition_request_count"
    if key in payload:
        return _int_value(payload.get(key))
    return sum(
        _text(item.get("dispatch_status")) == status
        for item in domain_progress_transition_requests(payload)
    )


def adapter_count(payload: Mapping[str, Any]) -> int:
    return legacy_owner_callable_adapter_count(payload)


def legacy_owner_callable_adapter_count(payload: Mapping[str, Any]) -> int:
    diagnostics = _mapping(payload.get("legacy_owner_callable_adapter_diagnostics"))
    if "legacy_dispatch_count" in diagnostics:
        return _int_value(diagnostics.get("legacy_dispatch_count"))
    return len(legacy_owner_callable_adapter_refs(payload))


def adapter_status_count(payload: Mapping[str, Any], status: str) -> int:
    return legacy_owner_callable_adapter_status_count(payload, status)


def legacy_owner_callable_adapter_status_count(payload: Mapping[str, Any], status: str) -> int:
    diagnostics = _mapping(payload.get("legacy_owner_callable_adapter_diagnostics"))
    diagnostic_key = f"legacy_{status}_count"
    if diagnostic_key in diagnostics:
        return _int_value(diagnostics.get(diagnostic_key))
    return sum(
        _text(item.get("dispatch_status")) == status
        for item in legacy_owner_callable_adapter_refs(payload)
    )


def legacy_owner_callable_adapter_refs(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    diagnostics = _mapping(payload.get("legacy_owner_callable_adapter_diagnostics"))
    diagnostic_refs = diagnostics.get("legacy_dispatch_refs")
    if isinstance(diagnostic_refs, list):
        return [dict(item) for item in diagnostic_refs if isinstance(item, Mapping)]
    diagnostic_refs = diagnostics.get("legacy_dispatches")
    if isinstance(diagnostic_refs, list):
        return [dict(item) for item in diagnostic_refs if isinstance(item, Mapping)]
    return [
        _legacy_owner_callable_adapter_ref(item)
        for item in _legacy_owner_callable_adapter_bodies(payload)
    ]


def legacy_owner_callable_adapter_diagnostics(payload: Mapping[str, Any]) -> dict[str, Any]:
    adapters = _legacy_owner_callable_adapter_bodies(payload)
    if adapters:
        legacy_dispatch_refs = [_legacy_owner_callable_adapter_ref(item) for item in adapters]
        legacy_ready_count = _status_count(adapters, "ready")
        legacy_blocked_count = _status_count(adapters, "blocked")
        legacy_transition_request_pending_count = _status_count(
            adapters,
            "transition_request_pending",
        )
    else:
        legacy_dispatch_refs = legacy_owner_callable_adapter_refs(payload)
        legacy_ready_count = _status_count(legacy_dispatch_refs, "ready")
        legacy_blocked_count = _status_count(legacy_dispatch_refs, "blocked")
        legacy_transition_request_pending_count = _status_count(
            legacy_dispatch_refs,
            "transition_request_pending",
        )
    return {
        "surface": "legacy_owner_callable_adapter_diagnostics",
        "canonical_transition_request_surface": "domain_progress_transition_requests",
        "diagnostic_only": True,
        "counts_authority": False,
        "readiness_authority": False,
        "can_create_success_outcome": False,
        "body_authority": False,
        "body_projection": False,
        "legacy_dispatch_count": len(legacy_dispatch_refs),
        "legacy_ready_count": legacy_ready_count,
        "legacy_blocked_count": legacy_blocked_count,
        "legacy_transition_request_pending_count": legacy_transition_request_pending_count,
        "legacy_payload_scope": "identity_refs_only",
        "legacy_dispatch_refs": legacy_dispatch_refs,
        "legacy_dispatches": legacy_dispatch_refs,
        "legacy_dispatch_body_omitted": True,
        "omitted_body_fields": [
            "authority_boundary",
            "domain_intent",
            "handoff_packet",
            "opl_domain_progress_transition_request",
            "owner_route",
            "prompt_contract",
            "source_action",
            "stage_transition_authority_boundary",
        ],
    }


def with_owner_callable_adapter_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    projected = dict(payload)
    adapters = _legacy_owner_callable_adapter_bodies(projected)
    transition_requests = domain_progress_transition_requests(projected)
    diagnostics = legacy_owner_callable_adapter_diagnostics(projected) if adapters else None
    for key in (
        "owner_callable_adapters",
        "owner_callable_adapter_count",
        "ready_owner_callable_adapter_count",
        "blocked_owner_callable_adapter_count",
        "transition_request_pending_owner_callable_adapter_count",
    ):
        projected.pop(key, None)
    projected.setdefault("canonical_transition_request_surface", "domain_progress_transition_requests")
    if diagnostics:
        projected.setdefault("legacy_owner_callable_adapter_diagnostics", diagnostics)
    projected.setdefault("domain_progress_transition_request_count", len(transition_requests))
    projected.setdefault(
        "ready_domain_progress_transition_request_count",
        _status_count(transition_requests, "ready"),
    )
    projected.setdefault(
        "blocked_domain_progress_transition_request_count",
        _status_count(transition_requests, "blocked"),
    )
    projected.setdefault(
        "transition_request_pending_domain_progress_transition_request_count",
        _status_count(transition_requests, "transition_request_pending"),
    )
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


def _legacy_owner_callable_adapter_bodies(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    adapters = payload.get("owner_callable_adapters")
    if isinstance(adapters, list):
        return [dict(item) for item in adapters if isinstance(item, Mapping)]
    return []


def _legacy_owner_callable_adapter_ref(adapter: Mapping[str, Any]) -> dict[str, Any]:
    refs = _mapping(adapter.get("refs"))
    source_action = _mapping(adapter.get("source_action"))
    identity = {
        "diagnostic_ref_only": True,
        "payload_body_omitted": True,
        "study_id": _text(adapter.get("study_id")),
        "quest_id": _text(adapter.get("quest_id")),
        "action_type": _text(adapter.get("action_type")),
        "next_executable_owner": _text(adapter.get("next_executable_owner")),
        "work_unit_id": (
            _text(adapter.get("work_unit_id"))
            or _text(adapter.get("next_work_unit"))
            or _text(source_action.get("work_unit_id"))
        ),
        "work_unit_fingerprint": (
            _text(adapter.get("work_unit_fingerprint"))
            or _text(adapter.get("action_fingerprint"))
            or _text(source_action.get("work_unit_fingerprint"))
        ),
        "action_fingerprint": (
            _text(adapter.get("action_fingerprint"))
            or _text(adapter.get("work_unit_fingerprint"))
        ),
        "dispatch_status": _text(adapter.get("dispatch_status")),
        "blocked_reason": _text(adapter.get("blocked_reason")),
        "dispatch_authority": _text(adapter.get("dispatch_authority")),
        "required_output_surface": _text(adapter.get("required_output_surface")),
        "target_runtime_owner": _text(adapter.get("target_runtime_owner")),
        "dispatch_path": _text(adapter.get("dispatch_path")) or _text(refs.get("dispatch_path")),
        "dispatch_ref": _text(adapter.get("dispatch_path")) or _text(refs.get("dispatch_path")),
        "transition_request_ref": (
            _text(adapter.get("transition_request_ref"))
            or _text(refs.get("transition_request_ref"))
        ),
        "stage_packet_ref": _text(adapter.get("stage_packet_ref")) or _text(refs.get("stage_packet_ref")),
        "stage_packet_refs": adapter.get("stage_packet_refs") or refs.get("stage_packet_refs"),
    }
    return {key: value for key, value in identity.items() if value is not None}


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
    "legacy_owner_callable_adapter_count",
    "legacy_owner_callable_adapter_diagnostics",
    "legacy_owner_callable_adapter_refs",
    "legacy_owner_callable_adapter_status_count",
    "owner_callable_adapters",
    "transition_request_count",
    "transition_request_status_count",
    "with_owner_callable_adapter_projection",
]
