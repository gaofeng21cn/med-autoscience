from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import study_transition_receipt_consumption
from med_autoscience.controllers.owner_route_reconcile_parts import controller_followthrough_actions
from med_autoscience.controllers.owner_route_reconcile_parts import current_truth_owner
from med_autoscience.controllers.study_transition_receipt_consumption_parts.default_executor_candidates import (
    default_executor_execution_candidates,
)
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
        followthrough_candidate = _previous_owner_route_receipt_for_current_controller_followthrough(
            study_root=study_root,
            status=status,
        )
        if followthrough_candidate is not None:
            receipt = study_transition_receipt_consumption.default_executor_execution_receipt_consumption(
                study_root=study_root,
                owner_route=followthrough_candidate["owner_route"],
                actions=followthrough_candidate["actions"],
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


def _previous_owner_route_receipt_for_current_controller_followthrough(
    *,
    study_root: Path,
    status: Mapping[str, Any],
) -> dict[str, Any] | None:
    transition = _mapping(status.get("domain_transition"))
    action_type = _text(transition.get("controller_action"))
    next_work_unit = _mapping(transition.get("next_work_unit"))
    work_unit_id = _text(next_work_unit.get("unit_id")) or _text(next_work_unit.get("work_unit_id"))
    if action_type not in {"request_opl_stage_attempt", "run_quality_repair_batch"}:
        return None
    if not work_unit_id:
        return None
    controller_route = current_truth_owner.current_controller_runtime_route(
        study_root=study_root,
        publication_eval_payload=_mapping(status.get("publication_eval")),
    )
    if controller_followthrough_actions.action_from_controller_route(controller_route or {}) is None:
        return None
    for execution, _receipt_ref in default_executor_execution_candidates(study_root=study_root):
        if _text(execution.get("action_type")) != "run_quality_repair_batch":
            continue
        owner_route = owner_route_part.ensure_owner_route_v2(
            _mapping(execution.get("current_owner_route"))
            or _mapping(_mapping(execution.get("prompt_contract")).get("owner_route"))
        )
        if not owner_route:
            continue
        if "run_quality_repair_batch" not in {_text(item) for item in owner_route.get("allowed_actions") or []}:
            continue
        route_refs = _mapping(owner_route.get("source_refs"))
        basis = _mapping(route_refs.get("owner_route_currentness_basis"))
        route_work_unit_id = (
            _text(route_refs.get("work_unit_id"))
            or _text(basis.get("work_unit_id"))
            or _text(owner_route.get("owner_reason"))
        )
        if route_work_unit_id != work_unit_id:
            continue
        return {
            "owner_route": owner_route,
            "actions": [{"action_type": "run_quality_repair_batch"}],
        }
    return None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["route_and_consume_current_execution_receipt"]
