from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.literature_provider_runtime_parts.shared import (
    ARTIFACT_RELATIVE_PATH,
    LITERATURE_REF_CATEGORIES,
    PARTIAL_OUTAGE_STATUSES,
    PROVIDER_HEALTH_CHECKS,
    RATE_LIMITED_STATUSES,
    REQUIRED_PROVIDERS,
    SCHEMA_VERSION,
    SUPPORTED_PROVIDERS,
    SURFACE,
    UNAVAILABLE_STATUSES,
    _cache_freshness,
    _citation_freshness,
    _credential_status,
    _has_ref_items,
    _has_text,
    _list,
    _mapping,
    _provider_name,
    _provider_query_fingerprint,
    _provider_refs,
    _provider_response_ledger_refs,
    _provider_response_status,
    _query_fingerprint,
    _rate_limit_status,
    _text,
)
from med_autoscience.controllers.literature_provider_runtime_parts.provider_payloads import (
    _normalize_provider_backed_payload,
    _providers,
    _screening_decisions_are_complete,
)


def _keyword_terms_are_complete(payload: Mapping[str, Any]) -> bool:
    strategy = _mapping(payload.get("search_strategy"))
    return _has_ref_items(strategy.get("keywords")) or _has_ref_items(payload.get("keywords"))


def _search_strategy_is_complete(payload: Mapping[str, Any]) -> bool:
    strategy = _mapping(payload.get("search_strategy"))
    return _has_text(strategy.get("query")) and _has_ref_items(strategy.get("mesh_terms"))


def _study_rationale(payload: Mapping[str, Any]) -> str:
    for key in ("why_worth_doing", "study_rationale", "research_rationale", "rationale"):
        value = _text(payload.get(key))
        if value:
            return value
    return ""


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


