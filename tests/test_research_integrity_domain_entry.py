from __future__ import annotations

import importlib


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
    assert action["supported_surfaces"]["mcp"]["surface_kind"] == "research_integrity_gate_input_bundle"
    assert "only produces evidence" in action["summary"]
    assert "does not write publication authority" in action["summary"]
    assert mcp_projection["research_integrity_gate_input"]["input_schema"]["properties"]["payload"] == {
        "type": "object"
    }
    assert mcp_projection["research_integrity_gate_input"]["input_schema"]["properties"]["reference_checks"] == {
        "type": "array"
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


def test_action_catalog_exposes_research_integrity_reference_verification_descriptor() -> None:
    action_catalog = importlib.import_module("med_autoscience.action_catalog")

    catalog = action_catalog.build_mas_action_catalog()
    actions = {item["action_id"]: item for item in catalog["actions"]}
    mcp_projection = action_catalog.action_catalog_metadata_by_mcp_tool(catalog)
    action = actions["research_integrity_reference_verification"]
    boundary = action["authority_boundary"]

    assert action["effect"] == "read_only"
    assert action["source_command"]["surface_kind"] == (
        "research_integrity_reference_verification_gate_input_bundle"
    )
    assert action["supported_surfaces"]["mcp"]["descriptor_only"] is True
    assert action["supported_surfaces"]["mcp"]["public_runtime"] is False
    assert "complete-reference verification lane" in action["summary"]
    assert "does not write publication authority" in action["summary"]
    assert mcp_projection["research_integrity_reference_verification"]["input_schema"]["properties"][
        "references"
    ] == {"type": "array"}
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


def test_action_catalog_exposes_research_integrity_stage_hook_descriptor() -> None:
    action_catalog = importlib.import_module("med_autoscience.action_catalog")

    catalog = action_catalog.build_mas_action_catalog()
    actions = {item["action_id"]: item for item in catalog["actions"]}
    mcp_projection = action_catalog.action_catalog_metadata_by_mcp_tool(catalog)
    action = actions["research_integrity_review_publication_gate_stage_hook"]
    boundary = action["authority_boundary"]

    assert action["effect"] == "read_only"
    assert action["source_command"]["surface_kind"] == (
        "research_integrity_review_publication_gate_stage_hook"
    )
    assert action["supported_surfaces"]["mcp"]["descriptor_only"] is True
    assert action["supported_surfaces"]["mcp"]["public_runtime"] is False
    assert "Mandatory Review/Publication Gate stage-hook input" in action["summary"]
    assert "trigger research-integrity-reference-verification" in action["summary"]
    assert mcp_projection["research_integrity_review_publication_gate_stage_hook"]["input_schema"][
        "properties"
    ]["manuscript"] == {"type": "object"}
    assert boundary["outputs_are_gate_inputs"] is True
    assert boundary["stage_hook_consumers"] == ["review_gate", "publication_gate"]
    assert boundary["triggered_action"] == "research-integrity-reference-verification"
    assert boundary["can_request_provider_lookup"] is True
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
        "reference_checks",
        "reference",
        "references",
        "claim_spans",
        "claim",
        "claims",
        "citation_refs",
        "evidence_refs",
        "reference_attestation_refs",
        "manuscript_sections",
        "manuscript",
        "numeric_facts",
        "display_facts",
        "provider_evidence",
        "reference_attestations",
        "display_to_claim_map",
        "reporting_guideline_expectations",
    ]
    assert contracts["research-integrity-reference-verification"]["required_fields"] == []
    assert contracts["research-integrity-reference-verification"]["optional_fields"] == [
        "payload",
        "reference",
        "references",
        "provider_evidence",
        "provider_receipts",
        "source_refs",
        "reference_manager_ref",
        "manuscript_ref",
    ]
    assert contracts["research-integrity-review-publication-gate-stage-hook"]["required_fields"] == []
    assert "manuscript" in contracts["research-integrity-review-publication-gate-stage-hook"][
        "optional_fields"
    ]
    assert "display_to_claim_map" in contracts["research-integrity-review-publication-gate-stage-hook"][
        "optional_fields"
    ]


