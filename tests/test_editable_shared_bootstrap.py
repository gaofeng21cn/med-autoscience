from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_shared_dependency_uses_standard_locked_packaging() -> None:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependency = next(
        item for item in pyproject["project"]["dependencies"] if item.startswith("opl-harness-shared ")
    )
    lock_text = (REPO_ROOT / "uv.lock").read_text(encoding="utf-8")

    assert "git+https://github.com/gaofeng21cn/one-person-lab.git@" in dependency
    assert "#subdirectory=python/opl-harness-shared" in dependency
    assert 'name = "opl-harness-shared"' in lock_text
    assert "subdirectory=python%2Fopl-harness-shared&rev=" in lock_text


def test_package_import_does_not_mutate_import_paths_or_preload_shared_modules() -> None:
    script = """
import json
import sys

before_path = list(sys.path)
before_shared = sorted(name for name in sys.modules if name == "opl_harness_shared" or name.startswith("opl_harness_shared."))
import med_autoscience
after_shared = sorted(name for name in sys.modules if name == "opl_harness_shared" or name.startswith("opl_harness_shared."))
print(json.dumps({
    "path_unchanged": sys.path == before_path,
    "shared_before": before_shared,
    "shared_after": after_shared,
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
    assert payload["shared_after"] == payload["shared_before"]
    assert payload["package_path"] == [str(REPO_ROOT / "src" / "med_autoscience")]


def test_runtime_bootstrap_modules_are_physically_retired() -> None:
    package_root = REPO_ROOT / "src" / "med_autoscience"

    assert not (package_root / "editable_shared_bootstrap.py").exists()
    assert not (package_root / "family_shared_release.py").exists()

    for relative_path in (
        "src/med_autoscience/__init__.py",
        "src/med_autoscience/domain_entry.py",
        "src/med_autoscience/domain_entry_contract.py",
    ):
        source = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert "editable_shared_bootstrap" not in source
        assert "sys.path" not in source
        assert "sys.modules" not in source
