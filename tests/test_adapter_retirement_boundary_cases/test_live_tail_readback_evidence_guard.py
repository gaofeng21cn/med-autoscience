from __future__ import annotations

import importlib


def test_no_active_tail_scan_does_not_satisfy_live_readback_evidence() -> None:
    layers_module = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.completion_evidence_layers"
    )
    surface = {
        "surface_id": "future_opl_tail_projection",
        "current_disposition": "refs_only_tail_open",
        "generic_runtime_owner": "one-person-lab",
        "retirement_gate": {
            "completion_claim_requires_live_owner_or_opl_readback": True,
            "opl_workbench_shell_readback_required": True,
        },
        "opl_workbench_shell_readback_tail": {
            "surface_kind": "opl_workbench_shell_readback_requirement",
            "status": "tail_open",
            "runtime_owner": "one-person-lab",
            "required_before_physical_delete": (
                "future_opl_tail_projection_workbench_shell_readback_ref"
            ),
            "physical_delete_requires": [
                "opl_workbench_shell_action_transport_readback",
                "no_active_workbench_projection_action_caller_scan",
            ],
            "tail_readback_proven": False,
            "no_active_workbench_projection_action_caller_proven": True,
            "physical_delete_allowed": False,
            "forbidden_completion_claims": [
                "workbench_no_active_scan_as_live_tail_readback",
            ],
        },
    }
    audit = {
        "surface_id": "future_opl_tail_projection",
        "authority_status": "refs_only_tail_open",
        "physical_delete_gate_open": True,
    }

    layers = layers_module.completion_evidence_layers(
        [surface],
        surface_audits=[audit],
        violations=[],
    )
    tails = {
        item["surface_id"]: item
        for item in layers["live_soak_or_no_active_caller"]["open_surface_tails"]
    }

    assert layers["live_soak_or_no_active_caller"]["status"] == "evidence_required"
    assert layers["live_soak_or_no_active_caller"]["proven"] is False
    assert tails["future_opl_tail_projection"]["live_or_no_active_proven"] is False
    assert (
        "workbench_no_active_scan_as_live_tail_readback"
        in tails["future_opl_tail_projection"]["forbidden_completion_interpretations"]
    )
