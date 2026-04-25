from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_install_repo_local_codex_plugin_uses_repo_local_plugin_and_marketplace(tmp_path: Path) -> None:
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
    marketplace_path = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
    marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    plugin_entry = next(item for item in marketplace["plugins"] if item["name"] == "mas")

    assert not legacy_plugin_link.exists()
    assert not legacy_skill_link.exists()
    assert all(item["name"] != "med-autoscience" for item in marketplace["plugins"])
    assert result["plugin_root"] == str(REPO_ROOT / "plugins" / "mas")
    assert result["skill_root"] == str(REPO_ROOT / "plugins" / "mas" / "skills" / "mas")
    assert not plugin_link.exists()
    assert not skill_link.exists()
    assert plugin_entry["source"] == {
        "source": "local",
        "path": "./plugins/mas",
    }
    assert plugin_entry["category"] == "Research"


def test_install_repo_local_codex_plugin_keeps_skill_repo_local(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.codex_plugin_installer")
    home = tmp_path / "home"

    result = module.install_repo_local_codex_plugin(repo_root=REPO_ROOT, home=home)

    assert not (home / ".agents" / "skills" / "mas").exists()
    assert not (home / ".codex" / "skills" / "mas").exists()
    assert result["skill_root"] == str(REPO_ROOT / "plugins" / "mas" / "skills" / "mas")


def test_install_home_local_codex_plugin_is_idempotent(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.codex_plugin_installer")
    home = tmp_path / "home"

    first = module.install_home_local_codex_plugin(repo_root=REPO_ROOT, home=home)
    second = module.install_home_local_codex_plugin(repo_root=REPO_ROOT, home=home)

    assert first["marketplace_path"] == second["marketplace_path"]
    assert first["plugin_root"] == second["plugin_root"]
    assert first["skill_root"] == second["skill_root"]
