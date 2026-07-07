from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any

from med_autoscience.runtime_protocol.runtime_surface_retirement.live_runtime_gap_work_orders import (
    live_runtime_gap_evidence_intake_summary,
)
from med_autoscience.runtime_protocol.runtime_surface_retirement.live_tail_work_orders import (
    live_tail_evidence_intake_summary,
)
from med_autoscience.runtime_protocol.runtime_surface_retirement.surface_helpers import (
    _text,
    _text_list as _base_text_list,
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
        "repo_source_retirement_completion": _repo_source_retirement_completion(
            rollup_contract
        ),
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


def evidence_records_from_bundle(
    bundle: Mapping[str, Any],
) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]:
    if not isinstance(bundle, Mapping):
        raise TypeError("live runtime evidence bundle must be a JSON object")
    tail_records = bundle.get("live_tail_evidence_records", [])
    gap_records = bundle.get("live_runtime_gap_evidence_records", [])
    if not isinstance(tail_records, list):
        raise TypeError("live_tail_evidence_records must be a JSON list")
    if not isinstance(gap_records, list):
        raise TypeError("live_runtime_gap_evidence_records must be a JSON list")
    return tail_records, gap_records


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
    repo_source_completion = contract.get("repo_source_retirement_completion")
    repo_source_completion_mapping = (
        repo_source_completion if isinstance(repo_source_completion, Mapping) else {}
    )
    if (
        repo_source_completion_mapping.get("surface_kind")
        != "mas_repo_source_private_surface_retirement_completion"
    ):
        violations.append(_violation("<contract>", "repo_source_completion_surface_kind_mismatch"))
    if repo_source_completion_mapping.get("status") != "complete":
        violations.append(_violation("<contract>", "repo_source_completion_status_mismatch"))
    if repo_source_completion_mapping.get("scope") != "repo_source_physical_retirement_only":
        violations.append(_violation("<contract>", "repo_source_completion_scope_mismatch"))
    if repo_source_completion_mapping.get("completion_claim_allowed") is not True:
        violations.append(_violation("<contract>", "repo_source_completion_claim_not_allowed"))
    if repo_source_completion_mapping.get("repo_source_retirement_blocked") is not False:
        violations.append(_violation("<contract>", "repo_source_completion_blocked"))
    if repo_source_completion_mapping.get("blocked_by_missing_live_evidence") is not False:
        violations.append(_violation("<contract>", "repo_source_completion_live_evidence_blocked"))
    if repo_source_completion_mapping.get("live_runtime_readiness_claim_allowed") is not False:
        violations.append(
            _violation("<contract>", "repo_source_completion_live_runtime_claim_allowed")
        )
    if repo_source_completion_mapping.get("does_not_satisfy_live_runtime_work_orders") is not True:
        violations.append(
            _violation("<contract>", "repo_source_completion_satisfies_live_work_orders")
        )
    if not _text_list(repo_source_completion_mapping.get("evidence_refs")):
        violations.append(_violation("<contract>", "repo_source_completion_missing_evidence_refs"))
    typed_blocker_details = contract.get("typed_blocker_details_readback")
    typed_blocker_details_mapping = (
        typed_blocker_details if isinstance(typed_blocker_details, Mapping) else {}
    )
    if (
        typed_blocker_details_mapping.get("surface_kind")
        != "mas_live_runtime_evidence_rollup_typed_blocker_details"
    ):
        violations.append(_violation("<contract>", "typed_blocker_details_surface_kind_mismatch"))
    expected_detail_fields = [
        "acceptable_evidence_ref_families",
        "live_runtime_readiness_claim_allowed",
        "next_owner",
        "repo_source_retirement_blocked",
        "typed_blocker",
        "work_order_kind",
    ]
    if _text_list(typed_blocker_details_mapping.get("required_fields")) != expected_detail_fields:
        violations.append(_violation("<contract>", "typed_blocker_details_fields_mismatch"))
    if typed_blocker_details_mapping.get("live_tail_identity_field") != "surface_id":
        violations.append(_violation("<contract>", "typed_blocker_details_tail_identity_mismatch"))
    if typed_blocker_details_mapping.get("live_runtime_gap_identity_field") != "gap_id":
        violations.append(_violation("<contract>", "typed_blocker_details_gap_identity_mismatch"))
    templates = contract.get("evidence_record_templates_readback")
    templates_mapping = templates if isinstance(templates, Mapping) else {}
    if (
        templates_mapping.get("surface_kind")
        != "mas_live_runtime_evidence_rollup_evidence_record_templates"
    ):
        violations.append(_violation("<contract>", "evidence_templates_surface_kind_mismatch"))
    if templates_mapping.get("template_status") != "operator_input_required":
        violations.append(_violation("<contract>", "evidence_templates_status_mismatch"))
    if templates_mapping.get("templates_are_evidence_records") is not False:
        violations.append(_violation("<contract>", "evidence_templates_are_records"))
    if templates_mapping.get("templates_can_satisfy_work_orders") is not False:
        violations.append(_violation("<contract>", "evidence_templates_can_satisfy"))
    if templates_mapping.get("templates_can_claim_live_runtime_ready") is not False:
        violations.append(_violation("<contract>", "evidence_templates_can_claim_ready"))
    expected_template_fields = [
        "acceptable_evidence_source_prefixes",
        "concrete_evidence_ref_fields",
        "forbidden_evidence_source_prefixes",
        "live_runtime_readiness_claim_allowed",
        "next_owner",
        "record_template",
        "repo_source_retirement_blocked",
        "transition_identity_ref_fields",
        "work_order_kind",
    ]
    if _text_list(templates_mapping.get("required_template_fields")) != expected_template_fields:
        violations.append(_violation("<contract>", "evidence_templates_fields_mismatch"))
    owner_handoff = contract.get("owner_handoff_readback")
    owner_handoff_mapping = owner_handoff if isinstance(owner_handoff, Mapping) else {}
    if (
        owner_handoff_mapping.get("surface_kind")
        != "mas_live_runtime_evidence_rollup_owner_handoff_queue"
    ):
        violations.append(_violation("<contract>", "owner_handoff_surface_kind_mismatch"))
    if owner_handoff_mapping.get("handoff_status") != "owner_evidence_required":
        violations.append(_violation("<contract>", "owner_handoff_status_mismatch"))
    if owner_handoff_mapping.get("handoff_is_action_authorization") is not False:
        violations.append(_violation("<contract>", "owner_handoff_is_authorization"))
    if owner_handoff_mapping.get("handoff_can_satisfy_work_orders") is not False:
        violations.append(_violation("<contract>", "owner_handoff_can_satisfy"))
    if owner_handoff_mapping.get("handoff_can_claim_live_runtime_ready") is not False:
        violations.append(_violation("<contract>", "owner_handoff_can_claim_ready"))
    expected_handoff_fields = [
        "evidence_record_templates",
        "live_runtime_readiness_claim_allowed",
        "next_owner",
        "repo_source_retirement_blocked",
        "typed_blockers",
        "work_order_count",
        "work_order_keys",
    ]
    if (
        _text_list(owner_handoff_mapping.get("required_handoff_fields"))
        != expected_handoff_fields
    ):
        violations.append(_violation("<contract>", "owner_handoff_fields_mismatch"))
    evidence_bundle = contract.get("evidence_bundle_intake")
    evidence_bundle_mapping = evidence_bundle if isinstance(evidence_bundle, Mapping) else {}
    if (
        evidence_bundle_mapping.get("surface_kind")
        != "mas_live_runtime_evidence_rollup_bundle_intake"
    ):
        violations.append(_violation("<contract>", "evidence_bundle_surface_kind_mismatch"))
    if evidence_bundle_mapping.get("bundle_status") != "operator_input_required":
        violations.append(_violation("<contract>", "evidence_bundle_status_mismatch"))
    if evidence_bundle_mapping.get("bundle_is_evidence_record") is not False:
        violations.append(_violation("<contract>", "evidence_bundle_is_record"))
    if evidence_bundle_mapping.get("bundle_can_satisfy_work_orders_without_records") is not False:
        violations.append(_violation("<contract>", "evidence_bundle_can_satisfy_without_records"))
    if evidence_bundle_mapping.get("bundle_can_claim_live_runtime_ready") is not False:
        violations.append(_violation("<contract>", "evidence_bundle_can_claim_ready"))
    expected_bundle_fields = [
        "live_runtime_gap_evidence_records",
        "live_tail_evidence_records",
    ]
    if (
        _text_list(evidence_bundle_mapping.get("required_bundle_fields"))
        != expected_bundle_fields
    ):
        violations.append(_violation("<contract>", "evidence_bundle_fields_mismatch"))

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
    typed_blocker_details = _typed_blocker_details(
        live_tail_contract=live_tail_contract,
        live_runtime_gap_contract=live_runtime_gap_contract,
        live_tail_summary=tail_summary,
        live_runtime_gap_summary=gap_summary,
    )
    evidence_record_templates = _evidence_record_templates(
        live_tail_contract=live_tail_contract,
        live_runtime_gap_contract=live_runtime_gap_contract,
        live_tail_summary=tail_summary,
        live_runtime_gap_summary=gap_summary,
    )
    owner_handoffs = _owner_handoffs(
        typed_blocker_details=typed_blocker_details,
        evidence_record_templates=evidence_record_templates,
    )
    evidence_bundle_template = _evidence_bundle_template(evidence_record_templates)
    return {
        "surface_kind": "mas_live_runtime_evidence_rollup_summary",
        "version": VERSION,
        "repo_source_retirement_completion": {
            "surface_kind": "mas_repo_source_private_surface_retirement_completion",
            "status": "complete",
            "scope": "repo_source_physical_retirement_only",
            "completion_claim_allowed": True,
            "repo_source_retirement_blocked": False,
            "blocked_by_missing_live_evidence": False,
            "live_runtime_readiness_claim_allowed": False,
            "does_not_satisfy_live_runtime_work_orders": True,
        },
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
        "typed_blocker_details": typed_blocker_details,
        "evidence_record_templates": evidence_record_templates,
        "evidence_bundle_template": evidence_bundle_template,
        "owner_handoffs": owner_handoffs,
        "satisfied_surface_ids": tail_summary.get("satisfied_surface_ids", []),
        "satisfied_gap_ids": gap_summary.get("satisfied_gap_ids", []),
    }


