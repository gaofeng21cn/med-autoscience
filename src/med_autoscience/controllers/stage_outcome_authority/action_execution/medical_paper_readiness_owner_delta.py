from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import medical_paper_readiness as readiness_surface


def build_owner_delta_result(
    *,
    study_id: str,
    study_root: Path,
    owner_result: Mapping[str, Any],
    closeout_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    quality_gate_receipt = _quality_gate_receipt(study_root=study_root, owner_result=owner_result)
    typed_blocker = _typed_blocker(owner_result)
    quality_gate_refs = _quality_gate_receipt_refs(quality_gate_receipt)
    stable_blocker_refs = _stable_typed_blocker_refs(owner_result)
    result_kind = _owner_delta_result_kind(
        readiness_status=_text(owner_result.get("readiness_status")),
        quality_gate_refs=quality_gate_refs,
        stable_blocker_refs=stable_blocker_refs,
    )
    result = {
        "surface_kind": "mas_current_owner_delta_result",
        "study_id": study_id,
        "owner": "MedAutoScience",
        "result_kind": result_kind,
        "required_return_shape_satisfied": result_kind in {
            "owner_receipt",
            "quality_gate_receipt",
            "quality_gate_receipt_with_stable_typed_blocker",
            "stable_typed_blocker",
        },
        "owner_receipt_refs": quality_gate_refs if result_kind == "owner_receipt" else [],
        "quality_gate_receipt_refs": quality_gate_refs,
        "stable_typed_blocker_refs": stable_blocker_refs,
        "quality_gate_receipt": quality_gate_receipt or None,
        "typed_blocker": typed_blocker or None,
        "body_included": False,
        "authority_boundary": {
            "owner": "med-autoscience",
            "writes_publication_eval": False,
            "writes_controller_decision": bool(stable_blocker_refs),
            "writes_paper_or_package": False,
            "writes_memory_body": False,
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    }
    if closeout_binding:
        binding = dict(closeout_binding)
        result["closeout_binding"] = binding
        result["stage_run_id"] = _text(binding.get("stage_run_id"))
        result["stage_manifest_ref"] = _text(binding.get("stage_manifest_ref"))
        result["current_pointer_ref"] = _text(binding.get("current_pointer_ref"))
        result["source_fingerprint"] = _text(binding.get("source_fingerprint"))
        result["idempotency_key"] = _text(binding.get("idempotency_key"))
    return result


def _owner_delta_result_kind(
    *,
    readiness_status: str | None,
    quality_gate_refs: list[str],
    stable_blocker_refs: list[str],
) -> str:
    if readiness_status == "ready" and quality_gate_refs:
        return "owner_receipt"
    if quality_gate_refs and stable_blocker_refs:
        return "quality_gate_receipt_with_stable_typed_blocker"
    if quality_gate_refs:
        return "quality_gate_receipt"
    if stable_blocker_refs:
        return "stable_typed_blocker"
    return "missing_owner_delta_result"


def _quality_gate_receipt(*, study_root: Path, owner_result: Mapping[str, Any]) -> dict[str, Any]:
    action_result = _mapping(owner_result.get("guarded_operator_action_result"))
    if not action_result:
        return {}
    return {
        "surface_kind": "medical_paper_readiness_quality_gate_receipt",
        "readiness_ref": _text(owner_result.get("readiness_ref"))
        or str(readiness_surface.stable_medical_paper_readiness_path(study_root=study_root)),
        "readiness_status": _text(owner_result.get("readiness_status")),
        "completed_surface_key": _text(owner_result.get("completed_surface_key")),
        "action_result_ref": _text(action_result.get("action_result_ref")),
        "durable_ref": _text(action_result.get("durable_ref")),
        "replay_ref": _text(action_result.get("replay_ref")),
        "action_status": _text(action_result.get("status")),
        "missing_reason": _text(action_result.get("missing_reason")),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _quality_gate_receipt_refs(receipt: Mapping[str, Any]) -> list[str]:
    refs = [
        _text(receipt.get("readiness_ref")),
        _text(receipt.get("action_result_ref")),
    ]
    return [ref for ref in refs if ref]


def _stable_typed_blocker_refs(owner_result: Mapping[str, Any]) -> list[str]:
    blocker = _mapping(owner_result.get("owner_blocker"))
    ref = _text(blocker.get("controller_decision_ref"))
    if ref and blocker.get("will_write_controller_decision") is True:
        return [ref]
    return []


def _typed_blocker(owner_result: Mapping[str, Any]) -> dict[str, Any]:
    blocker = _mapping(owner_result.get("owner_blocker"))
    controller_decision = _mapping(blocker.get("controller_decision"))
    controller_blocker = _mapping(controller_decision.get("controller_blocker"))
    if controller_blocker:
        return controller_blocker
    if _text(owner_result.get("status")) == "typed_blocker_or_stop_loss":
        return {
            "blocker_id": _text(owner_result.get("requested_surface_key"))
            or "medical_paper_readiness_surface_input_required",
            "owner": "MedAutoScience",
            "write_permitted": False,
        }
    return {}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["build_owner_delta_result"]
