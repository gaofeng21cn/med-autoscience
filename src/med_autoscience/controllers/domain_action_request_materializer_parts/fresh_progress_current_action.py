from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from med_autoscience.controllers.default_executor_action_policy import (
    SUPPORTED_ACTION_TYPES,
    request_output_surface_for_action_type,
    request_owner_for_action_type,
)
from med_autoscience.controllers.domain_action_request_materializer_parts import (
    fresh_progress_arbitration,
    fresh_progress_identity,
    repair_progress_currentness,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.controllers.opl_execution_boundary import OPL_EXECUTION_AUTHORIZATION_BLOCKER
from med_autoscience.runtime_control import owner_route as owner_route_part


READINESS_ACTION_TYPE = "complete_medical_paper_readiness_surface"
DomainTransitionActions = Callable[[Mapping[str, Any]], list[dict[str, Any]]]
ExplicitReadinessAction = Callable[[Mapping[str, Any]], Mapping[str, Any]]


def current_actions(
    *,
    profile: WorkspaceProfile | None,
    study_ids: tuple[str, ...],
    domain_transition_actions: DomainTransitionActions,
    explicit_readiness_action: ExplicitReadinessAction,
) -> list[dict[str, Any]]:
    if profile is None:
        return []
    actions: list[dict[str, Any]] = []
    for study_id in study_ids:
        progress = _read_fresh_study_progress(profile=profile, study_id=study_id)
        if progress is None:
            continue
        action = _fresh_progress_current_action(
            study_id=study_id,
            progress=progress,
            domain_transition_actions=domain_transition_actions,
            explicit_readiness_action=explicit_readiness_action,
        )
        if action is not None:
            actions.append(action)
    return actions


def _read_fresh_study_progress(*, profile: WorkspaceProfile, study_id: str) -> dict[str, Any] | None:
    try:
        from med_autoscience.controllers import study_progress

        payload = study_progress.read_study_progress(
            profile=profile,
            study_id=study_id,
            sync_runtime_summary=False,
            materialize_read_model_artifacts=False,
        )
    except Exception:
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _fresh_progress_current_action(
    *,
    study_id: str,
    progress: Mapping[str, Any],
    domain_transition_actions: DomainTransitionActions,
    explicit_readiness_action: ExplicitReadinessAction,
) -> dict[str, Any] | None:
    accepted_owner_gate_action = _accepted_owner_gate_decision_action(
        study_id=study_id,
        progress=progress,
    )
    if accepted_owner_gate_action is not None:
        return accepted_owner_gate_action
    barrier = _fresh_progress_currentness_barrier(
        study_id=study_id,
        progress=progress,
        explicit_readiness_action=explicit_readiness_action,
    )
    if barrier is not None:
        return barrier
    if not _progress_has_executable_owner_action(progress):
        return None
    current_action = _mapping(progress.get("current_executable_owner_action"))
    repair_progress_followup = repair_progress_currentness.current_action_is_repair_progress_followup(
        current_action
    )
    explicit_gate_followthrough_action = _gate_followthrough_owner_action_has_strong_identity(
        current_action
    )
    ticket = (
        {}
        if repair_progress_followup or explicit_gate_followthrough_action
        else _current_owner_ticket(progress)
    )
    target_surface = _mapping(ticket.get("target_surface")) or _mapping(current_action.get("target_surface"))
    surface_key = (
        _text(ticket.get("surface_key"))
        or _text(target_surface.get("surface_key"))
        or _text(current_action.get("surface_key"))
        or _text(_mapping(current_action.get("target_surface")).get("surface_key"))
    )
    ticket_action_type = _text(ticket.get("allowed_action"))
    action_type = ticket_action_type if ticket_action_type in SUPPORTED_ACTION_TYPES else None
    source_surface = "study_progress.current_owner_ticket"
    if repair_progress_followup or explicit_gate_followthrough_action:
        action_type = fresh_progress_arbitration.current_action_supported_action_type(current_action)
        source_surface = "study_progress.current_executable_owner_action"
    if action_type is None:
        transition_action = _fresh_progress_domain_transition_action(
            study_id=study_id,
            progress=progress,
            current_action=current_action,
            domain_transition_actions=domain_transition_actions,
        )
        if transition_action is not None:
            return transition_action
        action_type = fresh_progress_arbitration.current_action_supported_action_type(current_action)
        source_surface = "study_progress.current_executable_owner_action"
    if action_type not in SUPPORTED_ACTION_TYPES:
        return None
    if action_type == READINESS_ACTION_TYPE:
        transition_action = _fresh_progress_domain_transition_action(
            study_id=study_id,
            progress=progress,
            current_action=current_action,
            domain_transition_actions=domain_transition_actions,
        )
        if transition_action is not None:
            return transition_action
        if surface_key is None:
            return None
    quest_id = _text(progress.get("quest_id"))
    work_unit_id = (
        _text(_mapping(ticket.get("work_unit")).get("work_unit_id"))
        or _text(current_action.get("work_unit_id"))
        or action_type
    )
    owner = (
        _text(ticket.get("owner"))
        or _text(current_action.get("next_owner"))
        or request_owner_for_action_type(action_type)
    )
    owner_route = _fresh_progress_owner_route(
        progress=progress,
        study_id=study_id,
        quest_id=quest_id,
        action_type=action_type,
        owner=owner,
        work_unit_id=work_unit_id,
    )
    if not owner_route:
        return fresh_progress_identity.weak_current_owner_ticket_action(
            study_id=study_id,
            quest_id=quest_id,
            action_type=action_type,
            owner=owner,
            work_unit_id=work_unit_id,
            source_surface=source_surface,
            current_action=current_action,
            ticket=ticket,
        )
    action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": action_type,
        "action_id": f"study-progress-current-owner-ticket::{study_id}::{action_type}",
        "reason": work_unit_id,
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "authority": source_surface,
        "required_output_surface": request_output_surface_for_action_type(action_type),
        "source_surface": source_surface,
        "current_action_source": _text(current_action.get("source"))
        or _text(current_action.get("source_surface")),
        "source_ref": _text(current_action.get("source_ref")),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": _text(owner_route.get("work_unit_fingerprint")),
        "surface_key": surface_key,
        "target_surface": target_surface or None,
        "required_delta_kind": _text(current_action.get("required_delta_kind")),
        "terminal_stage_next_forced_delta": (
            True if current_action.get("terminal_stage_next_forced_delta") is True else None
        ),
        "repair_progress_precedence": _mapping(current_action.get("repair_progress_precedence")) or None,
        "owner_route": owner_route,
        "handoff_packet": {
            "action_type": action_type,
            "request_owner": owner,
            "recommended_owner": owner,
            "next_executable_owner": owner,
            "source_surface": source_surface,
            "current_action_source": _text(current_action.get("source"))
            or _text(current_action.get("source_surface")),
            "source_ref": _text(current_action.get("source_ref")),
            "surface_key": surface_key,
            "owner_route": owner_route,
            "idempotency_key": _text(owner_route.get("idempotency_key")),
        },
    }
    return {key: value for key, value in action.items() if value is not None}


