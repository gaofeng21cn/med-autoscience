from __future__ import annotations

import importlib
import json
from dataclasses import asdict

import pytest


class _Response:
    def __init__(self, payload: object, *, headers: dict[str, str] | None = None) -> None:
        self._payload = payload
        self.headers = headers or {}
        self.status = 200

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_search_papers_uses_graph_search_endpoint_and_api_key_header(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.adapters.literature.semantic_scholar")
    requests: list[object] = []

    def fake_urlopen(request: object, timeout: int) -> _Response:
        requests.append(request)
        assert timeout == 30
        return _Response(
            {
                "total": 1,
                "offset": 0,
                "data": [
                    {
                        "paperId": "S2PAPER1",
                        "title": "Semantic Scholar neighbor",
                        "year": 2025,
                        "venue": "JAMA Internal Medicine",
                    }
                ],
            },
            headers={
                "x-ratelimit-remaining": "99",
                "x-ratelimit-reset": "2026-05-24T00:00:00Z",
            },
        )

    monkeypatch.setattr(module, "urlopen", fake_urlopen)

    result = module.search_papers(
        query="pituitary endocrine prediction",
        limit=5,
        fields=("paperId", "title", "year", "venue"),
        api_key="secret-key",
    )

    request = requests[0]
    assert request.full_url.startswith("https://api.semanticscholar.org/graph/v1/paper/search?")
    assert "query=pituitary+endocrine+prediction" in request.full_url
    assert "limit=5" in request.full_url
    assert "fields=paperId%2Ctitle%2Cyear%2Cvenue" in request.full_url
    assert request.get_header("X-api-key") == "secret-key"
    assert result["response_status"] == "ok"
    assert result["rate_limit_status"] == {
        "status": "ok",
        "remaining": 99,
        "reset_at": "2026-05-24T00:00:00Z",
        "backoff": {"policy": "exponential", "retry_after_seconds": 0},
    }
    assert result["payload"]["data"][0]["paperId"] == "S2PAPER1"


def test_fetch_paper_batch_posts_ids_and_keeps_null_results(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.adapters.literature.semantic_scholar")
    requests: list[object] = []

    def fake_urlopen(request: object, timeout: int) -> _Response:
        requests.append(request)
        assert timeout == 30
        return _Response(
            [
                {
                    "paperId": "S2PAPER1",
                    "title": "Semantic Scholar neighbor",
                    "externalIds": {"DOI": "10.1000/neighbor", "PubMed": "12345678"},
                },
                None,
            ]
        )

    monkeypatch.setattr(module, "urlopen", fake_urlopen)

    result = module.fetch_paper_batch(
        paper_ids=["S2PAPER1", "missing-paper"],
        fields=("paperId", "title", "externalIds"),
        api_key=None,
    )

    request = requests[0]
    assert request.full_url.startswith("https://api.semanticscholar.org/graph/v1/paper/batch?")
    assert request.get_method() == "POST"
    assert json.loads(request.data.decode("utf-8")) == {"ids": ["S2PAPER1", "missing-paper"]}
    assert result["payload"][0]["paperId"] == "S2PAPER1"
    assert result["payload"][1] is None
    assert result["response_status"] == "ok"


def test_record_from_paper_crosswalks_semantic_scholar_metadata_to_literature_record() -> None:
    module = importlib.import_module("med_autoscience.adapters.literature.semantic_scholar")

    record = module.record_from_paper(
        {
            "paperId": "S2PAPER1",
            "title": "Semantic Scholar neighbor",
            "year": 2025,
            "venue": "JAMA Internal Medicine",
            "abstract": "Structured abstract",
            "authors": [{"name": "A Author"}, {"name": "B Author"}],
            "externalIds": {"DOI": "10.1000/neighbor", "PubMed": "12345678"},
        },
        relevance_role="journal_fit_neighbor",
        claim_support_scope=("paper_framing", "journal_fit_neighbor"),
    )

    assert asdict(record) == {
        "record_id": "semantic_scholar:S2PAPER1",
        "title": "Semantic Scholar neighbor",
        "authors": ("A Author", "B Author"),
        "year": 2025,
        "journal": "JAMA Internal Medicine",
        "doi": "10.1000/neighbor",
        "pmid": "12345678",
        "pmcid": None,
        "arxiv_id": None,
        "abstract": "Structured abstract",
        "full_text_availability": "abstract_only",
        "source_priority": 4,
        "citation_payload": {
            "semantic_scholar": {
                "paperId": "S2PAPER1",
                "externalIds": {"DOI": "10.1000/neighbor", "PubMed": "12345678"},
            }
        },
        "local_asset_paths": (),
        "relevance_role": "journal_fit_neighbor",
        "claim_support_scope": ("paper_framing", "journal_fit_neighbor"),
    }


def test_provider_payload_from_response_emits_runtime_ready_provenance() -> None:
    module = importlib.import_module("med_autoscience.adapters.literature.semantic_scholar")

    provider_payload = module.provider_payload_from_response(
        query="clinical endocrinology pituitary invasive biomarker",
        retrieved_at="2026-05-24T09:30:00Z",
        request_id="semantic-scholar-2026-05-24",
        response={
            "payload": {
                "data": [
                    {
                        "paperId": "S2PAPER1",
                        "title": "Semantic Scholar neighbor",
                        "year": 2025,
                        "venue": "JAMA Internal Medicine",
                    }
                ]
            },
            "response_status": "ok",
            "rate_limit_status": {
                "status": "ok",
                "remaining": 12,
                "reset_at": "2026-05-24T10:00:00Z",
                "backoff": {"policy": "exponential", "retry_after_seconds": 0},
            },
        },
        credential_ref="env:SEMANTIC_SCHOLAR_API_KEY",
        provider_response_ledger_ref="ops/provider_responses/semantic-scholar-2026-05-24.json",
        citation_ledger_refs={"S2PAPER1": "paper/evidence_ledger.json#semantic-S2PAPER1"},
        category_by_paper_id={"S2PAPER1": "journal_neighbor_refs"},
        score_by_paper_id={"S2PAPER1": 0.91},
        score_source_ref="semantic_scholar:semantic-scholar-2026-05-24",
        cache_freshness={
            "status": "fresh",
            "checked_at": "2026-05-24T09:31:00Z",
            "expires_at": "2026-05-25T09:31:00Z",
        },
    )

    assert provider_payload == {
        "provider": "semantic_scholar",
        "query": "clinical endocrinology pituitary invasive biomarker",
        "retrieved_at": "2026-05-24T09:30:00Z",
        "request_id": "semantic-scholar-2026-05-24",
        "response_status": "ok",
        "credential_status": {
            "status": "ready",
            "credential_ref": "env:SEMANTIC_SCHOLAR_API_KEY",
        },
        "rate_limit_status": {
            "status": "ok",
            "remaining": 12,
            "reset_at": "2026-05-24T10:00:00Z",
            "backoff": {"policy": "exponential", "retry_after_seconds": 0},
        },
        "cache_freshness": {
            "status": "fresh",
            "checked_at": "2026-05-24T09:31:00Z",
            "expires_at": "2026-05-25T09:31:00Z",
        },
        "provider_response_ledger_refs": [
            "ops/provider_responses/semantic-scholar-2026-05-24.json"
        ],
        "results": [
            {
                "paperId": "S2PAPER1",
                "title": "Semantic Scholar neighbor",
                "category": "journal_neighbor_refs",
                "score": 0.91,
                "score_source_ref": "semantic_scholar:semantic-scholar-2026-05-24",
                "citation_ledger_ref": "paper/evidence_ledger.json#semantic-S2PAPER1",
            }
        ],
    }


def test_provider_payload_marks_rate_limited_response_as_blockable() -> None:
    module = importlib.import_module("med_autoscience.adapters.literature.semantic_scholar")

    provider_payload = module.provider_payload_from_response(
        query="clinical endocrinology pituitary invasive biomarker",
        retrieved_at="2026-05-24T09:30:00Z",
        request_id="semantic-scholar-2026-05-24",
        response={
            "payload": {},
            "response_status": "rate_limited",
            "rate_limit_status": {
                "status": "rate_limited",
                "remaining": 0,
                "reset_at": "2026-05-24T10:00:00Z",
                "backoff": {"policy": "exponential", "retry_after_seconds": 900},
            },
        },
        credential_ref="env:SEMANTIC_SCHOLAR_API_KEY",
        provider_response_ledger_ref="ops/provider_responses/semantic-scholar-2026-05-24.json",
    )

    assert provider_payload["response_status"] == "rate_limited"
    assert provider_payload["rate_limit_status"]["status"] == "rate_limited"
    assert provider_payload["rate_limit_status"]["backoff"]["retry_after_seconds"] == 900


def test_record_from_paper_rejects_missing_semantic_scholar_identity() -> None:
    module = importlib.import_module("med_autoscience.adapters.literature.semantic_scholar")

    with pytest.raises(ValueError, match="paperId"):
        module.record_from_paper({"title": "Missing paper id"})
