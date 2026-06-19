from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.default_executor_action_policy import (
    request_output_surface_for_action_type,
    request_owner_for_action_type,
)
from med_autoscience.controllers.domain_action_request_materializer_parts import currentness_identity
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part


BRIDGE_AUTHORITY = "domain_action_request_materializer_paper_recovery_owner_callable"
PUBLISHABILITY_REPAIR_SPRINT_REQUIRED_INPUT = (
    "publishability_repair_sprint_or_single_typed_blocker_or_human_or_operator_gate"
)
PUBLISHABILITY_REPAIR_SPRINT_ACTION_TYPE = "run_quality_repair_batch"
PUBLISHABILITY_REPAIR_SPRINT_WORK_UNIT_ID = "publishability_repair_sprint"
SUPERVISOR_POLICY_PROJECTION_SURFACE = "paper_autonomy_supervisor_policy_projection"
SUPERVISOR_POLICY_PROJECTION_BOUNDARY = {
    "surface_kind": "paper_autonomy_supervisor_policy_projection_boundary",
    "decision_field_role": "policy_recommendation_label",
    "decision_field_is_authority": False,
    "mas_can_authorize_provider_admission": False,
    "mas_can_run_supervisor_decision_engine": False,
    "mas_can_store_recovery_obligation": False,
    "mas_can_run_fixed_point_runtime": False,
    "requires_opl_supervisor_decision_engine_readback": True,
}


def current_actions(
    *,
    profile: WorkspaceProfile | None,
    study_ids: tuple[str, ...],
) -> dict[str, dict[str, Any]]:
    if profile is None:
        return {}
    try:
        from med_autoscience.controllers import study_progress
        from med_autoscience.controllers.paper_recovery_state import build_paper_recovery_state
    except Exception:
        return {}
    actions: dict[str, dict[str, Any]] = {}
    for study_id in study_ids:
        try:
            progress = study_progress.read_study_progress(
                profile=profile,
                study_id=study_id,
                sync_runtime_summary=False,
                materialize_read_model_artifacts=False,
            )
        except Exception:
            continue
        if not isinstance(progress, Mapping):
            continue
        recovery = _current_recovery_state(progress, build_paper_recovery_state)
        action = action_for_study(
            {
                **dict(progress),
                "paper_recovery_state": recovery,
            }
        )
        if action is not None:
            actions[study_id] = action
    return actions


def action_for_study(study: Mapping[str, Any]) -> dict[str, Any] | None:
    recovery = _mapping(study.get("paper_recovery_state"))
    supervisor_decision = _mapping(recovery.get("supervisor_decision"))
    next_action = _mapping(recovery.get("next_safe_action"))
    if _text(recovery.get("phase")) != "owner_action_ready":
        return None
    if _text(supervisor_decision.get("decision")) not in {None, "materialize_recovery_action"}:
        return None
    if _terminal_owner_receipt_consumed_same_identity(
        study=study,
        recovery=recovery,
        next_action=next_action,
    ):
        return None
    successor_owner_action = _mapping(next_action.get("successor_owner_action"))
    if _text(next_action.get("kind")) == "materialize_successor_owner_action":
        return _action_from_successor_owner_action(
            study=study,
            recovery=recovery,
            supervisor_decision=supervisor_decision,
            next_action=next_action,
            successor_owner_action=successor_owner_action,
        )
    if _text(next_action.get("kind")) == "materialize_successor_owner_gate":
        return _action_from_successor_owner_gate(
            study=study,
            recovery=recovery,
            supervisor_decision=supervisor_decision,
            next_action=next_action,
            successor_owner_gate=_mapping(next_action.get("successor_owner_gate")),
        )
    if _text(next_action.get("kind")) != "run_mas_owner_callable":
        return None
    owner_callable = _mapping(next_action.get("owner_callable"))
    action_type = _text(owner_callable.get("action_type"))
    if action_type is None:
        return None
    obligation = _mapping(_mapping(recovery.get("current_authority")).get("obligation"))
    study_id = _text(obligation.get("study_id")) or _text(study.get("study_id"))
    if study_id is None:
        return None
    quest_id = _text(obligation.get("quest_id")) or _text(study.get("quest_id"))
    work_unit_id = _text(obligation.get("work_unit_id")) or action_type
    work_unit_fingerprint = _text(obligation.get("work_unit_fingerprint"))
    if work_unit_fingerprint is None:
        return None
    owner = _text(next_action.get("owner")) or _text(obligation.get("owner")) or _text(owner_callable.get("owner"))
    if owner is None:
        owner = request_owner_for_action_type(action_type)
    owner_route = owner_route_part.ensure_owner_route_v2(
        _mapping(study.get("owner_route"))
        or _owner_route(
            study_id=study_id,
            quest_id=quest_id,
            owner=owner,
            action_type=action_type,
            work_unit_id=work_unit_id,
            work_unit_fingerprint=work_unit_fingerprint,
            blocker_type=_text(obligation.get("blocker_type")),
            supervisor_decision=supervisor_decision,
        )
    )
    action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": action_type,
        "action_id": f"paper-recovery-owner-callable::{study_id}::{action_type}",
        "reason": _text(obligation.get("blocker_type")) or work_unit_id,
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "next_executable_owner": owner,
        "authority": "paper_recovery_state",
        "required_output_surface": request_output_surface_for_action_type(action_type),
        "source_surface": "paper_recovery_state",
        "source_ref": _text(recovery.get("recovery_obligation_id")),
        **_supervisor_policy_projection_fields(supervisor_decision),
        "work_unit_id": work_unit_id,
        "next_work_unit": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": work_unit_fingerprint,
        "owner_callable_surface": _text(owner_callable.get("callable_surface")),
        "owner_route": owner_route,
        "handoff_packet": {
            "action_type": action_type,
            "request_owner": owner,
            "recommended_owner": owner,
            "next_executable_owner": owner,
            "source_surface": "paper_recovery_state",
            "source_ref": _text(recovery.get("recovery_obligation_id")),
            **_supervisor_policy_projection_fields(supervisor_decision),
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "owner_callable_surface": _text(owner_callable.get("callable_surface")),
            "owner_route": owner_route,
            "idempotency_key": _text(owner_route.get("idempotency_key")),
        },
    }
    return {key: value for key, value in action.items() if value not in (None, "", [], {})}


