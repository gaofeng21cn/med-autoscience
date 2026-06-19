from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPLETION_AUDIT_PATH = REPO_ROOT / "contracts" / "paper_progress_transition_runtime_completion_audit.json"
WORK_ORDER_PATH = REPO_ROOT / "contracts" / "runtime" / "mas-live-runtime-gap-work-orders.json"


def _completion_audit() -> dict:
    return json.loads(COMPLETION_AUDIT_PATH.read_text(encoding="utf-8"))


def _contract() -> dict:
    return json.loads(WORK_ORDER_PATH.read_text(encoding="utf-8"))


def test_live_runtime_gap_work_order_contract_matches_completion_audit() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_gap_work_orders"
    )
    completion = _completion_audit()
    contract = _contract()

    assert work_orders.validate_live_runtime_gap_work_order_contract(
        contract,
        completion,
    ) == []
    assert contract["surface_kind"] == "mas_live_runtime_gap_work_orders"
    assert contract["repo_source_retirement_blocked"] is False
    assert contract["live_runtime_readiness_claim_allowed"] is False
    assert {
        "ready",
        "runtime ready",
        "provider running",
        "paper progress",
        "publication-ready",
        "production-ready",
    } <= set(
        contract["completion_claim_boundary"]["evidence_record_schema"][
            "forbidden_claim_terms"
        ]
    )
    schema = contract["completion_claim_boundary"]["evidence_record_schema"]
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
        "opl_live_readback:",
        "operator_readback:",
        "owner_readback:",
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
    assert schema["authority_outcome_ref_required_for_families"] == [
        "MAS_owner_receipt_or_stable_typed_blocker_or_human_gate_or_route_back_ref"
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
    assert schema["transition_identity_ref_required_for_families"] == [
        "DHD_apply_exactly_one_live_outcome_ref",
        "MAS_owner_receipt_or_stable_typed_blocker_or_human_gate_or_route_back_ref",
        "OPL_command_event_outbox_live_readback_ref",
        "OPL_domain_progress_transition_runtime_live_readback_same_identity_ref",
        "StageRun_identity_packet_currentness_ref",
        "fresh_DM002_DM003_paper_line_accepted_outcome_ref",
        "provider_admission_arbiter_consumes_opl_transition_event_ref",
        "same_identity_opl_provider_admission_live_readback_ref",
    ]
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

    expected = {
        order["gap_id"]: order
        for order in work_orders.live_runtime_gap_work_orders_from_completion_audit(completion)
    }
    observed = {order["gap_id"]: order for order in contract["work_orders"]}
    assert set(observed) == set(expected)
    assert len(observed) == 5

    for gap_id, order in observed.items():
        assert order["status"] == "evidence_required"
        assert order["repo_source_retirement_blocked"] is False
        assert order["live_runtime_readiness_claim_allowed"] is False
        assert order["typed_blocker_when_missing"] == (
            f"{gap_id}_live_runtime_evidence_required"
        )
        assert order["acceptable_evidence_ref_families"]
        assert order["forbidden_evidence_substitutes"]


def test_live_runtime_gap_evidence_intake_rejects_false_substitutes() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_gap_work_orders"
    )
    contract = _contract()
    by_text = {order["gap_text"]: order for order in contract["work_orders"]}
    provider_readback = by_text[
        "fresh DM002/DM003 same-identity OPL provider-admission live readback instead of replay fixture readback"
    ]

    accepted = work_orders.evaluate_live_runtime_gap_evidence_record(
        provider_readback,
        {
            "gap_id": provider_readback["gap_id"],
            "evidence_source": "opl_live_readback:provider-admission:2026-06-20T00:00:00Z",
            "evidence_ref_families": [
                "same_identity_opl_provider_admission_live_readback_ref"
            ],
            "evidence_refs": [
                (
                    "live-gap-evidence:"
                    f"{provider_readback['gap_id']}:"
                    "same_identity_opl_provider_admission_live_readback_ref"
                )
            ],
            **_transition_identity(),
        },
    )
    assert accepted["status"] == "satisfied_by_accepted_ref"
    assert accepted["live_runtime_readiness_claim_allowed"] is True
    assert accepted["typed_blocker"] is None

    forbidden = work_orders.evaluate_live_runtime_gap_evidence_record(
        provider_readback,
        {
            "gap_id": provider_readback["gap_id"],
            "evidence_source": "replay_fixture",
            "evidence_ref_families": [
                "same_identity_opl_provider_admission_live_readback_ref"
            ],
            "evidence_refs": [
                (
                    "live-gap-evidence:"
                    f"{provider_readback['gap_id']}:"
                    "same_identity_opl_provider_admission_live_readback_ref"
                )
            ],
            "evidence_substitutes": [
                "provider_admission_same_identity_replay_as_fresh_opl_readback"
            ],
            **_transition_identity(),
        },
    )
    assert forbidden["status"] == "typed_blocker_required"
    assert forbidden["live_runtime_readiness_claim_allowed"] is False
    assert forbidden["repo_source_retirement_blocked"] is False
    assert forbidden["typed_blocker"] == (
        f"{provider_readback['gap_id']}_live_runtime_evidence_required"
    )

    false_ready_claim = work_orders.evaluate_live_runtime_gap_evidence_record(
        provider_readback,
        {
            "gap_id": provider_readback["gap_id"],
            "claim": "live runtime ready after provider running readback",
            "evidence_source": "opl_live_readback:provider-admission:2026-06-20T00:00:00Z",
            "evidence_ref_families": [
                "same_identity_opl_provider_admission_live_readback_ref"
            ],
            "evidence_refs": [
                (
                    "live-gap-evidence:"
                    f"{provider_readback['gap_id']}:"
                    "same_identity_opl_provider_admission_live_readback_ref"
                )
            ],
            **_transition_identity(),
        },
    )
    assert false_ready_claim["status"] == "typed_blocker_required"
    assert false_ready_claim["forbidden_claim_terms_present"] == [
        "live runtime ready",
        "provider running",
        "ready",
        "runtime ready",
    ]
    assert false_ready_claim["live_runtime_readiness_claim_allowed"] is False

    non_forbidden_word_boundary = work_orders.evaluate_live_runtime_gap_evidence_record(
        provider_readback,
        {
            "gap_id": provider_readback["gap_id"],
            "claim": "accepted readback already recorded",
            "evidence_source": "opl_live_readback:provider-admission:2026-06-20T00:00:00Z",
            "evidence_ref_families": [
                "same_identity_opl_provider_admission_live_readback_ref"
            ],
            "evidence_refs": [
                (
                    "live-gap-evidence:"
                    f"{provider_readback['gap_id']}:"
                    "same_identity_opl_provider_admission_live_readback_ref"
                )
            ],
            **_transition_identity(),
        },
    )
    assert non_forbidden_word_boundary["status"] == "satisfied_by_accepted_ref"
    assert non_forbidden_word_boundary["forbidden_claim_terms_present"] == []


