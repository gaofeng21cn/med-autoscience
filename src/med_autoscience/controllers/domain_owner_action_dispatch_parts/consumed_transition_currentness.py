from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.runtime_control import owner_route as owner_route_part


def gate_replay_matches_dispatch(
    *,
    dispatch: Mapping[str, Any],
    route: Mapping[str, Any],
) -> bool:
    if owner_route_part.owner_route_matches(dispatch=dispatch, current_route=route):
        return True
    dispatch_route = owner_route_part.ensure_owner_route_v2(
        _mapping(dispatch.get("owner_route")) or _mapping(_mapping(dispatch.get("prompt_contract")).get("owner_route"))
    )
    if not dispatch_route:
        return False
    route_refs = _mapping(route.get("source_refs"))
    dispatch_refs = _mapping(dispatch_route.get("source_refs"))
    return (
        _text(dispatch_route.get("next_owner")) == _text(route.get("next_owner"))
        and {_text(item) for item in dispatch_route.get("allowed_actions") or []}
        == {_text(item) for item in route.get("allowed_actions") or []}
        and _text(dispatch_refs.get("work_unit_id")) == _text(route_refs.get("work_unit_id"))
        and _text(dispatch_refs.get("work_unit_fingerprint")) == _text(route_refs.get("work_unit_fingerprint"))
        and _text(dispatch_route.get("source_fingerprint")) == _text(route.get("source_fingerprint"))
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
