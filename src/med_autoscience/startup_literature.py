from __future__ import annotations

from dataclasses import asdict
from dataclasses import replace
import re
from typing import Any
from urllib.parse import urlparse

from med_autoscience.adapters.literature import doi as doi_adapter
from med_autoscience.adapters.literature import pubmed as pubmed_adapter
from med_autoscience.literature_records import LiteratureRecord


_PUBMED_HOSTS = {
    "pubmed.ncbi.nlm.nih.gov",
    "www.pubmed.ncbi.nlm.nih.gov",
    "ncbi.nlm.nih.gov",
    "www.ncbi.nlm.nih.gov",
}
_DOI_HOSTS = {
    "doi.org",
    "www.doi.org",
    "dx.doi.org",
}
_ARXIV_HOSTS = {
    "arxiv.org",
    "www.arxiv.org",
}
_PMID_PATTERN = re.compile(r"/(?:pubmed|sites/entrez|sites/myncbi)/(?P<pmid>\d+)(?:[/?#]|$)")
_PUBMED_PATH_PATTERN = re.compile(r"^/(?P<pmid>\d+)(?:/)?$")
_ARXIV_PATH_PATTERN = re.compile(r"^/(?:abs|pdf)/(?P<arxiv_id>[^/?#]+)")


def _string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _string(item)) is not None]


def _pubmed_pmid_from_url(url: str) -> str | None:
    try:
        parsed = urlparse(url)
    except ValueError:
        return None
    host = parsed.netloc.strip().lower()
    path = parsed.path.strip()
    if host in {"pubmed.ncbi.nlm.nih.gov", "www.pubmed.ncbi.nlm.nih.gov"}:
        match = _PUBMED_PATH_PATTERN.match(path)
        return match.group("pmid") if match else None
    if host in {"ncbi.nlm.nih.gov", "www.ncbi.nlm.nih.gov"}:
        match = _PMID_PATTERN.search(path)
        return match.group("pmid") if match else None
    return None


def _doi_from_url(url: str) -> str | None:
    try:
        parsed = urlparse(url)
    except ValueError:
        return None
    if parsed.netloc.strip().lower() not in _DOI_HOSTS:
        return None
    text = parsed.path.strip("/")
    return text or None


def _arxiv_id_from_url(url: str) -> str | None:
    try:
        parsed = urlparse(url)
    except ValueError:
        return None
    if parsed.netloc.strip().lower() not in _ARXIV_HOSTS:
        return None
    match = _ARXIV_PATH_PATTERN.match(parsed.path.strip())
    return match.group("arxiv_id") if match else None


def _seed_record_id(*, url: str | None, title: str | None) -> str:
    raw = url or title or "startup-seed"
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", raw).strip("_")
    return normalized[:80] or "startup_seed"


def _seed_from_paper_url(url: str) -> dict[str, Any]:
    return {
        "paper_id": _seed_record_id(url=url, title=None),
        "role": "anchor_paper",
        "url": url,
        "title": None,
        "journal": None,
        "year": None,
        "pmid": _pubmed_pmid_from_url(url),
        "doi": _doi_from_url(url),
        "arxiv_id": _arxiv_id_from_url(url),
        "claim_support_scope": (),
    }


def _seed_from_similar_paper(example: dict[str, Any]) -> dict[str, Any]:
    source_url = _string(example.get("source_url"))
    title = _string(example.get("title"))
    journal = _string(example.get("journal"))
    year = example.get("year")
    normalized_year = year if isinstance(year, int) else None
    pmid = _string(example.get("pmid")) or (_pubmed_pmid_from_url(source_url) if source_url else None)
    doi = _string(example.get("doi")) or (_doi_from_url(source_url) if source_url else None)
    arxiv_id = _string(example.get("arxiv_id")) or (_arxiv_id_from_url(source_url) if source_url else None)
    claim_support_scope = tuple(
        scope
        for scope in ("paper_framing", "journal_fit_neighbor")
        if scope
    )
    return {
        "paper_id": _seed_record_id(url=source_url, title=title),
        "role": "adjacent_inspiration",
        "url": source_url,
        "title": title,
        "journal": journal,
        "year": normalized_year,
        "pmid": pmid,
        "doi": doi,
        "arxiv_id": arxiv_id,
        "claim_support_scope": claim_support_scope,
    }


