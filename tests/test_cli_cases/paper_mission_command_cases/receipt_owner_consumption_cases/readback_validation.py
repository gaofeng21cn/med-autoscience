from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_cli_cases.paper_mission_command_helpers import _write_profile_with_study
from tests.test_cli_cases.paper_mission_command_cases.receipt_owner_consumption_cases.shared import (
    readback as _readback,
)


def test_receipt_owner_consumption_keeps_dm003_submission_ready_mirror_non_terminal(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "dm003-readback.json"
    readback_file.write_text(
        json.dumps(
            _readback(
                study_id=study_id,
                stage_outcome="next_stage_transition",
                transition_kind="route_back_candidate_checkpoint",
                package_kind="submission_ready_package",
                can_submit=True,
            )
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "receipt-owner-consumption",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--paper-mission-readback-file",
            str(readback_file),
            "--output-root",
            str(tmp_path / "receipt-owner-consumption"),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["current_package"]["package_kind"] == "submission_ready_package"
    assert payload["current_package"]["can_submit"] is True
    assert payload["owner_consumption_verdict"]["verdict_kind"] == (
        "consume_route_back_checkpoint_owner_consumption_required"
    )
    assert payload["owner_consumption_verdict"]["can_claim_submission_ready"] is False
    assert payload["owner_consumption_verdict"]["durable_stop_allowed"] is False
    assert payload["output_manifest"]["writes_authority"] is False
    packet_ref = Path(payload["output_manifest"]["packet_ref"])
    assert packet_ref.exists()
    assert json.loads(packet_ref.read_text(encoding="utf-8"))[
        "submission_ready_claim_authorized"
    ] is False


def test_receipt_owner_consumption_fails_closed_without_opl_receipt(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "missing-receipt.json"
    readback_file.write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_materialized_readback",
                "study_id": study_id,
                "stage_closure_decision": {"outcome": {"kind": "typed_blocker"}},
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "receipt-owner-consumption",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--paper-mission-readback-file",
            str(readback_file),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "blocked_missing_consumable_opl_receipt"
    assert payload["readback_validation"]["missing_required_fields"] == [
        "opl_runtime_carrier_readback",
        "opl_runtime_carrier_readback.opl_transition_receipt",
        "opl_runtime_carrier_readback.receipt_evidence",
        "opl_runtime_carrier_readback.mas_receipt_consumption",
    ]
    assert payload["implementation_gap"]["gap_kind"] == (
        "mas_owner_consumption_authority_apply_surface_missing"
    )


def test_receipt_owner_consumption_accepts_top_level_receipt_projection(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback = _readback(
        study_id=study_id,
        stage_outcome="typed_blocker",
        transition_kind=None,
        package_kind="current_package",
        can_submit=False,
    )
    carrier = readback["opl_runtime_carrier_readback"]
    assert isinstance(carrier, dict)
    readback["receipt_evidence"] = carrier.pop("receipt_evidence")
    readback["opl_transition_receipt"] = carrier.pop("opl_transition_receipt")
    readback["mas_receipt_consumption"] = carrier.pop("mas_receipt_consumption")
    readback_file = tmp_path / "top-level-receipt.json"
    readback_file.write_text(json.dumps(readback), encoding="utf-8")

    exit_code = cli.main(
        [
            "paper-mission",
            "receipt-owner-consumption",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--paper-mission-readback-file",
            str(readback_file),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "owner_consumption_evidence_materialized"
    assert payload["readback_validation"]["valid"] is True
    assert payload["owner_consumption_verdict"]["required_authority_surface_exists"] is True


def test_receipt_owner_consumption_accepts_already_owner_consumed_route_checkpoint_readback(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "dm003-owner-consumed-readback.json"
    readback = _readback(
        study_id=study_id,
        stage_outcome="next_stage_transition",
        transition_kind="route_back_candidate_checkpoint",
        package_kind="current_package",
        can_submit=False,
    )
    carrier = readback["opl_runtime_carrier_readback"]
    checkpoint_ref = (
        "ops/medautoscience/paper_mission_stage_attempts/"
        "sat-receipt/stage_attempt_closeout_packet.json"
    )
    carrier["mas_receipt_consumption"].update(
        {
            "status": "owner_consumed_route_checkpoint",
            "owner_result_kind": "route_checkpoint",
            "route_checkpoint_evidence_ref": checkpoint_ref,
        }
    )
    readback_file.write_text(json.dumps(readback), encoding="utf-8")

    exit_code = cli.main(
        [
            "paper-mission",
            "receipt-owner-consumption",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--paper-mission-readback-file",
            str(readback_file),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "owner_consumption_already_materialized"
    assert payload["readback_validation"]["valid"] is True
    assert payload["readback_validation"]["observed_consumption_status"] == (
        "owner_consumed_route_checkpoint"
    )
    assert payload["owner_consumption_already_materialized"] is True
    assert payload["mas_receipt_consumption"]["status"] == (
        "owner_consumed_route_checkpoint"
    )

    output_root = (
        tmp_path / "ops" / "medautoscience" / "paper_mission_receipt_owner_consumption"
    )
    exit_code = cli.main(
        [
            "paper-mission",
            "receipt-owner-consumption",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--paper-mission-readback-file",
            str(readback_file),
            "--output-root",
            str(output_root),
            "--apply-route-checkpoint",
            "--format",
            "json",
        ]
    )
    applied = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert applied["status"] == "owner_consumption_applied"
    assert applied["apply_mode"] == "route_checkpoint"
    assert applied["readback_validation"]["valid"] is True
    assert applied["mas_receipt_consumption"]["status"] == (
        "owner_consumed_route_checkpoint"
    )
