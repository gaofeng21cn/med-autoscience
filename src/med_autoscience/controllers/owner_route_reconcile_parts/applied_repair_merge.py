from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.owner_route_reconcile_parts import evidence_adoption


DOMAIN_PROJECTION_KEYS = (
    "controller_work_unit_evidence_adoption",
    "controller_decision_authorization_deduped",
    "controller_work_unit_next_route",
    "owner_receipt",
    "typed_blocker",
    "runtime_owner_handoff",
)


def merge_runtime_fact(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    apply_result: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not applied(apply_result):
        return dict(status), dict(progress)
    owner_result = _owner_projection_result(apply_result)
    merged_status = dict(status)
    if text := _text(owner_result.get("quest_status")):
        merged_status["quest_status"] = text
    if text := _text(owner_result.get("decision")):
        merged_status["decision"] = text
    if text := _text(owner_result.get("reason")):
        merged_status["reason"] = text
    for key in DOMAIN_PROJECTION_KEYS:
        value = owner_result.get(key)
        if isinstance(value, Mapping):
            merged_status[key] = dict(value)
    return merged_status, dict(progress)


def merge_evidence_adoption_projection(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    apply_result: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any], bool]:
    if apply_result is None:
        return dict(status), dict(progress), False
    owner_result = _owner_projection_result(apply_result)
    if _text(owner_result.get("reason")) != evidence_adoption.ADOPTED_REASON:
        return dict(status), dict(progress), False
    next_route = _mapping(owner_result.get("controller_work_unit_next_route"))
    if next_route.get("runtime_relaunch_required") is not False:
        return dict(status), dict(progress), False
    adoption = _mapping(owner_result.get("controller_work_unit_evidence_adoption"))
    if not adoption:
        return dict(status), dict(progress), False
    merged_status = dict(status)
    for key in ("quest_status", "decision", "reason"):
        if key in owner_result:
            merged_status[key] = owner_result.get(key)
    merged_status["controller_work_unit_next_route"] = next_route
    merged_status["controller_work_unit_evidence_adoption"] = adoption
    return merged_status, dict(progress), True


def applied(value: Mapping[str, Any] | None) -> bool:
    return value is not None and _text(value.get("dispatch_status")) == "applied"


def owner_route_required(value: Mapping[str, Any] | None) -> bool:
    return value is not None and _text(value.get("dispatch_status")) == "owner_route_required"


def _owner_projection_result(value: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = _mapping(value)
    for key in ("domain_owner_result", "owner_result", "dispatch_result"):
        nested = _mapping(payload.get(key))
        if nested:
            return nested
    return payload


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "applied",
    "merge_evidence_adoption_projection",
    "merge_runtime_fact",
    "owner_route_required",
]
