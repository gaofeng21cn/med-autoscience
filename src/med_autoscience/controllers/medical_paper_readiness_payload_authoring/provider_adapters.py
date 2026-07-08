from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any

import yaml

from med_autoscience.adapters.literature import doi as crossref
from med_autoscience.adapters.literature import pubmed
from med_autoscience.adapters.literature import semantic_scholar


def payload_from_existing_literature_intelligence(
    *,
    study_root: Path,
    generated_at: str,
    source: str,
    surface: str,
    schema_version: int,
) -> dict[str, Any]:
    path = study_root / "artifacts" / "medical_paper" / "literature_intelligence_os.json"
    payload = _read_json(path)
    if not payload:
        return {}
    if _text(payload.get("status")) != "ready":
        return {}
    provider_names = {
        _text(item.get("provider_name"))
        for item in _mapping_list(payload.get("provider_provenance"))
    }
    if not {"pubmed", "crossref", "semantic_scholar"}.issubset(provider_names):
        return {}
    providers: list[dict[str, Any]] = []
    for provider in _mapping_list(payload.get("provider_provenance")):
        provider_name = _text(provider.get("provider_name"))
        refs = [_text(item) for item in _list(provider.get("source_refs")) if _text(item)]
        providers.append(
            {
                "provider": provider_name,
                "query": _text(provider.get("query")) or _search_query_from_payload(payload),
                "retrieved_at": _text(provider.get("retrieved_at")) or generated_at,
                "request_id": f"{provider_name}-existing-literature-intelligence",
                "response_status": _text(provider.get("response_status")) or "ok",
                "credential_status": _ready_credential(provider_name),
                "rate_limit_status": _ok_rate_limit(),
                "cache_freshness": _fresh_cache(generated_at),
                "provider_response_ledger_refs": refs,
                "items": _items_for_provider(provider_name=provider_name, payload=payload),
            }
        )
    return _payload(
        study_root=study_root,
        generated_at=generated_at,
        search_strategy=_mapping(payload.get("search_strategy")),
        search_date=_text(payload.get("search_date")) or _date_from_timestamp(generated_at),
        why_worth_doing=_text(payload.get("why_worth_doing")) or _text(payload.get("study_rationale")),
        providers=providers,
        screening_decisions=_mapping_list(payload.get("screening_decisions")),
        citation_ledger_refs=[_text(item) for item in _list(payload.get("citation_ledger_refs")) if _text(item)],
        source_basis="existing_literature_intelligence_os",
        source_refs=[str(path)],
        source=source,
        surface=surface,
        schema_version=schema_version,
    )


