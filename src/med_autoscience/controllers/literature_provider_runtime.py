from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = 1
SURFACE = "literature_provider_runtime"
ARTIFACT_RELATIVE_PATH = Path("artifacts/medical_paper/literature_provider_runtime.json")
REQUIRED_PROVIDERS = ("pubmed", "crossref", "semantic_scholar")
SUPPORTED_PROVIDERS = {"pubmed", "crossref", "semantic_scholar"}
UNAVAILABLE_STATUSES = {"provider_unavailable", "network_unavailable"}
READY_CREDENTIAL_STATUSES = {"available", "configured", "ok", "present", "ready", "valid"}
RATE_LIMITED_STATUSES = {"backoff_required", "limited", "rate_limited", "throttled"}
STALE_CACHE_STATUSES = {"expired", "outdated", "stale"}
LITERATURE_REF_CATEGORIES = {
    "anchor_papers",
    "guidelines",
    "systematic_reviews",
    "journal_neighbor_refs",
}


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


def _normalize_provider_backed_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    raw_providers = [provider for provider in _list(payload.get("provider_payloads")) if isinstance(provider, Mapping)]
    if not raw_providers:
        return _normalize_direct_provider_payload(payload)

    providers: list[dict[str, Any]] = []
    citation_ledger_refs: list[str] = []
    missing_ledger_providers: list[str] = []
    for raw_provider in raw_providers:
        provider_name = _text(raw_provider.get("provider_name")) or _text(raw_provider.get("provider"))
        source_refs = _provider_request_ref(provider_name, raw_provider)
        normalized_items: list[dict[str, Any]] = []
        provider_missing_ledger_ref = False
        for raw_item in _provider_items(raw_provider):
            item = _mapping(raw_item)
            ref = _provider_item_ref(provider_name, item)
            if not ref:
                continue
            ledger_ref = _provider_item_ledger_ref(item)
            if not ledger_ref:
                provider_missing_ledger_ref = True
            else:
                citation_ledger_refs.append(ledger_ref)
            normalized_items.append(
                {
                    "ref": ref,
                    "category": _text(item.get("category")),
                    "title": _provider_item_title(item),
                    "citation_ledger_ref": ledger_ref,
                }
            )
        if provider_missing_ledger_ref and provider_name:
            missing_ledger_providers.append(provider_name)
        providers.append(
            {
                "provider_name": provider_name,
                "query": _text(raw_provider.get("query")) or _text(payload.get("query")),
                "retrieved_at": _text(raw_provider.get("retrieved_at")),
                "source_refs": source_refs,
                "response_status": _provider_response_status(raw_provider),
                "credential_status": raw_provider.get("credential_status"),
                "credentials": raw_provider.get("credentials"),
                "credential_ref": _text(raw_provider.get("credential_ref")),
                "credential_present": raw_provider.get("credential_present"),
                "credential_ready": raw_provider.get("credential_ready"),
                "rate_limit_status": raw_provider.get("rate_limit_status"),
                "rate_limit": raw_provider.get("rate_limit"),
                "backoff": dict(_mapping(raw_provider.get("backoff"))),
                "cache_freshness": raw_provider.get("cache_freshness"),
                "cache": raw_provider.get("cache"),
                "cache_status": raw_provider.get("cache_status"),
                "provider_response_ledger_refs": _provider_response_ledger_refs(raw_provider),
                "items": normalized_items,
            }
        )

    normalized = dict(payload)
    normalized["providers"] = providers
    normalized["citation_ledger_refs"] = list(dict.fromkeys(citation_ledger_refs))
    normalized["_missing_provider_citation_ledger_refs"] = missing_ledger_providers
    normalized["search_strategy"] = {
        **dict(_mapping(payload.get("search_strategy"))),
        "query": _text(_mapping(payload.get("search_strategy")).get("query")) or _text(payload.get("query")),
    }
    return normalized


def _normalize_direct_provider_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    providers = _providers(normalized)
    if not providers:
        return normalized

    citation_ledger_refs = [_text(ref) for ref in _list(normalized.get("citation_ledger_refs")) if _has_text(ref)]
    missing_ledger_providers: list[str] = []
    for provider in providers:
        provider_name = _provider_name(provider)
        provider_missing_ledger_ref = False
        for raw_item in _list(provider.get("items")):
            item = _mapping(raw_item)
            if not _has_text(item.get("ref")):
                continue
            ledger_ref = _provider_item_ledger_ref(item)
            if not ledger_ref:
                provider_missing_ledger_ref = True
            else:
                citation_ledger_refs.append(ledger_ref)
        if provider_missing_ledger_ref and provider_name:
            missing_ledger_providers.append(provider_name)

    normalized["citation_ledger_refs"] = list(dict.fromkeys(citation_ledger_refs))
    normalized["_missing_provider_citation_ledger_refs"] = missing_ledger_providers
    return normalized


