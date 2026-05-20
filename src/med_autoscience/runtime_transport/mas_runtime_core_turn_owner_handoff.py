from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.runtime_control import owner_callable_for_action


def blocked_closeout_owner_handoff_authorization(
    runtime_state: Mapping[str, Any],
    *,
    action_names_for_authorization,
    mapping,
    text,
) -> dict[str, Any]:
    wakeup = runtime_state.get("last_explicit_user_wakeup")
    if not isinstance(wakeup, Mapping):
        return {}
    authorization = wakeup.get("owner_handoff_authorization")
    if not isinstance(authorization, Mapping):
        return {}
    normalized = dict(authorization)
    if text(normalized.get("authorization_basis")) != "blocked_turn_closeout_owner_handoff":
        return {}
    action_names = action_names_for_authorization(normalized)
    if len(action_names) != 1:
        return {}
    action_name = action_names[0]
    owner_callable = owner_callable_for_action(action_name)
    if not isinstance(owner_callable, Mapping):
        return {}
    next_owner = text(normalized.get("next_owner"))
    callable_owner = text(owner_callable.get("owner"))
    if next_owner is None or callable_owner is None or next_owner != callable_owner:
        return {}
    if text(normalized.get("owner_callable_surface")) != text(owner_callable.get("callable_surface")):
        return {}
    work_unit_id = text(normalized.get("work_unit_id"))
    if work_unit_id is None or work_unit_id != action_name:
        return {}
    next_work_unit = mapping(normalized.get("next_work_unit"))
    if text(next_work_unit.get("unit_id")) != action_name:
        return {}
    return normalized


__all__ = ["blocked_closeout_owner_handoff_authorization"]
