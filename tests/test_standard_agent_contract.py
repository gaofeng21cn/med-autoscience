from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> dict[str, object]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_mas_declares_a_presence_only_dynamic_agent_task_provider() -> None:
    package = _read("contracts/opl_agent_package_manifest.json")
    descriptor = _read("contracts/domain_descriptor.json")

    assert package["kind"] == descriptor["kind"] == "agent"
    assert package["agent_id"] == descriptor["agent_id"] == "mas"
    assert package["package_id"] == descriptor["package_id"] == "mas"
    assert package["domain_descriptor_ref"] == "contracts/domain_descriptor.json"
    assert package["task_provider_ref"] == (
        "contracts/domain_descriptor.json#/task_provider"
    )
    assert package["action_catalog_ref"] == descriptor["action_catalog_ref"] == (
        "contracts/action_catalog.json"
    )
    assert package["view_refs"] == [
        "contracts/domain_descriptor.json#/task_provider/views/0"
    ]
    assert package["requires"] == [
        {"package_id": "mas-scholar-skills", "presence": "required"}
    ]
    assert not {
        "version",
        "version_requirement",
        "abi",
        "capability_abi",
        "digest",
        "lock",
        "receipt",
    }.intersection(package["requires"][0])


def test_mas_view_envelope_keeps_medical_schema_and_task_binding_owner_side() -> None:
    descriptor = _read("contracts/domain_descriptor.json")
    provider = descriptor["task_provider"]
    view = provider["views"][0]

    assert provider["inventory_ref"] == (
        "contracts/domain_descriptor.json"
        "#/standard_agent_interface/inventory_projection"
    )
    assert provider["business_lifecycle_owner"] == "MedAutoScience"
    assert provider["temporal_execution_ref"] == {
        "source_kind": "opaque_framework_execution_scope",
        "join_field": "work_item_scope_id",
    }
    assert view == {
        "view_id": "research-roadmap",
        "view_kind": "research-roadmap",
        "title": "Research roadmap",
        "schema_ref": (
            "contracts/schemas/v2/"
            "mas-research-trajectory-snapshot-v2.schema.json"
        ),
        "source_kind": "work_item_relative_json",
        "relative_path": "artifacts/research_trajectory/snapshot.json",
        "revision_pointer": "/revision",
        "owner_task_binding": {
            "task_id_pointer": "/study_id",
            "task_ref_pointer": "/study_ref/ref",
            "task_ref_template": "mas-study:{task_id}",
        },
    }


def test_package_boundary_does_not_restore_the_retired_framework_manager() -> None:
    package = _read("contracts/opl_agent_package_manifest.json")
    boundary = str(package["machine_boundary"])

    assert "configured carrier owns physical lifecycle" in boundary
    assert "Framework aggregates fresh presence" in boundary
    assert "dependency resolution" not in boundary
    assert "lifecycle receipt" not in boundary
    assert "atomic update" not in boundary
    assert "rollback" not in boundary
