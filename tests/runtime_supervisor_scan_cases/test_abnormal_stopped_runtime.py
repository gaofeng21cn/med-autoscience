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

