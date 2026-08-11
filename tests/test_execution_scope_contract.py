from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
import pytest


ROOT = Path(__file__).resolve().parents[1]
STUDY_ID_SCHEMA = {
    "type": "string",
    "minLength": 1,
    "maxLength": 128,
    "pattern": r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$",
}
IDENTITY_SCHEMA_PATHS = (
    "contracts/schemas/v2/mas-stage-action.input.schema.json",
    "contracts/schemas/v2/mas-candidate-admission-authority.input.schema.json",
    "contracts/schemas/v2/mas-candidate-admission-authority.output.schema.json",
    "contracts/schemas/v2/mas-paper-mission-authority.input.schema.json",
    "contracts/schemas/v2/mas-paper-mission-authority.output.schema.json",
)
WORKSPACE_SCHEMA_PATH = (
    "contracts/schemas/v2/mas-workspace-index.schema.json"
)


def _load(relative_path: str) -> dict[str, Any]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def _study_id_schema(schema: dict[str, Any]) -> dict[str, Any]:
    definitions = schema.get("$defs", {})
    if "study_id" in definitions:
        return definitions["study_id"]
    return schema["properties"]["study_id"]


def _refs(value: Any) -> list[str]:
    if isinstance(value, dict):
        refs = [value["$ref"]] if isinstance(value.get("$ref"), str) else []
        return refs + [ref for item in value.values() for ref in _refs(item)]
    if isinstance(value, list):
        return [ref for item in value for ref in _refs(item)]
    return []


def _workspace_index() -> dict[str, Any]:
    return {
        "surface_kind": "workspace_index",
        "schema_version": "mas.workspace_index.v1",
        "generated_at": "2026-07-22T00:00:00Z",
        "studies": [
            {
                "study_id": "study-003",
                "canonical_study_root": "studies/study-003",
                "display_name": "Current MAS study",
                "status": "active",
                "current_stage_id": None,
                "current_stage_status": None,
                "package_status": "not_ready",
                "lifecycle_ref": "control/lifecycle.json",
                "diagnostic_blockers": [],
            }
        ],
    }


def test_study_id_contract_is_consistent_across_mas_identity_surfaces() -> None:
    for relative_path in IDENTITY_SCHEMA_PATHS:
        schema = _load(relative_path)
        Draft202012Validator.check_schema(schema)
        assert _study_id_schema(schema) == STUDY_ID_SCHEMA

    paper_input = _load(
        "contracts/schemas/v2/mas-paper-mission-authority.input.schema.json"
    )
    paper_output = _load(
        "contracts/schemas/v2/mas-paper-mission-authority.output.schema.json"
    )
    assert _refs(paper_input).count("#/$defs/study_id") == 2
    assert _refs(paper_output).count("#/$defs/study_id") == 1


@pytest.mark.parametrize(
    "study_id",
    ["study", "study-003", "study_003", "study.003", "s1"],
)
def test_study_id_contract_accepts_current_consumers(study_id: str) -> None:
    for relative_path in IDENTITY_SCHEMA_PATHS:
        validator = Draft202012Validator(_study_id_schema(_load(relative_path)))
        assert validator.is_valid(study_id)


@pytest.mark.parametrize(
    "study_id",
    ["", "Study-003", "-study", "study-", "study--003", "study/003", "a" * 129],
)
def test_study_id_contract_rejects_ambiguous_identity(study_id: str) -> None:
    for relative_path in IDENTITY_SCHEMA_PATHS:
        validator = Draft202012Validator(_study_id_schema(_load(relative_path)))
        assert not validator.is_valid(study_id)


def test_workspace_index_schema_is_non_enforcing_and_extensible() -> None:
    schema = _load(WORKSPACE_SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    assert "does not declare host enforcement" in schema["description"]
    assert schema["additionalProperties"] is True
    assert schema["$defs"]["study"]["additionalProperties"] is True
    serialized = json.dumps(schema, sort_keys=True)
    for unavailable_dependency in (
        "execution-scope-snapshot.schema.json",
        "work_item_scope_binding",
        "work_item_root_template",
    ):
        assert unavailable_dependency not in serialized

    current = _workspace_index()
    validator.validate(current)

    extended = deepcopy(current)
    extended["host_projection_extensions"] = {"projection_version": 2}
    extended["studies"][0]["future_host_projection"] = {
        "identity_alias": "study-003",
        "opaque_ref": "host-owned",
    }
    validator.validate(extended)


def test_workspace_index_accepts_opl_identity_only_initialization_without_business_truth() -> None:
    validator = Draft202012Validator(_load(WORKSPACE_SCHEMA_PATH))
    index = {
        "surface_kind": "opl_workspace_index",
        "version": "workspace-index.v1",
        "studies": [
            {
                "study_id": "study-001",
                "canonical_study_root": "studies/study-001",
            }
        ],
    }

    validator.validate(index)
    study = index["studies"][0]
    for mas_owned_field in (
        "status",
        "current_stage_id",
        "current_stage_status",
        "package_status",
        "lifecycle_ref",
        "next_action",
    ):
        assert mas_owned_field not in study

    invalid_hybrid = deepcopy(index)
    invalid_hybrid["schema_version"] = "mas.workspace_index.v1"
    assert not validator.is_valid(invalid_hybrid)


def test_domain_descriptor_declares_the_canonical_study_collection_path() -> None:
    descriptor = _load("contracts/domain_descriptor.json")
    interface = descriptor["standard_agent_interface"]

    assert interface["workspace_binding"]["project_collection_path"] == "studies"
    assert interface["inventory_projection"]["items_pointer"] == "/studies"
    assert interface["inventory_projection"]["work_item_root_template"] == (
        "studies/{study_id}"
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("study_id", "Study-003"),
        ("study_id", "../study-003"),
        ("canonical_study_root", "../studies/study-003"),
        ("lifecycle_ref", "../control/lifecycle.json"),
    ],
)
def test_workspace_index_schema_rejects_unsafe_identity_or_path(
    field: str,
    value: str,
) -> None:
    index = _workspace_index()
    index["studies"][0][field] = value
    validator = Draft202012Validator(_load(WORKSPACE_SCHEMA_PATH))
    assert not validator.is_valid(index)


def test_workspace_index_schema_does_not_claim_host_identity_enforcement() -> None:
    validator = Draft202012Validator(_load(WORKSPACE_SCHEMA_PATH))
    index = _workspace_index()
    index["studies"].append(deepcopy(index["studies"][0]))
    index["studies"][0]["canonical_study_root"] = "studies/another-study"

    validator.validate(index)
