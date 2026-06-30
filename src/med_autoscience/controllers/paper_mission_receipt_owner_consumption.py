from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

FORBIDDEN_AUTHORITY_WRITES = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "owner receipt",
    "typed blocker",
    "human gate",
    "current_package",
    "runtime queue/provider attempts",
    "Yang study truth surfaces",
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


def latest_receipt_owner_consumption_readback(
    *,
    workspace_root: Path,
    study_id: str,
) -> dict[str, Any] | None:
    ledger_root = (
        workspace_root.expanduser().resolve()
        / "ops"
        / "medautoscience"
        / "paper_mission_receipt_owner_consumption"
    )
    if not ledger_root.exists():
        return None
    candidates: list[tuple[float, str, dict[str, Any]]] = []
    for packet_ref in ledger_root.glob(f"**/{study_id}/receipt_owner_consumption.json"):
        payload = _valid_owner_consumption_readback(
            packet_ref=packet_ref,
            study_id=study_id,
        )
        if payload is None:
            continue
        try:
            mtime = packet_ref.stat().st_mtime
        except OSError:
            mtime = 0.0
        candidates.append((mtime, str(packet_ref), payload))
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item[0], item[1]))[2]


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
    if consumption and _text(consumption.get("status")) != "requires_mas_owner_consumption":
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
    return {
        "surface_kind": "paper_mission_receipt_owner_consumption",
        "schema_version": 1,
        "status": "owner_consumption_evidence_materialized",
        "study_id": study_id,
        "profile_ref": profile_ref,
        "source": source,
        "write_permitted": False,
        "authority_materialized": False,
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


def _owner_consumption_verdict(
    *,
    paper_mission_readback: Mapping[str, Any],
    receipt: Mapping[str, Any],
    consumption: Mapping[str, Any],
) -> dict[str, Any]:
    stage = _stage_closure_summary(paper_mission_readback)
    package = _current_package_summary(paper_mission_readback)
    if stage["outcome_kind"] == "typed_blocker":
        verdict_kind = "record_typed_blocker_owner_consumption_required"
        required_authority_surface = "paper-mission receipt-owner-consumption --apply-typed-blocker"
    elif (
        stage["outcome_kind"] == "next_stage_transition"
        and stage["transition_kind"] == "route_back_candidate_checkpoint"
    ):
        verdict_kind = "consume_route_back_checkpoint_owner_consumption_required"
        required_authority_surface = "paper-mission receipt-owner-consumption --apply-route-checkpoint"
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
    receipt_ref = _first_text(
        evidence.get("typed_runtime_blocker_ref"),
        consumption.get("typed_runtime_blocker_ref"),
        evidence.get("runtime_closeout_ref"),
        receipt.get("stage_attempt_ref"),
        receipt.get("receipt_ref"),
    )
    stage_closure_decision = _applied_stage_closure_decision(
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
    applied_stage = {
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
        "durable_stop_allowed": True,
        "authority_materialized": True,
        "typed_blocker_evidence_ref": receipt_ref,
    }
    applied_consumption = {
        **dict(consumption),
        "surface_kind": "mas_receipt_consumption_projection",
        "status": "owner_consumed_typed_blocker",
        "authority_materialized": True,
        "owner_result_kind": "typed_blocker",
        "typed_blocker_evidence_ref": receipt_ref,
        "durable_stop_allowed": True,
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
            "typed_blocker_evidence_ref": receipt_ref,
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


def _applied_stage_closure_decision(
    *,
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
    return {
        "surface_kind": "mas_stage_closure_decision",
        "schema_version": 1,
        "source": source,
        "study_id": study_id,
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


def _write_output_packet(
    *,
    output_root: Path,
    study_id: str,
    payload: Mapping[str, Any],
    writes_authority: bool = False,
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    packet_path = output_root / study_id / "receipt_owner_consumption.json"
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    packet_path.write_text(text + "\n", encoding="utf-8")
    return {
        "surface_kind": "paper_mission_receipt_owner_consumption_output_manifest",
        "schema_version": 1,
        "output_root": str(output_root),
        "packet_ref": str(packet_path),
        "packet_sha256": hashlib.sha256((text + "\n").encode("utf-8")).hexdigest(),
        "writes_authority": bool(writes_authority),
        "writes_yang_authority": False,
        "writes_receipt_owner_consumption": bool(writes_authority),
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
    }


def _valid_owner_consumption_readback(
    *,
    packet_ref: Path,
    study_id: str,
) -> dict[str, Any] | None:
    payload = _read_json_object(packet_ref)
    if payload.get("surface_kind") != "paper_mission_receipt_owner_consumption":
        return None
    if _text(payload.get("study_id")) != study_id:
        return None
    if payload.get("status") != "owner_consumption_applied":
        return None
    if payload.get("authority_materialized") is not True:
        return None
    decision = _mapping(payload.get("stage_closure_decision"))
    outcome = _mapping(decision.get("outcome"))
    if outcome.get("kind") != "typed_blocker":
        return None
    if decision.get("counts_as_typed_blocker") is not True:
        return None
    boundary = _mapping(decision.get("authority_boundary"))
    if any(
        boundary.get(flag) is True
        for flag in (
            "writes_owner_receipt",
            "writes_human_gate",
            "writes_current_package",
            "writes_submission_ready_package",
            "writes_runtime_queue_or_provider_attempt",
        )
    ):
        return None
    return {
        **payload,
        "source_ref": str(packet_ref),
        "decision_ref": str(packet_ref),
        "source_surface_kind": "paper_mission_receipt_owner_consumption_ledger",
    }


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _stage_closure_summary(readback: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(readback.get("stage_closure_decision"))
    outcome = _mapping(decision.get("outcome"))
    guard = _mapping(readback.get("durable_mission_stop_guard"))
    return {
        "outcome_kind": _text(outcome.get("kind")) or _text(readback.get("stage_closure_outcome")),
        "transition_kind": _text(outcome.get("transition_kind")) or None,
        "next_legal_action": _first_text(outcome.get("next_legal_action"), decision.get("next_legal_action")),
        "decision_ref": _first_text(decision.get("decision_ref"), readback.get("stage_closure_decision_ref")),
        "durable_stop_allowed": guard.get("durable_stop_allowed") is True,
    }


def _current_package_summary(readback: Mapping[str, Any]) -> dict[str, Any]:
    package = _mapping(readback.get("current_package"))
    return {
        "status": _first_text(package.get("status"), package.get("freshness")),
        "package_kind": _text(package.get("package_kind")) or None,
        "can_submit": package.get("can_submit") is True,
        "quality_gate_status": _first_text(package.get("quality_gate_status"), package.get("gate_status")),
        "known_blockers": _text_list(package.get("known_blockers")),
        "root": _text(package.get("root")) or None,
        "zip_path": _text(package.get("zip_path")) or None,
        "zip_exists": package.get("zip_exists") is True,
    }


def _receipt_summary(receipt: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface_kind": _text(receipt.get("surface_kind")) or None,
        "receipt_status": _text(receipt.get("receipt_status")) or None,
        "role": _text(receipt.get("role")) or None,
        "task_id": _text(receipt.get("task_id")) or None,
        "task_status": _text(receipt.get("task_status")) or None,
        "stage_attempt_id": _text(receipt.get("stage_attempt_id")) or None,
        "stage_attempt_ref": _text(receipt.get("stage_attempt_ref")) or None,
        "closeout_receipt_status": _text(receipt.get("closeout_receipt_status")) or None,
        "blocked_reason": _text(receipt.get("blocked_reason")) or None,
        "can_claim_paper_progress": receipt.get("can_claim_paper_progress") is True,
    }


def _carrier(readback: Mapping[str, Any]) -> Mapping[str, Any]:
    carrier = dict(_mapping(readback.get("opl_runtime_carrier_readback")))
    for key in ("opl_transition_receipt", "receipt_evidence", "mas_receipt_consumption"):
        if not _mapping(carrier.get(key)):
            value = _mapping(readback.get(key))
            if value:
                carrier[key] = value
    return carrier


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _text(value)
        if text:
            return text
    return None


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
