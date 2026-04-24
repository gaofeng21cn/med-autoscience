from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_install_home_local_codex_plugin_creates_plugin_links_and_marketplace(tmp_path: Path) -> None:
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

    result = module.install_home_local_codex_plugin(repo_root=REPO_ROOT, home=home)

    plugin_link = home / "plugins" / "mas"
    skill_link = home / ".agents" / "skills" / "mas"
    marketplace_path = home / ".agents" / "plugins" / "marketplace.json"
    marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    plugin_entry = next(item for item in marketplace["plugins"] if item["name"] == "mas")

    assert not legacy_plugin_link.exists()
    assert not legacy_skill_link.exists()
    assert all(item["name"] != "med-autoscience" for item in marketplace["plugins"])
    assert result["plugin_root"] == str(plugin_link)
    assert result["skill_root"] == str(skill_link)
    assert plugin_link.is_symlink()
    assert skill_link.is_symlink()
    assert plugin_link.resolve() == REPO_ROOT / "plugins" / "mas"
    assert skill_link.resolve() == REPO_ROOT / "plugins" / "mas" / "skills" / "mas"
    assert plugin_entry["source"] == {
        "source": "local",
        "path": "./plugins/mas",
    }
    assert plugin_entry["category"] == "Research"


def test_install_home_local_codex_plugin_is_idempotent(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.codex_plugin_installer")
    home = tmp_path / "home"

    first = module.install_home_local_codex_plugin(repo_root=REPO_ROOT, home=home)
    second = module.install_home_local_codex_plugin(repo_root=REPO_ROOT, home=home)

    assert first["marketplace_path"] == second["marketplace_path"]
    assert first["plugin_root"] == second["plugin_root"]
    assert first["skill_root"] == second["skill_root"]
