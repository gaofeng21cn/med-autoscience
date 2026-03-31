from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from med_autoscience.literature_records import LiteratureRecord


PUBMED_ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


def _fetch_bytes(url: str) -> bytes:
    with urlopen(url, timeout=30) as response:
        return response.read()


def _parse_year(pubdate: object) -> int | None:
    if not isinstance(pubdate, str):
        return None
    head = pubdate.strip().split(" ", maxsplit=1)[0]
    return int(head) if head.isdigit() else None


def _parse_authors(entry: dict[str, Any]) -> tuple[str, ...]:
    raw_authors = entry.get("authors")
    if not isinstance(raw_authors, list):
        return tuple()
    authors: list[str] = []
    for item in raw_authors:
        if isinstance(item, dict):
            name = item.get("name")
            if isinstance(name, str) and name.strip():
                authors.append(name.strip())
    return tuple(authors)


def _parse_doi(entry: dict[str, Any]) -> str | None:
    raw_ids = entry.get("articleids")
    if not isinstance(raw_ids, list):
        return None
    for item in raw_ids:
        if not isinstance(item, dict):
            continue
        idtype = item.get("idtype")
        value = item.get("value")
        if idtype == "doi" and isinstance(value, str) and value.strip():
            return value.strip()
    return None


def fetch_pubmed_summary(*, pmids: list[str]) -> list[LiteratureRecord]:
    if not pmids:
        return []
    query = urlencode({"db": "pubmed", "id": ",".join(pmids), "retmode": "json"})
    payload = json.loads(_fetch_bytes(f"{PUBMED_ESUMMARY_URL}?{query}").decode("utf-8"))
    result = payload.get("result")
    if not isinstance(result, dict):
        raise ValueError("PubMed ESummary payload missing result object")
    uids = result.get("uids")
    if not isinstance(uids, list):
        raise ValueError("PubMed ESummary payload missing uids list")

    records: list[LiteratureRecord] = []
    for uid in uids:
        uid_text = str(uid).strip()
        entry = result.get(uid_text)
        if not isinstance(entry, dict):
            raise ValueError(f"PubMed ESummary payload missing record for uid={uid_text}")

        title = entry.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"PubMed ESummary payload missing title for uid={uid_text}")
        journal = entry.get("fulljournalname")
        journal_text = journal.strip() if isinstance(journal, str) and journal.strip() else None

        records.append(
            LiteratureRecord(
                record_id=f"pmid:{uid_text}",
                title=title.strip(),
                authors=_parse_authors(entry),
                year=_parse_year(entry.get("pubdate")),
                journal=journal_text,
                doi=_parse_doi(entry),
                pmid=uid_text,
                pmcid=None,
                arxiv_id=None,
                abstract=None,
                full_text_availability="abstract_only",
                source_priority=2,
                citation_payload={"pubmed_esummary": entry},
                local_asset_paths=(),
                relevance_role="candidate",
                claim_support_scope=(),
            )
        )
    return records
