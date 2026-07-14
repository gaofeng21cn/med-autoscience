from __future__ import annotations

from med_autoscience.adapters.literature.opl_connect_receipts import (
    SUPPORTED_REQUEST_PROVIDERS,
    records_from_resolution,
    resolve_literature_records_from_receipts,
)


def test_request_contract_includes_framework_pubmed_and_pmc_providers() -> None:
    assert "pubmed" in SUPPORTED_REQUEST_PROVIDERS
    assert "pmc" in SUPPORTED_REQUEST_PROVIDERS


def test_receipt_resolution_filters_provider_and_preserves_structured_authors() -> None:
    resolution = resolve_literature_records_from_receipts(
        references=({"id": "pmid:123", "pmid": "123"},),
        providers=("pubmed",),
        accepted_evidence_providers=("pubmed",),
        provider_receipts=(
            {
                "receipt_ref": "opl://connect/references/verify/mixed",
                "provider_evidence": [
                    {
                        "reference_id": "pmid:123",
                        "provider": "crossref",
                        "lookup_status": "found",
                        "status": "matched",
                        "match_status": "identifier_matched",
                        "matched_identifiers": {"pmid": "123"},
                        "metadata": {"title": "Wrong provider"},
                    },
                    {
                        "reference_id": "pmid:123",
                        "provider": "pubmed",
                        "lookup_status": "found",
                        "status": "matched",
                        "match_status": "identifier_matched",
                        "matched_identifiers": {"pmid": "123"},
                        "provider_identifiers": {"pmid": "123", "pmcid": "PMC999"},
                        "metadata": {
                            "title": "Canonical PubMed record",
                            "authors": [
                                {"given": "Ada", "family": "Lovelace"},
                                {"name": "Grace Hopper"},
                            ],
                        },
                    },
                ],
            },
        ),
    )

    record = records_from_resolution(resolution)[0]
    assert record.title == "Canonical PubMed record"
    assert record.authors == ("Ada Lovelace", "Grace Hopper")
    assert record.pmcid == "999"
    assert resolution["provider_resolution_request"]["providers"] == ["pubmed"]


def test_missing_receipt_is_request_only_and_never_claims_transport_authority() -> None:
    resolution = resolve_literature_records_from_receipts(
        references=({"id": "pmid:404", "pmid": "404"},),
        providers=("pubmed",),
    )

    assert resolution["status"] == "request_only"
    assert resolution["records"] == []
    assert resolution["provider_resolution_request"]["request_only"] is True
    assert resolution["authority_boundary"]["mas_can_call_external_provider"] is False
    assert resolution["authority_boundary"]["can_materialize_provider_receipt"] is False


def test_receipt_reference_id_cannot_override_mismatched_identifier_evidence() -> None:
    resolution = resolve_literature_records_from_receipts(
        references=({"id": "pmid:123", "pmid": "123"},),
        providers=("pubmed",),
        accepted_evidence_providers=("pubmed",),
        provider_receipts=(
            {
                "receipt_ref": "opl://connect/references/verify/mismatched-pmid",
                "provider_evidence": [
                    {
                        "reference_id": "pmid:123",
                        "provider": "pubmed",
                        "lookup_status": "found",
                        "status": "matched",
                        "match_status": "identifier_matched",
                        "matched_identifiers": {"pmid": "999"},
                        "metadata": {"title": "Different paper"},
                    }
                ],
            },
        ),
    )

    assert resolution["status"] == "missing_evidence"
    assert resolution["records"] == []
    assert resolution["missing_provider_evidence_reference_ids"] == ["pmid:123"]


def test_framework_connect_output_preserves_nested_receipt_identity() -> None:
    receipt_ref = "opl://connect/references/verify/pubmed-123"
    resolution = resolve_literature_records_from_receipts(
        references=({"id": "pmid:123", "pmid": "123"},),
        providers=("pubmed",),
        accepted_evidence_providers=("pubmed",),
        provider_receipts=(
            {
                "opl_connect_reference_verification": {
                    "provider_evidence": [
                        {
                            "reference_id": "pmid:123",
                            "provider": "pubmed",
                            "lookup_status": "found",
                            "status": "matched",
                            "match_status": "identifier_matched",
                            "receipt_ref": receipt_ref,
                            "matched_identifiers": {"pmid": "123"},
                            "metadata": {"title": "Canonical Framework receipt"},
                        }
                    ],
                    "provider_receipts": [
                        {
                            "reference_id": "pmid:123",
                            "provider_id": "pubmed",
                            "status": "matched",
                            "receipt_ref": receipt_ref,
                        }
                    ],
                }
            },
        ),
    )

    assert resolution["status"] == "resolved"
    assert resolution["provider_receipt_refs"] == [receipt_ref]
    assert records_from_resolution(resolution)[0].title == "Canonical Framework receipt"


def test_receipt_resolution_rejects_evidence_without_receipt_identity() -> None:
    resolution = resolve_literature_records_from_receipts(
        references=({"id": "pmid:123", "pmid": "123"},),
        providers=("pubmed",),
        accepted_evidence_providers=("pubmed",),
        provider_receipts=(
            {
                "provider_evidence": [
                    {
                        "reference_id": "pmid:123",
                        "provider": "pubmed",
                        "lookup_status": "found",
                        "status": "matched",
                        "match_status": "identifier_matched",
                        "matched_identifiers": {"pmid": "123"},
                        "metadata": {"title": "Unbound evidence"},
                    }
                ],
            },
        ),
    )

    assert resolution["status"] == "missing_evidence"
    assert resolution["records"] == []
    assert resolution["provider_receipt_refs"] == []
