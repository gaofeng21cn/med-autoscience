from __future__ import annotations

import importlib
import json
import os

import pytest

from med_autoscience.controllers.next_action_envelope import SURFACE_KIND
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


from tests.test_study_progress_mission_summary_cases.materialized_readback import *  # noqa: F403,F401
from tests.test_study_progress_mission_summary_cases.next_action_stage_closure import *  # noqa: F403,F401


def test_receipt_owner_consumption_route_checkpoint_maps_to_route_back_status() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.mission_summary"
    )

    status = module._effective_consume_candidate_status_for_receipt_owner_consumption(
        fallback="accepted",
        receipt_owner_consumption_readback={
            "mas_receipt_consumption": {
                "status": "owner_consumed_route_checkpoint",
            }
        },
    )

    assert status == "route_back"


def test_fallback_mission_summary_consumes_governed_ledger_without_materialized_run(
    tmp_path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    write_profile(profile_path, workspace_root=workspace_root)
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
    old_resolution = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_typed_blocker_resolution"
        / study_id
        / "typed_blocker_resolution.json"
    )
    old_resolution.parent.mkdir(parents=True)
    old_resolution.write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_typed_blocker_resolution",
                "schema_version": 1,
                "status": "human_gate_resolution_packet_materialized",
                "study_id": study_id,
                "typed_blocker": {
                    "blocker_type": "paper_mission_stage_route_domain_gate_pending",
                    "typed_blocker_evidence_ref": "/tmp/old-typed-blocker.json",
                },
                "next_owner_action": {
                    "surface_kind": "current_executable_owner_action",
                    "schema_version": 1,
                    "status": "ready",
                    "study_id": study_id,
                    "next_owner": "mas_authority_kernel",
                    "owner": "mas_authority_kernel",
                    "action_type": "classify_quality_blockers_or_materialize_degraded_handoff_gate",
                    "allowed_actions": [
                        "classify_quality_blockers_or_materialize_degraded_handoff_gate"
                    ],
                    "work_unit_id": "submission_blocker_degraded_handoff_or_quality_repair",
                    "work_unit_fingerprint": "oldtypedblockerroute",
                    "acceptance_refs": ["/tmp/old-typed-blocker.json"],
                },
            }
        ),
        encoding="utf-8",
    )
    old_time = old_resolution.stat().st_mtime - 10
    os.utime(old_resolution, (old_time, old_time))
    mission_id = f"paper-mission::{study_id}::fallback-ledger-current"
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
    capsys.readouterr()

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
    assert payload["stage_terminal_decision"]["decision_kind"] == (
        "continue_same_stage"
    )
    assert payload["opl_route_command"]["command_kind"] == "resume_stage"
    assert payload["next_owner_or_human_decision"]["next_owner"] == "mission_executor"
    assert payload["current_objective"]["next_owner"] == "mission_executor"
    assert payload["paper_mission_run"]["mission_state"] == "consumed"
    assert payload["paper_mission_run"]["consume_result"]["status"] == "accepted"
    assert _count_surface_kind(payload, SURFACE_KIND) == 1
    assert payload["canonical_next_action_source"] == (
        "artifact_first_mission_summary.next_action"
    )
    assert payload["next_action"]["surface_kind"] == SURFACE_KIND
    assert payload["next_action"]["action_family"] == "runtime.opl_route"
    assert payload["next_action"]["authority_source"] == "mas_next_action_compiler"
    assert payload["next_action"]["legacy_fields_are_diagnostic"] is True
    assert payload["next_action"]["legacy_field_diagnostic_roles"][
        "work_unit_id"
    ] == "diagnostic_currentness_id"
    assert payload["next_action"]["authority_boundary"][
        "exact_work_unit_id_authority"
    ] is False
    assert "next_action" not in payload["artifact_first_mission_summary"]
    assert payload["artifact_first_mission_summary"]["next_action_ref"] == (
        payload["next_action"]["action_id"]
    )
    assert payload["canonical_next_action_source"] != (
        "paper_mission_typed_blocker_resolution"
    )
    assert payload.get("typed_blocker_resolution_readback") is None
    assert "accepted_submission_milestone_candidate" in payload["paper_mission_run"][
        "stage_closure_readback"
    ]["known_blockers"]
    assert payload["artifact_first_mission_summary"]["read_model_source"] == {
        "source_kind": "paper_mission_consumption_ledger",
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
    assert_legacy_completion_surfaces_absent(payload)


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
    assert_legacy_completion_surfaces_absent(payload)


def test_artifact_first_mission_summary_ignores_platform_repair_for_terminal_outcome() -> None:
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
                "domain_diagnostic_report": "studies/002/artifacts/domain_diagnostic_report/latest.json",
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
    assert "legacy_path_role" not in summary
    assert summary["default_progress_metric"] == "paper_artifact_delta"
    assert summary["mission_state"] == "planned"
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
    assert paper_mission_run["mission_state"] == "planned"
    assert paper_mission_run["artifact_delta_ledger"] == []
    assert PaperMissionRun.from_payload(paper_mission_run).mission_id == (
        paper_mission_run["mission_id"]
    )
    assert PaperMissionTransaction.from_payload(
        summary["paper_mission_transaction"]
    ).mission_id == paper_mission_run["mission_id"]
    assert summary["stage_terminal_decision"]["decision_kind"] == "human_gate"
    assert summary["stage_terminal_decision"]["status"] == "human_gate"
    assert summary["stage_terminal_decision"]["reason"] == (
        "authoritative_stage_terminal_outcome_missing"
    )
    assert summary["opl_route_command"]["command_kind"] == "wait_for_human"
    assert summary["opl_runtime_carrier"]["opl_route_command"]["command_kind"] == (
        "wait_for_human"
    )
    assert summary["transaction_state"]["route_command_kind"] == "wait_for_human"
    assert "can_select_next_runtime_action" not in summary["read_model_source"]
    assert "fallback_transaction_is_runnable" not in summary["read_model_source"]
    assert paper_mission_run["consume_result"] == {
        "status": "human_gate",
        "outcome": "paper_mission_readback_missing",
        "reason": "authoritative_stage_terminal_outcome_missing",
        "question": (
            "Authoritative MAS stage terminal outcome is missing; do not infer "
            "the next runtime action from legacy progress projections."
        ),
        "required_receipt": "paper_mission_readback_missing",
    }
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
    assert "platform_diagnostics" not in summary
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
        "legacy_projection_accepted": False,
    }


