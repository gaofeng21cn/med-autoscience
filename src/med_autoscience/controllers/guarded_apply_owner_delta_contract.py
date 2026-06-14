from __future__ import annotations

from collections.abc import Mapping
from typing import Any


GUARDED_APPLY_STAGE_ID = "paper_autonomy/guarded-apply"
GUARDED_APPLY_DESIRED_DELTA = "domain_owner_receipt_quality_gate_or_typed_blocker_required"
GUARDED_APPLY_ACCEPTED_ANSWER_SHAPES = (
    "domain_owner_receipt_ref",
    "quality_gate_receipt_ref",
    "typed_blocker_ref",
    "human_gate_ref",
    "route_back_evidence_ref",
)


def guarded_apply_current_owner_delta_contract() -> dict[str, Any]:
    return {
        "surface_kind": "mas_expected_opl_current_owner_delta",
        "default_planning_root": "current_owner_delta",
        "stage_id": GUARDED_APPLY_STAGE_ID,
        "current_owner": "med-autoscience",
        "desired_delta": GUARDED_APPLY_DESIRED_DELTA,
        "desired_delta_kind": "owner_answer_or_typed_blocker",
        "accepted_answer_shape": list(GUARDED_APPLY_ACCEPTED_ANSWER_SHAPES),
        "accepted_return_shapes": list(GUARDED_APPLY_ACCEPTED_ANSWER_SHAPES),
        "owner_answer_missing": True,
        "owner_answer_still_required": True,
        "domain_ready_authorized": False,
        "authority_boundary": {
            "opl_can_write_domain_truth": False,
            "opl_can_create_domain_owner_receipt": False,
            "opl_can_create_quality_gate_receipt": False,
            "opl_can_create_typed_blocker": False,
            "provider_completion_is_domain_ready": False,
            "mas_domain_owner_answer_required": True,
        },
    }


