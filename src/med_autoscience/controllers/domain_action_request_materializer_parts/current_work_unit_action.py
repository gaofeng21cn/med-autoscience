from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.default_executor_action_policy import (
    SUPPORTED_ACTION_TYPES,
    request_output_surface_for_action_type,
    request_owner_for_action_type,
)
from med_autoscience.runtime_control import owner_route as owner_route_part


def canonical_current_work_unit_action(study: Mapping[str, Any]) -> dict[str, Any] | None:
    study_id = _text(study.get("study_id"))
    if study_id is None:
        return None
    current_work_unit = _mapping(study.get("current_work_unit"))
    current_action = _mapping(study.get("current_executable_owner_action"))
    if current_work_unit and not _current_work_unit_is_executable_action(current_work_unit):
        return None
    if not current_work_unit and (
        _text(current_action.get("source")) or _text(current_action.get("source_surface"))
    ) == "stage_kernel_projection.current_owner_delta":
        return None
    source = current_work_unit or current_action
    if not source:
        return None
    action_type = _canonical_action_type(source=source, current_action=current_action)
    if action_type not in SUPPORTED_ACTION_TYPES:
        return None
    owner_route = owner_route_part.ensure_owner_route_v2(
        _mapping(source.get("owner_route"))
        or _mapping(current_action.get("owner_route"))
        or _mapping(study.get("owner_route"))
    )
    source_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    work_unit_id = (
        _text(source.get("work_unit_id"))
        or _text(source.get("unit_id"))
        or _work_unit_id(source.get("next_work_unit"))
        or _text(current_action.get("work_unit_id"))
        or _work_unit_id(current_action.get("next_work_unit"))
        or _text(currentness_basis.get("work_unit_id"))
        or _text(source_refs.get("work_unit_id"))
    )
    work_unit_fingerprint = (
        _text(source.get("work_unit_fingerprint"))
        or _text(source.get("action_fingerprint"))
        or _text(current_action.get("work_unit_fingerprint"))
        or _text(current_action.get("action_fingerprint"))
        or _text(owner_route.get("work_unit_fingerprint"))
        or _text(source_refs.get("work_unit_fingerprint"))
        or _text(currentness_basis.get("work_unit_fingerprint"))
    )
    if work_unit_id is None or work_unit_fingerprint is None:
        return None
    owner = (
        _text(source.get("next_owner"))
        or _text(source.get("owner"))
        or _text(source.get("request_owner"))
        or _text(current_action.get("next_owner"))
        or _text(current_action.get("owner"))
        or _text(owner_route.get("next_owner"))
        or request_owner_for_action_type(action_type)
    )
    candidate = {
        "action_type": action_type,
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "next_executable_owner": owner,
    }
    if owner_route and not owner_route_part.route_allows_action(action=candidate, owner_route=owner_route):
        return None
    quest_id = _text(study.get("quest_id")) or _text(source.get("quest_id")) or _text(current_action.get("quest_id"))
    source_name = (
        _text(source.get("authority"))
        or _text(source.get("source"))
        or _text(source.get("source_surface"))
        or "canonical_current_work_unit"
    )
    source_ref = _text(source.get("source_ref")) or _text(current_action.get("source_ref"))
    target_surface = _mapping(source.get("target_surface")) or _mapping(current_action.get("target_surface"))
    surface_key = (
        _text(source.get("surface_key"))
        or _text(target_surface.get("surface_key"))
        or _text(current_action.get("surface_key"))
        or _text(_mapping(current_action.get("target_surface")).get("surface_key"))
    )
    required_output_surface = (
        _text(source.get("required_output_surface"))
        or _text(target_surface.get("surface_ref"))
        or request_output_surface_for_action_type(action_type)
    )
    action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": action_type,
        "action_id": f"canonical-current-work-unit::{study_id}::{action_type}",
        "reason": _text(source.get("reason")) or _text(current_action.get("reason")) or work_unit_id,
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "next_executable_owner": owner,
        "authority": source_name,
        "required_output_surface": required_output_surface,
        "source_surface": "current_work_unit" if current_work_unit else "current_executable_owner_action",
        "current_action_source": _text(current_action.get("source")) or _text(current_action.get("source_surface")),
        "source_ref": source_ref,
        "work_unit_id": work_unit_id,
        "next_work_unit": _mapping(source.get("next_work_unit")) or work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": work_unit_fingerprint,
        "surface_key": surface_key,
        "target_surface": target_surface or None,
        "repair_progress_precedence": _mapping(current_action.get("repair_progress_precedence")) or None,
        "owner_route": owner_route,
        "handoff_packet": {
            "action_type": action_type,
            "request_owner": owner,
            "recommended_owner": owner,
            "next_executable_owner": owner,
            "source_surface": "current_work_unit" if current_work_unit else "current_executable_owner_action",
            "current_action_source": _text(current_action.get("source")) or _text(current_action.get("source_surface")),
            "source_ref": source_ref,
            "surface_key": surface_key,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "owner_route": owner_route,
            "idempotency_key": _text(owner_route.get("idempotency_key")),
        },
    }
    return {key: value for key, value in action.items() if value is not None}


def _canonical_action_type(*, source: Mapping[str, Any], current_action: Mapping[str, Any]) -> str | None:
    direct = _text(source.get("action_type")) or _text(current_action.get("action_type"))
    if direct in SUPPORTED_ACTION_TYPES:
        return direct
    allowed_actions = [
        action
        for value in [*(source.get("allowed_actions") or []), *(current_action.get("allowed_actions") or [])]
        if (action := _text(value)) in SUPPORTED_ACTION_TYPES
    ]
    unique_actions = sorted(set(allowed_actions))
    return unique_actions[0] if len(unique_actions) == 1 else None


def _current_work_unit_is_executable_action(current_work_unit: Mapping[str, Any]) -> bool:
    if _text(current_work_unit.get("status")) != "executable_owner_action":
        return False
    state = _mapping(current_work_unit.get("state"))
    state_kind = _text(state.get("state_kind"))
    return state_kind in {None, "executable_owner_action"}


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, str):
        return _text(value)
    if isinstance(value, Mapping):
        return _text(value.get("work_unit_id")) or _text(value.get("id")) or _text(value.get("action_id"))
    return None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = ["canonical_current_work_unit_action"]