def assert_legacy_completion_surfaces_absent(payload: dict[str, object]) -> None:
    for key in (
        "current_work_unit",
        "current_executable_owner_action",
        "paper_recovery_state",
        "progress_first_monitoring_summary",
        "provider_admission_candidates",
        "provider_admission_pending_count",
        "provider_admission_terminal_closeout_consumed",
        "transition_request_candidates",
        "transition_request_pending_count",
        "owner_action_admission",
        "current_execution_envelope",
        "current_execution_evidence",
    ):
        assert key not in payload
    assert payload["legacy_next_action_authority_retired"] == {
        "status": "retired",
        "authority": "NextActionEnvelope",
        "reason": "legacy_next_action_authority_retired_use_next_action_envelope",
        "retired_surfaces": [
            "current_work_unit",
            "current_executable_owner_action",
            "provider_admission",
            "current_execution_envelope",
        ],
        "default_selector_policy": "fail_closed",
        "diagnostic_only": True,
    }


def _count_surface_kind(value: object, surface_kind: str) -> int:
    if isinstance(value, dict):
        count = 1 if value.get("surface_kind") == surface_kind else 0
        return count + sum(_count_surface_kind(item, surface_kind) for item in value.values())
    if isinstance(value, list):
        return sum(_count_surface_kind(item, surface_kind) for item in value)
    return 0


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
            "delivery_inspection": {
                "current_package": {
                    "status": "current",
                    "package_kind": "current_package",
                    "can_submit": False,
                    "quality_gate_status": "blocked",
                    "known_blockers": ["claim_evidence_consistency_failed"],
                    "source_signature": "sha256:current",
                    "generated_from_current_source": True,
                }
            },
            "quality_repair_batch_followthrough": {
                "surface_kind": "quality_repair_batch_followthrough",
                "status": "executed",
                "repair_budget": {
                    "repair_budget_max": 3,
                    "repair_attempt_count": 3,
                    "repair_budget_status": "exhausted",
                    "on_exhausted": "degraded_handoff",
                },
            },
        }
    )

    assert payload["mission_state"] == "candidate_ready_for_consumption"
    assert payload["latest_artifact_delta"]["count"] == 1
    assert payload["latest_artifact_delta"]["counts_as_paper_progress"] is True
    assert payload["artifact_first_mission_summary"]["paper_mission_run"]["mission_state"] == (
        "candidate_ready_for_consumption"
    )
    assert payload["stage_terminal_decision"]["decision_kind"] == "human_gate"
    assert payload["stage_terminal_decision"]["status"] == "human_gate"
    assert payload["opl_route_command"]["command_kind"] == "wait_for_human"
    assert "next_action" not in payload
    assert "canonical_next_action_source" not in payload
    assert _count_surface_kind(payload, SURFACE_KIND) == 0
    assert "next_action" not in payload["artifact_first_mission_summary"]
    assert "next_action_ref" not in payload["artifact_first_mission_summary"]
    assert payload["artifact_first_mission_summary"]["next_action_projection"] == (
        "suppressed_noncanonical_legacy_progress_fallback"
    )
    assert payload["artifact_first_mission_summary"]["read_model_source"] == {
        "source_kind": "legacy_progress_projection_fallback",
        "legacy_projection_accepted": False,
    }
    assert payload["next_owner_or_human_decision"].get("next_owner") is None
    assert payload["stage_closure_decision"] == {}
    assert payload["stage_closure_outcome"] is None
    assert payload["current_package"] == {
        "status": "current",
        "package_kind": "current_package",
        "can_submit": False,
        "quality_gate_status": "blocked",
        "known_blockers": ["claim_evidence_consistency_failed"],
        "source_signature": "sha256:current",
        "generated_from_current_source": True,
    }
    assert payload["repair_budget"] == {
        "repair_budget_max": 3,
        "repair_attempt_count": 3,
        "repair_budget_status": "exhausted",
        "on_exhausted": "degraded_handoff",
    }
    assert payload["stage_closure"]["repair_budget"] == payload["repair_budget"]
    assert payload["artifact_first_mission_summary"]["stage_closure_decision"] == (
        payload["stage_closure_decision"]
    )
    assert "stage_closure_readback" not in payload["artifact_first_mission_summary"][
        "paper_mission_run"
    ]
    assert payload["opl_runtime_carrier"]["carrier_status"] == (
        "waiting_for_opl_runtime_live_readback"
    )
    assert payload["opl_transition_receipt"] == {
        "surface_kind": "opl_transition_receipt",
        "status": "not_requested_from_study_progress",
        "role": "transport_receipt_only",
        "can_change_stage_terminal_decision": False,
        "can_select_next_owner": False,
        "can_claim_paper_progress": False,
    }
    assert "next_owner" not in payload["next_owner_or_human_decision"]
    assert "platform_diagnostics" not in payload


