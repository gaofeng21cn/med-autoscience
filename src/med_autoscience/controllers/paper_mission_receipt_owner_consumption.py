from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.paper_mission_receipt_owner_consumption_parts.alignment import (
    align_carrier_readback_with_owner_consumption,
)
from med_autoscience.controllers.paper_mission_receipt_owner_consumption_parts.apply_payloads import (
    _applied_stage_closure_decision,
    _route_checkpoint_aligned_receipt_inputs,
)
from med_autoscience.controllers.paper_mission_receipt_owner_consumption_parts.common import (
    FORBIDDEN_AUTHORITY_WRITES,
    _first_text,
    _mapping,
    _text,
    _utc_now,
)
from med_autoscience.controllers.paper_mission_receipt_owner_consumption_parts.readback_summary import (
    _carrier,
    _current_package_summary,
    _receipt_summary,
    _stage_closure_summary,
)
from med_autoscience.controllers.paper_mission_receipt_owner_consumption_parts.storage import (
    _write_output_packet,
    latest_receipt_owner_consumption_readback,
)


def materialize_receipt_owner_consumption(
    *,
    paper_mission_readback: Mapping[str, Any],
    study_id: str,
    profile_ref: str,
    output_root: Path | None = None,
    apply_mode: str | None = None,
    source: str = "unknown",
) -> dict[str, Any]:
    validation = _validate_readback(
        paper_mission_readback=paper_mission_readback,
        study_id=study_id,
    )
    if validation["valid"] is not True:
        result = _blocked_result(
            paper_mission_readback=paper_mission_readback,
            study_id=study_id,
            profile_ref=profile_ref,
            validation=validation,
            source=source,
        )
    else:
        result = _consumption_result(
            paper_mission_readback=paper_mission_readback,
            study_id=study_id,
            profile_ref=profile_ref,
            validation=validation,
            apply_mode=apply_mode,
            source=source,
        )
    if output_root is not None:
        result = {
            **result,
            "output_manifest": _write_output_packet(
                output_root=output_root,
                study_id=study_id,
                payload=result,
                writes_authority=result.get("authority_materialized") is True,
            ),
        }
    return result


def _validate_readback(
    *,
    paper_mission_readback: Mapping[str, Any],
    study_id: str,
) -> dict[str, Any]:
    missing: list[str] = []
    mismatched: list[str] = []
    if _text(paper_mission_readback.get("study_id")) != study_id:
        mismatched.append("study_id")
    carrier = _carrier(paper_mission_readback)
    if not carrier:
        missing.append("opl_runtime_carrier_readback")
    receipt = _mapping(carrier.get("opl_transition_receipt"))
    evidence = _mapping(carrier.get("receipt_evidence"))
    consumption = _mapping(carrier.get("mas_receipt_consumption"))
    if not receipt:
        missing.append("opl_runtime_carrier_readback.opl_transition_receipt")
    if not evidence:
        missing.append("opl_runtime_carrier_readback.receipt_evidence")
    if not consumption:
        missing.append("opl_runtime_carrier_readback.mas_receipt_consumption")
    consumption_status = _text(consumption.get("status"))
    if (
        consumption
        and consumption_status != "requires_mas_owner_consumption"
        and not _owner_consumption_already_materialized(consumption_status)
    ):
        mismatched.append("mas_receipt_consumption.status")
    if receipt and receipt.get("can_claim_paper_progress") is not False:
        mismatched.append("opl_transition_receipt.can_claim_paper_progress")
    return {
        "valid": not missing and not mismatched,
        "missing_required_fields": missing,
        "mismatched_fields": mismatched,
        "observed_receipt_status": _text(receipt.get("receipt_status")) or None,
        "observed_consumption_status": _text(consumption.get("status")) or None,
    }