def test_live_runtime_gap_evidence_rejects_repo_test_source_even_with_accepted_refs() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_gap_work_orders"
    )
    contract = _contract()
    by_text = {order["gap_text"]: order for order in contract["work_orders"]}
    provider_readback = by_text[
        "fresh DM002/DM003 same-identity OPL provider-admission live readback instead of replay fixture readback"
    ]

    repo_test_source = work_orders.evaluate_live_runtime_gap_evidence_record(
        provider_readback,
        {
            "gap_id": provider_readback["gap_id"],
            "evidence_source": "focused_tests",
            "evidence_ref_families": [
                "same_identity_opl_provider_admission_live_readback_ref"
            ],
            "evidence_refs": [
                (
                    "live-gap-evidence:"
                    f"{provider_readback['gap_id']}:"
                    "same_identity_opl_provider_admission_live_readback_ref"
                )
            ],
        },
    )

    assert repo_test_source["status"] == "typed_blocker_required"
    assert repo_test_source["accepted_evidence_source_prefix"] is None
    assert repo_test_source["forbidden_evidence_source_prefixes_present"] == [
        "focused_tests"
    ]
    assert repo_test_source["live_runtime_readiness_claim_allowed"] is False


def test_live_runtime_gap_contract_rejects_undeclared_concrete_evidence_ref_fields() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_gap_work_orders"
    )
    completion = _completion_audit()
    contract = _contract()
    bad_contract = json.loads(json.dumps(contract))
    schema = bad_contract["completion_claim_boundary"]["evidence_record_schema"]
    schema["optional_fields"].remove("evidence_refs")

    violations = work_orders.validate_live_runtime_gap_work_order_contract(
        bad_contract,
        completion,
    )

    assert {
        "gap_id": "<contract>",
        "reason": "undeclared_concrete_evidence_ref_fields",
    } in violations