def test_stage_closure_projection_uses_real_followthrough_budget_for_degraded_handoff() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.mission_summary"
    )

    payload = module.attach_artifact_first_mission_summary(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "paper_progress_delta": {"count": 0, "token_usage_total": 0, "sources": []},
            "delivery_inspection": {
                "current_package": {
                    "status": "stale",
                    "package_kind": "current_package",
                    "can_submit": False,
                    "quality_gate_status": "blocked",
                    "known_blockers": ["claim_evidence_consistency_failed"],
                    "source_signature": "sha256:stale",
                    "generated_from_current_source": False,
                }
            },
            "stage_closure_decision": {
                "projection_status": "terminalizer_outcome_observed",
                "decision_ref": "stage-closure::dm002",
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "degraded_handoff",
                    "next_action": "review_degraded_handoff_package",
                    "package_kind": "degraded_handoff_package",
                    "can_submit": False,
                    "known_blockers": ["claim_evidence_consistency_failed"],
                },
                "known_blockers": ["claim_evidence_consistency_failed"],
            },
            "quality_repair_batch_followthrough": {
                "surface_kind": "quality_repair_batch_followthrough",
                "repair_budget": {
                    "quality_repair_batch": {
                        "repair_budget_max": 2,
                        "repair_attempt_count": 2,
                        "repair_budget_status": "exhausted",
                        "on_exhausted": "degraded_handoff",
                    }
                },
            },
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "repair_budget": {
                    "gate_clearing_batch": {
                        "repair_budget_max": 3,
                        "repair_attempt_count": 1,
                        "repair_budget_status": "remaining",
                    }
                },
            },
        }
    )

    assert payload["current_package"]["status"] == "stale"
    assert payload["current_package"]["package_kind"] == "current_package"
    assert payload["current_package"]["can_submit"] is False
    assert payload["repair_budget"] == {
        "repair_budget_max": 2,
        "repair_attempt_count": 2,
        "repair_budget_status": "exhausted",
        "on_exhausted": "degraded_handoff",
    }
    assert payload["stage_closure"]["outcome_kind"] == "next_stage_transition"
    assert payload["stage_closure"]["next_transition"] == "degraded_handoff"
    assert payload["stage_closure"]["next_legal_action"] == (
        "review_degraded_handoff_package"
    )
    assert payload["next_legal_action"] == "review_degraded_handoff_package"
    assert payload["stage_closure"]["package_kind"] == "degraded_handoff_package"
    assert payload["stage_closure"]["known_blockers"] == [
        "claim_evidence_consistency_failed"
    ]


