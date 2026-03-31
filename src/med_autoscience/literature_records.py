from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LiteratureRecord:
    record_id: str
    title: str
    authors: tuple[str, ...]
    year: int | None
    journal: str | None
    doi: str | None
    pmid: str | None
    pmcid: str | None
    arxiv_id: str | None
    abstract: str | None
    full_text_availability: str
    source_priority: int
    citation_payload: dict[str, object]
    local_asset_paths: tuple[str, ...]
    relevance_role: str
    claim_support_scope: tuple[str, ...]

    @property
    def primary_source(self) -> str:
        if self.pmid:
            return "pubmed"
        if self.pmcid:
            return "pmc"
        if self.doi:
            return "doi"
        if self.arxiv_id:
            return "arxiv"
        return "local"
