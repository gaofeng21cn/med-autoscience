from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers import current_execution_envelope, current_work_unit
from med_autoscience.controllers.current_work_unit_parts.policy_constants import (
    CURRENT_ACTION_SUPERSEDED_RUNTIME_BLOCKERS,
)
from med_autoscience.controllers.current_work_unit_parts.terminal_closeout_currentness import (
    OPL_RUNTIME_TERMINAL_BLOCKERS,
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
from ..shared import _mapping_copy, _non_empty_text


def refresh_current_execution_surfaces(
    *,
    payload: dict[str, Any],
    status: Mapping[str, Any],
    handoff: Mapping[str, Any],
    runtime_health_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    updated = dict(payload)
    handoff_executable_action = current_control_executable_owner_action(handoff)
    if handoff_executable_action:
        updated["current_executable_owner_action"] = handoff_executable_action
        handoff = current_control_executable_currentness_handoff(
            handoff,
            current_control_executable_action=handoff_executable_action,
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


def _canonical_current_control_typed_blocker_work_unit(handoff: Mapping[str, Any]) -> dict[str, Any]:
    if handoff.get("running_provider_attempt") is True:
        return {}
    current = _mapping_copy(handoff.get("current_work_unit"))
    if _non_empty_text(current.get("status")) in {"typed_blocker", "blocked_current_work_unit"}:
        return current
    return {}


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
    source_fingerprint = _non_empty_text(repair.get("source_fingerprint"))
    if source_work_unit is None or source_fingerprint is None:
        return {}
    return {
        "paper_delta_observed": True,
        "accepted_owner_receipt": True,
        "superseded_stage_native_action": "run_quality_repair_batch",
        "source_work_unit_id": source_work_unit,
        "source_fingerprint": source_fingerprint,
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
    typed_blocker = _mapping_copy(handoff.get("typed_blocker"))
    if typed_blocker:
        return typed_blocker
    if not current_execution_handoff_consumes_current_action(handoff):
        return {}
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


def _handoff_consumes_current_action_for_refresh(
    *,
    payload: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> bool:
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
