from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .opl_current_control_state_handoff_values import _observability_mapping, _work_unit_identity
from .shared_base import _non_empty_text

IDENTITY_BINDING_KEYS = (
    "action_type",
    "work_unit_id",
    "work_unit_fingerprint",
    "action_fingerprint",
)


def bind_live_attempt_to_handoff_identity(
    *,
    handoff: Mapping[str, Any],
    live_attempt_handoff: Mapping[str, Any],
) -> dict[str, Any]:
    merged = dict(handoff)
    identity = _live_attempt_identity_candidate(
        handoff=handoff,
        live_attempt_handoff=live_attempt_handoff,
    )
    if identity is None:
        return merged
    for key in IDENTITY_BINDING_KEYS:
        value = _non_empty_text(identity.get(key))
        if value is not None and _non_empty_text(merged.get(key)) is None:
            merged[key] = value
    runtime_health = _observability_mapping(merged.get("runtime_health"))
    for key in IDENTITY_BINDING_KEYS:
        value = _non_empty_text(merged.get(key))
        if value is not None and _non_empty_text(runtime_health.get(key)) is None:
            runtime_health[key] = value
    if runtime_health:
        merged["runtime_health"] = runtime_health
    return merged


def _live_attempt_identity_candidate(
    *,
    handoff: Mapping[str, Any],
    live_attempt_handoff: Mapping[str, Any],
) -> dict[str, Any] | None:
    direct = _identity_fields(live_attempt_handoff)
    if _identity_has_action_and_work_unit(direct):
        return direct
    queue = [
        _identity_fields(item)
        for item in handoff.get("action_queue") or []
        if isinstance(item, Mapping)
    ]
    queue = [item for item in queue if _identity_has_action_and_work_unit(item)]
    if len(queue) == 1:
        return {**queue[0], **{key: value for key, value in direct.items() if value is not None}}
    handoff_identity = _identity_fields(handoff)
    if _identity_has_action_and_work_unit(handoff_identity):
        return {**handoff_identity, **{key: value for key, value in direct.items() if value is not None}}
    return None


def _identity_fields(payload: Mapping[str, Any]) -> dict[str, Any]:
    owner_route = _observability_mapping(payload.get("owner_route"))
    source_refs = _observability_mapping(owner_route.get("source_refs"))
    basis = _observability_mapping(source_refs.get("owner_route_currentness_basis")) or _observability_mapping(
        payload.get("owner_route_currentness_basis")
    )
    return {
        "action_type": _non_empty_text(payload.get("action_type"))
        or _non_empty_text(owner_route.get("action_type")),
        "work_unit_id": (
            _work_unit_identity(payload.get("work_unit_id"))
            or _work_unit_identity(payload.get("next_work_unit"))
            or _work_unit_identity(owner_route.get("work_unit_id"))
            or _work_unit_identity(owner_route.get("next_work_unit"))
            or _work_unit_identity(source_refs.get("work_unit_id"))
            or _work_unit_identity(basis.get("work_unit_id"))
        ),
        "work_unit_fingerprint": _non_empty_text(payload.get("work_unit_fingerprint"))
        or _non_empty_text(payload.get("action_fingerprint"))
        or _non_empty_text(owner_route.get("work_unit_fingerprint"))
        or _non_empty_text(owner_route.get("source_fingerprint"))
        or _non_empty_text(source_refs.get("work_unit_fingerprint"))
        or _non_empty_text(basis.get("work_unit_fingerprint")),
        "action_fingerprint": _non_empty_text(payload.get("action_fingerprint"))
        or _non_empty_text(payload.get("work_unit_fingerprint"))
        or _non_empty_text(owner_route.get("work_unit_fingerprint"))
        or _non_empty_text(owner_route.get("source_fingerprint"))
        or _non_empty_text(source_refs.get("work_unit_fingerprint"))
        or _non_empty_text(basis.get("work_unit_fingerprint")),
    }


def _identity_has_action_and_work_unit(identity: Mapping[str, Any]) -> bool:
    return _non_empty_text(identity.get("action_type")) is not None and _work_unit_identity(
        identity.get("work_unit_id")
    ) is not None


__all__ = ["bind_live_attempt_to_handoff_identity"]
