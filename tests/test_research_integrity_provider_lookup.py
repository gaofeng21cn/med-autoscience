from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from med_autoscience.research_integrity import (
    build_reference_provider_receipt_consumption_bundle,
)
from med_autoscience.research_integrity.provider_lookup import PROVIDER_LOOKUP_MODE


def _matched_crossref(reference_id: str = "smith2024") -> dict[str, Any]:
    return {
        "reference_id": reference_id,
        "provider": "crossref",
        "provider_id": "crossref",
        "lookup_status": "found",
        "status": "matched",
        "match_status": "identifier_matched",
        "matched_identifiers": {"doi": "10.1000/abc"},
        "metadata": {
            "title": "A Mature Classifier Paper",
            "year": "2024",
            "journal": "Medical AI",
        },
        "retraction_or_update_flags": {},
        "receipt_ref": "opl://connect/references/verify/crossref-smith2024",
    }


def test_provider_lookup_consumes_host_supplied_opl_connect_evidence() -> None:
    bundle = build_reference_provider_receipt_consumption_bundle(
        references=[
            {
                "id": "smith2024",
                "doi": "10.1000/ABC",
                "title": "A Mature Classifier Paper",
            }
        ],
        provider_config={"providers": ["crossref"]},
        provider_evidence=[_matched_crossref()],
    )

    assert bundle["provider_lookup_mode"] == PROVIDER_LOOKUP_MODE
    assert bundle["provider_resolution_action"] == "opl_connect_reference_verification"
    assert bundle["provider_evidence_input_only"] is True
    assert bundle["provider_receipt_required"] is False
    assert bundle["provider_summary"] == {"found": 1, "not_found": 0, "error": 0}
    assert bundle["references"][0]["attestation"]["status"] == "verified"
    assert bundle["status"] == "clear"
    assert bundle["authority_boundary"]["provider_lookup_owner"] == "OPL Connect"
    assert bundle["authority_boundary"]["mas_can_call_external_provider"] is False
    assert bundle["authority_boundary"]["can_invoke_opl_connect"] is False


def test_provider_lookup_preserves_domain_claim_support_gate() -> None:
    bundle = build_reference_provider_receipt_consumption_bundle(
        references={
            "id": "clinical2025",
            "doi": "10.1000/abc",
            "title": "A Mature Classifier Paper",
        },
        provider_config={"providers": ["crossref"]},
        provider_evidence=[_matched_crossref("clinical2025")],
        claim_spans=[
            {
                "claim_id": "C1",
                "citation_refs": [{"ref": "ref:clinical2025"}],
                "evidence_refs": ["analysis/results.json#/C1"],
                "support_grade": "direct_support",
            }
        ],
    )

    matrix = bundle["gate_input_bundle"]["surfaces"]["claim_citation_support_matrix_v2"]
    assert matrix["claims"][0]["support_grade"] == "direct_support"


def test_provider_lookup_keeps_connector_errors_as_non_authorizing_review_evidence() -> None:
    bundle = build_reference_provider_receipt_consumption_bundle(
        references={"id": "unresolved", "title": "Unresolved Citation"},
        provider_config={"providers": ["crossref"]},
        provider_evidence=[
            {
                "reference_id": "unresolved",
                "provider": "crossref",
                "provider_id": "crossref",
                "lookup_status": "error",
                "status": "deferred",
                "matched_identifiers": {},
                "metadata": {},
                "retraction_or_update_flags": {},
                "error": {"code": "provider_unavailable"},
            }
        ],
    )

    assert bundle["status"] == "needs_review"
    assert bundle["references"][0]["attestation"]["status"] == "unresolved"
    assert bundle["authority_boundary"]["can_authorize_publication_readiness"] is False
    assert bundle["authority_boundary"]["can_materialize_provider_receipt"] is False


def test_provider_lookup_contract_declares_opl_connect_transport_boundary() -> None:
    contract = json.loads(
        (Path(__file__).resolve().parents[1] / "contracts/research-integrity-layer.json").read_text()
    )

    boundary = contract["provider_lookup_boundary"]
    target = contract["implementation_contract"]["provider_lookup_target"]
    assert boundary["provider_lookup_mode"] == PROVIDER_LOOKUP_MODE
    assert boundary["provider_lookup_owner"] == "OPL Connect"
    assert boundary["mas_can_call_external_provider"] is False
    assert boundary["can_invoke_opl_connect"] is False
    assert boundary["provider_evidence_input_only"] is True
    assert target["owner"] == "OPL Connect"
    assert target["mas_role"] == "consume_provider_receipts_and_apply_medical_gate_judgment"
    assert "falls back to OPL Connect" not in target["provider_evidence_consumption"]


def test_missing_provider_evidence_requests_host_resolution_without_invoking_transport() -> None:
    bundle = build_reference_provider_receipt_consumption_bundle(
        references={"id": "missing", "doi": "10.1000/missing"},
        provider_config={"providers": ["crossref"]},
    )

    assert bundle["status"] == "needs_review"
    assert bundle["provider_receipt_required"] is True
    assert bundle["missing_provider_evidence_reference_ids"] == ["missing"]
    assert bundle["provider_resolution_action"] == "opl_connect_reference_verification"
    assert bundle["authority_boundary"]["can_call_external_provider"] is False


def test_provider_lookup_rejects_unsupported_provider() -> None:
    with pytest.raises(ValueError, match="unsupported provider lookup provider"):
        build_reference_provider_receipt_consumption_bundle(
            references={"id": "bad"},
            provider_config={"providers": ["google_scholar"]},
        )
