from __future__ import annotations

import json
from pathlib import Path

from tests.test_adapter_retirement_boundary_cases.runtime_inventory_core import (
    assert_runtime_inventory_core,
)
from tests.test_adapter_retirement_boundary_cases.runtime_inventory_tails import (
    assert_runtime_inventory_tails,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def assert_runtime_like_surfaces_have_machine_readable_opl_migration_inventory() -> None:
    inventory_path = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))

    assert inventory["surface_kind"] == "mas_runtime_surface_retirement_inventory"
    assert inventory["version"] == "mas-runtime-surface-retirement-inventory.v1"
    assert inventory["authority_boundary"] == {
        "opl_owns": [
            "queue",
            "attempt",
            "retry",
            "dead_letter",
            "provider_liveness",
            "generic_stage_state",
        ],
        "mas_owns": [
            "domain_truth",
            "ai_reviewer",
            "publication_gate",
            "artifact_authority",
            "owner_receipt",
            "typed_blocker",
        ],
    }
    assert inventory["compatibility_alias_policy"] == {
        "new_alias_allowed": False,
        "active_adapter_can_claim_mas_owner": False,
    }

    surfaces = {item["surface_id"]: item for item in inventory["surfaces"]}
    assert set(surfaces) >= {
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
        "agent_tool_arsenal_scientific_capability_registry",
    }
    for surface in surfaces.values():
        assert surface["generic_runtime_owner"] == "one-person-lab"
        assert surface["mas_owner_claim_allowed"] is False
        assert surface["compatibility_alias_allowed"] is False
        if surface["surface_id"] in {
            "runtime_transport_core_bridge",
            "runtime_turn_runner_closeout_adapter",
            "worker_lease_residency_projection",
            "domain_action_request_materializer_local_carrier_persistence_api",
            "owner_callable_adapter_legacy_dispatch_projection_alias",
            "domain_action_request_materializer_current_owner_callable_adapters_api",
        }:
            assert surface["active_caller_migrated"] is True
            assert surface["current_disposition"] == "physically_retired"
        assert "mas_owned_generic_runtime" in surface["forbidden_claims"]
    assert_runtime_inventory_core(surfaces)
    assert_runtime_inventory_tails(surfaces)
