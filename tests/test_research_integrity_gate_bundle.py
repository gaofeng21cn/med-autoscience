from __future__ import annotations

import json

from med_autoscience.research_integrity import build_research_integrity_gate_input_bundle


def test_research_integrity_gate_input_bundle_blocks_hard_integrity_findings() -> None:
    result = build_research_integrity_gate_input_bundle(
        reference_checks=[
            {
                "reference": {"id": "ref1", "doi": "10.1000/source", "title": "Original"},
                "provider_evidence": [
                    {
                        "provider": "crossref",
                        "matched_identifiers": {"doi": "10.1000/source"},
                        "retraction_or_update_flags": {"retracted": True},
                    }
                ],
            }
        ],
        claim_spans=[
            {
                "claim_id": "C1",
                "citation_refs": [{"ref": "ref:ref1"}],
                "evidence_refs": ["analysis/results.json#/C1"],
                "support_grade": "direct_support",
            }
        ],
        manuscript_sections={
            "abstract": {"numeric_facts": [_fact("cohort_n", 100)]},
            "results": {"numeric_facts": [_fact("cohort_n", 101)]},
        },
    )

    assert json.loads(json.dumps(result, sort_keys=True)) == result
    assert result["surface_kind"] == "research_integrity_gate_input_bundle"
    assert result["status"] == "blocked"
    reasons = {(item["family"], item["reason"]) for item in result["blocker_candidates"]}
    assert ("reference_authenticity", "retracted") in reasons
    assert result["surfaces"]["claim_citation_support_matrix_v2"]["blocker_candidates"][0][
        "reason"
    ] == "reference_attestation_retracted"
    assert result["surfaces"]["manuscript_consistency_meta_review"]["status"] == "blocked"
    assert all(value is False for value in result["authority_boundary"].values())


def test_research_integrity_gate_input_bundle_separates_review_candidates() -> None:
    result = build_research_integrity_gate_input_bundle(
        reference_checks=[
            {
                "reference": {"id": "ref2", "doi": "10.1000/source", "title": "Original"},
                "provider_evidence": [
                    {
                        "provider": "semantic_scholar",
                        "matched_identifiers": {"doi": "10.1000/source"},
                        "metadata": {"title": "Corrected"},
                    }
                ],
            }
        ],
        claim_spans=[
            {
                "claim_id": "C2",
                "citation_refs": [{"ref": "ref:ref2"}],
                "evidence_refs": ["analysis/results.json#/C2"],
                "support_grade": "partial_support",
            }
        ],
        manuscript_sections={"abstract": {"numeric_facts": [_fact("event_rate", "7.5", unit="%")]}},
        reporting_checklist_expectations=[
            {"item_id": "optional_threshold_rationale", "status": "missing", "required": False}
        ],
    )

    assert result["status"] == "needs_review"
    assert result["blocker_candidates"] == []
    families = {item["family"] for item in result["review_candidates"]}
    assert families == {
        "reference_authenticity",
        "claim_citation_support",
        "manuscript_consistency",
    }


def _fact(fact_id: str, value: object, *, unit: str = "patients") -> dict[str, object]:
    return {
        "fact_id": fact_id,
        "reported_value": value,
        "unit": unit,
        "population": "eligible cohort",
        "window": "2018-2022",
    }
