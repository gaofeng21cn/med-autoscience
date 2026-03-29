from __future__ import annotations

import os
from pathlib import Path
import subprocess


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


def test_release_installer_exits_zero_after_successful_install(tmp_path: Path) -> None:
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    home_dir = tmp_path / "home"
    home_dir.mkdir()

    (fake_bin / "uv").write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "mkdir -p \"${UV_TOOL_BIN_DIR}\"\n"
        "printf '#!/usr/bin/env bash\\nexit 0\\n' > \"${UV_TOOL_BIN_DIR}/medautosci\"\n"
        "chmod +x \"${UV_TOOL_BIN_DIR}/medautosci\"\n",
        encoding="utf-8",
    )
    (fake_bin / "curl").write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "output=''\n"
        "while (($#)); do\n"
        "  if [[ \"$1\" == '-o' ]]; then\n"
        "    output=\"$2\"\n"
        "    shift 2\n"
        "    continue\n"
        "  fi\n"
        "  shift\n"
        "done\n"
        "if [[ -n \"${output}\" ]]; then\n"
        "  printf 'wheel' > \"${output}\"\n"
        "fi\n",
        encoding="utf-8",
    )
    for tool in ("uv", "curl"):
        path = fake_bin / tool
        path.chmod(0o755)

    env = os.environ.copy()
    env["HOME"] = str(home_dir)
    env["PATH"] = f"{fake_bin}:{env['PATH']}"

    result = subprocess.run(
        ["bash", str(INSTALLER_PATH)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (home_dir / ".local" / "bin" / "medautosci").exists()
