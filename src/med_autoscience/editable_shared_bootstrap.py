from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path


_SHARED_HELPER_MODULE_NAME = "opl_harness_shared.editable_consumer_bootstrap"
_SHARED_PACKAGE_NAME = "opl_harness_shared"
_SHARED_BOOTSTRAP_MODULE_FILE = "editable_consumer_bootstrap.py"


def _module_spec(module_name: str):
    try:
        return importlib.util.find_spec(module_name)
    except ModuleNotFoundError:
        return None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


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


def _candidate_shared_helper_module_paths() -> tuple[Path, ...]:
    repo_root = _repo_root()
    return (
        repo_root.parent
        / "one-person-lab"
        / "python"
        / "opl-harness-shared"
        / "src"
        / _SHARED_PACKAGE_NAME
        / _SHARED_BOOTSTRAP_MODULE_FILE,
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


def _load_shared_helper_module_from_path(helper_path: Path):
    spec = importlib.util.spec_from_file_location(
        f"{_SHARED_PACKAGE_NAME}_editable_consumer_bootstrap_{abs(hash(helper_path))}",
        helper_path,
    )
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _import_shared_helper_module():
    if _module_spec(_SHARED_HELPER_MODULE_NAME) is not None:
        return importlib.import_module(_SHARED_HELPER_MODULE_NAME)
    for helper_path in _candidate_shared_helper_module_paths():
        if helper_path.exists():
            return _load_shared_helper_module_from_path(helper_path)
    return None


def ensure_editable_dependency_paths() -> tuple[Path, ...]:
    repo_root = _repo_root()
    added_paths: list[Path] = []
    helper_module = _import_shared_helper_module()
    if helper_module is None:
        for candidate_root in _candidate_repo_site_packages_roots():
            if _prepend_path(candidate_root):
                added_paths.append(candidate_root)
        helper_module = _import_shared_helper_module()
    if helper_module is None:
        return tuple(added_paths)

    ensure_paths = getattr(helper_module, "ensure_consumer_editable_dependency_paths", None)
    if not callable(ensure_paths):
        return tuple(added_paths)

    delegated_added_paths = tuple(
        Path(entry)
        for entry in ensure_paths(
            repo_root=repo_root,
            shared_package_name=_SHARED_PACKAGE_NAME,
        )
    )
    if delegated_added_paths:
        return delegated_added_paths
    return tuple(added_paths)
