from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.adapters.literature.opl_connect_receipts import (
    resolve_literature_records_from_receipts,
)


def resolve_pubmed_summaries_from_receipts(
    *,
    pmids: Sequence[str],
    provider_receipts: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    normalized_pmids = tuple(dict.fromkeys(pmid.strip() for pmid in pmids if pmid.strip()))
    if not normalized_pmids:
        return {
            **resolve_literature_records_from_receipts(references=(), provider_receipts=provider_receipts),
            "status": "resolved",
        }
    resolution = resolve_literature_records_from_receipts(
        references=tuple({"id": f"pmid:{pmid}", "pmid": pmid} for pmid in normalized_pmids),
        provider_receipts=provider_receipts,
        providers=("pubmed",),
        accepted_evidence_providers=("pubmed",),
    )
    resolution["provider_resolution_request"]["identifier_provider"] = "pubmed"
    return resolution


__all__ = [
    "resolve_pubmed_summaries_from_receipts",
]
