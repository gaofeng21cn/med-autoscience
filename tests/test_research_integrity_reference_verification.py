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


def test_reference_verification_consumes_provider_receipts_without_network(monkeypatch) -> None:
    def fail_provider_lookup_bundle(**_kwargs):
        raise AssertionError("provider receipts with evidence must not call MAS thin provider lookup")

    monkeypatch.setattr(
        "med_autoscience.research_integrity.reference_verification.build_reference_provider_lookup_bundle",
        fail_provider_lookup_bundle,
    )

    payload = build_reference_verification_payload(
        payload={
            "source_refs": ["paper/references.bib"],
            "references": [
                {"id": "smith2024", "doi": "10.1000/abc", "title": "Stable Paper"},
                {"id": "lee2025", "doi": "10.1000/missing", "title": "Missing Paper"},
                {"id": "ng2026", "pmid": "999", "title": "Provider Error Paper"},
            ],
            "provider_receipts": [
                {
                    "receipt_ref": "opl-connect/receipts/crossref-smith.json",
                    "source_refs": ["crossref:works:10.1000/abc"],
                    "provider_evidence": [
                        {
                            "provider": "crossref",
                            "reference_id": "smith2024",
                            "lookup_status": "found",
                            "matched_identifiers": {"doi": "10.1000/abc"},
                            "metadata": {"title": "Stable Paper"},
                        }
                    ],
                },
                {
                    "receipt_ref": "opl-connect/receipts/openalex-lee.json",
                    "source_refs": ["openalex:W123"],
                    "references": [
                        {
                            "reference_id": "lee2025",
                            "provider_evidence": [
                                {
                                    "provider": "openalex",
                                    "reference_id": "lee2025",
                                    "lookup_status": "not_found",
                                    "matched_identifiers": {},
                                    "metadata": {},
                                }
                            ],
                        }
                    ],
                },
                {
                    "ref": "opl-connect/receipts/pubmed-ng.json",
                    "opl_connect_reference_verification": {
                        "source_refs": ["pubmed:999"],
                        "provider_evidence": [
                            {
                                "provider": "pubmed",
                                "reference_id": "ng2026",
                                "lookup_status": "error",
                                "matched_identifiers": {},
                                "metadata": {},
                                "error": {"code": "provider_timeout"},
                            }
                        ],
                    },
                },
            ],
        }
    )

    assert payload["provider_summary"] == {"found": 1, "not_found": 1, "error": 1}
    assert payload["surfaces"]["provider_lookup_bundle"] is None
    assert payload["provider_receipt_refs"] == (
        "opl-connect/receipts/crossref-smith.json",
        "opl-connect/receipts/openalex-lee.json",
        "opl-connect/receipts/pubmed-ng.json",
    )
    assert payload["source_refs"] == (
        "paper/references.bib",
        "crossref:works:10.1000/abc",
        "openalex:W123",
        "pubmed:999",
    )
    assert payload["authority_boundary"]["can_call_external_provider"] is False
    assert payload["authority_boundary"]["can_write_provider_lookup_cache_or_receipt"] is False
    assert payload["authority_boundary"]["can_write_owner_receipt"] is False
    assert payload["authority_boundary"]["can_sign_owner_receipt"] is False


def test_reference_verification_triggers_provider_lookup_when_receipts_have_no_evidence(monkeypatch) -> None:
    calls = []

    def fake_provider_lookup_bundle(**kwargs):
        calls.append(kwargs)
        return {
            "surface_kind": "reference_provider_lookup_bundle",
            "schema_version": "mas-reference-provider-lookup.v1",
            "status": "clear",
            "provider_summary": {"found": 1, "not_found": 0, "error": 0},
            "gate_input_bundle": {
                "surface_kind": "research_integrity_gate_input_bundle",
                "schema_version": 1,
                "status": "clear",
                "surfaces": {},
                "blocker_candidates": [],
                "review_candidates": [],
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
            "provider_receipts": [
                {
                    "receipt_ref": "opl-connect/receipts/empty-doe.json",
                    "source_refs": ["opl-connect:lookup:doe2026"],
                }
            ],
        }
    )

    assert calls[0]["references"] == ({"id": "doe2026", "doi": "10.2000/missing"},)
    assert payload["surfaces"]["provider_lookup_bundle"]["surface_kind"] == "reference_provider_lookup_bundle"
    assert payload["provider_receipt_refs"] == ("opl-connect/receipts/empty-doe.json",)
    assert payload["source_refs"] == ("opl-connect:lookup:doe2026",)
    assert payload["authority_boundary"]["can_call_external_provider"] is True


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
