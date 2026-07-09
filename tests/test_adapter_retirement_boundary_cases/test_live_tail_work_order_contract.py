from __future__ import annotations

import importlib
import json
from collections.abc import Callable
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = (
    REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
)
WORK_ORDER_PATH = (
    REPO_ROOT / "contracts" / "runtime" / "mas-runtime-live-tail-work-orders.json"
)


def _module():
    return importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement.live_tail_work_orders"
    )


def _audit() -> dict:
    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    return retirement.audit_runtime_surface_retirement_inventory(inventory)


def _contract() -> dict:
    return json.loads(WORK_ORDER_PATH.read_text(encoding="utf-8"))


def _order(surface_id: str) -> dict:
    return {order["surface_id"]: order for order in _contract()["work_orders"]}[surface_id]


def test_live_tail_work_order_contract_matches_runtime_surface_audit() -> None:
    work_orders = _module()
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
    assert all(order["status"] == "evidence_required" for order in observed.values())
    assert all(
        order["typed_blocker_when_missing"]
        == f"{surface_id}_live_runtime_readiness_evidence_required"
        for surface_id, order in observed.items()
    )

    schema = contract["completion_claim_boundary"]["evidence_record_schema"]
    assert {
        "ready",
        "runtime ready",
        "provider running",
        "paper progress",
        "publication-ready",
        "production-ready",
    } <= set(schema["forbidden_claim_terms"])
    assert {
        "focused_tests",
        "repo_tests",
        "queue_empty",
        "repo_source_retirement_complete",
        "scripts_verify",
    } <= set(schema["forbidden_evidence_source_prefixes"])
    assert schema["unknown_evidence_record_id_status"] == "typed_blocker_required"
    assert schema["duplicate_evidence_record_id_status"] == "typed_blocker_required"
    assert schema["missing_evidence_record_id_status"] == "typed_blocker_required"
    assert schema["malformed_evidence_record_status"] == "typed_blocker_required"
    assert schema["forbidden_or_unaccepted_source_can_satisfy_work_order"] is False
    assert schema["accepted_family_without_concrete_ref_can_satisfy_work_order"] is False
    assert schema["authority_family_without_outcome_ref_can_satisfy_work_order"] is False
    assert (
        schema["same_identity_family_without_transition_identity_can_satisfy_work_order"]
        is False
    )


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (
            lambda schema: schema["optional_fields"].remove("evidence_refs"),
            "undeclared_concrete_evidence_ref_fields",
        ),
        (
            lambda schema: schema.pop("authority_outcome_ref_required_for_families"),
            "authority_outcome_ref_families_mismatch",
        ),
        (
            lambda schema: schema.pop("transition_identity_ref_required_for_families"),
            "transition_identity_ref_families_mismatch",
        ),
    ],
)
def test_live_tail_contract_rejects_broken_evidence_schema(
    mutate: Callable[[dict], object],
    reason: str,
) -> None:
    work_orders = _module()
    bad_contract = json.loads(json.dumps(_contract()))
    mutate(bad_contract["completion_claim_boundary"]["evidence_record_schema"])

    violations = work_orders.validate_live_tail_work_order_contract(
        bad_contract,
        _audit(),
    )

    assert {"surface_id": "<contract>", "reason": reason} in violations


def test_live_tail_evidence_record_guard_cases() -> None:
    work_orders = _module()
    runtime_health = _order("runtime_health_kernel")
    runtime_health_ref = "runtime_health_kernel_opl_observability_live_readback_ref"
    accepted_record = _tail_record(
        runtime_health,
        evidence_source="runtime_readback:observability:2026-06-20T00:00:00Z",
        ref_family=runtime_health_ref,
    )

    accepted = work_orders.evaluate_live_tail_evidence_record(
        runtime_health,
        accepted_record,
    )
    assert accepted["status"] == "satisfied_by_accepted_ref"
    assert accepted["live_runtime_readiness_claim_allowed"] is True

    guard_cases = [
        (
            {**accepted_record, "evidence_source": "focused_tests"},
            {
                "status": "typed_blocker_required",
                "forbidden_evidence_source_prefixes_present": ["focused_tests"],
            },
        ),
        (
            {key: value for key, value in accepted_record.items() if key != "evidence_refs"},
            {
                "status": "typed_blocker_required",
                "missing_concrete_evidence_ref_families": [runtime_health_ref],
            },
        ),
        (
            {**accepted_record, "claim": "runtime ready from accepted readback"},
            {
                "status": "typed_blocker_required",
                "forbidden_claim_terms_present": ["ready", "runtime ready"],
            },
        ),
        (
            {**accepted_record, "surface_id": "stage_outcome_authority"},
            {
                "status": "typed_blocker_required",
                "evidence_record_id_mismatch": True,
            },
        ),
    ]
    for record, expected in guard_cases:
        result = work_orders.evaluate_live_tail_evidence_record(runtime_health, record)
        for key, value in expected.items():
            assert result[key] == value
        assert result["live_runtime_readiness_claim_allowed"] is False


