from __future__ import annotations

from pathlib import Path

import yaml


MODULE_CONTRACT_PATH = (
    Path(__file__).resolve().parents[2] / "modules" / "controller_charter" / "module_contract.yaml"
)


def load_module_contract() -> dict[str, object]:
    return yaml.safe_load(MODULE_CONTRACT_PATH.read_text(encoding="utf-8")) or {}


def test_controller_charter_contract_declares_expected_fields() -> None:
    contract = load_module_contract()

    assert contract["module"] == "controller_charter"
    assert contract["status"] == "scaffold"
    assert contract["owns"] == [
        "study / workspace controller truth",
        "study_charter compile logic",
        "route / policy / objective / trigger authority",
    ]
    assert contract["consumes_refs"] == ["none"]
    assert contract["emits_refs"] == [
        "runtime-facing projection refs",
        "eval-consumable controller refs",
    ]
    assert contract["forbids"] == [
        "direct runtime private state mutation",
        "runtime event ownership",
        "eval verdict ownership",
    ]
