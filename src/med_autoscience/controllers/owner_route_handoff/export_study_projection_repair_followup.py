from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from ..owner_callable_action_policy import (
    SUPPORTED_ACTION_TYPES,
    request_output_surface_for_action_type,
    request_owner_for_action_type,
)
from ..study_progress import repair_progress_projection
from .export_study_projection_common import (
    stage_outcome_opl_handoff_task_boundary,
    mapping,
    text,
)


def repair_progress_followup_owner_action_record(
    *,
    study_root: Path,
) -> dict[str, Any] | None:
    repair_progress = repair_progress_projection.build_repair_progress_projection(study_root=study_root)
    if repair_progress.get("paper_delta_observed") is not True:
        return None
    if repair_progress.get("accepted_owner_receipt") is not True:
        return None
    current_action = _repair_progress_current_owner_action(repair_progress=repair_progress)
    action_type = text(current_action.get("action_type"))
    work_unit_id = text(current_action.get("work_unit_id"))
    if action_type is None or work_unit_id is None:
        return None
    source_ref = text(current_action.get("source_ref")) or text(repair_progress.get("owner_receipt_ref"))
    action_fingerprint = (
        text(current_action.get("action_fingerprint"))
        or text(current_action.get("work_unit_fingerprint"))
        or text(repair_progress.get("source_fingerprint"))
        or (
            f"repair-progress-current-owner::{study_root.name}::{work_unit_id}::{action_type}::{source_ref}"
            if source_ref is not None
            else None
        )
    )
    if action_fingerprint is None:
        return None
    quest_id = text(current_action.get("quest_id")) or study_root.name
    next_owner = text(current_action.get("next_owner")) or request_owner_for_action_type(action_type)
    currentness_basis = {
        "owner_reason": text(current_action.get("required_delta_kind")) or work_unit_id,
        "runtime_health_epoch": action_fingerprint,
        "truth_epoch": action_fingerprint,
        "work_unit_fingerprint": action_fingerprint,
        "work_unit_id": work_unit_id,
    }
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_root.name,
        "quest_id": quest_id,
        "truth_epoch": action_fingerprint,
        "runtime_health_epoch": action_fingerprint,
        "work_unit_fingerprint": action_fingerprint,
        "source_fingerprint": action_fingerprint,
        "route_epoch": action_fingerprint,
        "current_owner": "med-autoscience",
        "next_owner": next_owner,
        "owner_reason": currentness_basis["owner_reason"],
        "active_run_id": None,
        "allowed_actions": [action_type],
        "blocked_actions": sorted(item for item in SUPPORTED_ACTION_TYPES if item != action_type),
        "source_refs": {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
            "source_surface": text(current_action.get("source")) or "repair_progress_projection",
            "source_ref": source_ref,
            "owner_route_currentness_basis": currentness_basis,
        },
        "idempotency_key": f"repair-progress-followup::{study_root.name}::{action_fingerprint}",
    }
    return {
        "surface_kind": "mas_current_owner_action_record",
        "schema_version": 1,
        "source": "repair_progress_followup.current_executable_owner_action",
        "study_id": study_root.name,
        "quest_id": quest_id,
        "recorded_at": text(repair_progress.get("recorded_at")),
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        **stage_outcome_opl_handoff_task_boundary(),
        "next_owner": next_owner,
        "allowed_actions": [action_type],
        "required_output_surface": text(mapping(current_action.get("target_surface")).get("surface_ref"))
        or request_output_surface_for_action_type(action_type),
        "source_ref_role": "repair_progress_current_owner_action",
        "source_relative_path": source_ref,
        "source_surface": text(current_action.get("source")) or "repair_progress_projection",
        "repair_progress_followup": current_action,
        "owner_route_currentness_basis": currentness_basis,
        "owner_route": owner_route,
        "currentness_status": "repair_progress_followup_active",
        "authority_boundary": {
            "mas_writes_generic_runtime_queue": False,
            "mas_submits_runtime_chat": False,
            "mas_resumes_provider_worker": False,
            "opl_writes_mas_truth": False,
            "mas_owner_receipt_required": True,
        },
    }


