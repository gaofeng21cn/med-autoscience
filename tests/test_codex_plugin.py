from __future__ import annotations

import json
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "med-autoscience"
PLUGIN_MANIFEST_PATH = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
PLUGIN_SKILL_PATH = PLUGIN_ROOT / "skills" / "med-autoscience" / "SKILL.md"
MARKETPLACE_PATH = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
GUIDE_PATH = REPO_ROOT / "guides" / "codex_plugin.md"
RELEASE_GUIDE_PATH = REPO_ROOT / "guides" / "codex_plugin_release.md"
README_PATH = REPO_ROOT / "README.md"


def test_codex_plugin_manifest_tracks_repo_metadata_and_skill_layout() -> None:
    pyproject_data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    manifest = json.loads(PLUGIN_MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["name"] == "med-autoscience"
    assert manifest["version"] == pyproject_data["project"]["version"]
    assert manifest["repository"] == "https://github.com/gaofeng21cn/med-autoscience"
    assert manifest["skills"] == "./skills/"
    assert manifest["mcpServers"] == "./.mcp.json"
    assert manifest["interface"]["displayName"] == "MedAutoScience"
    assert manifest["interface"]["category"] == "Research"
    assert "runtime" in manifest["description"].lower()
    assert PLUGIN_SKILL_PATH.is_file()


def test_codex_plugin_marketplace_points_to_repo_local_plugin() -> None:
    marketplace = json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))

    plugin_entry = next(item for item in marketplace["plugins"] if item["name"] == "med-autoscience")

    assert plugin_entry["source"] == {
        "source": "local",
        "path": "./plugins/med-autoscience",
    }
    assert plugin_entry["policy"] == {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    }
    assert plugin_entry["category"] == "Research"


def test_codex_plugin_guide_states_plugin_is_additive_and_non_exclusive() -> None:
    guide = GUIDE_PATH.read_text(encoding="utf-8")

    assert "Codex plugin" in guide
    assert "It does not replace `medautosci`" in guide
    assert "does not reduce compatibility with non-Codex agents or wrappers" in guide


def test_readme_links_codex_plugin_guide() -> None:
    readme = README_PATH.read_text(encoding="utf-8")

    assert "Codex plugin 接入" in readme
    assert "guides/codex_plugin.md" in readme
    assert "如果你主要通过 Codex 驱动 `MedAutoScience`" in readme


def test_codex_plugin_release_guide_is_linked_from_readme_and_install_guide() -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    install_guide = GUIDE_PATH.read_text(encoding="utf-8")
    release_guide = RELEASE_GUIDE_PATH.read_text(encoding="utf-8")

    assert "Codex plugin 发布说明" in readme
    assert "guides/codex_plugin_release.md" in readme
    assert "codex_plugin_release.md" in install_guide
    assert "用途" in release_guide
    assert "安装方式" in release_guide
