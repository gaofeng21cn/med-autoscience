from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MATERIALIZER_SURFACE_ID = "domain_action_request_materializer_request_tasks_projection"
RUNTIME_HEALTH_SURFACE_ID = "runtime_health_kernel"


def _inventory() -> dict:
    inventory_path = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
    return json.loads(inventory_path.read_text(encoding="utf-8"))


def _surface(inventory: dict, surface_id: str) -> dict:
    return {item["surface_id"]: item for item in inventory["surfaces"]}[surface_id]


def test_materializer_projection_tail_rejects_status_and_ref_completion_regression() -> None:
    inventory = _inventory()
    materializer = _surface(inventory, MATERIALIZER_SURFACE_ID)
    tail = materializer["opl_materializer_projection_tail_readback"]
    tail["status"] = "satisfied_with_request_tasks_alias_retirement"
    tail["required_before_physical_delete"] = "request_tasks_alias_retired_ref"

    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )
    violations = retirement.validate_runtime_surface_retirement_inventory(inventory)

    assert {
        (
            MATERIALIZER_SURFACE_ID,
            "materializer_projection_tail_status_not_open",
        ),
        (
            MATERIALIZER_SURFACE_ID,
            "materializer_projection_tail_required_before_physical_delete_invalid",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in violations}


def test_runtime_health_tail_rejects_status_and_ref_completion_regression() -> None:
    inventory = _inventory()
    runtime_health = _surface(inventory, RUNTIME_HEALTH_SURFACE_ID)
    tail = runtime_health["opl_runtime_health_observability_tail_readback"]
    tail["status"] = "satisfied_with_runtime_health_snapshot"
    tail["required_before_physical_delete"] = "runtime_health_snapshot_clean_ref"

    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )
    violations = retirement.validate_runtime_surface_retirement_inventory(inventory)

    assert {
        (
            RUNTIME_HEALTH_SURFACE_ID,
            "runtime_health_tail_status_not_open",
        ),
        (
            RUNTIME_HEALTH_SURFACE_ID,
            "runtime_health_tail_required_before_physical_delete_invalid",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in violations}
