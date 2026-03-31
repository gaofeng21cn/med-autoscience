from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

import med_autoscience.python_environment_contract as contract
from med_autoscience.python_environment_contract import (
    REQUIRED_RUNTIME_MODULES,
    REQUIRED_RUNTIME_REQUIREMENTS,
    ensure_python_environment_contract,
    inspect_python_environment_contract,
)


def test_required_modules_match_default_rule_set() -> None:
    assert REQUIRED_RUNTIME_MODULES == ("matplotlib", "pandas")
    assert REQUIRED_RUNTIME_REQUIREMENTS == ("matplotlib>=3.9", "pandas>=2.2")


def test_inspect_reports_missing_modules(monkeypatch) -> None:
    original_import_module = contract.importlib.import_module

    def failing_import_module(name, package=None):
        if name in REQUIRED_RUNTIME_MODULES:
            raise ImportError(f"Simulated missing module {name}")
        return original_import_module(name, package)

    monkeypatch.setattr(contract.importlib, "import_module", failing_import_module)
    environment = inspect_python_environment_contract()

    assert environment["ready"] is False
    for module in REQUIRED_RUNTIME_MODULES:
        check_name = f"{module}_importable"
        assert environment["checks"][check_name] is False
        assert environment["modules"][module]["version"] is None
    assert environment["missing_requirements"] == list(REQUIRED_RUNTIME_REQUIREMENTS)


def test_inspect_reports_version_mismatch(monkeypatch) -> None:
    def fake_module(name: str) -> SimpleNamespace:
        version_str = "3.8.0" if name == "matplotlib" else "2.1.0"
        return SimpleNamespace(__version__=version_str)

    monkeypatch.setattr(contract.importlib, "import_module", lambda name, package=None: fake_module(name))
    environment = inspect_python_environment_contract()

    assert environment["ready"] is False
    assert environment["checks"]["matplotlib_version_satisfied"] is False
    assert environment["checks"]["pandas_version_satisfied"] is False
    assert environment["missing_requirements"] == list(REQUIRED_RUNTIME_REQUIREMENTS)


def test_ensure_indicates_already_ready(monkeypatch) -> None:
    ready_state = {
        "ready": True,
        "checks": {f"{REQUIRED_RUNTIME_MODULES[0]}_importable": True},
        "issues": [],
        "modules": {},
        "interpreter": "/usr/bin/python",
        "requirements": list(REQUIRED_RUNTIME_REQUIREMENTS),
        "missing_requirements": [],
    }

    monkeypatch.setattr(contract, "inspect_python_environment_contract", lambda **kwargs: ready_state)
    monkeypatch.setattr(contract, "_is_managed_runtime", lambda: True)
    result = ensure_python_environment_contract()

    assert result["action"] == "already_ready"
    assert result["before"] == ready_state
    assert result["after"] == ready_state


def test_ensure_external_runtime_reports_managed_requirement(tmp_path) -> None:
    external_venv = tmp_path / "external"
    subprocess.run([sys.executable, "-m", "venv", str(external_venv)], check=True)
    bin_dir = "Scripts" if os.name == "nt" else "bin"
    python_exe = external_venv / bin_dir / ("python.exe" if os.name == "nt" else "python")

    script = """
import json
from med_autoscience.python_environment_contract import ensure_python_environment_contract
print(json.dumps(ensure_python_environment_contract()))
"""

    env = os.environ.copy()
    site_paths = [
        contract.MANAGED_RUNTIME_PREFIX / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages",
        contract.MANAGED_RUNTIME_PREFIX / "Lib" / "site-packages",
    ]
    effective_paths = [str(REPO_ROOT / "src")] + [str(path) for path in site_paths if path.exists()]
    env["PYTHONPATH"] = os.pathsep.join(effective_paths)
    completed = subprocess.run(
        [str(python_exe), "-c", script],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    result = json.loads(completed.stdout.strip())
    assert result["action"] == "managed_runtime_required"
    assert result["after"] == result["before"]
    assert ".venv" in result["stderr"]
    assert "rtk uv run" in result["stderr"]


def test_ensure_runs_uv_pip_install_when_missing(monkeypatch) -> None:
    before_state = {
        "ready": False,
        "checks": {f"{REQUIRED_RUNTIME_MODULES[0]}_importable": False},
        "issues": ["python_environment.sample_missing"],
        "modules": {REQUIRED_RUNTIME_MODULES[0]: {"version": None}},
        "interpreter": "/usr/bin/python",
        "requirements": list(REQUIRED_RUNTIME_REQUIREMENTS),
        "missing_requirements": list(REQUIRED_RUNTIME_REQUIREMENTS),
    }
    after_state = {
        "ready": True,
        "checks": {f"{REQUIRED_RUNTIME_MODULES[0]}_importable": True},
        "issues": [],
        "modules": {REQUIRED_RUNTIME_MODULES[0]: {"version": "2.2.0"}},
        "interpreter": "/usr/bin/python",
        "requirements": list(REQUIRED_RUNTIME_REQUIREMENTS),
        "missing_requirements": [],
    }

    class Inspector:
        def __init__(self) -> None:
            self.calls = 0

        def __call__(self, **kwargs) -> dict[str, object]:
            self.calls += 1
            return before_state if self.calls == 1 else after_state

    inspector = Inspector()
    monkeypatch.setattr(contract, "inspect_python_environment_contract", inspector)
    monkeypatch.setattr(contract, "_is_managed_runtime", lambda: True)
    fake_completed = SimpleNamespace(returncode=17, stdout="sync-out", stderr="sync-err")
    recorded: dict[str, object] = {}

    def fake_run(*args, **kwargs):
        recorded["args"] = args
        recorded["kwargs"] = kwargs
        return fake_completed

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = ensure_python_environment_contract()

    assert result["action"] == "uv_pip_install"
    assert result["before"] == before_state
    assert result["after"] == after_state
    assert result["exit_code"] == 17
    assert result["stdout"] == "sync-out"
    assert result["stderr"] == "sync-err"
    assert recorded["args"] == (
        ["uv", "pip", "install", "--python", sys.executable, *REQUIRED_RUNTIME_REQUIREMENTS],
    )
    assert recorded["kwargs"]["cwd"] == contract.REPO_ROOT
    assert recorded["kwargs"]["capture_output"] is True
    assert recorded["kwargs"]["text"] is True
    assert recorded["kwargs"]["check"] is False


def test_ensure_ready_external_runtime_reports_managed_requirement(monkeypatch) -> None:
    ready_state = {
        "ready": True,
        "checks": {f"{REQUIRED_RUNTIME_MODULES[0]}_importable": True},
        "issues": [],
        "modules": {},
        "interpreter": "/usr/bin/python",
        "requirements": list(REQUIRED_RUNTIME_REQUIREMENTS),
        "missing_requirements": [],
    }

    monkeypatch.setattr(contract, "inspect_python_environment_contract", lambda **kwargs: ready_state)
    monkeypatch.setattr(contract, "_is_managed_runtime", lambda: False)

    result = ensure_python_environment_contract()

    assert result["action"] == "managed_runtime_required"
    assert result["before"] == ready_state
    assert result["after"] == ready_state
