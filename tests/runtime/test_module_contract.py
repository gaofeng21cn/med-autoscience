from __future__ import annotations

from pathlib import Path

import yaml


def load_contract() -> dict[str, object]:
    contract_path = Path(__file__).resolve().parents[2] / "modules" / "runtime" / "module_contract.yaml"
    assert contract_path.exists(), f"missing contract: {contract_path}"
    payload = yaml.safe_load(contract_path.read_text(encoding="utf-8")) or {}
    assert isinstance(payload, dict)
    return payload


def test_runtime_contract_declares_expected_authority_boundaries() -> None:
    payload = load_contract()

    assert payload["module"] == "runtime"
    assert payload["status"] == "scaffold"
    assert "quest execution truth" in payload["owns"]
    assert "session / worktree / artifact execution truth" in payload["owns"]
    assert "runtime escalation record and runtime status refs" in payload["owns"]
    assert "controller runtime-facing projections" in payload["consumes_refs"]
    assert "runtime status / runtime artifact / escalation refs" in payload["emits_refs"]
    assert "publication authority ownership" in payload["forbids"]
    assert "controller authority truth mutation" in payload["forbids"]
    assert "eval verdict as runtime authority" in payload["forbids"]
