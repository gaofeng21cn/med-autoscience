from __future__ import annotations

import importlib


def _structured_payload(result: dict[str, object]) -> dict[str, object]:
    structured = result["structuredContent"]
    assert isinstance(structured, dict)
    assert structured["surface_kind"] == "mas_tool_result_envelope"
    payload = structured["structured_payload"]
    assert isinstance(payload, dict)
    return payload


def test_agent_tool_arsenal_mcp_returns_hosted_consumption_evidence() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")

    result = module.call_tool(
        "agent_tool_arsenal",
        {
            "mode": "hosted_consumption",
            "current_owner_delta": {
                "action_type": "run_quality_repair_batch",
                "action_id": "dispatch-001",
                "owner": "MedAutoScience",
                "source_ref": "projection/current_owner_delta.json",
                "work_unit_fingerprint": "sha256:repair",
            },
        },
    )

    assert result["isError"] is False
    structured = result["structuredContent"]
    assert isinstance(structured, dict)
    assert structured["surface_kind"] == "mas_tool_result_envelope"
    assert structured["tool_id"] == "agent_tool_arsenal"
    assert structured["tool_mode"] == "hosted_consumption"
    assert structured["status"] == "succeeded"
    payload = _structured_payload(result)
    assert payload["surface_kind"] == "mas_hosted_ordinary_path_consumption_evidence"
    assert payload["ordinary_path_consumes"]["agent_execution_index"] is True
    assert payload["ordinary_path_consumes"]["operational_tool_card"] is True
    assert payload["ordinary_path_consumes"]["capability_invocation_plan"] is True
    assert payload["ordinary_path_consumes"]["tool_result_envelope_recovery"] is True
    assert payload["friction_policy"]["raw_contract_direct_read_required"] is False
    assert payload["friction_policy"]["default_preflight_added"] is False
    assert payload["friction_policy"]["docker_or_dind_required"] is False
    assert payload["authority_boundary"]["can_write_domain_truth"] is False
    assert payload["authority_boundary"]["can_block_current_owner_action"] is False
