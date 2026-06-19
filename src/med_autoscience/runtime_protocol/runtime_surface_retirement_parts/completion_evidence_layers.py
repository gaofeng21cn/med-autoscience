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
    )
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
        },
        "physical_retirement": {
            "status": "allowed" if physical_delete_allowed else "evidence_required",
            "allowed": physical_delete_allowed,
            "blocked_surface_ids": blocked_surface_ids,
        },
    }


def _physical_delete_required_refs(surface: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for container_key in ("retirement_gate", "active_caller_boundary"):
        container = surface.get(container_key)
        if isinstance(container, Mapping):
            ref = _text(container.get("required_before_physical_delete"))
            if ref is not None:
                refs.append(ref)
    nested_paths = (
        ("active_caller_soak_boundary",),
        ("opl_state_index_takeover_bridge", "legacy_helper_active_caller_scan"),
        ("legacy_stage_run_abi_boundary", "active_stage_run_abi_caller_scan"),
    )
    for path in nested_paths:
        container: Any = surface
        for key in path:
            container = container.get(key) if isinstance(container, Mapping) else None
        if isinstance(container, Mapping):
            ref = _text(container.get("required_before_physical_delete"))
            if ref is not None:
                refs.append(ref)
    return refs


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
    )
    return any(_nested_value(surface, path) is True for path in proof_fields)


def _nested_value(surface: Mapping[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = surface
    for key in path:
        value = value.get(key) if isinstance(value, Mapping) else None
    return value


def _text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["completion_evidence_layers"]