def dispatch_matches_progress_successor(
    *,
    progress: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> bool:
    recovery = _mapping(progress.get("paper_recovery_state"))
    if _text(recovery.get("phase")) != "owner_action_ready":
        return False
    supervisor_decision = _mapping(recovery.get("supervisor_decision"))
    if _text(supervisor_decision.get("decision")) not in {None, "materialize_recovery_action"}:
        return False
    action = action_for_study(
        {
            **dict(progress),
            "paper_recovery_state": recovery,
        }
    )
    if action is None:
        return False
    if _text(action.get("action_type")) != _text(dispatch.get("action_type")):
        return False
    if _text(action.get("study_id")) != _text(dispatch.get("study_id")):
        return False
    action_owner = (
        _text(action.get("next_executable_owner"))
        or _text(action.get("owner"))
        or _text(action.get("next_owner"))
    )
    route = _dispatch_owner_route(dispatch)
    dispatch_owner = (
        _text(dispatch.get("next_executable_owner"))
        or _text(dispatch.get("owner"))
        or _text(route.get("next_owner"))
    )
    if action_owner is None or dispatch_owner != action_owner:
        return False
    source_refs = _mapping(route.get("source_refs"))
    if _text(source_refs.get("bridge_authority")) != BRIDGE_AUTHORITY:
        return False
    action_work_unit = _text(action.get("work_unit_id")) or _text(action.get("next_work_unit"))
    dispatch_work_unit = (
        _text(dispatch.get("work_unit_id"))
        or _text(dispatch.get("next_work_unit"))
        or _text(source_refs.get("work_unit_id"))
    )
    if action_work_unit is None or dispatch_work_unit != action_work_unit:
        return False
    action_fingerprint = _text(action.get("work_unit_fingerprint")) or _text(
        action.get("action_fingerprint")
    )
    dispatch_fingerprints = {
        text
        for value in (
            dispatch.get("work_unit_fingerprint"),
            dispatch.get("action_fingerprint"),
            dispatch.get("source_fingerprint"),
            route.get("work_unit_fingerprint"),
            route.get("source_fingerprint"),
            source_refs.get("work_unit_fingerprint"),
        )
        if (text := _text(value)) is not None
    }
    if action_fingerprint is None or action_fingerprint not in dispatch_fingerprints:
        return False
    action_decision_ref = _text(action.get("supervisor_decision_ref")) or _text(
        supervisor_decision.get("decision_id")
    )
    dispatch_decision_ref = _text(source_refs.get("supervisor_decision_ref")) or _text(
        _mapping(dispatch.get("source_action")).get("supervisor_decision_ref")
    )
    if action_decision_ref or dispatch_decision_ref:
        return action_decision_ref is not None and dispatch_decision_ref == action_decision_ref
    return True


def _action_from_successor_owner_gate(
    *,
    study: Mapping[str, Any],
    recovery: Mapping[str, Any],
    supervisor_decision: Mapping[str, Any],
    next_action: Mapping[str, Any],
    successor_owner_gate: Mapping[str, Any],
) -> dict[str, Any] | None:
    required_input = _text(next_action.get("required_input")) or _text(
        successor_owner_gate.get("required_input")
    )
    if required_input != PUBLISHABILITY_REPAIR_SPRINT_REQUIRED_INPUT:
        return None
    obligation = _mapping(_mapping(recovery.get("current_authority")).get("obligation"))
    study_id = _text(obligation.get("study_id")) or _text(study.get("study_id"))
    if study_id is None:
        return None
    quest_id = _text(obligation.get("quest_id")) or _text(study.get("quest_id"))
    predecessor = {
        "action_type": _text(obligation.get("action_type")),
        "work_unit_id": _text(obligation.get("work_unit_id")) or _text(
            successor_owner_gate.get("work_unit_id")
        ),
        "work_unit_fingerprint": _text(obligation.get("work_unit_fingerprint"))
        or _text(successor_owner_gate.get("work_unit_fingerprint")),
        "blocker_type": _text(obligation.get("blocker_type")),
    }
    predecessor_work_unit_id = _text(predecessor.get("work_unit_id"))
    predecessor_fingerprint = _text(predecessor.get("work_unit_fingerprint"))
    if predecessor_work_unit_id is None or predecessor_fingerprint is None:
        return None
    action_type = PUBLISHABILITY_REPAIR_SPRINT_ACTION_TYPE
    work_unit_id = PUBLISHABILITY_REPAIR_SPRINT_WORK_UNIT_ID
    work_unit_fingerprint = f"publishability-repair-sprint::anti-loop::{predecessor_work_unit_id}"
    owner = request_owner_for_action_type(action_type)
    owner_route = owner_route_part.ensure_owner_route_v2(
        _owner_route(
            study_id=study_id,
            quest_id=quest_id,
            owner=owner,
            action_type=action_type,
            work_unit_id=work_unit_id,
            work_unit_fingerprint=work_unit_fingerprint,
            blocker_type=_text(predecessor.get("blocker_type")) or required_input,
            supervisor_decision=supervisor_decision,
            predecessor=predecessor,
            source_surface=_text(successor_owner_gate.get("source_surface")),
            source_ref=_first_text(*_text_items(successor_owner_gate.get("evidence_refs"))),
        )
    )
    evidence_refs = _text_items(successor_owner_gate.get("evidence_refs"))
    compact_predecessor = {
        key: value for key, value in predecessor.items() if value not in (None, "", [], {})
    }
    action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": action_type,
        "action_id": f"paper-recovery-owner-gate::{study_id}::{action_type}::{work_unit_id}",
        "reason": required_input,
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "next_executable_owner": owner,
        "authority": "paper_recovery_state",
        "required_output_surface": request_output_surface_for_action_type(action_type),
        "source_surface": "paper_recovery_state",
        "source_ref": _text(recovery.get("recovery_obligation_id")),
        **_supervisor_policy_projection_fields(supervisor_decision),
        "work_unit_id": work_unit_id,
        "next_work_unit": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": work_unit_fingerprint,
        "required_delta_kind": required_input,
        "successor_source_surface": _text(successor_owner_gate.get("source_surface")),
        "successor_source_ref": evidence_refs[0] if evidence_refs else None,
        "predecessor_work_unit": compact_predecessor,
        "owner_gate": {
            "kind": "materialize_successor_owner_gate",
            "required_input": required_input,
            "provider_admission_allowed": False,
            "provider_admission_requires_opl_runtime_result": True,
            "evidence_refs": evidence_refs,
        },
        "owner_route": owner_route,
        "handoff_packet": {
            "action_type": action_type,
            "request_owner": owner,
            "recommended_owner": owner,
            "next_executable_owner": owner,
            "source_surface": "paper_recovery_state",
            "source_ref": _text(recovery.get("recovery_obligation_id")),
            **_supervisor_policy_projection_fields(supervisor_decision),
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "required_delta_kind": required_input,
            "successor_source_surface": _text(successor_owner_gate.get("source_surface")),
            "successor_source_ref": evidence_refs[0] if evidence_refs else None,
            "predecessor_work_unit": compact_predecessor,
            "owner_gate": {
                "kind": "materialize_successor_owner_gate",
                "required_input": required_input,
                "provider_admission_allowed": False,
                "provider_admission_requires_opl_runtime_result": True,
                "evidence_refs": evidence_refs,
            },
            "owner_route": owner_route,
            "idempotency_key": _text(owner_route.get("idempotency_key")),
        },
    }
    return {key: value for key, value in action.items() if value not in (None, "", [], {})}


