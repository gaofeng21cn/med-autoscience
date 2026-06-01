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
    transition = _mapping(current_study.get("domain_transition"))
    completion = _mapping(transition.get("completion_receipt_consumption"))
    next_work_unit = _mapping(transition.get("next_work_unit"))
    current_basis = owner_route_attempt_protocol.currentness_basis(consumed_transition_route)
    current_values = {
        "source_eval_id": _text(completion.get("eval_id"))
        or _text(transition.get("source_eval_id"))
        or _text(transition.get("publication_eval_id"))
        or _text(_mapping(transition.get("publication_eval_ref")).get("eval_id"))
        or _text(_mapping(current_study.get("publication_eval")).get("eval_id"))
        or _text(current_basis.get("source_eval_id")),
        "work_unit_id": _text(next_work_unit.get("unit_id"))
        or _text(next_work_unit.get("work_unit_id"))
        or _text(completion.get("work_unit_id"))
        or _text(current_basis.get("work_unit_id")),
        "work_unit_fingerprint": _text(transition.get("work_unit_fingerprint"))
        or _text(next_work_unit.get("fingerprint"))
        or _text(completion.get("work_unit_fingerprint"))
        or _text(current_basis.get("work_unit_fingerprint")),
    }
    current_values = {key: value for key, value in current_values.items() if value}
    if not current_values:
        return True
    request_basis = owner_route_attempt_protocol.currentness_basis(request_route)
    compared = 0
    for key, current_value in current_values.items():
        request_value = _text(request_basis.get(key))
        if request_value is None:
            continue
        compared += 1
        if request_value != current_value:
            return False
    return compared > 0


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
