from __future__ import annotations

import importlib
import json
from collections.abc import Callable
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPLETION_AUDIT_PATH = (
    REPO_ROOT / "contracts" / "paper_progress_transition_runtime_completion_audit.json"
)
WORK_ORDER_PATH = (
    REPO_ROOT / "contracts" / "runtime" / "mas-live-runtime-gap-work-orders.json"
)


def _module():
    return importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement.live_runtime_gap_work_orders"
    )


def _completion_audit() -> dict:
    return json.loads(COMPLETION_AUDIT_PATH.read_text(encoding="utf-8"))


def _contract() -> dict:
    return json.loads(WORK_ORDER_PATH.read_text(encoding="utf-8"))


def _order_with_family(ref_family: str) -> dict:
    return next(
        order
        for order in _contract()["work_orders"]
        if ref_family in order["acceptable_evidence_ref_families"]
    )


def test_live_runtime_gap_work_order_contract_matches_completion_audit() -> None:
    work_orders = _module()
    completion = _completion_audit()
    contract = _contract()

    assert work_orders.validate_live_runtime_gap_work_order_contract(
        contract,
        completion,
    ) == []
    assert contract["surface_kind"] == "mas_live_runtime_gap_work_orders"
    assert contract["repo_source_retirement_blocked"] is False
    assert contract["live_runtime_readiness_claim_allowed"] is False

    expected = {
        order["gap_id"]: order
        for order in work_orders.live_runtime_gap_work_orders_from_completion_audit(
            completion
        )
    }
    observed = {order["gap_id"]: order for order in contract["work_orders"]}
    assert set(observed) == set(expected)
    assert len(observed) == 5
    assert all(order["status"] == "evidence_required" for order in observed.values())
    assert all(
        order["typed_blocker_when_missing"]
        == f"{gap_id}_live_runtime_evidence_required"
        for gap_id, order in observed.items()
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
    assert schema["authority_family_without_outcome_ref_can_satisfy_work_order"] is False
    assert schema["accepted_family_without_concrete_ref_can_satisfy_work_order"] is False
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
            lambda schema: schema.pop("transition_identity_ref_required_for_families"),
            "transition_identity_ref_families_mismatch",
        ),
    ],
)
def test_live_runtime_gap_contract_rejects_broken_evidence_schema(
    mutate: Callable[[dict], object],
    reason: str,
) -> None:
    work_orders = _module()
    bad_contract = json.loads(json.dumps(_contract()))
    mutate(bad_contract["completion_claim_boundary"]["evidence_record_schema"])

    violations = work_orders.validate_live_runtime_gap_work_order_contract(
        bad_contract,
        _completion_audit(),
    )

    assert {"gap_id": "<contract>", "reason": reason} in violations


def test_live_runtime_gap_evidence_record_guard_cases() -> None:
    work_orders = _module()
    ref_family = "same_identity_opl_provider_admission_live_readback_ref"
    provider_readback = _order_with_family(ref_family)
    accepted_record = _gap_record(
        provider_readback,
        evidence_source="opl_live_readback:provider-admission:2026-06-20T00:00:00Z",
        ref_family=ref_family,
    )

    accepted = work_orders.evaluate_live_runtime_gap_evidence_record(
        provider_readback,
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
                "missing_concrete_evidence_ref_families": [ref_family],
            },
        ),
        (
            {
                key: value
                for key, value in accepted_record.items()
                if key not in {"route_identity_key", "attempt_idempotency_key"}
            },
            {
                "status": "typed_blocker_required",
                "missing_transition_identity_ref_families": [ref_family],
            },
        ),
        (
            {**accepted_record, "claim": "live runtime ready after provider running readback"},
            {
                "status": "typed_blocker_required",
                "forbidden_claim_terms_present": [
                    "live runtime ready",
                    "provider running",
                    "ready",
                    "runtime ready",
                ],
            },
        ),
        (
            {
                **accepted_record,
                "gap_id": "domain_diagnostic_apply_exactly_one_live_outcome_when_explicitly_delegated",
            },
            {
                "status": "typed_blocker_required",
                "evidence_record_id_mismatch": True,
            },
        ),
    ]
    for record, expected in guard_cases:
        result = work_orders.evaluate_live_runtime_gap_evidence_record(
            provider_readback,
            record,
        )
        for key, value in expected.items():
            assert result[key] == value
        assert result["live_runtime_readiness_claim_allowed"] is False