def _action_from_successor_owner_action(
    *,
    study: Mapping[str, Any],
    recovery: Mapping[str, Any],
    supervisor_decision: Mapping[str, Any],
    next_action: Mapping[str, Any],
    successor_owner_action: Mapping[str, Any],
) -> dict[str, Any] | None:
    action_type = _text(successor_owner_action.get("action_type"))
    work_unit_id = _text(successor_owner_action.get("work_unit_id"))
    work_unit_fingerprint = _text(successor_owner_action.get("work_unit_fingerprint"))
    if action_type is None or work_unit_id is None or work_unit_fingerprint is None:
        return None
    obligation = _mapping(_mapping(recovery.get("current_authority")).get("obligation"))
    current_work_unit = _mapping(study.get("current_work_unit"))
    typed_blocker = _mapping(_mapping(current_work_unit.get("state")).get("typed_blocker"))
    study_id = (
        _text(obligation.get("study_id"))
        or _text(study.get("study_id"))
        or _text(current_work_unit.get("study_id"))
        or _text(typed_blocker.get("study_id"))
    )
    if study_id is None:
        return None
    quest_id = (
        _text(obligation.get("quest_id"))
        or _text(study.get("quest_id"))
        or _text(current_work_unit.get("quest_id"))
        or _text(typed_blocker.get("quest_id"))
    )
    predecessor_action_type = (
        _text(obligation.get("action_type"))
        or _text(current_work_unit.get("action_type"))
        or _text(typed_blocker.get("action_type"))
    )
    predecessor_work_unit_id = (
        _text(obligation.get("work_unit_id"))
        or _text(current_work_unit.get("work_unit_id"))
        or _text(typed_blocker.get("work_unit_id"))
    )
    predecessor_work_unit_fingerprint = (
        _text(obligation.get("work_unit_fingerprint"))
        or _text(current_work_unit.get("work_unit_fingerprint"))
        or _text(current_work_unit.get("action_fingerprint"))
        or _text(typed_blocker.get("work_unit_fingerprint"))
        or _text(typed_blocker.get("action_fingerprint"))
    )
    predecessor_blocker_type = (
        _text(obligation.get("blocker_type"))
        or _text(typed_blocker.get("blocker_type"))
        or _text(current_work_unit.get("blocker_type"))
    )
    transition_source_eval_id = currentness_identity.source_eval_id_from_study(study)
    source_eval_id = (
        _text(successor_owner_action.get("source_eval_id"))
        or _text(next_action.get("source_eval_id"))
        or transition_source_eval_id
        or _text(obligation.get("source_eval_id"))
        or _text(current_work_unit.get("source_eval_id"))
        or _text(typed_blocker.get("source_eval_id"))
    )
    owner = (
        _text(successor_owner_action.get("owner"))
        or _text(successor_owner_action.get("next_owner"))
        or _text(next_action.get("owner"))
        or request_owner_for_action_type(action_type)
    )
    predecessor = {
        "action_type": predecessor_action_type,
        "work_unit_id": predecessor_work_unit_id,
        "work_unit_fingerprint": predecessor_work_unit_fingerprint,
        "blocker_type": predecessor_blocker_type,
        "source_eval_id": source_eval_id,
    }
    owner_route = owner_route_part.ensure_owner_route_v2(
        _owner_route(
            study_id=study_id,
            quest_id=quest_id,
            owner=owner,
            action_type=action_type,
            work_unit_id=work_unit_id,
            work_unit_fingerprint=work_unit_fingerprint,
            blocker_type=predecessor_blocker_type,
            supervisor_decision=supervisor_decision,
            predecessor=predecessor,
            source_surface=_text(successor_owner_action.get("source_surface")),
            source_ref=_text(successor_owner_action.get("source_ref")),
            source_eval_id=source_eval_id,
        )
    )
    successor_source_ref = _text(successor_owner_action.get("source_ref"))
    source_ref = _text(recovery.get("recovery_obligation_id")) or successor_source_ref
    action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": action_type,
        "action_id": f"paper-recovery-successor::{study_id}::{action_type}::{work_unit_id}",
        "reason": _text(obligation.get("blocker_type")) or work_unit_id,
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "next_executable_owner": owner,
        "authority": "paper_recovery_state",
        "required_output_surface": request_output_surface_for_action_type(action_type),
        "source_surface": "paper_recovery_state",
        "source_ref": source_ref,
        "source_eval_id": source_eval_id,
        **_supervisor_policy_projection_fields(supervisor_decision),
        "work_unit_id": work_unit_id,
        "next_work_unit": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": work_unit_fingerprint,
        "successor_source_surface": _text(successor_owner_action.get("source_surface")),
        "successor_source_ref": successor_source_ref,
        "predecessor_work_unit": {key: value for key, value in predecessor.items() if value not in (None, "", [], {})},
        "owner_route": owner_route,
        "handoff_packet": {
            "action_type": action_type,
            "request_owner": owner,
            "recommended_owner": owner,
            "next_executable_owner": owner,
            "source_surface": "paper_recovery_state",
            "source_ref": source_ref,
            "source_eval_id": source_eval_id,
            **_supervisor_policy_projection_fields(supervisor_decision),
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "successor_source_surface": _text(successor_owner_action.get("source_surface")),
            "successor_source_ref": successor_source_ref,
            "predecessor_work_unit": {
                key: value for key, value in predecessor.items() if value not in (None, "", [], {})
            },
            "owner_route": owner_route,
            "idempotency_key": _text(owner_route.get("idempotency_key")),
        },
    }
    return {key: value for key, value in action.items() if value not in (None, "", [], {})}