def _high_score_neighbor_refs(providers: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for provider in providers:
        for item in _list(provider.get("items")):
            source_item = _mapping(item)
            if _text(source_item.get("category")) != "journal_neighbor_refs":
                continue
            ref = _text(source_item.get("ref"))
            score_source_ref = _text(source_item.get("score_source_ref"))
            if not ref or source_item.get("score") is None or not score_source_ref:
                continue
            refs.append(
                {
                    "ref": ref,
                    "score": source_item.get("score"),
                    "score_source_ref": score_source_ref,
                }
            )
    return refs


def _literature_intelligence_missing_reason(
    payload: Mapping[str, Any],
    providers: list[Mapping[str, Any]],
) -> str:
    categorized = _categorized_refs(providers)
    if not _search_strategy_is_complete(payload):
        return "missing_search_strategy"
    if not _keyword_terms_are_complete(payload):
        return "missing_keyword_terms"
    if not _study_rationale(payload):
        return "missing_study_rationale"
    if not _has_ref_items(categorized["anchor_papers"]):
        return "missing_anchor_paper_refs"
    if not _has_ref_items(categorized["guidelines"]):
        return "missing_guideline_refs"
    if not _has_ref_items(categorized["systematic_reviews"]):
        return "missing_systematic_review_refs"
    if not _has_ref_items(categorized["journal_neighbor_refs"]):
        return "missing_journal_neighbor_refs"
    if not _has_ref_items(_high_score_neighbor_refs(providers)):
        return "missing_high_score_neighbor_refs"
    return ""


def _missing_reason(payload: Mapping[str, Any]) -> str:
    providers = _providers(payload)
    if not providers:
        return "missing_provider_sources"
    support_reason = _provider_support_missing_reason(providers)
    if support_reason:
        return support_reason
    provider_names = {_provider_name(provider) for provider in providers}
    for required_provider in REQUIRED_PROVIDERS:
        if required_provider not in provider_names:
            return f"missing_provider_sources_{required_provider}"
    for provider in providers:
        runtime_reason = _provider_runtime_missing_reason(provider)
        if runtime_reason:
            return runtime_reason
    missing_ledger_providers = [_text(item) for item in _list(payload.get("_missing_provider_citation_ledger_refs"))]
    if missing_ledger_providers:
        return f"missing_provider_citation_ledger_refs_{missing_ledger_providers[0]}"
    query_drift_reason = _query_fingerprint_drift_missing_reason(payload, providers)
    if query_drift_reason:
        return query_drift_reason
    if not _has_text(payload.get("search_date")):
        return "missing_search_date"
    literature_reason = _literature_intelligence_missing_reason(payload, providers)
    if literature_reason:
        return literature_reason
    if not _has_ref_items(payload.get("citation_ledger_refs")):
        return "missing_citation_ledger_refs"
    if _citation_freshness(payload)["stale"]:
        return "stale_citation_ledger_refs"
    if not _screening_decisions_are_complete(payload.get("screening_decisions")):
        return "missing_screening_decision_reason"
    return ""


def _provider_support_missing_reason(providers: Iterable[Mapping[str, Any]]) -> str | None:
    for provider in providers:
        name = _provider_name(provider)
        if not name:
            return "missing_provider_name"
        if name not in SUPPORTED_PROVIDERS:
            return f"unsupported_provider_{name}"
    return None


def _provider_runtime_missing_reason(provider: Mapping[str, Any]) -> str | None:
    name = _provider_name(provider)
    if not _credential_status(provider)["ready"]:
        return f"missing_credential_{name}"
    status = _provider_response_status(provider)
    if status in UNAVAILABLE_STATUSES:
        return f"provider_unavailable_{name}"
    if status in PARTIAL_OUTAGE_STATUSES:
        return f"provider_partial_outage_{name}"
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
    return None


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


def _expected_query_fingerprint(payload: Mapping[str, Any]) -> str:
    contract = _mapping(payload.get("query_fingerprint_contract"))
    return (
        _text(payload.get("expected_query_fingerprint"))
        or _text(payload.get("baseline_query_fingerprint"))
        or _text(payload.get("previous_query_fingerprint"))
        or _text(contract.get("expected_query_fingerprint"))
        or _text(contract.get("baseline_query_fingerprint"))
    )


def _expected_provider_query_fingerprints(payload: Mapping[str, Any]) -> dict[str, str]:
    contract = _mapping(payload.get("query_fingerprint_contract"))
    raw = (
        _mapping(payload.get("expected_provider_query_fingerprints"))
        or _mapping(payload.get("baseline_provider_query_fingerprints"))
        or _mapping(payload.get("previous_provider_query_fingerprints"))
        or _mapping(contract.get("expected_provider_query_fingerprints"))
        or _mapping(contract.get("baseline_provider_query_fingerprints"))
    )
    return {_text(key): _text(value) for key, value in raw.items() if _has_text(key) and _has_text(value)}


def _query_fingerprint_drift(
    payload: Mapping[str, Any],
    providers: list[Mapping[str, Any]],
) -> dict[str, Any]:
    actual_query_fingerprint = _aggregate_query_fingerprint(payload, providers)
    actual_provider_fingerprints = _provider_query_fingerprints(providers)
    expected_query_fingerprint = _expected_query_fingerprint(payload)
    expected_provider_fingerprints = _expected_provider_query_fingerprints(payload)
    drifted_providers = [
        provider_name
        for provider_name, expected in expected_provider_fingerprints.items()
        if actual_provider_fingerprints.get(provider_name) != expected
    ]
    aggregate_drifted = bool(expected_query_fingerprint and expected_query_fingerprint != actual_query_fingerprint)
    return {
        "status": "drifted" if aggregate_drifted or drifted_providers else "stable",
        "expected_query_fingerprint": expected_query_fingerprint,
        "actual_query_fingerprint": actual_query_fingerprint,
        "expected_provider_query_fingerprints": expected_provider_fingerprints,
        "actual_provider_query_fingerprints": actual_provider_fingerprints,
        "drifted_providers": drifted_providers,
    }


def _query_fingerprint_drift_missing_reason(
    payload: Mapping[str, Any],
    providers: list[Mapping[str, Any]],
) -> str:
    drift = _query_fingerprint_drift(payload, providers)
    if drift["status"] != "drifted":
        return ""
    drifted_providers = [item for item in _list(drift.get("drifted_providers")) if _has_text(item)]
    if drifted_providers:
        return f"query_fingerprint_drift_{drifted_providers[0]}"
    return "query_fingerprint_drift"


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


def _provider_health_authority_contract() -> dict[str, Any]:
    return {
        "authority": "provider_health_read_model_only",
        "read_model_only": True,
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


def _provider_response_ledger_health(providers: list[Mapping[str, Any]]) -> dict[str, Any]:
    missing_providers = [
        _provider_name(provider)
        for provider in providers
        if _provider_name(provider) and not _has_ref_items(_provider_response_ledger_refs(provider))
    ]
    return {
        "complete": not missing_providers,
        "missing_providers": missing_providers,
        "refs": _all_provider_response_ledger_refs(providers),
    }


def _citation_ledger_health(payload: Mapping[str, Any]) -> dict[str, Any]:
    missing_providers = [
        _text(item) for item in _list(payload.get("_missing_provider_citation_ledger_refs")) if _has_text(item)
    ]
    refs = [_text(item) for item in _list(payload.get("citation_ledger_refs")) if _has_text(item)]
    return {
        "complete": bool(refs) and not missing_providers,
        "missing_providers": missing_providers,
        "refs": refs,
    }


def _screening_reason_health(payload: Mapping[str, Any]) -> dict[str, Any]:
    missing_refs: list[str] = []
    for index, raw_decision in enumerate(_list(payload.get("screening_decisions"))):
        decision = _mapping(raw_decision)
        if not decision:
            continue
        if _text(decision.get("decision")) not in {"include", "exclude"} or not _has_text(decision.get("reason")):
            missing_refs.append(_text(decision.get("ref")) or f"screening_decision:{index}")
    return {
        "complete": _screening_decisions_are_complete(payload.get("screening_decisions")),
        "missing_refs": missing_refs,
    }


def _cache_age_by_provider(providers: list[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    cache_age: dict[str, dict[str, Any]] = {}
    for provider in providers:
        provider_name = _provider_name(provider)
        if not provider_name:
            continue
        cache = _cache_freshness(provider)
        cache_age[provider_name] = {
            "retrieved_at": _text(provider.get("retrieved_at")) or cache["retrieved_at"],
            "checked_at": cache["checked_at"],
            "expires_at": cache["expires_at"],
            "status": cache["status"],
            "stale": cache["stale"],
        }
    return cache_age


def _provider_health_diagnostic(
    reason_code: str,
    *,
    category: str,
    provider_name: str = "",
) -> dict[str, Any]:
    diagnostic: dict[str, Any] = {
        "reason_code": reason_code,
        "severity": "blocking",
    }
    if provider_name:
        diagnostic["provider_name"] = provider_name
    diagnostic["category"] = category
    return diagnostic


def _provider_missing_reason_category(reason_code: str) -> str:
    if reason_code in {
        "missing_search_strategy",
        "missing_keyword_terms",
        "missing_study_rationale",
        "missing_anchor_paper_refs",
        "missing_guideline_refs",
        "missing_systematic_review_refs",
        "missing_journal_neighbor_refs",
        "missing_high_score_neighbor_refs",
    }:
        return "literature_intelligence_readiness"
    return "provider_health_projection"


def _provider_health_diagnostics(
    *,
    payload: Mapping[str, Any],
    providers: list[Mapping[str, Any]],
    missing_reason: str,
    provider_response_ledger: Mapping[str, Any],
    citation_ledger: Mapping[str, Any],
    screening_reasons: Mapping[str, Any],
    citation_freshness: Mapping[str, Any],
    query_fingerprint_drift: Mapping[str, Any],
) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    for provider in providers:
        name = _provider_name(provider)
        if not name:
            diagnostics.append(
                _provider_health_diagnostic(
                    "missing_provider_name",
                    category="provider_identity",
                )
            )
            continue
        if not _credential_status(provider)["ready"]:
            diagnostics.append(
                _provider_health_diagnostic(
                    f"missing_credential_{name}",
                    category="credential_status",
                    provider_name=name,
                )
            )
        status = _provider_response_status(provider)
        if status in UNAVAILABLE_STATUSES:
            diagnostics.append(
                _provider_health_diagnostic(
                    f"provider_unavailable_{name}",
                    category="provider_response",
                    provider_name=name,
                )
            )
        if status in PARTIAL_OUTAGE_STATUSES:
            diagnostics.append(
                _provider_health_diagnostic(
                    f"provider_partial_outage_{name}",
                    category="provider_partial_outage",
                    provider_name=name,
                )
            )
        if _rate_limit_status(provider)["limited"]:
            diagnostics.append(
                _provider_health_diagnostic(
                    f"rate_limited_{name}",
                    category="rate_limit_backoff",
                    provider_name=name,
                )
            )
        if _cache_freshness(provider)["stale"]:
            diagnostics.append(
                _provider_health_diagnostic(
                    f"stale_cache_{name}",
                    category="cache_age",
                    provider_name=name,
                )
            )
        if not _has_text(provider.get("query")):
            diagnostics.append(
                _provider_health_diagnostic(
                    f"missing_provider_query_{name}",
                    category="query_fingerprint_drift",
                    provider_name=name,
                )
            )
        if not _has_text(provider.get("retrieved_at")):
            diagnostics.append(
                _provider_health_diagnostic(
                    f"missing_provider_retrieved_at_{name}",
                    category="cache_age",
                    provider_name=name,
                )
            )
        if not _has_ref_items(_provider_refs(provider)):
            diagnostics.append(
                _provider_health_diagnostic(
                    f"missing_provider_source_refs_{name}",
                    category="provider_source_refs",
                    provider_name=name,
                )
            )

    for provider_name in _list(provider_response_ledger.get("missing_providers")):
        name = _text(provider_name)
        if name:
            diagnostics.append(
                _provider_health_diagnostic(
                    f"missing_provider_response_ledger_{name}",
                    category="provider_response_ledger_completeness",
                    provider_name=name,
                )
            )
    for provider_name in _list(citation_ledger.get("missing_providers")):
        name = _text(provider_name)
        if name:
            diagnostics.append(
                _provider_health_diagnostic(
                    f"missing_provider_citation_ledger_refs_{name}",
                    category="citation_ledger_completeness",
                    provider_name=name,
                )
            )
    if not _has_ref_items(payload.get("citation_ledger_refs")):
        diagnostics.append(
            _provider_health_diagnostic(
                "missing_citation_ledger_refs",
                category="citation_ledger_completeness",
            )
        )
    if citation_freshness.get("stale") is True:
        diagnostics.append(
            _provider_health_diagnostic(
                "stale_citation_ledger_refs",
                category="citation_freshness",
            )
        )
    if query_fingerprint_drift.get("status") == "drifted":
        drifted_providers = [_text(item) for item in _list(query_fingerprint_drift.get("drifted_providers")) if _has_text(item)]
        if drifted_providers:
            for provider_name in drifted_providers:
                diagnostics.append(
                    _provider_health_diagnostic(
                        f"query_fingerprint_drift_{provider_name}",
                        category="query_fingerprint_drift",
                        provider_name=provider_name,
                    )
                )
        else:
            diagnostics.append(
                _provider_health_diagnostic(
                    "query_fingerprint_drift",
                    category="query_fingerprint_drift",
                )
            )
    if screening_reasons.get("complete") is False:
        diagnostics.append(
            _provider_health_diagnostic(
                "missing_screening_decision_reason",
                category="screening_reason_completeness",
            )
        )
    if missing_reason and not any(item.get("reason_code") == missing_reason for item in diagnostics):
        diagnostics.append(
            _provider_health_diagnostic(
                missing_reason,
                category=_provider_missing_reason_category(missing_reason),
            )
        )
    return diagnostics


def _provider_health(
    *,
    payload: Mapping[str, Any],
    providers: list[Mapping[str, Any]],
    missing_reason: str,
    provider_operations: Mapping[str, Any],
) -> dict[str, Any]:
    provider_response_ledger = _provider_response_ledger_health(providers)
    citation_ledger = _citation_ledger_health(payload)
    screening_reasons = _screening_reason_health(payload)
    citation_freshness = _citation_freshness(payload)
    query_fingerprint_drift = _query_fingerprint_drift(payload, providers)
    diagnostics = _provider_health_diagnostics(
        payload=payload,
        providers=providers,
        missing_reason=missing_reason,
        provider_response_ledger=provider_response_ledger,
        citation_ledger=citation_ledger,
        screening_reasons=screening_reasons,
        citation_freshness=citation_freshness,
        query_fingerprint_drift=query_fingerprint_drift,
    )
    return {
        "contract": "scheduled_provider_health_read_model",
        "status": "blocked" if missing_reason or diagnostics else "ready",
        "missing_reason": missing_reason,
        "checks": list(PROVIDER_HEALTH_CHECKS),
        "diagnostics": diagnostics,
        "credential_status": dict(_mapping(provider_operations.get("credential_status"))),
        "rate_limit_status": dict(_mapping(provider_operations.get("rate_limit_status"))),
        "backoff": dict(_mapping(provider_operations.get("backoff"))),
        "cache_freshness": dict(_mapping(provider_operations.get("cache_freshness"))),
        "cache_age": _cache_age_by_provider(providers),
        "query_fingerprint_drift": query_fingerprint_drift,
        "provider_response_ledger": provider_response_ledger,
        "citation_ledger": citation_ledger,
        "citation_freshness": citation_freshness,
        "screening_reasons": screening_reasons,
        "authority_contract": _provider_health_authority_contract(),
        "health_can_authorize_quality": False,
        "health_can_authorize_submission": False,
        "health_can_authorize_finalize": False,
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


def _literature_intelligence_payload(
    payload: Mapping[str, Any],
    providers: list[Mapping[str, Any]],
) -> dict[str, Any]:
    categorized = _categorized_refs(providers)
    return {
        "source_basis": _text(payload.get("source_basis")),
        "source_refs": _list(payload.get("source_refs")),
        "search_strategy": dict(_mapping(payload.get("search_strategy"))),
        "search_date": _text(payload.get("search_date")),
        "searched_sources": _provider_source_refs(providers),
        "provider_provenance": _provider_provenance(providers),
        "why_worth_doing": _study_rationale(payload),
        "anchor_papers": categorized["anchor_papers"],
        "guidelines": categorized["guidelines"],
        "systematic_reviews": categorized["systematic_reviews"],
        "journal_neighbor_refs": categorized["journal_neighbor_refs"],
        "high_score_neighbor_refs": _high_score_neighbor_refs(providers),
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
    provider_health = _provider_health(
        payload=payload,
        providers=providers,
        missing_reason=missing_reason,
        provider_operations=provider_operations,
    )
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "status": "ready" if not missing_reason else "blocked",
        "missing_reason": missing_reason,
        "providers": [_provider_name(provider) for provider in providers],
        "provider_provenance": _provider_provenance(providers),
        "source_basis": _text(payload.get("source_basis")),
        "source_refs": _list(payload.get("source_refs")),
        "query": _text(payload.get("query")) or _text(_mapping(payload.get("search_strategy")).get("query")),
        "search_date": _text(payload.get("search_date")),
        "search_strategy": dict(_mapping(payload.get("search_strategy"))),
        "citation_ledger_refs": _list(payload.get("citation_ledger_refs")),
        "screening_decisions": _list(payload.get("screening_decisions")),
        "source_response_digest": _source_response_digest(providers),
        "provider_operations": provider_operations,
        "provider_health": provider_health,
        "diagnostics": provider_health["diagnostics"],
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
        "provider_health": projection["provider_health"],
        "diagnostics": projection["diagnostics"],
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
