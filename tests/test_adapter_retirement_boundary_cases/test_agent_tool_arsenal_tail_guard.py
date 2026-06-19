from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SURFACE_ID = "agent_tool_arsenal_scientific_capability_registry"


def _inventory() -> dict:
    inventory_path = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
    return json.loads(inventory_path.read_text(encoding="utf-8"))


def _surface(inventory: dict, surface_id: str) -> dict:
    return {item["surface_id"]: item for item in inventory["surfaces"]}[surface_id]


def test_agent_tool_arsenal_no_active_scan_does_not_satisfy_hosted_parity_tail() -> None:
    inventory = _inventory()
    capability = _surface(inventory, SURFACE_ID)
    live_soak = capability["live_owner_consumption_soak_boundary"]
    live_soak["no_active_caller_proven"] = True

    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )
    audit = retirement.audit_runtime_surface_retirement_inventory(inventory)
    tails = {
        item["surface_id"]: item
        for item in audit["completion_evidence_layers"]["live_soak_or_no_active_caller"][
            "open_surface_tails"
        ]
    }

    assert tails[SURFACE_ID]["live_or_no_active_proven"] is False
    assert tails[SURFACE_ID]["status"] == "evidence_required"
    assert tails[SURFACE_ID]["physical_delete_allowed"] is False
    assert (
        "agent_tool_arsenal_live_owner_consumption_soak_and_direct_hosted_parity_ref"
        in tails[SURFACE_ID]["required_ref_families"]
    )
