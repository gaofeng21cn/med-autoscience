from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path


_SHARED_HELPER_MODULE_NAME = "opl_harness_shared.editable_consumer_launcher"
_SHARED_HELPER_MODULE_FILE = "editable_consumer_launcher.py"
_SHARED_PACKAGE_NAME = "opl_harness_shared"
_REQUIRED_SHARED_MODULE_EXPORTS = {
    "opl_harness_shared.editable_consumer_bootstrap": ("ensure_consumer_editable_dependency_paths",),
    "opl_harness_shared.family_entry_contracts": ("build_family_domain_entry_contract",),
    "opl_harness_shared.family_shared_release": ("load_shared_owner_release_contract",),
    "opl_harness_shared.managed_runtime": ("read_bundled_managed_runtime_three_layer_contract",),
    "opl_harness_shared.product_entry_companions": ("build_family_product_entry_manifest",),
    "opl_harness_shared.product_entry_program_companions": ("build_clearance_lane",),
}
_REQUIRED_SHARED_CONTRACT_FILES = (
    Path("contracts") / "managed-runtime-three-layer-contract.json",
)


def _module_spec(module_name: str):
    try:
        return importlib.util.find_spec(module_name)
    except ModuleNotFoundError:
        return None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _candidate_repo_site_packages_roots() -> tuple[Path, ...]:
    repo_root = _repo_root()
    repo_roots = [repo_root]
    for ancestor in repo_root.parents:
        if ancestor.name in {".worktrees", "worktrees"}:
            main_checkout_root = ancestor.parent
            if main_checkout_root not in repo_roots:
                repo_roots.append(main_checkout_root)
            break
    roots: list[Path] = []
    for candidate_repo_root in repo_roots:
        venv_root = candidate_repo_root / ".venv"
        roots.extend(
            (
                venv_root / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages",
                venv_root / "Lib" / "site-packages",
            )
        )
    return tuple(dict.fromkeys(roots))


def _candidate_shared_src_roots() -> tuple[Path, ...]:
    repo_root = _repo_root()
    candidate_base_roots = [repo_root.parent]
    for ancestor in repo_root.parents:
        if ancestor.name in {".worktrees", "worktrees"} and ancestor.parent.parent not in candidate_base_roots:
            candidate_base_roots.append(ancestor.parent.parent)

    unique_base_roots: list[Path] = []
    for candidate in candidate_base_roots:
        if candidate not in unique_base_roots:
            unique_base_roots.append(candidate)

    return tuple(
        base_root / "one-person-lab" / "python" / "opl-harness-shared" / "src"
        for base_root in unique_base_roots
    )


