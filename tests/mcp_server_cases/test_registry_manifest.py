from __future__ import annotations

import builtins
import importlib
import sys

import pytest

from tests.mcp_server_cases.result_envelope import _assert_tool_result_envelope

EXPECTED_MCP_TOOLS = [
    "doctor_audit",
    "workspace_readiness",
    "research_assets",
    "study_progress",
    "open_auto_research_soak",
    "publication_status",
    "display_pack_agent",
    "scientific_capability_registry",
    "authority_operations",
    "agent_tool_arsenal",
]

def test_mcp_server_tool_registry_import_is_lightweight(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = builtins.__import__
    blocked_roots = {"pypdf", "matplotlib"}

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name.split(".", 1)[0] in blocked_roots:
            raise ModuleNotFoundError(f"No module named {name!r}")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    sys.modules.pop("med_autoscience.mcp_server", None)

    module = importlib.import_module("med_autoscience.mcp_server")

    assert [tool["name"] for tool in module.list_tools()] == EXPECTED_MCP_TOOLS
def test_mcp_server_lists_read_only_tools() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")

    tools = module.list_tools()
    names = [tool["name"] for tool in tools]

    assert names == EXPECTED_MCP_TOOLS
def test_mcp_tools_expose_agent_invocation_annotations_and_output_schema() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")

    tools = {tool["name"]: tool for tool in module.build_tool_manifest()}

    for tool in tools.values():
        assert tool["outputSchema"]["title"] == "MAS ToolResultEnvelope"
        assert "recovery" in tool["outputSchema"]["required"]
        assert "recovery" in tool["outputSchema"]["properties"]
        assert "readOnlyHint" in tool["annotations"]
        assert "destructiveHint" in tool["annotations"]
        assert "idempotentHint" in tool["annotations"]
        assert tool["metadata"]["evidence_gap_consumption_abi"]["contract_ref"] == (
            "contracts/evidence-gap-consumption-abi.json"
        )
        assert tool["metadata"]["evidence_gap_consumption_abi"]["missing_evidence_policy"] == (
            "classify_with_evidence_gap_decision_then_progress_first"
        )

    progress = tools["study_progress"]
    assert "action_catalog_projection" in progress["metadata"]
    assert progress["annotations"]["readOnlyHint"] is True
    assert progress["annotations"]["destructiveHint"] is False
    assert progress["annotations"]["idempotentHint"] is True
    assert progress["outputSchema"]["properties"]["status"]["enum"] == [
        "succeeded",
        "blocked",
        "no_op_current",
        "failed",
    ]

    arsenal = tools["agent_tool_arsenal"]
    assert arsenal["annotations"]["readOnlyHint"] is True
    assert arsenal["annotations"]["destructiveHint"] is False
    assert arsenal["inputSchema"]["properties"]["mode"]["enum"] == [
        "index",
        "card",
        "resolve",
        "plan",
        "result_envelope_schema",
        "completeness_diagnostic",
        "hosted_consumption",
    ]
    assert arsenal["inputSchema"]["properties"]["task_intent"] == {"type": "string"}
    assert arsenal["inputSchema"]["properties"]["available_refs"] == {
        "type": "array",
        "items": {"type": "string"},
    }
    assert arsenal["metadata"]["surface_kind"] == "mas_agent_tool_arsenal_mcp_surface"
    assert arsenal["outputSchema"]["title"] == "MAS ToolResultEnvelope"

    display_agent = tools["display_pack_agent"]
    assert display_agent["annotations"]["readOnlyHint"] is False
    assert set(display_agent["inputSchema"]["properties"]["mode"]["enum"]) == {
        "discover",
        "orchestrate",
        "plan",
        "preflight",
        "render",
    }
    assert display_agent["inputSchema"]["properties"]["current_owner_delta"] == {
        "type": "object"
    }
    assert display_agent["outputSchema"]["title"] == "MAS ToolResultEnvelope"
    capability_registry = tools["scientific_capability_registry"]
    assert capability_registry["annotations"]["readOnlyHint"] is False
    assert capability_registry["inputSchema"]["properties"]["mode"]["enum"] == [
        "summary",
        "inventory",
        "index",
        "resolve",
        "invoke",
    ]
    assert capability_registry["outputSchema"]["title"] == "MAS ToolResultEnvelope"

    assert tools["workspace_readiness"]["annotations"]["readOnlyHint"] is False
    assert tools["authority_operations"]["annotations"]["readOnlyHint"] is False
def test_mcp_tools_call_jsonrpc_returns_single_result_envelope() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")

    response = module.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "agent_tool_arsenal",
                "arguments": {"mode": "result_envelope_schema"},
            },
        }
    )

    assert response is not None
    result = response["result"]
    envelope = result["structuredContent"]
    assert envelope["surface_kind"] == "mas_tool_result_envelope"
    assert envelope["tool_id"] == "agent_tool_arsenal"
    assert envelope["tool_mode"] == "result_envelope_schema"
    assert envelope["status"] == "succeeded"
    assert envelope["structured_payload"]["title"] == "MAS ToolResultEnvelope"
    assert "structured_payload" not in envelope["structured_payload"]
    assert envelope["retryability"] == "retry_safe"
    assert envelope["next_safe_actions"][0]["action"] == "consume_structured_payload"
    assert envelope["next_safe_actions"][0]["authority"] is False
    assert envelope["next_safe_actions"][0]["can_execute"] is False
    assert envelope["next_safe_actions"][0]["can_generate_action"] is False
    assert envelope["next_safe_actions"][0]["action_role"] == "tool_result_consumption_metadata"
    assert envelope["recovery"]["retryability"] == "retry_safe"
    assert "structured_payload" not in envelope["recovery"]
def test_mcp_server_exposes_medical_reporting_audit_tool() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    tools = module.build_tool_manifest()
    descriptions = {tool["name"]: tool["description"] for tool in tools}
    assert "publication_status" in descriptions
    assert "medical_reporting_audit" in descriptions["publication_status"]
    assert "medical_literature_audit" in descriptions["publication_status"]
def test_mcp_server_does_not_resurrect_study_runtime_tool() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    tools = {tool["name"]: tool for tool in module.build_tool_manifest()}

    assert "study_runtime" not in tools
    assert "study_progress" in tools
def test_mcp_server_doctor_tool_describes_backend_audit_surface() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    descriptions = {tool["name"]: tool["description"] for tool in module.build_tool_manifest()}

    description = descriptions["doctor_audit"]

    assert "backend_audit" in description
    assert "backend_" + "upgrade" not in description
    assert "med_deepscientist_" + "upgrade" not in description
