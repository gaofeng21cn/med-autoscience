from __future__ import annotations

import importlib


def test_citation_integrity_projection_blocks_metadata_only_and_missing_medical_provenance() -> None:
    module = importlib.import_module("med_autoscience.controllers.citation_integrity")

    result = module.project_citation_integrity(
        claim_segments=[
            {
                "claim_segment_id": "claim-001",
                "candidate_citation_refs": [
                    {
                        "ref_id": "ref-metadata",
                        "metadata_only": True,
                        "provenance": {"doi": "10.1000/metadata-only"},
                    },
                    {
                        "ref_id": "ref-fulltext",
                        "metadata_only": False,
                        "provenance": {
                            "doi": "10.1000/fulltext",
                            "publisher": "Nature",
                            "full_text_path": "refs/ref.pdf",
                        },
                    },
                ],
            },
            {
                "claim_segment_id": "claim-002",
                "candidate_citation_refs": [
                    {
                        "ref_id": "ref-incomplete",
                        "metadata_only": False,
                        "provenance": {"title": "Unverifiable clinical claim"},
                    }
                ],
            },
        ]
    )

    first = result["claim_segments"][0]
    second = result["claim_segments"][1]
    assert result["authority_scope"] == "submission_compliance_reviewer_input"
    assert result["can_authorize_study_truth"] is False
    assert result["can_authorize_publication_verdict"] is False
    assert result["can_authorize_artifact_authority"] is False
    assert first["claim_segment_id"] == "claim-001"
    assert first["support_grade"] == "supported"
    assert first["review_required_blocker"] is False
    assert first["candidate_citation_refs"][0]["metadata_only"] is True
    assert first["candidate_citation_refs"][0]["support_evidence_eligible"] is False
    assert first["candidate_citation_refs"][0]["blockers"] == ["metadata_only_not_support_evidence"]
    assert first["candidate_citation_refs"][1]["support_evidence_eligible"] is True
    assert first["export_ref_manager_note"] == "Export eligible supporting refs to the reference manager before submission."
    assert second["support_grade"] == "unsupported"
    assert second["review_required_blocker"] is True
    assert "missing_medical_claim_full_text_or_indexed_provenance" in second["blockers"]
