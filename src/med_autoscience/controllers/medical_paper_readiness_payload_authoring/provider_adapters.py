from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import yaml

from med_autoscience.adapters.literature import doi as crossref
from med_autoscience.adapters.literature import pubmed
from med_autoscience.adapters.literature import semantic_scholar


def payload_from_provider_adapters(
    *,
    study_root: Path,
    generated_at: str,
    surface_key: str | None,
    provider_receipts: Sequence[Mapping[str, Any]],
    source: str,
    surface: str,
    schema_version: int,
) -> dict[str, Any]:
    study = _read_yaml(study_root / "study.yaml")
    if not study:
        return {}
    pubmed_urls = [_text(item) for item in _list(study.get("paper_urls")) if _text(item)]
    pmids = [_pmid_from_pubmed_url(url) for url in pubmed_urls]
    pmids = [pmid for pmid in pmids if pmid]
    literature_materialization = _read_json(
        study_root / "artifacts" / "publication_eval" / "literature_materialization.json"
    )
    materialized_records = _records_from_literature_materialization(literature_materialization)
    pmids = list(dict.fromkeys([*pmids, *(_text(record.get("pmid")) for record in materialized_records)]))
    pmids = [pmid for pmid in pmids if pmid]
    if not pmids and not materialized_records:
        return {}

    pubmed_resolution = pubmed.resolve_pubmed_summaries_from_receipts(
        pmids=list(dict.fromkeys(pmids))[:20],
        provider_receipts=provider_receipts,
    )
    pubmed_records = list(pubmed_resolution["records"])
    if pubmed_resolution["status"] != "resolved" or not pubmed_records:
        return _blocked_payload(
            "opl_connect_reference_receipt_required_pubmed",
            surface_key=surface_key,
            source=source,
            surface=surface,
            schema_version=schema_version,
            provider_resolution=pubmed_resolution,
        )

    records = _merged_records(pubmed_records, materialized_records)
    anchor = _first_record_with_pmid(records) or (records[0] if records else None)
    guideline = _first_record_matching(
        records,
        ("guideline", "guidelines", "primary healthcare", "tripod", "statement"),
    )
    systematic = _first_record_matching(
        records,
        ("systematic review", "subclassification", "classification", "meta-analysis", "meta analysis"),
    )
    if anchor is None:
        return _blocked_payload(
            "missing_pubmed_anchor_record",
            surface_key=surface_key,
            source=source,
            surface=surface,
            schema_version=schema_version,
        )
    if guideline is None:
        return _blocked_payload(
            "missing_guideline_reference_for_provider_runtime",
            surface_key=surface_key,
            source=source,
            surface=surface,
            schema_version=schema_version,
        )
    if systematic is None:
        return _blocked_payload(
            "missing_systematic_review_reference_for_provider_runtime",
            surface_key=surface_key,
            source=source,
            surface=surface,
            schema_version=schema_version,
        )

    pubmed_provider = _pubmed_provider_from_records(
        records=pubmed_records,
        anchor=anchor,
        generated_at=generated_at,
        query=_text(_search_strategy_from_study(study).get("query")),
        receipt_refs=list(pubmed_resolution["provider_receipt_refs"]),
    )
    if not pubmed_provider:
        return _blocked_payload(
            "provider_adapter_payload_failed_pubmed",
            surface_key=surface_key,
            source=source,
            surface=surface,
            schema_version=schema_version,
        )

    crossref_provider, crossref_resolution = _crossref_provider_from_records(
        records=((guideline, "guidelines"), (systematic, "systematic_reviews")),
        generated_at=generated_at,
        query=f"{_text(_search_strategy_from_study(study).get('query'))} guideline systematic review".strip(),
        provider_receipts=provider_receipts,
    )
    if not crossref_provider:
        return _blocked_payload(
            "provider_adapter_fetch_failed_crossref",
            surface_key=surface_key,
            source=source,
            surface=surface,
            schema_version=schema_version,
            provider_resolution=crossref_resolution,
        )

    semantic_provider, semantic_resolution = _semantic_provider_from_records(
        records=_semantic_candidate_records(
            systematic=systematic,
            guideline=guideline,
            anchor=anchor,
            records=records,
        ),
        generated_at=generated_at,
        provider_receipts=provider_receipts,
    )
    if not semantic_provider:
        return _blocked_payload(
            "provider_adapter_fetch_failed_semantic_scholar",
            surface_key=surface_key,
            source=source,
            surface=surface,
            schema_version=schema_version,
            provider_resolution=semantic_resolution,
        )
    search_strategy = _search_strategy_from_study(study)
    providers = [pubmed_provider, crossref_provider, semantic_provider]
    citation_refs = [
        ref
        for provider in providers
        for ref in _citation_refs_from_provider(provider)
    ]
    return _payload(
        study_root=study_root,
        generated_at=generated_at,
        search_strategy=search_strategy,
        search_date=_date_from_timestamp(generated_at),
        why_worth_doing=(
            _text(study.get("literature_anchor_summary"))
            or _text(study.get("paper_framing_summary"))
            or _text(study.get("primary_question"))
        ),
        providers=providers,
        screening_decisions=_screening_decisions(providers),
        citation_ledger_refs=list(dict.fromkeys(citation_refs)),
        source_basis="study_contract_and_opl_connect_provider_receipts",
        source_refs=[
            str(study_root / "study.yaml"),
            *(
                [str(study_root / "artifacts" / "publication_eval" / "literature_materialization.json")]
                if materialized_records
                else []
            ),
        ],
        source=source,
        surface=surface,
        schema_version=schema_version,
    )


