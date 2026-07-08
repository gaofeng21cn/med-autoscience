from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers import study_domain_transition_guard


def domain_transition_canonical_next_action(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    transition = _mapping(payload.get("domain_transition"))
    if study_domain_transition_guard.runtime_redrive_decision_type(
        {"domain_transition": transition}
    ) is None:
        return {}
    next_action = _mapping(transition.get("next_action")) or _mapping(
        transition.get("next_action_envelope")
    )
    if _stage_closure_route_checkpoint_suppresses_domain_transition(
        payload,
        domain_transition_next_action=next_action,
    ):
        return {}
    if _text(next_action.get("surface_kind")) != "mas_next_action_envelope":
        return {}
    if not _text(next_action.get("action_family")):
        return {}
    if not _text(next_action.get("owner")):
        return {}
    return next_action


def _stage_closure_route_checkpoint_suppresses_domain_transition(
    payload: Mapping[str, Any],
    *,
    domain_transition_next_action: Mapping[str, Any],
) -> bool:
    current_next_action = _mapping(payload.get("next_action"))
    if _text(current_next_action.get("action_family")) != (
        "paper.stage_closure.owner_consumption"
    ):
        return False
    receipt = _mapping(payload.get("receipt_owner_consumption_readback")) or _mapping(
        _mapping(payload.get("artifact_first_mission_summary")).get(
            "receipt_owner_consumption_readback"
        )
    )
    consumption = _mapping(receipt.get("mas_receipt_consumption"))
    if _text(consumption.get("status")) != "owner_consumed_route_checkpoint":
        return False
    current_work_unit_id = _text(current_next_action.get("work_unit_id"))
    transition_work_unit_id = _text(domain_transition_next_action.get("work_unit_id"))
    if current_work_unit_id is None or transition_work_unit_id is None:
        return False
    return current_work_unit_id != transition_work_unit_id


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["domain_transition_canonical_next_action"]
