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


def test_agent_tool_arsenal_mcp_resolve_and_plan_are_opl_hosted_readback_consumers() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")

    resolve_result = module.call_tool(
        "agent_tool_arsenal",
        {
            "mode": "resolve",
            "task_intent": "need display pack baseline for ROC figure",
            "available_refs": ["current_owner_delta"],
            "current_owner_delta": {
                "action_type": "display_pack_orchestrate",
                "display_intent": "Create a ROC curve for model performance.",
            },
        },
    )

    assert resolve_result["isError"] is False
    resolve_payload = _structured_payload(resolve_result)
    assert resolve_payload["surface_kind"] == "mas_capability_resolution"
    assert resolve_payload["authority_boundary"]["hosted_opl_capability_runtime_required"] is True
    assert resolve_payload["authority_boundary"]["mas_resolve_mode_is_selector_authority"] is False
    assert resolve_payload["authority_boundary"]["resolve_or_plan_can_invoke_tool"] is False
    assert (
        resolve_payload["authority_boundary"]["resolve_or_plan_can_authorize_provider_admission"]
        is False
    )

    plan_result = module.call_tool(
        "agent_tool_arsenal",
        {
            "mode": "plan",
            "current_owner_delta": {
                "action_type": "run_quality_repair_batch",
                "source_ref": "controller_decisions/latest.json",
            },
        },
    )

    assert plan_result["isError"] is False
    plan_payload = _structured_payload(plan_result)
    assert plan_payload["surface_kind"] == "mas_capability_invocation_plan"
    assert plan_payload["authority_boundary"]["mas_plan_mode_is_invocation_authority"] is False
    assert plan_payload["authority_boundary"]["resolve_or_plan_can_invoke_tool"] is False
    assert (
        plan_payload["authority_boundary"][
            "resolve_or_plan_can_replace_owner_receipt_or_typed_blocker"
        ]
        is False
    )