def normalize_guarded_apply_current_owner_delta(value: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = _mapping(value)
    if not payload:
        return {}
    hard_gate = _mapping(payload.get("hard_gate"))
    latest_owner_answer_ref = _optional_text(payload.get("latest_owner_answer_ref")) or _optional_text(
        hard_gate.get("owner_answer_ref")
    )
    accepted_shape = _string_list(payload.get("accepted_answer_shape")) or _string_list(
        payload.get("accepted_return_shapes")
    )
    owner_answer_missing = _bool_value(payload.get("owner_answer_missing"))
    if owner_answer_missing is None:
        owner_answer_missing = _bool_value(hard_gate.get("owner_answer_missing"))
    if (
        owner_answer_missing is None
        and latest_owner_answer_ref is None
        and _optional_text(hard_gate.get("state")) in {
        "owner_delta_open",
        "owner_answer_missing",
        }
    ):
        owner_answer_missing = latest_owner_answer_ref is None
    owner_answer_still_required = _bool_value(payload.get("owner_answer_still_required"))
    if owner_answer_still_required is None:
        owner_answer_still_required = _bool_value(hard_gate.get("owner_answer_still_required"))
    if owner_answer_still_required is None:
        owner_answer_still_required = _bool_value(hard_gate.get("human_or_domain_owner_required"))
    domain_ready_authorized = payload.get("domain_ready_authorized")
    if not isinstance(domain_ready_authorized, bool):
        domain_ready_authorized = hard_gate.get("domain_ready_authorized")
    result = {
        key: item
        for key, item in {
            "surface_kind": _optional_text(payload.get("surface_kind")) or "opl_current_owner_delta",
            "default_planning_root": _optional_text(payload.get("default_planning_root")),
            "stage_id": _optional_text(payload.get("stage_id")),
            "lineage_ref": _optional_text(payload.get("lineage_ref")),
            "owner": _optional_text(payload.get("owner")) or _optional_text(payload.get("current_owner")),
            "current_owner": _optional_text(payload.get("current_owner")) or _optional_text(payload.get("owner")),
            "action": _optional_text(payload.get("action")) or _optional_text(payload.get("action_type")),
            "desired_delta": _optional_text(payload.get("desired_delta"))
            or _optional_text(payload.get("desired_delta_description"))
            or _optional_text(payload.get("payload_requirement")),
            "desired_delta_kind": _optional_text(payload.get("desired_delta_kind")),
            "accepted_answer_shape": accepted_shape,
            "accepted_return_shapes": accepted_shape,
            "latest_owner_answer_ref": latest_owner_answer_ref,
            "domain_ready_authorized": domain_ready_authorized
            if isinstance(domain_ready_authorized, bool)
            else None,
            "owner_answer_missing": owner_answer_missing,
            "owner_answer_still_required": owner_answer_still_required,
            "hard_gate": dict(hard_gate) if hard_gate else None,
        }.items()
        if item not in (None, [], {})
    }
    return result if _optional_text(result.get("stage_id")) is not None else {}


def guarded_apply_current_owner_delta_validation(
    value: Mapping[str, Any] | None,
    *,
    require_lineage_ref: bool = True,
) -> dict[str, Any]:
    delta = normalize_guarded_apply_current_owner_delta(value)
    missing: list[str] = []
    if not delta:
        missing.append("current_owner_delta")
    if _optional_text(delta.get("stage_id")) != GUARDED_APPLY_STAGE_ID:
        missing.append("stage_id")
    if _optional_text(delta.get("desired_delta")) != GUARDED_APPLY_DESIRED_DELTA:
        missing.append("desired_delta")
    if require_lineage_ref and _optional_text(delta.get("lineage_ref")) is None:
        missing.append("lineage_ref")
    latest_owner_answer_ref = _optional_text(delta.get("latest_owner_answer_ref"))
    if latest_owner_answer_ref is not None:
        missing.append("latest_owner_answer_ref_must_be_null")
    if latest_owner_answer_ref is None and delta.get("owner_answer_missing") is not True:
        missing.append("owner_answer_missing")
    if delta.get("owner_answer_still_required") is False:
        missing.append("owner_answer_still_required")
    if delta.get("domain_ready_authorized") is not False:
        missing.append("domain_ready_authorized_false")
    owner = _optional_text(delta.get("owner")) or _optional_text(delta.get("current_owner"))
    if owner not in {"med-autoscience", "MedAutoScience", None}:
        missing.append("owner")
    shapes = set(_string_list(delta.get("accepted_answer_shape")) or _string_list(delta.get("accepted_return_shapes")))
    required_shapes = set(GUARDED_APPLY_ACCEPTED_ANSWER_SHAPES)
    missing.extend(f"accepted_answer_shape.{shape}" for shape in sorted(required_shapes - shapes))
    return {
        "valid": not missing,
        "missing_required_fields": missing,
        "normalized": delta,
        "required_stage_id": GUARDED_APPLY_STAGE_ID,
        "required_desired_delta": GUARDED_APPLY_DESIRED_DELTA,
        "required_accepted_answer_shape": list(GUARDED_APPLY_ACCEPTED_ANSWER_SHAPES),
        "require_lineage_ref": require_lineage_ref,
    }


def guarded_apply_current_owner_delta_binding_summary(
    value: Mapping[str, Any] | None,
    *,
    require_lineage_ref: bool = True,
) -> dict[str, Any]:
    validation = guarded_apply_current_owner_delta_validation(
        value,
        require_lineage_ref=require_lineage_ref,
    )
    delta = _mapping(validation.get("normalized"))
    common = {
        "required": True,
        "stage_id": _optional_text(delta.get("stage_id")),
        "lineage_ref": _optional_text(delta.get("lineage_ref")),
        "desired_delta": _optional_text(delta.get("desired_delta")),
        "accepted_answer_shape": _string_list(delta.get("accepted_answer_shape")),
        "latest_owner_answer_ref": _optional_text(delta.get("latest_owner_answer_ref")),
        "domain_ready_authorized": delta.get("domain_ready_authorized") is True,
        "owner_answer_missing": delta.get("owner_answer_missing") is True,
        "owner_answer_still_required": delta.get("owner_answer_still_required") is not False,
        "mas_can_create_owner_answer": True,
        "opl_can_create_owner_answer": False,
    }
    if validation.get("valid") is not True:
        return {
            **common,
            "bound": False,
            "reason": "current_owner_delta_identity_missing_or_invalid",
            "missing_required_fields": list(validation.get("missing_required_fields") or []),
        }
    return {**common, "bound": True}


def guarded_apply_identity_typed_blocker(value: Mapping[str, Any] | None) -> dict[str, Any] | None:
    validation = guarded_apply_current_owner_delta_validation(value)
    if validation.get("valid") is True:
        return None
    return {
        "blocker_id": "current_owner_delta_identity_missing_or_invalid",
        "owner": "med-autoscience",
        "reason": "paper_autonomy/guarded-apply requires a live OPL current_owner_delta identity before MAS can answer.",
        "required_owner_surface": "OPL current_owner_delta / MAS guarded-apply owner-answer work unit",
        "write_permitted": False,
        "current_owner_delta_validation": validation,
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, (list, tuple, set)):
        return []
    return [text for item in value if (text := _optional_text(item)) is not None]


def _bool_value(value: object) -> bool | None:
    return value if isinstance(value, bool) else None