def test_live_runtime_gap_contract_rejects_missing_transition_identity_schema() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_gap_work_orders"
    )
    completion = _completion_audit()
    contract = _contract()
    bad_contract = json.loads(json.dumps(contract))
    bad_contract["completion_claim_boundary"]["evidence_record_schema"].pop(
        "transition_identity_ref_required_for_families"
    )

    violations = work_orders.validate_live_runtime_gap_work_order_contract(
        bad_contract,
        completion,
    )

    assert {
        "gap_id": "<contract>",
        "reason": "transition_identity_ref_families_mismatch",
    } in violations


def test_live_runtime_gap_evidence_requires_concrete_authority_outcome_ref() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_gap_work_orders"
    )
    contract = _contract()
    dhd_apply = next(
        order
        for order in contract["work_orders"]
        if order["gap_id"] == "dhd_apply_exactly_one_live_outcome_when_explicitly_delegated"
    )
    authority_family = (
        "MAS_owner_receipt_or_stable_typed_blocker_or_human_gate_or_route_back_ref"
    )

    family_only = work_orders.evaluate_live_runtime_gap_evidence_record(
        dhd_apply,
        {
            "gap_id": dhd_apply["gap_id"],
            "evidence_source": "mas_owner_gate:typed-blocker-recorded",
            "evidence_ref_families": [authority_family],
        },
    )

    assert family_only["status"] == "typed_blocker_required"
    assert family_only["missing_authority_outcome_ref_families"] == [authority_family]
    assert family_only["authority_outcome_ref_fields_present"] == []
    assert family_only["live_runtime_readiness_claim_allowed"] is False

    concrete_typed_blocker = work_orders.evaluate_live_runtime_gap_evidence_record(
        dhd_apply,
        {
            "gap_id": dhd_apply["gap_id"],
            "evidence_source": "mas_owner_gate:typed-blocker-recorded",
            "evidence_ref_families": [authority_family],
            "typed_blocker_ref": "typed-blocker:dm003:no-selected-dispatch",
            **_transition_identity(),
        },
    )

    assert concrete_typed_blocker["status"] == "satisfied_by_accepted_ref"
    assert concrete_typed_blocker["missing_authority_outcome_ref_families"] == []
    assert concrete_typed_blocker["authority_outcome_ref_fields_present"] == [
        "typed_blocker_ref"
    ]
    assert concrete_typed_blocker["missing_concrete_evidence_ref_families"] == []
    assert concrete_typed_blocker["concrete_evidence_ref_fields_present"] == [
        "typed_blocker_ref"
    ]
    assert concrete_typed_blocker["live_runtime_readiness_claim_allowed"] is True


def test_live_runtime_gap_evidence_requires_concrete_evidence_ref_for_opl_families() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_gap_work_orders"
    )
    contract = _contract()
    provider_readback = next(
        order
        for order in contract["work_orders"]
        if (
            "same_identity_opl_provider_admission_live_readback_ref"
            in order["acceptable_evidence_ref_families"]
        )
    )
    ref_family = "same_identity_opl_provider_admission_live_readback_ref"

    family_only = work_orders.evaluate_live_runtime_gap_evidence_record(
        provider_readback,
        {
            "gap_id": provider_readback["gap_id"],
            "evidence_source": "opl_live_readback:provider-admission:2026-06-20T00:00:00Z",
            "evidence_ref_families": [ref_family],
        },
    )

    assert family_only["status"] == "typed_blocker_required"
    assert family_only["missing_concrete_evidence_ref_families"] == [ref_family]
    assert family_only["concrete_evidence_ref_fields_present"] == []
    assert family_only["live_runtime_readiness_claim_allowed"] is False

    concrete_ref = work_orders.evaluate_live_runtime_gap_evidence_record(
        provider_readback,
        {
            "gap_id": provider_readback["gap_id"],
            "evidence_source": "opl_live_readback:provider-admission:2026-06-20T00:00:00Z",
            "evidence_ref_families": [ref_family],
            "evidence_refs": [
                f"live-gap-evidence:{provider_readback['gap_id']}:{ref_family}"
            ],
            **_transition_identity(),
        },
    )

    assert concrete_ref["status"] == "satisfied_by_accepted_ref"
    assert concrete_ref["missing_concrete_evidence_ref_families"] == []
    assert concrete_ref["concrete_evidence_ref_fields_present"] == ["evidence_refs"]
    assert concrete_ref["live_runtime_readiness_claim_allowed"] is True


