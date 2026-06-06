from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from med_autoscience.controllers.default_executor_action_policy import (
    request_output_surface_for_action_type,
)


ACTION_TYPE = "publication_handoff_owner_gate"
OWNER = "publication_gate_owner"
READINESS_ACTION_TYPE = "complete_medical_paper_readiness_surface"
READINESS_OWNER = "MedAutoScience"


def typed_blocker_followup_action(progress: Mapping[str, Any]) -> dict[str, Any] | None:
    if _medical_paper_readiness_ready(progress):
        return None
    delta = _current_owner_delta(progress)
    if _text(delta.get("action")) != READINESS_ACTION_TYPE:
        return None
    if _text(delta.get("reason")) != "medical_paper_readiness_not_ready":
        return None
    source_ref = _text(delta.get("source_ref"))
    return {
        "action_type": READINESS_ACTION_TYPE,
        "authority": "mas_owner_surface",
        "owner": _text(delta.get("owner")) or READINESS_OWNER,
        "request_owner": _text(delta.get("owner")) or READINESS_OWNER,
        "recommended_owner": _text(delta.get("owner")) or READINESS_OWNER,
        "reason": _text(delta.get("reason")) or "medical_paper_readiness_not_ready",
        "summary": "Complete the MAS medical-paper readiness surface named by the terminal handoff typed blocker.",
        "required_output_surface": _text(delta.get("required_input")) or READINESS_ACTION_TYPE,
        "work_unit_id": READINESS_ACTION_TYPE,
        "next_work_unit": READINESS_ACTION_TYPE,
        "work_unit_fingerprint": _text(delta.get("delta_id"))
        or f"stage-current-owner-delta::{READINESS_ACTION_TYPE}::{source_ref or 'unknown'}",
        "source_ref": source_ref,
        "source_surface": "stage_kernel_projection.current_owner_delta",
        "blocked_surface": _text(delta.get("blocked_surface")) or ACTION_TYPE,
        "latest_owner_answer_ref": _text(delta.get("latest_owner_answer_ref")) or source_ref,
        "latest_owner_answer_kind": _text(delta.get("latest_owner_answer_kind")) or _text(delta.get("source_kind")),
        "terminal_publication_handoff": False,
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
        "can_authorize_submission_ready": False,
    }


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
    followup = typed_blocker_followup_action(progress)
    if followup is not None:
        return [decorate_action(study_id=study_id, quest_id=quest_id, action=followup)]
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
    followup = typed_blocker_followup_action(progress)
    if followup is not None:
        result["current_executable_owner_action"] = _projection_action_from_followup(followup)
        return result
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


def _projection_action_from_followup(action: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": _text(action.get("source_surface")) or "stage_kernel_projection.current_owner_delta",
        "next_owner": _text(action.get("owner")) or READINESS_OWNER,
        "work_unit_id": _text(action.get("work_unit_id")) or READINESS_ACTION_TYPE,
        "allowed_actions": [_text(action.get("action_type")) or READINESS_ACTION_TYPE],
        "owner_receipt_required": True,
        "required_delta_kind": "medical_paper_readiness_surface_or_typed_blocker",
        "target_surface": {
            "ref_kind": "mas_owner_surface",
            "surface_ref": _text(action.get("required_output_surface")) or READINESS_ACTION_TYPE,
            "blocked_surface": _text(action.get("blocked_surface")) or ACTION_TYPE,
        },
        "target_surface_specificity": "stage_kernel_typed_blocker_followup",
        "blocked_surface": _text(action.get("blocked_surface")) or ACTION_TYPE,
        "source_ref": _text(action.get("source_ref")),
        "latest_owner_answer_ref": _text(action.get("latest_owner_answer_ref"))
        or _text(action.get("source_ref")),
        "latest_owner_answer_kind": _text(action.get("latest_owner_answer_kind")),
        "artifact_first_precedence": {
            "superseded_stage_artifact_action": ACTION_TYPE,
            "reason": _text(action.get("reason")) or "medical_paper_readiness_not_ready",
            "typed_blocker_followup_takes_precedence": True,
        },
        "authority_boundary": {
            "refs_only": True,
            "can_write_runtime_owned_surfaces": False,
            "can_write_paper_or_package": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_ready": False,
        },
    }


def _current_owner_delta(progress: Mapping[str, Any]) -> dict[str, Any]:
    direct = _mapping(progress.get("current_owner_delta"))
    if direct:
        return direct
    stage_kernel = _mapping(progress.get("stage_kernel_projection"))
    delta = _mapping(stage_kernel.get("current_owner_delta"))
    if delta:
        return delta
    stage_run_kernel = _mapping(stage_kernel.get("stage_run_kernel"))
    return _mapping(stage_run_kernel.get("current_owner_delta"))


def _medical_paper_readiness_ready(progress: Mapping[str, Any]) -> bool:
    readiness = _mapping(progress.get("medical_paper_readiness"))
    return _text(readiness.get("overall_status")) == "ready"


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
    "typed_blocker_followup_action",
]
