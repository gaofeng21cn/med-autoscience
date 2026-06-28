from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
LIVE_TAIL_PATH = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-live-tail-work-orders.json"
LIVE_GAP_PATH = REPO_ROOT / "contracts" / "runtime" / "mas-live-runtime-gap-work-orders.json"
ROLLUP_PATH = REPO_ROOT / "contracts" / "runtime" / "mas-live-runtime-evidence-rollup.json"


def _live_tail_contract() -> dict:
    return json.loads(LIVE_TAIL_PATH.read_text(encoding="utf-8"))


def _live_gap_contract() -> dict:
    return json.loads(LIVE_GAP_PATH.read_text(encoding="utf-8"))


def _rollup_contract() -> dict:
    return json.loads(ROLLUP_PATH.read_text(encoding="utf-8"))


def test_live_runtime_evidence_rollup_contract_matches_tail_and_gap_work_orders() -> None:
    rollup = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_evidence_rollup"
    )
    tail_contract = _live_tail_contract()
    gap_contract = _live_gap_contract()
    rollup_contract = _rollup_contract()

    assert rollup.validate_live_runtime_evidence_rollup_contract(
        rollup_contract,
        live_tail_contract=tail_contract,
        live_runtime_gap_contract=gap_contract,
    ) == []
    assert rollup_contract["surface_kind"] == "mas_live_runtime_evidence_rollup"
    assert rollup_contract["repo_source_retirement_blocked"] is False
    assert rollup_contract["repo_source_retirement_completion"] == {
        "surface_kind": "mas_repo_source_private_surface_retirement_completion",
        "status": "complete",
        "scope": "repo_source_physical_retirement_only",
        "claim": (
            "MAS private control-plane modules, aliases, wrappers and compatibility shims "
            "have been physically retired or guarded at the repo-source boundary; remaining "
            "live-tail work orders are live-runtime readiness evidence gates, not repo-source "
            "deletion blockers."
        ),
        "completion_claim_allowed": True,
        "repo_source_retirement_blocked": False,
        "blocked_by_missing_live_evidence": False,
        "live_runtime_readiness_claim_allowed": False,
        "does_not_satisfy_live_runtime_work_orders": True,
        "evidence_refs": [
            "docs/history/runtime/mas-private-surface-retirement.md",
            (
                "med_autoscience.cli doctor live-runtime-evidence-rollup --format json#/"
                "repo_source_retirement_completion"
            ),
        ],
    }
    assert rollup_contract["live_runtime_readiness_claim_allowed"] is False
    assert rollup_contract["evidence_record_templates_readback"] == {
        "surface_kind": "mas_live_runtime_evidence_rollup_evidence_record_templates",
        "purpose": (
            "Expose fillable evidence-record templates for every remaining live-tail or "
            "live-runtime-gap blocker so the next owner can provide canonical evidence "
            "without relying on docs, tests, queue-empty, dry-run or repo-source "
            "retirement claims."
        ),
        "template_status": "operator_input_required",
        "templates_are_evidence_records": False,
        "templates_can_satisfy_work_orders": False,
        "templates_can_claim_live_runtime_ready": False,
        "required_template_fields": [
            "work_order_kind",
            "next_owner",
            "record_template",
            "acceptable_evidence_source_prefixes",
            "forbidden_evidence_source_prefixes",
            "concrete_evidence_ref_fields",
            "transition_identity_ref_fields",
            "repo_source_retirement_blocked",
            "live_runtime_readiness_claim_allowed",
        ],
    }
    assert rollup_contract["owner_handoff_readback"] == {
        "surface_kind": "mas_live_runtime_evidence_rollup_owner_handoff_queue",
        "purpose": (
            "Group remaining live-tail and live-runtime-gap blockers by next_owner with "
            "their typed blocker details and fillable evidence templates, so MAS/OPL "
            "owners can take the next evidence-producing action without a MAS private "
            "control plane."
        ),
        "handoff_status": "owner_evidence_required",
        "handoff_is_action_authorization": False,
        "handoff_can_satisfy_work_orders": False,
        "handoff_can_claim_live_runtime_ready": False,
        "required_handoff_fields": [
            "next_owner",
            "work_order_count",
            "work_order_keys",
            "typed_blockers",
            "evidence_record_templates",
            "repo_source_retirement_blocked",
            "live_runtime_readiness_claim_allowed",
        ],
    }
    assert rollup_contract["evidence_bundle_intake"] == {
        "surface_kind": "mas_live_runtime_evidence_rollup_bundle_intake",
        "purpose": (
            "Accept one canonical owner-provided evidence bundle containing live-tail "
            "and live-runtime-gap evidence records, while preserving the same fail-closed "
            "record validators used by split evidence files."
        ),
        "bundle_status": "operator_input_required",
        "bundle_is_evidence_record": False,
        "bundle_can_satisfy_work_orders_without_records": False,
        "bundle_can_claim_live_runtime_ready": False,
        "required_bundle_fields": [
            "live_runtime_gap_evidence_records",
            "live_tail_evidence_records",
        ],
        "split_file_compatibility": {
            "tail_evidence_file_field": "live_tail_evidence_records",
            "gap_evidence_file_field": "live_runtime_gap_evidence_records",
            "bundle_and_split_files_can_be_combined": False,
        },
    }
    assert rollup_contract["completion_claim_boundary"] == {
        "repo_source_retirement_blocked_by_missing_live_evidence": False,
        "docs_tests_inventory_or_queue_empty_can_satisfy_rollup": False,
        "partial_rollup_can_claim_live_runtime_ready": False,
        "live_runtime_readiness_claim_requires_all_tail_and_gap_work_orders_satisfied": True,
        "accepted_record_families": [
            (
                "contracts/runtime/mas-runtime-live-tail-work-orders.json#/"
                "completion_claim_boundary/evidence_record_schema"
            ),
            (
                "contracts/runtime/mas-live-runtime-gap-work-orders.json#/"
                "completion_claim_boundary/evidence_record_schema"
            ),
        ],
        "accepted_rollup_result_status": "all_work_orders_satisfied",
        "missing_or_forbidden_result_status": "typed_blocker_required",
        "unknown_or_duplicate_evidence_records_can_satisfy_rollup": False,
        "unknown_or_duplicate_evidence_records_result_status": "typed_blocker_required",
        "missing_or_malformed_evidence_records_can_satisfy_rollup": False,
        "missing_or_malformed_evidence_records_result_status": "typed_blocker_required",
        "forbidden_or_unaccepted_evidence_source_can_satisfy_rollup": False,
        "forbidden_or_unaccepted_evidence_source_result_status": "typed_blocker_required",
        "authority_family_without_outcome_ref_can_satisfy_rollup": False,
        "missing_authority_outcome_ref_result_status": "typed_blocker_required",
        "tail_authority_family_without_outcome_ref_can_satisfy_rollup": False,
        "missing_tail_authority_outcome_ref_result_status": "typed_blocker_required",
        "accepted_tail_family_without_concrete_ref_can_satisfy_rollup": False,
        "missing_tail_concrete_evidence_ref_result_status": "typed_blocker_required",
        "accepted_gap_family_without_concrete_ref_can_satisfy_rollup": False,
        "missing_gap_concrete_evidence_ref_result_status": "typed_blocker_required",
    }
    assert rollup_contract["live_tail_surface_ids"] == sorted(
        order["surface_id"] for order in tail_contract["work_orders"]
    )
    assert rollup_contract["live_runtime_gap_ids"] == sorted(
        order["gap_id"] for order in gap_contract["work_orders"]
    )


