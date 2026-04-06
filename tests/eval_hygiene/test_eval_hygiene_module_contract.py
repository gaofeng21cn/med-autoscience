from __future__ import annotations

from pathlib import Path

import yaml


MODULE_CONTRACT_PATH = (
    Path(__file__).resolve().parents[2] / "modules" / "eval_hygiene" / "module_contract.yaml"
)


def load_module_contract() -> dict[str, object]:
    return yaml.safe_load(MODULE_CONTRACT_PATH.read_text(encoding="utf-8")) or {}


def test_eval_hygiene_contract_declares_expected_fields() -> None:
    contract = load_module_contract()

    assert contract["module"] == "eval_hygiene"
    assert contract["status"] == "scaffold"
    assert contract["owns"] == [
        "verdict / gap / recommendation",
        "promotion / stop-loss / hygiene gate conclusions",
    ]
    assert contract["consumes_refs"] == [
        "controller refs",
        "runtime refs",
        "delivery-facing refs",
    ]
    assert contract["emits_refs"] == [
        "hygiene verdict refs",
        "promotion decision refs",
        "stop-loss recommendation refs",
    ]
    assert contract["forbids"] == [
        "controller truth mutation",
        "runtime truth mutation",
        "becoming a new controller",
    ]
