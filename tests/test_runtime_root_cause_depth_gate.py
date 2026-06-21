from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "contracts" / "runtime" / "mas-root-cause-depth-gate.json"


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_root_cause_depth_gate_contract_validates_required_boundaries() -> None:
    gate = importlib.import_module("med_autoscience.runtime_protocol.root_cause_depth_gate")
    contract = _contract()

    assert gate.validate_root_cause_depth_gate_contract(contract) == []
    assert contract["surface_kind"] == "mas_root_cause_depth_gate"
    assert contract["required_report_fields"] == [
        "symptom",
        "failing_boundary",
        "root_cause",
        "owner_surface",
        "fix_or_next_action",
        "proof",
    ]
    assert contract["minimum_depth_by_context"]["supervisor_heartbeat"] == "L3_owner_repair_path"
    assert contract["minimum_depth_by_context"]["repair_lane_proposal"] == "L3_owner_repair_path"
    assert (
        contract["minimum_depth_by_context"]["thorough_root_cause_request"]
        == "L4_prevention_writeback"
    )
    assert "blocked" in contract["symptom_only_statuses"]
    assert "current_owner_identity_unavailable_for_guard" in contract["symptom_only_statuses"]
    assert "owner_consumption_saturation_wait" in contract["symptom_only_statuses"]
    assert (
        "candidate_absorption_as_owner_path_unblocked"
        in contract["forbidden_completion_interpretations"]
    )
    assert (
        "current_owner_identity_unavailable_for_guard_as_owner_path_repaired"
        in contract["forbidden_completion_interpretations"]
    )
    assert (
        contract["repair_lane_claim_boundary"][
            "cannot_claim_owner_path_unblocked_from_guardrail_only_fix"
        ]
        is True
    )
    assert (
        contract["completion_claim_boundary"][
            "root_cause_depth_gate_validation_can_claim_paper_progress"
        ]
        is False
    )
    assert (
        contract["completion_claim_boundary"]["guardrail_only_fix_can_claim_owner_path_unblocked"]
        is False
    )


def test_root_cause_depth_gate_rejects_symptom_only_report() -> None:
    gate = importlib.import_module("med_autoscience.runtime_protocol.root_cause_depth_gate")
    contract = _contract()
    bad_record = {
        "context": "repair_lane_proposal",
        "symptom": "current_owner_identity_unavailable_for_guard",
        "failing_boundary": "current_owner_identity_unavailable_for_guard",
        "root_cause": "current_owner_identity_unavailable_for_guard",
        "owner_surface": "MAS owner precheck",
        "fix_or_next_action": "add guarded no-write precheck",
        "proof": {
            "evidence_refs": ["dhd-dry-run:/tmp/b002-owner-precheck.json"],
            "proves": "no forbidden files were written",
            "does_not_prove": "B002 owner path is unblocked",
        },
    }

    summary = gate.root_cause_depth_gate_audit_summary(contract, [bad_record])

    assert summary["result_status"] == "typed_blocker_required"
    assert summary["typed_blocker_count"] == 1
    assert summary["all_records_closeout_eligible"] is False
    assert summary["results"][0]["status"] == "typed_blocker_required"
    assert "root_cause_repeats_symptom" in summary["results"][0]["reasons"]
    assert "root_cause_is_symptom_only_status" in summary["results"][0]["reasons"]


def test_root_cause_depth_gate_accepts_l3_owner_repair_path_report() -> None:
    gate = importlib.import_module("med_autoscience.runtime_protocol.root_cause_depth_gate")
    contract = _contract()
    record = {
        "context": "repair_lane_proposal",
        "symptom": "owner_consumption_saturation_wait",
        "failing_boundary": "MAS owner-consumption precheck cannot bind current owner identity",
        "root_cause": (
            "current_owner_delta and current_work_unit readback do not expose the identity "
            "field consumed by the guarded owner precheck"
        ),
        "owner_surface": "MAS study_progress current owner projection",
        "fix_or_next_action": (
            "repair the current owner identity projection or emit a MAS typed blocker with "
            "the missing identity ref family"
        ),
        "proof": {
            "evidence_refs": [
                "study-progress:/tmp/b002-progress.json",
                "dhd-dry-run:/tmp/b002-dhd.json",
            ],
            "proves": "the current identity is absent from the read model consumed by precheck",
            "does_not_prove": "paper progress or publication readiness",
        },
    }

    summary = gate.root_cause_depth_gate_audit_summary(contract, [record])

    assert summary["result_status"] == "closeout_eligible"
    assert summary["closeout_eligible_count"] == 1
    assert summary["typed_blocker_count"] == 0
    assert summary["all_records_closeout_eligible"] is True
    assert summary["results"][0]["depth"] == "L3_owner_repair_path"


def test_root_cause_depth_gate_cli_outputs_readback_json(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    exit_code = cli.main(
        [
            "doctor",
            "root-cause-depth-gate",
            "--repo-root",
            str(REPO_ROOT),
            "--format",
            "json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["surface_kind"] == "mas_root_cause_depth_gate_readback"
    assert output["contract_refs"] == {
        "root_cause_depth_gate": "contracts/runtime/mas-root-cause-depth-gate.json",
    }
    assert output["contract_validation"]["status"] == "passed"
    assert output["audit_summary"]["result_status"] == "no_audit_records"
    assert output["completion_claim_allowed"] is False
    assert output["paper_progress_claim_allowed"] is False
    assert output["runtime_readiness_claim_allowed"] is False


def test_root_cause_depth_gate_cli_consumes_audit_record_file(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    records = [
        {
            "context": "candidate_absorption",
            "symptom": "blocked",
            "failing_boundary": "blocked",
            "root_cause": "blocked",
            "owner_surface": "repair lane",
            "fix_or_next_action": "absorb candidate",
            "proof": {
                "evidence_refs": ["focused-tests:pytest"],
                "proves": "focused tests passed",
                "does_not_prove": "owner path unblocked",
            },
        }
    ]
    record_file = tmp_path / "audit-records.json"
    record_file.write_text(json.dumps(records), encoding="utf-8")

    exit_code = cli.main(
        [
            "doctor",
            "root-cause-depth-gate",
            "--repo-root",
            str(REPO_ROOT),
            "--audit-record-file",
            str(record_file),
            "--format",
            "json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["audit_summary"]["result_status"] == "typed_blocker_required"
    assert output["audit_summary"]["typed_blocker_count"] == 1
    assert output["completion_claim_allowed"] is False
