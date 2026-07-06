from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_cli_cases.paper_mission_command_helpers import *  # noqa: F401,F403


def test_paper_mission_consume_candidate_typed_blocker_handoff_waits_for_authority(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = _write_profile_with_study(tmp_path)
    candidate_path = _write_candidate_manifest(
        tmp_path,
        requested_outcome="typed_blocker_required",
    )
    output_root = tmp_path / "consumption-ledger"

    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(candidate_path),
            "--output-root",
            str(output_root),
            "--profile",
            str(profile_path),
            "--study-id",
            "001-paper",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    output_manifest = payload["consume_output_manifest"]
    assert output_manifest["route_handoff_status"] == (
        "waiting_for_typed_blocker_authority"
    )
    assert output_manifest["route_command_kind"] == "resume_stage"
    handoff = json.loads(
        Path(output_manifest["opl_route_handoff_ref"]).read_text(encoding="utf-8")
    )
    assert handoff["handoff_status"] == "waiting_for_typed_blocker_authority"
    assert handoff["can_submit_to_opl_runtime"] is False
    assert handoff["can_claim_paper_progress"] is False
    assert handoff["authority_boundary"]["can_write_typed_blocker"] is False
    assert "typed blocker" in handoff["forbidden_authority_writes"]
    _assert_forbidden_authority_untouched(tmp_path)


def test_paper_mission_consume_candidate_picks_up_transaction_fields(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = _write_profile_with_study(tmp_path)
    mission_id = "paper-mission::001-paper::gate-clearing::manual"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id="001-paper",
    )
    candidate_path = _write_candidate_manifest(
        tmp_path,
        paper_mission_transaction=transaction,
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(candidate_path),
            "--dry-run",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-paper",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["transaction_state"] == "terminal_decision_recorded"
    assert payload["stage_terminal_decision"] == transaction["stage_terminal_decision"]
    assert payload["opl_route_command"] == transaction["opl_route_command"]
    assert payload["paper_mission_run_candidate"]["transaction_state"] == (
        "terminal_decision_recorded"
    )
    assert payload["paper_mission_transaction_readback"]["writes_authority"] is False
    assert payload["mutation_policy"]["writes_authority"] is False
    assert payload["authority_consume_readback"]["write_plan"]["written_files"] == []
    _assert_forbidden_authority_untouched(tmp_path)


def test_paper_mission_consume_candidate_route_back_readback_exposes_owner_answer_delta_ref(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = _write_profile_with_study(tmp_path)
    transaction = _paper_mission_transaction_payload(
        mission_id="paper-mission::001-paper::gate-clearing::manual",
        study_id="001-paper",
    )
    transaction["stage_terminal_decision"]["status"] = "route_back"
    transaction["stage_terminal_decision"]["reason"] = "domain_gate_pending"
    transaction["artifact_delta_refs"] = []
    candidate_path = _write_candidate_manifest(
        tmp_path,
        paper_mission_transaction=transaction,
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(candidate_path),
            "--dry-run",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-paper",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    owner_answer = payload["terminal_owner_gate_owner_answer_readback"]
    assert owner_answer["owner_answer_shape"] == "paper_facing_delta_ref"
    assert owner_answer["paper_facing_delta_ref"].startswith(
        "paper-facing-delta:owner-answer:001-paper:"
    )
    assert payload["route_back_budget"]["opl_redrive_budget_remaining"] == 0
    assert payload["mission_executor_fallback_action"]["default_action"] == (
        "materialize_submission_milestone_candidate"
    )
    assert payload["carry_forward_risk_receipt_ref"].startswith(
        "carry-forward-risk:paper-mission-owner-fallback:001-paper:"
    )
    assert payload["paper_mission_transaction"]["artifact_delta_refs"] == [
        {
            "ref_id": "paper_facing_delta_ref",
            "ref_kind": "paper_facing_delta_ref",
            "uri": owner_answer["paper_facing_delta_ref"],
        }
    ]
    assert payload["stage_terminal_decision"]["paper_facing_delta_ref"] == (
        owner_answer["paper_facing_delta_ref"]
    )
    assert owner_answer["write_plan"]["written_files"] == []
    assert payload["mutation_policy"]["writes_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path)