def _screening_decisions_are_complete(value: object) -> bool:
    decisions = [item for item in _list(value) if isinstance(item, Mapping)]
    if not decisions:
        return False
    for decision in decisions:
        if _text(decision.get("decision")) not in {"include", "exclude"}:
            return False
        if not _has_text(decision.get("reason")):
            return False
    return True


def _providers(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [provider for provider in _list(payload.get("providers")) if isinstance(provider, Mapping)]


def _missing_reason(payload: Mapping[str, Any]) -> str:
    providers = _providers(payload)
    if not providers:
        return "missing_provider_sources"
    for provider in providers:
        name = _provider_name(provider)
        if not name:
            return "missing_provider_name"
        if name not in SUPPORTED_PROVIDERS:
            return f"unsupported_provider_{name}"
    provider_names = {_provider_name(provider) for provider in providers}
    for required_provider in REQUIRED_PROVIDERS:
        if required_provider not in provider_names:
            return f"missing_provider_sources_{required_provider}"
    for provider in providers:
        name = _provider_name(provider)
        if not _credential_status(provider)["ready"]:
            return f"missing_credential_{name}"
        status = _provider_response_status(provider)
        if status in UNAVAILABLE_STATUSES:
            return f"provider_unavailable_{name}"
        if _rate_limit_status(provider)["limited"]:
            return f"rate_limited_{name}"
        if _cache_freshness(provider)["stale"]:
            return f"stale_cache_{name}"
        if not _has_text(provider.get("query")):
            return f"missing_provider_query_{name}"
        if not _has_text(provider.get("retrieved_at")):
            return f"missing_provider_retrieved_at_{name}"
        if not _has_ref_items(_provider_refs(provider)):
            return f"missing_provider_source_refs_{name}"
        if not _has_ref_items(_provider_response_ledger_refs(provider)):
            return f"missing_provider_response_ledger_{name}"
    missing_ledger_providers = [_text(item) for item in _list(payload.get("_missing_provider_citation_ledger_refs"))]
    if missing_ledger_providers:
        return f"missing_provider_citation_ledger_refs_{missing_ledger_providers[0]}"
    if not _has_text(payload.get("search_date")):
        return "missing_search_date"
    if not _has_ref_items(payload.get("citation_ledger_refs")):
        return "missing_citation_ledger_refs"
    if not _screening_decisions_are_complete(payload.get("screening_decisions")):
        return "missing_screening_decision_reason"
    return ""


def _source_response_digest(providers: list[Mapping[str, Any]]) -> dict[str, Any]:
    statuses = sorted({_provider_response_status(provider) for provider in providers})
    return {
        "provider_count": len(providers),
        "source_ref_count": sum(len(_provider_refs(provider)) for provider in providers),
        "item_count": sum(len(_list(provider.get("items"))) for provider in providers),
        "response_statuses": statuses,
    }


def _provider_source_refs(providers: list[Mapping[str, Any]]) -> list[object]:
    refs: list[object] = []
    for provider in providers:
        refs.extend(_provider_refs(provider))
    return refs


def _all_provider_response_ledger_refs(providers: list[Mapping[str, Any]]) -> list[str]:
    refs: list[str] = []
    for provider in providers:
        refs.extend(_provider_response_ledger_refs(provider))
    return list(dict.fromkeys(refs))


def _credential_status_by_provider(providers: list[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        _provider_name(provider): _credential_status(provider)
        for provider in providers
        if _provider_name(provider)
    }


def _rate_limit_status_by_provider(providers: list[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        _provider_name(provider): _rate_limit_status(provider)
        for provider in providers
        if _provider_name(provider)
    }


def _backoff_by_provider(providers: list[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        _provider_name(provider): dict(_rate_limit_status(provider).get("backoff") or {})
        for provider in providers
        if _provider_name(provider)
    }


def _cache_freshness_by_provider(providers: list[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        _provider_name(provider): _cache_freshness(provider)
        for provider in providers
        if _provider_name(provider)
    }


def _provider_query_fingerprints(providers: list[Mapping[str, Any]]) -> dict[str, str]:
    return {
        _provider_name(provider): _provider_query_fingerprint(provider)
        for provider in providers
        if _provider_name(provider)
    }


def _aggregate_query_fingerprint(
    payload: Mapping[str, Any],
    providers: list[Mapping[str, Any]],
) -> str:
    return _query_fingerprint(
        {
            "query": _text(payload.get("query")) or _text(_mapping(payload.get("search_strategy")).get("query")),
            "search_strategy": dict(_mapping(payload.get("search_strategy"))),
            "providers": [
                {
                    "provider_name": _provider_name(provider),
                    "query": _text(provider.get("query")),
                }
                for provider in providers
            ],
        }
    )


def _authority_contract() -> dict[str, Any]:
    return {
        "authority": "provider_operations_read_model_only",
        "can_authorize_quality": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
    }


def _provider_operations(
    *,
    payload: Mapping[str, Any],
    providers: list[Mapping[str, Any]],
    missing_reason: str,
) -> dict[str, Any]:
    return {
        "contract": "production_provider_operations",
        "required_providers": list(REQUIRED_PROVIDERS),
        "status": "ready" if not missing_reason else "blocked",
        "missing_reason": missing_reason,
        "credential_status": _credential_status_by_provider(providers),
        "rate_limit_status": _rate_limit_status_by_provider(providers),
        "backoff": _backoff_by_provider(providers),
        "query_fingerprint": _aggregate_query_fingerprint(payload, providers),
        "provider_query_fingerprints": _provider_query_fingerprints(providers),
        "cache_freshness": _cache_freshness_by_provider(providers),
        "provider_response_ledger_refs": _all_provider_response_ledger_refs(providers),
        "authority_contract": _authority_contract(),
    }


def _provider_provenance(providers: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "provider_name": _provider_name(provider),
            "query": _text(provider.get("query")),
            "retrieved_at": _text(provider.get("retrieved_at")),
            "response_status": _provider_response_status(provider),
            "source_refs": _provider_refs(provider),
        }
        for provider in providers
    ]


def _categorized_refs(providers: list[Mapping[str, Any]]) -> dict[str, list[object]]:
    categorized = {category: [] for category in LITERATURE_REF_CATEGORIES}
    for provider in providers:
        for item in _list(provider.get("items")):
            source_item = _mapping(item)
            category = _text(source_item.get("category"))
            ref = source_item.get("ref")
            if category in categorized and _has_text(ref):
                categorized[category].append(ref)
    return categorized


def _literature_intelligence_payload(
    payload: Mapping[str, Any],
    providers: list[Mapping[str, Any]],
) -> dict[str, Any]:
    categorized = _categorized_refs(providers)
    return {
        "search_strategy": dict(_mapping(payload.get("search_strategy"))),
        "search_date": _text(payload.get("search_date")),
        "searched_sources": _provider_source_refs(providers),
        "anchor_papers": categorized["anchor_papers"],
        "guidelines": categorized["guidelines"],
        "systematic_reviews": categorized["systematic_reviews"],
        "journal_neighbor_refs": categorized["journal_neighbor_refs"],
        "screening_decisions": _list(payload.get("screening_decisions")),
        "citation_ledger_refs": _list(payload.get("citation_ledger_refs")),
    }


def build_literature_provider_runtime_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    payload = _normalize_provider_backed_payload(payload)
    providers = _providers(payload)
    missing_reason = _missing_reason(payload)
    provider_operations = _provider_operations(
        payload=payload,
        providers=providers,
        missing_reason=missing_reason,
    )
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "status": "ready" if not missing_reason else "blocked",
        "missing_reason": missing_reason,
        "providers": [_provider_name(provider) for provider in providers],
        "provider_provenance": _provider_provenance(providers),
        "query": _text(payload.get("query")) or _text(_mapping(payload.get("search_strategy")).get("query")),
        "search_date": _text(payload.get("search_date")),
        "search_strategy": dict(_mapping(payload.get("search_strategy"))),
        "citation_ledger_refs": _list(payload.get("citation_ledger_refs")),
        "screening_decisions": _list(payload.get("screening_decisions")),
        "source_response_digest": _source_response_digest(providers),
        "provider_operations": provider_operations,
        "credential_status": provider_operations["credential_status"],
        "rate_limit_status": provider_operations["rate_limit_status"],
        "backoff": provider_operations["backoff"],
        "query_fingerprint": provider_operations["query_fingerprint"],
        "cache_freshness": provider_operations["cache_freshness"],
        "provider_response_ledger_refs": provider_operations["provider_response_ledger_refs"],
        "authority_contract": _authority_contract(),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "literature_intelligence_payload": _literature_intelligence_payload(payload, providers),
    }


def stable_literature_provider_runtime_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / ARTIFACT_RELATIVE_PATH).resolve()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def materialize_literature_provider_runtime(
    *,
    study_root: Path,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    path = stable_literature_provider_runtime_path(study_root=study_root)
    projection = build_literature_provider_runtime_projection(payload)
    artifact = dict(projection)
    artifact["study_root"] = str(Path(study_root).expanduser().resolve())
    _write_json(path, artifact)
    return {
        "surface": SURFACE,
        "status": projection["status"],
        "missing_reason": projection["missing_reason"],
        "artifact_path": str(path),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "provider_provenance": projection["provider_provenance"],
        "provider_operations": projection["provider_operations"],
        "credential_status": projection["credential_status"],
        "rate_limit_status": projection["rate_limit_status"],
        "backoff": projection["backoff"],
        "query_fingerprint": projection["query_fingerprint"],
        "cache_freshness": projection["cache_freshness"],
        "provider_response_ledger_refs": projection["provider_response_ledger_refs"],
        "authority_contract": projection["authority_contract"],
        "citation_ledger_refs": projection["citation_ledger_refs"],
        "literature_intelligence_payload": projection["literature_intelligence_payload"],
    }
