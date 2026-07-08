from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.guarded_apply_owner_delta_contract import (
    GUARDED_APPLY_ACCEPTED_ANSWER_SHAPES,
    GUARDED_APPLY_DESIRED_DELTA,
    GUARDED_APPLY_STAGE_ID,
    guarded_apply_current_owner_delta_validation,
    guarded_apply_identity_typed_blocker,
    normalize_guarded_apply_current_owner_delta,
)

from .primitives import mapping as _mapping
from .primitives import text as _text
from .primitives import text_items as _text_items


def stage_owner_answer_typed_blocker(progress: Mapping[str, Any]) -> dict[str, Any] | None:
    delta = stage_current_owner_delta(progress)
    if not stage_delta_is_typed_blocker_owner_answer(progress=progress, delta=delta):
        return None
    reason = (
        _text(delta.get("reason"))
        or _text(delta.get("blocker_id"))
        or _text(delta.get("blocker_type"))
        or "typed_blocker"
    )
    source_ref = _text(delta.get("latest_owner_answer_ref")) or _text(delta.get("source_ref"))
    work_unit = _text(delta.get("action")) or _text(delta.get("action_type"))
    return {
        "blocker_type": reason,
        "blocker_id": reason,
        "owner": _text(delta.get("owner")) or "MedAutoScience",
        "work_unit_id": work_unit,
        "source_ref": source_ref,
        "latest_owner_answer_ref": source_ref,
        "latest_owner_answer_kind": "typed_blocker",
        "acceptance_refs": _text_items(delta.get("acceptance_refs")),
    }


def stage_owner_answer_missing_action(progress: Mapping[str, Any]) -> dict[str, Any] | None:
    delta = stage_current_owner_delta(progress)
    if not stage_delta_requires_mas_owner_answer(delta):
        return None
    validation = guarded_apply_current_owner_delta_validation(delta)
    if validation.get("valid") is not True:
        return None
    normalized = normalize_guarded_apply_current_owner_delta(_mapping(validation.get("normalized")) or delta)
    stage_id = _text(normalized.get("stage_id")) or _text(progress.get("current_stage")) or GUARDED_APPLY_STAGE_ID
    desired_delta = _text(normalized.get("desired_delta")) or GUARDED_APPLY_DESIRED_DELTA
    accepted_return_shape = list(
        dict.fromkeys(
            [
                *_text_items(normalized.get("accepted_answer_shape")),
                *GUARDED_APPLY_ACCEPTED_ANSWER_SHAPES,
            ]
        )
    )
    work_unit_fingerprint = (
        _text(normalized.get("work_unit_fingerprint"))
        or _text(normalized.get("source_fingerprint"))
        or _text(normalized.get("lineage_ref"))
    )
    owner = _text(normalized.get("owner")) or _text(normalized.get("current_owner")) or "med-autoscience"
    return {
        "source": "stage_kernel_projection.current_owner_delta",
        "source_surface": "stage_kernel_projection.current_owner_delta",
        "stage_id": stage_id,
        "action_type": _text(normalized.get("action")) or stage_id,
        "owner": owner,
        "next_owner": owner,
        "recommended_owner": owner,
        "work_unit_id": desired_delta,
        "next_work_unit": desired_delta,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": work_unit_fingerprint,
        "required_delta_kind": desired_delta,
        "owner_receipt_required": True,
        "input_refs": _text_items(normalized.get("input_refs")),
        "acceptance_refs": _text_items(normalized.get("acceptance_refs")),
        "required_output_contract": {
            "owner_receipt_required": True,
            "quality_gate_receipt_accepted": True,
            "typed_blocker_accepted": True,
            "human_gate_accepted": True,
            "route_back_evidence_accepted": True,
            "accepted_return_shape": accepted_return_shape,
            "desired_delta": desired_delta,
            "latest_owner_answer_ref": _text(normalized.get("latest_owner_answer_ref")),
            "domain_ready_authorized": normalized.get("domain_ready_authorized") is True,
        },
        "owner_route_currentness_basis": {
            "source": "stage_kernel_projection.current_owner_delta",
            "stage_id": stage_id,
            "lineage_ref": _text(normalized.get("lineage_ref")),
            "work_unit_id": desired_delta,
            "work_unit_fingerprint": work_unit_fingerprint,
            "owner_answer_missing": True,
        },
        "owner_answer_missing": True,
        "owner_answer_still_required": True,
        "latest_owner_answer_ref": _text(normalized.get("latest_owner_answer_ref")),
    }