def test_live_runtime_evidence_rollup_fails_closed_when_any_tail_or_gap_is_missing() -> None:
    rollup = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_evidence_rollup"
    )
    tail_contract = _live_tail_contract()
    gap_contract = _live_gap_contract()

    empty = rollup.live_runtime_evidence_rollup_summary(
        live_tail_contract=tail_contract,
        live_runtime_gap_contract=gap_contract,
    )
    assert empty["surface_kind"] == "mas_live_runtime_evidence_rollup_summary"
    assert empty["total_work_order_count"] == 12
    assert empty["satisfied_count"] == 0
    assert empty["typed_blocker_count"] == 12
    assert empty["repo_source_retirement_completion"] == {
        "surface_kind": "mas_repo_source_private_surface_retirement_completion",
        "status": "complete",
        "scope": "repo_source_physical_retirement_only",
        "completion_claim_allowed": True,
        "repo_source_retirement_blocked": False,
        "blocked_by_missing_live_evidence": False,
        "live_runtime_readiness_claim_allowed": False,
        "does_not_satisfy_live_runtime_work_orders": True,
    }
    assert empty["repo_source_retirement_blocked"] is False
    assert empty["live_runtime_readiness_claim_allowed"] is False
    assert empty["rollup_result_status"] == "typed_blocker_required"

    one_tail = tail_contract["work_orders"][0]
    one_gap = gap_contract["work_orders"][0]
    partial = rollup.live_runtime_evidence_rollup_summary(
        live_tail_contract=tail_contract,
        live_runtime_gap_contract=gap_contract,
        live_tail_evidence_records=[
            {
                "surface_id": one_tail["surface_id"],
                "evidence_source": f"owner_readback:{one_tail['surface_id']}",
                "evidence_ref_families": [one_tail["acceptable_evidence_ref_families"][0]],
                "evidence_refs": [
                    (
                        "live-tail-evidence:"
                        f"{one_tail['surface_id']}:{one_tail['acceptable_evidence_ref_families'][0]}"
                    )
                ],
                **_transition_identity_refs(),
            }
        ],
        live_runtime_gap_evidence_records=[
            {
                "gap_id": one_gap["gap_id"],
                "evidence_source": f"owner_readback:{one_gap['gap_id']}",
                "evidence_ref_families": [one_gap["acceptable_evidence_ref_families"][0]],
                "evidence_refs": [
                    (
                        "live-gap-evidence:"
                        f"{one_gap['gap_id']}:{one_gap['acceptable_evidence_ref_families'][0]}"
                    )
                ],
                **_transition_identity_refs(),
            }
        ],
    )
    assert partial["satisfied_count"] == 2
    assert partial["typed_blocker_count"] == 10
    assert partial["live_runtime_readiness_claim_allowed"] is False
    assert partial["rollup_result_status"] == "typed_blocker_required"
    assert one_tail["surface_id"] in partial["satisfied_surface_ids"]
    assert one_gap["gap_id"] in partial["satisfied_gap_ids"]


