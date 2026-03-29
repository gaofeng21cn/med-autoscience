from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER_PATH = REPO_ROOT / "scripts" / "install-macos.sh"


def test_release_installer_declares_explicit_version_and_wheel_filename_constants() -> None:
    script = INSTALLER_PATH.read_text(encoding="utf-8")

    assert 'readonly RELEASE_VERSION=' in script
    assert 'readonly WHEEL_FILENAME=' in script
    assert "${RELEASE_VERSION}" in script


def test_release_installer_enforces_platform_and_dependencies() -> None:
    script = INSTALLER_PATH.read_text(encoding="utf-8")

    assert 'uname -s' in script
    assert "Darwin" in script
    assert 'uname -m' in script
    assert "arm64" in script
    assert "x86_64" in script
    assert 'for cmd in curl tar bash' in script


def test_release_installer_bootstraps_uv_and_installs_tool_with_managed_python() -> None:
    script = INSTALLER_PATH.read_text(encoding="utf-8")

    assert 'command -v uv' in script
    assert 'UV_INSTALL_DIR="${HOME}/.local/bin"' in script
    assert "astral.sh/uv/install.sh" in script
    assert 'UV_TOOL_BIN_DIR="${HOME}/.local/bin"' in script
    assert "uv tool install" in script
    assert "--python 3.12" in script
    assert "--managed-python" in script
    assert "--python-preference managed" not in script


def test_release_installer_prints_path_guidance() -> None:
    script = INSTALLER_PATH.read_text(encoding="utf-8")

    assert "Add ~/.local/bin to your PATH" in script
