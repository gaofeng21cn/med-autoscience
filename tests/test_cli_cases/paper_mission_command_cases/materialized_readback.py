from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

from tests.study_runtime_test_helpers import write_synced_submission_delivery

from med_autoscience.controllers.next_action_envelope import SURFACE_KIND
from med_autoscience.paper_mission_stage_closure_ledger import (
    latest_paper_mission_stage_closure_decision_readback,
    write_paper_mission_stage_closure_decision,
)
from tests.test_cli_cases.paper_mission_command_helpers import *  # noqa: F401,F403


def test_paper_mission_inspect_materialized_readback_defaults_to_no_live_opl_probe(
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
    def fail_live_probe(**_kwargs):
        raise AssertionError("materialized inspect should not request OPL live probe by default")

    monkeypatch.setattr(
        readback_module,
        "_matching_opl_runtime_live_probe",
        fail_live_probe,
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
    assert payload["opl_runtime_readback_status"] == "waiting_for_opl_runtime_live_readback"
    assert payload["opl_runtime_carrier_readback"]["runtime_readback_status"] == "missing"


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
                                "mas_impact_receipt": {
                                    "surface_kind": "mas_impact_receipt",
                                    "schema_version": 1,
                                    "receipt_status": "requires_mas_owner_consumption",
                                    "study_id": study_id,
                                    "paper_mission_transaction_ref": transaction[
                                        "transaction_id"
                                    ],
                                    "opl_route_command_ref": route_command_ref,
                                    "receipt_ref": (
                                        f"opl://stage-attempts/{stage_attempt_id}"
                                        "/mas-impact"
                                    ),
                                    "next_legal_action": "consume_opl_transition_receipt",
                                    "forbidden_next_action": (
                                        "synonymous_route_back_redrive"
                                    ),
                                    "can_claim_paper_progress": False,
                                    "can_claim_publication_ready": False,
                                },
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
                                },
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
    receipt_evidence = carrier_readback["receipt_evidence"]
    assert receipt_evidence["receipt_kind"] == "opl_transition_receipt"
    assert receipt_evidence["receipt_ref"] == (
        f"opl://stage-attempts/{stage_attempt_id}"
    )
    assert receipt_evidence["impact_receipt_kind"] == "mas_impact_receipt"
    assert receipt_evidence["impact_receipt_ref"] == (
        f"opl://stage-attempts/{stage_attempt_id}/mas-impact"
    )
    assert receipt_evidence["runtime_closeout_ref"] == (
        f"opl://family-runtime/tasks/{task_id}/terminal-closeout-readback"
    )
    assert receipt_evidence["can_claim_paper_progress"] is False
    consumption = carrier_readback["mas_receipt_consumption"]
    assert consumption["status"] == "requires_mas_owner_consumption"
    assert consumption["next_legal_action"] == "consume_opl_transition_receipt"
    assert consumption["forbidden_next_action"] == (
        "synonymous_route_back_redrive"
    )
    assert consumption["durable_stop_allowed"] is False
    assert consumption["can_claim_publication_ready"] is False
    assert consumption["can_claim_paper_progress"] is False


def test_transaction_readback_reattaches_runtime_receipt_after_owner_answer_route(
    tmp_path: Path,
) -> None:
    from med_autoscience.cli_parts.paper_mission_command_parts.transaction_readback import (
        _paper_mission_transaction_readback,
    )

    study_id = "obesity_multicenter_phenotype_atlas"
    mission_id = f"paper-mission::{study_id}::route-back"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    calls: list[str] = []

    def attach_runtime_readback(
        *,
        readback: dict,
        study_root: Path,
        enable_opl_live_probe: bool = False,
        opl_bin: str | Path | None = None,
    ) -> dict:
        payload = dict(readback)
        carrier = payload["opl_runtime_carrier"]
        calls.append(carrier["work_unit_id"])
        payload["opl_runtime_carrier_readback"] = {
            "surface_kind": "paper_mission_opl_runtime_carrier_readback",
            "schema_version": 1,
            "carrier_status": "opl_runtime_terminal_readback_observed",
            "runtime_readback_status": "terminal_closeout_observed",
            "domain_ready_verdict": "domain_gate_pending",
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
            "authority_materialized": False,
            "terminal_closeout": {
                "surface_kind": "stage_attempt_closeout_packet",
                "closeout_ref": f"closeout://{carrier['work_unit_id']}",
                "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
                "stage_attempt_id": f"sat-{len(calls)}",
                "work_unit_id": carrier["work_unit_id"],
            },
        }
        payload["opl_runtime_readback_status"] = (
            "opl_runtime_terminal_readback_observed"
        )
        return payload

    readback = _paper_mission_transaction_readback(
        mission_id=mission_id,
        study_id=study_id,
        objective="Ensure owner-answer carrier gets its own live readback.",
        paper_mission_command="inspect",
        study_root=tmp_path / "workspace" / "studies" / study_id,
        mission={"paper_mission_transaction": transaction},
        enable_opl_live_probe=True,
        attach_runtime_readback=attach_runtime_readback,
    )

    assert len(calls) == 2
    assert calls[0] == "continue paper-facing submission milestone work"
    assert calls[1] == readback["opl_runtime_carrier"]["work_unit_id"]
    assert readback["source"] == "terminal_owner_gate_owner_answer"
    assert readback["opl_runtime_carrier_readback"]["terminal_closeout"][
        "work_unit_id"
    ] == calls[1]


def test_authority_consumed_candidate_delta_suppresses_stale_terminal_owner_gate(
    tmp_path: Path,
) -> None:
    from med_autoscience.cli_parts.paper_mission_command_parts.transaction_readback import (
        _paper_mission_transaction_readback,
    )

    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    mission_id = f"paper-mission::{study_id}::write-repair"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    paper_delta_ref = "paper-facing-delta://dm003/write-repair-candidate"

    def attach_runtime_readback(
        *,
        readback: dict,
        study_root: Path,
        enable_opl_live_probe: bool = False,
        opl_bin: str | Path | None = None,
    ) -> dict:
        del study_root, enable_opl_live_probe, opl_bin
        payload = dict(readback)
        payload["opl_runtime_carrier_readback"] = {
            "surface_kind": "paper_mission_opl_runtime_carrier_readback",
            "schema_version": 1,
            "carrier_status": "opl_runtime_terminal_readback_observed",
            "runtime_readback_status": "terminal_closeout_observed",
            "domain_ready_verdict": "domain_gate_pending",
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
            "authority_materialized": False,
            "terminal_closeout": {
                "surface_kind": "stage_attempt_closeout_packet",
                "closeout_ref": "closeout://stale-domain-gate",
                "blocked_reason": "domain_gate_pending",
                "stage_attempt_id": "sat_stale_domain_gate",
                "work_unit_id": "submission_milestone_candidate",
            },
        }
        payload["opl_runtime_readback_status"] = (
            "opl_runtime_terminal_readback_observed"
        )
        return payload

    readback = _paper_mission_transaction_readback(
        mission_id=mission_id,
        study_id=study_id,
        objective="Consume concrete DM003 paper-facing delta.",
        paper_mission_command="consume-candidate",
        study_root=tmp_path / "workspace" / "studies" / study_id,
        mission=None,
        authority_consume_readback={
            "status": "accepted_candidate",
            "consume_result": {
                "status": "accepted",
                "outcome": "accepted_candidate",
                "paper_facing_delta_ref": paper_delta_ref,
                "canonical_paper_or_artifact_delta_ref": paper_delta_ref,
                "authority_materialized": False,
            },
            "paper_mission_transaction": transaction,
        },
        attach_runtime_readback=attach_runtime_readback,
    )

    assert readback["transaction_state"] == "accepted_submission_milestone_candidate"
    assert readback["stage_terminal_decision"]["decision_kind"] == "continue_same_stage"
    assert readback["opl_route_command"]["command_kind"] == "resume_stage"
    assert readback["terminal_owner_gate"] is None
    assert readback["terminal_owner_gate_owner_answer_readback"] is None
    assert readback["source"] != "terminal_owner_gate_owner_answer"


def test_consumption_ledger_candidate_delta_suppresses_older_terminal_owner_gate(
    tmp_path: Path,
) -> None:
    from med_autoscience.cli_parts.paper_mission_command_parts.transaction_readback import (
        _paper_mission_transaction_readback,
    )

    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    closeout_ref = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_attempts"
        / "sat-stale"
        / study_id
        / "stage_attempt_closeout_packet.json"
    )
    closeout_ref.parent.mkdir(parents=True)
    closeout_ref.write_text("{}", encoding="utf-8")
    source_ref = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / study_id
        / "consume_record.json"
    )
    source_ref.parent.mkdir(parents=True)
    source_ref.write_text("{}", encoding="utf-8")
    os.utime(closeout_ref, (1_000_000_000, 1_000_000_000))
    os.utime(source_ref, (2_000_000_000, 2_000_000_000))
    mission_id = f"paper-mission::{study_id}::write-repair"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    paper_delta_ref = "paper-facing-delta://dm003/write-repair-candidate"

    def attach_runtime_readback(
        *,
        readback: dict,
        study_root: Path,
        enable_opl_live_probe: bool = False,
        opl_bin: str | Path | None = None,
    ) -> dict:
        del study_root, enable_opl_live_probe, opl_bin
        return {
            **readback,
            "opl_runtime_carrier_readback": {
                "surface_kind": "paper_mission_opl_runtime_carrier_readback",
                "schema_version": 1,
                "carrier_status": "opl_runtime_terminal_readback_observed",
                "runtime_readback_status": "terminal_closeout_observed",
                "domain_ready_verdict": "domain_gate_pending",
                "can_claim_paper_progress": False,
                "can_claim_runtime_ready": False,
                "authority_materialized": False,
                "terminal_closeout": {
                    "surface_kind": "stage_attempt_closeout_packet",
                    "closeout_ref": str(closeout_ref.relative_to(workspace_root)),
                    "blocked_reason": "domain_gate_pending",
                    "stage_attempt_id": "sat-stale",
                    "work_unit_id": "submission_milestone_candidate",
                },
            },
            "opl_runtime_readback_status": "opl_runtime_terminal_readback_observed",
        }

    readback = _paper_mission_transaction_readback(
        mission_id=mission_id,
        study_id=study_id,
        objective="Consume concrete DM003 paper-facing delta.",
        paper_mission_command="inspect",
        study_root=study_root,
        mission=None,
        transaction_override=transaction,
        transaction_source_override="paper_mission_consumption_ledger",
        authority_consume_readback={
            "status": "accepted_candidate",
            "source_ref": str(source_ref),
            "consume_result": {
                "status": "accepted",
                "outcome": "accepted_candidate",
                "paper_facing_delta_ref": paper_delta_ref,
            },
        },
        attach_runtime_readback=attach_runtime_readback,
    )

    assert readback["transaction_state"] == "accepted_submission_milestone_candidate"
    assert readback["terminal_owner_gate"] is None
    assert readback["terminal_owner_gate_owner_answer_readback"] is None


