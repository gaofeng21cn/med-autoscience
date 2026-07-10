from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(module_name: str) -> dict[str, object]:
    path = REPO_ROOT / "contracts" / "modules" / module_name / "module_contract.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_scaffold_modules_exchange_refs_without_authority_overlap() -> None:
    controller = _load("controller_charter")
    runtime = _load("runtime")
    evaluation = _load("eval_hygiene")

    assert "controller_summary_ref" in controller["emits_refs"]
    assert "controller_summary_ref" in evaluation["consumes_refs"]
    assert "runtime_escalation_record_ref" in runtime["emits_refs"]
    assert "runtime_escalation_record_ref" in evaluation["consumes_refs"]

    controller_owns = set(controller["owns"])
    runtime_owns = set(runtime["owns"])
    evaluation_owns = set(evaluation["owns"])
    assert controller_owns.isdisjoint(runtime_owns)
    assert controller_owns.isdisjoint(evaluation_owns)
    assert runtime_owns.isdisjoint(evaluation_owns)
