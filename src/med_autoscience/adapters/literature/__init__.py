"""Medical literature adapters for PubMed, PMC, and DOI providers."""

from .doi import fetch_crossref_work
from .pmc import fetch_pmc_record
from .pubmed import fetch_pubmed_summary

__all__ = [
    "fetch_crossref_work",
    "fetch_pmc_record",
    "fetch_pubmed_summary",
]
