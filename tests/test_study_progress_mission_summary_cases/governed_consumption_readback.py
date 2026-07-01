from __future__ import annotations

import importlib
import json
import os

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
    consume_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / "sat-current"
    )
    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(package_path),
            "--output-root",
            str(consume_root),
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    assert exit_code == 0
    stale_receipt_ref = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_receipt_owner_consumption"
        / "stale-opl-attempt"
        / study_id
        / "receipt_owner_consumption.json"
    )
    stale_receipt_ref.parent.mkdir(parents=True)
    stale_receipt_ref.write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_receipt_owner_consumption",
                "schema_version": 1,
                "status": "owner_consumption_applied",
                "study_id": study_id,
                "apply_mode": "typed_blocker",
                "authority_materialized": True,
                "stage_closure_decision": {
                    "surface_kind": "mas_stage_closure_decision",
                    "schema_version": 1,
                    "study_id": study_id,
                    "authority_materialized": True,
                    "counts_as_typed_blocker": True,
                    "outcome": {
                        "kind": "typed_blocker",
                        "blocker_type": "paper_mission_stage_route_domain_gate_pending",
                        "next_action": "resolve_typed_blocker_or_route_redesign",
                        "known_blockers": [
                            "paper_mission_stage_route_domain_gate_pending"
                        ],
                        "authority_materialized": True,
                    },
                    "authority_boundary": {
                        "surface_role": "paper_mission_receipt_owner_consumption",
                        "writes_receipt_owner_consumption": True,
                        "writes_owner_receipt": False,
                        "writes_typed_blocker": False,
                        "writes_human_gate": False,
                        "writes_current_package": False,
                        "writes_submission_ready_package": False,
                        "writes_runtime_queue_or_provider_attempt": False,
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    os.utime(stale_receipt_ref, (2_000_000_000, 2_000_000_000))
    os.utime(
        consume_root / study_id / "consume_record.json",
        (3_000_000_000, 3_000_000_000),
    )
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
    assert payload["receipt_owner_consumption_readback"] is None
    assert payload["artifact_first_mission_summary"][
        "receipt_owner_consumption_readback"
    ] is None
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


def test_consumption_ledger_summary_uses_terminalized_stage_closure_readback(
    tmp_path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    ledger = importlib.import_module("med_autoscience.paper_mission_stage_closure_ledger")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    write_profile(profile_path, workspace_root=workspace_root)
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
    mission_id = f"paper-mission::{study_id}::reviewer-revision"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    package_path = _write_submission_milestone_package(
        workspace_root=workspace_root,
        study_id=study_id,
        mission_id=mission_id,
        base_transaction=transaction,
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
                / "reviewer-revision"
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
    consume_readback = consume_payload["paper_mission_transaction_readback"]
    ledger.write_paper_mission_stage_closure_decision(
        output_root=(
            workspace_root
            / "ops"
            / "medautoscience"
            / "paper_mission_stage_closure"
            / "paper_mission_terminalize_stage"
        ),
        study_id=study_id,
        decision={
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "consume_route_back_checkpoint",
                "next_action": (
                    "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                ),
                "next_owner": "MedAutoScience.paper_mission",
            },
            "known_blockers": ["accepted_submission_milestone_candidate"],
        },
        source_readback=consume_readback,
        source="pytest",
        forbidden_authority_writes=("publication_eval/latest.json",),
        forbidden_authority_claims=("submission_ready",),
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
    assert payload["artifact_first_mission_summary"]["read_model_source"][
        "source_kind"
    ] == "paper_mission_consumption_ledger"
    assert payload["stage_closure_decision"]["projection_status"] == (
        "terminalizer_outcome_observed"
    )
    assert payload["stage_closure_outcome"] == "next_stage_transition"
    assert payload["stage_closure"]["outcome_kind"] == "next_stage_transition"
    assert payload["stage_closure"]["next_legal_action"] == (
        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
    )
    assert payload["artifact_first_mission_summary"]["stage_closure_ledger_readback"][
        "source_surface_kind"
    ] == "paper_mission_stage_closure_ledger"
    assert payload["paper_mission_run"]["stage_closure_readback"][
        "projection_status"
    ] == "terminalizer_outcome_observed"


def test_materialized_mission_summary_consumes_receipt_owner_consumption_ledger(
    tmp_path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
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
    receipt_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_receipt_owner_consumption"
        / study_id
    )
    write_profile(profile_path, workspace_root=workspace_root)
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
    mission_root.mkdir(parents=True)
    receipt_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::one-shot-migration"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(
            {
                "schema_version": "paper-mission-run.v1",
                "mission_id": mission_id,
                "study_id": study_id,
                "objective": "Accepted submission milestone candidate.",
                "mission_state": "consumed",
                "artifact_delta_ledger": [],
                "source_refs": [],
                "authority_touchpoints": [],
                "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
                "consume_result": {
                    "status": "accepted",
                    "outcome": "accepted_submission_milestone_candidate",
                },
                "paper_mission_transaction": transaction,
                "one_shot_migration_readback": {
                    "required_output": {
                        "next_owner": "mission_executor",
                        "work_unit_id": "submission_milestone_candidate",
                    },
                    "consume_candidate_status": (
                        "accepted_submission_milestone_candidate"
                    ),
                },
            }
        ),
        encoding="utf-8",
    )
    receipt_packet = {
        "surface_kind": "paper_mission_receipt_owner_consumption",
        "schema_version": 1,
        "status": "owner_consumption_applied",
        "study_id": study_id,
        "apply_mode": "typed_blocker",
        "authority_materialized": True,
        "receipt_evidence": {
            "surface_kind": "mas_receipt_evidence",
            "receipt_kind": "opl_transition_receipt",
            "receipt_ref": "opl://stage-attempts/sat-obesity",
            "typed_runtime_blocker_ref": "stage_closure_decision.json",
            "can_claim_paper_progress": False,
            "can_claim_publication_ready": False,
            "durable_stop_allowed": True,
        },
        "opl_transition_receipt": {
            "surface_kind": "opl_transition_receipt",
            "receipt_status": "terminal_closeout_observed",
            "role": "transport_receipt_only",
            "stage_attempt_ref": "opl://stage-attempts/sat-obesity",
            "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
            "can_claim_paper_progress": False,
        },
        "mas_receipt_consumption": {
            "surface_kind": "mas_receipt_consumption_projection",
            "schema_version": 1,
            "status": "owner_consumed_typed_blocker",
            "next_legal_action": "record_typed_blocker",
            "owner_result_kind": "typed_blocker",
            "typed_blocker_evidence_ref": "stage_closure_decision.json",
            "durable_stop_allowed": True,
            "can_claim_paper_progress": False,
            "can_claim_publication_ready": False,
            "can_claim_runtime_ready": False,
        },
        "stage_closure_decision": {
            "surface_kind": "mas_stage_closure_decision",
            "schema_version": 1,
            "study_id": study_id,
            "authority_materialized": True,
            "counts_as_typed_blocker": True,
            "outcome": {
                "kind": "typed_blocker",
                "blocker_type": "paper_mission_stage_route_domain_gate_pending",
                "next_action": "resolve_typed_blocker_or_route_redesign",
                "known_blockers": [
                    "paper_mission_stage_route_domain_gate_pending"
                ],
                "authority_materialized": True,
            },
            "authority_boundary": {
                "surface_role": "paper_mission_receipt_owner_consumption",
                "writes_receipt_owner_consumption": True,
                "writes_owner_receipt": False,
                "writes_typed_blocker": False,
                "writes_human_gate": False,
                "writes_current_package": False,
                "writes_submission_ready_package": False,
                "writes_runtime_queue_or_provider_attempt": False,
            },
        },
    }
    (receipt_root / "receipt_owner_consumption.json").write_text(
        json.dumps(receipt_packet),
        encoding="utf-8",
    )

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
    assert payload["receipt_owner_consumption_readback"]["status"] == (
        "owner_consumption_applied"
    )
    assert payload["mas_receipt_consumption"]["status"] == (
        "owner_consumed_typed_blocker"
    )
    assert payload["stage_closure_outcome"] == "typed_blocker"
    assert payload["stage_closure"]["next_legal_action"] == (
        "resolve_typed_blocker_or_route_redesign"
    )
    assert payload["next_legal_action"] == "resolve_typed_blocker_or_route_redesign"
    assert payload["artifact_first_mission_summary"][
        "receipt_owner_consumption_readback"
    ]["source_surface_kind"] == "paper_mission_receipt_owner_consumption_ledger"


def test_typed_blocker_resolution_successor_supersedes_stale_wakeup_top_level(
    tmp_path,
) -> None:
    from types import SimpleNamespace

    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly"
    )
    study_id = "obesity_multicenter_phenotype_atlas"
    workspace_root = tmp_path / "workspace"
    packet_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_typed_blocker_resolution"
        / study_id
    )
    packet_root.mkdir(parents=True)
    typed_ref = "/tmp/obesity/stage_closure_decision.json"
    (packet_root / "typed_blocker_resolution.json").write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_typed_blocker_resolution",
                "schema_version": 1,
                "status": "human_gate_resolution_packet_materialized",
                "study_id": study_id,
                "resolution_packet_materialized": True,
                "authority_materialized": False,
                "writes_authority": False,
                "submission_ready_claim_authorized": False,
                "authority_boundary": {
                    "projection_only": True,
                    "writes_owner_receipt": False,
                    "writes_typed_blocker": False,
                    "writes_human_gate": False,
                    "writes_current_package": False,
                    "writes_publication_eval": False,
                    "writes_controller_decision": False,
                    "writes_runtime_queue_or_provider_attempt": False,
                },
                "typed_blocker": {
                    "blocker_type": "paper_mission_stage_route_domain_gate_pending",
                    "typed_blocker_evidence_ref": typed_ref,
                },
                "next_owner_action": {
                    "surface_kind": "current_executable_owner_action",
                    "schema_version": 1,
                    "status": "ready",
                    "study_id": study_id,
                    "next_owner": "mas_authority_kernel",
                    "owner": "mas_authority_kernel",
                    "action_type": (
                        "await_human_or_mas_authority_decision_for_submission_blocker"
                    ),
                    "allowed_actions": [
                        "await_human_or_mas_authority_decision_for_submission_blocker"
                    ],
                    "work_unit_id": "submission_blocker_human_gate",
                    "work_unit_fingerprint": "665aca9bc8dce75bc5d41f9a",
                    "acceptance_refs": [typed_ref, "typed_blocker_resolution_packet_ref"],
                    "paper_facing_delta": {
                        "can_submit": False,
                        "delta_kind": "human_gate_decision",
                        "expected_delta": (
                            "paper_mission_stage_route_domain_gate_pending"
                        ),
                        "known_blockers": [],
                        "package_kind": None,
                        "paper_surface": "manuscript/current_package",
                    },
                    "accepted_answer_shape": {
                        "shape_kind": "human_gate_or_degraded_handoff",
                        "accepted_statuses": ["human_gate", "route_back", "typed_blocker"],
                        "required_refs": [
                            "human_gate_question_ref",
                            "known_blockers",
                            "resume_condition",
                        ],
                    },
                    "route_back": {
                        "required": True,
                        "route_back_to": "paper-mission inspect",
                        "route_back_evidence_ref": typed_ref,
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    payload = module._attach_typed_blocker_resolution_successor_projection(
        payload={
            "study_id": study_id,
            "current_stage": "queued",
            "current_stage_summary": "旧 queued/wakeup 投影",
            "runtime_decision": "blocked",
            "runtime_reason": "quest_user_paused_requires_explicit_wakeup",
            "current_blockers": [
                "OPL current_control_state handoff 已陈旧，当前不能确认 stage/runtime owner 仍在接管。",
                "quest user paused requires explicit wakeup",
                "claim_evidence_consistency_failed",
            ],
            "next_system_action": "需要先刷新 OPL current_control_state handoff。",
            "stage_closure_decision": {
                "stage_id": "submission_milestone_candidate",
                "outcome": {
                    "kind": "typed_blocker",
                    "blocker_type": "paper_mission_stage_route_domain_gate_pending",
                },
            },
            "study_macro_state": {"details": {}},
            "user_visible_projection": {
                "current_stage": "queued",
                "next_owner": "one-person-lab",
            },
            "status_narration_contract": {"stage": {}, "readiness": {}},
        },
        profile=SimpleNamespace(workspace_root=workspace_root),
        study_id=study_id,
    )

    assert payload["current_stage"] == "owner_action_ready"
    assert payload["runtime_decision"] == "owner_action_required"
    assert payload["runtime_reason"] == "typed_blocker_resolution_owner_action_ready"
    assert payload["next_action"]["owner"] == "mas_authority_kernel"
    assert payload["current_executable_owner_action"]["next_owner"] == (
        "mas_authority_kernel"
    )
    assert payload["paper_facing_action"]["status"] == "owner_action_ready"
    assert payload["paper_facing_action"]["source_surface"] == "paper_mission.next_action"
    assert payload["user_visible_projection"]["current_stage"] == "owner_action_ready"
    assert payload["user_visible_projection"]["next_owner"] == "mas_authority_kernel"
    assert payload["current_blockers"][0] == (
        "paper_mission_stage_route_domain_gate_pending"
    )
    assert not any(
        "wakeup" in blocker or "OPL current_control_state handoff" in blocker
        for blocker in payload["current_blockers"]
    )


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
    assert payload["opl_runtime_readback_status"] == (
        "not_requested_from_study_progress"
    )
    assert "opl_runtime_carrier_readback" not in payload
    assert payload["opl_transition_receipt"]["status"] == (
        "not_requested_from_study_progress"
    )
    assert payload["artifact_first_mission_summary"]["read_model_source"][
        "consumption_ledger_role"
    ] == "current_paper_mission_transaction"
