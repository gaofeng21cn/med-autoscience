from __future__ import annotations

from pathlib import Path

import yaml


def load_contract() -> dict[str, object]:
    contract_path = Path(__file__).resolve().parents[2] / "modules" / "eval_hygiene" / "module_contract.yaml"
    assert contract_path.exists(), f"missing contract: {contract_path}"
    payload = yaml.safe_load(contract_path.read_text(encoding="utf-8")) or {}
    assert isinstance(payload, dict)
    return payload


def test_eval_hygiene_contract_declares_expected_authority_boundaries() -> None:
    payload = load_contract()

    assert payload["module"] == "eval_hygiene"
    assert payload["status"] == "scaffold"
    assert "verdict / gap / recommendation" in payload["owns"]
    assert "promotion / stop-loss / hygiene gate conclusions" in payload["owns"]
    assert "controller refs" in payload["consumes_refs"]
    assert "runtime refs" in payload["consumes_refs"]
    assert "delivery-facing refs" in payload["consumes_refs"]
    assert "controller truth mutation" in payload["forbids"]
    assert "runtime truth mutation" in payload["forbids"]
    assert "becoming a new outer controller" in payload["forbids"]
