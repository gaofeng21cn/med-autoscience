from __future__ import annotations

import json
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "med-autoscience"
LEGACY_PLUGIN_ROOT = REPO_ROOT / "plugins" / "mas"
PLUGIN_MANIFEST_PATH = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"


def test_codex_plugin_scaffold_exists_as_tracked_plugin_source() -> None:
    manifest = json.loads(PLUGIN_MANIFEST_PATH.read_text(encoding="utf-8"))

    assert PLUGIN_ROOT.is_dir()
    assert manifest["name"] == "med-autoscience"
    assert manifest["skills"] == "./skills/"
    assert "mcpServers" not in manifest
    assert manifest["interface"]["displayName"] == "Med Auto Science"
    assert not (PLUGIN_ROOT / "bin" / "medautosci-mcp").exists()
    assert not LEGACY_PLUGIN_ROOT.exists()

    assert not (REPO_ROOT / ".agents" / "plugins" / "marketplace.json").exists()


def test_codex_plugin_defers_generated_cli_and_mcp_to_opl() -> None:
    pyproject_data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert "scripts" not in pyproject_data["project"]
    assert not any((REPO_ROOT / "src" / "med_autoscience" / "cli").glob("*.py"))
    assert not (REPO_ROOT / "scripts" / "install-codex-plugin.sh").exists()
