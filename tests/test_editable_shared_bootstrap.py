from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

from med_autoscience import editable_shared_bootstrap as module


def test_bootstrap_adds_repo_venv_site_packages_when_shared_helper_imports_from_site_packages(
    monkeypatch,
    tmp_path: Path,
) -> None:
    fake_site_packages = tmp_path / ".venv" / "lib" / "python3.12" / "site-packages"
    fake_site_packages.mkdir(parents=True)
    fake_site_packages_str = str(fake_site_packages)
    original_sys_path = list(sys.path)
    sys.path[:] = [item for item in sys.path if item != fake_site_packages_str]
    imported_module_names: list[str] = []
    helper_module = types.SimpleNamespace(
        ensure_consumer_editable_dependency_paths=lambda **_: (),
    )

    def fake_module_spec(module_name: str):
        if module_name != "opl_harness_shared.editable_consumer_bootstrap":
            return importlib.util.find_spec(module_name)
        if fake_site_packages_str not in sys.path:
            return None
        return object()

    monkeypatch.setattr(module, "_candidate_repo_site_packages_roots", lambda: (fake_site_packages,))
    monkeypatch.setattr(module, "_candidate_shared_helper_module_paths", lambda: ())
    monkeypatch.setattr(module, "_module_spec", fake_module_spec)
    monkeypatch.setattr(
        module.importlib,
        "import_module",
        lambda module_name: imported_module_names.append(module_name) or helper_module,
    )

    try:
        added = module.ensure_editable_dependency_paths()
    finally:
        sys.path[:] = original_sys_path

    assert added == (fake_site_packages,)
    assert imported_module_names == ["opl_harness_shared.editable_consumer_bootstrap"]


def test_bootstrap_delegates_to_shared_helper_when_sibling_owner_is_present(monkeypatch, tmp_path: Path) -> None:
    fake_repo_root = tmp_path / "med-autoscience"
    fake_repo_root.mkdir()
    helper_path = (
        tmp_path
        / "one-person-lab"
        / "python"
        / "opl-harness-shared"
        / "src"
        / "opl_harness_shared"
        / "editable_consumer_bootstrap.py"
    )
    helper_path.parent.mkdir(parents=True)
    helper_path.write_text(
        "from pathlib import Path\n"
        "def ensure_consumer_editable_dependency_paths(*, repo_root, shared_package_name='opl_harness_shared'):\n"
        "    marker = Path(repo_root) / 'shared-helper-called.txt'\n"
        "    marker.write_text(shared_package_name, encoding='utf-8')\n"
        "    return (Path(repo_root) / 'delegated-src',)\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "_repo_root", lambda: fake_repo_root)
    monkeypatch.setattr(module, "_candidate_repo_site_packages_roots", lambda: ())
    monkeypatch.setattr(module, "_module_spec", lambda module_name: None)

    added = module.ensure_editable_dependency_paths()

    assert added == (fake_repo_root / "delegated-src",)
    assert (fake_repo_root / "shared-helper-called.txt").read_text(encoding="utf-8") == "opl_harness_shared"


def test_bootstrap_delegates_to_importable_shared_helper_without_touching_sys_path(monkeypatch) -> None:
    original_sys_path = list(sys.path)
    imported_module_names: list[str] = []
    helper_module = types.SimpleNamespace(
        ensure_consumer_editable_dependency_paths=lambda **_: (),
    )
    monkeypatch.setattr(
        module,
        "_module_spec",
        lambda module_name: object() if module_name == "opl_harness_shared.editable_consumer_bootstrap" else None,
    )
    monkeypatch.setattr(module, "_candidate_repo_site_packages_roots", lambda: ())
    monkeypatch.setattr(
        module.importlib,
        "import_module",
        lambda module_name: imported_module_names.append(module_name) or helper_module,
    )

    try:
        added = module.ensure_editable_dependency_paths()
    finally:
        sys.path[:] = original_sys_path

    assert added == ()
    assert sys.path == original_sys_path
    assert imported_module_names == ["opl_harness_shared.editable_consumer_bootstrap"]


def test_bootstrap_returns_added_site_packages_when_shared_helper_remains_unavailable(
    monkeypatch,
    tmp_path: Path,
) -> None:
    fake_site_packages = tmp_path / ".venv" / "lib" / "python3.12" / "site-packages"
    fake_site_packages.mkdir(parents=True)
    fake_site_packages_str = str(fake_site_packages)
    original_sys_path = list(sys.path)
    sys.path[:] = [item for item in sys.path if item != fake_site_packages_str]

    monkeypatch.setattr(module, "_candidate_repo_site_packages_roots", lambda: (fake_site_packages,))
    monkeypatch.setattr(module, "_candidate_shared_helper_module_paths", lambda: ())
    monkeypatch.setattr(module, "_module_spec", lambda module_name: None)

    try:
        added = module.ensure_editable_dependency_paths()
    finally:
        sys.path[:] = original_sys_path

    assert added == (fake_site_packages,)
