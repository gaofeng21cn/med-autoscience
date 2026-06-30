from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers import current_execution_envelope
from .current_execution_alignment import (
    current_action_aligned_with_execution_envelope,
    typed_blocker_reason,
)
from .current_execution_surfaces_active_projection import (
    build_active_current_execution_envelope,
    build_active_current_work_unit,
)
from .current_execution_surfaces_handoff import (
    _canonical_current_control_owner_receipt_work_unit,
    _canonical_current_control_typed_blocker,
    _canonical_current_control_typed_blocker_work_unit,
    _canonical_typed_blocker_for_execution_refresh,
    _consumed_terminal_typed_blocker_for_execution_refresh,
    _handoff_current_work_unit_is_owner_receipt,
    _handoff_has_bound_running_provider_attempt,
    _identities_conflict,
    _identity_values,
    _paper_recovery_owner_callable_action,
    _provider_admission_supersedes_request_action,
    _running_handoff_conflicts_current_surface,
)

from ..current_owner_action_projection_reconcile import (
    current_control_typed_blocker_successor_action,
    current_execution_evidence_actions,
    current_execution_envelope_actions,
    current_execution_handoff_consumes_current_action,
)
from ..current_control_executable_handoff import (
    current_control_executable_currentness_handoff,
    current_control_executable_owner_action,
)
from ..provider_admission_currentness import (
    active_provider_control,
    current_control_provider_admission_action,
    with_provider_admission_executable_currentness,
)
from ..canonical_owner_action_projection import build_canonical_owner_action_projection
from ..current_executable_owner_action_parts.non_advancing_terminal_closeout import (
    canonical_current_work_unit_terminal_typed_blocker,
)
from ..shared import _mapping_copy, _non_empty_text


