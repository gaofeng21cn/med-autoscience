from __future__ import annotations

from med_autoscience.adapters.literature.opl_connect_receipts import records_from_resolution
from med_autoscience.adapters.literature.semantic_scholar import (
    resolve_semantic_scholar_records_from_receipts,
)


def test_semantic_scholar_adapter_consumes_canonical_opl_connect_receipt() -> None:
    resolution = resolve_semantic_scholar_records_from_receipts(
        references=(
            {
                "id": "doi:10.1000/neighbor",
                "doi": "10.1000/neighbor",
                "title": "Semantic Scholar neighbor",
            },
        ),
        provider_receipts=(
            {
                "receipt_ref": "opl://connect/references/verify/semantic-neighbor",
                "opl_connect_reference_verification": {
                    "surface_kind": "opl_connect_reference_verification_readonly",
                    "provider_evidence": [
                        {
                            "reference_id": "doi:10.1000/neighbor",
                            "provider": "semantic_scholar",
                            "provider_id": "semantic-scholar",
                            "lookup_status": "found",
                            "status": "matched",
                            "match_status": "identifier_matched",
                            "matched_identifiers": {"doi": "10.1000/neighbor"},
                            "provider_identifiers": {
                                "doi": "10.1000/neighbor",
                                "pmid": "12345678",
                                "semantic_scholar": "S2PAPER1",
                            },
                            "metadata": {
                                "title": "Semantic Scholar neighbor",
                                "year": "2025",
                                "journal": "JAMA Internal Medicine",
                            },
                            "normalized": {
                                "doi": "10.1000/neighbor",
                                "pmid": "12345678",
                                "title": "Semantic Scholar neighbor",
                            },
                        }
                    ],
                },
            },
        ),
    )

    assert resolution["status"] == "resolved"
    record = records_from_resolution(resolution)[0]
    assert record.record_id == "pmid:12345678"
    assert record.doi == "10.1000/neighbor"
    assert record.journal == "JAMA Internal Medicine"
    assert record.source_priority == 4


def test_semantic_scholar_adapter_rejects_metadata_conflict_as_missing_evidence() -> None:
    resolution = resolve_semantic_scholar_records_from_receipts(
        references=({"id": "doi:10.1000/conflict", "doi": "10.1000/conflict"},),
        provider_receipts=(
            {
                "receipt_ref": "opl://connect/references/verify/conflict",
                "provider_evidence": [
                    {
                        "reference_id": "doi:10.1000/conflict",
                        "provider": "semantic_scholar",
                        "lookup_status": "found",
                        "status": "deferred",
                        "match_status": "metadata_conflict",
                        "matched_identifiers": {},
                        "metadata": {"title": "Wrong paper"},
                    }
                ],
            },
        ),
    )

    assert resolution["status"] == "missing_evidence"
    assert resolution["records"] == []
