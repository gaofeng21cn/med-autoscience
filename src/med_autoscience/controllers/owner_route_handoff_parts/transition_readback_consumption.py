from __future__ import annotations

from typing import Any, Mapping

from .export_study_projection import mapping, text
from med_autoscience.controllers.study_progress_parts.owner_receipt_successor import (
    paper_recovery_consumed_owner_receipt_successor,
)


def currentness_consumes_current_control_transition_request(
    currentness: Mapping[str, Any],
    *,
    action_type: str | None,
    work_unit_id: str | None,
    work_unit_fingerprint: str | None,
) -> bool:
    if paper_recovery_consumed_owner_receipt_successor(
        mapping(currentness.get("paper_recovery_state"))
    ):
        return False
    current_work_unit = mapping(currentness.get("current_work_unit"))
    current_execution_envelope = mapping(currentness.get("current_execution_envelope"))
    current_control_handoff = mapping(currentness.get("opl_current_control_state_handoff"))
    return any(
        _terminal_surface_matches_transition_request(
            terminal_surface,
            action_type=action_type,
            work_unit_id=work_unit_id,
            work_unit_fingerprint=work_unit_fingerprint,
        )
        for terminal_surface in _transition_consuming_terminal_surfaces(
            current_work_unit=current_work_unit,
            current_execution_envelope=current_execution_envelope,
            current_control_handoff=current_control_handoff,
        )
    )


def current_owner_action_supersedes_transition_request(
    current_owner_action: Mapping[str, Any],
    *,
    action_type: str | None,
    work_unit_id: str | None,
    work_unit_fingerprint: str | None,
) -> bool:
    action = mapping(current_owner_action)
    if not action:
        return False
    current_action_type = text(action.get("action_type"))
    current_work_unit_id = text(action.get("work_unit_id")) or text(action.get("next_work_unit"))
    current_fingerprint = (
        text(action.get("work_unit_fingerprint"))
        or text(action.get("action_fingerprint"))
        or text(mapping(action.get("owner_route_currentness_basis")).get("work_unit_fingerprint"))
        or text(mapping(action.get("owner_route_currentness_basis")).get("source_fingerprint"))
    )
    if current_action_type is None and current_work_unit_id is None and current_fingerprint is None:
        return False
    if current_action_type is not None and action_type is not None and current_action_type != action_type:
        return True
    if (
        current_work_unit_id is not None
        and work_unit_id is not None
        and current_work_unit_id != work_unit_id
    ):
        return True
    if (
        current_fingerprint is not None
        and work_unit_fingerprint is not None
        and current_fingerprint != work_unit_fingerprint
    ):
        return True
    return False


def _transition_consuming_terminal_surfaces(
    *,
    current_work_unit: Mapping[str, Any],
    current_execution_envelope: Mapping[str, Any],
    current_control_handoff: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    terminal_surfaces: list[Mapping[str, Any]] = []
    for surface in (
        current_work_unit,
        current_execution_envelope,
        mapping(current_control_handoff.get("current_work_unit")),
        mapping(current_control_handoff.get("current_execution_envelope")),
        mapping(current_control_handoff.get("provider_admission_terminal_closeout_consumed")),
    ):
        status = (
            text(surface.get("status"))
            or text(surface.get("state_kind"))
            or text(surface.get("execution_state_kind"))
            or text(surface.get("surface_kind"))
        )
        if status in {
            "owner_receipt_recorded",
            "typed_blocker",
            "blocked_current_work_unit",
            "provider_admission_terminal_closeout_consumed",
        } and _terminal_surface_has_consuming_ref(surface, status=status):
            terminal_surfaces.append(surface)
    return terminal_surfaces


def _terminal_surface_has_consuming_ref(surface: Mapping[str, Any], *, status: str) -> bool:
    state = mapping(surface.get("state"))
    binding = mapping(surface.get("owner_answer_binding")) or mapping(
        state.get("owner_answer_binding")
    )
    if status in {"owner_receipt_recorded", "provider_admission_terminal_closeout_consumed"}:
        return (
            text(surface.get("owner_receipt_ref"))
            or text(state.get("owner_receipt_ref"))
            or text(binding.get("owner_receipt_ref"))
        ) is not None
    return (
        text(surface.get("typed_blocker_ref"))
        or text(surface.get("blocker_ref"))
        or text(state.get("typed_blocker_ref"))
        or text(state.get("blocker_ref"))
        or text(binding.get("typed_blocker_ref"))
        or text(binding.get("blocker_ref"))
    ) is not None


def _terminal_surface_matches_transition_request(
    surface: Mapping[str, Any],
    *,
    action_type: str | None,
    work_unit_id: str | None,
    work_unit_fingerprint: str | None,
) -> bool:
    surface_action = text(surface.get("action_type"))
    surface_work_unit_id = text(surface.get("work_unit_id")) or text(surface.get("next_work_unit"))
    surface_fingerprint = (
        text(surface.get("work_unit_fingerprint"))
        or text(surface.get("action_fingerprint"))
        or text(mapping(surface.get("currentness_basis")).get("work_unit_fingerprint"))
        or text(mapping(surface.get("currentness_basis")).get("source_fingerprint"))
    )
    if surface_action is not None and action_type is not None and surface_action != action_type:
        return False
    if (
        surface_work_unit_id is not None
        and work_unit_id is not None
        and surface_work_unit_id != work_unit_id
    ):
        return False
    if (
        surface_fingerprint is not None
        and work_unit_fingerprint is not None
        and surface_fingerprint != work_unit_fingerprint
    ):
        return False
    return any(
        item is not None
        for item in (surface_action, surface_work_unit_id, surface_fingerprint)
    )


__all__ = [
    "current_owner_action_supersedes_transition_request",
    "currentness_consumes_current_control_transition_request",
]
