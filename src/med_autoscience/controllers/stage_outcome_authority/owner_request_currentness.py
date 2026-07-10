from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.runtime_control import owner_route_attempt_protocol


ACTIVE_OWNER_REQUEST_STATUSES = frozenset({None, "requested", "pending", "assigned"})


def request_basics_match_dispatch(
    *,
    request: Mapping[str, Any] | None,
    action_type: str,
    dispatch_owner: str | None,
) -> bool:
    if not request:
        return False
    request_kind = _text(request.get("request_kind")) or _text(request.get("action_type"))
    if request_kind != action_type:
        return False
    if not lifecycle_active(request):
        return False
    request_owner = (
        _text(request.get("request_owner"))
        or _text(request.get("expected_owner"))
        or _text(request.get("next_executable_owner"))
        or _text(request.get("assigned_to"))
    )
    if request_owner is not None and dispatch_owner is not None and request_owner != dispatch_owner:
        return False
    return True


def lifecycle_active(request: Mapping[str, Any]) -> bool:
    status = _text(request.get("status"))
    if status not in ACTIVE_OWNER_REQUEST_STATUSES:
        return False
    lifecycle_state = _text(_mapping(request.get("request_lifecycle")).get("state"))
    if lifecycle_state is not None and lifecycle_state not in ACTIVE_OWNER_REQUEST_STATUSES:
        return False
    owner_pickup_state = _text(_mapping(request.get("owner_pickup")).get("state"))
    if owner_pickup_state is not None and owner_pickup_state not in ACTIVE_OWNER_REQUEST_STATUSES:
        return False
    return True


def route_basis_matches_current_study(
    *,
    request_route: Mapping[str, Any],
    current_study: Mapping[str, Any],
    consumed_transition_route: Mapping[str, Any],
) -> bool:
    del consumed_transition_route
    current_values = _canonical_next_action_values(current_study)
    if not current_values:
        return False
    return _request_route_matches_current_values(
        request_route=request_route,
        current_values=current_values,
    )


def _request_route_matches_current_values(
    *,
    request_route: Mapping[str, Any],
    current_values: Mapping[str, str],
) -> bool:
    request_basis = owner_route_attempt_protocol.normalize_currentness_sources(request_route)
    for key, current_value in current_values.items():
        request_value = _text(request_basis.get(key))
        if request_value is None:
            return False
        if request_value != current_value:
            return False
    return True


def _canonical_next_action_values(current_study: Mapping[str, Any]) -> dict[str, str]:
    payload = _mapping(current_study.get("next_action"))
    if _text(payload.get("surface_kind")) != "mas_next_action_envelope":
        return {}
    basis = _mapping(payload.get("currentness_basis"))
    values = owner_route_attempt_protocol.normalize_currentness_sources(payload, basis)
    return {
        name: text
        for name, value in values.items()
        if (
            name.endswith("_id")
            or "fingerprint" in name
            or "eval" in name
            or name.endswith("_epoch")
        )
        and (text := _text(value)) is not None
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
