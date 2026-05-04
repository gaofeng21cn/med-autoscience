from __future__ import annotations

from typing import Any, Iterable, Mapping

from med_autoscience.controllers.supervisor_action_request_lifecycle import (
    AI_REVIEWER_REQUEST_STATES,
    AI_REVIEWER_REQUIRED_INPUT_SURFACES,
)
from med_autoscience.policies import DEFAULT_PUBLICATION_CRITIQUE_POLICY

__all__ = [
    "build_ai_reviewer_publication_eval_request",
    "build_publication_gate_specificity_request",
]


_REQUEST_AUTHORITY_CONTRACT = {
    "authority": "observability_only",
    "authoritative": False,
    "can_clear_quality_gate": False,
    "quality_gate_relaxation_allowed": False,
    "paper_package_mutation_allowed": False,
    "manual_study_patch_allowed": False,
    "paper_patch_allowed": False,
    "current_package_patch_allowed": False,
    "medical_claim_authoring_allowed": False,
    "medical_conclusion_allowed": False,
    "forbidden_actions": [
        "paper_package_mutation",
        "manual_study_patch",
        "quality_gate_relaxation",
        "medical_claim_authoring",
    ],
}
_SPECIFICITY_TARGET_TYPES = ("claim", "figure", "table", "metric", "source_path")


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _required_text(label: str, value: object) -> str:
    text = _text(value)
    if text is None:
        raise ValueError(f"{label} must be non-empty")
    return text


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text_list(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    items: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None:
            items.append(text)
    return items


def _mapping_copy(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _ref_contract(value: object, *, surface: str) -> dict[str, Any]:
    ref = _mapping_copy(value)
    if not ref:
        return {"surface": surface, "required": True, "present": False, "valid": False}
    ref.setdefault("surface", surface)
    ref.setdefault("required", True)
    if "present" not in ref:
        ref["present"] = bool(_text(ref.get("path")) or _text(ref.get("relative_path")) or _text(ref.get("ref")))
    if "valid" not in ref:
        ref["valid"] = bool(ref["present"])
    return ref


def _ai_reviewer_input_contract(input_refs: Mapping[str, Any] | None) -> dict[str, Any]:
    refs = _mapping(input_refs)
    required_refs = {
        surface: _ref_contract(refs.get(surface), surface=surface)
        for surface in AI_REVIEWER_REQUIRED_INPUT_SURFACES
    }
    missing = [
        surface
        for surface, ref in required_refs.items()
        if ref.get("present") is False or ref.get("valid") is False
    ]
    return {
        "contract_id": "return_to_ai_reviewer_workflow_inputs_v1",
        "required_refs": required_refs,
        "required_surfaces": list(AI_REVIEWER_REQUIRED_INPUT_SURFACES),
        "all_required_refs_present": not missing,
        "missing_or_invalid_refs": missing,
        "assessment_scope": "manuscript_evidence_review_charter",
    }


def _ai_reviewer_request_lifecycle(
    *,
    state: str,
    assigned_to: str | None,
    assessment_ref: str | None,
    blocked_reason: str | None,
) -> dict[str, Any]:
    resolved_state = _required_text("request_lifecycle.state", state)
    if resolved_state not in AI_REVIEWER_REQUEST_STATES:
        raise ValueError(f"request_lifecycle.state must be one of: {', '.join(AI_REVIEWER_REQUEST_STATES)}")
    return {
        "state": resolved_state,
        "allowed_states": list(AI_REVIEWER_REQUEST_STATES),
        "assigned_to": assigned_to,
        "assessment_ref": assessment_ref,
        "blocked_reason": blocked_reason,
        "authority": "observability_only",
        "can_authorize_quality": False,
        "can_authorize_finalize": False,
        "can_authorize_submission": False,
    }


def _request_id(kind: str, *, study_id: str, quest_id: str | None) -> str:
    if quest_id is None:
        return f"{kind}::{study_id}"
    return f"{kind}::{study_id}::{quest_id}"


def _base_packet(kind: str, *, study_id: str, quest_id: str | None, source_surface: str) -> dict[str, Any]:
    return {
        "surface": "supervisor_action_request",
        "schema_version": 1,
        "request_id": _request_id(kind, study_id=study_id, quest_id=quest_id),
        "request_kind": kind,
        "study_id": study_id,
        "quest_id": quest_id,
        "source_surface": source_surface,
        **_REQUEST_AUTHORITY_CONTRACT,
    }


def _gap_ref(gap: Mapping[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for field_name in ("gap_id", "gap_type", "summary"):
        text = _text(gap.get(field_name))
        if text is not None:
            payload[field_name] = text
    evidence_refs = _text_list(gap.get("evidence_refs"))
    if evidence_refs:
        payload["evidence_refs"] = evidence_refs
    return payload


def build_publication_gate_specificity_request(
    *,
    study_id: str,
    quest_id: str | None,
    source_surface: str,
    source_action: Mapping[str, Any],
    blocking_gaps: Iterable[Mapping[str, Any]],
    requested_targets: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    if requested_targets:
        raise ValueError("request packet must not prepopulate gate specificity targets")

    resolved_study_id = _required_text("study_id", study_id)
    resolved_quest_id = _text(quest_id)
    resolved_source_surface = _required_text("source_surface", source_surface)
    action = _mapping(source_action)
    next_work_unit = _mapping(action.get("next_work_unit"))
    work_unit_id = _text(next_work_unit.get("unit_id"))

    packet = _base_packet(
        "publication_gate_specificity_required",
        study_id=resolved_study_id,
        quest_id=resolved_quest_id,
        source_surface=resolved_source_surface,
    )
    packet.update(
        {
            "request_owner": "controller",
            "request_summary": (
                "Publication gate must return concrete claim/figure/table/metric/source_path targets "
                "before any repair or authoring worker can run."
            ),
            "requested_target_types": list(_SPECIFICITY_TARGET_TYPES),
            "requested_targets": [],
            "target_requirements": {
                f"{target_type}_targets_required": True for target_type in _SPECIFICITY_TARGET_TYPES
            },
            "source_action_ref": {
                "action_id": _text(action.get("action_id")),
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": _text(action.get("work_unit_fingerprint")),
                "source_surface": resolved_source_surface,
            },
            "blocking_gap_refs": [
                ref for gap in blocking_gaps if (ref := _gap_ref(_mapping(gap)))
            ],
        }
    )
    return packet


def build_ai_reviewer_publication_eval_request(
    *,
    study_id: str,
    quest_id: str | None,
    source_surface: str,
    workflow_state: Mapping[str, Any],
    input_refs: Mapping[str, Any] | None = None,
    lifecycle_state: str = "requested",
    assigned_to: str | None = None,
    assessment_ref: str | None = None,
    blocked_reason: str | None = None,
) -> dict[str, Any]:
    resolved_study_id = _required_text("study_id", study_id)
    resolved_quest_id = _text(quest_id)
    resolved_source_surface = _required_text("source_surface", source_surface)
    workflow = _mapping(workflow_state)
    quality_authority = _mapping(workflow.get("quality_authority"))
    route_back = _mapping(workflow.get("route_back"))
    input_contract = _ai_reviewer_input_contract(input_refs or _mapping(workflow.get("input_refs")))

    packet = _base_packet(
        "return_to_ai_reviewer_workflow",
        study_id=resolved_study_id,
        quest_id=resolved_quest_id,
        source_surface=resolved_source_surface,
    )
    packet.update(
        {
            "request_owner": "ai_reviewer",
            "request_summary": (
                "Request an AI reviewer-owned publication_eval/latest.json; missing reviewer provenance "
                "is request-only and cannot authorize quality closure."
            ),
            "request_lifecycle": _ai_reviewer_request_lifecycle(
                state=lifecycle_state,
                assigned_to=_text(assigned_to),
                assessment_ref=_text(assessment_ref),
                blocked_reason=_text(blocked_reason),
            ),
            "input_contract": input_contract,
            "required_publication_eval_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "policy_id": DEFAULT_PUBLICATION_CRITIQUE_POLICY["policy_id"],
                "ai_reviewer_required": False,
            },
            "required_output": {
                "surface": "publication_eval/latest.json",
                "writer": "ai_reviewer_publication_eval_workflow",
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "writeback_required": True,
                "assessment_written_lifecycle_state": "assessment_written",
                "pre_writeback_authority": "observability_only",
                "pre_writeback_can_authorize_quality": False,
                "pre_writeback_can_authorize_finalize": False,
                "pre_writeback_can_authorize_submission": False,
            },
            "requested_artifact": {
                "surface": "publication_eval/latest.json",
                "writer": "ai_reviewer_publication_eval_workflow",
                "materialization_mode": "request_only",
            },
            "source_workflow_ref": {
                "surface": resolved_source_surface,
                "authority_owner": _text(quality_authority.get("owner")),
                "authority_state": _text(quality_authority.get("state")),
                "route_back_required": route_back.get("required") is True,
                "route_back_target": _text(route_back.get("target")),
            },
            "blockers": _text_list(workflow.get("blockers")),
        }
    )
    return packet
