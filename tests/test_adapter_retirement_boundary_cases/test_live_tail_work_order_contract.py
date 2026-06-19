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
    schema = boundary["evidence_record_schema"]
    assert boundary["repo_source_retirement_can_complete_without_these_work_orders"] is True
    assert boundary["these_work_orders_can_claim_live_runtime_ready_without_evidence"] is False
    assert boundary["docs_tests_inventory_or_queue_empty_can_satisfy_work_order"] is False
    assert {
        "ready",
        "runtime ready",
        "provider running",
        "paper progress",
        "publication-ready",
        "production-ready",
    } <= set(schema["forbidden_claim_terms"])
    assert schema["unknown_evidence_record_id_status"] == "typed_blocker_required"
    assert schema["duplicate_evidence_record_id_status"] == "typed_blocker_required"
    assert schema["unknown_or_duplicate_evidence_record_can_satisfy_work_order"] is False
    assert (
        schema["unknown_or_duplicate_evidence_record_blocks_live_runtime_readiness_claim"]
        is True
    )
    assert schema["missing_evidence_record_id_status"] == "typed_blocker_required"
    assert schema["malformed_evidence_record_status"] == "typed_blocker_required"
    assert schema["missing_or_malformed_evidence_record_can_satisfy_work_order"] is False
    assert (
        schema["missing_or_malformed_evidence_record_blocks_live_runtime_readiness_claim"]
        is True
    )
    assert schema["accepted_evidence_source_prefixes"] == [
        "live_soak:",
        "mas_owner_gate:",
        "no_active_caller_scan:",
        "operator_readback:",
        "owner_readback:",
        "production_caller_scan:",
        "runtime_readback:",
    ]
    assert {
        "DHD_dry_run",
        "contract_landed",
        "docs",
        "focused_tests",
        "make_test_meta",
        "queue_empty",
        "replay_fixture",
        "repo_source_retirement_complete",
        "repo_tests",
        "scripts_verify",
    } <= set(schema["forbidden_evidence_source_prefixes"])
    assert schema["unaccepted_evidence_source_status"] == "typed_blocker_required"
    assert schema["forbidden_evidence_source_status"] == "typed_blocker_required"
    assert schema["forbidden_or_unaccepted_source_can_satisfy_work_order"] is False
    assert (
        schema["forbidden_or_unaccepted_source_blocks_live_runtime_readiness_claim"]
        is True
    )
    assert "evidence_refs" in schema["optional_fields"]
    assert schema["concrete_evidence_ref_fields"] == [
        "evidence_refs",
        "owner_receipt_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_ref",
    ]
    assert schema["missing_concrete_evidence_ref_status"] == "typed_blocker_required"
    assert schema["accepted_family_without_concrete_ref_can_satisfy_work_order"] is False
    assert (
        schema["missing_concrete_evidence_ref_blocks_live_runtime_readiness_claim"]
        is True
    )
    assert schema["authority_outcome_ref_required_for_families"] == [
        "owner_receipt_or_stable_typed_blocker_or_human_gate_or_route_back_ref"
    ]
    assert schema["authority_outcome_ref_fields"] == [
        "owner_receipt_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_ref",
    ]
    assert schema["missing_authority_outcome_ref_status"] == "typed_blocker_required"
    assert schema["authority_family_without_outcome_ref_can_satisfy_work_order"] is False
    assert (
        schema["missing_authority_outcome_ref_blocks_live_runtime_readiness_claim"]
        is True
    )
    assert {
        "domain_owner_action_dispatch_current_execution_running_proof_live_readback_ref",
        "domain_owner_action_dispatch_provider_hosted_stage_packet_live_readback_ref",
        "progress_portal_study_workbench_overview_action_projection_opl_domain_progress_transition_runtime_readback_ref",
        "runtime_health_kernel_opl_route_reconciler_live_readback_ref",
    } <= set(schema["transition_identity_ref_required_for_families"])
    assert schema["transition_identity_ref_fields"] == [
        "study_id",
        "work_unit_id",
        "work_unit_fingerprint",
        "route_identity_key",
        "attempt_idempotency_key",
    ]
    assert schema["missing_transition_identity_ref_status"] == "typed_blocker_required"
    assert (
        schema["same_identity_family_without_transition_identity_can_satisfy_work_order"]
        is False
    )
    assert (
        schema["missing_transition_identity_ref_blocks_live_runtime_readiness_claim"]
        is True
    )
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


