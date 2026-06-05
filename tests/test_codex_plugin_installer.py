from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_install_repo_local_codex_plugin_uses_tracked_plugin_source_without_marketplace_write(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.codex_plugin_installer")
    home = tmp_path / "home"
    legacy_plugin_link = home / "plugins" / "med-autoscience"
    legacy_skill_link = home / ".agents" / "skills" / "med-autoscience"
    legacy_target = tmp_path / "legacy-target"
    legacy_target.mkdir()
    legacy_plugin_link.parent.mkdir(parents=True)
    legacy_skill_link.parent.mkdir(parents=True)
    legacy_plugin_link.symlink_to(legacy_target)
    legacy_skill_link.symlink_to(legacy_target)
    legacy_marketplace_path = home / ".agents" / "plugins" / "marketplace.json"
    legacy_marketplace_path.parent.mkdir(parents=True)
    legacy_marketplace_path.write_text(
        json.dumps({"plugins": [{"name": "med-autoscience", "source": {"path": "./plugins/med-autoscience"}}]}),
        encoding="utf-8",
    )

    result = module.install_repo_local_codex_plugin(repo_root=REPO_ROOT, home=home)

    plugin_link = home / "plugins" / "mas"
    skill_link = home / ".agents" / "skills" / "mas"
    manifest_path = REPO_ROOT / "plugins" / "mas" / ".codex-plugin" / "plugin.json"
    skill_path = REPO_ROOT / "plugins" / "mas" / "skills" / "mas" / "SKILL.md"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert not legacy_plugin_link.exists()
    assert not legacy_skill_link.exists()
    assert legacy_marketplace_path.exists()
    assert result["plugin_root"] == str(REPO_ROOT / "plugins" / "mas")
    assert result["skill_root"] == str(REPO_ROOT / "plugins" / "mas" / "skills" / "mas")
    assert result["plugin_manifest_path"] == str(manifest_path)
    assert result["skill_path"] == str(skill_path)
    assert result["marketplace_path"] == str(REPO_ROOT / ".agents" / "plugins" / "marketplace.json")
    assert result["repo_local_marketplace_written"] == "false"
    assert result["repo_local_marketplace_removed"] == "false"
    assert result["codex_marketplace_owner"] == "opl_owned_wrapper"
    assert not plugin_link.exists()
    assert not skill_link.exists()
    assert not (REPO_ROOT / ".agents" / "plugins" / "marketplace.json").exists()
    assert manifest["name"] == "mas"
    assert manifest["skills"] == "./skills/"
    assert manifest["mcpServers"] == "./.mcp.json"
    assert skill_path.is_file()


def test_install_repo_local_codex_plugin_keeps_skill_repo_local(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.codex_plugin_installer")
    home = tmp_path / "home"

    result = module.install_repo_local_codex_plugin(repo_root=REPO_ROOT, home=home)

    assert not (home / ".agents" / "skills" / "mas").exists()
    assert not (home / ".codex" / "skills" / "mas").exists()
    assert result["skill_root"] == str(REPO_ROOT / "plugins" / "mas" / "skills" / "mas")


def test_install_repo_local_codex_plugin_removes_legacy_test_skill_stub(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.codex_plugin_installer")
    home = tmp_path / "home"
    stub = home / ".codex" / "skills" / "mas"
    stub.mkdir(parents=True)
    (stub / "SKILL.md").write_text(
        "---\nname: mas\ndescription: mas test skill\n---\n\n# mas\n",
        encoding="utf-8",
    )

    module.install_repo_local_codex_plugin(repo_root=REPO_ROOT, home=home)

    assert not stub.exists()


def test_install_repo_local_codex_plugin_preserves_non_stub_user_skill(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.codex_plugin_installer")
    home = tmp_path / "home"
    skill = home / ".codex" / "skills" / "mas"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: mas\ndescription: custom local MAS skill\n---\n\n# mas\n",
        encoding="utf-8",
    )

    module.install_repo_local_codex_plugin(repo_root=REPO_ROOT, home=home)

    assert skill.exists()
    assert "custom local MAS skill" in (skill / "SKILL.md").read_text(encoding="utf-8")


def test_install_home_local_codex_plugin_is_idempotent(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.codex_plugin_installer")
    home = tmp_path / "home"

    first = module.install_home_local_codex_plugin(repo_root=REPO_ROOT, home=home)
    second = module.install_home_local_codex_plugin(repo_root=REPO_ROOT, home=home)

    assert first["plugin_root"] == second["plugin_root"]
    assert first["skill_root"] == second["skill_root"]
    assert first["plugin_manifest_path"] == second["plugin_manifest_path"]
    assert first["skill_path"] == second["skill_path"]
    assert first["marketplace_path"] == second["marketplace_path"]
    assert first["repo_local_marketplace_written"] == second["repo_local_marketplace_written"] == "false"
    assert first["codex_marketplace_owner"] == second["codex_marketplace_owner"] == "opl_owned_wrapper"
