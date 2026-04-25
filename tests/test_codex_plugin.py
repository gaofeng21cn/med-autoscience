from __future__ import annotations

import json
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "mas"
PLUGIN_MANIFEST_PATH = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
PLUGIN_SKILL_PATH = PLUGIN_ROOT / "skills" / "mas" / "SKILL.md"
MARKETPLACE_PATH = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
GUIDE_PATH = REPO_ROOT / "docs" / "references" / "codex_plugin.md"
RELEASE_GUIDE_PATH = REPO_ROOT / "docs" / "references" / "codex_plugin_release.md"
README_PATH = REPO_ROOT / "README.md"
MCP_SERVER_PATH = REPO_ROOT / "src" / "med_autoscience" / "mcp_server.py"
AGENT_ENTRY_MODES_PATH = REPO_ROOT / "docs" / "runtime" / "agent_entry_modes.md"


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
    assert "runtime" in manifest["description"].lower()
    assert PLUGIN_SKILL_PATH.is_file()


def test_codex_plugin_marketplace_points_to_repo_local_plugin() -> None:
    marketplace = json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))

    plugin_entry = next(item for item in marketplace["plugins"] if item["name"] == "mas")

    assert plugin_entry["source"] == {
        "source": "local",
        "path": "./plugins/mas",
    }
    assert plugin_entry["policy"] == {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    }
    assert plugin_entry["category"] == "Research"


def test_codex_plugin_support_files_exist() -> None:
    assert GUIDE_PATH.is_file()
    assert RELEASE_GUIDE_PATH.is_file()


def test_mas_skill_pins_domain_runtime_guardrails() -> None:
    skill_text = PLUGIN_SKILL_PATH.read_text(encoding="utf-8")

    assert "Domain runtime 护栏" in skill_text
    assert "必须通过 MAS product-entry、controller、overlay 或 study runtime surface 推进" in skill_text
    assert "不得用 ad-hoc Python/R 脚本、通用文档/PDF/Office skill" in skill_text
    assert "回到 repo 层补最小 callable/controller surface" in skill_text


def test_readme_scopes_stable_callable_surface_to_mas_contracts() -> None:
    readme_text = README_PATH.read_text(encoding="utf-8")

    assert "stable callable surface is the local CLI, MCP tools, product-entry surfaces" in readme_text
    assert "controller-authorized workspace commands/scripts" in readme_text
    assert "The current operator entry surfaces are `CLI`, `MCP`, `product-entry`, and `controller`" in readme_text


def test_product_entry_tool_blocks_ad_hoc_execution_without_contract() -> None:
    mcp_server_text = MCP_SERVER_PATH.read_text(encoding="utf-8")

    assert "If the needed MAS contract is missing" in mcp_server_text
    assert "close the contract gap through a controller-authorized/CLI/MCP/product-entry surface" in mcp_server_text
    assert "do not perform ad-hoc execution" in mcp_server_text


def test_agent_entry_modes_pin_no_ad_hoc_execution_rule() -> None:
    modes_text = AGENT_ENTRY_MODES_PATH.read_text(encoding="utf-8")

    assert "No Ad-hoc Execution Rule" in modes_text
    assert "agents must use controller-authorized `CLI`, `MCP`, `product-entry`, or runtime surfaces" in modes_text
    assert "stop and close the contract gap" in modes_text
    assert "do not bypass MAS with ad-hoc scripts" in modes_text