def test_live_tail_contract_rejects_undeclared_concrete_evidence_ref_fields() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_tail_work_orders"
    )
    contract = _contract()
    audit = _audit()
    bad_contract = json.loads(json.dumps(contract))
    schema = bad_contract["completion_claim_boundary"]["evidence_record_schema"]
    schema["optional_fields"].remove("evidence_refs")

    violations = work_orders.validate_live_tail_work_order_contract(
        bad_contract,
        audit,
    )

    assert {
        "surface_id": "<contract>",
        "reason": "undeclared_concrete_evidence_ref_fields",
    } in violations


def test_live_tail_contract_rejects_missing_authority_outcome_schema() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_tail_work_orders"
    )
    contract = _contract()
    audit = _audit()
    bad_contract = json.loads(json.dumps(contract))
    schema = bad_contract["completion_claim_boundary"]["evidence_record_schema"]
    schema.pop("authority_outcome_ref_required_for_families")

    violations = work_orders.validate_live_tail_work_order_contract(
        bad_contract,
        audit,
    )

    assert {
        "surface_id": "<contract>",
        "reason": "authority_outcome_ref_families_mismatch",
    } in violations


def test_live_tail_contract_rejects_missing_transition_identity_schema() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_tail_work_orders"
    )
    contract = _contract()
    audit = _audit()
    bad_contract = json.loads(json.dumps(contract))
    bad_contract["completion_claim_boundary"]["evidence_record_schema"].pop(
        "transition_identity_ref_required_for_families"
    )

    violations = work_orders.validate_live_tail_work_order_contract(
        bad_contract,
        audit,
    )

    assert {
        "surface_id": "<contract>",
        "reason": "transition_identity_ref_families_mismatch",
    } in violations


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
            "evidence_refs": [
                "opl-observability-readback:runtime-health-kernel:2026-06-20T00:00:00Z"
            ],
            **_transition_identity(),
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
            "evidence_refs": [
                "opl-observability-readback:runtime-health-kernel:2026-06-20T00:00:00Z"
            ],
            "evidence_substitutes": [
                "repo_no_authority_guard_as_runtime_health_tail_readback"
            ],
            **_transition_identity(),
        },
    )
    assert forbidden["status"] == "typed_blocker_required"
    assert forbidden["live_runtime_readiness_claim_allowed"] is False
    assert forbidden["typed_blocker"] == (
        "runtime_health_kernel_live_runtime_readiness_evidence_required"
    )
    assert forbidden["repo_source_retirement_blocked"] is False

    false_ready_claim = work_orders.evaluate_live_tail_evidence_record(
        runtime_health,
        {
            "surface_id": "runtime_health_kernel",
            "claim": "runtime ready from accepted readback",
            "evidence_source": "runtime_readback:observability:2026-06-20T00:00:00Z",
            "evidence_ref_families": [
                "runtime_health_kernel_opl_observability_live_readback_ref"
            ],
            "evidence_refs": [
                "opl-observability-readback:runtime-health-kernel:2026-06-20T00:00:00Z"
            ],
            **_transition_identity(),
        },
    )
    assert false_ready_claim["status"] == "typed_blocker_required"
    assert false_ready_claim["forbidden_claim_terms_present"] == [
        "ready",
        "runtime ready",
    ]
    assert false_ready_claim["live_runtime_readiness_claim_allowed"] is False

    non_forbidden_word_boundary = work_orders.evaluate_live_tail_evidence_record(
        runtime_health,
        {
            "surface_id": "runtime_health_kernel",
            "claim": "accepted readback already recorded",
            "evidence_source": "runtime_readback:observability:2026-06-20T00:00:00Z",
            "evidence_ref_families": [
                "runtime_health_kernel_opl_observability_live_readback_ref"
            ],
            "evidence_refs": [
                "opl-observability-readback:runtime-health-kernel:2026-06-20T00:00:00Z"
            ],
            **_transition_identity(),
        },
    )
    assert non_forbidden_word_boundary["status"] == "satisfied_by_accepted_ref"
    assert non_forbidden_word_boundary["forbidden_claim_terms_present"] == []

    missing = work_orders.evaluate_live_tail_evidence_record(runtime_health, {})
    assert missing["status"] == "typed_blocker_required"
    assert missing["matched_evidence_ref_families"] == []
    assert missing["typed_blocker"] == (
        "runtime_health_kernel_live_runtime_readiness_evidence_required"
    )


