from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


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
