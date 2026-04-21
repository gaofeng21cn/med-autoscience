from __future__ import annotations

import importlib
import importlib.util
import sys
import types
from pathlib import Path

import pytest

from med_autoscience import editable_shared_bootstrap as module

pytestmark = pytest.mark.family


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
        ensure_repo_editable_dependency_paths=lambda **_: (),
    )

    def fake_module_spec(module_name: str):
        if module_name != "opl_harness_shared.editable_consumer_launcher":
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
    assert imported_module_names == ["opl_harness_shared.editable_consumer_launcher"]


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
        / "editable_consumer_launcher.py"
    )
    helper_path.parent.mkdir(parents=True)
    helper_path.write_text(
        "from pathlib import Path\n"
        "def ensure_repo_editable_dependency_paths(*, repo_root, shared_package_name='opl_harness_shared'):\n"
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
        ensure_repo_editable_dependency_paths=lambda **_: (),
    )
    monkeypatch.setattr(module, "_candidate_shared_helper_module_paths", lambda: ())
    monkeypatch.setattr(
        module,
        "_module_spec",
        lambda module_name: object() if module_name == "opl_harness_shared.editable_consumer_launcher" else None,
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
    assert imported_module_names == ["opl_harness_shared.editable_consumer_launcher"]


def test_bootstrap_prefers_sibling_owner_helper_over_importable_site_packages(monkeypatch, tmp_path: Path) -> None:
    fake_repo_root = tmp_path / "med-autoscience"
    fake_repo_root.mkdir()
    helper_path = (
        tmp_path
        / "one-person-lab"
        / "python"
        / "opl-harness-shared"
        / "src"
        / "opl_harness_shared"
        / "editable_consumer_launcher.py"
    )
    helper_path.parent.mkdir(parents=True)
    helper_path.write_text(
        "from pathlib import Path\n"
        "def ensure_repo_editable_dependency_paths(*, repo_root, shared_package_name='opl_harness_shared'):\n"
        "    marker = Path(repo_root) / 'preferred-sibling-helper.txt'\n"
        "    marker.write_text(shared_package_name, encoding='utf-8')\n"
        "    return ()\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "_repo_root", lambda: fake_repo_root)
    monkeypatch.setattr(module, "_candidate_repo_site_packages_roots", lambda: ())
    monkeypatch.setattr(
        module,
        "_module_spec",
        lambda module_name: object() if module_name == "opl_harness_shared.editable_consumer_launcher" else None,
    )

    added = module.ensure_editable_dependency_paths()

    assert added == (helper_path.parent.parent,)
    assert (fake_repo_root / "preferred-sibling-helper.txt").read_text(encoding="utf-8") == "opl_harness_shared"


def test_bootstrap_detects_workspace_sibling_owner_from_nested_worktree_layout(
    monkeypatch,
    tmp_path: Path,
) -> None:
    fake_repo_root = tmp_path / "med-autoscience" / ".worktrees" / "codex" / "family-release-pre-shape-mas"
    fake_repo_root.mkdir(parents=True)
    helper_path = (
        tmp_path
        / "one-person-lab"
        / "python"
        / "opl-harness-shared"
        / "src"
        / "opl_harness_shared"
        / "editable_consumer_launcher.py"
    )
    helper_path.parent.mkdir(parents=True)
    helper_path.write_text(
        "from pathlib import Path\n"
        "def ensure_repo_editable_dependency_paths(*, repo_root, shared_package_name='opl_harness_shared'):\n"
        "    marker = Path(repo_root) / 'nested-worktree-helper.txt'\n"
        "    marker.write_text(shared_package_name, encoding='utf-8')\n"
        "    return (Path(repo_root).parents[3] / 'one-person-lab' / 'python' / 'opl-harness-shared' / 'src',)\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "_repo_root", lambda: fake_repo_root)
    monkeypatch.setattr(module, "_candidate_repo_site_packages_roots", lambda: ())
    monkeypatch.setattr(module, "_module_spec", lambda module_name: None)

    added = module.ensure_editable_dependency_paths()

    assert added == (tmp_path / "one-person-lab" / "python" / "opl-harness-shared" / "src",)
    assert (fake_repo_root / "nested-worktree-helper.txt").read_text(encoding="utf-8") == "opl_harness_shared"


def test_bootstrap_makes_required_shared_entrypoints_importable_from_sibling_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    fake_repo_root = tmp_path / "med-autoscience"
    fake_repo_root.mkdir()
    shared_src = tmp_path / "one-person-lab" / "python" / "opl-harness-shared" / "src"
    package_root = shared_src / "opl_harness_shared"
    package_root.mkdir(parents=True)
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    (package_root / "editable_consumer_launcher.py").write_text(
        "import importlib\n"
        "import sys\n"
        "from pathlib import Path\n"
        "def ensure_repo_editable_dependency_paths(*, repo_root, shared_package_name='opl_harness_shared'):\n"
        "    candidate = Path(repo_root).parent / 'one-person-lab' / 'python' / 'opl-harness-shared' / 'src'\n"
        "    candidate_str = str(candidate)\n"
        "    if candidate_str not in sys.path:\n"
        "        sys.path.insert(0, candidate_str)\n"
        "        importlib.invalidate_caches()\n"
        "    bootstrap = importlib.import_module(f'{shared_package_name}.editable_consumer_bootstrap')\n"
        "    return bootstrap.ensure_consumer_editable_dependency_paths(repo_root=repo_root, shared_package_name=shared_package_name)\n",
        encoding="utf-8",
    )
    (package_root / "editable_consumer_bootstrap.py").write_text(
        "import importlib\n"
        "import sys\n"
        "from pathlib import Path\n"
        "def ensure_consumer_editable_dependency_paths(*, repo_root, shared_package_name='opl_harness_shared'):\n"
        "    candidate = Path(repo_root).parent / 'one-person-lab' / 'python' / 'opl-harness-shared' / 'src'\n"
        "    candidate_str = str(candidate)\n"
        "    if candidate_str not in sys.path:\n"
        "        sys.path.insert(0, candidate_str)\n"
        "        importlib.invalidate_caches()\n"
        "    return (candidate,)\n",
        encoding="utf-8",
    )
    (package_root / "family_entry_contracts.py").write_text(
        "SOURCE = 'family_entry_contracts'\n",
        encoding="utf-8",
    )
    (package_root / "family_shared_release.py").write_text(
        "SOURCE = 'family_shared_release'\n",
        encoding="utf-8",
    )
    (package_root / "product_entry_companions.py").write_text(
        "SOURCE = 'product_entry_companions'\n",
        encoding="utf-8",
    )
    original_sys_path = list(sys.path)
    original_modules = {
        name: sys.modules.pop(name, None)
        for name in (
            "opl_harness_shared",
            "opl_harness_shared.editable_consumer_launcher",
            "opl_harness_shared.editable_consumer_bootstrap",
            "opl_harness_shared.family_entry_contracts",
            "opl_harness_shared.family_shared_release",
            "opl_harness_shared.product_entry_companions",
        )
    }

    monkeypatch.setattr(module, "_repo_root", lambda: fake_repo_root)
    monkeypatch.setattr(module, "_candidate_repo_site_packages_roots", lambda: ())
    monkeypatch.setattr(module, "_module_spec", lambda module_name: None)

    try:
        added = module.ensure_editable_dependency_paths()
        imported_paths = {
            module_name: Path(importlib.import_module(module_name).__file__).resolve()
            for module_name in (
                "opl_harness_shared.editable_consumer_launcher",
                "opl_harness_shared.editable_consumer_bootstrap",
                "opl_harness_shared.family_entry_contracts",
                "opl_harness_shared.family_shared_release",
                "opl_harness_shared.product_entry_companions",
            )
        }
    finally:
        sys.path[:] = original_sys_path
        for module_name, original_module in original_modules.items():
            if original_module is None:
                sys.modules.pop(module_name, None)
            else:
                sys.modules[module_name] = original_module

    assert added == (shared_src,)
    assert imported_paths["opl_harness_shared.editable_consumer_launcher"] == (
        package_root / "editable_consumer_launcher.py"
    ).resolve()
    assert imported_paths["opl_harness_shared.editable_consumer_bootstrap"] == (
        package_root / "editable_consumer_bootstrap.py"
    ).resolve()
    assert imported_paths["opl_harness_shared.family_entry_contracts"] == (
        package_root / "family_entry_contracts.py"
    ).resolve()
    assert imported_paths["opl_harness_shared.family_shared_release"] == (
        package_root / "family_shared_release.py"
    ).resolve()
    assert imported_paths["opl_harness_shared.product_entry_companions"] == (
        package_root / "product_entry_companions.py"
    ).resolve()


def test_required_shared_entrypoints_are_resolvable_from_current_checkout() -> None:
    original_sys_path = list(sys.path)
    try:
        module.ensure_editable_dependency_paths()
        required_modules = (
            "opl_harness_shared.editable_consumer_bootstrap",
            "opl_harness_shared.family_entry_contracts",
            "opl_harness_shared.family_shared_release",
            "opl_harness_shared.product_entry_companions",
        )
        for module_name in required_modules:
            assert importlib.util.find_spec(module_name) is not None
            imported = importlib.import_module(module_name)
            assert getattr(imported, "__file__", None)
    finally:
        sys.path[:] = original_sys_path


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
