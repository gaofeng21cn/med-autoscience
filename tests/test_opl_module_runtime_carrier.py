from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.family


def _carrier_env(tmp_path: Path) -> dict[str, str]:
    runtime_root = tmp_path / "runtime"
    cache_root = tmp_path / "cache"
    python_bin = runtime_root / "venv" / "bin" / "python"
    python_bin.parent.mkdir(parents=True)
    python_bin.symlink_to(sys.executable)
    return {
        **os.environ,
        "MAS_OPL_MODULE_RUNTIME_ROOT": str(runtime_root),
        "MAS_OPL_MODULE_CACHE_ROOT": str(cache_root),
    }


def _run_healthcheck(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "scripts/opl-module-healthcheck.sh", *args],
        cwd=REPO_ROOT,
        env=_carrier_env(tmp_path),
        text=True,
        capture_output=True,
        check=False,
    )


def test_domain_handler_probe_calls_canonical_read_only_target(tmp_path: Path) -> None:
    before = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    completed = _run_healthcheck(tmp_path, "--probe")
    after = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload == {
        "domain_handler_target": "med_autoscience.domain_entry:MedAutoScienceDomainEntry.dispatch",
        "domain_mutation": False,
        "module_id": "medautoscience",
        "ok": True,
        "probe_command": "mainline-status",
        "probe_effect": "read_only",
        "surface_kind": "opl_module_domain_handler_probe",
    }
    assert after == before


def test_module_healthcheck_includes_live_domain_handler_probe(tmp_path: Path) -> None:
    completed = _run_healthcheck(tmp_path)

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["surface_kind"] == "opl_module_runtime_source_healthcheck"
    assert payload["checks"]["domain_handler_probe"]["probe_effect"] == "read_only"
    assert payload["checks"]["domain_handler_probe"]["domain_mutation"] is False
    assert payload["checks"]["repo_cli"] == "retired"


def test_module_healthcheck_help_is_diagnostic_only() -> None:
    completed = subprocess.run(
        ["bash", "scripts/opl-module-healthcheck.sh", "--help"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "MedAutoScienceDomainEntry.dispatch" in completed.stdout
    assert "--probe" in completed.stdout


def test_bootstrap_routes_environment_and_cache_outside_checkout(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    uv_log = tmp_path / "uv-log.json"
    fake_uv = fake_bin / "uv"
    fake_uv.write_text(
        """#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys

environment = Path(os.environ["UV_PROJECT_ENVIRONMENT"])
(environment / "bin").mkdir(parents=True, exist_ok=True)
(environment / "bin" / "python").symlink_to(os.environ["MAS_TEST_PYTHON"])
Path(os.environ["MAS_TEST_UV_LOG"]).write_text(json.dumps({
    "args": sys.argv[1:],
    "environment": str(environment),
    "cache": os.environ["UV_CACHE_DIR"],
    "pycache": os.environ["PYTHONPYCACHEPREFIX"],
}), encoding="utf-8")
""",
        encoding="utf-8",
    )
    fake_uv.chmod(0o755)
    runtime_root = tmp_path / "state" / "mas"
    cache_root = tmp_path / "cache" / "mas"
    completed = subprocess.run(
        ["bash", "scripts/opl-module-bootstrap.sh"],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PATH": f"{fake_bin}:{os.environ['PATH']}",
            "MAS_OPL_MODULE_RUNTIME_ROOT": str(runtime_root),
            "MAS_OPL_MODULE_CACHE_ROOT": str(cache_root),
            "MAS_TEST_PYTHON": sys.executable,
            "MAS_TEST_UV_LOG": str(uv_log),
        },
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    invocation = json.loads(uv_log.read_text(encoding="utf-8"))
    assert invocation["args"] == ["sync", "--frozen", "--no-install-project", "--no-dev"]
    for field in ("environment", "cache", "pycache"):
        assert not Path(invocation[field]).is_relative_to(REPO_ROOT)
    payload = json.loads(completed.stdout)
    assert payload["environment_owner"] == "opl_base"
    assert payload["source_checkout_mutation"] is False


def test_bootstrap_rejects_state_inside_source_checkout(tmp_path: Path) -> None:
    completed = subprocess.run(
        ["bash", "scripts/opl-module-bootstrap.sh"],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "MAS_OPL_MODULE_RUNTIME_ROOT": str(REPO_ROOT / ".forbidden-runtime"),
            "MAS_OPL_MODULE_CACHE_ROOT": str(tmp_path / "cache"),
        },
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 2
    assert "must be outside the source checkout" in completed.stderr
    assert not (REPO_ROOT / ".forbidden-runtime").exists()
