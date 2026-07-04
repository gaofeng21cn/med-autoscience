from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import os
import re
from typing import Any
from urllib.parse import quote, urlencode, urlsplit, urlunsplit, parse_qsl
from urllib.request import Request, urlopen

from med_autoscience.research_integrity.gate_bundle import (
    authority_boundary as gate_authority_boundary,
    build_research_integrity_gate_input_bundle,
)
from med_autoscience.research_integrity.reference_authenticity import (
    build_reference_verification_attestation_dict,
)


SURFACE_KIND = "reference_provider_lookup_bundle"
SCHEMA_VERSION = "mas-reference-provider-lookup.v1"
DEFAULT_PROVIDERS = ("crossref", "pubmed", "openalex", "semantic_scholar")
SUPPORTED_LOOKUP_PROVIDERS = frozenset(DEFAULT_PROVIDERS + ("crossmark", "publisher"))
PROVIDER_LOOKUP_MODE = "transition_only_receipt_first"
AUTHORITATIVE_PROVIDER_TRUTH_OWNER = "OPL Connect provider receipts"

JsonHttpClient = Callable[[str, Mapping[str, str], float], Mapping[str, Any]]


@dataclass(frozen=True)
class ProviderLookupConfig:
    providers: tuple[str, ...] = DEFAULT_PROVIDERS
    timeout_seconds: float = 10.0
    mailto: str | None = None
    user_agent: str = "MedAutoScience Research Integrity/1.0"
    ncbi_tool: str = "med-autoscience"
    ncbi_email: str | None = None
    ncbi_api_key: str | None = None
    openalex_api_key: str | None = None
    semantic_scholar_api_key: str | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None = None) -> ProviderLookupConfig:
        payload = payload or {}
        providers = payload.get("providers") or payload.get("provider") or DEFAULT_PROVIDERS
        if isinstance(providers, str):
            providers = (providers,)
        if not isinstance(providers, Sequence) or isinstance(providers, (bytes, bytearray)):
            raise ValueError("provider lookup `providers` 必须是字符串或字符串数组。")
        normalized = tuple(_provider_name(provider) for provider in providers)
        timeout_value = payload.get("timeout_seconds", os.getenv("MAS_REFERENCE_LOOKUP_TIMEOUT_SECONDS", "10"))
        return cls(
            providers=normalized,
            timeout_seconds=float(timeout_value),
            mailto=_text(payload.get("mailto")) or _text(os.getenv("MAS_REFERENCE_LOOKUP_MAILTO")),
            user_agent=(
                _text(payload.get("user_agent"))
                or _text(os.getenv("MAS_REFERENCE_LOOKUP_USER_AGENT"))
                or cls.user_agent
            ),
            ncbi_tool=_text(payload.get("ncbi_tool")) or _text(os.getenv("NCBI_TOOL")) or cls.ncbi_tool,
            ncbi_email=(
                _text(payload.get("ncbi_email"))
                or _text(payload.get("email"))
                or _text(os.getenv("NCBI_EMAIL"))
            ),
            ncbi_api_key=_text(payload.get("ncbi_api_key")) or _text(os.getenv("NCBI_API_KEY")),
            openalex_api_key=_text(payload.get("openalex_api_key")) or _text(os.getenv("OPENALEX_API_KEY")),
            semantic_scholar_api_key=(
                _text(payload.get("semantic_scholar_api_key"))
                or _text(payload.get("s2_api_key"))
                or _text(os.getenv("SEMANTIC_SCHOLAR_API_KEY"))
                or _text(os.getenv("S2_API_KEY"))
            ),
        )


