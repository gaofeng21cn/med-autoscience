from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.current_work_unit_parts.primitives import (
    mapping as _mapping,
    text as _text,
)


def domain_transition_supersedes_provider_completion_blocker(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    if _text(blocker.get("blocker_type")) != "provider_completion_is_not_domain_ready":
        return False
    if _text(action.get("source")) != "domain_transition":
        return False
    current = _mapping(progress.get("current_work_unit"))
    state = _mapping(current.get("state"))
    if _text(state.get("source")) != "accepted_closeout_consumed_pending":
        return False
    transition = _mapping(progress.get("domain_transition"))
    consumption = _mapping(transition.get("completion_receipt_consumption"))
    if _text(consumption.get("status")) not in {"consumed", "receipt_consumed", "completed"}:
        return False
    if not _mapping(transition.get("next_work_unit")):
        return False
    current_work_unit_id = _text(current.get("work_unit_id"))
    if current_work_unit_id is None:
        return False
    consumed_work_unit_id = _text(consumption.get("work_unit_id")) or _text(
        transition.get("consumed_work_unit_id")
    )
    if consumed_work_unit_id is not None and consumed_work_unit_id != current_work_unit_id:
        return False
    return _text(action.get("work_unit_id")) is not None and _text(action.get("action_type")) is not None


__all__ = ["domain_transition_supersedes_provider_completion_blocker"]