def _fresh_progress_currentness_barrier(
    *,
    study_id: str,
    progress: Mapping[str, Any],
    explicit_readiness_action: ExplicitReadinessAction,
) -> dict[str, Any] | None:
    envelope = _mapping(progress.get("current_execution_envelope"))
    state_kind = _text(envelope.get("state_kind")) or _text(envelope.get("execution_state_kind"))
    if state_kind not in {"typed_blocker", "parked", "running_provider_attempt"}:
        return None
    current_action = _mapping(progress.get("current_executable_owner_action"))
    if state_kind == "typed_blocker" and _fresh_progress_typed_blocker_reason(envelope) == (
        OPL_EXECUTION_AUTHORIZATION_BLOCKER
    ):
        return _typed_blocker_barrier(
            study_id=study_id,
            progress=progress,
            envelope=envelope,
            blocker=_mapping(envelope.get("typed_blocker")),
            reason=OPL_EXECUTION_AUTHORIZATION_BLOCKER,
            state_kind=state_kind,
        )
    if repair_progress_currentness.typed_blocker_allows_repair_progress_followup(
        envelope=envelope,
        current_action=current_action,
    ) or (
        state_kind == "typed_blocker"
        and repair_progress_currentness.current_action_is_repair_progress_followup(current_action)
    ) or _typed_blocker_allows_gate_followthrough_owner_action(
        envelope=envelope,
        current_action=current_action,
    ) or _typed_blocker_allows_domain_transition_owner_action(
        progress=progress,
        envelope=envelope,
        current_action=current_action,
    ):
        return None
    blocker = _mapping(envelope.get("typed_blocker"))
    current_work_unit = _mapping(progress.get("current_work_unit"))
    current_work_unit_state = _mapping(current_work_unit.get("state"))
    reason = (
        _text(blocker.get("blocker_id"))
        or _text(blocker.get("blocker_type"))
        or _text(blocker.get("reason"))
        or state_kind
    )
    if (
        state_kind == "typed_blocker"
        and reason == "medical_paper_readiness_missing"
        and explicit_readiness_action(progress)
    ):
        return None
    return _typed_blocker_barrier(
        study_id=study_id,
        progress=progress,
        envelope=envelope,
        blocker=blocker,
        reason=reason,
        state_kind=state_kind,
    )


