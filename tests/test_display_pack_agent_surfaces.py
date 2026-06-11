from __future__ import annotations

import importlib
from pathlib import Path


def test_action_catalog_exposes_display_pack_agent_capability_as_grouped_mcp_runtime(tmp_path: Path) -> None:
    action_catalog = importlib.import_module("med_autoscience.action_catalog")
    mcp_server = importlib.import_module("med_autoscience.mcp_server")

    profile_ref = tmp_path / "profile.local.toml"
    catalog = action_catalog.build_mas_action_catalog(profile_ref=profile_ref)
    neutral_catalog = action_catalog.build_mas_action_catalog()
    actions = {item["action_id"]: item for item in catalog["actions"]}
    cli_projection = {item["action_id"]: item for item in action_catalog.project_mas_action_catalog("cli", catalog)}
    product_entry_projection = {
        item["action_key"]: item for item in action_catalog.project_mas_action_catalog("product_entry", catalog)
    }
    mcp_projection_items = [
        item
        for item in action_catalog.project_mas_action_catalog("mcp", neutral_catalog)
        if item["name"] == "display_pack_agent"
    ]
    mcp_metadata_by_tool = action_catalog.action_catalog_metadata_by_mcp_tool(neutral_catalog)
    mcp_tool_names = {tool["name"] for tool in mcp_server.build_tool_manifest()}

    expected_actions = {
        "display_pack_capability_discover": "display_pack_agent_capability",
        "display_pack_figure_plan": "display_pack_agent_figure_plan",
        "display_pack_orchestrate": "display_pack_agent_orchestration",
        "display_pack_preflight": "display_pack_agent_preflight",
        "display_pack_render": "display_pack_agent_render_receipt",
    }

    assert expected_actions.keys() <= actions.keys()
    assert "display_pack_agent" in mcp_tool_names
    assert len(mcp_projection_items) == len(expected_actions)
    assert {item["name"] for item in mcp_projection_items} == {"display_pack_agent"}
    assert {item["surface_kind"] for item in mcp_projection_items} == set(expected_actions.values())
    assert mcp_metadata_by_tool["display_pack_agent"]["surface_kind"] == "mas_mcp_tool_group_projection"
    for action_id, surface_kind in expected_actions.items():
        action = actions[action_id]
        assert cli_projection[action_id]["surface_kind"] == surface_kind
        assert product_entry_projection[action_id]["surface_kind"] == surface_kind
        assert action["supported_surfaces"]["mcp"]["tool_name"] == "display_pack_agent"
        assert action["supported_surfaces"]["mcp"]["descriptor_only"] is False
        assert action["supported_surfaces"]["mcp"]["public_runtime"] is True
        assert action["authority_boundary"]["can_mutate_data_or_statistics"] is False
        assert action["authority_boundary"]["can_authorize_publication_readiness"] is False
        assert action["authority_boundary"]["can_replace_owner_receipt"] is False

    assert actions["display_pack_render"]["effect"] == "mutating"
    assert actions["display_pack_orchestrate"]["effect"] == "read_only"
    assert actions["display_pack_render"]["authority_boundary"]["helper_write_policy"] == (
        "display_artifacts_and_refs_only"
    )
