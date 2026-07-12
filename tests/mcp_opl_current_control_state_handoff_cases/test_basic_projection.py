from __future__ import annotations

import importlib

from tests.mcp_opl_current_control_state_handoff_cases.shared import (
    make_profile,
    write_json,
)


def test_stage_attempt_context_projection_is_observability_only(tmp_path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.opl_current_control_state_handoff"
    )
    profile = make_profile(tmp_path)
    handoff_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    write_json(
        handoff_path,
        {
            "studies": [
                {
                    "study_id": "001-risk",
                    "active_run_id": "run-001",
                    "active_stage_attempt_id": "attempt-001",
                    "running_provider_attempt": True,
                    "artifact_refs": ["artifact://negative-result"],
                }
            ]
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(
        profile=profile,
        study_id="001-risk",
    )

    assert projection["surface_kind"] == "opl_stage_attempt_context_handoff"
    assert projection["authority"] == "observability_only"
    assert projection["progress_first"]["next_stage_may_start"] is True
    assert projection["progress_first"]["missing_transport_readback_blocks_stage_transition"] is False
    assert "provider_admission_candidates" not in projection


def test_missing_stage_attempt_context_does_not_materialize_a_blocker(tmp_path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.opl_current_control_state_handoff"
    )
    profile = make_profile(tmp_path)

    assert module.opl_current_control_state_study_handoff_projection(
        profile=profile,
        study_id="missing",
    ) is None
