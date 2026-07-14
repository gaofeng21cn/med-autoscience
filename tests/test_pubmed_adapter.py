from __future__ import annotations

from med_autoscience.adapters.literature.opl_connect_receipts import records_from_resolution
from med_autoscience.adapters.literature.pubmed import resolve_pubmed_summaries_from_receipts


def test_pubmed_adapter_consumes_host_receipt_metadata() -> None:
    resolution = resolve_pubmed_summaries_from_receipts(
        pmids=["12345"],
        provider_receipts=(
            {
                "receipt_ref": "opl://connect/references/verify/pubmed-12345",
                "provider_evidence": [
                    {
                        "reference_id": "pmid:12345",
                        "provider": "pubmed",
                        "lookup_status": "found",
                        "status": "matched",
                        "match_status": "identifier_matched",
                        "matched_identifiers": {"pmid": "12345"},
                        "metadata": {
                            "title": "Paper title",
                            "journal": "BMC Medicine",
                            "year": "2024",
                        },
                    }
                ],
            },
        ),
    )

    assert resolution["status"] == "resolved"
    record = records_from_resolution(resolution)[0]
    assert record.pmid == "12345"
    assert record.journal == "BMC Medicine"
    assert record.title == "Paper title"
    assert record.year == 2024


def test_pubmed_adapter_returns_missing_evidence_for_empty_receipt() -> None:
    resolution = resolve_pubmed_summaries_from_receipts(
        pmids=["12345"],
        provider_receipts=({"receipt_ref": "opl://connect/references/verify/empty"},),
    )

    assert resolution["status"] == "missing_evidence"
    assert resolution["provider_resolution_request"]["identifier_provider"] == "pubmed"
    assert resolution["authority_boundary"]["can_materialize_provider_receipt"] is False
