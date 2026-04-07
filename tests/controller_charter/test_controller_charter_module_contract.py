from __future__ import annotations

from pathlib import Path

import yaml


def _load_contract() -> dict[str, object]:
    path = Path(__file__).resolve().parents[2] / "modules" / "controller_charter" / "module_contract.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_controller_charter_contract_declares_controller_authority_boundary() -> None:
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
    assert contract["module"] == "controller_charter"
    assert contract["status"] == "scaffold"
    assert contract["owns"] == [
        "study_charter",
        "controller_policy",
        "route_trigger_authority",
    ]
    assert contract["consumes_refs"] == [
        "workspace_profile",
        "study_metadata",
        "policy_surface",
    ]
    assert contract["emits_refs"] == [
        "runtime_startup_projection",
        "controller_summary_ref",
    ]
    assert contract["forbids"] == [
        "runtime_private_state_mutation",
        "runtime_event_ownership",
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
