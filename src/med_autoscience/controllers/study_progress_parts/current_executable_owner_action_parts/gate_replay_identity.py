from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.study_progress_parts.shared import (
    _mapping_copy,
    _non_empty_text,
)

from .action_types import GATE_CLEARING_ACTION


def action_fingerprint(action: Mapping[str, Any]) -> str | None:
    return (
        _non_empty_text(action.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("action_fingerprint"))
        or _non_empty_text(action.get("fingerprint"))
    )


def canonical_gate_replay_typed_blocker_matches_repair_progress(
    *,
    payload: Mapping[str, Any] | None,
    repair_action: Mapping[str, Any],
    repair_fingerprint: str | None,
    gate_replay_work_units: frozenset[str],
) -> bool:
    if not payload:
        return False
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("status")) != "typed_blocker":
        return False
    state = _mapping_copy(current_work_unit.get("state"))
    typed_blocker = _mapping_copy(state.get("typed_blocker")) or _mapping_copy(
        current_work_unit.get("typed_blocker")
    )
    current_action = _non_empty_text(current_work_unit.get("action_type")) or _non_empty_text(
        typed_blocker.get("action_type")
    )
    if current_action != GATE_CLEARING_ACTION:
        return False
    current_work_unit_id = _non_empty_text(current_work_unit.get("work_unit_id")) or _non_empty_text(
        typed_blocker.get("work_unit_id")
    )
    if current_work_unit_id not in gate_replay_work_units:
        return False
    repair_work_unit_id = _non_empty_text(repair_action.get("work_unit_id"))
    if repair_work_unit_id not in gate_replay_work_units:
        return False
    current_fingerprint = (
        _non_empty_text(current_work_unit.get("work_unit_fingerprint"))
        or _non_empty_text(current_work_unit.get("action_fingerprint"))
        or _non_empty_text(typed_blocker.get("work_unit_fingerprint"))
        or _non_empty_text(typed_blocker.get("action_fingerprint"))
    )
    return repair_fingerprint is not None and current_fingerprint == repair_fingerprint


__all__ = [
    "action_fingerprint",
    "canonical_gate_replay_typed_blocker_matches_repair_progress",
]
