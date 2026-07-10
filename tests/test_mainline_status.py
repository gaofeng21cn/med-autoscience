from __future__ import annotations

import importlib


def test_mainline_status_projects_current_owner_and_no_authority_boundaries() -> None:
    module = importlib.import_module("med_autoscience.controllers.mainline_status")

    payload = module.read_mainline_status()

    assert payload["program_id"] == "research-foundry-medical-mainline"
    assert payload["current_stage"]["id"] == "mas_owner_truth_hardening"
    assert payload["current_stage"]["status"] == "in_progress"
    assert payload["ideal_state"]["runtime_topology"]["runtime_owner"] == "one-person-lab"
    assert payload["capability_owner_boundary"]["owner"] == "MedAutoScience"
    assert [lane["lane_id"] for lane in payload["active_tranche_owner_truth"]["lanes"]] == [
        "autonomy",
        "quality",
        "single_project_owner",
    ]
    assert payload["unified_enhancement_program"]["projection_only"] is True
    command_sources = [
        *payload["phase2_user_product_loop"]["single_path"],
        *payload["phase2_user_product_loop"]["operator_questions"],
        *[
            item
            for item in payload["phase2_user_product_loop"]["proof_surfaces"]
            if "command_ref" in item
        ],
    ]
    assert command_sources
    assert all(
        item["command_ref"]["authority"] is False
        and item["command_ref"]["can_generate_action"] is False
        and item["command_ref"]["can_execute"] is False
        for item in command_sources
    )
    markdown = module.render_mainline_status_markdown(payload)
    assert payload["program_id"] in markdown
    assert payload["current_stage"]["id"] in markdown


def test_mainline_phase_status_resolves_current_and_next_phase() -> None:
    module = importlib.import_module("med_autoscience.controllers.mainline_status")

    current = module.read_mainline_phase_status("current")
    next_phase = module.read_mainline_phase_status("next")

    assert current["phase"]["id"] == "phase_1_mainline_established"
    assert current["phase"]["usable_now"] is True
    assert current["phase"]["capability_owner_boundary"]["owner"] == "MedAutoScience"
    assert next_phase["phase"]["id"] == "phase_2_user_product_loop"
    assert any("workspace cockpit" in item["command"] for item in next_phase["phase"]["entry_points"])
    markdown = module.render_mainline_phase_markdown(next_phase)
    assert next_phase["program_id"] in markdown
    assert next_phase["phase"]["id"] in markdown
