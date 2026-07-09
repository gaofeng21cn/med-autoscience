from __future__ import annotations

import ast
import sys
import tomllib
from pathlib import Path
from types import SimpleNamespace

from packaging.requirements import Requirement


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

import med_autoscience.python_environment_contract as contract
from med_autoscience.python_environment_contract import (
    REQUIRED_RUNTIME_MODULES,
    REQUIRED_RUNTIME_REQUIREMENTS,
    inspect_python_environment_contract,
)


def test_required_modules_match_default_rule_set() -> None:
    assert REQUIRED_RUNTIME_MODULES == ("matplotlib",)
    assert REQUIRED_RUNTIME_REQUIREMENTS == ("matplotlib>=3.9",)


def test_runtime_contract_uses_only_stdlib_for_requirement_inspection() -> None:
    module_ast = ast.parse(Path(contract.__file__).read_text(encoding="utf-8"))
    imported_modules = set()
    for node in ast.walk(module_ast):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module.split(".", maxsplit=1)[0])

    assert imported_modules <= {"__future__", "dataclasses", "importlib", "sys", "typing"}


def test_curated_analysis_bundle_is_declared_as_project_extra() -> None:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    analysis_extra = pyproject["project"]["optional-dependencies"]["analysis"]

    declared = tuple(str(Requirement(item)) for item in analysis_extra)
    expected = tuple(str(Requirement(item)) for item in contract.CURATED_PYTHON_ANALYSIS_BUNDLE_REQUIREMENTS)

    assert declared == expected


def test_inspect_reports_missing_modules(monkeypatch) -> None:
    original_import_module = contract.importlib.import_module

    def failing_import_module(name, package=None):
        if name in REQUIRED_RUNTIME_MODULES:
            raise ImportError(f"Simulated missing module {name}")
        return original_import_module(name, package)

    monkeypatch.setattr(contract.importlib, "import_module", failing_import_module)
    environment = inspect_python_environment_contract()

    assert environment["ready"] is False
    assert environment["checks"]["matplotlib_importable"] is False
    assert environment["modules"]["matplotlib"]["version"] is None
    assert environment["missing_requirements"] == list(REQUIRED_RUNTIME_REQUIREMENTS)


def test_inspect_reports_version_mismatch(monkeypatch) -> None:
    monkeypatch.setattr(
        contract.importlib,
        "import_module",
        lambda name, package=None: SimpleNamespace(__version__="3.8.0"),
    )

    environment = inspect_python_environment_contract()

    assert environment["ready"] is False
    assert environment["checks"]["matplotlib_version_satisfied"] is False
    assert environment["missing_requirements"] == list(REQUIRED_RUNTIME_REQUIREMENTS)


def test_inspect_uses_distribution_import_name_mapping(monkeypatch) -> None:
    requirements = ("scikit-learn>=1.5", "python-docx>=1.1", "pillow>=10.0")
    imported: list[str] = []
    versions = {"sklearn": "1.8.0", "docx": "1.2.0", "PIL": "12.1.1"}

    def fake_import_module(name: str, package=None) -> SimpleNamespace:
        imported.append(name)
        return SimpleNamespace(__version__=versions[name])

    monkeypatch.setattr(contract.importlib, "import_module", fake_import_module)

    environment = inspect_python_environment_contract(requirements=requirements)

    assert environment["ready"] is True
    assert imported == ["sklearn", "docx", "PIL"]
    assert environment["missing_requirements"] == []


def test_python_environment_surface_is_read_only() -> None:
    source = Path(contract.__file__).read_text(encoding="utf-8")
    environment = inspect_python_environment_contract(requirements=[])

    assert not hasattr(contract, "ensure_python_environment_contract")
    assert "uv pip install" not in source
    assert "subprocess" not in source
    assert environment["provisioning"] == {
        "owner": "uv",
        "owner_surface": "project dependency resolution",
        "requirement_profile": "med-autoscience[analysis]",
        "effect": "read_only",
        "mas_provisioning_allowed": False,
    }
