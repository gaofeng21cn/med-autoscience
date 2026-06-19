from __future__ import annotations

import importlib


def test_blocked_surface_prevents_physical_retirement_allowed_status() -> None:
    layers_module = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.completion_evidence_layers"
    )
    surface = {
        "surface_id": "future_specialized_tail_surface",
        "current_disposition": "refs_only_tail_open",
        "generic_runtime_owner": "one-person-lab",
        "retirement_gate": {
            "completion_claim_requires_live_owner_or_opl_readback": True,
            "physical_delete_requires": ["live_readback_ref"],
        },
    }
    audit = {
        "surface_id": "future_specialized_tail_surface",
        "authority_status": "specialized_tail_open",
        "physical_delete_gate_open": False,
        "agent_tool_arsenal_physical_delete_allowed": False,
    }

    layers = layers_module.completion_evidence_layers(
        [surface],
        surface_audits=[audit],
        violations=[],
    )

    assert layers["physical_retirement"]["blocked_surface_ids"] == [
        "future_specialized_tail_surface"
    ]
    assert layers["physical_retirement"]["status"] == "evidence_required"
    assert layers["physical_retirement"]["allowed"] is False