def test_live_runtime_gap_evidence_requires_current_transition_identity() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_gap_work_orders"
    )
    contract = _contract()
    provider_readback = next(
        order
        for order in contract["work_orders"]
        if (
            "same_identity_opl_provider_admission_live_readback_ref"
            in order["acceptable_evidence_ref_families"]
        )
    )
    ref_family = "same_identity_opl_provider_admission_live_readback_ref"

    generic_live_ref = work_orders.evaluate_live_runtime_gap_evidence_record(
        provider_readback,
        {
            "gap_id": provider_readback["gap_id"],
            "evidence_source": "opl_live_readback:provider-admission:2026-06-20T00:00:00Z",
            "evidence_ref_families": [ref_family],
            "evidence_refs": [
                f"live-gap-evidence:{provider_readback['gap_id']}:{ref_family}"
            ],
        },
    )

    assert generic_live_ref["status"] == "typed_blocker_required"
    assert generic_live_ref["missing_transition_identity_ref_families"] == [ref_family]
    assert generic_live_ref["transition_identity_ref_fields_present"] == []
    assert generic_live_ref["live_runtime_readiness_claim_allowed"] is False

    incomplete_identity = work_orders.evaluate_live_runtime_gap_evidence_record(
        provider_readback,
        {
            "gap_id": provider_readback["gap_id"],
            "evidence_source": "opl_live_readback:provider-admission:2026-06-20T00:00:00Z",
            "evidence_ref_families": [ref_family],
            "evidence_refs": [
                f"live-gap-evidence:{provider_readback['gap_id']}:{ref_family}"
            ],
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        },
    )

    assert incomplete_identity["status"] == "typed_blocker_required"
    assert incomplete_identity["missing_transition_identity_ref_families"] == [
        ref_family
    ]
    assert incomplete_identity["transition_identity_ref_fields_present"] == [
        "study_id",
        "work_unit_fingerprint",
        "work_unit_id",
    ]


def test_live_runtime_gap_direct_evaluator_rejects_mismatched_gap_id() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_gap_work_orders"
    )
    contract = _contract()
    provider_readback = next(
        order
        for order in contract["work_orders"]
        if (
            "same_identity_opl_provider_admission_live_readback_ref"
            in order["acceptable_evidence_ref_families"]
        )
    )
    ref_family = "same_identity_opl_provider_admission_live_readback_ref"

    mismatched = work_orders.evaluate_live_runtime_gap_evidence_record(
        provider_readback,
        {
            "gap_id": "dhd_apply_exactly_one_live_outcome_when_explicitly_delegated",
            "evidence_source": "opl_live_readback:provider-admission:2026-06-20T00:00:00Z",
            "evidence_ref_families": [ref_family],
            "evidence_refs": [
                f"live-gap-evidence:{provider_readback['gap_id']}:{ref_family}"
            ],
            **_transition_identity(),
        },
    )

    assert mismatched["status"] == "typed_blocker_required"
    assert (
        mismatched["evidence_record_gap_id"]
        == "dhd_apply_exactly_one_live_outcome_when_explicitly_delegated"
    )
    assert mismatched["evidence_record_id_mismatch"] is True
    assert mismatched["matched_evidence_ref_families"] == [ref_family]
    assert mismatched["live_runtime_readiness_claim_allowed"] is False