def test_live_runtime_evidence_rollup_readback_exposes_typed_blocker_gate() -> None:
    rollup = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_evidence_rollup"
    )

    readback = rollup.live_runtime_evidence_rollup_readback(repo_root=REPO_ROOT)

    assert readback["surface_kind"] == "mas_live_runtime_evidence_rollup_readback"
    assert readback["repo_source_retirement_blocked"] is False
    assert readback["contract_validation"] == {
        "status": "passed",
        "violation_count": 0,
        "violations": [],
    }
    assert readback["repo_source_retirement_completion"]["status"] == "complete"
    assert readback["repo_source_retirement_completion"]["completion_claim_allowed"] is True
    assert (
        readback["repo_source_retirement_completion"]["blocked_by_missing_live_evidence"]
        is False
    )
    assert (
        readback["repo_source_retirement_completion"][
            "does_not_satisfy_live_runtime_work_orders"
        ]
        is True
    )
    assert readback["repo_source_retirement_completion"][
        "live_runtime_readiness_claim_allowed"
    ] is False
    assert readback["summary"]["total_work_order_count"] == 12
    assert readback["summary"]["typed_blocker_count"] == 12
    assert readback["summary"]["rollup_result_status"] == "typed_blocker_required"
    assert len(readback["summary"]["typed_blocker_details"]) == 12
    assert len(readback["summary"]["evidence_record_templates"]) == 12
    assert readback["summary"]["evidence_bundle_template"]["surface_kind"] == (
        "mas_live_runtime_evidence_rollup_bundle_template"
    )
    assert (
        len(readback["summary"]["evidence_bundle_template"]["live_tail_evidence_records"])
        == 7
    )
    assert (
        len(
            readback["summary"]["evidence_bundle_template"][
                "live_runtime_gap_evidence_records"
            ]
        )
        == 5
    )
    assert (
        readback["summary"]["evidence_bundle_template"][
            "bundle_can_satisfy_work_orders_without_filled_records"
        ]
        is False
    )
    assert (
        readback["summary"]["evidence_bundle_template"][
            "bundle_can_claim_live_runtime_ready"
        ]
        is False
    )
    assert sum(
        handoff["work_order_count"]
        for handoff in readback["summary"]["owner_handoffs"]
    ) == 12
    observability_handoff = next(
        handoff
        for handoff in readback["summary"]["owner_handoffs"]
        if handoff["next_owner"] == "one-person-lab Observability / RouteReconciler owner"
    )
    assert observability_handoff["handoff_status"] == "owner_evidence_required"
    assert observability_handoff["handoff_is_action_authorization"] is False
    assert observability_handoff["handoff_can_satisfy_work_orders"] is False
    assert observability_handoff["handoff_can_claim_live_runtime_ready"] is False
    assert observability_handoff["live_runtime_readiness_claim_allowed"] is False
    assert observability_handoff["work_order_keys"] == ["live_tail:runtime_health_kernel"]
    assert observability_handoff["typed_blockers"][0]["surface_id"] == "runtime_health_kernel"
    assert observability_handoff["evidence_record_templates"][0]["surface_id"] == (
        "runtime_health_kernel"
    )
    runtime_health_detail = next(
        item
        for item in readback["summary"]["typed_blocker_details"]
        if item.get("surface_id") == "runtime_health_kernel"
    )
    assert runtime_health_detail["work_order_kind"] == "live_tail"
    assert runtime_health_detail["next_owner"] == (
        "one-person-lab Observability / RouteReconciler owner"
    )
    assert runtime_health_detail["typed_blocker"] == (
        "runtime_health_kernel_live_runtime_readiness_evidence_required"
    )
    assert runtime_health_detail["acceptable_evidence_ref_families"]
    runtime_health_template = next(
        item
        for item in readback["summary"]["evidence_record_templates"]
        if item.get("surface_id") == "runtime_health_kernel"
    )
    assert runtime_health_template["work_order_kind"] == "live_tail"
    assert runtime_health_template["template_status"] == "operator_input_required"
    assert runtime_health_template["templates_can_satisfy_work_orders"] is False
    assert runtime_health_template["record_template"]["surface_id"] == "runtime_health_kernel"
    assert "evidence_refs" in runtime_health_template["record_template"]
    assert "focused_tests" in runtime_health_template["forbidden_evidence_source_prefixes"]
    domain_diagnostic_apply_detail = next(
        item
        for item in readback["summary"]["typed_blocker_details"]
        if item.get("gap_id") == "domain_diagnostic_apply_exactly_one_live_outcome_when_explicitly_delegated"
    )
    assert domain_diagnostic_apply_detail["work_order_kind"] == "live_runtime_gap"
    assert domain_diagnostic_apply_detail["next_owner"] == (
        "MAS domain diagnostic apply owner with OPL runtime authorization"
    )
    assert "MAS_owner_receipt_or_stable_typed_blocker_or_human_gate_or_route_back_ref" in (
        domain_diagnostic_apply_detail["acceptable_evidence_ref_families"]
    )
    domain_diagnostic_apply_template = next(
        item
        for item in readback["summary"]["evidence_record_templates"]
        if item.get("gap_id") == "domain_diagnostic_apply_exactly_one_live_outcome_when_explicitly_delegated"
    )
    assert domain_diagnostic_apply_template["work_order_kind"] == "live_runtime_gap"
    assert domain_diagnostic_apply_template["record_template"]["gap_id"] == (
        "domain_diagnostic_apply_exactly_one_live_outcome_when_explicitly_delegated"
    )
    assert domain_diagnostic_apply_template["templates_are_evidence_records"] is False
    assert {
        "study_id",
        "work_unit_id",
        "work_unit_fingerprint",
        "route_identity_key",
        "attempt_idempotency_key",
    } <= set(domain_diagnostic_apply_template["record_template"])
    assert readback["completion_claim_allowed"] is False
    assert {
        "typed_blocker_required_live_runtime_evidence_rollup",
        "repo_source_retirement_complete_as_live_runtime_ready",
        "docs_tests_inventory_or_queue_empty_as_live_runtime_ready",
    } <= set(readback["false_completion_boundary"])


