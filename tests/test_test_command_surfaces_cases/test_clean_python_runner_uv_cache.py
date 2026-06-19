from __future__ import annotations

import json
import os
import subprocess
import sys
import time
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


def test_clean_python_runner_status_reports_cache_without_sync(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_uv = fake_bin / "uv"
    fake_uv.write_text(
        "#!/usr/bin/env bash\n"
        "echo 'status mode must not call uv sync' >&2\n"
        "exit 99\n",
        encoding="utf-8",
    )
    fake_uv.chmod(0o755)
    reuse_root = tmp_path / "shared-clean-runner"
    lock_dir = reuse_root / "uv-sync.done.lock"
    lock_dir.mkdir(parents=True)

    result = subprocess.run(
        [str(REPO_ROOT / "scripts/run-python-clean.sh"), "--clean-runner-status"],
        cwd=REPO_ROOT,
        env=_clean_runner_env(
            CI="",
            PATH=f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
            MAS_CLEAN_RUNNER_REUSE_ENV="1",
            MAS_CLEAN_RUNNER_REUSE_ROOT=str(reuse_root),
            PYTHONPATH="",
        ),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    status = json.loads(result.stdout)
    assert status["surface_kind"] == "mas_clean_python_runner_status"
    assert status["mode"] == "status"
    assert status["status"] == "waiting_for_dependency_sync"
    assert status["reuse_env_enabled"] is True
    assert status["tmp_root"] == str(reuse_root)
    assert status["uv_project_environment"] == str(reuse_root / "venv")
    assert status["uv_cache_dir"] == str(reuse_root / "uv-cache")
    assert status["sync_marker"] == str(reuse_root / "uv-sync.done")
    assert status["marker_current"] is False
    assert status["sync_required"] is True
    assert status["lock_present"] is True
    assert status["venv_python_present"] is False


def test_clean_python_runner_warm_primes_reuse_env_once(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    sync_log = tmp_path / "uv-sync.log"
    host_python = repr(sys.executable)
    fake_uv = fake_bin / "uv"
    fake_uv.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "printf 'sync %s %s\\n' \"${UV_PROJECT_ENVIRONMENT}\" \"${UV_CACHE_DIR}\" >> \"${MAS_TEST_SYNC_LOG}\"\n"
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
    reuse_root = tmp_path / "shared-clean-runner"
    command = [str(REPO_ROOT / "scripts/run-python-clean.sh"), "--clean-runner-warm"]
    env = _clean_runner_env(
        CI="",
        PATH=f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        MAS_CLEAN_RUNNER_REUSE_ENV="1",
        MAS_CLEAN_RUNNER_REUSE_ROOT=str(reuse_root),
        MAS_TEST_SYNC_LOG=str(sync_log),
        PYTHONPATH="",
    )

    first = subprocess.run(command, cwd=REPO_ROOT, env=env, check=False, capture_output=True, text=True)
    second = subprocess.run(command, cwd=REPO_ROOT, env=env, check=False, capture_output=True, text=True)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    first_status = json.loads(first.stdout)
    second_status = json.loads(second.stdout)
    assert first_status["mode"] == "warm"
    assert second_status["mode"] == "warm"
    assert first_status["status"] == "warm_ready"
    assert second_status["status"] == "warm_ready"
    assert first_status["marker_current"] is True
    assert second_status["marker_current"] is True
    assert first_status["sync_required"] is False
    assert second_status["sync_required"] is False
    assert sync_log.read_text(encoding="utf-8").splitlines() == [
        f"sync {reuse_root / 'venv'} {reuse_root / 'uv-cache'}"
    ]


def test_clean_python_runner_reuse_marker_is_independent_of_checkout_path(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    sync_log = tmp_path / "uv-sync.log"
    host_python = repr(sys.executable)
    fake_uv = fake_bin / "uv"
    fake_uv.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "printf '%s\\n' \"$PWD\" >> \"${MAS_TEST_SYNC_LOG}\"\n"
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
    reuse_root = tmp_path / "shared-clean-runner"
    command = ["scripts/run-python-clean.sh", "-c", "print('runner-ok')"]
    env = _clean_runner_env(
        CI="",
        PATH=f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        MAS_CLEAN_RUNNER_REUSE_ENV="1",
        MAS_CLEAN_RUNNER_REUSE_ROOT=str(reuse_root),
        MAS_TEST_SYNC_LOG=str(sync_log),
        PYTHONPATH="",
    )
    checkouts: list[Path] = []
    for name in ("checkout-a", "checkout-b"):
        checkout = tmp_path / name
        (checkout / "scripts").mkdir(parents=True)
        (checkout / "scripts" / "run-python-clean.sh").write_text(
            (REPO_ROOT / "scripts" / "run-python-clean.sh").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (checkout / "scripts" / "run-python-clean.sh").chmod(0o755)
        for filename in ("pyproject.toml", "uv.lock"):
            (checkout / filename).write_text(
                (REPO_ROOT / filename).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        checkouts.append(checkout)

    first = subprocess.run(command, cwd=checkouts[0], env=env, check=False, capture_output=True, text=True)
    second = subprocess.run(command, cwd=checkouts[1], env=env, check=False, capture_output=True, text=True)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert first.stdout.strip() == "runner-ok"
    assert second.stdout.strip() == "runner-ok"
    assert sync_log.read_text(encoding="utf-8").splitlines() == [str(checkouts[0])]


def test_clean_python_runner_serializes_reused_dependency_sync(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    sync_log = tmp_path / "uv-sync.log"
    sync_started = tmp_path / "uv-sync.started"
    host_python = repr(sys.executable)
    fake_uv = fake_bin / "uv"
    fake_uv.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "if [[ \"${1:-}\" != \"sync\" ]]; then\n"
        "  echo \"fake uv only supports sync\" >&2\n"
        "  exit 64\n"
        "fi\n"
        "printf 'sync-start\\n' >>\"${MAS_TEST_SYNC_LOG}\"\n"
        "touch \"${MAS_TEST_SYNC_STARTED}\"\n"
        "sleep 0.4\n"
        "mkdir -p \"${UV_PROJECT_ENVIRONMENT}/bin\"\n"
        "cat >\"${UV_PROJECT_ENVIRONMENT}/bin/python\" <<'PY'\n"
        "#!/usr/bin/env python3\n"
        "import os\n"
        "import sys\n"
        f"os.execv({host_python}, [{host_python}, *sys.argv[1:]])\n"
        "PY\n"
        "chmod +x \"${UV_PROJECT_ENVIRONMENT}/bin/python\"\n"
        "printf 'sync-end\\n' >>\"${MAS_TEST_SYNC_LOG}\"\n",
        encoding="utf-8",
    )
    fake_uv.chmod(0o755)

    reuse_root = tmp_path / "shared-clean-runner"
    command = [str(REPO_ROOT / "scripts/run-python-clean.sh"), "-c", "print('runner-ok')"]
    env = _clean_runner_env(
        CI="",
        PATH=f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        MAS_CLEAN_RUNNER_REUSE_ENV="1",
        MAS_CLEAN_RUNNER_REUSE_ROOT=str(reuse_root),
        MAS_CLEAN_RUNNER_SYNC_LOCK_TIMEOUT_SECONDS="30",
        MAS_CLEAN_RUNNER_SYNC_LOCK_POLL_SECONDS="0.05",
        MAS_TEST_SYNC_LOG=str(sync_log),
        MAS_TEST_SYNC_STARTED=str(sync_started),
        PYTHONPATH="",
    )

    first = subprocess.Popen(command, cwd=REPO_ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 5
        while not sync_started.exists():
            if first.poll() is not None:
                stdout, stderr = first.communicate()
                raise AssertionError(f"first runner exited before sync started: {stdout=} {stderr=}")
            if time.monotonic() > deadline:
                first.kill()
                stdout, stderr = first.communicate()
                raise AssertionError(f"timed out waiting for fake uv sync start: {stdout=} {stderr=}")
            time.sleep(0.02)

        second = subprocess.Popen(
            command,
            cwd=REPO_ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        second_stdout, second_stderr = second.communicate(timeout=10)
        first_stdout, first_stderr = first.communicate(timeout=10)
    finally:
        if first.poll() is None:
            first.kill()
            first.communicate()

    assert first.returncode == 0, first_stderr
    assert second.returncode == 0, second_stderr
    assert first_stdout.strip() == "runner-ok"
    assert second_stdout.strip() == "runner-ok"
    assert sync_log.read_text(encoding="utf-8").splitlines() == ["sync-start", "sync-end"]
    assert not (reuse_root / "uv-sync.done.lock").exists()


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
