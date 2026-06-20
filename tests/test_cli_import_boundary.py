from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_cli_import_does_not_require_overlay_installer_or_yaml_modules() -> None:
    code = """
import importlib.abc
import importlib
import sys


class BlockOverlayInstallerAndYaml(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in {"yaml", "med_autoscience.overlay.installer"}:
            raise ModuleNotFoundError(fullname)
        return None


sys.meta_path.insert(0, BlockOverlayInstallerAndYaml())
importlib.import_module("med_autoscience.cli")
assert "med_autoscience.overlay.installer" not in sys.modules
assert "yaml" not in sys.modules
"""
    env = dict(os.environ)
    existing_pythonpath = env.get("PYTHONPATH")
    src_path = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src_path if not existing_pythonpath else f"{src_path}{os.pathsep}{existing_pythonpath}"

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
