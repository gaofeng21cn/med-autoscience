from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from ..current_executable_owner_action_parts.non_advancing_terminal_closeout import (
    canonical_current_work_unit_terminal_typed_blocker,
    without_same_identity_terminal_typed_blocker,
)
from ...current_work_unit_parts.paper_recovery_successor import (
    PAPER_RECOVERY_SUCCESSOR_DELTA_KIND,
    PAPER_RECOVERY_SUCCESSOR_SOURCE,
    action_supersedes_terminal_selector_residue,
    paper_recovery_successor_supersedes_terminal_selector_residue,
)
from ..current_executable_owner_action_parts.paper_recovery import (
    owner_action_from_paper_recovery_state,
    paper_recovery_successor_action_ready,
)
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
    updated["paper_recovery_state"] = _build_recovery_state_unless_successor_current(
        updated,
        handoff=handoff,
        build_paper_recovery_state=build_paper_recovery_state,
        build_current_executable_owner_action=build_current_executable_owner_action,
    )
    updated = _with_recovery_supervisor_decision(updated)
    recovery_current_action = _current_action_for_recovery_refresh(
        updated,
        handoff=handoff,
        build_current_executable_owner_action=build_current_executable_owner_action,
    )
    refreshed = refresh_current_execution_surfaces(
        payload={**updated, "current_executable_owner_action": recovery_current_action},
        status=status,
        handoff=handoff,
        runtime_health_snapshot=runtime_health_snapshot,
    )
    refreshed["paper_recovery_state"] = _build_recovery_state_unless_successor_current(
        refreshed,
        handoff=handoff,
        build_paper_recovery_state=build_paper_recovery_state,
        build_current_executable_owner_action=build_current_executable_owner_action,
    )
    refreshed = _with_recovery_supervisor_decision(refreshed)
    refreshed = _without_stale_provider_supervisor_block(refreshed)
    normalized_current_action = _current_action_for_recovery_refresh(
        refreshed,
        handoff=handoff,
        build_current_executable_owner_action=build_current_executable_owner_action,
    )
    refreshed = refresh_current_execution_surfaces(
        payload={**refreshed, "current_executable_owner_action": normalized_current_action},
        status=status,
        handoff=handoff,
        runtime_health_snapshot=runtime_health_snapshot,
    )
    refreshed["paper_recovery_state"] = _build_recovery_state_unless_successor_current(
        refreshed,
        handoff=handoff,
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
        handoff=handoff,
        build_paper_recovery_state=build_paper_recovery_state,
        build_current_executable_owner_action=build_current_executable_owner_action,
    )
    refreshed = _with_recovery_supervisor_decision(refreshed)
    if "provider_admission_blocked_by_supervisor_decision" not in provider_fields:
        refreshed = _without_stale_provider_supervisor_block(refreshed)
    final_current_action = _current_action_for_recovery_refresh(
        refreshed,
        handoff=handoff,
        build_current_executable_owner_action=build_current_executable_owner_action,
    )
    refreshed = refresh_current_execution_surfaces(
        payload={**refreshed, "current_executable_owner_action": final_current_action},
        status=status,
        handoff=handoff,
        runtime_health_snapshot=runtime_health_snapshot,
    )
    final_provider_fields = provider_admission_projection_fields(
        payload=refreshed,
        handoff=handoff,
        study_root=study_root,
    )
    refreshed.update(final_provider_fields)
    if "provider_admission_blocked_by_supervisor_decision" not in final_provider_fields:
        refreshed = _without_stale_provider_supervisor_block(refreshed)
    refreshed = sync_progress_first_owner_action_admission(refreshed)
    refreshed["paper_recovery_state"] = _build_recovery_state_unless_successor_current(
        refreshed,
        handoff=handoff,
        build_paper_recovery_state=build_paper_recovery_state,
        build_current_executable_owner_action=build_current_executable_owner_action,
    )
    refreshed = _with_recovery_supervisor_decision(refreshed)
    final_current_action = _current_action_for_recovery_refresh(
        refreshed,
        handoff=handoff,
        build_current_executable_owner_action=build_current_executable_owner_action,
    )
    if final_current_action != _mapping_copy(refreshed.get("current_executable_owner_action")):
        refreshed = refresh_current_execution_surfaces(
            payload={**refreshed, "current_executable_owner_action": final_current_action},
            status=status,
            handoff=handoff,
            runtime_health_snapshot=runtime_health_snapshot,
        )
        final_provider_fields = provider_admission_projection_fields(
            payload=refreshed,
            handoff=handoff,
            study_root=study_root,
        )
        refreshed.update(final_provider_fields)
        if "provider_admission_blocked_by_supervisor_decision" not in final_provider_fields:
            refreshed = _without_stale_provider_supervisor_block(refreshed)
        refreshed = sync_progress_first_owner_action_admission(refreshed)
        refreshed["paper_recovery_state"] = _build_recovery_state_unless_successor_current(
            refreshed,
            handoff=handoff,
            build_paper_recovery_state=build_paper_recovery_state,
            build_current_executable_owner_action=build_current_executable_owner_action,
        )
        refreshed = _with_recovery_supervisor_decision(refreshed)
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


