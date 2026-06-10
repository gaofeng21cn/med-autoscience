from __future__ import annotations

import importlib

from med_autoscience.action_catalog import build_mas_action_catalog


def test_agent_tool_arsenal_builds_agent_facing_cards_from_action_catalog() -> None:
    module = importlib.import_module("med_autoscience.agent_tool_arsenal")

    arsenal = module.build_agent_tool_arsenal_index()
    catalog_action_ids = {item["action_id"] for item in build_mas_action_catalog()["actions"]}
    cards = {item["action_id"]: item for item in arsenal["tool_cards"]}

    assert arsenal["surface_kind"] == "mas_agent_tool_arsenal_index"
    assert arsenal["contract_id"] == "mas_agent_tool_arsenal.v1"
    assert arsenal["audience"] == "autonomous_agent_executor"
    assert arsenal["human_operator_role"] == "governance_and_authorization_not_manual_tool_composition"
    assert arsenal["ordinary_planning_root"] == "current_owner_delta"
    assert set(cards) == catalog_action_ids
    assert {item["action_id"] for item in arsenal["tool_index_entries"]} == catalog_action_ids

    progress = cards["study_progress"]
    assert progress["surface_kind"] == "mas_tool_use_card"
    assert progress["tool_id"] == "study_progress"
    assert progress["callability"] == "mcp_runtime"
    assert progress["risk_annotations"]["readOnlyHint"] is True
    assert progress["risk_annotations"]["requires_human_gate"] is False
    assert progress["risk_annotations"]["requires_opl_stage_attempt_or_lease"] is False
    assert progress["authority_effects"]["can_return_owner_receipt"] is False
    assert progress["allowed_writes"] == []
    assert progress["result_envelope_schema_ref"] == (
        "contracts/agent_tool_arsenal.json#/result_envelope_schema"
    )
    assert "current_owner_delta" in progress["when_to_use"]

    display_preflight = cards["display_pack_preflight"]
    assert display_preflight["tool_id"] == "display_pack_agent"
    assert display_preflight["tool_mode"] == "preflight"
    assert display_preflight["callability"] == "mcp_runtime"
    assert display_preflight["mcp_invocation"] == {
        "tool_name": "display_pack_agent",
        "mode": "preflight",
        "public_runtime": True,
    }
    assert display_preflight["risk_annotations"]["readOnlyHint"] is True

    dispatch = cards["domain_handler_dispatch"]
    assert dispatch["effect"] == "mutating"
    assert dispatch["callability"] == "descriptor_only"
    assert dispatch["risk_annotations"]["readOnlyHint"] is False
    assert dispatch["risk_annotations"]["requires_opl_stage_attempt_or_lease"] is True
    assert dispatch["authority_effects"]["can_return_owner_receipt"] is True
    assert "publication_quality" in dispatch["forbidden_authority"]
    assert "current_package" in dispatch["forbidden_authority"]


def test_agent_tool_arsenal_indexes_owner_callable_cards_with_lifecycle_contract() -> None:
    module = importlib.import_module("med_autoscience.agent_tool_arsenal")

    arsenal = module.build_agent_tool_arsenal_index()
    owner_cards = {item["action_type"]: item for item in arsenal["owner_callable_cards"]}
    repair = owner_cards["run_quality_repair_batch"]

    assert repair["surface_kind"] == "mas_owner_callable_tool_card"
    assert repair["card_kind"] == "owner_callable"
    assert repair["owner"] == "quality_repair_batch"
    assert repair["callable_surface"] == "quality_repair_batch.run_quality_repair_batch"
    assert "controller_decisions/latest.json" in repair["input_refs"]
    assert "paper/draft.md" in repair["allowed_writes"]
    assert "artifacts/publication_eval/latest.json" in repair["forbidden_writes"]
    assert repair["closeout_contract"]["requires_owner_receipt_or_typed_blocker"] is True
    assert repair["result_envelope_schema_ref"] == (
        "contracts/agent_tool_arsenal.json#/result_envelope_schema"
    )

    schema = arsenal["result_envelope_schema"]
    assert schema["title"] == "MAS ToolResultEnvelope"
    assert {"surface_kind", "tool_id", "status", "audit_trail", "authority_boundary"} <= set(
        schema["required"]
    )
    assert schema["properties"]["status"]["enum"] == [
        "succeeded",
        "blocked",
        "no_op_current",
        "failed",
    ]


def test_agent_tool_arsenal_builds_capability_invocation_plan_from_current_owner_delta() -> None:
    module = importlib.import_module("med_autoscience.agent_tool_arsenal")

    plan = module.build_capability_invocation_plan(
        current_owner_delta={
            "action_type": "run_quality_repair_batch",
            "source_ref": "artifacts/controller_decisions/latest.json",
            "work_unit_fingerprint": "sha256:test",
        }
    )

    assert plan["surface_kind"] == "mas_capability_invocation_plan"
    assert plan["planning_root"] == "current_owner_delta"
    assert plan["selected_card_kind"] == "owner_callable"
    assert plan["selected_action_type"] == "run_quality_repair_batch"
    assert plan["selected_tool_id"] == "owner_callable:run_quality_repair_batch"
    assert plan["requires"]["owner_receipt_or_typed_blocker"] is True
    assert plan["authority_boundary"]["can_write_publication_quality"] is False
    assert "verify_required_input_refs" in plan["invocation_steps"]
    assert "emit_tool_result_envelope" in plan["invocation_steps"]

    display_plan = module.build_capability_invocation_plan(
        current_owner_delta={
            "action_type": "display_pack_preflight",
            "source_ref": "paper/figure_intent.json",
            "work_unit_fingerprint": "sha256:display",
        }
    )

    assert display_plan["selected_card_kind"] == "action_catalog"
    assert display_plan["selected_action_id"] == "display_pack_preflight"
    assert display_plan["selected_tool_id"] == "display_pack_agent"
    assert display_plan["selected_tool_mode"] == "preflight"
    assert display_plan["requires"]["owner_receipt_or_typed_blocker"] is False
