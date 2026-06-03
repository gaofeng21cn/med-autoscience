from __future__ import annotations

from typing import Any

from med_autoscience.controllers.study_transition_receipt_consumption import (
    default_executor_execution_receipt_consumption,
)
from med_autoscience.profiles import WorkspaceProfile

from . import current_writer_handoff


def without_consumed_default_executor_dispatches(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        dispatch
        for dispatch in dispatches
        if not consumed_default_executor_dispatch(
            profile=profile,
            study_id=study_id,
            dispatch=dispatch,
        )
    ]


def consumed_default_executor_dispatch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: dict[str, Any],
) -> bool:
    action_type = _text(dispatch.get("action_type"))
    if action_type is None:
        return False
    route = current_writer_handoff.raw_dispatch_owner_route(dispatch) or current_writer_handoff.dispatch_owner_route(
        dispatch
    )
    if not route:
        return False
    receipt = default_executor_execution_receipt_consumption(
        study_root=profile.studies_root / study_id,
        owner_route=route,
        actions=[{"action_type": action_type}],
    )
    return bool(receipt)


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "consumed_default_executor_dispatch",
    "without_consumed_default_executor_dispatches",
]
