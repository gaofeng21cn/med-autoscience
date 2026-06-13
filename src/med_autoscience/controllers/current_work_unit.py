from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.controllers import control_identity
from med_autoscience.controllers.current_work_unit_parts.terminal_closeout_currentness import (
    consumed_gate_replay_blocker_for_action,
    gate_replay_consumed_by_source_eval,
    terminal_closeout_blocker_for_action,
)
from med_autoscience.controllers.gate_clearing_batch_work_units import (
    PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS,
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
from med_autoscience.controllers.current_work_unit_parts.current_action_selection import (
    action_from_envelope as _action_from_envelope,
    selected_current_action as _selected_current_action,
)
from med_autoscience.controllers.current_work_unit_parts.policy_constants import (
    CURRENT_ACTION_SUPERSEDED_PRIOR_ACTION_BLOCKERS,
    CURRENT_ACTION_SUPERSEDED_RUNTIME_BLOCKERS,
    MEDICAL_READINESS_BLOCKERS,
    OPL_CURRENT_CONTROL_ACTION_QUEUE_SOURCE,
    PAPER_DELTA_PRIOR_BLOCKER_SUPERSEDING_ACTION_SOURCES,
    PUBLICATION_EVAL_READINESS_REPAIR_SOURCE,
    PROVIDER_ADMISSION_AUTHORITIES,
    PROVIDER_ADMISSION_REPAIR_ACTIONS,
    REASON_ONLY_TYPED_BLOCKERS,
)
from med_autoscience.controllers.current_work_unit_parts.primitives import (
    mapping as _mapping,
    text as _text,
    text_items as _text_items,
)
from med_autoscience.controllers.current_work_unit_parts.readiness_identity import (
    readiness_typed_blocker_currentness_basis,
    stage_owner_readiness_blocker_should_own_identity,
)
from med_autoscience.controllers.current_work_unit_parts.repair_progress_precedence import (
    gate_replay_action_supersedes_stage_packet_blocker,
)
from med_autoscience.controllers.current_work_unit_parts.running_provider_attempt import (
    provider_attempt_proof_state,
    running_attempt_can_supersede_blocker,
    running_attempt_invalidated_by_progress,
    running_attempt_matches_current_action,
    running_attempt_satisfies_stage_owner_answer,
    running_required_output_contract,
    running_work_unit_id,
    strict_running_provider_attempt,
    typed_blocker_is_terminal_stop_loss,
)
from med_autoscience.controllers.current_work_unit_parts.stage_owner_answer import (
    stage_owner_answer_identity_typed_blocker as _stage_owner_answer_identity_typed_blocker,
    stage_owner_answer_missing_action as _stage_owner_answer_missing_action,
    stage_owner_answer_typed_blocker as _stage_owner_answer_typed_blocker,
)
from med_autoscience.runtime_control.owner_route_attempt_protocol import (
    currentness_basis as owner_route_currentness_basis,
    owner_reason_contract,
)


SURFACE_KIND = "current_work_unit"
SCHEMA_VERSION = 1
ALLOWED_STATUSES = (
    "executable_owner_action",
    "running_provider_attempt",
    "typed_blocker",
    "blocked_current_work_unit",
)
GATE_REPLAY_WORK_UNITS = PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS | frozenset({READINESS_GATE_REPAIR_WORK_UNIT})
AUTHORITY_BOUNDARY = {
    "surface_kind": SURFACE_KIND,
    "authority": "mas_current_work_unit_reducer",
    "top_level_truth": "status",
    "stage_transition_authority": "OPL Stage Transition Authority",
    "stage_authority_role": "non_authoritative_observation_and_intent_producer",
    "allowed_statuses": list(ALLOWED_STATUSES),
    "mas_owner_authority_preserved": True,
    "can_write_stage_current_pointer": False,
    "can_write_current_owner_delta": False,
    "can_write_stage_terminal_state": False,
    "can_write_runtime_owned_surfaces": False,
    "can_write_paper_or_package": False,
    "can_authorize_quality_verdict": False,
    "can_authorize_publication_ready": False,
}


def build_current_work_unit(
    *,
    status: Mapping[str, Any] | None = None,
    progress: Mapping[str, Any] | None = None,
    actions: Sequence[Mapping[str, Any]] | None = None,
    current_executable_owner_action: Mapping[str, Any] | None = None,
    current_execution_envelope: Mapping[str, Any] | None = None,
    owner_route: Mapping[str, Any] | None = None,
    provider_admission: Mapping[str, Any] | None = None,
    provider_running_proof: Mapping[str, Any] | None = None,
    live_provider_attempt: Mapping[str, Any] | None = None,
    typed_blocker: Mapping[str, Any] | None = None,
    blocked_reason: str | None = None,
    next_owner: str | None = None,
    runtime_health: Mapping[str, Any] | None = None,
    source_refs: Sequence[str] | None = None,
) -> dict[str, Any]:
    status_payload = _mapping(status)
    progress_payload = _mapping(progress)
    route_payload = _mapping(owner_route)
    runtime_health_payload = _mapping(runtime_health)
    resolved_source_refs = _source_refs(status_payload, progress_payload, source_refs)
    stage_owner_answer_action = _stage_owner_answer_missing_action(progress_payload)
    action = _selected_current_action(
        actions=actions,
        current_executable_owner_action=current_executable_owner_action,
    )
    if stage_owner_answer_action is not None and not _action_supersedes_stage_owner_answer(
        action=action,
        progress=progress_payload,
    ):
        action = stage_owner_answer_action
    elif action is not None and _action_consumed_by_dispatch_receipt(action=action, progress=progress_payload):
        action = None
    if action is None:
        action = _action_from_envelope(current_execution_envelope)
    if action is not None:
        action = _action_with_derived_currentness_identity(action=action, progress=progress_payload)
        if not _action_has_strong_currentness_identity(action):
            action = None
    resolved_typed_blocker = _typed_blocker(
        typed_blocker,
        blocked_reason=blocked_reason,
        owner=next_owner,
    )
    terminal_action_blocker = terminal_closeout_blocker_for_action(
        progress_payload,
        action=action,
        mapping=_mapping,
        text=_text,
        text_items=_text_items,
        action_type=_action_type,
        work_unit_id=_work_unit_id,
        work_unit_fingerprint=_work_unit_fingerprint,
        action_fingerprint=_action_fingerprint,
    )
    terminal_action_blocker_selected = False
    if terminal_action_blocker is not None and (
        not _typed_blocker_has_owner_answer_currentness(resolved_typed_blocker)
        or _typed_blocker_is_stage_owner_answer(resolved_typed_blocker)
    ):
        resolved_typed_blocker = terminal_action_blocker
        terminal_action_blocker_selected = True
    running_attempt = strict_running_provider_attempt(
        live_provider_attempt=live_provider_attempt,
        provider_running_proof=provider_running_proof,
        runtime_health=runtime_health_payload,
        owner=next_owner,
    )
    if running_attempt is None:
        running_attempt = strict_running_provider_attempt(
            live_provider_attempt=provider_admission,
            provider_running_proof=None,
            runtime_health=runtime_health_payload,
            owner=next_owner,
        )
    if running_attempt is not None and running_attempt_invalidated_by_progress(progress_payload):
        running_attempt = None
    if running_attempt is not None and not running_attempt_matches_current_action(
        running_attempt=running_attempt,
        action=action,
    ):
        running_attempt = None
    if (
        running_attempt is not None
        and stage_owner_answer_action is not None
        and not running_attempt_satisfies_stage_owner_answer(
            running_attempt=running_attempt,
            owner_answer_action=stage_owner_answer_action,
        )
    ):
        running_attempt = None
    stage_owner_identity_blocker = _stage_owner_answer_identity_typed_blocker(progress_payload)
    basis = _currentness_basis(
        owner_route=route_payload,
        action=action,
        progress=progress_payload,
        runtime_health=runtime_health_payload,
        running_attempt=running_attempt,
    )
    gate_replay_blocker = consumed_gate_replay_blocker_for_action(
        progress=progress_payload,
        action=action,
        currentness_basis=basis,
        mapping=_mapping,
        text=_text,
        text_items=_text_items,
    )
    if gate_replay_blocker is not None:
        return _typed_blocker_work_unit(
            blocker=gate_replay_blocker,
            action=action,
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            source="gate_clearing_batch_followthrough",
        )
    if running_attempt is not None:
        if running_attempt_can_supersede_blocker(resolved_typed_blocker):
            return _current_work_unit(
                status="running_provider_attempt",
                owner=_text(running_attempt.get("owner")) or _text(next_owner),
                action_type=_text(running_attempt.get("action_type")),
                work_unit_id=running_work_unit_id(running_attempt, currentness_basis=basis, action=action),
                work_unit_fingerprint=_text(running_attempt.get("work_unit_fingerprint")),
                action_fingerprint=_text(running_attempt.get("action_fingerprint")),
                input_refs=resolved_source_refs,
                required_output_contract=running_required_output_contract(running_attempt),
                acceptance_refs=_text_items(running_attempt.get("acceptance_refs")),
                currentness_basis=basis,
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
        if resolved_typed_blocker is not None:
            if action is not None and _action_supersedes_typed_blocker(
                action=action,
                blocker=resolved_typed_blocker,
                progress=progress_payload,
            ):
                return _action_work_unit(
                    action=action,
                    owner=_action_owner(action, next_owner=next_owner),
                    status_payload=status_payload,
                    progress_payload=progress_payload,
                    source_refs=resolved_source_refs,
                    currentness_basis=basis,
                    provider_admission=provider_admission,
                )
            return _typed_blocker_work_unit(
                blocker=resolved_typed_blocker,
                action=action,
                status_payload=status_payload,
                progress_payload=progress_payload,
                source_refs=resolved_source_refs,
                currentness_basis=basis,
                source="typed_blocker",
            )
    if resolved_typed_blocker is not None and typed_blocker_is_terminal_stop_loss(resolved_typed_blocker):
        return _typed_blocker_work_unit(
            blocker=resolved_typed_blocker,
            action=action,
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            source="typed_blocker",
        )
    if terminal_action_blocker_selected:
        return _typed_blocker_work_unit(
            blocker=terminal_action_blocker,
            action=action,
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            source="terminal_closeout_typed_blocker",
        )
    if stage_owner_identity_blocker is not None:
        return _typed_blocker_work_unit(
            blocker=stage_owner_identity_blocker,
            action=action,
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            source="stage_owner_answer_identity",
            status_kind="blocked_current_work_unit",
        )
    stage_owner_answer_blocker = _stage_owner_answer_typed_blocker(progress_payload)
    if stage_owner_answer_blocker is not None and not _action_supersedes_stage_owner_answer(
        action=action,
        progress=progress_payload,
    ):
        return _typed_blocker_work_unit(
            blocker=stage_owner_answer_blocker,
            action=action,
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            source="stage_owner_answer",
        )
    if action is not None and _action_supersedes_typed_blocker(
        action=action,
        blocker=resolved_typed_blocker,
        progress=progress_payload,
    ):
        return _action_work_unit(
            action=action,
            owner=_action_owner(action, next_owner=next_owner),
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            provider_admission=provider_admission,
        )
    if resolved_typed_blocker is not None:
        return _typed_blocker_work_unit(
            blocker=resolved_typed_blocker,
            action=action,
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            source="typed_blocker",
        )
    if action is not None:
        return _action_work_unit(
            action=action,
            owner=_action_owner(action, next_owner=next_owner),
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            provider_admission=provider_admission,
        )
    blocker = _minimal_blocker(blocked_reason or "current_work_unit_unresolved", owner=next_owner)
    return _typed_blocker_work_unit(
        blocker=blocker,
        action=None,
        status_payload=status_payload,
        progress_payload=progress_payload,
        source_refs=resolved_source_refs,
        currentness_basis=basis,
        source="blocked_current_work_unit",
        status_kind="blocked_current_work_unit",
    )


def _action_work_unit(
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
    work_unit_id = _work_unit_id(action.get("next_work_unit")) or _work_unit_id(action.get("work_unit_id")) or action_type
    pending_provider_admission = _provider_admission_pending(provider_admission)
    return _current_work_unit(
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


def _typed_blocker_work_unit(
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
    owner = _text(blocker.get("owner")) or _text(blocker.get("next_owner")) or "med-autoscience"
    blocker_type = (
        _text(blocker.get("blocker_type"))
        or _text(blocker.get("blocker_id"))
        or _text(blocker.get("blocked_reason"))
        or "typed_blocker"
    )
    resolved_action = action
    resolved_basis = dict(currentness_basis)
    resolved_work_unit_fingerprint = _text(blocker.get("work_unit_fingerprint"))
    resolved_action_fingerprint = _text(blocker.get("action_fingerprint"))
    if stage_owner_readiness_blocker_should_own_identity(
        blocker=blocker,
        source=source,
        blocker_type=blocker_type,
    ):
        resolved_action = None
        resolved_basis = readiness_typed_blocker_currentness_basis(
            blocker=blocker,
            progress=progress_payload,
            fallback_basis=currentness_basis,
        )
        resolved_work_unit_fingerprint = _text(resolved_basis.get("work_unit_fingerprint"))
        resolved_action_fingerprint = resolved_work_unit_fingerprint
    enriched_blocker = _owner_answer_typed_blocker(
        blocker=blocker,
        action=resolved_action,
        currentness_basis=resolved_basis,
        work_unit_id=_work_unit_id(blocker.get("work_unit_id")) or _work_unit_id(blocker.get("next_work_unit")),
        work_unit_fingerprint=resolved_work_unit_fingerprint,
        action_fingerprint=resolved_action_fingerprint,
    )
    owner_answer_binding = _owner_answer_binding(
        blocker=enriched_blocker,
        action=resolved_action,
        currentness_basis=resolved_basis,
        progress_payload=progress_payload,
        status_payload=status_payload,
    )
    return _current_work_unit(
        status=status_kind,
        owner=owner,
        action_type=_text(enriched_blocker.get("action_type")) or _text(enriched_blocker.get("work_unit_id")),
        work_unit_id=_work_unit_id(enriched_blocker.get("work_unit_id")) or _work_unit_id(
            enriched_blocker.get("next_work_unit")
        ),
        work_unit_fingerprint=resolved_work_unit_fingerprint,
        action_fingerprint=resolved_action_fingerprint,
        input_refs=_input_refs(enriched_blocker, source_refs),
        required_output_contract=_typed_blocker_required_output_contract(enriched_blocker),
        acceptance_refs=_acceptance_refs(enriched_blocker),
        currentness_basis=_mapping(enriched_blocker.get("currentness_basis")) or resolved_basis,
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


def _owner_answer_typed_blocker(
    *,
    blocker: Mapping[str, Any],
    action: Mapping[str, Any] | None,
    currentness_basis: Mapping[str, Any],
    work_unit_id: str | None,
    work_unit_fingerprint: str | None,
    action_fingerprint: str | None,
) -> dict[str, Any]:
    payload = dict(blocker)
    answer_ref = _typed_blocker_answer_ref(payload)
    if answer_ref is not None:
        payload["typed_blocker_ref"] = answer_ref
        payload["latest_owner_answer_ref"] = answer_ref
        payload["latest_owner_answer_kind"] = "typed_blocker"
    basis = _typed_blocker_owner_answer_basis(
        blocker=payload,
        action=action,
        currentness_basis=currentness_basis,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
        action_fingerprint=action_fingerprint,
    )
    if basis:
        payload["currentness_basis"] = basis
        payload["owner_route_currentness_basis"] = basis
    payload["owner_answer_shape"] = "typed_blocker_ref"
    return payload


def _typed_blocker_answer_ref(blocker: Mapping[str, Any]) -> str | None:
    closeout_refs = _text_items(blocker.get("closeout_refs"))
    for ref in closeout_refs:
        if ref.endswith("#typed_blocker"):
            return ref
    return _text(blocker.get("typed_blocker_ref")) or _text(blocker.get("source_ref"))


def _typed_blocker_has_owner_answer_currentness(blocker: Mapping[str, Any] | None) -> bool:
    payload = _mapping(blocker)
    if not payload:
        return False
    if _typed_blocker_answer_ref(payload) is not None:
        return True
    if _text(payload.get("latest_owner_answer_ref")) is not None:
        return True
    if _text_items(payload.get("closeout_refs")):
        return True
    if _mapping(payload.get("owner_answer_binding")):
        return True
    basis = _mapping(payload.get("currentness_basis")) or _mapping(
        payload.get("owner_route_currentness_basis")
    )
    return bool(
        _text(basis.get("work_unit_id"))
        and (
            _text(basis.get("work_unit_fingerprint"))
            or _text(basis.get("source_fingerprint"))
            or _text(basis.get("stage_attempt_id"))
        )
    )


def _typed_blocker_is_stage_owner_answer(blocker: Mapping[str, Any] | None) -> bool:
    payload = _mapping(blocker)
    if not payload:
        return False
    basis = _mapping(payload.get("currentness_basis")) or _mapping(
        payload.get("owner_route_currentness_basis")
    )
    return (
        _text(basis.get("source")) == "stage_owner_answer.typed_blocker"
        or _text(payload.get("latest_owner_answer_kind")) == "typed_blocker"
        and _text(payload.get("action_type")) == "complete_medical_paper_readiness_surface"
    )


def _typed_blocker_owner_answer_basis(
    *,
    blocker: Mapping[str, Any],
    action: Mapping[str, Any] | None,
    currentness_basis: Mapping[str, Any],
    work_unit_id: str | None,
    work_unit_fingerprint: str | None,
    action_fingerprint: str | None,
) -> dict[str, Any]:
    action_payload = _mapping(action)
    action_source_refs = _mapping(action_payload.get("source_refs"))
    existing = _mapping(blocker.get("currentness_basis")) or _mapping(
        blocker.get("owner_route_currentness_basis")
    )
    basis = {
        key: value
        for key, value in existing.items()
        if value not in (None, "", [], {}) and key not in _OWNER_ANSWER_IDENTITY_BASIS_KEYS
    }
    basis.update(
        {
            key: value
            for key, value in currentness_basis.items()
            if value not in (None, "", [], {})
        }
    )
    for key, value in {
        "source_eval_id": _text(action_payload.get("source_eval_id"))
        or _text(action_source_refs.get("source_eval_id")),
        "truth_epoch": _text(action_payload.get("truth_epoch")),
        "runtime_health_epoch": _text(action_payload.get("runtime_health_epoch")),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": action_fingerprint,
        "source_fingerprint": _text(blocker.get("source_fingerprint"))
        or _text(action_payload.get("source_fingerprint")),
        "idempotency_key": _text(blocker.get("idempotency_key")) or _text(action_payload.get("idempotency_key")),
        "stage_attempt_id": _text(blocker.get("stage_attempt_id")) or _text(action_payload.get("stage_attempt_id")),
    }.items():
        if value is not None:
            basis[key] = value
    return {key: value for key, value in basis.items() if value not in (None, "", [], {})}


_OWNER_ANSWER_IDENTITY_BASIS_KEYS = frozenset(
    {
        "source_eval_id",
        "truth_epoch",
        "runtime_health_epoch",
        "work_unit_id",
        "work_unit_fingerprint",
        "action_fingerprint",
        "source_fingerprint",
        "idempotency_key",
        "stage_attempt_id",
    }
)


def _owner_answer_binding(
    *,
    blocker: Mapping[str, Any],
    action: Mapping[str, Any] | None,
    currentness_basis: Mapping[str, Any],
    progress_payload: Mapping[str, Any],
    status_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    typed_blocker_ref = _typed_blocker_answer_ref(blocker)
    if typed_blocker_ref is None:
        return None
    basis = _mapping(blocker.get("currentness_basis")) or dict(currentness_basis)
    return {
        "answer_kind": "typed_blocker_ref",
        "typed_blocker_ref": typed_blocker_ref,
        "latest_owner_answer_ref": typed_blocker_ref,
        "accepted_answer_shape": [
            "domain_owner_receipt_ref",
            "quality_gate_receipt_ref",
            "typed_blocker_ref",
            "human_gate_ref",
            "route_back_evidence_ref",
        ],
        "stage_id": _stage_id(action=action, progress=progress_payload, status=status_payload),
        "work_unit_id": _text(basis.get("work_unit_id")) or _text(blocker.get("work_unit_id")),
        "work_unit_fingerprint": _text(basis.get("work_unit_fingerprint"))
        or _text(blocker.get("work_unit_fingerprint")),
        "source_fingerprint": _text(basis.get("source_fingerprint")) or _text(blocker.get("source_fingerprint")),
        "idempotency_key": _text(basis.get("idempotency_key")) or _text(blocker.get("idempotency_key")),
        "stage_attempt_id": _text(basis.get("stage_attempt_id")) or _text(blocker.get("stage_attempt_id")),
        "currentness_basis": basis,
        "stage_run_closeout_policy": {
            "owner_answer_required": True,
            "accepted_terminal_results": ["owner_receipt", "typed_blocker"],
            "provider_completion_is_domain_completion": False,
            "domain_ready_authorized": False,
        },
    }


def _typed_blocker_required_output_contract(blocker: Mapping[str, Any]) -> dict[str, Any]:
    contract = _required_output_contract(blocker)
    typed_blocker_ref = _typed_blocker_answer_ref(blocker)
    if typed_blocker_ref is None:
        return contract
    accepted = list(contract.get("accepted_terminal_results") or [])
    for item in ("owner_receipt", "typed_blocker"):
        if item not in accepted:
            accepted.append(item)
    return {
        **contract,
        "owner_receipt_required": contract.get("owner_receipt_required") is not False,
        "typed_blocker_accepted": True,
        "accepted_terminal_results": accepted,
        "accepted_return_shape": [
            "domain_owner_receipt_ref",
            "quality_gate_receipt_ref",
            "typed_blocker_ref",
            "human_gate_ref",
            "route_back_evidence_ref",
        ],
        "typed_blocker_ref": typed_blocker_ref,
        "provider_completion_is_domain_completion": False,
        "domain_ready_authorized": False,
    }


def _current_work_unit(
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


def _action_supersedes_stage_owner_answer(
    *,
    action: Mapping[str, Any] | None,
    progress: Mapping[str, Any],
) -> bool:
    payload = _mapping(action)
    if not payload:
        return False
    if _provider_admission_repair_action_supersedes_readiness_blocker(payload):
        return True
    if _gate_consumption_action_supersedes_readiness_blocker(payload):
        return True
    if _publication_eval_repair_action_supersedes_readiness_blocker(payload):
        return True
    if _terminal_routeback_action_from_gate_closeout(action=payload, progress=progress):
        return True
    return _paper_delta_current_action_supersedes_prior_blocker(
        action=payload,
        progress=progress,
    )


def _action_supersedes_typed_blocker(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any] | None,
    progress: Mapping[str, Any] | None = None,
) -> bool:
    payload = _mapping(blocker)
    if not payload:
        return True
    blocker_type = _text(payload.get("blocker_type"))
    if gate_replay_action_supersedes_stage_packet_blocker(
        action=action,
        blocker=payload,
        gate_replay_work_units=GATE_REPLAY_WORK_UNITS,
    ):
        return True
    if _terminal_routeback_action_supersedes_gate_replay_blocker(
        action=action,
        blocker=payload,
        progress=_mapping(progress),
    ):
        return True
    if blocker_type in CURRENT_ACTION_SUPERSEDED_RUNTIME_BLOCKERS:
        return (
            _action_is_stage_current_owner_delta(action)
            or _provider_admission_repair_action_supersedes_readiness_blocker(action)
            or _publication_eval_repair_action_supersedes_readiness_blocker(action)
            or _paper_delta_current_action_supersedes_prior_blocker(
                action=action,
                progress=_mapping(progress),
            )
        )
    if blocker_type in CURRENT_ACTION_SUPERSEDED_PRIOR_ACTION_BLOCKERS:
        return (
            _gate_followthrough_actionable_repair_action(action)
            or _publication_eval_repair_action_supersedes_readiness_blocker(action)
            or _paper_delta_current_action_supersedes_prior_blocker(
                action=action,
                progress=_mapping(progress),
            )
        )
    if blocker_type not in MEDICAL_READINESS_BLOCKERS:
        return False
    if _readiness_action_without_current_authority_binding(action):
        return False
    if _text(action.get("action_type")) == "complete_medical_paper_readiness_surface":
        return True
    if "complete_medical_paper_readiness_surface" in _text_items(action.get("allowed_actions")):
        return True
    if _provider_admission_repair_action_supersedes_readiness_blocker(action):
        return True
    if _gate_consumption_action_supersedes_readiness_blocker(action):
        return True
    if _publication_eval_repair_action_supersedes_readiness_blocker(action):
        return True
    return _paper_delta_current_action_supersedes_prior_blocker(
        action=action,
        progress=_mapping(progress),
    )


def _terminal_routeback_action_supersedes_gate_replay_blocker(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    action_source = _text(action.get("source_surface")) or _text(action.get("source"))
    if action_source != "study_progress.next_forced_delta.owner_action":
        return False
    if action.get("terminal_stage_next_forced_delta") is not True:
        return False
    if _text(action.get("action_type")) != "run_quality_repair_batch":
        return False
    if _text(action.get("next_owner")) != "write" and _text(action.get("owner")) != "write":
        return False
    action_work_unit = _work_unit_id(action.get("work_unit_id")) or _work_unit_id(
        action.get("next_work_unit")
    )
    if action_work_unit in {None, "publication_gate_replay", "complete_medical_paper_readiness_surface"}:
        return False
    blocker_work_unit = _work_unit_id(blocker.get("work_unit_id")) or _work_unit_id(
        blocker.get("next_work_unit")
    )
    blocker_type = (
        _text(blocker.get("blocker_type"))
        or _text(blocker.get("blocker_id"))
        or _text(blocker.get("blocked_reason"))
    )
    blocker_action_type = _text(blocker.get("action_type"))
    if blocker_action_type != "run_gate_clearing_batch":
        return False
    source_ref = _text(blocker.get("source_ref"))
    if source_ref is None:
        return False
    if not _terminal_gate_closeout_routes_to_action(
        progress=progress,
        action=action,
        source_ref=source_ref,
    ):
        return False
    if blocker_work_unit in GATE_REPLAY_WORK_UNITS:
        return True
    if blocker_work_unit == action_work_unit and blocker_type in {
        "publication_gate_replay_blocked",
        "medical_publication_surface_blocked",
    }:
        return True
    return blocker_type == "publication_gate_replay_blocked"


def _terminal_routeback_action_from_gate_closeout(
    *,
    action: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    action_source = _text(action.get("source_surface")) or _text(action.get("source"))
    if action_source != "study_progress.next_forced_delta.owner_action":
        return False
    if action.get("terminal_stage_next_forced_delta") is not True:
        return False
    if _text(action.get("action_type")) != "run_quality_repair_batch":
        return False
    if _text(action.get("next_owner")) != "write" and _text(action.get("owner")) != "write":
        return False
    action_work_unit = _work_unit_id(action.get("work_unit_id")) or _work_unit_id(
        action.get("next_work_unit")
    )
    if action_work_unit in {None, "publication_gate_replay", "complete_medical_paper_readiness_surface"}:
        return False
    for ref in _acceptance_refs(action):
        if _terminal_gate_closeout_routes_to_action(
            progress=progress,
            action=action,
            source_ref=ref,
        ):
            return True
    return False


def _terminal_gate_closeout_routes_to_action(
    *,
    progress: Mapping[str, Any],
    action: Mapping[str, Any],
    source_ref: str,
) -> bool:
    action_work_unit = _work_unit_id(action.get("work_unit_id")) or _work_unit_id(
        action.get("next_work_unit")
    )
    if action_work_unit is None:
        return False
    action_refs = set(_acceptance_refs(action))
    for terminal in _terminal_stage_candidates(progress):
        if _text(terminal.get("action_type")) != "run_gate_clearing_batch":
            continue
        paper_stage_log = _mapping(terminal.get("paper_stage_log"))
        next_delta = _mapping(terminal.get("next_forced_delta")) or _mapping(
            paper_stage_log.get("next_forced_delta")
        )
        terminal_work_unit = (
            _work_unit_id(terminal.get("work_unit_id"))
            or _work_unit_id(terminal.get("next_work_unit"))
            or _work_unit_id(next_delta.get("work_unit_id"))
        )
        if terminal_work_unit not in GATE_REPLAY_WORK_UNITS:
            continue
        terminal_ref = _text(terminal.get("source_path")) or _text(terminal.get("record_path"))
        terminal_refs = set(_text_items(terminal.get("closeout_refs")))
        if (
            source_ref != terminal_ref
            and source_ref not in terminal_refs
            and terminal_ref not in action_refs
            and not bool(action_refs.intersection(terminal_refs))
        ):
            continue
        owner_action = _mapping(next_delta.get("owner_action"))
        next_owner = _text(owner_action.get("next_owner")) or _text(owner_action.get("owner"))
        raw_action_type = _text(owner_action.get("action_type")) or _text(next_delta.get("action_type"))
        next_work_unit = _work_unit_id(owner_action.get("work_unit_id")) or _work_unit_id(
            next_delta.get("work_unit_id")
        )
        if next_owner != "write":
            continue
        if raw_action_type not in {"return_to_write", "run_quality_repair_batch"}:
            continue
        if next_work_unit != action_work_unit:
            continue
        return True
    return False


def _terminal_stage_candidates(progress: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    progress_first = _mapping(progress.get("progress_first_monitoring_summary"))
    handoff = _mapping(progress.get("opl_current_control_state_handoff"))
    candidates: list[dict[str, Any]] = []
    for value in (
        progress_first.get("latest_terminal_stage"),
        progress_first.get("latest_terminal_stage_log"),
        handoff.get("latest_terminal_stage_log"),
        progress.get("latest_terminal_stage"),
        progress.get("latest_terminal_stage_log"),
    ):
        terminal = _mapping(value)
        if terminal:
            candidates.append(terminal)
    return tuple(candidates)


def action_supersedes_typed_blocker(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any] | None,
    progress: Mapping[str, Any] | None = None,
) -> bool:
    return _action_supersedes_typed_blocker(
        action=action,
        blocker=blocker,
        progress=progress,
    )


def _action_has_strong_currentness_identity(action: Mapping[str, Any]) -> bool:
    if _action_type(action) is None:
        return False
    if _work_unit_id(action.get("next_work_unit")) is None and _work_unit_id(action.get("work_unit_id")) is None:
        return False
    fingerprint = _action_strong_currentness_fingerprint(action)
    if fingerprint is None or control_identity.is_synthetic_current_owner_ticket(fingerprint):
        return False
    return True


def _action_strong_currentness_fingerprint(action: Mapping[str, Any]) -> str | None:
    basis = _mapping(action.get("owner_route_currentness_basis"))
    fingerprint = (
        _text(action.get("work_unit_fingerprint"))
        or _text(action.get("action_fingerprint"))
        or _text(action.get("fingerprint"))
        or _text(basis.get("work_unit_fingerprint"))
        or _text(basis.get("source_fingerprint"))
    )
    if fingerprint is not None:
        if control_identity.is_synthetic_current_owner_ticket(fingerprint):
            return None
        return fingerprint
    return _route_currentness_fingerprint(action=action, progress={})


def _route_currentness_fingerprint(
    *,
    action: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> str | None:
    source = _text(action.get("source_surface")) or _text(action.get("source"))
    if source == "current_executable_owner_action":
        source = "study_progress.next_forced_delta.owner_action"
    if source not in {"study_progress.next_forced_delta.owner_action", OPL_CURRENT_CONTROL_ACTION_QUEUE_SOURCE}:
        return None
    for key in ("work_unit_fingerprint", "action_fingerprint", "fingerprint"):
        if control_identity.is_synthetic_current_owner_ticket(action.get(key)):
            return None
    action_type = _action_type(action)
    work_unit_id = _work_unit_id(action.get("work_unit_id")) or _work_unit_id(action.get("next_work_unit"))
    if action_type is None or work_unit_id is None:
        return None
    if action_type == "run_quality_repair_batch":
        return None
    if action_type == "run_gate_clearing_batch" and work_unit_id not in GATE_REPLAY_WORK_UNITS:
        return None
    if source == OPL_CURRENT_CONTROL_ACTION_QUEUE_SOURCE and not _action_matches_next_forced_delta(
        action=action,
        progress=progress,
    ):
        return None
    if (
        source == "study_progress.next_forced_delta.owner_action"
        and _mapping(action.get("target_surface")) == {}
        and _mapping(progress.get("next_forced_delta")) == {}
        and _text(action.get("source_eval_id")) is None
    ):
        return None
    target = _mapping(action.get("target_surface"))
    return control_identity.stable_route_currentness_fingerprint(
        study_id=_text(progress.get("study_id")),
        source=source,
        work_unit_id=work_unit_id,
        action_type=action_type,
        next_owner=_text(action.get("next_owner")) or _text(action.get("owner")),
        source_eval_id=_text(action.get("source_eval_id")),
        target_surface_ref=_text(target.get("surface_ref")),
        required_delta_kind=_text(action.get("required_delta_kind")),
    )


def _action_with_derived_currentness_identity(
    *,
    action: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(action)
    if _action_strong_currentness_fingerprint(payload) is not None:
        return payload
    fingerprint = _route_currentness_fingerprint(action=payload, progress=progress)
    if fingerprint is None:
        return payload
    payload["work_unit_fingerprint"] = fingerprint
    payload["action_fingerprint"] = fingerprint
    basis = dict(_mapping(payload.get("owner_route_currentness_basis")))
    basis["source"] = _text(payload.get("source_surface")) or _text(payload.get("source"))
    basis["work_unit_id"] = _work_unit_id(payload.get("work_unit_id")) or _work_unit_id(
        payload.get("next_work_unit")
    )
    basis["work_unit_fingerprint"] = fingerprint
    if source_eval_id := _text(payload.get("source_eval_id")):
        basis["source_eval_id"] = source_eval_id
    payload["owner_route_currentness_basis"] = basis
    return payload


def _readiness_action_without_current_authority_binding(action: Mapping[str, Any]) -> bool:
    action_types = {_text(action.get("action_type")), *_text_items(action.get("allowed_actions"))}
    if "complete_medical_paper_readiness_surface" not in action_types:
        return False
    source = _text(action.get("source_surface")) or _text(action.get("source"))
    if source == "stage_kernel_projection.current_owner_delta":
        return False
    if source == "study_progress.next_forced_delta.owner_action":
        return _mapping(action.get("terminal_closeout_dispatch")) == {}
    if _text(action.get("authority")) in PROVIDER_ADMISSION_AUTHORITIES:
        return False
    return True


def _action_is_stage_current_owner_delta(action: Mapping[str, Any]) -> bool:
    return (
        _text(action.get("source_surface"))
        or _text(action.get("source"))
    ) == "stage_kernel_projection.current_owner_delta"


def _paper_delta_current_action_supersedes_prior_blocker(
    *,
    action: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    progress_first = _mapping(progress.get("progress_first_sprint_state"))
    paper_delta = _mapping(progress.get("paper_progress_delta"))
    if progress_first.get("paper_progress_delta_counted") is not True and _delta_count(paper_delta) <= 0:
        return False
    action_source = _text(action.get("source_surface")) or _text(action.get("source"))
    if _text(action.get("action_type")) not in {
        "request_opl_stage_attempt",
        "return_to_ai_reviewer_workflow",
        "run_gate_clearing_batch",
        "run_quality_repair_batch",
    }:
        return False
    if _text(action.get("work_unit_id")) == "complete_medical_paper_readiness_surface":
        return False
    if action_source == "study_progress.next_forced_delta.owner_action":
        if _mapping(_mapping(progress.get("next_forced_delta")).get("owner_action")):
            return _action_matches_next_forced_delta(action=action, progress=progress)
        return True
    if action_source in PAPER_DELTA_PRIOR_BLOCKER_SUPERSEDING_ACTION_SOURCES:
        return True
    if action_source == OPL_CURRENT_CONTROL_ACTION_QUEUE_SOURCE:
        return _action_matches_next_forced_delta(action=action, progress=progress)
    return False


def _action_matches_next_forced_delta(
    *,
    action: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    next_forced_delta = _mapping(progress.get("next_forced_delta"))
    owner_action = _mapping(next_forced_delta.get("owner_action"))
    if not owner_action:
        return False
    expected_owner = _text(owner_action.get("next_owner")) or _text(owner_action.get("owner"))
    action_owner = _text(action.get("owner")) or _text(action.get("next_owner"))
    if expected_owner is None or action_owner != expected_owner:
        return False
    expected_work_unit = (
        _work_unit_id(owner_action.get("next_work_unit"))
        or _work_unit_id(owner_action.get("work_unit_id"))
        or _work_unit_id(next_forced_delta.get("work_unit_id"))
    )
    action_work_unit = (
        _work_unit_id(action.get("work_unit_id"))
        or _work_unit_id(action.get("next_work_unit"))
        or _work_unit_id(action.get("controller_next_work_unit"))
    )
    if expected_work_unit is None or action_work_unit != expected_work_unit:
        return False
    if expected_work_unit == "complete_medical_paper_readiness_surface":
        return False
    expected_actions = _text_items(owner_action.get("allowed_actions")) or _text_items(
        next_forced_delta.get("allowed_actions")
    )
    owner_action_type = _text(owner_action.get("action_type"))
    if owner_action_type is not None and owner_action_type not in expected_actions:
        expected_actions = [owner_action_type, *expected_actions]
    if not expected_actions:
        return False
    return _action_type(action) in set(expected_actions)


def _provider_admission_repair_action_supersedes_readiness_blocker(action: Mapping[str, Any]) -> bool:
    action_type = _text(action.get("action_type"))
    action_types = {action_type, *_text_items(action.get("allowed_actions"))}
    if not action_types.intersection(PROVIDER_ADMISSION_REPAIR_ACTIONS):
        return False
    if _text(action.get("work_unit_id")) == "complete_medical_paper_readiness_surface":
        return False
    if _text(action.get("next_work_unit")) == "complete_medical_paper_readiness_surface":
        return False
    if _mapping(action.get("repair_progress_followup")).get("accepted_owner_receipt") is True:
        return True
    authority = _text(action.get("authority"))
    if authority in PROVIDER_ADMISSION_AUTHORITIES:
        return True
    if _mapping(action.get("repair_progress_precedence")).get("accepted_owner_receipt") is True:
        return True
    if _gate_followthrough_actionable_repair_action(action):
        return True
    action_id = _text(action.get("action_id"))
    if action_id is not None and action_id.startswith("provider-admission::"):
        return True
    for key in ("action_fingerprint", "work_unit_fingerprint", "fingerprint"):
        text = _text(action.get(key))
        if text is not None and text.startswith("study-progress-current-owner-ticket::"):
            return True
    return False


def _publication_eval_repair_action_supersedes_readiness_blocker(action: Mapping[str, Any]) -> bool:
    if (_text(action.get("source_surface")) or _text(action.get("source"))) != PUBLICATION_EVAL_READINESS_REPAIR_SOURCE:
        return False
    action_type = _text(action.get("action_type"))
    action_types = {action_type, *_text_items(action.get("allowed_actions"))}
    if "run_quality_repair_batch" not in action_types:
        return False
    if _text(action.get("work_unit_id")) in {None, "complete_medical_paper_readiness_surface"}:
        return False
    return bool(_mapping(action.get("target_surface")).get("next_work_unit"))


def _gate_followthrough_actionable_repair_action(action: Mapping[str, Any]) -> bool:
    if _text(action.get("source")) != "gate_clearing_batch_followthrough.actionable_current_work_unit":
        return False
    work_unit = _text(action.get("work_unit_id"))
    if work_unit in {None, "complete_medical_paper_readiness_surface"}:
        return False
    target = _mapping(action.get("target_surface"))
    if _text(target.get("target_surface_specificity")) == "stage_kernel_typed_blocker_followup":
        return False
    return _text(target.get("ref_kind")) == "publication_work_unit"


def _gate_consumption_action_supersedes_readiness_blocker(action: Mapping[str, Any]) -> bool:
    action_types = {_text(action.get("action_type")), *_text_items(action.get("allowed_actions"))}
    if not action_types.intersection({"request_opl_stage_attempt", "run_gate_clearing_batch", "run_quality_repair_batch"}):
        return False
    work_unit = _text(action.get("work_unit_id")) or _text(action.get("next_work_unit"))
    if work_unit not in GATE_REPLAY_WORK_UNITS:
        return False
    target = _mapping(action.get("target_surface"))
    return _text(target.get("surface_ref")) == "artifacts/controller/gate_clearing_batch/latest.json"


def _typed_blocker(
    typed_blocker: Mapping[str, Any] | None,
    *,
    blocked_reason: str | None,
    owner: str | None,
) -> dict[str, Any] | None:
    if isinstance(typed_blocker, Mapping) and typed_blocker:
        return dict(typed_blocker)
    text = _text(blocked_reason)
    if text is None:
        return None
    if not _reason_only_blocked_reason_is_typed_blocker(reason=text, owner=owner):
        return None
    return _minimal_blocker(text, owner=owner)


def _minimal_blocker(blocker_type: str, *, owner: str | None) -> dict[str, Any]:
    return {
        "blocker_type": blocker_type,
        "owner": _text(owner) or "med-autoscience",
    }


def _reason_only_blocked_reason_is_typed_blocker(*, reason: str, owner: str | None) -> bool:
    if reason in REASON_ONLY_TYPED_BLOCKERS:
        return True
    contract = owner_reason_contract(reason=reason, owner=owner)
    if contract.get("registered") is not True:
        return True
    return not any(_text(action) is not None for action in contract.get("allowed_actions") or [])


def _currentness_basis(
    *,
    owner_route: Mapping[str, Any],
    action: Mapping[str, Any] | None,
    progress: Mapping[str, Any],
    runtime_health: Mapping[str, Any],
    running_attempt: Mapping[str, Any] | None,
) -> dict[str, Any]:
    basis = _mapping(owner_route_currentness_basis(owner_route)) if owner_route else {}
    action_payload = _mapping(action)
    action_source_refs = _mapping(action_payload.get("source_refs"))
    embedded = (
        _mapping(action_payload.get("owner_route_currentness_basis"))
        or _mapping(action_payload.get("currentness_basis"))
        or _mapping(action_source_refs.get("owner_route_currentness_basis"))
    )
    publication_eval = _mapping(progress.get("publication_eval"))
    running = _mapping(running_attempt)
    result = {
        **basis,
        **{key: value for key, value in embedded.items() if value not in (None, "", [], {})},
    }
    for key, value in {
        "source_eval_id": (
            _text(action_payload.get("source_eval_id"))
            or _text(action_source_refs.get("source_eval_id"))
            or _text(publication_eval.get("eval_id"))
        ),
        "work_unit_id": _work_unit_id(action_payload.get("work_unit_id"))
        or _work_unit_id(action_payload.get("next_work_unit"))
        or _route_work_unit_id(owner_route)
        or running_work_unit_id(running),
        "work_unit_fingerprint": _work_unit_fingerprint(action_payload, currentness_basis=result)
        or _text(running.get("work_unit_fingerprint")),
        "truth_epoch": _text(action_payload.get("truth_epoch")) or _text(progress.get("truth_epoch")),
        "runtime_health_epoch": _text(runtime_health.get("runtime_health_epoch"))
        or _text(action_payload.get("runtime_health_epoch")),
    }.items():
        if value is not None and result.get(key) in (None, "", [], {}):
            result[key] = value
    return {key: value for key, value in result.items() if value not in (None, "", [], {})}


def _action_consumed_by_dispatch_receipt(
    *,
    action: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    consumption = _mapping(_mapping(progress.get("progress_first_monitoring_summary")).get("dispatch_consumption"))
    if not consumption:
        consumption = _mapping(progress.get("dispatch_consumption"))
    if _text(consumption.get("consumption_status")) not in {"consumed", "receipt_consumed"}:
        return False
    action_work_unit = _work_unit_id(action.get("work_unit_id")) or _work_unit_id(action.get("next_work_unit"))
    consumed_work_unit = _work_unit_id(consumption.get("work_unit_id"))
    if action_work_unit is None or consumed_work_unit != action_work_unit:
        return False
    action_fingerprints = {
        text
        for value in (
            action.get("work_unit_fingerprint"),
            action.get("action_fingerprint"),
            action.get("fingerprint"),
        )
        if (text := _text(value)) is not None
    }
    if not action_fingerprints:
        current_action = _mapping(progress.get("current_executable_owner_action"))
        current_action_work_unit = _work_unit_id(current_action.get("work_unit_id")) or _work_unit_id(
            current_action.get("next_work_unit")
        )
        if (
            current_action_work_unit == action_work_unit
            and _text(current_action.get("action_type")) == _text(action.get("action_type"))
        ):
            action_fingerprints.update(
                text
                for value in (
                    current_action.get("work_unit_fingerprint"),
                    current_action.get("action_fingerprint"),
                    current_action.get("fingerprint"),
                )
                if (text := _text(value)) is not None
            )
    consumed_fingerprints = {
        text
        for value in (
            consumption.get("work_unit_fingerprint"),
            consumption.get("action_fingerprint"),
            _mapping(consumption.get("canonical_work_unit_identity")).get("work_unit_fingerprint"),
        )
        if (text := _text(value)) is not None
    }
    if not action_fingerprints or not consumed_fingerprints:
        return False
    if action_fingerprints.intersection(consumed_fingerprints):
        return True
    return gate_replay_consumed_by_source_eval(
        action=action,
        consumption=consumption,
        mapping=_mapping,
        text=_text,
    )


def _route_work_unit_id(route: Mapping[str, Any]) -> str | None:
    payload = _mapping(route)
    return _work_unit_id(payload.get("work_unit_id")) or _work_unit_id(payload.get("next_work_unit"))


def _provider_admission_pending(provider_admission: Mapping[str, Any] | None) -> bool:
    payload = _mapping(provider_admission)
    if not payload:
        return False
    if payload.get("running_provider_attempt") is True:
        return False
    return (
        payload.get("provider_admission_pending_count") not in (None, 0)
        or payload.get("provider_attempt_or_lease_required") is True
        or _text(payload.get("execution_status")) == "handoff_ready"
        or any(
            _text(item.get("authority")) in PROVIDER_ADMISSION_AUTHORITIES
            for item in payload.get("action_queue") or []
            if isinstance(item, Mapping)
        )
    )


def _pending_provider_admission_evidence(provider_admission: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = _mapping(provider_admission)
    return {
        "provider_admission_pending_count": payload.get("provider_admission_pending_count"),
        "execution_status": _text(payload.get("execution_status")),
        "provider_attempt_or_lease_required": payload.get("provider_attempt_or_lease_required") is True,
        "running_provider_attempt": payload.get("running_provider_attempt") is True,
    }


def _action_owner(action: Mapping[str, Any], *, next_owner: str | None) -> str:
    return (
        _text(action.get("owner"))
        or _text(action.get("recommended_owner"))
        or _text(action.get("next_owner"))
        or _text(next_owner)
        or "med-autoscience"
    )


def _action_source(action: Mapping[str, Any]) -> str | None:
    source = _text(action.get("source_surface")) or _text(action.get("source"))
    if source is not None:
        return source
    if (
        _mapping(action.get("repair_progress_followup")).get("accepted_owner_receipt") is True
        or _mapping(action.get("repair_progress_precedence")).get("accepted_owner_receipt") is True
    ):
        return "repair_progress_projection.mas_owner_repair_execution_evidence"
    return None


def _source_refs(
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    source_refs: Sequence[str] | None,
) -> list[str]:
    refs: list[str] = []
    for item in source_refs or []:
        ref = _text(item)
        if ref is not None:
            refs.append(ref)
    refs.extend(_refs_from(_mapping(progress.get("refs"))))
    refs.extend(_refs_from(_mapping(status.get("refs"))))
    return sorted(dict.fromkeys(refs))


def _refs_from(value: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("controller_decision_path", "publication_eval_path", "runtime_status_summary_path"):
        if (ref := _text(value.get(key))) is not None:
            refs.append(ref)
    return refs


def _stage_id(
    *,
    action: Mapping[str, Any] | None,
    progress: Mapping[str, Any],
    status: Mapping[str, Any],
) -> str | None:
    action_payload = _mapping(action)
    return (
        _text(action_payload.get("stage_id"))
        or _text(progress.get("current_stage"))
        or _text(status.get("current_stage"))
        or _text(status.get("stage_id"))
    )


def _delta_count(value: Mapping[str, Any]) -> int:
    try:
        return int(value.get("count") or 0)
    except (TypeError, ValueError):
        return 0


__all__ = [
    "ALLOWED_STATUSES",
    "SURFACE_KIND",
    "action_supersedes_typed_blocker",
    "build_current_work_unit",
]
