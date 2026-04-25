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
