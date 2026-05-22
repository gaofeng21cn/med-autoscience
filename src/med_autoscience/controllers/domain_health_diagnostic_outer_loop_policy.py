from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.study_decision_record import StudyDecisionActionType


def outer_loop_request_requires_fresh_controller_execution(tick_request: Mapping[str, Any]) -> bool:
    controller_action_types = {
        str(action.get("action_type") or "").strip() or None
        for action in (tick_request.get("controller_actions") or [])
        if isinstance(action, Mapping)
    }
    return bool(
        controller_action_types
        & {
            StudyDecisionActionType.RUN_GATE_CLEARING_BATCH.value,
            StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH.value,
        }
    )
