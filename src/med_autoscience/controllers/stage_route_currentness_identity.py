from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from med_autoscience.controllers import control_identity


@dataclass(frozen=True)
class StageRouteCurrentnessIdentity:
    action_type: str | None
    work_unit_id: str | None
    fingerprints: frozenset[str]
    source_eval_id: str | None = None

    @property
    def has_strong_match_key(self) -> bool:
        return self.work_unit_id is not None or bool(self.fingerprints)


def currentness_identity(payload: Mapping[str, Any] | None) -> StageRouteCurrentnessIdentity:
    data = _mapping(payload)
    owner_route = _owner_route(data)
    payload_basis = _mapping(data.get("owner_route_currentness_basis"))
    source_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = _currentness_basis(owner_route)
    handoff = _mapping(data.get("handoff_packet"))
    handoff_basis = _mapping(handoff.get("owner_route_currentness_basis"))
    handoff_route = _mapping(handoff.get("owner_route"))
    handoff_refs = _mapping(handoff_route.get("source_refs"))
    handoff_route_basis = _currentness_basis(handoff_route)
    return StageRouteCurrentnessIdentity(
        action_type=_action_type(data, owner_route),
        work_unit_id=_first_text(
            payload_basis.get("work_unit_id"),
            data.get("work_unit_id"),
            _work_unit_text(data.get("next_work_unit")),
            source_refs.get("work_unit_id"),
            currentness_basis.get("work_unit_id"),
            handoff.get("work_unit_id"),
            _work_unit_text(handoff.get("next_work_unit")),
            handoff_basis.get("work_unit_id"),
            handoff_refs.get("work_unit_id"),
            handoff_route_basis.get("work_unit_id"),
        ),
        fingerprints=frozenset(
            _strong_fingerprint(value)
            for value in (
                payload_basis.get("work_unit_fingerprint"),
                payload_basis.get("action_fingerprint"),
                data.get("work_unit_fingerprint"),
                data.get("action_fingerprint"),
                data.get("fingerprint"),
                owner_route.get("work_unit_fingerprint"),
                owner_route.get("source_fingerprint"),
                source_refs.get("work_unit_fingerprint"),
                source_refs.get("action_fingerprint"),
                currentness_basis.get("work_unit_fingerprint"),
                currentness_basis.get("action_fingerprint"),
                handoff.get("work_unit_fingerprint"),
                handoff.get("action_fingerprint"),
                handoff_basis.get("work_unit_fingerprint"),
                handoff_basis.get("action_fingerprint"),
                handoff_route.get("work_unit_fingerprint"),
                handoff_route.get("source_fingerprint"),
                handoff_refs.get("work_unit_fingerprint"),
                handoff_refs.get("action_fingerprint"),
                handoff_route_basis.get("work_unit_fingerprint"),
                handoff_route_basis.get("action_fingerprint"),
            )
            if _strong_fingerprint(value) is not None
        ),
        source_eval_id=_first_text(
            payload_basis.get("source_eval_id"),
            data.get("source_eval_id"),
            owner_route.get("source_eval_id"),
            source_refs.get("source_eval_id"),
            currentness_basis.get("source_eval_id"),
            handoff.get("source_eval_id"),
            handoff_basis.get("source_eval_id"),
            handoff_route.get("source_eval_id"),
            handoff_refs.get("source_eval_id"),
            handoff_route_basis.get("source_eval_id"),
        ),
    )


def currentness_identities_match(
    left: Mapping[str, Any] | None,
    right: Mapping[str, Any] | None,
    *,
    require_fingerprint: bool = False,
) -> bool:
    left_identity = currentness_identity(left)
    right_identity = currentness_identity(right)
    if (
        left_identity.action_type is not None
        and right_identity.action_type is not None
        and left_identity.action_type != right_identity.action_type
    ):
        return False
    if (
        left_identity.work_unit_id is not None
        and right_identity.work_unit_id is not None
        and left_identity.work_unit_id != right_identity.work_unit_id
    ):
        return False
    if not left_identity.has_strong_match_key or not right_identity.has_strong_match_key:
        return False
    shared_fingerprints = left_identity.fingerprints.intersection(right_identity.fingerprints)
    if left_identity.fingerprints and right_identity.fingerprints:
        return bool(shared_fingerprints)
    if left_identity.source_eval_id is not None or right_identity.source_eval_id is not None:
        return (
            not require_fingerprint
            and left_identity.source_eval_id is not None
            and left_identity.source_eval_id == right_identity.source_eval_id
            and left_identity.work_unit_id is not None
            and right_identity.work_unit_id is not None
        )
    return not require_fingerprint and left_identity.work_unit_id is not None and right_identity.work_unit_id is not None


def currentness_fingerprints(payload: Mapping[str, Any] | None) -> frozenset[str]:
    return currentness_identity(payload).fingerprints


def work_unit_identity(payload: Mapping[str, Any] | None) -> str | None:
    return currentness_identity(payload).work_unit_id


def _action_type(payload: Mapping[str, Any], owner_route: Mapping[str, Any]) -> str | None:
    direct = _text(payload.get("action_type"))
    if direct is not None:
        return direct
    allowed_actions = payload.get("allowed_actions")
    if isinstance(allowed_actions, str):
        return _text(allowed_actions)
    if isinstance(allowed_actions, list | tuple):
        for item in allowed_actions:
            if text := _text(item):
                return text
    route_actions = owner_route.get("allowed_actions")
    if isinstance(route_actions, str):
        return _text(route_actions)
    if isinstance(route_actions, list | tuple):
        for item in route_actions:
            if text := _text(item):
                return text
    return None


def _owner_route(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    direct = _mapping(payload.get("owner_route"))
    if direct:
        return direct
    handoff_route = _mapping(_mapping(payload.get("handoff_packet")).get("owner_route"))
    if handoff_route:
        return handoff_route
    if _text(payload.get("surface")) == "domain_route_owner_route":
        return payload
    return {}


def _currentness_basis(owner_route: Mapping[str, Any]) -> Mapping[str, Any]:
    source_refs = _mapping(owner_route.get("source_refs"))
    source_basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    if source_basis:
        return source_basis
    return _mapping(_mapping(owner_route.get("currentness_contract")).get("basis"))


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _work_unit_text(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id")) or _text(value.get("work_unit_id"))
    return _text(value)


def _first_text(*values: object) -> str | None:
    for value in values:
        if text := _text(value):
            return text
    return None


def _text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _strong_fingerprint(value: object) -> str | None:
    text = _text(value)
    if text is None or control_identity.is_synthetic_current_owner_ticket(text):
        return None
    return text


__all__ = [
    "StageRouteCurrentnessIdentity",
    "currentness_fingerprints",
    "currentness_identities_match",
    "currentness_identity",
    "work_unit_identity",
]
