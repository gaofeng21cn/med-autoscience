from __future__ import annotations

import json
from pathlib import Path


def test_action_catalog_exposes_display_pack_agent_capability_for_opl_generation() -> None:
    catalog = json.loads(
        (Path(__file__).resolve().parents[1] / "contracts/action_catalog.json").read_text(
            encoding="utf-8"
        )
    )
    actions = {item["action_id"]: item for item in catalog["actions"]}

    expected_actions = {
        "display_pack_capability_discover": "display_pack_agent_capability",
        "display_pack_figure_plan": "display_pack_agent_figure_plan",
        "display_pack_orchestrate": "display_pack_agent_orchestration",
        "display_pack_preflight": "display_pack_agent_preflight",
        "display_pack_render": "display_pack_agent_render_receipt",
    }

    assert expected_actions.keys() <= actions.keys()
    for action_id, surface_kind in expected_actions.items():
        action = actions[action_id]
        assert action["source_command"]["surface_kind"] == surface_kind
        assert action["source_command"]["command"].endswith(f"#{action_id}")
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
