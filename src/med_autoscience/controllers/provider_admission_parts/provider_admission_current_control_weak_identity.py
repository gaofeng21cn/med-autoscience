from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.provider_admission_parts.managed_wakeup import _non_empty_text
from med_autoscience.controllers.provider_admission_parts.provider_admission_helpers import (
    mapping as _mapping,
)


def weak_provider_admission_identity(identity: Mapping[str, Any]) -> dict[str, Any]:
    missing: list[str] = []
    for key in ("study_id", "action_type", "work_unit_id"):
        if _non_empty_text(identity.get(key)) is None:
            missing.append(key)
    if (
        _non_empty_text(identity.get("work_unit_fingerprint")) is None
        and _non_empty_text(identity.get("action_fingerprint")) is None
    ):
        missing.append("work_unit_fingerprint")
    if (
        _non_empty_text(identity.get("dispatch_path")) is None
        and _non_empty_text(identity.get("dispatch_ref")) is None
    ):
        missing.append("dispatch_path_or_ref")
    if _non_empty_text(identity.get("route_identity_key")) is None:
        missing.append("route_identity_key")
    if _non_empty_text(identity.get("attempt_idempotency_key")) is None:
        missing.append("attempt_idempotency_key")
    stage_packet_refs = [
        item
        for item in identity.get("stage_packet_refs") or []
        if _non_empty_text(item) is not None
    ]
    if (
        _non_empty_text(identity.get("stage_packet_ref")) is None
        and not stage_packet_refs
        and not _identity_is_strong_current_owner_delta(identity)
    ):
        missing.append("stage_packet_ref_or_refs")
    if not currentness_basis_strong(_mapping(identity.get("currentness_basis"))):
        missing.append("currentness_basis")
    if not missing:
        return {}
    return {
        "status": "weak_provider_admission_identity",
        "missing_identity_fields": missing,
    }


def currentness_basis_strong(basis: Mapping[str, Any]) -> bool:
    if _non_empty_text(basis.get("work_unit_id")) is None:
        return False
    if _non_empty_text(basis.get("work_unit_fingerprint")) is None:
        return False
    if _non_empty_text(basis.get("truth_epoch")) is None:
        return False
    return (
        _non_empty_text(basis.get("runtime_health_epoch")) is not None
        or _non_empty_text(basis.get("source_eval_id")) is not None
    )


def _identity_is_strong_current_owner_delta(identity: Mapping[str, Any]) -> bool:
    if (
        _non_empty_text(identity.get("source"))
        != "opl_current_control_state.study_current_executable_owner_action"
    ):
        return False
    if _non_empty_text(identity.get("next_executable_owner")) != "write":
        return False
    basis = _mapping(identity.get("currentness_basis"))
    source = _non_empty_text(basis.get("current_action_source")) or _non_empty_text(
        basis.get("current_work_unit_source")
    )
    if source not in {
        "publication_eval.recommended_actions.readiness_blocker_repair",
        "gate_clearing_batch_followthrough.actionable_current_work_unit",
    }:
        return False
    return currentness_basis_strong(basis)


__all__ = [
    "currentness_basis_strong",
    "weak_provider_admission_identity",
]