def test_consumption_ledger_inspect_routes_transaction_bound_route_back_evidence_to_owner_consumption(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_id = f"paper-mission::{study_id}::route-back-evidence-regression"
    base_transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    package_path = _write_submission_milestone_package(
        workspace_root=workspace_root,
        study_id=study_id,
        mission_id=mission_id,
        base_transaction=base_transaction,
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
                / "sat-route-back-evidence"
            ),
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    consume_payload = json.loads(capsys.readouterr().out)
    assert consume_exit_code == 0
    current_transaction = consume_payload["paper_mission_transaction_readback"][
        "paper_mission_transaction"
    ]

    closeout_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_attempts"
        / "sat-route-back-evidence"
        / study_id
    )
    closeout_root.mkdir(parents=True)
    route_back_ref = (
        "ops/medautoscience/paper_mission_stage_attempts/"
        f"sat-route-back-evidence/{study_id}/route_back_evidence_packet.json"
    )
    (closeout_root / "route_back_evidence_packet.json").write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_stage_route_back_evidence_packet",
                "study_id": study_id,
                "route_back_evidence_ref": route_back_ref,
                "next_forced_paper_action": {
                    "action_kind": "owner_consume_route_back_evidence_then_write_repair"
                },
            }
        ),
        encoding="utf-8",
    )
    (closeout_root / "stage_attempt_closeout_packet.json").write_text(
        json.dumps(
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "status": "non_advancing_route_back_evidence_candidate",
                "study_id": study_id,
                "stage_id": current_transaction["opl_route_command"]["target"],
                "stage_attempt_id": "sat-route-back-evidence",
                "stage_packet_ref": current_transaction["transaction_id"],
                "work_unit_id": None,
                "work_unit_fingerprint": None,
                "route_impact": {
                    "owner_answer_kind": "route_back_evidence_ref",
                    "route_back_evidence_ref": route_back_ref,
                    "can_claim_paper_progress": False,
                },
                "closeout_refs": [
                    {
                        "ref_kind": "route_back_evidence_packet",
                        "workspace_relative_ref": route_back_ref,
                    }
                ],
                "authority_boundary": {
                    "candidate_is_authority": False,
                    "writes_authority_surface": False,
                    "writes_publication_eval": False,
                    "writes_controller_decision": False,
                    "writes_owner_receipt": False,
                    "writes_typed_blocker": False,
                    "writes_human_gate": False,
                    "writes_current_package": False,
                    "writes_runtime_queue": False,
                    "writes_provider_attempt": False,
                    "writes_yang_authority": False,
                },
            }
        ),
        encoding="utf-8",
    )

    inspect_exit_code = cli.main(
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
    inspect_payload = json.loads(capsys.readouterr().out)

    assert inspect_exit_code == 0
    assert inspect_payload["paper_mission_current_transaction_source"] == (
        "paper_mission_consumption_ledger"
    )
    assert inspect_payload["opl_runtime_carrier_readback"]["terminal_closeout"][
        "stage_attempt_id"
    ] == "sat-route-back-evidence"
    assert inspect_payload["opl_runtime_carrier_readback"][
        "mas_receipt_consumption"
    ]["next_legal_action"] == (
        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
    )
    assert inspect_payload["stage_closure_decision"]["outcome"]["kind"] == (
        "next_stage_transition"
    )
    assert inspect_payload["stage_closure_decision"]["outcome"][
        "transition_kind"
    ] == "route_back_candidate_checkpoint"
    assert inspect_payload["next_action"]["action_family"] == (
        "paper.stage_closure.owner_consumption"
    )
    assert inspect_payload["next_action"]["action_type"] == (
        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
    )
    assert inspect_payload["next_action"]["authority_boundary"][
        "can_submit_to_opl_runtime"
    ] is False
    assert inspect_payload["durable_mission_stop_guard"][
        "durable_stop_allowed"
    ] is False


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
    assert inspect_payload["next_action"]["action_family"] == (
        "paper.stage_closure.owner_consumption"
    )
    assert inspect_payload["next_action"]["action_kind"] == "owner_consumption"
    assert inspect_payload["next_action"]["action_type"] == (
        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
    )
    assert inspect_payload["next_action"]["owner"] == "MedAutoScience"
    assert inspect_payload["next_action"]["authority_boundary"][
        "can_submit_to_opl_runtime"
    ] is False
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


def test_paper_mission_inspect_projects_ledger_typed_blocker_owner_gate(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260630Tledger-typed-blocker"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::submission-milestone::typed-blocker"
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
                "objective": "Consumed milestone with typed blocker stage closure.",
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
                "paper_mission_transaction": one_shot_transaction,
                "one_shot_migration_readback": {
                    "required_output": {
                        "next_owner": "one-person-lab",
                        "work_unit_id": "submission_milestone_candidate",
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
    consume_exit_code = cli.main(
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
    assert consume_exit_code == 0
    consume_payload = json.loads(capsys.readouterr().out)
    current_transaction = consume_payload["paper_mission_transaction_readback"][
        "paper_mission_transaction"
    ]
    stage_closure_ref = "typed-blocker:dm002:submission-authority-human-gate"
    write_paper_mission_stage_closure_decision(
        output_root=(
            workspace_root
            / "ops"
            / "medautoscience"
            / "paper_mission_stage_closure"
            / "sat-current"
        ),
        study_id=study_id,
        decision={
            "decision_ref": stage_closure_ref,
            "study_id": study_id,
            "stage_id": "submission_milestone_candidate",
            "work_unit_id": "submission_blocker_human_gate",
            "outcome": {
                "kind": "typed_blocker",
                "blocker_id": "submission_authority_human_gate_required",
                "typed_blocker_evidence_ref": stage_closure_ref,
                "authority_materialized": False,
            },
        },
        source_readback={
            **consume_payload,
            "paper_mission_transaction": current_transaction,
        },
        source="test",
        forbidden_authority_writes=FORBIDDEN_AUTHORITY_RELATIVE_PATHS,
        forbidden_authority_claims=("publication_ready", "owner_receipt_written"),
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
    assert payload["stage_closure_outcome"] == "typed_blocker"
    gate = payload["terminal_owner_gate"]
    assert gate["owner"] == "mas_authority_kernel"
    assert gate["gate_kind"] == "typed_blocker"
    assert gate["typed_blocker_ref"] == stage_closure_ref
    assert gate["legal_next_action"] == "route_to_owner_or_human_gate"
    assert gate["can_claim_paper_progress"] is False
    assert gate["can_claim_runtime_ready"] is False
    assert payload["next_owner_or_human_decision"] == {
        "kind": "owner_or_route",
        "next_owner": "mas_authority_kernel",
        "human_decision_required": False,
        "summary": "submission_authority_human_gate_required",
        "typed_blocker_ref": stage_closure_ref,
        "can_execute": False,
        "can_authorize_provider_admission": False,
    }
    authority_readback = payload["terminal_owner_gate_authority_readback"]
    assert authority_readback["status"] == "owner_answer_required"
    assert authority_readback["next_owner"] == "mas_authority_kernel"
    assert authority_readback["authority_boundary"]["can_write_typed_blocker"] is False
    assert payload["paper_mission_transaction_readback"]["terminal_owner_gate"] == gate
    assert payload["next_action"]["owner"] == "mas_authority_kernel"
    assert payload["next_action"]["authority_boundary"][
        "can_claim_publication_ready"
    ] is False
    assert payload["mutation_policy"]["writes_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_stage_closure_readback_accepts_latest_followthrough_for_base_transaction(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    study_id = "obesity_multicenter_phenotype_atlas"
    base_ref = (
        "paper-mission-transaction::obesity_multicenter_phenotype_atlas::"
        "submission_milestone_candidate::paper-mission::"
        "obesity_multicenter_phenotype_atlas::paper_mission_import::one-shot-migration"
    )
    followthrough_ref = (
        "paper-mission-transaction::obesity_multicenter_phenotype_atlas::"
        "submission_milestone_candidate::followthrough::followthrough-01::"
        "paper-mission::obesity_multicenter_phenotype_atlas::"
        "paper_mission_import::one-shot-migration"
    )

    write_paper_mission_stage_closure_decision(
        output_root=(
            workspace_root
            / "ops"
            / "medautoscience"
            / "paper_mission_stage_closure"
            / "f6_submission_stage_packet"
        ),
        study_id=study_id,
        decision={
            "stage_id": "submission_milestone_candidate",
            "work_unit_id": "submission_milestone_candidate",
            "outcome": {"kind": "next_stage_transition"},
        },
        source_readback={
            "mission_id": "mission-base",
            "paper_mission_transaction": {
                "transaction_id": base_ref,
                "stage_id": "submission_milestone_candidate",
            },
        },
        source="test",
        forbidden_authority_writes=FORBIDDEN_AUTHORITY_RELATIVE_PATHS,
        forbidden_authority_claims=("publication_ready",),
    )
    output_manifest = write_paper_mission_stage_closure_decision(
        output_root=(
            workspace_root
            / "ops"
            / "medautoscience"
            / "paper_mission_stage_closure"
            / "paper_mission_terminalize_stage"
        ),
        study_id=study_id,
        decision={
            "stage_id": "submission_milestone_candidate::followthrough::followthrough-01",
            "work_unit_id": "submission_milestone_candidate::followthrough::followthrough-01",
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "route_back_candidate_checkpoint",
            },
        },
        source_readback={
            "mission_id": "mission-followthrough",
            "paper_mission_transaction": {
                "transaction_id": followthrough_ref,
                "stage_id": "submission_milestone_candidate::followthrough::followthrough-01",
            },
        },
        source="test",
        forbidden_authority_writes=FORBIDDEN_AUTHORITY_RELATIVE_PATHS,
        forbidden_authority_claims=("publication_ready",),
    )

    readback = latest_paper_mission_stage_closure_decision_readback(
        workspace_root=workspace_root,
        study_id=study_id,
        transaction_ref=base_ref,
    )

    assert readback is not None
    assert readback["decision_ref"] == output_manifest["stage_closure_decision_ref"]
    assert readback["paper_mission_transaction_ref"] == followthrough_ref
    assert readback["stage_id"] == (
        "submission_milestone_candidate::followthrough::followthrough-01"
    )
    assert readback["can_claim_paper_progress"] is False


def test_stage_closure_readback_accepts_base_for_followthrough_transaction(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    base_ref = (
        "paper-mission-transaction::003-dpcc-primary-care-phenotype-treatment-gap::"
        "write::paper-mission::003-dpcc-primary-care-phenotype-treatment-gap::"
        "medical_prose_write_repair_publication_gate_replay::one-shot-migration"
    )
    followthrough_ref = (
        "paper-mission-transaction::003-dpcc-primary-care-phenotype-treatment-gap::"
        "write::paper-mission::003-dpcc-primary-care-phenotype-treatment-gap::"
        "medical_prose_write_repair_publication_gate_replay::one-shot-migration"
        "::followthrough::89b46ab394eb"
    )

    output_manifest = write_paper_mission_stage_closure_decision(
        output_root=(
            workspace_root
            / "ops"
            / "medautoscience"
            / "paper_mission_stage_closure"
            / "paper_mission_terminalize_stage"
        ),
        study_id=study_id,
        decision={
            "stage_id": "write",
            "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "route_back_candidate_checkpoint",
            },
        },
        source_readback={
            "mission_id": "mission-base",
            "paper_mission_transaction": {
                "transaction_id": base_ref,
                "stage_id": "write",
            },
        },
        source="test",
        forbidden_authority_writes=FORBIDDEN_AUTHORITY_RELATIVE_PATHS,
        forbidden_authority_claims=("publication_ready",),
    )

    readback = latest_paper_mission_stage_closure_decision_readback(
        workspace_root=workspace_root,
        study_id=study_id,
        transaction_ref=followthrough_ref,
    )

    assert readback is not None
    assert readback["decision_ref"] == output_manifest["stage_closure_decision_ref"]
    assert readback["paper_mission_transaction_ref"] == base_ref
    assert readback["stage_id"] == "write"
    assert readback["can_claim_paper_progress"] is False


def test_consumption_ledger_route_back_projection_uses_stage_closure_ledger() -> None:
    commands = importlib.import_module("med_autoscience.cli_parts.paper_mission_commands")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    transaction = {
        "transaction_id": (
            "paper-mission-transaction::003-dpcc-primary-care-phenotype-treatment-gap::"
            "write::paper-mission::003-dpcc-primary-care-phenotype-treatment-gap::"
            "medical_prose_write_repair_publication_gate_replay::one-shot-migration"
            "::followthrough::89b46ab394eb"
        ),
        "study_id": study_id,
        "stage_id": "write",
        "stage_terminal_decision": {
            "decision_kind": "continue_same_stage",
            "next_owner": "write",
            "next_work_unit": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
        },
    }
    stage_closure_decision = {
        "surface_kind": "mas_stage_closure_decision",
        "projection_status": "terminalizer_outcome_observed",
        "source_surface_kind": "paper_mission_stage_closure_ledger",
        "decision_ref": "/tmp/dm003/stage_closure_decision.json",
        "stage_id": "write",
        "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
        "outcome": {
            "kind": "next_stage_transition",
            "transition_kind": "route_back_candidate_checkpoint",
            "next_owner": "MedAutoScience",
            "next_action": "consume_route_back_checkpoint_or_materialize_terminalizer_outcome",
            "authority_materialized": False,
        },
        "authority_boundary": {
            "authority_materialized": False,
            "writes_owner_receipt": False,
            "writes_typed_blocker": False,
            "writes_human_gate": False,
            "writes_current_package": False,
            "writes_submission_ready_package": False,
            "writes_runtime_queue_or_provider_attempt": False,
        },
    }

    payload = commands._consumption_ledger_route_back_projection(
        transaction_readback={
            "paper_mission_transaction": transaction,
            "stage_terminal_decision": transaction["stage_terminal_decision"],
            "opl_route_command": {
                "command_kind": "resume_stage",
                "target": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
            },
            "opl_runtime_carrier": {},
            "opl_runtime_carrier_readback": {},
            "opl_runtime_readback_status": None,
            "terminal_owner_gate_owner_answer_readback": {
                "owner_answer_shape": "route_back_evidence_ref"
            },
            "next_owner_or_human_decision": {
                "kind": "owner_or_route",
                "next_owner": "write",
            },
            "transaction_state": "accepted_submission_milestone_candidate",
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
        },
        consumption_readback={
            "consume_candidate_status": "accepted_submission_milestone_candidate",
            "opl_route_handoff": {},
        },
        base_readback={"study_id": study_id},
        stage_closure_ledger_readback=stage_closure_decision,
    )

    assert payload is not None
    assert payload["stage_closure_decision"]["projection_status"] == (
        "terminalizer_outcome_observed"
    )
    assert payload["stage_closure_decision_ref"] == (
        "/tmp/dm003/stage_closure_decision.json"
    )
    assert payload["stage_closure_outcome"] == "next_stage_transition"
    assert payload["canonical_next_action_source"] == "stage_closure.next_action"
    assert payload["next_action"]["work_unit_id"] == (
        "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
    )


def test_paper_mission_inspect_prefers_latest_governed_consumption_ledger_transaction(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    write_synced_submission_delivery(
        study_root=study_root,
        quest_root=workspace_root / "managed-runtime" / "quests" / "quest-003",
        include_submission_checklist=False,
    )
    current_package_manifest = (
        study_root
        / "manuscript"
        / "current_package"
        / "audit"
        / "submission_manifest.json"
    )
    current_package_manifest.parent.mkdir(parents=True, exist_ok=True)
    current_package_manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_signature": "source::dm003-current",
                "package_kind": "submission_ready_package",
                "can_submit": True,
                "quality_gate_status": "clear",
                "known_blockers": [],
                "generated_from_current_source": True,
            }
        ),
        encoding="utf-8",
    )
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
    consume_record_ref = consume_root / study_id / "consume_record.json"
    os.utime(stale_receipt_ref, (2_000_000_000, 2_000_000_000))
    os.utime(consume_record_ref, (3_000_000_000, 3_000_000_000))
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
    assert payload["stage_closure"]["outcome_kind"] == "next_stage_transition"
    assert payload["stage_closure"]["next_transition"] != "complete_mission"
    assert "receipt_owner_consumption_readback" not in payload
    assert payload["next_action"]["action_family"] != "mission.complete"
    assert payload["current_package"]["status"] == "missing"
    assert payload["current_package"]["package_kind"] == "submission_ready_package"
    assert payload["current_package"]["can_submit"] is True
    assert payload["current_package"]["known_blockers"] == []
    assert payload["current_package"]["generated_from_current_source"] is True
    assert payload["current_package"]["root"] == str(
        study_root / "manuscript" / "current_package"
    )
    assert payload["current_package"]["zip_path"] == str(
        study_root / "manuscript" / "current_package.zip"
    )
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


def test_stage_closure_owner_receipt_suppresses_same_work_unit_domain_transition() -> None:
    materialized_readback = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_command_parts.materialized_mission_readback"
    )
    same_work_unit_next_action = {
        "surface_kind": SURFACE_KIND,
        "action_type": "request_opl_stage_attempt",
        "action_family": "paper.review.ai_reviewer",
        "stage_id": "review",
        "work_unit_id": "ai_reviewer_medical_prose_quality_review",
        "owner": "ai_reviewer",
    }
    stage_closure_decision = {
        "stage_id": "review",
        "work_unit_id": "ai_reviewer_medical_prose_quality_review",
        "outcome": {
            "kind": "owner_receipt",
            "package_kind": "current_package",
            "can_submit": False,
        },
    }

    assert materialized_readback._stage_closure_suppresses_domain_transition_next_action(
        stage_closure_decision=stage_closure_decision,
        next_action=None,
        domain_transition_next_action=same_work_unit_next_action,
    )
    assert materialized_readback._stage_closure_suppresses_domain_transition_next_action(
        stage_closure_decision=stage_closure_decision,
        next_action={
            "surface_kind": SURFACE_KIND,
            "action_family": "paper.package.submission_minimal",
            "work_unit_id": "submission_authority_owner_verdict",
        },
        domain_transition_next_action=same_work_unit_next_action,
    )
    assert not materialized_readback._stage_closure_suppresses_domain_transition_next_action(
        stage_closure_decision=stage_closure_decision,
        next_action={
            "surface_kind": SURFACE_KIND,
            "action_family": "paper.stage_closure.owner_consumption",
            "work_unit_id": "ai_reviewer_medical_prose_quality_review",
        },
        domain_transition_next_action=same_work_unit_next_action,
    )
    assert not materialized_readback._stage_closure_suppresses_domain_transition_next_action(
        stage_closure_decision=stage_closure_decision,
        next_action=None,
        domain_transition_next_action={
            **same_work_unit_next_action,
            "work_unit_id": "submission_package_finalize",
        },
    )
    assert not materialized_readback._stage_closure_suppresses_domain_transition_next_action(
        stage_closure_decision={
            **stage_closure_decision,
            "outcome": {
                "kind": "owner_receipt",
                "package_kind": "submission_ready_package",
                "can_submit": True,
            },
        },
        next_action=None,
        domain_transition_next_action=same_work_unit_next_action,
    )
