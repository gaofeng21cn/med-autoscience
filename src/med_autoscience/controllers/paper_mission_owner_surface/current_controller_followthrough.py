from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.paper_mission_owner_surface import action_decorators
from med_autoscience.controllers import ai_reviewer_owner_output_consumption
from med_autoscience.controllers.paper_mission_owner_surface import controller_followthrough_actions
from med_autoscience.controllers.paper_mission_owner_surface import current_truth_owner
from med_autoscience.controllers.paper_mission_owner_surface import domain_route_contract


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
    return action_decorators.decorate_action(
        study_id=study_id,
        quest_id=quest_id,
        action=action,
        request_allowed_write_surfaces=list(domain_route_contract.SUPERVISION_REQUEST_ALLOWED_WRITE_SURFACES),
        control_allowed_write_surfaces=list(domain_route_contract.SUPERVISION_CONTROL_ALLOWED_WRITE_SURFACES),
        forbidden_actions=list(domain_route_contract.SUPERVISION_FORBIDDEN_ACTIONS),
    )


def owner_output_consumption_from_completion_receipt(
    *,
    status: Mapping[str, Any],
    record_requirements: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    transition = _mapping(status.get("domain_transition"))
    receipt = _mapping(transition.get("completion_receipt_consumption"))
    if _text(receipt.get("status")) != "consumed":
        return None
    if _text(receipt.get("receipt_kind")) != "ai_reviewer_publication_eval":
        return None
    record_ref = _text(receipt.get("record_ref")) or _text(receipt.get("receipt_ref"))
    eval_id = _text(receipt.get("eval_id"))
    if record_ref is None or eval_id is None:
        return None
    payload = {
        "status": "consumed",
        "receipt_kind": "ai_reviewer_publication_eval",
        "record_ref": record_ref,
        "eval_id": eval_id,
        "consumption_mode": "refs_only_current_ai_reviewer_record",
    }
    required_refs = _string_items(_mapping(record_requirements).get("required_currentness_refs"))
    if required_refs:
        payload["required_currentness_refs"] = required_refs
    payload["next_action"] = _text(receipt.get("next_action")) or "honor_ai_reviewer_publication_eval_authority"
    return payload


def bind_ai_reviewer_owner_output_consumption(
    *,
    action: Mapping[str, Any],
    status: Mapping[str, Any],
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any]:
    del study_root, publication_eval_payload
    payload = dict(action)
    owner_output_consumption = owner_output_consumption_from_completion_receipt(
        status=status,
        record_requirements=None,
    )
    if owner_output_consumption is not None:
        payload["owner_output_consumption"] = owner_output_consumption
    return payload


def current_controller_action(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
    action_type: str,
) -> dict[str, Any] | None:
    controller_route = current_truth_owner.current_controller_runtime_route(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if controller_route is None:
        return None
    action = controller_followthrough_actions.action_from_controller_route(controller_route)
    if _text(_mapping(action).get("action_type")) != action_type:
        return None
    return action


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _string_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _text(item))]


__all__ = [
    "action_after_consumed_receipt",
    "bind_ai_reviewer_owner_output_consumption",
    "current_controller_action",
    "owner_output_consumption_from_completion_receipt",
]