def _typed_blocker_barrier(
    *,
    study_id: str,
    progress: Mapping[str, Any],
    envelope: Mapping[str, Any],
    blocker: Mapping[str, Any],
    reason: str,
    state_kind: str,
) -> dict[str, Any]:
    current_work_unit = _mapping(progress.get("current_work_unit"))
    current_work_unit_state = _mapping(current_work_unit.get("state"))
    state_kind = _text(envelope.get("state_kind")) or _text(envelope.get("execution_state_kind")) or "typed_blocker"
    owner = _text(envelope.get("owner")) or _text(blocker.get("owner")) or "MedAutoScience"
    return {
        "study_id": study_id,
        "quest_id": _text(progress.get("quest_id")),
        "action_type": f"current_execution_envelope_{state_kind}",
        "action_id": f"study-progress-current-execution-envelope::{study_id}::{state_kind}",
        "reason": reason,
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "authority": "study_progress.current_execution_envelope",
        "source_surface": "study_progress.current_execution_envelope",
        "source_ref": _text(blocker.get("source_ref")),
        "work_unit_id": _text(blocker.get("work_unit_id")) or _work_unit_id(envelope.get("next_work_unit")),
        "current_work_unit_status": _text(current_work_unit.get("status")),
        "current_work_unit_state_kind": _text(current_work_unit_state.get("state_kind")),
        "current_work_unit_id": _text(current_work_unit.get("work_unit_id")),
        "current_work_unit_fingerprint": _text(current_work_unit.get("work_unit_fingerprint")),
        "current_work_unit_stale_queue_or_handoff_can_override": current_work_unit_state.get(
            "stale_queue_or_handoff_can_override"
        ),
    }


def _fresh_progress_typed_blocker_reason(envelope: Mapping[str, Any]) -> str | None:
    blocker = _mapping(envelope.get("typed_blocker"))
    return (
        _text(blocker.get("blocker_id"))
        or _text(blocker.get("blocker_type"))
        or _text(blocker.get("reason"))
        or _text(blocker.get("blocked_reason"))
    )


def _progress_has_executable_owner_action(progress: Mapping[str, Any]) -> bool:
    current_action = _mapping(progress.get("current_executable_owner_action"))
    envelope = _mapping(progress.get("current_execution_envelope"))
    state_kind = _text(envelope.get("state_kind")) or _text(envelope.get("execution_state_kind"))
    if state_kind is not None:
        if (
            state_kind == "typed_blocker"
            and _fresh_progress_typed_blocker_reason(envelope) == OPL_EXECUTION_AUTHORIZATION_BLOCKER
        ):
            return False
        if repair_progress_currentness.typed_blocker_allows_repair_progress_followup(
            envelope=envelope,
            current_action=current_action,
        ):
            return _text(current_action.get("surface_kind")) == "current_executable_owner_action"
        if (
            state_kind == "typed_blocker"
            and _fresh_progress_typed_blocker_reason(envelope) == "medical_paper_readiness_missing"
        ):
            return _text(current_action.get("surface_kind")) == "current_executable_owner_action"
        if _typed_blocker_allows_gate_followthrough_owner_action(
            envelope=envelope,
            current_action=current_action,
        ):
            return _text(current_action.get("surface_kind")) == "current_executable_owner_action"
        if _typed_blocker_allows_domain_transition_owner_action(
            progress=progress,
            envelope=envelope,
            current_action=current_action,
        ):
            return _text(current_action.get("surface_kind")) == "current_executable_owner_action"
        return state_kind == "executable_owner_action"
    return _text(current_action.get("surface_kind")) == "current_executable_owner_action"


