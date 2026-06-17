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
    refreshed["paper_recovery_state"] = _build_recovery_state_unless_successor_current(
        refreshed,
        build_paper_recovery_state=build_paper_recovery_state,
        build_current_executable_owner_action=build_current_executable_owner_action,
    )
    refreshed = _with_recovery_supervisor_decision(refreshed)
    refreshed = _without_stale_provider_supervisor_block(refreshed)
    normalized_current_action = build_current_executable_owner_action(refreshed)
    refreshed = refresh_current_execution_surfaces(
        payload={**refreshed, "current_executable_owner_action": normalized_current_action},
        status=status,
        handoff=handoff,
        runtime_health_snapshot=runtime_health_snapshot,
    )
    refreshed["paper_recovery_state"] = _build_recovery_state_unless_successor_current(
        refreshed,
        build_paper_recovery_state=build_paper_recovery_state,
        build_current_executable_owner_action=build_current_executable_owner_action,
    )
    refreshed = _with_recovery_supervisor_decision(refreshed)
    refreshed = _without_stale_provider_supervisor_block(refreshed)
    provider_fields = provider_admission_projection_fields(
        payload=refreshed,
        handoff=handoff,
        study_root=study_root,
    )
    refreshed.update(provider_fields)
    refreshed = sync_progress_first_owner_action_admission(refreshed)
    refreshed["paper_recovery_state"] = _build_recovery_state_unless_successor_current(
        refreshed,
        build_paper_recovery_state=build_paper_recovery_state,
        build_current_executable_owner_action=build_current_executable_owner_action,
    )
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
        "derived_from_event_id": _projection_metadata_value(
            refreshed,
            "derived_from_event_id",
            handoff=handoff,
        ),
        "observed_generation": _projection_metadata_value(
            refreshed,
            "observed_generation",
            handoff=handoff,
        ),
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


def _build_recovery_state_unless_successor_current(
    payload: Mapping[str, Any],
    *,
    build_paper_recovery_state: Callable[[Mapping[str, Any]], dict[str, Any]],
    build_current_executable_owner_action: Callable[[Mapping[str, Any]], dict[str, Any] | None],
) -> dict[str, Any]:
    recovery = _mapping_copy(payload.get("paper_recovery_state"))
    current_action = build_current_executable_owner_action(payload)
    if _paper_recovery_successor_state_current(recovery) and _action_source(
        current_action
    ) in {None, "paper_recovery_state.next_safe_action.successor_owner_action"}:
        return recovery
    return build_paper_recovery_state(payload)


def _action_source(action: Mapping[str, Any] | None) -> str | None:
    return _text(_mapping_copy(action).get("source"))


def _text(value: object) -> str | None:
    if isinstance(value, str):
        text = value.strip()
        return text or None
    return None


def _paper_recovery_successor_state_current(recovery: Mapping[str, Any]) -> bool:
    if recovery.get("phase") != "owner_action_ready":
        return False
    next_safe_action = _mapping_copy(recovery.get("next_safe_action"))
    if next_safe_action.get("kind") != "materialize_successor_owner_action":
        return False
    successor = _mapping_copy(next_safe_action.get("successor_owner_action"))
    return (
        bool(successor.get("action_type"))
        and bool(successor.get("work_unit_id"))
        and bool(successor.get("work_unit_fingerprint") or successor.get("action_fingerprint"))
    )


def _projection_metadata_value(
    payload: Mapping[str, Any],
    key: str,
    *,
    handoff: Mapping[str, Any],
) -> Any:
    for source in (
        _mapping_copy(_mapping_copy(payload.get("current_work_unit")).get("projection_metadata")),
        _mapping_copy(_mapping_copy(payload.get("current_work_unit")).get("currentness_basis")),
        _mapping_copy(_mapping_copy(payload.get("current_executable_owner_action")).get("projection_metadata")),
        _mapping_copy(_mapping_copy(payload.get("current_executable_owner_action")).get("owner_route_currentness_basis")),
        _mapping_copy(handoff.get("projection_metadata")),
        _mapping_copy(_mapping_copy(handoff.get("paper_progress_policy_result")).get("projection_metadata")),
    ):
        value = source.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


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
