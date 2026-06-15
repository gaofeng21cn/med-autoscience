from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.current_work_unit_parts.action_projection_fields import (
    work_unit_fingerprint,
    work_unit_id,
)
from med_autoscience.controllers.current_work_unit_parts.primitives import mapping, text


SUPERSEDED_RECOVERY_SUCCESSOR_BLOCKERS = frozenset(
    {
        "opl_execution_authorization_required",
        "publication_gate_replay_blocked",
    }
)


def paper_recovery_successor_supersedes_publication_gate_replay_blocker(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any],
) -> bool:
    blocker_type = (
        text(blocker.get("blocker_type"))
        or text(blocker.get("blocker_id"))
        or text(blocker.get("blocked_reason"))
        or text(blocker.get("reason"))
    )
    if blocker_type not in SUPERSEDED_RECOVERY_SUCCESSOR_BLOCKERS:
        return False
    if text(action.get("source")) != "paper_recovery_state.next_safe_action.successor_owner_action":
        return False
    successor = mapping(action.get("paper_recovery_successor"))
    if successor.get("provider_admission_allowed") is not True:
        return False
    currentness_basis = mapping(action.get("owner_route_currentness_basis"))
    return (
        text(action.get("action_type")) is not None
        and work_unit_id(action.get("work_unit_id")) is not None
        and work_unit_fingerprint(action, currentness_basis=currentness_basis) is not None
    )


__all__ = ["paper_recovery_successor_supersedes_publication_gate_replay_blocker"]