def refresh_current_execution_surfaces(
    *,
    payload: dict[str, Any],
    status: Mapping[str, Any],
    handoff: Mapping[str, Any],
    runtime_health_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    updated = dict(payload)
    if _handoff_has_bound_running_provider_attempt(handoff) and not _running_handoff_conflicts_current_surface(
        payload=updated,
        handoff=handoff,
    ):
        updated["current_executable_owner_action"] = None
        updated["current_work_unit"] = build_active_current_work_unit(
            status=status,
            progress=updated,
            current_executable_owner_action=None,
            provider_admission=handoff,
            live_provider_attempt=handoff,
            typed_blocker={},
            blocked_reason=None,
            next_owner=_non_empty_text(handoff.get("next_owner")),
            runtime_health=runtime_health_snapshot,
            running_provider_attempt_bound=_handoff_has_bound_running_provider_attempt(handoff),
        )
        updated["current_execution_envelope"] = build_active_current_execution_envelope(
            progress=updated,
            actions=[],
            blocked_reason=None,
            next_owner=_non_empty_text(handoff.get("next_owner")),
            typed_blocker={},
            runtime_health=runtime_health_snapshot,
            current_work_unit_payload=_mapping_copy(updated.get("current_work_unit")),
            running_provider_attempt_bound=_handoff_has_bound_running_provider_attempt(handoff),
        )
        updated["current_execution_evidence"] = current_execution_envelope.build_current_execution_evidence(
            action_queue=[],
            runtime_health=runtime_health_snapshot,
            extra={
                "opl_current_control_state_handoff": dict(handoff) if handoff else None,
            },
        )
        return updated
    handoff_executable_action = current_control_executable_owner_action(handoff)
    provider_admission_action = (
        current_control_provider_admission_action(handoff) if active_provider_control(handoff) else None
    )
    if provider_admission_action is not None and _provider_admission_supersedes_request_action(
        provider_admission_action,
        request_action=handoff_executable_action,
    ):
        handoff_executable_action = provider_admission_action
    if handoff_executable_action is None:
        handoff_executable_action = provider_admission_action
    payload_executable_action = _payload_executable_action_for_execution_refresh(payload)
    if (
        payload_executable_action
        and handoff_executable_action
        and _identities_conflict(
            _identity_values(payload_executable_action),
            _identity_values(handoff_executable_action),
        )
        and current_control_typed_blocker_successor_action(
            payload_executable_action,
            typed_blocker=_canonical_current_control_typed_blocker(handoff),
            progress=payload,
        )
    ):
        handoff_executable_action = payload_executable_action
    if (
        payload_executable_action
        and handoff_executable_action
        and _paper_recovery_owner_callable_action(payload_executable_action)
        and not _identities_conflict(
            _identity_values(payload_executable_action),
            _identity_values(handoff_executable_action),
        )
    ):
        handoff_executable_action = payload_executable_action
    terminal_typed_blocker = _consumed_terminal_typed_blocker_for_execution_refresh(
        handoff,
        payload=updated,
    )
    if (
        terminal_typed_blocker
        and payload_executable_action
        and current_control_typed_blocker_successor_action(
            payload_executable_action,
            typed_blocker=terminal_typed_blocker,
            progress=updated,
        )
    ):
        handoff_executable_action = payload_executable_action
    if terminal_typed_blocker and not current_control_typed_blocker_successor_action(
        handoff_executable_action,
        typed_blocker=terminal_typed_blocker,
        progress=payload,
    ):
        return _with_terminal_typed_blocker_execution_surfaces(
            payload=updated,
            status=status,
            handoff=handoff,
            runtime_health_snapshot=runtime_health_snapshot,
            typed_blocker=terminal_typed_blocker,
        )
    if handoff_executable_action:
        updated["current_executable_owner_action"] = handoff_executable_action
        handoff = current_control_executable_currentness_handoff(
            handoff,
            current_control_executable_action=handoff_executable_action,
        )
        handoff = with_provider_admission_executable_currentness(
            handoff,
            current_action=handoff_executable_action,
        )
        if handoff_executable_action.get("transition_request_pending") is True:
            current_work = build_active_current_work_unit(
                status=status,
                progress=updated,
                current_executable_owner_action=handoff_executable_action,
                provider_admission=handoff,
                live_provider_attempt=handoff,
                typed_blocker=_canonical_typed_blocker_for_execution_refresh(handoff),
                blocked_reason=_non_empty_text(handoff.get("blocked_reason")),
                next_owner=_non_empty_text(handoff.get("next_owner")),
                runtime_health=runtime_health_snapshot,
                running_provider_attempt_bound=_handoff_has_bound_running_provider_attempt(handoff),
            )
            if _non_empty_text(current_work.get("status")) == "executable_owner_action":
                updated["current_work_unit"] = current_work
                updated["current_execution_envelope"] = build_active_current_execution_envelope(
                    progress=updated,
                    actions=[handoff_executable_action],
                    blocked_reason=None,
                    next_owner=_non_empty_text(handoff_executable_action.get("next_owner")),
                    typed_blocker={},
                    runtime_health=runtime_health_snapshot,
                    current_work_unit_payload=current_work,
                    running_provider_attempt_bound=_handoff_has_bound_running_provider_attempt(handoff),
                )
                updated["current_execution_evidence"] = current_execution_envelope.build_current_execution_evidence(
                    action_queue=_execution_evidence_actions_for_payload(payload=updated, handoff=handoff),
                    runtime_health=runtime_health_snapshot,
                    extra={
                        "opl_current_control_state_handoff": dict(handoff) if handoff else None,
                    },
                )
                return updated
        if handoff_executable_action.get("provider_admission_pending") is True:
            updated["current_work_unit"] = {}
            updated["current_execution_envelope"] = {}
            updated["current_execution_evidence"] = current_execution_envelope.build_current_execution_evidence(
                action_queue=_execution_evidence_actions_for_payload(payload=updated, handoff=handoff),
                runtime_health=runtime_health_snapshot,
                extra={
                    "opl_current_control_state_handoff": dict(handoff) if handoff else None,
                },
            )
            return updated
    handoff_owner_receipt_work_unit = _canonical_current_control_owner_receipt_work_unit(handoff)
    if handoff_owner_receipt_work_unit:
        updated["current_executable_owner_action"] = None
        updated["current_work_unit"] = {}
        updated["current_execution_envelope"] = {}
        updated["current_execution_evidence"] = current_execution_envelope.build_current_execution_evidence(
            action_queue=[],
            runtime_health=runtime_health_snapshot,
            extra={
                "opl_current_control_state_handoff": dict(handoff) if handoff else None,
            },
        )
        return updated
    handoff_work_unit = _canonical_current_control_typed_blocker_work_unit(handoff)
    if handoff_work_unit:
        updated["current_execution_envelope"] = {}
        successor_action = build_canonical_owner_action_projection(updated)
        if current_control_typed_blocker_successor_action(
            successor_action,
            typed_blocker=_canonical_current_control_typed_blocker(handoff),
            progress=updated,
        ):
            updated["current_executable_owner_action"] = successor_action
            actions = _canonical_actions_for_execution_refresh(payload=updated, handoff=handoff)
            evidence_actions = _execution_evidence_actions_for_payload(payload=updated, handoff=handoff)
            next_owner = _non_empty_text(_mapping_copy(successor_action).get("next_owner"))
            updated["current_work_unit"] = build_active_current_work_unit(
                status=status,
                progress=updated,
                current_executable_owner_action=successor_action,
                provider_admission=handoff,
                live_provider_attempt=handoff,
                typed_blocker={},
                blocked_reason=None,
                next_owner=next_owner,
                runtime_health=runtime_health_snapshot,
                running_provider_attempt_bound=_handoff_has_bound_running_provider_attempt(handoff),
            )
            updated["current_execution_envelope"] = build_active_current_execution_envelope(
                progress=updated,
                actions=actions,
                blocked_reason=None,
                next_owner=next_owner,
                typed_blocker={},
                runtime_health=runtime_health_snapshot,
                current_work_unit_payload=_mapping_copy(updated.get("current_work_unit")),
                running_provider_attempt_bound=_handoff_has_bound_running_provider_attempt(handoff),
            )
            updated["current_execution_evidence"] = current_execution_envelope.build_current_execution_evidence(
                action_queue=evidence_actions,
                runtime_health=runtime_health_snapshot,
                extra={
                    "opl_current_control_state_handoff": dict(handoff) if handoff else None,
                },
            )
            return updated
        else:
            updated["current_executable_owner_action"] = None
    if handoff_work_unit:
        updated["current_executable_owner_action"] = None
        updated["current_work_unit"] = handoff_work_unit
        handoff_envelope = _mapping_copy(handoff.get("current_execution_envelope"))
        if handoff_envelope:
            updated["current_execution_envelope"] = handoff_envelope
        else:
            updated["current_execution_envelope"] = build_active_current_execution_envelope(
                progress=updated,
                actions=[],
                blocked_reason=_non_empty_text(handoff_work_unit.get("blocker_type")),
                next_owner=_non_empty_text(handoff_work_unit.get("owner")),
                typed_blocker=_canonical_typed_blocker_for_execution_refresh(handoff),
                runtime_health=runtime_health_snapshot,
                current_work_unit_payload=handoff_work_unit,
                running_provider_attempt_bound=_handoff_has_bound_running_provider_attempt(handoff),
            )
        updated["current_execution_evidence"] = current_execution_envelope.build_current_execution_evidence(
            action_queue=[],
            runtime_health=runtime_health_snapshot,
            extra={
                "opl_current_control_state_handoff": dict(handoff) if handoff else None,
            },
        )
        return updated
    retained_terminal_blocker = _retained_current_terminal_typed_blocker(updated)
    if retained_terminal_blocker:
        updated["current_executable_owner_action"] = None
        updated["current_execution_envelope"] = build_active_current_execution_envelope(
            progress=updated,
            actions=[],
            blocked_reason=typed_blocker_reason(retained_terminal_blocker),
            next_owner=_non_empty_text(retained_terminal_blocker.get("owner")),
            typed_blocker=retained_terminal_blocker,
            runtime_health=runtime_health_snapshot,
            current_work_unit_payload=_mapping_copy(updated.get("current_work_unit")),
            running_provider_attempt_bound=_handoff_has_bound_running_provider_attempt(handoff),
        )
        updated["current_execution_evidence"] = current_execution_envelope.build_current_execution_evidence(
            action_queue=[],
            runtime_health=runtime_health_snapshot,
            extra={
                "opl_current_control_state_handoff": dict(handoff) if handoff else None,
            },
        )
        return updated
    actions = _canonical_actions_for_execution_refresh(payload=updated, handoff=handoff)
    evidence_actions = _execution_evidence_actions_for_payload(payload=updated, handoff=handoff)
    current_action = _current_action_for_execution_refresh(payload=updated, handoff=handoff)
    typed_blocker = _canonical_typed_blocker_for_execution_refresh(handoff)
    if current_action and (
        not typed_blocker
        or _current_action_aligned_or_successor(
            action=current_action,
            typed_blocker=typed_blocker,
            progress=updated,
        )
    ):
        typed_blocker = {}
        blocked_reason = None
    else:
        blocked_reason = _non_empty_text(typed_blocker.get("blocker_type")) or _non_empty_text(
            handoff.get("blocked_reason")
        )
    next_owner = _non_empty_text(typed_blocker.get("owner")) or _non_empty_text(handoff.get("next_owner"))
    updated["current_work_unit"] = build_active_current_work_unit(
        status=status,
        progress=updated,
        current_executable_owner_action=current_action,
        provider_admission=handoff,
        live_provider_attempt=handoff,
        typed_blocker=typed_blocker,
        blocked_reason=blocked_reason,
        next_owner=next_owner,
        runtime_health=runtime_health_snapshot,
        running_provider_attempt_bound=_handoff_has_bound_running_provider_attempt(handoff),
    )
    updated["current_execution_envelope"] = build_active_current_execution_envelope(
        progress=updated,
        actions=actions,
        blocked_reason=blocked_reason,
        next_owner=next_owner,
        typed_blocker=typed_blocker,
        runtime_health=runtime_health_snapshot,
        current_work_unit_payload=_mapping_copy(updated.get("current_work_unit")),
        running_provider_attempt_bound=_handoff_has_bound_running_provider_attempt(handoff),
    )
    aligned_action = current_action_aligned_with_execution_envelope(
        action=current_action,
        envelope=_mapping_copy(updated.get("current_execution_envelope")),
    )
    if aligned_action != _mapping_copy(updated.get("current_executable_owner_action")):
        updated["current_executable_owner_action"] = aligned_action
        actions = _canonical_actions_for_execution_refresh(payload=updated, handoff=handoff)
        current_action = _current_action_for_execution_refresh(payload=updated, handoff=handoff)
        updated["current_work_unit"] = build_active_current_work_unit(
            status=status,
            progress=updated,
            current_executable_owner_action=current_action,
            provider_admission=handoff,
            live_provider_attempt=handoff,
            typed_blocker=typed_blocker,
            blocked_reason=blocked_reason,
            next_owner=next_owner,
            runtime_health=runtime_health_snapshot,
            running_provider_attempt_bound=_handoff_has_bound_running_provider_attempt(handoff),
        )
        updated["current_execution_envelope"] = build_active_current_execution_envelope(
            progress=updated,
            actions=actions,
            blocked_reason=blocked_reason,
            next_owner=next_owner,
            typed_blocker=typed_blocker,
            runtime_health=runtime_health_snapshot,
            current_work_unit_payload=_mapping_copy(updated.get("current_work_unit")),
            running_provider_attempt_bound=_handoff_has_bound_running_provider_attempt(handoff),
        )
    updated["current_execution_evidence"] = current_execution_envelope.build_current_execution_evidence(
        action_queue=evidence_actions,
        runtime_health=runtime_health_snapshot,
        extra={
            "opl_current_control_state_handoff": dict(handoff) if handoff else None,
        },
    )
    return updated


def _retained_current_terminal_typed_blocker(payload: Mapping[str, Any]) -> dict[str, Any]:
    if _mapping_copy(payload.get("current_executable_owner_action")):
        return {}
    blocker = canonical_current_work_unit_terminal_typed_blocker(payload)
    if not blocker:
        return {}
    current = _mapping_copy(payload.get("current_work_unit"))
    state = _mapping_copy(current.get("state"))
    if _non_empty_text(state.get("source")) != "terminal_closeout_typed_blocker":
        return {}
    return blocker


def _with_terminal_typed_blocker_execution_surfaces(
    *,
    payload: dict[str, Any],
    status: Mapping[str, Any],
    handoff: Mapping[str, Any],
    runtime_health_snapshot: Mapping[str, Any],
    typed_blocker: Mapping[str, Any],
) -> dict[str, Any]:
    updated = dict(payload)
    updated["current_executable_owner_action"] = None
    progress_for_blocker = _without_owner_receipt_recovery_projection(updated)
    current_work = build_active_current_work_unit(
        status=status,
        progress=progress_for_blocker,
        current_executable_owner_action=None,
        provider_admission=handoff,
        live_provider_attempt=handoff,
        typed_blocker=typed_blocker,
        blocked_reason=typed_blocker_reason(typed_blocker),
        next_owner=_non_empty_text(typed_blocker.get("owner")) or _non_empty_text(handoff.get("next_owner")),
        runtime_health=runtime_health_snapshot,
        running_provider_attempt_bound=_handoff_has_bound_running_provider_attempt(handoff),
    )
    current_work = _with_current_work_unit_state_source(
        current_work,
        source="terminal_closeout_typed_blocker",
    )
    updated["current_work_unit"] = current_work
    updated["current_execution_envelope"] = build_active_current_execution_envelope(
        progress={**progress_for_blocker, "current_work_unit": current_work},
        actions=[],
        blocked_reason=typed_blocker_reason(typed_blocker),
        next_owner=_non_empty_text(typed_blocker.get("owner")) or _non_empty_text(handoff.get("next_owner")),
        typed_blocker=typed_blocker,
        runtime_health=runtime_health_snapshot,
        current_work_unit_payload=current_work,
        running_provider_attempt_bound=_handoff_has_bound_running_provider_attempt(handoff),
    )
    updated["current_execution_evidence"] = current_execution_envelope.build_current_execution_evidence(
        action_queue=[],
        runtime_health=runtime_health_snapshot,
        extra={
            "opl_current_control_state_handoff": dict(handoff) if handoff else None,
        },
    )
    return updated


def _with_current_work_unit_state_source(
    current_work_unit_payload: Mapping[str, Any],
    *,
    source: str,
) -> dict[str, Any]:
    updated = dict(current_work_unit_payload)
    state = _mapping_copy(updated.get("state"))
    if state:
        state["source"] = source
        updated["state"] = state
    return updated


def _without_owner_receipt_recovery_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    updated = dict(payload)
    updated["current_executable_owner_action"] = None
    for key in (
        "paper_recovery_state",
        "paper_autonomy_supervisor_decision",
        "repair_progress_projection",
        "gate_clearing_batch_followthrough",
    ):
        updated.pop(key, None)
    return updated


def _canonical_actions_for_execution_refresh(
    *,
    payload: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if _handoff_consumes_current_action_for_refresh(payload=payload, handoff=handoff):
        return []
    return _execution_actions_for_payload(payload=payload, handoff=handoff)


def _execution_actions_for_payload(
    *,
    payload: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return current_execution_envelope_actions(
        handoff=handoff,
        current_executable_owner_action=_mapping_copy(payload.get("current_executable_owner_action")),
        paper_progress_delta_counted=_mapping_copy(payload.get("progress_first_sprint_state")).get(
            "paper_progress_delta_counted"
        )
        is True,
    )


def _execution_evidence_actions_for_payload(
    *,
    payload: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return current_execution_evidence_actions(
        handoff=handoff,
        current_executable_owner_action=_mapping_copy(payload.get("current_executable_owner_action")),
        paper_progress_delta_counted=_mapping_copy(payload.get("progress_first_sprint_state")).get(
            "paper_progress_delta_counted"
        )
        is True,
    )


def _current_action_for_execution_refresh(
    *,
    payload: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> dict[str, Any]:
    if _handoff_has_bound_running_provider_attempt(handoff) and not _running_handoff_conflicts_current_surface(
        payload=payload,
        handoff=handoff,
    ):
        return {}
    if _handoff_current_work_unit_is_owner_receipt(handoff):
        return {}
    current_action = _mapping_copy(payload.get("current_executable_owner_action"))
    if not current_execution_handoff_consumes_current_action(handoff):
        return current_action
    if _current_action_aligned_or_successor(
        action=current_action,
        typed_blocker=_canonical_typed_blocker_for_execution_refresh(handoff),
        progress=payload,
    ):
        return current_action
    return {}


def _current_action_aligned_or_successor(
    *,
    action: Mapping[str, Any],
    typed_blocker: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    if current_action_aligned_with_execution_envelope(
        action=action,
        envelope={
            "state_kind": "typed_blocker",
            "typed_blocker": typed_blocker,
            "progress_payload": progress,
        },
    ):
        return True
    return current_control_typed_blocker_successor_action(
        action,
        typed_blocker=typed_blocker,
        progress=progress,
    )


def _payload_executable_action_for_execution_refresh(payload: Mapping[str, Any]) -> dict[str, Any]:
    action = _mapping_copy(payload.get("current_executable_owner_action"))
    recovery = _mapping_copy(payload.get("paper_recovery_state"))
    next_action = _mapping_copy(recovery.get("next_safe_action"))
    if _non_empty_text(next_action.get("kind")) != "run_mas_owner_callable":
        return action
    rebuilt = build_canonical_owner_action_projection(payload)
    if _paper_recovery_owner_callable_action(_mapping_copy(rebuilt)):
        return dict(rebuilt)
    return action


def _handoff_consumes_current_action_for_refresh(
    *,
    payload: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> bool:
    if _handoff_current_work_unit_is_owner_receipt(handoff):
        return True
    if not current_execution_handoff_consumes_current_action(handoff):
        return False
    current_action = _mapping_copy(payload.get("current_executable_owner_action"))
    if not current_action:
        return True
    return not _current_action_aligned_or_successor(
        action=current_action,
        typed_blocker=_canonical_typed_blocker_for_execution_refresh(handoff),
        progress=payload,
    )


__all__ = [
    "current_action_aligned_with_execution_envelope",
    "refresh_current_execution_surfaces",
    "typed_blocker_reason",
]