def payload_from_provider_adapters(
    *,
    study_root: Path,
    generated_at: str,
    surface_key: str | None,
    write_provider_response_ledger: bool,
    source: str,
    surface: str,
    schema_version: int,
) -> dict[str, Any]:
    if not write_provider_response_ledger:
        return {}
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

    pubmed_records = _fetch_pubmed_records(pmids)
    if not pubmed_records:
        fallback = _payload_from_verified_literature_materialization(
            study_root=study_root,
            generated_at=generated_at,
            study=study,
            materialized_records=materialized_records,
            write_provider_response_ledger=write_provider_response_ledger,
            source=source,
            surface=surface,
            schema_version=schema_version,
        )
        if fallback:
            return fallback
        return _blocked_payload(
            "provider_adapter_fetch_failed_pubmed",
            surface_key=surface_key,
            source=source,
            surface=surface,
            schema_version=schema_version,
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
        study_root=study_root,
        records=pubmed_records,
        anchor=anchor,
        generated_at=generated_at,
        query=_text(_search_strategy_from_study(study).get("query")),
        schema_version=schema_version,
    )
    if not pubmed_provider:
        return _blocked_payload(
            "provider_adapter_payload_failed_pubmed",
            surface_key=surface_key,
            source=source,
            surface=surface,
            schema_version=schema_version,
        )

    crossref_provider = _crossref_provider_from_records(
        study_root=study_root,
        records=((guideline, "guidelines"), (systematic, "systematic_reviews")),
        generated_at=generated_at,
        query=f"{_text(_search_strategy_from_study(study).get('query'))} guideline systematic review".strip(),
        schema_version=schema_version,
    )
    if not crossref_provider:
        return _blocked_payload(
            "provider_adapter_fetch_failed_crossref",
            surface_key=surface_key,
            source=source,
            surface=surface,
            schema_version=schema_version,
        )

    semantic_provider = _semantic_provider_from_records(
        records=_semantic_candidate_records(
            systematic=systematic,
            guideline=guideline,
            anchor=anchor,
            records=records,
        ),
        study_root=study_root,
        generated_at=generated_at,
        write_provider_response_ledger=write_provider_response_ledger,
        schema_version=schema_version,
    )
    if not semantic_provider:
        return _blocked_payload(
            "provider_adapter_fetch_failed_semantic_scholar",
            surface_key=surface_key,
            source=source,
            surface=surface,
            schema_version=schema_version,
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
        source_basis="study_contract_and_live_provider_adapters",
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


def _payload_from_verified_literature_materialization(
    *,
    study_root: Path,
    generated_at: str,
    study: Mapping[str, Any],
    materialized_records: list[Mapping[str, Any]],
    write_provider_response_ledger: bool,
    source: str,
    surface: str,
    schema_version: int,
) -> dict[str, Any]:
    verified_records = [
        dict(record)
        for record in materialized_records
        if _text(record.get("pmid"))
        and _text(record.get("materialization_status")) in {"verified_pubmed", "pubmed_verified"}
    ]
    if not verified_records:
        return {}
    anchor = _first_record_with_pmid(verified_records) or verified_records[0]
    guideline = _first_record_matching(
        verified_records,
        ("guideline", "guidelines", "primary healthcare", "tripod", "statement"),
    )
    systematic = _first_record_matching(
        verified_records,
        ("systematic review", "subclassification", "classification", "meta-analysis", "meta analysis"),
    )
    if anchor is None or guideline is None or systematic is None:
        return {}
    semantic_record = systematic if _record_ref(systematic) != _record_ref(anchor) else guideline
    query = _text(_search_strategy_from_study(study).get("query"))
    materialization_ref = "artifacts/publication_eval/literature_materialization.json"
    ledger_ref = (
        _write_provider_response_ledger(
            study_root=study_root,
            provider="pubmed",
            request_id="pubmed-verified-literature-materialization-"
            + _slug("-".join(_text(record.get("pmid")) for record in verified_records if _text(record.get("pmid")))),
            retrieved_at=generated_at,
            response_status="ok",
            payload={
                "source_basis": "verified_literature_materialization",
                "records": verified_records,
            },
            schema_version=schema_version,
        )
        if write_provider_response_ledger
        else materialization_ref
    )
    providers = [
        _materialized_provider(
            provider="pubmed",
            records=tuple((record, "anchor_papers") for record in verified_records if _record_ref(record)),
            generated_at=generated_at,
            query=query,
            ledger_ref=ledger_ref,
            source_ref=materialization_ref,
        ),
        _materialized_provider(
            provider="crossref",
            records=((guideline, "guidelines"), (systematic, "systematic_reviews")),
            generated_at=generated_at,
            query=f"{query} guideline systematic review".strip(),
            ledger_ref=ledger_ref,
            source_ref=materialization_ref,
        ),
        _materialized_provider(
            provider="semantic_scholar",
            records=((semantic_record, "journal_neighbor_refs"),),
            generated_at=generated_at,
            query=_text(semantic_record.get("title")) or query,
            ledger_ref=ledger_ref,
            source_ref=materialization_ref,
            semantic_score=True,
        ),
    ]
    if any(not provider.get("items") for provider in providers):
        return {}
    citation_refs = [
        ref
        for provider in providers
        for ref in _citation_refs_from_provider(provider)
    ]
    return _payload(
        study_root=study_root,
        generated_at=generated_at,
        search_strategy=_search_strategy_from_study(study),
        search_date=_date_from_timestamp(generated_at),
        why_worth_doing=(
            _text(study.get("literature_anchor_summary"))
            or _text(study.get("paper_framing_summary"))
            or _text(study.get("primary_question"))
        ),
        providers=providers,
        screening_decisions=_screening_decisions(providers),
        citation_ledger_refs=list(dict.fromkeys(citation_refs)),
        source_basis="verified_literature_materialization",
        source_refs=[str(study_root / materialization_ref)],
        source=source,
        surface=surface,
        schema_version=schema_version,
    )


def _materialized_provider(
    *,
    provider: str,
    records: tuple[tuple[Mapping[str, Any], str], ...],
    generated_at: str,
    query: str | None,
    ledger_ref: str,
    source_ref: str,
    semantic_score: bool = False,
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for record, category in records:
        item = _provider_item_from_record(record, category=category)
        if semantic_score:
            item["score"] = 0.9
            item["score_source_ref"] = source_ref
        if item.get("ref"):
            items.append(item)
    return {
        "provider": provider,
        "query": _text(query) or (items[0]["title"] if items else "verified literature materialization"),
        "retrieved_at": generated_at,
        "request_id": f"{provider}-verified-literature-materialization",
        "response_status": "ok",
        "credential_status": _public_api_credential(provider),
        "rate_limit_status": _ok_rate_limit(),
        "cache_freshness": _fresh_cache(generated_at),
        "provider_response_ledger_refs": [ledger_ref],
        "source_refs": [source_ref],
        "items": items,
    }


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
    study_root: Path,
    generated_at: str,
    write_provider_response_ledger: bool,
    schema_version: int,
) -> dict[str, Any]:
    for record in records:
        provider = _semantic_provider_from_record(
            record=record,
            study_root=study_root,
            generated_at=generated_at,
            write_provider_response_ledger=write_provider_response_ledger,
            schema_version=schema_version,
        )
        if provider:
            return provider
    return {}


def _semantic_provider_from_record(
    *,
    record: Mapping[str, Any],
    study_root: Path,
    generated_at: str,
    write_provider_response_ledger: bool,
    schema_version: int,
) -> dict[str, Any]:
    doi = _text(record.get("doi"))
    pmid = _text(record.get("pmid"))
    try:
        if doi:
            response = semantic_scholar.fetch_paper_batch(
                paper_ids=[f"DOI:{doi}"],
                fields=("paperId", "title", "year", "venue", "externalIds", "citationCount"),
            )
            request_id = f"semantic-scholar-doi-{_slug(doi)}"
        elif pmid:
            response = semantic_scholar.fetch_paper_batch(
                paper_ids=[f"PMID:{pmid}"],
                fields=("paperId", "title", "year", "venue", "externalIds", "citationCount"),
            )
            request_id = f"semantic-scholar-pmid-{pmid}"
        else:
            return {}
    except Exception:
        return {}
    if _text(response.get("response_status")) != "ok":
        return {}
    papers = _semantic_papers(response.get("payload"))
    if not papers:
        return {}
    paper = papers[0]
    paper_id = _text(paper.get("paperId")) or _text(paper.get("paper_id"))
    if not paper_id:
        return {}
    provider_response_ledger_ref = (
        _write_provider_response_ledger(
            study_root=study_root,
            provider="semantic_scholar",
            request_id=request_id,
            retrieved_at=generated_at,
            response_status=_text(response.get("response_status")) or "ok",
            payload=dict(response),
            schema_version=schema_version,
        )
        if write_provider_response_ledger
        else ""
    )
    return semantic_scholar.provider_payload_from_response(
        query=_text(record.get("title")) or _text(record.get("ref")) or "medical literature neighbor",
        retrieved_at=generated_at,
        request_id=request_id,
        response=response,
        credential_ref="public_api:semantic_scholar_graph",
        provider_response_ledger_ref=provider_response_ledger_ref,
        citation_ledger_refs={paper_id: _citation_ref_for_record(record)},
        category_by_paper_id={paper_id: "journal_neighbor_refs"},
        score_by_paper_id={paper_id: _semantic_score(paper)},
        score_source_ref=f"semantic_scholar:{request_id}",
        cache_freshness=_fresh_cache(generated_at),
    )


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
) -> dict[str, Any]:
    return {
        "payload_source": source,
        "surface": surface,
        "schema_version": schema_version,
        "status": "blocked",
        "blocked_reason": reason,
        "surface_key": _text(surface_key),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _fetch_pubmed_records(pmids: list[str]) -> list[dict[str, Any]]:
    try:
        records = pubmed.fetch_pubmed_summary(pmids=list(dict.fromkeys(pmids))[:20])
    except Exception:
        return []
    return [
        {
            "record_id": record.record_id,
            "title": record.title,
            "doi": record.doi,
            "pmid": record.pmid,
            "year": record.year,
            "journal": record.journal,
            "citation_payload": dict(record.citation_payload),
        }
        for record in records
    ]


def _fetch_crossref_record(record: Mapping[str, Any]) -> dict[str, Any]:
    doi = _text(record.get("doi"))
    if not doi:
        return {}
    try:
        fetched = crossref.fetch_crossref_work(doi=doi)
    except Exception:
        return {}
    return {
        "record_id": fetched.record_id,
        "title": fetched.title,
        "doi": fetched.doi,
        "pmid": fetched.pmid,
        "year": fetched.year,
        "journal": fetched.journal,
        "citation_payload": dict(fetched.citation_payload),
    }


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
    study_root: Path,
    records: list[Mapping[str, Any]],
    anchor: Mapping[str, Any],
    generated_at: str,
    query: str | None,
    schema_version: int,
) -> dict[str, Any]:
    if not records:
        return {}
    request_id = "pubmed-esummary-" + _slug(
        "-".join(_text(record.get("pmid")) for record in records if record.get("pmid"))
    )
    ledger_ref = _write_provider_response_ledger(
        study_root=study_root,
        provider="pubmed",
        request_id=request_id,
        retrieved_at=generated_at,
        response_status="ok",
        payload={"records": [dict(record) for record in records]},
        schema_version=schema_version,
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
        "credential_status": _public_api_credential("pubmed"),
        "rate_limit_status": _ok_rate_limit(),
        "cache_freshness": _fresh_cache(generated_at),
        "provider_response_ledger_refs": [ledger_ref],
        "items": [item for item in items if item.get("ref")],
    }