def _current_action_for_recovery_refresh(
    payload: Mapping[str, Any],
    *,
    handoff: Mapping[str, Any],
    build_current_executable_owner_action: Callable[[Mapping[str, Any]], dict[str, Any] | None],
) -> dict[str, Any] | None:
    current_action = _mapping_copy(payload.get("current_executable_owner_action"))
    if (
        _handoff_current_work_unit_is_owner_receipt(handoff)
        and paper_recovery_successor_action_ready(current_action)
        and _same_handoff_receipt_identity(current_action, handoff)
    ):
        return current_action
    recovery = _mapping_copy(payload.get("paper_recovery_state"))
    decision = _mapping_copy(recovery.get("supervisor_decision"))
    if (
        _handoff_current_work_unit_is_owner_receipt(handoff)
        and _paper_recovery_successor_state_current(recovery)
        and decision.get("identity_match") is True
    ):
        recovery_action = owner_action_from_paper_recovery_state(
            payload,
            surface_kind="current_executable_owner_action",
        )
        if paper_recovery_successor_action_ready(recovery_action):
            return recovery_action
    return build_current_executable_owner_action(payload)


def _handoff_current_work_unit_is_owner_receipt(handoff: Mapping[str, Any]) -> bool:
    current = _mapping_copy(handoff.get("current_work_unit"))
    if _text(current.get("status")) != "owner_receipt_recorded":
        return False
    state = _mapping_copy(current.get("state"))
    if _text(state.get("state_kind")) != "owner_receipt_recorded":
        return False
    contract = _mapping_copy(current.get("required_output_contract"))
    return _text(state.get("owner_receipt_ref")) is not None or _text(
        contract.get("owner_receipt_ref")
    ) is not None


def _same_handoff_receipt_identity(
    action: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> bool:
    current = _mapping_copy(handoff.get("current_work_unit"))
    action_type = _text(action.get("action_type"))
    current_action_type = _text(current.get("action_type"))
    if action_type is None or current_action_type is None or action_type != current_action_type:
        return False
    work_unit = _text(action.get("work_unit_id"))
    current_work_unit = _text(current.get("work_unit_id"))
    if work_unit is None or current_work_unit is None or work_unit != current_work_unit:
        return False
    fingerprint = _text(action.get("work_unit_fingerprint")) or _text(action.get("action_fingerprint"))
    current_fingerprint = _text(current.get("work_unit_fingerprint")) or _text(
        current.get("action_fingerprint")
    )
    return (
        fingerprint is not None
        and current_fingerprint is not None
        and fingerprint == current_fingerprint
    )


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
    handoff: Mapping[str, Any],
    build_paper_recovery_state: Callable[[Mapping[str, Any]], dict[str, Any]],
    build_current_executable_owner_action: Callable[[Mapping[str, Any]], dict[str, Any] | None],
) -> dict[str, Any]:
    recovery_payload = _payload_with_handoff(payload, handoff=handoff)
    recovery = _mapping_copy(recovery_payload.get("paper_recovery_state"))
    current_action = build_current_executable_owner_action(recovery_payload)
    if _recovery_successor_supersedes_terminal_selector_residue(
        recovery_payload,
        recovery=recovery,
        current_action=current_action,
    ):
        return build_paper_recovery_state(
            _payload_with_terminal_selector_residue_blocker(recovery_payload)
        )
    if (
        _paper_recovery_successor_state_current(recovery)
        and _action_source(current_action) in {None, "paper_recovery_state.next_safe_action.successor_owner_action"}
        and not _terminal_typed_blocker_supersedes_recovery_successor(
            recovery_payload,
            recovery=recovery,
        )
    ):
        return recovery
    return build_paper_recovery_state(recovery_payload)


