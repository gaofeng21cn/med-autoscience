from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SURFACE_ID = "domain_health_diagnostic_obligation_actuator"


def _inventory() -> dict:
    inventory_path = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
    return json.loads(inventory_path.read_text(encoding="utf-8"))


def _surface(inventory: dict, surface_id: str) -> dict:
    return {item["surface_id"]: item for item in inventory["surfaces"]}[surface_id]


def test_obligation_actuator_tail_rejects_status_and_ref_completion_regression() -> None:
    inventory = _inventory()
    obligation = _surface(inventory, SURFACE_ID)
    tail = obligation["opl_obligation_actuator_tail_readback"]
    tail["status"] = "satisfied_with_typed_blocker"
    tail["required_before_physical_delete"] = "typed_blocker_authority_result_ref"

    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )
    violations = retirement.validate_runtime_surface_retirement_inventory(inventory)

    assert {
        (
            SURFACE_ID,
            "obligation_actuator_tail_status_not_open",
        ),
        (
            SURFACE_ID,
            "obligation_actuator_tail_required_before_physical_delete_invalid",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in violations}
