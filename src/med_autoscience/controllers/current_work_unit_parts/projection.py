from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.controllers.gate_clearing_batch_work_units import (
    PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS,
)
from med_autoscience.controllers.opl_execution_boundary import (
    OPL_EXECUTION_AUTHORIZATION_BLOCKER,
    OPL_EXECUTION_AUTHORIZATION_OWNER,
)
from med_autoscience.controllers.owner_route_reconcile_parts.stage_artifact_owner_actions import (
    READINESS_GATE_REPAIR_WORK_UNIT,
)
from med_autoscience.controllers.current_work_unit_parts.action_projection_fields import (
    acceptance_refs as _acceptance_refs,
    action_fingerprint as _action_fingerprint,
    action_type as _action_type,
    input_refs as _input_refs,
    required_output_contract as _required_output_contract,
    work_unit_fingerprint as _work_unit_fingerprint,
    work_unit_id as _work_unit_id,
)
from med_autoscience.controllers.current_work_unit_parts.contract import (
    AUTHORITY_BOUNDARY,
    SCHEMA_VERSION,
    SURFACE_KIND,
)
from med_autoscience.controllers.current_work_unit_parts.primitives import (
    mapping as _mapping,
    text as _text,
)
from med_autoscience.controllers.current_work_unit_parts.readiness_identity import (
    readiness_typed_blocker_currentness_basis,
    stage_owner_readiness_blocker_should_own_identity,
)
from med_autoscience.controllers.current_work_unit_parts.running_provider_attempt import (
    provider_attempt_proof_state,
    running_required_output_contract,
)
from med_autoscience.controllers.current_work_unit_parts.stage_packet_identity import (
    action_currentness_basis as _action_currentness_basis,
    current_action_fingerprint as _current_action_fingerprint,
    current_work_unit_fingerprint as _current_work_unit_fingerprint,
    currentness_basis_with_current_action_identity as _currentness_basis_with_current_action_identity,
    stage_packet_blocker_current_identity_action as _stage_packet_blocker_current_identity_action,
)
from med_autoscience.controllers.current_work_unit_parts.typed_blocker_owner_answer import (
    owner_answer_binding as _owner_answer_binding,
    owner_answer_typed_blocker as _owner_answer_typed_blocker,
    typed_blocker_required_output_contract as _typed_blocker_required_output_contract,
)
from med_autoscience.controllers.current_work_unit_parts.work_unit_fields import (
    action_source as _action_source,
    pending_provider_admission_evidence as _pending_provider_admission_evidence,
    provider_admission_pending as _provider_admission_pending,
    stage_id as _stage_id,
)

GATE_REPLAY_WORK_UNITS = PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS | frozenset(
    {READINESS_GATE_REPAIR_WORK_UNIT}
)


def action_work_unit(
    *,
    action: Mapping[str, Any],
    owner: str,
    status_payload: Mapping[str, Any],
    progress_payload: Mapping[str, Any],
    source_refs: Sequence[str],
    currentness_basis: Mapping[str, Any],
    provider_admission: Mapping[str, Any] | None,
) -> dict[str, Any]:
    action_type = _action_type(action)
    work_unit_id = (
        _work_unit_id(action.get("next_work_unit"))
        or _work_unit_id(action.get("work_unit_id"))
        or action_type
    )
    pending_provider_admission = _provider_admission_pending(provider_admission)
    return current_work_unit(
        status="executable_owner_action",
        owner=owner,
        action_type=action_type,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=_work_unit_fingerprint(action, currentness_basis=currentness_basis),
        action_fingerprint=_action_fingerprint(action, currentness_basis=currentness_basis),
        input_refs=_input_refs(action, source_refs),
        required_output_contract=_required_output_contract(action),
        acceptance_refs=_acceptance_refs(action),
        currentness_basis=currentness_basis,
        state={
            "state_kind": "executable_owner_action",
            "source": _action_source(action),
            "next_work_unit": work_unit_id,
            "owner_answer_missing": action.get("owner_answer_missing") is True,
            "owner_answer_still_required": action.get("owner_answer_still_required") is True,
            "latest_owner_answer_ref": _text(action.get("latest_owner_answer_ref")),
            "provider_admission_pending": pending_provider_admission,
            "pending_provider_admission_evidence": _pending_provider_admission_evidence(
                provider_admission
            )
            if pending_provider_admission
            else None,
        },
        status_payload=status_payload,
        progress_payload=progress_payload,
        action=action,
    )