def _crossref_provider_from_records(
    *,
    study_root: Path,
    records: tuple[tuple[Mapping[str, Any], str], ...],
    generated_at: str,
    query: str | None,
    schema_version: int,
) -> dict[str, Any]:
    fetched_records: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []
    for record, category in records:
        fetched = _fetch_crossref_record(record)
        if not fetched:
            return {}
        fetched_records.append(fetched)
        item = _provider_item_from_record(fetched, category=category)
        if item.get("ref"):
            items.append(item)
    request_id = "crossref-works-" + _slug("-".join(_text(record.get("doi")) for record in fetched_records))
    ledger_ref = _write_provider_response_ledger(
        study_root=study_root,
        provider="crossref",
        request_id=request_id,
        retrieved_at=generated_at,
        response_status="ok",
        payload={"records": fetched_records},
        schema_version=schema_version,
    )
    return {
        "provider": "crossref",
        "query": _text(query) or _text(fetched_records[0].get("title")),
        "retrieved_at": generated_at,
        "request_id": request_id,
        "response_status": "ok",
        "credential_status": _public_api_credential("crossref"),
        "rate_limit_status": _ok_rate_limit(),
        "cache_freshness": _fresh_cache(generated_at),
        "provider_response_ledger_refs": [ledger_ref],
        "items": items,
    }


