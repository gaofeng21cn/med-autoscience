from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_contract(module_name: str) -> dict[str, object]:
    contract_path = REPO_ROOT / "modules" / module_name / "module_contract.yaml"
    assert contract_path.exists(), f"missing contract: {contract_path}"
    payload = yaml.safe_load(contract_path.read_text(encoding="utf-8")) or {}
    assert isinstance(payload, dict)
    return payload


def test_scaffold_directories_exist_only_for_the_minimal_modules_and_tests() -> None:
    expected_directories = [
        REPO_ROOT / "modules" / "controller_charter",
        REPO_ROOT / "modules" / "runtime",
        REPO_ROOT / "modules" / "eval_hygiene",
        REPO_ROOT / "tests" / "controller_charter",
        REPO_ROOT / "tests" / "runtime",
        REPO_ROOT / "tests" / "eval_hygiene",
        REPO_ROOT / "tests" / "integration",
    ]

    for directory in expected_directories:
        assert directory.is_dir(), f"missing scaffold directory: {directory}"


def test_scaffold_contracts_share_the_same_cross_module_communication_firewall() -> None:
    expected_allowed = [
        "explicit contract",
        "explicit artifact ref",
        "explicit typed output",
        "explicit typed summary",
    ]
    expected_forbidden = [
        "ad-hoc dict mixed-layer shortcut",
        "hidden import shortcut",
        "direct private-state mutation",
        "authority takeover via read-model",
    ]

    for module_name in ("controller_charter", "runtime", "eval_hygiene"):
        payload = load_contract(module_name)
        rules = payload["communication_rules"]
        assert rules["allowed"] == expected_allowed
        assert rules["forbidden"] == expected_forbidden


def test_scaffold_contracts_preserve_module_firewalls() -> None:
    controller_contract = load_contract("controller_charter")
    runtime_contract = load_contract("runtime")
    eval_contract = load_contract("eval_hygiene")

    assert "direct runtime private state mutation" in controller_contract["forbids"]
    assert "publication authority ownership" in runtime_contract["forbids"]
    assert "controller truth mutation" in eval_contract["forbids"]
    assert "runtime truth mutation" in eval_contract["forbids"]
