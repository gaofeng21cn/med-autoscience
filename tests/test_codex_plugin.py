from __future__ import annotations

import json
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "med-autoscience"


def test_codex_plugin_metadata_matches_package_and_assets() -> None:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    manifest = json.loads(
        (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )

    assert manifest["version"] == pyproject["project"]["version"]
    assert manifest["repository"] == "https://github.com/gaofeng21cn/med-autoscience"
    assert manifest["interface"]["composerIcon"] == manifest["interface"]["logo"]
    assert (PLUGIN_ROOT / manifest["interface"]["composerIcon"]).is_file()
    assert (
        PLUGIN_ROOT / "skills" / "med-autoscience" / "agents" / "openai.yaml"
    ).is_file()
