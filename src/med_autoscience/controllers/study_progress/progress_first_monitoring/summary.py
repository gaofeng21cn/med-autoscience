from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.next_action_envelope import SURFACE_KIND
from med_autoscience.paper_mission_opl_readback.receipt_events import (
    matches_opl_transition_receipt,
)


def build_progress_first_monitoring_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    next_action = _mapping(payload.get("next_action"))
    if _text(next_action.get("surface_kind")) != SURFACE_KIND:
        next_action = {}
    receipt = _transition_receipt(payload)
    typed_blocker = _mapping(payload.get("typed_blocker"))
    owner_receipt = _mapping(payload.get("owner_receipt")) or _mapping(
        payload.get("owner_callable_receipt_consumption")
    )
    status = (
        "typed_blocked"
        if typed_blocker
        else "owner_receipt_recorded"
        if owner_receipt
        else "runtime_receipt_recorded"
        if receipt
        else "next_action_ready"
        if next_action
        else "awaiting_stage_outcome"
    )
    return {
        "surface_kind": "progress_first_monitoring_summary",
        "schema_version": 2,
        "status": status,
        "study_id": _text(payload.get("study_id")),
        "stage_id": _text(next_action.get("stage_id")),
        "next_action": next_action or None,
        "next_owner": _text(next_action.get("owner")),
        "action_family": _text(next_action.get("action_family")),
        "opl_transition_receipt": receipt or None,
        "typed_blocker": typed_blocker or None,
        "owner_receipt": owner_receipt or None,
        "authority_boundary": {
            "next_action_authority": "StageOutcome -> NextActionEnvelope",
            "runtime_receipt_authority": "one-person-lab",
            "domain_outcome_authority": "MedAutoScience",
            "projection_can_select_next_action": False,
            "projection_can_authorize_runtime": False,
        },
    }


def _transition_receipt(payload: Mapping[str, Any]) -> dict[str, Any]:
    carrier = _request_carrier(payload)
    if not carrier:
        return {}
    for value in (
        payload.get("opl_transition_receipt"),
        _mapping(payload.get("domain_transition")).get("opl_transition_receipt"),
        _mapping(payload.get("paper_mission_transaction_readback")).get("opl_transition_receipt"),
    ):
        receipt = _mapping(value)
        if matches_opl_transition_receipt(receipt=receipt, carrier=carrier):
            return receipt
    return {}


def _request_carrier(payload: Mapping[str, Any]) -> dict[str, Any]:
    for source in (
        payload,
        _mapping(payload.get("domain_transition")),
        _mapping(payload.get("paper_mission_transaction_readback")),
    ):
        carrier = _mapping(source.get("opl_runtime_carrier"))
        if carrier:
            return carrier
    return {}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["build_progress_first_monitoring_summary"]
