from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta
REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_json(relative_path: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def test_stage_action_schema_is_closed_and_matches_catalog_fields() -> None:
    catalog = _read_json("contracts/action_catalog.json")
    input_schema = _read_json("contracts/schemas/v2/mas-stage-action.input.schema.json")
    output_schema = _read_json("contracts/schemas/v2/mas-stage-action.output.schema.json")
    stage_actions = [
        action
        for action in catalog["actions"]
        if action["execution_binding"]["kind"] == "stage_binding"
    ]

    assert input_schema["additionalProperties"] is False
    assert input_schema["required"] == ["workspace_root", "study_id"]
    assert set(input_schema["properties"]) == {
        "workspace_root",
        "study_id",
        "user_intent",
        "input_refs",
        "route_context_refs",
        "human_gate_refs",
    }
    assert output_schema["additionalProperties"] is False
    assert set(output_schema["properties"]["stage_id"]["enum"]) == {
        action["action_id"] for action in stage_actions
    }
    for action in stage_actions:
        assert action["required_fields"] == input_schema["required"]
        assert set(action["required_fields"] + action["optional_fields"]) == set(
            input_schema["properties"]
        )


def test_handler_registry_and_source_closure_contract_are_explicit() -> None:
    descriptor = _read_json("contracts/domain_descriptor.json")
    compiler_input = _read_json("contracts/pack_compiler_input.json")
    source_closure = _read_json("contracts/source_closure_audit.json")

    assert descriptor["standard_contract_refs"]["domain_handler_registry"] == (
        "contracts/domain_handler_registry.json"
    )
    assert descriptor["standard_contract_refs"]["source_closure_audit"] == (
        "contracts/source_closure_audit.json"
    )
    assert "paper_mission_authority_evaluate" in compiler_input[
        "minimal_authority_functions"
    ]
    assert source_closure["surface_kind"] == "standard_agent_source_closure_audit"
    assert source_closure["version"] == "standard-agent-source-closure-audit.v1"
    entries = source_closure["entries"]
    assert {entry["file"] for entry in entries} == {"scripts/repo_hygiene_audit.py"}
    assert {entry["role"] for entry in entries} == {"developer_tool"}
    assert {
        entry["symbol"]: (entry["allowed_effects"], entry["allowed_targets"])
        for entry in entries
    } == {
        "_default_repo_root": (["process_spawn"], ["git"]),
        "audit_tracked_paths": (["process_spawn"], ["git"]),
        "audit_active_surface_residue": (["process_spawn"], ["git"]),
        "_is_git_ignored": (["process_spawn"], ["git"]),
        "_remove_path": (["filesystem_write"], []),
    }
