from __future__ import annotations

import importlib
from typing import Any, cast


def test_mainline_status_omits_workspace_cockpit_compatibility() -> None:
    module = importlib.import_module("med_autoscience.controllers.mainline_status")

    payload = module.read_mainline_status()

    assert "workspace_cockpit" not in payload["commands"]
    assert all(
        entry_point["name"] != "workspace_cockpit"
        for phase in payload["phase_ladder"]
        for entry_point in phase["entry_points"]
    )
    assert all(
        step["surface_kind"] != "workspace_cockpit"
        for step in payload["phase2_user_product_loop"]["single_path"]
    )
    assert "cockpit" not in payload["single_project_boundary"]["summary"]
    assert "cockpit" not in next(
        step["title"]
        for step in payload["phase2_user_product_loop"]["single_path"]
        if step["step_id"] == "handle_human_gate"
    )


def test_study_recovery_omits_workspace_cockpit_compatibility() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.operator_view")
    profile = cast(Any, None)

    commands = module._study_command_surfaces(
        profile=profile,
        study_id="study-1",
        profile_ref=None,
    )

    assert "workspace_cockpit" not in commands
    for lane_id in (
        "user_decision_gate",
        "auto_runtime_parked",
        "manual_finishing",
        "quality_floor_blocker",
    ):
        _, steps, _ = module._recovery_contract(
            profile=profile,
            study_id="study-1",
            profile_ref=None,
            intervention_lane={"lane_id": lane_id},
            current_stage_summary="current",
            next_system_action="next",
            current_blockers=[],
        )
        assert all(step["surface_kind"] != "workspace_cockpit" for step in steps)
