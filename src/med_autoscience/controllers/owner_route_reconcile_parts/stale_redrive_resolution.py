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


def superseded_by_live_provider_attempt(
    *,
    live_attempt: Mapping[str, Any] | None,
    actions: list[Mapping[str, Any]],
    receipt: Mapping[str, Any] | None,
) -> bool:
    if _mapping(live_attempt).get("running_provider_attempt") is not True:
        return False
    if actions:
        return False
    return _text(_mapping(receipt).get("blocked_reason")) == REDRIVE_BUDGET_EXHAUSTED_REASON


def annotate_live_attempt_superseded_receipt(
    receipt: Mapping[str, Any],
    *,
    live_attempt: Mapping[str, Any] | None,
) -> dict[str, Any]:
    attempt = _mapping(live_attempt)
    return {
        **dict(receipt),
        "stale_blocker_resolution": {
            "status": "superseded",
            "blocker_type": REDRIVE_BUDGET_EXHAUSTED_REASON,
            "basis": "live_provider_attempt_running",
            "active_stage_attempt_id": _text(attempt.get("active_stage_attempt_id")),
            "active_run_id": _text(attempt.get("active_run_id")),
        },
        "next_action": "honor_live_provider_attempt_after_stale_redrive_blocker",
    }


def live_attempt_overlay(
    *,
    live_attempt: Mapping[str, Any] | None,
    actions: list[Mapping[str, Any]],
    receipt: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if not superseded_by_live_provider_attempt(
        live_attempt=live_attempt,
        actions=actions,
        receipt=receipt,
    ):
        return {}
    return {
        "receipt": annotate_live_attempt_superseded_receipt(
            _mapping(receipt),
            live_attempt=live_attempt,
        ),
        "blocked_reason": None,
        "why_not_applied": None,
        "next_owner": "supervisor_only/live_provider_attempt",
        "lifecycle": {},
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "REDRIVE_BUDGET_EXHAUSTED_REASON",
    "annotate_live_attempt_superseded_receipt",
    "annotate_superseded_receipt",
    "live_attempt_overlay",
    "superseded_by_live_provider_attempt",
    "superseded_by_current_delta",
]
