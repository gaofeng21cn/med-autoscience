from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote
from urllib.request import urlopen

from med_autoscience.literature_records import LiteratureRecord


CROSSREF_WORKS_URL = "https://api.crossref.org/works"


def _fetch_bytes(url: str) -> bytes:
    with urlopen(url, timeout=30) as response:
        return response.read()


def _first_text(values: object) -> str | None:
    if not isinstance(values, list):
        return None
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _parse_year(message: dict[str, Any]) -> int | None:
    for field in ("published-print", "published-online", "issued"):
        date_block = message.get(field)
        if not isinstance(date_block, dict):
            continue
        date_parts = date_block.get("date-parts")
        if not isinstance(date_parts, list) or not date_parts:
            continue
        first_part = date_parts[0]
        if isinstance(first_part, list) and first_part:
            year = first_part[0]
            if isinstance(year, int):
                return year
            if isinstance(year, str) and year.isdigit():
                return int(year)
    return None


def _parse_authors(message: dict[str, Any]) -> tuple[str, ...]:
    raw_authors = message.get("author")
    if not isinstance(raw_authors, list):
        return tuple()
    authors: list[str] = []
    for item in raw_authors:
        if not isinstance(item, dict):
            continue
        given = item.get("given")
        family = item.get("family")
        if isinstance(given, str) and given.strip() and isinstance(family, str) and family.strip():
            authors.append(f"{given.strip()} {family.strip()}")
            continue
        if isinstance(family, str) and family.strip():
            authors.append(family.strip())
    return tuple(authors)


def fetch_crossref_work(*, doi: str) -> LiteratureRecord:
    normalized_doi = doi.strip()
    if not normalized_doi:
        raise ValueError("doi must not be empty")

    payload = json.loads(_fetch_bytes(f"{CROSSREF_WORKS_URL}/{quote(normalized_doi, safe='')}").decode("utf-8"))
    message = payload.get("message")
    if not isinstance(message, dict):
        raise ValueError("Crossref payload missing message object")

    title = _first_text(message.get("title"))
    if title is None:
        raise ValueError("Crossref payload missing title")
    journal = _first_text(message.get("container-title"))

    message_doi = message.get("DOI")
    parsed_doi = message_doi.strip() if isinstance(message_doi, str) and message_doi.strip() else normalized_doi

    return LiteratureRecord(
        record_id=f"doi:{parsed_doi}",
        title=title,
        authors=_parse_authors(message),
        year=_parse_year(message),
        journal=journal,
        doi=parsed_doi,
        pmid=None,
        pmcid=None,
        arxiv_id=None,
        abstract=None,
        full_text_availability="metadata_only",
        source_priority=3,
        citation_payload={"crossref_message": message},
        local_asset_paths=(),
        relevance_role="candidate",
        claim_support_scope=(),
    )
