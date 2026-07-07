from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.cli_parts.paper_mission_command_parts.common import (
    _first_text,
    _mapping,
    _optional_text,
)
from med_autoscience.cli_parts.paper_mission_command_parts.materialized_owner_consumption import (
    _path_mtime,
)
from med_autoscience.controllers.study_transition_receipt_consumption import (
    mas_owner_apply_receipt_consumption as _mas_owner_apply_receipt_consumption,
)


def _owner_repair_receipt_consumption_readback(
    *,
    study_root: Path,
    study_id: str,
) -> dict[str, Any] | None:
    consumption = _mas_owner_apply_receipt_consumption(study_root=study_root)
    if _optional_text(consumption.get("apply_result")) != "artifact_delta":
        return None
    if _optional_text(consumption.get("receipt_surface")) not in {
        "paper_repair_owner_receipt",
        "paper_story_repair_owner_receipt",
    }:
        return None
    receipt_ref = _optional_text(consumption.get("receipt_ref"))
    evidence_ref = _optional_text(consumption.get("evidence_ref"))
    if receipt_ref is None or evidence_ref is None:
        return None
    receipt_path = (study_root / receipt_ref).expanduser().resolve()
    evidence_path = (study_root / evidence_ref).expanduser().resolve()
    story_refs = _mapping_list(consumption.get("story_surface_delta_refs"))
    paper_delta_refs = _story_surface_delta_ref_texts(story_refs)
    owner_decision_refs = _dedupe_texts([str(receipt_path), str(evidence_path)])
    source_ref = str(evidence_path if evidence_path.exists() else receipt_path)
    work_unit_id = _optional_text(consumption.get("work_unit_id")) or "medical_prose_write_repair"
    stage_closure_decision = {
        "surface_kind": "mas_stage_closure_decision",
        "schema_version": 1,
        "source": "study_controller_owner_repair_receipt",
        "source_surface_kind": "paper_mission_receipt_owner_consumption",
        "study_id": study_id,
        "stage_id": "write",
        "work_unit_id": work_unit_id,
        "source_ref": source_ref,
        "decision_ref": source_ref,
        "authority_materialized": True,
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "counts_as_stage_closure_terminalizer_evidence": True,
        "counts_as_owner_receipt": True,
        "counts_as_typed_blocker": False,
        "counts_as_human_gate": False,
        "counts_as_current_package": False,
        "counts_as_runtime_truth": False,
        "can_claim_paper_progress": bool(paper_delta_refs),
        "can_claim_submission_ready": False,
        "can_claim_publication_ready": False,
        "can_claim_runtime_ready": False,
        "receipt_evidence_ref": str(receipt_path),
        "repair_execution_evidence_ref": str(evidence_path),
        "semantic_delta": {
            "paper_delta_refs": paper_delta_refs,
            "owner_decision_refs": owner_decision_refs,
            "reviewer_delta_refs": [],
            "gate_delta_refs": [],
            "delivery_delta_refs": [],
        },
        "known_blockers": [],
        "outcome": {
            "kind": "owner_receipt",
            "next_owner": "MedAutoScience",
            "next_action": _optional_text(consumption.get("next_action")),
            "can_submit": False,
            "package_kind": None,
            "known_blockers": [],
            "authority_materialized": True,
            "resume_condition": "continue via MAS guarded apply, gate replay, or reviewer recheck surfaces",
        },
        "authority_boundary": {
            "surface_role": "paper_mission_receipt_owner_consumption",
            "authority_materialized": True,
            "writes_receipt_owner_consumption": False,
            "writes_owner_receipt": False,
            "writes_typed_blocker": False,
            "writes_human_gate": False,
            "writes_current_package": False,
            "writes_submission_ready_package": False,
            "writes_runtime_queue_or_provider_attempt": False,
        },
    }
    return {
        "surface_kind": "paper_mission_receipt_owner_consumption",
        "schema_version": 1,
        "status": "owner_consumption_applied",
        "study_id": study_id,
        "source": "study_controller_owner_repair_receipt",
        "source_ref": source_ref,
        "decision_ref": source_ref,
        "apply_mode": "mas_owner_repair_receipt",
        "authority_materialized": True,
        "receipt_evidence": {
            "source_kind": "mas_owner_repair_execution_evidence",
            "receipt_ref": str(receipt_path),
            "evidence_ref": str(evidence_path),
            "story_surface_delta_refs": story_refs,
            "paper_delta_refs": paper_delta_refs,
        },
        "mas_receipt_consumption": {
            "surface_kind": "mas_receipt_consumption_projection",
            "schema_version": 1,
            "status": "owner_consumed_mas_repair_delta",
            "owner_result_kind": "artifact_delta",
            "receipt_kind": consumption.get("receipt_kind"),
            "receipt_surface": consumption.get("receipt_surface"),
            "receipt_execution_status": consumption.get("receipt_execution_status"),
            "receipt_ref": str(receipt_path),
            "evidence_ref": str(evidence_path),
            "story_surface_delta_ref_count": consumption.get("story_surface_delta_ref_count"),
            "story_surface_delta_refs": story_refs,
            "next_legal_action": consumption.get("next_action"),
            "can_claim_paper_progress": bool(paper_delta_refs),
            "can_claim_publication_ready": False,
            "can_claim_submission_ready": False,
            "can_claim_runtime_ready": False,
        },
        "stage_closure_decision": stage_closure_decision,
    }


