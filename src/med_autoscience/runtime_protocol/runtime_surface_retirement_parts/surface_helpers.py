from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.runtime_protocol.runtime_surface_retirement_validators import _text


SURFACE_KIND = "mas_runtime_surface_retirement_no_authority_audit"
SCHEMA_VERSION = 1

REPO_SOURCE_ACCEPTED_ADAPTER_DISPOSITIONS = frozenset(
    {
        "opl_authorized_owner_callable_adapter",
        "obligation_readback_projection_consumer",
        "read_only_diagnostic_publisher",
        "read_only_workbench_projection",
        "opl_capability_runtime_projection",
        "opl_authorized_maintenance_callable_adapter_live_takeover_tail_open",
        "opl_authorized_storage_maintenance_callable_adapter_live_takeover_tail_open",
    }
)


def _text_list(value: Any, *, sort: bool = False) -> list[str]:
    if isinstance(value, list):
        texts = [text for item in value if (text := _text(item)) is not None]
        return sorted(texts) if sort else texts
    text = _text(value)
    return [text] if text is not None else []


def _text_set(value: Any) -> set[str]:
    return set(_text_list(value))


def repo_source_retired(surface: Mapping[str, Any]) -> bool:
    disposition = _text(surface.get("current_disposition")) or ""
    if disposition == "physically_retired":
        return True
    return disposition in REPO_SOURCE_ACCEPTED_ADAPTER_DISPOSITIONS


def authority_status(surface: Mapping[str, Any]) -> str:
    surface_id = surface.get("surface_id")
    disposition = _text(surface.get("current_disposition")) or ""
    if surface_id == "stage_outcome_authority":
        return "opl_authorized_owner_callable_adapter_live_tail_open"
    if surface_id in {"runtime_lifecycle_payload_retention", "runtime_storage_maintenance"}:
        return "opl_authorized_maintenance_callable_adapter_live_tail_open"
    if surface_id == "domain_diagnostic_obligation_actuator":
        return "consume_only_readback_projection_live_tail_open"
    if surface_id == "domain_authority_refs_index":
        return "active_callers_migrated_opl_state_index_source_adapter_live_tail_open"
    if surface_id == "agent_tool_arsenal_scientific_capability_registry":
        return "opl_capability_runtime_projection_live_owner_soak_tail_open"
    if surface_id == "progress_portal_study_workbench_overview_action_projection":
        return "read_only_workbench_projection_opl_shell_tail_open"
    if surface_id == "owner_callable_adapter_receipt_latest_wire_projection":
        return "legacy_latest_history_only_stage_run_abi_provenance_tail_open"
    if surface_id == "owner_callable_dispatch_request":
        return "legacy_owner_callable_adapter_carrier_opl_stage_run_abi_provenance_only"
    if disposition.startswith("read_only"):
        return "read_only_projection_no_authority"
    if "projection" in disposition or "refs_only" in disposition:
        return "refs_only_projection_no_authority"
    if "handoff_contract" in disposition:
        return "transition_request_carrier_no_authority"
    return "open_surface_no_authority_guarded"


def allowed_effect(surface: Mapping[str, Any]) -> str:
    boundary = surface.get("active_caller_boundary")
    if isinstance(boundary, Mapping) and _text(boundary.get("active_caller_effect")):
        return str(boundary["active_caller_effect"])
    if surface.get("surface_id") == "stage_outcome_authority":
        return "execute_only_with_trusted_opl_authorization_or_bound_readback"
    if surface.get("surface_id") == "owner_callable_adapter_receipt_latest_wire_projection":
        return "canonical_owner_receipt_or_legacy_stage_run_closeout_provenance_only"
    if isinstance(surface.get("apply_gate"), Mapping):
        return "mutate_only_when_bound_opl_maintenance_authorization_is_present"
    if surface.get("surface_id") == "runtime_health_kernel":
        return "read_only_diagnostic_projection"
    if surface.get("surface_id") == "progress_portal_study_workbench_overview_action_projection":
        return "read_only_owner_delta_summary"
    if surface.get("surface_id") == "agent_tool_arsenal_scientific_capability_registry":
        return "current_owner_delta_bound_capability_projection_explicit_request_only"
    return "refs_only_or_diagnostic_projection"


def requires_readback(surface: Mapping[str, Any]) -> bool:
    gate = surface.get("retirement_gate")
    if isinstance(gate, Mapping):
        return gate.get("completion_claim_requires_live_owner_or_opl_readback") is True
    boundary = surface.get("active_caller_boundary")
    if isinstance(boundary, Mapping):
        return boundary.get("completion_claim_requires_live_owner_or_opl_readback") is True
    return True


def physical_delete_gate_open(surface: Mapping[str, Any]) -> bool:
    if surface.get("current_disposition") == "physically_retired":
        return False
    legacy_stage_run_boundary = surface.get("legacy_stage_run_abi_boundary")
    if (
        isinstance(legacy_stage_run_boundary, Mapping)
        and legacy_stage_run_boundary.get(
            "physical_delete_requires_no_active_stage_run_abi_caller_scan"
        )
        is True
    ):
        scan = legacy_stage_run_boundary.get("active_stage_run_abi_caller_scan")
        return not (
            isinstance(scan, Mapping)
            and scan.get("no_active_stage_run_abi_caller_proven") is True
            and scan.get("physical_delete_allowed") is True
        )
    gate = surface.get("retirement_gate")
    if not isinstance(gate, Mapping):
        return False
    return bool(
        gate.get("no_active_caller_required_before_physical_delete")
        or gate.get("live_opl_cleanup_policy_takeover_required")
        or gate.get("live_opl_storage_policy_takeover_required")
        or gate.get("owner_retirement_decision_required")
        or gate.get("opl_owner_callable_adapter_carrier_tail_readback_required")
        or gate.get("opl_materializer_projection_tail_readback_required")
        or gate.get("opl_workbench_shell_readback_required")
    )


def surfaces(inventory: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    raw_surfaces = inventory.get("surfaces")
    if not isinstance(raw_surfaces, list):
        raise ValueError("runtime surface retirement inventory must contain a surfaces list")
    return [surface for surface in raw_surfaces if isinstance(surface, Mapping)]
