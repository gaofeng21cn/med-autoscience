from __future__ import annotations

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_PLUGIN_ROOT = REPO_ROOT / "plugins" / "med-autoscience"


def test_plugin_local_mcp_launcher_execs_clean_runner(tmp_path: Path) -> None:
    temp_repo = tmp_path / "repo"
    temp_launcher = temp_repo / "plugins" / "med-autoscience" / "bin" / "medautosci-mcp"
    temp_runner = temp_repo / "scripts" / "run-python-clean.sh"
    temp_mcp_server = temp_repo / "src" / "med_autoscience" / "mcp_server" / "__init__.py"
    temp_launcher.parent.mkdir(parents=True)
    temp_runner.parent.mkdir(parents=True)
    temp_mcp_server.parent.mkdir(parents=True)
    temp_launcher.write_text(
        (CANONICAL_PLUGIN_ROOT / "bin" / "medautosci-mcp").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    temp_launcher.chmod(0o755)
    temp_mcp_server.write_text("# test fixture\n", encoding="utf-8")
    capture_path = tmp_path / "runner-argv.txt"
    temp_runner.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "printf '%s\\n' \"$@\" > \"$RUNNER_ARGV_CAPTURE\"\n",
        encoding="utf-8",
    )
    temp_runner.chmod(0o755)

    env = os.environ.copy()
    env["RUNNER_ARGV_CAPTURE"] = str(capture_path)

    result = subprocess.run(
        [str(temp_launcher)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert capture_path.read_text(encoding="utf-8").splitlines() == [
        "-m",
        "med_autoscience.mcp_server",
    ]


def test_plugin_cache_mcp_launcher_resolves_repo_from_opl_marketplace(tmp_path: Path) -> None:
    temp_repo = tmp_path / "repo"
    cache_launcher = (
        tmp_path / "codex-cache" / "med-autoscience-local" / "med-autoscience" / "0.1.0a4" / "bin" / "medautosci-mcp"
    )
    marketplace_plugin = (
        tmp_path
        / "home"
        / "Library"
        / "Application Support"
        / "OPL"
        / "state"
        / "codex-plugin-marketplaces"
        / "med-autoscience-local"
        / "plugins"
        / "med-autoscience"
    )
    temp_runner = temp_repo / "scripts" / "run-python-clean.sh"
    temp_mcp_server = temp_repo / "src" / "med_autoscience" / "mcp_server" / "__init__.py"
    cache_launcher.parent.mkdir(parents=True)
    marketplace_plugin.parent.mkdir(parents=True)
    temp_runner.parent.mkdir(parents=True)
    temp_mcp_server.parent.mkdir(parents=True)
    marketplace_plugin.symlink_to(temp_repo / "plugins" / "med-autoscience")
    (temp_repo / "plugins" / "med-autoscience").mkdir(parents=True)
    cache_launcher.write_text(
        (CANONICAL_PLUGIN_ROOT / "bin" / "medautosci-mcp").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    cache_launcher.chmod(0o755)
    temp_mcp_server.write_text("# test fixture\n", encoding="utf-8")
    capture_path = tmp_path / "runner-argv.txt"
    temp_runner.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "printf '%s\\n' \"$@\" > \"$RUNNER_ARGV_CAPTURE\"\n",
        encoding="utf-8",
    )
    temp_runner.chmod(0o755)

    env = os.environ.copy()
    env["HOME"] = str(tmp_path / "home")
    env["RUNNER_ARGV_CAPTURE"] = str(capture_path)

    result = subprocess.run(
        [str(cache_launcher)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert capture_path.read_text(encoding="utf-8").splitlines() == [
        "-m",
        "med_autoscience.mcp_server",
    ]


def test_plugin_cache_mcp_launcher_retires_legacy_marketplace_lookup(tmp_path: Path) -> None:
    temp_repo = tmp_path / "repo"
    cache_launcher = tmp_path / "codex-cache" / "mas-local" / "mas" / "0.1.0a4" / "bin" / "medautosci-mcp"
    marketplace_plugin = (
        tmp_path
        / "home"
        / "Library"
        / "Application Support"
        / "OPL"
        / "state"
        / "codex-plugin-marketplaces"
        / "mas-local"
        / "plugins"
        / "mas"
    )
    temp_runner = temp_repo / "scripts" / "run-python-clean.sh"
    temp_mcp_server = temp_repo / "src" / "med_autoscience" / "mcp_server" / "__init__.py"
    cache_launcher.parent.mkdir(parents=True)
    marketplace_plugin.parent.mkdir(parents=True)
    temp_runner.parent.mkdir(parents=True)
    temp_mcp_server.parent.mkdir(parents=True)
    marketplace_plugin.symlink_to(temp_repo / "plugins" / "med-autoscience")
    (temp_repo / "plugins" / "med-autoscience").mkdir(parents=True)
    cache_launcher.write_text(
        (CANONICAL_PLUGIN_ROOT / "bin" / "medautosci-mcp").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    cache_launcher.chmod(0o755)
    temp_mcp_server.write_text("# test fixture\n", encoding="utf-8")
    capture_path = tmp_path / "runner-argv-legacy.txt"
    temp_runner.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "printf '%s\\n' \"$@\" > \"$RUNNER_ARGV_CAPTURE\"\n",
        encoding="utf-8",
    )
    temp_runner.chmod(0o755)

    env = os.environ.copy()
    env["HOME"] = str(tmp_path / "home")
    env["RUNNER_ARGV_CAPTURE"] = str(capture_path)

    result = subprocess.run(
        [str(cache_launcher)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 127
    assert not capture_path.exists()
    assert "med-autoscience-local marketplace" in result.stderr