def _fresh_progress_domain_transition_action(
    *,
    study_id: str,
    progress: Mapping[str, Any],
    current_action: Mapping[str, Any],
    domain_transition_actions: DomainTransitionActions,
) -> dict[str, Any] | None:
    source = _text(current_action.get("source")) or _text(current_action.get("source_surface"))
    if source != "domain_transition":
        return None
    if _text(current_action.get("work_unit_id")) == READINESS_ACTION_TYPE:
        return None
    study_payload = _fresh_progress_domain_transition_study(
        study_id=study_id,
        progress=progress,
        current_action=current_action,
    )
    actions = domain_transition_actions(study_payload)
    return actions[0] if actions else None


def _typed_blocker_allows_gate_followthrough_owner_action(
    *,
    envelope: Mapping[str, Any],
    current_action: Mapping[str, Any],
) -> bool:
    state_kind = _text(envelope.get("state_kind")) or _text(envelope.get("execution_state_kind"))
    if state_kind != "typed_blocker":
        return False
    if _fresh_progress_typed_blocker_reason(envelope) == OPL_EXECUTION_AUTHORIZATION_BLOCKER:
        return False
    if not _gate_followthrough_owner_action_has_strong_identity(current_action):
        return False
    action_work_unit_id = _text(current_action.get("work_unit_id"))
    action_fingerprint = _text(current_action.get("work_unit_fingerprint")) or _text(
        current_action.get("action_fingerprint")
    )
    if action_work_unit_id is None or action_fingerprint is None:
        return False
    blocker = _mapping(envelope.get("typed_blocker"))
    blocker_work_unit_id = _text(blocker.get("work_unit_id")) or _work_unit_id(
        envelope.get("next_work_unit")
    )
    blocker_fingerprint = _text(blocker.get("work_unit_fingerprint")) or _text(
        blocker.get("action_fingerprint")
    )
    return (action_work_unit_id, action_fingerprint) != (
        blocker_work_unit_id,
        blocker_fingerprint,
    )


def _typed_blocker_allows_domain_transition_owner_action(
    *,
    progress: Mapping[str, Any],
    envelope: Mapping[str, Any],
    current_action: Mapping[str, Any],
) -> bool:
    state_kind = _text(envelope.get("state_kind")) or _text(envelope.get("execution_state_kind"))
    if state_kind != "typed_blocker":
        return False
    if _fresh_progress_typed_blocker_reason(envelope) == OPL_EXECUTION_AUTHORIZATION_BLOCKER:
        return False
    if not _domain_transition_owner_action_has_strong_identity(current_action):
        return False
    blocker = _mapping(envelope.get("typed_blocker"))
    if _text(blocker.get("blocker_type")) != "provider_completion_is_not_domain_ready" and _text(
        blocker.get("reason")
    ) != "provider_completion_is_not_domain_ready":
        return False
    if _text(envelope.get("source")) != "accepted_closeout_consumed_pending":
        current_work_unit = _mapping(progress.get("current_work_unit"))
        current_work_unit_state = _mapping(current_work_unit.get("state"))
        if _text(current_work_unit_state.get("source")) != "accepted_closeout_consumed_pending":
            return False
    transition = _mapping(progress.get("domain_transition"))
    completion = _mapping(transition.get("completion_receipt_consumption"))
    if _text(completion.get("status")) not in {"consumed", "receipt_consumed", "completed"}:
        return False
    if not _mapping(transition.get("next_work_unit")):
        return False
    action_work_unit_id = _text(current_action.get("work_unit_id")) or _work_unit_id(
        current_action.get("next_work_unit")
    )
    action_fingerprint = _text(current_action.get("work_unit_fingerprint")) or _text(
        current_action.get("action_fingerprint")
    )
    blocker_work_unit_id = _text(blocker.get("work_unit_id")) or _work_unit_id(
        envelope.get("next_work_unit")
    )
    blocker_fingerprint = _text(blocker.get("work_unit_fingerprint")) or _text(
        blocker.get("action_fingerprint")
    )
    return (action_work_unit_id, action_fingerprint) != (
        blocker_work_unit_id,
        blocker_fingerprint,
    )


