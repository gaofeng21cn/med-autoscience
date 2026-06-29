from __future__ import annotations

import importlib
import json
from pathlib import Path

from med_autoscience.controllers.next_action_envelope import SURFACE_KIND
from med_autoscience.cli_parts import paper_mission_commands as commands
from tests.test_cli_cases.paper_mission_command_helpers import *  # noqa: F401,F403


def test_paper_mission_inspect_materialized_readback_defaults_to_no_live_opl_probe(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "full_cutover_20260623"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::medical-prose-repair::one-shot"
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
                "objective": "Read materialized mission without probing OPL by default.",
                "mission_state": "consumed",
                "artifact_delta_ledger": [],
                "source_refs": [],
                "authority_touchpoints": [],
                "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
                "consume_result": {
                    "status": "accepted",
                    "outcome": "accepted_submission_milestone_candidate",
                },
                "claim_permissions": {
                    "can_claim_artifact_delta": False,
                    "can_claim_owner_handoff": True,
                    "can_claim_publication_ready": False,
                    "can_claim_current_package": False,
                    "can_claim_owner_receipt_written": False,
                },
                "paper_mission_transaction": transaction,
            }
        ),
        encoding="utf-8",
    )
    live_probe_flags: list[bool] = []
    original = commands.attach_opl_runtime_carrier_readback

    def spy_attach_opl_runtime_carrier_readback(**kwargs):
        live_probe_flags.append(bool(kwargs.get("enable_opl_live_probe")))
        if kwargs.get("enable_opl_live_probe"):
            raise AssertionError("materialized inspect should not request OPL live probe by default")
        return original(**kwargs)

    monkeypatch.setattr(
        commands,
        "attach_opl_runtime_carrier_readback",
        spy_attach_opl_runtime_carrier_readback,
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "inspect",
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
    assert live_probe_flags
    assert live_probe_flags == [False]


def test_paper_mission_inspect_can_request_opl_transition_receipt_readback(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    readback_module = importlib.import_module("med_autoscience.paper_mission_opl_readback")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "full_cutover_20260623"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::medical-prose-repair::one-shot"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    route = transaction["opl_route_command"]
    route_command_ref = f"{transaction['transaction_id']}#opl_route_command"
    task_id = "frt-opl-receipt"
    stage_attempt_id = "sat-opl-receipt"
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(
            {
                "schema_version": "paper-mission-run.v1",
                "mission_id": mission_id,
                "study_id": study_id,
                "objective": "Read OPL transition receipt on request.",
                "mission_state": "consumed",
                "artifact_delta_ledger": [],
                "source_refs": [],
                "authority_touchpoints": [],
                "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
                "consume_result": {
                    "status": "accepted",
                    "outcome": "accepted_submission_milestone_candidate",
                },
                "claim_permissions": {
                    "can_claim_artifact_delta": False,
                    "can_claim_owner_handoff": True,
                    "can_claim_publication_ready": False,
                    "can_claim_current_package": False,
                    "can_claim_owner_receipt_written": False,
                },
                "paper_mission_transaction": transaction,
            }
        ),
        encoding="utf-8",
    )
    opl_bin = tmp_path / "opl"
    opl_bin.write_text("#!/bin/sh\n", encoding="utf-8")

    def fake_opl_json(_opl_bin, args, *, timeout_seconds=8.0):
        assert timeout_seconds > 0
        if args[:3] == ("family-runtime", "queue", "list"):
            return {
                "version": "g2",
                "family_runtime_queue": {
                    "tasks": [
                        {
                            "task_id": task_id,
                            "domain_id": "medautoscience",
                            "task_kind": "paper_mission/stage-route",
                            "payload": {
                                "study_id": study_id,
                                "paper_mission_transaction_ref": transaction[
                                    "transaction_id"
                                ],
                                "opl_route_command_ref": route_command_ref,
                                "command_kind": route["command_kind"],
                                "route_target": route["target"],
                            },
                            "status": "blocked",
                            "last_error": "paper_mission_stage_route_domain_gate_pending",
                        }
                    ]
                },
            }
        if args[:3] == ("family-runtime", "queue", "inspect"):
            return {
                "version": "g2",
                "family_runtime_task": {
                    "surface_id": "opl_family_runtime_task",
                    "task": {
                        "task_id": task_id,
                        "domain_id": "medautoscience",
                        "task_kind": "paper_mission/stage-route",
                        "payload": {
                            "study_id": study_id,
                            "paper_mission_transaction_ref": transaction[
                                "transaction_id"
                            ],
                            "opl_route_command_ref": route_command_ref,
                            "command_kind": route["command_kind"],
                            "route_target": route["target"],
                        },
                        "status": "blocked",
                        "last_error": "paper_mission_stage_route_domain_gate_pending",
                        "current_control_state": {
                            "current_stage_attempt_id": stage_attempt_id,
                            "running_provider_attempt": False,
                            "closeout_refs": [route["source_terminal_decision_ref"]],
                            "closeout_receipt_status": "accepted_typed_closeout",
                            "stage_run_currentness_identity": {
                                "stage_id": route["target"],
                            },
                        },
                    },
                    "stage_attempts": [
                        {
                            "stage_attempt_id": stage_attempt_id,
                            "status": "completed",
                            "stage_id": route["target"],
                        }
                    ],
                    "events": [
                        {
                            "event_type": "paper_mission_stage_route_terminal_task_reconciled",
                            "payload": {
                                "opl_transition_receipt": {
                                    "surface_kind": "opl_transition_receipt",
                                    "schema_version": 1,
                                    "receipt_status": "terminal_closeout_observed",
                                    "role": "transport_receipt_only",
                                    "study_id": study_id,
                                    "paper_mission_transaction_ref": transaction[
                                        "transaction_id"
                                    ],
                                    "opl_route_command_ref": route_command_ref,
                                    "command_kind": route["command_kind"],
                                    "route_target": route["target"],
                                    "task_id": task_id,
                                    "task_status": "blocked",
                                    "stage_attempt_id": stage_attempt_id,
                                    "stage_attempt_ref": (
                                        f"opl://stage-attempts/{stage_attempt_id}"
                                    ),
                                    "closeout_refs": [
                                        route["source_terminal_decision_ref"]
                                    ],
                                    "closeout_receipt_status": "accepted_typed_closeout",
                                    "blocked_reason": (
                                        "paper_mission_stage_route_domain_gate_pending"
                                    ),
                                    "can_change_stage_terminal_decision": False,
                                    "can_select_next_owner": False,
                                    "can_claim_paper_progress": False,
                                    "authority_boundary": {
                                        "writes_owner_receipt": False,
                                        "writes_typed_blocker": False,
                                        "writes_human_gate": False,
                                        "writes_current_package": False,
                                        "can_claim_paper_progress": False,
                                    },
                                }
                            },
                        }
                    ],
                },
            }
        raise AssertionError(f"unexpected OPL command: {args}")

    monkeypatch.setattr(readback_module, "_ranked_opl_bin_candidates", lambda: [opl_bin])
    monkeypatch.setattr(readback_module, "_run_opl_json", fake_opl_json)

    exit_code = cli.main(
        [
            "paper-mission",
            "inspect",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--request-opl-runtime-readback",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    carrier_readback = payload["opl_runtime_carrier_readback"]
    assert carrier_readback["runtime_readback_status"] == "terminal_closeout_observed"
    receipt = carrier_readback["opl_transition_receipt"]
    assert receipt["surface_kind"] == "opl_transition_receipt"
    assert receipt["receipt_status"] == "terminal_closeout_observed"
    assert receipt["task_id"] == task_id
    assert receipt["stage_attempt_id"] == stage_attempt_id
    assert receipt["can_claim_paper_progress"] is False
    assert payload["next_action"]["action_family"] != "runtime.opl_route"


def test_paper_mission_materialized_readback_keeps_governed_consumption_current_when_terminal_residue_exists(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
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
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": "Older typed blocker mission with terminal residue.",
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
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
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
    current_transaction = consume_payload["paper_mission_transaction_readback"][
        "paper_mission_transaction"
    ]
    _write_matching_domain_gate_closeout(
        study_root=study_root,
        study_id=study_id,
        transaction=current_transaction,
    )

    inspect_exit_code = cli.main(
        [
            "paper-mission",
            "inspect",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    inspect_payload = json.loads(capsys.readouterr().out)

    assert inspect_exit_code == 0
    assert inspect_payload["mission_state"] == "consumed"
    assert inspect_payload["consume_candidate_status"] == (
        "accepted_submission_milestone_candidate"
    )
    assert inspect_payload["paper_mission_current_transaction_source"] == (
        "paper_mission_consumption_ledger"
    )
    assert inspect_payload["next_owner"] == "mission_executor"
    assert inspect_payload["owner_answer_shape"] == "route_back_evidence_ref"
    assert inspect_payload["artifact_delta_refs"] == (
        inspect_payload["paper_mission_transaction"]["artifact_delta_refs"]
    )
    assert [Path(ref["uri"]).name for ref in inspect_payload["artifact_delta_refs"]] == [
        "paper_facing_candidate_delta.json",
    ]
    assert inspect_payload["paper_mission_run"]["consume_result"]["status"] == (
        "accepted"
    )
    assert inspect_payload["paper_mission_run"]["consume_result"]["outcome"] == (
        "accepted_submission_milestone_candidate"
    )
    assert inspect_payload["stage_terminal_decision"]["decision_kind"] == (
        "continue_same_stage"
    )
    assert inspect_payload["opl_route_command"]["command_kind"] == "resume_stage"
    assert inspect_payload["paper_mission_transaction"]["stage_id"] == (
        "submission_milestone_candidate"
    )
    assert _unique_surface_action_ids(inspect_payload, SURFACE_KIND) == {
        inspect_payload["next_action"]["action_id"]
    }
    assert inspect_payload["next_action"] == inspect_payload[
        "paper_mission_transaction_readback"
    ]["next_action"]
    assert inspect_payload["next_action"]["surface_kind"] == SURFACE_KIND
    assert inspect_payload["next_action"]["authority_source"] == (
        "mas_next_action_compiler"
    )
    assert inspect_payload["next_action"]["action_family"] == "runtime.opl_route"
    assert inspect_payload["next_action"]["legacy_fields_are_diagnostic"] is True
    assert inspect_payload["next_action"]["legacy_field_diagnostic_roles"][
        "work_unit_id"
    ] == "diagnostic_currentness_id"
    assert inspect_payload["next_action"]["authority_boundary"][
        "exact_work_unit_id_authority"
    ] is False
    assert inspect_payload["paper_mission_transaction_readback"]["source"] == (
        "paper_mission_consumption_ledger"
    )
    assert inspect_payload["next_owner_or_human_decision"]["next_owner"] == (
        "mission_executor"
    )
    assert inspect_payload["next_owner_or_human_decision"]["route_command"] == (
        "resume_stage"
    )
    terminal_gate = inspect_payload["terminal_owner_gate"]
    assert terminal_gate["owner"] == "mas_authority_kernel"
    assert terminal_gate["gate_kind"] == "domain_gate"
    assert terminal_gate["can_claim_paper_progress"] is False
    assert terminal_gate["can_claim_runtime_ready"] is False
    authority_readback = inspect_payload["terminal_owner_gate_authority_readback"]
    assert authority_readback["status"] == "route_back"
    assert authority_readback["selected_outcome"] == "route_back_evidence_ref"
    assert authority_readback["owner_answer_materialized"] is True
    assert authority_readback["authority_boundary"]["can_claim_paper_progress"] is False
    owner_answer = inspect_payload["terminal_owner_gate_owner_answer_readback"]
    assert owner_answer["owner_answer_shape"] == "route_back_evidence_ref"
    assert owner_answer["can_claim_paper_progress"] is False
    assert owner_answer["can_claim_runtime_ready"] is False
    assert owner_answer["write_plan"]["written_files"] == []
    assert owner_answer["stage_terminal_decision"]["decision_kind"] == "route_back"
    assert inspect_payload["route_back_budget"] == owner_answer["route_back_budget"]
    assert inspect_payload["mission_executor_fallback_action"] == (
        owner_answer["mission_executor_fallback_action"]
    )
    assert inspect_payload["carry_forward_risk_receipt_ref"] == (
        owner_answer["carry_forward_risk_receipt_ref"]
    )
    assert inspect_payload["paper_mission_transaction_readback"][
        "terminal_owner_gate_owner_answer_readback"
    ] == owner_answer
    assert inspect_payload["mutation_policy"]["writes_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_inspect_prefers_latest_governed_consumption_ledger_transaction(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "full_cutover_20260623"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = (
        f"paper-mission::{study_id}::"
        "medical_prose_write_repair_publication_gate_replay::one-shot-migration"
    )
    one_shot_transaction = _paper_mission_transaction_payload(
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
                "objective": "Older one-shot typed blocker mission.",
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
                "paper_mission_transaction": one_shot_transaction,
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
        base_transaction=one_shot_transaction,
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
    capsys.readouterr()

    exit_code = cli.main(
        [
            "paper-mission",
            "inspect",
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
    assert payload["surface_kind"] == "paper_mission_materialized_readback"
    assert payload["paper_mission_current_transaction_source"] == (
        "paper_mission_consumption_ledger"
    )
    assert payload["consume_candidate_status"] == (
        "accepted_submission_milestone_candidate"
    )
    assert payload["paper_mission_run"]["mission_state"] == "consumed"
    assert payload["paper_mission_run"]["consume_result"]["status"] == "accepted"
    assert payload["paper_mission_run"]["consume_result"]["outcome"] == (
        "accepted_submission_milestone_candidate"
    )
    assert payload["transaction_state"] == "accepted_submission_milestone_candidate"
    assert payload["stage_terminal_decision"]["decision_kind"] == "continue_same_stage"
    assert payload["durable_mission_stop_guard"][
        "accepted_submission_milestone_candidate_is_durable_stop"
    ] is False
    assert payload["durable_mission_stop_guard"]["durable_stop_allowed"] is False
    assert payload["stage_closure"]["outcome_kind"] == "stage_closure_decision_missing"
    assert payload["stage_closure"]["next_transition"] == "run_stage_closure_terminalizer"
    assert "accepted_submission_milestone_candidate" in payload["stage_closure"][
        "known_blockers"
    ]
    assert payload["current_package"]["status"] == "missing"
    assert payload["current_package"]["package_kind"] == "current_package"
    assert payload["current_package"]["can_submit"] is False
    assert payload["opl_route_command"]["command_kind"] == "resume_stage"
    assert payload["next_owner_or_human_decision"]["next_owner"] == (
        "mission_executor"
    )
    assert payload["next_owner_or_human_decision"]["route_command"] == (
        "resume_stage"
    )
    assert payload["paper_mission_transaction_readback"]["source"] == (
        "paper_mission_consumption_ledger"
    )
    assert payload["paper_mission_transaction"]["stage_id"] == (
        "submission_milestone_candidate"
    )
    assert payload["paper_mission_run"]["mission_state"] == "consumed"
    assert payload["paper_mission_run"]["paper_mission_transaction"] == (
        payload["paper_mission_transaction"]
    )
    assert payload["paper_mission_consumption_ledger_readback"]["source_ref"].endswith(
        f"/paper_mission_consumption_ledger/sat-current/{study_id}/consume_record.json"
    )
    assert payload["mutation_policy"]["writes_authority"] is False
    assert payload["mutation_policy"]["writes_runtime"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def _unique_surface_action_ids(value: object, surface_kind: str) -> set[str]:
    if isinstance(value, dict):
        ids = (
            {str(value["action_id"])}
            if value.get("surface_kind") == surface_kind and value.get("action_id")
            else set()
        )
        for item in value.values():
            ids.update(_unique_surface_action_ids(item, surface_kind))
        return ids
    if isinstance(value, list):
        ids: set[str] = set()
        for item in value:
            ids.update(_unique_surface_action_ids(item, surface_kind))
        return ids
    return set()
