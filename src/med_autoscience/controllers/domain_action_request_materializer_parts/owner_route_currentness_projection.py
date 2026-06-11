from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from med_autoscience.controllers.owner_route_reconcile_parts import (
    domain_transition_actions,
)


def study_with_owner_route_currentness(
    study: Mapping[str, Any],
    *,
    generated: list[dict[str, Any]],
    ensure_owner_route_v2: Callable[[Mapping[str, Any]], dict[str, Any]],
    action_allowed_by_owner_route: Callable[[Mapping[str, Any], Mapping[str, Any]], bool],
) -> dict[str, Any]:
    payload = dict(study)
    owner_route = ensure_owner_route_v2(_mapping(payload.get("owner_route")))
    if not owner_route or not _owner_route_currentness_applies_to_generated(
        owner_route=owner_route,
        generated=generated,
        action_allowed_by_owner_route=action_allowed_by_owner_route,
    ):
        return payload
    basis = _owner_route_currentness_basis(owner_route)
    if "runtime_health_snapshot" not in payload and (runtime_epoch := _text(basis.get("runtime_health_epoch"))):
        payload["runtime_health_snapshot"] = {"runtime_health_epoch": runtime_epoch}
    if "study_truth_snapshot" not in payload:
        truth_epoch = _text(basis.get("truth_epoch")) or _text(owner_route.get("truth_epoch"))
        source_signature = _text(owner_route.get("source_fingerprint"))
        if truth_epoch or source_signature:
            payload["study_truth_snapshot"] = {
                key: value
                for key, value in {
                    "truth_epoch": truth_epoch,
                    "source_signature": source_signature,
                }.items()
                if value is not None
            }
    if "publication_eval" not in payload and (source_eval_id := _text(basis.get("source_eval_id"))):
        payload["publication_eval"] = {"eval_id": source_eval_id}
    return payload


def _owner_route_currentness_applies_to_generated(
    *,
    owner_route: Mapping[str, Any],
    generated: list[dict[str, Any]],
    action_allowed_by_owner_route: Callable[[Mapping[str, Any], Mapping[str, Any]], bool],
) -> bool:
    if any(action_allowed_by_owner_route(action, owner_route) for action in generated):
        return True
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _owner_route_currentness_basis(owner_route)
    route_work_unit_id = _text(basis.get("work_unit_id")) or _text(source_refs.get("work_unit_id"))
    route_work_unit_fingerprint = _text(basis.get("work_unit_fingerprint")) or _text(
        source_refs.get("work_unit_fingerprint")
    )
    if route_work_unit_id is None and route_work_unit_fingerprint is None:
        return False
    for action in generated:
        action_work_unit_id = (
            _text(action.get("controller_work_unit_id"))
            or _text(action.get("executable_work_unit"))
            or _work_unit_id(action.get("next_work_unit"))
        )
        action_work_unit_fingerprint = _text(action.get("work_unit_fingerprint"))
        if (
            route_work_unit_id is not None
            and route_work_unit_id == action_work_unit_id
            and (
                action_allowed_by_owner_route(action, owner_route)
                or action_work_unit_id in domain_transition_actions.AI_REVIEWER_RECORD_PRODUCTION_WORK_UNIT_IDS
            )
        ):
            return True
        if (
            route_work_unit_fingerprint is not None
            and action_work_unit_fingerprint is not None
            and route_work_unit_fingerprint != action_work_unit_fingerprint
        ):
            continue
        if (
            route_work_unit_fingerprint is not None
            and action_work_unit_fingerprint is not None
            and route_work_unit_fingerprint == action_work_unit_fingerprint
        ):
            return True
    return False


def _owner_route_currentness_basis(owner_route: Mapping[str, Any]) -> dict[str, Any]:
    source_refs = _mapping(owner_route.get("source_refs"))
    return _mapping(_mapping(owner_route.get("currentness_contract")).get("basis")) or _mapping(
        source_refs.get("owner_route_currentness_basis")
    )


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id")) or _text(value.get("work_unit_id"))
    return _text(value)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["study_with_owner_route_currentness"]