def _payload_with_handoff(
    payload: Mapping[str, Any],
    *,
    handoff: Mapping[str, Any],
) -> dict[str, Any]:
    if not handoff:
        return dict(payload)
    return {
        **dict(payload),
        "opl_current_control_state_handoff": dict(handoff),
    }


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


def _terminal_typed_blocker_supersedes_recovery_successor(
    payload: Mapping[str, Any],
    *,
    recovery: Mapping[str, Any],
) -> bool:
    next_safe_action = _mapping_copy(recovery.get("next_safe_action"))
    successor = _mapping_copy(next_safe_action.get("successor_owner_action"))
    if not successor:
        return False
    blocker = canonical_current_work_unit_terminal_typed_blocker(payload)
    if blocker and paper_recovery_successor_supersedes_terminal_selector_residue(
        action=_successor_as_paper_recovery_action(recovery),
        blocker=blocker,
        progress=payload,
    ):
        return False
    return without_same_identity_terminal_typed_blocker(payload, successor) is None


def _recovery_successor_supersedes_terminal_selector_residue(
    payload: Mapping[str, Any],
    *,
    recovery: Mapping[str, Any],
    current_action: Mapping[str, Any] | None,
) -> bool:
    blocker = _terminal_selector_residue_blocker(payload)
    if not blocker:
        return False
    action = _mapping_copy(current_action) or _successor_as_paper_recovery_action(recovery)
    return action_supersedes_terminal_selector_residue(
        action=action,
        blocker=blocker,
        progress=payload,
    )


def _terminal_selector_residue_blocker(payload: Mapping[str, Any]) -> dict[str, Any]:
    blocker = canonical_current_work_unit_terminal_typed_blocker(payload)
    if blocker:
        return blocker
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if _text(current_work_unit.get("status")) == "owner_receipt_recorded":
        return {}
    consumed = _mapping_copy(payload.get("provider_admission_terminal_closeout_consumed"))
    return _mapping_copy(consumed.get("typed_blocker"))


def _payload_with_terminal_selector_residue_blocker(payload: Mapping[str, Any]) -> dict[str, Any]:
    blocker = _terminal_selector_residue_blocker(payload)
    if not blocker:
        return dict(payload)
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    state = {
        "state_kind": "typed_blocker",
        "source": "terminal_closeout_typed_blocker",
        "typed_blocker": dict(blocker),
    }
    selector_work_unit = {
        **current_work_unit,
        "status": "typed_blocker",
        "owner": _text(blocker.get("owner")) or _text(current_work_unit.get("owner")),
        "action_type": _text(blocker.get("action_type")) or _text(current_work_unit.get("action_type")),
        "work_unit_id": _text(blocker.get("work_unit_id")) or _text(current_work_unit.get("work_unit_id")),
        "work_unit_fingerprint": _text(blocker.get("work_unit_fingerprint"))
        or _text(current_work_unit.get("work_unit_fingerprint")),
        "action_fingerprint": _text(blocker.get("action_fingerprint"))
        or _text(current_work_unit.get("action_fingerprint")),
        "state": state,
    }
    return {
        **dict(payload),
        "current_work_unit": {
            key: value
            for key, value in selector_work_unit.items()
            if value not in (None, "", [], {})
        },
    }


def _successor_as_paper_recovery_action(recovery: Mapping[str, Any]) -> dict[str, Any]:
    next_safe_action = _mapping_copy(recovery.get("next_safe_action"))
    successor = _mapping_copy(next_safe_action.get("successor_owner_action"))
    fingerprint = _text(successor.get("work_unit_fingerprint")) or _text(
        successor.get("action_fingerprint")
    )
    owner = (
        _text(successor.get("owner"))
        or _text(successor.get("next_owner"))
        or _text(next_safe_action.get("owner"))
    )
    return {
        key: value
        for key, value in {
            **successor,
            "source": PAPER_RECOVERY_SUCCESSOR_SOURCE,
            "source_surface": _text(successor.get("source_surface")),
            "next_owner": owner,
            "owner": owner,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "owner_receipt_required": True,
            "required_delta_kind": PAPER_RECOVERY_SUCCESSOR_DELTA_KIND,
            "paper_recovery_successor": {
                "phase": _text(recovery.get("phase")),
                "source_next_safe_action_kind": _text(next_safe_action.get("kind")),
                "source_surface": _text(successor.get("source_surface")),
            },
        }.items()
        if value not in (None, "", [], {})
    }


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
