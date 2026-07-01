from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_cli_cases.paper_mission_command_helpers import *  # noqa: F401,F403


def test_paper_mission_inspect_projects_receipt_owner_consumption_without_materialized_mission(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_id = f"paper-mission::{study_id}::external-sci-registry-review-v3"
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
    readback_file = tmp_path / "receipt-source-readback.json"
    readback_file.write_text(
        json.dumps(
            {
                **consume_payload,
                "surface_kind": "paper_mission_materialized_readback",
                "mission_state": "consumed",
                "stage_closure_decision": {
                    "decision_ref": f"mas://paper-mission/{study_id}/receipt-owner-consumption",
                    "outcome": {
                        "kind": "next_stage_transition",
                        "transition_kind": "route_back_candidate_checkpoint",
                        "can_submit": False,
                    },
                },
                "stage_closure_outcome": "next_stage_transition",
                "current_package": {
                    "status": "stale",
                    "package_kind": "current_package",
                    "can_submit": False,
                    "known_blockers": ["prose_revision_required"],
                },
                "opl_runtime_carrier_readback": {
                    "runtime_readback_status": "terminal_closeout_observed",
                    "receipt_evidence": {
                        "receipt_kind": "opl_transition_receipt",
                        "receipt_ref": "opl://stage-attempts/sat-obesity/receipt",
                        "impact_receipt_kind": "mas_impact_receipt",
                        "impact_receipt_ref": "opl://stage-attempts/sat-obesity/mas-impact",
                        "can_claim_paper_progress": False,
                    },
                    "opl_transition_receipt": {
                        "surface_kind": "opl_transition_receipt",
                        "receipt_status": "terminal_closeout_observed",
                        "role": "transport_receipt_only",
                        "task_id": "frt-obesity",
                        "task_status": "completed",
                        "stage_attempt_id": "sat-obesity",
                        "stage_attempt_ref": "opl://stage-attempts/sat-obesity",
                        "closeout_receipt_status": "accepted_typed_closeout",
                        "can_claim_paper_progress": False,
                    },
                    "mas_receipt_consumption": {
                        "surface_kind": "mas_receipt_consumption_projection",
                        "status": "requires_mas_owner_consumption",
                        "next_legal_action": "record_typed_blocker",
                        "forbidden_next_action": "synonymous_route_back_redrive",
                        "durable_stop_allowed": False,
                        "can_claim_paper_progress": False,
                        "can_claim_publication_ready": False,
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    receipt_exit_code = cli.main(
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
            str(
                workspace_root
                / "ops"
                / "medautoscience"
                / "paper_mission_receipt_owner_consumption"
            ),
            "--apply-typed-blocker",
            "--format",
            "json",
        ]
    )
    assert receipt_exit_code == 0
    receipt_payload = json.loads(capsys.readouterr().out)
    assert receipt_payload["status"] == "owner_consumption_applied"

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
    payload = json.loads(capsys.readouterr().out)

    assert inspect_exit_code == 0
    assert payload["surface_kind"] == "paper_mission_consumption_ledger_transaction_readback"
    assert payload["receipt_owner_consumption_readback"]["status"] == (
        "owner_consumption_applied"
    )
    assert payload["mas_receipt_consumption"]["status"] == (
        "owner_consumed_typed_blocker"
    )
    assert payload["consume_candidate_status"] == "typed_blocker"
    assert payload["mission_state"] == "stable_blocker"
    assert payload["stage_closure_outcome"] == "typed_blocker"
    assert payload["next_action"]["action_family"] == "blocked.typed"
    assert payload["durable_mission_stop_guard"]["durable_stop_allowed"] is True

    resolution_readback_file = tmp_path / "fallback-inspect-readback.json"
    resolution_readback_file.write_text(json.dumps(payload), encoding="utf-8")
    resolution_exit_code = cli.main(
        [
            "paper-mission",
            "typed-blocker-resolution",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--paper-mission-readback-file",
            str(resolution_readback_file),
            "--output-root",
            str(
                workspace_root
                / "ops"
                / "medautoscience"
                / "paper_mission_typed_blocker_resolution"
            ),
            "--apply-route-redesign",
            "--format",
            "json",
        ]
    )
    assert resolution_exit_code == 0
    resolution_payload = json.loads(capsys.readouterr().out)
    assert resolution_payload["status"] == "owner_route_redesign_applied"

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
    payload = json.loads(capsys.readouterr().out)

    assert inspect_exit_code == 0
    assert payload["typed_blocker_resolution_readback"]["status"] == (
        "owner_route_redesign_applied"
    )
    assert payload["next_action"]["action_family"] == (
        "paper.package.submission_minimal"
    )
    assert payload["next_action"]["diagnostic_refs"] == [
        {
            "role": "typed_blocker_resolution",
            "ref": payload["typed_blocker_resolution_readback"]["source_ref"],
        }
    ]
