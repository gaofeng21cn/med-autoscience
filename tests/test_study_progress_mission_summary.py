from __future__ import annotations

import importlib
import json

from med_autoscience.paper_mission_run import PaperMissionRun
from med_autoscience.paper_mission_transaction import PaperMissionTransaction
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
    assert summary["authority"]["can_start_provider_attempt"] is False
    assert summary["authority"]["can_mark_dm002_dm003_complete"] is False


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
    assert payload["next_owner_or_human_decision"]["next_owner"] == "ai_reviewer"
    assert payload["platform_diagnostics"]["counts_as_paper_progress"] is False
