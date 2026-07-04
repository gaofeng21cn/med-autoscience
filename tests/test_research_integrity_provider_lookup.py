from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any

import pytest

from med_autoscience.research_integrity import build_reference_provider_lookup_bundle
from med_autoscience.research_integrity.provider_lookup import PROVIDER_LOOKUP_MODE


class FakeJsonClient:
    def __init__(self, responses: Mapping[str, Mapping[str, Any] | Exception]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, Mapping[str, str], float]] = []

    def __call__(self, url: str, headers: Mapping[str, str], timeout_seconds: float) -> Mapping[str, Any]:
        self.calls.append((url, headers, timeout_seconds))
        for needle, response in self.responses.items():
            if needle in url:
                if isinstance(response, Exception):
                    raise response
                return response
        raise AssertionError(f"unexpected provider URL: {url}")


def test_provider_lookup_verifies_reference_through_crossref_doi() -> None:
    client = FakeJsonClient(
        {
            "api.crossref.org/works/10.1000%2Fabc": {
                "message": {
                    "DOI": "10.1000/ABC",
                    "title": ["A Mature Classifier Paper"],
                    "container-title": ["Medical AI"],
                    "published-print": {"date-parts": [[2024, 1, 2]]},
                }
            }
        }
    )

    bundle = build_reference_provider_lookup_bundle(
        references=[{"id": "smith2024", "doi": "10.1000/ABC", "title": "A mature classifier paper"}],
        provider_config={"providers": ["crossref"], "mailto": "ops@example.org"},
        http_get_json=client,
    )

    reference = bundle["references"][0]
    evidence = reference["provider_evidence"][0]

    assert bundle["surface_kind"] == "reference_provider_lookup_bundle"
    assert bundle["provider_lookup_mode"] == PROVIDER_LOOKUP_MODE
    assert bundle["receipt_first"] is True
    assert bundle["transition_only"] is True
    assert bundle["live_provider_authority_claimed"] is False
    assert bundle["authoritative_provider_truth_owner"] == "OPL Connect provider receipts"
    assert bundle["status"] == "clear"
    assert bundle["provider_summary"] == {"found": 1, "not_found": 0, "error": 0}
    assert reference["attestation"]["status"] == "verified"
    assert evidence["provider"] == "crossref"
    assert evidence["lookup_status"] == "found"
    assert evidence["matched_identifiers"] == {"doi": "10.1000/abc"}
    assert evidence["metadata"] == {
        "title": "A Mature Classifier Paper",
        "year": "2024",
        "journal": "Medical AI",
    }
    assert "mailto=ops%40example.org" in client.calls[0][0]
    assert client.calls[0][1]["User-Agent"].endswith("(mailto:ops@example.org)")
    assert bundle["authority_boundary"]["can_call_external_provider"] is True
    assert bundle["authority_boundary"]["provider_lookup_mode"] == PROVIDER_LOOKUP_MODE
    assert bundle["authority_boundary"]["receipt_first"] is True
    assert bundle["authority_boundary"]["transition_only"] is True
    assert bundle["authority_boundary"]["live_provider_authority_claimed"] is False
    assert bundle["authority_boundary"]["can_claim_live_provider_truth"] is False
    assert (
        bundle["authority_boundary"]["can_be_used_as_authoritative_provider_truth_without_opl_receipt"]
        is False
    )
    assert bundle["authority_boundary"]["can_write_mas_study_truth"] is False
    assert bundle["authority_boundary"]["can_write_runtime_queue_or_provider_attempt"] is False
    assert bundle["authority_boundary"]["can_write_provider_attempt"] is False


def test_provider_lookup_contract_declares_receipt_first_transition_only_boundary() -> None:
    contract = json.loads(
        (Path(__file__).resolve().parents[1] / "contracts/research-integrity-layer.json").read_text()
    )

    boundary = contract["provider_lookup_boundary"]
    target = contract["implementation_contract"]["provider_lookup_target"]

    assert boundary["provider_lookup_mode"] == PROVIDER_LOOKUP_MODE
    assert boundary["receipt_first"] is True
    assert boundary["transition_only"] is True
    assert boundary["live_provider_authority_claimed"] is False
    assert boundary["authoritative_provider_truth_owner"] == "OPL Connect provider receipts"
    assert boundary["can_claim_live_provider_truth"] is False
    assert boundary["can_be_used_as_authoritative_provider_truth_without_opl_receipt"] is False
    assert boundary["can_materialize_provider_receipt"] is False
    assert "Claude Science equivalent online verification" in boundary["forbidden_claims"]
    assert target["provider_lookup_mode"] == PROVIDER_LOOKUP_MODE
    assert target["receipt_first"] is True
    assert target["live_provider_authority_claimed"] is False