def _blocked_result(
    *,
    paper_mission_readback: Mapping[str, Any],
    study_id: str,
    profile_ref: str,
    validation: Mapping[str, Any],
    source: str,
) -> dict[str, Any]:
    return {
        "surface_kind": "paper_mission_receipt_owner_consumption",
        "schema_version": 1,
        "status": "blocked_missing_consumable_opl_receipt",
        "study_id": study_id,
        "profile_ref": profile_ref,
        "source": source,
        "write_permitted": False,
        "authority_materialized": False,
        "paper_ready_claim_authorized": False,
        "publication_ready_claim_authorized": False,
        "submission_ready_claim_authorized": False,
        "readback_validation": dict(validation),
        "stage_closure": _stage_closure_summary(paper_mission_readback),
        "current_package": _current_package_summary(paper_mission_readback),
        "implementation_gap": _implementation_gap(),
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
    }


def _consumption_result(
    *,
    paper_mission_readback: Mapping[str, Any],
    study_id: str,
    profile_ref: str,
    validation: Mapping[str, Any],
    apply_mode: str | None,
    source: str,
) -> dict[str, Any]:
    carrier = _carrier(paper_mission_readback)
    receipt = _mapping(carrier.get("opl_transition_receipt"))
    evidence = _mapping(carrier.get("receipt_evidence"))
    consumption = _mapping(carrier.get("mas_receipt_consumption"))
    verdict = _owner_consumption_verdict(
        paper_mission_readback=paper_mission_readback,
        receipt=receipt,
        consumption=consumption,
    )
    if apply_mode is not None:
        return _apply_result(
            paper_mission_readback=paper_mission_readback,
            study_id=study_id,
            profile_ref=profile_ref,
            validation=validation,
            source=source,
            receipt=receipt,
            evidence=evidence,
            consumption=consumption,
            verdict=verdict,
            apply_mode=apply_mode,
        )
    already_materialized = _owner_consumption_already_materialized(
        _text(consumption.get("status"))
    )
    return {
        "surface_kind": "paper_mission_receipt_owner_consumption",
        "schema_version": 1,
        "status": (
            "owner_consumption_already_materialized"
            if already_materialized
            else "owner_consumption_evidence_materialized"
        ),
        "study_id": study_id,
        "profile_ref": profile_ref,
        "source": source,
        "write_permitted": False,
        "authority_materialized": False,
        "owner_consumption_already_materialized": already_materialized,
        "paper_ready_claim_authorized": False,
        "publication_ready_claim_authorized": False,
        "submission_ready_claim_authorized": False,
        "readback_validation": dict(validation),
        "receipt_evidence": dict(evidence),
        "opl_transition_receipt": _receipt_summary(receipt),
        "mas_receipt_consumption": dict(consumption),
        "stage_closure": _stage_closure_summary(paper_mission_readback),
        "current_package": _current_package_summary(paper_mission_readback),
        "owner_consumption_verdict": verdict,
        "implementation_gap": _implementation_gap(),
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
    }


def _owner_consumption_already_materialized(status: str | None) -> bool:
    return bool(status and status.startswith("owner_consumed_"))


