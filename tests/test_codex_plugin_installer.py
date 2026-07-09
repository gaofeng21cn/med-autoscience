from __future__ import annotations

import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_repo_specific_plugin_installers_are_physically_retired() -> None:
    assert not (REPO_ROOT / "scripts" / "install-codex-plugin.sh").exists()
    assert not (REPO_ROOT / "src" / "med_autoscience" / "codex_plugin_installer.py").exists()


def test_python_cli_installation_uses_standard_project_scripts() -> None:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["scripts"] == {
        "medautosci": "med_autoscience.cli:entrypoint",
        "medautosci-mcp": "med_autoscience.mcp_server:entrypoint",
    }


def test_codex_plugin_is_a_tracked_opl_materialization_source() -> None:
    plugin_root = REPO_ROOT / "plugins" / "med-autoscience"

    assert (REPO_ROOT / "agent" / "primary_skill" / "SKILL.md").is_file()
    assert (plugin_root / ".codex-plugin" / "plugin.json").is_file()
    assert (plugin_root / "skills" / "med-autoscience" / "SKILL.md").is_file()
    assert not (REPO_ROOT / ".agents" / "plugins" / "marketplace.json").exists()
