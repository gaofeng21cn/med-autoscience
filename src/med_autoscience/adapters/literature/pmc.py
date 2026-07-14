from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.adapters.literature.opl_connect_receipts import (
    resolve_literature_records_from_receipts,
)


def resolve_pmc_record_from_receipts(
    *,
    pmcid: str,
    provider_receipts: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    normalized_pmcid = pmcid.strip()
    if not normalized_pmcid:
        raise ValueError("pmcid must not be empty")
    resolution = resolve_literature_records_from_receipts(
        references=({"id": f"pmc:{normalized_pmcid}", "pmcid": normalized_pmcid},),
        provider_receipts=provider_receipts,
        providers=("pmc", "pubmed"),
        accepted_evidence_providers=("pmc", "pubmed"),
    )
    resolution["provider_resolution_request"]["identifier_provider"] = "pmc"
    return resolution


__all__ = [
    "resolve_pmc_record_from_receipts",
]