def _provider_item_from_record(record: Mapping[str, Any], *, category: str) -> dict[str, Any]:
    return {
        "ref": _record_ref(record),
        "category": category,
        "title": _text(record.get("title")),
        "citation_ledger_ref": _citation_ref_for_record(record),
    }


def _write_provider_response_ledger(
    *,
    study_root: Path,
    provider: str,
    request_id: str,
    retrieved_at: str,
    response_status: str,
    payload: Mapping[str, Any],
    schema_version: int,
) -> str:
    relative_path = Path("artifacts") / "medical_paper" / "provider_responses" / f"{_slug(request_id)}.json"
    output_path = study_root / relative_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                "surface": "literature_provider_response_ledger_entry",
                "schema_version": schema_version,
                "provider": provider,
                "request_id": request_id,
                "retrieved_at": retrieved_at,
                "response_status": response_status,
                "payload": dict(payload),
                "quality_claim_authorized": False,
                "mechanical_projection_can_authorize_quality": False,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(relative_path)


def _public_api_credential(provider: str) -> dict[str, str]:
    refs = {
        "pubmed": "public_api:pubmed_esummary",
        "crossref": "public_api:crossref_works",
        "semantic_scholar": "public_api:semantic_scholar_graph",
    }
    return {
        "status": "ready",
        "credential_ref": refs.get(provider, "public_api:provider"),
    }


