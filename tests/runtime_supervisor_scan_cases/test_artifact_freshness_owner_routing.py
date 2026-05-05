from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_supervisor_scan_runtime_repair_routes_package_freshness_terminal_to_gate_clearing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-dm-cvd-mortality-risk", quest_id="quest-dm")
    quest_root = profile.runtime_root / "quest-dm"
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "active",
            "quest_id": "quest-dm",
            "active_run_id": None,
            "worker_running": False,
            "pending_user_message_count": 0,
        },
    )

    def fake_ensure_study_runtime(**_: object) -> dict[str, object]:
        return {
            "study_id": "001-dm-cvd-mortality-risk",
            "quest_id": "quest-dm",
            "quest_status": "active",
            "decision": "blocked",
            "reason": "resume_request_failed",
            "resume_postcondition": {
                "effective": False,
                "failure_mode": "no_live_run_started",
                "snapshot_status": "active",
                "active_run_id": None,
                "scheduled": False,
                "started": False,
                "queued": False,
                "blocked_reason": "current_package_freshness_required",
                "terminal_reason": "current_package_freshness_required",
                "terminal_source": "controller_work_unit_authorization",
            },
            "runtime_liveness_audit": {
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
        }

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure_study_runtime)
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "study_root": str(study_root),
            "quest_id": "quest-dm",
            "quest_root": str(quest_root),
            "quest_status": "active",
            "reason": "runtime_recovery_retry_budget_exhausted",
            "runtime_liveness_audit": {
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "current_stage": "managed_runtime_escalated",
            "paper_stage": "bundle_stage_blocked",
            "auto_runtime_parked": {"parked": False, "auto_execution_complete": False},
            "supervision": {"active_run_id": None, "health_status": "escalated"},
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=("001-dm-cvd-mortality-risk",),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
    )

    study = result["studies"][0]
    apply_result = study["runtime_platform_repair_apply"]
    assert apply_result["dispatch_status"] == "blocked"
    assert apply_result["reason"] == "current_package_freshness_required"
    assert apply_result["repair_kind"] == "active_runtime_no_live_worker_relaunch"
    assert apply_result["resume_postcondition"]["terminal_reason"] == "current_package_freshness_required"
    assert [item["action_type"] for item in study["action_queue"]] == ["current_package_freshness_required"]
    assert study["action_queue"][0]["owner"] == "artifact_os"
    assert study["ai_repair_lifecycle"]["state"] == "blocked"
    assert study["ai_repair_lifecycle"]["blocked_reason"] == "current_package_freshness_required"
    assert study["ai_repair_lifecycle"]["next_owner"] == "artifact_os"
    assert study["why_not_applied"] == "current_package_freshness_required"
    assert study["blocked_reason"] == "current_package_freshness_required"
    assert study["next_owner"] == "artifact_os"
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["next_owner"] == "artifact_os"
    assert study["owner_route"]["owner_reason"] == "current_package_freshness_required"
    assert study["owner_route"]["allowed_actions"] == ["current_package_freshness_required"]
    assert study["paper_package_mutated"] is False