def _domain_transition_owner_action_has_strong_identity(
    current_action: Mapping[str, Any],
) -> bool:
    if _text(current_action.get("surface_kind")) != "current_executable_owner_action":
        return False
    if _text(current_action.get("status")) not in {None, "ready"}:
        return False
    if (
        _text(current_action.get("source"))
        or _text(current_action.get("source_surface"))
    ) != "domain_transition":
        return False
    action_type = fresh_progress_arbitration.current_action_supported_action_type(current_action)
    if action_type not in SUPPORTED_ACTION_TYPES:
        return False
    return (
        (
            _text(current_action.get("work_unit_id"))
            or _work_unit_id(current_action.get("next_work_unit"))
        )
        is not None
        and (
            _text(current_action.get("work_unit_fingerprint"))
            or _text(current_action.get("action_fingerprint"))
        )
        is not None
    )


def _gate_followthrough_owner_action_has_strong_identity(
    current_action: Mapping[str, Any],
) -> bool:
    if _text(current_action.get("surface_kind")) != "current_executable_owner_action":
        return False
    if _text(current_action.get("status")) != "ready":
        return False
    if (
        _text(current_action.get("source"))
        or _text(current_action.get("source_surface"))
    ) != "gate_clearing_batch_followthrough.actionable_current_work_unit":
        return False
    action_type = fresh_progress_arbitration.current_action_supported_action_type(current_action)
    if action_type not in SUPPORTED_ACTION_TYPES:
        return False
    return (
        _text(current_action.get("work_unit_id")) is not None
        and (
            _text(current_action.get("work_unit_fingerprint"))
            or _text(current_action.get("action_fingerprint"))
        )
        is not None
    )


