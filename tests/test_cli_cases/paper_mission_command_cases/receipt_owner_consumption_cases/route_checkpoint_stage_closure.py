from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

from med_autoscience.controllers.paper_mission_receipt_owner_consumption import (
    latest_receipt_owner_consumption_readback,
    materialize_receipt_owner_consumption,
)

from tests.test_cli_cases.paper_mission_command_cases.receipt_owner_consumption import (
    _readback,
)
from tests.test_cli_cases.paper_mission_command_helpers import _write_profile_with_study


def test_receipt_owner_consumption_route_checkpoint_supersedes_stale_typed_blocker_action(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "obesity-readback.json"
    output_root = (
        tmp_path / "ops" / "medautoscience" / "paper_mission_receipt_owner_consumption"
    )
    readback_file.write_text(
        json.dumps(
            _readback(
                study_id=study_id,
                stage_outcome="next_stage_transition",
                transition_kind="route_back_candidate_checkpoint",
                package_kind="current_package",
                can_submit=False,
                consumption_next_legal_action="record_typed_blocker",
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
    packet_ref = output_root / study_id / "receipt_owner_consumption.json"
    latest = latest_receipt_owner_consumption_readback(
        workspace_root=tmp_path,
        study_id=study_id,
    )

    assert exit_code == 0
    assert payload["status"] == "owner_consumption_applied"
    assert payload["apply_mode"] == "route_checkpoint"
    assert payload["owner_consumption_verdict"]["verdict_kind"] == (
        "consume_route_back_checkpoint_owner_consumption_required"
    )
    assert payload["owner_consumption_verdict"]["required_authority_surface"] == (
        "paper-mission receipt-owner-consumption --apply-route-checkpoint"
    )
    assert payload["stage_closure_decision"]["outcome"]["kind"] == "next_stage_transition"
    assert payload["stage_closure_decision"]["outcome"]["transition_kind"] == (
        "route_back_candidate_checkpoint"
    )
    assert payload["stage_closure_decision"]["counts_as_typed_blocker"] is False
    assert payload["stage_closure"]["outcome_kind"] == "next_stage_transition"
    assert payload["stage_closure"]["transition_kind"] == "route_back_candidate_checkpoint"
    assert payload["submission_ready_claim_authorized"] is False
    assert packet_ref.exists()
    assert latest is not None
    assert latest["source_ref"] == str(packet_ref)
    assert latest["stage_closure_decision"]["outcome"]["transition_kind"] == (
        "route_back_candidate_checkpoint"
    )


def test_receipt_owner_consumption_prefers_stage_closure_ledger_route_checkpoint_over_stale_top_level_typed_blocker(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "obesity-readback.json"
    readback = _readback(
        study_id=study_id,
        stage_outcome="typed_blocker",
        transition_kind=None,
        package_kind="current_package",
        can_submit=False,
        consumption_next_legal_action="record_typed_blocker",
    )
    readback["paper_mission_stage_closure_ledger_readback"] = {
        "decision_ref": f"mas://paper-mission/{study_id}/newer-stage-closure",
        "outcome": {
            "kind": "next_stage_transition",
            "transition_kind": "route_back_candidate_checkpoint",
            "next_action": "consume_route_back_checkpoint_or_materialize_terminalizer_outcome",
        },
    }
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
            "--apply-route-checkpoint",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "owner_consumption_applied"
    assert payload["owner_consumption_verdict"]["verdict_kind"] == (
        "consume_route_back_checkpoint_owner_consumption_required"
    )
    assert payload["stage_closure"]["outcome_kind"] == "next_stage_transition"
    assert payload["stage_closure"]["transition_kind"] == "route_back_candidate_checkpoint"
    assert payload["mas_receipt_consumption"]["owner_result_kind"] == "route_checkpoint"


def test_receipt_owner_consumption_route_checkpoint_uses_domain_transition_successor_identity() -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    payload = materialize_receipt_owner_consumption(
        paper_mission_readback={
            **_readback(
                study_id=study_id,
                stage_outcome="next_stage_transition",
                transition_kind="route_back_candidate_checkpoint",
                package_kind="current_package",
                can_submit=False,
            ),
            "stage_closure_decision": {
                "decision_ref": f"mas://paper-mission/{study_id}/stage-closure",
                "stage_id": "review",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                "opl_closeout": {
                    "stage_attempt_id": "sat-review",
                    "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                },
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "route_back_candidate_checkpoint",
                    "next_action": "consume_route_back_checkpoint_or_materialize_terminalizer_outcome",
                    "route_checkpoint_evidence_ref": (
                        "ops/medautoscience/paper_mission_stage_attempts/"
                        "sat-review/stage_attempt_closeout_packet.json"
                    ),
                },
            },
            "domain_transition": {
                "route_target": "write",
                "next_work_unit": {
                    "unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
                },
                "next_action": {
                    "stage_id": "write",
                    "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
                },
            },
        },
        study_id=study_id,
        profile_ref="/tmp/dm003.local.toml",
        apply_mode="route_checkpoint",
        source="pytest",
    )

    assert payload["status"] == "owner_consumption_applied"
    assert payload["stage_closure_decision"]["stage_id"] == "write"
    assert payload["stage_closure_decision"]["work_unit_id"] == (
        "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
    )


def test_receipt_owner_consumption_route_checkpoint_succeeds_from_stage_closure_only_readback(
    tmp_path: Path,
) -> None:
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = tmp_path / "workspace" / "studies" / study_id
    study_root.mkdir(parents=True)
    payload = materialize_receipt_owner_consumption(
        paper_mission_readback={
            **_readback(
                study_id=study_id,
                stage_outcome="next_stage_transition",
                transition_kind="route_back_candidate_checkpoint",
                package_kind="current_package",
                can_submit=False,
            ),
            "study_root": str(study_root),
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "action_family": "paper.stage_closure.owner_consumption",
                "action_kind": "owner_consumption",
                "action_type": "consume_route_back_checkpoint_or_materialize_terminalizer_outcome",
                "owner": "MedAutoScience",
                "outcome_ref": "ops/medautoscience/paper_mission_stage_closure/dm002.json",
            },
            "stage_closure_decision": {
                "decision_ref": f"mas://paper-mission/{study_id}/stage-closure",
                "stage_id": "write",
                "work_unit_id": "dm002_after_story_repair_medical_prose_hardening",
                "opl_closeout": {
                    "status": "opl_runtime_terminal_readback_observed",
                    "stage_attempt_id": "sat-dm002-write",
                    "work_unit_id": "dm002_after_story_repair_medical_prose_hardening",
                },
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "route_back_candidate_checkpoint",
                    "next_action": "consume_route_back_checkpoint_or_materialize_terminalizer_outcome",
                },
            },
            "opl_runtime_carrier_readback": {
                "surface_kind": "paper_mission_opl_runtime_carrier_readback",
                "carrier_status": "waiting_for_opl_runtime_live_readback",
                "runtime_readback_status": "terminal_closeout_superseded",
                "dispatch_status": "transition_request_pending",
                "domain_ready_verdict": "authority_consumed_candidate_supersedes_terminal_closeout",
                "can_claim_paper_progress": False,
            },
        },
        study_id=study_id,
        profile_ref="/tmp/dm002.local.toml",
        output_root=tmp_path / "receipt-owner-consumption",
        apply_mode="route_checkpoint",
        source="pytest",
    )

    assert payload["status"] == "owner_consumption_applied"
    assert payload["mas_receipt_consumption"]["status"] == (
        "owner_consumed_route_checkpoint"
    )
    assert payload["receipt_evidence"]["route_checkpoint_evidence_ref"].endswith(
        "sat-dm002-write/stage_attempt_closeout_packet.json"
    )


def test_receipt_owner_consumption_apply_mode_mismatch_fails_closed(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "dm002-readback.json"
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
            "--apply-route-checkpoint",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "blocked_apply_mode_mismatch"
    assert payload["write_permitted"] is False
    assert payload["authority_materialized"] is False
    assert payload["requested_apply_mode"] == "route_checkpoint"
    assert payload["expected_apply_mode"] == "typed_blocker"


def test_receipt_owner_consumption_route_checkpoint_uses_current_receipt_identity(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "dm003-current-receipt-readback.json"
    readback = _readback(
        study_id=study_id,
        stage_outcome="next_stage_transition",
        transition_kind="route_back_candidate_checkpoint",
        package_kind="current_package",
        can_submit=False,
    )
    readback["stage_closure_decision"]["stage_id"] = "review"
    readback["stage_closure_decision"]["work_unit_id"] = (
        "ai_reviewer_medical_prose_quality_review"
    )
    readback["stage_closure_decision"]["opl_closeout"] = {
        "status": "opl_runtime_terminal_readback_observed",
        "stage_attempt_id": "sat-stale-review",
        "work_unit_id": "ai_reviewer_medical_prose_quality_review",
    }
    receipt = readback["opl_runtime_carrier_readback"]["opl_transition_receipt"]
    receipt["stage_attempt_id"] = "sat-current-write"
    receipt["route_target"] = "write"
    receipt["work_unit_id"] = "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
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
            "--apply-route-checkpoint",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "owner_consumption_applied"
    assert payload["stage_closure_decision"]["stage_id"] == "write"
    assert payload["stage_closure_decision"]["work_unit_id"] == (
        "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
    )
    assert payload["stage_closure_decision"]["opl_closeout"]["stage_attempt_id"] == (
        "sat-current-write"
    )
    assert payload["stage_closure_decision"]["opl_closeout"]["work_unit_id"] == (
        "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
    )
    assert payload["stage_closure_decision"]["outcome"]["transition_kind"] == (
        "route_back_candidate_checkpoint"
    )


def test_receipt_owner_consumption_route_checkpoint_prefers_stage_closure_checkpoint_over_stale_carrier(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "dm003-stage-closure-checkpoint-readback.json"
    readback = _readback(
        study_id=study_id,
        stage_outcome="next_stage_transition",
        transition_kind="route_back_candidate_checkpoint",
        package_kind="current_package",
        can_submit=False,
    )
    work_unit_id = "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
    current_checkpoint_ref = (
        "ops/medautoscience/paper_mission_stage_attempts/"
        "sat-current-write/stage_attempt_closeout_packet.json"
    )
    readback["stage_closure_decision"].update(
        {
            "stage_id": "write",
            "work_unit_id": work_unit_id,
            "receipt_evidence_ref": "opl://stage-attempts/sat-current-write",
            "route_checkpoint_evidence_ref": current_checkpoint_ref,
            "opl_closeout": {
                "status": "opl_runtime_terminal_readback_observed",
                "stage_attempt_id": "sat-current-write",
                "work_unit_id": work_unit_id,
            },
        }
    )
    readback["stage_closure_decision"]["outcome"][
        "route_checkpoint_evidence_ref"
    ] = current_checkpoint_ref
    stale_carrier = readback["opl_runtime_carrier_readback"]
    stale_carrier["opl_transition_receipt"]["stage_attempt_id"] = "sat-stale-candidate"
    stale_carrier["opl_transition_receipt"]["stage_attempt_ref"] = (
        "opl://stage-attempts/sat-stale-candidate"
    )
    stale_carrier["receipt_evidence"]["receipt_ref"] = (
        "opl://stage-attempts/sat-stale-candidate"
    )
    stale_carrier["receipt_evidence"]["runtime_closeout_ref"] = (
        "ops/medautoscience/paper_mission_stage_attempts/sat-stale-candidate/"
        f"{study_id}/stage_attempt_closeout_packet.json"
    )
    stale_carrier["receipt_evidence"]["stage_attempt_ref"] = (
        "opl://stage-attempts/sat-stale-candidate"
    )
    stale_carrier["mas_receipt_consumption"]["receipt_evidence_ref"] = (
        "opl://stage-attempts/sat-stale-candidate"
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
            "--apply-route-checkpoint",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "owner_consumption_applied"
    assert payload["receipt_evidence"]["receipt_ref"] == (
        "opl://stage-attempts/sat-current-write"
    )
    assert payload["receipt_evidence"]["runtime_closeout_ref"] == current_checkpoint_ref
    assert payload["stage_closure"]["route_checkpoint_evidence_ref"] == (
        current_checkpoint_ref
    )
    assert payload["stage_closure_decision"]["route_checkpoint_evidence_ref"] == (
        current_checkpoint_ref
    )
    assert payload["stage_closure_decision"]["receipt_evidence_ref"] == (
        "opl://stage-attempts/sat-current-write"
    )
    assert payload["stage_closure_decision"]["opl_closeout"]["stage_attempt_id"] == (
        "sat-current-write"
    )
    assert payload["owner_consumption_verdict"]["receipt_ref"] == (
        "opl://stage-attempts/sat-current-write"
    )


def test_receipt_owner_consumption_keeps_newer_stage_closure_over_stale_route_back_carrier(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "dm003-newer-stage-closure-readback.json"
    stale_closeout = tmp_path / "stale" / "stage_attempt_closeout_packet.json"
    current_closeout = tmp_path / "current" / "stage_attempt_closeout_packet.json"
    stale_closeout.parent.mkdir(parents=True)
    current_closeout.parent.mkdir(parents=True)
    stale_closeout.write_text("{}", encoding="utf-8")
    current_closeout.write_text("{}", encoding="utf-8")
    os.utime(stale_closeout, (1_000, 1_000))
    os.utime(current_closeout, (2_000, 2_000))
    readback = _readback(
        study_id=study_id,
        stage_outcome="next_stage_transition",
        transition_kind="route_back_candidate_checkpoint",
        package_kind="current_package",
        can_submit=False,
    )
    work_unit_id = "submission_blocker_degraded_handoff_or_quality_repair"
    readback["next_action"] = {
        "action_family": "paper.stage_closure.owner_consumption",
        "outcome_ref": str(current_closeout),
    }
    readback["stage_closure_decision"].update(
        {
            "source_ref": str(current_closeout),
            "stage_id": "submission_milestone_candidate",
            "work_unit_id": work_unit_id,
            "opl_closeout": {
                "status": "opl_runtime_terminal_readback_observed",
                "stage_attempt_id": "sat-current",
                "work_unit_id": work_unit_id,
            },
        }
    )
    stale_carrier = readback["opl_runtime_carrier_readback"]
    stale_carrier["terminal_closeout"] = {
        "status": "completed",
        "stage_attempt_id": "sat-stale",
        "work_unit_id": work_unit_id,
        "closeout_ref": str(stale_closeout),
    }
    stale_carrier["opl_transition_receipt"].update(
        {
            "stage_attempt_id": "sat-stale",
            "stage_attempt_ref": "opl://stage-attempts/sat-stale",
            "work_unit_id": work_unit_id,
            "route_back_evidence_ref": "ops/stale/route_back_evidence_packet.json",
        }
    )
    stale_carrier["receipt_evidence"].update(
        {
            "receipt_ref": "opl://stage-attempts/sat-stale",
            "stage_attempt_ref": "opl://stage-attempts/sat-stale",
            "runtime_closeout_ref": str(stale_closeout),
            "route_back_evidence_ref": "ops/stale/route_back_evidence_packet.json",
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
            "--apply-route-checkpoint",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["stage_closure_decision"]["opl_closeout"]["stage_attempt_id"] == (
        "sat-current"
    )
    assert payload["owner_consumption_verdict"]["receipt_ref"] == (
        "opl://stage-attempts/sat-current"
    )


def test_receipt_owner_consumption_route_checkpoint_reads_current_next_action_stage_closure(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    closeout_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_attempts"
        / "sat-current-write"
    )
    stage_closure_ref = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_closure"
        / "paper_mission_terminalize_stage"
        / study_id
        / "stage_closure_decision.json"
    )
    closeout_root.mkdir(parents=True)
    stage_closure_ref.parent.mkdir(parents=True)
    (closeout_root / "stage_attempt_closeout_packet.json").write_text(
        json.dumps({"surface_kind": "stage_attempt_closeout_packet"}),
        encoding="utf-8",
    )
    work_unit_id = "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
    stage_closure_ref.write_text(
        json.dumps(
            {
                "surface_kind": "mas_stage_closure_decision",
                "study_id": study_id,
                "stage_id": "write",
                "work_unit_id": work_unit_id,
                "decision_ref": str(stage_closure_ref),
                "opl_closeout": {
                    "status": "opl_runtime_terminal_readback_observed",
                    "stage_attempt_id": "sat-current-write",
                    "work_unit_id": work_unit_id,
                },
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "route_back_candidate_checkpoint",
                    "next_action": (
                        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                    ),
                },
            }
        ),
        encoding="utf-8",
    )
    readback_file = tmp_path / "dm003-next-action-stage-closure-readback.json"
    readback = _readback(
        study_id=study_id,
        stage_outcome="next_stage_transition",
        transition_kind="route_back_candidate_checkpoint",
        package_kind="current_package",
        can_submit=False,
    )
    readback["study_root"] = str(study_root)
    readback["stage_closure_decision"].update(
        {
            "stage_id": "write",
            "work_unit_id": work_unit_id,
            "receipt_evidence_ref": "opl://stage-attempts/sat-stale-candidate",
            "route_checkpoint_evidence_ref": (
                "ops/medautoscience/paper_mission_stage_attempts/"
                f"sat-stale-candidate/{study_id}/stage_attempt_closeout_packet.json"
            ),
            "opl_closeout": {
                "status": "opl_runtime_terminal_readback_observed",
                "stage_attempt_id": "sat-stale-candidate",
                "work_unit_id": work_unit_id,
            },
        }
    )
    stale_carrier = readback["opl_runtime_carrier_readback"]
    stale_carrier["terminal_closeout"] = {
        "status": "completed",
        "stage_attempt_id": "sat-stale-candidate",
        "work_unit_id": work_unit_id,
        "closeout_ref": (
            "ops/medautoscience/paper_mission_stage_attempts/"
            f"sat-stale-candidate/{study_id}/stage_attempt_closeout_packet.json"
        ),
    }
    stale_carrier["opl_transition_receipt"].update(
        {
            "stage_attempt_id": "sat-stale-candidate",
            "stage_attempt_ref": "opl://stage-attempts/sat-stale-candidate",
            "work_unit_id": work_unit_id,
            "route_back_evidence_ref": (
                "ops/medautoscience/paper_mission_stage_attempts/"
                f"sat-stale-candidate/{study_id}/route_back_evidence_packet.json"
            ),
        }
    )
    stale_carrier["receipt_evidence"].update(
        {
            "receipt_ref": "opl://stage-attempts/sat-stale-candidate",
            "stage_attempt_ref": "opl://stage-attempts/sat-stale-candidate",
            "runtime_closeout_ref": (
                "ops/medautoscience/paper_mission_stage_attempts/"
                f"sat-stale-candidate/{study_id}/stage_attempt_closeout_packet.json"
            ),
            "route_back_evidence_ref": (
                "ops/medautoscience/paper_mission_stage_attempts/"
                f"sat-stale-candidate/{study_id}/route_back_evidence_packet.json"
            ),
        }
    )
    readback["next_action"] = {
        "action_family": "paper.stage_closure.owner_consumption",
        "outcome_ref": str(stage_closure_ref),
    }
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
            "--apply-route-checkpoint",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    current_checkpoint_ref = (
        "ops/medautoscience/paper_mission_stage_attempts/"
        "sat-current-write/stage_attempt_closeout_packet.json"
    )
    assert exit_code == 0
    assert payload["status"] == "owner_consumption_applied"
    assert payload["receipt_evidence"]["receipt_ref"] == (
        "opl://stage-attempts/sat-current-write"
    )
    assert payload["stage_closure_decision"]["route_checkpoint_evidence_ref"] == (
        current_checkpoint_ref
    )
    assert payload["stage_closure_decision"]["opl_closeout"]["stage_attempt_id"] == (
        "sat-current-write"
    )


def test_receipt_owner_consumption_route_checkpoint_synthesizes_current_stage_closure_from_carrier(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "dm003-synthesized-stage-closure-readback.json"
    work_unit_id = "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
    current_checkpoint_ref = (
        "ops/medautoscience/paper_mission_stage_attempts/"
        "sat-current-write/stage_attempt_closeout_packet.json"
    )
    readback = _readback(
        study_id=study_id,
        stage_outcome="next_stage_transition",
        transition_kind="route_back_candidate_checkpoint",
        package_kind="current_package",
        can_submit=False,
    )
    readback["stage_closure_decision"].update(
        {
            "stage_id": "review",
            "work_unit_id": "ai_reviewer_medical_prose_quality_review",
            "route_checkpoint_evidence_ref": (
                "ops/medautoscience/paper_mission_stage_attempts/"
                "sat-stale-review/stage_attempt_closeout_packet.json"
            ),
            "opl_closeout": {
                "status": "opl_runtime_terminal_readback_observed",
                "stage_attempt_id": "sat-stale-review",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
            },
        }
    )
    readback["next_action"] = {
        "action_family": "paper.stage_closure.owner_consumption",
        "stage_id": "write",
        "work_unit_id": work_unit_id,
    }
    readback["domain_transition"] = {
        "route_target": "write",
        "next_work_unit": {"unit_id": work_unit_id},
    }
    readback["current_opl_runtime_carrier_readback"] = {
        "terminal_closeout": {
            "status": "route_back_evidence_candidate",
            "closeout_ref": current_checkpoint_ref,
            "stage_attempt_id": "sat-current-write",
            "stage_id": "write",
            "work_unit_id": work_unit_id,
        },
        "opl_transition_receipt": {
            "surface_kind": "opl_transition_receipt",
            "receipt_status": "route_back_evidence_closeout_observed",
            "stage_attempt_id": "sat-current-write",
            "stage_attempt_ref": "opl://stage-attempts/sat-current-write",
            "runtime_closeout_ref": current_checkpoint_ref,
            "can_claim_paper_progress": False,
        },
        "receipt_evidence": {
            "surface_kind": "mas_receipt_evidence",
            "receipt_ref": "opl://stage-attempts/sat-current-write",
            "runtime_closeout_ref": current_checkpoint_ref,
            "can_claim_paper_progress": False,
            "can_claim_publication_ready": False,
        },
        "mas_receipt_consumption": {
            "surface_kind": "mas_receipt_consumption_projection",
            "status": "requires_mas_owner_consumption",
            "next_legal_action": (
                "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
            ),
            "can_claim_paper_progress": False,
            "can_claim_publication_ready": False,
            "can_claim_runtime_ready": False,
        },
    }
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
            "--apply-route-checkpoint",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "owner_consumption_applied"
    assert payload["receipt_evidence"]["receipt_ref"] == (
        "opl://stage-attempts/sat-current-write"
    )
    assert payload["stage_closure_decision"]["stage_id"] == "write"
    assert payload["stage_closure_decision"]["work_unit_id"] == work_unit_id
    assert payload["stage_closure_decision"]["route_checkpoint_evidence_ref"] == (
        current_checkpoint_ref
    )
    assert payload["stage_closure_decision"]["opl_closeout"]["stage_attempt_id"] == (
        "sat-current-write"
    )


def test_receipt_owner_consumption_route_checkpoint_synthesizes_route_back_only_carrier(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "dm003-route-back-only-readback.json"
    work_unit_id = "medical_prose_write_repair"
    route_back_ref = (
        "ops/medautoscience/paper_mission_stage_attempts/"
        f"sat-current-write/{study_id}/route_back_evidence_packet.json"
    )
    readback = _readback(
        study_id=study_id,
        stage_outcome="",
        transition_kind=None,
        package_kind="current_package",
        can_submit=False,
        consumption_next_legal_action=(
            "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
        ),
    )
    readback["stage_closure_decision"] = {}
    readback["next_action"] = {
        "action_family": "paper.write.prose_repair",
        "stage_id": "write",
        "work_unit_id": work_unit_id,
    }
    readback["opl_runtime_carrier_readback"] = {
        "terminal_closeout": {
            "surface_kind": "stage_attempt_closeout_packet",
            "status": "owner_answer_candidate_materialized",
            "closeout_ref": route_back_ref,
            "stage_attempt_id": "sat-current-write",
            "stage_id": "write",
            "work_unit_id": work_unit_id,
        },
        "opl_transition_receipt": {
            "surface_kind": "opl_transition_receipt",
            "receipt_status": "route_back_evidence_closeout_observed",
            "stage_attempt_id": "sat-current-write",
            "stage_attempt_ref": "opl://stage-attempts/sat-current-write",
            "runtime_closeout_ref": route_back_ref,
            "route_back_evidence_ref": route_back_ref,
            "can_claim_paper_progress": False,
        },
        "receipt_evidence": {
            "surface_kind": "mas_receipt_evidence",
            "receipt_ref": "opl://stage-attempts/sat-current-write",
            "runtime_closeout_ref": route_back_ref,
            "route_back_evidence_ref": route_back_ref,
            "can_claim_paper_progress": False,
            "can_claim_publication_ready": False,
        },
        "mas_receipt_consumption": {
            "surface_kind": "mas_receipt_consumption_projection",
            "status": "requires_mas_owner_consumption",
            "next_legal_action": (
                "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
            ),
            "receipt_evidence_ref": "opl://stage-attempts/sat-current-write",
            "route_back_evidence_ref": route_back_ref,
            "forbidden_next_action": "synonymous_route_back_redrive",
            "can_claim_paper_progress": False,
            "can_claim_publication_ready": False,
            "can_claim_runtime_ready": False,
        },
    }
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
            "--apply-route-checkpoint",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "owner_consumption_applied"
    assert payload["owner_consumption_verdict"]["verdict_kind"] == (
        "consume_route_back_checkpoint_owner_consumption_required"
    )
    assert payload["stage_closure"]["outcome_kind"] == "next_stage_transition"
    assert payload["stage_closure"]["transition_kind"] == "route_back_candidate_checkpoint"
    assert payload["stage_closure_decision"]["stage_id"] == "write"
    assert payload["stage_closure_decision"]["work_unit_id"] == work_unit_id
    assert payload["stage_closure_decision"]["route_checkpoint_evidence_ref"] == (
        route_back_ref
    )
    assert payload["mas_receipt_consumption"]["status"] == (
        "owner_consumed_route_checkpoint"
    )
