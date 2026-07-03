from __future__ import annotations

from med_autoscience.research_integrity.stage_hooks import (
    FORBIDDEN_AUTHORITY_FLAGS,
    build_review_publication_gate_stage_hook_payload,
)


def test_review_publication_gate_stage_hook_builds_reference_verification_gate_input() -> None:
    payload = build_review_publication_gate_stage_hook_payload(
        payload={
            "stage_id": "publication_supervision",
            "stage_event": "review_gate_entered",
            "stage_hook_ref": "stage-hook:publication_supervision:review_gate",
            "source_refs": ["paper/references.bib"],
            "references": [{"id": "smith2024", "doi": "10.1000/example", "title": "Example Trial"}],
            "provider_evidence": [
                {
                    "provider": "crossref",
                    "reference_id": "smith2024",
                    "matched_identifiers": {"doi": "10.1000/example"},
                    "metadata": {"title": "Example Trial", "year": "2024"},
                }
            ],
            "claim": {
                "claim_id": "C1",
                "citation_refs": [{"ref": "ref:smith2024"}],
                "evidence_refs": ["analysis/results.json#/C1"],
                "support_grade": "direct_support",
            },
            "manuscript": {
                "results": {
                    "numeric_facts": [
                        {
                            "fact_id": "auc",
                            "reported_value": "0.71",
                            "unit": "AUROC",
                        }
                    ]
                }
            },
            "display_facts": [{"fact_id": "auc", "reported_value": "0.71", "unit": "AUROC"}],
        }
    )

    gate_bundle = payload["gate_input_bundle"]

    assert payload["surface_kind"] == "research_integrity_review_publication_gate_stage_hook"
    assert payload["hook_role"] == "mandatory_review_publication_gate_input"
    assert payload["triggered_action"] == "research-integrity-reference-verification"
    assert "reference_list_entered" in payload["trigger_points"]
    assert "publication_gate_entered" in payload["trigger_points"]
    assert payload["stage_context"] == {
        "stage_id": "publication_supervision",
        "stage_event": "review_gate_entered",
        "stage_hook_ref": "stage-hook:publication_supervision:review_gate",
    }
    assert gate_bundle["surface_kind"] == "research_integrity_gate_input_bundle"
    assert payload["surfaces"]["research_integrity_reference_verification"]["surfaces"][
        "research_integrity_gate_input_bundle"
    ] == gate_bundle
    assert set(payload["required_gate_input_surfaces"]) == {
        "reference_verification_attestations",
        "claim_citation_support_matrix_v2",
        "manuscript_consistency_meta_review",
    }
    assert gate_bundle["surfaces"]["manuscript_consistency_meta_review"]["status"] == "clear"
    assert all(payload["authority_boundary"][flag] is False for flag in FORBIDDEN_AUTHORITY_FLAGS)