def _stage_closure_ledger_readback_for_output(
    *,
    stage_closure_ledger_readback: Mapping[str, Any] | None,
    receipt_owner_consumption_readback: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    if not _receipt_owner_consumption_is_owner_repair_delta(receipt_owner_consumption_readback):
        return stage_closure_ledger_readback
    receipt_decision = _mapping(receipt_owner_consumption_readback.get("stage_closure_decision"))
    if not receipt_decision:
        return stage_closure_ledger_readback
    if _route_checkpoint_without_semantic_delta(stage_closure_ledger_readback):
        return receipt_decision
    if _owner_repair_receipt_is_newer(
        candidate=receipt_owner_consumption_readback,
        current=stage_closure_ledger_readback,
    ):
        return receipt_decision
    return stage_closure_ledger_readback


def _receipt_owner_consumption_is_owner_repair_delta(
    receipt_owner_consumption_readback: Mapping[str, Any] | None,
) -> bool:
    receipt = _mapping(receipt_owner_consumption_readback)
    if _optional_text(receipt.get("source")) == "study_controller_owner_repair_receipt":
        return True
    mas_consumption = _mapping(receipt.get("mas_receipt_consumption"))
    return _optional_text(mas_consumption.get("status")) == "owner_consumed_mas_repair_delta"


def _route_checkpoint_without_semantic_delta(
    stage_closure_ledger_readback: Mapping[str, Any] | None,
) -> bool:
    stage_closure = _mapping(stage_closure_ledger_readback)
    outcome = _mapping(stage_closure.get("outcome"))
    if (
        _optional_text(outcome.get("kind")) != "next_stage_transition"
        or _optional_text(outcome.get("transition_kind"))
        != "route_back_candidate_checkpoint"
    ):
        return False
    return not _semantic_delta_has_refs(_mapping(stage_closure.get("semantic_delta")))


def _semantic_delta_has_refs(semantic_delta: Mapping[str, Any]) -> bool:
    for key in (
        "paper_delta_refs",
        "owner_decision_refs",
        "reviewer_delta_refs",
        "gate_delta_refs",
        "delivery_delta_refs",
        "semantic_delta_refs",
    ):
        value = semantic_delta.get(key)
        if isinstance(value, list | tuple) and len(value) > 0:
            return True
    return False


def _owner_repair_receipt_is_newer(
    *,
    candidate: Mapping[str, Any] | None,
    current: Mapping[str, Any] | None,
) -> bool:
    if candidate is None:
        return False
    if current is None:
        return True
    candidate_mtime = _path_mtime(_optional_text(candidate.get("source_ref")))
    current_mtime = _path_mtime(_optional_text(current.get("source_ref")))
    return candidate_mtime is not None and (current_mtime is None or candidate_mtime > current_mtime)


def _story_surface_delta_ref_texts(refs: list[Mapping[str, Any]]) -> list[str]:
    return _dedupe_texts(
        _first_text(ref.get("path"), ref.get("artifact_ref"), ref.get("ref"))
        for ref in refs
    )


def _mapping_list(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _dedupe_texts(values: Iterable[object]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _optional_text(value)
        if text is None or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result