def test_live_runtime_evidence_rollup_requires_all_tail_and_gap_records() -> None:
    rollup = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_evidence_rollup"
    )
    tail_contract = _live_tail_contract()
    gap_contract = _live_gap_contract()
    tail_records = [_satisfying_tail_record(order) for order in tail_contract["work_orders"]]
    gap_records = [_satisfying_gap_record(order) for order in gap_contract["work_orders"]]

    complete = rollup.live_runtime_evidence_rollup_summary(
        live_tail_contract=tail_contract,
        live_runtime_gap_contract=gap_contract,
        live_tail_evidence_records=tail_records,
        live_runtime_gap_evidence_records=gap_records,
    )
    assert complete["total_work_order_count"] == 12
    assert complete["satisfied_count"] == 12
    assert complete["typed_blocker_count"] == 0
    assert complete["intake_violation_count"] == 0
    assert complete["live_runtime_readiness_claim_allowed"] is True
    assert complete["rollup_result_status"] == "all_work_orders_satisfied"


def test_live_runtime_evidence_templates_are_not_evidence_records() -> None:
    rollup = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_evidence_rollup"
    )
    tail_contract = _live_tail_contract()
    gap_contract = _live_gap_contract()
    summary = rollup.live_runtime_evidence_rollup_summary(
        live_tail_contract=tail_contract,
        live_runtime_gap_contract=gap_contract,
    )
    templates = summary["evidence_record_templates"]

    template_as_evidence = rollup.live_runtime_evidence_rollup_summary(
        live_tail_contract=tail_contract,
        live_runtime_gap_contract=gap_contract,
        live_tail_evidence_records=[
            item for item in templates if item["work_order_kind"] == "live_tail"
        ],
        live_runtime_gap_evidence_records=[
            item for item in templates if item["work_order_kind"] == "live_runtime_gap"
        ],
    )
    record_templates_as_evidence = rollup.live_runtime_evidence_rollup_summary(
        live_tail_contract=tail_contract,
        live_runtime_gap_contract=gap_contract,
        live_tail_evidence_records=[
            item["record_template"]
            for item in templates
            if item["work_order_kind"] == "live_tail"
        ],
        live_runtime_gap_evidence_records=[
            item["record_template"]
            for item in templates
            if item["work_order_kind"] == "live_runtime_gap"
        ],
    )
    template_bundle = summary["evidence_bundle_template"]
    tail_bundle_records, gap_bundle_records = rollup.evidence_records_from_bundle(
        template_bundle
    )
    bundle_templates_as_evidence = rollup.live_runtime_evidence_rollup_summary(
        live_tail_contract=tail_contract,
        live_runtime_gap_contract=gap_contract,
        live_tail_evidence_records=tail_bundle_records,
        live_runtime_gap_evidence_records=gap_bundle_records,
    )

    assert summary["typed_blocker_count"] == 12
    assert summary["live_runtime_readiness_claim_allowed"] is False
    assert all(template["record_template"]["evidence_source"] is None for template in templates)
    assert all(template["record_template"]["evidence_ref_families"] == [] for template in templates)
    assert all(template["record_template"]["evidence_refs"] == [] for template in templates)
    assert template_as_evidence["satisfied_count"] == 0
    assert template_as_evidence["typed_blocker_count"] == 12
    assert template_as_evidence["rollup_result_status"] == "typed_blocker_required"
    assert template_as_evidence["live_runtime_readiness_claim_allowed"] is False
    assert record_templates_as_evidence["satisfied_count"] == 0
    assert record_templates_as_evidence["typed_blocker_count"] == 12
    assert record_templates_as_evidence["rollup_result_status"] == "typed_blocker_required"
    assert record_templates_as_evidence["live_runtime_readiness_claim_allowed"] is False
    assert template_bundle["bundle_is_evidence_record"] is False
    assert template_bundle["bundle_can_satisfy_work_orders_without_filled_records"] is False
    assert bundle_templates_as_evidence["satisfied_count"] == 0
    assert bundle_templates_as_evidence["typed_blocker_count"] == 12
    assert bundle_templates_as_evidence["rollup_result_status"] == "typed_blocker_required"
    assert bundle_templates_as_evidence["live_runtime_readiness_claim_allowed"] is False