def test_live_runtime_gap_intake_summary_requires_all_gap_evidence() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_gap_work_orders"
    )
    contract = _contract()

    empty = work_orders.live_runtime_gap_evidence_intake_summary(contract, [])
    assert empty["surface_kind"] == "mas_live_runtime_gap_evidence_intake_summary"
    assert empty["total_work_order_count"] == 5
    assert empty["typed_blocker_count"] == 5
    assert empty["satisfied_count"] == 0
    assert empty["repo_source_retirement_blocked"] is False
    assert empty["live_runtime_readiness_claim_allowed"] is False

    first_order = contract["work_orders"][0]
    partial = work_orders.live_runtime_gap_evidence_intake_summary(
        contract,
        [
            {
                "gap_id": first_order["gap_id"],
                "evidence_source": f"owner_readback:{first_order['gap_id']}",
                "evidence_ref_families": [first_order["acceptable_evidence_ref_families"][0]],
                "evidence_refs": [
                    (
                        "live-gap-evidence:"
                        f"{first_order['gap_id']}:"
                        f"{first_order['acceptable_evidence_ref_families'][0]}"
                    )
                ],
                **_transition_identity(),
            }
        ],
    )
    assert partial["satisfied_count"] == 1
    assert partial["typed_blocker_count"] == 4
    assert partial["live_runtime_readiness_claim_allowed"] is False

    false_claim = work_orders.live_runtime_gap_evidence_intake_summary(
        contract,
        [
            {
                "gap_id": first_order["gap_id"],
                "claim": "paper progress complete",
                "evidence_source": f"owner_readback:{first_order['gap_id']}",
                "evidence_ref_families": [first_order["acceptable_evidence_ref_families"][0]],
                "evidence_refs": [
                    (
                        "live-gap-evidence:"
                        f"{first_order['gap_id']}:"
                        f"{first_order['acceptable_evidence_ref_families'][0]}"
                    )
                ],
                **_transition_identity(),
            }
        ],
    )
    first_result = next(
        result for result in false_claim["results"] if result["gap_id"] == first_order["gap_id"]
    )
    assert first_result["status"] == "typed_blocker_required"
    assert first_result["forbidden_claim_terms_present"] == ["paper progress"]
    assert first_order["gap_id"] in false_claim["typed_blocker_gap_ids"]
    assert first_order["gap_id"] not in false_claim["satisfied_gap_ids"]

    complete_records = [_satisfying_gap_record(order) for order in contract["work_orders"]]
    complete = work_orders.live_runtime_gap_evidence_intake_summary(
        contract,
        complete_records,
    )
    assert complete["satisfied_count"] == 5
    assert complete["typed_blocker_count"] == 0
    assert complete["live_runtime_readiness_claim_allowed"] is True


def test_live_runtime_gap_intake_fails_closed_on_unknown_or_duplicate_records() -> None:
    work_orders = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_gap_work_orders"
    )
    contract = _contract()
    complete_records = [_satisfying_gap_record(order) for order in contract["work_orders"]]

    polluted = work_orders.live_runtime_gap_evidence_intake_summary(
        contract,
        [
            *complete_records,
            {
                **complete_records[0],
                "evidence_source": "owner_readback:duplicate",
            },
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
    assert polluted["duplicate_gap_ids"] == [complete_records[0]["gap_id"]]
    assert polluted["unknown_gap_ids"] == ["unknown_live_runtime_gap"]
    assert polluted["missing_gap_id_record_indexes"] == [7]
    assert polluted["malformed_record_indexes"] == [8]
    assert polluted["live_runtime_readiness_claim_allowed"] is False
    assert {
        "duplicate_live_runtime_gap_evidence_gap_id",
        "malformed_live_runtime_gap_evidence_record",
        "missing_live_runtime_gap_evidence_gap_id",
        "unknown_live_runtime_gap_evidence_gap_id",
    } == {violation["typed_blocker"] for violation in polluted["intake_violations"]}


def _satisfying_gap_record(order: dict) -> dict:
    ref_family = order["acceptable_evidence_ref_families"][0]
    record = {
        "gap_id": order["gap_id"],
        "evidence_source": f"owner_readback:{order['gap_id']}",
        "evidence_ref_families": [ref_family],
        "evidence_refs": [f"live-gap-evidence:{order['gap_id']}:{ref_family}"],
    }
    if ref_family == "MAS_owner_receipt_or_stable_typed_blocker_or_human_gate_or_route_back_ref":
        record["typed_blocker_ref"] = f"typed-blocker:{order['gap_id']}"
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
