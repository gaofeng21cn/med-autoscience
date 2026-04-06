from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULES_ROOT = REPO_ROOT / "modules"
TESTS_ROOT = REPO_ROOT / "tests"


def load_contract(module_name: str) -> dict[str, object]:
    return yaml.safe_load(
        (MODULES_ROOT / module_name / "module_contract.yaml").read_text(encoding="utf-8")
    ) or {}


def test_minimal_scaffold_directories_exist() -> None:
    assert (MODULES_ROOT / "controller_charter").is_dir()
    assert (MODULES_ROOT / "runtime").is_dir()
    assert (MODULES_ROOT / "eval_hygiene").is_dir()
    assert (TESTS_ROOT / "controller_charter").is_dir()
    assert (TESTS_ROOT / "runtime").is_dir()
    assert (TESTS_ROOT / "eval_hygiene").is_dir()
    assert (TESTS_ROOT / "integration").is_dir()


def test_scaffold_contracts_preserve_authority_boundaries() -> None:
    controller_contract = load_contract("controller_charter")
    runtime_contract = load_contract("runtime")
    eval_contract = load_contract("eval_hygiene")

    assert "direct runtime private state mutation" in controller_contract["forbids"]
    assert "runtime event ownership" in controller_contract["forbids"]
    assert "publication authority ownership" in runtime_contract["forbids"]
    assert "controller truth mutation" in runtime_contract["forbids"]
    assert "controller truth mutation" in eval_contract["forbids"]
    assert "runtime truth mutation" in eval_contract["forbids"]
    assert "becoming a new controller" in eval_contract["forbids"]
    assert "publication authority ownership" not in runtime_contract["owns"]


def test_scaffold_contracts_only_exchange_explicit_refs() -> None:
    controller_contract = load_contract("controller_charter")
    runtime_contract = load_contract("runtime")
    eval_contract = load_contract("eval_hygiene")

    assert controller_contract["consumes_refs"] == ["none"]
    assert all("refs" in item for item in controller_contract["emits_refs"])
    assert all("refs" in item for item in runtime_contract["consumes_refs"])
    assert all("refs" in item for item in runtime_contract["emits_refs"])
    assert all("refs" in item for item in eval_contract["consumes_refs"])
    assert all("refs" in item for item in eval_contract["emits_refs"])