def test_live_runtime_evidence_rollup_fails_closed_on_unknown_or_duplicate_records() -> None:
    rollup = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_evidence_rollup"
    )
    tail_contract = _live_tail_contract()
    gap_contract = _live_gap_contract()
    tail_records = [_satisfying_tail_record(order) for order in tail_contract["work_orders"]]
    gap_records = [_satisfying_gap_record(order) for order in gap_contract["work_orders"]]

    polluted = rollup.live_runtime_evidence_rollup_summary(
        live_tail_contract=tail_contract,
        live_runtime_gap_contract=gap_contract,
        live_tail_evidence_records=[
            *tail_records,
            {**tail_records[0], "evidence_source": "owner_readback:duplicate"},
            {
                "surface_id": "unknown_private_surface",
                "evidence_source": "owner_readback:unknown",
                "evidence_ref_families": [
                    "runtime_health_kernel_opl_observability_live_readback_ref"
                ],
            },
            {
                "evidence_source": "owner_readback:missing-id",
                "evidence_ref_families": [
                    "runtime_health_kernel_opl_observability_live_readback_ref"
                ],
            },
            "malformed-record",
        ],
        live_runtime_gap_evidence_records=[
            *gap_records,
            {**gap_records[0], "evidence_source": "owner_readback:duplicate"},
            {
                "gap_id": "unknown_live_runtime_gap",
                "evidence_source": "owner_readback:unknown",
                "evidence_ref_families": [
                    "OPL_domain_progress_transition_runtime_live_readback_same_identity_ref"
                ],
            },
            {
                "evidence_source": "owner_readback:missing-id",
                "evidence_ref_families": [
                    "OPL_domain_progress_transition_runtime_live_readback_same_identity_ref"
                ],
            },
            "malformed-record",
        ],
    )

    assert polluted["satisfied_count"] == 12
    assert polluted["typed_blocker_count"] == 8
    assert polluted["intake_violation_count"] == 8
    assert polluted["live_runtime_readiness_claim_allowed"] is False
    assert polluted["rollup_result_status"] == "typed_blocker_required"
    assert polluted["live_tail"]["intake_violation_count"] == 4
    assert polluted["live_runtime_gaps"]["intake_violation_count"] == 4