def _owner_consumption_verdict(
    *,
    paper_mission_readback: Mapping[str, Any],
    receipt: Mapping[str, Any],
    consumption: Mapping[str, Any],
) -> dict[str, Any]:
    stage = _stage_closure_summary(paper_mission_readback)
    package = _current_package_summary(paper_mission_readback)
    consumption_action = _text(consumption.get("next_legal_action"))
    if (
        stage["outcome_kind"] == "next_stage_transition"
        and stage["transition_kind"] == "route_back_candidate_checkpoint"
    ):
        verdict_kind = "consume_route_back_checkpoint_owner_consumption_required"
        required_authority_surface = "paper-mission receipt-owner-consumption --apply-route-checkpoint"
    elif (
        consumption_action == "record_typed_blocker"
        or stage["outcome_kind"] == "typed_blocker"
    ):
        verdict_kind = "record_typed_blocker_owner_consumption_required"
        required_authority_surface = "paper-mission receipt-owner-consumption --apply-typed-blocker"
    elif package["can_submit"] is True:
        verdict_kind = "submission_ready_owner_verdict_required"
        required_authority_surface = "paper-mission receipt-owner-consumption --apply-owner-verdict"
    else:
        verdict_kind = "owner_consumption_required"
        required_authority_surface = "paper-mission receipt-owner-consumption --apply"
    return {
        "verdict_kind": verdict_kind,
        "required_authority_surface": required_authority_surface,
        "required_authority_surface_exists": required_authority_surface in {
            "paper-mission receipt-owner-consumption --apply-typed-blocker",
            "paper-mission receipt-owner-consumption --apply-route-checkpoint",
        },
        "implemented_surface_role": (
            "mas_owner_consumption_authority_apply_surface"
            if required_authority_surface
            in {
                "paper-mission receipt-owner-consumption --apply-typed-blocker",
                "paper-mission receipt-owner-consumption --apply-route-checkpoint",
            }
            else "diagnostic_owner_consumption_evidence_only"
        ),
        "next_legal_action": _text(consumption.get("next_legal_action")) or "record_typed_blocker",
        "forbidden_next_action": _text(consumption.get("forbidden_next_action"))
        or "synonymous_route_back_redrive",
        "receipt_ref": _first_text(
            stage.get("receipt_evidence_ref")
            if verdict_kind == "consume_route_back_checkpoint_owner_consumption_required"
            else None,
            stage.get("route_checkpoint_evidence_ref")
            if verdict_kind == "consume_route_back_checkpoint_owner_consumption_required"
            else None,
            receipt.get("stage_attempt_ref"),
            receipt.get("receipt_ref"),
            receipt.get("runtime_closeout_ref"),
        ),
        "can_claim_paper_progress": False,
        "can_claim_publication_ready": False,
        "can_claim_submission_ready": False,
        "durable_stop_allowed": False,
    }


