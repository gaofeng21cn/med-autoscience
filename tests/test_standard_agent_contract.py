from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> dict[str, object]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_mas_declares_a_presence_only_dynamic_agent_task_provider() -> None:
    package = _read("opl-package.json")
    descriptor = _read("contracts/domain_descriptor.json")

    assert package["schema_version"] == "opl.package.v2"
    assert package["identity"]["intent"] == descriptor["kind"] == "agent"
    assert package["identity"]["id"] == descriptor["agent_id"] == descriptor["package_id"] == "mas"
    assert package["provides"]["agent"]["stages_ref"] == "agent/stages/manifest.json"
    assert package["dependencies"]["packages"][0]["id"] == "mas-scholar-skills"
    assert package["dependencies"]["packages"][0]["optional"] is False
    assert not {
        "version_requirement",
        "abi",
        "capability_abi",
        "digest",
        "lock",
        "receipt",
    }.intersection(package["dependencies"]["packages"][0])


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
    package = _read("opl-package.json")
    serialized = json.dumps(package)

    assert package["schema_version"] == "opl.package.v2"
    assert "dependency_resolution" not in serialized
    assert "lifecycle_receipt" not in serialized
    assert "rollback" not in serialized
    assert "codex_surface" not in package