def test_domain_entry_dispatches_research_integrity_gate_input_without_profile() -> None:
    domain_entry = importlib.import_module("med_autoscience.domain_entry")

    def fail_if_profile_loaded(_profile_ref):
        raise AssertionError("research integrity gate input must not require a workspace profile")

    payload = domain_entry.MedAutoScienceDomainEntry(profile_loader=fail_if_profile_loaded).dispatch(
        {
            "command": "research-integrity-gate-input",
            "provider_evidence": [
                {
                    "provider": "crossref",
                    "matched_identifiers": {"doi": "10.1000/example"},
                    "metadata": {"title": "Example Trial", "year": "2024"},
                }
            ],
            "reference": {
                "id": "smith2024",
                "doi": "10.1000/example",
                "title": "Example Trial",
                "year": "2024",
            },
            "claim": {
                "claim_id": "c1",
                "text": "Intervention improved AUC.",
                "citation_refs": ["ref:smith2024"],
                "evidence_refs": ["analysis:auc"],
            },
            "manuscript": {
                "results": {
                    "numeric_facts": [
                        {
                            "fact_id": "auc",
                            "value": "0.71",
                            "unit": "AUROC",
                            "source_ref": "analysis:auc",
                        }
                    ]
                }
            },
            "display_facts": [
                {
                    "fact_id": "auc",
                    "value": "0.71",
                    "unit": "AUROC",
                    "display_id": "figure_1",
                }
            ],
        }
    )

    assert payload["command"] == "research-integrity-gate-input"
    assert payload["surface_kind"] == "research_integrity_gate_input_bundle"
    assert payload["status"] == "clear"
    assert payload["surfaces"]["reference_verification_attestations"][0]["status"] == "verified"
    assert (
        payload["surfaces"]["claim_citation_support_matrix_v2"]["claims"][0]["support_grade"]
        == "direct_support"
    )
    assert payload["surfaces"]["manuscript_consistency_meta_review"]["status"] == "clear"
    assert payload["authority_boundary"]["can_write_publication_eval_latest"] is False
    assert payload["authority_boundary"]["can_write_controller_decisions"] is False
    assert payload["authority_boundary"]["can_mutate_current_package"] is False
    assert payload["authority_boundary"]["can_sign_owner_receipt"] is False
    assert payload["authority_boundary"]["can_materialize_typed_blocker"] is False
    assert payload["authority_boundary"]["can_materialize_human_gate"] is False
    assert payload["authority_boundary"]["can_write_runtime_queue_or_provider_attempt"] is False


def test_domain_entry_dispatches_research_integrity_reference_verification_with_lazy_provider(
    monkeypatch,
) -> None:
    domain_entry = importlib.import_module("med_autoscience.domain_entry")
    calls = []

    def fake_loader():
        def fake_builder(*, payload):
            calls.append(payload)
            return {
                "surface_kind": "research_integrity_reference_verification_gate_input_bundle",
                "schema_version": 1,
                "status": "clear",
                "surfaces": {
                    "reference_verification_payload": {
                        "reference_count": len(payload["references"]),
                        "source_refs": payload["source_refs"],
                    }
                },
                "blocker_candidates": [],
                "review_candidates": [],
                "authority_boundary": {
                    "can_write_mas_study_truth": False,
                    "can_write_publication_eval_latest": False,
                    "can_write_publication_eval": False,
                    "can_write_controller_decisions": False,
                    "can_mutate_current_package": False,
                    "can_write_current_package": False,
                    "can_sign_owner_receipt": False,
                    "can_write_owner_receipt": False,
                    "can_materialize_typed_blocker": False,
                    "can_write_typed_blocker": False,
                    "can_materialize_human_gate": False,
                    "can_write_runtime_queue_or_provider_attempt": False,
                    "can_authorize_publication_quality": False,
                    "can_authorize_publication_readiness": False,
                    "can_authorize_submission_readiness": False,
                },
            }

        return fake_builder

    def fail_if_profile_loaded(_profile_ref):
        raise AssertionError("research integrity reference verification must not require a workspace profile")

    monkeypatch.setattr(
        domain_entry,
        "_load_research_integrity_reference_verification_builder",
        fake_loader,
    )

    payload = domain_entry.MedAutoScienceDomainEntry(profile_loader=fail_if_profile_loaded).dispatch(
        {
            "command": "research-integrity-reference-verification",
            "payload": {"source_refs": ["manuscript.md#references"]},
            "references": [{"id": "smith2024", "doi": "10.1000/example"}],
            "provider_evidence": [{"provider": "crossref", "receipt_ref": "provider/crossref/smith2024"}],
        }
    )

    assert calls == [
        {
            "source_refs": ["manuscript.md#references"],
            "references": [{"id": "smith2024", "doi": "10.1000/example"}],
            "provider_evidence": [{"provider": "crossref", "receipt_ref": "provider/crossref/smith2024"}],
        }
    ]
    assert payload["command"] == "research-integrity-reference-verification"
    assert payload["surface_kind"] == "research_integrity_reference_verification_gate_input_bundle"
    assert payload["status"] == "clear"
    assert payload["surfaces"]["reference_verification_payload"]["reference_count"] == 1
    assert all(value is False for value in payload["authority_boundary"].values())


