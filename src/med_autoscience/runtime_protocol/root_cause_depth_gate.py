from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


SURFACE_KIND = "mas_root_cause_depth_gate"
READBACK_SURFACE_KIND = "mas_root_cause_depth_gate_readback"
VERSION = "mas-root-cause-depth-gate.v1"
CONTRACT_PATH = Path("contracts/runtime/mas-root-cause-depth-gate.json")
MINIMUM_REPORT_DEPTH = "L3_owner_repair_path"


def root_cause_depth_gate_readback(
    *,
    repo_root: Path,
    audit_records: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    contract = _load_json_object(Path(repo_root) / CONTRACT_PATH)
    contract_violations = validate_root_cause_depth_gate_contract(contract)
    audit_summary = root_cause_depth_gate_audit_summary(
        contract,
        audit_records or [],
    )
    return {
        "surface_kind": READBACK_SURFACE_KIND,
        "version": VERSION,
        "repo_root": str(Path(repo_root).resolve()),
        "contract_refs": {
            "root_cause_depth_gate": str(CONTRACT_PATH),
        },
        "contract_validation": {
            "status": "passed" if not contract_violations else "failed",
            "violation_count": len(contract_violations),
            "violations": contract_violations,
        },
        "audit_summary": audit_summary,
        "completion_claim_boundary": contract.get("completion_claim_boundary", {}),
        "completion_claim_allowed": (
            not contract_violations
            and audit_summary.get("all_records_closeout_eligible") is True
        ),
        "paper_progress_claim_allowed": False,
        "runtime_readiness_claim_allowed": False,
        "false_completion_boundary": contract.get(
            "forbidden_completion_interpretations",
            [],
        ),
    }


def audit_records_from_bundle(bundle: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    if not isinstance(bundle, Mapping):
        raise TypeError("root cause audit bundle must be a JSON object")
    records = bundle.get("audit_records", [])
    if not isinstance(records, list):
        raise TypeError("audit_records must be a JSON list")
    return records


def root_cause_depth_gate_audit_summary(
    contract: Mapping[str, Any],
    audit_records: list[Mapping[str, Any]],
) -> dict[str, Any]:
    results = [
        validate_root_cause_audit_record(contract, record, index=index)
        for index, record in enumerate(audit_records)
    ]
    closeout_eligible_count = sum(
        1 for result in results if result["closeout_eligible"] is True
    )
    typed_blocker_count = sum(
        1 for result in results if result["status"] == "typed_blocker_required"
    )
    return {
        "surface_kind": "mas_root_cause_depth_gate_audit_summary",
        "record_count": len(audit_records),
        "closeout_eligible_count": closeout_eligible_count,
        "typed_blocker_count": typed_blocker_count,
        "all_records_closeout_eligible": bool(audit_records)
        and closeout_eligible_count == len(audit_records),
        "result_status": (
            "no_audit_records"
            if not audit_records
            else "closeout_eligible"
            if closeout_eligible_count == len(audit_records)
            else "typed_blocker_required"
        ),
        "results": results,
        "report_template": contract.get("report_template", {}),
        "minimum_depth_by_context": contract.get("minimum_depth_by_context", {}),
    }


def validate_root_cause_audit_record(
    contract: Mapping[str, Any],
    record: Mapping[str, Any],
    *,
    index: int = 0,
) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        return _record_result(
            index=index,
            status="typed_blocker_required",
            closeout_eligible=False,
            reasons=["record_not_mapping"],
        )

    required_fields = _text_list(contract.get("required_report_fields"))
    proof_required_fields = _text_list(contract.get("proof_required_fields"))
    symptom_only_statuses = set(_text_list(contract.get("symptom_only_statuses")))
    minimum_depth_by_context = {
        key: value
        for key, value in _mapping(contract.get("minimum_depth_by_context")).items()
        if isinstance(key, str) and isinstance(value, str)
    }

    reasons: list[str] = []
    missing_fields = [
        field for field in required_fields if not _has_non_empty_value(record.get(field))
    ]
    if missing_fields:
        reasons.append("missing_required_fields")

    proof = _mapping(record.get("proof"))
    missing_proof_fields = [
        field
        for field in proof_required_fields
        if not _has_non_empty_value(proof.get(field))
    ]
    if missing_proof_fields:
        reasons.append("missing_proof_fields")

    evidence_refs = _text_list(proof.get("evidence_refs"))
    if not evidence_refs:
        reasons.append("missing_cross_surface_evidence")

    symptom = _text(record.get("symptom"))
    root_cause = _text(record.get("root_cause"))
    failing_boundary = _text(record.get("failing_boundary"))
    owner_surface = _text(record.get("owner_surface"))
    fix_or_next_action = _text(record.get("fix_or_next_action"))

    if symptom and symptom in symptom_only_statuses:
        if root_cause == symptom:
            reasons.append("root_cause_repeats_symptom")
        if not failing_boundary:
            reasons.append("symptom_without_failing_boundary")

    if root_cause and root_cause in symptom_only_statuses:
        reasons.append("root_cause_is_symptom_only_status")

    if root_cause and failing_boundary and root_cause == failing_boundary:
        reasons.append("root_cause_repeats_failing_boundary")

    context = _text(record.get("context")) or "repair_lane_proposal"
    depth = _text(record.get("depth")) or _infer_depth(
        failing_boundary=failing_boundary,
        evidence_refs=evidence_refs,
        owner_surface=owner_surface,
        fix_or_next_action=fix_or_next_action,
        prevention=_text(record.get("prevention")),
    )
    required_depth = minimum_depth_by_context.get(context, MINIMUM_REPORT_DEPTH)
    if _depth_rank(depth) < _depth_rank(required_depth):
        reasons.append("depth_below_required")

    status = "closeout_eligible" if not reasons else "typed_blocker_required"
    return _record_result(
        index=index,
        status=status,
        closeout_eligible=status == "closeout_eligible",
        reasons=reasons,
        context=context,
        depth=depth,
        required_depth=required_depth,
        missing_fields=missing_fields,
        missing_proof_fields=missing_proof_fields,
    )


def validate_root_cause_depth_gate_contract(
    contract: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    if contract.get("surface_kind") != SURFACE_KIND:
        violations.append(_violation("<contract>", "surface_kind_mismatch"))
    if contract.get("version") != VERSION:
        violations.append(_violation("<contract>", "version_mismatch"))

    expected_fields = [
        "symptom",
        "failing_boundary",
        "root_cause",
        "owner_surface",
        "fix_or_next_action",
        "proof",
    ]
    if _text_list(contract.get("required_report_fields")) != expected_fields:
        violations.append(_violation("<contract>", "required_report_fields_mismatch"))

    expected_proof_fields = ["evidence_refs", "proves", "does_not_prove"]
    if _text_list(contract.get("proof_required_fields")) != expected_proof_fields:
        violations.append(_violation("<contract>", "proof_required_fields_mismatch"))

    ladder_depths = [
        _text(item.get("depth"))
        for item in _list_of_mappings(contract.get("depth_ladder"))
    ]
    expected_depths = [
        "L0_symptom",
        "L1_failing_boundary",
        "L2_cross_surface_evidence",
        "L3_owner_repair_path",
        "L4_prevention_writeback",
    ]
    if ladder_depths != expected_depths:
        violations.append(_violation("<contract>", "depth_ladder_mismatch"))

    minimum_depth = _mapping(contract.get("minimum_depth_by_context"))
    for required_key in (
        "supervisor_heartbeat",
        "currentness_drift",
        "false_progress_or_readiness_claim",
        "repair_lane_proposal",
        "candidate_absorption",
        "mission_closeout",
    ):
        if minimum_depth.get(required_key) != MINIMUM_REPORT_DEPTH:
            violations.append(
                _violation("<contract>", f"minimum_depth_mismatch:{required_key}")
            )
    if minimum_depth.get("thorough_root_cause_request") != "L4_prevention_writeback":
        violations.append(
            _violation("<contract>", "minimum_depth_mismatch:thorough_root_cause_request")
        )

    symptom_only_statuses = set(_text_list(contract.get("symptom_only_statuses")))
    for status in (
        "blocked",
        "owner_consumption_saturation_wait",
        "current_owner_identity_unavailable_for_guard",
    ):
        if status not in symptom_only_statuses:
            violations.append(_violation("<contract>", f"missing_symptom_only_status:{status}"))

    forbidden = set(_text_list(contract.get("forbidden_completion_interpretations")))
    for interpretation in (
        "symptom_label_as_root_cause",
        "repair_lane_commit_as_paper_progress",
        "candidate_absorption_as_owner_path_unblocked",
        "owner_consumption_saturation_wait_as_mission_closeout",
        "current_owner_identity_unavailable_for_guard_as_owner_path_repaired",
    ):
        if interpretation not in forbidden:
            violations.append(
                _violation("<contract>", f"missing_forbidden_interpretation:{interpretation}")
            )

    accounting = _mapping(contract.get("paper_progress_accounting"))
    if accounting.get("platform_repair_alone_can_claim_paper_progress") is not False:
        violations.append(_violation("<contract>", "platform_repair_progress_boundary_mismatch"))
    if not _text_list(accounting.get("paper_progress_requires_one_of")):
        violations.append(_violation("<contract>", "missing_paper_progress_evidence_families"))

    repair_boundary = _mapping(contract.get("repair_lane_claim_boundary"))
    if repair_boundary.get("cannot_claim_owner_path_unblocked_from_guardrail_only_fix") is not True:
        violations.append(_violation("<contract>", "guardrail_fix_boundary_mismatch"))

    b002_guardrail = _mapping(contract.get("b002_b003_guardrail"))
    owner_identity = _mapping(b002_guardrail.get("current_owner_identity_unavailable_for_guard"))
    if owner_identity.get("allowed_claim") != "precheck_does_not_write_forbidden_surfaces":
        violations.append(_violation("<contract>", "owner_identity_allowed_claim_mismatch"))
    owner_identity_forbidden = set(_text_list(owner_identity.get("forbidden_claims")))
    if "B002_owner_path_repaired" not in owner_identity_forbidden:
        violations.append(_violation("<contract>", "owner_identity_missing_forbidden_claim"))
    saturation = _mapping(b002_guardrail.get("owner_consumption_saturation_wait"))
    saturation_forbidden = set(_text_list(saturation.get("forbidden_claims")))
    if "mission_closeout" not in saturation_forbidden:
        violations.append(_violation("<contract>", "saturation_missing_forbidden_claim"))

    boundary = _mapping(contract.get("completion_claim_boundary"))
    if boundary.get("root_cause_depth_gate_validation_can_claim_runtime_ready") is not False:
        violations.append(_violation("<contract>", "runtime_ready_claim_boundary_mismatch"))
    if boundary.get("root_cause_depth_gate_validation_can_claim_paper_progress") is not False:
        violations.append(_violation("<contract>", "paper_progress_claim_boundary_mismatch"))
    if boundary.get("audit_record_missing_required_fields_result_status") != "typed_blocker_required":
        violations.append(_violation("<contract>", "missing_fields_result_status_mismatch"))
    if boundary.get("audit_record_symptom_only_result_status") != "typed_blocker_required":
        violations.append(_violation("<contract>", "symptom_only_result_status_mismatch"))
    if boundary.get("audit_record_without_cross_surface_evidence_result_status") != "typed_blocker_required":
        violations.append(_violation("<contract>", "missing_cross_surface_result_status_mismatch"))
    if boundary.get("repair_lane_or_closeout_below_owner_repair_path_can_close") is not False:
        violations.append(_violation("<contract>", "below_l3_closeout_boundary_mismatch"))
    if boundary.get("guardrail_only_fix_can_claim_owner_path_unblocked") is not False:
        violations.append(_violation("<contract>", "guardrail_owner_path_boundary_mismatch"))

    template = _mapping(contract.get("report_template"))
    if _text(template.get("context")) != "repair_lane_proposal":
        violations.append(_violation("<contract>", "report_template_context_mismatch"))
    if not _mapping(template.get("proof")):
        violations.append(_violation("<contract>", "report_template_missing_proof"))

    return violations


def _infer_depth(
    *,
    failing_boundary: str | None,
    evidence_refs: list[str],
    owner_surface: str | None,
    fix_or_next_action: str | None,
    prevention: str | None,
) -> str:
    if prevention:
        return "L4_prevention_writeback"
    if failing_boundary and evidence_refs and owner_surface and fix_or_next_action:
        return "L3_owner_repair_path"
    if failing_boundary and evidence_refs:
        return "L2_cross_surface_evidence"
    if failing_boundary:
        return "L1_failing_boundary"
    return "L0_symptom"


def _depth_rank(depth: str | None) -> int:
    order = {
        "L0_symptom": 0,
        "L1_failing_boundary": 1,
        "L2_cross_surface_evidence": 2,
        "L3_owner_repair_path": 3,
        "L4_prevention_writeback": 4,
    }
    return order.get(depth or "", -1)


def _record_result(
    *,
    index: int,
    status: str,
    closeout_eligible: bool,
    reasons: list[str],
    context: str | None = None,
    depth: str | None = None,
    required_depth: str | None = None,
    missing_fields: list[str] | None = None,
    missing_proof_fields: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "record_index": index,
        "status": status,
        "closeout_eligible": closeout_eligible,
        "reasons": reasons,
        "context": context,
        "depth": depth,
        "required_depth": required_depth,
        "missing_fields": missing_fields or [],
        "missing_proof_fields": missing_proof_fields or [],
    }


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return payload


def _has_non_empty_value(value: object) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, list):
        return bool(value)
    return value is not None


def _text(value: object) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list_of_mappings(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _violation(path: str, reason: str) -> dict[str, str]:
    return {"path": path, "reason": reason}


__all__ = [
    "CONTRACT_PATH",
    "SURFACE_KIND",
    "VERSION",
    "audit_records_from_bundle",
    "root_cause_depth_gate_audit_summary",
    "root_cause_depth_gate_readback",
    "validate_root_cause_audit_record",
    "validate_root_cause_depth_gate_contract",
]
