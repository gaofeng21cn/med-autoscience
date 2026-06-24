from __future__ import annotations

import importlib
import json

from med_autoscience.paper_mission_run import PaperMissionRun
from med_autoscience.paper_mission_transaction import PaperMissionTransaction
from tests.test_cli_cases.paper_mission_commands import (
    _paper_mission_transaction_payload,
    _paper_mission_forbidden_write_guard,
    _write_submission_milestone_package,
)
from tests.test_cli_cases.shared import write_profile


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
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution"
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
                "provider_completion_is_domain_completion": False,
                "provider_completion_is_domain_ready": False,
                "domain_completion_claimed": False,
                "domain_ready_claimed": False,
                "typed_blocker_ref": "closeout.json#domain_blocker",
                "blocked_reason": "domain_gate_pending",
                "closeout_refs": ["closeout.json", "typed-blocker:domain_gate_pending"],
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
            "artifacts/supervision/consumer/default_executor_execution/"
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
    assert authority_readback["consume_result"]["authority_materialized"] is True
    owner_answer = summary["terminal_owner_gate_owner_answer_readback"]
    assert owner_answer["surface_kind"] == (
        "mas_terminal_owner_gate_owner_answer_readback"
    )
    assert owner_answer["status"] == "route_back"
    assert owner_answer["owner_answer_shape"] == "route_back_evidence_ref"
    assert owner_answer["authority_materialized"] is True
    assert owner_answer["can_claim_paper_progress"] is False
    assert owner_answer["can_claim_runtime_ready"] is False
    assert owner_answer["write_plan"]["written_files"] == []
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
    assert authority_readback["write_plan"]["written_files"] == []
    assert payload["terminal_owner_gate_authority_readback"] == authority_readback
    assert payload["terminal_owner_gate_owner_answer_readback"] == owner_answer
    assert payload["opl_runtime_readback_status"] == (
        "opl_runtime_terminal_readback_observed"
    )


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
        "legacy_progress_projection_role": "diagnostic_drilldown",
    }


def test_study_progress_resolves_dm_alias_to_materialized_paper_mission_run(
    tmp_path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_id = "002-dm-china-us-mortality-attribution"
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
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": (
            f"paper-mission::{study_id}::gate_clearing_claim_evidence_repair"
        ),
        "study_id": study_id,
        "objective": "Prepare a no-write paper mission for gate-clearing.",
        "mission_state": "consumed",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::dm002::one-shot",
                "artifact_ref": "mission://dm002/claim-evidence-owner-decision",
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
                "mission_id": f"paper-mission::{study_id}::gate-clearing",
                "study_id": study_id,
                "objective_kind": "gate_clearing_claim_evidence_repair",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "kind": "owner_decision_packet_or_consumable_artifact_delta",
                "next_owner": "analysis-campaign",
                "work_unit_id": "analysis_claim_evidence_repair",
            },
            "consume_candidate_status": "accepted",
        },
    }
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "study",
            "progress",
            "--profile",
            str(profile_path),
            "--study-id",
            "DM002",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["study_id"] == study_id
    assert payload["mission_state"] == "consumed"
    assert payload["artifact_first_mission_summary"]["default_progress_metric"] == (
        "paper_mission_run"
    )
    assert payload["artifact_first_mission_summary"]["consume_candidate_status"] == (
        "accepted"
    )
    assert payload["artifact_first_mission_summary"]["paper_mission_run"]["mission_id"] == (
        mission_payload["mission_id"]
    )
    assert payload["stage_terminal_decision"]["decision_kind"] == "advance"
    assert payload["opl_route_command"]["command_kind"] == "start_next_stage"
    assert payload["opl_runtime_carrier"]["opl_route_command"]["command_kind"] == (
        "start_next_stage"
    )
    assert payload["next_owner_or_human_decision"]["next_owner"] == "analysis-campaign"


