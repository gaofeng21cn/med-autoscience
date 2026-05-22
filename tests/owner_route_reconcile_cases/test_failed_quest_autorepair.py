from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.owner_route_reconcile_cases.owner_route_test_helpers import assert_owner_route_required
from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _specificity_targets(study_root: Path) -> list[dict[str, str]]:
    return [
        {
            "target_kind": "claim",
            "target_id": "primary_claim",
            "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
            "blocking_reason": "publication_gate_blocked",
        },
        {
            "target_kind": "figure",
            "target_id": "figure_catalog",
            "source_path": str(study_root / "paper" / "figures" / "figure_catalog.json"),
            "blocking_reason": "publication_gate_blocked",
        },
        {
            "target_kind": "table",
            "target_id": "submission_manifest",
            "source_path": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
            "blocking_reason": "publication_gate_blocked",
        },
        {
            "target_kind": "metric",
            "target_id": "main_result_metrics",
            "source_path": str(study_root / "artifacts" / "results" / "main_result.json"),
            "blocking_reason": "publication_gate_blocked",
        },
        {
            "target_kind": "source_path",
            "target_id": "publishability_gate",
            "source_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "blocking_reason": "publication_gate_blocked",
        },
    ]


def test_scan_domain_routes_routes_failed_non_resumable_quest_to_platform_repair(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.managed_runtime_home / "quests" / study_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": f"publication-eval::{study_id}::current",
        "study_id": study_id,
        "quest_id": study_id,
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": "publication-blockers::current",
                "next_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                },
                "specificity_targets": _specificity_targets(study_root),
            }
        ],
    }

    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (
            {
                "study_id": study_id,
                "study_root": str(study_root),
                "quest_id": study_id,
                "quest_root": str(quest_root),
                "quest_status": "failed",
                "decision": "blocked",
                "reason": "quest_exists_with_non_resumable_state",
                "active_run_id": None,
                "auto_runtime_parked": {
                    "parked": True,
                    "parked_state": "explicit_resume_pending",
                    "parked_owner": "user",
                    "awaiting_explicit_wakeup": True,
                    "auto_execution_complete": False,
                    "source_reason": "quest_exists_with_non_resumable_state",
                    "source_decision": "blocked",
                    "source_quest_status": "failed",
                    "runtime_failure_classification": {
                        "auto_recovery_allowed": True,
                        "external_blocker": False,
                        "requires_human_gate": False,
                    },
                },
                "runtime_liveness_audit": {
                    "status": "none",
                    "active_run_id": None,
                    "runtime_audit": {"worker_running": False, "active_run_id": None},
                },
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "external_supervisor_required",
                    "attempt_state": "escalated",
                    "retry_budget_remaining": 0,
                    "observed_quest_state": {
                        "decision": "blocked",
                        "quest_status": "failed",
                        "reason": "quest_exists_with_non_resumable_state",
                    },
                    "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
                },
                "continuation_state": {
                    "quest_status": "failed",
                    "active_run_id": None,
                    "continuation_policy": "auto",
                    "continuation_reason": None,
                },
                "publication_eval": publication_eval,
                "study_truth_snapshot": {
                    "truth_epoch": "truth-epoch-failed-quest",
                    "source_signature": "truth-source-failed-quest",
                },
            },
            {
                "study_id": study_id,
                "quest_id": study_id,
                "current_stage": "publication_supervision",
                "paper_stage": "publishability_gate_blocked",
                "auto_runtime_parked": {
                    "parked": False,
                    "parked_state": "explicit_resume_pending",
                    "superseded_by_task_intake": True,
                },
                "supervision": {"active_run_id": None, "health_status": "escalated"},
                "quality_review_loop": {"closure_state": "review_required"},
                "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            },
            study_id,
            publication_eval,
        ),
    )

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["runtime_platform_repair"]
    assert study["action_queue"][0]["authority"] == "external_supervisor"
    assert study["action_queue"][0]["reason"] == "failed_quest_runtime_relaunch_required"
    assert study["next_owner"] == "external_supervisor"
    assert study["blocked_reason"] == "failed_quest_runtime_relaunch_required"
    assert study["external_supervisor_required"] is True
    macro_state = study["owner_route"]["source_refs"]["study_macro_state"]
    assert macro_state["writer_state"] == "parked"
    assert macro_state["reason"] == "unknown"
    assert study["owner_route"]["current_owner"] == "mas_controller"
    assert study["owner_route"]["allowed_actions"] == ["runtime_platform_repair"]
    assert study["owner_route"]["blocked_actions"] == [
        "publication_gate_specificity_required",
        "current_package_freshness_required",
        "artifact_display_surface_materialization_required",
        "return_to_ai_reviewer_workflow",
        "canonical_paper_inputs_rehydrate_required",
        "run_quality_repair_batch",
    ]
    assert study["recovery_intent"]["current_action"] == "safe_reconcile_ready"
    assert study["recovery_intent"]["reason"] == "failed_quest_runtime_relaunch_required"


