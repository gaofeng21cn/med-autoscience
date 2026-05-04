from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.literature_provider_runtime_parts.shared import (
    _has_text,
    _list,
    _mapping,
    _provider_item_ledger_ref,
    _provider_item_ref,
    _provider_item_title,
    _provider_items,
    _provider_name,
    _provider_refs,
    _provider_request_ref,
    _provider_response_ledger_refs,
    _provider_response_status,
    _text,
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
                    "score": item.get("score"),
                    "score_source_ref": _text(item.get("score_source_ref")),
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
