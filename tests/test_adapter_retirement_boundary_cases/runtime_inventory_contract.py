from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = (
    REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
)

REQUIRED_SURFACES = {
    "runtime_transport_core_bridge",
    "runtime_turn_runner_closeout_adapter",
    "worker_lease_residency_projection",
    "domain_authority_refs_index",
    "owner_callable_dispatch_request",
    "domain_action_request_materializer_local_carrier_persistence_api",
    "owner_callable_adapter_legacy_dispatch_projection_alias",
    "domain_action_request_materializer_current_owner_callable_adapters_api",
    "domain_action_request_materializer_owner_callable_adapter_projection",
    "owner_callable_adapter_receipt_latest_wire_projection",
    "stage_outcome_authority",
    "domain_diagnostic_obligation_actuator",
    "runtime_health_kernel",
    "progress_portal_study_workbench_overview_action_projection",
    "agent_tool_arsenal_scientific_capability_registry",
    "runtime_lifecycle_payload_retention",
    "runtime_storage_maintenance",
}

RETIRED_REPO_SOURCE_SURFACES = {
    "domain_authority_refs_index",
    "owner_callable_dispatch_request",
    "owner_callable_adapter_receipt_latest_wire_projection",
    "domain_action_request_materializer_owner_callable_adapter_projection",
}

LIVE_TAIL_SURFACES = {
    "stage_outcome_authority",
    "domain_diagnostic_obligation_actuator",
    "runtime_health_kernel",
    "progress_portal_study_workbench_overview_action_projection",
    "agent_tool_arsenal_scientific_capability_registry",
    "runtime_lifecycle_payload_retention",
    "runtime_storage_maintenance",
}


def _inventory_surfaces() -> dict[str, dict]:
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    assert inventory["surface_kind"] == "mas_runtime_surface_retirement_inventory"
    assert inventory["version"] == "mas-runtime-surface-retirement-inventory.v1"
    assert inventory["authority_boundary"]["opl_owns"] == [
        "queue",
        "attempt",
        "retry",
        "dead_letter",
        "provider_liveness",
        "generic_stage_state",
    ]
    assert inventory["authority_boundary"]["mas_owns"] == [
        "domain_truth",
        "ai_reviewer",
        "publication_gate",
        "artifact_authority",
        "owner_receipt",
        "typed_blocker",
    ]
    assert inventory["compatibility_alias_policy"] == {
        "new_alias_allowed": False,
        "active_adapter_can_claim_mas_owner": False,
    }
    return {item["surface_id"]: item for item in inventory["surfaces"]}


def assert_runtime_like_surfaces_have_machine_readable_opl_migration_inventory() -> None:
    surfaces = _inventory_surfaces()
    assert REQUIRED_SURFACES <= set(surfaces)

    for surface in surfaces.values():
        assert surface["generic_runtime_owner"] == "one-person-lab"
        assert surface["mas_owner_claim_allowed"] is False
        assert surface["compatibility_alias_allowed"] is False
        assert "mas_owned_generic_runtime" in surface["forbidden_claims"]
        assert "provider_completion_as_domain_ready" in surface["forbidden_claims"]

    for surface_id in RETIRED_REPO_SOURCE_SURFACES:
        surface = surfaces[surface_id]
        assert surface["current_disposition"] == "physically_retired"
        assert surface["retirement_gate"][
            "repo_source_physical_retirement_authorized"
        ] is True
        assert surface["retirement_gate"][
            "live_runtime_readiness_required_for_repo_source_delete"
        ] is False

    open_live_tails = {
        surface_id
        for surface_id, surface in surfaces.items()
        if surface.get("current_disposition") != "physically_retired"
    }
    assert LIVE_TAIL_SURFACES == open_live_tails
    assert surfaces["stage_outcome_authority"]["execution_authorization_boundary"][
        "closeout_binding_authorizes_execution"
    ] is False
    assert surfaces["runtime_health_kernel"]["diagnostic_projection_boundary"][
        "authority"
    ] is False
    assert surfaces["domain_diagnostic_obligation_actuator"][
        "actuator_can_write_private_blocker_surface"
    ] is False
    assert surfaces["agent_tool_arsenal_scientific_capability_registry"][
        "authority_boundary"
    ]["mas_tool_invocation_runtime_authority"] is False
