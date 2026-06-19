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
            "evidence_substitutes": [
                "provider_admission_same_identity_replay_as_fresh_opl_readback"
            ],
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

    complete_records = [
        {
            "gap_id": order["gap_id"],
            "evidence_source": f"owner_readback:{order['gap_id']}",
            "evidence_ref_families": [order["acceptable_evidence_ref_families"][0]],
        }
        for order in contract["work_orders"]
    ]
    complete = work_orders.live_runtime_gap_evidence_intake_summary(
        contract,
        complete_records,
    )
    assert complete["satisfied_count"] == 5
    assert complete["typed_blocker_count"] == 0
    assert complete["live_runtime_readiness_claim_allowed"] is True