def test_artifact_first_mission_summary_projects_opl_transition_receipt_from_runtime_readback() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.mission_summary"
    )

    payload = module.attach_artifact_first_mission_summary(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "paper_progress_delta": {"count": 0, "token_usage_total": 0, "sources": []},
            "opl_runtime_carrier_readback": {
                "surface_kind": "paper_mission_opl_runtime_carrier_readback",
                "carrier_status": "opl_runtime_terminal_readback_observed",
                "opl_transition_receipt": {
                    "surface_kind": "opl_transition_receipt",
                    "schema_version": 1,
                    "receipt_status": "terminal_closeout_observed",
                    "role": "transport_receipt_only",
                    "paper_mission_transaction_ref": "paper-mission-transaction::dm002",
                    "opl_route_command_ref": (
                        "paper-mission-transaction::dm002#opl_route_command"
                    ),
                    "stage_attempt_ref": "opl://stage-attempts/sat-terminal",
                    "runtime_closeout_ref": (
                        "opl://family-runtime/tasks/frt-stage-route/"
                        "terminal-closeout-readback"
                    ),
                    "can_change_stage_terminal_decision": True,
                    "can_select_next_owner": True,
                    "can_claim_paper_progress": True,
                    "authority_boundary": {
                        "writes_owner_receipt": False,
                        "writes_typed_blocker": False,
                        "writes_human_gate": False,
                        "writes_current_package": False,
                        "can_claim_paper_progress": False,
                    },
                },
                "receipt_evidence": {
                    "surface_kind": "mas_receipt_evidence",
                    "schema_version": 1,
                    "receipt_kind": "opl_transition_receipt",
                    "receipt_ref": "opl://stage-attempts/sat-terminal",
                    "runtime_closeout_ref": (
                        "opl://family-runtime/tasks/frt-stage-route/"
                        "terminal-closeout-readback"
                    ),
                    "can_claim_paper_progress": False,
                    "can_claim_publication_ready": False,
                    "durable_stop_allowed": False,
                },
                "mas_receipt_consumption": {
                    "surface_kind": "mas_receipt_consumption_projection",
                    "schema_version": 1,
                    "status": "requires_mas_owner_consumption",
                    "next_legal_action": "consume_opl_transition_receipt",
                    "receipt_evidence_ref": "opl://stage-attempts/sat-terminal",
                    "forbidden_next_action": "synonymous_route_back_redrive",
                    "durable_stop_allowed": False,
                    "can_claim_paper_progress": False,
                    "can_claim_publication_ready": False,
                    "can_claim_runtime_ready": False,
                },
            },
        }
    )

    receipt = payload["opl_transition_receipt"]
    assert receipt["surface_kind"] == "opl_transition_receipt"
    assert receipt["receipt_status"] == "terminal_closeout_observed"
    assert receipt["role"] == "transport_receipt_only"
    assert receipt["paper_mission_transaction_ref"] == (
        "paper-mission-transaction::dm002"
    )
    assert receipt["stage_attempt_ref"] == "opl://stage-attempts/sat-terminal"
    assert receipt["can_change_stage_terminal_decision"] is False
    assert receipt["can_select_next_owner"] is False
    assert receipt["can_claim_paper_progress"] is False
    assert payload["artifact_first_mission_summary"]["opl_transition_receipt"] == receipt
    assert payload["receipt_evidence"]["surface_kind"] == "mas_receipt_evidence"
    assert payload["receipt_evidence"]["receipt_ref"] == "opl://stage-attempts/sat-terminal"
    assert payload["mas_receipt_consumption"]["surface_kind"] == (
        "mas_receipt_consumption_projection"
    )
    assert payload["mas_receipt_consumption"]["next_legal_action"] == (
        "consume_opl_transition_receipt"
    )
    assert payload["mas_receipt_consumption"]["forbidden_next_action"] == (
        "synonymous_route_back_redrive"
    )
    assert payload["artifact_first_mission_summary"]["receipt_evidence"] == (
        payload["receipt_evidence"]
    )
    assert payload["artifact_first_mission_summary"]["mas_receipt_consumption"] == (
        payload["mas_receipt_consumption"]
    )


