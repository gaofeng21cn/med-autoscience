from __future__ import annotations

from pathlib import Path

import yaml


def _load_contract() -> dict[str, object]:
    path = (
        Path(__file__).resolve().parents[2]
        / "contracts"
        / "modules"
        / "runtime"
        / "module_contract.yaml"
    )
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
    assert contract["status"] == "retired_private_runtime_control_boundary"
    assert contract["owns"] == [
        "domain_authority_refs",
        "owner_receipt_refs",
        "typed_blocker_refs",
        "runtime_escalation_record_refs",
    ]
    assert contract["consumes_refs"] == [
        "opl_current_control_state_ref",
        "opl_provider_attempt_ref",
        "runtime_policy_summary_ref",
    ]
    assert contract["emits_refs"] == [
        "domain_health_diagnostic_ref",
        "owner_route_ref",
        "typed_blocker_ref",
        "runtime_escalation_record_ref",
    ]
    assert contract["forbids"] == [
        "quest_execution_truth",
        "runtime_session_truth",
        "runtime_artifact_truth",
        "generic_queue_owner",
        "generic_attempt_ledger_owner",
        "generic_runtime_lifecycle_owner",
        "provider_liveness_ownership",
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
