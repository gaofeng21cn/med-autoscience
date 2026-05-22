from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def build_route_stage_residue_boundary(
    *,
    active_path_residue_cleanup_gates: Iterable[Mapping[str, Any]],
    functional_module_inventory: Iterable[Mapping[str, Any]],
    physical_delete_requires_all_gates: Iterable[str],
) -> dict[str, Any]:
    active_path_gates = list(active_path_residue_cleanup_gates)
    module_inventory = list(functional_module_inventory)
    sqlite_gate = _active_path_gate_by_id(
        "lifecycle_refs_sqlite_index",
        active_path_gates,
    )
    status_gate = _active_path_gate_by_id(
        "status_projection_domain_truth_refs",
        active_path_gates,
    )
    sidecar_gate = _active_path_gate_by_id("owner_route_handoff_adapter", active_path_gates)
    domain_health_diagnostic_loop = _module_by_id("domain_health_diagnostic_loop_shell", module_inventory)
    return {
        "surface_kind": "mas_route_stage_residue_boundary",
        "version": "mas-route-stage-residue-boundary.v1",
        "route_is_stage": False,
        "route_semantics_owner": "med-autoscience",
        "domain_truth_owner": "med-autoscience",
        "stage_graph_owner": "one-person-lab",
        "stage_lifecycle_owner": "one-person-lab",
        "runtime_transition_owner": "one-person-lab",
        "queue_attempt_owner": "one-person-lab",
        "opl_hydrates_route_refs_to_queue_and_stage_attempts": True,
        "mas_owns_inter_route_scheduler": False,
        "legacy_surface_names_current_active": False,
        "all_residual_surfaces_physically_retired": True,
        "physical_retirement_scope": "legacy_mas_private_runtime_route_surface_names",
        "physical_retirement_gate": list(physical_delete_requires_all_gates),
        "residual_surfaces": _residual_surfaces(
            sqlite_gate=sqlite_gate,
            status_gate=status_gate,
            sidecar_gate=sidecar_gate,
            domain_health_diagnostic_loop=domain_health_diagnostic_loop,
            module_inventory=module_inventory,
        ),
        "forbidden_claims": [
            "route_is_stage",
            "mas_owned_generic_route_scheduler",
            "mas_owned_generic_stage_attempt_graph",
            "legacy_surface_names_current_active",
            "sqlite_lifecycle_ref_deleted",
            "status_projection_deleted",
            "owner_route_handoff_adapter_deleted",
            "domain_status_authority_migrated_to_opl",
        ],
    }