def build_reference_provider_lookup_bundle(
    *,
    references: Sequence[Mapping[str, Any]] | Mapping[str, Any],
    provider_config: Mapping[str, Any] | ProviderLookupConfig | None = None,
    http_get_json: JsonHttpClient | None = None,
    claim_spans: Sequence[Mapping[str, Any]] = (),
    citation_refs: Sequence[Mapping[str, Any] | str] = (),
    evidence_refs: Sequence[Mapping[str, Any] | str] = (),
    reference_attestation_refs: Sequence[Mapping[str, Any] | str] = (),
    manuscript_sections: Mapping[str, Any] | None = None,
    numeric_facts: object = (),
    display_facts: object = (),
    reporting_checklist_expectations: object = (),
) -> dict[str, Any]:
    config = _config(provider_config)
    reference_items = _reference_sequence(references)
    checks = [
        {
            "reference": normalized_reference,
            "provider_evidence": lookup_reference_provider_evidence(
                normalized_reference,
                provider_config=config,
                http_get_json=http_get_json,
            ),
        }
        for normalized_reference in (_reference_with_id(reference) for reference in reference_items)
    ]
    attestations = [
        {
            "reference_id": str(check["reference"]["id"]),
            "reference": check["reference"],
            "provider_evidence": check["provider_evidence"],
            "attestation": build_reference_verification_attestation_dict(
                check["reference"],
                check["provider_evidence"],
            ),
        }
        for check in checks
    ]
    gate_input = build_research_integrity_gate_input_bundle(
        reference_checks=checks,
        claim_spans=claim_spans,
        citation_refs=citation_refs,
        evidence_refs=evidence_refs,
        reference_attestation_refs=reference_attestation_refs,
        manuscript_sections=manuscript_sections,
        numeric_facts=numeric_facts,
        display_facts=display_facts,
        reporting_checklist_expectations=reporting_checklist_expectations,
    )
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "provider_lookup_mode": PROVIDER_LOOKUP_MODE,
        "receipt_first": True,
        "transition_only": True,
        "live_provider_authority_claimed": False,
        "authoritative_provider_truth_owner": AUTHORITATIVE_PROVIDER_TRUTH_OWNER,
        "status": gate_input["status"],
        "providers": list(config.providers),
        "references": attestations,
        "provider_summary": _provider_summary(attestations),
        "gate_input_bundle": gate_input,
        "authority_boundary": provider_lookup_authority_boundary(),
    }


def lookup_reference_provider_evidence(
    reference: Mapping[str, Any],
    *,
    provider_config: Mapping[str, Any] | ProviderLookupConfig | None = None,
    http_get_json: JsonHttpClient | None = None,
) -> list[dict[str, Any]]:
    config = _config(provider_config)
    client = http_get_json or urllib_json_http_client
    normalized_reference = _reference_with_id(reference)
    evidence: list[dict[str, Any]] = []
    for provider in config.providers:
        try:
            evidence.append(_lookup_provider(provider, normalized_reference, config=config, client=client))
        except Exception as exc:  # pragma: no cover - exercised through fake client failures.
            evidence.append(_provider_error(provider, "provider_lookup_error", str(exc)))
    return evidence


def urllib_json_http_client(url: str, headers: Mapping[str, str], timeout_seconds: float) -> Mapping[str, Any]:
    request = Request(url, headers=dict(headers))
    with urlopen(request, timeout=timeout_seconds) as response:
        payload = response.read().decode("utf-8")
    parsed = json.loads(payload)
    if not isinstance(parsed, Mapping):
        raise ValueError("provider response JSON root must be an object")
    return parsed


def provider_lookup_authority_boundary() -> dict[str, Any]:
    boundary = gate_authority_boundary()
    boundary.update(
        {
            "surface_role": "transition_only_provider_evidence_fetcher",
            "provider_lookup_mode": PROVIDER_LOOKUP_MODE,
            "receipt_first": True,
            "transition_only": True,
            "live_provider_authority_claimed": False,
            "authoritative_provider_truth_owner": AUTHORITATIVE_PROVIDER_TRUTH_OWNER,
            "can_call_external_provider": True,
            "can_claim_live_provider_truth": False,
            "can_be_used_as_authoritative_provider_truth_without_opl_receipt": False,
            "can_write_provider_attempt": False,
            "can_write_provider_cache": False,
            "can_materialize_provider_receipt": False,
            "can_assert_publisher_or_crossmark_status_without_provider_receipt": False,
        }
    )
    return boundary


