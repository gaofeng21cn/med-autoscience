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


def test_active_operator_projections_use_mainline_status_without_cockpit_alias() -> None:
    observability = importlib.import_module("med_autoscience.controllers.ai_first_observability")
    soak = importlib.import_module("med_autoscience.controllers.open_auto_research_soak")

    dashboard = observability.build_ai_first_operations_dashboard_summary(
        drift_audit={"status": "pass", "summary": {"fail_count": 0}},
        progress_snapshot={},
        runtime_snapshot={},
        quality_snapshot={},
        artifact_snapshot={},
    )
    projection = soak._entry_projection_results(
        {
            "status": "ready",
            "counts": {},
            "actions": [],
            "delivery_journal_usability_guard": {},
            "authority": {},
            "refs": {},
        }
    )

    assert dashboard["contract"]["shared_read_model_consumers"] == [
        "product_entry_status",
        "mainline_status",
        "study_progress",
    ]
    assert "workspace_cockpit" not in dashboard["contract"]["shared_read_model_consumers"]
    assert "mainline_status" in projection
    assert "workspace_cockpit" not in projection


def test_active_boundary_and_parity_read_models_omit_cockpit_alias() -> None:
    architecture = importlib.import_module("med_autoscience.controllers.architecture_owner_boundary")
    boundaries = importlib.import_module("med_autoscience.controllers.module_boundary_audit")
    parity = importlib.import_module("med_autoscience.controllers.mds_capability_parity.behavior_equivalence")

    architecture_report = architecture.build_architecture_owner_boundary_report()
    boundary_report = boundaries.build_module_boundary_audit_report()
    parity_matrix = parity.build_mds_behavior_equivalence_matrix()

    assert "workspace-cockpit" not in str(architecture_report)
    assert "workspace-cockpit" not in str(boundary_report)
    assert "workspace_cockpit" not in str(parity_matrix)