def test_domain_entry_dispatches_research_integrity_stage_hook_through_reference_verification(
    monkeypatch,
) -> None:
    domain_entry = importlib.import_module("med_autoscience.domain_entry")
    stage_hooks = importlib.import_module("med_autoscience.research_integrity.stage_hooks")
    calls = []

    def fake_reference_verification(*, payload):
        calls.append(payload)
        gate_input = {
            "surface_kind": "research_integrity_gate_input_bundle",
            "schema_version": 1,
            "status": "needs_review",
            "surfaces": {
                "manuscript_consistency_meta_review": {
                    "surface_kind": "manuscript_consistency_meta_review",
                    "status": "needs_review",
                }
            },
            "blocker_candidates": [],
            "review_candidates": [{"family": "manuscript_consistency", "reason": "needs_review"}],
            "authority_boundary": {},
        }
        return {
            "surface_kind": "research_integrity_reference_verification_gate_input_bundle",
            "schema_version": 1,
            "status": "needs_review",
            "surfaces": {"research_integrity_gate_input_bundle": gate_input},
            "blocker_candidates": [],
            "review_candidates": gate_input["review_candidates"],
            "authority_boundary": {},
        }

    def fail_if_profile_loaded(_profile_ref):
        raise AssertionError("research integrity stage hook must not require a workspace profile")

    monkeypatch.setattr(stage_hooks, "build_reference_verification_payload", fake_reference_verification)

    payload = domain_entry.MedAutoScienceDomainEntry(profile_loader=fail_if_profile_loaded).dispatch(
        {
            "command": "research-integrity-review-publication-gate-stage-hook",
            "payload": {"source_refs": ["paper/references.bib"]},
            "stage_id": "publication_supervision",
            "stage_event": "publication_gate_entered",
            "references": [{"id": "smith2024", "doi": "10.1000/example"}],
            "manuscript": {"results": {"numeric_facts": [{"fact_id": "auc", "value": "0.71"}]}},
        }
    )

    assert calls == [
        {
            "source_refs": ["paper/references.bib"],
            "stage_id": "publication_supervision",
            "stage_event": "publication_gate_entered",
            "references": [{"id": "smith2024", "doi": "10.1000/example"}],
            "manuscript": {"results": {"numeric_facts": [{"fact_id": "auc", "value": "0.71"}]}},
        }
    ]
    assert payload["command"] == "research-integrity-review-publication-gate-stage-hook"
    assert payload["surface_kind"] == "research_integrity_review_publication_gate_stage_hook"
    assert payload["triggered_action"] == "research-integrity-reference-verification"
    assert payload["gate_input_bundle"]["surfaces"]["manuscript_consistency_meta_review"][
        "status"
    ] == "needs_review"
    assert payload["authority_boundary"]["can_write_publication_eval_latest"] is False
    assert payload["authority_boundary"]["can_write_controller_decisions"] is False
    assert payload["authority_boundary"]["can_mutate_current_package"] is False
    assert payload["authority_boundary"]["can_sign_owner_receipt"] is False
    assert payload["authority_boundary"]["can_materialize_typed_blocker"] is False
    assert payload["authority_boundary"]["can_materialize_human_gate"] is False
    assert payload["authority_boundary"]["can_write_runtime_queue_or_provider_attempt"] is False
