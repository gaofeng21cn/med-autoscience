from __future__ import annotations

import importlib


def test_mainline_status_projects_ideal_state_current_stage_and_gaps() -> None:
    module = importlib.import_module("med_autoscience.controllers.mainline_status")

    payload = module.read_mainline_status()

    assert payload["program_id"] == "research-foundry-medical-mainline"
    assert payload["current_stage"]["id"] == "f4_blocker_closeout"
    assert payload["current_stage"]["status"] == "in_progress"
    assert payload["ideal_state"]["runtime_topology"]["outer_runtime_substrate_owner"] == "upstream Hermes-Agent"
    assert payload["ideal_state"]["runtime_topology"]["research_backend"] == "MedDeepScientist (controlled backend)"
    assert payload["current_program_phase"]["id"] == "phase_1_mainline_established"
    assert payload["current_program_phase"]["status"] == "in_progress"
    assert len(payload["phase_ladder"]) == 5
    assert payload["phase_ladder"][1]["id"] == "phase_2_user_product_loop"
    assert payload["phase_ladder"][0]["usable_now"] is True
    assert payload["phase3_clearance_lane"]["surface_kind"] == "phase3_host_clearance_lane"
    assert payload["phase3_clearance_lane"]["clearance_targets"][0]["target_id"] == "external_runtime_contract"
    assert payload["phase3_clearance_lane"]["proof_surfaces"] == [
        "doctor.external_runtime_contract",
        "study_runtime_status.autonomous_runtime_notice",
        "runtime_watch/latest.json",
        "runtime_supervision/latest.json",
        "controller_decisions/latest.json",
    ]
    assert payload["phase4_backend_deconstruction"]["surface_kind"] == "phase4_backend_deconstruction_lane"
    assert payload["phase4_backend_deconstruction"]["substrate_targets"][0]["capability_id"] == "session_run_watch_recovery"
    assert payload["phase4_backend_deconstruction"]["deconstruction_map_doc"] == (
        "docs/program/med_deepscientist_deconstruction_map.md"
    )
    assert payload["platform_target"]["surface_kind"] == "phase5_platform_target"
    assert payload["platform_target"]["north_star_topology"]["monorepo_status"] == "post_gate_target"
    assert payload["platform_target"]["promotion_gates"] == [
        "phase_1_mainline_established",
        "phase_2_user_product_loop",
        "phase_3_multi_workspace_host_clearance",
        "phase_4_backend_deconstruction",
    ]
    assert any(item["name"] == "workspace_cockpit" for item in payload["phase_ladder"][1]["entry_points"])
    assert any(item["id"] == "f3_real_study_soak_recovery_proof" for item in payload["completed_tranches"])
    assert any("standalone" in item for item in payload["remaining_gaps"])
    assert any("physical migration" in item for item in payload["explicitly_not_now"])


def test_render_mainline_status_markdown_surfaces_stage_and_next_focus() -> None:
    module = importlib.import_module("med_autoscience.controllers.mainline_status")

    markdown = module.render_mainline_status_markdown(module.read_mainline_status())

    assert "# Mainline Status" in markdown
    assert "f4_blocker_closeout" in markdown
    assert "Ideal State" in markdown
    assert "Program Phases" in markdown
    assert "phase_1_mainline_established" in markdown
    assert "Platform Target" in markdown
    assert "Phase 3 Clearance" in markdown
    assert "Phase 4 Deconstruction" in markdown
    assert "Remaining Gaps" in markdown
    assert "Next Focus" in markdown


def test_mainline_phase_status_resolves_current_and_next_phase() -> None:
    module = importlib.import_module("med_autoscience.controllers.mainline_status")

    current_payload = module.read_mainline_phase_status("current")
    next_payload = module.read_mainline_phase_status("next")

    assert current_payload["phase"]["id"] == "phase_1_mainline_established"
    assert current_payload["phase"]["usable_now"] is True
    assert any(item["name"] == "mainline_status" for item in current_payload["phase"]["entry_points"])
    assert next_payload["phase"]["id"] == "phase_2_user_product_loop"
    assert any("workspace-cockpit" in item["command"] for item in next_payload["phase"]["entry_points"])


def test_render_mainline_phase_markdown_surfaces_entry_points_and_exit_criteria() -> None:
    module = importlib.import_module("med_autoscience.controllers.mainline_status")

    markdown = module.render_mainline_phase_markdown(module.read_mainline_phase_status("phase_2_user_product_loop"))

    assert "# Mainline Phase" in markdown
    assert "phase_2_user_product_loop" in markdown
    assert "Entry Points" in markdown
    assert "Exit Criteria" in markdown
