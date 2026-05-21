from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_route_scan_cases.owner_route_test_helpers import assert_owner_route_required
from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scan_domain_routes_runtime_repair_routes_package_freshness_terminal_to_gate_clearing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
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

    ensure_calls: list[dict[str, object]] = []

    def fake_ensure_study_runtime(**kwargs: object) -> dict[str, object]:
        ensure_calls.append(dict(kwargs))
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

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=("001-dm-cvd-mortality-risk",),
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
    assert apply_result["repair_kind"] == "active_runtime_no_live_worker_relaunch"
    assert [item["action_type"] for item in study["action_queue"]] == []
    assert study["ai_repair_lifecycle"]["state"] == "owner_route_required"
    assert study["ai_repair_lifecycle"]["blocked_reason"] == "opl_runtime_owner_route_required"
    assert study["ai_repair_lifecycle"]["next_owner"] == "one-person-lab"
    assert study["why_not_applied"] == "runtime_recovery_retry_budget_exhausted"
    assert study["blocked_reason"] == "opl_runtime_owner_route_required"
    assert study["next_owner"] == "one-person-lab"
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["next_owner"] == "one-person-lab"
    assert study["owner_route"]["owner_reason"] == "opl_runtime_owner_route_required"
    assert study["owner_route"]["allowed_actions"] == []
    assert study["paper_package_mutated"] is False