def test_live_terminal_receipt_consumption_supersedes_stale_runtime_readback_request(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.mission_summary"
    )

    def fake_live_readback(**kwargs):
        assert kwargs["enable_opl_live_probe"] is True
        return {
            "opl_runtime_readback_status": "opl_runtime_terminal_readback_observed",
            "opl_runtime_carrier_readback": {
                "surface_kind": "paper_mission_opl_runtime_carrier_readback",
                "carrier_status": "opl_runtime_terminal_readback_observed",
                "runtime_readback_status": "terminal_closeout_observed",
                "dispatch_status": "terminal_closeout_observed",
                "can_claim_provider_running": False,
                "can_claim_paper_progress": False,
                "opl_transition_receipt": {
                    "surface_kind": "opl_transition_receipt",
                    "receipt_status": "terminal_closeout_observed",
                    "role": "transport_receipt_only",
                    "stage_attempt_ref": "opl://stage-attempts/sat-obesity-terminal",
                    "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
                    "can_claim_paper_progress": False,
                },
                "receipt_evidence": {
                    "surface_kind": "mas_receipt_evidence",
                    "receipt_kind": "opl_transition_receipt",
                    "receipt_ref": "opl://stage-attempts/sat-obesity-terminal",
                    "typed_runtime_blocker_ref": (
                        "/tmp/obesity/stage_closure_decision.json"
                    ),
                    "can_claim_paper_progress": False,
                    "can_claim_publication_ready": False,
                    "durable_stop_allowed": False,
                },
                "mas_receipt_consumption": {
                    "surface_kind": "mas_receipt_consumption_projection",
                    "status": "requires_mas_owner_consumption",
                    "next_legal_action": "record_typed_blocker",
                    "typed_runtime_blocker_ref": (
                        "/tmp/obesity/stage_closure_decision.json"
                    ),
                    "forbidden_next_action": "synonymous_route_back_redrive",
                    "durable_stop_allowed": False,
                    "can_claim_paper_progress": False,
                    "can_claim_publication_ready": False,
                    "can_claim_runtime_ready": False,
                },
            },
        }

    monkeypatch.setattr(module, "_study_progress_opl_runtime_readback", fake_live_readback)

    payload = module.attach_artifact_first_mission_summary(
        {
            "study_id": "obesity_multicenter_phenotype_atlas",
            "study_root": str(
                tmp_path / "studies" / "obesity_multicenter_phenotype_atlas"
            ),
            "paper_progress_delta": {"count": 0, "token_usage_total": 0, "sources": []},
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "action_id": "next-action::obesity::runtime-route",
                "action_family": "runtime.opl_route",
                "action_kind": "submit_to_opl_runtime",
                "owner": "one-person-lab",
            },
            "canonical_next_action_source": "precomputed_canonical_next_action",
            "stage_closure_decision": {
                "projection_status": "terminalizer_outcome_observed",
                "decision_ref": "/tmp/obesity/stage_closure_decision.json",
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "route_back_candidate_checkpoint",
                    "next_action": (
                        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                    ),
                },
            },
        },
        enable_opl_live_probe=True,
    )

    assert payload["next_action"]["action_family"] == "runtime.opl_route"
    assert payload["canonical_next_action_source"] == "precomputed_canonical_next_action"
    assert payload["opl_runtime_readback_status"] == (
        "opl_runtime_terminal_readback_observed"
    )
    assert payload["mas_receipt_consumption"]["next_legal_action"] == (
        "record_typed_blocker"
    )
    assert payload["next_legal_action"] == "record_typed_blocker"
    assert payload["artifact_first_mission_summary"]["mas_receipt_consumption"] == (
        payload["mas_receipt_consumption"]
    )