def test_live_tail_transition_identity_and_authority_boundaries() -> None:
    work_orders = _module()
    stage_outcome = _order("stage_outcome_authority")
    readback_family = (
        "stage_outcome_authority_current_execution_running_proof_live_readback_ref"
    )

    generic_readback = work_orders.evaluate_live_tail_evidence_record(
        stage_outcome,
        _tail_record(
            stage_outcome,
            evidence_source="runtime_readback:current-execution-running-proof",
            ref_family=readback_family,
            include_transition_identity=False,
        ),
    )
    assert generic_readback["status"] == "typed_blocker_required"
    assert generic_readback["missing_transition_identity_ref_families"] == [
        readback_family
    ]

    no_active_scan = work_orders.evaluate_live_tail_evidence_record(
        stage_outcome,
        _tail_record(
            stage_outcome,
            evidence_source="no_active_caller_scan:owner-callable-adapter",
            ref_family="stage_outcome_authority_no_active_owner_callable_adapter_caller_scan_ref",
            include_transition_identity=False,
        ),
    )
    assert no_active_scan["status"] == "satisfied_by_accepted_ref"
    assert no_active_scan["transition_identity_ref_fields_present"] == []

    authority_family = (
        "owner_receipt_or_stable_typed_blocker_or_human_gate_or_route_back_ref"
    )
    authority_order = {
        "surface_id": "future_tail_authority_outcome",
        "acceptable_evidence_ref_families": [authority_family],
        "forbidden_evidence_substitutes": [],
        "typed_blocker_when_missing": "future_tail_authority_outcome_required",
    }
    missing_authority_ref = work_orders.evaluate_live_tail_evidence_record(
        authority_order,
        {
            "surface_id": "future_tail_authority_outcome",
            "evidence_source": "mas_owner_gate:typed-blocker-recorded",
            "evidence_ref_families": [authority_family],
            "evidence_refs": ["generic-live-tail-evidence:future-tail"],
            **_transition_identity(),
        },
    )
    assert missing_authority_ref["status"] == "typed_blocker_required"
    assert missing_authority_ref["missing_authority_outcome_ref_families"] == [
        authority_family
    ]

    typed_blocker_ref = work_orders.evaluate_live_tail_evidence_record(
        authority_order,
        {
            "surface_id": "future_tail_authority_outcome",
            "evidence_source": "mas_owner_gate:typed-blocker-recorded",
            "evidence_ref_families": [authority_family],
            "typed_blocker_ref": "typed-blocker:future-tail",
            **_transition_identity(),
        },
    )
    assert typed_blocker_ref["status"] == "satisfied_by_accepted_ref"
    assert typed_blocker_ref["authority_outcome_ref_fields_present"] == [
        "typed_blocker_ref"
    ]


def test_live_tail_evidence_intake_summary_gates_ready_claims() -> None:
    work_orders = _module()
    contract = _contract()
    records = [_tail_record(order) for order in contract["work_orders"]]

    partial = work_orders.live_tail_evidence_intake_summary(contract, records[:1])
    assert partial["satisfied_count"] == 1
    assert partial["typed_blocker_count"] == 6
    assert partial["live_runtime_readiness_claim_allowed"] is False

    false_claim = work_orders.live_tail_evidence_intake_summary(
        contract,
        [{**records[0], "claim": "provider running and paper progress"}],
    )
    first_result = next(
        result for result in false_claim["results"] if result["surface_id"] == records[0]["surface_id"]
    )
    assert first_result["status"] == "typed_blocker_required"
    assert first_result["forbidden_claim_terms_present"] == [
        "paper progress",
        "provider running",
    ]

    complete = work_orders.live_tail_evidence_intake_summary(contract, records)
    assert complete["satisfied_count"] == 7
    assert complete["typed_blocker_count"] == 0
    assert complete["live_runtime_readiness_claim_allowed"] is True

    polluted = work_orders.live_tail_evidence_intake_summary(
        contract,
        [
            *records,
            {**records[0], "evidence_source": "owner_readback:duplicate"},
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
    )
    assert polluted["satisfied_count"] == 7
    assert polluted["typed_blocker_count"] == 4
    assert polluted["intake_violation_count"] == 4
    assert {
        "duplicate_live_tail_evidence_surface_id",
        "malformed_live_tail_evidence_record",
        "missing_live_tail_evidence_surface_id",
        "unknown_live_tail_evidence_surface_id",
    } == {violation["typed_blocker"] for violation in polluted["intake_violations"]}


def _tail_record(
    order: dict,
    *,
    evidence_source: str | None = None,
    ref_family: str | None = None,
    include_transition_identity: bool = True,
) -> dict:
    selected_family = ref_family or order["acceptable_evidence_ref_families"][0]
    record = {
        "surface_id": order["surface_id"],
        "evidence_source": evidence_source or f"owner_readback:{order['surface_id']}",
        "evidence_ref_families": [selected_family],
        "evidence_refs": [f"live-tail-evidence:{order['surface_id']}:{selected_family}"],
    }
    if include_transition_identity:
        record.update(_transition_identity())
    return record


def _transition_identity() -> dict[str, str]:
    return {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        "route_identity_key": "provider-admission::003::publication-blockers",
        "attempt_idempotency_key": "provider-admission::003::publication-blockers",
    }
