from __future__ import annotations

from pathlib import Path

import yaml


def _load_contract() -> dict[str, object]:
    path = Path(__file__).resolve().parents[2] / "modules" / "eval_hygiene" / "module_contract.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_eval_hygiene_contract_declares_evaluation_authority_boundary() -> None:
    contract = _load_contract()

    assert set(contract) == {
        "module",
        "status",
        "owns",
        "consumes_refs",
        "emits_refs",
        "forbids",
        "communication_rules",
    }
    assert contract["module"] == "eval_hygiene"
    assert contract["status"] == "scaffold"
    assert contract["owns"] == [
        "evaluation_verdict",
        "gap_recommendation",
        "promotion_stop_loss_gate",
    ]
    assert contract["consumes_refs"] == [
        "controller_summary_ref",
        "runtime_status_ref",
        "runtime_escalation_record_ref",
    ]
    assert contract["emits_refs"] == [
        "evaluation_summary_ref",
        "promotion_gate_ref",
    ]
    assert contract["forbids"] == [
        "controller_truth_mutation",
        "runtime_truth_mutation",
        "outer_controller_ownership",
    ]
    assert contract["communication_rules"] == {
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
