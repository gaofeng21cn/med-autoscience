from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys
import tempfile


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


def _repo_cache_root(repo_root: Path) -> Path:
    digest = hashlib.sha256(str(repo_root).encode("utf-8")).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / "mas-python-cache" / digest


def _mas_repo_root_from_import_path() -> Path | None:
    for raw_entry in sys.path:
        if not raw_entry:
            continue
        try:
            entry = Path(raw_entry).expanduser().resolve()
        except OSError:
            continue
        if entry.name == "src" and (entry / "med_autoscience").is_dir():
            repo_root = entry.parent
            if _is_mas_repo_root(repo_root):
                return repo_root
        if _is_mas_repo_root(entry):
            return entry
    return None


def _set_pytest_cache_dir(cache_dir: Path) -> None:
    existing = os.environ.get("PYTEST_ADDOPTS", "")
    if "cache_dir" in existing:
        return
    value = f"-o cache_dir={cache_dir}"
    os.environ["PYTEST_ADDOPTS"] = f"{existing} {value}".strip()


def _path_is_inside(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return True


def _existing_pycache_prefix_is_checkout_local(repo_root: Path) -> bool:
    existing = os.environ.get("PYTHONPYCACHEPREFIX")
    if not existing:
        return False
    try:
        existing_path = Path(existing).expanduser().resolve()
    except OSError:
        return False
    return existing_path == repo_root or _path_is_inside(existing_path, repo_root)


def _remove_empty_checkout_pycache_prefix(repo_root: Path) -> None:
    existing = os.environ.get("PYTHONPYCACHEPREFIX")
    if not existing:
        return
    try:
        existing_path = Path(existing).expanduser().resolve()
    except OSError:
        return
    if existing_path == repo_root or not _path_is_inside(existing_path, repo_root):
        return
    if existing_path.is_dir():
        try:
            directories = sorted(
                (path for path in existing_path.rglob("*") if path.is_dir()),
                key=lambda path: len(path.parts),
                reverse=True,
            )
        except OSError:
            directories = []
        for directory in directories:
            try:
                directory.rmdir()
            except OSError:
                pass
    try:
        existing_path.rmdir()
    except OSError:
        return


def _configure_mas_runtime_pycache() -> None:
    existing_pycache_prefix = os.environ.get("PYTHONPYCACHEPREFIX")
    if existing_pycache_prefix:
        repo_root = _mas_repo_root_from_import_path()
        if repo_root is None:
            try:
                cwd = Path.cwd().resolve()
            except OSError:
                cwd = None
            if cwd is not None and _is_mas_repo_root(cwd):
                repo_root = cwd
        if repo_root is None or not _existing_pycache_prefix_is_checkout_local(repo_root):
            return
        _remove_empty_checkout_pycache_prefix(repo_root)
        os.environ.pop("PYTHONPYCACHEPREFIX", None)
        sys.pycache_prefix = None

    if os.environ.get("PYTHONPYCACHEPREFIX"):
        return
    try:
        cwd = Path.cwd().resolve()
    except OSError:
        return
    if _is_mas_repo_root(cwd):
        cache_root = _repo_cache_root(cwd)
        _set_pycache_prefix(cache_root / "pycache")
        _set_pytest_cache_dir(cache_root / "pytest-cache")
        return
    workspace_root = _mas_workspace_root(cwd)
    if workspace_root is not None:
        _set_pycache_prefix(workspace_root / "ops" / "medautoscience" / "python_pycache")
        return
    quest_root = _mas_quest_root(cwd)
    if quest_root is None:
        repo_root = _mas_repo_root_from_import_path()
        if repo_root is None:
            return
        cache_root = _repo_cache_root(repo_root)
        _set_pycache_prefix(cache_root / "pycache")
        _set_pytest_cache_dir(cache_root / "pytest-cache")
        return
    _set_pycache_prefix(quest_root / ".ds" / "python_pycache")


_configure_mas_runtime_pycache()
