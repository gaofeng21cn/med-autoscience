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


@pytest.fixture(autouse=True)
def _disable_default_opl_live_probe(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("OPL_BIN", str(tmp_path / "missing-opl"))


def test_artifact_first_mission_summary_prefers_materialized_paper_mission_run(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.mission_summary"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
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
    study_root.mkdir(parents=True)
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": (
            f"paper-mission::{study_id}::medical_prose_write_repair_publication_gate_replay"
        ),
        "study_id": study_id,
        "objective": "Prepare a no-write paper mission for medical prose repair.",
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
        "authority_touchpoints": [
            {
                "touchpoint_id": "typed_blocker",
                "owner": "MedAutoScience",
                "surface": "typed blocker",
                "status": "not_touched",
            }
        ],
        "forbidden_write_guard": {
            "candidate_writes_authority": False,
            "blocked_paths": [
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "current_package",
                "runtime queue/provider attempts",
                "/Users/gaofeng/workspace/Yang/**",
            ],
            "forbidden_claims": [
                "publication_ready",
                "current_package",
                "owner_receipt_written",
            ],
        },
        "consume_result": {"status": "typed_blocker"},
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
        "one_shot_migration_readback": {
            "current_mission": {
                "mission_id": f"paper-mission::{study_id}::medical_prose",
                "study_id": study_id,
                "objective_kind": "medical_prose_write_repair_publication_gate_replay",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "kind": "owner_decision_packet_or_consumable_artifact_delta",
                "next_owner": "one-person-lab",
                "work_unit_id": "analysis_claim_evidence_repair",
            },
            "consume_candidate_status": "typed_blocker",
            "mission_input": {
                "legacy_blocker": {
                    "typed_blocker": {
                        "blocker_id": "current_owner_route_superseded_by_existing_typed_blocker"
                    }
                }
            },
        },
    }
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )

    payload = module.attach_artifact_first_mission_summary(
        {
            "study_id": study_id,
            "study_root": str(study_root),
            "paper_progress_delta": {
                "count": 1,
                "token_usage_total": 1200,
                "sources": ["stale_progress_delta"],
                "refs": ["studies/003/paper/draft.md"],
            },
            "progress_delta_classification": "deliverable_progress",
            "current_work_unit": {
                "status": "typed_blocker",
                "owner": "one-person-lab",
                "work_unit_id": "analysis_claim_evidence_repair",
            },
        }
    )

    assert payload["mission_state"] == "stable_blocker"
    assert payload["artifact_first_mission_summary"]["consume_candidate_status"] == (
        "typed_blocker"
    )
    assert payload["artifact_first_mission_summary"]["default_progress_metric"] == (
        "paper_mission_run"
    )
    assert payload["artifact_first_mission_summary"]["current_objective"]["next_owner"] == (
        "one-person-lab"
    )
    assert payload["next_owner_or_human_decision"]["next_owner"] == "one-person-lab"
    assert payload["latest_artifact_delta"]["refs"] == [
        "mission://dm003/prose-repair-owner-decision"
    ]
    mission_run = payload["artifact_first_mission_summary"]["paper_mission_run"]
    transaction = payload["artifact_first_mission_summary"]["paper_mission_transaction"]
    assert PaperMissionRun.from_payload(mission_run).mission_id == mission_run["mission_id"]
    assert PaperMissionTransaction.from_payload(transaction).mission_id == (
        mission_run["mission_id"]
    )
    assert payload["stage_terminal_decision"]["decision_kind"] == "typed_blocker"
    assert payload["opl_route_command"]["command_kind"] == "stop_with_typed_blocker"
    assert payload["opl_runtime_carrier"]["surface_kind"] == (
        "mas_domain_progress_transition_request"
    )
    assert payload["opl_runtime_carrier"]["opl_route_command"]["command_kind"] == (
        "stop_with_typed_blocker"
    )
    assert payload["opl_runtime_carrier"][
        "provider_admission_requires_opl_runtime_result"
    ] is True
    assert payload["opl_runtime_carrier"]["can_write_opl_stage_run"] is False
    assert payload["transaction_state"] == {
        "transaction_id": transaction["transaction_id"],
        "contract_ref": "contracts/paper_mission_transaction_contract.json",
        "validator": "med_autoscience.paper_mission_transaction.PaperMissionTransaction",
        "decision_kind": "typed_blocker",
        "route_command_kind": "stop_with_typed_blocker",
        "mas_authority_owner": "MedAutoScience",
        "runtime_owner": "one-person-lab",
        "projection_only": True,
        "writes_authority_surface": False,
        "writes_runtime_queue": False,
        "writes_provider_attempt": False,
    }
    assert payload["artifact_first_mission_summary"]["read_model_source"] == {
        "source_kind": "materialized_paper_mission_run",
        "materialized_mission_ref": str(mission_root / "paper_mission_run.json"),
        "legacy_progress_projection_role": "diagnostic_drilldown",
    }


