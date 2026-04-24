from __future__ import annotations

import os
from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER_PATH = REPO_ROOT / "scripts" / "install-codex-plugin.sh"


def test_codex_plugin_installer_script_sets_up_user_level_codex_paths(tmp_path: Path) -> None:
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    home_dir = tmp_path / "home"
    home_dir.mkdir()

    (fake_bin / "uv").write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "mkdir -p \"${UV_TOOL_BIN_DIR}\"\n"
        "printf '#!/usr/bin/env bash\\nexit 0\\n' > \"${UV_TOOL_BIN_DIR}/medautosci\"\n"
        "printf '#!/usr/bin/env bash\\nexit 0\\n' > \"${UV_TOOL_BIN_DIR}/medautosci-mcp\"\n"
        "chmod +x \"${UV_TOOL_BIN_DIR}/medautosci\" \"${UV_TOOL_BIN_DIR}/medautosci-mcp\"\n",
        encoding="utf-8",
    )
    (fake_bin / "uv").chmod(0o755)

    env = os.environ.copy()
    env["HOME"] = str(home_dir)
    env["PATH"] = f"{fake_bin}:{env['PATH']}"

    result = subprocess.run(
        ["bash", str(INSTALLER_PATH), "--home", str(home_dir), "--repo-root", str(REPO_ROOT)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (home_dir / ".local" / "bin" / "medautosci").exists()
    assert (home_dir / ".local" / "bin" / "medautosci-mcp").exists()
    assert (home_dir / "plugins" / "med-autoscience").is_symlink()
    assert (home_dir / ".agents" / "skills" / "med-autoscience").is_symlink()
    assert (home_dir / ".agents" / "plugins" / "marketplace.json").exists()


def test_codex_plugin_installer_script_skip_tools_only_syncs_plugin_paths(tmp_path: Path) -> None:
    home_dir = tmp_path / "home"
    home_dir.mkdir()

    env = os.environ.copy()
    env["HOME"] = str(home_dir)

    result = subprocess.run(
        ["bash", str(INSTALLER_PATH), "--skip-tools", "--home", str(home_dir), "--repo-root", str(REPO_ROOT)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (home_dir / "plugins" / "med-autoscience").is_symlink()
    assert (home_dir / ".agents" / "skills" / "med-autoscience").is_symlink()
    assert (home_dir / ".agents" / "plugins" / "marketplace.json").exists()
