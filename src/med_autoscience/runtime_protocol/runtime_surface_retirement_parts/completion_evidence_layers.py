from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def completion_evidence_layers(
    open_surfaces: list[Mapping[str, Any]],
    *,
    surface_audits: list[dict[str, Any]],
    violations: list[dict[str, str]],
) -> dict[str, Any]:
    surfaces_by_id = {str(surface.get("surface_id")): surface for surface in open_surfaces}
    audits_by_id = {str(audit.get("surface_id")): audit for audit in surface_audits}
    required_refs = sorted(
        {
            ref
            for surface in open_surfaces
            for ref in _physical_delete_required_refs(surface)
        }
    )
    blocked_surface_ids = sorted(
        str(audit["surface_id"])
        for audit in surface_audits
        if audit.get("physical_delete_gate_open") is True
        or audit.get("domain_owner_action_dispatch_physical_delete_allowed") is False
        or audit.get("domain_authority_refs_physical_delete_allowed") is False
        or audit.get("legacy_stage_run_physical_delete_allowed") is False
        or audit.get("agent_tool_arsenal_physical_delete_allowed") is False
    )
    open_surface_tails = [
        _open_surface_tail(
            surface_id,
            surfaces_by_id.get(surface_id, {}),
            audits_by_id.get(surface_id, {}),
        )
        for surface_id in blocked_surface_ids
    ]
    live_soak_proven = bool(required_refs) and all(
        _surface_live_or_no_active_proven(surfaces_by_id.get(str(audit["surface_id"]), {}), audit)
        for audit in surface_audits
    )
    physical_delete_allowed = bool(surface_audits) and all(
        audit.get("physical_delete_gate_open") is False for audit in surface_audits
    )
    return {
        "repo_no_authority_guard": {
            "status": (
                "satisfied_with_repo_evidence" if not violations else "violations_present"
            ),
            "violations_count": len(violations),
        },
        "live_soak_or_no_active_caller": {
            "status": "satisfied_with_live_evidence" if live_soak_proven else "evidence_required",
            "proven": live_soak_proven,
            "required_ref_families": required_refs,
            "open_surface_tails": open_surface_tails,
        },
        "physical_retirement": {
            "status": "allowed" if physical_delete_allowed else "evidence_required",
            "allowed": physical_delete_allowed,
            "blocked_surface_ids": blocked_surface_ids,
            "open_surface_tails": open_surface_tails,
        },
    }


