from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_supervisor_scan_clears_stale_ai_reviewer_lifecycle_after_reviewer_eval_materialized(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm")
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    ai_reviewer_eval = {
        "schema_version": 1,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
        },
        "recommended_actions": [],
    }
    _write_json(publication_eval_path, ai_reviewer_eval)
    lifecycle_path = study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json"
    _write_json(
        lifecycle_path,
        {
            "surface": "ai_repair_lifecycle",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": "quest-dm",
            "state": "blocked",
            "blocked_reason": "ai_reviewer_assessment_required",
            "next_owner": "ai_reviewer",
            "external_supervisor_required": False,
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": "quest-dm",
            "quest_root": str(profile.runtime_root / "quest-dm"),
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "active_run_id": "run-live",
            "runtime_liveness_audit": {
                "active_run_id": "run-live",
                "runtime_audit": {"worker_running": True, "active_run_id": "run-live"},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "observe_runtime",
                "attempt_state": "live",
                "retry_budget_remaining": 3,
            },
            "publication_eval": ai_reviewer_eval,
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-current",
                "source_signature": "truth-source-current",
                "canonical_next_action": "supervise_runtime",
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "current_stage": "publication_supervision",
            "paper_stage": "write",
            "refs": {"publication_eval_path": str(publication_eval_path)},
            "supervision": {"active_run_id": "run-live", "health_status": "live"},
            "quality_review_loop": {"closure_state": "review_required"},
            "ai_repair_lifecycle": {
                "state": "blocked",
                "blocked_reason": "ai_reviewer_assessment_required",
                "next_owner": "ai_reviewer",
                "external_supervisor_required": False,
            },
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
    )

    study = result["studies"][0]
    assert study["ai_reviewer_assessment"] == {
        "present": True,
        "owner": "ai_reviewer",
        "required": False,
        "missing": False,
    }
    assert study["action_queue"] == []
    assert study["ai_repair_lifecycle"] is None
    assert study["why_not_applied"] is None
    assert study["blocked_reason"] is None
    assert study["next_owner"] is None
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["owner_reason"] is None
    assert study["owner_route"]["allowed_actions"] == []
    assert not lifecycle_path.exists()


def test_supervisor_scan_clears_stale_runtime_relaunch_lifecycle_after_live_worker_observed(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    ai_reviewer_eval = {
        "schema_version": 1,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
        },
        "recommended_actions": [],
    }
    _write_json(publication_eval_path, ai_reviewer_eval)
    lifecycle_path = study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json"
    _write_json(
        lifecycle_path,
        {
            "surface": "ai_repair_lifecycle",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "state": "blocked",
            "blocked_reason": "runtime_relaunch_no_live_run_started",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": study_id,
            "quest_root": str(profile.runtime_root / study_id),
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "active_run_id": "run-live",
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-live",
                "runtime_audit": {"status": "live", "worker_running": True, "active_run_id": "run-live"},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "recover_runtime",
                "attempt_state": "recovering",
                "retry_budget_remaining": 3,
                "worker_liveness_state": {
                    "state": "activity_timeout",
                    "runtime_liveness_status": "live",
                    "worker_running": True,
                    "active_run_id": "run-live",
                },
                "blocking_reasons": [
                    "live_worker_meaningful_artifact_delta_timeout",
                    "same_fingerprint_loop",
                ],
            },
            "publication_eval": ai_reviewer_eval,
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-live",
                "source_signature": "truth-source-live",
                "canonical_next_action": "resume_same_study_line",
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
            "refs": {"publication_eval_path": str(publication_eval_path)},
            "supervision": {"active_run_id": "run-live", "health_status": "recovering"},
            "quality_review_loop": {"closure_state": "review_required"},
            "ai_repair_lifecycle": {
                "state": "blocked",
                "blocked_reason": "runtime_relaunch_no_live_run_started",
                "next_owner": "external_supervisor",
                "external_supervisor_required": True,
            },
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
    )

    study = result["studies"][0]
    assert study["action_queue"] == []
    assert study["ai_repair_lifecycle"] is None
    assert study["why_not_applied"] is None
    assert study["blocked_reason"] is None
    assert study["next_owner"] is None
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["next_owner"] is None
    assert study["owner_route"]["allowed_actions"] == []
    assert not lifecycle_path.exists()


def test_supervisor_scan_suppresses_projection_only_external_supervisor_after_live_worker_observed(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    ai_reviewer_eval = {
        "schema_version": 1,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
        },
        "recommended_actions": [],
    }
    _write_json(publication_eval_path, ai_reviewer_eval)
    _write_json(
        study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json",
        {
            "surface": "autonomy_repair_orchestration",
            "schema_version": 1,
            "state": "ready_for_repair",
            "study_id": study_id,
            "quest_id": study_id,
            "actions": [
                {
                    "action_type": "controller_repair",
                    "auto_apply_allowed": True,
                    "owner": "mas_controller",
                    "repair_kind": "analysis_claim_evidence_redrive",
                    "risk": "medium",
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
            "quest_id": study_id,
            "quest_root": str(profile.runtime_root / study_id),
            "quest_status": "running",
            "decision": "resume",
            "reason": "quest_drifting_into_write_without_gate_approval",
            "active_run_id": "run-live",
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-live",
                "runtime_audit": {"status": "live", "worker_running": True, "active_run_id": "run-live"},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "recover_runtime",
                "attempt_state": "recovering",
                "retry_budget_remaining": 2,
                "worker_liveness_state": {
                    "state": "activity_timeout",
                    "runtime_liveness_status": "live",
                    "worker_running": True,
                    "active_run_id": "run-live",
                },
                "blocking_reasons": [
                    "live_worker_meaningful_artifact_delta_timeout",
                    "same_fingerprint_loop",
                ],
            },
            "publication_eval": ai_reviewer_eval,
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-live",
                "source_signature": "truth-source-live",
                "canonical_next_action": "resume_same_study_line",
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "current_stage": "publication_supervision",
            "paper_stage": "write",
            "refs": {"publication_eval_path": str(publication_eval_path)},
            "supervision": {"active_run_id": "run-live", "health_status": "recovering"},
            "quality_review_loop": {"closure_state": "review_required"},
            "ai_repair_lifecycle": {
                "state": "external_supervisor_required",
                "blocked_reason": "runtime_recovery_not_authorized",
                "next_owner": "external_supervisor",
                "external_supervisor_required": True,
                "projection_only": True,
            },
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["action_queue"] == []
    assert study["ai_repair_lifecycle"] is None
    assert study["why_not_applied"] is None
    assert study["blocked_reason"] is None
    assert study["next_owner"] is None
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["next_owner"] is None
    assert study["owner_route"]["allowed_actions"] == []
