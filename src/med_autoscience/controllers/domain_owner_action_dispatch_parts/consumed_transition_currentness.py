from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.runtime_control import owner_route as owner_route_part


def gate_replay_matches_dispatch(
    *,
    dispatch: Mapping[str, Any],
    route: Mapping[str, Any],
) -> bool:
    dispatch_route = owner_route_part.ensure_owner_route_v2(
        _mapping(dispatch.get("owner_route")) or _mapping(_mapping(dispatch.get("prompt_contract")).get("owner_route"))
    )
    if not dispatch_route:
        return False
    route_refs = _mapping(route.get("source_refs"))
    dispatch_refs = _mapping(dispatch_route.get("source_refs"))
    route_eval_id = _source_eval_id(route)
    dispatch_eval_id = _source_eval_id(dispatch_route)
    source_eval_matches = (
        dispatch_eval_id == route_eval_id
        if route_eval_id or dispatch_eval_id
        else True
    )
    if owner_route_part.owner_route_matches(dispatch=dispatch, current_route=route):
        return source_eval_matches
    return (
        _text(dispatch_route.get("next_owner")) == _text(route.get("next_owner"))
        and {_text(item) for item in dispatch_route.get("allowed_actions") or []}
        == {_text(item) for item in route.get("allowed_actions") or []}
        and _text(dispatch_refs.get("work_unit_id")) == _text(route_refs.get("work_unit_id"))
        and _text(dispatch_refs.get("work_unit_fingerprint")) == _text(route_refs.get("work_unit_fingerprint"))
        and source_eval_matches
    )


def owner_action_matches_dispatch(
    *,
    dispatch: Mapping[str, Any],
    route: Mapping[str, Any],
) -> bool:
    dispatch_route = owner_route_part.ensure_owner_route_v2(
        _mapping(dispatch.get("owner_route")) or _mapping(_mapping(dispatch.get("prompt_contract")).get("owner_route"))
    )
    if not dispatch_route:
        return False
    if not owner_route_part.route_allows_action(action=dispatch, owner_route=dispatch_route):
        return False
    if _text(dispatch_route.get("next_owner")) != _text(route.get("next_owner")):
        return False
    if {_text(item) for item in dispatch_route.get("allowed_actions") or []} != {
        _text(item) for item in route.get("allowed_actions") or []
    }:
        return False
    route_refs = _mapping(route.get("source_refs"))
    dispatch_refs = _mapping(dispatch_route.get("source_refs"))
    if _text(dispatch_refs.get("work_unit_id")) != _text(route_refs.get("work_unit_id")):
        return False
    if _text(dispatch_refs.get("work_unit_fingerprint")) != _text(route_refs.get("work_unit_fingerprint")):
        return False
    route_eval_id = _source_eval_id(route)
    dispatch_eval_id = _source_eval_id(dispatch_route)
    if (route_eval_id or dispatch_eval_id) and dispatch_eval_id != route_eval_id:
        return False
    return True


def matching_route_for_dispatch(
    *,
    dispatch: Mapping[str, Any],
    transition_route: Mapping[str, Any],
    gate_replay: bool,
) -> dict[str, Any] | None:
    route = owner_route_part.ensure_owner_route_v2(transition_route)
    if gate_replay:
        if not gate_replay_matches_dispatch(dispatch=dispatch, route=route):
            return None
        if not owner_route_part.route_allows_action(action=dispatch, owner_route=route):
            return None
        return route
    if not owner_action_matches_dispatch(dispatch=dispatch, route=route):
        return None
    dispatch_route = _dispatch_current_owner_route(dispatch)
    if dispatch_route is None:
        return None
    return dispatch_route


def _dispatch_current_owner_route(dispatch: Mapping[str, Any]) -> dict[str, Any] | None:
    route = owner_route_part.ensure_owner_route_v2(
        _mapping(dispatch.get("owner_route")) or _mapping(_mapping(dispatch.get("prompt_contract")).get("owner_route"))
    )
    if not route:
        return None
    if not owner_route_part.owner_route_matches(dispatch=dispatch, current_route=route):
        return None
    if not owner_route_part.route_allows_action(action=dispatch, owner_route=route):
        return None
    return route


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _source_eval_id(route: Mapping[str, Any]) -> str | None:
    refs = _mapping(route.get("source_refs"))
    basis = _mapping(refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(route.get("currentness_contract")).get("basis")
    )
    return _text(route.get("source_eval_id")) or _text(refs.get("source_eval_id")) or _text(
        basis.get("source_eval_id")
    )


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
