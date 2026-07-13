from __future__ import annotations

from typing import Any

from med_autoscience.authority_kernel_inventory.schema import (
    FORBIDDEN_DOMAIN_AUTHORITY,
    GENERIC_RUNTIME_OWNER_NAMES,
    REQUIRED_ITEM_FIELDS,
    AuthorityKernelItem,
)


REQUIRED_CATEGORIES = {
    "owner_receipt_signer",
    "typed_blocker_materializer",
    "source_readiness",
    "publication_quality_gate",
    "artifact_mutation_authorization",
    "memory_accept_reject",
    "no_forbidden_write_proof",
    "refs_only_helper",
    "paper_mission_authority_handler",
    "retired_diagnostic_provenance",
}


def inventory_gaps(items: tuple[AuthorityKernelItem, ...]) -> list[dict[str, Any]]:
    categories = {item.category for item in items}
    gaps: list[dict[str, Any]] = [
        {
            "gap_id": "missing_required_category",
            "missing_categories": sorted(REQUIRED_CATEGORIES - categories),
        }
    ] if REQUIRED_CATEGORIES - categories else []
    for item in items:
        optional_empty_fields = (
            {"active_caller_refs", "allowed_writes"}
            if item.category
            in {"retired_diagnostic_provenance", "paper_mission_authority_handler"}
            else set()
        )
        missing_fields = [
            field
            for field in REQUIRED_ITEM_FIELDS
            if field not in optional_empty_fields and getattr(item, field) in (None, "", (), [])
        ]
        if missing_fields:
            gaps.append(
                {
                    "gap_id": "inventory_item_missing_required_fields",
                    "item_id": item.item_id,
                    "missing_fields": missing_fields,
                }
            )
        missing_forbidden = sorted(set(FORBIDDEN_DOMAIN_AUTHORITY) - set(item.forbidden_authority))
        if missing_forbidden:
            gaps.append(
                {
                    "gap_id": "inventory_item_missing_forbidden_authority",
                    "item_id": item.item_id,
                    "missing_forbidden_authority": missing_forbidden,
                }
            )
        if item.owner in GENERIC_RUNTIME_OWNER_NAMES:
            gaps.append(
                {
                    "gap_id": "generic_runtime_owner_listed_as_retained_authority",
                    "item_id": item.item_id,
                    "owner": item.owner,
                }
            )
    return gaps
