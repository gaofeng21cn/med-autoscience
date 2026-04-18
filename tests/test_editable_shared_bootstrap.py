from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from med_autoscience import editable_shared_bootstrap as module


def test_bootstrap_adds_repo_venv_site_packages_when_present(monkeypatch, tmp_path: Path) -> None:
    fake_site_packages = tmp_path / ".venv" / "lib" / "python3.12" / "site-packages"
    fake_site_packages.mkdir(parents=True)
    fake_site_packages_str = str(fake_site_packages)
    original_sys_path = list(sys.path)
    sys.path[:] = [item for item in sys.path if item != fake_site_packages_str]

    def fake_module_spec(module_name: str):
        if module_name != "opl_harness_shared":
            return importlib.util.find_spec(module_name)
        if fake_site_packages_str not in sys.path:
            return None
        return object()

    monkeypatch.setattr(module, "_candidate_repo_site_packages_roots", lambda: (fake_site_packages,))
    monkeypatch.setattr(module, "_module_spec", fake_module_spec)

    try:
        added = module.ensure_editable_dependency_paths()
    finally:
        sys.path[:] = original_sys_path

    assert added == (fake_site_packages,)


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
        / "editable_dependency_bootstrap.py"
    )
    helper_path.parent.mkdir(parents=True)
    helper_path.write_text(
        "from pathlib import Path\n"
        "def ensure_editable_dependency_paths(*, repo_root, shared_package_name='opl_harness_shared'):\n"
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


def test_bootstrap_is_noop_when_shared_package_is_already_importable(monkeypatch) -> None:
    original_sys_path = list(sys.path)
    monkeypatch.setattr(module, "_module_spec", lambda module_name: object() if module_name == "opl_harness_shared" else None)
    monkeypatch.setattr(module, "_candidate_repo_site_packages_roots", lambda: ())

    try:
        added = module.ensure_editable_dependency_paths()
    finally:
        sys.path[:] = original_sys_path

    assert added == ()
    assert sys.path == original_sys_path