def test_attach_artifact_first_mission_summary_prefers_stage_closure_owner_consumption_over_stale_existing_next_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.mission_summary"
    )
    stale_next_action = {
        "surface_kind": SURFACE_KIND,
        "action_id": "next-action::stale-write",
        "action_family": "paper.write.prose_repair",
        "owner": "write",
        "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
    }
    summary_next_action = {
        "surface_kind": SURFACE_KIND,
        "action_id": "next-action::owner-consumption",
        "action_family": "paper.stage_closure.owner_consumption",
        "owner": "MedAutoScience",
        "work_unit_id": "ai_reviewer_medical_prose_quality_review",
    }

    monkeypatch.setattr(
        module,
        "build_artifact_first_mission_summary",
        lambda *_args, **_kwargs: {
            "mission_state": "route_back",
            "consume_candidate_status": "route_back",
            "stage_closure_decision": {
                "decision_ref": "stage-closure::review",
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "route_back_candidate_checkpoint",
                },
            },
            "paper_mission_run": {"mission_state": "consumed"},
            "current_objective": {},
            "latest_artifact_delta": {},
            "next_owner_or_human_decision": {},
            "paper_mission_transaction": {},
            "stage_terminal_decision": {},
            "opl_route_command": {},
            "opl_runtime_carrier": {},
            "opl_transition_receipt": {},
            "receipt_evidence": {},
            "mas_receipt_consumption": {},
            "transaction_state": "consumed",
            "read_model_source": {"source_kind": "paper_mission_consumption_ledger"},
            "next_action": summary_next_action,
            "receipt_owner_consumption_readback": {
                "mas_receipt_consumption": {
                    "status": "owner_consumed_route_checkpoint"
                }
            },
        },
    )

    payload = module.attach_artifact_first_mission_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "next_action": stale_next_action,
            "canonical_next_action_source": "precomputed_canonical_next_action",
        }
    )

    assert payload["next_action"] == summary_next_action
    assert payload["canonical_next_action_source"] == "stage_closure.next_action"


def test_domain_transition_next_action_yields_to_stage_closure_route_checkpoint() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.canonical_next_action_selection"
    )

    next_action = module.domain_transition_canonical_next_action(
        {
            "next_action": {
                "surface_kind": SURFACE_KIND,
                "action_id": "next-action::owner-consumption",
                "action_family": "paper.stage_closure.owner_consumption",
                "owner": "MedAutoScience",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
            },
            "receipt_owner_consumption_readback": {
                "mas_receipt_consumption": {
                    "status": "owner_consumed_route_checkpoint",
                }
            },
            "domain_transition": {
                "decision_type": "continue_same_stage",
                "next_action": {
                    "surface_kind": SURFACE_KIND,
                    "action_id": "next-action::stale-write",
                    "action_family": "paper.write.prose_repair",
                    "owner": "write",
                    "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
                    "expected_output_contract": {
                        "output_kind": "canonical_manuscript_delta"
                    },
                },
            },
        }
    )

    assert next_action == {}
