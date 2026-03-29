from __future__ import annotations

import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_release_version_is_first_macos_prerelease() -> None:
    pyproject_data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    init_text = (REPO_ROOT / "src" / "med_autoscience" / "__init__.py").read_text(encoding="utf-8")

    assert pyproject_data["project"]["version"] == "0.1.0a2"
    assert '__version__ = "0.1.0a2"' in init_text


def test_release_installer_version_matches_package_version() -> None:
    pyproject_data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    script = (REPO_ROOT / "scripts" / "install-macos.sh").read_text(encoding="utf-8")
    version = pyproject_data["project"]["version"]

    assert f'readonly RELEASE_VERSION="{version}"' in script
    assert f'readonly WHEEL_FILENAME="med_autoscience-{version}-py3-none-any.whl"' in script
