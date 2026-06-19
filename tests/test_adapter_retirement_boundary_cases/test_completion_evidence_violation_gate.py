from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _inventory() -> dict:
    inventory_path = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
    return json.loads(inventory_path.read_text(encoding="utf-8"))


def _surface(inventory: dict, surface_id: str) -> dict:
    return {item["surface_id"]: item for item in inventory["surfaces"]}[surface_id]


def _force_all_live_tail_proofs(inventory: dict) -> None:
    _surface(inventory, "domain_owner_action_dispatch")["active_caller_soak_boundary"][
        "live_every_active_caller_soak_proven"
    ] = True
    _surface(inventory, "domain_authority_refs_index")["opl_state_index_takeover_bridge"][
        "legacy_helper_active_caller_scan"
    ]["no_active_replay_or_local_inspection_caller_proven"] = True
    _surface(inventory, "default_executor_execution_latest_wire_projection")[
        "legacy_stage_run_abi_boundary"
    ]["active_stage_run_abi_caller_scan"]["no_active_stage_run_abi_caller_proven"] = True
    capability_soak = _surface(
        inventory,
        "agent_tool_arsenal_scientific_capability_registry",
    )["live_owner_consumption_soak_boundary"]
    capability_soak["live_owner_consumption_soak_proven"] = True
    capability_soak["direct_hosted_parity_proven"] = True

    tail_keys = (
        "opl_default_executor_carrier_tail_readback",
        "opl_obligation_actuator_tail_readback",
        "opl_runtime_health_observability_tail_readback",
        "opl_materializer_projection_tail_readback",
        "opl_workbench_shell_readback_tail",
        "opl_runtime_lifecycle_maintenance_tail_readback",
        "opl_runtime_storage_maintenance_tail_readback",
    )
    for surface in inventory["surfaces"]:
        for key in tail_keys:
            if isinstance(surface.get(key), dict):
                surface[key]["tail_readback_proven"] = True


def test_completion_evidence_layers_do_not_satisfy_live_evidence_when_authority_violates() -> None:
    inventory = _inventory()
    _force_all_live_tail_proofs(inventory)
    _surface(inventory, "domain_owner_action_dispatch")["mas_owner_claim_allowed"] = True

    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )
    audit = retirement.audit_runtime_surface_retirement_inventory(inventory)
    layers = audit["completion_evidence_layers"]

    assert audit["violations"]
    assert audit["status"] == "authority_boundary_violation"
    assert layers["repo_no_authority_guard"]["status"] == "violations_present"
    assert layers["live_soak_or_no_active_caller"]["status"] == "evidence_required"
    assert layers["live_soak_or_no_active_caller"]["proven"] is False
    assert audit["live_soak_or_no_active_caller_proven"] is False
