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
    launcher = PLUGIN_ROOT / "bin" / "medautosci-mcp"
    assert launcher.is_file()
    launcher_text = launcher.read_text(encoding="utf-8")
    assert "export MAS_CLEAN_RUNNER_ANALYSIS_EXTRA=1" in launcher_text
    assert 'exec "${repo_root}/scripts/run-python-clean.sh" -m med_autoscience.mcp_server "$@"' in launcher_text
    assert 'uv run --directory "${repo_root}"' not in launcher_text
    assert not LEGACY_PLUGIN_ROOT.exists()

    assert not (REPO_ROOT / ".agents" / "plugins" / "marketplace.json").exists()


def test_codex_plugin_is_additive_and_keeps_python_cli_entrypoint() -> None:
    pyproject_data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    cli_text = (REPO_ROOT / "src" / "med_autoscience" / "cli" / "__init__.py").read_text(
        encoding="utf-8"
    )
    clean_runner_script = (REPO_ROOT / "scripts" / "run-python-clean.sh").read_text(encoding="utf-8")

    assert "mas" not in pyproject_data["project"]["scripts"]
    assert pyproject_data["project"]["scripts"]["medautosci"] == "med_autoscience.cli:entrypoint"
    assert pyproject_data["project"]["scripts"]["medautosci-mcp"] == "med_autoscience.mcp_server:entrypoint"
    assert "def entrypoint() -> None:" in cli_text
    assert not (REPO_ROOT / "scripts" / "install-codex-plugin.sh").exists()
    assert "write_launcher medautosci med_autoscience.cli" in clean_runner_script
    assert "write_launcher mas med_autoscience.cli" not in clean_runner_script