def _owner_route(
    *,
    study_id: str,
    quest_id: str | None,
    owner: str,
    action_type: str,
    work_unit_id: str,
    work_unit_fingerprint: str,
    blocker_type: str | None,
    supervisor_decision: Mapping[str, Any] | None = None,
    predecessor: Mapping[str, Any] | None = None,
    source_surface: str | None = None,
    source_ref: str | None = None,
    source_eval_id: str | None = None,
) -> dict[str, Any]:
    decision = _mapping(supervisor_decision)
    predecessor_payload = _mapping(predecessor)
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": work_unit_fingerprint,
        "route_epoch": work_unit_fingerprint,
        "runtime_health_epoch": work_unit_fingerprint,
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_fingerprint": work_unit_fingerprint,
        "current_owner": "MedAutoScience",
        "next_owner": owner,
        "owner_reason": blocker_type or work_unit_id,
        "active_run_id": None,
        "allowed_actions": [action_type],
        "blocked_actions": [],
        "idempotency_key": f"paper-recovery::{study_id}::{action_type}::{work_unit_fingerprint}",
        "source_refs": {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "bridge_authority": BRIDGE_AUTHORITY,
            "source_surface": "paper_recovery_state",
            "successor_source_surface": source_surface,
            "successor_source_ref": source_ref,
            "source_eval_id": source_eval_id,
            **_supervisor_policy_projection_ref_fields(decision),
            "predecessor_action_type": _text(predecessor_payload.get("action_type")),
            "predecessor_work_unit_id": _text(predecessor_payload.get("work_unit_id")),
            "predecessor_work_unit_fingerprint": _text(
                predecessor_payload.get("work_unit_fingerprint")
            ),
            "predecessor_blocker_type": _text(predecessor_payload.get("blocker_type")),
            "owner_route_currentness_basis": {
                "truth_epoch": work_unit_fingerprint,
                "runtime_health_epoch": work_unit_fingerprint,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "source_eval_id": source_eval_id,
            },
        },
    }


