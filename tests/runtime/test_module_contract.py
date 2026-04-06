from __future__ import annotations

from pathlib import Path

import yaml


MODULE_CONTRACT_PATH = Path(__file__).resolve().parents[2] / "modules" / "runtime" / "module_contract.yaml"


def load_module_contract() -> dict[str, object]:
    return yaml.safe_load(MODULE_CONTRACT_PATH.read_text(encoding="utf-8")) or {}


def test_runtime_contract_declares_expected_fields() -> None:
    contract = load_module_contract()

    assert contract["module"] == "runtime"
    assert contract["status"] == "scaffold"
    assert contract["owns"] == [
        "quest execution truth",
        "session / worktree / artifact execution truth",
        "runtime escalation record",
    ]
    assert contract["consumes_refs"] == ["runtime-facing controller projection refs"]
    assert contract["emits_refs"] == [
        "runtime status refs",
        "runtime artifact refs",
        "runtime escalation refs",
    ]
    assert contract["forbids"] == [
        "publication authority ownership",
        "controller truth mutation",
        "inline eval verdict authority",
    ]