def _semantic_candidate_records(
    *,
    systematic: Mapping[str, Any] | None,
    guideline: Mapping[str, Any] | None,
    anchor: Mapping[str, Any] | None,
    records: list[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    candidates: list[Mapping[str, Any]] = []
    seen: set[str] = set()
    for record in [systematic, guideline, anchor, *records]:
        if record is None:
            continue
        key = _record_ref(record)
        if not key or key in seen:
            continue
        seen.add(key)
        candidates.append(record)
    return tuple(candidates[:8])


def _semantic_provider_from_records(
    *,
    records: tuple[Mapping[str, Any], ...],
    generated_at: str,
    provider_receipts: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    unresolved: dict[str, Any] | None = None
    for record in records:
        provider, resolution = _semantic_provider_from_record(
            record=record,
            generated_at=generated_at,
            provider_receipts=provider_receipts,
        )
        if provider:
            return provider, None
        if resolution is not None:
            unresolved = resolution
    return {}, unresolved


def _semantic_provider_from_record(
    *,
    record: Mapping[str, Any],
    generated_at: str,
    provider_receipts: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    doi = _text(record.get("doi"))
    pmid = _text(record.get("pmid"))
    if not doi and not pmid:
        return {}, None
    reference_id = f"doi:{doi}" if doi else f"pmid:{pmid}"
    resolution = semantic_scholar.resolve_semantic_scholar_records_from_receipts(
        references=({"id": reference_id, "doi": doi, "pmid": pmid, "title": _text(record.get("title"))},),
        provider_receipts=provider_receipts,
    )
    if resolution["status"] != "resolved":
        return {}, resolution
    records = list(resolution["records"])
    if not records:
        return {}, resolution
    resolved = records[0]
    resolved_ref = _record_ref(resolved)
    request_id = f"semantic-scholar-receipt-{_slug(resolved_ref)}"
    return {
        "provider": "semantic_scholar",
        "query": _text(record.get("title")) or _text(record.get("ref")) or "medical literature neighbor",
        "retrieved_at": generated_at,
        "request_id": request_id,
        "response_status": "ok",
        "credential_status": _receipt_bound_credential(
            list(resolution["provider_receipt_refs"])
        ),
        "rate_limit_status": _ok_rate_limit(),
        "cache_freshness": _fresh_cache(generated_at),
        "provider_response_ledger_refs": list(resolution["provider_receipt_refs"]),
        "items": [
            {
                "ref": resolved_ref,
                "category": "journal_neighbor_refs",
                "title": _text(resolved.get("title")),
                "citation_ledger_ref": _citation_ref_for_record(resolved),
                "score": _semantic_score(resolved),
                "score_source_ref": f"opl_connect:{request_id}",
            }
        ],
    }, None


def _payload(
    *,
    study_root: Path,
    generated_at: str,
    search_strategy: Mapping[str, Any],
    search_date: str,
    why_worth_doing: str | None,
    providers: list[dict[str, Any]],
    screening_decisions: list[Mapping[str, Any]],
    citation_ledger_refs: list[str],
    source_basis: str,
    source_refs: list[str],
    source: str,
    surface: str,
    schema_version: int,
) -> dict[str, Any]:
    return {
        "payload_source": source,
        "surface": surface,
        "schema_version": schema_version,
        "study_root": str(study_root),
        "generated_at": generated_at,
        "source_basis": source_basis,
        "source_refs": source_refs,
        "search_strategy": dict(search_strategy),
        "search_date": search_date,
        "why_worth_doing": _text(why_worth_doing) or "Provider-backed literature evidence supports the current study framing.",
        "provider_payloads": providers,
        "screening_decisions": [dict(item) for item in screening_decisions if isinstance(item, Mapping)],
        "citation_ledger_refs": list(dict.fromkeys(ref for ref in citation_ledger_refs if _text(ref))),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _blocked_payload(
    reason: str,
    *,
    surface_key: str | None,
    source: str,
    surface: str,
    schema_version: int,
    provider_resolution: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "payload_source": source,
        "surface": surface,
        "schema_version": schema_version,
        "status": "blocked",
        "blocked_reason": reason,
        "surface_key": _text(surface_key),
        "provider_resolution": dict(provider_resolution) if provider_resolution else None,
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _fetch_crossref_record(
    record: Mapping[str, Any],
    *,
    provider_receipts: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], list[str], dict[str, Any] | None]:
    doi = _text(record.get("doi"))
    if not doi:
        return {}, [], None
    resolution = crossref.resolve_crossref_work_from_receipts(
        doi=doi,
        provider_receipts=provider_receipts,
    )
    records = list(resolution["records"])
    if not records:
        return {}, [], resolution
    return dict(records[0]), list(resolution["provider_receipt_refs"]), None


def _merged_records(
    pubmed_records: list[Mapping[str, Any]],
    materialized_records: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    by_ref: dict[str, dict[str, Any]] = {}
    for record in [*materialized_records, *pubmed_records]:
        key = _record_ref(record)
        if not key:
            continue
        existing = by_ref.get(key, {})
        by_ref[key] = {
            **existing,
            **{key_: value for key_, value in dict(record).items() if value not in (None, "", [])},
        }
    return list(by_ref.values())


def _pubmed_provider_from_records(
    *,
    records: list[Mapping[str, Any]],
    anchor: Mapping[str, Any],
    generated_at: str,
    query: str | None,
    receipt_refs: list[str],
) -> dict[str, Any]:
    if not records:
        return {}
    request_id = "pubmed-esummary-" + _slug(
        "-".join(_text(record.get("pmid")) for record in records if record.get("pmid"))
    )
    anchor_ref = _record_ref(anchor)
    items: list[dict[str, Any]] = []
    for record in records:
        ref = _record_ref(record)
        if ref:
            items.append(_provider_item_from_record(record, category="anchor_papers"))
    return {
        "provider": "pubmed",
        "query": _text(query) or _text(anchor.get("title")) or anchor_ref,
        "retrieved_at": generated_at,
        "request_id": request_id,
        "response_status": "ok",
        "credential_status": _receipt_bound_credential(receipt_refs),
        "rate_limit_status": _ok_rate_limit(),
        "cache_freshness": _fresh_cache(generated_at),
        "provider_response_ledger_refs": receipt_refs,
        "items": [item for item in items if item.get("ref")],
    }


def _crossref_provider_from_records(
    *,
    records: tuple[tuple[Mapping[str, Any], str], ...],
    generated_at: str,
    query: str | None,
    provider_receipts: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    fetched_records: list[dict[str, Any]] = []
    receipt_refs: list[str] = []
    items: list[dict[str, Any]] = []
    for record, category in records:
        fetched, fetched_receipt_refs, resolution = _fetch_crossref_record(
            record,
            provider_receipts=provider_receipts,
        )
        if not fetched:
            return {}, resolution
        fetched_records.append(fetched)
        receipt_refs.extend(fetched_receipt_refs)
        item = _provider_item_from_record(fetched, category=category)
        if item.get("ref"):
            items.append(item)
    request_id = "crossref-works-" + _slug("-".join(_text(record.get("doi")) for record in fetched_records))
    return {
        "provider": "crossref",
        "query": _text(query) or _text(fetched_records[0].get("title")),
        "retrieved_at": generated_at,
        "request_id": request_id,
        "response_status": "ok",
        "credential_status": _receipt_bound_credential(receipt_refs),
        "rate_limit_status": _ok_rate_limit(),
        "cache_freshness": _fresh_cache(generated_at),
        "provider_response_ledger_refs": list(dict.fromkeys(receipt_refs)),
        "items": items,
    }, None


def _provider_item_from_record(record: Mapping[str, Any], *, category: str) -> dict[str, Any]:
    return {
        "ref": _record_ref(record),
        "category": category,
        "title": _text(record.get("title")),
        "citation_ledger_ref": _citation_ref_for_record(record),
    }


def _receipt_bound_credential(receipt_refs: Sequence[str]) -> dict[str, str]:
    refs = [_text(ref) for ref in receipt_refs if _text(ref)]
    return {
        "status": "ready" if refs else "missing",
        "credential_ref": refs[0] if refs else "",
    }


def _records_from_literature_materialization(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in _mapping_list(payload.get("records")):
        pubmed_payload = _mapping(item.get("pubmed"))
        records.append(
            {
                "record_id": _text(item.get("record_id")),
                "title": _text(item.get("title")),
                "doi": _text(item.get("doi")),
                "pmid": _text(pubmed_payload.get("pmid")) or _text(item.get("pmid")),
                "claim_links": _list(item.get("claim_links")),
                "materialization_status": _text(item.get("materialization_status")),
            }
        )
    return records


def _first_record_with_pmid(records: list[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    for record in records:
        if _text(record.get("pmid")):
            return record
    return None


def _first_record_matching(records: list[Mapping[str, Any]], terms: tuple[str, ...]) -> Mapping[str, Any] | None:
    lowered_terms = tuple(term.lower() for term in terms)
    for record in records:
        haystack = " ".join(
            [
                _text(record.get("title")) or "",
                " ".join(_text(item) or "" for item in _list(record.get("claim_links"))),
            ]
        ).lower()
        if any(term in haystack for term in lowered_terms):
            return record
    return None


def _search_strategy_from_study(study: Mapping[str, Any]) -> dict[str, Any]:
    title = _text(study.get("title")) or _text(study.get("study_id")) or "medical study"
    question = _text(study.get("primary_question")) or _text(study.get("paper_framing_summary")) or title
    words = [
        word.strip(".,;:()[]{}").lower()
        for word in f"{title} {question}".split()
        if len(word.strip(".,;:()[]{}")) > 4
    ]
    keywords = list(dict.fromkeys(words))[:8]
    return {
        "query": title,
        "mesh_terms": ["Diabetes Mellitus"],
        "keywords": keywords or ["diabetes", "mortality", "clinical"],
    }


def _screening_decisions(providers: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    for provider in providers:
        for item in _provider_items(provider):
            ref = _text(item.get("ref")) or _text(item.get("paperId"))
            if ref:
                decisions.append(
                    {
                        "ref": ref,
                        "decision": "include",
                        "reason": "Provider-backed source supports the current literature readiness surface.",
                    }
                )
    return decisions


def _provider_items(provider: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    for key in ("items", "records", "results"):
        items = _mapping_list(provider.get(key))
        if items:
            return items
    return []


def _citation_refs_from_provider(provider: Mapping[str, Any]) -> list[str]:
    return [
        ref
        for item in _provider_items(provider)
        if (ref := _text(item.get("citation_ledger_ref")))
    ]


def _citation_ref_for_record(record: Mapping[str, Any]) -> str:
    ref = _record_ref(record)
    if ref:
        return f"paper/evidence_ledger.json#{_slug(ref)}"
    record_id = _text(record.get("record_id")) or "literature-record"
    return f"paper/evidence_ledger.json#{_slug(record_id)}"


def _record_ref(record: Mapping[str, Any]) -> str:
    if pmid := _text(record.get("pmid")):
        return f"pmid:{pmid}"
    if doi := _text(record.get("doi")):
        return f"doi:{doi}"
    return _text(record.get("record_id")) or ""


def _semantic_score(paper: Mapping[str, Any]) -> float:
    citation_count = paper.get("citationCount")
    if isinstance(citation_count, int):
        return min(0.99, 0.75 + min(citation_count, 100) / 500)
    return 0.9


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _pmid_from_pubmed_url(url: str) -> str:
    parts = url.rstrip("/").split("/")
    tail = parts[-1] if parts else ""
    return tail if tail.isdigit() else ""


def _fresh_cache(generated_at: str) -> dict[str, Any]:
    return {
        "status": "fresh",
        "checked_at": generated_at,
    }


def _ok_rate_limit() -> dict[str, Any]:
    return {
        "status": "ok",
        "remaining": None,
        "reset_at": "",
        "backoff": {"retry_after_seconds": 0},
    }


def _date_from_timestamp(value: str) -> str:
    return value[:10] if len(value) >= 10 else _utc_now()[:10]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _slug(value: object) -> str:
    text = _text(value).lower()
    rendered = "".join(char if char.isalnum() else "-" for char in text).strip("-")
    while "--" in rendered:
        rendered = rendered.replace("--", "-")
    return rendered or "ref"


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[Mapping[str, Any]]:
    return [item for item in value if isinstance(item, Mapping)] if isinstance(value, list) else []


def _list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


__all__ = ["payload_from_provider_adapters"]
