from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.controllers.current_work_unit_parts.action_projection_fields import (
    work_unit_id,
)
from med_autoscience.controllers.current_work_unit_parts.primitives import (
    mapping,
    text,
    text_items,
)
from med_autoscience.controllers.stage_route_currentness_identity import (
    currentness_identities_match,
)


def selected_current_action(
    *,
    actions: Sequence[Mapping[str, Any]] | None,
    current_executable_owner_action: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    current_action = action_from_current_action(current_executable_owner_action)
    queued_action = first_action(actions)
    if current_action is None:
        return queued_action
    if queued_action is None:
        return current_action
    if currentness_identities_match(current_action, queued_action):
        return {**queued_action, **current_action}
    return current_action


def action_from_current_action(
    current_executable_owner_action: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    current = mapping(current_executable_owner_action)
    if text(current.get("surface_kind")) != "current_executable_owner_action":
        return None
    allowed_actions = text_items(current.get("allowed_actions"))
    action_type = text(current.get("action_type")) or (allowed_actions[0] if allowed_actions else None)
    owner = text(current.get("next_owner")) or text(current.get("owner"))
    current_work_unit_id = text(current.get("work_unit_id"))
    if action_type is None and owner is None and current_work_unit_id is None:
        return None
    return {
        **current,
        "action_type": action_type,
        "owner": owner,
        "recommended_owner": text(current.get("recommended_owner")) or owner,
        "next_owner": owner,
        "next_work_unit": current_work_unit_id or action_type,
        "work_unit_id": current_work_unit_id,
        "source_surface": text(current.get("source")) or text(current.get("source_surface")),
    }


def action_from_envelope(envelope: Mapping[str, Any] | None) -> dict[str, Any] | None:
    payload = mapping(envelope)
    if text(payload.get("state_kind")) != "executable_owner_action":
        return None
    current_work_unit_id = work_unit_id(payload.get("next_work_unit"))
    owner = text(payload.get("owner"))
    if owner is None and current_work_unit_id is None:
        return None
    return {
        "owner": owner,
        "next_owner": owner,
        "work_unit_id": current_work_unit_id,
        "next_work_unit": current_work_unit_id,
        "source_surface": "current_execution_envelope",
    }


def first_action(actions: Sequence[Mapping[str, Any]] | None) -> dict[str, Any] | None:
    for item in actions or []:
        if isinstance(item, Mapping):
            return dict(item)
    return None


__all__ = [
    "action_from_current_action",
    "action_from_envelope",
    "first_action",
    "selected_current_action",
]
