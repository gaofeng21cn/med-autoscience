from __future__ import annotations

from typing import Any, Mapping


OPL_CAPABILITY_RUNTIME_OWNER = "one-person-lab"
OPL_CAPABILITY_RUNTIME_KIND = "OPL Capability Runtime"


def opl_capability_runtime_boundary() -> dict[str, Any]:
    return {
        "selection_runtime_owner": OPL_CAPABILITY_RUNTIME_OWNER,
        "capability_runtime_owner": OPL_CAPABILITY_RUNTIME_OWNER,
        "capability_runtime_kind": OPL_CAPABILITY_RUNTIME_KIND,
        "opl_owns_capability_selection_runtime": True,
        "opl_owns_capability_invocation_runtime": True,
        "mas_selector_authority": False,
        "mas_tool_invocation_runtime_authority": False,
        "missing_refs_trigger_mutating_invocation": False,
        "support_or_diagnostic_tools_auto_selected": False,
        "capability_plan_can_write_domain_truth": False,
        "capability_plan_can_authorize_publication_quality": False,
        "capability_plan_can_authorize_submission_readiness": False,
        "capability_plan_can_replace_owner_receipt": False,
        "capability_plan_can_replace_typed_blocker": False,
    }


def merge_opl_capability_runtime_boundary(
    boundary: Mapping[str, Any] | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    merged = dict(boundary or {})
    merged.update(opl_capability_runtime_boundary())
    for key, value in overrides.items():
        if value is not None:
            merged[key] = value
    return merged


__all__ = [
    "OPL_CAPABILITY_RUNTIME_KIND",
    "OPL_CAPABILITY_RUNTIME_OWNER",
    "merge_opl_capability_runtime_boundary",
    "opl_capability_runtime_boundary",
]