def test_artifact_first_mission_summary_demotes_platform_repair_to_diagnostics() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.mission_summary"
    )

    summary = module.build_artifact_first_mission_summary(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "paper_progress_delta": {"count": 0, "token_usage_total": 0, "sources": []},
            "platform_repair_delta": {
                "count": 1,
                "sources": [
                    "opl_current_control_state.blocked_reason",
                    "opl_current_control_state.runtime_health",
                ],
            },
            "progress_delta_classification": "platform_repair",
            "next_forced_delta": {
                "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                "work_unit_id": "dm002-currentness-repair",
                "target_surface": {"surface_ref": "canonical_manuscript"},
                "acceptance_refs": ["canonical_manuscript_delta"],
                "owner_action": {"next_owner": "runtime_mechanism_repair"},
            },
            "refs": {
                "progress_projection": "studies/002/progress_projection.json",
                "domain_health_diagnostic": "studies/002/artifacts/domain_health_diagnostic/latest.json",
            },
            "opl_current_control_state_handoff": {
                "blocked_reason": "currentness_drift",
                "runtime_health": {"health_status": "degraded"},
            },
        }
    )

    assert summary["surface_kind"] == "artifact_first_paper_mission_summary"
    assert summary["contract_ref"] == "contracts/paper_mission_run_contract.json"
    assert summary["validator"] == "med_autoscience.paper_mission_run.PaperMissionRun"
    assert summary["legacy_path_role"] == "diagnostics_migration_provenance_only"
    assert summary["default_progress_metric"] == "paper_artifact_delta"
    assert summary["mission_state"] == "running"
    assert summary["current_objective"] == {
        "objective": "paper_progress_delta_or_typed_blocker",
        "work_unit_id": "dm002-currentness-repair",
        "target_surface": {"surface_ref": "canonical_manuscript"},
        "acceptance_refs": ["canonical_manuscript_delta"],
        "next_owner": "runtime_mechanism_repair",
    }
    assert summary["latest_artifact_delta"] == {
        "count": 0,
        "token_usage_total": 0,
        "sources": [],
        "refs": ["canonical_manuscript_delta"],
        "classification": "platform_repair",
        "counts_as_paper_progress": False,
        "platform_repair_excluded": True,
        "artifact_delta_ledger": [],
    }
    paper_mission_run = summary["paper_mission_run"]
    assert set(paper_mission_run) >= {
        "mission_id",
        "study_id",
        "objective",
        "mission_state",
        "artifact_delta_ledger",
        "source_refs",
        "authority_touchpoints",
        "forbidden_write_guard",
        "consume_result",
        "claim_permissions",
    }
    assert paper_mission_run["schema_version"] == "paper-mission-run.v1"
    assert paper_mission_run["mission_state"] == "running"
    assert paper_mission_run["artifact_delta_ledger"] == []
    assert PaperMissionRun.from_payload(paper_mission_run).mission_id == (
        paper_mission_run["mission_id"]
    )
    assert PaperMissionTransaction.from_payload(
        summary["paper_mission_transaction"]
    ).mission_id == paper_mission_run["mission_id"]
    assert summary["stage_terminal_decision"]["decision_kind"] == "continue_same_stage"
    assert summary["opl_route_command"]["command_kind"] == "resume_stage"
    assert summary["opl_runtime_carrier"]["opl_route_command"]["command_kind"] == (
        "resume_stage"
    )
    assert summary["transaction_state"]["route_command_kind"] == "resume_stage"
    assert paper_mission_run["consume_result"] == {"status": "not_consumed"}
    assert paper_mission_run["forbidden_write_guard"]["candidate_writes_authority"] is False
    assert {
        "publication_eval/latest.json",
        "controller_decisions/latest.json",
        "current_package",
        "runtime queue/provider attempts",
        "/Users/gaofeng/workspace/Yang/**",
    } <= set(paper_mission_run["forbidden_write_guard"]["blocked_paths"])
    assert paper_mission_run["claim_permissions"]["can_claim_publication_ready"] is False
    assert paper_mission_run["claim_permissions"]["can_claim_current_package"] is False
    assert paper_mission_run["claim_permissions"]["can_claim_owner_receipt_written"] is False
    assert paper_mission_run["claim_permissions"]["can_claim_artifact_delta"] is False
    assert summary["platform_diagnostics"]["count"] == 1
    assert summary["platform_diagnostics"]["counts_as_paper_progress"] is False
    assert "DHD" in summary["platform_diagnostics"]["folded_surfaces"]
    assert "dispatch" in summary["platform_diagnostics"]["folded_surfaces"]
    assert summary["paper_progress_counting_policy"]["platform_repair_counts_as_paper_progress"] is False
    assert (
        summary["paper_progress_counting_policy"][
            "legacy_current_work_unit_counts_as_next_action_authority"
        ]
        is False
    )
    assert summary["authority"]["can_start_provider_attempt"] is False
    assert summary["authority"]["can_mark_dm002_dm003_complete"] is False
    assert summary["read_model_source"] == {
        "source_kind": "legacy_progress_projection_fallback",
        "legacy_projection_role": "diagnostic_fallback_not_execution_authority",
        "legacy_fields_folded": [
            "next_forced_delta",
            "current_owner_delta",
            "current_work_unit",
            "current_executable_owner_action",
        ],
        "current_objective_source": "diagnostic_fallback",
        "next_owner_source": "diagnostic_fallback",
        "can_select_next_runtime_action": False,
        "can_authorize_provider_admission": False,
    }


def test_attach_artifact_first_mission_summary_exposes_top_level_read_model_fields() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.mission_summary"
    )

    payload = module.attach_artifact_first_mission_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "paper_progress_delta": {
                "count": 1,
                "token_usage_total": 1200,
                "sources": ["repair_progress_projection.mas_owner_repair_execution_evidence"],
                "refs": ["studies/003/paper/draft.md"],
            },
            "progress_delta_classification": "deliverable_progress",
            "current_owner_delta": {
                "owner": "ai_reviewer",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "quality-repair-003",
            },
        }
    )

    assert payload["mission_state"] == "candidate_ready_for_consumption"
    assert payload["latest_artifact_delta"]["count"] == 1
    assert payload["latest_artifact_delta"]["counts_as_paper_progress"] is True
    assert payload["artifact_first_mission_summary"]["paper_mission_run"]["mission_state"] == (
        "candidate_ready_for_consumption"
    )
    assert payload["stage_terminal_decision"]["decision_kind"] == "continue_same_stage"
    assert payload["opl_route_command"]["command_kind"] == "resume_stage"
    assert payload["opl_runtime_carrier"]["carrier_status"] == (
        "waiting_for_opl_runtime_live_readback"
    )
    assert payload["next_owner_or_human_decision"]["next_owner"] == "ai_reviewer"
    assert payload["platform_diagnostics"]["counts_as_paper_progress"] is False
