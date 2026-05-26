from __future__ import annotations

import importlib
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def test_scan_domain_routes_projects_supervisor_only_live_quality_repair_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "obesity_multicenter_phenotype_atlas"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": study_id,
            "quest_root": str(quest_root),
            "quest_status": "active",
            "decision": "noop",
            "reason": "quest_already_running",
            "active_run_id": "run-obesity",
            "execution_owner_guard": {"supervisor_only": True, "active_run_id": "run-obesity"},
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-obesity",
                "runtime_audit": {"status": "live", "worker_running": True, "active_run_id": "run-obesity"},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "continue_supervising_runtime",
                "attempt_state": "live",
                "retry_budget_remaining": 3,
                "worker_liveness_state": {"state": "live", "worker_running": True},
                "blocking_reasons": [],
            },
            "publication_eval": {
                "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
            },
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-obesity",
                "source_signature": "truth-source-obesity",
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "current_stage": "publication_supervision",
            "paper_stage": "publishability_gate_blocked",
            "active_run_id": "run-obesity",
            "supervision": {"active_run_id": "run-obesity", "health_status": "live"},
            "progress_freshness": {
                "meaningful_artifact_delta_freshness": {
                    "status": "fresh",
                    "latest_progress_at": "2026-05-10T09:11:59+00:00",
                    "latest_progress_source": "gate_clearing_batch",
                }
            },
            "publication_supervisor_state": {"bundle_tasks_downstream_only": True},
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-obesity",
                "source_signature": "truth-source-obesity",
            },
            "ai_repair_lifecycle": {
                "state": "blocked",
                "blocked_reason": "execution_owner_guard_supervisor_only",
                "next_owner": "supervisor_only",
                "external_supervisor_required": False,
            },
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["meaningful_artifact_delta"] is True
    assert study["supervisor_only"] is True
    assert study["action_queue"] == []
    assert study["next_owner"] == "supervisor_only/live_quality_repair"
    assert study["blocked_reason"] == "execution_owner_guard_supervisor_only"
    assert study["external_supervisor_required"] is False


def test_supervisor_only_live_quality_repair_does_not_suppress_ai_reviewer_workflow(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id

    publication_eval = {
        "eval_id": "publication-eval::002::fresh",
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "recommended_actions": [
            {
                "action_type": "continue_same_line",
                "work_unit_fingerprint": "publication-blockers::fresh",
                "next_work_unit": {
                    "unit_id": "publication_gate_blocker_review",
                    "lane": "review",
                },
            }
        ],
    }
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": study_id,
            "quest_root": str(quest_root),
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "active_run_id": "run-dm002",
            "execution_owner_guard": {"supervisor_only": True, "active_run_id": "run-dm002"},
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-dm002",
                "runtime_audit": {"status": "live", "worker_running": True, "active_run_id": "run-dm002"},
            },
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-epoch-dm002",
                "canonical_runtime_action": "continue_supervising_runtime",
                "attempt_state": "live",
                "retry_budget_remaining": 3,
                "worker_liveness_state": {"state": "live", "worker_running": True},
                "blocking_reasons": [],
            },
            "publication_eval": publication_eval,
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-dm002",
                "source_signature": "truth-source-dm002",
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "current_stage": "publication_supervision",
            "paper_stage": "analysis-campaign",
            "active_run_id": "run-dm002",
            "supervision": {"active_run_id": "run-dm002", "health_status": "live"},
            "progress_freshness": {
                "meaningful_artifact_delta_freshness": {
                    "status": "fresh",
                    "latest_progress_at": "2026-05-13T15:10:07+00:00",
                    "latest_progress_source": "runtime_turn_closeout",
                }
            },
            "publication_eval": publication_eval,
            "publication_supervisor_state": {"bundle_tasks_downstream_only": False},
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-dm002",
                "source_signature": "truth-source-dm002",
            },
            "ai_repair_lifecycle": {
                "state": "blocked",
                "blocked_reason": "execution_owner_guard_supervisor_only",
                "next_owner": "supervisor_only",
                "external_supervisor_required": False,
            },
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    assert study["next_owner"] == "ai_reviewer"
    assert study["blocked_reason"] == "ai_reviewer_assessment_required"
    assert study["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert study["owner_route"]["blocked_actions"] == [
        "publication_gate_specificity_required",
        "current_package_freshness_required",
        "artifact_display_surface_materialization_required",
        "canonical_paper_inputs_rehydrate_required",
        "run_quality_repair_batch",
        "run_gate_clearing_batch",
    ]
