from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
WORK_ORDER_PATH = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-live-tail-work-orders.json"


def _audit() -> dict:
    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    return retirement.audit_runtime_surface_retirement_inventory(inventory)


def _contract() -> dict:
    return json.loads(WORK_ORDER_PATH.read_text(encoding="utf-8"))


def test_live_tail_work_order_contract_matches_runtime_surface_audit() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_tail_work_orders"
    )
    audit = _audit()
    contract = _contract()

    assert work_orders.validate_live_tail_work_order_contract(contract, audit) == []
    assert contract["surface_kind"] == "mas_runtime_live_tail_work_orders"
    assert contract["repo_source_retirement_blocked"] is False
    assert contract["live_runtime_readiness_claim_allowed"] is False

    expected = {
        order["surface_id"]: order
        for order in work_orders.live_tail_work_orders_from_audit(audit)
    }
    observed = {order["surface_id"]: order for order in contract["work_orders"]}
    assert set(observed) == set(expected)
    assert len(observed) == 7

    for surface_id, order in observed.items():
        assert order["status"] == "evidence_required"
        assert order["repo_source_retirement_blocked"] is False
        assert order["live_runtime_readiness_claim_allowed"] is False
        assert order["typed_blocker_when_missing"] == (
            f"{surface_id}_live_runtime_readiness_evidence_required"
        )
        assert order["acceptable_evidence_ref_families"]
        assert order["forbidden_evidence_substitutes"]


def test_live_tail_work_order_contract_rejects_false_completion_substitutes() -> None:
    contract = _contract()

    boundary = contract["completion_claim_boundary"]
    assert boundary["repo_source_retirement_can_complete_without_these_work_orders"] is True
    assert boundary["these_work_orders_can_claim_live_runtime_ready_without_evidence"] is False
    assert boundary["docs_tests_inventory_or_queue_empty_can_satisfy_work_order"] is False
    assert {
        "same_identity_opl_live_readback",
        "owner_receipt_or_stable_typed_blocker_or_human_gate_or_route_back",
        "no_active_production_caller_scan_with_owner_retirement_decision",
    } <= set(boundary["accepted_outcomes"])

    forbidden = {
        substitute
        for order in contract["work_orders"]
        for substitute in order["forbidden_evidence_substitutes"]
    }
    assert {
        "repo_tests_green_as_physical_delete",
        "repo_no_authority_guard_as_runtime_health_tail_readback",
        "repo_no_authority_guard_as_obligation_actuator_tail_readback",
        "repo_no_authority_guard_as_workbench_tail_readback",
    } <= forbidden


def test_live_tail_evidence_record_intake_requires_accepted_ref_family() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_tail_work_orders"
    )
    contract = _contract()
    runtime_health = {
        order["surface_id"]: order for order in contract["work_orders"]
    }["runtime_health_kernel"]

    accepted = work_orders.evaluate_live_tail_evidence_record(
        runtime_health,
        {
            "surface_id": "runtime_health_kernel",
            "claim": "opl_observability_tail_satisfied",
            "evidence_source": "runtime_readback:observability:2026-06-20T00:00:00Z",
            "evidence_ref_families": [
                "runtime_health_kernel_opl_observability_live_readback_ref"
            ],
        },
    )
    assert accepted["status"] == "satisfied_by_accepted_ref"
    assert accepted["live_runtime_readiness_claim_allowed"] is True
    assert accepted["typed_blocker"] is None

    forbidden = work_orders.evaluate_live_tail_evidence_record(
        runtime_health,
        {
            "surface_id": "runtime_health_kernel",
            "claim": "repo_no_authority_guard_is_enough",
            "evidence_source": "focused_tests",
            "evidence_ref_families": [
                "runtime_health_kernel_opl_observability_live_readback_ref"
            ],
            "evidence_substitutes": [
                "repo_no_authority_guard_as_runtime_health_tail_readback"
            ],
        },
    )
    assert forbidden["status"] == "typed_blocker_required"
    assert forbidden["live_runtime_readiness_claim_allowed"] is False
    assert forbidden["typed_blocker"] == (
        "runtime_health_kernel_live_runtime_readiness_evidence_required"
    )
    assert forbidden["repo_source_retirement_blocked"] is False

    missing = work_orders.evaluate_live_tail_evidence_record(runtime_health, {})
    assert missing["status"] == "typed_blocker_required"
    assert missing["matched_evidence_ref_families"] == []
    assert missing["typed_blocker"] == (
        "runtime_health_kernel_live_runtime_readiness_evidence_required"
    )


def test_live_tail_evidence_intake_summary_does_not_claim_ready_until_all_tails_satisfied() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_tail_work_orders"
    )
    contract = _contract()
    runtime_health_record = {
        "surface_id": "runtime_health_kernel",
        "evidence_source": "runtime_readback:observability:2026-06-20T00:00:00Z",
        "evidence_ref_families": [
            "runtime_health_kernel_opl_observability_live_readback_ref"
        ],
    }

    partial = work_orders.live_tail_evidence_intake_summary(
        contract,
        [runtime_health_record],
    )
    assert partial["surface_kind"] == "mas_runtime_live_tail_evidence_intake_summary"
    assert partial["total_work_order_count"] == 7
    assert partial["satisfied_count"] == 1
    assert partial["typed_blocker_count"] == 6
    assert partial["repo_source_retirement_blocked"] is False
    assert partial["live_runtime_readiness_claim_allowed"] is False
    assert "runtime_health_kernel" in partial["satisfied_surface_ids"]

    all_records = [
        {
            "surface_id": order["surface_id"],
            "evidence_source": f"owner_readback:{order['surface_id']}",
            "evidence_ref_families": [order["acceptable_evidence_ref_families"][0]],
        }
        for order in contract["work_orders"]
    ]
    complete = work_orders.live_tail_evidence_intake_summary(contract, all_records)
    assert complete["satisfied_count"] == 7
    assert complete["typed_blocker_count"] == 0
    assert complete["live_runtime_readiness_claim_allowed"] is True
