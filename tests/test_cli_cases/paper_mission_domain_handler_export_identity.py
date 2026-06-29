from __future__ import annotations

import importlib
import json
from pathlib import Path

from med_autoscience.paper_mission_opl_carrier import paper_mission_opl_runtime_carrier

from .paper_mission_commands import (
    _paper_mission_forbidden_write_guard,
    _paper_mission_transaction_payload,
    _write_profile_with_study,
)

def test_domain_handler_export_enriches_current_governed_consumption_handoff_identity(
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
        / "20260623T2032Z"
        / study_id
    )
    mission_root.mkdir(parents=True)
    old_mission_id = f"paper-mission::{study_id}::gate-clearing::one-shot-migration"
    current_transaction = _paper_mission_transaction_payload(
        mission_id=old_mission_id,
        study_id=study_id,
        decision_kind="advance",
    )
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(
            {
                "schema_version": "paper-mission-run.v1",
                "mission_id": old_mission_id,
                "study_id": study_id,
                "objective": "Older materialized mission readback.",
                "mission_state": "candidate_ready_for_consumption",
                "artifact_delta_ledger": [],
                "source_refs": [],
                "authority_touchpoints": [],
                "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
                "consume_result": {"status": "accepted"},
                "claim_permissions": {
                    "can_claim_artifact_delta": True,
                    "can_claim_owner_handoff": True,
                    "can_claim_publication_ready": False,
                    "can_claim_current_package": False,
                    "can_claim_owner_receipt_written": False,
                },
                "one_shot_migration_readback": {
                    "required_output": {
                        "next_owner": "analysis-campaign",
                        "kind": "owner_decision_packet_or_consumable_artifact_delta",
                    },
                    "consume_candidate_status": "accepted",
                },
                "paper_mission_transaction": current_transaction,
            }
        ),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps({"candidate_id": "pmc-old", "study_id": study_id}),
        encoding="utf-8",
    )
    handoff_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / "20260624Tnew"
        / study_id
    )
    handoff_root.mkdir(parents=True)
    current_transaction_ref = current_transaction["transaction_id"]
    current_carrier = paper_mission_opl_runtime_carrier(current_transaction)
    handoff = {
        "surface_kind": "mas_paper_mission_opl_route_handoff_record",
        "schema_version": 1,
        "source": "paper-mission-consumption-ledger",
        "study_id": study_id,
        "mission_id": f"paper-mission::{study_id}::route-back::new",
        "candidate_ref": str(handoff_root / "package_manifest.json"),
        "candidate_id": "pmc-new",
        "status": "accepted_candidate",
        "selected_outcome": "accepted_candidate",
        "handoff_status": "ready_for_opl_route_command",
        "next_owner": "mission_executor",
        "paper_mission_transaction_ref": current_transaction_ref,
        "transaction_state": current_transaction["transaction_state"],
        "stage_terminal_decision_ref": (
            f"{current_transaction_ref}#stage_terminal_decision"
        ),
        "stage_terminal_decision": current_transaction["stage_terminal_decision"],
        "opl_route_command_ref": f"{current_transaction_ref}#opl_route_command",
        "opl_route_command": current_transaction["opl_route_command"],
        "opl_runtime_carrier": current_carrier,
        "route_command_kind": current_transaction["opl_route_command"]["command_kind"],
        "route_target": current_transaction["opl_route_command"]["target"],
        "transaction_materialized": True,
        "can_submit_to_opl_runtime": True,
        "can_claim_opl_runtime_enqueued": False,
        "can_claim_opl_stage_run_created": False,
        "can_claim_provider_running": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_boundary": {
            "writes_authority_surface": False,
            "writes_publication_eval": False,
            "writes_controller_decision": False,
            "can_write_owner_receipt": False,
            "can_write_typed_blocker": False,
            "can_write_human_gate": False,
            "can_write_current_package": False,
            "can_write_paper_body": False,
            "can_write_runtime_queue": False,
            "can_write_opl_outbox": False,
            "can_write_opl_event": False,
            "can_write_opl_stage_run": False,
            "can_write_provider_attempt": False,
        },
        "forbidden_authority_claims": ["paper_progress", "runtime_ready"],
        "forbidden_authority_writes": ["owner receipt", "OPL runtime queue"],
    }
    (handoff_root / "opl_route_handoff.json").write_text(
        json.dumps(handoff),
        encoding="utf-8",
    )

    exit_code = cli.main(
        ["domain-handler", "export", "--profile", str(profile_path), "--format", "json"]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    paper_mission_task = next(
        task
        for task in payload["paper_mission_default_tasks"]
        if task["task_kind"] == "paper_mission/start_or_resume"
        and task["study_id"] == study_id
    )
    task_handoff = paper_mission_task["opl_route_handoff"]
    task_payload = paper_mission_task["payload"]
    assert task_handoff == task_payload["opl_route_handoff"]
    assert paper_mission_task["opl_route_handoff_record"] == task_handoff
    assert task_handoff["paper_mission_transaction_ref"] == current_transaction_ref
    assert task_handoff["route_identity_key"] == current_carrier["route_identity_key"]
    assert task_handoff["attempt_idempotency_key"] == current_carrier[
        "attempt_idempotency_key"
    ]
    assert task_handoff["request_idempotency_key"] == current_carrier[
        "request_idempotency_key"
    ]
    assert task_payload["route_identity_key"] == current_carrier["route_identity_key"]
    assert task_payload["attempt_idempotency_key"] == current_carrier[
        "attempt_idempotency_key"
    ]
    assert task_payload["request_idempotency_key"] == current_carrier[
        "request_idempotency_key"
    ]
    assert paper_mission_task["route_identity_key"] == current_carrier[
        "route_identity_key"
    ]
    assert task_handoff["source_ref"].endswith(
        "/paper_mission_consumption_ledger/20260624Tnew/"
        f"{study_id}/opl_route_handoff.json"
    )
    assert task_handoff["source_surface_kind"] == (
        "mas_paper_mission_opl_route_handoff_record"
    )
    assert paper_mission_task["paper_mission_default_handoff_source"] == (
        "paper_mission_consumption_ledger"
    )
    assert paper_mission_task["workspace_root"] == str(workspace_root)
    assert paper_mission_task["domain_workspace_root"] == str(workspace_root)
    assert paper_mission_task["profile_ref"] == str(profile_path)
    assert task_payload["paper_mission_default_handoff_source"] == (
        "paper_mission_consumption_ledger"
    )
    assert task_payload["workspace_root"] == str(workspace_root)
    assert task_payload["domain_workspace_root"] == str(workspace_root)
    assert task_payload["profile_ref"] == str(profile_path)
    assert task_payload["paper_mission_default_handoff_ref"] == task_handoff[
        "source_ref"
    ]
    assert task_handoff["workspace_root"] == str(workspace_root)
    assert task_handoff["domain_workspace_root"] == str(workspace_root)
    assert task_handoff["profile_ref"] == str(profile_path)
    assert task_payload["route_command_kind"] == "start_next_stage"
    assert task_payload["route_target"] == "publication_gate_replay"
    assert task_payload["paper_mission"]["candidate_manifest_ref"].endswith(
        "/paper_mission_one_shot_migration/20260623T2032Z/"
        f"{study_id}/candidate_manifest.json"
    )
    assert task_payload["stage_packet_ref"] == current_carrier["stage_run_ref"]
    assert task_payload["provider_completion_is_domain_completion"] is False
    assert task_handoff["can_claim_paper_progress"] is False
    assert task_handoff["can_claim_runtime_ready"] is False
    pending_handoff_task = next(
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "paper_mission/stage-outcome"
        and task["study_id"] == study_id
    )
    assert pending_handoff_task["reason"] == (
        "paper_mission_consumption_opl_route_handoff_pending"
    )
    assert pending_handoff_task["domain_owner"] == "one-person-lab"
    assert pending_handoff_task["dispatch_owner"] == "one-person-lab"
    assert pending_handoff_task["queue_owner"] == "one-person-lab"
    assert pending_handoff_task["domain_truth_owner"] == "med-autoscience"
    assert pending_handoff_task["opl_route_handoff"] == task_handoff
    assert pending_handoff_task["payload"]["opl_route_handoff"] == task_handoff
    assert pending_handoff_task["payload"]["opl_domain_progress_transition_request"] == current_carrier
    assert pending_handoff_task["payload"]["provider_admission_requires_opl_runtime_result"] is True
    assert pending_handoff_task["payload"]["paper_mission_default_handoff_ref"] == task_handoff[
        "source_ref"
    ]
    assert pending_handoff_task["domain_dispatch_evidence_record_payload"]["task_kind"] == (
        "paper_mission/stage-outcome"
    )


def test_domain_handler_export_ignores_stale_consumption_handoff_as_default(
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
        / "20260623T2032Z"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::gate-clearing::one-shot-migration"
    current_transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="advance",
    )
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(
            {
                "schema_version": "paper-mission-run.v1",
                "mission_id": mission_id,
                "study_id": study_id,
                "objective": "Current materialized mission readback.",
                "mission_state": "candidate_ready_for_consumption",
                "artifact_delta_ledger": [],
                "source_refs": [],
                "authority_touchpoints": [],
                "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
                "consume_result": {"status": "accepted"},
                "claim_permissions": {
                    "can_claim_artifact_delta": True,
                    "can_claim_owner_handoff": True,
                    "can_claim_publication_ready": False,
                    "can_claim_current_package": False,
                    "can_claim_owner_receipt_written": False,
                },
                "one_shot_migration_readback": {
                    "required_output": {
                        "next_owner": "analysis-campaign",
                        "kind": "owner_decision_packet_or_consumable_artifact_delta",
                    },
                    "consume_candidate_status": "accepted",
                },
                "paper_mission_transaction": current_transaction,
            }
        ),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps({"candidate_id": "pmc-current", "study_id": study_id}),
        encoding="utf-8",
    )
    stale_transaction = json.loads(json.dumps(current_transaction))
    stale_transaction["transaction_id"] = "paper-mission-transaction::dm002::stale"
    stale_transaction["opl_route_command"]["source_terminal_decision_ref"] = (
        f"{stale_transaction['transaction_id']}#stage_terminal_decision"
    )
    stale_carrier = paper_mission_opl_runtime_carrier(stale_transaction)
    handoff_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / "20260624Tstale"
        / study_id
    )
    handoff_root.mkdir(parents=True)
    (handoff_root / "opl_route_handoff.json").write_text(
        json.dumps(
            {
                "surface_kind": "mas_paper_mission_opl_route_handoff_record",
                "schema_version": 1,
                "study_id": study_id,
                "mission_id": stale_transaction["mission_id"],
                "candidate_ref": str(handoff_root / "package_manifest.json"),
                "handoff_status": "ready_for_opl_route_command",
                "next_owner": "mission_executor",
                "paper_mission_transaction_ref": stale_transaction["transaction_id"],
                "stage_terminal_decision_ref": (
                    f"{stale_transaction['transaction_id']}#stage_terminal_decision"
                ),
                "stage_terminal_decision": stale_transaction[
                    "stage_terminal_decision"
                ],
                "opl_route_command_ref": (
                    f"{stale_transaction['transaction_id']}#opl_route_command"
                ),
                "opl_route_command": stale_transaction["opl_route_command"],
                "opl_runtime_carrier": stale_carrier,
                "route_command_kind": stale_transaction["opl_route_command"][
                    "command_kind"
                ],
                "route_target": stale_transaction["opl_route_command"]["target"],
                "transaction_materialized": True,
                "can_submit_to_opl_runtime": True,
                "can_claim_opl_runtime_enqueued": False,
                "can_claim_opl_stage_run_created": False,
                "can_claim_provider_running": False,
                "can_claim_paper_progress": False,
                "can_claim_runtime_ready": False,
                "authority_boundary": {
                    "writes_authority_surface": False,
                    "writes_publication_eval": False,
                    "writes_controller_decision": False,
                    "can_write_owner_receipt": False,
                    "can_write_typed_blocker": False,
                    "can_write_human_gate": False,
                    "can_write_current_package": False,
                    "can_write_paper_body": False,
                    "can_write_runtime_queue": False,
                    "can_write_opl_outbox": False,
                    "can_write_opl_event": False,
                    "can_write_opl_stage_run": False,
                    "can_write_provider_attempt": False,
                },
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        ["domain-handler", "export", "--profile", str(profile_path), "--format", "json"]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    paper_mission_task = next(
        task
        for task in payload["paper_mission_default_tasks"]
        if task["task_kind"] == "paper_mission/start_or_resume"
        and task["study_id"] == study_id
    )
    task_payload = paper_mission_task["payload"]
    carrier = task_payload["paper_mission"]["opl_runtime_carrier"]
    assert "opl_route_handoff" not in paper_mission_task
    assert "opl_route_handoff" not in task_payload
    assert "paper_mission_default_handoff_source" not in paper_mission_task
    assert "paper_mission_default_handoff_source" not in task_payload
    assert task_payload["route_identity_key"] == carrier["route_identity_key"]
    assert task_payload["attempt_idempotency_key"] == carrier[
        "attempt_idempotency_key"
    ]
    assert task_payload["request_idempotency_key"] == carrier[
        "request_idempotency_key"
    ]
    diagnostic = task_payload["paper_mission_consumption_ledger_diagnostic"]
    assert diagnostic["status"] == "ignored_for_default_paper_mission_task"
    assert diagnostic["paper_mission_transaction_ref"] == stale_transaction[
        "transaction_id"
    ]
    assert diagnostic["current_paper_mission_transaction_ref"] == current_transaction[
        "transaction_id"
    ]


def test_domain_handler_export_selects_matching_consumption_handoff_when_newer_stale_exists(
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
        / "20260629Tcurrent"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = (
        f"paper-mission::{study_id}::medical_prose_write_repair_publication_gate_replay"
    )
    current_transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    current_transaction["transaction_id"] = (
        f"paper-mission-transaction::{study_id}::submission_milestone_candidate"
        f"::followthrough::followthrough-02::{mission_id}"
    )
    current_transaction["stage_terminal_decision"]["status"] = (
        "accepted_submission_milestone_candidate"
    )
    current_transaction["opl_route_command"]["source_terminal_decision_ref"] = (
        f"{current_transaction['transaction_id']}#stage_terminal_decision"
    )
    current_transaction["idempotency"]["idempotency_key"] = (
        f"{study_id}::followthrough-02::terminal-owner-gate"
    )
    current_transaction["idempotency"]["transaction_fingerprint"] = (
        f"{study_id}::followthrough-02::typed_blocker"
    )
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(
            {
                "schema_version": "paper-mission-run.v1",
                "mission_id": mission_id,
                "study_id": study_id,
                "objective": "Current DM003 followthrough mission.",
                "mission_state": "candidate_ready_for_consumption",
                "artifact_delta_ledger": [],
                "source_refs": [],
                "authority_touchpoints": [],
                "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
                "consume_result": {"status": "accepted_submission_milestone_candidate"},
                "claim_permissions": {
                    "can_claim_artifact_delta": True,
                    "can_claim_owner_handoff": True,
                    "can_claim_publication_ready": False,
                    "can_claim_current_package": False,
                    "can_claim_owner_receipt_written": False,
                },
                "one_shot_migration_readback": {
                    "consume_candidate_status": "accepted_submission_milestone_candidate",
                    "required_output": {
                        "next_owner": "mission_executor",
                        "kind": "owner_decision_packet_or_consumable_artifact_delta",
                    },
                },
                "paper_mission_transaction": current_transaction,
            }
        ),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps({"candidate_id": "pmc-current", "study_id": study_id}),
        encoding="utf-8",
    )
    matching_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / "20260629Tmatching"
        / study_id
    )
    stale_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / "20260629Tstale"
        / study_id
    )
    matching_root.mkdir(parents=True)
    stale_root.mkdir(parents=True)

    def handoff_for(transaction: dict, root: Path) -> dict:
        carrier = paper_mission_opl_runtime_carrier(transaction)
        return {
            "surface_kind": "mas_paper_mission_opl_route_handoff_record",
            "schema_version": 1,
            "study_id": study_id,
            "mission_id": transaction["mission_id"],
            "candidate_ref": str(root / "package_manifest.json"),
            "handoff_status": "ready_for_opl_route_command",
            "next_owner": "mission_executor",
            "paper_mission_transaction_ref": transaction["transaction_id"],
            "stage_terminal_decision_ref": (
                f"{transaction['transaction_id']}#stage_terminal_decision"
            ),
            "stage_terminal_decision": transaction["stage_terminal_decision"],
            "opl_route_command_ref": f"{transaction['transaction_id']}#opl_route_command",
            "opl_route_command": transaction["opl_route_command"],
            "opl_runtime_carrier": carrier,
            "route_command_kind": transaction["opl_route_command"]["command_kind"],
            "route_target": transaction["opl_route_command"]["target"],
            "transaction_materialized": True,
            "can_submit_to_opl_runtime": True,
            "can_claim_opl_runtime_enqueued": False,
            "can_claim_opl_stage_run_created": False,
            "can_claim_provider_running": False,
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
            "authority_boundary": {
                "writes_authority_surface": False,
                "writes_publication_eval": False,
                "writes_controller_decision": False,
                "can_write_owner_receipt": False,
                "can_write_typed_blocker": False,
                "can_write_human_gate": False,
                "can_write_current_package": False,
                "can_write_paper_body": False,
                "can_write_runtime_queue": False,
                "can_write_opl_outbox": False,
                "can_write_opl_event": False,
                "can_write_opl_stage_run": False,
                "can_write_provider_attempt": False,
            },
        }

    stale_transaction = json.loads(json.dumps(current_transaction))
    stale_transaction["transaction_id"] = (
        f"paper-mission-transaction::{study_id}::submission_milestone_candidate"
        f"::{mission_id}"
    )
    stale_transaction["opl_route_command"]["source_terminal_decision_ref"] = (
        f"{stale_transaction['transaction_id']}#stage_terminal_decision"
    )
    matching_handoff = handoff_for(current_transaction, matching_root)
    matching_carrier = matching_handoff["opl_runtime_carrier"]
    matching_carrier["idempotency_key"] = (
        f"{study_id}::followthrough-02::submission-milestone-candidate-consumed"
    )
    matching_carrier["attempt_idempotency_key"] = (
        f"{matching_carrier['idempotency_key']}::opl-attempt"
    )
    matching_carrier["request_idempotency_key"] = (
        f"{matching_carrier['idempotency_key']}::opl-request"
    )
    (matching_root / "opl_route_handoff.json").write_text(
        json.dumps(matching_handoff),
        encoding="utf-8",
    )
    (stale_root / "opl_route_handoff.json").write_text(
        json.dumps(handoff_for(stale_transaction, stale_root)),
        encoding="utf-8",
    )
    stale_mtime = 2_000_000_000
    matching_mtime = 1_900_000_000
    (stale_root / "opl_route_handoff.json").touch()
    (matching_root / "opl_route_handoff.json").touch()
    import os

    os.utime(stale_root / "opl_route_handoff.json", (stale_mtime, stale_mtime))
    os.utime(matching_root / "opl_route_handoff.json", (matching_mtime, matching_mtime))

    exit_code = cli.main(
        ["domain-handler", "export", "--profile", str(profile_path), "--format", "json"]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    pending_handoff_task = next(
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "paper_mission/stage-outcome"
        and task["study_id"] == study_id
    )
    assert pending_handoff_task["payload"]["paper_mission_default_handoff_ref"].endswith(
        "/20260629Tmatching/"
        f"{study_id}/opl_route_handoff.json"
    )
    assert pending_handoff_task["payload"]["opl_route_handoff"][
        "paper_mission_transaction_ref"
    ] == current_transaction["transaction_id"]
    default_task = next(
        task
        for task in payload["paper_mission_default_tasks"]
        if task["study_id"] == study_id
    )
    assert default_task["opl_route_handoff"]["source_ref"] == pending_handoff_task[
        "payload"
    ]["paper_mission_default_handoff_ref"]
