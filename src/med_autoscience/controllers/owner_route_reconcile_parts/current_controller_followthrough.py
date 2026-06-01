from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.owner_route_reconcile_parts import action_projection
from med_autoscience.controllers.owner_route_reconcile_parts import controller_followthrough_actions
from med_autoscience.controllers.owner_route_reconcile_parts import current_truth_owner
from med_autoscience.controllers.owner_route_reconcile_parts import domain_route_contract


def action_after_consumed_receipt(
    *,
    study_id: str,
    quest_id: str | None,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
    consumed_receipt: Mapping[str, Any],
) -> dict[str, Any] | None:
    if _text(consumed_receipt.get("execution_status")) != "executed":
        return None
    if _text(consumed_receipt.get("status")) != "consumed":
        return None
    controller_route = current_truth_owner.current_controller_runtime_route(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if controller_route is None:
        return None
    action = controller_followthrough_actions.action_from_controller_route(controller_route)
    if action is None:
        return None
    consumed_action_type = _text(consumed_receipt.get("action_type"))
    action_type = _text(action.get("action_type"))
    consumed_work_unit_id = _text(consumed_receipt.get("work_unit_id")) or _text(
        _mapping(consumed_receipt.get("owner_route_currentness_basis")).get("work_unit_id")
    )
    if action_type == consumed_action_type and _text(action.get("controller_work_unit_id")) == consumed_work_unit_id:
        return None
    return action_projection.decorate_action(
        study_id=study_id,
        quest_id=quest_id,
        action=action,
        request_allowed_write_surfaces=list(domain_route_contract.SUPERVISION_REQUEST_ALLOWED_WRITE_SURFACES),
        control_allowed_write_surfaces=list(domain_route_contract.SUPERVISION_CONTROL_ALLOWED_WRITE_SURFACES),
        forbidden_actions=list(domain_route_contract.SUPERVISION_FORBIDDEN_ACTIONS),
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["action_after_consumed_receipt"]
