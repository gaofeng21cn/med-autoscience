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
        "sqlite_lifecycle_sidecar_index",
        active_path_gates,
    )
    status_gate = _active_path_gate_by_id(
        "status_projection_domain_truth_refs",
        active_path_gates,
    )
    sidecar_gate = _active_path_gate_by_id("sidecar_dispatch_adapter", active_path_gates)
    runtime_watch_loop = _module_by_id("runtime_watch_loop_shell", module_inventory)
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
        "all_residual_surfaces_physically_retired": False,
        "physical_retirement_gate": list(physical_delete_requires_all_gates),
        "residual_surfaces": _residual_surfaces(
            sqlite_gate=sqlite_gate,
            status_gate=status_gate,
            sidecar_gate=sidecar_gate,
            runtime_watch_loop=runtime_watch_loop,
            module_inventory=module_inventory,
        ),
        "forbidden_claims": [
            "route_is_stage",
            "mas_owned_generic_route_scheduler",
            "mas_owned_generic_stage_attempt_graph",
            "all_residual_surfaces_physically_retired",
            "sqlite_lifecycle_sidecar_deleted",
            "status_projection_deleted",
            "sidecar_dispatch_adapter_deleted",
            "status_and_decision_migrated_to_opl",
        ],
    }


def _residual_surfaces(
    *,
    sqlite_gate: Mapping[str, Any],
    status_gate: Mapping[str, Any],
    sidecar_gate: Mapping[str, Any],
    runtime_watch_loop: Mapping[str, Any],
    module_inventory: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "surface_id": "domain_route_scan",
            "current_role": "domain_owner_route_projection_and_receipt_guard",
            "classification": "declarative_pack_generated_surface",
            "owner": "med-autoscience",
            "generic_runtime_owner_claim_allowed": False,
            "physical_retired": False,
            "physical_delete_permitted": False,
            "opl_consumes_as": "owner_route_refs_for_opl_queue_stage_attempt_hydration",
            "stage_or_queue_owner": "one-person-lab",
            "gate_ref": "functional_module_inventory.domain_route_scan_materialize_dispatch_shell",
        },
        {
            "surface_id": "study_runtime_status",
            "current_role": status_gate["current_role"],
            "classification": "minimal_authority_function",
            "owner": "med-autoscience",
            "generic_runtime_owner_claim_allowed": False,
            "physical_retired": False,
            "physical_delete_permitted": status_gate["physical_delete_permitted"],
            "delete_or_tombstone_after": list(status_gate["delete_or_tombstone_after"]),
            "gate_ref": "active_path_residue_cleanup_gates.status_projection_domain_truth_refs",
        },
        {
            "surface_id": "runtime_watch",
            "current_role": "domain_health_one_shot_diagnostic_not_long_loop_scheduler",
            "classification": "minimal_authority_function",
            "owner": "med-autoscience",
            "generic_runtime_owner_claim_allowed": False,
            "physical_retired": False,
            "long_loop_shell_physical_retired": runtime_watch_loop.get("physical_retired") is True,
            "active_long_loop_caller_allowed": runtime_watch_loop.get("active_caller_allowed") is True,
            "physical_delete_permitted": False,
            "gate_ref": "functional_module_inventory.runtime_watch_domain_health",
        },
        {
            "surface_id": "status_and_decision",
            "current_role": "domain_decision_authority_with_refs_only_projection_shell",
            "classification": "control_plane_thinning_item",
            "owner": "med-autoscience",
            "generic_runtime_owner_claim_allowed": False,
            "physical_retired": False,
            "physical_delete_permitted": False,
            "migration_state": "needs_split_before_opl_status_projection_migration",
            "gate_ref": "docs/runtime/opl_private_implementation_migration_inventory.md#status_and_decision",
        },
        {
            "surface_id": "runtime_lifecycle_sqlite_sidecar",
            "current_role": sqlite_gate["current_role"],
            "classification": "refs_only_adapter",
            "owner": "med-autoscience",
            "generic_runtime_owner_claim_allowed": False,
            "physical_retired": False,
            "physical_delete_permitted": sqlite_gate["physical_delete_permitted"],
            "active_caller_count": sqlite_gate["active_caller_count"],
            "delete_or_tombstone_after": list(sqlite_gate["delete_or_tombstone_after"]),
            "gate_ref": "active_path_residue_cleanup_gates.sqlite_lifecycle_sidecar_index",
            "refs_only_gate": _refs_only_adapter_gate_by_id(
                "runtime_lifecycle_sqlite_reference_adapter",
                module_inventory,
            ),
        },
        {
            "surface_id": "sidecar_dispatch_adapter",
            "current_role": sidecar_gate["current_role"],
            "classification": "retained_owner_route_handoff_adapter",
            "owner": "med-autoscience",
            "generic_runtime_owner_claim_allowed": False,
            "physical_retired": False,
            "physical_delete_permitted": sidecar_gate["physical_delete_permitted"],
            "active_caller_count": sidecar_gate["active_caller_count"],
            "delete_or_tombstone_after": list(sidecar_gate["delete_or_tombstone_after"]),
            "gate_ref": "active_path_residue_cleanup_gates.sidecar_dispatch_adapter",
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
