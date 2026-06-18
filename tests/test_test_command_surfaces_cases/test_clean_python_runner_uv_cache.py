from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _clean_runner_env(**updates: str) -> dict[str, str]:
    env = os.environ.copy()
    env.pop("MAS_CLEAN_RUNNER_REUSE_ENV", None)
    env.pop("MAS_CLEAN_RUNNER_REUSE_ROOT", None)
    env.update(updates)
    return env


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
        env=_clean_runner_env(
            MAS_CLEAN_RUNNER_SKIP_SYNC="1",
            MAS_CLEAN_RUNNER_TMP_ROOT=str(runner_tmp),
            MAS_CLEAN_RUNNER_PRESERVE_UV_CACHE="1",
            UV_PROJECT_ENVIRONMENT=str(fake_venv),
            UV_CACHE_DIR=str(external_uv_cache),
        ),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(external_uv_cache)


def test_clean_python_runner_routes_uv_cache_to_runner_tmp_by_default(tmp_path: Path) -> None:
    runner_tmp, fake_venv = _runner_tmp_with_fake_venv(tmp_path)
    stable_cache_root = tmp_path / "stable-clean-runner"
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
        env=_clean_runner_env(
            PATH=f"{tmp_path}{os.pathsep}{os.environ['PATH']}",
            MAS_CLEAN_RUNNER_SKIP_SYNC="1",
            MAS_CLEAN_RUNNER_CACHE_ROOT=str(stable_cache_root),
            MAS_CLEAN_RUNNER_TMP_ROOT=str(runner_tmp),
            MAS_TEST_SYNC_LOG=str(sync_log),
            UV_PROJECT_ENVIRONMENT=str(fake_venv),
        ),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "runner-ok"
    expected_uv_cache = stable_cache_root / "uv-cache"
    assert sync_log.read_text(encoding="utf-8").splitlines() == [
        str(expected_uv_cache),
        (
            "sync --frozen --group dev --no-install-project --inexact "
            f"-C--global-option=egg_info -C--global-option=--egg-base={runner_tmp / 'egg-info'}"
        ),
    ]
    assert expected_uv_cache.is_dir()
    assert (runner_tmp / "egg-info").is_dir()
    assert not (runner_tmp / "uv-cache").exists()


def test_clean_python_runner_can_isolate_uv_cache_for_cold_runs(tmp_path: Path) -> None:
    runner_tmp, fake_venv = _runner_tmp_with_fake_venv(tmp_path)
    stable_cache_root = tmp_path / "stable-clean-runner"
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
        env=_clean_runner_env(
            PATH=f"{tmp_path}{os.pathsep}{os.environ['PATH']}",
            MAS_CLEAN_RUNNER_CACHE_ROOT=str(stable_cache_root),
            MAS_CLEAN_RUNNER_ISOLATE_UV_CACHE="1",
            MAS_CLEAN_RUNNER_SKIP_SYNC="1",
            MAS_CLEAN_RUNNER_TMP_ROOT=str(runner_tmp),
            MAS_TEST_SYNC_LOG=str(sync_log),
            UV_PROJECT_ENVIRONMENT=str(fake_venv),
        ),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "runner-ok"
    assert sync_log.read_text(encoding="utf-8").splitlines()[0] == str(runner_tmp / "uv-cache")
    assert not (stable_cache_root / "uv-cache").exists()


def test_clean_python_runner_defaults_to_external_reuse_env_locally(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    sync_log = tmp_path / "uv-sync.log"
    host_python = repr(sys.executable)
    fake_uv = fake_bin / "uv"
    fake_uv.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "printf '%s\\n' \"${UV_PROJECT_ENVIRONMENT}\" >> \"${MAS_TEST_SYNC_LOG}\"\n"
        "printf '%s\\n' \"${UV_CACHE_DIR}\" >> \"${MAS_TEST_SYNC_LOG}\"\n"
        "printf '%s\\n' \"$*\" >> \"${MAS_TEST_SYNC_LOG}\"\n"
        "mkdir -p \"${UV_PROJECT_ENVIRONMENT}/bin\"\n"
        "cat >\"${UV_PROJECT_ENVIRONMENT}/bin/python\" <<'PY'\n"
        "#!/usr/bin/env python3\n"
        "import os\n"
        "import sys\n"
        f"os.execv({host_python}, [{host_python}, *sys.argv[1:]])\n"
        "PY\n"
        "chmod +x \"${UV_PROJECT_ENVIRONMENT}/bin/python\"\n",
        encoding="utf-8",
    )
    fake_uv.chmod(0o755)
    xdg_cache_home = tmp_path / "xdg-cache"
    expected_reuse_root = xdg_cache_home / "med-autoscience" / "clean-runner"

    script = (
        "import json, os; "
        "print(json.dumps({"
        "'venv': os.environ['UV_PROJECT_ENVIRONMENT'], "
        "'cache': os.environ['UV_CACHE_DIR'], "
        "'pycache': os.environ['PYTHONPYCACHEPREFIX']"
        "}, sort_keys=True))"
    )
    command = [str(REPO_ROOT / "scripts/run-python-clean.sh"), "-c", script]
    env = _clean_runner_env(
        CI="",
        PATH=f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        MAS_CLEAN_RUNNER_TMP_ROOT="",
        MAS_TEST_SYNC_LOG=str(sync_log),
        XDG_CACHE_HOME=str(xdg_cache_home),
        UV_CACHE_DIR="",
        UV_PROJECT_ENVIRONMENT="",
        PYTHONPYCACHEPREFIX="",
    )

    first = subprocess.run(command, cwd=REPO_ROOT, env=env, check=False, capture_output=True, text=True)
    second = subprocess.run(command, cwd=REPO_ROOT, env=env, check=False, capture_output=True, text=True)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    first_env = json.loads(first.stdout)
    second_env = json.loads(second.stdout)
    assert first_env == second_env
    assert Path(first_env["venv"]).is_relative_to(expected_reuse_root)
    assert Path(first_env["cache"]).is_relative_to(expected_reuse_root)
    assert Path(first_env["pycache"]).is_relative_to(expected_reuse_root)
    assert not Path(first_env["venv"]).is_relative_to(REPO_ROOT)
    assert not Path(first_env["cache"]).is_relative_to(REPO_ROOT)
    assert sync_log.read_text(encoding="utf-8").splitlines() == [
        str(expected_reuse_root / "venv"),
        str(expected_reuse_root / "uv-cache"),
        (
            "sync --frozen --group dev --no-install-project --inexact "
            f"-C--global-option=egg_info -C--global-option=--egg-base={expected_reuse_root / 'egg-info'}"
        ),
    ]