def _items_for_provider(*, provider_name: str, payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    categories = {
        "pubmed": ("anchor_papers",),
        "crossref": ("guidelines", "systematic_reviews"),
        "semantic_scholar": ("journal_neighbor_refs",),
    }.get(provider_name, ())
    items: list[dict[str, Any]] = []
    for category in categories:
        for ref in [_text(item) for item in _list(payload.get(category)) if _text(item)]:
            item: dict[str, Any] = {
                "ref": ref,
                "category": category,
                "title": ref,
                "citation_ledger_ref": _citation_ref_from_ref(ref, payload),
            }
            if category == "journal_neighbor_refs":
                item["score"] = 0.9
                item["score_source_ref"] = "existing_literature_intelligence_os"
            items.append(item)
    return items


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


def _citation_ref_from_ref(ref: str, payload: Mapping[str, Any]) -> str:
    for existing in [_text(item) for item in _list(payload.get("citation_ledger_refs")) if _text(item)]:
        if _slug(ref).lower() in _slug(existing).lower() or ref in existing:
            return existing
    return f"paper/evidence_ledger.json#{_slug(ref)}"


def _record_ref(record: Mapping[str, Any]) -> str:
    if pmid := _text(record.get("pmid")):
        return f"pmid:{pmid}"
    if doi := _text(record.get("doi")):
        return f"doi:{doi}"
    return _text(record.get("record_id")) or ""


def _semantic_papers(payload: object) -> list[Mapping[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, Mapping)]
    if isinstance(payload, Mapping):
        data = payload.get("data")
        if isinstance(data, list):
            return [item for item in data if isinstance(item, Mapping)]
        if payload.get("paperId") or payload.get("paper_id"):
            return [payload]
    return []


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
        "expires_at": _plus_one_day(generated_at),
    }


def _ok_rate_limit() -> dict[str, Any]:
    return {
        "status": "ok",
        "remaining": None,
        "reset_at": "",
        "backoff": {"policy": "exponential", "retry_after_seconds": 0},
    }


def _ready_credential(provider: str | None) -> dict[str, str]:
    return _public_api_credential(_text(provider))


def _search_query_from_payload(payload: Mapping[str, Any]) -> str:
    return _text(_mapping(payload.get("search_strategy")).get("query")) or _text(payload.get("query"))


def _date_from_timestamp(value: str) -> str:
    return value[:10] if len(value) >= 10 else _utc_now()[:10]


def _plus_one_day(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        parsed = datetime.now(timezone.utc)
    return (parsed + timedelta(days=1)).isoformat()


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


__all__ = [
    "payload_from_existing_literature_intelligence",
    "payload_from_provider_adapters",
]
