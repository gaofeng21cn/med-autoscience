from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_install_home_local_codex_plugin_creates_plugin_links_and_marketplace(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.codex_plugin_installer")
    home = tmp_path / "home"

    result = module.install_home_local_codex_plugin(repo_root=REPO_ROOT, home=home)

    plugin_link = home / "plugins" / "med-autoscience"
    skill_link = home / ".agents" / "skills" / "med-autoscience"
    marketplace_path = home / ".agents" / "plugins" / "marketplace.json"
    marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    plugin_entry = next(item for item in marketplace["plugins"] if item["name"] == "med-autoscience")

    assert result["plugin_root"] == str(plugin_link)
    assert result["skill_root"] == str(skill_link)
    assert plugin_link.is_symlink()
    assert skill_link.is_symlink()
    assert plugin_link.resolve() == REPO_ROOT / "plugins" / "med-autoscience"
    assert skill_link.resolve() == REPO_ROOT / "plugins" / "med-autoscience" / "skills" / "med-autoscience"
    assert plugin_entry["source"] == {
        "source": "local",
        "path": "./plugins/med-autoscience",
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