def _collect_startup_seeds(startup_contract: dict[str, Any]) -> list[dict[str, Any]]:
    seeds: list[dict[str, Any]] = []
    for url in _string_list(startup_contract.get("paper_urls")):
        seeds.append(_seed_from_paper_url(url))

    journal_shortlist = startup_contract.get("journal_shortlist")
    candidates = journal_shortlist.get("candidates") if isinstance(journal_shortlist, dict) else None
    if isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            similar_examples = candidate.get("similar_paper_examples")
            if not isinstance(similar_examples, list):
                continue
            for item in similar_examples:
                if not isinstance(item, dict):
                    continue
                seeds.append(_seed_from_similar_paper(item))
    return seeds


def _dedupe_keys(seed: dict[str, Any]) -> tuple[str, ...]:
    keys: list[str] = []
    for prefix, raw in (
        ("pmid", seed.get("pmid")),
        ("doi", seed.get("doi")),
        ("arxiv", seed.get("arxiv_id")),
        ("url", seed.get("url")),
        ("paper", seed.get("paper_id")),
    ):
        text = _string(raw)
        if text is not None:
            keys.append(f"{prefix}:{text.lower()}")
    return tuple(keys)


def _dedupe_seeds(seeds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    seen: set[str] = set()
    for seed in seeds:
        keys = _dedupe_keys(seed)
        if any(key in seen for key in keys):
            continue
        kept.append(seed)
        seen.update(keys)
    return kept


def _merge_record(record: LiteratureRecord, *, role: str | None, claim_support_scope: tuple[str, ...]) -> LiteratureRecord:
    next_role = role or record.relevance_role
    next_claim_scope = claim_support_scope or record.claim_support_scope
    return replace(record, relevance_role=next_role, claim_support_scope=next_claim_scope)


def _record_from_seed(seed: dict[str, Any]) -> LiteratureRecord | None:
    title = _string(seed.get("title"))
    url = _string(seed.get("url"))
    if title is None or url is None:
        return None
    journal = _string(seed.get("journal"))
    year = seed.get("year")
    normalized_year = year if isinstance(year, int) else None
    claim_support_scope = tuple(_string_list(list(seed.get("claim_support_scope") or ())))
    return LiteratureRecord(
        record_id=f"url:{_seed_record_id(url=url, title=title)}",
        title=title,
        authors=(),
        year=normalized_year,
        journal=journal,
        doi=_string(seed.get("doi")),
        pmid=_string(seed.get("pmid")),
        pmcid=None,
        arxiv_id=_string(seed.get("arxiv_id")),
        abstract=None,
        full_text_availability="metadata_only",
        source_priority=5,
        citation_payload={"url": url},
        local_asset_paths=(),
        relevance_role=_string(seed.get("role")) or "candidate",
        claim_support_scope=claim_support_scope,
    )


def resolve_startup_literature_records(*, startup_contract: dict[str, Any]) -> list[dict[str, object]]:
    if not isinstance(startup_contract, dict):
        raise TypeError("startup_contract must be a mapping")

    seeds = _dedupe_seeds(_collect_startup_seeds(startup_contract))
    if not seeds:
        return []

    pmid_order: list[str] = []
    doi_order: list[str] = []
    for seed in seeds:
        pmid = _string(seed.get("pmid"))
        doi = _string(seed.get("doi"))
        if pmid is not None and pmid not in pmid_order:
            pmid_order.append(pmid)
        elif doi is not None and doi not in doi_order:
            doi_order.append(doi)

    records_by_pmid: dict[str, LiteratureRecord] = {}
    if pmid_order:
        for record in pubmed_adapter.fetch_pubmed_summary(pmids=pmid_order):
            records_by_pmid[str(record.pmid)] = record

    records_by_doi: dict[str, LiteratureRecord] = {}
    for doi in doi_order:
        record = doi_adapter.fetch_crossref_work(doi=doi)
        if record.doi is not None:
            records_by_doi[record.doi.lower()] = record

    resolved: list[LiteratureRecord] = []
    seen_record_ids: set[str] = set()
    for seed in seeds:
        claim_support_scope = tuple(_string_list(list(seed.get("claim_support_scope") or ())))
        role = _string(seed.get("role"))
        pmid = _string(seed.get("pmid"))
        doi = _string(seed.get("doi"))
        record: LiteratureRecord | None = None
        if pmid is not None:
            fetched = records_by_pmid.get(pmid)
            if fetched is not None:
                record = _merge_record(fetched, role=role, claim_support_scope=claim_support_scope)
        elif doi is not None:
            fetched = records_by_doi.get(doi.lower())
            if fetched is not None:
                record = _merge_record(fetched, role=role, claim_support_scope=claim_support_scope)
        if record is None:
            record = _record_from_seed(seed)
        if record is None or record.record_id in seen_record_ids:
            continue
        seen_record_ids.add(record.record_id)
        resolved.append(record)
    return [asdict(record) for record in resolved]