def test_live_runtime_evidence_rollup_rejects_authority_family_without_outcome_ref() -> None:
    rollup = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_evidence_rollup"
    )
    tail_contract = _live_tail_contract()
    gap_contract = _live_gap_contract()
    tail_records = [_satisfying_tail_record(order) for order in tail_contract["work_orders"]]
    authority_family = (
        "MAS_owner_receipt_or_stable_typed_blocker_or_human_gate_or_route_back_ref"
    )
    authority_order = next(
        order
        for order in gap_contract["work_orders"]
        if authority_family in order["acceptable_evidence_ref_families"]
    )
    gap_records = [
        _satisfying_gap_record(order)
        for order in gap_contract["work_orders"]
        if order["gap_id"] != authority_order["gap_id"]
    ] + [
        {
            "gap_id": authority_order["gap_id"],
            "evidence_source": f"owner_readback:{authority_order['gap_id']}",
            "evidence_ref_families": [authority_family],
        }
    ]

    summary = rollup.live_runtime_evidence_rollup_summary(
        live_tail_contract=tail_contract,
        live_runtime_gap_contract=gap_contract,
        live_tail_evidence_records=tail_records,
        live_runtime_gap_evidence_records=gap_records,
    )
    result = next(
        item
        for item in summary["live_runtime_gaps"]["results"]
        if item["gap_id"] == authority_order["gap_id"]
    )

    assert result["status"] == "typed_blocker_required"
    assert result["missing_authority_outcome_ref_families"] == [authority_family]
    assert result["authority_outcome_ref_fields_present"] == []
    assert result["missing_concrete_evidence_ref_families"] == [authority_family]
    assert result["concrete_evidence_ref_fields_present"] == []
    assert summary["rollup_result_status"] == "typed_blocker_required"
    assert summary["live_runtime_readiness_claim_allowed"] is False


def test_live_runtime_evidence_rollup_rejects_tail_family_without_concrete_ref() -> None:
    rollup = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_evidence_rollup"
    )
    tail_contract = _live_tail_contract()
    gap_contract = _live_gap_contract()
    tail_records = [_satisfying_tail_record(order) for order in tail_contract["work_orders"]]
    first_tail = tail_records[0]
    first_tail.pop("evidence_refs")
    gap_records = [_satisfying_gap_record(order) for order in gap_contract["work_orders"]]

    summary = rollup.live_runtime_evidence_rollup_summary(
        live_tail_contract=tail_contract,
        live_runtime_gap_contract=gap_contract,
        live_tail_evidence_records=tail_records,
        live_runtime_gap_evidence_records=gap_records,
    )
    result = next(
        item
        for item in summary["live_tail"]["results"]
        if item["surface_id"] == first_tail["surface_id"]
    )

    assert result["status"] == "typed_blocker_required"
    assert result["missing_concrete_evidence_ref_families"] == first_tail[
        "evidence_ref_families"
    ]
    assert result["concrete_evidence_ref_fields_present"] == []
    assert summary["rollup_result_status"] == "typed_blocker_required"
    assert summary["live_runtime_readiness_claim_allowed"] is False


def test_live_runtime_evidence_rollup_rejects_gap_family_without_concrete_ref() -> None:
    rollup = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_evidence_rollup"
    )
    tail_contract = _live_tail_contract()
    gap_contract = _live_gap_contract()
    tail_records = [_satisfying_tail_record(order) for order in tail_contract["work_orders"]]
    gap_records = [_satisfying_gap_record(order) for order in gap_contract["work_orders"]]
    first_gap = gap_records[0]
    first_gap.pop("evidence_refs")

    summary = rollup.live_runtime_evidence_rollup_summary(
        live_tail_contract=tail_contract,
        live_runtime_gap_contract=gap_contract,
        live_tail_evidence_records=tail_records,
        live_runtime_gap_evidence_records=gap_records,
    )
    result = next(
        item
        for item in summary["live_runtime_gaps"]["results"]
        if item["gap_id"] == first_gap["gap_id"]
    )

    assert result["status"] == "typed_blocker_required"
    assert result["missing_concrete_evidence_ref_families"] == first_gap[
        "evidence_ref_families"
    ]
    assert result["concrete_evidence_ref_fields_present"] == []
    assert summary["rollup_result_status"] == "typed_blocker_required"
    assert summary["live_runtime_readiness_claim_allowed"] is False