def _repair_progress_current_owner_action(*, repair_progress: Mapping[str, Any]) -> dict[str, Any]:
    ai_reviewer_request_ref = text(repair_progress.get("ai_reviewer_recheck_request_ref"))
    gate_replay_refs = _text_list(repair_progress.get("gate_replay_refs"))
    source_ref = text(repair_progress.get("repair_execution_evidence_ref")) or text(
        repair_progress.get("owner_receipt_ref")
    )
    if ai_reviewer_request_ref is not None:
        action_type = "return_to_ai_reviewer_workflow"
        work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
        next_owner = "ai_reviewer"
        target_surface = {
            "ref_kind": "route_obligation",
            "route_target": "review",
            "surface_ref": "artifacts/publication_eval/latest.json",
            "request_ref": ai_reviewer_request_ref,
            **({"gate_replay_request_ref": gate_replay_refs[0]} if gate_replay_refs else {}),
        }
        acceptance_refs = [ai_reviewer_request_ref, *gate_replay_refs]
    elif gate_replay_refs:
        action_type = "run_gate_clearing_batch"
        work_unit_id = "publication_gate_replay"
        next_owner = "gate_clearing_batch"
        target_surface = {
            "ref_kind": "route_obligation",
            "route_target": "finalize",
            "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
            "request_ref": gate_replay_refs[0],
        }
        acceptance_refs = gate_replay_refs
    else:
        action_type = None
        work_unit_id = None
        next_owner = None
        target_surface = {}
        acceptance_refs = []
    return {
        key: value
        for key, value in {
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "next_owner": next_owner,
            "work_unit_id": work_unit_id,
            "action_type": action_type,
            "allowed_actions": [action_type] if action_type is not None else [],
            "owner_receipt_required_for_quality_or_ready_claim": True,
            "target_surface": target_surface or None,
            "target_surface_specificity": "repair_progress_followup_owner_surface",
            "source_ref": source_ref,
            "acceptance_refs": [
                ref
                for ref in [
                    text(repair_progress.get("repair_execution_evidence_ref")),
                    text(repair_progress.get("owner_receipt_ref")),
                    *acceptance_refs,
                ]
                if ref is not None
            ],
        }.items()
        if value is not None
    }


def _owner_route_currentness_basis(owner_route: Mapping[str, Any]) -> dict[str, str] | None:
    source_refs = mapping(owner_route.get("source_refs"))
    embedded_basis = mapping(source_refs.get("owner_route_currentness_basis"))
    basis = {
        "owner_reason": text(owner_route.get("owner_reason"))
        or text(owner_route.get("failure_signature"))
        or text(source_refs.get("blocked_reason"))
        or text(embedded_basis.get("owner_reason")),
        "runtime_health_epoch": text(owner_route.get("runtime_health_epoch"))
        or text(source_refs.get("runtime_health_epoch"))
        or text(embedded_basis.get("runtime_health_epoch")),
        "source_eval_id": text(owner_route.get("source_eval_id"))
        or text(source_refs.get("source_eval_id"))
        or text(embedded_basis.get("source_eval_id")),
        "truth_epoch": text(owner_route.get("truth_epoch"))
        or text(owner_route.get("route_epoch"))
        or text(embedded_basis.get("truth_epoch")),
        "work_unit_fingerprint": text(owner_route.get("work_unit_fingerprint"))
        or text(source_refs.get("work_unit_fingerprint"))
        or text(embedded_basis.get("work_unit_fingerprint")),
        "work_unit_id": text(owner_route.get("work_unit_id"))
        or text(source_refs.get("work_unit_id"))
        or text(embedded_basis.get("work_unit_id")),
    }
    if basis["truth_epoch"] is None:
        return None
    if basis["work_unit_fingerprint"] is None:
        return None
    if basis["work_unit_id"] is None:
        return None
    if basis["runtime_health_epoch"] is None and basis["source_eval_id"] is None:
        return None
    return {key: value for key, value in basis.items() if value is not None}


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in (text(entry) for entry in value) if item is not None]


__all__ = [
    "repair_progress_followup_owner_action_record",
]
