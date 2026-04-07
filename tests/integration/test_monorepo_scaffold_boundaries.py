from __future__ import annotations

import ast
from pathlib import Path

import yaml


EXPECTED_MODULE_DIRS = {"controller_charter", "runtime", "eval_hygiene"}
EXPECTED_MODULE_TEST_FILES = {
    "controller_charter": "test_controller_charter_module_contract.py",
    "runtime": "test_runtime_module_contract.py",
    "eval_hygiene": "test_eval_hygiene_module_contract.py",
}
EXPECTED_RULES = {
    "allowed": [
        "explicit_contract",
        "explicit_artifact_ref",
        "explicit_typed_output",
    ],
    "forbidden": [
        "ad_hoc_dict_shortcut",
        "hidden_import_shortcut",
        "direct_private_state_mutation",
        "authority_takeover_via_read_model",
    ],
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_contract(module_name: str) -> dict[str, object]:
    path = _repo_root() / "modules" / module_name / "module_contract.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_monorepo_scaffold_layout_contains_exact_module_directories() -> None:
    modules_root = _repo_root() / "modules"

    assert {path.name for path in modules_root.iterdir() if path.is_dir()} == EXPECTED_MODULE_DIRS
    for module_name in EXPECTED_MODULE_DIRS:
        files = {path.name for path in (modules_root / module_name).iterdir() if path.is_file()}
        assert files == {"module_contract.yaml"}


def test_monorepo_scaffold_layout_contains_exact_test_files() -> None:
    tests_root = _repo_root() / "tests"

    for dirname, filename in EXPECTED_MODULE_TEST_FILES.items():
        files = {path.name for path in (tests_root / dirname).iterdir() if path.is_file()}
        assert files == {filename}
    integration_files = {path.name for path in (tests_root / "integration").iterdir() if path.is_file()}
    assert integration_files == {"test_monorepo_scaffold_boundaries.py"}


def test_monorepo_scaffold_contracts_define_only_allowed_cross_module_refs() -> None:
    controller = _load_contract("controller_charter")
    runtime = _load_contract("runtime")
    eval_hygiene = _load_contract("eval_hygiene")

    assert "runtime_startup_projection" in controller["emits_refs"]
    assert "runtime_startup_projection" in runtime["consumes_refs"]
    assert "controller_summary_ref" in controller["emits_refs"]
    assert "controller_summary_ref" in eval_hygiene["consumes_refs"]
    assert "runtime_status_ref" in runtime["emits_refs"]
    assert "runtime_status_ref" in eval_hygiene["consumes_refs"]
    assert "runtime_escalation_record_ref" in runtime["emits_refs"]
    assert "runtime_escalation_record_ref" in eval_hygiene["consumes_refs"]
    assert controller["communication_rules"] == EXPECTED_RULES
    assert runtime["communication_rules"] == EXPECTED_RULES
    assert eval_hygiene["communication_rules"] == EXPECTED_RULES


def test_monorepo_scaffold_contracts_preserve_authority_firewalls() -> None:
    controller = _load_contract("controller_charter")
    runtime = _load_contract("runtime")
    eval_hygiene = _load_contract("eval_hygiene")

    assert "publication_authority_ownership" not in runtime["owns"]
    assert "runtime_private_state_mutation" in controller["forbids"]
    assert "controller_truth_mutation" in eval_hygiene["forbids"]
    assert "runtime_truth_mutation" in eval_hygiene["forbids"]


def test_monorepo_scaffold_tests_do_not_import_runtime_or_external_repo_surfaces() -> None:
    paths = [
        _repo_root() / "tests" / "controller_charter" / "test_controller_charter_module_contract.py",
        _repo_root() / "tests" / "runtime" / "test_runtime_module_contract.py",
        _repo_root() / "tests" / "eval_hygiene" / "test_eval_hygiene_module_contract.py",
        _repo_root() / "tests" / "integration" / "test_monorepo_scaffold_boundaries.py",
    ]

    for path in paths:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "med_autoscience"
            elif isinstance(node, ast.ImportFrom):
                assert node.module != "med_autoscience"
        if path.name != "test_monorepo_scaffold_boundaries.py":
            assert "src/med_autoscience" not in text
            assert "med-deepscientist" not in text