def test_live_runtime_evidence_rollup_rejects_repo_test_sources_with_accepted_refs() -> None:
    rollup = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_evidence_rollup"
    )
    tail_contract = _live_tail_contract()
    gap_contract = _live_gap_contract()
    tail_records = [_satisfying_tail_record(order) for order in tail_contract["work_orders"]]
    gap_records = [_satisfying_gap_record(order) for order in gap_contract["work_orders"]]
    tail_records[0]["evidence_source"] = "focused_tests"
    gap_records[0]["evidence_source"] = "scripts_verify"

    summary = rollup.live_runtime_evidence_rollup_summary(
        live_tail_contract=tail_contract,
        live_runtime_gap_contract=gap_contract,
        live_tail_evidence_records=tail_records,
        live_runtime_gap_evidence_records=gap_records,
    )
    tail_result = next(
        item
        for item in summary["live_tail"]["results"]
        if item["surface_id"] == tail_records[0]["surface_id"]
    )
    gap_result = next(
        item
        for item in summary["live_runtime_gaps"]["results"]
        if item["gap_id"] == gap_records[0]["gap_id"]
    )

    assert tail_result["status"] == "typed_blocker_required"
    assert tail_result["forbidden_evidence_source_prefixes_present"] == [
        "focused_tests"
    ]
    assert gap_result["status"] == "typed_blocker_required"
    assert gap_result["forbidden_evidence_source_prefixes_present"] == [
        "scripts_verify"
    ]
    assert summary["satisfied_count"] == 10
    assert summary["typed_blocker_count"] == 2
    assert summary["rollup_result_status"] == "typed_blocker_required"
    assert summary["live_runtime_readiness_claim_allowed"] is False


