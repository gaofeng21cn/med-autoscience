from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
CLAIM_REF = "claim:dm-cvd-primary-roc-discrimination"
DATA_REF = "artifact:analysis/primary_roc_payload.json"


def _current_owner_delta() -> dict[str, Any]:
    return {
        "action_type": "artifact_display_surface_materialization_required",
        "action_id": "display-pack-primary-roc",
        "study_id": "DM-CVD",
        "quest_id": "DM002",
        "owner": "display_pack_agent",
        "work_unit_id": "primary_roc_display_pack",
        "claim_ref": CLAIM_REF,
        "data_ref": DATA_REF,
        "cohort_ref": "cohort:dm-cvd-validation",
        "endpoint_ref": "endpoint:all-cause-mortality",
        "risk_horizon": "5y",
        "display_goal": "Render a publication-ready ROC curve for the primary mortality model.",
        "capability_families": ["display_pack"],
    }


def _orchestration_payload() -> dict[str, Any]:
    return {
        "claim_ref": CLAIM_REF,
        "data_ref": DATA_REF,
        "intent": "ROC curve for primary mortality risk discrimination",
        "figure_goal": "ROC curve for primary mortality risk discrimination",
        "quality_floor": {
            "requires_style_profile": True,
            "requires_runtime_ready": True,
            "requires_golden_case_or_typed_repair": True,
        },
    }


def _structured_payload(result: dict[str, object]) -> dict[str, object]:
    envelope = result["structuredContent"]
    assert isinstance(envelope, dict)
    assert envelope["surface_kind"] == "mas_tool_result_envelope"
    assert envelope["authority_boundary"]["tool_result_envelope_is_authority_outcome"] is False
    payload = envelope["structured_payload"]
    assert isinstance(payload, dict)
    return payload


def test_display_pack_agent_orchestrates_figure_intent_from_current_owner_delta() -> None:
    module = importlib.import_module("med_autoscience.display_pack_agent")
    orchestrate = getattr(module, "display_pack_orchestrate", None)
    assert callable(orchestrate), (
        "display_pack_agent must expose display_pack_orchestrate(...) for "
        "agent-native current_owner_delta orchestration."
    )

    result = orchestrate(
        repo_root=REPO_ROOT,
        current_owner_delta=_current_owner_delta(),
        claim_ref=CLAIM_REF,
        data_ref=DATA_REF,
        intent="ROC curve for primary mortality risk discrimination",
        max_recommendations=2,
        check_runtime_dependencies=False,
    )

    assert result["surface_kind"] == "display_pack_agent_orchestration"
    assert result["status"] in {"ready_to_render", "needs_repair"}
    assert result["publication_readiness_verdict"] is False
    assert result["authority_boundary"]["can_authorize_publication_readiness"] is False
    assert result["agent_manual_template_selection_required"] is False

    figure_intent = result["figure_intent"]
    assert figure_intent["claim_ref"] == CLAIM_REF
    assert figure_intent["data_ref"] == DATA_REF
    assert figure_intent["planning_root"] == "current_owner_delta"
    assert figure_intent["intent_text"] == "ROC curve for primary mortality risk discrimination"

    figure_request = result["figure_request"]
    assert figure_request["figure_kind"] == "evidence_figure"
    assert figure_request["audit_family"] == "Prediction Performance"
    assert figure_request["preferred_renderer_family"] == "r_ggplot2"
    assert figure_request["query"] == "roc"
    assert figure_request["claim_ref"] == CLAIM_REF
    assert figure_request["data_ref"] == DATA_REF
    assert "template_id" not in _current_owner_delta()
    assert result["plan"]["recommended_template"]["template_id"] == "roc_curve_binary"

    quality_floor = result["quality_floor"]
    assert quality_floor["surface_kind"] == "display_pack_quality_floor"
    assert quality_floor["publication_readiness_verdict"] is False