def test_live_tail_evidence_record_rejects_repo_test_source_even_with_accepted_refs() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_tail_work_orders"
    )
    contract = _contract()
    runtime_health = {
        order["surface_id"]: order for order in contract["work_orders"]
    }["runtime_health_kernel"]

    repo_test_source = work_orders.evaluate_live_tail_evidence_record(
        runtime_health,
        {
            "surface_id": "runtime_health_kernel",
            "claim": "accepted readback already recorded",
            "evidence_source": "focused_tests",
            "evidence_ref_families": [
                "runtime_health_kernel_opl_observability_live_readback_ref"
            ],
            "evidence_refs": [
                "opl-observability-readback:runtime-health-kernel:2026-06-20T00:00:00Z"
            ],
        },
    )

    assert repo_test_source["status"] == "typed_blocker_required"
    assert repo_test_source["accepted_evidence_source_prefix"] is None
    assert repo_test_source["forbidden_evidence_source_prefixes_present"] == [
        "focused_tests"
    ]
    assert repo_test_source["live_runtime_readiness_claim_allowed"] is False


def test_live_tail_evidence_record_requires_concrete_evidence_ref() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_tail_work_orders"
    )
    contract = _contract()
    runtime_health = {
        order["surface_id"]: order for order in contract["work_orders"]
    }["runtime_health_kernel"]
    ref_family = "runtime_health_kernel_opl_observability_live_readback_ref"

    family_only = work_orders.evaluate_live_tail_evidence_record(
        runtime_health,
        {
            "surface_id": "runtime_health_kernel",
            "evidence_source": "runtime_readback:observability:2026-06-20T00:00:00Z",
            "evidence_ref_families": [ref_family],
        },
    )

    assert family_only["status"] == "typed_blocker_required"
    assert family_only["missing_concrete_evidence_ref_families"] == [ref_family]
    assert family_only["concrete_evidence_ref_fields_present"] == []
    assert family_only["live_runtime_readiness_claim_allowed"] is False

    concrete_ref = work_orders.evaluate_live_tail_evidence_record(
        runtime_health,
        {
            "surface_id": "runtime_health_kernel",
            "evidence_source": "runtime_readback:observability:2026-06-20T00:00:00Z",
            "evidence_ref_families": [ref_family],
            "evidence_refs": [
                "opl-observability-readback:runtime-health-kernel:2026-06-20T00:00:00Z"
            ],
            **_transition_identity(),
        },
    )

    assert concrete_ref["status"] == "satisfied_by_accepted_ref"
    assert concrete_ref["missing_concrete_evidence_ref_families"] == []
    assert concrete_ref["concrete_evidence_ref_fields_present"] == ["evidence_refs"]
    assert concrete_ref["live_runtime_readiness_claim_allowed"] is True


def test_live_tail_evidence_requires_current_transition_identity_for_readback_families() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_tail_work_orders"
    )
    contract = _contract()
    owner_dispatch = {
        order["surface_id"]: order for order in contract["work_orders"]
    }["domain_owner_action_dispatch"]
    readback_family = "domain_owner_action_dispatch_current_execution_running_proof_live_readback_ref"

    generic_readback = work_orders.evaluate_live_tail_evidence_record(
        owner_dispatch,
        {
            "surface_id": "domain_owner_action_dispatch",
            "evidence_source": "runtime_readback:current-execution-running-proof",
            "evidence_ref_families": [readback_family],
            "evidence_refs": [
                "live-tail-evidence:domain_owner_action_dispatch:current_execution"
            ],
        },
    )

    assert generic_readback["status"] == "typed_blocker_required"
    assert generic_readback["missing_transition_identity_ref_families"] == [
        readback_family
    ]
    assert generic_readback["transition_identity_ref_fields_present"] == []
    assert generic_readback["live_runtime_readiness_claim_allowed"] is False

    complete_identity = work_orders.evaluate_live_tail_evidence_record(
        owner_dispatch,
        {
            "surface_id": "domain_owner_action_dispatch",
            "evidence_source": "runtime_readback:current-execution-running-proof",
            "evidence_ref_families": [readback_family],
            "evidence_refs": [
                "live-tail-evidence:domain_owner_action_dispatch:current_execution"
            ],
            **_transition_identity(),
        },
    )

    assert complete_identity["status"] == "satisfied_by_accepted_ref"
    assert complete_identity["missing_transition_identity_ref_families"] == []
    assert complete_identity["transition_identity_ref_fields_present"] == [
        "attempt_idempotency_key",
        "route_identity_key",
        "study_id",
        "work_unit_fingerprint",
        "work_unit_id",
    ]


