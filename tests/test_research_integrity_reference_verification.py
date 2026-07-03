from __future__ import annotations

from med_autoscience.research_integrity.reference_verification import (
    build_reference_verification_payload,
)


def test_reference_verification_consumes_existing_provider_evidence_without_network() -> None:
    payload = build_reference_verification_payload(
        payload={
            "source_refs": ["manuscript.md#refs"],
            "references": [{"id": "smith2024", "doi": "10.1000/abc", "title": "Stable Paper"}],
            "provider_evidence": [
                {
                    "provider": "crossref",
                    "reference_id": "smith2024",
                    "matched_identifiers": {"doi": "10.1000/abc"},
                    "metadata": {"title": "Stable Paper"},
                }
            ],
            "claim_spans": [
                {
                    "claim_id": "C1",
                    "citation_refs": [{"ref": "ref:smith2024"}],
                    "evidence_refs": ["analysis/results.json#/C1"],
                    "support_grade": "direct_support",
                }
            ],
        }
    )

    gate_input = payload["surfaces"]["research_integrity_gate_input_bundle"]

    assert payload["surface_kind"] == "research_integrity_reference_verification_gate_input_bundle"
    assert payload["status"] == "clear"
    assert payload["reference_count"] == 1
    assert payload["source_refs"] == ("manuscript.md#refs",)
    assert payload["provider_summary"] == {"found": 1, "not_found": 0, "error": 0}
    assert payload["surfaces"]["provider_lookup_bundle"] is None
    assert gate_input["surfaces"]["reference_verification_attestations"][0]["status"] == "verified"
    assert gate_input["surfaces"]["claim_citation_support_matrix_v2"]["claims"][0]["support_grade"] == (
        "direct_support"
    )
    assert payload["authority_boundary"]["can_call_external_provider"] is False
    assert payload["authority_boundary"]["can_write_provider_lookup_cache_or_receipt"] is False
    assert payload["authority_boundary"]["can_run_independent_professional_skill"] is False
    assert payload["authority_boundary"]["can_write_publication_eval_latest"] is False
    assert payload["authority_boundary"]["can_write_controller_decisions"] is False
    assert payload["authority_boundary"]["can_write_runtime_queue_or_provider_attempt"] is False


def test_reference_verification_triggers_provider_lookup_when_evidence_is_absent(monkeypatch) -> None:
    calls = []

    def fake_provider_lookup_bundle(**kwargs):
        calls.append(kwargs)
        return {
            "surface_kind": "reference_provider_lookup_bundle",
            "schema_version": "mas-reference-provider-lookup.v1",
            "status": "needs_review",
            "provider_summary": {"found": 0, "not_found": 0, "error": 1},
            "gate_input_bundle": {
                "surface_kind": "research_integrity_gate_input_bundle",
                "schema_version": 1,
                "status": "needs_review",
                "surfaces": {},
                "blocker_candidates": [],
                "review_candidates": [
                    {
                        "candidate_ref": "research-integrity:reference_authenticity:doe2026:unresolved",
                        "family": "reference_authenticity",
                        "target_id": "doe2026",
                        "reason": "unresolved",
                    }
                ],
                "authority_boundary": {},
            },
        }

    monkeypatch.setattr(
        "med_autoscience.research_integrity.reference_verification.build_reference_provider_lookup_bundle",
        fake_provider_lookup_bundle,
    )

    payload = build_reference_verification_payload(
        payload={
            "reference": {"id": "doe2026", "doi": "10.2000/missing"},
            "provider_config": {"providers": ["crossref"]},
            "manuscript_ref": "draft.md",
        }
    )

    assert calls[0]["references"] == ({"id": "doe2026", "doi": "10.2000/missing"},)
    assert calls[0]["provider_config"] == {"providers": ["crossref"]}
    assert payload["status"] == "needs_review"
    assert payload["manuscript_ref"] == "draft.md"
    assert payload["surfaces"]["provider_lookup_bundle"]["surface_kind"] == "reference_provider_lookup_bundle"
    assert payload["review_candidates"][0]["reason"] == "unresolved"
    assert payload["authority_boundary"]["can_call_external_provider"] is True
    assert payload["authority_boundary"]["can_write_provider_attempt"] is False
    assert payload["authority_boundary"]["can_write_runtime_queue_or_provider_attempt"] is False
