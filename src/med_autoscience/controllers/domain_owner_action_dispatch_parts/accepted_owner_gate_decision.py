from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.runtime_control import owner_route as owner_route_part

from . import stage_native_dispatch_selection


AUTHORITY = "paper_recovery_state.accepted_owner_gate_decision"


def dispatches_only(
    *,
    progress: Mapping[str, Any],
    dispatches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [dispatch for dispatch in dispatches if dispatch_matches_progress(progress=progress, dispatch=dispatch)]


def dispatch_matches_progress(
    *,
    progress: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> bool:
    accepted = accepted_decision(progress)
    if not accepted:
        return False
    if not _dispatch_uses_accepted_owner_gate_authority(dispatch):
        return False
    action_type = _text(accepted.get("action_type"))
    if action_type is None or _text(dispatch.get("action_type")) != action_type:
        return False
    accepted_fingerprint = _text(accepted.get("work_unit_fingerprint"))
    if accepted_fingerprint is None or accepted_fingerprint not in _dispatch_fingerprint_values(dispatch):
        return False
    accepted_work_unit = _text(accepted.get("work_unit_id"))
    if accepted_work_unit is not None and accepted_work_unit not in _dispatch_work_unit_values(dispatch):
        return False
    route_back_ref = _text(accepted.get("route_back_evidence_ref"))
    if route_back_ref is not None and route_back_ref not in _dispatch_source_ref_values(dispatch):
        return False
    route = dispatch_owner_route(dispatch)
    return bool(
        route
        and owner_route_part.owner_route_matches(dispatch=dispatch, current_route=route)
        and owner_route_part.route_allows_action(action=dispatch, owner_route=route)
    )


def dispatch_matches_study_progress(
    *,
    profile: Any,
    study_id: str,
    dispatch: Mapping[str, Any],
) -> bool:
    return dispatch_matches_progress(
        progress=_mapping(stage_native_dispatch_selection.read_fresh_study_progress(profile=profile, study_id=study_id)),
        dispatch=dispatch,
    )


def accepted_decision(progress: Mapping[str, Any]) -> dict[str, Any]:
    recovery = _mapping(progress.get("paper_recovery_state"))
    if _text(recovery.get("phase")) != "owner_action_ready":
        return {}
    next_safe_action = _mapping(recovery.get("next_safe_action"))
    if _text(next_safe_action.get("kind")) != "route_back_to_owner_or_repair_materialization":
        return {}
    accepted = _mapping(next_safe_action.get("accepted_owner_gate_decision"))
    if not _text(accepted.get("action_type")) or not _text(accepted.get("work_unit_fingerprint")):
        return {}
    return accepted


def dispatch_owner_route(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    return owner_route_part.ensure_owner_route_v2(
        _mapping(dispatch.get("owner_route")) or _mapping(_mapping(dispatch.get("prompt_contract")).get("owner_route"))
    )


def dispatch_owner_route_for_progress(
    progress: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> dict[str, Any]:
    if not dispatch_matches_progress(progress=progress, dispatch=dispatch):
        return {}
    return dispatch_owner_route(dispatch)


def _dispatch_uses_accepted_owner_gate_authority(dispatch: Mapping[str, Any]) -> bool:
    source_action = _mapping(dispatch.get("source_action"))
    route = dispatch_owner_route(dispatch)
    source_refs = _mapping(route.get("source_refs"))
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    return AUTHORITY in {
        _text(source_action.get("authority")),
        _text(source_action.get("source_surface")),
        _text(source_refs.get("source_surface")),
        _text(prompt_contract.get("source_surface")),
    }


def _dispatch_fingerprint_values(dispatch: Mapping[str, Any]) -> set[str]:
    source_action = _mapping(dispatch.get("source_action"))
    route = dispatch_owner_route(dispatch)
    source_refs = _mapping(route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(route.get("currentness_contract")).get("basis")
    )
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    prompt_basis = _mapping(prompt_contract.get("owner_route_currentness_basis"))
    values = (
        dispatch.get("action_fingerprint"),
        dispatch.get("work_unit_fingerprint"),
        dispatch.get("repeat_suppression_key"),
        source_action.get("action_fingerprint"),
        source_action.get("work_unit_fingerprint"),
        route.get("work_unit_fingerprint"),
        route.get("source_fingerprint"),
        source_refs.get("work_unit_fingerprint"),
        source_refs.get("runtime_health_epoch"),
        source_refs.get("study_truth_epoch"),
        basis.get("work_unit_fingerprint"),
        basis.get("truth_epoch"),
        basis.get("runtime_health_epoch"),
        prompt_basis.get("work_unit_fingerprint"),
        prompt_basis.get("truth_epoch"),
        prompt_basis.get("runtime_health_epoch"),
    )
    return {text for value in values if (text := _text(value)) is not None}


def _dispatch_work_unit_values(dispatch: Mapping[str, Any]) -> set[str]:
    source_action = _mapping(dispatch.get("source_action"))
    route = dispatch_owner_route(dispatch)
    source_refs = _mapping(route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(route.get("currentness_contract")).get("basis")
    )
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    prompt_basis = _mapping(prompt_contract.get("owner_route_currentness_basis"))
    values = (
        source_action.get("work_unit_id"),
        source_refs.get("work_unit_id"),
        basis.get("work_unit_id"),
        prompt_basis.get("work_unit_id"),
    )
    return {text for value in values if (text := _work_unit_id(value)) is not None}


def _dispatch_source_ref_values(dispatch: Mapping[str, Any]) -> set[str]:
    source_action = _mapping(dispatch.get("source_action"))
    route = dispatch_owner_route(dispatch)
    source_refs = _mapping(route.get("source_refs"))
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    handoff_packet = _mapping(source_action.get("handoff_packet"))
    stall = _mapping(prompt_contract.get("paper_progress_stall")) or _mapping(dispatch.get("paper_progress_stall"))
    values = (
        source_action.get("source_ref"),
        handoff_packet.get("source_ref"),
        source_refs.get("source_ref"),
        prompt_contract.get("source_ref"),
        stall.get("route_back_evidence_ref"),
    )
    return {text for value in values if (text := _text(value)) is not None}


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id")) or _text(value.get("work_unit_id"))
    return _text(value)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "AUTHORITY",
    "accepted_decision",
    "dispatch_matches_progress",
    "dispatch_matches_study_progress",
    "dispatch_owner_route",
    "dispatch_owner_route_for_progress",
    "dispatches_only",
]
