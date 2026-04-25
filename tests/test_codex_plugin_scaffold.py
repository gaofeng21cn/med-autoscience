from __future__ import annotations

import json
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "mas"
PLUGIN_MANIFEST_PATH = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
PLUGIN_SKILL_PATH = PLUGIN_ROOT / "skills" / "mas" / "SKILL.md"
PLUGIN_MCP_PATH = PLUGIN_ROOT / ".mcp.json"
MARKETPLACE_PATH = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"


def test_codex_plugin_scaffold_exists_and_points_to_repo_local_plugin() -> None:
    manifest = json.loads(PLUGIN_MANIFEST_PATH.read_text(encoding="utf-8"))
    marketplace = json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))
    skill_text = PLUGIN_SKILL_PATH.read_text(encoding="utf-8")

    assert PLUGIN_ROOT.is_dir()
    assert manifest["name"] == "mas"
    assert manifest["skills"] == "./skills/"
    assert manifest["mcpServers"] == "./.mcp.json"
    assert manifest["interface"]["displayName"] == "Med Auto Science"
    assert "medautosci" in skill_text
    assert json.loads(PLUGIN_MCP_PATH.read_text(encoding="utf-8"))["mcpServers"]["med-autoscience"]["command"] == (
        "medautosci-mcp"
    )

    plugin_entry = next(item for item in marketplace["plugins"] if item["name"] == "mas")
    assert plugin_entry["source"] == {
        "source": "local",
        "path": "./plugins/mas",
    }
    assert plugin_entry["policy"] == {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    }


def test_codex_plugin_is_additive_and_keeps_python_cli_entrypoint() -> None:
    pyproject_data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    cli_text = (REPO_ROOT / "src" / "med_autoscience" / "cli.py").read_text(encoding="utf-8")

    assert pyproject_data["project"]["scripts"]["medautosci"] == "med_autoscience.cli:entrypoint"
    assert pyproject_data["project"]["scripts"]["medautosci-mcp"] == "med_autoscience.mcp_server:entrypoint"
    assert "def entrypoint() -> None:" in cli_text