def _supervisor_policy_projection_fields(supervisor_decision: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(supervisor_decision)
    if not decision:
        return {}
    return {
        "paper_autonomy_supervisor_decision": decision,
        "supervisor_decision": decision,
        "supervisor_decision_ref": _text(decision.get("decision_id")),
        "supervisor_policy_projection": SUPERVISOR_POLICY_PROJECTION_SURFACE,
        "supervisor_authority": SUPERVISOR_POLICY_PROJECTION_SURFACE,
        "supervisor_authority_boundary": "policy_projection_requires_opl_readback",
        "supervisor_policy_projection_boundary": dict(SUPERVISOR_POLICY_PROJECTION_BOUNDARY),
    }


def _supervisor_policy_projection_ref_fields(supervisor_decision: Mapping[str, Any]) -> dict[str, Any]:
    fields = _supervisor_policy_projection_fields(supervisor_decision)
    fields.pop("supervisor_authority", None)
    return fields


def _terminal_owner_receipt_consumed_same_identity(
    *,
    study: Mapping[str, Any],
    recovery: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> bool:
    target_work_unit_id, target_fingerprint = _target_recovery_identity(
        recovery=recovery,
        next_action=next_action,
    )
    if target_work_unit_id is None or target_fingerprint is None:
        return False
    for surface in (
        _mapping(study.get("current_work_unit")),
        _mapping(study.get("current_execution_envelope")),
    ):
        if not surface:
            continue
        if _terminal_surface_state_kind(surface) != "owner_receipt_recorded":
            continue
        if _owner_receipt_ref(surface) is None:
            continue
        work_unit_id, fingerprint = _surface_identity(surface)
        if work_unit_id == target_work_unit_id and fingerprint == target_fingerprint:
            return True
    return False


def _target_recovery_identity(
    *,
    recovery: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> tuple[str | None, str | None]:
    successor_owner_action = _mapping(next_action.get("successor_owner_action"))
    successor_owner_gate = _mapping(next_action.get("successor_owner_gate"))
    obligation = _mapping(_mapping(recovery.get("current_authority")).get("obligation"))
    return (
        _first_text(
            successor_owner_action.get("work_unit_id"),
            successor_owner_gate.get("work_unit_id"),
            obligation.get("work_unit_id"),
        ),
        _first_text(
            successor_owner_action.get("work_unit_fingerprint"),
            successor_owner_action.get("action_fingerprint"),
            successor_owner_gate.get("work_unit_fingerprint"),
            successor_owner_gate.get("action_fingerprint"),
            obligation.get("work_unit_fingerprint"),
            obligation.get("action_fingerprint"),
        ),
    )


def _terminal_surface_state_kind(surface: Mapping[str, Any]) -> str | None:
    state = _mapping(surface.get("state"))
    return _first_text(
        surface.get("status"),
        surface.get("state_kind"),
        state.get("state_kind"),
    )


def _surface_identity(surface: Mapping[str, Any]) -> tuple[str | None, str | None]:
    state = _mapping(surface.get("state"))
    binding = _mapping(state.get("owner_answer_binding")) or _mapping(
        surface.get("owner_answer_binding")
    )
    basis = _mapping(state.get("currentness_basis")) or _mapping(surface.get("currentness_basis"))
    return (
        _first_text(
            surface.get("work_unit_id"),
            state.get("work_unit_id"),
            binding.get("work_unit_id"),
            basis.get("work_unit_id"),
        ),
        _first_text(
            surface.get("work_unit_fingerprint"),
            surface.get("action_fingerprint"),
            state.get("work_unit_fingerprint"),
            state.get("action_fingerprint"),
            binding.get("work_unit_fingerprint"),
            binding.get("action_fingerprint"),
            basis.get("work_unit_fingerprint"),
            basis.get("action_fingerprint"),
        ),
    )


def _owner_receipt_ref(surface: Mapping[str, Any]) -> str | None:
    state = _mapping(surface.get("state"))
    binding = _mapping(state.get("owner_answer_binding")) or _mapping(
        surface.get("owner_answer_binding")
    )
    return _first_text(
        surface.get("owner_receipt_ref"),
        state.get("owner_receipt_ref"),
        binding.get("owner_receipt_ref"),
    )


def _dispatch_owner_route(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    return _mapping(dispatch.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))


def _current_recovery_state(
    progress: Mapping[str, Any],
    build_paper_recovery_state: Any,
) -> dict[str, Any]:
    recovery = _mapping(progress.get("paper_recovery_state"))
    if _text(recovery.get("phase")) is not None and _mapping(recovery.get("next_safe_action")):
        return recovery
    return build_paper_recovery_state(progress)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _first_text(*values: object) -> str | None:
    for value in values:
        if text := _text(value):
            return text
    return None


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return [text for item in value if (text := _text(item)) is not None]


__all__ = ["action_for_study", "current_actions", "dispatch_matches_progress_successor"]
