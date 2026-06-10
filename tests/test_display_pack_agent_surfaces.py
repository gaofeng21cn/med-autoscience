from __future__ import annotations

import importlib
from pathlib import Path


def test_action_catalog_exposes_display_pack_agent_capability_without_public_mcp_runtime(tmp_path: Path) -> None:
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
    mcp_projection = {
        item["name"]: item for item in action_catalog.project_mas_action_catalog("mcp", neutral_catalog)
    }
    mcp_tool_names = {tool["name"] for tool in mcp_server.build_tool_manifest()}

    expected_actions = {
        "display_pack_capability_discover": "display_pack_agent_capability",
        "display_pack_figure_plan": "display_pack_agent_figure_plan",
        "display_pack_preflight": "display_pack_agent_preflight",
        "display_pack_render": "display_pack_agent_render_receipt",
    }

    assert expected_actions.keys() <= actions.keys()
    for action_id, surface_kind in expected_actions.items():
        assert cli_projection[action_id]["surface_kind"] == surface_kind
        assert product_entry_projection[action_id]["surface_kind"] == surface_kind
        assert mcp_projection[action_id]["descriptor_only"] is True
        assert mcp_projection[action_id]["public_runtime"] is False
        assert action_id not in mcp_tool_names
        assert actions[action_id]["authority_boundary"]["can_mutate_data_or_statistics"] is False
        assert actions[action_id]["authority_boundary"]["can_authorize_publication_readiness"] is False
        assert actions[action_id]["authority_boundary"]["can_replace_owner_receipt"] is False

    assert actions["display_pack_render"]["effect"] == "mutating"
    assert actions["display_pack_render"]["authority_boundary"]["helper_write_policy"] == (
        "display_artifacts_and_refs_only"
    )
