from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_supervisor_scan_queues_runtime_repair_for_abnormal_stopped_resume_required(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-dm-cvd-mortality-risk", quest_id="quest-dm")
    quest_root = profile.runtime_root / "quest-dm"
    _write_json(
        study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json",
        {
            "surface": "autonomy_repair_orchestration",
            "schema_version": 1,
            "state": "ready_for_repair",
            "study_id": "001-dm-cvd-mortality-risk",
            "quest_id": "quest-dm",
            "actions": [{"action_type": "controller_repair", "repair_kind": "abnormal_stopped_resume_redrive"}],
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "study_root": str(study_root),
            "quest_id": "quest-dm",
            "quest_root": str(quest_root),
            "quest_status": "stopped",
            "decision": "resume",
            "reason": "quest_stopped_by_controller_guard",
            "runtime_liveness_audit": {
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "recover_runtime",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
            },
            "publication_eval": {
                "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
                "recommended_actions": [{"next_work_unit": {"unit_id": "gate_needs_specificity"}}],
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
            "quality_review_loop": {"closure_state": "review_required"},
            "ai_repair_lifecycle": {
                "state": "blocked",
                "blocked_reason": "ai_reviewer_assessment_required",
                "external_supervisor_required": True,
                "projection_only": True,
            },
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=("001-dm-cvd-mortality-risk",),
        apply_safe_actions=True,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == [
        "runtime_platform_repair",
        "publication_gate_specificity_required",
        "return_to_ai_reviewer_workflow",
    ]
    assert study["action_queue"][0]["reason"] == "abnormal_stopped_runtime_resume_required"
    assert study["why_not_applied"] == "abnormal_stopped_runtime_resume_required"
    assert study["blocked_reason"] == "abnormal_stopped_runtime_resume_required"
    assert study["next_owner"] == "external_supervisor"
    assert study["external_supervisor_required"] is True
    assert study["ai_repair_lifecycle"]["blocked_reason"] == "abnormal_stopped_runtime_resume_required"
    assert study["gate_specificity"]["required"] is True
    assert study["ai_reviewer_assessment"]["missing"] is True
    assert study["paper_package_mutated"] is False


def test_supervisor_scan_explicit_runtime_platform_repair_relaunches_abnormal_stopped_runtime(
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
            "status": "stopped",
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
            "decision": "resume",
            "runtime_liveness_audit": {
                "active_run_id": "run-dm-recovered",
                "runtime_audit": {"worker_running": True, "active_run_id": "run-dm-recovered"},
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
            "quest_status": "stopped",
            "decision": "resume",
            "reason": "quest_stopped_by_controller_guard",
            "runtime_liveness_audit": {
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "recover_runtime",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
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
    assert len(ensure_calls) == 1
    assert ensure_calls[0]["source"] == "runtime_supervisor_scan_platform_repair"
    assert study["runtime_platform_repair_apply"]["dispatch_status"] == "applied"
    assert study["runtime_platform_repair_apply"]["reason"] == "abnormal_stopped_runtime_relaunch_requested"
    assert study["runtime_platform_repair_apply"]["repair_kind"] == "abnormal_stopped_runtime_relaunch"
    assert study["runtime_platform_repair_apply"]["resume_result"]["runtime_liveness_audit"]["active_run_id"] == "run-dm-recovered"
    assert study["ai_repair_lifecycle"]["top_action"]["repair_kind"] == "abnormal_stopped_runtime_relaunch"
    assert study["paper_package_mutated"] is False


def test_supervisor_scan_explicit_runtime_platform_repair_relaunches_active_runtime_with_no_live_worker(
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
            "last_controller_decision_authorization": {"decision_id": "stale-specificity"},
        },
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "stale-specificity",
            "study_id": "001-dm-cvd-mortality-risk",
            "quest_id": "quest-dm",
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "request_gate_specificity"}],
            "route_target": "controller",
            "next_work_unit": {"unit_id": "gate_needs_specificity"},
        },
    )
    ensure_calls: list[dict[str, object]] = []

    def fake_ensure_study_runtime(**kwargs: object) -> dict[str, object]:
        ensure_calls.append(dict(kwargs))
        return {
            "study_id": "001-dm-cvd-mortality-risk",
            "quest_id": "quest-dm",
            "quest_status": "active",
            "decision": "resume",
            "runtime_liveness_audit": {
                "active_run_id": "run-dm-recovered",
                "runtime_audit": {"worker_running": True, "active_run_id": "run-dm-recovered"},
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
            "publication_eval": {
                "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
                "recommended_actions": [{"next_work_unit": {"unit_id": "gate_needs_specificity"}}],
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
            "quality_review_loop": {"closure_state": "review_required"},
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=("001-dm-cvd-mortality-risk",),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
    )

    study = result["studies"][0]
    assert len(ensure_calls) == 1
    assert ensure_calls[0]["source"] == "runtime_supervisor_scan_platform_repair"
    assert study["runtime_platform_repair_apply"]["dispatch_status"] == "applied"
    assert study["runtime_platform_repair_apply"]["reason"] == "abnormal_stopped_runtime_relaunch_requested"
    assert study["runtime_platform_repair_apply"]["repair_kind"] == "active_runtime_no_live_worker_relaunch"
    assert "controller_supersession" not in study["runtime_platform_repair_apply"]
    assert study["runtime_platform_repair_apply"]["resume_result"]["runtime_liveness_audit"]["active_run_id"] == "run-dm-recovered"
    assert study["ai_repair_lifecycle"]["state"] == "applied"
    assert study["paper_package_mutated"] is False


def test_supervisor_scan_blocks_runtime_platform_repair_when_relaunch_starts_no_live_run(
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
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "resume_postcondition": {
                "effective": False,
                "failure_mode": "no_live_run_started",
                "snapshot_status": "active",
                "active_run_id": None,
                "scheduled": True,
                "started": False,
                "queued": False,
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
    assert apply_result["reason"] == "runtime_relaunch_no_live_run_started"
    assert apply_result["repair_kind"] == "active_runtime_no_live_worker_relaunch"
    assert apply_result["resume_postcondition"]["failure_mode"] == "no_live_run_started"
    assert study["ai_repair_lifecycle"]["state"] == "blocked"
    assert study["ai_repair_lifecycle"]["blocked_reason"] == "runtime_relaunch_no_live_run_started"
    assert study["why_not_applied"] == "runtime_recovery_retry_budget_exhausted"
    assert study["paper_package_mutated"] is False


def test_supervisor_scan_queues_runtime_repair_for_paused_resume_without_live_worker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-dm-cvd-mortality-risk", quest_id="quest-dm")
    quest_root = profile.runtime_root / "quest-dm"
    publication_eval = {
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::return_to_controller::publication-blockers::dm002",
                "action_type": "return_to_controller",
                "work_unit_fingerprint": "publication-blockers::dm002",
                "specificity_targets": [
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
                        "target_kind": "table",
                        "target_id": "submission_minimal_authority",
                        "source_path": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
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
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "study_root": str(study_root),
            "quest_id": "quest-dm",
            "quest_root": str(quest_root),
            "quest_status": "paused",
            "decision": "resume",
            "reason": "quest_paused",
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
            "publication_eval": publication_eval,
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
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["runtime_platform_repair"]
    assert study["why_not_applied"] == "abnormal_stopped_runtime_resume_required"
    assert study["blocked_reason"] == "abnormal_stopped_runtime_resume_required"
    assert study["next_owner"] == "external_supervisor"
    assert study["external_supervisor_required"] is True
    assert study["gate_specificity"]["status"] == "not_required"
    assert study["ai_reviewer_assessment"]["present"] is True
    assert study["paper_package_mutated"] is False


def test_supervisor_scan_does_not_repair_paused_delivered_package_without_live_worker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-dm-cvd-mortality-risk", quest_id="quest-dm")
    quest_root = profile.runtime_root / "quest-dm"
    _write_json(
        study_root / "manuscript" / "delivery_manifest.json",
        {
            "schema_version": 1,
            "stage": "submission_minimal",
            "surface_roles": {
                "human_facing_current_package_root": str(study_root / "manuscript" / "current_package"),
                "human_facing_current_package_zip": str(study_root / "manuscript" / "current_package.zip"),
            },
        },
    )
    (study_root / "manuscript" / "current_package").mkdir(parents=True, exist_ok=True)
    (study_root / "manuscript" / "current_package" / "manuscript.docx").write_text("docx", encoding="utf-8")
    (study_root / "manuscript" / "current_package" / "paper.pdf").write_text("pdf", encoding="utf-8")
    (study_root / "manuscript" / "current_package.zip").write_text("zip", encoding="utf-8")
    status_payload = {
        "study_id": "001-dm-cvd-mortality-risk",
        "study_root": str(study_root),
        "quest_id": "quest-dm",
        "quest_root": str(quest_root),
        "quest_status": "paused",
        "decision": "blocked",
        "reason": "quest_waiting_for_submission_metadata",
        "active_run_id": None,
        "auto_runtime_parked": {
            "parked": True,
            "parked_state": "external_metadata_pending",
            "auto_execution_complete": True,
        },
        "runtime_liveness_audit": {
            "active_run_id": None,
            "runtime_audit": {"worker_running": False, "active_run_id": None},
        },
        "runtime_health_snapshot": {
            "canonical_runtime_action": "await_explicit_resume",
            "attempt_state": "parked",
            "blocking_reasons": ["quest_waiting_for_submission_metadata"],
        },
        "publication_eval": {
            "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
            "recommended_actions": [],
        },
    }
    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "current_stage": "auto_runtime_parked",
            "paper_stage": "bundle_stage_blocked",
            "auto_runtime_parked": status_payload["auto_runtime_parked"],
            "supervision": {"active_run_id": None, "health_status": "parked"},
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=("001-dm-cvd-mortality-risk",),
        apply_safe_actions=True,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == []
    assert study["why_not_applied"] is None
    assert study["blocked_reason"] is None
    assert study["next_owner"] is None
    assert study["external_supervisor_required"] is False
    assert study["paper_package_mutated"] is False


def test_supervisor_scan_runtime_repair_routes_controller_gate_skip_to_publication_gate(
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
                "blocked_reason": "gate_needs_specificity",
                "terminal_reason": "gate_needs_specificity",
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
    assert apply_result["reason"] == "publication_gate_specificity_required"
    assert apply_result["repair_kind"] == "active_runtime_no_live_worker_relaunch"
    assert apply_result["resume_postcondition"]["terminal_reason"] == "gate_needs_specificity"
    assert [item["action_type"] for item in study["action_queue"]] == ["publication_gate_specificity_required"]
    assert study["action_queue"][0]["owner"] == "publication_gate"
    assert study["ai_repair_lifecycle"]["state"] == "blocked"
    assert study["ai_repair_lifecycle"]["blocked_reason"] == "publication_gate_specificity_required"
    assert study["ai_repair_lifecycle"]["next_owner"] == "publication_gate"
    assert study["why_not_applied"] == "publication_gate_specificity_required"
    assert study["blocked_reason"] == "publication_gate_specificity_required"
    assert study["next_owner"] == "publication_gate"
    assert study["external_supervisor_required"] is False
    assert study["paper_package_mutated"] is False


def test_supervisor_scan_clears_stale_specificity_terminal_when_targets_are_complete(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-dm-cvd-mortality-risk", quest_id="quest-dm")
    quest_root = profile.runtime_root / "quest-dm"
    _write_json(
        quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json",
        {
            "schema_version": 1,
            "status": "blocked",
            "blockers": [
                "stale_submission_minimal_authority",
                "medical_publication_surface_blocked",
                "submission_hardening_incomplete",
            ],
            "current_required_action": "complete_bundle_stage",
            "supervisor_phase": "bundle_stage_blocked",
        },
    )
    publication_eval = {
        "schema_version": 1,
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::return_to_controller::publication-blockers::dm002",
                "action_type": "return_to_controller",
                "next_work_unit": {"unit_id": "gate_needs_specificity"},
                "specificity_targets": [
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
                        "target_kind": "table",
                        "target_id": "submission_minimal_authority",
                        "source_path": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
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
            "decision_id": "old-specificity",
            "study_id": "001-dm-cvd-mortality-risk",
            "quest_id": "quest-dm",
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "request_gate_specificity"}],
            "route_target": "controller",
            "next_work_unit": {"unit_id": "gate_needs_specificity"},
        },
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "active",
            "quest_id": "quest-dm",
            "active_run_id": None,
            "worker_running": False,
            "pending_user_message_count": 0,
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "needs_specificity",
            "same_fingerprint_auto_turn_count": 11,
            "retry_state": {"terminal": True, "gate_needs_specificity": True},
            "last_controller_decision_authorization": {
                "decision_id": "old-specificity",
                "route_target": "controller",
                "work_unit_id": "gate_needs_specificity",
                "work_unit_fingerprint": "publication-blockers::old",
                "controller_work_unit_lifecycle": {
                    "lifecycle_state": "needs_specificity",
                    "latest_event_type": "needs_specificity",
                    "delivery_blocked": True,
                    "block_reason": "needs_specificity",
                    "terminal_consumed": True,
                },
            },
        },
    )
    ensure_calls: list[dict[str, object]] = []

    def fake_ensure_study_runtime(**kwargs: object) -> dict[str, object]:
        ensure_calls.append(dict(kwargs))
        return {
            "study_id": "001-dm-cvd-mortality-risk",
            "quest_id": "quest-dm",
            "quest_status": "active",
            "decision": "resume",
            "runtime_liveness_audit": {
                "active_run_id": "run-dm-recovered",
                "runtime_audit": {"worker_running": True, "active_run_id": "run-dm-recovered"},
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
            "resume_postcondition": {
                "effective": False,
                "blocked_reason": "needs_specificity",
                "terminal_reason": "needs_specificity",
                "terminal_source": "controller_work_unit_authorization",
            },
            "publication_eval": publication_eval,
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "current_stage": "managed_runtime_escalated",
            "paper_stage": "bundle_stage_blocked",
            "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            "supervision": {"active_run_id": None, "health_status": "recovering"},
            "quality_review_loop": {"closure_state": "review_required"},
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=("001-dm-cvd-mortality-risk",),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
    )

    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    study = result["studies"][0]
    assert len(ensure_calls) == 1
    assert "last_controller_decision_authorization" not in runtime_state
    assert "retry_state" not in runtime_state
    assert runtime_state["same_fingerprint_auto_turn_count"] == 0
    assert runtime_state["continuation_reason"] == "runtime_platform_repair_redrive"
    assert study["gate_specificity"]["status"] == "specific_targets_present"
    assert [item["action_type"] for item in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    assert study["runtime_platform_repair_apply"]["dispatch_status"] == "applied"
    assert study["runtime_platform_repair_apply"]["reason"] == "stale_specificity_terminal_targets_resolved"
    assert study["runtime_platform_repair_apply"]["stale_specificity_cleared"] is True
    assert study["runtime_platform_repair_apply"]["resume_result"]["runtime_liveness_audit"]["active_run_id"] == "run-dm-recovered"
    assert study["why_not_applied"] == "ai_reviewer_assessment_required"
    assert study["blocked_reason"] == "ai_reviewer_assessment_required"
    assert study["next_owner"] == "ai_reviewer"
    assert study["external_supervisor_required"] is False
    assert study["paper_package_mutated"] is False


def test_supervisor_scan_prefers_current_ai_reviewer_publication_eval_over_stale_status_projection(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-dm-cvd-mortality-risk", quest_id="quest-dm")
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "policy_id": "medical_publication_critique_v1",
                "ai_reviewer_required": False,
            },
            "recommended_actions": [
                {
                    "action_type": "return_to_finalize",
                    "next_work_unit": {"unit_id": "submission_minimal_refresh"},
                }
            ],
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "study_root": str(study_root),
            "quest_id": "quest-dm",
            "quest_root": str(profile.runtime_root / "quest-dm"),
            "quest_status": "active",
            "runtime_liveness_audit": {
                "active_run_id": "run-live",
                "runtime_audit": {"worker_running": True, "active_run_id": "run-live"},
            },
            "publication_eval": {
                "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
                "recommended_actions": [{"next_work_unit": {"unit_id": "gate_needs_specificity"}}],
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "paper_stage": "bundle_stage_blocked",
            "refs": {"publication_eval_path": str(publication_eval_path)},
            "supervision": {"active_run_id": "run-live", "health_status": "live"},
            "quality_review_loop": {"closure_state": "review_required"},
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=("001-dm-cvd-mortality-risk",),
        apply_safe_actions=True,
    )

    study = result["studies"][0]
    assert study["ai_reviewer_assessment"]["present"] is True
    assert study["ai_reviewer_assessment"]["missing"] is False
    assert [item["action_type"] for item in study["action_queue"]] == []
