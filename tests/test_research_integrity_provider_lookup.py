from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from med_autoscience.research_integrity import build_reference_provider_lookup_bundle


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
    assert bundle["authority_boundary"]["can_write_mas_study_truth"] is False
    assert bundle["authority_boundary"]["can_write_runtime_queue_or_provider_attempt"] is False
    assert bundle["authority_boundary"]["can_write_provider_attempt"] is False


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


def test_provider_lookup_rejects_unsupported_provider() -> None:
    with pytest.raises(ValueError, match="unsupported provider lookup provider"):
        build_reference_provider_lookup_bundle(
            references={"id": "bad"},
            provider_config={"providers": ["google_scholar"]},
            http_get_json=FakeJsonClient({}),
        )
