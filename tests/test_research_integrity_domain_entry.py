from __future__ import annotations

import importlib
import sys
from types import ModuleType


def test_action_catalog_exposes_research_integrity_gate_input_as_read_only_descriptor() -> None:
    action_catalog = importlib.import_module("med_autoscience.action_catalog")

    catalog = action_catalog.build_mas_action_catalog()
    actions = {item["action_id"]: item for item in catalog["actions"]}
    mcp_projection = action_catalog.action_catalog_metadata_by_mcp_tool(catalog)
    action = actions["research_integrity_gate_input"]
    boundary = action["authority_boundary"]

    assert action["effect"] == "read_only"
    assert action["source_command"]["surface_kind"] == "research_integrity_gate_input_bundle"
    assert action["supported_surfaces"]["mcp"]["descriptor_only"] is True
    assert action["supported_surfaces"]["mcp"]["public_runtime"] is False
    assert action["supported_surfaces"]["mcp"]["surface_kind"] == (
        "research_integrity_gate_input_bundle"
    )
    assert "only produces evidence" in action["summary"]
    assert "does not write publication authority" in action["summary"]
    assert mcp_projection["research_integrity_gate_input"]["input_schema"]["properties"]["payload"] == {
        "type": "object"
    }
    assert boundary["outputs_are_gate_inputs"] is True
    assert boundary["can_write_mas_study_truth"] is False
    assert boundary["can_write_publication_eval_latest"] is False
    assert boundary["can_write_publication_eval"] is False
    assert boundary["can_write_controller_decisions"] is False
    assert boundary["can_mutate_current_package"] is False
    assert boundary["can_write_current_package"] is False
    assert boundary["can_sign_owner_receipt"] is False
    assert boundary["can_write_owner_receipt"] is False
    assert boundary["can_materialize_typed_blocker"] is False
    assert boundary["can_write_typed_blocker"] is False
    assert boundary["can_materialize_human_gate"] is False
    assert boundary["can_write_runtime_queue_or_provider_attempt"] is False
    assert boundary["can_authorize_publication_quality"] is False
    assert boundary["can_authorize_publication_readiness"] is False
    assert boundary["can_authorize_submission_readiness"] is False


def test_domain_entry_contract_exposes_research_integrity_gate_input_without_workspace() -> None:
    contract_module = importlib.import_module("med_autoscience.domain_entry_contract")

    contracts = {
        item["command"]: item
        for item in contract_module.build_domain_entry_contract()["command_contracts"]
    }

    contract = contracts["research-integrity-gate-input"]
    assert contract["required_fields"] == []
    assert contract["optional_fields"] == [
        "payload",
        "reference",
        "references",
        "claim",
        "claims",
        "manuscript",
        "provider_evidence",
        "reference_attestations",
        "display_to_claim_map",
        "reporting_guideline_expectations",
    ]


def test_domain_entry_dispatches_research_integrity_gate_input_without_profile(monkeypatch) -> None:
    domain_entry = importlib.import_module("med_autoscience.domain_entry")
    captured: dict[str, object] = {}
    fake_gate_bundle = ModuleType("med_autoscience.research_integrity.gate_bundle")

    def fake_build_research_integrity_gate_input_bundle(*, payload):
        captured["payload"] = payload
        return {
            "surface_kind": "research_integrity_gate_input_bundle",
            "authority_boundary": {
                "outputs_are_gate_inputs": True,
                "can_write_publication_eval_latest": False,
                "can_write_controller_decisions": False,
                "can_mutate_current_package": False,
                "can_sign_owner_receipt": False,
                "can_materialize_typed_blocker": False,
                "can_materialize_human_gate": False,
                "can_write_runtime_queue_or_provider_attempt": False,
            },
        }

    fake_gate_bundle.build_research_integrity_gate_input_bundle = (
        fake_build_research_integrity_gate_input_bundle
    )
    monkeypatch.setitem(
        sys.modules,
        "med_autoscience.research_integrity.gate_bundle",
        fake_gate_bundle,
    )

    payload = domain_entry.MedAutoScienceDomainEntry().dispatch(
        {
            "command": "research-integrity-gate-input",
            "payload": {"provider_evidence": [{"provider": "crossref"}]},
            "reference": {"id": "smith2024", "doi": "10.1000/example"},
            "claim": {"claim_id": "c1", "text": "Claim text"},
            "manuscript": {"sections": [{"name": "results"}]},
        }
    )

    assert captured["payload"] == {
        "provider_evidence": [{"provider": "crossref"}],
        "reference": {"id": "smith2024", "doi": "10.1000/example"},
        "claim": {"claim_id": "c1", "text": "Claim text"},
        "manuscript": {"sections": [{"name": "results"}]},
    }
    assert payload["command"] == "research-integrity-gate-input"
    assert payload["surface_kind"] == "research_integrity_gate_input_bundle"
    assert payload["authority_boundary"]["outputs_are_gate_inputs"] is True
    assert payload["authority_boundary"]["can_write_publication_eval_latest"] is False
    assert payload["authority_boundary"]["can_write_controller_decisions"] is False
    assert payload["authority_boundary"]["can_mutate_current_package"] is False
    assert payload["authority_boundary"]["can_sign_owner_receipt"] is False
    assert payload["authority_boundary"]["can_materialize_typed_blocker"] is False
    assert payload["authority_boundary"]["can_materialize_human_gate"] is False
    assert payload["authority_boundary"]["can_write_runtime_queue_or_provider_attempt"] is False
