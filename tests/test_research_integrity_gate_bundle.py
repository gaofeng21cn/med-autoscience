from __future__ import annotations

from med_autoscience.domain_entry import MedAutoScienceDomainEntry
from med_autoscience.research_integrity.gate_bundle import (
    build_research_integrity_gate_input_bundle,
)


def test_research_integrity_gate_bundle_combines_reference_claim_and_manuscript_checks() -> None:
    bundle = build_research_integrity_gate_input_bundle(
        payload={
            "reference": {
                "reference_id": "smith2024",
                "doi": "10.1000/example",
                "title": "Recorded metabolic diagnostic fields",
                "year": "2024",
            },
            "provider_evidence": [
                {
                    "provider": "crossref",
                    "reference_id": "smith2024",
                    "doi": "10.1000/example",
                    "title": "Recorded metabolic diagnostic fields",
                    "year": "2024",
                }
            ],
            "claim": {
                "claim_id": "claim-1",
                "claim_text": "Diagnostic fields are recorded among populated records.",
                "citation_refs": ["smith2024"],
                "evidence_refs": ["table-2"],
            },
            "manuscript": {
                "results": {
                    "numeric_facts": [
                        {
                            "fact_id": "n-records",
                            "reported_value": 4189,
                            "unit": "records",
                            "population": "registry",
                        }
                    ]
                },
                "tables": {
                    "numeric_facts": [
                        {
                            "fact_id": "n-records",
                            "reported_value": 4189,
                            "unit": "records",
                            "population": "registry",
                        }
                    ]
                },
            },
            "reporting_guideline_expectations": [
                {"item_id": "ethics_approval", "status": "missing", "required": True}
            ],
        }
    )

    assert bundle["surface_kind"] == "research_integrity_gate_input_bundle"
    assert bundle["status"] == "blocked"
    assert bundle["reference_attestations"][0]["status"] == "verified"
    assert bundle["claim_citation_support_matrix"]["claims"][0]["support_grade"] == "direct_support"
    assert bundle["manuscript_consistency_meta_review"]["status"] == "blocked"
    assert bundle["blocker_candidates"][0]["authority_boundary"]["can_write_owner_receipt"] is False
    assert bundle["authority_boundary"]["can_write_current_package"] is False


def test_domain_entry_dispatches_real_research_integrity_gate_bundle_without_profile() -> None:
    payload = MedAutoScienceDomainEntry().dispatch(
        {
            "command": "research-integrity-gate-input",
            "reference": {"reference_id": "smith2024", "doi": "10.1000/example"},
            "provider_evidence": [
                {
                    "provider": "crossref",
                    "reference_id": "smith2024",
                    "doi": "10.1000/example",
                }
            ],
            "claim": {
                "claim_id": "claim-1",
                "citation_refs": ["smith2024"],
                "evidence_refs": ["analysis-1"],
            },
        }
    )

    assert payload["command"] == "research-integrity-gate-input"
    assert payload["surface_kind"] == "research_integrity_gate_input_bundle"
    assert payload["status"] == "clear"
    assert payload["authority_boundary"]["outputs_are_gate_inputs"] is True
    assert payload["authority_boundary"]["can_write_runtime_queue_or_provider_attempt"] is False