def _candidate_shared_helper_module_paths() -> tuple[Path, ...]:
    return tuple(
        candidate_root / _SHARED_PACKAGE_NAME / _SHARED_HELPER_MODULE_FILE
        for candidate_root in _candidate_shared_src_roots()
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


def _path_is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _prefer_existing_package_path(candidate_root: Path) -> None:
    package = sys.modules.get(_SHARED_PACKAGE_NAME)
    if package is None or not hasattr(package, "__path__"):
        return
    package_root = str(candidate_root / _SHARED_PACKAGE_NAME)
    existing = [entry for entry in package.__path__ if entry != package_root]
    package.__path__[:] = [package_root, *existing]


def _drop_shared_root(candidate_root: Path, added_paths: list[Path]) -> None:
    candidate_root_str = str(candidate_root)
    sys.path[:] = [entry for entry in sys.path if entry != candidate_root_str]
    added_paths[:] = [entry for entry in added_paths if entry != candidate_root]
    package_root = candidate_root / _SHARED_PACKAGE_NAME
    package = sys.modules.get(_SHARED_PACKAGE_NAME)
    if package is not None and hasattr(package, "__path__"):
        package.__path__[:] = [
            entry
            for entry in package.__path__
            if not _path_is_relative_to(Path(entry), package_root)
        ]
    for module_name, imported_module in list(sys.modules.items()):
        if module_name != _SHARED_PACKAGE_NAME and not module_name.startswith(f"{_SHARED_PACKAGE_NAME}."):
            continue
        module_file = getattr(imported_module, "__file__", None)
        if module_file and _path_is_relative_to(Path(module_file), package_root):
            sys.modules.pop(module_name, None)
    importlib.invalidate_caches()


def _drop_unready_sibling_shared_roots(added_paths: list[Path]) -> None:
    for shared_src_root in _candidate_shared_src_roots():
        if shared_src_root.exists() and not _shared_contract_ready(shared_src_root):
            _drop_shared_root(shared_src_root, added_paths)


def _load_shared_helper_module_from_path(helper_path: Path):
    spec = importlib.util.spec_from_file_location(
        f"{_SHARED_PACKAGE_NAME}_editable_consumer_launcher_{abs(hash(helper_path))}",
        helper_path,
    )
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _shared_module_path(shared_src_root: Path, module_name: str) -> Path:
    module_root = shared_src_root.joinpath(*module_name.split("."))
    module_path = module_root.with_suffix(".py")
    if module_path.exists():
        return module_path
    return module_root / "__init__.py"


def _load_shared_module_from_path(shared_src_root: Path, module_name: str):
    module_path = _shared_module_path(shared_src_root, module_name)
    if not module_path.exists():
        return None
    spec_name = f"{module_name}_editable_contract_check_{abs(hash(module_path))}"
    if module_path.name == "__init__.py":
        spec = importlib.util.spec_from_file_location(
            spec_name,
            module_path,
            submodule_search_locations=[str(module_path.parent)],
        )
    else:
        spec = importlib.util.spec_from_file_location(spec_name, module_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    previous_module = sys.modules.get(spec_name)
    sys.modules[spec_name] = module
    inserted_shared_root = _prepend_path(shared_src_root)
    try:
        spec.loader.exec_module(module)
    finally:
        if previous_module is None:
            sys.modules.pop(spec_name, None)
        else:
            sys.modules[spec_name] = previous_module
        if inserted_shared_root:
            sys.path[:] = [entry for entry in sys.path if entry != str(shared_src_root)]
            importlib.invalidate_caches()
    return module


def _shared_contract_ready(shared_src_root: Path) -> bool:
    package_root = shared_src_root / _SHARED_PACKAGE_NAME
    if not (package_root / "__init__.py").exists():
        return False
    for relative_path in _REQUIRED_SHARED_CONTRACT_FILES:
        if not (package_root / relative_path).exists():
            return False
    for module_name, required_exports in _REQUIRED_SHARED_MODULE_EXPORTS.items():
        try:
            module = _load_shared_module_from_path(shared_src_root, module_name)
        except Exception:
            return False
        if module is None:
            return False
        for export_name in required_exports:
            if not hasattr(module, export_name):
                return False
    return True


def _load_sibling_shared_helper(added_paths: list[Path]):
    for helper_path in _candidate_shared_helper_module_paths():
        if not helper_path.exists():
            continue
        shared_src_root = helper_path.parent.parent
        if not _shared_contract_ready(shared_src_root):
            continue
        inserted = _prepend_path(shared_src_root)
        _prefer_existing_package_path(shared_src_root)
        if inserted:
            added_paths.append(shared_src_root)
        return _load_shared_helper_module_from_path(helper_path)
    return None


def _has_existing_sibling_shared_helper_candidate() -> bool:
    return any(helper_path.exists() for helper_path in _candidate_shared_helper_module_paths())


def _import_installed_shared_helper():
    if _module_spec(_SHARED_HELPER_MODULE_NAME) is None:
        return None
    return importlib.import_module(_SHARED_HELPER_MODULE_NAME)


def ensure_editable_dependency_paths() -> tuple[Path, ...]:
    repo_root = _repo_root()
    added_paths: list[Path] = []
    helper_module = _load_sibling_shared_helper(added_paths)
    sibling_candidate_present = _has_existing_sibling_shared_helper_candidate()
    if helper_module is None and not sibling_candidate_present:
        helper_module = _import_installed_shared_helper()
    if helper_module is None:
        for candidate_root in _candidate_repo_site_packages_roots():
            candidate_root_str = str(candidate_root)
            already_on_path = candidate_root_str in sys.path
            if _prepend_path(candidate_root):
                added_paths.append(candidate_root)
                already_on_path = True
            if already_on_path:
                helper_module = _import_installed_shared_helper()
                if helper_module is not None:
                    break
    if helper_module is None:
        return tuple(added_paths)

    ensure_paths = getattr(helper_module, "ensure_repo_editable_dependency_paths", None)
    if not callable(ensure_paths):
        return tuple(added_paths)

    delegated_added_paths = tuple(
        Path(entry)
        for entry in ensure_paths(
            repo_root=repo_root,
            shared_package_name=_SHARED_PACKAGE_NAME,
        )
    )
    delegated_paths = list(delegated_added_paths)
    _drop_unready_sibling_shared_roots(delegated_paths)
    _drop_unready_sibling_shared_roots(added_paths)
    delegated_added_paths = tuple(delegated_paths)
    if delegated_added_paths:
        return delegated_added_paths
    return tuple(added_paths)
