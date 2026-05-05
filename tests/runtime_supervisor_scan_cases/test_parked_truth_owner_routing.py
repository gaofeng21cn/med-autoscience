from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study


def test_auto_runtime_parked_truth_suppresses_stale_external_supervisor_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-dm-cvd-mortality-risk", quest_id="quest-dm001")
    status_payload = _parked_status(
        study_root=study_root,
        quest_id="quest-dm001",
        parked_state="external_metadata_pending",
        reason="quest_waiting_for_submission_metadata",
    )
    progress_payload = {
        "study_id": "001-dm-cvd-mortality-risk",
        "quest_id": "quest-dm001",
        "current_stage": "auto_runtime_parked",
        "paper_stage": "bundle_stage_blocked",
        "auto_runtime_parked": status_payload["auto_runtime_parked"],
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "ai_repair_lifecycle": {
            "state": "blocked",
            "blocked_reason": "abnormal_stopped_runtime_resume_required",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
        },
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            status_payload,
            progress_payload,
            "quest-dm001",
            _ai_reviewer_eval(required=False),
        ),
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=["001-dm-cvd-mortality-risk"],
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["action_queue"] == []
    assert study["why_not_applied"] is None
    assert study["blocked_reason"] is None
    assert study["next_owner"] is None
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["current_owner"] == "controller_stop"
    assert study["owner_route"]["allowed_actions"] == []


@pytest.mark.parametrize(
    ("study_id", "parked_state", "reason", "paper_stage"),
    [
        (
            "004-dpcc-longitudinal-care-inertia-intensification-gap",
            "manual_hold",
            "quest_waiting_for_explicit_wakeup_after_manual_hold",
            "manual_hold",
        ),
        ("001-lineage-pfs", "publishability_stop_loss", "publishability_stop_loss_recommended", "stop_loss"),
    ],
)
def test_terminal_parked_truth_does_not_reopen_ai_reviewer_queue(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    study_id: str,
    parked_state: str,
    reason: str,
    paper_stage: str,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    status_payload = _parked_status(
        study_root=study_root,
        quest_id=f"quest-{study_id}",
        parked_state=parked_state,
        reason=reason,
    )
    progress_payload = {
        "study_id": study_id,
        "quest_id": f"quest-{study_id}",
        "current_stage": "auto_runtime_parked",
        "paper_stage": paper_stage,
        "auto_runtime_parked": status_payload["auto_runtime_parked"],
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "quality_review_loop": {"closure_state": "review_required"},
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            status_payload,
            progress_payload,
            f"quest-{study_id}",
            _ai_reviewer_eval(required=True),
        ),
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["action_queue"] == []
    assert study["why_not_applied"] is None
    assert study["blocked_reason"] is None
    assert study["next_owner"] is None
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["current_owner"] == "controller_stop"
    assert study["owner_route"]["next_owner"] is None


def _parked_status(*, study_root: Path, quest_id: str, parked_state: str, reason: str) -> dict:
    return {
        "study_id": study_root.name,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_status": "paused",
        "decision": "blocked",
        "reason": reason,
        "active_run_id": None,
        "auto_runtime_parked": {
            "parked": True,
            "parked_state": parked_state,
            "awaiting_explicit_wakeup": True,
            "auto_execution_complete": parked_state == "external_metadata_pending",
        },
        "runtime_liveness_audit": {
            "active_run_id": None,
            "runtime_audit": {"worker_running": False, "active_run_id": None},
        },
        "runtime_health_snapshot": {
            "canonical_runtime_action": "await_explicit_resume",
            "attempt_state": "parked",
            "blocking_reasons": [reason],
        },
    }


def _ai_reviewer_eval(*, required: bool) -> dict:
    return {
        "assessment_provenance": {
            "owner": "mechanical_projection" if required else "ai_reviewer",
            "ai_reviewer_required": required,
        },
        "recommended_actions": [],
    }