def stage_owner_answer_identity_typed_blocker(progress: Mapping[str, Any]) -> dict[str, Any] | None:
    delta = stage_current_owner_delta(progress)
    if not stage_delta_requires_mas_owner_answer(delta, allow_invalid_owner_answer_fields=True):
        return None
    blocker = guarded_apply_identity_typed_blocker(delta)
    if blocker is None:
        return None
    normalized = normalize_guarded_apply_current_owner_delta(delta)
    return {
        **blocker,
        "blocker_type": "current_owner_delta_identity_missing_or_invalid",
        "work_unit_id": _text(normalized.get("desired_delta")) or GUARDED_APPLY_DESIRED_DELTA,
        "stage_id": _text(normalized.get("stage_id")) or GUARDED_APPLY_STAGE_ID,
        "source_ref": _text(normalized.get("lineage_ref")),
        "missing_required_fields": list(
            _mapping(blocker.get("current_owner_delta_validation")).get("missing_required_fields") or []
        ),
    }


def stage_delta_requires_mas_owner_answer(
    delta: Mapping[str, Any],
    *,
    allow_invalid_owner_answer_fields: bool = False,
) -> bool:
    normalized = normalize_guarded_apply_current_owner_delta(delta)
    if not normalized:
        return False
    hard_gate = _mapping(delta.get("hard_gate"))
    if (
        normalized.get("owner_answer_missing") is not True
        and _text(hard_gate.get("state")) != "owner_answer_missing"
    ):
        return False
    if normalized.get("owner_answer_still_required") is False:
        return False
    if not allow_invalid_owner_answer_fields and _text(normalized.get("latest_owner_answer_ref")) is not None:
        return False
    if _text(normalized.get("stage_id")) != GUARDED_APPLY_STAGE_ID:
        return False
    if _text(normalized.get("desired_delta")) != GUARDED_APPLY_DESIRED_DELTA:
        return False
    owner = _text(normalized.get("owner")) or _text(normalized.get("current_owner"))
    return owner in {"med-autoscience", "MedAutoScience", None}


def stage_delta_is_typed_blocker_owner_answer(
    *,
    progress: Mapping[str, Any],
    delta: Mapping[str, Any],
) -> bool:
    hard_gate = _mapping(delta.get("hard_gate"))
    if _text(hard_gate.get("state")) == "domain_owner_answer_recorded":
        answer_kind = (
            _text(hard_gate.get("owner_answer_kind"))
            or _text(delta.get("latest_owner_answer_kind"))
            or _text(delta.get("source_kind"))
        )
        return answer_kind == "typed_blocker"
    stage_kernel = _mapping(progress.get("stage_kernel_projection"))
    stage_run_kernel = _mapping(stage_kernel.get("stage_run_kernel"))
    return (
        _text(stage_run_kernel.get("status")) == "TypedBlocked"
        and _text(delta.get("source_kind")) == "typed_blocker"
        and _text(delta.get("source_ref")) is not None
    )


def stage_current_owner_delta(progress: Mapping[str, Any]) -> dict[str, Any]:
    direct = _mapping(progress.get("current_owner_delta"))
    if direct:
        return direct
    stage_kernel = _mapping(progress.get("stage_kernel_projection"))
    delta = _mapping(stage_kernel.get("current_owner_delta"))
    if delta:
        return delta
    stage_run_kernel = _mapping(stage_kernel.get("stage_run_kernel"))
    return _mapping(stage_run_kernel.get("current_owner_delta"))


__all__ = [
    "stage_current_owner_delta",
    "stage_delta_is_typed_blocker_owner_answer",
    "stage_delta_requires_mas_owner_answer",
    "stage_owner_answer_identity_typed_blocker",
    "stage_owner_answer_missing_action",
    "stage_owner_answer_typed_blocker",
]
