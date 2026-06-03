from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _runner_tmp_with_fake_venv(tmp_path: Path) -> tuple[Path, Path]:
    runner_tmp = tmp_path / "runner-tmp"
    fake_venv = runner_tmp / "venv"
    fake_bin = fake_venv / "bin"
    fake_bin.mkdir(parents=True)
    (fake_bin / "python").symlink_to(sys.executable)
    return runner_tmp, fake_venv


def test_clean_python_runner_preserves_external_uv_cache_only_when_requested(tmp_path: Path) -> None:
    runner_tmp, fake_venv = _runner_tmp_with_fake_venv(tmp_path)
    external_uv_cache = tmp_path / "external-uv-cache"
    external_uv_cache.mkdir()
    (runner_tmp / "uv-sync.done").write_text("synced\n", encoding="utf-8")

    result = subprocess.run(
        [
            str(REPO_ROOT / "scripts/run-python-clean.sh"),
            "-c",
            "import os; print(os.environ['UV_CACHE_DIR'])",
        ],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "MAS_CLEAN_RUNNER_SKIP_SYNC": "1",
            "MAS_CLEAN_RUNNER_TMP_ROOT": str(runner_tmp),
            "MAS_CLEAN_RUNNER_PRESERVE_UV_CACHE": "1",
            "UV_PROJECT_ENVIRONMENT": str(fake_venv),
            "UV_CACHE_DIR": str(external_uv_cache),
        },
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(external_uv_cache)


def test_clean_python_runner_routes_uv_cache_to_runner_tmp_by_default(tmp_path: Path) -> None:
    runner_tmp, fake_venv = _runner_tmp_with_fake_venv(tmp_path)
    sync_log = tmp_path / "uv-sync.log"
    fake_uv = tmp_path / "uv"
    fake_uv.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "printf '%s\\n' \"${UV_CACHE_DIR}\" >> \"${MAS_TEST_SYNC_LOG}\"\n"
        "printf '%s\\n' \"$*\" >> \"${MAS_TEST_SYNC_LOG}\"\n",
        encoding="utf-8",
    )
    fake_uv.chmod(0o755)

    result = subprocess.run(
        [
            str(REPO_ROOT / "scripts/run-python-clean.sh"),
            "-c",
            "print('runner-ok')",
        ],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PATH": f"{tmp_path}{os.pathsep}{os.environ['PATH']}",
            "MAS_CLEAN_RUNNER_SKIP_SYNC": "1",
            "MAS_CLEAN_RUNNER_TMP_ROOT": str(runner_tmp),
            "MAS_TEST_SYNC_LOG": str(sync_log),
            "UV_PROJECT_ENVIRONMENT": str(fake_venv),
        },
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "runner-ok"
    assert sync_log.read_text(encoding="utf-8").splitlines() == [
        str(runner_tmp / "uv-cache"),
        "sync --frozen --group dev --no-install-project --inexact",
    ]
    assert (runner_tmp / "uv-cache").is_dir()
