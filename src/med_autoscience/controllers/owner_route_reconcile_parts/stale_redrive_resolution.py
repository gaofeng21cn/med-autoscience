from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.study_state_matrix_parts.progress_first_tick_accounting import (
    redrive_budget_blocker_superseded_by_terminal_delta,
)


REDRIVE_BUDGET_EXHAUSTED_REASON = "progress_first_owner_redrive_budget_exhausted"


def superseded_by_current_delta(*, progress: Mapping[str, Any], receipt: Mapping[str, Any]) -> bool:
    if _text(receipt.get("blocked_reason")) != REDRIVE_BUDGET_EXHAUSTED_REASON:
        return False
    return redrive_budget_blocker_superseded_by_terminal_delta(
        _mapping(progress.get("progress_first_monitoring_summary"))
    )


def annotate_superseded_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **dict(receipt),
        "stale_blocker_resolution": {
            "status": "superseded",
            "blocker_type": REDRIVE_BUDGET_EXHAUSTED_REASON,
            "basis": "terminal_deliverable_delta",
        },
        "next_action": "honor_current_owner_route_after_stale_redrive_blocker",
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "REDRIVE_BUDGET_EXHAUSTED_REASON",
    "annotate_superseded_receipt",
    "superseded_by_current_delta",
]
