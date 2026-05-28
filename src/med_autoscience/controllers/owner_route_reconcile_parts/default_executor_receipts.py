from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import study_transition_receipt_consumption
from med_autoscience.runtime_control import owner_route as owner_route_part


def route_and_consume_current_execution_receipt(
    *,
    study_id: str,
    quest_id: str | None,
    study_root: Path,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    actions: list[dict[str, Any]],
    blocked_reason: str | None,
    next_owner: str | None,
    active_run_id: str | None,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
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
    routed_actions = [
        action
        for action in routed_actions
        if owner_route_part.route_allows_action(action=action, owner_route=owner_route)
    ]
    receipt = study_transition_receipt_consumption.default_executor_execution_followthrough_receipt_consumption(
        study_root=study_root,
        owner_route=owner_route,
        actions=routed_actions,
    )
    if not receipt:
        receipt = study_transition_receipt_consumption.default_executor_execution_receipt_consumption(
            study_root=study_root,
            owner_route=owner_route,
            actions=routed_actions,
        )
    if not receipt:
        return dict(owner_route), routed_actions, {}
    blocked_reason_text = _text(receipt.get("blocked_reason"))
    if _text(receipt.get("execution_status")) == "blocked" and blocked_reason_text:
        return dict(owner_route), [], {**receipt, "next_action": "honor_typed_blocker_without_redrive"}
    consumed_route, consumed_actions = owner_route_part.route_and_decorate_actions(
        study_id=study_id,
        quest_id=quest_id,
        status=status,
        progress=progress,
        actions=[],
        blocked_reason=None,
        next_owner=None,
        active_run_id=active_run_id,
    )
    return consumed_route, consumed_actions, receipt


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["route_and_consume_current_execution_receipt"]
