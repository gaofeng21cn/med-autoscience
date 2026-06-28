from __future__ import annotations

import importlib
from pathlib import Path

from tests.mcp_server_cases.result_envelope import _assert_tool_result_envelope, _structured_payload


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_mcp_display_pack_agent_plans_from_structured_figure_request() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")

    result = module.call_tool(
        "display_pack_agent",
        {
            "mode": "plan",
            "repo_root": str(REPO_ROOT),
            "figure_request": {
                "figure_kind": "evidence_figure",
                "audit_family": "Prediction Performance",
                "preferred_renderer_family": "r_ggplot2",
                "query": "roc",
            },
            "max_recommendations": 2,
        },
    )

    assert result["isError"] is False
    envelope = _assert_tool_result_envelope(result, tool_id="display_pack_agent", tool_mode="plan")
    payload = _structured_payload(result)
    assert payload["surface_kind"] == "display_pack_agent_figure_plan"
    assert payload["recommended_template"]["template_id"] == "roc_curve_binary"
    assert payload["next_callable"] == "display-pack-preflight"
    assert envelope["raw_surface_kind"] == "display_pack_agent_figure_plan"


def test_mcp_display_pack_agent_orchestrates_from_current_owner_delta(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    from med_autoscience.publication_display_contract import seed_publication_display_contracts_if_missing

    paper_root = tmp_path / "paper"
    seed_publication_display_contracts_if_missing(paper_root=paper_root)

    result = module.call_tool(
        "display_pack_agent",
        {
            "mode": "orchestrate",
            "repo_root": str(REPO_ROOT),
            "paper_root": str(paper_root),
            "current_owner_delta": {
                "action_type": "display_pack_orchestrate",
                "display_intent": "Create a ROC curve for prediction model performance.",
            },
            "claim_ref": "claim:roc",
            "data_ref": "data:roc",
            "check_runtime_dependencies": False,
        },
    )

    assert result["isError"] is False
    envelope = _assert_tool_result_envelope(
        result,
        tool_id="display_pack_agent",
        tool_mode="orchestrate",
    )
    payload = _structured_payload(result)
    assert payload["surface_kind"] == "display_pack_agent_orchestration"
    assert payload["status"] == "ready_to_render"
    assert payload["plan"]["recommended_template"]["template_id"] == "roc_curve_binary"
    assert payload["agent_manual_template_selection_required"] is False
    assert payload["publication_readiness_verdict"] is False
    assert envelope["raw_surface_kind"] == "display_pack_agent_orchestration"


def test_mcp_scientific_capability_registry_resolves_and_invokes_display_pack(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    from med_autoscience.publication_display_contract import seed_publication_display_contracts_if_missing

    paper_root = tmp_path / "paper"
    seed_publication_display_contracts_if_missing(paper_root=paper_root)

    index_result = module.call_tool("scientific_capability_registry", {"mode": "index"})
    _assert_tool_result_envelope(
        index_result,
        tool_id="scientific_capability_registry",
        tool_mode="index",
    )
    assert index_result["isError"] is False
    index_payload = _structured_payload(index_result)
    assert index_payload["surface_kind"] == "mas_scientific_capability_registry"
    assert index_payload["default_policy"]["fail_open"] is True
    assert any(
        item["capability_id"] == "display_pack_visual_capability"
        for item in index_payload["capabilities"]
    )

    resolve_result = module.call_tool(
        "scientific_capability_registry",
        {
            "mode": "resolve",
            "current_owner_delta": {
                "action_type": "display_pack_orchestrate",
                "capability_families": ["display_pack"],
            },
        },
    )
    _assert_tool_result_envelope(
        resolve_result,
        tool_id="scientific_capability_registry",
        tool_mode="resolve",
    )
    assert resolve_result["isError"] is False
    resolve_payload = _structured_payload(resolve_result)
    assert resolve_payload["surface_kind"] == "mas_scientific_capability_resolution"
    assert resolve_payload["status"] == "resolved"
    assert any(
        item["capability_id"] == "display_pack_visual_capability"
        for item in resolve_payload["selected_capabilities"]
    )
    assert resolve_payload["missing_capability_blocks_owner_action"] is False

    invoke_result = module.call_tool(
        "scientific_capability_registry",
        {
            "mode": "invoke",
            "capability_id": "display_pack_visual_capability",
            "payload": {
                "repo_root": str(REPO_ROOT),
                "paper_root": str(paper_root),
                "claim_ref": "claim:roc",
                "data_ref": "data:roc",
                "check_runtime_dependencies": False,
                "figure_request": {
                    "figure_kind": "evidence_figure",
                    "audit_family": "Prediction Performance",
                    "preferred_renderer_family": "r_ggplot2",
                    "query": "roc",
                },
            },
        },
    )
    _assert_tool_result_envelope(
        invoke_result,
        tool_id="scientific_capability_registry",
        tool_mode="invoke",
    )
    assert invoke_result["isError"] is False
    invoke_payload = _structured_payload(invoke_result)
    assert invoke_payload["surface_kind"] == "mas_scientific_capability_invocation"
    assert invoke_payload["capability_id"] == "display_pack_visual_capability"
    assert invoke_payload["can_block_current_owner_action"] is False
    assert invoke_payload["status"] == "opl_capability_request_pending"
    assert invoke_payload["mas_local_capability_actuator"] is False
    assert invoke_payload["result"]["surface_kind"] == (
        "mas_scientific_capability_invocation_request_projection"
    )
    request = invoke_payload["opl_capability_invocation_request"]
    assert request["target_runtime_owner"] == "one-person-lab"
    assert request["target_runtime_kind"] == "CapabilityRegistry"
    assert request["mas_can_run_capability_actuator"] is False