def _apply_result(
    *,
    paper_mission_readback: Mapping[str, Any],
    study_id: str,
    profile_ref: str,
    validation: Mapping[str, Any],
    source: str,
    receipt: Mapping[str, Any],
    evidence: Mapping[str, Any],
    consumption: Mapping[str, Any],
    verdict: Mapping[str, Any],
    apply_mode: str,
) -> dict[str, Any]:
    expected_surface = _text(verdict.get("required_authority_surface"))
    expected_mode = {
        "paper-mission receipt-owner-consumption --apply-typed-blocker": "typed_blocker",
        "paper-mission receipt-owner-consumption --apply-route-checkpoint": "route_checkpoint",
    }.get(expected_surface)
    if apply_mode != expected_mode:
        return {
            "surface_kind": "paper_mission_receipt_owner_consumption",
            "schema_version": 1,
            "status": "blocked_apply_mode_mismatch",
            "study_id": study_id,
            "profile_ref": profile_ref,
            "source": source,
            "write_permitted": False,
            "authority_materialized": False,
            "requested_apply_mode": apply_mode,
            "expected_apply_mode": expected_mode,
            "owner_consumption_verdict": dict(verdict),
            "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
        }
    generated_at = _utc_now()
    stage = _stage_closure_summary(paper_mission_readback)
    package = _current_package_summary(paper_mission_readback)
    if apply_mode == "route_checkpoint":
        receipt, evidence, consumption = _route_checkpoint_aligned_receipt_inputs(
            stage=stage,
            receipt=receipt,
            evidence=evidence,
            consumption=consumption,
        )
    receipt_ref = _first_text(
        stage.get("route_checkpoint_evidence_ref")
        if apply_mode == "route_checkpoint"
        else None,
        evidence.get("typed_runtime_blocker_ref"),
        consumption.get("typed_runtime_blocker_ref"),
        evidence.get("runtime_closeout_ref"),
        receipt.get("stage_attempt_ref"),
        receipt.get("receipt_ref"),
    )
    stage_closure_decision = _applied_stage_closure_decision(
        apply_mode=apply_mode,
        study_id=study_id,
        stage=stage,
        package=package,
        receipt=receipt,
        evidence=evidence,
        consumption=consumption,
        receipt_ref=receipt_ref,
        generated_at=generated_at,
        source=source,
    )
    applied_outcome = _mapping(stage_closure_decision.get("outcome"))
    durable_stop_allowed = apply_mode in {"typed_blocker", "route_checkpoint"}
    applied_stage = {
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
        "outcome_kind": _text(applied_outcome.get("kind")) or stage.get("outcome_kind"),
        "transition_kind": _text(applied_outcome.get("transition_kind")) or None,
        "next_legal_action": _first_text(
            applied_outcome.get("next_legal_action"),
            stage_closure_decision.get("next_legal_action"),
        ),
        "decision_ref": _first_text(
            stage_closure_decision.get("decision_ref"),
            stage.get("decision_ref"),
        ),
        "durable_stop_allowed": durable_stop_allowed,
        "authority_materialized": True,
        **(
            {"typed_blocker_evidence_ref": receipt_ref}
            if apply_mode == "typed_blocker"
            else {"route_checkpoint_evidence_ref": receipt_ref}
        ),
        **(
            {"opl_closeout": stage["opl_closeout"]}
            if _mapping(stage.get("opl_closeout"))
            else {}
        ),
    }
    applied_consumption = {
        **dict(consumption),
        "surface_kind": "mas_receipt_consumption_projection",
        "status": (
            "owner_consumed_typed_blocker"
            if apply_mode == "typed_blocker"
            else "owner_consumed_route_checkpoint"
        ),
        "authority_materialized": True,
        "owner_result_kind": "typed_blocker" if apply_mode == "typed_blocker" else "route_checkpoint",
        **(
            {"typed_blocker_evidence_ref": receipt_ref}
            if apply_mode == "typed_blocker"
            else {"route_checkpoint_evidence_ref": receipt_ref}
        ),
        "durable_stop_allowed": durable_stop_allowed,
        "can_claim_paper_progress": False,
        "can_claim_publication_ready": False,
        "can_claim_runtime_ready": False,
    }
    return {
        "surface_kind": "paper_mission_receipt_owner_consumption",
        "schema_version": 1,
        "status": "owner_consumption_applied",
        "study_id": study_id,
        "profile_ref": profile_ref,
        "source": source,
        "apply_mode": apply_mode,
        "write_permitted": True,
        "authority_materialized": True,
        "paper_ready_claim_authorized": False,
        "publication_ready_claim_authorized": False,
        "submission_ready_claim_authorized": False,
        "readback_validation": dict(validation),
        "receipt_evidence": {
            **dict(evidence),
            "authority_materialized": True,
            **(
                {"typed_blocker_evidence_ref": receipt_ref}
                if apply_mode == "typed_blocker"
                else {"route_checkpoint_evidence_ref": receipt_ref}
            ),
        },
        "opl_transition_receipt": _receipt_summary(receipt),
        "mas_receipt_consumption": applied_consumption,
        "stage_closure": applied_stage,
        "stage_closure_decision": stage_closure_decision,
        "current_package": package,
        "owner_consumption_verdict": {
            **dict(verdict),
            "required_authority_surface_exists": True,
            "implemented_surface_role": "mas_owner_consumption_authority_apply_surface",
            "can_claim_submission_ready": False,
            "durable_stop_allowed": True,
        },
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
    }

def _implementation_gap() -> dict[str, Any]:
    return {
        "gap_kind": "mas_owner_consumption_authority_apply_surface_missing",
        "missing_command_or_api": "paper-mission receipt-owner-consumption --apply",
        "required_inputs": [
            "paper-mission inspect --request-opl-runtime-readback JSON",
            "opl_runtime_carrier_readback.receipt_evidence",
            "opl_runtime_carrier_readback.mas_receipt_consumption",
            "stage_closure_decision.outcome",
            "current_package projection",
        ],
        "allowed_write_set": [
            "MAS governed owner receipt / typed blocker / human gate surface only after authority contract exists",
            "ops/medautoscience/paper_mission_receipt_owner_consumption diagnostic packet",
        ],
        "forbidden_write_set": list(FORBIDDEN_AUTHORITY_WRITES),
        "verification": [
            "focused CLI/controller tests",
            "live paper-mission inspect readback for DM002 and DM003",
            "post-consumption paper-mission inspect durable_mission_stop_guard readback",
        ],
    }
