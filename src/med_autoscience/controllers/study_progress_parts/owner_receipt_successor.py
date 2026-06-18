from __future__ import annotations

from typing import Any, Mapping

from .shared import _mapping_copy, _non_empty_text


def paper_recovery_consumed_owner_receipt_successor(
    recovery: Mapping[str, Any],
) -> bool:
    if recovery.get("phase") != "owner_action_ready":
        return False
    next_safe_action = _mapping_copy(recovery.get("next_safe_action"))
    if next_safe_action.get("kind") != "materialize_successor_owner_action":
        return False
    successor = _mapping_copy(next_safe_action.get("successor_owner_action"))
    if _non_empty_text(successor.get("action_type")) is None:
        return False
    if _non_empty_text(successor.get("work_unit_id")) is None:
        return False
    if (
        _non_empty_text(successor.get("work_unit_fingerprint"))
        or _non_empty_text(successor.get("action_fingerprint"))
    ) is None:
        return False
    decision = _mapping_copy(recovery.get("supervisor_decision"))
    if decision.get("identity_match") is False:
        return False
    return any(
        _non_empty_text(_mapping_copy(item).get("condition"))
        == "consumed_owner_receipt_routeback_successor"
        for item in recovery.get("conditions") or []
        if isinstance(item, Mapping)
    )