def _fresh_progress_domain_transition_study(
    *,
    study_id: str,
    progress: Mapping[str, Any],
    current_action: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(progress)
    payload["study_id"] = _text(payload.get("study_id")) or study_id
    if quest_id := _text(progress.get("quest_id")):
        payload["quest_id"] = quest_id
    payload["current_executable_owner_action"] = dict(current_action)
    if _mapping(payload.get("domain_transition")):
        return payload
    transition = _domain_transition_from_current_action(progress=progress, current_action=current_action)
    if transition:
        payload["domain_transition"] = transition
    return payload


def _domain_transition_from_current_action(
    *,
    progress: Mapping[str, Any],
    current_action: Mapping[str, Any],
) -> dict[str, Any]:
    envelope = _mapping(progress.get("current_execution_envelope"))
    work_unit_id = (
        _text(current_action.get("work_unit_id"))
        or _text(current_action.get("executable_work_unit"))
        or _work_unit_id(current_action.get("next_work_unit"))
        or _text(envelope.get("next_work_unit"))
    )
    if work_unit_id is None:
        return {}
    next_work_unit = _mapping(current_action.get("next_work_unit")) or {"unit_id": work_unit_id}
    if "lane" not in next_work_unit:
        if "gate_replay" in work_unit_id or "publication_gate" in work_unit_id:
            next_work_unit["lane"] = "publication_gate"
        elif _text(current_action.get("next_owner")) == "write" or _text(envelope.get("owner")) == "write":
            next_work_unit["lane"] = "write"
    route_target = (
        _text(current_action.get("route_target"))
        or _text(current_action.get("original_route_target"))
        or _text(current_action.get("next_owner"))
        or _text(envelope.get("owner"))
        or "controller"
    )
    return {
        "decision_type": _text(current_action.get("domain_transition_decision_type")) or "route_back_same_line",
        "route_target": route_target,
        "owner": route_target,
        "controller_action": _text(current_action.get("controller_action")) or "request_opl_stage_attempt",
        "next_work_unit": next_work_unit,
        "completion_receipt_consumption": {
            "status": "consumed",
            "receipt_ref": _text(current_action.get("source_ref")),
        },
    }


def _current_owner_ticket(progress: Mapping[str, Any]) -> dict[str, Any]:
    for value in (
        progress.get("current_owner_ticket"),
        _mapping(progress.get("progress_first_sprint_state")).get("current_owner_ticket"),
        _mapping(progress.get("next_forced_delta")).get("current_owner_ticket"),
    ):
        payload = _mapping(value)
        if _text(payload.get("surface_kind")) == "mas_current_owner_ticket":
            return payload
    return {}


def _accepted_owner_gate_decision_action(
    *,
    study_id: str,
    progress: Mapping[str, Any],
) -> dict[str, Any] | None:
    recovery = _mapping(progress.get("paper_recovery_state"))
    if _text(recovery.get("phase")) != "owner_action_ready":
        return None
    next_safe_action = _mapping(recovery.get("next_safe_action"))
    if _text(next_safe_action.get("kind")) != "route_back_to_owner_or_repair_materialization":
        return None
    accepted = _mapping(next_safe_action.get("accepted_owner_gate_decision"))
    if _text(accepted.get("decision")) != "route_back_to_mas_packet_materialization_bug":
        return None
    action_type = _text(accepted.get("action_type"))
    if action_type not in SUPPORTED_ACTION_TYPES:
        return None
    work_unit_id = _text(accepted.get("work_unit_id"))
    work_unit_fingerprint = _text(accepted.get("work_unit_fingerprint"))
    if work_unit_id is None or work_unit_fingerprint is None:
        return None
    current_work_unit = _mapping(progress.get("current_work_unit"))
    current_action_type = _text(current_work_unit.get("action_type"))
    current_work_unit_id = _text(current_work_unit.get("work_unit_id"))
    current_fingerprint = _text(current_work_unit.get("work_unit_fingerprint")) or _text(
        current_work_unit.get("action_fingerprint")
    )
    if current_action_type not in {None, action_type}:
        return None
    if current_work_unit_id not in {None, work_unit_id}:
        return None
    if current_fingerprint not in {None, work_unit_fingerprint}:
        return None
    quest_id = _text(progress.get("quest_id"))
    owner = request_owner_for_action_type(action_type)
    provider_admission_allowed = next_safe_action.get("provider_admission_allowed") is True
    owner_route = owner_route_part.ensure_owner_route_v2(
        {
            "surface": "domain_route_owner_route",
            "schema_version": 2,
            "study_id": study_id,
            "quest_id": quest_id,
            "truth_epoch": work_unit_fingerprint,
            "runtime_health_epoch": work_unit_fingerprint,
            "work_unit_fingerprint": work_unit_fingerprint,
            "source_fingerprint": work_unit_fingerprint,
            "current_owner": "mas_controller",
            "next_owner": owner,
            "owner_reason": work_unit_id,
            "active_run_id": _text(progress.get("active_run_id")),
            "allowed_actions": [action_type],
            "blocked_actions": sorted(item for item in SUPPORTED_ACTION_TYPES if item != action_type),
            "source_refs": {
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "source_surface": "paper_recovery_state.accepted_owner_gate_decision",
                "source_ref": _text(accepted.get("route_back_evidence_ref")),
                "owner_route_currentness_basis": {
                    "truth_epoch": work_unit_fingerprint,
                    "runtime_health_epoch": work_unit_fingerprint,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": work_unit_fingerprint,
                },
            },
            "idempotency_key": (
                f"paper-recovery-owner-gate::{study_id}::{action_type}::{work_unit_fingerprint}"
            ),
        }
    )
    return {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": action_type,
        "action_id": f"paper-recovery-owner-gate::{study_id}::{action_type}",
        "reason": work_unit_id,
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "authority": "paper_recovery_state.accepted_owner_gate_decision",
        "required_output_surface": request_output_surface_for_action_type(action_type),
        "source_surface": "paper_recovery_state.accepted_owner_gate_decision",
        "source_ref": _text(accepted.get("route_back_evidence_ref")),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": work_unit_fingerprint,
        "provider_admission_allowed": provider_admission_allowed,
        "paper_progress_stall": (
            None
            if provider_admission_allowed
            else {
                "kind": "owner_gate_route_back",
                "route_back_evidence_ref": _text(accepted.get("route_back_evidence_ref")),
                "provider_admission_allowed": False,
            }
        ),
        "owner_route": owner_route,
        "handoff_packet": {
            "action_type": action_type,
            "request_owner": owner,
            "recommended_owner": owner,
            "next_executable_owner": owner,
            "source_surface": "paper_recovery_state.accepted_owner_gate_decision",
            "source_ref": _text(accepted.get("route_back_evidence_ref")),
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "provider_admission_allowed": provider_admission_allowed,
            "owner_route": owner_route,
            "idempotency_key": _text(owner_route.get("idempotency_key")),
        },
    }


def _fresh_progress_owner_route(
    *,
    progress: Mapping[str, Any],
    study_id: str,
    quest_id: str | None,
    action_type: str,
    owner: str,
    work_unit_id: str,
) -> dict[str, Any]:
    raw_current_route = _mapping(progress.get("owner_route"))
    current_route = owner_route_part.ensure_owner_route_v2(raw_current_route)
    candidate_action = {
        "action_type": action_type,
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "next_executable_owner": owner,
    }
    if current_route and owner_route_part.route_allows_action(
        action=candidate_action,
        owner_route=current_route,
    ):
        if fresh_progress_identity.owner_route_has_strong_currentness(raw_current_route):
            return current_route
        return {}
    current_action = _mapping(progress.get("current_executable_owner_action"))
    ticket = _current_owner_ticket(progress)
    route_values = fresh_progress_identity.owner_route_values(
        progress=progress,
        current_action=current_action,
        ticket=ticket,
        action_type=action_type,
        work_unit_id=work_unit_id,
    )
    if not route_values:
        return {}
    truth_epoch = route_values["truth_epoch"]
    runtime_health_epoch = route_values["runtime_health_epoch"]
    source_fingerprint = route_values["source_fingerprint"]
    work_unit_fingerprint = route_values["work_unit_fingerprint"]
    source_ref = route_values.get("source_ref") or "unknown"
    owner_reason = _text(current_action.get("reason")) or work_unit_id
    currentness_basis = {
        key: value
        for key, value in {
            "truth_epoch": truth_epoch,
            "runtime_health_epoch": runtime_health_epoch,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "source_eval_id": route_values.get("source_eval_id"),
        }.items()
        if value is not None
    }
    route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": truth_epoch,
        "runtime_health_epoch": runtime_health_epoch,
        "work_unit_fingerprint": work_unit_fingerprint,
        "failure_signature": owner_reason,
        "trace_id": f"owner-route-trace::{study_id}::{action_type}",
        "route_epoch": truth_epoch,
        "source_fingerprint": source_fingerprint,
        "current_owner": "mas_controller",
        "next_owner": owner,
        "owner_reason": owner_reason,
        "active_run_id": _text(progress.get("active_run_id")),
        "allowed_actions": [action_type],
        "blocked_actions": sorted(item for item in SUPPORTED_ACTION_TYPES if item != action_type),
        "source_refs": {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "source_surface": "study_progress.current_owner_ticket",
            "source_ref": source_ref,
            "owner_route_currentness_basis": currentness_basis,
        },
        "idempotency_key": (
            f"owner-route::{study_id}::{truth_epoch}::{owner}::{action_type}::{work_unit_fingerprint}"
        ),
    }
    return owner_route_part.ensure_owner_route_v2(route)


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id")) or _text(value.get("work_unit_id"))
    return _text(value)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["current_actions"]
