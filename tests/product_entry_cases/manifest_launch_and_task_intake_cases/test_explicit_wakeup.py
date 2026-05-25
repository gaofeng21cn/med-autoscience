from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study

pytestmark = pytest.mark.contract


def test_launch_study_explicit_wakeup_records_truth_resume(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    launch_surface = importlib.import_module(
        "med_autoscience.controllers.product_entry_parts.workspace_cockpit.launch_surface"
    )
    truth_kernel = importlib.import_module("med_autoscience.controllers.study_truth_kernel")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    study_root = write_study(profile.workspace_root, "001-risk")

    monkeypatch.setattr(
        launch_surface.domain_status_projection,
        "progress_projection",
        lambda **kwargs: {
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_status": "active",
            "decision": "blocked",
            "reason": "quest_waiting_for_submission_metadata",
            "continuation_state": {
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            },
            "auto_runtime_parked": {"awaiting_explicit_wakeup": True},
        },
    )
    monkeypatch.setattr(
        launch_surface.study_progress,
        "build_study_progress_projection",
        lambda **kwargs: {"study_id": "001-risk", "current_stage": "auto_runtime_parked"},
    )

    payload = module.launch_study(
        profile=profile,
        profile_ref=profile_ref,
        study_id="001-risk",
        explicit_user_wakeup=True,
    )

    events = truth_kernel.read_truth_events(study_root=study_root)
    assert [event["event_type"] for event in events] == ["explicit_resume"]
    assert events[0]["payload"]["current_required_action"] == "resume_same_study_line"
    assert events[0]["payload"]["resume_owner"] == "one-person-lab"
    assert payload["runtime_status"]["product_entry_launch_policy"]["explicit_user_wakeup_recorded"] is True
    assert payload["runtime_status"]["study_truth_snapshot"]["canonical_next_action"] == "resume_same_study_line"
    assert payload["runtime_status"]["study_truth_snapshot"]["dominant_authority_refs"][0]["event_type"] == "explicit_resume"