def test_scan_domain_routes_explicit_runtime_platform_repair_relaunches_failed_non_resumable_quest(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "failed",
            "quest_id": study_id,
            "active_run_id": None,
            "worker_running": False,
            "pending_user_message_count": 0,
            "continuation_policy": "auto",
        },
    )
    publication_eval = {
        "schema_version": 1,
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": "publication-blockers::current",
                "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
            }
        ],
    }
    ensure_calls: list[dict[str, object]] = []

    def fake_ensure_study_runtime(**kwargs: object) -> dict[str, object]:
        ensure_calls.append(dict(kwargs))
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "quest_status": "running",
            "decision": "relaunch_stopped",
            "reason": "quest_stopped_explicit_relaunch_requested",
            "runtime_liveness_audit": {
                "active_run_id": "run-dpcc-recovered",
                "runtime_audit": {"worker_running": True, "active_run_id": "run-dpcc-recovered"},
            },
        }

    status_calls = 0

    def fake_progress_projection(**_: object) -> dict[str, object]:
        nonlocal status_calls
        status_calls += 1
        if status_calls > 1:
            return {
                "study_id": study_id,
                "study_root": str(study_root),
                "quest_id": study_id,
                "quest_root": str(quest_root),
                "quest_status": "running",
                "decision": "noop",
                "reason": "quest_already_running",
                "active_run_id": "run-dpcc-recovered",
                "runtime_liveness_audit": {
                    "active_run_id": "run-dpcc-recovered",
                    "runtime_audit": {"worker_running": True, "active_run_id": "run-dpcc-recovered"},
                },
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "continue_supervising_runtime",
                    "attempt_state": "recovering",
                    "retry_budget_remaining": 3,
                    "observed_quest_state": {
                        "decision": "noop",
                        "quest_status": "running",
                        "reason": "quest_already_running",
                    },
                    "blocking_reasons": [],
                },
                "continuation_state": {
                    "quest_status": "running",
                    "active_run_id": "run-dpcc-recovered",
                    "continuation_policy": "auto",
                },
                "publication_eval": publication_eval,
            }
        return {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": study_id,
            "quest_root": str(quest_root),
            "quest_status": "failed",
            "decision": "blocked",
            "reason": "quest_exists_with_non_resumable_state",
            "runtime_liveness_audit": {
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "observed_quest_state": {
                    "decision": "blocked",
                    "quest_status": "failed",
                    "reason": "quest_exists_with_non_resumable_state",
                },
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
            "continuation_state": {
                "quest_status": "failed",
                "active_run_id": None,
                "continuation_policy": "auto",
            },
            "publication_eval": publication_eval,
        }

    progress_calls = 0

    def fake_read_study_progress(**_: object) -> dict[str, object]:
        nonlocal progress_calls
        progress_calls += 1
        supervision = {"active_run_id": "run-dpcc-recovered", "health_status": "recovering"} if progress_calls > 1 else {
            "active_run_id": None,
            "health_status": "escalated",
        }
        return {
            "study_id": study_id,
            "paper_stage": "write",
            "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            "supervision": supervision,
        }

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure_study_runtime)
    monkeypatch.setattr(module.study_runtime_router, "progress_projection", fake_progress_projection)
    monkeypatch.setattr(module.study_progress, "read_study_progress", fake_read_study_progress)

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
    )

    study = result["studies"][0]
    apply_result = study["runtime_platform_repair_apply"]
    assert_owner_route_required(
        apply_result=apply_result,
        ensure_calls=ensure_calls,
        quest_root=quest_root,
        expected_reason="opl_runtime_owner_route_required",
    )
    assert apply_result["repair_kind"] == "failed_non_resumable_relaunch"
    assert status_calls == 1
    assert progress_calls == 1
    assert study["quest_status"] == "failed"
    assert study["active_run_id"] is None
    assert study["recovery_intent"]["current_action"] == "escalated"
    assert study["owner_route"]["next_owner"] == "one-person-lab"
    assert study["paper_package_mutated"] is False
