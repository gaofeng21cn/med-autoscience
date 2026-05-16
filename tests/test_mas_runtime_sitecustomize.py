from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
import tempfile


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_sitecustomize_routes_mas_quest_cwd_pycache_to_quest_runtime(tmp_path: Path) -> None:
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-001"
    (quest_root / ".ds").mkdir(parents=True)
    (quest_root / ".ds" / "runtime_state.json").write_text("{}", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-c", "import os, sys; print(sys.pycache_prefix or ''); print(os.environ.get('PYTHONPYCACHEPREFIX') or '')"],
        cwd=quest_root,
        env=_sitecustomize_env(tmp_path),
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout.splitlines() == [
        str(quest_root / ".ds" / "python_pycache"),
        str(quest_root / ".ds" / "python_pycache"),
    ]


def test_sitecustomize_routes_mas_workspace_cwd_pycache_to_workspace_ops(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    (workspace_root / "ops" / "medautoscience").mkdir(parents=True)
    (workspace_root / "runtime").mkdir()

    result = subprocess.run(
        [sys.executable, "-c", "import os, sys; print(sys.pycache_prefix or ''); print(os.environ.get('PYTHONPYCACHEPREFIX') or '')"],
        cwd=workspace_root,
        env=_sitecustomize_env(tmp_path),
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout.splitlines() == [
        str(workspace_root / "ops" / "medautoscience" / "python_pycache"),
        str(workspace_root / "ops" / "medautoscience" / "python_pycache"),
    ]


def test_sitecustomize_routes_repo_root_caches_to_temp_root(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import os, pathlib, sys; "
                "print(sys.pycache_prefix or ''); "
                "print(os.environ.get('PYTHONPYCACHEPREFIX') or ''); "
                "print(os.environ.get('PYTEST_ADDOPTS') or '')"
            ),
        ],
        cwd=REPO_ROOT,
        env=_sitecustomize_env(tmp_path),
        text=True,
        capture_output=True,
        check=True,
    )

    lines = result.stdout.splitlines()
    assert lines[0] == lines[1]
    assert lines[0].startswith(str(Path(tempfile.gettempdir()) / "mas-python-cache"))
    assert str(REPO_ROOT) not in lines[0]
    assert "-o cache_dir=" in lines[2]
    assert str(REPO_ROOT) not in lines[2]


def test_sitecustomize_prevents_repo_cache_when_direct_pytest_is_used(tmp_path: Path) -> None:
    shutil.rmtree(REPO_ROOT / ".pytest_cache", ignore_errors=True)
    shutil.rmtree(REPO_ROOT / "src" / "med_autoscience" / "__pycache__", ignore_errors=True)

    probe_test = tmp_path / "probe_test.py"
    probe_test.write_text(
        "def test_import_mas_runtime_surface():\n"
        "    import med_autoscience.controllers.runtime_watch\n"
        "    assert True\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(probe_test)],
        cwd=REPO_ROOT,
        env=_sitecustomize_env(tmp_path, pythonpath=REPO_ROOT / "src"),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert not (REPO_ROOT / ".pytest_cache").exists()
    assert not (REPO_ROOT / "src" / "med_autoscience" / "__pycache__").exists()


def test_sitecustomize_prevents_repo_source_pycache_when_importing_from_quest_cwd(tmp_path: Path) -> None:
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-001"
    (quest_root / ".ds").mkdir(parents=True)
    (quest_root / ".ds" / "runtime_state.json").write_text("{}", encoding="utf-8")
    source_root = tmp_path / "editable-src"
    package_root = source_root / "sample_package"
    package_root.mkdir(parents=True)
    (package_root / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-c", "import sample_package; print(sample_package.VALUE)"],
        cwd=quest_root,
        env=_sitecustomize_env(tmp_path, pythonpath=source_root),
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout.strip() == "1"
    assert not (package_root / "__pycache__").exists()
    pycache_files = list((quest_root / ".ds" / "python_pycache").rglob("*.pyc"))
    assert pycache_files


def test_sitecustomize_does_not_change_non_quest_cwd_pycache(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import sys; print(sys.pycache_prefix or '')"],
        cwd=tmp_path,
        env=_sitecustomize_env(tmp_path),
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout.strip() == ""


def _sitecustomize_env(tmp_path: Path, *, pythonpath: Path | None = None) -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("PYTHONDONTWRITEBYTECODE", None)
    env.pop("PYTHONPYCACHEPREFIX", None)
    sitecustomize_root = tmp_path / "sitecustomize-src"
    sitecustomize_root.mkdir()
    shutil.copy2(REPO_ROOT / "src" / "sitecustomize.py", sitecustomize_root / "sitecustomize.py")
    paths = [str(sitecustomize_root)]
    if pythonpath is not None:
        paths.append(str(pythonpath))
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env