def _lookup_provider(
    provider: str,
    reference: Mapping[str, Any],
    *,
    config: ProviderLookupConfig,
    client: JsonHttpClient,
) -> dict[str, Any]:
    handlers = {
        "crossref": _lookup_crossref,
        "pubmed": _lookup_pubmed,
        "openalex": _lookup_openalex,
        "semantic_scholar": _lookup_semantic_scholar,
        "crossmark": _lookup_crossmark,
        "publisher": _lookup_publisher,
    }
    return handlers[provider](reference, config=config, client=client)


def _lookup_crossref(
    reference: Mapping[str, Any],
    *,
    config: ProviderLookupConfig,
    client: JsonHttpClient,
) -> dict[str, Any]:
    doi = _doi(reference)
    title = _title(reference)
    params = _optional_params({"mailto": config.mailto})
    if doi:
        url = _url("https://api.crossref.org/works/" + quote(doi, safe=""), params)
    elif title:
        url = _url(
            "https://api.crossref.org/works",
            {**params, "query.title": title, "rows": "1"},
        )
    else:
        return _provider_error("crossref", "insufficient_reference_query", "doi or title is required")

    payload = client(url, _headers(config), config.timeout_seconds)
    message = payload.get("message")
    item: Mapping[str, Any] | None
    if isinstance(message, Mapping) and isinstance(message.get("items"), Sequence):
        item = _first_mapping(message.get("items"))
    elif isinstance(message, Mapping):
        item = message
    else:
        item = None
    if item is None:
        return _provider_not_found("crossref", url)
    return {
        "provider": "crossref",
        "lookup_status": "found",
        "request_url": _redacted_url(url),
        "matched_identifiers": _crossref_identifiers(item),
        "metadata": _crossref_metadata(item),
        "retraction_or_update_flags": _crossref_flags(item),
    }


