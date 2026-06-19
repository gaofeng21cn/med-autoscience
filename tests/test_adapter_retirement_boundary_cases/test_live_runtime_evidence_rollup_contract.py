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
    assert readback["summary"]["total_work_order_count"] == 12
    assert readback["summary"]["typed_blocker_count"] == 12
    assert readback["summary"]["rollup_result_status"] == "typed_blocker_required"
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
    assert complete["rollup_result_status"] == "all_work_orders_satisfied"


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
    assert output["summary"]["rollup_result_status"] == "typed_blocker_required"
    assert output["completion_claim_allowed"] is False


def test_live_runtime_evidence_rollup_cli_consumes_evidence_files(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
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
    assert output["completion_claim_allowed"] is True
