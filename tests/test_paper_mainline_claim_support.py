from __future__ import annotations

from med_autoscience.paper_mainline_claim_support import build_claim_citation_support_matrix


NO_AUTHORITY_BOUNDARY = {
    "can_write_mas_truth": False,
    "can_mutate_paper_body": False,
    "can_authorize_quality_verdict": False,
    "can_authorize_publication_readiness": False,
    "can_run_external_search": False,
}


def test_builds_refs_only_progress_first_claim_citation_support_matrix() -> None:
    result = build_claim_citation_support_matrix(
        [
            {
                "claim_id": "A1",
                "claim_ref": "paper/claim_evidence_map.json#/claims/A1",
                "evidence_refs": [
                    "paper/evidence_ledger.json#/claims/A1/evidence/E1",
                    {"evidence_ref": "artifacts/stage_outputs/evidence/E2.json"},
                ],
                "citation_refs": [{"doi": "10.1038/example-primary"}, {"pmid": "12345678"}],
                "support_grade": "supportive",
                "source_tier": "peer_reviewed_primary_source",
                "checked_at": "2026-06-18T00:00:00Z",
            }
        ]
    )

    assert result["status"] == "complete"
    assert result["refs_only"] is result["fail_open"] is True
    assert result["mainline_waits_for_support_matrix"] is False
    assert result["can_block_current_owner_action"] is False
    assert result["missing_required_refs"] == result["typed_blocker_candidates"] == []
    assert result["authority_boundary"] == NO_AUTHORITY_BOUNDARY
    entry = result["matrix_entries"][0]
    assert entry["evidence_refs"] == [
        "paper/evidence_ledger.json#/claims/A1/evidence/E1",
        "artifacts/stage_outputs/evidence/E2.json",
    ]
    assert entry["citation_refs"] == ["doi:10.1038/example-primary", "pmid:12345678"]


def test_typed_blocker_candidates_are_fail_open_and_non_authoritative() -> None:
    result = build_claim_citation_support_matrix(
        [
            {"claim_id": "missing", "support_grade": "strong"},
            {
                "claim_id": "metadata",
                "claim_ref": "claim:metadata",
                "evidence_refs": ["evidence:metadata"],
                "citation_refs": ["doi:metadata"],
                "support_grade": "metadata_only",
                "source_tier": "metadata_record",
                "checked_at": "2026-06-18T00:00:00Z",
                "metadata_only_candidate_flag": True,
            },
            {
                "claim_id": "limiting",
                "claim_ref": "claim:limiting",
                "evidence_refs": ["evidence:limiting"],
                "citation_refs": ["doi:limiting"],
                "support_grade": "contradictory",
                "source_tier": "peer_reviewed_primary_source",
                "checked_at": "2026-06-18T00:00:00Z",
                "contradictory_or_limiting_refs": ["doi:limiting"],
            },
            {
                "claim_id": "stale",
                "claim_ref": "claim:stale",
                "evidence_refs": ["evidence:stale"],
                "citation_refs": ["doi:stale"],
                "support_grade": "partial",
                "source_tier": "peer_reviewed_primary_source",
                "checked_at": "2020-01-01T00:00:00Z",
                "expires_or_stale_after": "2020-01-02T00:00:00Z",
            },
        ]
    )

    assert result["status"] == "typed_blocker_candidate"
    assert result["refs_only"] is result["fail_open"] is True
    assert result["can_block_current_owner_action"] is False
    assert result["authority_boundary"] == NO_AUTHORITY_BOUNDARY
    reasons = {(item["claim_id"], item["reason"]) for item in result["typed_blocker_candidates"]}
    assert reasons == {
        ("missing", "invalid_support_grade"),
        ("missing", "missing_required_ref"),
        ("metadata", "metadata_only_candidate"),
        ("limiting", "contradictory_or_limiting_refs_present"),
        ("stale", "support_stale_after_expiry"),
    }
