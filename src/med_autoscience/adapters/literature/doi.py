from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.adapters.literature.opl_connect_receipts import (
    resolve_literature_records_from_receipts,
)


def resolve_crossref_work_from_receipts(
    *,
    doi: str,
    provider_receipts: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    normalized_doi = doi.strip()
    if not normalized_doi:
        raise ValueError("doi must not be empty")
    return resolve_literature_records_from_receipts(
        references=({"id": f"doi:{normalized_doi}", "doi": normalized_doi},),
        provider_receipts=provider_receipts,
        providers=("crossref",),
        accepted_evidence_providers=("crossref",),
    )


def crossref_records_from_receipts(
    *,
    dois: Sequence[str],
    provider_receipts: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    normalized_dois = tuple(dict.fromkeys(doi.strip() for doi in dois if doi.strip()))
    return resolve_literature_records_from_receipts(
        references=tuple({"id": f"doi:{doi}", "doi": doi} for doi in normalized_dois),
        provider_receipts=provider_receipts,
        providers=("crossref",),
        accepted_evidence_providers=("crossref",),
    )


__all__ = [
    "crossref_records_from_receipts",
    "resolve_crossref_work_from_receipts",
]
