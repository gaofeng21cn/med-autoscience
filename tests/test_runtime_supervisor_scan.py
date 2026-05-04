from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_supervisor_scan_queues_external_repair_for_retry_exhausted_no_live_worker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "003-dpcc-primary-care-phenotype-treatment-gap", quest_id="quest-dpcc")
    quest_root = profile.runtime_root / "quest-dpcc"

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "study_root": str(study_root),
            "quest_id": "quest-dpcc",
            "quest_root": str(quest_root),
            "quest_status": "running",
            "decision": "blocked",
            "reason": "runtime_recovery_retry_budget_exhausted",
            "runtime_liveness_status": "not_live",
            "runtime_liveness_audit": {
                "status": "not_live",
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
            "control_plane_snapshot": {
                "control_state": "blocked_runtime_escalation",
                "canonical_runtime_action": "external_supervisor_required",
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "paper_stage": "publication_supervision",
            "supervision": {"active_run_id": None, "health_status": "recovering"},
            "ai_repair_lifecycle": {
                "state": "external_supervisor_required",
                "blocked_reason": "runtime_recovery_not_authorized",
                "external_supervisor_required": True,
            },
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=("003-dpcc-primary-care-phenotype-treatment-gap",),
        apply_safe_actions=True,
    )

    study = result["studies"][0]
    assert study["external_supervisor_required"] is True
    assert study["action_queue"][0]["action_type"] == "runtime_platform_repair"
    assert study["action_queue"][0]["authority"] == "external_supervisor"
    assert study["why_not_applied"] == "runtime_recovery_retry_budget_exhausted"
    assert study["escalation_reason"] == "runtime_recovery_retry_budget_exhausted"
    assert study["gate_specificity"]["required"] is False
    assert study["ai_reviewer_assessment"]["missing"] is False
    assert Path(result["refs"]["latest_path"]).is_file()


def test_supervisor_scan_queues_specificity_and_ai_reviewer_actions_without_quality_authority(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-dm-cvd-mortality-risk", quest_id="quest-dm")
    quest_root = profile.runtime_root / "quest-dm"

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "study_root": str(study_root),
            "quest_id": "quest-dm",
            "quest_root": str(quest_root),
            "quest_status": "stopped",
            "decision": "blocked",
            "reason": "publication_gate_specificity_required",
            "execution_owner_guard": {"supervisor_only": True},
            "publication_eval": {
                "current_required_action": "generic_blocker_repair",
                "assessment_provenance": {"owner": "mechanical_gate"},
                "blockers": ["generic blocker"],
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "current_stage": "publication_supervision",
            "paper_stage": "publishability_gate_blocked",
            "current_blockers": ["generic blocker"],
            "quality_review_loop": {"closure_state": "open"},
            "control_plane_snapshot": {"blocking_reasons": ["publication_eval.ai_reviewer_required"]},
            "ai_repair_lifecycle": {
                "state": "blocked",
                "blocked_reason": "publication_gate_specificity_required",
                "external_supervisor_required": True,
            },
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=("001-dm-cvd-mortality-risk",),
        apply_safe_actions=True,
    )

    action_types = [item["action_type"] for item in result["studies"][0]["action_queue"]]
    assert action_types == ["publication_gate_specificity_required", "return_to_ai_reviewer_workflow"]
    assert {item["authority"] for item in result["studies"][0]["action_queue"]} == {"observability_only"}
    assert result["studies"][0]["current_stage"] == "publication_supervision"
    assert result["studies"][0]["gate_specificity"]["required"] is True
    assert result["studies"][0]["ai_reviewer_assessment"] == {
        "present": False,
        "owner": "mechanical_gate",
        "required": True,
        "missing": True,
    }
    assert result["studies"][0]["supervisor_only"] is True
    assert result["studies"][0]["paper_package_mutated"] is False
