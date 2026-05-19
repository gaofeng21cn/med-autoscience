from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study, write_text


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scan_consumes_analysis_harmonization_typed_blocker_without_requeue(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::hard-methodology",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::ai-reviewer-re-eval",
                "action_type": "return_to_controller",
                "work_unit_fingerprint": (
                    "domain-transition::ai_reviewer_re_eval::ai_reviewer_medical_prose_quality_review"
                ),
                "next_work_unit": {
                    "unit_id": "ai_reviewer_medical_prose_quality_review",
                    "lane": "review",
                },
            }
        ],
    }
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "schema_version": 1,
            "status": "blocked",
            "ok": False,
            "study_id": study_id,
            "quest_id": quest_id,
            "blocked_reason": "unit_harmonized_rerun_required",
            "next_owner": "analysis_harmonization_owner",
            "next_work_unit": "unit_harmonized_external_validation_rerun",
            "hard_methodology_target": {
                "target_id": "hdl_unit_standardized_sensitivity",
                "required_owner": "analysis_harmonization_owner",
                "required_next_work_unit": "unit_harmonized_external_validation_rerun",
                "typed_blocker": "unit_harmonized_rerun_required",
            },
            "quality_gate_relaxation_allowed": False,
            "current_package_write_allowed": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json",
        {
            "surface": "analysis_harmonization_owner_result",
            "schema_version": 1,
            "study_id": study_id,
            "owner": "analysis_harmonization_owner",
            "work_unit": "unit_harmonized_external_validation_rerun",
            "status": "blocked",
            "blocked_reason": "unit_harmonized_rerun_required",
            "typed_blocker_owner": "analysis_harmonization_owner",
            "typed_blocker": {"blocker_id": "unit_harmonized_rerun_required"},
            "unit_harmonized_rerun_completed": False,
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "medical_claim_authoring_allowed": False,
            "publication_eval_written": False,
            "controller_decision_written": False,
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "paused",
        "decision": "blocked",
        "reason": "quest_waiting_for_user",
        "active_run_id": None,
        "auto_runtime_parked": {
            "parked": True,
            "parked_state": "explicit_resume_pending",
            "awaiting_explicit_wakeup": True,
            "auto_execution_complete": False,
        },
        "runtime_liveness_audit": {
            "active_run_id": None,
            "runtime_audit": {"worker_running": False, "active_run_id": None},
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-epoch-dm002-hard",
            "canonical_runtime_action": "external_supervisor_required",
            "attempt_state": "escalated",
            "retry_budget_remaining": 0,
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-hard-methodology",
            "source_signature": "truth-source-dm002-hard-methodology",
        },
        "publication_eval": publication_eval,
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "auto_runtime_parked",
        "paper_stage": "analysis-campaign",
        "auto_runtime_parked": status_payload["auto_runtime_parked"],
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "quality_review_loop": {"closure_state": "review_required"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
        "ai_repair_lifecycle": {
            "state": "blocked",
            "blocked_reason": "domain_transition_ai_reviewer_re_eval",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
        },
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["action_queue"] == []
    assert result["action_queue"] == []
    assert study["why_not_applied"] == "unit_harmonized_rerun_required"
    assert study["blocked_reason"] == "unit_harmonized_rerun_required"
    assert study["next_owner"] == "analysis_harmonization_owner"
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["next_owner"] == "analysis_harmonization_owner"
    assert study["owner_route"]["owner_reason"] == "unit_harmonized_rerun_required"
    assert study["owner_route"]["allowed_actions"] == []


def test_scan_queues_source_provenance_owner_for_model_provenance_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::hard-methodology",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "recommended_actions": [],
    }
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "schema_version": 1,
            "status": "blocked",
            "ok": False,
            "study_id": study_id,
            "quest_id": quest_id,
            "blocked_reason": "unit_harmonized_rerun_required",
            "next_owner": "analysis_harmonization_owner",
            "next_work_unit": "unit_harmonized_external_validation_rerun",
            "hard_methodology_target": {
                "target_id": "hdl_unit_standardized_sensitivity",
                "required_owner": "analysis_harmonization_owner",
                "required_next_work_unit": "unit_harmonized_external_validation_rerun",
                "typed_blocker": "unit_harmonized_rerun_required",
            },
            "quality_gate_relaxation_allowed": False,
            "current_package_write_allowed": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json",
        {
            "surface": "analysis_harmonization_owner_result",
            "schema_version": 1,
            "study_id": study_id,
            "owner": "analysis_harmonization_owner",
            "work_unit": "unit_harmonized_external_validation_rerun",
            "status": "blocked",
            "blocked_reason": "unit_harmonized_rerun_required",
            "typed_blocker_owner": "analysis_harmonization_owner",
            "typed_blocker": {
                "blocker_id": "unit_harmonized_rerun_required",
                "blocking_reasons": [
                    "hdl_unit_scale_mismatch",
                    "cox_model_application_provenance_insufficient_for_rerun",
                ],
            },
            "blocking_owner_route": {
                "blocked_reason": "transport_model_provenance_recovery_required",
                "next_owner": "source_provenance_owner",
                "next_work_unit": "recover_transport_model_provenance",
            },
            "unit_harmonized_rerun_completed": False,
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "medical_claim_authoring_allowed": False,
            "publication_eval_written": False,
            "controller_decision_written": False,
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "paused",
        "decision": "blocked",
        "reason": "quest_waiting_for_user",
        "active_run_id": None,
        "auto_runtime_parked": {
            "parked": True,
            "parked_state": "explicit_resume_pending",
            "awaiting_explicit_wakeup": True,
            "auto_execution_complete": False,
        },
        "runtime_liveness_audit": {
            "active_run_id": None,
            "runtime_audit": {"worker_running": False, "active_run_id": None},
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-epoch-dm002-hard",
            "canonical_runtime_action": "external_supervisor_required",
            "attempt_state": "escalated",
            "retry_budget_remaining": 0,
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-hard-methodology",
            "source_signature": "truth-source-dm002-hard-methodology",
        },
        "publication_eval": publication_eval,
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "auto_runtime_parked",
        "paper_stage": "analysis-campaign",
        "auto_runtime_parked": status_payload["auto_runtime_parked"],
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "quality_review_loop": {"closure_state": "review_required"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
        "ai_repair_lifecycle": {
            "state": "blocked",
            "blocked_reason": "domain_transition_ai_reviewer_re_eval",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
        },
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [action["action_type"] for action in study["action_queue"]] == ["recover_transport_model_provenance"]
    assert [action["action_type"] for action in result["action_queue"]] == ["recover_transport_model_provenance"]
    action = study["action_queue"][0]
    assert action["owner"] == "source_provenance_owner"
    assert action["reason"] == "transport_model_provenance_recovery_required"
    assert action["required_output_surface"] == (
        "canonical transport model provenance bundle or "
        "typed blocker:transport_model_provenance_recovery_required"
    )
    assert study["why_not_applied"] == "transport_model_provenance_recovery_required"
    assert study["blocked_reason"] == "transport_model_provenance_recovery_required"
    assert study["next_owner"] == "source_provenance_owner"
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["next_owner"] == "source_provenance_owner"
    assert study["owner_route"]["owner_reason"] == "transport_model_provenance_recovery_required"
    assert study["owner_route"]["allowed_actions"] == ["recover_transport_model_provenance"]


def test_scan_requeues_stale_source_provenance_typed_blocker_without_search_trace(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::hard-methodology",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "recommended_actions": [],
    }
    _write_json(
        study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json",
        {
            "surface": "analysis_harmonization_owner_result",
            "schema_version": 1,
            "study_id": study_id,
            "owner": "analysis_harmonization_owner",
            "work_unit": "unit_harmonized_external_validation_rerun",
            "status": "blocked",
            "blocked_reason": "unit_harmonized_rerun_required",
            "typed_blocker_owner": "analysis_harmonization_owner",
            "typed_blocker": {
                "blocker_id": "unit_harmonized_rerun_required",
                "blocking_reasons": ["cox_model_application_provenance_insufficient_for_rerun"],
            },
            "blocking_owner_route": {
                "blocked_reason": "transport_model_provenance_recovery_required",
                "next_owner": "source_provenance_owner",
                "next_work_unit": "recover_transport_model_provenance",
            },
            "unit_harmonized_rerun_completed": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "source_provenance" / "latest.json",
        {
            "surface": "source_provenance_owner_result",
            "schema_version": 1,
            "study_id": study_id,
            "owner": "source_provenance_owner",
            "work_unit": "recover_transport_model_provenance",
            "status": "blocked",
            "blocked_reason": "transport_model_provenance_recovery_required",
            "typed_blocker_owner": "source_provenance_owner",
            "typed_blocker": {
                "blocker_id": "transport_model_provenance_recovery_required",
                "blocking_reasons": ["cox_model_coefficients_missing"],
            },
            "transport_model_provenance_recovered": False,
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "medical_claim_authoring_allowed": False,
            "publication_eval_written": False,
            "controller_decision_written": False,
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "paused",
        "decision": "blocked",
        "reason": "quest_waiting_for_user",
        "active_run_id": None,
        "auto_runtime_parked": {
            "parked": True,
            "parked_state": "explicit_resume_pending",
            "awaiting_explicit_wakeup": True,
            "auto_execution_complete": False,
        },
        "runtime_liveness_audit": {
            "active_run_id": None,
            "runtime_audit": {"worker_running": False, "active_run_id": None},
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-epoch-dm002-hard",
            "canonical_runtime_action": "external_supervisor_required",
            "attempt_state": "escalated",
            "retry_budget_remaining": 0,
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-hard-methodology",
            "source_signature": "truth-source-dm002-hard-methodology",
        },
        "publication_eval": publication_eval,
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "auto_runtime_parked",
        "paper_stage": "analysis-campaign",
        "auto_runtime_parked": status_payload["auto_runtime_parked"],
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "quality_review_loop": {"closure_state": "review_required"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
        "ai_repair_lifecycle": {
            "state": "blocked",
            "blocked_reason": "domain_transition_ai_reviewer_re_eval",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
        },
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [action["action_type"] for action in study["action_queue"]] == ["recover_transport_model_provenance"]
    assert [action["action_type"] for action in result["action_queue"]] == ["recover_transport_model_provenance"]
    assert study["why_not_applied"] == "transport_model_provenance_recovery_required"
    assert study["blocked_reason"] == "transport_model_provenance_recovery_required"
    assert study["next_owner"] == "source_provenance_owner"
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["next_owner"] == "source_provenance_owner"
    assert study["owner_route"]["owner_reason"] == "transport_model_provenance_recovery_required"
    assert study["owner_route"]["allowed_actions"] == ["recover_transport_model_provenance"]


def test_scan_consumes_current_source_provenance_typed_blocker_without_requeue(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::hard-methodology",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "recommended_actions": [],
    }
    _write_json(
        study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json",
        {
            "surface": "analysis_harmonization_owner_result",
            "schema_version": 1,
            "study_id": study_id,
            "owner": "analysis_harmonization_owner",
            "work_unit": "unit_harmonized_external_validation_rerun",
            "status": "blocked",
            "blocked_reason": "unit_harmonized_rerun_required",
            "typed_blocker_owner": "analysis_harmonization_owner",
            "typed_blocker": {
                "blocker_id": "unit_harmonized_rerun_required",
                "blocking_reasons": ["cox_model_application_provenance_insufficient_for_rerun"],
            },
            "blocking_owner_route": {
                "blocked_reason": "transport_model_provenance_recovery_required",
                "next_owner": "source_provenance_owner",
                "next_work_unit": "recover_transport_model_provenance",
            },
            "unit_harmonized_rerun_completed": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "source_provenance" / "latest.json",
        {
            "surface": "source_provenance_owner_result",
            "schema_version": 1,
            "study_id": study_id,
            "owner": "source_provenance_owner",
            "work_unit": "recover_transport_model_provenance",
            "status": "blocked",
            "blocked_reason": "transport_model_provenance_recovery_required",
            "typed_blocker_owner": "source_provenance_owner",
            "typed_blocker": {
                "blocker_id": "transport_model_provenance_recovery_required",
                "blocking_reasons": [
                    "cox_model_coefficients_missing",
                    "canonical_transport_model_provenance_bundle_missing",
                ],
            },
            "transport_model_provenance_recovered": False,
            "provenance_search": {
                "searched": True,
                "accepted_bundle_ref": None,
                "candidate_count": 0,
                "candidates": [],
                "result_summary_acceptance_allowed": False,
                "substitute_refit_allowed": False,
            },
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "medical_claim_authoring_allowed": False,
            "publication_eval_written": False,
            "controller_decision_written": False,
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "paused",
        "decision": "blocked",
        "reason": "quest_waiting_for_user",
        "active_run_id": None,
        "auto_runtime_parked": {
            "parked": True,
            "parked_state": "explicit_resume_pending",
            "awaiting_explicit_wakeup": True,
            "auto_execution_complete": False,
        },
        "runtime_liveness_audit": {
            "active_run_id": None,
            "runtime_audit": {"worker_running": False, "active_run_id": None},
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-epoch-dm002-hard",
            "canonical_runtime_action": "external_supervisor_required",
            "attempt_state": "escalated",
            "retry_budget_remaining": 0,
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-hard-methodology",
            "source_signature": "truth-source-dm002-hard-methodology",
        },
        "publication_eval": publication_eval,
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "auto_runtime_parked",
        "paper_stage": "analysis-campaign",
        "auto_runtime_parked": status_payload["auto_runtime_parked"],
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "quality_review_loop": {"closure_state": "review_required"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
        "ai_repair_lifecycle": {
            "state": "blocked",
            "blocked_reason": "domain_transition_ai_reviewer_re_eval",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
        },
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [action["action_type"] for action in study["action_queue"]] == ["methodology_reframe_route_decision"]
    assert [action["action_type"] for action in result["action_queue"]] == ["methodology_reframe_route_decision"]
    action = study["action_queue"][0]
    assert action["owner"] == "decision"
    assert action["reason"] == "methodology_reframe_required"
    assert action["required_output_surface"] == (
        "controller route decision for a provenance-limited reframe, reproducible-model restart, "
        "stop-loss, or human gate"
    )
    assert study["why_not_applied"] == "methodology_reframe_required"
    assert study["blocked_reason"] == "methodology_reframe_required"
    assert study["next_owner"] == "decision"
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["next_owner"] == "decision"
    assert study["owner_route"]["owner_reason"] == "methodology_reframe_required"
    assert study["owner_route"]["allowed_actions"] == ["methodology_reframe_route_decision"]


def test_scan_does_not_requeue_methodology_reframe_after_controller_decision_materialized(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    quest_root.mkdir(parents=True)
    write_text(quest_root / "quest.yaml", f"quest_id: {quest_id}\nstudy_id: {study_id}\n")
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::methodology-reframe",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "quality_assessment": {"medical_journal_prose_quality": {"status": "underdefined"}},
        "recommended_actions": [],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller" / "source_provenance" / "latest.json",
        {
            "surface": "source_provenance_owner_result",
            "schema_version": 1,
            "study_id": study_id,
            "owner": "source_provenance_owner",
            "work_unit": "recover_transport_model_provenance",
            "status": "blocked",
            "blocked_reason": "transport_model_provenance_recovery_required",
            "typed_blocker_owner": "source_provenance_owner",
            "typed_blocker": {"blocker_id": "transport_model_provenance_recovery_required"},
            "transport_model_provenance_recovered": False,
            "provenance_search": {
                "searched": True,
                "accepted_bundle_ref": None,
                "result_summary_acceptance_allowed": False,
                "substitute_refit_allowed": False,
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "study-decision::dm002::methodology-reframe",
            "study_id": study_id,
            "quest_id": quest_id,
            "emitted_at": "2026-05-18T23:13:18+00:00",
            "decision_type": "bounded_analysis",
            "charter_ref": {
                "charter_id": f"charter::{study_id}::v1",
                "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            },
            "runtime_escalation_ref": {
                "record_id": "runtime-escalation::dm002::methodology_reframe_required",
                "artifact_path": str(
                    study_root / "artifacts" / "runtime" / "escalation" / "methodology_reframe_required.json"
                ),
                "summary_ref": str(
                    study_root / "artifacts" / "runtime" / "escalation" / "methodology_reframe_required.md"
                ),
            },
            "publication_eval_ref": {
                "eval_id": publication_eval["eval_id"],
                "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            },
            "requires_human_confirmation": False,
            "controller_actions": [
                {
                    "action_type": "ensure_study_runtime",
                    "payload_ref": str(study_root / "artifacts" / "supervision" / "requests" / "decision" / "latest.json"),
                }
            ],
            "reason": "methodology reframe route decision materialized",
            "route_target": "analysis-campaign",
            "route_key_question": "Can DM002 continue without original transported model provenance?",
            "route_rationale": "Route back for methodology reframe before manuscript work.",
            "work_unit_fingerprint": "decision::methodology_reframe_route_decision",
            "next_work_unit": {
                "unit_id": "provenance_limited_harmonization_audit",
                "lane": "analysis-campaign",
                "hard_methodology": True,
                "selected_route_option": "provenance_limited_harmonization_audit",
                "terminal_source_provenance_blocker_consumed": True,
                "current_transport_claim_must_not_be_used_as_medical_conclusion": True,
                "route_options": [
                    "stop_loss_current_transport_claim",
                    "provenance_limited_harmonization_audit",
                    "rebuild_reproducible_model_route",
                    "human_gate",
                ],
            },
        },
    )
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "active_run_id": None,
        "current_stage": "publication_supervision",
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-methodology-reframe",
            "source_signature": "truth-source-dm002-methodology-reframe",
        },
        "publication_eval": publication_eval,
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "auto_runtime_parked",
        "paper_stage": "analysis-campaign",
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "quality_review_loop": {"closure_state": "review_required"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
        "ai_repair_lifecycle": {
            "state": "blocked",
            "blocked_reason": "domain_transition_ai_reviewer_re_eval",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
        },
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [action["action_type"] for action in study["action_queue"]] == [
        "provenance_limited_harmonization_audit"
    ]
    assert [action["action_type"] for action in result["action_queue"]] == [
        "provenance_limited_harmonization_audit"
    ]
    action = study["action_queue"][0]
    assert action["owner"] == "provenance_limited_harmonization_owner"
    assert action["reason"] == "provenance_limited_harmonization_audit_required"
    assert study["blocked_reason"] == "provenance_limited_harmonization_audit_required"
    assert study["next_owner"] == "provenance_limited_harmonization_owner"
    assert study["owner_route"]["allowed_actions"] == ["provenance_limited_harmonization_audit"]


def test_scan_requeues_stale_self_loop_methodology_reframe_decision(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    quest_root.mkdir(parents=True)
    write_text(quest_root / "quest.yaml", f"quest_id: {quest_id}\nstudy_id: {study_id}\n")
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::stale-self-loop",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "recommended_actions": [],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller" / "source_provenance" / "latest.json",
        {
            "surface": "source_provenance_owner_result",
            "schema_version": 1,
            "study_id": study_id,
            "owner": "source_provenance_owner",
            "work_unit": "recover_transport_model_provenance",
            "status": "blocked",
            "blocked_reason": "transport_model_provenance_recovery_required",
            "typed_blocker_owner": "source_provenance_owner",
            "typed_blocker": {"blocker_id": "transport_model_provenance_recovery_required"},
            "transport_model_provenance_recovered": False,
            "provenance_search": {
                "searched": True,
                "accepted_bundle_ref": None,
                "result_summary_acceptance_allowed": False,
                "substitute_refit_allowed": False,
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "study-decision::dm002::stale-methodology-self-loop",
            "study_id": study_id,
            "quest_id": quest_id,
            "decision_type": "route_back_same_line",
            "work_unit_fingerprint": "decision::methodology_reframe_route_decision",
            "next_work_unit": {"unit_id": "methodology_reframe_route_decision", "owner": "decision"},
        },
    )
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "active_run_id": None,
        "publication_eval": publication_eval,
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "auto_runtime_parked",
        "paper_stage": "analysis-campaign",
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "ai_repair_lifecycle": {"state": "blocked", "blocked_reason": "domain_transition_ai_reviewer_re_eval"},
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [action["action_type"] for action in study["action_queue"]] == ["methodology_reframe_route_decision"]