def test_materialized_mission_summary_reports_opl_terminal_closeout_readback(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.mission_summary"
    )
    study_id = "002-dm-china-us-mortality-attribution"
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
    study_root.mkdir(parents=True)
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": f"paper-mission::{study_id}::gate-clearing",
        "study_id": study_id,
        "objective": "Accepted paper mission terminalized by OPL closeout.",
        "mission_state": "consumed",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::dm002::one-shot",
                "artifact_ref": "mission://dm002/owner-decision",
                "delta_kind": "formal_paper_mission_owner_decision_packet",
                "status": "candidate_consumed",
            }
        ],
        "source_refs": [
            {
                "ref_id": "legacy_truth_import_pack",
                "ref_kind": "legacy_truth_import_pack",
                "uri": "mission://dm002/import-pack",
            }
        ],
        "authority_touchpoints": [
            {
                "touchpoint_id": "publication_eval",
                "owner": "MedAutoScience",
                "surface": "publication_eval/latest.json",
                "status": "not_touched",
            }
        ],
        "forbidden_write_guard": {
            "candidate_writes_authority": False,
            "blocked_paths": [
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "current_package",
                "runtime queue/provider attempts",
                "/Users/gaofeng/workspace/Yang/**",
            ],
            "forbidden_claims": [
                "publication_ready",
                "current_package",
                "owner_receipt_written",
            ],
        },
        "consume_result": {"status": "accepted"},
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "gate_clearing_claim_evidence_repair",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "analysis-campaign",
                "kind": "owner_decision_packet_or_consumable_artifact_delta",
            },
            "consume_candidate_status": "accepted",
        },
    }
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    closeout_root = (
        study_root / "artifacts" / "supervision" / "consumer" / "owner_callable_adapter_receipt"
    )
    closeout_root.mkdir(parents=True)
    (closeout_root / "sat-terminal.closeout.json").write_text(
        json.dumps(
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "status": "blocked",
                "study_id": study_id,
                "stage_id": "publication_gate_replay",
                "stage_attempt_id": "sat-terminal",
                "action_type": "advance",
                "work_unit_id": "gate_clearing_claim_evidence_repair",
                "work_unit_fingerprint": (
                    f"paper-mission::{study_id}::gate-clearing::"
                    "gate_clearing_claim_evidence_repair::advance::accepted"
                ),
                "stage_packet_ref": (
                    f"paper-mission-transaction::{study_id}::"
                    "gate_clearing_claim_evidence_repair::"
                    f"paper-mission::{study_id}::gate-clearing"
                    "#stage_terminal_decision"
                ),
                "opl_route_command_ref": (
                    f"paper-mission-transaction::{study_id}::"
                    "gate_clearing_claim_evidence_repair::"
                    f"paper-mission::{study_id}::gate-clearing"
                    "#opl_route_command"
                ),
                "provider_completion_is_domain_completion": False,
                "provider_completion_is_domain_ready": False,
                "domain_completion_claimed": False,
                "domain_ready_claimed": False,
                "typed_blocker_ref": "closeout.json#domain_blocker",
                "blocked_reason": "domain_gate_pending",
                "closeout_refs": [
                    f"paper-mission-transaction::{study_id}::"
                    "gate_clearing_claim_evidence_repair::"
                    f"paper-mission::{study_id}::gate-clearing"
                    "#opl_route_command",
                    "closeout.json",
                    "typed-blocker:domain_gate_pending",
                ],
                "authority_boundary": {
                    "record_only_surface": True,
                    "provider_completion_is_domain_completion": False,
                    "artifact_mutation_authorized": False,
                    "publication_eval_latest_write_authorized": False,
                    "controller_decision_write_authorized": False,
                },
            }
        ),
        encoding="utf-8",
    )

    payload = module.attach_artifact_first_mission_summary(
        {
            "study_id": study_id,
            "study_root": str(study_root),
        }
    )

    summary = payload["artifact_first_mission_summary"]
    assert summary["opl_runtime_carrier"]["carrier_status"] == (
        "waiting_for_opl_runtime_live_readback"
    )
    assert summary["opl_runtime_readback_status"] == (
        "opl_runtime_terminal_readback_observed"
    )
    assert summary["opl_runtime_carrier_readback"]["domain_ready_verdict"] == (
        "domain_gate_pending"
    )
    assert summary["opl_runtime_carrier_readback"]["can_claim_paper_progress"] is False
    assert summary["opl_runtime_carrier_readback"][
        "provider_completion_is_domain_completion"
    ] is False
    assert summary["terminal_owner_gate"] == {
        "surface_kind": "paper_mission_terminal_owner_gate",
        "owner": "mas_authority_kernel",
        "gate_kind": "domain_gate",
        "blocked_reason": "domain_gate_pending",
        "typed_blocker_ref": "closeout.json#domain_blocker",
        "closeout_ref": (
            "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
            "sat-terminal.closeout.json"
        ),
        "stage_attempt_id": "sat-terminal",
        "work_unit_id": "gate_clearing_claim_evidence_repair",
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_materialized": False,
        "legal_next_action": "route_to_owner_or_human_gate",
    }
    assert summary["next_owner_or_human_decision"] == {
        "kind": "owner_or_route",
        "next_owner": "mission_executor",
        "human_decision_required": False,
        "summary": "route_back",
        "route_back_evidence_ref": summary[
            "terminal_owner_gate_owner_answer_readback"
        ]["route_back_evidence_ref"],
        "opl_route_command_ref": summary[
            "terminal_owner_gate_owner_answer_readback"
        ]["opl_route_command"]["source_terminal_decision_ref"],
        "can_execute": False,
        "can_authorize_provider_admission": False,
    }
    assert payload["terminal_owner_gate"] == summary["terminal_owner_gate"]
    assert payload["next_owner_or_human_decision"] == (
        summary["next_owner_or_human_decision"]
    )
    authority_readback = summary["terminal_owner_gate_authority_readback"]
    assert authority_readback["surface_kind"] == (
        "mas_terminal_owner_gate_authority_readback"
    )
    assert authority_readback["status"] == "route_back"
    assert authority_readback["next_owner"] == "mas_authority_kernel"
    assert authority_readback["owner_answer_materialized"] is True
    assert authority_readback["consume_result"]["status"] == "route_back"
    assert authority_readback["consume_result"]["outcome"] == "route_back_evidence_ref"
    assert authority_readback["consume_result"]["authority_materialized"] is False
    assert authority_readback["consume_result"][
        "authority_answer_readback_materialized"
    ] is True
    assert authority_readback["consume_result"]["authority_file_materialized"] is False
    owner_answer = summary["terminal_owner_gate_owner_answer_readback"]
    assert owner_answer["surface_kind"] == (
        "mas_terminal_owner_gate_owner_answer_readback"
    )
    assert owner_answer["status"] == "route_back"
    assert owner_answer["owner_answer_shape"] == "route_back_evidence_ref"
    assert owner_answer["authority_materialized"] is False
    assert owner_answer["authority_answer_readback_materialized"] is True
    assert owner_answer["authority_file_materialized"] is False
    assert owner_answer["can_claim_paper_progress"] is False
    assert owner_answer["can_claim_runtime_ready"] is False
    assert owner_answer["write_plan"]["written_files"] == []
    assert owner_answer["write_plan"]["can_write_owner_receipts"] is False
    assert owner_answer["write_plan"]["can_write_typed_blockers"] is False
    assert owner_answer["write_plan"]["can_write_human_gate_authority_records"] is False
    assert owner_answer["stage_terminal_decision"]["decision_kind"] == "route_back"
    assert owner_answer["opl_route_command"]["command_kind"] == "route_back"
    assert summary["stage_terminal_decision"] == owner_answer["stage_terminal_decision"]
    assert summary["opl_route_command"] == owner_answer["opl_route_command"]
    assert summary["paper_mission_transaction"] == owner_answer["paper_mission_transaction"]
    assert summary["mission_state"] == "route_back"
    assert summary["transaction_state"]["decision_kind"] == "route_back"
    assert summary["transaction_state"]["route_command_kind"] == "route_back"
    assert authority_readback["owner_answer_contract"]["typed_blocker_ref"] == (
        "closeout.json#domain_blocker"
    )
    assert authority_readback["authority_boundary"]["can_claim_paper_progress"] is False
    assert authority_readback["authority_boundary"][
        "can_authorize_provider_admission"
    ] is False
    assert authority_readback["authority_boundary"]["writes_authority_files"] is False
    assert authority_readback["authority_boundary"]["authority_file_materialized"] is False
    assert authority_readback["authority_boundary"]["can_write_owner_receipt"] is False
    assert authority_readback["authority_boundary"]["can_write_typed_blocker"] is False
    assert authority_readback["authority_boundary"]["can_write_human_gate"] is False
    assert authority_readback["write_plan"]["written_files"] == []
    assert payload["terminal_owner_gate_authority_readback"] == authority_readback
    assert payload["terminal_owner_gate_owner_answer_readback"] == owner_answer
    assert payload["opl_runtime_readback_status"] == (
        "opl_runtime_terminal_readback_observed"
    )