def test_live_tail_no_active_caller_evidence_does_not_require_transition_identity() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_tail_work_orders"
    )
    contract = _contract()
    owner_dispatch = {
        order["surface_id"]: order for order in contract["work_orders"]
    }["domain_owner_action_dispatch"]
    no_active_family = "domain_owner_action_dispatch_no_active_owner_callable_adapter_caller_scan_ref"

    no_active_scan = work_orders.evaluate_live_tail_evidence_record(
        owner_dispatch,
        {
            "surface_id": "domain_owner_action_dispatch",
            "evidence_source": "no_active_caller_scan:owner-callable-adapter",
            "evidence_ref_families": [no_active_family],
            "evidence_refs": ["repo-scan:domain_owner_action_dispatch:no-active-caller"],
        },
    )

    assert no_active_scan["status"] == "satisfied_by_accepted_ref"
    assert no_active_scan["missing_transition_identity_ref_families"] == []
    assert no_active_scan["transition_identity_ref_fields_present"] == []
    assert no_active_scan["live_runtime_readiness_claim_allowed"] is True


def test_live_tail_direct_evaluator_rejects_mismatched_surface_id() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_tail_work_orders"
    )
    contract = _contract()
    runtime_health = {
        order["surface_id"]: order for order in contract["work_orders"]
    }["runtime_health_kernel"]
    ref_family = "runtime_health_kernel_opl_observability_live_readback_ref"

    mismatched = work_orders.evaluate_live_tail_evidence_record(
        runtime_health,
        {
            "surface_id": "domain_owner_action_dispatch",
            "evidence_source": "runtime_readback:observability:2026-06-20T00:00:00Z",
            "evidence_ref_families": [ref_family],
            "evidence_refs": [
                "opl-observability-readback:runtime-health-kernel:2026-06-20T00:00:00Z"
            ],
            **_transition_identity(),
        },
    )

    assert mismatched["status"] == "typed_blocker_required"
    assert mismatched["evidence_record_surface_id"] == "domain_owner_action_dispatch"
    assert mismatched["evidence_record_id_mismatch"] is True
    assert mismatched["matched_evidence_ref_families"] == [ref_family]
    assert mismatched["live_runtime_readiness_claim_allowed"] is False


def test_live_tail_authority_outcome_family_requires_authority_ref() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_tail_work_orders"
    )
    authority_family = (
        "owner_receipt_or_stable_typed_blocker_or_human_gate_or_route_back_ref"
    )
    order = {
        "surface_id": "future_tail_authority_outcome",
        "acceptable_evidence_ref_families": [authority_family],
        "forbidden_evidence_substitutes": [],
        "typed_blocker_when_missing": "future_tail_authority_outcome_required",
    }

    family_with_generic_ref = work_orders.evaluate_live_tail_evidence_record(
        order,
        {
            "surface_id": "future_tail_authority_outcome",
            "evidence_source": "mas_owner_gate:typed-blocker-recorded",
            "evidence_ref_families": [authority_family],
            "evidence_refs": ["generic-live-tail-evidence:future-tail"],
        },
    )

    assert family_with_generic_ref["status"] == "typed_blocker_required"
    assert family_with_generic_ref["missing_authority_outcome_ref_families"] == [
        authority_family
    ]
    assert family_with_generic_ref["authority_outcome_ref_fields_present"] == []
    assert family_with_generic_ref["concrete_evidence_ref_fields_present"] == [
        "evidence_refs"
    ]
    assert family_with_generic_ref["live_runtime_readiness_claim_allowed"] is False

    typed_blocker_ref = work_orders.evaluate_live_tail_evidence_record(
        order,
        {
            "surface_id": "future_tail_authority_outcome",
            "evidence_source": "mas_owner_gate:typed-blocker-recorded",
            "evidence_ref_families": [authority_family],
            "typed_blocker_ref": "typed-blocker:future-tail",
            **_transition_identity(),
        },
    )

    assert typed_blocker_ref["status"] == "satisfied_by_accepted_ref"
    assert typed_blocker_ref["missing_authority_outcome_ref_families"] == []
    assert typed_blocker_ref["authority_outcome_ref_fields_present"] == [
        "typed_blocker_ref"
    ]
    assert typed_blocker_ref["live_runtime_readiness_claim_allowed"] is True


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
        "evidence_refs": [
            "opl-observability-readback:runtime-health-kernel:2026-06-20T00:00:00Z"
        ],
        **_transition_identity(),
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

    false_claim = work_orders.live_tail_evidence_intake_summary(
        contract,
        [
            {
                **runtime_health_record,
                "claim": "provider running and paper progress",
            }
        ],
    )
    runtime_health_result = next(
        result
        for result in false_claim["results"]
        if result["surface_id"] == "runtime_health_kernel"
    )
    assert runtime_health_result["status"] == "typed_blocker_required"
    assert runtime_health_result["forbidden_claim_terms_present"] == [
        "paper progress",
        "provider running",
    ]
    assert "runtime_health_kernel" in false_claim["typed_blocker_surface_ids"]
    assert "runtime_health_kernel" not in false_claim["satisfied_surface_ids"]

    all_records = [_satisfying_tail_record(order) for order in contract["work_orders"]]
    complete = work_orders.live_tail_evidence_intake_summary(contract, all_records)
    assert complete["satisfied_count"] == 7
    assert complete["typed_blocker_count"] == 0
    assert complete["live_runtime_readiness_claim_allowed"] is True


