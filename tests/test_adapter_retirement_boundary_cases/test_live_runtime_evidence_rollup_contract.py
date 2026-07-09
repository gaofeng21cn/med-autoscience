from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
LIVE_TAIL_PATH = (
    REPO_ROOT / "contracts" / "runtime" / "mas-runtime-live-tail-work-orders.json"
)
LIVE_GAP_PATH = (
    REPO_ROOT / "contracts" / "runtime" / "mas-live-runtime-gap-work-orders.json"
)
ROLLUP_PATH = (
    REPO_ROOT / "contracts" / "runtime" / "mas-live-runtime-evidence-rollup.json"
)


def _module():
    return importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement.live_runtime_evidence_rollup"
    )


def _live_tail_contract() -> dict:
    return json.loads(LIVE_TAIL_PATH.read_text(encoding="utf-8"))


def _live_gap_contract() -> dict:
    return json.loads(LIVE_GAP_PATH.read_text(encoding="utf-8"))


def _rollup_contract() -> dict:
    return json.loads(ROLLUP_PATH.read_text(encoding="utf-8"))


def test_live_runtime_evidence_rollup_contract_matches_tail_and_gap_work_orders() -> None:
    rollup = _module()
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
    assert rollup_contract["repo_source_retirement_completion"]["status"] == "complete"
    assert (
        rollup_contract["repo_source_retirement_completion"][
            "does_not_satisfy_live_runtime_work_orders"
        ]
        is True
    )
    assert rollup_contract["evidence_record_templates_readback"][
        "templates_can_satisfy_work_orders"
    ] is False
    assert rollup_contract["owner_handoff_readback"][
        "handoff_is_action_authorization"
    ] is False
    assert rollup_contract["evidence_bundle_intake"][
        "bundle_can_satisfy_work_orders_without_records"
    ] is False
    boundary = rollup_contract["completion_claim_boundary"]
    assert boundary[
        "live_runtime_readiness_claim_requires_all_tail_and_gap_work_orders_satisfied"
    ] is True
    assert boundary["docs_tests_inventory_or_queue_empty_can_satisfy_rollup"] is False
    assert boundary["unknown_or_duplicate_evidence_records_can_satisfy_rollup"] is False
    assert boundary["forbidden_or_unaccepted_evidence_source_can_satisfy_rollup"] is False
    assert rollup_contract["live_tail_surface_ids"] == sorted(
        order["surface_id"] for order in tail_contract["work_orders"]
    )
    assert rollup_contract["live_runtime_gap_ids"] == sorted(
        order["gap_id"] for order in gap_contract["work_orders"]
    )


def test_live_runtime_evidence_rollup_summary_requires_all_records() -> None:
    rollup = _module()
    tail_contract = _live_tail_contract()
    gap_contract = _live_gap_contract()
    tail_records = [_tail_record(order) for order in tail_contract["work_orders"]]
    gap_records = [_gap_record(order) for order in gap_contract["work_orders"]]

    empty = rollup.live_runtime_evidence_rollup_summary(
        live_tail_contract=tail_contract,
        live_runtime_gap_contract=gap_contract,
    )
    assert empty["total_work_order_count"] == 12
    assert empty["satisfied_count"] == 0
    assert empty["typed_blocker_count"] == 12
    assert empty["repo_source_retirement_blocked"] is False
    assert empty["live_runtime_readiness_claim_allowed"] is False
    assert empty["rollup_result_status"] == "typed_blocker_required"
    assert empty["repo_source_retirement_completion"]["status"] == "complete"
    assert empty["repo_source_retirement_completion"][
        "live_runtime_readiness_claim_allowed"
    ] is False

    partial = rollup.live_runtime_evidence_rollup_summary(
        live_tail_contract=tail_contract,
        live_runtime_gap_contract=gap_contract,
        live_tail_evidence_records=tail_records[:1],
        live_runtime_gap_evidence_records=gap_records[:1],
    )
    assert partial["satisfied_count"] == 2
    assert partial["typed_blocker_count"] == 10
    assert partial["live_runtime_readiness_claim_allowed"] is False

    complete = rollup.live_runtime_evidence_rollup_summary(
        live_tail_contract=tail_contract,
        live_runtime_gap_contract=gap_contract,
        live_tail_evidence_records=tail_records,
        live_runtime_gap_evidence_records=gap_records,
    )
    assert complete["satisfied_count"] == 12
    assert complete["typed_blocker_count"] == 0
    assert complete["intake_violation_count"] == 0
    assert complete["live_runtime_readiness_claim_allowed"] is True
    assert complete["rollup_result_status"] == "all_work_orders_satisfied"


