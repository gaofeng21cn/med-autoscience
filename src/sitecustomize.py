from __future__ import annotations

import os
from pathlib import Path
import sys


def _is_mas_repo_root(path: Path) -> bool:
    return (path / "pyproject.toml").is_file() and (path / "src" / "med_autoscience").is_dir()


def _mas_workspace_root(path: Path) -> Path | None:
    if (path / "ops" / "medautoscience").is_dir() and (path / "runtime").is_dir():
        return path
    return None


def _mas_quest_root(path: Path) -> Path | None:
    ds_root = path / ".ds"
    if not ds_root.is_dir():
        return None
    if (ds_root / "runtime_state.json").is_file() or (ds_root / "runs").is_dir() or (path / "quest.yaml").is_file():
        return path
    return None


def _set_pycache_prefix(cache_root: Path) -> None:
    cache_root.mkdir(parents=True, exist_ok=True)
    value = str(cache_root)
    os.environ["PYTHONPYCACHEPREFIX"] = value
    sys.pycache_prefix = value


def _configure_mas_runtime_pycache() -> None:
    if os.environ.get("PYTHONPYCACHEPREFIX") or os.environ.get("PYTHONDONTWRITEBYTECODE"):
        return
    try:
        cwd = Path.cwd().resolve()
    except OSError:
        return
    if _is_mas_repo_root(cwd):
        sys.dont_write_bytecode = True
        return
    workspace_root = _mas_workspace_root(cwd)
    if workspace_root is not None:
        _set_pycache_prefix(workspace_root / "ops" / "medautoscience" / "python_pycache")
        return
    quest_root = _mas_quest_root(cwd)
    if quest_root is None:
        return
    _set_pycache_prefix(quest_root / ".ds" / "python_pycache")


_configure_mas_runtime_pycache()
