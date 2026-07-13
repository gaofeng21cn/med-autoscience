from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, cast

import pytest


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


def test_active_direction_prompt_omits_cockpit_alias() -> None:
    prompt = (
        Path(__file__).resolve().parents[1] / "agent/prompts/direction_and_route_selection.md"
    ).read_text(encoding="utf-8")

    assert "workspace_cockpit" not in prompt


def test_active_contracts_use_mainline_status_not_cockpit_alias() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    schema = json.loads(
        (repo_root / "contracts/schemas/v1/product-entry-manifest.schema.json").read_text(
            encoding="utf-8"
        )
    )
    adoption = json.loads(
        (repo_root / "contracts/opl-framework/family-contract-adoption.json").read_text(
            encoding="utf-8"
        )
    )
    acceptance = json.loads(
        (repo_root / "contracts/production_acceptance/mas-production-acceptance.json").read_text(
            encoding="utf-8"
        )
    )

    commands = schema["$defs"]["domainEntryContract"]["properties"]["supported_commands"]["items"]["enum"]
    assert "mainline-status" in commands
    assert "workspace-cockpit" not in commands

    operator_surfaces = adoption["operator_projection"]["source_surfaces"]
    assert "mainline-status" in operator_surfaces
    assert "workspace-cockpit" not in operator_surfaces

    source_guard = next(
        lane
        for lane in acceptance["codex_first_landing_program"]["lanes"]
        if lane["lane_id"] == "standard_agent_source_morphology_guard"
    )
    assert "controllers/mainline_status" in source_guard["primary_surfaces"]
    assert "product_entry/workspace_cockpit" not in source_guard["primary_surfaces"]


def test_public_dispatch_rejects_cockpit_alias_and_keeps_mainline_status() -> None:
    domain_entry = importlib.import_module("med_autoscience.domain_entry")
    entry = domain_entry.MedAutoScienceDomainEntry()

    with pytest.raises(ValueError, match="不支持的 domain entry command"):
        entry.dispatch({"command": "workspace-cockpit"})

    payload = entry.dispatch({"command": "mainline-status"})
    assert payload["command"] == "mainline-status"
