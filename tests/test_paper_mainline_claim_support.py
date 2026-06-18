from __future__ import annotations

from med_autoscience.paper_mainline_claim_support import build_claim_citation_support_matrix


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
                "citation_refs": [
                    {"doi": "10.1038/example-primary"},
                    {"pmid": "12345678"},
                ],
                "support_grade": "supportive",
                "source_tier": "peer_reviewed_primary_source",
                "checked_at": "2026-06-18T00:00:00Z",
            }
        ]
    )

    assert result["status"] == "complete"
    assert result["refs_only"] is True
    assert result["fail_open"] is True
    assert result["mainline_waits_for_support_matrix"] is False
    assert result["can_block_current_owner_action"] is False
    assert result["missing_required_refs"] == []
    assert result["typed_blocker_candidates"] == []
    assert result["source_refs"]["external_skill_refs"] == [
        "nature-skills@1609daf:skills/nature-academic-search",
        "nature-skills@1609daf:skills/nature-citation",
    ]
    assert result["source_refs"]["mas_contract_refs"] == ["citation_integrity_pack"]
    assert result["authority_boundary"] == {
        "can_write_mas_truth": False,
        "can_mutate_paper_body": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_run_external_search": False,
    }

    entry = result["matrix_entries"][0]
    assert entry == {
        "claim_id": "A1",
        "claim_ref": "paper/claim_evidence_map.json#/claims/A1",
        "evidence_refs": [
            "paper/evidence_ledger.json#/claims/A1/evidence/E1",
            "artifacts/stage_outputs/evidence/E2.json",
        ],
        "citation_refs": ["doi:10.1038/example-primary", "pmid:12345678"],
        "support_grade": "supportive",
        "source_tier": "peer_reviewed_primary_source",
        "checked_at": "2026-06-18T00:00:00Z",
        "expires_or_stale_after": None,
        "metadata_only_candidate_flag": False,
        "contradictory_or_limiting_refs": [],
        "status": "complete",
        "typed_blocker_candidate_refs": [],
    }


def test_typed_blocker_candidates_are_fail_open_and_non_authoritative() -> None:
    result = build_claim_citation_support_matrix(
        [
            {
                "claim_id": "A2",
                "claim_ref": "",
                "evidence_refs": [],
                "citation_refs": [],
                "support_grade": "strong",
                "source_tier": "",
                "checked_at": "",
            },
            {
                "claim_id": "A3",
                "claim_ref": "paper/claim_evidence_map.json#/claims/A3",
                "evidence_refs": ["paper/evidence_ledger.json#/claims/A3/evidence/E1"],
                "citation_refs": ["doi:10.1038/metadata-only"],
                "support_grade": "metadata_only",
                "source_tier": "metadata_record",
                "checked_at": "2026-06-18T00:00:00Z",
                "metadata_only_candidate_flag": True,
            },
            {
                "claim_id": "A4",
                "claim_ref": "paper/claim_evidence_map.json#/claims/A4",
                "evidence_refs": ["paper/evidence_ledger.json#/claims/A4/evidence/E1"],
                "citation_refs": ["doi:10.1038/limiting"],
                "support_grade": "contradictory",
                "source_tier": "peer_reviewed_primary_source",
                "checked_at": "2026-06-18T00:00:00Z",
                "contradictory_or_limiting_refs": [{"doi": "10.1038/limiting"}],
            },
            {
                "claim_id": "A5",
                "claim_ref": "paper/claim_evidence_map.json#/claims/A5",
                "evidence_refs": ["paper/evidence_ledger.json#/claims/A5/evidence/E1"],
                "citation_refs": ["doi:10.1038/stale"],
                "support_grade": "partial",
                "source_tier": "peer_reviewed_primary_source",
                "checked_at": "2020-01-01T00:00:00Z",
                "expires_or_stale_after": "2020-01-02T00:00:00Z",
            },
        ]
    )

    assert result["status"] == "typed_blocker_candidate"
    assert result["refs_only"] is True
    assert result["fail_open"] is True
    assert result["mainline_waits_for_support_matrix"] is False
    assert result["can_block_current_owner_action"] is False
    assert all(value is False for value in result["authority_boundary"].values())

    missing = {
        (item["claim_id"], item["field"], item["reason"])
        for item in result["missing_required_refs"]
    }
    assert ("A2", "claim_ref", "missing_required_ref") in missing
    assert ("A2", "evidence_refs", "missing_required_ref") in missing
    assert ("A2", "citation_refs", "missing_required_ref") in missing
    assert ("A2", "source_tier", "missing_required_field") in missing
    assert ("A2", "checked_at", "missing_required_field") in missing

    blocker_reasons = {
        (candidate["claim_id"], candidate["reason"])
        for candidate in result["typed_blocker_candidates"]
    }
    assert ("A2", "invalid_support_grade") in blocker_reasons
    assert ("A2", "missing_required_ref") in blocker_reasons
    assert ("A3", "metadata_only_candidate") in blocker_reasons
    assert ("A4", "contradictory_or_limiting_refs_present") in blocker_reasons
    assert ("A5", "support_stale_after_expiry") in blocker_reasons

    entries = {entry["claim_id"]: entry for entry in result["matrix_entries"]}
    assert entries["A2"]["support_grade"] == "strong"
    assert entries["A2"]["status"] == "typed_blocker_candidate"
    assert entries["A3"]["metadata_only_candidate_flag"] is True
    assert entries["A4"]["contradictory_or_limiting_refs"] == ["doi:10.1038/limiting"]
    assert entries["A5"]["expires_or_stale_after"] == "2020-01-02T00:00:00Z"