def test_live_runtime_evidence_templates_and_bundle_are_not_evidence() -> None:
    rollup = _module()
    tail_contract = _live_tail_contract()
    gap_contract = _live_gap_contract()
    summary = rollup.live_runtime_evidence_rollup_summary(
        live_tail_contract=tail_contract,
        live_runtime_gap_contract=gap_contract,
    )
    templates = summary["evidence_record_templates"]
    template_bundle = summary["evidence_bundle_template"]
    tail_bundle_records, gap_bundle_records = rollup.evidence_records_from_bundle(
        template_bundle
    )

    attempts = [
        rollup.live_runtime_evidence_rollup_summary(
            live_tail_contract=tail_contract,
            live_runtime_gap_contract=gap_contract,
            live_tail_evidence_records=[
                item for item in templates if item["work_order_kind"] == "live_tail"
            ],
            live_runtime_gap_evidence_records=[
                item for item in templates if item["work_order_kind"] == "live_runtime_gap"
            ],
        ),
        rollup.live_runtime_evidence_rollup_summary(
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
        ),
        rollup.live_runtime_evidence_rollup_summary(
            live_tail_contract=tail_contract,
            live_runtime_gap_contract=gap_contract,
            live_tail_evidence_records=tail_bundle_records,
            live_runtime_gap_evidence_records=gap_bundle_records,
        ),
    ]
    assert all(attempt["satisfied_count"] == 0 for attempt in attempts)
    assert all(attempt["typed_blocker_count"] == 12 for attempt in attempts)
    assert all(
        attempt["live_runtime_readiness_claim_allowed"] is False
        for attempt in attempts
    )
    assert template_bundle["bundle_is_evidence_record"] is False
    assert template_bundle["bundle_can_satisfy_work_orders_without_filled_records"] is False


def test_live_runtime_evidence_rollup_fails_closed_on_bad_intake_records() -> None:
    rollup = _module()
    tail_contract = _live_tail_contract()
    gap_contract = _live_gap_contract()
    tail_records = [_tail_record(order) for order in tail_contract["work_orders"]]
    gap_records = [_gap_record(order) for order in gap_contract["work_orders"]]

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
            {"evidence_source": "owner_readback:missing-id"},
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
            {"evidence_source": "owner_readback:missing-id"},
            "malformed-record",
        ],
    )
    assert polluted["satisfied_count"] == 12
    assert polluted["typed_blocker_count"] == 8
    assert polluted["intake_violation_count"] == 8
    assert polluted["rollup_result_status"] == "typed_blocker_required"

    tail_records[0]["evidence_source"] = "focused_tests"
    gap_records[0]["evidence_source"] = "scripts_verify"
    forbidden_sources = rollup.live_runtime_evidence_rollup_summary(
        live_tail_contract=tail_contract,
        live_runtime_gap_contract=gap_contract,
        live_tail_evidence_records=tail_records,
        live_runtime_gap_evidence_records=gap_records,
    )
    assert forbidden_sources["satisfied_count"] == 10
    assert forbidden_sources["typed_blocker_count"] == 2
    assert forbidden_sources["live_runtime_readiness_claim_allowed"] is False


def test_live_runtime_evidence_rollup_rejects_missing_required_refs() -> None:
    rollup = _module()
    tail_contract = _live_tail_contract()
    gap_contract = _live_gap_contract()
    tail_records = [_tail_record(order) for order in tail_contract["work_orders"]]
    gap_records = [_gap_record(order) for order in gap_contract["work_orders"]]
    tail_records[0].pop("evidence_refs")
    authority_gap = next(
        order
        for order in gap_contract["work_orders"]
        if "MAS_owner_receipt_or_stable_typed_blocker_or_human_gate_or_route_back_ref"
        in order["acceptable_evidence_ref_families"]
    )
    gap_records = [
        _gap_record(order)
        for order in gap_contract["work_orders"]
        if order["gap_id"] != authority_gap["gap_id"]
    ] + [
        {
            "gap_id": authority_gap["gap_id"],
            "evidence_source": f"owner_readback:{authority_gap['gap_id']}",
            "evidence_ref_families": [
                "MAS_owner_receipt_or_stable_typed_blocker_or_human_gate_or_route_back_ref"
            ],
            **_transition_identity_refs(),
        }
    ]

    summary = rollup.live_runtime_evidence_rollup_summary(
        live_tail_contract=tail_contract,
        live_runtime_gap_contract=gap_contract,
        live_tail_evidence_records=tail_records,
        live_runtime_gap_evidence_records=gap_records,
    )

    assert summary["rollup_result_status"] == "typed_blocker_required"
    assert summary["typed_blocker_count"] == 2
    tail_result = next(
        item
        for item in summary["live_tail"]["results"]
        if item["surface_id"] == tail_records[0]["surface_id"]
    )
    gap_result = next(
        item
        for item in summary["live_runtime_gaps"]["results"]
        if item["gap_id"] == authority_gap["gap_id"]
    )
    assert tail_result["missing_concrete_evidence_ref_families"]
    assert gap_result["missing_authority_outcome_ref_families"] == [
        "MAS_owner_receipt_or_stable_typed_blocker_or_human_gate_or_route_back_ref"
    ]


def test_live_runtime_evidence_rollup_cli_readback_and_evidence_files(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    tail_contract = _live_tail_contract()
    gap_contract = _live_gap_contract()
    tail_records = [_tail_record(order) for order in tail_contract["work_orders"]]
    gap_records = [_gap_record(order) for order in gap_contract["work_orders"]]

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
    readback = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert readback["contract_validation"]["status"] == "passed"
    assert readback["summary"]["rollup_result_status"] == "typed_blocker_required"
    assert readback["completion_claim_allowed"] is False

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
    split_output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert split_output["summary"]["rollup_result_status"] == "all_work_orders_satisfied"
    assert split_output["completion_claim_allowed"] is True

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
    bundle_output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert bundle_output["summary"]["satisfied_count"] == 12
    assert bundle_output["summary"]["typed_blocker_count"] == 0
    assert bundle_output["completion_claim_allowed"] is True


def test_live_runtime_evidence_rollup_cli_rejects_bad_bundle_inputs(
    tmp_path: Path,
) -> None:
    rollup = _module()
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


def _gap_record(order: dict) -> dict:
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


def _tail_record(order: dict) -> dict:
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
