from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from ..shared import _mapping_copy


def normalize_paper_recovery_execution_projection(
    *,
    payload: dict[str, Any],
    status: Mapping[str, Any],
    handoff: Mapping[str, Any],
    runtime_health_snapshot: Mapping[str, Any],
    study_root: object,
    build_current_executable_owner_action: Callable[[Mapping[str, Any]], dict[str, Any] | None],
    refresh_current_execution_surfaces: Callable[..., dict[str, Any]],
    provider_admission_projection_fields: Callable[..., dict[str, Any]],
    sync_progress_first_owner_action_admission: Callable[[dict[str, Any]], dict[str, Any]],
    build_paper_recovery_state: Callable[[Mapping[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    updated = _with_recovery_supervisor_decision(dict(payload))
    recovery_current_action = build_current_executable_owner_action(updated)
    refreshed = refresh_current_execution_surfaces(
        payload={**updated, "current_executable_owner_action": recovery_current_action},
        status=status,
        handoff=handoff,
        runtime_health_snapshot=runtime_health_snapshot,
    )
    refreshed["paper_recovery_state"] = build_paper_recovery_state(refreshed)
    refreshed = _with_recovery_supervisor_decision(refreshed)
    refreshed = _without_stale_provider_supervisor_block(refreshed)
    normalized_current_action = build_current_executable_owner_action(refreshed)
    refreshed = refresh_current_execution_surfaces(
        payload={**refreshed, "current_executable_owner_action": normalized_current_action},
        status=status,
        handoff=handoff,
        runtime_health_snapshot=runtime_health_snapshot,
    )
    refreshed["paper_recovery_state"] = build_paper_recovery_state(refreshed)
    refreshed = _with_recovery_supervisor_decision(refreshed)
    refreshed = _without_stale_provider_supervisor_block(refreshed)
    provider_fields = provider_admission_projection_fields(
        payload=refreshed,
        handoff=handoff,
        study_root=study_root,
    )
    refreshed.update(provider_fields)
    refreshed = sync_progress_first_owner_action_admission(refreshed)
    refreshed["paper_recovery_state"] = build_paper_recovery_state(refreshed)
    refreshed = _with_recovery_supervisor_decision(refreshed)
    if "provider_admission_blocked_by_supervisor_decision" not in provider_fields:
        refreshed = _without_stale_provider_supervisor_block(refreshed)
    refreshed["paper_recovery_execution_projection"] = {
        "surface_kind": "paper_recovery_execution_projection",
        "schema_version": 1,
        "authority": False,
        "projection_owner": "med-autoscience",
        "transition_runtime_owner": "one-person-lab",
        "refresh_mode": "single_pass_projection_normalization",
        "fixed_point_runtime_owner": "one-person-lab",
        "mas_can_run_fixed_point_runtime": False,
        "source_signature": _refresh_signature(payload),
        "derived_signature": _refresh_signature(refreshed),
    }
    return refreshed


def _with_recovery_supervisor_decision(payload: dict[str, Any]) -> dict[str, Any]:
    updated = dict(payload)
    recovery = _mapping_copy(updated.get("paper_recovery_state"))
    if not recovery:
        return updated
    decision = _mapping_copy(recovery.get("supervisor_decision"))
    if decision:
        updated["paper_autonomy_supervisor_decision"] = decision
    else:
        updated.pop("paper_autonomy_supervisor_decision", None)
    return updated


def _without_stale_provider_supervisor_block(payload: dict[str, Any]) -> dict[str, Any]:
    updated = dict(payload)
    updated.pop("provider_admission_blocked_by_supervisor_decision", None)
    return updated


def _refresh_signature(payload: Mapping[str, Any]) -> tuple[Any, ...]:
    return tuple(
        _mapping_copy(payload.get(key)) if key not in {"provider_admission_pending_count"} else payload.get(key)
        for key in (
            "current_executable_owner_action",
            "current_work_unit",
            "current_execution_envelope",
            "paper_recovery_state",
            "provider_admission_pending_count",
            "provider_admission_candidates",
            "owner_action_admission",
            "paper_autonomy_supervisor_decision",
            "provider_admission_blocked_by_supervisor_decision",
        )
    )


__all__ = ["normalize_paper_recovery_execution_projection"]
