from __future__ import annotations

import os
from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER_PATH = REPO_ROOT / "scripts" / "install-codex-plugin.sh"


def test_codex_plugin_installer_script_keeps_codex_paths_repo_local(tmp_path: Path) -> None:
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    home_dir = tmp_path / "home"
    home_dir.mkdir()

    (fake_bin / "uv").write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "echo 'uv should not be invoked by wrapper-only installer' >&2\n"
        "exit 99\n",
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
    assert not (home_dir / ".local" / "bin" / "mas").exists()
    assert (home_dir / ".local" / "bin" / "medautosci").exists()
    assert (home_dir / ".local" / "bin" / "medautosci-mcp").exists()
    assert not (home_dir / ".local" / "bin" / "medautosci.uv-entrypoint").exists()
    assert not (home_dir / ".local" / "bin" / "medautosci-mcp.uv-entrypoint").exists()
    medautosci_text = (home_dir / ".local" / "bin" / "medautosci").read_text(encoding="utf-8")
    mcp_text = (home_dir / ".local" / "bin" / "medautosci-mcp").read_text(encoding="utf-8")
    assert 'export MAS_CLEAN_RUNNER_ANALYSIS_EXTRA=1' in medautosci_text
    assert 'exec "' + str(REPO_ROOT) + '/scripts/run-python-clean.sh" -m "med_autoscience.cli" "$@"' in medautosci_text
    assert 'export MAS_CLEAN_RUNNER_ANALYSIS_EXTRA=1' in mcp_text
    assert 'exec "' + str(REPO_ROOT) + '/scripts/run-python-clean.sh" -m "med_autoscience.mcp_server" "$@"' in mcp_text
    assert "uv tool install" not in INSTALLER_PATH.read_text(encoding="utf-8")
    assert "--editable" not in INSTALLER_PATH.read_text(encoding="utf-8")
    assert not (home_dir / "plugins" / "mas").exists()
    assert not (home_dir / ".agents" / "skills" / "mas").exists()
    assert not (home_dir / ".agents" / "plugins" / "marketplace.json").exists()
    assert not (REPO_ROOT / ".agents" / "plugins" / "marketplace.json").exists()
    assert "OPL-owned Codex marketplace wrapper" in result.stderr


def test_codex_plugin_installer_removes_stale_mas_cli_wrapper(tmp_path: Path) -> None:
    home_dir = tmp_path / "home"
    local_bin = home_dir / ".local" / "bin"
    local_bin.mkdir(parents=True)
    stale_wrapper = local_bin / "mas"
    stale_wrapper.write_text(
        "#!/usr/bin/env bash\n"
        "exec /repo/scripts/run-python-clean.sh -m med_autoscience.cli \"$@\"\n",
        encoding="utf-8",
    )
    stale_wrapper.chmod(0o755)

    env = os.environ.copy()
    env["HOME"] = str(home_dir)

    result = subprocess.run(
        ["bash", str(INSTALLER_PATH), "--home", str(home_dir), "--repo-root", str(REPO_ROOT)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert not stale_wrapper.exists()
    assert (local_bin / "medautosci").exists()


def test_codex_plugin_installer_script_replaces_stale_uv_tool_symlink(tmp_path: Path) -> None:
    home_dir = tmp_path / "home"
    uv_tool_bin = home_dir / ".local" / "share" / "uv" / "tools" / "med-autoscience" / "bin"
    local_bin = home_dir / ".local" / "bin"
    uv_tool_bin.mkdir(parents=True)
    local_bin.mkdir(parents=True)
    stale_target = uv_tool_bin / "medautosci"
    stale_target.write_text("#!/usr/bin/env python3\nprint('stale uv tool')\n", encoding="utf-8")
    stale_target.chmod(0o755)
    (local_bin / "medautosci").symlink_to(stale_target)

    env = os.environ.copy()
    env["HOME"] = str(home_dir)

    result = subprocess.run(
        ["bash", str(INSTALLER_PATH), "--home", str(home_dir), "--repo-root", str(REPO_ROOT)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )

    installed = local_bin / "medautosci"
    assert result.returncode == 0, result.stderr
    assert installed.exists()
    assert not installed.is_symlink()
    assert "stale uv tool" in stale_target.read_text(encoding="utf-8")
    assert 'exec "' + str(REPO_ROOT) + '/scripts/run-python-clean.sh" -m "med_autoscience.cli" "$@"' in installed.read_text(
        encoding="utf-8"
    )


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
    assert not (home_dir / "plugins" / "mas").exists()
    assert not (home_dir / ".agents" / "skills" / "mas").exists()
    assert not (home_dir / ".agents" / "plugins" / "marketplace.json").exists()
    assert not (REPO_ROOT / ".agents" / "plugins" / "marketplace.json").exists()
    assert "only validating MedAutoScience tracked Codex plugin source" in result.stderr


def test_plugin_local_mcp_launcher_execs_clean_runner(tmp_path: Path) -> None:
    temp_repo = tmp_path / "repo"
    temp_launcher = temp_repo / "plugins" / "mas" / "bin" / "medautosci-mcp"
    temp_runner = temp_repo / "scripts" / "run-python-clean.sh"
    temp_mcp_server = temp_repo / "src" / "med_autoscience" / "mcp_server.py"
    temp_launcher.parent.mkdir(parents=True)
    temp_runner.parent.mkdir(parents=True)
    temp_mcp_server.parent.mkdir(parents=True)
    temp_launcher.write_text(
        (REPO_ROOT / "plugins" / "mas" / "bin" / "medautosci-mcp").read_text(encoding="utf-8"),
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
    temp_mcp_server = temp_repo / "src" / "med_autoscience" / "mcp_server.py"
    cache_launcher.parent.mkdir(parents=True)
    marketplace_plugin.parent.mkdir(parents=True)
    temp_runner.parent.mkdir(parents=True)
    temp_mcp_server.parent.mkdir(parents=True)
    marketplace_plugin.symlink_to(temp_repo / "plugins" / "mas")
    (temp_repo / "plugins" / "mas").mkdir(parents=True)
    cache_launcher.write_text(
        (REPO_ROOT / "plugins" / "mas" / "bin" / "medautosci-mcp").read_text(encoding="utf-8"),
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
