from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.provider_admission.managed_wakeup import _non_empty_text
from med_autoscience.controllers.provider_admission.provider_admission_helpers import (
    mapping as _mapping,
)


def candidate_with_current_action_identity(
    candidate: Mapping[str, Any],
    *,
    current_action_identity: Mapping[str, Any] | None,
) -> dict[str, Any]:
    payload = dict(candidate)
    if not current_action_identity:
        return payload
    fingerprint = _non_empty_text(payload.get("work_unit_fingerprint")) or _non_empty_text(
        payload.get("action_fingerprint")
    )
    if fingerprint is None:
        return payload
    if _non_empty_text(payload.get("route_identity_key")) is None:
        study_id = _non_empty_text(payload.get("study_id"))
        if study_id is not None:
            payload["route_identity_key"] = f"provider-admission::{study_id}::{fingerprint}"
    if _non_empty_text(payload.get("attempt_idempotency_key")) is None and _non_empty_text(
        payload.get("route_identity_key")
    ) is not None:
        payload["attempt_idempotency_key"] = _non_empty_text(payload.get("route_identity_key"))
    currentness_basis = _mapping(payload.get("currentness_basis"))
    current_basis = _mapping(current_action_identity.get("currentness_basis"))
    if current_basis:
        payload["currentness_basis"] = {
            **dict(currentness_basis),
            **dict(current_basis),
            "work_unit_id": _non_empty_text(currentness_basis.get("work_unit_id"))
            or _non_empty_text(current_action_identity.get("work_unit_id"))
            or _non_empty_text(payload.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(currentness_basis.get("work_unit_fingerprint"))
            or fingerprint,
            "source_eval_id": _non_empty_text(currentness_basis.get("source_eval_id"))
            or _non_empty_text(current_basis.get("source_eval_id")),
        }
    return payload


__all__ = ["candidate_with_current_action_identity"]
