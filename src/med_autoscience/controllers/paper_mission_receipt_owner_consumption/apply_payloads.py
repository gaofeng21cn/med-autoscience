from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.paper_mission_receipt_owner_consumption.common import (
    FORBIDDEN_AUTHORITY_WRITES,
    _first_text,
    _mapping,
    _text,
    _text_list,
)


def _route_checkpoint_aligned_receipt_inputs(
    *,
    stage: Mapping[str, Any],
    receipt: Mapping[str, Any],
    evidence: Mapping[str, Any],
    consumption: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if _text(stage.get("transition_kind")) != "route_back_candidate_checkpoint":
        return dict(receipt), dict(evidence), dict(consumption)
    checkpoint_ref = _first_text(stage.get("route_checkpoint_evidence_ref"))
    if checkpoint_ref is None:
        return dict(receipt), dict(evidence), dict(consumption)
    closeout = _mapping(stage.get("opl_closeout"))
    stage_attempt_id = _first_text(closeout.get("stage_attempt_id"))
    stage_attempt_ref = (
        f"opl://stage-attempts/{stage_attempt_id}" if stage_attempt_id else None
    )
    receipt_ref = _first_text(
        stage.get("receipt_evidence_ref"),
        stage_attempt_ref,
        evidence.get("receipt_ref"),
        receipt.get("stage_attempt_ref"),
        receipt.get("receipt_ref"),
    )
    aligned_receipt = {
        **dict(receipt),
        **(
            {"stage_attempt_id": stage_attempt_id}
            if stage_attempt_id is not None
            else {}
        ),
        **(
            {"stage_attempt_ref": stage_attempt_ref}
            if stage_attempt_ref is not None
            else {}
        ),
        "runtime_closeout_ref": checkpoint_ref,
        "route_target": _first_text(stage.get("stage_id")),
        "work_unit_id": _first_text(stage.get("work_unit_id")),
    }
    aligned_evidence = {
        **dict(evidence),
        **({"receipt_ref": receipt_ref} if receipt_ref is not None else {}),
        "runtime_closeout_ref": checkpoint_ref,
        **(
            {"stage_attempt_ref": stage_attempt_ref}
            if stage_attempt_ref is not None
            else {}
        ),
        "route_checkpoint_evidence_ref": checkpoint_ref,
        "route_back_evidence_ref": _first_text(
            evidence.get("route_back_evidence_ref"),
            consumption.get("route_back_evidence_ref"),
        ),
    }
    aligned_consumption = {
        **dict(consumption),
        **(
            {"receipt_evidence_ref": receipt_ref}
            if receipt_ref is not None
            else {}
        ),
        "route_checkpoint_evidence_ref": checkpoint_ref,
    }
    return aligned_receipt, aligned_evidence, aligned_consumption


def _applied_stage_closure_decision(
    *,
    apply_mode: str,
    study_id: str,
    stage: Mapping[str, Any],
    package: Mapping[str, Any],
    receipt: Mapping[str, Any],
    evidence: Mapping[str, Any],
    consumption: Mapping[str, Any],
    receipt_ref: str | None,
    generated_at: str,
    source: str,
) -> dict[str, Any]:
    known_blockers = _text_list(package.get("known_blockers"))
    blocked_reason = _first_text(
        receipt.get("blocked_reason"),
        consumption.get("blocked_reason"),
        stage.get("transition_kind"),
        "paper_mission_opl_transition_receipt_consumed",
    )
    if apply_mode == "route_checkpoint":
        route_stage_id = _first_text(
            receipt.get("route_target"),
            receipt.get("stage_id"),
            stage.get("stage_id"),
        )
        route_work_unit_id = _first_text(
            receipt.get("work_unit_id"),
            consumption.get("work_unit_id"),
            stage.get("work_unit_id"),
        )
        route_opl_closeout = _receipt_aligned_opl_closeout(
            stage=stage,
            receipt=receipt,
            work_unit_id=route_work_unit_id,
        )
        return {
            "surface_kind": "mas_stage_closure_decision",
            "schema_version": 1,
            "source": source,
            "study_id": study_id,
            **(
                {"stage_id": route_stage_id}
                if route_stage_id is not None
                else {}
            ),
            **(
                {"work_unit_id": route_work_unit_id}
                if route_work_unit_id is not None
                else {}
            ),
            "decision_ref": _text(stage.get("decision_ref")),
            "source_stage_closure_decision_ref": _text(stage.get("decision_ref")),
            "authority_materialized": True,
            "writes_authority": True,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "counts_as_stage_closure_terminalizer_evidence": False,
            "counts_as_owner_receipt": False,
            "counts_as_typed_blocker": False,
            "counts_as_human_gate": False,
            "counts_as_current_package": False,
            "counts_as_runtime_truth": False,
            "can_claim_paper_progress": False,
            "can_claim_submission_ready": False,
            "can_claim_publication_ready": False,
            "can_claim_runtime_ready": False,
            "receipt_evidence_ref": _text(evidence.get("receipt_ref")),
            "route_checkpoint_evidence_ref": receipt_ref,
            "recorded_at": generated_at,
            **(
                {"opl_closeout": route_opl_closeout}
                if route_opl_closeout
                else {}
            ),
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "route_back_candidate_checkpoint",
                "next_owner": "MedAutoScience",
                "next_action": (
                    stage.get("next_legal_action")
                    or "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                ),
                "known_blockers": known_blockers or [blocked_reason],
                "resume_condition": (
                    "route-back candidate checkpoint must be consumed into owner receipt, "
                    "typed blocker, human gate, or next stage transition"
                ),
                "authority_materialized": True,
                "route_checkpoint_evidence_ref": receipt_ref,
                "package_kind": package.get("package_kind"),
                "can_submit": package.get("can_submit") is True,
            },
            "authority_boundary": {
                "surface_role": "paper_mission_receipt_owner_consumption",
                "authority_materialized": True,
                "writes_receipt_owner_consumption": True,
                "writes_owner_receipt": False,
                "writes_typed_blocker": False,
                "writes_human_gate": False,
                "writes_current_package": False,
                "writes_submission_ready_package": False,
                "writes_runtime_queue_or_provider_attempt": False,
            },
            "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
        }
    return {
        "surface_kind": "mas_stage_closure_decision",
        "schema_version": 1,
        "source": source,
        "study_id": study_id,
        **(
            {"stage_id": stage["stage_id"]}
            if _text(stage.get("stage_id")) is not None
            else {}
        ),
        **(
            {"work_unit_id": stage["work_unit_id"]}
            if _text(stage.get("work_unit_id")) is not None
            else {}
        ),
        "decision_ref": _text(stage.get("decision_ref")),
        "source_stage_closure_decision_ref": _text(stage.get("decision_ref")),
        "authority_materialized": True,
        "writes_authority": True,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "counts_as_stage_closure_terminalizer_evidence": False,
        "counts_as_owner_receipt": False,
        "counts_as_typed_blocker": True,
        "counts_as_human_gate": False,
        "counts_as_current_package": False,
        "counts_as_runtime_truth": False,
        "can_claim_paper_progress": False,
        "can_claim_submission_ready": False,
        "can_claim_publication_ready": False,
        "can_claim_runtime_ready": False,
        "receipt_evidence_ref": _text(evidence.get("receipt_ref")),
        "typed_runtime_blocker_ref": _text(evidence.get("typed_runtime_blocker_ref")),
        "typed_blocker_evidence_ref": receipt_ref,
        "recorded_at": generated_at,
        **(
            {"opl_closeout": stage["opl_closeout"]}
            if _mapping(stage.get("opl_closeout"))
            else {}
        ),
        "outcome": {
            "kind": "typed_blocker",
            "blocker_type": blocked_reason,
            "next_owner": "MedAutoScience",
            "next_action": "resolve_typed_blocker_or_route_redesign",
            "known_blockers": known_blockers or [blocked_reason],
            "resume_condition": "resolve typed blocker through MAS owner route; do not redrive synonymous OPL route",
            "authority_materialized": True,
            "typed_blocker_evidence_ref": receipt_ref,
            "package_kind": package.get("package_kind"),
            "can_submit": package.get("can_submit") is True,
        },
        "authority_boundary": {
            "surface_role": "paper_mission_receipt_owner_consumption",
            "authority_materialized": True,
            "writes_receipt_owner_consumption": True,
            "writes_owner_receipt": False,
            "writes_typed_blocker": False,
            "writes_human_gate": False,
            "writes_current_package": False,
            "writes_submission_ready_package": False,
            "writes_runtime_queue_or_provider_attempt": False,
        },
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
    }


def _receipt_aligned_opl_closeout(
    *,
    stage: Mapping[str, Any],
    receipt: Mapping[str, Any],
    work_unit_id: str | None,
) -> dict[str, Any]:
    closeout = _mapping(stage.get("opl_closeout"))
    receipt_stage_attempt_id = _text(receipt.get("stage_attempt_id"))
    if receipt_stage_attempt_id is None:
        return closeout
    if _text(closeout.get("stage_attempt_id")) == receipt_stage_attempt_id:
        return closeout
    aligned = {
        "status": "opl_runtime_terminal_readback_observed",
        "stage_attempt_id": receipt_stage_attempt_id,
    }
    if work_unit_id is not None:
        aligned["work_unit_id"] = work_unit_id
    return aligned
