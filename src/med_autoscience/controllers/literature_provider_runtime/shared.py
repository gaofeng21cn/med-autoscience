from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SURFACE = "literature_provider_runtime"
ARTIFACT_RELATIVE_PATH = Path("artifacts/medical_paper/literature_provider_runtime.json")
REQUIRED_PROVIDERS = ("pubmed", "crossref", "semantic_scholar")
SUPPORTED_PROVIDERS = {"pubmed", "crossref", "semantic_scholar"}
UNAVAILABLE_STATUSES = {"provider_unavailable", "network_unavailable"}
PARTIAL_OUTAGE_STATUSES = {"degraded", "partial", "partial_outage"}
READY_CREDENTIAL_STATUSES = {"available", "configured", "ok", "present", "ready", "valid"}
RATE_LIMITED_STATUSES = {"backoff_required", "limited", "rate_limited", "throttled"}
STALE_CACHE_STATUSES = {"expired", "outdated", "stale"}
STALE_CITATION_STATUSES = {"expired", "outdated", "stale"}
LITERATURE_REF_CATEGORIES = {
    "anchor_papers",
    "guidelines",
    "systematic_reviews",
    "journal_neighbor_refs",
}
PROVIDER_HEALTH_CHECKS = (
    "credential_status",
    "rate_limit_backoff",
    "cache_age",
    "query_fingerprint_drift",
    "provider_response_ledger_completeness",
    "citation_ledger_completeness",
    "screening_reason_completeness",
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


def _has_text(value: object) -> bool:
    return bool(_text(value))


def _has_ref_items(value: object) -> bool:
    return any(_has_text(item) or bool(_mapping(item).get("ref")) for item in _list(value))


def _provider_name(provider: Mapping[str, Any]) -> str:
    return _text(provider.get("provider_name"))


def _provider_response_status(provider: Mapping[str, Any]) -> str:
    return _text(provider.get("response_status")) or "ok"


def _provider_refs(provider: Mapping[str, Any]) -> list[object]:
    return _list(provider.get("source_refs"))


def _provider_items(provider: Mapping[str, Any]) -> list[object]:
    for key in ("records", "items", "results"):
        items = _list(provider.get(key))
        if items:
            return items
    return []


def _provider_request_ref(provider_name: str, provider: Mapping[str, Any]) -> list[str]:
    explicit_refs = [str(item) for item in _provider_refs(provider) if _has_text(item)]
    if explicit_refs:
        return explicit_refs
    for key in ("request_id", "search_id", "run_id"):
        value = _text(provider.get(key))
        if value:
            return [f"{provider_name}:{value}"]
    return []


def _provider_response_ledger_refs(provider: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in (
        "provider_response_ledger_refs",
        "response_ledger_refs",
        "provider_ledger_refs",
    ):
        refs.extend(_text(item) for item in _list(provider.get(key)) if _has_text(item))
    for key in (
        "provider_response_ledger_ref",
        "response_ledger_ref",
        "provider_ledger_ref",
    ):
        value = _text(provider.get(key))
        if value:
            refs.append(value)
    return list(dict.fromkeys(refs))


def _provider_item_ref(provider_name: str, item: Mapping[str, Any]) -> str:
    explicit_ref = _text(item.get("ref"))
    if explicit_ref:
        return explicit_ref
    if provider_name == "pubmed":
        pmid = _text(item.get("pmid")) or _text(item.get("PMID"))
        return f"pmid:{pmid}" if pmid else ""
    if provider_name == "crossref":
        doi = _text(item.get("doi")) or _text(item.get("DOI"))
        return f"doi:{doi}" if doi else ""
    if provider_name == "semantic_scholar":
        paper_id = _text(item.get("paperId")) or _text(item.get("paper_id"))
        return f"semantic_scholar:{paper_id}" if paper_id else ""
    return ""


def _provider_item_title(item: Mapping[str, Any]) -> str:
    title = item.get("title")
    if isinstance(title, list):
        return _text(title[0]) if title else ""
    return _text(title)


def _provider_item_ledger_ref(item: Mapping[str, Any]) -> str:
    explicit_ref = _text(item.get("citation_ledger_ref"))
    if explicit_ref:
        return explicit_ref
    refs = [_text(ref) for ref in _list(item.get("citation_ledger_refs")) if _has_text(ref)]
    return refs[0] if refs else ""


def _credential_status(provider: Mapping[str, Any]) -> dict[str, Any]:
    raw = _mapping(provider.get("credential_status")) or _mapping(provider.get("credentials"))
    status = _text(raw.get("status")) or _text(provider.get("credential_status"))
    credential_ref = (
        _text(raw.get("credential_ref"))
        or _text(raw.get("source_ref"))
        or _text(raw.get("secret_ref"))
        or _text(provider.get("credential_ref"))
    )
    if not status:
        if raw.get("present") is True or provider.get("credential_present") is True:
            status = "present"
        elif raw.get("ready") is True or provider.get("credential_ready") is True:
            status = "ready"
        else:
            status = "missing"
    ready = status in READY_CREDENTIAL_STATUSES
    return {
        "status": status,
        "ready": ready,
        "credential_ref": credential_ref,
    }


def _rate_limit_status(provider: Mapping[str, Any]) -> dict[str, Any]:
    raw = _mapping(provider.get("rate_limit_status")) or _mapping(provider.get("rate_limit"))
    status = _text(raw.get("status")) or _text(provider.get("rate_limit_status")) or "ok"
    backoff = _mapping(raw.get("backoff")) or _mapping(provider.get("backoff"))
    return {
        "status": status,
        "limited": status in RATE_LIMITED_STATUSES,
        "remaining": raw.get("remaining"),
        "reset_at": _text(raw.get("reset_at")),
        "backoff": dict(backoff),
    }


def _cache_freshness(provider: Mapping[str, Any]) -> dict[str, Any]:
    raw = _mapping(provider.get("cache_freshness")) or _mapping(provider.get("cache"))
    status = _text(raw.get("status")) or _text(provider.get("cache_status")) or "fresh"
    return {
        "status": status,
        "stale": status in STALE_CACHE_STATUSES,
        "checked_at": _text(raw.get("checked_at")),
        "retrieved_at": _text(raw.get("retrieved_at")) or _text(provider.get("retrieved_at")),
        "expires_at": _text(raw.get("expires_at")),
    }


def _citation_freshness(payload: Mapping[str, Any]) -> dict[str, Any]:
    raw = _mapping(payload.get("citation_freshness")) or _mapping(payload.get("citation_ledger_freshness"))
    stale_refs = [_text(item) for item in _list(raw.get("stale_refs")) if _has_text(item)]
    status = _text(raw.get("status")) or ("stale" if stale_refs else "fresh")
    return {
        "status": status,
        "stale": status in STALE_CITATION_STATUSES or bool(stale_refs),
        "checked_at": _text(raw.get("checked_at")),
        "stale_refs": stale_refs,
    }


def _query_fingerprint(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(dict(value), ensure_ascii=False, sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _provider_query_fingerprint(provider: Mapping[str, Any]) -> str:
    return _query_fingerprint(
        {
            "provider_name": _provider_name(provider),
            "query": _text(provider.get("query")),
        }
    )