def test_live_tail_evidence_intake_fails_closed_on_unknown_or_duplicate_records() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_tail_work_orders"
    )
    contract = _contract()
    all_records = [_satisfying_tail_record(order) for order in contract["work_orders"]]

    polluted = work_orders.live_tail_evidence_intake_summary(
        contract,
        [
            *all_records,
            {
                **all_records[0],
                "evidence_source": "owner_readback:duplicate",
            },
            {
                "surface_id": "unknown_private_surface",
                "evidence_source": "owner_readback:unknown",
                "evidence_ref_families": ["runtime_health_kernel_opl_observability_live_readback_ref"],
            },
            {
                "evidence_source": "owner_readback:missing-id",
                "evidence_ref_families": ["runtime_health_kernel_opl_observability_live_readback_ref"],
            },
            "malformed-record",
        ],
    )

    assert polluted["satisfied_count"] == 7
    assert polluted["typed_blocker_count"] == 4
    assert polluted["intake_violation_count"] == 4
    assert polluted["duplicate_surface_ids"] == [all_records[0]["surface_id"]]
    assert polluted["unknown_surface_ids"] == ["unknown_private_surface"]
    assert polluted["missing_surface_id_record_indexes"] == [9]
    assert polluted["malformed_record_indexes"] == [10]
    assert polluted["live_runtime_readiness_claim_allowed"] is False
    assert {
        "duplicate_live_tail_evidence_surface_id",
        "malformed_live_tail_evidence_record",
        "missing_live_tail_evidence_surface_id",
        "unknown_live_tail_evidence_surface_id",
    } == {violation["typed_blocker"] for violation in polluted["intake_violations"]}


def _satisfying_tail_record(order: dict) -> dict:
    ref_family = order["acceptable_evidence_ref_families"][0]
    record = {
        "surface_id": order["surface_id"],
        "evidence_source": f"owner_readback:{order['surface_id']}",
        "evidence_ref_families": [ref_family],
        "evidence_refs": [f"live-tail-evidence:{order['surface_id']}:{ref_family}"],
    }
    if _tail_family_requires_transition_identity(ref_family):
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


def _tail_family_requires_transition_identity(ref_family: str) -> bool:
    markers = (
        "live_readback",
        "running_proof",
        "current_owner_delta_readback",
        "current_control_readback",
        "domain_progress_transition_runtime_readback",
        "provider_hosted_stage_packet",
        "stage_native_owner_action",
        "execute_dispatch",
        "authorization_live_readback",
        "live_every_active_caller_soak",
        "live_opl",
        "tail_readback",
    )
    excluded = ("no_active", "tombstone", "replacement_parity", "no_forbidden_write")
    return any(marker in ref_family for marker in markers) and not any(
        marker in ref_family for marker in excluded
    )
