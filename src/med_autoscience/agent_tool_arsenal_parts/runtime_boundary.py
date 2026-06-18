from __future__ import annotations

from typing import Any, Mapping


OPL_CAPABILITY_RUNTIME_OWNER = "one-person-lab"
OPL_CAPABILITY_RUNTIME_KIND = "OPL Capability Runtime"
OPL_CAPABILITY_RUNTIME_READBACK_REQUIREMENT = "opl_capability_runtime_hosted_readback"


def opl_capability_runtime_readback_requirement() -> dict[str, Any]:
    return {
        "requirement_id": OPL_CAPABILITY_RUNTIME_READBACK_REQUIREMENT,
        "runtime_owner": OPL_CAPABILITY_RUNTIME_OWNER,
        "runtime_kind": OPL_CAPABILITY_RUNTIME_KIND,
        "required_for_modes": ["resolve", "plan", "hosted_consumption"],
        "required_readback_fields": [
            "capability_runtime_owner",
            "capability_runtime_identity",
            "capability_selection_receipt_ref",
            "capability_invocation_receipt_ref",
            "current_owner_delta_ref",
            "exactly_one_outcome",
        ],
        "mas_readback_consumer_only": True,
        "missing_readback_blocks_mutating_invocation": True,
        "missing_readback_can_authorize_provider_admission": False,
        "missing_readback_can_write_domain_truth": False,
        "missing_readback_can_replace_owner_receipt_or_typed_blocker": False,
    }


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
        "hosted_opl_capability_runtime_required": True,
        "opl_capability_runtime_readback_requirement": (
            opl_capability_runtime_readback_requirement()
        ),
        "mas_resolve_mode_is_selector_authority": False,
        "mas_plan_mode_is_invocation_authority": False,
        "resolve_or_plan_can_invoke_tool": False,
        "resolve_or_plan_can_write_domain_truth": False,
        "resolve_or_plan_can_authorize_provider_admission": False,
        "resolve_or_plan_can_replace_owner_receipt_or_typed_blocker": False,
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
    "OPL_CAPABILITY_RUNTIME_READBACK_REQUIREMENT",
    "merge_opl_capability_runtime_boundary",
    "opl_capability_runtime_boundary",
    "opl_capability_runtime_readback_requirement",
]
