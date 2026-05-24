"""Medical literature adapters for PubMed, PMC, DOI, and Semantic Scholar providers."""

from .doi import fetch_crossref_work
from .pmc import fetch_pmc_record
from .pubmed import fetch_pubmed_summary
from .semantic_scholar import fetch_paper_batch
from .semantic_scholar import match_paper
from .semantic_scholar import provider_payload_from_response as semantic_scholar_provider_payload_from_response
from .semantic_scholar import record_from_paper as semantic_scholar_record_from_paper
from .semantic_scholar import search_papers as search_semantic_scholar_papers

__all__ = [
    "fetch_crossref_work",
    "fetch_paper_batch",
    "fetch_pmc_record",
    "fetch_pubmed_summary",
    "match_paper",
    "search_semantic_scholar_papers",
    "semantic_scholar_provider_payload_from_response",
    "semantic_scholar_record_from_paper",
]
