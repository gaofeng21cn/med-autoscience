from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _inventory() -> dict:
    inventory_path = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
    return json.loads(inventory_path.read_text(encoding="utf-8"))


def _surface(inventory: dict, surface_id: str) -> dict:
    return {item["surface_id"]: item for item in inventory["surfaces"]}[surface_id]


def test_open_surface_without_retirement_gate_cannot_satisfy_completion_evidence() -> None:
    inventory = _inventory()
    surface = copy.deepcopy(_surface(inventory, "domain_owner_action_dispatch"))
    surface["surface_id"] = "future_open_surface_without_retirement_gate"
    surface.pop("retirement_gate")

    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )
    audit = retirement.audit_runtime_surface_retirement_inventory({"surfaces": [surface]})
    layers = audit["completion_evidence_layers"]
    tails = {
        item["surface_id"]: item
        for item in layers["live_soak_or_no_active_caller"]["open_surface_tails"]
    }

    assert (
        "future_open_surface_without_retirement_gate",
        "missing_open_surface_retirement_gate",
    ) in {(item["surface_id"], item["reason"]) for item in audit["violations"]}
    assert audit["status"] == "authority_boundary_violation"
    assert audit["live_soak_or_no_active_caller_proven"] is False
    assert audit["physical_delete_allowed"] is False
    assert layers["live_soak_or_no_active_caller"]["status"] == "evidence_required"
    assert layers["live_soak_or_no_active_caller"]["proven"] is False
    assert layers["physical_retirement"]["status"] == "evidence_required"
    assert layers["physical_retirement"]["allowed"] is False
    assert tails["future_open_surface_without_retirement_gate"]["live_or_no_active_proven"] is False
    assert tails["future_open_surface_without_retirement_gate"]["surface_violation_reasons"] == [
        "missing_open_surface_retirement_gate"
    ]
