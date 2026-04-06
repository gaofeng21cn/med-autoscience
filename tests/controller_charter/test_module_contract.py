from __future__ import annotations

from pathlib import Path

import yaml


def load_contract() -> dict[str, object]:
    contract_path = (
        Path(__file__).resolve().parents[2] / "modules" / "controller_charter" / "module_contract.yaml"
    )
    assert contract_path.exists(), f"missing contract: {contract_path}"
    payload = yaml.safe_load(contract_path.read_text(encoding="utf-8")) or {}
    assert isinstance(payload, dict)
    return payload


def test_controller_charter_contract_declares_expected_authority_boundaries() -> None:
    payload = load_contract()

    assert payload["module"] == "controller_charter"
    assert payload["status"] == "scaffold"
    assert "study / workspace controller-owned authority truth" in payload["owns"]
    assert "study_charter and compiled charter logic" in payload["owns"]
    assert "route / policy / objective / trigger authority" in payload["owns"]
    assert "runtime-facing projection refs" in payload["emits_refs"]
    assert "eval-consumable controller refs" in payload["emits_refs"]
    assert "direct runtime private state mutation" in payload["forbids"]
    assert "runtime event ownership" in payload["forbids"]
    assert "eval verdict ownership" in payload["forbids"]
