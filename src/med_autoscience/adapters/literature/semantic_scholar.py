from __future__ import annotations

import json
from collections.abc import Mapping
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from med_autoscience.literature_records import LiteratureRecord


SEMANTIC_SCHOLAR_GRAPH_URL = "https://api.semanticscholar.org/graph/v1"
SEMANTIC_SCHOLAR_API_KEY_ENV = "SEMANTIC_SCHOLAR_API_KEY"
DEFAULT_PAPER_FIELDS = (
    "paperId",
    "title",
    "abstract",
    "year",
    "venue",
    "externalIds",
    "authors",
    "citationCount",
    "influentialCitationCount",
    "publicationDate",
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _optional_text(value: object) -> str | None:
    text = _text(value)
    return text or None


def _fields_param(fields: tuple[str, ...] | list[str] | None) -> str:
    selected_fields = tuple(fields or DEFAULT_PAPER_FIELDS)
    return ",".join(field.strip() for field in selected_fields if field.strip())


def _api_key(explicit_api_key: str | None) -> str:
    return _text(explicit_api_key) or _text(os.environ.get(SEMANTIC_SCHOLAR_API_KEY_ENV))


def _request(
    *,
    endpoint: str,
    query: Mapping[str, object],
    method: str = "GET",
    payload: Mapping[str, object] | None = None,
    api_key: str | None = None,
) -> Request:
    encoded_query = urlencode({key: value for key, value in query.items() if value is not None})
    url = f"{SEMANTIC_SCHOLAR_GRAPH_URL}{endpoint}"
    if encoded_query:
        url = f"{url}?{encoded_query}"
    data = json.dumps(dict(payload)).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    key = _api_key(api_key)
    if key:
        headers["x-api-key"] = key
    return Request(url, data=data, headers=headers, method=method)


def _parse_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _header_value(headers: object, key: str) -> str:
    getter = getattr(headers, "get", None)
    if callable(getter):
        return _text(getter(key))
    return ""


def _retry_after_seconds(headers: object) -> int:
    retry_after = _parse_int(_header_value(headers, "retry-after"))
    return retry_after if retry_after is not None else 0


def _rate_limit_status(headers: object, *, response_status: str) -> dict[str, object]:
    retry_after = _retry_after_seconds(headers)
    remaining = _parse_int(_header_value(headers, "x-ratelimit-remaining"))
    reset_at = _header_value(headers, "x-ratelimit-reset")
    status = "rate_limited" if response_status == "rate_limited" else "ok"
    return {
        "status": status,
        "remaining": remaining,
        "reset_at": reset_at,
        "backoff": {
            "policy": "exponential",
            "retry_after_seconds": retry_after,
        },
    }


def _decode_response(response: object) -> object:
    return json.loads(response.read().decode("utf-8"))


def _provider_response_status(error: HTTPError) -> str:
    if error.code == 429:
        return "rate_limited"
    if error.code in {500, 502, 503, 504}:
        return "provider_unavailable"
    return "provider_error"


def _fetch_json(request: Request) -> dict[str, object]:
    try:
        with urlopen(request, timeout=30) as response:
            return {
                "payload": _decode_response(response),
                "response_status": "ok",
                "rate_limit_status": _rate_limit_status(response.headers, response_status="ok"),
            }
    except HTTPError as error:
        response_status = _provider_response_status(error)
        try:
            payload = _decode_response(error)
        except (OSError, json.JSONDecodeError):
            payload = {}
        return {
            "payload": payload,
            "response_status": response_status,
            "rate_limit_status": _rate_limit_status(error.headers, response_status=response_status),
        }
    except URLError:
        return {
            "payload": {},
            "response_status": "network_unavailable",
            "rate_limit_status": {
                "status": "ok",
                "remaining": None,
                "reset_at": "",
                "backoff": {"policy": "exponential", "retry_after_seconds": 0},
            },
        }


def search_papers(
    *,
    query: str,
    limit: int = 10,
    offset: int = 0,
    fields: tuple[str, ...] | list[str] | None = None,
    api_key: str | None = None,
) -> dict[str, object]:
    normalized_query = _text(query)
    if not normalized_query:
        raise ValueError("query must not be empty")
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")
    if offset < 0:
        raise ValueError("offset must not be negative")
    request = _request(
        endpoint="/paper/search",
        query={
            "query": normalized_query,
            "limit": limit,
            "offset": offset,
            "fields": _fields_param(fields),
        },
        api_key=api_key,
    )
    return _fetch_json(request)


def match_paper(
    *,
    query: str,
    fields: tuple[str, ...] | list[str] | None = None,
    api_key: str | None = None,
) -> dict[str, object]:
    normalized_query = _text(query)
    if not normalized_query:
        raise ValueError("query must not be empty")
    request = _request(
        endpoint="/paper/search/match",
        query={
            "query": normalized_query,
            "fields": _fields_param(fields),
        },
        api_key=api_key,
    )
    return _fetch_json(request)


def fetch_paper_batch(
    *,
    paper_ids: list[str],
    fields: tuple[str, ...] | list[str] | None = None,
    api_key: str | None = None,
) -> dict[str, object]:
    ids = [_text(paper_id) for paper_id in paper_ids if _text(paper_id)]
    if not ids:
        raise ValueError("paper_ids must contain at least one non-empty id")
    request = _request(
        endpoint="/paper/batch",
        query={"fields": _fields_param(fields)},
        method="POST",
        payload={"ids": ids},
        api_key=api_key,
    )
    return _fetch_json(request)


def _external_ids(paper: Mapping[str, object]) -> Mapping[str, object]:
    raw = paper.get("externalIds")
    return raw if isinstance(raw, Mapping) else {}


def _external_id(paper: Mapping[str, object], *keys: str) -> str | None:
    external_ids = _external_ids(paper)
    lowered = {str(key).lower(): value for key, value in external_ids.items()}
    for key in keys:
        value = external_ids.get(key)
        if value is None:
            value = lowered.get(key.lower())
        text = _optional_text(value)
        if text:
            return text
    return None


def _authors(paper: Mapping[str, object]) -> tuple[str, ...]:
    raw_authors = paper.get("authors")
    if not isinstance(raw_authors, list):
        return tuple()
    authors: list[str] = []
    for raw_author in raw_authors:
        if not isinstance(raw_author, Mapping):
            continue
        name = _optional_text(raw_author.get("name"))
        if name:
            authors.append(name)
    return tuple(authors)


def _record_title(paper: Mapping[str, object], *, paper_id: str) -> str:
    title = _optional_text(paper.get("title"))
    if not title:
        raise ValueError(f"Semantic Scholar paper `{paper_id}` missing title")
    return title


def record_from_paper(
    paper: Mapping[str, object],
    *,
    relevance_role: str = "candidate",
    claim_support_scope: tuple[str, ...] = (),
) -> LiteratureRecord:
    paper_id = _optional_text(paper.get("paperId")) or _optional_text(paper.get("paper_id"))
    if not paper_id:
        raise ValueError("Semantic Scholar paper requires paperId")
    pmcid = _external_id(paper, "PMCID", "PMC")
    return LiteratureRecord(
        record_id=f"semantic_scholar:{paper_id}",
        title=_record_title(paper, paper_id=paper_id),
        authors=_authors(paper),
        year=_parse_int(paper.get("year")),
        journal=_optional_text(paper.get("venue")),
        doi=_external_id(paper, "DOI"),
        pmid=_external_id(paper, "PubMed", "PMID"),
        pmcid=pmcid.removeprefix("PMC") if pmcid and pmcid.upper().startswith("PMC") else pmcid,
        arxiv_id=_external_id(paper, "ArXiv"),
        abstract=_optional_text(paper.get("abstract")),
        full_text_availability="abstract_only" if _optional_text(paper.get("abstract")) else "metadata_only",
        source_priority=4,
        citation_payload={
            "semantic_scholar": {
                "paperId": paper_id,
                "externalIds": dict(_external_ids(paper)),
            }
        },
        local_asset_paths=(),
        relevance_role=relevance_role,
        claim_support_scope=claim_support_scope,
    )


def _paper_items(response_payload: object) -> list[Mapping[str, object]]:
    if isinstance(response_payload, Mapping):
        data = response_payload.get("data")
        if isinstance(data, list):
            return [item for item in data if isinstance(item, Mapping)]
        if response_payload.get("paperId") or response_payload.get("paper_id"):
            return [response_payload]
    if isinstance(response_payload, list):
        return [item for item in response_payload if isinstance(item, Mapping)]
    return []


def provider_payload_from_response(
    *,
    query: str,
    retrieved_at: str,
    request_id: str,
    response: Mapping[str, object],
    credential_ref: str = f"env:{SEMANTIC_SCHOLAR_API_KEY_ENV}",
    provider_response_ledger_ref: str = "",
    citation_ledger_refs: Mapping[str, str] | None = None,
    category_by_paper_id: Mapping[str, str] | None = None,
    score_by_paper_id: Mapping[str, float] | None = None,
    score_source_ref: str = "",
    cache_freshness: Mapping[str, object] | None = None,
) -> dict[str, object]:
    citation_refs = citation_ledger_refs or {}
    categories = category_by_paper_id or {}
    scores = score_by_paper_id or {}
    normalized_request_id = _text(request_id)
    if not normalized_request_id:
        raise ValueError("request_id must not be empty")
    results: list[dict[str, object]] = []
    for paper in _paper_items(response.get("payload")):
        paper_id = _optional_text(paper.get("paperId")) or _optional_text(paper.get("paper_id"))
        if not paper_id:
            continue
        result: dict[str, object] = {
            "paperId": paper_id,
            "title": _text(paper.get("title")),
            "category": _text(categories.get(paper_id)),
            "score": scores.get(paper_id),
            "score_source_ref": _text(score_source_ref),
            "citation_ledger_ref": _text(citation_refs.get(paper_id)),
        }
        results.append(result)
    provider_payload: dict[str, object] = {
        "provider": "semantic_scholar",
        "query": _text(query),
        "retrieved_at": _text(retrieved_at),
        "request_id": normalized_request_id,
        "response_status": _text(response.get("response_status")) or "ok",
        "credential_status": {
            "status": "ready" if _text(credential_ref) else "missing",
            "credential_ref": _text(credential_ref),
        },
        "rate_limit_status": dict(
            response.get("rate_limit_status")
            if isinstance(response.get("rate_limit_status"), Mapping)
            else {}
        ),
        "cache_freshness": dict(cache_freshness or {}),
        "provider_response_ledger_refs": [provider_response_ledger_ref] if _text(provider_response_ledger_ref) else [],
        "results": results,
    }
    return provider_payload


__all__ = [
    "DEFAULT_PAPER_FIELDS",
    "SEMANTIC_SCHOLAR_API_KEY_ENV",
    "SEMANTIC_SCHOLAR_GRAPH_URL",
    "fetch_paper_batch",
    "match_paper",
    "provider_payload_from_response",
    "record_from_paper",
    "search_papers",
]