def _evidence_bundle_template(
    evidence_record_templates: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_live_runtime_evidence_rollup_bundle_template",
        "template_status": "operator_input_required",
        "live_tail_evidence_records": [
            template["record_template"]
            for template in evidence_record_templates
            if template.get("work_order_kind") == "live_tail"
        ],
        "live_runtime_gap_evidence_records": [
            template["record_template"]
            for template in evidence_record_templates
            if template.get("work_order_kind") == "live_runtime_gap"
        ],
        "bundle_is_evidence_record": False,
        "bundle_can_satisfy_work_orders_without_filled_records": False,
        "bundle_can_claim_live_runtime_ready": False,
        "repo_source_retirement_blocked": False,
        "live_runtime_readiness_claim_allowed": False,
    }


def _typed_blocker_details(
    *,
    live_tail_contract: Mapping[str, Any],
    live_runtime_gap_contract: Mapping[str, Any],
    live_tail_summary: Mapping[str, Any],
    live_runtime_gap_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    tail_orders = _work_orders_by_id(live_tail_contract, "surface_id")
    gap_orders = _work_orders_by_id(live_runtime_gap_contract, "gap_id")
    return [
        _tail_blocker_detail(surface_id, tail_orders.get(surface_id, {}))
        for surface_id in _text_list(live_tail_summary.get("typed_blocker_surface_ids"))
    ] + [
        _gap_blocker_detail(gap_id, gap_orders.get(gap_id, {}))
        for gap_id in _text_list(live_runtime_gap_summary.get("typed_blocker_gap_ids"))
    ]


def _evidence_record_templates(
    *,
    live_tail_contract: Mapping[str, Any],
    live_runtime_gap_contract: Mapping[str, Any],
    live_tail_summary: Mapping[str, Any],
    live_runtime_gap_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    tail_orders = _work_orders_by_id(live_tail_contract, "surface_id")
    gap_orders = _work_orders_by_id(live_runtime_gap_contract, "gap_id")
    tail_schema = _evidence_record_schema(live_tail_contract)
    gap_schema = _evidence_record_schema(live_runtime_gap_contract)
    return [
        _tail_evidence_record_template(
            surface_id,
            tail_orders.get(surface_id, {}),
            tail_schema,
        )
        for surface_id in _text_list(live_tail_summary.get("typed_blocker_surface_ids"))
    ] + [
        _gap_evidence_record_template(
            gap_id,
            gap_orders.get(gap_id, {}),
            gap_schema,
        )
        for gap_id in _text_list(live_runtime_gap_summary.get("typed_blocker_gap_ids"))
    ]


def _owner_handoffs(
    *,
    typed_blocker_details: list[dict[str, Any]],
    evidence_record_templates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    details_by_key = {
        _work_order_key(detail): detail
        for detail in typed_blocker_details
        if _work_order_key(detail) is not None
    }
    templates_by_key = {
        _work_order_key(template): template
        for template in evidence_record_templates
        if _work_order_key(template) is not None
    }
    owners = sorted(
        {
            _text(detail.get("next_owner")) or "runtime owner"
            for detail in details_by_key.values()
        }
    )
    handoffs: list[dict[str, Any]] = []
    for owner in owners:
        owner_keys = sorted(
            key
            for key, detail in details_by_key.items()
            if (_text(detail.get("next_owner")) or "runtime owner") == owner
        )
        handoffs.append(
            {
                "surface_kind": "mas_live_runtime_evidence_rollup_owner_handoff",
                "next_owner": owner,
                "handoff_status": "owner_evidence_required",
                "work_order_count": len(owner_keys),
                "work_order_keys": owner_keys,
                "typed_blockers": [details_by_key[key] for key in owner_keys],
                "evidence_record_templates": [
                    templates_by_key[key] for key in owner_keys if key in templates_by_key
                ],
                "handoff_is_action_authorization": False,
                "handoff_can_satisfy_work_orders": False,
                "handoff_can_claim_live_runtime_ready": False,
                "repo_source_retirement_blocked": False,
                "live_runtime_readiness_claim_allowed": False,
            }
        )
    return handoffs


def _work_order_key(item: Mapping[str, Any]) -> str | None:
    work_order_kind = _text(item.get("work_order_kind"))
    if work_order_kind == "live_tail":
        surface_id = _text(item.get("surface_id"))
        return f"live_tail:{surface_id}" if surface_id is not None else None
    if work_order_kind == "live_runtime_gap":
        gap_id = _text(item.get("gap_id"))
        return f"live_runtime_gap:{gap_id}" if gap_id is not None else None
    return None


def _tail_evidence_record_template(
    surface_id: str,
    order: Mapping[str, Any],
    schema: Mapping[str, Any],
) -> dict[str, Any]:
    return _evidence_record_template(
        work_order_kind="live_tail",
        identity_field="surface_id",
        identity_value=surface_id,
        order=order,
        schema=schema,
    )


def _gap_evidence_record_template(
    gap_id: str,
    order: Mapping[str, Any],
    schema: Mapping[str, Any],
) -> dict[str, Any]:
    template = _evidence_record_template(
        work_order_kind="live_runtime_gap",
        identity_field="gap_id",
        identity_value=gap_id,
        order=order,
        schema=schema,
    )
    template["gap_text"] = _text(order.get("gap_text"))
    return template


def _evidence_record_template(
    *,
    work_order_kind: str,
    identity_field: str,
    identity_value: str,
    order: Mapping[str, Any],
    schema: Mapping[str, Any],
) -> dict[str, Any]:
    evidence_families = _text_list(order.get("acceptable_evidence_ref_families"))
    record_template: dict[str, Any] = {
        identity_field: identity_value,
        "evidence_source": None,
        "evidence_ref_families": [],
        "evidence_refs": [],
    }
    if _families_need_authority_outcome(evidence_families, schema):
        record_template["typed_blocker_ref"] = None
    if _families_need_transition_identity(evidence_families, schema):
        for field in _text_list(schema.get("transition_identity_ref_fields")):
            record_template[field] = None
    return {
        "work_order_kind": work_order_kind,
        identity_field: identity_value,
        "next_owner": _text(order.get("next_owner")) or "runtime owner",
        "typed_blocker": _text(order.get("typed_blocker_when_missing"))
        or f"{identity_value}_live_runtime_evidence_required",
        "template_status": "operator_input_required",
        "record_template": record_template,
        "acceptable_evidence_source_prefixes": _text_list(
            schema.get("accepted_evidence_source_prefixes")
        ),
        "forbidden_evidence_source_prefixes": _text_list(
            schema.get("forbidden_evidence_source_prefixes")
        ),
        "acceptable_evidence_ref_families": evidence_families,
        "concrete_evidence_ref_fields": _text_list(
            schema.get("concrete_evidence_ref_fields")
        ),
        "authority_outcome_ref_fields": _text_list(
            schema.get("authority_outcome_ref_fields")
        ),
        "transition_identity_ref_fields": _text_list(
            schema.get("transition_identity_ref_fields")
        ),
        "templates_are_evidence_records": False,
        "templates_can_satisfy_work_orders": False,
        "repo_source_retirement_blocked": False,
        "live_runtime_readiness_claim_allowed": False,
    }


def _families_need_authority_outcome(
    evidence_families: list[str],
    schema: Mapping[str, Any],
) -> bool:
    required = set(_text_list(schema.get("authority_outcome_ref_required_for_families")))
    return bool(required.intersection(evidence_families))


def _families_need_transition_identity(
    evidence_families: list[str],
    schema: Mapping[str, Any],
) -> bool:
    required = set(_text_list(schema.get("transition_identity_ref_required_for_families")))
    return bool(required.intersection(evidence_families))


def _repo_source_retirement_completion(contract: Mapping[str, Any]) -> dict[str, Any]:
    raw_completion = contract.get("repo_source_retirement_completion")
    completion = raw_completion if isinstance(raw_completion, Mapping) else {}
    return {
        "surface_kind": _text(completion.get("surface_kind"))
        or "mas_repo_source_private_surface_retirement_completion",
        "status": _text(completion.get("status")) or "unknown",
        "scope": _text(completion.get("scope")) or "repo_source_physical_retirement_only",
        "claim": _text(completion.get("claim")),
        "completion_claim_allowed": completion.get("completion_claim_allowed") is True,
        "repo_source_retirement_blocked": completion.get("repo_source_retirement_blocked")
        is True,
        "blocked_by_missing_live_evidence": completion.get("blocked_by_missing_live_evidence")
        is True,
        "live_runtime_readiness_claim_allowed": (
            completion.get("live_runtime_readiness_claim_allowed") is True
        ),
        "does_not_satisfy_live_runtime_work_orders": (
            completion.get("does_not_satisfy_live_runtime_work_orders") is True
        ),
        "evidence_refs": _text_list(completion.get("evidence_refs")),
    }


def _tail_blocker_detail(surface_id: str, order: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "work_order_kind": "live_tail",
        "surface_id": surface_id,
        "next_owner": _text(order.get("next_owner")) or "surface owner",
        "typed_blocker": _text(order.get("typed_blocker_when_missing"))
        or f"{surface_id}_live_runtime_readiness_evidence_required",
        "acceptable_evidence_ref_families": _text_list(
            order.get("acceptable_evidence_ref_families")
        ),
        "forbidden_evidence_substitutes": _text_list(
            order.get("forbidden_evidence_substitutes")
        ),
        "repo_source_retirement_blocked": False,
        "live_runtime_readiness_claim_allowed": False,
    }


def _gap_blocker_detail(gap_id: str, order: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "work_order_kind": "live_runtime_gap",
        "gap_id": gap_id,
        "gap_text": _text(order.get("gap_text")),
        "next_owner": _text(order.get("next_owner")) or "runtime owner",
        "typed_blocker": _text(order.get("typed_blocker_when_missing"))
        or f"{gap_id}_live_runtime_evidence_required",
        "acceptable_evidence_ref_families": _text_list(
            order.get("acceptable_evidence_ref_families")
        ),
        "forbidden_evidence_substitutes": _text_list(
            order.get("forbidden_evidence_substitutes")
        ),
        "repo_source_retirement_blocked": False,
        "live_runtime_readiness_claim_allowed": False,
    }


def _work_orders_by_id(contract: Mapping[str, Any], key: str) -> dict[str, Mapping[str, Any]]:
    raw_orders = contract.get("work_orders")
    orders = raw_orders if isinstance(raw_orders, list) else []
    return {
        text: order
        for order in orders
        if isinstance(order, Mapping) and (text := _text(order.get(key))) is not None
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
    return _base_text_list(value, sort=True)


def _evidence_record_schema(contract: Mapping[str, Any]) -> Mapping[str, Any]:
    boundary = contract.get("completion_claim_boundary")
    if not isinstance(boundary, Mapping):
        return {}
    schema = boundary.get("evidence_record_schema")
    return schema if isinstance(schema, Mapping) else {}


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