def test_display_pack_preflight_returns_typed_repair_routes_without_readiness_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.display_pack_agent")

    monkeypatch.setattr(
        module,
        "_r_runtime_status",
        lambda records, *, check_runtime_dependencies: {
            "required": True,
            "status": "missing_dependency",
            "binary": "Rscript",
            "packages": {"ggplot2": False},
        },
    )

    result = module.display_pack_preflight(
        repo_root=REPO_ROOT,
        paper_root=None,
        figure_request={
            "figure_kind": "evidence_figure",
            "audit_family": "Prediction Performance",
            "preferred_renderer_family": "r_ggplot2",
            "query": "roc",
            "claim_ref": CLAIM_REF,
            "data_ref": DATA_REF,
        },
        check_runtime_dependencies=True,
    )

    assert result["surface_kind"] == "display_pack_agent_preflight"
    assert result["status"] == "blocked"
    assert result["publication_readiness_verdict"] is False
    assert result["authority_boundary"]["can_authorize_publication_readiness"] is False
    assert result["repair_owner"] == "MedAutoScience"
    assert result["next_callable"] == "display-pack-preflight"

    routes = result["typed_repair_routes"]
    assert isinstance(routes, list)
    route_codes = {route["code"] for route in routes}
    assert {
        "paper_root_missing",
        "r_runtime_not_ready",
        "golden_case_not_declared",
    } <= route_codes
    assert all(route["repair_owner"] for route in routes)
    assert all(
        route["authority_boundary"]["repair_route_can_authorize_publication_readiness"] is False
        for route in routes
    )


def test_mcp_display_pack_agent_orchestrate_mode_returns_tool_result_envelope() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    tools = {tool["name"]: tool for tool in module.build_tool_manifest()}

    assert "orchestrate" in tools["display_pack_agent"]["inputSchema"]["properties"]["mode"]["enum"]
    assert tools["display_pack_agent"]["inputSchema"]["properties"]["current_owner_delta"] == {
        "type": "object"
    }

    result = module.call_tool(
        "display_pack_agent",
        {
            "mode": "orchestrate",
            "repo_root": str(REPO_ROOT),
            "current_owner_delta": _current_owner_delta(),
            "claim_ref": CLAIM_REF,
            "data_ref": DATA_REF,
            "intent": "ROC curve for primary mortality risk discrimination",
            "max_recommendations": 2,
            "check_runtime_dependencies": False,
        },
    )

    assert result["isError"] is False
    envelope = result["structuredContent"]
    assert isinstance(envelope, dict)
    assert envelope["surface_kind"] == "mas_tool_result_envelope"
    assert envelope["tool_id"] == "display_pack_agent"
    assert envelope["tool_mode"] == "orchestrate"
    assert envelope["status"] in {"succeeded", "blocked"}

    payload = _structured_payload(result)
    assert payload["surface_kind"] == "display_pack_agent_orchestration"
    assert payload["figure_intent"]["claim_ref"] == CLAIM_REF
    assert payload["figure_request"]["data_ref"] == DATA_REF
    assert payload["quality_floor"]["publication_readiness_verdict"] is False
    assert payload["next_callable"] in {"display-pack-render", "display-pack-repair"}


def test_scientific_capability_registry_invokes_display_pack_agent_native_plan() -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")

    result = module.invoke_scientific_capability(
        capability_id="display_pack_visual_capability",
        current_owner_delta=_current_owner_delta(),
        payload={
            "repo_root": str(REPO_ROOT),
            "check_runtime_dependencies": False,
            **_orchestration_payload(),
        },
    )

    assert result["surface_kind"] == "mas_scientific_capability_invocation"
    assert result["capability_id"] == "display_pack_visual_capability"
    assert result["status"] == "invoked"
    assert result["refs_only"] is True
    assert result["can_block_current_owner_action"] is False
    assert result["authority_boundary"]["can_authorize_publication_readiness"] is False

    orchestration = result["result"]
    assert orchestration["surface_kind"] == "display_pack_agent_orchestration"
    assert orchestration["figure_intent"]["claim_ref"] == CLAIM_REF
    assert orchestration["figure_request"]["query"] == "roc"
    assert orchestration["quality_floor"]["publication_readiness_verdict"] is False
    assert orchestration["next_callable"] in {"display-pack-render", "display-pack-repair"}
