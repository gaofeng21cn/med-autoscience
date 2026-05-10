from __future__ import annotations

import importlib

from .shared import *  # noqa: F403,F401


def test_mas_action_catalog_drives_cli_product_entry_skill_and_mcp_metadata(tmp_path: Path) -> None:
    action_catalog = importlib.import_module("med_autoscience.action_catalog")
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")
    mcp_server = importlib.import_module("med_autoscience.mcp_server")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    catalog = action_catalog.build_mas_action_catalog(profile_ref=profile_ref)
    neutral_catalog = action_catalog.build_mas_action_catalog()
    manifest = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    skill_catalog = product_entry.build_skill_catalog(profile=profile, profile_ref=profile_ref)
    mcp_tools = {tool["name"]: tool for tool in mcp_server.build_tool_manifest()}

    assert manifest["family_action_catalog"] == catalog
    assert skill_catalog["action_catalog"] == catalog
    assert catalog["authority_boundary"] == {
        "domain_truth_owner": "MedAutoScience",
        "opl_role": "projection_consumer_only",
        "write_policy": "no_domain_truth_writes",
    }

    cli_projection = {item["action_id"]: item for item in action_catalog.project_mas_action_catalog("cli", catalog)}
    product_entry_projection = {
        item["action_key"]: item for item in action_catalog.project_mas_action_catalog("product_entry", catalog)
    }
    skill_projection = {
        item["action_id"]: item for item in action_catalog.project_mas_action_catalog("skill", catalog)
    }
    mcp_projection = {
        item["name"]: item for item in action_catalog.project_mas_action_catalog("mcp", neutral_catalog)
    }

    for action_id, cli_item in cli_projection.items():
        assert manifest["product_entry_shell"][action_id]["command"] == cli_item["command"]
        assert manifest["product_entry_shell"][action_id]["surface_kind"] == cli_item["surface_kind"]
        assert manifest["product_entry_shell"][action_id]["purpose"] == cli_item["summary"]

        assert product_entry_projection[action_id]["command"] == cli_item["command"]
        assert product_entry_projection[action_id]["surface_kind"] == cli_item["surface_kind"]
        assert product_entry_projection[action_id]["summary"] == cli_item["summary"]

        assert skill_projection[action_id]["command"] == cli_item["command"]
        assert skill_projection[action_id]["surface_kind"] == cli_item["surface_kind"]
        assert skill_projection[action_id]["summary"] == cli_item["summary"]

    assert skill_catalog["skills"][0]["domain_projection"]["shell_commands"] == {
        action_id: cli_item["command"] for action_id, cli_item in cli_projection.items()
    }
    assert skill_catalog["skills"][0]["domain_projection"]["action_catalog_projection"] == list(skill_projection.values())

    product_entry_mcp = mcp_projection["product_entry"]
    product_entry_tool = mcp_tools["product_entry"]
    assert product_entry_tool["description"].startswith(product_entry_mcp["description"])
    assert product_entry_tool["inputSchema"]["properties"]["mode"] == product_entry_mcp["input_schema"]
    assert product_entry_tool["metadata"]["action_catalog_projection"] == product_entry_mcp

    assert mcp_tools["study_progress"]["metadata"]["action_catalog_projection"] == mcp_projection["study_progress"]
    assert mcp_tools["study_runtime"]["metadata"]["action_catalog_projection"] == mcp_projection["study_runtime"]


def test_mas_action_catalog_projects_sidecar_bridge_without_new_mcp_tool(tmp_path: Path) -> None:
    action_catalog = importlib.import_module("med_autoscience.action_catalog")
    mcp_server = importlib.import_module("med_autoscience.mcp_server")

    profile_ref = tmp_path / "profile.local.toml"
    catalog = action_catalog.build_mas_action_catalog(profile_ref=profile_ref)
    neutral_catalog = action_catalog.build_mas_action_catalog()

    cli_projection = {item["action_id"]: item for item in action_catalog.project_mas_action_catalog("cli", catalog)}
    product_entry_projection = {
        item["action_key"]: item for item in action_catalog.project_mas_action_catalog("product_entry", catalog)
    }
    skill_projection = {
        item["action_id"]: item for item in action_catalog.project_mas_action_catalog("skill", catalog)
    }
    mcp_projection = {
        item["name"]: item for item in action_catalog.project_mas_action_catalog("mcp", neutral_catalog)
    }
    mcp_tool_names = {tool["name"] for tool in mcp_server.build_tool_manifest()}

    sidecar_export = cli_projection["sidecar_export"]
    assert sidecar_export["effect"] == "read_only"
    assert sidecar_export["command"] == (
        "medautosci sidecar export --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert sidecar_export["surface_kind"] == "mas_family_sidecar_export"

    sidecar_dispatch = cli_projection["sidecar_dispatch"]
    assert sidecar_dispatch["effect"] == "mutating"
    assert sidecar_dispatch["command"] == "medautosci sidecar dispatch --task <task.json> --format json"
    assert sidecar_dispatch["surface_kind"] == "mas_family_sidecar_dispatch_receipt"
    assert "guarded dispatch receipt" in sidecar_dispatch["summary"]
    assert "OPL/Hermes typed queue" in sidecar_dispatch["summary"]
    assert "does not authorize domain truth" in sidecar_dispatch["summary"]
    assert "publication quality" in sidecar_dispatch["summary"]
    assert "artifact gate" in sidecar_dispatch["summary"]
    assert "current package" in sidecar_dispatch["summary"]

    assert product_entry_projection["sidecar_export"]["command"] == sidecar_export["command"]
    assert product_entry_projection["sidecar_dispatch"]["command"] == sidecar_dispatch["command"]
    assert skill_projection["sidecar_export"]["effect"] == "read_only"
    assert skill_projection["sidecar_dispatch"]["effect"] == "mutating"

    assert mcp_projection["sidecar_export"]["descriptor_only"] is True
    assert mcp_projection["sidecar_export"]["public_runtime"] is False
    assert mcp_projection["sidecar_dispatch"]["descriptor_only"] is True
    assert mcp_projection["sidecar_dispatch"]["public_runtime"] is False
    assert {"sidecar_export", "sidecar_dispatch"}.isdisjoint(mcp_tool_names)
