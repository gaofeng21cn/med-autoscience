from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.ai_route_context import is_nonbinding_codex_route_context
from med_autoscience.paper_mission_stage_run_readback.receipt_events import (
    matches_opl_stage_attempt_receipt,
)


def build_progress_first_monitoring_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    route_context = _mapping(payload.get("ai_route_context")) or _mapping(
        payload.get("next_action")
    )
    if not is_nonbinding_codex_route_context(route_context):
        route_context = {}
    receipt = _stage_attempt_receipt(payload)
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
        else "route_context_available"
        if route_context
        else "awaiting_stage_outcome"
    )
    return {
        "surface_kind": "progress_first_monitoring_summary",
        "schema_version": 2,
        "status": status,
        "study_id": _text(payload.get("study_id")),
        "stage_id": _text(route_context.get("stage_id")),
        "codex_route_context": route_context or None,
        "next_owner_hint": _text(route_context.get("owner")),
        "action_family_hint": _text(route_context.get("action_family")),
        "opl_stage_attempt_receipt": receipt or None,
        "typed_blocker": typed_blocker or None,
        "owner_receipt": owner_receipt or None,
        "authority_boundary": {
            "next_action_authority": "codex_cli",
            "route_context_role": "nonbinding_context_only",
            "runtime_receipt_authority": "one-person-lab",
            "domain_outcome_authority": "MedAutoScience",
            "projection_can_select_next_action": False,
            "projection_can_authorize_runtime": False,
        },
    }


def _stage_attempt_receipt(payload: Mapping[str, Any]) -> dict[str, Any]:
    carrier = _request_carrier(payload)
    if not carrier:
        return {}
    for value in (
        payload.get("opl_stage_attempt_receipt"),
        _mapping(payload.get("domain_transition")).get("opl_stage_attempt_receipt"),
        _mapping(payload.get("paper_mission_transaction_readback")).get("opl_stage_attempt_receipt"),
    ):
        receipt = _mapping(value)
        if matches_opl_stage_attempt_receipt(receipt=receipt, carrier=carrier):
            return receipt
    return {}


def _request_carrier(payload: Mapping[str, Any]) -> dict[str, Any]:
    for source in (
        payload,
        _mapping(payload.get("domain_transition")),
        _mapping(payload.get("paper_mission_transaction_readback")),
    ):
        carrier = _mapping(source.get("opl_stage_run_context"))
        if carrier:
            return carrier
    return {}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["build_progress_first_monitoring_summary"]
