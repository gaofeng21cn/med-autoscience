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
    assert "Remaining Gaps" in markdown
    assert "Next Focus" in markdown
