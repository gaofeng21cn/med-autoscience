from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import study_transition_receipt_consumption
from med_autoscience.controllers.default_executor_action_policy import SUPPORTED_ACTION_TYPES
from med_autoscience.controllers.owner_route_reconcile_parts import domain_transition_actions
from med_autoscience.runtime_control import owner_route as owner_route_part


def consumed_current_transition_receipt(
    *,
    study_id: str,
    quest_id: str | None,
    study_root: Path,
    status: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
    transition: Mapping[str, Any],
    active_run_id: str | None,
) -> dict[str, Any]:
    generated_actions = _transition_actions(
        status=status,
        transition=transition,
        publication_eval_payload=publication_eval_payload,
    )
    if not generated_actions:
        return {}
    owner_route, routed_actions = owner_route_part.route_and_decorate_actions(
        study_id=study_id,
        quest_id=quest_id,
        status=_status_with_transition(status=status, transition=transition),
        progress={},
        actions=generated_actions,
        blocked_reason=_text(generated_actions[0].get("reason")),
        next_owner=(
            _text(generated_actions[0].get("owner"))
            or _text(generated_actions[0].get("request_owner"))
            or _text(transition.get("owner"))
        ),
        active_run_id=active_run_id,
    )
    routed_actions = [
        action
        for action in routed_actions
        if owner_route_part.route_allows_action(action=action, owner_route=owner_route)
    ]
    if not routed_actions:
        return {}
    receipt = study_transition_receipt_consumption.default_executor_execution_receipt_consumption(
        study_root=study_root,
        owner_route=owner_route,
        actions=routed_actions,
    )
    if _text(receipt.get("status")) != "consumed":
        return {}
    return receipt


def _transition_actions(
    *,
    status: Mapping[str, Any],
    transition: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
) -> list[dict[str, Any]]:
    actions = domain_transition_actions.actions(
        _status_with_transition(status=status, transition=transition),
        publication_eval_payload=publication_eval_payload,
    )
    return [
        dict(action)
        for action in actions or []
        if isinstance(action, Mapping) and _text(action.get("action_type")) in SUPPORTED_ACTION_TYPES
    ]


def _status_with_transition(
    *,
    status: Mapping[str, Any],
    transition: Mapping[str, Any],
) -> dict[str, Any]:
    return {**dict(status), "domain_transition": dict(transition)}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["consumed_current_transition_receipt"]
