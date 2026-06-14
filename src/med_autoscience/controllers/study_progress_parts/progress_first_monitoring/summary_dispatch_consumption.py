from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.progress_first_receipt_identity import (
    canonical_work_unit_identity_from_completion,
    consumed_ai_reviewer_receipt_matches_transition_work_unit,
    gate_clearing_batch_receipt_consumption_for_transition,
)

from .primitives import _mapping, _numeric, _text
from .summary_work_units import work_unit_projection as _work_unit_projection


def dispatch_consumption_summary(
    *,
    handoff: Mapping[str, Any],
    execution: Mapping[str, Any],
    domain_transition: Mapping[str, Any],
) -> dict[str, Any] | None:
    explicit = _mapping(handoff.get("dispatch_consumption")) or _mapping(execution.get("dispatch_consumption"))
    if explicit:
        return explicit
    completion_receipt = _mapping(domain_transition.get("completion_receipt_consumption"))
    execution_receipt = _mapping(domain_transition.get("default_executor_execution_receipt_consumption"))
    if completion_receipt or execution_receipt:
        status = (
            _text(completion_receipt.get("consumption_status"))
            or _text(completion_receipt.get("status"))
            or _text(execution_receipt.get("consumption_status"))
            or _text(execution_receipt.get("status"))
            or "receipt_consumed"
        )
        identity = canonical_work_unit_identity_from_completion(completion_receipt or execution_receipt)
        return {
            "consumption_status": status,
            "receipt_ref": _text(completion_receipt.get("receipt_ref")) or _text(execution_receipt.get("receipt_ref")),
            "receipt_kind": _text(completion_receipt.get("receipt_kind")) or _text(execution_receipt.get("receipt_kind")),
            "execution_status": _text(execution_receipt.get("execution_status")),
            "action_fingerprint": _text(completion_receipt.get("action_fingerprint"))
            or _text(execution_receipt.get("action_fingerprint")),
            "work_unit_id": _text(identity.get("work_unit_id")),
            "work_unit_fingerprint": _text(identity.get("work_unit_fingerprint")),
            "canonical_work_unit_identity": identity or None,
        }
    queue_item = _first_action_queue_item(handoff.get("action_queue"))
    if queue_item is None:
        return None
    return {
        "consumption_status": _text(queue_item.get("consumption_status")) or "unconsumed",
        "action_fingerprint": _text(queue_item.get("action_fingerprint"))
        or _text(queue_item.get("work_unit_fingerprint"))
        or _text(queue_item.get("source_fingerprint")),
        "receipt_ref": _text(queue_item.get("receipt_ref")),
        "execution_status": _text(queue_item.get("execution_status")),
        "unconsumed_duration_hours": _numeric(queue_item.get("queue_age_hours"))
        or _numeric(queue_item.get("unconsumed_duration_hours")),
    }


def gate_clearing_batch_dispatch_consumption(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    domain_transition = _mapping(payload.get("domain_transition"))
    followthrough = _mapping(payload.get("gate_clearing_batch_followthrough"))
    if followthrough:
        record = {
            "status": _text(followthrough.get("status")),
            "source_eval_id": _text(followthrough.get("source_eval_id")),
            "work_unit_id": _text(followthrough.get("work_unit_id")),
            "work_unit_fingerprint": _text(followthrough.get("work_unit_fingerprint")),
            "owner_route_currentness_basis": _mapping(followthrough.get("owner_route_currentness_basis")),
            "work_unit_currentness": _mapping(followthrough.get("work_unit_currentness")),
            "explicit_publication_work_unit": _mapping(followthrough.get("explicit_publication_work_unit")),
        }
        if record.get("source_eval_id") is None:
            record["source_eval_id"] = _text(
                _mapping(_mapping(domain_transition.get("source_refs")).get("owner_route_currentness_basis")).get(
                    "source_eval_id"
                )
            )
        receipt = gate_clearing_batch_receipt_consumption_for_transition(
            transition=domain_transition,
            record=record,
            receipt_ref=_text(followthrough.get("latest_record_path"))
            or "artifacts/controller/gate_clearing_batch/latest.json",
        )
        if receipt is not None:
            return receipt
    return None


def transition_consumed_owner_action(domain_transition: Mapping[str, Any]) -> bool:
    if _mapping(domain_transition.get("typed_blocker")):
        return False
    completion = _mapping(domain_transition.get("completion_receipt_consumption"))
    if _text(completion.get("status")) not in {"consumed", "receipt_consumed", "completed"}:
        return False
    if _consumed_receipt_matches_transition_work_unit(domain_transition=domain_transition, completion=completion):
        return False
    return (
        _text(domain_transition.get("owner")) is not None
        or _text(domain_transition.get("controller_action")) is not None
        or _work_unit_projection(domain_transition.get("next_work_unit")) is not None
    )


def transition_receipt_consumed(domain_transition: Mapping[str, Any]) -> bool:
    completion = _mapping(domain_transition.get("completion_receipt_consumption"))
    execution = _mapping(domain_transition.get("default_executor_execution_receipt_consumption"))
    status = (
        _text(completion.get("consumption_status"))
        or _text(completion.get("status"))
        or _text(execution.get("consumption_status"))
        or _text(execution.get("status"))
    )
    return status in {"consumed", "receipt_consumed", "completed"}


def transition_consumed_same_ai_reviewer_work_unit(domain_transition: Mapping[str, Any]) -> bool:
    completion = _mapping(domain_transition.get("completion_receipt_consumption"))
    if _text(completion.get("status")) not in {"consumed", "receipt_consumed", "completed"}:
        return False
    return _consumed_receipt_matches_transition_work_unit(
        domain_transition=domain_transition,
        completion=completion,
    )


def _consumed_receipt_matches_transition_work_unit(
    *,
    domain_transition: Mapping[str, Any],
    completion: Mapping[str, Any],
) -> bool:
    return consumed_ai_reviewer_receipt_matches_transition_work_unit(
        transition=domain_transition,
        completion=completion,
    )


def _first_action_queue_item(value: object) -> dict[str, Any] | None:
    if not isinstance(value, list):
        return None
    for item in value:
        if isinstance(item, Mapping):
            return dict(item)
    return None


def first_current_action_queue_item(value: object) -> dict[str, Any] | None:
    if not isinstance(value, list):
        return None
    for item in value:
        if not isinstance(item, Mapping):
            continue
        payload = dict(item)
        consumption = _mapping(payload.get("consumption"))
        status = _text(payload.get("consumption_status")) or _text(consumption.get("status"))
        if status in {"consumed", "receipt_consumed", "completed"}:
            continue
        return payload
    return None


__all__ = [
    "dispatch_consumption_summary",
    "first_current_action_queue_item",
    "gate_clearing_batch_dispatch_consumption",
    "transition_consumed_owner_action",
    "transition_consumed_same_ai_reviewer_work_unit",
    "transition_receipt_consumed",
]
