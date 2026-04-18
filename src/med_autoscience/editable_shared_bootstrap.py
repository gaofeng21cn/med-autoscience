from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path


_SHARED_PACKAGE_NAME = "opl_harness_shared"


def _module_spec(module_name: str):
    try:
        return importlib.util.find_spec(module_name)
    except ModuleNotFoundError:
        return None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _candidate_shared_src_roots() -> tuple[Path, ...]:
    repo_root = _repo_root()
    return (
        repo_root.parent / "one-person-lab" / "python" / "opl-harness-shared" / "src",
    )


def _candidate_repo_site_packages_roots() -> tuple[Path, ...]:
    repo_root = _repo_root()
    venv_root = repo_root / ".venv"
    versioned_site_packages = (
        venv_root / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
    )
    windows_site_packages = venv_root / "Lib" / "site-packages"
    return (
        versioned_site_packages,
        windows_site_packages,
    )


def _prepend_path(candidate_root: Path) -> bool:
    if not candidate_root.exists():
        return False
    candidate_root_str = str(candidate_root)
    if candidate_root_str in sys.path:
        return False
    sys.path.insert(0, candidate_root_str)
    importlib.invalidate_caches()
    return True


def _prefer_existing_package_path(candidate_root: Path) -> None:
    package = sys.modules.get(_SHARED_PACKAGE_NAME)
    if package is None or not hasattr(package, "__path__"):
        return
    package_root = str(candidate_root / _SHARED_PACKAGE_NAME)
    existing = [entry for entry in package.__path__ if entry != package_root]
    package.__path__[:] = [package_root, *existing]


def ensure_editable_dependency_paths() -> tuple[Path, ...]:
    added_paths: list[Path] = []
    for candidate_root in _candidate_shared_src_roots():
        if not (candidate_root / _SHARED_PACKAGE_NAME).exists():
            continue
        inserted = _prepend_path(candidate_root)
        _prefer_existing_package_path(candidate_root)
        if _module_spec(_SHARED_PACKAGE_NAME) is not None:
            if inserted:
                added_paths.append(candidate_root)
            return tuple(added_paths)

    for candidate_root in _candidate_repo_site_packages_roots():
        if _prepend_path(candidate_root):
            added_paths.append(candidate_root)

    if _module_spec(_SHARED_PACKAGE_NAME) is not None:
        return tuple(added_paths)
    return tuple(added_paths)