def test_live_runtime_evidence_rollup_cli_outputs_readback_json(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    exit_code = cli.main(
        [
            "doctor",
            "live-runtime-evidence-rollup",
            "--repo-root",
            str(REPO_ROOT),
            "--format",
            "json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["surface_kind"] == "mas_live_runtime_evidence_rollup_readback"
    assert output["contract_refs"] == {
        "live_tail_work_orders": "contracts/runtime/mas-runtime-live-tail-work-orders.json",
        "live_runtime_gap_work_orders": "contracts/runtime/mas-live-runtime-gap-work-orders.json",
        "live_runtime_evidence_rollup": "contracts/runtime/mas-live-runtime-evidence-rollup.json",
    }
    assert output["contract_validation"]["status"] == "passed"
    assert output["repo_source_retirement_completion"]["status"] == "complete"
    assert output["repo_source_retirement_completion"]["completion_claim_allowed"] is True
    assert (
        output["repo_source_retirement_completion"]["live_runtime_readiness_claim_allowed"]
        is False
    )
    assert output["summary"]["rollup_result_status"] == "typed_blocker_required"
    assert output["completion_claim_allowed"] is False


def test_live_runtime_evidence_rollup_cli_consumes_evidence_files(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    tail_contract = _live_tail_contract()
    gap_contract = _live_gap_contract()
    tail_records = [_satisfying_tail_record(order) for order in tail_contract["work_orders"]]
    gap_records = [_satisfying_gap_record(order) for order in gap_contract["work_orders"]]
    tail_file = tmp_path / "tail-evidence.json"
    gap_file = tmp_path / "gap-evidence.json"
    tail_file.write_text(json.dumps(tail_records), encoding="utf-8")
    gap_file.write_text(json.dumps(gap_records), encoding="utf-8")

    exit_code = cli.main(
        [
            "doctor",
            "live-runtime-evidence-rollup",
            "--repo-root",
            str(REPO_ROOT),
            "--tail-evidence-file",
            str(tail_file),
            "--gap-evidence-file",
            str(gap_file),
            "--format",
            "json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["summary"]["rollup_result_status"] == "all_work_orders_satisfied"
    assert output["summary"]["typed_blocker_count"] == 0
    assert output["summary"]["intake_violation_count"] == 0
    assert output["completion_claim_allowed"] is True


def test_live_runtime_evidence_rollup_cli_consumes_evidence_bundle_file(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    tail_contract = _live_tail_contract()
    gap_contract = _live_gap_contract()
    tail_records = [_satisfying_tail_record(order) for order in tail_contract["work_orders"]]
    gap_records = [_satisfying_gap_record(order) for order in gap_contract["work_orders"]]
    bundle_file = tmp_path / "live-evidence-bundle.json"
    bundle_file.write_text(
        json.dumps(
            {
                "surface_kind": "mas_live_runtime_evidence_rollup_evidence_bundle",
                "live_tail_evidence_records": tail_records,
                "live_runtime_gap_evidence_records": gap_records,
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "doctor",
            "live-runtime-evidence-rollup",
            "--repo-root",
            str(REPO_ROOT),
            "--evidence-bundle-file",
            str(bundle_file),
            "--format",
            "json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["summary"]["rollup_result_status"] == "all_work_orders_satisfied"
    assert output["summary"]["satisfied_count"] == 12
    assert output["summary"]["typed_blocker_count"] == 0
    assert output["summary"]["intake_violation_count"] == 0
    assert output["completion_claim_allowed"] is True


def test_live_runtime_evidence_rollup_cli_rejects_bundle_combined_with_split_file(
    tmp_path: Path,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    bundle_file = tmp_path / "live-evidence-bundle.json"
    tail_file = tmp_path / "tail-evidence.json"
    bundle_file.write_text(
        json.dumps(
            {
                "live_tail_evidence_records": [],
                "live_runtime_gap_evidence_records": [],
            }
        ),
        encoding="utf-8",
    )
    tail_file.write_text("[]", encoding="utf-8")

    try:
        cli.main(
            [
                "doctor",
                "live-runtime-evidence-rollup",
                "--repo-root",
                str(REPO_ROOT),
                "--evidence-bundle-file",
                str(bundle_file),
                "--tail-evidence-file",
                str(tail_file),
                "--format",
                "json",
            ]
        )
    except TypeError as exc:
        assert "--evidence-bundle-file cannot be combined" in str(exc)
    else:
        raise AssertionError("combined bundle and split evidence files should fail closed")


def test_live_runtime_evidence_rollup_bundle_rejects_malformed_record_lists() -> None:
    rollup = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_evidence_rollup"
    )

    try:
        rollup.evidence_records_from_bundle(
            {
                "live_tail_evidence_records": {},
                "live_runtime_gap_evidence_records": [],
            }
        )
    except TypeError as exc:
        assert "live_tail_evidence_records must be a JSON list" in str(exc)
    else:
        raise AssertionError("malformed tail evidence bundle should fail closed")


def test_live_runtime_evidence_rollup_cli_rejects_polluted_evidence_files(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    tail_contract = _live_tail_contract()
    gap_contract = _live_gap_contract()
    tail_records = [_satisfying_tail_record(order) for order in tail_contract["work_orders"]]
    gap_records = [_satisfying_gap_record(order) for order in gap_contract["work_orders"]]
    tail_file = tmp_path / "polluted-tail-evidence.json"
    gap_file = tmp_path / "polluted-gap-evidence.json"
    tail_file.write_text(
        json.dumps(
            [
                *tail_records,
                {**tail_records[0], "evidence_source": "owner_readback:duplicate"},
                {
                    "evidence_source": "owner_readback:missing-id",
                    "evidence_ref_families": [
                        "runtime_health_kernel_opl_observability_live_readback_ref"
                    ],
                },
                "malformed-record",
            ]
        ),
        encoding="utf-8",
    )
    gap_file.write_text(
        json.dumps(
            [
                *gap_records,
                {**gap_records[0], "evidence_source": "owner_readback:duplicate"},
                {
                    "evidence_source": "owner_readback:missing-id",
                    "evidence_ref_families": [
                        "OPL_domain_progress_transition_runtime_live_readback_same_identity_ref"
                    ],
                },
                "malformed-record",
            ]
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "doctor",
            "live-runtime-evidence-rollup",
            "--repo-root",
            str(REPO_ROOT),
            "--tail-evidence-file",
            str(tail_file),
            "--gap-evidence-file",
            str(gap_file),
            "--format",
            "json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["summary"]["satisfied_count"] == 12
    assert output["summary"]["typed_blocker_count"] == 6
    assert output["summary"]["intake_violation_count"] == 6
    assert output["summary"]["rollup_result_status"] == "typed_blocker_required"
    assert output["completion_claim_allowed"] is False


def _satisfying_gap_record(order: dict) -> dict:
    ref_family = order["acceptable_evidence_ref_families"][0]
    record = {
        "gap_id": order["gap_id"],
        "evidence_source": f"owner_readback:{order['gap_id']}",
        "evidence_ref_families": [ref_family],
        "evidence_refs": [f"live-gap-evidence:{order['gap_id']}:{ref_family}"],
        **_transition_identity_refs(),
    }
    if ref_family == "MAS_owner_receipt_or_stable_typed_blocker_or_human_gate_or_route_back_ref":
        record["typed_blocker_ref"] = f"typed-blocker:{order['gap_id']}"
    return record


def _satisfying_tail_record(order: dict) -> dict:
    ref_family = order["acceptable_evidence_ref_families"][0]
    return {
        "surface_id": order["surface_id"],
        "evidence_source": f"owner_readback:{order['surface_id']}",
        "evidence_ref_families": [ref_family],
        "evidence_refs": [f"live-tail-evidence:{order['surface_id']}:{ref_family}"],
        **_transition_identity_refs(),
    }


def _transition_identity_refs() -> dict:
    return {
        "study_id": "study:dm-cvd-mortality-risk",
        "work_unit_id": "work-unit:canonical-live-evidence-template",
        "work_unit_fingerprint": "work-unit-fingerprint:canonical-live-evidence-template",
        "route_identity_key": "route-identity:canonical-live-evidence-template",
        "attempt_idempotency_key": "attempt-idempotency:canonical-live-evidence-template",
    }
