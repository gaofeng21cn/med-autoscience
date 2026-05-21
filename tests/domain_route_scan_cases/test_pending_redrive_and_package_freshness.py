from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_route_scan_cases.owner_route_test_helpers import (
    assert_controller_authorization_handoff,
    assert_owner_route_required,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scan_domain_routes_resumes_existing_pending_message_for_no_live_redrive(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    work_unit_fingerprint = "publication-blockers::current"
    publication_eval = {
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
                "specificity_targets": [
                    {"target_kind": "claim", "target_id": "claim_map", "source_path": str(study_root / "paper" / "claim_evidence_map.json")}
                ],
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "decision_id": "current-dpcc-write-redrive",
            "study_id": study_id,
            "quest_id": study_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "run_quality_repair_batch"}],
            "route_target": "write",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        },
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "active",
            "quest_id": study_id,
            "active_run_id": None,
            "worker_running": False,
            "pending_user_message_count": 1,
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "same_fingerprint_no_artifact_delta",
            "same_fingerprint_auto_turn_count": 5,
            "retry_state": {"terminal": True},
        },
    )
    _write_json(
        quest_root / ".ds" / "user_message_queue.json",
        {
            "version": 1,
            "pending": [{"message_id": "msg-hard-stop", "source": "codex-publication-gate", "status": "queued"}],
            "completed": [],
        },
    )

    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            {
                "study_id": study_id,
                "study_root": str(study_root),
                "quest_id": study_id,
                "quest_root": str(quest_root),
                "quest_status": "active",
                "decision": "resume",
                "reason": "quest_marked_running_but_no_live_session",
                "active_run_id": None,
                "runtime_liveness_audit": {"active_run_id": None, "runtime_audit": {"worker_running": False}},
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "external_supervisor_required",
                    "attempt_state": "escalated",
                    "retry_budget_remaining": 0,
                    "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
                },
                "publication_eval": publication_eval,
            },
            {
                "study_id": study_id,
                "current_stage": "managed_runtime_escalated",
                "paper_stage": "write",
                "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
                "supervision": {"active_run_id": None, "health_status": "recovering"},
                "quality_review_loop": {"closure_state": "review_required"},
            },
            study_id,
            publication_eval,
        ),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
    )

    apply_result = result["studies"][0]["runtime_platform_repair_apply"]
    runtime_state = assert_owner_route_required(apply_result=apply_result, quest_root=quest_root)
    assert apply_result["current_controller_authorization_written"] is False
    assert apply_result["current_controller_authorization"]["reason"] == "pending_user_messages_present"
    assert apply_result["existing_pending_user_message_resume"]["marked"] is True
    assert runtime_state["pending_user_message_count"] == 1
    assert runtime_state["same_fingerprint_auto_turn_count"] == 0
    assert "last_controller_decision_authorization" not in runtime_state
    assert "retry_state" not in runtime_state


def test_scan_domain_routes_blocks_pending_redrive_when_resume_adopts_evidence_without_live_worker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_fingerprint = "publication-blockers::497d1260db522f01"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dpcc::current",
        "assessment_provenance": {"owner": "ai_reviewer"},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "decision_id": "pending-dpcc-write-redrive",
            "study_id": study_id,
            "quest_id": study_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "run_quality_repair_batch"}],
            "route_target": "write",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        },
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "waiting_for_user",
            "quest_id": study_id,
            "active_run_id": None,
            "worker_running": False,
            "pending_user_message_count": 0,
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "controller_work_unit_pending",
            "last_controller_decision_authorization": {
                "authorized_at": "2026-05-09T18:23:16+00:00",
                "controller_actions": ["run_quality_repair_batch"],
                "decision_id": "pending-dpcc-write-redrive",
                "route_target": "analysis-campaign",
                "work_unit_fingerprint": work_unit_fingerprint,
                "work_unit_id": "analysis_claim_evidence_repair",
                "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
            },
        },
    )

    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            {
                "study_id": study_id,
                "study_root": str(study_root),
                "quest_id": study_id,
                "quest_root": str(quest_root),
                "quest_status": "waiting_for_user",
                "decision": "resume",
                "reason": "quest_waiting_platform_repair_redrive",
                "active_run_id": None,
                "runtime_liveness_audit": {"active_run_id": None, "runtime_audit": {"worker_running": False}},
                "continuation_state": {
                    "active_run_id": None,
                    "status": "waiting_for_user",
                    "continuation_policy": "auto",
                    "continuation_anchor": "decision",
                    "continuation_reason": "controller_work_unit_pending",
                    "pending_user_message_count": 0,
                },
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "recover_runtime",
                    "attempt_state": "recovering",
                    "retry_budget_remaining": 2,
                    "blocking_reasons": ["quest_marked_running_but_no_live_session"],
                },
                "publication_eval": publication_eval,
            },
            {
                "study_id": study_id,
                "current_stage": "publication_supervision",
                "paper_stage": "write",
                "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
                "supervision": {"active_run_id": None, "health_status": "recovering"},
                "quality_review_loop": {"closure_state": "review_required"},
            },
            study_id,
            publication_eval,
        ),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
    )

    apply_result = result["studies"][0]["runtime_platform_repair_apply"]
    runtime_state = assert_owner_route_required(
        apply_result=apply_result,
        quest_root=quest_root,
        expected_reason="runtime_controller_redrive_required",
    )
    assert_controller_authorization_handoff(
        apply_result,
        expected_decision_id="pending-dpcc-write-redrive",
        expected_work_unit_id="analysis_claim_evidence_repair",
    )
    assert runtime_state["last_controller_decision_authorization"]["decision_id"] == "pending-dpcc-write-redrive"
    assert result["studies"][0]["ai_repair_lifecycle"]["state"] == "owner_route_required"
