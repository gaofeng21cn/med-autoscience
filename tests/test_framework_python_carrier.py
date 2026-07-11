from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_framework_python_carrier_is_not_an_agent_dependency() -> None:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    lock_text = (REPO_ROOT / "uv.lock").read_text(encoding="utf-8")

    assert not any("one-person-lab.git" in item for item in pyproject["project"]["dependencies"])
    assert "one-person-lab.git" not in lock_text


def test_package_import_does_not_mutate_import_paths_or_preload_shared_modules() -> None:
    script = """
import json
import sys

before_path = list(sys.path)
before_framework = sorted(name for name in sys.modules if name == "opl_framework" or name.startswith("opl_framework."))
import med_autoscience
after_framework = sorted(name for name in sys.modules if name == "opl_framework" or name.startswith("opl_framework."))
print(json.dumps({
    "path_unchanged": sys.path == before_path,
    "framework_before": before_framework,
    "framework_after": after_framework,
    "package_path": list(med_autoscience.__path__),
}))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["path_unchanged"] is True
    assert payload["framework_after"] == payload["framework_before"]
    assert payload["package_path"] == [str(REPO_ROOT / "src" / "med_autoscience")]


def test_runtime_bootstrap_modules_are_physically_retired() -> None:
    package_root = REPO_ROOT / "src" / "med_autoscience"

    assert not (package_root / "framework_python_carrier.py").exists()
    assert not (package_root / "family_shared_release.py").exists()

    for relative_path in (
        "src/med_autoscience/__init__.py",
        "src/med_autoscience/domain_entry.py",
        "src/med_autoscience/domain_entry_contract.py",
    ):
        source = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert "framework_python_carrier" not in source
        assert "sys.path" not in source
        assert "sys.modules" not in source
