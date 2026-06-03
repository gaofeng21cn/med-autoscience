from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.owner_route_reconcile_parts import artifact_freshness
from med_autoscience.runtime_control import owner_route as owner_route_part
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


def superseded_by_fresh_artifact_delta(
    *,
    progress: Mapping[str, Any],
    receipt: Mapping[str, Any],
    actions: list[Mapping[str, Any]],
) -> bool:
    if _text(receipt.get("blocked_reason")) != REDRIVE_BUDGET_EXHAUSTED_REASON:
        return False
    if _text(receipt.get("action_type")) != "run_quality_repair_batch":
        return False
    if not actions:
        return False
    return _fresh_meaningful_artifact_delta(progress)


def superseded_basis(
    *,
    progress: Mapping[str, Any],
    receipt: Mapping[str, Any],
    actions: list[Mapping[str, Any]],
) -> str | None:
    if superseded_by_fresh_artifact_delta(progress=progress, receipt=receipt, actions=actions):
        return "fresh_meaningful_artifact_delta"
    if superseded_by_current_delta(progress=progress, receipt=receipt):
        return "terminal_deliverable_delta"
    return None


def annotate_superseded_receipt(receipt: Mapping[str, Any], *, basis: str = "terminal_deliverable_delta") -> dict[str, Any]:
    return {
        **dict(receipt),
        "stale_blocker_resolution": {
            "status": "superseded",
            "blocker_type": REDRIVE_BUDGET_EXHAUSTED_REASON,
            "basis": basis,
        },
        "next_action": "honor_current_owner_route_after_stale_redrive_blocker",
    }


def rebuild_route_after_superseded_blocker(
    *,
    study_id: str,
    quest_id: str | None,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    actions: list[Mapping[str, Any]],
    block_state: Mapping[str, Any],
    why_not_applied: str | None,
    block_state_next_owner: str | None,
    active_run_id: str | None,
) -> dict[str, Any]:
    blocked_reason = _text(block_state.get("blocked_reason")) or why_not_applied
    next_owner = block_state_next_owner
    owner_route, routed_actions = owner_route_part.route_and_decorate_actions(
        study_id=study_id,
        quest_id=quest_id,
        status=status,
        progress=progress,
        actions=actions,
        blocked_reason=blocked_reason,
        next_owner=next_owner,
        active_run_id=active_run_id,
    )
    return {
        "owner_route": owner_route,
        "actions": routed_actions,
        "blocked_reason": blocked_reason,
        "next_owner": next_owner,
    }


def restore_after_superseded_blocker(
    *,
    study_id: str,
    quest_id: str | None,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    actions: list[Mapping[str, Any]],
    receipt: Mapping[str, Any],
    block_state: Mapping[str, Any],
    why_not_applied: str | None,
    block_state_next_owner: str | None,
    active_run_id: str | None,
) -> dict[str, Any] | None:
    basis = superseded_basis(progress=progress, receipt=receipt, actions=actions)
    if basis is None:
        return None
    restored = rebuild_route_after_superseded_blocker(
        study_id=study_id,
        quest_id=quest_id,
        status=status,
        progress=progress,
        actions=actions,
        block_state=block_state,
        why_not_applied=why_not_applied,
        block_state_next_owner=block_state_next_owner,
        active_run_id=active_run_id,
    )
    return {"receipt": annotate_superseded_receipt(receipt, basis=basis), **restored}


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


def _fresh_meaningful_artifact_delta(progress: Mapping[str, Any]) -> bool:
    return artifact_freshness.meaningful_artifact_delta_observed(progress)


__all__ = [
    "REDRIVE_BUDGET_EXHAUSTED_REASON",
    "annotate_live_attempt_superseded_receipt",
    "annotate_superseded_receipt",
    "live_attempt_overlay",
    "rebuild_route_after_superseded_blocker",
    "restore_after_superseded_blocker",
    "superseded_by_live_provider_attempt",
    "superseded_by_current_delta",
    "superseded_basis",
    "superseded_by_fresh_artifact_delta",
]
