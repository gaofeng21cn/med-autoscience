from __future__ import annotations

from med_autoscience.adapters.literature.opl_connect_receipts import records_from_resolution
from med_autoscience.adapters.literature.pmc import resolve_pmc_record_from_receipts


def test_pmc_adapter_only_claims_full_text_when_receipt_scope_verifies_body() -> None:
    resolution = resolve_pmc_record_from_receipts(
        pmcid="PMC123",
        provider_receipts=(
            {
                "receipt_ref": "opl://connect/references/verify/pmc-123",
                "provider_evidence": [
                    {
                        "reference_id": "pmc:PMC123",
                        "provider": "pmc",
                        "lookup_status": "found",
                        "status": "matched",
                        "match_status": "identifier_matched",
                        "matched_identifiers": {"pmcid": "PMC123"},
                        "metadata": {"title": "Open article", "abstract": "Abstract"},
                        "verification_scope": {"full_text_body_verified": True},
                    }
                ],
            },
        ),
    )

    assert resolution["status"] == "resolved"
    record = records_from_resolution(resolution)[0]
    assert record.pmcid == "123"
    assert record.full_text_availability == "full_text"


def test_pmc_adapter_does_not_treat_provider_availability_as_verified_body() -> None:
    resolution = resolve_pmc_record_from_receipts(
        pmcid="PMC456",
        provider_receipts=(
            {
                "receipt_ref": "opl://connect/references/verify/pmc-456",
                "provider_evidence": [
                    {
                        "reference_id": "pmc:PMC456",
                        "provider": "pmc",
                        "lookup_status": "found",
                        "status": "matched",
                        "match_status": "identifier_matched",
                        "matched_identifiers": {"pmcid": "PMC456"},
                        "provider_identifiers": {"pmcid": "PMC456"},
                        "metadata": {
                            "title": "Available open article",
                            "abstract": "Abstract only in the receipt",
                            "full_text_available": True,
                        },
                        "verification_scope": {
                            "full_text_available": True,
                            "full_text_body_verified": False,
                        },
                    }
                ],
            },
        ),
    )

    record = records_from_resolution(resolution)[0]
    assert record.full_text_availability == "abstract_only"
    assert record.citation_payload["opl_connect_provider_evidence"]["verification_scope"] == {
        "full_text_available": True,
        "full_text_body_verified": False,
    }
