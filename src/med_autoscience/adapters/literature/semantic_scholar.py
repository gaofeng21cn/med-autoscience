from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.adapters.literature.opl_connect_receipts import (
    resolve_literature_records_from_receipts,
)


def resolve_semantic_scholar_records_from_receipts(
    *,
    references: Sequence[Mapping[str, Any]],
    provider_receipts: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    return resolve_literature_records_from_receipts(
        references=references,
        provider_receipts=provider_receipts,
        providers=("semantic-scholar",),
        accepted_evidence_providers=("semantic-scholar",),
    )


__all__ = [
    "resolve_semantic_scholar_records_from_receipts",
]
