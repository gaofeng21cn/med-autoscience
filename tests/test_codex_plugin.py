from __future__ import annotations

import json
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "mas"
PLUGIN_MANIFEST_PATH = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
PLUGIN_ICON_PATH = PLUGIN_ROOT / "assets" / "icon.png"
PLUGIN_ICON_SOURCE_PATH = PLUGIN_ROOT / "assets" / "icon.svg"
PLUGIN_SKILL_PATH = PLUGIN_ROOT / "skills" / "mas" / "SKILL.md"
PLUGIN_SKILL_UI_METADATA_PATH = PLUGIN_ROOT / "skills" / "mas" / "agents" / "openai.yaml"
MARKETPLACE_PATH = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
MCP_SERVER_PATH = REPO_ROOT / "src" / "med_autoscience" / "mcp_server.py"
ACTION_CATALOG_PATH = REPO_ROOT / "src" / "med_autoscience" / "action_catalog.py"


def test_codex_plugin_manifest_tracks_repo_metadata_and_skill_layout() -> None:
    pyproject_data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    manifest = json.loads(PLUGIN_MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["name"] == "mas"
    assert manifest["version"] == pyproject_data["project"]["version"]
    assert manifest["repository"] == "https://github.com/gaofeng21cn/med-autoscience"
    assert manifest["skills"] == "./skills/"
    assert manifest["mcpServers"] == "./.mcp.json"
    assert manifest["interface"]["displayName"] == "Med Auto Science"
    assert manifest["interface"]["category"] == "Research"
    assert manifest["interface"]["composerIcon"] == "./assets/icon.png"
    assert manifest["interface"]["logo"] == "./assets/icon.png"
    assert "runtime" in manifest["description"].lower()
    assert PLUGIN_ICON_PATH.is_file()
    assert PLUGIN_ICON_SOURCE_PATH.is_file()
    icon_source = PLUGIN_ICON_SOURCE_PATH.read_text(encoding="utf-8")
    assert '<rect width="512" height="512" rx="112"' in icon_source
    assert 'stroke-width="44"' in icon_source
    assert 'stroke="#8AD6FF"' in icon_source
    assert PLUGIN_SKILL_UI_METADATA_PATH.is_file()


def test_mas_plugin_skill_tracks_current_domain_handler_and_doc_boundaries() -> None:
    manifest = json.loads(PLUGIN_MANIFEST_PATH.read_text(encoding="utf-8"))
    skill_text = PLUGIN_SKILL_PATH.read_text(encoding="utf-8")

    assert "DeepScientist overlay workflow" not in manifest["interface"]["longDescription"]
    assert "domain-handler export" in skill_text
    assert "domain-handler dispatch" in skill_text
    assert "OPL framework-managed" in skill_text
    assert "docs/runtime/control/controllers.md" in skill_text
    assert "docs/runtime/contracts/runtime_boundary.md" in skill_text
    assert "docs/runtime/domain_authority_refs_index_guard.md" in skill_text
    assert "docs/runtime/control/runtime_supervision_loop.md" not in skill_text
    assert "docs/runtime/controllers.md" not in skill_text
    assert "docs/references/codex_plugin.md" not in skill_text

    for doc_path in (
        "bootstrap/README.md",
        "docs/runtime/control/controllers.md",
        "docs/runtime/contracts/runtime_boundary.md",
        "docs/runtime/domain_authority_refs_index_guard.md",
        "docs/history/runtime/runtime_supervision_loop.md",
        "docs/runtime/display/progress_portal.md",
        "docs/references/mds-parity/mds_behavior_equivalence_gap_matrix.md",
    ):
        assert (REPO_ROOT / doc_path).is_file()


def test_codex_plugin_marketplace_points_to_repo_local_plugin() -> None:
    marketplace = json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))

    plugin_entry = next(item for item in marketplace["plugins"] if item["name"] == "mas")

    assert marketplace["interface"]["displayName"] == "Med Auto Science Local"
    assert plugin_entry["source"] == {
        "source": "local",
        "path": "./plugins/mas",
    }
    assert plugin_entry["policy"] == {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    }
    assert plugin_entry["category"] == "Research"


def test_mas_skill_ui_metadata_tracks_plugin_display_contract() -> None:
    metadata_text = PLUGIN_SKILL_UI_METADATA_PATH.read_text(encoding="utf-8")

    assert 'display_name: "Med Auto Science"' in metadata_text
    assert 'default_prompt: "Use $mas' in metadata_text


def test_product_entry_tool_blocks_ad_hoc_execution_without_contract() -> None:
    action_catalog_text = ACTION_CATALOG_PATH.read_text(encoding="utf-8")
    mcp_server_text = MCP_SERVER_PATH.read_text(encoding="utf-8")

    assert "PRODUCT_ENTRY_CONTRACT_GAP_TEXT" in mcp_server_text
    assert "If the needed MAS contract is missing" in action_catalog_text
    assert (
        "close the contract gap through a controller-authorized domain handler surface exposed by CLI/MCP/Skill/product-entry"
        in action_catalog_text
    )
    assert "do not perform ad-hoc execution" in action_catalog_text