def running_provider_attempt_work_unit(
    *,
    owner: str | None,
    action_type: str | None,
    work_unit_id: str | None,
    work_unit_fingerprint: str | None,
    action_fingerprint: str | None,
    source_refs: Sequence[str],
    currentness_basis: Mapping[str, Any],
    running_attempt: Mapping[str, Any],
    status_payload: Mapping[str, Any],
    progress_payload: Mapping[str, Any],
    action: Mapping[str, Any] | None,
) -> dict[str, Any]:
    return current_work_unit(
        status="running_provider_attempt",
        owner=owner,
        action_type=action_type,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
        action_fingerprint=action_fingerprint,
        input_refs=source_refs,
        required_output_contract=running_required_output_contract(running_attempt),
        acceptance_refs=_text_items(running_attempt.get("acceptance_refs")),
        currentness_basis=currentness_basis,
        state={
            "state_kind": "running_provider_attempt",
            "provider_attempt_proof": provider_attempt_proof_state(running_attempt),
            "strict_running_proof": True,
            "pending_provider_admission_only": False,
        },
        status_payload=status_payload,
        progress_payload=progress_payload,
        action=action,
    )


def owner_receipt_work_unit(
    *,
    recovery: Mapping[str, Any],
    action: Mapping[str, Any] | None,
    status_payload: Mapping[str, Any],
    progress_payload: Mapping[str, Any],
    source_refs: Sequence[str],
    currentness_basis: Mapping[str, Any],
) -> dict[str, Any]:
    next_action = _mapping(recovery.get("next_safe_action"))
    obligation = _mapping(_mapping(recovery.get("current_authority")).get("obligation"))
    owner_receipt_ref = _text(next_action.get("owner_receipt_ref")) or _text(
        recovery.get("owner_receipt_ref")
    )
    return current_work_unit(
        status="owner_receipt_recorded",
        owner=_text(next_action.get("owner"))
        or _text(obligation.get("owner"))
        or _text(_mapping(action).get("next_owner"))
        or _text(_mapping(action).get("owner")),
        action_type=_text(obligation.get("action_type")) or _action_type(_mapping(action)),
        work_unit_id=_work_unit_id(obligation.get("work_unit_id"))
        or _work_unit_id(_mapping(action).get("work_unit_id"))
        or _work_unit_id(_mapping(action).get("next_work_unit")),
        work_unit_fingerprint=_text(obligation.get("work_unit_fingerprint"))
        or _work_unit_fingerprint(_mapping(action), currentness_basis=currentness_basis),
        action_fingerprint=_text(obligation.get("action_fingerprint"))
        or _action_fingerprint(_mapping(action), currentness_basis=currentness_basis),
        input_refs=_input_refs(recovery, source_refs),
        required_output_contract={
            "owner_receipt_consumed": True,
            "owner_receipt_ref": owner_receipt_ref,
            "provider_completion_is_domain_completion": False,
            "domain_ready_authorized": False,
        },
        acceptance_refs=_text_items(recovery.get("evidence_refs")),
        currentness_basis=currentness_basis,
        state={
            "state_kind": "owner_receipt_recorded",
            "source": "paper_recovery_state.owner_receipt_recorded",
            "owner_receipt_ref": owner_receipt_ref,
            "next_safe_action_kind": _text(next_action.get("kind")),
            "provider_admission_pending": False,
            "owner_answer_binding": {
                "answer_kind": "owner_receipt_ref",
                "owner_receipt_ref": owner_receipt_ref,
            },
            "mas_owner_authority_preserved": True,
            "stale_queue_or_handoff_can_override": False,
        },
        status_payload=status_payload,
        progress_payload=progress_payload,
        action=action,
    )