def _lookup_pubmed(
    reference: Mapping[str, Any],
    *,
    config: ProviderLookupConfig,
    client: JsonHttpClient,
) -> dict[str, Any]:
    pmid = _pmid(reference)
    doi = _doi(reference)
    title = _title(reference)
    if pmid:
        ids = (pmid,)
    else:
        if doi:
            term = f"{doi}[doi]"
        elif title:
            term = f"{title}[title]"
        else:
            return _provider_error("pubmed", "insufficient_reference_query", "pmid, doi or title is required")
        search_url = _url(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            _ncbi_params(config, {"db": "pubmed", "retmode": "json", "term": term, "retmax": "1"}),
        )
        search_payload = client(search_url, _headers(config), config.timeout_seconds)
        ids = tuple(str(item) for item in search_payload.get("esearchresult", {}).get("idlist", ()) if str(item))
    if not ids:
        return _provider_not_found("pubmed", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi")
    summary_url = _url(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
        _ncbi_params(config, {"db": "pubmed", "retmode": "json", "id": ",".join(ids)}),
    )
    summary_payload = client(summary_url, _headers(config), config.timeout_seconds)
    result = summary_payload.get("result")
    item = result.get(ids[0]) if isinstance(result, Mapping) else None
    if not isinstance(item, Mapping):
        return _provider_not_found("pubmed", summary_url)
    return {
        "provider": "pubmed",
        "lookup_status": "found",
        "request_url": _redacted_url(summary_url),
        "matched_identifiers": _pubmed_identifiers(item),
        "metadata": _pubmed_metadata(item),
        "retraction_or_update_flags": _pubmed_flags(item),
    }


def _lookup_openalex(
    reference: Mapping[str, Any],
    *,
    config: ProviderLookupConfig,
    client: JsonHttpClient,
) -> dict[str, Any]:
    if not config.openalex_api_key:
        return _provider_error("openalex", "openalex_api_key_required", "OPENALEX_API_KEY is required")
    doi = _doi(reference)
    title = _title(reference)
    params = {"api_key": config.openalex_api_key}
    if doi:
        url = _url("https://api.openalex.org/works/" + quote("https://doi.org/" + doi, safe=""), params)
    elif title:
        url = _url("https://api.openalex.org/works", {**params, "search": title, "per-page": "1"})
    else:
        return _provider_error("openalex", "insufficient_reference_query", "doi or title is required")
    payload = client(url, _headers(config), config.timeout_seconds)
    if isinstance(payload.get("results"), Sequence):
        item = _first_mapping(payload.get("results"))
    else:
        item = payload
    if item is None or not _text(item.get("id")):
        return _provider_not_found("openalex", url)
    return {
        "provider": "openalex",
        "lookup_status": "found",
        "request_url": _redacted_url(url),
        "matched_identifiers": _openalex_identifiers(item),
        "metadata": _openalex_metadata(item),
        "retraction_or_update_flags": _openalex_flags(item),
    }


def _lookup_semantic_scholar(
    reference: Mapping[str, Any],
    *,
    config: ProviderLookupConfig,
    client: JsonHttpClient,
) -> dict[str, Any]:
    doi = _doi(reference)
    title = _title(reference)
    fields = "paperId,externalIds,title,year,venue,publicationVenue"
    if doi:
        url = _url(
            "https://api.semanticscholar.org/graph/v1/paper/" + quote("DOI:" + doi, safe=""),
            {"fields": fields},
        )
    elif title:
        url = _url(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            {"query": title, "limit": "1", "fields": fields},
        )
    else:
        return _provider_error("semantic_scholar", "insufficient_reference_query", "doi or title is required")
    payload = client(url, _headers(config, provider="semantic_scholar"), config.timeout_seconds)
    if isinstance(payload.get("data"), Sequence):
        item = _first_mapping(payload.get("data"))
    else:
        item = payload
    if item is None or not _text(item.get("paperId")):
        return _provider_not_found("semantic_scholar", url)
    return {
        "provider": "semantic_scholar",
        "lookup_status": "found",
        "request_url": _redacted_url(url),
        "matched_identifiers": _semantic_scholar_identifiers(item),
        "metadata": _semantic_scholar_metadata(item),
        "retraction_or_update_flags": {},
        "provider_limitations": {
            "does_not_assert_retraction_status": True,
            "retraction_status_requires_crossmark_publisher_or_retraction_watch_evidence": True,
        },
    }


def _lookup_crossmark(
    reference: Mapping[str, Any],
    *,
    config: ProviderLookupConfig,
    client: JsonHttpClient,
) -> dict[str, Any]:
    doi = _doi(reference)
    if not doi:
        return _provider_error("crossmark", "insufficient_reference_query", "doi is required")
    url = _url("https://api.crossref.org/works/" + quote(doi, safe=""), _optional_params({"mailto": config.mailto}))
    payload = client(url, _headers(config), config.timeout_seconds)
    message = payload.get("message")
    if not isinstance(message, Mapping):
        return _provider_not_found("crossmark", url)
    return {
        "provider": "crossmark",
        "lookup_status": "found",
        "request_url": _redacted_url(url),
        "matched_identifiers": _crossref_identifiers(message),
        "metadata": _crossref_metadata(message),
        "retraction_or_update_flags": _crossmark_flags(message),
        "provider_limitations": {
            "source": "crossref_rest_api_crossmark_metadata",
            "publisher_update_policy_presence_is_not_publication_readiness": True,
        },
    }


def _lookup_publisher(
    reference: Mapping[str, Any],
    *,
    config: ProviderLookupConfig,
    client: JsonHttpClient,
) -> dict[str, Any]:
    del config, client
    doi = _doi(reference)
    landing_page = _text(
        reference.get("publisher_url")
        or reference.get("publisher_landing_page_url")
        or reference.get("url")
        or reference.get("URL")
    )
    if not (doi or landing_page):
        return _provider_error(
            "publisher",
            "publisher_connector_required",
            "publisher lookup requires DOI or publisher landing page and an OPL connector receipt",
        )
    return {
        "provider": "publisher",
        "lookup_status": "error",
        "error": {
            "code": "publisher_connector_required",
            "message": "MAS thin lookup does not assert publisher status without an OPL connector receipt.",
        },
        "matched_identifiers": {},
        "metadata": _metadata(title=_title(reference), year=_text(reference.get("year")), journal=None),
        "provider_receipt_required": True,
        "provider_limitations": {
            "does_not_call_publisher_site": True,
            "does_not_assert_retraction_status": True,
            "expected_owner": "OPL Connect publisher connector",
        },
    }


def _crossref_identifiers(item: Mapping[str, Any]) -> dict[str, str]:
    identifiers: dict[str, str] = {}
    doi = _text(item.get("DOI") or item.get("doi"))
    if doi:
        identifiers["doi"] = _normalize_doi(doi)
    return identifiers


def _crossref_metadata(item: Mapping[str, Any]) -> dict[str, Any]:
    return _metadata(
        title=_first_text_item(item.get("title")),
        year=_date_parts_year(item),
        journal=_first_text_item(item.get("container-title") or item.get("container_title")),
    )


def _crossref_flags(item: Mapping[str, Any]) -> dict[str, Any]:
    relation = item.get("relation")
    flags: dict[str, Any] = {}
    if isinstance(relation, Mapping):
        if relation.get("is-retracted-by") or relation.get("is-withdrawn-by"):
            flags["retracted"] = True
        if relation.get("is-corrected-by") or relation.get("has-update"):
            flags["has_update"] = True
    update_to = item.get("update-to")
    if isinstance(update_to, Sequence) and not isinstance(update_to, (str, bytes, bytearray)) and update_to:
        flags["has_update"] = True
    return flags


def _pubmed_identifiers(item: Mapping[str, Any]) -> dict[str, str]:
    identifiers: dict[str, str] = {}
    uid = _text(item.get("uid") or item.get("pmid"))
    if uid:
        identifiers["pmid"] = uid
    for article_id in item.get("articleids") or ():
        if not isinstance(article_id, Mapping):
            continue
        id_type = _text(article_id.get("idtype"))
        value = _text(article_id.get("value"))
        if not id_type or not value:
            continue
        if id_type == "doi":
            identifiers["doi"] = _normalize_doi(value)
        elif id_type == "pmcid":
            identifiers["pmcid"] = value
        elif id_type == "pubmed":
            identifiers["pmid"] = value
    return identifiers


def _pubmed_metadata(item: Mapping[str, Any]) -> dict[str, Any]:
    return _metadata(
        title=_text(item.get("title")),
        year=_year_from_text(_text(item.get("pubdate")) or _text(item.get("epubdate"))),
        journal=_text(item.get("fulljournalname")) or _text(item.get("source")),
    )


def _pubmed_flags(item: Mapping[str, Any]) -> dict[str, Any]:
    publication_types = " ".join(str(value) for value in item.get("pubtype") or ()).lower()
    if "retracted publication" in publication_types:
        return {"retracted": True}
    if "published erratum" in publication_types or "corrected and republished article" in publication_types:
        return {"correction": True}
    return {}


def _openalex_identifiers(item: Mapping[str, Any]) -> dict[str, str]:
    identifiers: dict[str, str] = {}
    ids = item.get("ids")
    if isinstance(ids, Mapping):
        doi = _text(ids.get("doi"))
        pmid = _text(ids.get("pmid"))
        pmcid = _text(ids.get("pmcid"))
        if doi:
            identifiers["doi"] = _normalize_doi(doi)
        if pmid:
            identifiers["pmid"] = pmid.removeprefix("https://pubmed.ncbi.nlm.nih.gov/")
        if pmcid:
            identifiers["pmcid"] = pmcid.removeprefix("https://www.ncbi.nlm.nih.gov/pmc/articles/")
    doi = _text(item.get("doi"))
    if doi:
        identifiers["doi"] = _normalize_doi(doi)
    openalex_id = _text(item.get("id"))
    if openalex_id:
        identifiers["openalex"] = openalex_id
    return identifiers


def _openalex_metadata(item: Mapping[str, Any]) -> dict[str, Any]:
    primary_location = item.get("primary_location")
    source = primary_location.get("source") if isinstance(primary_location, Mapping) else None
    journal = source.get("display_name") if isinstance(source, Mapping) else None
    return _metadata(
        title=_text(item.get("title") or item.get("display_name")),
        year=_text(item.get("publication_year")),
        journal=_text(journal),
    )


def _openalex_flags(item: Mapping[str, Any]) -> dict[str, Any]:
    flags: dict[str, Any] = {}
    if item.get("is_retracted") is True:
        flags["retracted"] = True
    if item.get("has_fulltext") is True:
        flags["has_update"] = False
    return flags


def _semantic_scholar_identifiers(item: Mapping[str, Any]) -> dict[str, str]:
    identifiers: dict[str, str] = {}
    paper_id = _text(item.get("paperId"))
    if paper_id:
        identifiers["semantic_scholar"] = paper_id
    external_ids = item.get("externalIds")
    if isinstance(external_ids, Mapping):
        doi = _text(external_ids.get("DOI") or external_ids.get("doi"))
        pmid = _text(external_ids.get("PubMed") or external_ids.get("PMID") or external_ids.get("pubmed"))
        if doi:
            identifiers["doi"] = _normalize_doi(doi)
        if pmid:
            identifiers["pmid"] = pmid
    return identifiers


def _semantic_scholar_metadata(item: Mapping[str, Any]) -> dict[str, Any]:
    publication_venue = item.get("publicationVenue")
    venue = publication_venue.get("name") if isinstance(publication_venue, Mapping) else None
    return _metadata(
        title=_text(item.get("title")),
        year=_text(item.get("year")),
        journal=_text(venue) or _text(item.get("venue")),
    )


def _crossmark_flags(item: Mapping[str, Any]) -> dict[str, Any]:
    flags = _crossref_flags(item)
    update_policy = item.get("update-policy")
    if _text(update_policy):
        flags["crossmark_update_policy"] = True
    assertions = item.get("assertion")
    if isinstance(assertions, Sequence) and not isinstance(assertions, (str, bytes, bytearray)):
        assertion_names = [
            _text(assertion.get("name") or assertion.get("label"))
            for assertion in assertions
            if isinstance(assertion, Mapping)
        ]
        if any(name and "retract" in name.lower() for name in assertion_names):
            flags["retracted"] = True
        if assertion_names:
            flags["crossmark_assertions_present"] = True
    return flags


def _provider_summary(results: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    summary = {"found": 0, "not_found": 0, "error": 0}
    for result in results:
        for evidence in result.get("provider_evidence") or ():
            if not isinstance(evidence, Mapping):
                continue
            status = str(evidence.get("lookup_status") or "error")
            if status in summary:
                summary[status] += 1
            else:
                summary["error"] += 1
    return summary


def _provider_error(provider: str, code: str, message: str) -> dict[str, Any]:
    return {
        "provider": provider,
        "lookup_status": "error",
        "error": {"code": code, "message": message},
        "matched_identifiers": {},
        "metadata": {},
    }


def _provider_not_found(provider: str, url: str) -> dict[str, Any]:
    return {
        "provider": provider,
        "lookup_status": "not_found",
        "request_url": _redacted_url(url),
        "matched_identifiers": {},
        "metadata": {},
    }


def _config(provider_config: Mapping[str, Any] | ProviderLookupConfig | None) -> ProviderLookupConfig:
    if isinstance(provider_config, ProviderLookupConfig):
        return provider_config
    return ProviderLookupConfig.from_mapping(provider_config)


def _reference_sequence(references: Sequence[Mapping[str, Any]] | Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    if isinstance(references, Mapping):
        return (references,)
    if isinstance(references, Sequence) and not isinstance(references, (str, bytes, bytearray)):
        result = tuple(reference for reference in references if isinstance(reference, Mapping))
        if len(result) == len(references):
            return result
    raise ValueError("provider lookup `references` 必须是 reference mapping 或 reference mapping 数组。")


def _reference_with_id(reference: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(reference)
    if _text(normalized.get("id") or normalized.get("reference_id") or normalized.get("ref_id")):
        return normalized
    normalized["id"] = _fingerprint_reference(reference)
    return normalized


def _fingerprint_reference(reference: Mapping[str, Any]) -> str:
    parts = [
        _doi(reference),
        _pmid(reference),
        _title(reference),
        _text(reference.get("year") or reference.get("publication_year")),
    ]
    seed = "|".join(part or "" for part in parts)
    if not seed.strip("|"):
        raise ValueError("reference must include id, doi, pmid, title, or year for provider lookup")
    return "ref_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def _metadata(*, title: str | None, year: str | None, journal: str | None) -> dict[str, str]:
    metadata: dict[str, str] = {}
    if title:
        metadata["title"] = title
    if year:
        metadata["year"] = year
    if journal:
        metadata["journal"] = journal
    return metadata


def _headers(config: ProviderLookupConfig, *, provider: str | None = None) -> dict[str, str]:
    user_agent = config.user_agent
    if config.mailto and "mailto:" not in user_agent:
        user_agent = f"{user_agent} (mailto:{config.mailto})"
    headers = {"Accept": "application/json", "User-Agent": user_agent}
    if provider == "semantic_scholar" and config.semantic_scholar_api_key:
        headers["x-api-key"] = config.semantic_scholar_api_key
    return headers


def _ncbi_params(config: ProviderLookupConfig, params: Mapping[str, str]) -> dict[str, str]:
    result = dict(params)
    result["tool"] = config.ncbi_tool
    if config.ncbi_email:
        result["email"] = config.ncbi_email
    if config.ncbi_api_key:
        result["api_key"] = config.ncbi_api_key
    return result


def _optional_params(params: Mapping[str, str | None]) -> dict[str, str]:
    return {key: value for key, value in params.items() if value}


def _url(base_url: str, params: Mapping[str, str]) -> str:
    if not params:
        return base_url
    return base_url + "?" + urlencode(params)


def _redacted_url(url: str) -> str:
    split = urlsplit(url)
    query = urlencode(
        [
            (key, "<redacted>" if key in {"api_key"} else value)
        for key, value in parse_qsl(split.query, keep_blank_values=True)
        ]
    )
    return urlunsplit((split.scheme, split.netloc, split.path, query, split.fragment))


def _provider_name(value: object) -> str:
    provider = str(value or "").strip().lower().replace("-", "_")
    if provider not in SUPPORTED_LOOKUP_PROVIDERS:
        raise ValueError(f"unsupported provider lookup provider: {provider!r}")
    return provider


def _first_mapping(value: object) -> Mapping[str, Any] | None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return None
    for item in value:
        if isinstance(item, Mapping):
            return item
    return None


def _doi(reference: Mapping[str, Any]) -> str | None:
    value = _text(reference.get("doi") or reference.get("DOI"))
    if not value:
        identifiers = reference.get("identifiers")
        if isinstance(identifiers, Mapping):
            value = _text(identifiers.get("doi") or identifiers.get("DOI"))
    return _normalize_doi(value) if value else None


def _pmid(reference: Mapping[str, Any]) -> str | None:
    value = _text(reference.get("pmid") or reference.get("PMID") or reference.get("pubmed_id"))
    if not value:
        identifiers = reference.get("identifiers")
        if isinstance(identifiers, Mapping):
            value = _text(identifiers.get("pmid") or identifiers.get("PMID") or identifiers.get("pubmed_id"))
    return value


def _title(reference: Mapping[str, Any]) -> str | None:
    return _text(reference.get("title") or reference.get("Title"))


def _normalize_doi(value: str) -> str:
    text = value.strip()
    text = text.removeprefix("https://doi.org/").removeprefix("http://doi.org/")
    text = text.removeprefix("doi:")
    return text.strip().lower()


def _first_text_item(value: object) -> str | None:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            text = _text(item)
            if text:
                return text
        return None
    return _text(value)


def _date_parts_year(item: Mapping[str, Any]) -> str | None:
    for key in ("published-print", "published-online", "published", "created", "deposited"):
        payload = item.get(key)
        if not isinstance(payload, Mapping):
            continue
        date_parts = payload.get("date-parts")
        if (
            isinstance(date_parts, Sequence)
            and date_parts
            and isinstance(date_parts[0], Sequence)
            and date_parts[0]
        ):
            return _year_from_text(_text(date_parts[0][0]))
    return None


def _year_from_text(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"\d{4}", value)
    return match.group(0) if match else None


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "DEFAULT_PROVIDERS",
    "AUTHORITATIVE_PROVIDER_TRUTH_OWNER",
    "PROVIDER_LOOKUP_MODE",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "ProviderLookupConfig",
    "build_reference_provider_lookup_bundle",
    "lookup_reference_provider_evidence",
    "provider_lookup_authority_boundary",
    "urllib_json_http_client",
]
