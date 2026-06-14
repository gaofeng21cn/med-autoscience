from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import Any

from med_autoscience.controllers.current_work_unit_parts.action_projection_fields import (
    work_unit_id as _work_unit_id,
)
from med_autoscience.controllers.current_work_unit_parts.primitives import (
    mapping as _mapping,
    text as _text,
)


REPAIR_PROGRESS_EVIDENCE_SOURCE = "repair_progress_projection.mas_owner_repair_execution_evidence"
STALE_STAGE_PACKET_BLOCKERS = frozenset(
    {
        "domain_owner_dispatch_zero_selected_after_materialized_current_request",
        "stage_packet_not_current_selected_dispatch",
    }
)


def gate_replay_action_supersedes_stage_packet_blocker(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any],
    gate_replay_work_units: Collection[str],
) -> bool:
    blocker_type = (
        _text(blocker.get("blocker_type"))
        or _text(blocker.get("blocker_id"))
        or _text(blocker.get("blocked_reason"))
    )
    if blocker_type not in STALE_STAGE_PACKET_BLOCKERS:
        return False
    if (_text(action.get("source_surface")) or _text(action.get("source"))) != REPAIR_PROGRESS_EVIDENCE_SOURCE:
        return False
    if _text(action.get("action_type")) != "run_gate_clearing_batch":
        return False
    if _work_unit_id(action.get("work_unit_id")) not in gate_replay_work_units:
        return False
    precedence = _mapping(action.get("repair_progress_precedence"))
    if precedence.get("paper_delta_observed") is not True:
        return False
    if precedence.get("accepted_owner_receipt") is not True:
        return False
    superseded_action = _text(precedence.get("superseded_stage_native_action"))
    blocker_action = _text(blocker.get("action_type"))
    if superseded_action is not None and blocker_action is not None and superseded_action != blocker_action:
        return False
    source_work_unit = _work_unit_id(precedence.get("source_work_unit_id"))
    blocker_work_unit = _work_unit_id(blocker.get("work_unit_id"))
    return source_work_unit is not None and source_work_unit == blocker_work_unit


__all__ = [
    "gate_replay_action_supersedes_stage_packet_blocker",
]