def test_live_runtime_gap_authority_outcome_requires_concrete_authority_ref() -> None:
    work_orders = _module()
    authority_family = (
        "MAS_owner_receipt_or_stable_typed_blocker_or_human_gate_or_route_back_ref"
    )
    authority_order = _order_with_family(authority_family)

    family_only = work_orders.evaluate_live_runtime_gap_evidence_record(
        authority_order,
        {
            "gap_id": authority_order["gap_id"],
            "evidence_source": "mas_owner_gate:typed-blocker-recorded",
            "evidence_ref_families": [authority_family],
            **_transition_identity(),
        },
    )
    assert family_only["status"] == "typed_blocker_required"
    assert family_only["missing_authority_outcome_ref_families"] == [authority_family]

    concrete_typed_blocker = work_orders.evaluate_live_runtime_gap_evidence_record(
        authority_order,
        {
            "gap_id": authority_order["gap_id"],
            "evidence_source": "mas_owner_gate:typed-blocker-recorded",
            "evidence_ref_families": [authority_family],
            "typed_blocker_ref": "typed-blocker:dm003:no-selected-dispatch",
            **_transition_identity(),
        },
    )
    assert concrete_typed_blocker["status"] == "satisfied_by_accepted_ref"
    assert concrete_typed_blocker["authority_outcome_ref_fields_present"] == [
        "typed_blocker_ref"
    ]
    assert concrete_typed_blocker["concrete_evidence_ref_fields_present"] == [
        "typed_blocker_ref"
    ]


def test_live_runtime_gap_intake_summary_gates_ready_claims() -> None:
    work_orders = _module()
    contract = _contract()
    records = [_gap_record(order) for order in contract["work_orders"]]

    empty = work_orders.live_runtime_gap_evidence_intake_summary(contract, [])
    assert empty["total_work_order_count"] == 5
    assert empty["typed_blocker_count"] == 5
    assert empty["live_runtime_readiness_claim_allowed"] is False

    partial = work_orders.live_runtime_gap_evidence_intake_summary(contract, records[:1])
    assert partial["satisfied_count"] == 1
    assert partial["typed_blocker_count"] == 4
    assert partial["live_runtime_readiness_claim_allowed"] is False

    false_claim = work_orders.live_runtime_gap_evidence_intake_summary(
        contract,
        [{**records[0], "claim": "paper progress complete"}],
    )
    first_result = next(
        result for result in false_claim["results"] if result["gap_id"] == records[0]["gap_id"]
    )
    assert first_result["status"] == "typed_blocker_required"
    assert first_result["forbidden_claim_terms_present"] == ["paper progress"]

    complete = work_orders.live_runtime_gap_evidence_intake_summary(contract, records)
    assert complete["satisfied_count"] == 5
    assert complete["typed_blocker_count"] == 0
    assert complete["live_runtime_readiness_claim_allowed"] is True

    polluted = work_orders.live_runtime_gap_evidence_intake_summary(
        contract,
        [
            *records,
            {**records[0], "evidence_source": "owner_readback:duplicate"},
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
    assert polluted["satisfied_count"] == 5
    assert polluted["typed_blocker_count"] == 4
    assert polluted["intake_violation_count"] == 4
    assert {
        "duplicate_live_runtime_gap_evidence_gap_id",
        "malformed_live_runtime_gap_evidence_record",
        "missing_live_runtime_gap_evidence_gap_id",
        "unknown_live_runtime_gap_evidence_gap_id",
    } == {violation["typed_blocker"] for violation in polluted["intake_violations"]}


def _gap_record(
    order: dict,
    *,
    evidence_source: str | None = None,
    ref_family: str | None = None,
) -> dict:
    selected_family = ref_family or order["acceptable_evidence_ref_families"][0]
    record = {
        "gap_id": order["gap_id"],
        "evidence_source": evidence_source or f"owner_readback:{order['gap_id']}",
        "evidence_ref_families": [selected_family],
        "evidence_refs": [f"live-gap-evidence:{order['gap_id']}:{selected_family}"],
        **_transition_identity(),
    }
    if selected_family == "MAS_owner_receipt_or_stable_typed_blocker_or_human_gate_or_route_back_ref":
        record["typed_blocker_ref"] = f"typed-blocker:{order['gap_id']}"
    return record


def _transition_identity() -> dict[str, str]:
    return {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        "route_identity_key": "provider-admission::003::publication-blockers",
        "attempt_idempotency_key": "provider-admission::003::publication-blockers",
    }