def test_clean_python_runner_rejects_checkout_local_default_uv_cache(tmp_path: Path) -> None:
    runner_tmp, fake_venv = _runner_tmp_with_fake_venv(tmp_path)
    checkout_local_default_cache = REPO_ROOT / ".mas-clean-runner-default-uv-cache"
    (runner_tmp / "uv-sync.done").write_text("synced\n", encoding="utf-8")

    result = subprocess.run(
        [
            str(REPO_ROOT / "scripts/run-python-clean.sh"),
            "-c",
            "print('runner-ok')",
        ],
        cwd=REPO_ROOT,
        env=_clean_runner_env(
            MAS_CLEAN_RUNNER_SKIP_SYNC="1",
            MAS_CLEAN_RUNNER_DEFAULT_UV_CACHE_DIR=str(checkout_local_default_cache),
            MAS_CLEAN_RUNNER_TMP_ROOT=str(runner_tmp),
            UV_PROJECT_ENVIRONMENT=str(fake_venv),
        ),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "default uv cache must be outside the checkout" in result.stderr
    assert not checkout_local_default_cache.exists()


def test_clean_python_runner_rejects_checkout_local_reuse_root() -> None:
    checkout_local_reuse_root = REPO_ROOT / ".mas-clean-runner-reuse"

    result = subprocess.run(
        [
            str(REPO_ROOT / "scripts/run-python-clean.sh"),
            "-c",
            "print('runner-ok')",
        ],
        cwd=REPO_ROOT,
        env=_clean_runner_env(
            MAS_CLEAN_RUNNER_REUSE_ENV="1",
            MAS_CLEAN_RUNNER_REUSE_ROOT=str(checkout_local_reuse_root),
        ),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "reuse root must be outside the checkout" in result.stderr
    assert not checkout_local_reuse_root.exists()


def test_clean_python_runner_rejects_checkout_local_egg_info_base() -> None:
    checkout_local_egg_info_base = REPO_ROOT / ".mas-clean-runner-egg-info-base"

    result = subprocess.run(
        [
            str(REPO_ROOT / "scripts/run-python-clean.sh"),
            "-c",
            "print('runner-ok')",
        ],
        cwd=REPO_ROOT,
        env=_clean_runner_env(
            MAS_CLEAN_RUNNER_EGG_INFO_BASE=str(checkout_local_egg_info_base),
        ),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "egg-info base must be outside the checkout" in result.stderr
    assert not checkout_local_egg_info_base.exists()


def test_clean_python_runner_removes_auto_tmp_root_after_success(tmp_path: Path) -> None:
    auto_tmp = tmp_path / "auto-tmp"
    auto_tmp.mkdir()
    persistent_cache = tmp_path / "persistent-uv-cache"
    fake_uv = tmp_path / "uv"
    fake_uv.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "mkdir -p \"${UV_PROJECT_ENVIRONMENT}/bin\"\n"
        "ln -sf \"${MAS_TEST_PYTHON}\" \"${UV_PROJECT_ENVIRONMENT}/bin/python\"\n",
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
        env=_clean_runner_env(
            PATH=f"{tmp_path}{os.pathsep}{os.environ['PATH']}",
            MAS_CLEAN_RUNNER_REUSE_ENV="0",
            MAS_CLEAN_RUNNER_SKIP_SYNC="0",
            MAS_CLEAN_RUNNER_DEFAULT_UV_CACHE_DIR=str(persistent_cache),
            MAS_CLEAN_RUNNER_TMP_ROOT="",
            MAS_TEST_PYTHON=sys.executable,
            TMPDIR=f"{auto_tmp}/",
            UV_PROJECT_ENVIRONMENT="",
        ),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "runner-ok"
    assert list(auto_tmp.glob("mas-python-run.*")) == []
