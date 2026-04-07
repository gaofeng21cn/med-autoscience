from __future__ import annotations

from pathlib import Path

import yaml


def _load_contract() -> dict[str, object]:
    path = Path(__file__).resolve().parents[2] / "modules" / "runtime" / "module_contract.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_runtime_contract_declares_execution_authority_boundary() -> None:
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
    assert contract["module"] == "runtime"
    assert contract["status"] == "scaffold"
    assert contract["owns"] == [
        "quest_execution_truth",
        "runtime_session_truth",
        "runtime_artifact_truth",
        "runtime_escalation_record",
    ]
    assert contract["consumes_refs"] == [
        "runtime_startup_projection",
        "runtime_policy_summary_ref",
    ]
    assert contract["emits_refs"] == [
        "runtime_status_ref",
        "runtime_artifact_ref",
        "runtime_escalation_record_ref",
    ]
    assert contract["forbids"] == [
        "publication_authority_ownership",
        "controller_truth_mutation",
        "eval_verdict_ownership",
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