def test_supervisor_scan_routes_failed_gate_clearing_display_unit_to_concrete_artifact_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    quest_root = profile.runtime_root / "quest-dm002"
    eval_id = "publication-eval::dm002::current"
    missing_registry = study_root / "paper" / "display_registry.json"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": eval_id,
            "study_id": study_id,
            "quest_id": "quest-dm002",
            "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
            "recommended_actions": [{"action_type": "route_back_same_line"}],
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json",
        {
            "schema_version": 1,
            "status": "executed",
            "source_eval_id": eval_id,
            "current_package_freshness_proof": None,
            "selected_publication_work_unit": {"unit_id": "analysis_claim_evidence_repair"},
            "unit_results": [
                {"unit_id": "repair_paper_live_paths", "status": "ok"},
                {
                    "unit_id": "materialize_display_surface",
                    "status": "failed",
                    "error": f"[Errno 2] No such file or directory: '{missing_registry}'",
                    "blocking_artifact_refs": [
                        {
                            "blocker": "display_surface_materialization_failed",
                            "artifact_path": str(missing_registry),
                            "artifact_role": "display_registry",
                            "failure_reason": f"[Errno 2] No such file or directory: '{missing_registry}'",
                        }
                    ],
                },
                {
                    "unit_id": "create_submission_minimal_package",
                    "status": "skipped_failed_dependency",
                    "failed_dependencies": ["materialize_display_surface"],
                },
            ],
            "repair_blocking_artifact_refs": [
                {
                    "blocker": "display_surface_materialization_failed",
                    "artifact_path": str(missing_registry),
                    "artifact_role": "display_registry",
                    "failure_reason": f"[Errno 2] No such file or directory: '{missing_registry}'",
                }
            ],
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": "quest-dm002",
            "quest_root": str(quest_root),
            "quest_status": "active",
            "active_run_id": None,
            "reason": "runtime_recovery_retry_budget_exhausted",
            "runtime_liveness_audit": {
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
            "publication_eval": {
                "eval_id": eval_id,
                "study_id": study_id,
                "quest_id": "quest-dm002",
                "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
                "recommended_actions": [{"action_type": "route_back_same_line"}],
            },
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-dm002",
                "source_signature": "truth-source-dm002",
            },
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **_: {
            "study_id": study_id,
            "quest_id": "quest-dm002",
            "quest_status": "active",
            "decision": "blocked",
            "reason": "resume_request_failed",
            "resume_postcondition": {
                "effective": False,
                "blocked_reason": "current_package_freshness_required",
                "terminal_reason": "current_package_freshness_required",
                "terminal_source": "controller_work_unit_authorization",
            },
            "runtime_liveness_audit": {
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "current_stage": "managed_runtime_escalated",
            "paper_stage": "bundle_stage_blocked",
            "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            "supervision": {"active_run_id": None, "health_status": "escalated"},
            "gate_clearing_batch_followthrough": {
                "status": "executed",
                "failed_unit_count": 1,
                "failed_units": [
                    {
                        "unit_id": "materialize_display_surface",
                        "status": "failed",
                        "blocking_artifact_refs": [
                            {
                                "blocker": "display_surface_materialization_failed",
                                "artifact_path": str(missing_registry),
                                "artifact_role": "display_registry",
                            }
                        ],
                    }
                ],
            },
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["artifact_display_surface_materialization_required"]
    action = study["action_queue"][0]
    assert action["reason"] == "display_surface_materialization_failed"
    assert action["owner"] == "artifact_os"
    assert action["required_output_surface"] == "paper/display_registry.json"
    assert action["failed_units"][0]["unit_id"] == "materialize_display_surface"
    assert action["blocking_artifact_refs"][0]["artifact_role"] == "display_registry"
    assert study["blocked_reason"] == "display_surface_materialization_failed"
    assert study["why_not_applied"] == "display_surface_materialization_failed"
    assert study["next_owner"] == "artifact_os"
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["owner_reason"] == "display_surface_materialization_failed"
    assert study["owner_route"]["allowed_actions"] == ["artifact_display_surface_materialization_required"]


def test_supervisor_scan_routes_failed_gate_clearing_when_eval_id_changed_but_work_unit_matches(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    quest_root = profile.runtime_root / "quest-dm002"
    current_eval_id = "publication-eval::dm002::current-generated-later"
    work_unit_fingerprint = "publication-blockers::same-work-unit"
    missing_registry = study_root / "paper" / "display_registry.json"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": current_eval_id,
            "study_id": study_id,
            "quest_id": "quest-dm002",
            "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
            "recommended_actions": [
                {
                    "action_type": "return_to_controller",
                    "work_unit_fingerprint": work_unit_fingerprint,
                    "specificity_targets": [
                        {
                            "target_kind": "metric",
                            "target_id": "main_result_metrics",
                            "source_path": str(quest_root / "artifacts" / "results" / "main_result.json"),
                            "blocking_reason": "stale_submission_minimal_authority",
                        }
                    ],
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json",
        {
            "schema_version": 1,
            "status": "executed",
            "source_eval_id": "publication-eval::dm002::previous-generated-at",
            "source_work_unit_fingerprint": work_unit_fingerprint,
            "current_package_freshness_proof": None,
            "selected_publication_work_unit": {"unit_id": "analysis_claim_evidence_repair"},
            "unit_results": [
                {"unit_id": "repair_paper_live_paths", "status": "ok"},
                {
                    "unit_id": "materialize_display_surface",
                    "status": "failed",
                    "error": f"[Errno 2] No such file or directory: '{missing_registry}'",
                    "blocking_artifact_refs": [
                        {
                            "blocker": "display_surface_materialization_failed",
                            "artifact_path": str(missing_registry),
                            "artifact_role": "display_registry",
                        }
                    ],
                },
            ],
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": "quest-dm002",
            "quest_root": str(quest_root),
            "quest_status": "active",
            "active_run_id": None,
            "reason": "runtime_recovery_retry_budget_exhausted",
            "runtime_liveness_audit": {
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
            "publication_eval": {
                "eval_id": current_eval_id,
                "study_id": study_id,
                "quest_id": "quest-dm002",
                "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
                "recommended_actions": [{"work_unit_fingerprint": work_unit_fingerprint}],
            },
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **_: {
            "study_id": study_id,
            "quest_id": "quest-dm002",
            "quest_status": "active",
            "decision": "blocked",
            "reason": "resume_request_failed",
            "resume_postcondition": {
                "effective": False,
                "blocked_reason": "current_package_freshness_required",
                "terminal_reason": "current_package_freshness_required",
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "current_stage": "managed_runtime_escalated",
            "paper_stage": "bundle_stage_blocked",
            "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == [
        "artifact_display_surface_materialization_required"
    ]
    assert study["blocked_reason"] == "display_surface_materialization_failed"


def test_supervisor_scan_routes_reused_display_input_failure_to_artifact_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    quest_root = profile.runtime_root / "quest-dm002"
    current_eval_id = "publication-eval::dm002::current-generated-later"
    work_unit_fingerprint = "publication-blockers::same-display-input"
    cohort_flow = study_root / "paper" / "cohort_flow.json"
    _write_json(cohort_flow, {"steps": []})
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": current_eval_id,
            "study_id": study_id,
            "quest_id": "quest-dm002",
            "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
            "recommended_actions": [
                {
                    "action_type": "return_to_controller",
                    "work_unit_fingerprint": work_unit_fingerprint,
                    "specificity_targets": [
                        {
                            "target_kind": "source_path",
                            "target_id": "cohort_flow",
                            "source_path": str(cohort_flow),
                            "blocking_reason": "display_surface_materialization_failed",
                        }
                    ],
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json",
        {
            "schema_version": 1,
            "status": "executed",
            "source_work_unit_fingerprint": work_unit_fingerprint,
            "selected_publication_work_unit": {"unit_id": "analysis_claim_evidence_repair"},
            "unit_results": [
                {
                    "unit_id": "materialize_display_surface",
                    "status": "blocked_matching_failed_unit_fingerprint",
                    "previous_status": "failed",
                    "previous_failure_reused": True,
                    "error": "cohort_flow.json must contain a non-empty steps list",
                    "blocking_artifact_refs": [
                        {
                            "blocker": "display_surface_materialization_failed",
                            "artifact_path": str(cohort_flow),
                            "artifact_role": "display_input_payload",
                            "failure_reason": "cohort_flow.json must contain a non-empty steps list",
                            "terminal_state": "gate_needs_specificity",
                        }
                    ],
                    "terminal_state": "gate_needs_specificity",
                },
            ],
            "repair_blocking_artifact_refs": [
                {
                    "blocker": "display_surface_materialization_failed",
                    "artifact_path": str(cohort_flow),
                    "artifact_role": "display_input_payload",
                    "failure_reason": "cohort_flow.json must contain a non-empty steps list",
                    "terminal_state": "gate_needs_specificity",
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": "quest-dm002",
            "quest_root": str(quest_root),
            "quest_status": "active",
            "active_run_id": None,
            "runtime_liveness_audit": {
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "attempt_state": "escalated",
            },
            "publication_eval": {
                "eval_id": current_eval_id,
                "study_id": study_id,
                "quest_id": "quest-dm002",
                "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
                "recommended_actions": [{"work_unit_fingerprint": work_unit_fingerprint}],
            },
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **_: {
            "study_id": study_id,
            "quest_id": "quest-dm002",
            "quest_status": "active",
            "decision": "blocked",
            "reason": "resume_request_failed",
            "resume_postcondition": {
                "effective": False,
                "blocked_reason": "current_package_freshness_required",
                "terminal_reason": "current_package_freshness_required",
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "current_stage": "managed_runtime_escalated",
            "paper_stage": "bundle_stage_blocked",
            "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == [
        "artifact_display_surface_materialization_required"
    ]
    action = study["action_queue"][0]
    assert action["required_output_surface"] == str(cohort_flow)
    assert action["failed_units"][0]["status"] == "blocked_matching_failed_unit_fingerprint"
    assert action["blocking_artifact_refs"][0]["artifact_role"] == "display_input_payload"
    assert study["blocked_reason"] == "display_surface_materialization_failed"
    assert study["next_owner"] == "artifact_os"
    assert study["external_supervisor_required"] is False
