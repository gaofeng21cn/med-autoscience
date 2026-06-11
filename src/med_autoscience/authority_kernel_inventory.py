from __future__ import annotations

from typing import Any

from med_autoscience.agent_tool_arsenal import FORBIDDEN_DOMAIN_AUTHORITY
from med_autoscience.authority_kernel_inventory_parts.gaps import inventory_gaps
from med_autoscience.authority_kernel_inventory_parts.items import inventory_items
from med_autoscience.authority_kernel_inventory_parts.schema import (
    CONTRACT_ID,
    CONTRACT_REF,
    GENERIC_RUNTIME_OWNER_NAMES,
    INVENTORY_STATE,
    OWNER,
    REQUIRED_ITEM_FIELDS,
    SCHEMA_VERSION,
    AuthorityKernelItem,
)


def build_authority_kernel_inventory() -> dict[str, Any]:
    items = tuple(inventory_items())
    gaps = inventory_gaps(items)
    return {
        "surface_kind": "mas_authority_kernel_inventory",
        "contract_id": CONTRACT_ID,
        "schema_version": SCHEMA_VERSION,
        "owner": OWNER,
        "state": INVENTORY_STATE,
        "contract_ref": CONTRACT_REF,
        "ordinary_planning_root": "current_owner_delta",
        "source_of_truth_refs": [
            "docs/runtime/designs/mas_opl_agent_os_target_operating_architecture.md",
            "docs/active/mas-ideal-state-gap-plan.md",
            "src/med_autoscience/runtime_control/owner_callable_registry.py",
            "src/med_autoscience/agent_tool_arsenal.py",
            "contracts/foundry-agent-os-domain-kernel-manifest.json",
            "contracts/mas-paper-study-stage-pack.json",
        ],
        "required_item_fields": list(REQUIRED_ITEM_FIELDS),
        "forbidden_domain_authority": list(FORBIDDEN_DOMAIN_AUTHORITY),
        "generic_runtime_owner_names": sorted(GENERIC_RUNTIME_OWNER_NAMES),
        "items": [item.to_payload() for item in items],
        "counts": {
            "item_count": len(items),
            "category_count": len({item.category for item in items}),
            "owner_callable_backed_count": sum(
                1
                for item in items
                if any(ref.startswith("owner_callable:") for ref in item.active_caller_refs)
            ),
            "upcollect_target_count": sum(1 for item in items if item.upcollect_target),
            "retirement_gate_count": sum(1 for item in items if item.retirement_gate),
            "gap_count": len(gaps),
        },
        "gaps": gaps,
        "non_claims": {
            "authority_fully_retired": False,
            "physical_thinning_complete": False,
            "production_ready": False,
            "paper_line_progress": False,
            "publication_ready": False,
            "artifact_mutation_authorized": False,
        },
    }


__all__ = [
    "CONTRACT_ID",
    "CONTRACT_REF",
    "GENERIC_RUNTIME_OWNER_NAMES",
    "REQUIRED_ITEM_FIELDS",
    "build_authority_kernel_inventory",
]