def test_provider_lookup_resolves_pubmed_from_doi_then_builds_gate_input() -> None:
    client = FakeJsonClient(
        {
            "esearch.fcgi": {"esearchresult": {"idlist": ["12345678"]}},
            "esummary.fcgi": {
                "result": {
                    "uids": ["12345678"],
                    "12345678": {
                        "uid": "12345678",
                        "title": "Clinical Evidence Paper",
                        "fulljournalname": "Journal of Clinical Evidence",
                        "pubdate": "2025 Jan",
                        "articleids": [
                            {"idtype": "pubmed", "value": "12345678"},
                            {"idtype": "doi", "value": "10.2000/evidence"},
                        ],
                    },
                }
            },
        }
    )

    bundle = build_reference_provider_lookup_bundle(
        references={"id": "clinical2025", "doi": "10.2000/evidence", "title": "Clinical Evidence Paper"},
        provider_config={"providers": ["pubmed"], "ncbi_email": "ops@example.org", "ncbi_api_key": "secret"},
        http_get_json=client,
        claim_spans=[
            {
                "claim_id": "C1",
                "citation_refs": [{"ref": "ref:clinical2025"}],
                "evidence_refs": ["analysis/results.json#/C1"],
                "support_grade": "direct_support",
            }
        ],
    )

    assert bundle["references"][0]["attestation"]["status"] == "verified"
    assert bundle["references"][0]["provider_evidence"][0]["matched_identifiers"] == {
        "pmid": "12345678",
        "doi": "10.2000/evidence",
    }
    assert bundle["gate_input_bundle"]["status"] == "clear"
    assert bundle["gate_input_bundle"]["surfaces"]["claim_citation_support_matrix_v2"]["claims"][0][
        "support_grade"
    ] == "direct_support"
    assert all("api_key=secret" in call[0] for call in client.calls)
    assert all("api_key=%3Credacted%3E" not in call[0] for call in client.calls)
    assert bundle["references"][0]["provider_evidence"][0]["request_url"].endswith("api_key=%3Credacted%3E")


def test_provider_lookup_errors_or_missing_credentials_become_review_evidence_not_authority() -> None:
    client = FakeJsonClient({"api.crossref.org": RuntimeError("temporary provider outage")})

    bundle = build_reference_provider_lookup_bundle(
        references={"title": "Unresolved Citation"},
        provider_config={"providers": ["crossref", "openalex"]},
        http_get_json=client,
    )

    reference = bundle["references"][0]
    statuses = [evidence["lookup_status"] for evidence in reference["provider_evidence"]]

    assert reference["reference_id"].startswith("ref_")
    assert statuses == ["error", "error"]
    assert reference["attestation"]["status"] == "unresolved"
    assert bundle["status"] == "needs_review"
    assert bundle["gate_input_bundle"]["review_candidates"][0]["family"] == "reference_authenticity"
    assert bundle["gate_input_bundle"]["review_candidates"][0]["reason"] == "unresolved"
    assert bundle["authority_boundary"]["can_authorize_publication_readiness"] is False
    assert bundle["authority_boundary"]["can_authorize_submission_readiness"] is False


def test_provider_lookup_openalex_uses_key_but_redacts_surface_url() -> None:
    client = FakeJsonClient(
        {
            "api.openalex.org/works/https%3A%2F%2Fdoi.org%2F10.3000%2Fopen": {
                "id": "https://openalex.org/W123",
                "doi": "https://doi.org/10.3000/open",
                "title": "OpenAlex Indexed Paper",
                "publication_year": 2026,
                "primary_location": {"source": {"display_name": "Open Medicine"}},
            }
        }
    )

    bundle = build_reference_provider_lookup_bundle(
        references={"id": "open2026", "doi": "10.3000/open"},
        provider_config={"providers": ["openalex"], "openalex_api_key": "openalex-secret"},
        http_get_json=client,
    )

    evidence = bundle["references"][0]["provider_evidence"][0]

    assert "api_key=openalex-secret" in client.calls[0][0]
    assert "openalex-secret" not in evidence["request_url"]
    assert evidence["request_url"].endswith("api_key=%3Credacted%3E")
    assert evidence["matched_identifiers"]["doi"] == "10.3000/open"
    assert evidence["matched_identifiers"]["openalex"] == "https://openalex.org/W123"
    assert bundle["references"][0]["attestation"]["status"] == "verified"