def _physical_delete_required_refs(surface: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    surface_id = _text(surface.get("surface_id")) or "unknown_surface"
    for container_key in ("retirement_gate", "active_caller_boundary"):
        container = surface.get(container_key)
        if isinstance(container, Mapping):
            refs.extend(_required_refs_from_container(surface_id, container))
    nested_paths = (
        ("active_caller_soak_boundary",),
        ("opl_state_index_takeover_bridge",),
        ("opl_state_index_takeover_bridge", "runtime_active_private_state_index_caller_scan"),
        ("opl_state_index_takeover_bridge", "legacy_helper_active_caller_scan"),
        ("legacy_stage_run_abi_boundary", "active_stage_run_abi_caller_scan"),
        ("live_owner_consumption_soak_boundary",),
        ("opl_obligation_actuator_tail_readback",),
        ("opl_runtime_health_observability_tail_readback",),
        (
            "opl_runtime_health_observability_tail_readback",
            "active_diagnostic_projection_caller_scan",
        ),
        ("opl_materializer_projection_tail_readback",),
        ("opl_workbench_shell_readback_tail",),
        ("opl_runtime_lifecycle_maintenance_tail_readback",),
        ("opl_runtime_storage_maintenance_tail_readback",),
    )
    for path in nested_paths:
        container: Any = surface
        for key in path:
            container = container.get(key) if isinstance(container, Mapping) else None
        if isinstance(container, Mapping):
            refs.extend(_required_refs_from_container(surface_id, container))
    return sorted(set(refs))


def _required_refs_from_container(
    surface_id: str,
    container: Mapping[str, Any],
) -> list[str]:
    refs: list[str] = []
    ref = _text(container.get("required_before_physical_delete"))
    if ref is not None:
        refs.append(ref)
    required = container.get("physical_delete_requires")
    if isinstance(required, list):
        refs.extend(
            _normalize_required_ref(surface_id, item)
            for item in required
            if _text(item) is not None
        )
    for gate_key, suffix in _BOOLEAN_GATE_REF_SUFFIXES.items():
        if container.get(gate_key) is True:
            refs.append(f"{surface_id}_{suffix}")
    return refs


_BOOLEAN_GATE_REF_SUFFIXES = {
    "direct_hosted_parity_required": "direct_hosted_parity_ref",
    "live_every_active_caller_soak_required": "live_every_active_caller_soak_ref",
    "live_opl_cleanup_policy_takeover_required": "live_opl_cleanup_policy_takeover_ref",
    "live_opl_storage_policy_takeover_required": "live_opl_storage_policy_takeover_ref",
    "live_owner_consumption_soak_required": "live_owner_consumption_soak_ref",
    "no_active_caller_required_before_physical_delete": "no_active_caller_physical_delete_ref",
    "owner_retirement_decision_required": "owner_retirement_decision_ref",
    "runtime_health_live_opl_observability_readback_required": (
        "live_opl_observability_readback_ref"
    ),
    "opl_workbench_shell_readback_required": "opl_workbench_shell_readback_ref",
}


def _normalize_required_ref(surface_id: str, value: Any) -> str:
    text = _text(value)
    if text is None:
        return f"{surface_id}_unknown_physical_delete_ref"
    if text.endswith("_ref"):
        return text
    return f"{surface_id}_{text}_ref"


def _open_surface_tail(
    surface_id: str,
    surface: Mapping[str, Any],
    audit: Mapping[str, Any],
) -> dict[str, Any]:
    required_refs = _physical_delete_required_refs(surface)
    live_or_no_active_proven = _surface_live_or_no_active_proven(surface, audit)
    return {
        "surface_id": surface_id,
        "authority_status": audit.get("authority_status"),
        "status": (
            "satisfied_with_live_evidence"
            if live_or_no_active_proven and audit.get("physical_delete_gate_open") is False
            else "evidence_required"
        ),
        "required_ref_families": required_refs,
        "live_or_no_active_proven": live_or_no_active_proven,
        "physical_delete_gate_open": audit.get("physical_delete_gate_open"),
        "physical_delete_allowed": audit.get("physical_delete_gate_open") is False,
        "forbidden_completion_interpretations": _forbidden_completion_interpretations(surface),
    }


def _surface_live_or_no_active_proven(
    surface: Mapping[str, Any],
    audit: Mapping[str, Any],
) -> bool:
    if audit.get("physical_delete_gate_open") is False:
        return True
    proof_fields = (
        ("active_caller_soak_boundary", "live_every_active_caller_soak_proven"),
        ("active_caller_soak_boundary", "no_active_caller_proven"),
        (
            "opl_state_index_takeover_bridge",
            "legacy_helper_active_caller_scan",
            "no_active_replay_or_local_inspection_caller_proven",
        ),
        (
            "legacy_stage_run_abi_boundary",
            "active_stage_run_abi_caller_scan",
            "no_active_stage_run_abi_caller_proven",
        ),
        ("live_owner_consumption_soak_boundary", "no_active_caller_proven"),
        ("opl_obligation_actuator_tail_readback", "tail_readback_proven"),
        (
            "opl_obligation_actuator_tail_readback",
            "no_active_mas_obligation_actuator_caller_proven",
        ),
        ("opl_runtime_health_observability_tail_readback", "tail_readback_proven"),
        (
            "opl_runtime_health_observability_tail_readback",
            "no_active_diagnostic_projection_caller_proven",
        ),
        ("opl_materializer_projection_tail_readback", "tail_readback_proven"),
        (
            "opl_materializer_projection_tail_readback",
            "no_active_materializer_projection_caller_proven",
        ),
        ("opl_workbench_shell_readback_tail", "tail_readback_proven"),
        (
            "opl_workbench_shell_readback_tail",
            "no_active_workbench_projection_action_caller_proven",
        ),
        ("opl_runtime_lifecycle_maintenance_tail_readback", "tail_readback_proven"),
        (
            "opl_runtime_lifecycle_maintenance_tail_readback",
            "no_active_lifecycle_maintenance_adapter_caller_proven",
        ),
        ("opl_runtime_storage_maintenance_tail_readback", "tail_readback_proven"),
        (
            "opl_runtime_storage_maintenance_tail_readback",
            "no_active_storage_maintenance_adapter_caller_proven",
        ),
    )
    if any(_nested_value(surface, path) is True for path in proof_fields):
        return True
    if surface.get("surface_id") == "agent_tool_arsenal_scientific_capability_registry":
        return (
            _nested_value(
                surface,
                ("live_owner_consumption_soak_boundary", "live_owner_consumption_soak_proven"),
            )
            is True
            and _nested_value(
                surface,
                ("live_owner_consumption_soak_boundary", "direct_hosted_parity_proven"),
            )
            is True
        )
    return False


def _nested_value(surface: Mapping[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = surface
    for key in path:
        value = value.get(key) if isinstance(value, Mapping) else None
    return value


def _forbidden_completion_interpretations(surface: Mapping[str, Any]) -> list[str]:
    claims: set[str] = set()
    for container in _completion_interpretation_containers(surface):
        forbidden = container.get("forbidden_completion_claims")
        if isinstance(forbidden, list):
            claims.update(str(item) for item in forbidden)
    return sorted(claims)


def _completion_interpretation_containers(surface: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    containers: list[Mapping[str, Any]] = []
    for key in (
        "active_caller_boundary",
        "active_caller_soak_boundary",
        "live_owner_consumption_soak_boundary",
        "retirement_gate",
        "opl_state_index_takeover_bridge",
        "legacy_stage_run_abi_boundary",
    ):
        value = surface.get(key)
        if isinstance(value, Mapping):
            containers.append(value)
    for path in (
        ("opl_state_index_takeover_bridge", "runtime_active_private_state_index_caller_scan"),
        ("opl_state_index_takeover_bridge", "legacy_helper_active_caller_scan"),
        ("legacy_stage_run_abi_boundary", "active_stage_run_abi_caller_scan"),
        ("opl_obligation_actuator_tail_readback",),
        ("opl_runtime_health_observability_tail_readback",),
        (
            "opl_runtime_health_observability_tail_readback",
            "active_diagnostic_projection_caller_scan",
        ),
        ("opl_materializer_projection_tail_readback",),
        ("opl_workbench_shell_readback_tail",),
        ("opl_runtime_lifecycle_maintenance_tail_readback",),
        ("opl_runtime_storage_maintenance_tail_readback",),
    ):
        value: Any = surface
        for key in path:
            value = value.get(key) if isinstance(value, Mapping) else None
        if isinstance(value, Mapping):
            containers.append(value)
    return containers


def _text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["completion_evidence_layers"]
