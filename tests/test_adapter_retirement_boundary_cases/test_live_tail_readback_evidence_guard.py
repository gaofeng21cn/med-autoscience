from __future__ import annotations

import importlib

import pytest


TAIL_CASES = (
    (
        "opl_default_executor_carrier_tail_readback",
        "no_active_default_executor_carrier_caller_proven",
        "default_executor_no_active_scan_as_live_tail_readback",
    ),
    (
        "opl_obligation_actuator_tail_readback",
        "no_active_mas_obligation_actuator_caller_proven",
        "obligation_no_active_scan_as_live_tail_readback",
    ),
    (
        "opl_runtime_health_observability_tail_readback",
        "no_active_diagnostic_projection_caller_proven",
        "runtime_health_no_active_scan_as_live_tail_readback",
    ),
    (
        "opl_materializer_projection_tail_readback",
        "no_active_materializer_projection_caller_proven",
        "materializer_no_active_scan_as_live_tail_readback",
    ),
    (
        "opl_workbench_shell_readback_tail",
        "no_active_workbench_projection_action_caller_proven",
        "workbench_no_active_scan_as_live_tail_readback",
    ),
    (
        "opl_runtime_lifecycle_maintenance_tail_readback",
        "no_active_lifecycle_maintenance_adapter_caller_proven",
        "lifecycle_no_active_scan_as_live_tail_readback",
    ),
    (
        "opl_runtime_storage_maintenance_tail_readback",
        "no_active_storage_maintenance_adapter_caller_proven",
        "storage_no_active_scan_as_live_tail_readback",
    ),
)


def _layers_for_tail(
    tail_key: str,
    no_active_key: str,
    forbidden_claim: str,
    *,
    tail_readback_proven: bool,
    no_active_caller_proven: bool,
) -> dict:
    layers_module = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement_parts.completion_evidence_layers"
    )
    surface_id = f"future_{tail_key}"
    surface = {
        "surface_id": surface_id,
        "current_disposition": "refs_only_tail_open",
        "generic_runtime_owner": "one-person-lab",
        "retirement_gate": {
            "completion_claim_requires_live_owner_or_opl_readback": True,
        },
        tail_key: {
            "surface_kind": f"{tail_key}_requirement",
            "status": "tail_open",
            "runtime_owner": "one-person-lab",
            "required_before_physical_delete": f"{surface_id}_tail_readback_ref",
            "physical_delete_requires": [
                "opl_live_readback",
                no_active_key.replace("_proven", "_scan"),
            ],
            "tail_readback_proven": tail_readback_proven,
            no_active_key: no_active_caller_proven,
            "physical_delete_allowed": False,
            "forbidden_completion_claims": [forbidden_claim],
        },
    }
    audit = {
        "surface_id": surface_id,
        "authority_status": "refs_only_tail_open",
        "physical_delete_gate_open": True,
    }

    return layers_module.completion_evidence_layers(
        [surface],
        surface_audits=[audit],
        violations=[],
    )


@pytest.mark.parametrize(
    ("tail_key", "no_active_key", "forbidden_claim"),
    TAIL_CASES,
)
def test_no_active_tail_scan_does_not_satisfy_live_readback_evidence(
    tail_key: str,
    no_active_key: str,
    forbidden_claim: str,
) -> None:
    layers = _layers_for_tail(
        tail_key,
        no_active_key,
        forbidden_claim,
        tail_readback_proven=False,
        no_active_caller_proven=True,
    )
    surface_id = f"future_{tail_key}"
    tails = {
        item["surface_id"]: item
        for item in layers["live_soak_or_no_active_caller"]["open_surface_tails"]
    }

    assert layers["live_soak_or_no_active_caller"]["status"] == "evidence_required"
    assert layers["live_soak_or_no_active_caller"]["proven"] is False
    assert tails[surface_id]["live_or_no_active_proven"] is False
    assert forbidden_claim in tails[surface_id]["forbidden_completion_interpretations"]


@pytest.mark.parametrize(
    ("tail_key", "no_active_key", "forbidden_claim"),
    TAIL_CASES,
)
def test_tail_readback_proof_satisfies_live_readback_evidence(
    tail_key: str,
    no_active_key: str,
    forbidden_claim: str,
) -> None:
    layers = _layers_for_tail(
        tail_key,
        no_active_key,
        forbidden_claim,
        tail_readback_proven=True,
        no_active_caller_proven=False,
    )

    assert layers["live_soak_or_no_active_caller"]["status"] == (
        "satisfied_with_live_evidence"
    )
    assert layers["live_soak_or_no_active_caller"]["proven"] is True
