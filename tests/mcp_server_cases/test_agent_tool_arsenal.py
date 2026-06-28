from __future__ import annotations

import importlib

from tests.mcp_server_cases.result_envelope import _assert_tool_result_envelope, _structured_payload

def test_mcp_agent_tool_arsenal_returns_index_card_plan_and_schema() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")

    index_result = module.call_tool("agent_tool_arsenal", {"mode": "index"})

    _assert_tool_result_envelope(index_result, tool_id="agent_tool_arsenal", tool_mode="index")
    assert index_result["isError"] is False
    index_payload = _structured_payload(index_result)
    assert index_payload["surface_kind"] == "mas_agent_tool_arsenal_index"
    assert index_payload["ordinary_planning_root"] == "current_owner_delta"
    assert index_payload["agent_execution_index"]["raw_contract_direct_read_required"] is False
    assert any(item["tool_id"] == "study_progress" for item in index_payload["tool_cards"])

    card_result = module.call_tool(
        "agent_tool_arsenal",
        {"mode": "card", "tool_id": "study_progress"},
    )

    _assert_tool_result_envelope(card_result, tool_id="agent_tool_arsenal", tool_mode="card")
    assert card_result["isError"] is False
    card_payload = _structured_payload(card_result)
    assert card_payload["tool_id"] == "study_progress"
    assert card_payload["risk_annotations"]["readOnlyHint"] is True
    assert card_payload["operational"]["required_refs"] == card_payload["required_refs"]

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

    _assert_tool_result_envelope(resolve_result, tool_id="agent_tool_arsenal", tool_mode="resolve")
    assert resolve_result["isError"] is False
    resolve_payload = _structured_payload(resolve_result)
    assert resolve_payload["surface_kind"] == "mas_capability_resolution"
    assert resolve_payload["discovery_fail_closed"] is False
    display_candidate = next(
        item
        for item in resolve_payload["candidate_tools"]
        if item["action_id"] == "display_pack_orchestrate"
    )
    assert display_candidate["fit_policy"] == "adaptable_baseline_not_exact_contract"
    assert display_candidate["hard_gate_status"] == "blocked_until_refs"
    assert "paper_root" in display_candidate["missing_refs"]

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

    _assert_tool_result_envelope(plan_result, tool_id="agent_tool_arsenal", tool_mode="plan")
    assert plan_result["isError"] is False
    plan_payload = _structured_payload(plan_result)
    assert plan_payload["selected_tool_id"] == "owner_callable:run_quality_repair_batch"
    assert plan_payload["requires"]["owner_receipt_or_typed_blocker"] is True
    assert plan_payload["primary_operational_card"]["tool_id"] == (
        "owner_callable:run_quality_repair_batch"
    )
    assert plan_payload["selection_policy"]["primary_selection"] == "owner_callable"

    schema_result = module.call_tool("agent_tool_arsenal", {"mode": "result_envelope_schema"})

    _assert_tool_result_envelope(
        schema_result,
        tool_id="agent_tool_arsenal",
        tool_mode="result_envelope_schema",
    )
    assert schema_result["isError"] is False
    schema_payload = _structured_payload(schema_result)
    assert schema_payload["title"] == "MAS ToolResultEnvelope"
    assert "recovery" in schema_payload["required"]

    diagnostic_result = module.call_tool("agent_tool_arsenal", {"mode": "completeness_diagnostic"})

    _assert_tool_result_envelope(
        diagnostic_result,
        tool_id="agent_tool_arsenal",
        tool_mode="completeness_diagnostic",
    )
    assert diagnostic_result["isError"] is False
    diagnostic_payload = _structured_payload(diagnostic_result)
    assert diagnostic_payload["surface_kind"] == (
        "mas_agent_tool_arsenal_completeness_diagnostic"
    )
    assert diagnostic_payload["status"] == "complete"
    assert diagnostic_payload["issues"] == []
    assert "doctor_audit" in diagnostic_payload["support_or_diagnostic_mcp_tools"]
    assert "workspace_readiness" in diagnostic_payload["support_or_diagnostic_mcp_tools"]
    assert "display_pack_agent" in diagnostic_payload["public_runtime_mcp_tools"]
    assert diagnostic_payload["doctor_surface_kind"] == (
        "mas_agent_tool_arsenal_drift_parity_doctor"
    )
    assert diagnostic_payload["parity_summary"]["status"] == "complete"
    assert diagnostic_payload["parity_summary"]["doctor_audit_available"] is True
    drift_checks = {item["check_id"]: item for item in diagnostic_payload["drift_checks"]}
    assert drift_checks["mcp_manifest_tool_card_parity"]["status"] == "passed"
