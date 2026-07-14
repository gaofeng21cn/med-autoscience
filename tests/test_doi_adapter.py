from __future__ import annotations

from med_autoscience.adapters.literature.doi import resolve_crossref_work_from_receipts
from med_autoscience.adapters.literature.opl_connect_receipts import records_from_resolution


def test_crossref_adapter_consumes_opl_connect_receipt_without_network() -> None:
    resolution = resolve_crossref_work_from_receipts(
        doi="10.1000/example",
        provider_receipts=(
            {
                "receipt_ref": "opl://connect/references/verify/crossref-example",
                "source_refs": ["crossref:works:10.1000/example"],
                "opl_connect_reference_verification": {
                    "provider_evidence": [
                        {
                            "reference_id": "doi:10.1000/example",
                            "provider": "crossref",
                            "provider_id": "crossref",
                            "lookup_status": "found",
                            "status": "matched",
                            "match_status": "identifier_matched",
                            "matched_identifiers": {"doi": "10.1000/example"},
                            "provider_identifiers": {"doi": "10.1000/example"},
                            "metadata": {
                                "title": "Paper title",
                                "journal": "Journal of Clinical Study",
                                "year": "2023",
                            },
                            "normalized": {
                                "doi": "10.1000/example",
                                "pmid": None,
                                "title": "Paper title",
                            },
                        }
                    ]
                },
            },
        ),
    )

    assert resolution["status"] == "resolved"
    assert resolution["provider_receipt_refs"] == ["opl://connect/references/verify/crossref-example"]
    record = records_from_resolution(resolution)[0]
    assert record.record_id == "doi:10.1000/example"
    assert record.title == "Paper title"
    assert record.journal == "Journal of Clinical Study"
    assert record.year == 2023
    assert resolution["authority_boundary"]["mas_can_call_external_provider"] is False


def test_crossref_adapter_returns_request_only_without_receipt() -> None:
    resolution = resolve_crossref_work_from_receipts(doi="10.1000/missing")

    assert resolution["status"] == "request_only"
    assert resolution["records"] == []
    assert resolution["missing_provider_evidence_reference_ids"] == ["doi:10.1000/missing"]
    assert resolution["provider_resolution_request"]["action_id"] == "opl_connect_reference_verification"
