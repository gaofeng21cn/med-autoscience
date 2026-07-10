from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = REPO_ROOT / "contracts/runtime/mas-runtime-surface-retirement-inventory.json"
SCHEMA_PATH = REPO_ROOT / "contracts/runtime/mas-runtime-surface-retirement.schema.json"
RETAINED_TAILS = {
    "stage_outcome_authority",
    "runtime_health_kernel",
    "progress_portal_study_workbench_overview_action_projection",
    "agent_tool_arsenal_scientific_capability_registry",
    "runtime_lifecycle_payload_retention",
    "runtime_storage_maintenance",
}


def _inventory() -> dict:
    return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))


def assert_runtime_like_surfaces_have_machine_readable_opl_migration_inventory() -> None:
    inventory = _inventory()
    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )

    assert retirement.validate_runtime_surface_retirement_inventory(inventory) == []
    assert inventory["schema_ref"] == (
        "contracts/runtime/mas-runtime-surface-retirement.schema.json"
    )
    assert SCHEMA_PATH.is_file()
    surfaces = {item["surface_id"]: item for item in inventory["surfaces"]}
    assert "domain_diagnostic_obligation_actuator" not in surfaces
    assert {
        surface_id
        for surface_id, surface in surfaces.items()
        if surface["disposition"] != "physically_retired"
    } == RETAINED_TAILS
    assert all(surface["mas_runtime_authority"] is False for surface in surfaces.values())
    assert set(inventory["authority_boundary"]["mas_retains"]) == set(
        retirement.REQUIRED_MAS_RETAINS
    )
    assert set(inventory["authority_boundary"]["opl_owns"]) == set(
        retirement.REQUIRED_OPL_OWNS
    )


def test_runtime_retirement_inventory_schema_is_closed_and_machine_readable() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False
    assert schema["$defs"]["surface"]["additionalProperties"] is False
    assert schema["$defs"]["surface"]["properties"]["mas_runtime_authority"] == {
        "const": False
    }
    authority = schema["properties"]["authority_boundary"]["properties"]
    assert set(authority["mas_retains"]["items"]["enum"]) == {
        "medical_truth",
        "publication_quality",
        "artifact_mutation_authority",
        "source_readiness",
        "stage_outcome_authority",
        "owner_receipt",
        "typed_blocker",
    }
    assert set(authority["opl_owns"]["items"]["enum"]) == {
        "queue",
        "attempt",
        "retry",
        "lifecycle",
        "state_index",
        "observability",
        "workbench_shell",
    }
    assert schema["properties"]["surfaces"]["contains"]["properties"]["surface_id"] == {
        "const": "stage_outcome_authority"
    }
