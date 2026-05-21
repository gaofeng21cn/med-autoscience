from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _prepare_fake_runner(tmp_path: Path) -> tuple[Path, Path]:
    runner_tmp = tmp_path / "runner-tmp"
    fake_venv = runner_tmp / "venv"
    fake_bin = fake_venv / "bin"
    fake_bin.mkdir(parents=True)
    fake_python = fake_bin / "python"
    fake_python.symlink_to(sys.executable)
    sync_log = tmp_path / "uv-sync.log"
    fake_uv = tmp_path / "uv"
    fake_uv.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "printf '%s\\n' \"$*\" >> \"${MAS_TEST_SYNC_LOG}\"\n",
        encoding="utf-8",
    )
    fake_uv.chmod(0o755)
    return runner_tmp, sync_log


def test_clean_python_runner_auto_enables_analysis_extra_for_owner_apply(tmp_path: Path) -> None:
    runner_tmp, sync_log = _prepare_fake_runner(tmp_path)

    result = subprocess.run(
        [
            str(REPO_ROOT / "scripts/run-python-clean.sh"),
            "-m",
            "med_autoscience.cli",
            "runtime",
            "domain-route-reconcile",
            "--profile",
            "profile.toml",
            "--studies",
            "DM002",
            "--mode",
            "developer_apply_safe",
            "--apply",
        ],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PATH": f"{tmp_path}{os.pathsep}{os.environ['PATH']}",
            "MAS_CLEAN_RUNNER_TMP_ROOT": str(runner_tmp),
            "MAS_CLEAN_RUNNER_SKIP_SYNC": "0",
            "MAS_TEST_SYNC_LOG": str(sync_log),
            "PYTHONPATH": "",
        },
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 127
    assert "--extra analysis" in sync_log.read_text(encoding="utf-8")
    assert (runner_tmp / "uv-sync.analysis.done").is_file()


def test_clean_python_runner_keeps_domain_route_dry_run_light(tmp_path: Path) -> None:
    runner_tmp, sync_log = _prepare_fake_runner(tmp_path)

    result = subprocess.run(
        [
            str(REPO_ROOT / "scripts/run-python-clean.sh"),
            "-m",
            "med_autoscience.cli",
            "runtime",
            "domain-route-reconcile",
            "--profile",
            "profile.toml",
            "--studies",
            "DM002",
            "--mode",
            "developer_apply_safe",
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PATH": f"{tmp_path}{os.pathsep}{os.environ['PATH']}",
            "MAS_CLEAN_RUNNER_TMP_ROOT": str(runner_tmp),
            "MAS_CLEAN_RUNNER_SKIP_SYNC": "0",
            "MAS_TEST_SYNC_LOG": str(sync_log),
            "PYTHONPATH": "",
        },
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 127
    assert "--extra analysis" not in sync_log.read_text(encoding="utf-8")
    assert (runner_tmp / "uv-sync.done").is_file()
    assert not (runner_tmp / "uv-sync.analysis.done").exists()