def test_scan_domain_routes_routes_blocked_submission_refresh_lifecycle_to_artifact_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    work_unit_fingerprint = "publication-blockers::submission-refresh"
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::submission-refresh",
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {
                    "unit_id": "submission_minimal_refresh",
                    "lane": "finalize",
                    "summary": "Refresh stale submission_minimal and current delivery surfaces.",
                },
                "specificity_targets": [
                    {
                        "target_kind": "table",
                        "target_id": "submission_minimal_authority",
                        "source_path": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
                        "blocking_reason": "stale_submission_minimal_authority",
                    },
                    {
                        "target_kind": "claim",
                        "target_id": "claim_evidence_map",
                        "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
                        "blocking_reason": "stale_submission_minimal_authority",
                    },
                    {
                        "target_kind": "figure",
                        "target_id": "figure_catalog",
                        "source_path": str(study_root / "paper" / "figures" / "figure_catalog.json"),
                        "blocking_reason": "stale_submission_minimal_authority",
                    },
                    {
                        "target_kind": "metric",
                        "target_id": "main_result_metrics",
                        "source_path": str(quest_root / "artifacts" / "results" / "main_result.json"),
                        "blocking_reason": "stale_submission_minimal_authority",
                    },
                    {
                        "target_kind": "source_path",
                        "target_id": "publication_gate_source_path",
                        "source_path": str(quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"),
                        "blocking_reason": "stale_submission_minimal_authority",
                    },
                ],
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "current-submission-refresh",
            "study_id": study_id,
            "quest_id": quest_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
            "route_target": "finalize",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {
                "unit_id": "submission_minimal_refresh",
                "lane": "finalize",
                "summary": "Refresh stale submission_minimal and current delivery surfaces.",
            },
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "blocked",
        "reason": "quest_waiting_for_user",
        "active_run_id": None,
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
        "continuation_state": {
            "quest_status": "waiting_for_user",
            "active_run_id": None,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "turn_closeout",
            "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            "pending_user_message_count": 0,
        },
        "blocked_turn_closeout": {
            "blocked_reason": "control_plane_route_blocked_bundle_build",
            "next_owner": "MAS/controller route authorization owner for bundle_build_allowed on submission_minimal_refresh",
        },
        "publication_eval": publication_eval,
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-submission-refresh",
            "source_signature": "truth-source-submission-refresh",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "current_stage": "auto_runtime_parked",
        "paper_stage": "bundle_stage_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "supervision": {"active_run_id": None, "health_status": "escalated"},
        "ai_repair_lifecycle": {
            "state": "blocked",
            "blocked_reason": "controller_decision_not_superseded",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
            "auto_apply_allowed": True,
            "top_action": {
                "action_type": "runtime_platform_repair",
                "repair_kind": "stale_specificity_terminal_gate_redrive",
                "owner": "mas_controller",
                "auto_apply_allowed": True,
            },
        },
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["current_package_freshness_required"]
    assert [item["action_type"] for item in result["action_queue"]] == ["current_package_freshness_required"]
    assert study["action_queue"][0]["owner"] == "artifact_os"
    assert study["why_not_applied"] == "current_package_freshness_required"
    assert study["blocked_reason"] == "current_package_freshness_required"
    assert study["next_owner"] == "artifact_os"
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["next_owner"] == "artifact_os"
    assert study["owner_route"]["owner_reason"] == "current_package_freshness_required"
    assert study["owner_route"]["allowed_actions"] == ["current_package_freshness_required"]


def test_scan_domain_routes_routes_owner_callable_submission_qc_closeout_to_artifact_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    work_unit_fingerprint = "publication-blockers::submission-qc"
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm003::submission-qc",
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {
                    "unit_id": "submission_minimal_refresh",
                    "lane": "finalize",
                    "summary": "Refresh submission surfaces after submission QC failure.",
                },
                "specificity_targets": [
                    {
                        "target_kind": "claim",
                        "target_id": "claim_evidence_map",
                        "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
                        "blocking_reason": "submission_surface_qc_failure_present",
                    },
                    {
                        "target_kind": "figure",
                        "target_id": "figure_catalog",
                        "source_path": str(study_root / "paper" / "figures" / "figure_catalog.json"),
                        "blocking_reason": "submission_surface_qc_failure_present",
                    },
                    {
                        "target_kind": "table",
                        "target_id": "submission_manifest",
                        "source_path": str(study_root / "paper" / "submission_minimal" / "audit" / "submission_manifest.json"),
                        "blocking_reason": "submission_surface_qc_failure_present",
                    },
                    {
                        "target_kind": "metric",
                        "target_id": "main_result_metrics",
                        "source_path": str(quest_root / "artifacts" / "results" / "main_result.json"),
                        "blocking_reason": "submission_surface_qc_failure_present",
                    },
                    {
                        "target_kind": "source_path",
                        "target_id": "publication_gate_source_path",
                        "source_path": str(quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"),
                        "blocking_reason": "submission_surface_qc_failure_present",
                    },
                ],
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "current-submission-qc-refresh",
            "study_id": study_id,
            "quest_id": quest_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
            "route_target": "finalize",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {
                "unit_id": "submission_minimal_refresh",
                "lane": "finalize",
                "summary": "Refresh submission surfaces after submission QC failure.",
            },
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "blocked",
        "reason": "quest_waiting_for_submission_metadata",
        "active_run_id": None,
        "runtime_liveness_audit": {
            "active_run_id": None,
            "runtime_audit": {"worker_running": False, "active_run_id": None},
        },
        "runtime_health_snapshot": {
            "canonical_runtime_action": "await_explicit_resume",
            "attempt_state": "awaiting_explicit_resume",
            "retry_budget_remaining": 0,
            "blocking_reasons": [],
        },
        "continuation_state": {
            "quest_status": "waiting_for_user",
            "active_run_id": None,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "turn_closeout",
            "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            "pending_user_message_count": 9,
        },
        "blocked_turn_closeout": {
            "blocked_reason": "owner_callable_surface_missing",
            "next_owner": "MAS/controller",
        },
        "interaction_arbitration": {
            "classification": "blocked_closeout_owner_wait",
            "action": "block",
            "reason_code": "blocked_turn_closeout_waiting_for_owner",
            "requires_user_input": False,
            "valid_blocking": True,
            "blocked_reason": "owner_callable_surface_missing",
            "next_owner": "MAS/controller",
        },
        "publication_eval": publication_eval,
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-submission-qc",
            "source_signature": "truth-source-submission-qc",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "current_stage": "auto_runtime_parked",
        "paper_stage": "bundle_stage_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "ai_repair_lifecycle": {
            "state": "blocked",
            "blocked_reason": "stale_specificity_terminal_gate_not_found",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
            "auto_apply_allowed": True,
            "top_action": {
                "action_type": "runtime_platform_repair",
                "repair_kind": "stale_specificity_terminal_gate_redrive",
                "owner": "mas_controller",
                "auto_apply_allowed": True,
            },
        },
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["current_package_freshness_required"]
    assert study["action_queue"][0]["owner"] == "artifact_os"
    assert study["why_not_applied"] == "current_package_freshness_required"
    assert study["next_owner"] == "artifact_os"
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["allowed_actions"] == ["current_package_freshness_required"]


def test_scan_domain_routes_routes_failed_gate_clearing_display_unit_to_concrete_artifact_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
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

    result = module.scan_domain_routes(
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


def test_scan_domain_routes_routes_failed_gate_clearing_when_eval_id_changed_but_work_unit_matches(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
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

    result = module.scan_domain_routes(
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


def test_scan_domain_routes_routes_reused_display_input_failure_to_artifact_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
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

    result = module.scan_domain_routes(
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
