from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.default_executor_action_policy import (
    request_output_surface_for_action_type,
    request_owner_for_action_type,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part


BRIDGE_AUTHORITY = "domain_action_request_materializer_paper_recovery_owner_callable"


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
        recovery = build_paper_recovery_state(progress)
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
    successor_owner_action = _mapping(next_action.get("successor_owner_action"))
    if _text(next_action.get("kind")) == "materialize_successor_owner_action":
        return _action_from_successor_owner_action(
            study=study,
            recovery=recovery,
            supervisor_decision=supervisor_decision,
            next_action=next_action,
            successor_owner_action=successor_owner_action,
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
    supervisor_decision_ref = _text(supervisor_decision.get("decision_id"))
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
        "supervisor_decision": supervisor_decision or None,
        "supervisor_decision_ref": supervisor_decision_ref,
        "supervisor_authority": "paper_autonomy_supervisor_decision" if supervisor_decision else None,
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
            "supervisor_decision": supervisor_decision or None,
            "supervisor_decision_ref": supervisor_decision_ref,
            "supervisor_authority": (
                "paper_autonomy_supervisor_decision" if supervisor_decision else None
            ),
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "owner_callable_surface": _text(owner_callable.get("callable_surface")),
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
    study_id = _text(obligation.get("study_id")) or _text(study.get("study_id"))
    if study_id is None:
        return None
    quest_id = _text(obligation.get("quest_id")) or _text(study.get("quest_id"))
    owner = (
        _text(successor_owner_action.get("owner"))
        or _text(successor_owner_action.get("next_owner"))
        or _text(next_action.get("owner"))
        or request_owner_for_action_type(action_type)
    )
    predecessor = {
        "action_type": _text(obligation.get("action_type")),
        "work_unit_id": _text(obligation.get("work_unit_id")),
        "work_unit_fingerprint": _text(obligation.get("work_unit_fingerprint")),
        "blocker_type": _text(obligation.get("blocker_type")),
    }
    owner_route = owner_route_part.ensure_owner_route_v2(
        _owner_route(
            study_id=study_id,
            quest_id=quest_id,
            owner=owner,
            action_type=action_type,
            work_unit_id=work_unit_id,
            work_unit_fingerprint=work_unit_fingerprint,
            blocker_type=_text(obligation.get("blocker_type")),
            supervisor_decision=supervisor_decision,
            predecessor=predecessor,
            source_surface=_text(successor_owner_action.get("source_surface")),
            source_ref=_text(successor_owner_action.get("source_ref")),
        )
    )
    supervisor_decision_ref = _text(supervisor_decision.get("decision_id"))
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
        "source_ref": _text(recovery.get("recovery_obligation_id")),
        "supervisor_decision": supervisor_decision or None,
        "supervisor_decision_ref": supervisor_decision_ref,
        "supervisor_authority": "paper_autonomy_supervisor_decision" if supervisor_decision else None,
        "work_unit_id": work_unit_id,
        "next_work_unit": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": work_unit_fingerprint,
        "successor_source_surface": _text(successor_owner_action.get("source_surface")),
        "successor_source_ref": _text(successor_owner_action.get("source_ref")),
        "predecessor_work_unit": {key: value for key, value in predecessor.items() if value not in (None, "", [], {})},
        "owner_route": owner_route,
        "handoff_packet": {
            "action_type": action_type,
            "request_owner": owner,
            "recommended_owner": owner,
            "next_executable_owner": owner,
            "source_surface": "paper_recovery_state",
            "source_ref": _text(recovery.get("recovery_obligation_id")),
            "supervisor_decision": supervisor_decision or None,
            "supervisor_decision_ref": supervisor_decision_ref,
            "supervisor_authority": (
                "paper_autonomy_supervisor_decision" if supervisor_decision else None
            ),
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "successor_source_surface": _text(successor_owner_action.get("source_surface")),
            "successor_source_ref": _text(successor_owner_action.get("source_ref")),
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
) -> dict[str, Any]:
    decision = _mapping(supervisor_decision)
    predecessor_payload = _mapping(predecessor)
    supervisor_decision_ref = _text(decision.get("decision_id"))
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
            "supervisor_authority": "paper_autonomy_supervisor_decision" if decision else None,
            "supervisor_decision_ref": supervisor_decision_ref,
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
            },
        },
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["action_for_study", "current_actions"]
