from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers import current_execution_envelope, current_work_unit
from med_autoscience.controllers.current_work_unit_parts.policy_constants import (
    CURRENT_ACTION_SUPERSEDED_RUNTIME_BLOCKERS,
)
from med_autoscience.controllers.current_work_unit_parts.terminal_closeout_currentness import (
    OPL_RUNTIME_TERMINAL_BLOCKERS,
)
from med_autoscience.runtime_control.owner_route_attempt_protocol import (
    currentness_basis as owner_route_currentness_basis,
    owner_reason_contract,
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
from ..current_executable_owner_action import build_current_executable_owner_action
from ..current_executable_owner_action_parts.non_advancing_terminal_closeout import (
    canonical_current_work_unit_terminal_typed_blocker,
)
from ..current_executable_owner_action_parts.paper_recovery import (
    paper_recovery_successor_action_ready,
)
from ..owner_receipt_successor import (
    paper_recovery_consumed_owner_receipt_successor,
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
        updated["current_work_unit"] = current_work_unit.build_current_work_unit(
            status=status,
            progress=updated,
            actions=[],
            current_executable_owner_action=None,
            provider_admission=handoff,
            live_provider_attempt=handoff,
            typed_blocker={},
            blocked_reason=None,
            next_owner=_non_empty_text(handoff.get("next_owner")),
            runtime_health=runtime_health_snapshot,
        )
        updated["current_execution_envelope"] = current_execution_envelope.build_current_execution_envelope(
            status=status,
            progress=updated,
            actions=[],
            blocked_reason=None,
            next_owner=_non_empty_text(handoff.get("next_owner")),
            typed_blocker={},
            runtime_health=runtime_health_snapshot,
            live_provider_attempt=handoff,
            current_work_unit_payload=_mapping_copy(updated.get("current_work_unit")),
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
    if handoff_executable_action:
        updated["current_executable_owner_action"] = handoff_executable_action
        handoff = current_control_executable_currentness_handoff(
            handoff,
            current_control_executable_action=handoff_executable_action,
        )
    terminal_typed_blocker = _consumed_terminal_typed_blocker_for_execution_refresh(handoff)
    if terminal_typed_blocker:
        return _with_terminal_typed_blocker_execution_surfaces(
            payload=updated,
            status=status,
            handoff=handoff,
            runtime_health_snapshot=runtime_health_snapshot,
            typed_blocker=terminal_typed_blocker,
        )
    handoff_owner_receipt_work_unit = _canonical_current_control_owner_receipt_work_unit(handoff)
    if handoff_owner_receipt_work_unit:
        successor_action = _paper_recovery_successor_action_for_owner_receipt_handoff(
            payload=updated,
            handoff=handoff,
        )
        if successor_action:
            updated["current_executable_owner_action"] = successor_action
            updated["current_work_unit"] = current_work_unit.build_current_work_unit(
                status=status,
                progress=updated,
                actions=[successor_action],
                current_executable_owner_action=successor_action,
                provider_admission=handoff,
                live_provider_attempt=handoff,
                typed_blocker={},
                blocked_reason=None,
                next_owner=_non_empty_text(successor_action.get("next_owner")),
                runtime_health=runtime_health_snapshot,
            )
            updated["current_execution_envelope"] = current_execution_envelope.build_current_execution_envelope(
                status=status,
                progress=updated,
                actions=[successor_action],
                blocked_reason=None,
                next_owner=_non_empty_text(successor_action.get("next_owner")),
                typed_blocker={},
                runtime_health=runtime_health_snapshot,
                live_provider_attempt=handoff,
                current_work_unit_payload=_mapping_copy(updated.get("current_work_unit")),
            )
            updated["current_execution_evidence"] = current_execution_envelope.build_current_execution_evidence(
                action_queue=_execution_evidence_actions_for_payload(payload=updated, handoff=handoff),
                runtime_health=runtime_health_snapshot,
                extra={
                    "opl_current_control_state_handoff": dict(handoff) if handoff else None,
                },
            )
            return updated
        else:
            updated["current_executable_owner_action"] = None
            updated["current_work_unit"] = handoff_owner_receipt_work_unit
            handoff_envelope = _mapping_copy(handoff.get("current_execution_envelope"))
            if _non_empty_text(handoff_envelope.get("state_kind")) == "owner_receipt_recorded":
                updated["current_execution_envelope"] = handoff_envelope
            else:
                updated["current_execution_envelope"] = current_execution_envelope.build_current_execution_envelope(
                    status=status,
                    progress=updated,
                    actions=[],
                    blocked_reason=None,
                    next_owner=_non_empty_text(handoff_owner_receipt_work_unit.get("owner")),
                    typed_blocker={},
                    runtime_health=runtime_health_snapshot,
                    live_provider_attempt=handoff,
                    current_work_unit_payload=handoff_owner_receipt_work_unit,
                )
            updated["current_execution_evidence"] = current_execution_envelope.build_current_execution_evidence(
                action_queue=[],
                runtime_health=runtime_health_snapshot,
                extra={
                    "opl_current_control_state_handoff": dict(handoff) if handoff else None,
                },
            )
            return updated
    paper_recovery_successor_action = _paper_recovery_successor_action(payload)
    if paper_recovery_successor_action:
        return _with_paper_recovery_successor_execution_surfaces(
            payload=updated,
            status=status,
            handoff=handoff,
            runtime_health_snapshot=runtime_health_snapshot,
            current_action=paper_recovery_successor_action,
        )
    handoff_work_unit = _canonical_current_control_typed_blocker_work_unit(handoff)
    if handoff_work_unit:
        updated["current_work_unit"] = handoff_work_unit
        handoff_envelope = _mapping_copy(handoff.get("current_execution_envelope"))
        if handoff_envelope:
            updated["current_execution_envelope"] = handoff_envelope
        successor_action = build_current_executable_owner_action(updated)
        if current_control_typed_blocker_successor_action(
            successor_action,
            typed_blocker=_canonical_current_control_typed_blocker(handoff),
            progress=updated,
        ):
            updated["current_executable_owner_action"] = successor_action
            handoff_work_unit = {}
        else:
            updated["current_executable_owner_action"] = None
    if handoff_work_unit:
        updated["current_executable_owner_action"] = None
        handoff_envelope = _mapping_copy(handoff.get("current_execution_envelope"))
        if handoff_envelope:
            updated["current_execution_envelope"] = handoff_envelope
        else:
            updated["current_execution_envelope"] = current_execution_envelope.build_current_execution_envelope(
                status=status,
                progress=updated,
                actions=[],
                blocked_reason=_non_empty_text(handoff_work_unit.get("blocker_type")),
                next_owner=_non_empty_text(handoff_work_unit.get("owner")),
                typed_blocker=_canonical_typed_blocker_for_execution_refresh(handoff),
                runtime_health=runtime_health_snapshot,
                live_provider_attempt=handoff,
                current_work_unit_payload=handoff_work_unit,
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
        updated["current_execution_envelope"] = current_execution_envelope.build_current_execution_envelope(
            status=status,
            progress=updated,
            actions=[],
            blocked_reason=typed_blocker_reason(retained_terminal_blocker),
            next_owner=_non_empty_text(retained_terminal_blocker.get("owner")),
            typed_blocker=retained_terminal_blocker,
            runtime_health=runtime_health_snapshot,
            live_provider_attempt=handoff,
            current_work_unit_payload=_mapping_copy(updated.get("current_work_unit")),
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
    if current_action and current_work_unit.action_supersedes_typed_blocker(
        action=current_action,
        blocker=typed_blocker,
        progress=updated,
    ):
        typed_blocker = {}
        blocked_reason = None
    else:
        blocked_reason = _non_empty_text(typed_blocker.get("blocker_type")) or _non_empty_text(
            handoff.get("blocked_reason")
        )
    next_owner = _non_empty_text(typed_blocker.get("owner")) or _non_empty_text(handoff.get("next_owner"))
    updated["current_work_unit"] = current_work_unit.build_current_work_unit(
        status=status,
        progress=updated,
        actions=actions,
        current_executable_owner_action=current_action,
        provider_admission=handoff,
        live_provider_attempt=handoff,
        typed_blocker=typed_blocker,
        blocked_reason=blocked_reason,
        next_owner=next_owner,
        runtime_health=runtime_health_snapshot,
    )
    updated["current_execution_envelope"] = current_execution_envelope.build_current_execution_envelope(
        status=status,
        progress=updated,
        actions=actions,
        blocked_reason=blocked_reason,
        next_owner=next_owner,
        typed_blocker=typed_blocker,
        runtime_health=runtime_health_snapshot,
        live_provider_attempt=handoff,
        current_work_unit_payload=_mapping_copy(updated.get("current_work_unit")),
    )
    aligned_action = current_action_aligned_with_execution_envelope(
        action=current_action,
        envelope=_mapping_copy(updated.get("current_execution_envelope")),
    )
    if aligned_action is None:
        aligned_action = _current_action_from_current_work_unit(
            updated.get("current_work_unit"),
            progress=updated,
        )
    if aligned_action != _mapping_copy(updated.get("current_executable_owner_action")):
        updated["current_executable_owner_action"] = aligned_action
        actions = _canonical_actions_for_execution_refresh(payload=updated, handoff=handoff)
        current_action = _current_action_for_execution_refresh(payload=updated, handoff=handoff)
        updated["current_work_unit"] = current_work_unit.build_current_work_unit(
            status=status,
            progress=updated,
            actions=actions,
            current_executable_owner_action=current_action,
            provider_admission=handoff,
            live_provider_attempt=handoff,
            typed_blocker=typed_blocker,
            blocked_reason=blocked_reason,
            next_owner=next_owner,
            runtime_health=runtime_health_snapshot,
        )
        updated["current_execution_envelope"] = current_execution_envelope.build_current_execution_envelope(
            status=status,
            progress=updated,
            actions=actions,
            blocked_reason=blocked_reason,
            next_owner=next_owner,
            typed_blocker=typed_blocker,
            runtime_health=runtime_health_snapshot,
            live_provider_attempt=handoff,
            current_work_unit_payload=_mapping_copy(updated.get("current_work_unit")),
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


def _paper_recovery_successor_action(payload: Mapping[str, Any]) -> dict[str, Any]:
    current_action = _mapping_copy(payload.get("current_executable_owner_action"))
    if paper_recovery_successor_action_ready(current_action):
        return current_action
    successor_action = build_current_executable_owner_action(payload)
    if paper_recovery_successor_action_ready(successor_action):
        return dict(successor_action)
    return {}


def _with_paper_recovery_successor_execution_surfaces(
    *,
    payload: dict[str, Any],
    status: Mapping[str, Any],
    handoff: Mapping[str, Any],
    runtime_health_snapshot: Mapping[str, Any],
    current_action: Mapping[str, Any],
) -> dict[str, Any]:
    current_work = current_work_unit.build_current_work_unit(
        status=status,
        progress={**payload, "current_executable_owner_action": current_action},
        actions=[dict(current_action)],
        current_executable_owner_action=current_action,
        provider_admission=handoff,
        live_provider_attempt=handoff,
        typed_blocker={},
        blocked_reason=None,
        next_owner=_non_empty_text(current_action.get("next_owner")),
        runtime_health=runtime_health_snapshot,
    )
    if _non_empty_text(current_work.get("status")) != "executable_owner_action":
        return payload
    if _non_empty_text(current_work.get("work_unit_id")) != _non_empty_text(current_action.get("work_unit_id")):
        return payload
    if _non_empty_text(current_work.get("work_unit_fingerprint")) != _non_empty_text(
        current_action.get("work_unit_fingerprint")
    ):
        return payload
    updated = dict(payload)
    updated["current_executable_owner_action"] = dict(current_action)
    updated["current_work_unit"] = current_work
    updated["current_execution_envelope"] = current_execution_envelope.build_current_execution_envelope(
        status=status,
        progress=updated,
        actions=[dict(current_action)],
        blocked_reason=None,
        next_owner=_non_empty_text(current_action.get("next_owner")),
        typed_blocker={},
        runtime_health=runtime_health_snapshot,
        live_provider_attempt=handoff,
        current_work_unit_payload=current_work,
    )
    updated["current_execution_evidence"] = current_execution_envelope.build_current_execution_evidence(
        action_queue=_execution_evidence_actions_for_payload(payload=updated, handoff=handoff),
        runtime_health=runtime_health_snapshot,
        extra={
            "opl_current_control_state_handoff": dict(handoff) if handoff else None,
        },
    )
    return updated


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
    current_work = current_work_unit.build_current_work_unit(
        status=status,
        progress=progress_for_blocker,
        actions=[],
        current_executable_owner_action=None,
        provider_admission=handoff,
        live_provider_attempt=handoff,
        typed_blocker=typed_blocker,
        blocked_reason=typed_blocker_reason(typed_blocker),
        next_owner=_non_empty_text(typed_blocker.get("owner")) or _non_empty_text(handoff.get("next_owner")),
        runtime_health=runtime_health_snapshot,
    )
    current_work = _with_current_work_unit_state_source(
        current_work,
        source="terminal_closeout_typed_blocker",
    )
    updated["current_work_unit"] = current_work
    updated["current_execution_envelope"] = current_execution_envelope.build_current_execution_envelope(
        status=status,
        progress={**progress_for_blocker, "current_work_unit": current_work},
        actions=[],
        blocked_reason=typed_blocker_reason(typed_blocker),
        next_owner=_non_empty_text(typed_blocker.get("owner")) or _non_empty_text(handoff.get("next_owner")),
        typed_blocker=typed_blocker,
        runtime_health=runtime_health_snapshot,
        live_provider_attempt=handoff,
        current_work_unit_payload=current_work,
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


def _canonical_current_control_typed_blocker_work_unit(handoff: Mapping[str, Any]) -> dict[str, Any]:
    if handoff.get("running_provider_attempt") is True:
        return {}
    if _handoff_current_work_unit_is_owner_receipt(handoff):
        return {}
    current = _mapping_copy(handoff.get("current_work_unit"))
    if _non_empty_text(current.get("status")) in {"typed_blocker", "blocked_current_work_unit"}:
        return current
    return {}


def _canonical_current_control_owner_receipt_work_unit(handoff: Mapping[str, Any]) -> dict[str, Any]:
    if handoff.get("running_provider_attempt") is True:
        return {}
    if not _handoff_current_work_unit_is_owner_receipt(handoff):
        return {}
    return _mapping_copy(handoff.get("current_work_unit"))


def _current_action_from_current_work_unit(
    value: object,
    *,
    progress: Mapping[str, Any],
) -> dict[str, Any] | None:
    current = _mapping_copy(value)
    if _non_empty_text(current.get("status")) != "executable_owner_action":
        return None
    action_type = _non_empty_text(current.get("action_type"))
    work_unit_id = _non_empty_text(current.get("work_unit_id"))
    owner = _non_empty_text(current.get("owner"))
    fingerprint = _non_empty_text(current.get("work_unit_fingerprint"))
    if action_type is None or work_unit_id is None or owner is None or fingerprint is None:
        return None
    contract = _mapping_copy(current.get("required_output_contract"))
    state = _mapping_copy(current.get("state"))
    currentness_basis = _mapping_copy(current.get("currentness_basis"))
    source = _non_empty_text(state.get("source")) or "canonical_current_work_unit"
    repair_precedence = _repair_progress_precedence_for_current_work_unit(
        current=current,
        progress=progress,
        source=source,
    )
    return {
        key: value
        for key, value in {
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": source,
            "next_owner": owner,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": _non_empty_text(current.get("action_fingerprint")) or fingerprint,
            "source_eval_id": _non_empty_text(currentness_basis.get("source_eval_id")),
            "action_type": action_type,
            "allowed_actions": [action_type],
            "owner_receipt_required": _mapping_copy(current.get("required_output_contract")).get(
                "owner_receipt_required"
            )
            is not False,
            "required_delta_kind": _non_empty_text(contract.get("required_delta_kind")),
            "target_surface": _mapping_copy(contract.get("target_surface")) or None,
            "target_surface_specificity": _non_empty_text(contract.get("target_surface_specificity")),
            "source_ref": _first_text(_text_list(current.get("input_refs"))),
            "acceptance_refs": _text_list(current.get("acceptance_refs")),
            "owner_route_currentness_basis": currentness_basis or None,
            "repair_progress_precedence": repair_precedence or None,
            "authority_boundary": {
                "refs_only": True,
                "source_current_work_unit": True,
                "can_write_runtime_owned_surfaces": False,
                "can_write_paper_or_package": False,
                "can_authorize_quality_verdict": False,
                "can_authorize_publication_ready": False,
            },
        }.items()
        if value not in (None, "", [], {})
    }


def _repair_progress_precedence_for_current_work_unit(
    *,
    current: Mapping[str, Any],
    progress: Mapping[str, Any],
    source: str,
) -> dict[str, Any]:
    if source != "repair_progress_projection.mas_owner_repair_execution_evidence":
        return {}
    repair = _mapping_copy(progress.get("repair_progress_projection"))
    if repair.get("paper_delta_observed") is not True or repair.get("accepted_owner_receipt") is not True:
        return {}
    source_work_unit = _non_empty_text(repair.get("work_unit_id"))
    work_unit_fingerprint = (
        _non_empty_text(repair.get("work_unit_fingerprint"))
        or _non_empty_text(repair.get("action_fingerprint"))
        or _non_empty_text(repair.get("source_fingerprint"))
    )
    if source_work_unit is None or work_unit_fingerprint is None:
        return {}
    return {
        "paper_delta_observed": True,
        "accepted_owner_receipt": True,
        "superseded_stage_native_action": "run_quality_repair_batch",
        "source_work_unit_id": source_work_unit,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": work_unit_fingerprint,
        "source_fingerprint": _non_empty_text(repair.get("source_fingerprint")),
    }


def _canonical_current_control_typed_blocker(handoff: Mapping[str, Any]) -> dict[str, Any]:
    typed_blocker = _mapping_copy(handoff.get("typed_blocker"))
    if typed_blocker:
        return typed_blocker
    current = _mapping_copy(handoff.get("current_work_unit"))
    state = _mapping_copy(current.get("state"))
    current_blocker = _mapping_copy(state.get("typed_blocker"))
    if current_blocker:
        return current_blocker
    envelope = _mapping_copy(handoff.get("current_execution_envelope"))
    envelope_blocker = _mapping_copy(envelope.get("typed_blocker"))
    if envelope_blocker:
        return envelope_blocker
    return {}


def _canonical_actions_for_execution_refresh(
    *,
    payload: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if _handoff_consumes_current_action_for_refresh(payload=payload, handoff=handoff):
        return []
    return _execution_actions_for_payload(payload=payload, handoff=handoff)


def _canonical_typed_blocker_for_execution_refresh(handoff: Mapping[str, Any]) -> dict[str, Any]:
    if _handoff_current_work_unit_is_owner_receipt(handoff):
        return _consumed_terminal_typed_blocker_for_execution_refresh(handoff)
    return _canonical_typed_blocker_from_handoff(handoff)


def _canonical_typed_blocker_from_handoff(handoff: Mapping[str, Any]) -> dict[str, Any]:
    typed_blocker = _mapping_copy(handoff.get("typed_blocker"))
    if typed_blocker:
        return typed_blocker
    if not current_execution_handoff_consumes_current_action(handoff):
        return {}
    handoff_blocker = _typed_blocker_from_current_control_blocked_reason(handoff)
    if handoff_blocker:
        return handoff_blocker
    latest_closeout = _mapping_copy(handoff.get("latest_typed_default_executor_closeout"))
    embedded = _mapping_copy(latest_closeout.get("typed_blocker"))
    blocked_reason = (
        _non_empty_text(embedded.get("blocker_type"))
        or _non_empty_text(embedded.get("blocked_reason"))
        or _non_empty_text(embedded.get("reason"))
        or _non_empty_text(embedded.get("blocker_id"))
        or _non_empty_text(latest_closeout.get("blocked_reason"))
    )
    if blocked_reason is None:
        return {}
    owner = (
        "one-person-lab"
        if blocked_reason in OPL_RUNTIME_TERMINAL_BLOCKERS
        else _non_empty_text(embedded.get("owner"))
        or _non_empty_text(embedded.get("next_owner"))
        or _non_empty_text(handoff.get("next_owner"))
        or "med-autoscience"
    )
    return {
        key: value
        for key, value in {
            **embedded,
            "blocker_type": blocked_reason,
            "blocked_reason": blocked_reason,
            "owner": owner,
            "action_type": _non_empty_text(latest_closeout.get("action_type")),
            "work_unit_id": _non_empty_text(latest_closeout.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(latest_closeout.get("work_unit_fingerprint")),
            "action_fingerprint": _non_empty_text(latest_closeout.get("action_fingerprint")),
            "source_fingerprint": _non_empty_text(latest_closeout.get("source_fingerprint")),
            "idempotency_key": _non_empty_text(latest_closeout.get("idempotency_key")),
            "stage_attempt_id": _non_empty_text(latest_closeout.get("stage_attempt_id")),
            "source_ref": _non_empty_text(latest_closeout.get("receipt_ref"))
            or _non_empty_text(latest_closeout.get("source_path")),
            "typed_blocker_ref": _non_empty_text(latest_closeout.get("receipt_ref"))
            or _non_empty_text(latest_closeout.get("source_path")),
        }.items()
        if value not in (None, "", [], {})
    }


def _consumed_terminal_typed_blocker_for_execution_refresh(handoff: Mapping[str, Any]) -> dict[str, Any]:
    if handoff.get("running_provider_attempt") is True:
        return {}
    if not _handoff_current_work_unit_is_owner_receipt(handoff):
        return {}
    consumed = _mapping_copy(handoff.get("provider_admission_terminal_closeout_consumed"))
    if _non_empty_text(consumed.get("typed_blocker_ref")) is None and not _mapping_copy(
        consumed.get("typed_blocker")
    ):
        return {}
    typed_blocker = _canonical_typed_blocker_from_handoff(handoff)
    if not typed_blocker:
        return {}
    current = _mapping_copy(handoff.get("current_work_unit"))
    if not _identity_overlaps_without_conflict(current, typed_blocker):
        return {}
    if not _identity_overlaps_without_conflict(consumed, typed_blocker):
        return {}
    return typed_blocker


def _identity_overlaps_without_conflict(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    left_identity = _identity_values(left)
    right_identity = _identity_values(right)
    if _identities_conflict(left_identity, right_identity):
        return False
    return any(
        left_identity.get(key) is not None and right_identity.get(key) is not None
        for key in ("action_type", "work_unit_id", "fingerprint")
    )


def _typed_blocker_from_current_control_blocked_reason(handoff: Mapping[str, Any]) -> dict[str, Any]:
    blocked_reason = _non_empty_text(handoff.get("blocked_reason"))
    if blocked_reason is None:
        return {}
    contract = owner_reason_contract(
        reason=blocked_reason,
        owner=_non_empty_text(handoff.get("next_owner")),
    )
    if contract.get("registered") is not True:
        return {}
    if _non_empty_text(contract.get("owner")) != "one-person-lab":
        return {}
    if any(_non_empty_text(action) is not None for action in contract.get("allowed_actions") or []):
        return {}
    owner_route = _mapping_copy(handoff.get("owner_route"))
    source_refs = _mapping_copy(owner_route.get("source_refs"))
    basis = owner_route_currentness_basis(owner_route) if owner_route else {}
    owner = _non_empty_text(handoff.get("next_owner")) or _non_empty_text(contract.get("owner")) or "one-person-lab"
    return {
        key: value
        for key, value in {
            "blocker_type": blocked_reason,
            "blocker_id": blocked_reason,
            "blocked_reason": blocked_reason,
            "owner": owner,
            "work_unit_id": _non_empty_text(source_refs.get("work_unit_id"))
            or _non_empty_text(owner_route.get("work_unit_id"))
            or _non_empty_text(basis.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(owner_route.get("work_unit_fingerprint"))
            or _non_empty_text(source_refs.get("work_unit_fingerprint"))
            or _non_empty_text(basis.get("work_unit_fingerprint"))
            or _non_empty_text(handoff.get("source_fingerprint")),
            "action_fingerprint": _non_empty_text(owner_route.get("action_fingerprint"))
            or _non_empty_text(source_refs.get("action_fingerprint"))
            or _non_empty_text(owner_route.get("work_unit_fingerprint"))
            or _non_empty_text(source_refs.get("work_unit_fingerprint"))
            or _non_empty_text(basis.get("work_unit_fingerprint"))
            or _non_empty_text(handoff.get("source_fingerprint")),
            "source_fingerprint": _non_empty_text(owner_route.get("source_fingerprint"))
            or _non_empty_text(source_refs.get("source_fingerprint"))
            or _non_empty_text(handoff.get("source_fingerprint")),
            "source_eval_id": _non_empty_text(source_refs.get("source_eval_id"))
            or _non_empty_text(basis.get("source_eval_id")),
            "source_ref": _non_empty_text(handoff.get("source_ref")) or _non_empty_text(handoff.get("source_path")),
            "required_output": _non_empty_text(contract.get("required_output")),
        }.items()
        if value not in (None, "", [], {})
    }


def _handoff_current_work_unit_is_owner_receipt(handoff: Mapping[str, Any]) -> bool:
    current = _mapping_copy(handoff.get("current_work_unit"))
    if _non_empty_text(current.get("status")) != "owner_receipt_recorded":
        return False
    state = _mapping_copy(current.get("state"))
    if _non_empty_text(state.get("state_kind")) != "owner_receipt_recorded":
        return False
    receipt_ref = _non_empty_text(state.get("owner_receipt_ref")) or _non_empty_text(
        _mapping_copy(current.get("required_output_contract")).get("owner_receipt_ref")
    )
    if receipt_ref is None:
        return False
    envelope = _mapping_copy(handoff.get("current_execution_envelope"))
    envelope_kind = _non_empty_text(envelope.get("state_kind"))
    if envelope_kind not in {None, "owner_receipt_recorded"}:
        return False
    return True


def current_action_aligned_with_execution_envelope(
    *,
    action: Mapping[str, Any],
    envelope: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not action:
        return None
    if _non_empty_text(action.get("surface_kind")) != "current_executable_owner_action":
        return None
    state_kind = _non_empty_text(envelope.get("state_kind"))
    if state_kind == "typed_blocker":
        typed_blocker = _mapping_copy(envelope.get("typed_blocker"))
        blocker_reason = typed_blocker_reason(typed_blocker) or _envelope_typed_blocker_reason(envelope)
        if (
            blocker_reason not in CURRENT_ACTION_SUPERSEDED_RUNTIME_BLOCKERS
            and not current_work_unit.action_supersedes_typed_blocker(
                action=action,
                blocker=typed_blocker,
                progress=envelope.get("progress_payload"),
            )
        ):
            return None
        return dict(action)
    action_source = _non_empty_text(action.get("source_surface")) or _non_empty_text(action.get("source"))
    if (
        state_kind == "typed_blocker"
        and action_source == "study_progress.next_forced_delta.owner_action"
        and _envelope_typed_blocker_reason(envelope) == "gate_clearing_batch_source_eval_currentness_mismatch"
    ):
        return dict(action)
    if (
        state_kind == "typed_blocker"
        and action_source == "study_progress.next_forced_delta.owner_action"
        and action.get("terminal_stage_next_forced_delta") is True
    ):
        return dict(action)
    if state_kind == "typed_blocker" and action_source == "stage_native_workspace_next_action":
        return dict(action)
    if state_kind != "executable_owner_action":
        return None
    envelope_work_unit = _work_unit_identity(envelope.get("next_work_unit"))
    envelope_action = _non_empty_text(envelope.get("action_type"))
    action_type = _non_empty_text(action.get("action_type"))
    action_work_units = {
        item
        for item in (
            _non_empty_text(action.get("work_unit_id")),
            _non_empty_text(action.get("action_type")),
            *_text_list(action.get("allowed_actions")),
        )
        if item is not None
    }
    if envelope_work_unit is not None and action_work_units and envelope_work_unit not in action_work_units:
        return None
    if envelope_action is not None and action_type is not None and envelope_action != action_type:
        return None
    envelope_fingerprint = _fingerprint_identity(envelope)
    action_fingerprint = _fingerprint_identity(action)
    if envelope_fingerprint is not None and action_fingerprint is not None:
        if envelope_fingerprint != action_fingerprint:
            return None
    return dict(action)


def typed_blocker_reason(typed_blocker: Mapping[str, Any]) -> str | None:
    for key in ("blocked_reason", "blocker_type", "blocker_kind", "reason", "blocker_id"):
        if text := _non_empty_text(typed_blocker.get(key)):
            return text
    anti_loop_budget = _mapping_copy(typed_blocker.get("anti_loop_budget"))
    if _non_empty_text(anti_loop_budget.get("status")) == "exhausted":
        return "anti_loop_budget_exhausted"
    return None


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
        successor_action = _paper_recovery_successor_action_for_owner_receipt_handoff(
            payload=payload,
            handoff=handoff,
        )
        if successor_action:
            return successor_action
        return {}
    current_action = _mapping_copy(payload.get("current_executable_owner_action"))
    if not current_execution_handoff_consumes_current_action(handoff):
        return current_action
    if current_action_aligned_with_execution_envelope(
        action=current_action,
        envelope={
            "state_kind": "typed_blocker",
            "typed_blocker": _canonical_typed_blocker_for_execution_refresh(handoff),
            "progress_payload": payload,
        },
    ):
        return current_action
    return {}


def _handoff_has_bound_running_provider_attempt(handoff: Mapping[str, Any]) -> bool:
    if handoff.get("running_provider_attempt") is not True:
        return False
    if _non_empty_text(handoff.get("active_stage_attempt_id")) is None and _non_empty_text(
        handoff.get("active_run_id")
    ) is None and _non_empty_text(handoff.get("active_workflow_id")) is None:
        return False
    runtime_health = _mapping_copy(handoff.get("runtime_health"))
    runtime_liveness_status = _non_empty_text(runtime_health.get("runtime_liveness_status"))
    health_status = _non_empty_text(runtime_health.get("health_status"))
    if runtime_liveness_status not in {
        "attempt_running",
        "provider_admitted",
        "running",
        "live",
    } and health_status not in {
        "attempt_running",
        "provider_admitted",
        "running",
        "live",
    }:
        return False
    return any(
        _non_empty_text(value) is not None
        for value in (
            handoff.get("action_type"),
            handoff.get("work_unit_id"),
            handoff.get("work_unit_fingerprint"),
            handoff.get("action_fingerprint"),
            runtime_health.get("action_type"),
            runtime_health.get("work_unit_id"),
            runtime_health.get("work_unit_fingerprint"),
            runtime_health.get("action_fingerprint"),
        )
    )


def _running_handoff_conflicts_current_surface(
    *,
    payload: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> bool:
    if not _handoff_has_bound_running_provider_attempt(handoff):
        return False
    handoff_identity = _identity_values(handoff)
    for surface in (
        _mapping_copy(payload.get("current_work_unit")),
        _mapping_copy(payload.get("current_execution_envelope")),
        _mapping_copy(payload.get("current_executable_owner_action")),
    ):
        if not surface:
            continue
        if _non_empty_text(surface.get("status")) not in {
            "executable_owner_action",
            "running_provider_attempt",
            "typed_blocker",
            "blocked_current_work_unit",
        } and _non_empty_text(surface.get("state_kind")) not in {
            "executable_owner_action",
            "running_provider_attempt",
            "typed_blocker",
            "blocked_current_work_unit",
        } and _non_empty_text(surface.get("surface_kind")) != "current_executable_owner_action":
            continue
        surface_identity = _identity_values(surface)
        if _identities_conflict(handoff_identity, surface_identity):
            return True
    return False


def _identity_values(value: Mapping[str, Any]) -> dict[str, str | None]:
    basis = _mapping_copy(value.get("owner_route_currentness_basis")) or _mapping_copy(
        value.get("currentness_basis")
    )
    state = _mapping_copy(value.get("state"))
    runtime_health = _mapping_copy(value.get("runtime_health"))
    return {
        "action_type": _non_empty_text(value.get("action_type"))
        or _non_empty_text(runtime_health.get("action_type")),
        "work_unit_id": _non_empty_text(value.get("work_unit_id"))
        or _non_empty_text(value.get("next_work_unit"))
        or _non_empty_text(runtime_health.get("work_unit_id"))
        or _non_empty_text(runtime_health.get("next_work_unit"))
        or _non_empty_text(state.get("next_work_unit"))
        or _non_empty_text(basis.get("work_unit_id")),
        "fingerprint": _non_empty_text(value.get("work_unit_fingerprint"))
        or _non_empty_text(value.get("action_fingerprint"))
        or _non_empty_text(runtime_health.get("work_unit_fingerprint"))
        or _non_empty_text(runtime_health.get("action_fingerprint"))
        or _non_empty_text(basis.get("work_unit_fingerprint")),
    }


def _identities_conflict(left: Mapping[str, str | None], right: Mapping[str, str | None]) -> bool:
    return any(
        left.get(key) is not None and right.get(key) is not None and left.get(key) != right.get(key)
        for key in ("action_type", "work_unit_id", "fingerprint")
    )


def _handoff_consumes_current_action_for_refresh(
    *,
    payload: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> bool:
    if _handoff_current_work_unit_is_owner_receipt(handoff):
        if _paper_recovery_successor_action_for_owner_receipt_handoff(
            payload=payload,
            handoff=handoff,
        ):
            return False
        return True
    if not current_execution_handoff_consumes_current_action(handoff):
        return False
    current_action = _mapping_copy(payload.get("current_executable_owner_action"))
    if not current_action:
        return True
    return not current_action_aligned_with_execution_envelope(
        action=current_action,
        envelope={
            "state_kind": "typed_blocker",
            "typed_blocker": _canonical_typed_blocker_for_execution_refresh(handoff),
            "progress_payload": payload,
        },
    )


def _paper_recovery_successor_action_for_owner_receipt_handoff(
    *,
    payload: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> dict[str, Any]:
    if not _handoff_current_work_unit_is_owner_receipt(handoff):
        return {}
    recovery = _mapping_copy(payload.get("paper_recovery_state"))
    decision = _mapping_copy(recovery.get("supervisor_decision"))
    if decision.get("identity_match") is not True:
        return {}
    successor_action = build_current_executable_owner_action(payload)
    if not paper_recovery_successor_action_ready(successor_action):
        return {}
    if _provider_admission_terminal_closeout_consumed_current_work_unit(
        handoff
    ) and not paper_recovery_consumed_owner_receipt_successor(recovery):
        return {}
    return dict(successor_action)


def _provider_admission_terminal_closeout_consumed_current_work_unit(
    handoff: Mapping[str, Any],
) -> bool:
    consumed = _mapping_copy(handoff.get("provider_admission_terminal_closeout_consumed"))
    if not consumed:
        return False
    if _non_empty_text(consumed.get("owner_receipt_ref")) is None and _non_empty_text(
        consumed.get("typed_blocker_ref")
    ) is None:
        return False
    current = _mapping_copy(handoff.get("current_work_unit"))
    if not current:
        return False
    consumed_identity = _identity_values(consumed)
    current_identity = _identity_values(current)
    return not _identities_conflict(consumed_identity, current_identity)


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return [text for item in value if (text := _non_empty_text(item)) is not None]


def _first_text(items: list[str]) -> str | None:
    return items[0] if items else None


def _envelope_typed_blocker_reason(envelope: Mapping[str, Any]) -> str | None:
    blocker = _mapping_copy(envelope.get("typed_blocker"))
    for key in ("blocker_type", "blocker_id", "blocked_reason", "reason"):
        if text := _non_empty_text(blocker.get(key)):
            return text
    return None


def _work_unit_identity(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _non_empty_text(value.get("unit_id")) or _non_empty_text(value.get("work_unit_id"))
    return _non_empty_text(value)


def _fingerprint_identity(value: Mapping[str, Any]) -> str | None:
    basis = _mapping_copy(value.get("owner_route_currentness_basis")) or _mapping_copy(value.get("currentness_basis"))
    return (
        _non_empty_text(value.get("work_unit_fingerprint"))
        or _non_empty_text(value.get("action_fingerprint"))
        or _non_empty_text(value.get("fingerprint"))
        or _non_empty_text(value.get("source_fingerprint"))
        or _non_empty_text(basis.get("work_unit_fingerprint"))
        or _non_empty_text(basis.get("source_fingerprint"))
    )


__all__ = [
    "current_action_aligned_with_execution_envelope",
    "refresh_current_execution_surfaces",
    "typed_blocker_reason",
]