def test_provider_lookup_semantic_scholar_uses_graph_api_and_api_key_header() -> None:
    client = FakeJsonClient(
        {
            "api.semanticscholar.org/graph/v1/paper/DOI%3A10.4000%2Fs2": {
                "paperId": "S2P123",
                "externalIds": {"DOI": "10.4000/S2", "PubMed": "987654"},
                "title": "Semantic Scholar Indexed Paper",
                "year": 2025,
                "publicationVenue": {"name": "Evidence Graphs"},
            }
        }
    )

    bundle = build_reference_provider_lookup_bundle(
        references={"id": "s2-2025", "doi": "10.4000/s2", "title": "Semantic Scholar Indexed Paper"},
        provider_config={"providers": ["semantic-scholar"], "semantic_scholar_api_key": "s2-secret"},
        http_get_json=client,
    )

    evidence = bundle["references"][0]["provider_evidence"][0]

    assert client.calls[0][1]["x-api-key"] == "s2-secret"
    assert evidence["provider"] == "semantic_scholar"
    assert evidence["lookup_status"] == "found"
    assert evidence["matched_identifiers"] == {
        "semantic_scholar": "S2P123",
        "doi": "10.4000/s2",
        "pmid": "987654",
    }
    assert evidence["metadata"] == {
        "title": "Semantic Scholar Indexed Paper",
        "year": "2025",
        "journal": "Evidence Graphs",
    }
    assert evidence["provider_limitations"]["does_not_assert_retraction_status"] is True
    assert bundle["references"][0]["attestation"]["status"] == "verified"


def test_provider_lookup_crossmark_reads_crossref_update_metadata_without_publication_authority() -> None:
    client = FakeJsonClient(
        {
            "api.crossref.org/works/10.5000%2Fcrossmark": {
                "message": {
                    "DOI": "10.5000/crossmark",
                    "title": ["Crossmark Indexed Paper"],
                    "container-title": ["Journal Updates"],
                    "published-online": {"date-parts": [[2024, 3, 4]]},
                    "relation": {"is-retracted-by": [{"id": "10.5000/retraction"}]},
                    "update-policy": "https://doi.org/10.5555/crossmark-policy",
                }
            }
        }
    )

    bundle = build_reference_provider_lookup_bundle(
        references={"id": "crossmark2024", "doi": "10.5000/crossmark"},
        provider_config={"providers": ["crossmark"], "mailto": "ops@example.org"},
        http_get_json=client,
    )

    evidence = bundle["references"][0]["provider_evidence"][0]

    assert evidence["provider"] == "crossmark"
    assert evidence["lookup_status"] == "found"
    assert evidence["matched_identifiers"] == {"doi": "10.5000/crossmark"}
    assert evidence["retraction_or_update_flags"]["retracted"] is True
    assert evidence["provider_limitations"]["publisher_update_policy_presence_is_not_publication_readiness"] is True
    assert bundle["references"][0]["attestation"]["status"] == "retracted"
    assert bundle["authority_boundary"]["can_assert_publisher_or_crossmark_status_without_provider_receipt"] is False


def test_provider_lookup_publisher_requires_opl_connector_receipt_instead_of_faking_status() -> None:
    bundle = build_reference_provider_lookup_bundle(
        references={"id": "publisher2025", "doi": "10.6000/publisher", "title": "Publisher Landing Page"},
        provider_config={"providers": ["publisher"]},
        http_get_json=FakeJsonClient({}),
    )

    evidence = bundle["references"][0]["provider_evidence"][0]

    assert evidence["provider"] == "publisher"
    assert evidence["lookup_status"] == "error"
    assert evidence["error"]["code"] == "publisher_connector_required"
    assert evidence["provider_receipt_required"] is True
    assert evidence["provider_limitations"]["expected_owner"] == "OPL Connect publisher connector"
    assert bundle["status"] == "needs_review"
    assert bundle["provider_summary"] == {"found": 0, "not_found": 0, "error": 1}


def test_provider_lookup_rejects_unsupported_provider() -> None:
    with pytest.raises(ValueError, match="unsupported provider lookup provider"):
        build_reference_provider_lookup_bundle(
            references={"id": "bad"},
            provider_config={"providers": ["google_scholar"]},
            http_get_json=FakeJsonClient({}),
        )