def typed_blocker_work_unit(
    *,
    blocker: Mapping[str, Any],
    action: Mapping[str, Any] | None,
    status_payload: Mapping[str, Any],
    progress_payload: Mapping[str, Any],
    source_refs: Sequence[str],
    currentness_basis: Mapping[str, Any],
    source: str,
    status_kind: str = "typed_blocker",
) -> dict[str, Any]:
    blocker_type = (
        _text(blocker.get("blocker_type"))
        or _text(blocker.get("blocker_id"))
        or _text(blocker.get("blocked_reason"))
        or "typed_blocker"
    )
    owner = typed_blocker_current_work_unit_owner(blocker, blocker_type=blocker_type)
    effective_blocker = dict(blocker)
    resolved_action = action
    resolved_basis = dict(currentness_basis)
    resolved_work_unit_fingerprint = _text(blocker.get("work_unit_fingerprint"))
    resolved_action_fingerprint = _text(blocker.get("action_fingerprint"))
    current_identity_action = _stage_packet_blocker_current_identity_action(
        blocker=effective_blocker,
        action=resolved_action,
        progress=progress_payload,
        gate_replay_work_units=GATE_REPLAY_WORK_UNITS,
    )
    if current_identity_action is not None:
        resolved_action = resolved_action or current_identity_action
        action_basis = _action_currentness_basis(current_identity_action)
        current_work_unit_id = _work_unit_id(
            current_identity_action.get("work_unit_id")
        ) or _work_unit_id(current_identity_action.get("next_work_unit"))
        current_work_unit_fingerprint = _current_work_unit_fingerprint(
            current_identity_action,
            currentness_basis=action_basis,
        )
        current_action_fingerprint = _current_action_fingerprint(
            current_identity_action,
            currentness_basis=action_basis,
        )
        resolved_basis = _currentness_basis_with_current_action_identity(
            resolved_basis,
            action=current_identity_action,
            action_basis=action_basis,
            work_unit_id=current_work_unit_id,
            work_unit_fingerprint=current_work_unit_fingerprint,
            action_fingerprint=current_action_fingerprint,
        )
        if current_work_unit_id is not None:
            effective_blocker["work_unit_id"] = current_work_unit_id
        if current_work_unit_fingerprint is not None:
            effective_blocker["work_unit_fingerprint"] = current_work_unit_fingerprint
            resolved_work_unit_fingerprint = current_work_unit_fingerprint
        if current_action_fingerprint is not None:
            effective_blocker["action_fingerprint"] = current_action_fingerprint
            resolved_action_fingerprint = current_action_fingerprint
    if stage_owner_readiness_blocker_should_own_identity(
        blocker=effective_blocker,
        source=source,
        blocker_type=blocker_type,
    ):
        resolved_action = None
        resolved_basis = readiness_typed_blocker_currentness_basis(
            blocker=effective_blocker,
            progress=progress_payload,
            fallback_basis=currentness_basis,
        )
        resolved_work_unit_fingerprint = _text(resolved_basis.get("work_unit_fingerprint"))
        resolved_action_fingerprint = resolved_work_unit_fingerprint
    enriched_blocker = _owner_answer_typed_blocker(
        blocker=effective_blocker,
        action=resolved_action,
        currentness_basis=resolved_basis,
        work_unit_id=_work_unit_id(effective_blocker.get("work_unit_id"))
        or _work_unit_id(effective_blocker.get("next_work_unit")),
        work_unit_fingerprint=resolved_work_unit_fingerprint,
        action_fingerprint=resolved_action_fingerprint,
    )
    enriched_basis = _mapping(enriched_blocker.get("currentness_basis")) or resolved_basis
    resolved_work_unit_fingerprint = (
        _text(enriched_basis.get("work_unit_fingerprint")) or resolved_work_unit_fingerprint
    )
    resolved_action_fingerprint = (
        _text(enriched_basis.get("action_fingerprint")) or resolved_action_fingerprint
    )
    owner_answer_binding = _owner_answer_binding(
        blocker=enriched_blocker,
        action=resolved_action,
        currentness_basis=enriched_basis,
        progress_payload=progress_payload,
        status_payload=status_payload,
    )
    return current_work_unit(
        status=status_kind,
        owner=owner,
        action_type=_text(enriched_blocker.get("action_type"))
        or _text(enriched_blocker.get("work_unit_id")),
        work_unit_id=_work_unit_id(enriched_blocker.get("work_unit_id"))
        or _work_unit_id(enriched_blocker.get("next_work_unit")),
        work_unit_fingerprint=resolved_work_unit_fingerprint,
        action_fingerprint=resolved_action_fingerprint,
        input_refs=_input_refs(enriched_blocker, source_refs),
        required_output_contract=_typed_blocker_required_output_contract(enriched_blocker),
        acceptance_refs=_acceptance_refs(enriched_blocker),
        currentness_basis=enriched_basis,
        state={
            "state_kind": status_kind,
            "source": source,
            "typed_blocker": enriched_blocker,
            "owner_answer_binding": owner_answer_binding,
            "blocker_type": blocker_type,
            "mas_owner_authority_preserved": True,
            "stale_queue_or_handoff_can_override": False,
        },
        status_payload=status_payload,
        progress_payload=progress_payload,
        action=resolved_action,
    )


