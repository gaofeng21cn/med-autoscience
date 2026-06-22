from __future__ import annotations

import importlib


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
    assert payload["next_owner_or_human_decision"]["next_owner"] == "ai_reviewer"
    assert payload["platform_diagnostics"]["counts_as_paper_progress"] is False