def _residual_surfaces(
    *,
    sqlite_gate: Mapping[str, Any],
    status_gate: Mapping[str, Any],
    sidecar_gate: Mapping[str, Any],
    domain_health_diagnostic_loop: Mapping[str, Any],
    module_inventory: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "surface_id": "owner_route_reconcile",
            "retired_legacy_surface_id": "domain_route_scan",
            "current_role": "domain_owner_route_projection_and_receipt_guard",
            "classification": "declarative_pack_generated_surface",
            "owner": "med-autoscience",
            "generic_runtime_owner_claim_allowed": False,
            "physical_retired": True,
            "physical_delete_permitted": False,
            "opl_consumes_as": "owner_route_refs_for_opl_queue_stage_attempt_hydration",
            "stage_or_queue_owner": "one-person-lab",
            "gate_ref": "functional_module_inventory.owner_route_reconcile_materialize_dispatch_shell",
        },
        {
            "surface_id": "progress_projection",
            "retired_legacy_surface_id": "study_runtime_status",
            "current_role": status_gate["current_role"],
            "classification": "minimal_authority_function",
            "owner": "med-autoscience",
            "generic_runtime_owner_claim_allowed": False,
            "physical_retired": True,
            "physical_delete_permitted": status_gate["physical_delete_permitted"],
            "delete_or_tombstone_after": list(status_gate["delete_or_tombstone_after"]),
            "gate_ref": "active_path_residue_cleanup_gates.status_projection_domain_truth_refs",
        },
        {
            "surface_id": "domain_health_diagnostic",
            "retired_legacy_surface_id": "runtime_watch",
            "current_role": "domain_health_one_shot_diagnostic_not_long_loop_scheduler",
            "classification": "minimal_authority_function",
            "owner": "med-autoscience",
            "generic_runtime_owner_claim_allowed": False,
            "physical_retired": True,
            "long_loop_shell_physical_retired": domain_health_diagnostic_loop.get("physical_retired") is True,
            "active_long_loop_caller_allowed": domain_health_diagnostic_loop.get("active_caller_allowed") is True,
            "physical_delete_permitted": False,
            "gate_ref": "functional_module_inventory.domain_health_diagnostic",
        },
        {
            "surface_id": "domain_decision_authority",
            "retired_legacy_surface_id": "status_and_decision",
            "current_role": "domain_decision_authority_with_refs_only_projection_shell",
            "classification": "control_plane_thinning_item",
            "owner": "med-autoscience",
            "generic_runtime_owner_claim_allowed": False,
            "physical_retired": True,
            "physical_delete_permitted": False,
            "migration_state": "legacy_name_retired_authority_and_projection_split_active",
            "gate_ref": "docs/runtime/opl_private_implementation_migration_inventory.md#domain_status_authority",
        },
        {
            "surface_id": "owner_receipt_lifecycle_ref_index",
            "retired_legacy_surface_id": "runtime_lifecycle_sqlite_sidecar",
            "current_role": sqlite_gate["current_role"],
            "classification": "refs_only_adapter",
            "owner": "med-autoscience",
            "generic_runtime_owner_claim_allowed": False,
            "physical_retired": True,
            "physical_delete_permitted": sqlite_gate["physical_delete_permitted"],
            "active_caller_count": sqlite_gate["active_caller_count"],
            "delete_or_tombstone_after": list(sqlite_gate["delete_or_tombstone_after"]),
            "gate_ref": "active_path_residue_cleanup_gates.lifecycle_refs_sqlite_index",
            "refs_only_gate": _refs_only_adapter_gate_by_id(
                "lifecycle_refs_adapter",
                module_inventory,
            ),
        },
        {
            "surface_id": "owner_route_dispatch_receipt",
            "retired_legacy_surface_id": "sidecar_dispatch_adapter",
            "current_role": sidecar_gate["current_role"],
            "classification": "retained_owner_route_handoff_adapter",
            "owner": "med-autoscience",
            "generic_runtime_owner_claim_allowed": False,
            "physical_retired": True,
            "physical_delete_permitted": sidecar_gate["physical_delete_permitted"],
            "active_caller_count": sidecar_gate["active_caller_count"],
            "delete_or_tombstone_after": list(sidecar_gate["delete_or_tombstone_after"]),
            "gate_ref": "active_path_residue_cleanup_gates.owner_route_handoff_adapter",
        },
    ]


def _active_path_gate_by_id(
    residue_id: str,
    active_path_gates: Iterable[Mapping[str, Any]],
) -> Mapping[str, Any]:
    for item in active_path_gates:
        if item["residue_id"] == residue_id:
            return item
    raise KeyError(f"unknown active-path residue gate: {residue_id}")


def _module_by_id(
    module_id: str,
    module_inventory: Iterable[Mapping[str, Any]],
) -> Mapping[str, Any]:
    for item in module_inventory:
        if item["module_id"] == module_id:
            return item
    raise KeyError(f"unknown functional module: {module_id}")


def _refs_only_adapter_gate_by_id(
    module_id: str,
    module_inventory: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    gate = _module_by_id(module_id, module_inventory).get("retirement_gate")
    if isinstance(gate, Mapping):
        return dict(gate)
    raise KeyError(f"unknown refs-only adapter gate: {module_id}")


__all__ = ["build_route_stage_residue_boundary"]