def typed_blocker_current_work_unit_owner(
    blocker: Mapping[str, Any],
    *,
    blocker_type: str,
) -> str:
    if blocker_type == OPL_EXECUTION_AUTHORIZATION_BLOCKER:
        return OPL_EXECUTION_AUTHORIZATION_OWNER
    return _text(blocker.get("owner")) or _text(blocker.get("next_owner")) or "med-autoscience"


def current_work_unit(
    *,
    status: str,
    owner: str | None,
    action_type: str | None,
    work_unit_id: str | None,
    work_unit_fingerprint: str | None,
    action_fingerprint: str | None,
    input_refs: Sequence[str],
    required_output_contract: Mapping[str, Any],
    acceptance_refs: Sequence[str],
    currentness_basis: Mapping[str, Any],
    state: Mapping[str, Any],
    status_payload: Mapping[str, Any],
    progress_payload: Mapping[str, Any],
    action: Mapping[str, Any] | None,
) -> dict[str, Any]:
    basis = dict(currentness_basis)
    if work_unit_id and not basis.get("work_unit_id"):
        basis["work_unit_id"] = work_unit_id
    if work_unit_fingerprint and not basis.get("work_unit_fingerprint"):
        basis["work_unit_fingerprint"] = work_unit_fingerprint
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "study_id": _text(progress_payload.get("study_id")) or _text(status_payload.get("study_id")),
        "quest_id": _text(progress_payload.get("quest_id")) or _text(status_payload.get("quest_id")),
        "stage_id": _stage_id(action=action, progress=progress_payload, status=status_payload),
        "owner": owner or "med-autoscience",
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": action_fingerprint,
        "input_refs": list(dict.fromkeys(input_refs)),
        "required_output_contract": dict(required_output_contract),
        "acceptance_refs": list(dict.fromkeys(acceptance_refs)),
        "state": {key: value for key, value in state.items() if value not in (None, "", [], {})},
        "currentness_basis": basis,
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _text(value)
        return [text] if text is not None else []
    if not isinstance(value, (list, tuple, set)):
        return []
    result: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


__all__ = [
    "action_work_unit",
    "current_work_unit",
    "owner_receipt_work_unit",
    "running_provider_attempt_work_unit",
    "typed_blocker_work_unit",
]
