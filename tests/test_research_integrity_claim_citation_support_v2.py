from __future__ import annotations

import json

from med_autoscience.research_integrity.claim_citation_support_v2 import (
    build_claim_citation_support_matrix_v2,
)


def test_builds_deterministic_serializable_claim_citation_support_matrix_v2() -> None:
    result = build_claim_citation_support_matrix_v2(
        claim_spans=[
            {
                "claim_id": "C1",
                "claim_ref": "paper/claims.json#/C1",
                "claim_text": "Treatment was associated with lower mortality.",
                "support_grade": "direct_support",
            }
        ],
        citation_refs=[
            {"claim_id": "C1", "doi": "10.1000/direct"},
            {"claim_id": "C1", "pmid": "12345"},
        ],
        evidence_refs=[
            {"claim_id": "C1", "evidence_ref": "analysis/results.json#/mortality"},
        ],
        reference_attestation_refs=[
            {
                "citation_ref": "doi:10.1000/direct",
                "reference_attestation_ref": "refs/attestations.json#/direct",
                "status": "verified",
            }
        ],
    )

    assert json.loads(json.dumps(result, sort_keys=True)) == result
    assert result["surface_kind"] == "claim_citation_support_matrix_v2"
    assert result["schema_version"] == 2
    assert result["authority_boundary"] == {
        "candidate_evidence_only": True,
        "can_write_typed_blocker": False,
        "can_write_owner_receipt": False,
        "can_mutate_claims": False,
        "can_mutate_reference_attestations": False,
        "can_authorize_publication_readiness": False,
    }
    assert result["claims"] == [
        {
            "claim_id": "C1",
            "claim_ref": "paper/claims.json#/C1",
            "claim_text": "Treatment was associated with lower mortality.",
            "citation_refs": ["doi:10.1000/direct", "pmid:12345"],
            "evidence_refs": ["analysis/results.json#/mortality"],
            "support_grade": "direct_support",
        }
    ]
    assert result["citation_links"] == [
        {
            "claim_id": "C1",
            "citation_ref": "doi:10.1000/direct",
            "evidence_refs": ["analysis/results.json#/mortality"],
            "support_grade": "direct_support",
            "reference_attestations": [
                {
                    "reference_attestation_ref": "refs/attestations.json#/direct",
                    "status": "verified",
                }
            ],
        },
        {
            "claim_id": "C1",
            "citation_ref": "pmid:12345",
            "evidence_refs": ["analysis/results.json#/mortality"],
            "support_grade": "direct_support",
            "reference_attestations": [],
        },
    ]
    assert result["blocker_candidates"] == []


def test_hard_gate_candidates_are_candidate_evidence_only() -> None:
    result = build_claim_citation_support_matrix_v2(
        claim_spans=[
            {
                "claim_id": "C2",
                "citation_refs": [{"doi": "10.1000/retracted"}],
                "evidence_refs": ["analysis/results.json#/C2"],
                "support_grade": "unsupported",
            },
            {
                "claim_id": "C3",
                "citation_refs": [{"doi": "10.1000/unresolved"}],
                "evidence_refs": ["analysis/results.json#/C3"],
                "support_grade": "contradicted",
            },
        ],
        reference_attestation_refs=[
            {
                "doi": "10.1000/retracted",
                "reference_attestation_ref": "refs/attestations.json#/retracted",
                "reference_attestation_status": "retracted",
            },
            {
                "doi": "10.1000/unresolved",
                "reference_attestation_ref": "refs/attestations.json#/unresolved",
                "reference_attestation_status": "unresolved",
            },
        ],
    )

    reasons = {
        (
            candidate["claim_id"],
            candidate["reason"],
            candidate["citation_ref"],
            candidate["reference_attestation_status"],
        )
        for candidate in result["blocker_candidates"]
    }
    assert ("C2", "claim_unsupported", None, None) in reasons
    assert (
        "C2",
        "reference_attestation_retracted",
        "doi:10.1000/retracted",
        "retracted",
    ) in reasons
    assert ("C3", "claim_contradicted", None, None) in reasons
    assert (
        "C3",
        "reference_attestation_unresolved",
        "doi:10.1000/unresolved",
        "unresolved",
    ) in reasons
    assert all(candidate["hard_gate"] is True for candidate in result["blocker_candidates"])
    assert all(
        candidate["authority_boundary"]["can_write_typed_blocker"] is False
        for candidate in result["blocker_candidates"]
    )
    assert all(
        candidate["authority_boundary"]["can_write_owner_receipt"] is False
        for candidate in result["blocker_candidates"]
    )


def test_missing_support_defaults_to_unsupported_without_evidence_and_citation() -> None:
    result = build_claim_citation_support_matrix_v2(claim_spans=[{"claim_id": "C4"}])

    assert result["claims"][0]["support_grade"] == "unsupported"
    assert result["blocker_candidates"][0]["reason"] == "claim_unsupported"


def test_single_claim_accepts_unscoped_top_level_refs() -> None:
    result = build_claim_citation_support_matrix_v2(
        claim_spans=[{"claim_id": "C5"}],
        citation_refs=[{"doi": "10.1000/unscoped"}],
        evidence_refs=["analysis/results.json#/C5"],
    )

    assert result["claims"][0]["citation_refs"] == ["doi:10.1000/unscoped"]
    assert result["claims"][0]["evidence_refs"] == ["analysis/results.json#/C5"]
    assert result["claims"][0]["support_grade"] == "direct_support"
