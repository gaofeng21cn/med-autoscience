from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_route_scan_cases.owner_route_test_helpers import assert_owner_route_required
from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scan_domain_routes_redrives_mas_controller_owner_handoff_for_current_paper_work(
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
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
                "work_unit_targets": [
                    {
                        "target_kind": "claim",
                        "target_id": "claim_evidence_map",
                        "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
                    }
                ],
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "decision_id": "current-dpcc-owner-handoff-redrive",
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
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "turn_closeout",
            "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            "blocked_turn_closeout": {
                "run_id": "mas-run-dpcc-owner-handoff",
                "blocked_reason": "controller_callable_surface_failed_path_normalization",
                "next_owner": "MAS/controller",
            },
            "last_liveness_reconcile_reason": "blocked_turn_closeout_waiting_for_owner",
            "same_fingerprint_auto_turn_count": 4,
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
                    "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
                },
                "blocked_turn_closeout": {
                    "run_id": "mas-run-dpcc-owner-handoff",
                    "blocked_reason": "controller_callable_surface_failed_path_normalization",
                    "next_owner": "MAS/controller",
                },
                "interaction_arbitration": {
                    "classification": "blocked_closeout_owner_wait",
                    "action": "block",
                    "reason_code": "blocked_turn_closeout_waiting_for_owner",
                    "requires_user_input": False,
                    "valid_blocking": True,
                    "kind": "turn_closeout",
                    "next_owner": "MAS/controller",
                },
                "publication_eval": publication_eval,
            },
            {
                "study_id": study_id,
                "current_stage": "publication_supervision",
                "paper_stage": "write",
                "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
                "supervision": {"active_run_id": None, "health_status": "escalated"},
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
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    apply_result = study["runtime_platform_repair_apply"]
    runtime_state = assert_owner_route_required(
        apply_result=apply_result,
        quest_root=quest_root,
        expected_reason=None,
    )
    assert apply_result["reason"] == "runtime_controller_redrive_required"
    assert apply_result["repair_kind"] == "current_controller_owner_handoff_redrive"
    assert apply_result["current_controller_authorization_written"] is True
    assert apply_result["blocked_turn_closeout_clear"]["cleared"] is True
    assert runtime_state["last_controller_decision_authorization"]["decision_id"] == (
        "current-dpcc-owner-handoff-redrive"
    )
    assert "blocked_turn_closeout" not in runtime_state
    assert study["external_supervisor_required"] is False
    assert study["paper_package_mutated"] is False


def test_scan_domain_routes_applies_authorized_controller_work_unit_wait_redrive(
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
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
                "work_unit_targets": [
                    {
                        "target_kind": "claim",
                        "target_id": "claim_evidence_map",
                        "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
                    }
                ],
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "decision_id": "current-authorized-work-unit-redrive",
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
            "same_fingerprint_auto_turn_count": 4,
            "last_controller_decision_authorization": {
                "decision_id": "current-authorized-work-unit-redrive",
                "route_target": "write",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": work_unit_fingerprint,
                "controller_actions": ["run_quality_repair_batch"],
                "work_unit_targets": [
                    {
                        "target_kind": "claim",
                        "target_id": "claim_evidence_map",
                        "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
                    }
                ],
            },
        },
    )
    ensure_calls: list[dict[str, object]] = []
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
                    "continuation_policy": "auto",
                    "continuation_anchor": "decision",
                    "continuation_reason": "controller_work_unit_pending",
                    "pending_user_message_count": 0,
                    "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
                },
                "last_controller_decision_authorization": {
                    "decision_id": "current-authorized-work-unit-redrive",
                    "route_target": "write",
                    "work_unit_id": "analysis_claim_evidence_repair",
                    "work_unit_fingerprint": work_unit_fingerprint,
                    "controller_actions": ["run_quality_repair_batch"],
                },
                "interaction_arbitration": {
                    "classification": "controller_work_unit_pending_redrive",
                    "action": "resume",
                    "reason_code": "controller_work_unit_pending_redrive",
                    "requires_user_input": False,
                    "valid_blocking": False,
                    "kind": "controller_work_unit",
                    "work_unit_id": "analysis_claim_evidence_repair",
                    "work_unit_fingerprint": work_unit_fingerprint,
                },
                "publication_eval": publication_eval,
            },
            {
                "study_id": study_id,
                "current_stage": "publication_supervision",
                "paper_stage": "write",
                "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
                "supervision": {"active_run_id": None, "health_status": "escalated"},
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
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    apply_result = study["runtime_platform_repair_apply"]
    runtime_state = assert_owner_route_required(
        apply_result=apply_result,
        ensure_calls=ensure_calls,
        quest_root=quest_root,
        expected_reason=None,
    )
    assert apply_result["reason"] == "runtime_controller_redrive_required"
    assert apply_result["repair_kind"] == "controller_work_unit_pending_redrive"
    assert runtime_state["last_controller_decision_authorization"]["decision_id"] == (
        "current-authorized-work-unit-redrive"
    )
    assert study["external_supervisor_required"] is False
    assert study["action_queue"] == []
    assert study["blocked_reason"] == "runtime_controller_redrive_required"
    assert study["next_owner"] == "one-person-lab"
    assert study["paper_package_mutated"] is False
