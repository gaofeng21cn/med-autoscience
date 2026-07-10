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
    markdown = module.render_mainline_status_markdown(payload)
    assert payload["program_id"] in markdown
    assert payload["current_stage"]["id"] in markdown
