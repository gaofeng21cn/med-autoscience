from __future__ import annotations

import importlib
import json
from pathlib import Path

from med_autoscience.controllers.paper_mission_receipt_owner_consumption import (
    latest_receipt_owner_consumption_readback,
)

from tests.test_cli_cases.paper_mission_command_cases.receipt_owner_consumption import (
    _readback,
)
from tests.test_cli_cases.paper_mission_command_helpers import _write_profile_with_study


def test_receipt_owner_consumption_apply_typed_blocker_writes_safe_consumption_ledger(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "dm002-readback.json"
    output_root = (
        tmp_path / "ops" / "medautoscience" / "paper_mission_receipt_owner_consumption"
    )
    readback_file.write_text(
        json.dumps(
            _readback(
                study_id=study_id,
                stage_outcome="typed_blocker",
                transition_kind=None,
                package_kind="current_package",
                can_submit=False,
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
            str(output_root),
            "--apply-typed-blocker",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    packet_ref = Path(payload["output_manifest"]["packet_ref"])
    packet = json.loads(packet_ref.read_text(encoding="utf-8"))
    latest = latest_receipt_owner_consumption_readback(
        workspace_root=tmp_path,
        study_id=study_id,
    )

    assert exit_code == 0
    assert payload["status"] == "owner_consumption_applied"
    assert payload["apply_mode"] == "typed_blocker"
    assert payload["authority_materialized"] is True
    assert payload["submission_ready_claim_authorized"] is False
    assert payload["output_manifest"]["writes_authority"] is True
    assert payload["output_manifest"]["writes_yang_authority"] is False
    assert payload["stage_closure_decision"]["outcome"]["kind"] == "typed_blocker"
    assert payload["stage_closure_decision"]["counts_as_typed_blocker"] is True
    assert payload["stage_closure_decision"]["authority_boundary"][
        "writes_owner_receipt"
    ] is False
    assert payload["stage_closure_decision"]["authority_boundary"][
        "writes_typed_blocker"
    ] is False
    assert payload["stage_closure_decision"]["authority_boundary"][
        "writes_human_gate"
    ] is False
    assert payload["stage_closure_decision"]["authority_boundary"][
        "writes_current_package"
    ] is False
    assert packet["status"] == "owner_consumption_applied"
    assert latest is not None
    assert latest["source_ref"] == str(packet_ref)


def test_receipt_owner_consumption_apply_route_checkpoint_records_checkpoint_not_submission_ready(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "dm003-readback.json"
    output_root = (
        tmp_path / "ops" / "medautoscience" / "paper_mission_receipt_owner_consumption"
    )
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
            str(output_root),
            "--apply-route-checkpoint",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "owner_consumption_applied"
    assert payload["current_package"]["package_kind"] == "submission_ready_package"
    assert payload["current_package"]["can_submit"] is True
    assert payload["submission_ready_claim_authorized"] is False
    assert payload["owner_consumption_verdict"]["can_claim_submission_ready"] is False
    assert payload["stage_closure_decision"]["outcome"]["kind"] == "next_stage_transition"
    assert payload["stage_closure_decision"]["outcome"]["transition_kind"] == (
        "route_back_candidate_checkpoint"
    )
    assert payload["stage_closure_decision"]["counts_as_typed_blocker"] is False
    assert payload["mas_receipt_consumption"]["status"] == (
        "owner_consumed_route_checkpoint"
    )
    assert payload["mas_receipt_consumption"]["owner_result_kind"] == "route_checkpoint"
    assert payload["stage_closure"]["outcome_kind"] == "next_stage_transition"
    assert payload["stage_closure"]["transition_kind"] == "route_back_candidate_checkpoint"
    assert payload["stage_closure"]["durable_stop_allowed"] is False
    assert payload["stage_closure_decision"]["outcome"]["can_submit"] is True
    assert payload["stage_closure_decision"]["authority_boundary"][
        "writes_current_package"
    ] is False
