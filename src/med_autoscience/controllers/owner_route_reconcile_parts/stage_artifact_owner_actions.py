from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from med_autoscience.controllers.default_executor_action_policy import (
    request_output_surface_for_action_type,
)


ACTION_TYPE = "publication_handoff_owner_gate"
OWNER = "publication_gate_owner"


def terminal_publication_handoff_action(progress: Mapping[str, Any]) -> dict[str, Any] | None:
    index = _mapping(progress.get("stage_artifact_index"))
    if _text(index.get("surface_kind")) != "stage_artifact_index":
        return None
    owner_action = _mapping(index.get("next_owner_action"))
    if _text(owner_action.get("action_type")) != ACTION_TYPE:
        return None
    if owner_action.get("terminal_publication_handoff") is not True and (
        _text(owner_action.get("required_delta_kind"))
        != "publication_handoff_owner_receipt_or_typed_blocker"
    ):
        return None
    work_unit_id = _text(owner_action.get("work_unit_id")) or ACTION_TYPE
    current_stage = _stage_id(index.get("current_stage")) or "08-publication_package_handoff"
    owner = _text(owner_action.get("next_owner")) or OWNER
    contract_refs = _stage_artifact_contract_refs(owner_action)
    return {
        "action_type": ACTION_TYPE,
        "authority": "observability_only",
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "reason": ACTION_TYPE,
        "summary": "Evaluate terminal publication handoff and write an owner receipt or stable typed blocker.",
        "required_output_surface": _text(owner_action.get("required_output_surface"))
        or request_output_surface_for_action_type(ACTION_TYPE),
        "work_unit_id": work_unit_id,
        "next_work_unit": work_unit_id,
        "work_unit_fingerprint": _text(owner_action.get("work_unit_fingerprint"))
        or f"stage-artifact-index::{current_stage}::{work_unit_id}",
        "source_ref": _text(owner_action.get("source_ref"))
        or _text(owner_action.get("manifest_ref"))
        or _text(owner_action.get("receipt_ref")),
        "source_surface": "stage_artifact_index.next_owner_action",
        "stage_artifact_index_source": "stage_artifact_index.next_owner_action",
        "stage_artifact_current_stage": current_stage,
        "stage_artifact_contract_refs": contract_refs,
        "required_delta_kind": _text(owner_action.get("required_delta_kind")),
        "target_surface": _mapping(owner_action.get("target_surface")) or None,
        "artifact_first_authority": True,
        "terminal_publication_handoff": True,
        "owner_receipt_required": owner_action.get("owner_receipt_required") is not False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
        "can_authorize_submission_ready": False,
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }


def action_queue_with_terminal_publication_handoff(
    *,
    actions: list[dict[str, Any]],
    progress: Mapping[str, Any],
    study_id: str,
    quest_id: str | None,
    decorate_action: Callable[..., dict[str, Any]],
) -> list[dict[str, Any]]:
    action = terminal_publication_handoff_action(progress)
    if action is None:
        return actions
    return [decorate_action(study_id=study_id, quest_id=quest_id, action=action)]


def projection_fields(progress: Mapping[str, Any]) -> dict[str, Any]:
    stage_artifact_index = _mapping(progress.get("stage_artifact_index"))
    current_action = _mapping(progress.get("current_executable_owner_action"))
    result: dict[str, Any] = {}
    if _text(stage_artifact_index.get("surface_kind")) == "stage_artifact_index":
        result["stage_artifact_index"] = stage_artifact_index
    if _text(current_action.get("surface_kind")) == "current_executable_owner_action":
        result["current_executable_owner_action"] = current_action
    return result


def _stage_artifact_contract_refs(owner_action: Mapping[str, Any]) -> dict[str, str]:
    refs = {
        "manifest_ref": _text(owner_action.get("manifest_ref")),
        "receipt_ref": _text(owner_action.get("receipt_ref")),
        "artifact_native_contract_ref": _text(owner_action.get("artifact_native_contract_ref")),
        "domain_stage_pack_ref": _text(owner_action.get("domain_stage_pack_ref")),
    }
    return {key: value for key, value in refs.items() if value is not None}


def _stage_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("stage_id"))
    return _text(value)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "ACTION_TYPE",
    "OWNER",
    "action_queue_with_terminal_publication_handoff",
    "projection_fields",
    "terminal_publication_handoff_action",
]
