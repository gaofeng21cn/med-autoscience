from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any

from med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_gap_work_orders import (
    live_runtime_gap_evidence_intake_summary,
)
from med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_tail_work_orders import (
    live_tail_evidence_intake_summary,
)


SURFACE_KIND = "mas_live_runtime_evidence_rollup"
VERSION = "mas-live-runtime-evidence-rollup.v1"
LIVE_TAIL_CONTRACT_PATH = Path("contracts/runtime/mas-runtime-live-tail-work-orders.json")
LIVE_RUNTIME_GAP_CONTRACT_PATH = Path("contracts/runtime/mas-live-runtime-gap-work-orders.json")
LIVE_RUNTIME_EVIDENCE_ROLLUP_CONTRACT_PATH = Path(
    "contracts/runtime/mas-live-runtime-evidence-rollup.json"
)


def live_runtime_evidence_rollup_readback(
    *,
    repo_root: Path,
    live_tail_evidence_records: list[Mapping[str, Any]] | None = None,
    live_runtime_gap_evidence_records: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    live_tail_contract = _load_json_object(repo_root / LIVE_TAIL_CONTRACT_PATH)
    live_runtime_gap_contract = _load_json_object(repo_root / LIVE_RUNTIME_GAP_CONTRACT_PATH)
    rollup_contract = _load_json_object(repo_root / LIVE_RUNTIME_EVIDENCE_ROLLUP_CONTRACT_PATH)
    contract_violations = validate_live_runtime_evidence_rollup_contract(
        rollup_contract,
        live_tail_contract=live_tail_contract,
        live_runtime_gap_contract=live_runtime_gap_contract,
    )
    summary = live_runtime_evidence_rollup_summary(
        live_tail_contract=live_tail_contract,
        live_runtime_gap_contract=live_runtime_gap_contract,
        live_tail_evidence_records=live_tail_evidence_records,
        live_runtime_gap_evidence_records=live_runtime_gap_evidence_records,
    )
    return {
        "surface_kind": "mas_live_runtime_evidence_rollup_readback",
        "version": VERSION,
        "repo_root": str(repo_root),
        "contract_refs": {
            "live_tail_work_orders": str(LIVE_TAIL_CONTRACT_PATH),
            "live_runtime_gap_work_orders": str(LIVE_RUNTIME_GAP_CONTRACT_PATH),
            "live_runtime_evidence_rollup": str(LIVE_RUNTIME_EVIDENCE_ROLLUP_CONTRACT_PATH),
        },
        "contract_validation": {
            "status": "passed" if not contract_violations else "failed",
            "violation_count": len(contract_violations),
            "violations": contract_violations,
        },
        "summary": summary,
        "completion_claim_boundary": rollup_contract.get("completion_claim_boundary", {}),
        "completion_claim_allowed": (
            not contract_violations
            and summary.get("rollup_result_status") == "all_work_orders_satisfied"
            and summary.get("live_runtime_readiness_claim_allowed") is True
        ),
        "repo_source_retirement_blocked": False,
        "false_completion_boundary": [
            "contract_validation_failed_means_rollup_untrusted",
            "typed_blocker_required_live_runtime_evidence_rollup",
            "partial_live_runtime_evidence_rollup",
            "repo_source_retirement_complete_as_live_runtime_ready",
            "docs_tests_inventory_or_queue_empty_as_live_runtime_ready",
        ],
    }


def validate_live_runtime_evidence_rollup_contract(
    contract: Mapping[str, Any],
    *,
    live_tail_contract: Mapping[str, Any],
    live_runtime_gap_contract: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    if contract.get("surface_kind") != SURFACE_KIND:
        violations.append(_violation("<contract>", "surface_kind_mismatch"))
    if contract.get("version") != VERSION:
        violations.append(_violation("<contract>", "version_mismatch"))
    if contract.get("repo_source_retirement_blocked") is not False:
        violations.append(_violation("<contract>", "repo_source_retirement_blocked"))
    if contract.get("live_runtime_readiness_claim_allowed") is not False:
        violations.append(_violation("<contract>", "live_runtime_claim_allowed"))

    expected_tail_ids = _work_order_ids(live_tail_contract, "surface_id")
    expected_gap_ids = _work_order_ids(live_runtime_gap_contract, "gap_id")
    if _text_list(contract.get("live_tail_surface_ids")) != expected_tail_ids:
        violations.append(_violation("<contract>", "live_tail_surface_ids_mismatch"))
    if _text_list(contract.get("live_runtime_gap_ids")) != expected_gap_ids:
        violations.append(_violation("<contract>", "live_runtime_gap_ids_mismatch"))

    boundary = contract.get("completion_claim_boundary")
    boundary_mapping = boundary if isinstance(boundary, Mapping) else {}
    required_false = (
        "repo_source_retirement_blocked_by_missing_live_evidence",
        "docs_tests_inventory_or_queue_empty_can_satisfy_rollup",
        "partial_rollup_can_claim_live_runtime_ready",
    )
    for key in required_false:
        if boundary_mapping.get(key) is not False:
            violations.append(_violation("<contract>", f"boundary_mismatch:{key}"))
    if boundary_mapping.get("live_runtime_readiness_claim_requires_all_tail_and_gap_work_orders_satisfied") is not True:
        violations.append(
            _violation(
                "<contract>",
                "boundary_mismatch:live_runtime_readiness_claim_requires_all_tail_and_gap_work_orders_satisfied",
            )
        )
    if boundary_mapping.get("unknown_or_duplicate_evidence_records_can_satisfy_rollup") is not False:
        violations.append(
            _violation(
                "<contract>",
                "boundary_mismatch:unknown_or_duplicate_evidence_records_can_satisfy_rollup",
            )
        )
    if (
        boundary_mapping.get("unknown_or_duplicate_evidence_records_result_status")
        != "typed_blocker_required"
    ):
        violations.append(
            _violation(
                "<contract>",
                "boundary_mismatch:unknown_or_duplicate_evidence_records_result_status",
            )
        )
    if boundary_mapping.get("missing_or_malformed_evidence_records_can_satisfy_rollup") is not False:
        violations.append(
            _violation(
                "<contract>",
                "boundary_mismatch:missing_or_malformed_evidence_records_can_satisfy_rollup",
            )
        )
    if (
        boundary_mapping.get("missing_or_malformed_evidence_records_result_status")
        != "typed_blocker_required"
    ):
        violations.append(
            _violation(
                "<contract>",
                "boundary_mismatch:missing_or_malformed_evidence_records_result_status",
            )
        )
    if (
        boundary_mapping.get("forbidden_or_unaccepted_evidence_source_can_satisfy_rollup")
        is not False
    ):
        violations.append(
            _violation(
                "<contract>",
                "boundary_mismatch:forbidden_or_unaccepted_evidence_source_can_satisfy_rollup",
            )
        )
    if (
        boundary_mapping.get("forbidden_or_unaccepted_evidence_source_result_status")
        != "typed_blocker_required"
    ):
        violations.append(
            _violation(
                "<contract>",
                "boundary_mismatch:forbidden_or_unaccepted_evidence_source_result_status",
            )
        )
    for contract_id, work_order_contract in (
        ("live_tail", live_tail_contract),
        ("live_runtime_gap", live_runtime_gap_contract),
    ):
        schema = _evidence_record_schema(work_order_contract)
        if not _text_list(schema.get("accepted_evidence_source_prefixes")):
            violations.append(
                _violation("<contract>", f"{contract_id}:missing_accepted_source_prefixes")
            )
        if not _text_list(schema.get("forbidden_evidence_source_prefixes")):
            violations.append(
                _violation("<contract>", f"{contract_id}:missing_forbidden_source_prefixes")
            )
        if schema.get("unaccepted_evidence_source_status") != "typed_blocker_required":
            violations.append(
                _violation("<contract>", f"{contract_id}:unaccepted_source_status_mismatch")
            )
        if schema.get("forbidden_evidence_source_status") != "typed_blocker_required":
            violations.append(
                _violation("<contract>", f"{contract_id}:forbidden_source_status_mismatch")
            )
        if schema.get("forbidden_or_unaccepted_source_can_satisfy_work_order") is not False:
            violations.append(
                _violation("<contract>", f"{contract_id}:source_can_satisfy_mismatch")
            )
        if (
            schema.get("forbidden_or_unaccepted_source_blocks_live_runtime_readiness_claim")
            is not True
        ):
            violations.append(
                _violation("<contract>", f"{contract_id}:source_does_not_block_readiness")
            )
    if boundary_mapping.get("authority_family_without_outcome_ref_can_satisfy_rollup") is not False:
        violations.append(
            _violation(
                "<contract>",
                "boundary_mismatch:authority_family_without_outcome_ref_can_satisfy_rollup",
            )
        )
    if (
        boundary_mapping.get("missing_authority_outcome_ref_result_status")
        != "typed_blocker_required"
    ):
        violations.append(
            _violation(
                "<contract>",
                "boundary_mismatch:missing_authority_outcome_ref_result_status",
            )
        )
    if (
        boundary_mapping.get("tail_authority_family_without_outcome_ref_can_satisfy_rollup")
        is not False
    ):
        violations.append(
            _violation(
                "<contract>",
                "boundary_mismatch:tail_authority_family_without_outcome_ref_can_satisfy_rollup",
            )
        )
    if (
        boundary_mapping.get("missing_tail_authority_outcome_ref_result_status")
        != "typed_blocker_required"
    ):
        violations.append(
            _violation(
                "<contract>",
                "boundary_mismatch:missing_tail_authority_outcome_ref_result_status",
            )
        )
    if (
        boundary_mapping.get("accepted_tail_family_without_concrete_ref_can_satisfy_rollup")
        is not False
    ):
        violations.append(
            _violation(
                "<contract>",
                "boundary_mismatch:accepted_tail_family_without_concrete_ref_can_satisfy_rollup",
            )
        )
    if (
        boundary_mapping.get("missing_tail_concrete_evidence_ref_result_status")
        != "typed_blocker_required"
    ):
        violations.append(
            _violation(
                "<contract>",
                "boundary_mismatch:missing_tail_concrete_evidence_ref_result_status",
            )
        )
    if (
        boundary_mapping.get("accepted_gap_family_without_concrete_ref_can_satisfy_rollup")
        is not False
    ):
        violations.append(
            _violation(
                "<contract>",
                "boundary_mismatch:accepted_gap_family_without_concrete_ref_can_satisfy_rollup",
            )
        )
    if (
        boundary_mapping.get("missing_gap_concrete_evidence_ref_result_status")
        != "typed_blocker_required"
    ):
        violations.append(
            _violation(
                "<contract>",
                "boundary_mismatch:missing_gap_concrete_evidence_ref_result_status",
            )
        )
    return violations


def live_runtime_evidence_rollup_summary(
    *,
    live_tail_contract: Mapping[str, Any],
    live_runtime_gap_contract: Mapping[str, Any],
    live_tail_evidence_records: list[Mapping[str, Any]] | None = None,
    live_runtime_gap_evidence_records: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    tail_summary = live_tail_evidence_intake_summary(
        live_tail_contract,
        live_tail_evidence_records or [],
    )
    gap_summary = live_runtime_gap_evidence_intake_summary(
        live_runtime_gap_contract,
        live_runtime_gap_evidence_records or [],
    )
    tail_blocker_count = int(tail_summary.get("typed_blocker_count") or 0)
    gap_blocker_count = int(gap_summary.get("typed_blocker_count") or 0)
    total_blocker_count = tail_blocker_count + gap_blocker_count
    tail_intake_violation_count = int(tail_summary.get("intake_violation_count") or 0)
    gap_intake_violation_count = int(gap_summary.get("intake_violation_count") or 0)
    total_intake_violation_count = (
        tail_intake_violation_count + gap_intake_violation_count
    )
    tail_satisfied_count = int(tail_summary.get("satisfied_count") or 0)
    gap_satisfied_count = int(gap_summary.get("satisfied_count") or 0)
    total_work_order_count = int(tail_summary.get("total_work_order_count") or 0) + int(
        gap_summary.get("total_work_order_count") or 0
    )
    all_work_orders_satisfied = bool(total_work_order_count) and total_blocker_count == 0
    return {
        "surface_kind": "mas_live_runtime_evidence_rollup_summary",
        "version": VERSION,
        "repo_source_retirement_blocked": False,
        "live_runtime_readiness_claim_allowed": all_work_orders_satisfied,
        "rollup_result_status": (
            "all_work_orders_satisfied"
            if all_work_orders_satisfied
            else "typed_blocker_required"
        ),
        "total_work_order_count": total_work_order_count,
        "satisfied_count": tail_satisfied_count + gap_satisfied_count,
        "typed_blocker_count": total_blocker_count,
        "intake_violation_count": total_intake_violation_count,
        "live_tail": tail_summary,
        "live_runtime_gaps": gap_summary,
        "typed_blocker_surface_ids": tail_summary.get("typed_blocker_surface_ids", []),
        "typed_blocker_gap_ids": gap_summary.get("typed_blocker_gap_ids", []),
        "satisfied_surface_ids": tail_summary.get("satisfied_surface_ids", []),
        "satisfied_gap_ids": gap_summary.get("satisfied_gap_ids", []),
    }


def _work_order_ids(contract: Mapping[str, Any], key: str) -> list[str]:
    raw_orders = contract.get("work_orders")
    orders = raw_orders if isinstance(raw_orders, list) else []
    return sorted(
        text
        for order in orders
        if isinstance(order, Mapping) and (text := _text(order.get(key))) is not None
    )


def _text_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return sorted(text for item in value if (text := _text(item)) is not None)
    text = _text(value)
    return [text] if text is not None else []


def _evidence_record_schema(contract: Mapping[str, Any]) -> Mapping[str, Any]:
    boundary = contract.get("completion_claim_boundary")
    if not isinstance(boundary, Mapping):
        return {}
    schema = boundary.get("evidence_record_schema")
    return schema if isinstance(schema, Mapping) else {}


def _text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return payload


def _violation(item_id: str, reason: str) -> dict[str, str]:
    return {"item_id": item_id, "reason": reason}


__all__ = [
    "LIVE_RUNTIME_EVIDENCE_ROLLUP_CONTRACT_PATH",
    "LIVE_RUNTIME_GAP_CONTRACT_PATH",
    "LIVE_TAIL_CONTRACT_PATH",
    "SURFACE_KIND",
    "VERSION",
    "live_runtime_evidence_rollup_readback",
    "live_runtime_evidence_rollup_summary",
    "validate_live_runtime_evidence_rollup_contract",
]
