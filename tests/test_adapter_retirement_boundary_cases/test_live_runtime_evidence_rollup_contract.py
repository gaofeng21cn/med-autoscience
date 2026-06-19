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
    assert rollup_contract["live_runtime_readiness_claim_allowed"] is False
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
    assert empty["repo_source_retirement_blocked"] is False
    assert empty["live_runtime_readiness_claim_allowed"] is False

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
            }
        ],
        live_runtime_gap_evidence_records=[
            {
                "gap_id": one_gap["gap_id"],
                "evidence_source": f"owner_readback:{one_gap['gap_id']}",
                "evidence_ref_families": [one_gap["acceptable_evidence_ref_families"][0]],
            }
        ],
    )
    assert partial["satisfied_count"] == 2
    assert partial["typed_blocker_count"] == 10
    assert partial["live_runtime_readiness_claim_allowed"] is False
    assert one_tail["surface_id"] in partial["satisfied_surface_ids"]
    assert one_gap["gap_id"] in partial["satisfied_gap_ids"]


def test_live_runtime_evidence_rollup_requires_all_tail_and_gap_records() -> None:
    rollup = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.live_runtime_evidence_rollup"
    )
    tail_contract = _live_tail_contract()
    gap_contract = _live_gap_contract()
    tail_records = [
        {
            "surface_id": order["surface_id"],
            "evidence_source": f"owner_readback:{order['surface_id']}",
            "evidence_ref_families": [order["acceptable_evidence_ref_families"][0]],
        }
        for order in tail_contract["work_orders"]
    ]
    gap_records = [
        {
            "gap_id": order["gap_id"],
            "evidence_source": f"owner_readback:{order['gap_id']}",
            "evidence_ref_families": [order["acceptable_evidence_ref_families"][0]],
        }
        for order in gap_contract["work_orders"]
    ]

    complete = rollup.live_runtime_evidence_rollup_summary(
        live_tail_contract=tail_contract,
        live_runtime_gap_contract=gap_contract,
        live_tail_evidence_records=tail_records,
        live_runtime_gap_evidence_records=gap_records,
    )
    assert complete["total_work_order_count"] == 12
    assert complete["satisfied_count"] == 12
    assert complete["typed_blocker_count"] == 0
    assert complete["live_runtime_readiness_claim_allowed"] is True
