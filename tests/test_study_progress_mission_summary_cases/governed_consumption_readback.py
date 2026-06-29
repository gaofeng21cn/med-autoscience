from __future__ import annotations

import importlib
import json

import pytest

from med_autoscience.paper_mission_run import PaperMissionRun
from med_autoscience.paper_mission_transaction import PaperMissionTransaction
from tests.test_cli_cases.paper_mission_commands import (
    _write_matching_domain_gate_closeout,
    _paper_mission_transaction_payload,
    _paper_mission_forbidden_write_guard,
    _write_submission_milestone_package,
)
from tests.test_cli_cases.shared import write_profile

def test_materialized_mission_summary_prefers_latest_governed_consumption_ledger(
    tmp_path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "full_cutover_20260623"
        / study_id
    )
    write_profile(profile_path, workspace_root=workspace_root)
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
    mission_root.mkdir(parents=True)
    mission_id = (
        f"paper-mission::{study_id}::"
        "medical_prose_write_repair_publication_gate_replay::one-shot-migration"
    )
    old_transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="typed_blocker",
    )
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(
            {
                "schema_version": "paper-mission-run.v1",
                "mission_id": mission_id,
                "study_id": study_id,
                "objective": "Older materialized typed blocker mission.",
                "mission_state": "stable_blocker",
                "artifact_delta_ledger": [
                    {
                        "delta_id": "delta::dm003::one-shot",
                        "artifact_ref": "mission://dm003/prose-repair-owner-decision",
                        "delta_kind": "formal_paper_mission_owner_decision_packet",
                        "status": "candidate",
                    }
                ],
                "source_refs": [
                    {
                        "ref_id": "legacy_truth_import_pack",
                        "ref_kind": "legacy_truth_import_pack",
                        "uri": "mission://dm003/import-pack",
                    }
                ],
                "authority_touchpoints": [],
                "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
                "consume_result": {"status": "typed_blocker"},
                "claim_permissions": {
                    "can_claim_artifact_delta": True,
                    "can_claim_owner_handoff": True,
                    "can_claim_publication_ready": False,
                    "can_claim_current_package": False,
                    "can_claim_owner_receipt_written": False,
                },
                "paper_mission_transaction": old_transaction,
                "one_shot_migration_readback": {
                    "required_output": {
                        "next_owner": "one-person-lab",
                        "work_unit_id": "analysis_claim_evidence_repair",
                    },
                    "consume_candidate_status": "typed_blocker",
                },
            }
        ),
        encoding="utf-8",
    )
    package_path = _write_submission_milestone_package(
        workspace_root=workspace_root,
        study_id=study_id,
        mission_id=mission_id,
        base_transaction=old_transaction,
    )
    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(package_path),
            "--output-root",
            str(
                workspace_root
                / "ops"
                / "medautoscience"
                / "paper_mission_consumption_ledger"
                / "sat-current"
            ),
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    assert exit_code == 0
    capsys.readouterr()

    exit_code = cli.main(
        [
            "study",
            "progress",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["mission_state"] == "consumed"
    assert payload["consume_candidate_status"] == (
        "accepted_submission_milestone_candidate"
    )
    assert payload["paper_mission_run"]["mission_state"] == "consumed"
    assert payload["paper_mission_run"]["consume_result"]["status"] == "accepted"
    assert payload["paper_mission_run"]["consume_result"]["outcome"] == (
        "accepted_submission_milestone_candidate"
    )
    assert payload["stage_terminal_decision"]["decision_kind"] == "continue_same_stage"
    assert payload["opl_route_command"]["command_kind"] == "resume_stage"
    assert payload["next_owner_or_human_decision"]["next_owner"] == (
        "mission_executor"
    )
    assert payload["next_owner_or_human_decision"]["route_command"] == (
        "resume_stage"
    )
    assert payload["current_objective"]["next_owner"] == "mission_executor"
    assert payload["artifact_first_mission_summary"]["current_objective"][
        "next_owner"
    ] == "mission_executor"
    assert payload["artifact_first_mission_summary"][
        "next_owner_or_human_decision"
    ]["next_owner"] == "mission_executor"
    assert payload["paper_mission_transaction"]["stage_id"] == (
        "submission_milestone_candidate"
    )
    assert payload["artifact_first_mission_summary"]["read_model_source"] == {
        "source_kind": "paper_mission_consumption_ledger",
        "materialized_mission_ref": str(mission_root / "paper_mission_run.json"),
        "consumption_ledger_ref": str(
            workspace_root
            / "ops"
            / "medautoscience"
            / "paper_mission_consumption_ledger"
            / "sat-current"
            / study_id
            / "consume_record.json"
        ),
        "consumption_ledger_role": "current_paper_mission_transaction",
        "legacy_projection_accepted": False,
    }


def test_materialized_mission_summary_keeps_governed_consumption_current_when_terminal_residue_exists(
    tmp_path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "full_cutover_20260623"
        / study_id
    )
    write_profile(profile_path, workspace_root=workspace_root)
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
    mission_root.mkdir(parents=True)
    mission_id = (
        f"paper-mission::{study_id}::"
        "medical_prose_write_repair_publication_gate_replay::one-shot-migration"
    )
    old_transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="typed_blocker",
    )
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(
            {
                "schema_version": "paper-mission-run.v1",
                "mission_id": mission_id,
                "study_id": study_id,
                "objective": "Older materialized typed blocker mission.",
                "mission_state": "stable_blocker",
                "artifact_delta_ledger": [
                    {
                        "delta_id": "delta::dm003::one-shot",
                        "artifact_ref": "mission://dm003/prose-repair-owner-decision",
                        "delta_kind": "formal_paper_mission_owner_decision_packet",
                        "status": "candidate",
                    }
                ],
                "source_refs": [
                    {
                        "ref_id": "legacy_truth_import_pack",
                        "ref_kind": "legacy_truth_import_pack",
                        "uri": "mission://dm003/import-pack",
                    }
                ],
                "authority_touchpoints": [],
                "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
                "consume_result": {"status": "typed_blocker"},
                "claim_permissions": {
                    "can_claim_artifact_delta": True,
                    "can_claim_owner_handoff": True,
                    "can_claim_publication_ready": False,
                    "can_claim_current_package": False,
                    "can_claim_owner_receipt_written": False,
                },
                "paper_mission_transaction": old_transaction,
                "one_shot_migration_readback": {
                    "required_output": {
                        "next_owner": "one-person-lab",
                        "work_unit_id": "analysis_claim_evidence_repair",
                    },
                    "consume_candidate_status": "typed_blocker",
                },
            }
        ),
        encoding="utf-8",
    )
    package_path = _write_submission_milestone_package(
        workspace_root=workspace_root,
        study_id=study_id,
        mission_id=mission_id,
        base_transaction=old_transaction,
    )
    consume_exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(package_path),
            "--output-root",
            str(
                workspace_root
                / "ops"
                / "medautoscience"
                / "paper_mission_consumption_ledger"
                / "sat-current"
            ),
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    assert consume_exit_code == 0
    consume_payload = json.loads(capsys.readouterr().out)
    _write_matching_domain_gate_closeout(
        study_root=study_root,
        study_id=study_id,
        transaction=consume_payload["paper_mission_transaction_readback"][
            "paper_mission_transaction"
        ],
    )

    progress_exit_code = cli.main(
        [
            "study",
            "progress",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert progress_exit_code == 0
    assert payload["mission_state"] == "consumed"
    assert payload["consume_candidate_status"] == (
        "accepted_submission_milestone_candidate"
    )
    assert payload["paper_mission_run"]["mission_state"] == "consumed"
    assert payload["paper_mission_run"]["consume_result"]["status"] == "accepted"
    assert payload["stage_terminal_decision"]["decision_kind"] == (
        "continue_same_stage"
    )
    assert payload["opl_route_command"]["command_kind"] == "resume_stage"
    assert payload["paper_mission_transaction"]["stage_id"] == (
        "submission_milestone_candidate"
    )
    assert payload["next_owner_or_human_decision"]["next_owner"] == (
        "mission_executor"
    )
    assert payload["next_owner_or_human_decision"]["route_command"] == (
        "resume_stage"
    )
    assert "terminal_owner_gate" not in payload
    assert "terminal_owner_gate_authority_readback" not in payload
    assert "terminal_owner_gate_owner_answer_readback" not in payload
    assert payload["opl_transition_receipt"]["status"] == (
        "not_requested_from_study_progress"
    )
    assert payload["artifact_first_mission_summary"]["read_model_source"][
        "source_kind"
    ] == "paper_mission_consumption_ledger"


def test_materialized_mission_summary_preserves_followthrough_ledger_transaction(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "full_cutover_20260623"
        / study_id
    )
    write_profile(profile_path, workspace_root=workspace_root)
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
    mission_root.mkdir(parents=True)
    legacy_mission_id = f"paper-mission::{study_id}::gate-clearing::one-shot-migration"
    legacy_transaction = _paper_mission_transaction_payload(
        mission_id=legacy_mission_id,
        study_id=study_id,
        decision_kind="typed_blocker",
    )
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(
            {
                "schema_version": "paper-mission-run.v1",
                "mission_id": legacy_mission_id,
                "study_id": study_id,
                "objective": "Older one-shot materialized mission.",
                "mission_state": "stable_blocker",
                "artifact_delta_ledger": [
                    {
                        "delta_id": "delta::dm002::one-shot",
                        "artifact_ref": "mission://dm002/legacy-owner-decision",
                        "delta_kind": "formal_paper_mission_owner_decision_packet",
                        "status": "candidate",
                    }
                ],
                "source_refs": [
                    {
                        "ref_id": "legacy_truth_import_pack",
                        "ref_kind": "legacy_truth_import_pack",
                        "uri": "mission://dm002/import-pack",
                    }
                ],
                "authority_touchpoints": [],
                "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
                "consume_result": {"status": "typed_blocker"},
                "claim_permissions": {
                    "can_claim_artifact_delta": True,
                    "can_claim_owner_handoff": True,
                    "can_claim_publication_ready": False,
                    "can_claim_current_package": False,
                    "can_claim_owner_receipt_written": False,
                },
                "paper_mission_transaction": legacy_transaction,
                "one_shot_migration_readback": {
                    "required_output": {
                        "next_owner": "one-person-lab",
                        "work_unit_id": "analysis_claim_evidence_repair",
                    },
                    "consume_candidate_status": "typed_blocker",
                },
            }
        ),
        encoding="utf-8",
    )
    followthrough_mission_id = f"{legacy_mission_id}::followthrough"
    followthrough_transaction = _paper_mission_transaction_payload(
        mission_id=followthrough_mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    package_path = _write_submission_milestone_package(
        workspace_root=workspace_root,
        study_id=study_id,
        mission_id=followthrough_mission_id,
        base_transaction=followthrough_transaction,
    )
    consume_exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(package_path),
            "--output-root",
            str(
                workspace_root
                / "ops"
                / "medautoscience"
                / "paper_mission_consumption_ledger"
                / "sat-followthrough"
            ),
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    assert consume_exit_code == 0
    consume_payload = json.loads(capsys.readouterr().out)
    followthrough_transaction = consume_payload["paper_mission_transaction_readback"][
        "paper_mission_transaction"
    ]

    opl_bin = tmp_path / "fake-opl"
    opl_bin.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    opl_bin.chmod(0o755)
    monkeypatch.setenv("OPL_BIN", str(opl_bin))

    readback_module = importlib.import_module("med_autoscience.paper_mission_opl_readback")

    def fake_opl_json(_opl_bin, args, *, timeout_seconds=8.0):
        assert timeout_seconds > 0
        payload = {
            "task_id": "frt-followthrough",
            "domain_id": "medautoscience",
            "task_kind": "paper_mission/stage-route",
            "status": "running",
            "payload": {
                "study_id": study_id,
                "paper_mission_transaction_ref": followthrough_transaction[
                    "transaction_id"
                ],
                "opl_route_command_ref": (
                    f"{followthrough_transaction['transaction_id']}"
                    "#opl_route_command"
                ),
                "command_kind": "resume_stage",
                "route_target": followthrough_transaction["opl_route_command"][
                    "target"
                ],
            },
        }
        attempt = {
            "surface_kind": "opl_stage_attempt_running_readback",
            "status": "running",
            "stage_id": followthrough_transaction["opl_route_command"]["target"],
            "stage_attempt_id": "sat-followthrough",
            "provider_status": "running",
            "workspace_locator": {
                "study_id": study_id,
                "paper_mission_transaction_ref": followthrough_transaction[
                    "transaction_id"
                ],
                "opl_route_command_ref": (
                    f"{followthrough_transaction['transaction_id']}"
                    "#opl_route_command"
                ),
                "command_kind": "resume_stage",
                "route_target": followthrough_transaction["opl_route_command"][
                    "target"
                ],
            },
        }
        if args[:3] == ("family-runtime", "queue", "list"):
            return {
                "family_runtime_queue": {
                    "tasks": [payload],
                    "stage_attempts": [attempt],
                }
            }
        if args[:3] == ("family-runtime", "queue", "inspect"):
            return {
                "family_runtime_task": {
                    "task": payload,
                    "stage_attempts": [attempt],
                }
            }
        raise AssertionError(f"unexpected OPL command: {args}")

    monkeypatch.setattr(readback_module, "_run_opl_json", fake_opl_json)

    progress_exit_code = cli.main(
        [
            "study",
            "progress",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert progress_exit_code == 0
    assert payload["paper_mission_run"]["mission_id"] == followthrough_mission_id
    assert payload["paper_mission_transaction"]["mission_id"] == (
        followthrough_mission_id
    )
    assert payload["paper_mission_transaction"]["transaction_id"] == (
        followthrough_transaction["transaction_id"]
    )
    assert payload["stage_terminal_decision"]["decision_kind"] == (
        "continue_same_stage"
    )
    assert payload["opl_route_command"]["command_kind"] == "resume_stage"
    assert "opl_runtime_readback_status" not in payload
    assert "opl_runtime_carrier_readback" not in payload
    assert payload["opl_transition_receipt"]["status"] == (
        "not_requested_from_study_progress"
    )
    assert payload["artifact_first_mission_summary"]["read_model_source"][
        "consumption_ledger_role"
    ] == "current_paper_mission_transaction"
